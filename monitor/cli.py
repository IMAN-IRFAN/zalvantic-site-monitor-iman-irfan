import argparse

from monitor.ssl_check import check_ssl
from monitor.uptime import check_uptime


def main() -> None:
    parser = argparse.ArgumentParser(description="Check uptime and SSL expiry for websites.")
    parser.add_argument("urls", nargs="+", help="one or more site URLs")
    args = parser.parse_args()

    print(f"{'SITE':<30}{'STATUS':<8}{'LATENCY':<10}{'SSL DAYS LEFT':<14}")
    for url in args.urls:
        up = check_uptime(url)
        ssl_result = check_ssl(url)
        status = up["status"] if up["status"] is not None else "DOWN"
        latency = f"{up['latency_ms']} ms" if up["latency_ms"] is not None else "-"
        days = ssl_result["days_left"] if ssl_result["days_left"] is not None else "-"
        print(f"{url:<30}{status!s:<8}{latency:<10}{days!s:<14}")


if __name__ == "__main__":
    main()