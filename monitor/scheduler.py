import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from monitor.ssl_check import check_ssl
from monitor.storage import get_session_factory, save_result
from monitor.uptime import check_uptime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger("monitor")


def run_checks(session_factory, urls):
    for url in urls:
        up = check_uptime(url)
        save_result(session_factory, url, "uptime", "up" if up["up"] else "down", up["latency_ms"])

        ssl_result = check_ssl(url)
        save_result(
            session_factory,
            url,
            "ssl",
            "ok" if ssl_result["error"] is None else "error",
            ssl_result["days_left"],
        )
        log.info("checked %s", url)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run checks on a schedule and store results.")
    parser.add_argument("urls", nargs="+", help="one or more site URLs")
    parser.add_argument("--minutes", type=float, default=5, help="minutes between runs")
    args = parser.parse_args()

    session_factory = get_session_factory()
    run_checks(session_factory, args.urls)  # run once right away

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_checks, "interval", minutes=args.minutes, args=[session_factory, args.urls]
    )
    log.info("scheduler started, running every %s minutes (Ctrl+C to stop)", args.minutes)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("scheduler stopped")


if __name__ == "__main__":
    main()