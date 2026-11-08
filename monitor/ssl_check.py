import certifi
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse


def check_ssl(url: str, timeout: float = 10.0) -> dict:
    host = urlparse(url).hostname or url
    context = ssl.create_default_context(cafile=certifi.where())
    try:
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
        expires = datetime.fromtimestamp(
            ssl.cert_time_to_seconds(cert["notAfter"]), tz=timezone.utc
        )
        days_left = (expires - datetime.now(timezone.utc)).days
        return {"host": host, "days_left": days_left, "expires": expires.date().isoformat(), "error": None}
    except (OSError, ssl.SSLError) as exc:
        return {"host": host, "days_left": None, "expires": None, "error": str(exc)}