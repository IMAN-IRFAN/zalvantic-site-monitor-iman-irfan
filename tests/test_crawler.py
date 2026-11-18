import functools
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

import pytest

from monitor.crawler import crawl


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def site(tmp_path):
    (tmp_path / "index.html").write_text(
        '<a href="about.html">About</a>'
        '<a href="missing-page.html">Broken</a>'
        '<a href="https://nonexistent.invalid">Broken external</a>'
    )
    (tmp_path / "about.html").write_text(
        '<a href="index.html">Home</a>'
        '<a href="deep-missing.html">Broken</a>'
        '<a href="private/secret.html">Private</a>'
    )
    (tmp_path / "robots.txt").write_text("User-agent: *\nDisallow: /private/\n")
    (tmp_path / "private").mkdir()
    (tmp_path / "private" / "secret.html").write_text("secret")

    handler = functools.partial(QuietHandler, directory=str(tmp_path))
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()


def test_reports_planted_broken_links(site):
    report = crawl(f"{site}/index.html", delay=0)
    broken = {item["url"] for item in report["broken"]}
    assert broken == {
        f"{site}/missing-page.html",
        f"{site}/deep-missing.html",
        "https://nonexistent.invalid",
    }


def test_working_links_not_reported(site):
    report = crawl(f"{site}/index.html", delay=0)
    broken = {item["url"] for item in report["broken"]}
    assert f"{site}/about.html" not in broken
    assert f"{site}/index.html" not in broken


def test_internal_and_external_types(site):
    report = crawl(f"{site}/index.html", delay=0)
    types = {item["url"]: item["type"] for item in report["broken"]}
    assert types[f"{site}/missing-page.html"] == "internal"
    assert types["https://nonexistent.invalid"] == "external"


def test_robots_txt_is_respected(site):
    report = crawl(f"{site}/index.html", delay=0)
    assert f"{site}/private/secret.html" in report["skipped_by_robots"]


def test_max_pages_limit(site):
    report = crawl(f"{site}/index.html", max_pages=1, delay=0)
    assert report["pages_fetched"] == 1