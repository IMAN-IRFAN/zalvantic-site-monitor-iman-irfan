import argparse
import time
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from monitor.crawler import HTTP_ERRORS, SKIP_PREFIXES, USER_AGENT, load_robots

TITLE_MIN, TITLE_MAX = 10, 60
DESC_MIN, DESC_MAX = 50, 160


def check_title(soup):
    tag = soup.find("title")
    text = tag.get_text(strip=True) if tag else ""
    if not text:
        return False, "Missing <title>"
    if not TITLE_MIN <= len(text) <= TITLE_MAX:
        return False, f"Title is {len(text)} characters (aim for {TITLE_MIN}-{TITLE_MAX})"
    return True, "Title length is good"


def check_meta_description(soup):
    tag = soup.find("meta", attrs={"name": "description"})
    text = (tag.get("content") or "").strip() if tag else ""
    if not text:
        return False, "Missing meta description"
    if not DESC_MIN <= len(text) <= DESC_MAX:
        return False, f"Meta description is {len(text)} characters (aim for {DESC_MIN}-{DESC_MAX})"
    return True, "Meta description length is good"


def check_h1(soup):
    count = len(soup.find_all("h1"))
    if count == 0:
        return False, "No <h1> heading"
    if count > 1:
        return False, f"{count} <h1> headings (use exactly one)"
    return True, "Exactly one <h1>"


def check_canonical(soup):
    tag = soup.find("link", rel="canonical")
    if tag is None or not (tag.get("href") or "").strip():
        return False, "Missing canonical link"
    return True, "Canonical link present"


def check_image_alt(soup):
    images = soup.find_all("img")
    missing = [img for img in images if not (img.get("alt") or "").strip()]
    if missing:
        return False, f"{len(missing)} of {len(images)} images have no alt text"
    return True, "All images have alt text"


# rule name -> (function, points). The points add up to 100.
PAGE_RULES = {
    "title": (check_title, 25),
    "meta_description": (check_meta_description, 25),
    "h1": (check_h1, 20),
    "canonical": (check_canonical, 15),
    "image_alt": (check_image_alt, 15),
}


def score_page(html):
    soup = BeautifulSoup(html, "html.parser")
    rules = {}
    score = 0
    for name, (check, points) in PAGE_RULES.items():
        passed, message = check(soup)
        rules[name] = {"passed": passed, "message": message, "points": points}
        if passed:
            score += points
    return {"score": score, "rules": rules}


def check_site_files(client, base, timeout=10.0):
    found = {}
    for name in ("sitemap.xml", "robots.txt"):
        try:
            found[name] = client.get(f"{base}/{name}", timeout=timeout).status_code == 200
        except HTTP_ERRORS:
            found[name] = False
    return found


def internal_links(soup, page_url, site):
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href or href.startswith(SKIP_PREFIXES):
            continue
        link = urldefrag(urljoin(page_url, href))[0]
        parsed = urlparse(link)
        if parsed.scheme in ("http", "https") and parsed.netloc == site and link not in links:
            links.append(link)
    return links


def build_report(pages, files):
    page_avg = round(sum(p["score"] for p in pages) / len(pages)) if pages else 0
    sitemap_points = 10 if files.get("sitemap.xml") else 0
    robots_points = 10 if files.get("robots.txt") else 0
    site_score = round(page_avg * 0.8) + sitemap_points + robots_points if pages else 0
    explanation = (
        f"Site score = 80% of the average page score ({page_avg}) "
        f"+ 10 for sitemap.xml ({sitemap_points}) + 10 for robots.txt ({robots_points})"
    )
    return {
        "pages": pages,
        "files": files,
        "page_average": page_avg,
        "site_score": site_score,
        "explanation": explanation,
    }


def audit_site(start_url, max_pages=10, delay=1.0, timeout=10.0):
    parsed = urlparse(start_url)
    site = parsed.netloc
    base = f"{parsed.scheme}://{site}"
    pages = []

    with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:
        robots = load_robots(client, base)
        files = check_site_files(client, base, timeout)
        queue = [start_url]
        seen = {start_url}
        while queue and len(pages) < max_pages:
            url = queue.pop(0)
            if not robots.can_fetch(USER_AGENT, url):
                continue
            time.sleep(delay)
            try:
                response = client.get(url, timeout=timeout, follow_redirects=True)
            except HTTP_ERRORS:
                continue
            if response.status_code >= 400 or "text/html" not in response.headers.get(
                "content-type", ""
            ):
                continue
            result = score_page(response.text)
            result["url"] = url
            pages.append(result)
            soup = BeautifulSoup(response.text, "html.parser")
            for link in internal_links(soup, url, site):
                if link not in seen:
                    seen.add(link)
                    queue.append(link)

    return build_report(pages, files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Basic SEO audit for a site you own.")
    parser.add_argument("url")
    parser.add_argument("--max-pages", type=int, default=10)
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    args = parser.parse_args()

    report = audit_site(args.url, args.max_pages, args.delay)
    print(f"SEO report for {args.url}")
    print(f"Pages audited: {len(report['pages'])}\n")
    for page in report["pages"]:
        print(f"{page['url']}  score {page['score']}/100")
        for name, rule in page["rules"].items():
            mark = "PASS" if rule["passed"] else "FAIL"
            print(f"  [{mark}] {name}: {rule['message']}")
        print()
    print("Site files:")
    for name, found in report["files"].items():
        print(f"  [{'PASS' if found else 'FAIL'}] {name}")
    print()
    print(f"SITE SCORE: {report['site_score']}/100")
    print(report["explanation"])


if __name__ == "__main__":
    main()