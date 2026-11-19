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