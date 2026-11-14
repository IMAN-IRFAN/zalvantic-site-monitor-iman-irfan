from monitor.storage import Result, get_session_factory, save_result


def test_save_result():
    sf = get_session_factory("sqlite:///:memory:")
    save_result(sf, "https://example.com", "uptime", "up", 123)
    save_result(sf, "https://example.com", "ssl", "ok", 50)
    with sf() as session:
        rows = session.query(Result).all()
    assert len(rows) == 2
    assert rows[0].check_type == "uptime"
    assert rows[1].value == 50