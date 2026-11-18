## Week 1: Uptime and SSL checks

Setup:
```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run:
```
python -m monitor.cli https://example.com https://python.org
```

## Week 2: Storage, scheduler and tests

Run checks every 5 minutes and store results in SQLite (`monitor.db`):
```
python -m monitor.scheduler https://example.com https://python.org --minutes 5
```

Run the tests:
```
python -m pytest -v
```

## Week 3: Broken link crawler

Start the test site (planted broken links) in one terminal:
```
python -m http.server 8000 --directory tests/testsite
```

Crawl it from another terminal:
```
python -m monitor.crawler http://localhost:8000/index.html --delay 0.2
```

Options: `--depth` (default 2), `--max-pages` (default 20), `--delay` seconds between requests (default 1.0).
The crawler obeys robots.txt, sends a clear User-Agent, and uses HEAD first, then GET if HEAD is not supported.
Only crawl sites you own or have permission to test.