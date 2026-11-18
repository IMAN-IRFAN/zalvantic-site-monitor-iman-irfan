import argparse
import time
from collections import deque
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

USER_AGENT = "ZalvanticSiteMonitor/1.0 (internship project)"
SKIP_PREFIXES = ("mailto:", "tel:", "javascript:", "#")
HTTP_ERRORS = (httpx.HTTPError, httpx.InvalidURL)


def load_robots(client, base):
    robots = RobotFileParser()
    try:
        response = client.get(f"{base}/robots.txt", timeout=10.0)
        lines = response.text.splitlines() if response.status_code == 200 else []
    except HTTP_ERRORS:
        lines = []
    robots.parse(lines)
    return robots


def check_link(client, url, timeout=10.0):
    """HEAD first; GET only if the server does not support HEAD."""
    try:
        response = client.head(url, timeout=timeout, follow_redirects=True)
        if response.status_code in (405, 501):
            response = client.get(url, timeout=timeout, follow_redirects=True)
        return response.status_code, None
    except HTTP_ERRORS as exc:
        return None, str(exc)


def crawl(start_url, max_depth=2, max_pages=20, delay=1.0, timeout=10.0):
    site = urlparse(start_url).netloc
    base = f"{urlparse(start_url).scheme}://{site}"
    last_request = 0.0
    checked = {}  # link -> (status, error)
    found_on = {}  # link -> page where it was first found
    skipped = set()
    fetched = 0

    with httpx.Client(headers={"User-Agent": USER_AGENT}) as client:

        def wait():
            nonlocal last_request
            pause = delay - (time.monotonic() - last_request)
            if pause > 0:
                time.sleep(pause)
            last_request = time.monotonic()

        robots = load_robots(client, base)
        queue = deque()
        queued = set()
        if robots.can_fetch(USER_AGENT, start_url):
            queue.append((start_url, 0))
            queued.add(start_url)
        else:
            skipped.add(start_url)

        while queue and fetched < max_pages:
            url, depth = queue.popleft()
            wait()
            try:
                response = client.get(url, timeout=timeout, follow_redirects=True)
            except HTTP_ERRORS as exc:
                checked[url] = (None, str(exc))
                continue
            fetched += 1
            checked[url] = (response.status_code, None)
            content_type = response.headers.get("content-type", "")
            if response.status_code >= 400 or "text/html" not in content_type:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup.find_all("a", href=True):
                href = tag["href"].strip()
                if not href or href.startswith(SKIP_PREFIXES):
                    continue
                link = urldefrag(urljoin(url, href))[0]
                if urlparse(link).scheme not in ("http", "https"):
                    continue
                found_on.setdefault(link, url)
                if link in checked or link in queued:
                    continue
                if urlparse(link).netloc == site:  # internal link
                    if not robots.can_fetch(USER_AGENT, link):
                        skipped.add(link)
                        continue
                    if depth + 1 <= max_depth:
                        queue.append((link, depth + 1))
                        queued.add(link)
                        continue
                wait()
                checked[link] = check_link(client, link, timeout)

        # pages that were queued but never fetched (max_pages reached)
        for link, _ in queue:
            wait()
            checked[link] = check_link(client, link, timeout)

    broken = [
        {
            "url": link,
            "found_on": found_on.get(link),
            "status": status,
            "error": error,
            "type": "internal" if urlparse(link).netloc == site else "external",
        }
        for link, (status, error) in checked.items()
        if status is None or status >= 400
    ]
    return {
        "pages_fetched": fetched,
        "links_checked": len(checked),
        "broken": broken,
        "skipped_by_robots": sorted(skipped),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Find broken links on a site you own.")
    parser.add_argument("url")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-pages", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    args = parser.parse_args()

    report = crawl(args.url, args.depth, args.max_pages, args.delay)
    print(f"Pages fetched: {report['pages_fetched']}   Links checked: {report['links_checked']}")
    print(f"Skipped because of robots.txt: {len(report['skipped_by_robots'])}")
    if not report["broken"]:
        print("No broken links found.")
    for item in report["broken"]:
        result = item["status"] if item["status"] is not None else item["error"]
        where = item["found_on"] or "start page"
        print(f"[{item['type']}] {item['url']} -> {result} (found on {where})")


if __name__ == "__main__":
    main()