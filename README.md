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