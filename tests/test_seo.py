from bs4 import BeautifulSoup

from monitor.seo import (
    build_report,
    check_canonical,
    check_h1,
    check_image_alt,
    check_meta_description,
    check_title,
    score_page,
)

GOOD_PAGE = """
<html><head>
<title>Zalvantic Test Site - Home Page</title>
<meta name="description" content="A small test website used to practise checking on-page SEO basics such as titles and headings.">
<link rel="canonical" href="https://example.com/">
</head><body>
<h1>Welcome</h1>
<img src="logo.png" alt="Company logo">
</body></html>
"""

BAD_PAGE = """
<html><head></head><body>
<h1>One</h1><h1>Two</h1>
<img src="photo.png">
</body></html>
"""


def soup(html):
    return BeautifulSoup(html, "html.parser")


def test_title_good():
    assert check_title(soup("<title>A good page title here</title>"))[0] is True


def test_title_missing():
    assert check_title(soup("<html></html>"))[0] is False


def test_title_too_short():
    assert check_title(soup("<title>Hi</title>"))[0] is False


def test_title_too_long():
    assert check_title(soup(f"<title>{'x' * 80}</title>"))[0] is False


def test_meta_description_good():
    html = f'<meta name="description" content="{"x" * 100}">'
    assert check_meta_description(soup(html))[0] is True


def test_meta_description_missing():
    assert check_meta_description(soup("<html></html>"))[0] is False


def test_meta_description_too_short():
    assert check_meta_description(soup('<meta name="description" content="short">'))[0] is False


def test_h1_exactly_one():
    assert check_h1(soup("<h1>Hello</h1>"))[0] is True


def test_h1_missing():
    assert check_h1(soup("<p>No heading</p>"))[0] is False


def test_h1_multiple():
    assert check_h1(soup("<h1>A</h1><h1>B</h1>"))[0] is False


def test_canonical_present():
    assert check_canonical(soup('<link rel="canonical" href="https://example.com/">'))[0] is True


def test_canonical_missing():
    assert check_canonical(soup("<html></html>"))[0] is False


def test_image_alt_all_present():
    assert check_image_alt(soup('<img src="a.png" alt="A picture">'))[0] is True


def test_image_alt_missing():
    assert check_image_alt(soup('<img src="a.png"><img src="b.png" alt="ok">'))[0] is False


def test_image_alt_no_images():
    assert check_image_alt(soup("<p>No images</p>"))[0] is True


def test_good_page_scores_100():
    assert score_page(GOOD_PAGE)["score"] == 100


def test_bad_page_scores_0():
    assert score_page(BAD_PAGE)["score"] == 0


def test_site_score_explained():
    pages = [{"score": 100}, {"score": 0}]
    report = build_report(pages, {"sitemap.xml": True, "robots.txt": True})
    assert report["site_score"] == 60
    assert "80%" in report["explanation"]


def test_site_score_without_site_files():
    pages = [{"score": 100}, {"score": 0}]
    report = build_report(pages, {"sitemap.xml": False, "robots.txt": False})
    assert report["site_score"] == 40


def test_site_score_with_no_pages():
    report = build_report([], {"sitemap.xml": True, "robots.txt": True})
    assert report["site_score"] == 0