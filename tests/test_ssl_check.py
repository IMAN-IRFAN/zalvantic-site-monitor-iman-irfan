from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from monitor.ssl_check import check_ssl


def fake_cert(days_from_now):
    expires = datetime.now(timezone.utc) + timedelta(days=days_from_now, hours=1)
    return {"notAfter": expires.strftime("%b %d %H:%M:%S %Y GMT")}


@patch("monitor.ssl_check.ssl.create_default_context")
@patch("monitor.ssl_check.socket.create_connection")
def test_days_left(mock_conn, mock_ctx):
    tls = MagicMock()
    tls.getpeercert.return_value = fake_cert(30)
    mock_ctx.return_value.wrap_socket.return_value.__enter__.return_value = tls
    result = check_ssl("https://example.com")
    assert result["days_left"] == 30
    assert result["error"] is None


@patch("monitor.ssl_check.socket.create_connection")
def test_connection_error(mock_conn):
    mock_conn.side_effect = OSError("connection refused")
    result = check_ssl("https://example.com")
    assert result["days_left"] is None
    assert "connection refused" in result["error"]