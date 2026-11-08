import time
import httpx


def check_uptime(url: str, timeout: float = 10.0) -> dict:
    start = time.perf_counter()
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=True)
        latency_ms = round((time.perf_counter() - start) * 1000)
        return {
            "url": url,
            "up": response.status_code < 400,
            "status": response.status_code,
            "latency_ms": latency_ms,
            "error": None,
        }
    except httpx.HTTPError as exc:
        return {
            "url": url,
            "up": False,
            "status": None,
            "latency_ms": None,
            "error": str(exc),
        }