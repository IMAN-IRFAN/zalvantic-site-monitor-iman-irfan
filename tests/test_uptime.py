from unittest.mock import MagicMock, patch

import httpx

from monitor.uptime import check_uptime


@patch("monitor.uptime.httpx.get")
def test_site_up(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    result = check_uptime("https://example.com")
    assert result["up"] is True
    assert result["status"] == 200
    assert result["error"] is None
    assert result["latency_ms"] is not None


@patch("monitor.uptime.httpx.get")
def test_server_error_is_down(mock_get):
    mock_get.return_value = MagicMock(status_code=500)
    result = check_uptime("https://example.com")
    assert result["up"] is False
    assert result["status"] == 500


@patch("monitor.uptime.httpx.get")
def test_timeout_is_down(mock_get):
    mock_get.side_effect = httpx.ConnectTimeout("timed out")
    result = check_uptime("https://example.com")
    assert result["up"] is False
    assert result["status"] is None
    assert "timed out" in result["error"]