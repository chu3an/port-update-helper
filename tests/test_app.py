import json
from types import SimpleNamespace
from unittest.mock import Mock

import app as helper


class FakeQB:
    def __init__(self, ports, *, login_result=True, set_result=True):
        self.ports = iter(ports)
        self.login_result = login_result
        self.set_result = set_result
        self.login_calls = 0
        self.logout_calls = 0
        self.set_calls = []

    def login(self):
        self.login_calls += 1
        return self.login_result

    def logout(self):
        self.logout_calls += 1
        return True

    def get_port(self):
        return next(self.ports)

    def set_port(self, port):
        self.set_calls.append(port)
        return self.set_result


class FakeGT:
    def __init__(self, port_data):
        self.port_data = port_data

    def get_forwarded_port(self):
        return self.port_data


def test_change_port_updates_and_verifies(monkeypatch):
    qb = FakeQB([6881, 53503])
    monkeypatch.setattr(helper, "qb", qb)
    monkeypatch.setattr(helper, "gt", FakeGT({"port": 53503}))

    assert helper.change_port() is True
    assert qb.set_calls == [53503]
    assert qb.logout_calls == 1


def test_change_port_skips_unchanged_port(monkeypatch):
    qb = FakeQB([53503])
    monkeypatch.setattr(helper, "qb", qb)
    monkeypatch.setattr(helper, "gt", FakeGT({"port": 53503}))

    assert helper.change_port() is True
    assert qb.set_calls == []
    assert qb.logout_calls == 1


def test_change_port_rejects_zero_before_qbittorrent_login(monkeypatch):
    qb = FakeQB([])
    monkeypatch.setattr(helper, "qb", qb)
    monkeypatch.setattr(helper, "gt", FakeGT({"port": 0}))

    assert helper.change_port() is False
    assert qb.login_calls == 0


def test_change_port_reports_failed_verification(monkeypatch):
    qb = FakeQB([6881, 6881])
    monkeypatch.setattr(helper, "qb", qb)
    monkeypatch.setattr(helper, "gt", FakeGT({"port": 53503}))

    assert helper.change_port() is False
    assert qb.set_calls == [53503]
    assert qb.logout_calls == 1


def test_qbittorrent_api_uses_matching_origin_and_correct_logout():
    api = helper.QBAPI("http://gluetun:8080/", "user", "password", 10)
    response = SimpleNamespace(status_code=200, text="Ok.")
    api._request = Mock(return_value=response)

    assert api.session.headers["Origin"] == "http://gluetun:8080"
    assert api.session.headers["Referer"] == "http://gluetun:8080/"
    assert api.login() is True
    api._request.assert_called_with(
        "POST",
        "/api/v2/auth/login",
        data={"username": "user", "password": "password"},
    )

    assert api.logout() is True
    api._request.assert_called_with("POST", "/api/v2/auth/logout")


def test_qbittorrent_login_accepts_no_content_success():
    api = helper.QBAPI("http://gluetun:8080", "user", "password", 10)
    api._request = Mock(return_value=SimpleNamespace(status_code=204, text=""))

    assert api.login() is True


def test_qbittorrent_login_rejects_failed_responses():
    api = helper.QBAPI("http://gluetun:8080", "user", "password", 10)
    for status_code, body in ((200, "Fails."), (401, "")):
        api._request = Mock(
            return_value=SimpleNamespace(status_code=status_code, text=body)
        )
        assert api.login() is False


def test_qbittorrent_logout_accepts_no_content_success():
    api = helper.QBAPI("http://gluetun:8080", "user", "password", 10)
    api._request = Mock(return_value=SimpleNamespace(status_code=204, text=""))

    assert api.logout() is True


def test_qbittorrent_set_port_uses_json_payload():
    api = helper.QBAPI("http://gluetun:8080", "user", "password", 10)
    api._request = Mock(return_value=SimpleNamespace(status_code=200, text=""))

    assert api.set_port(53503) is True
    payload = api._request.call_args.kwargs["data"]["json"]
    assert json.loads(payload) == {"listen_port": 53503}


def test_qbittorrent_set_port_accepts_no_content_success():
    api = helper.QBAPI("http://gluetun:8080", "user", "password", 10)
    api._request = Mock(return_value=SimpleNamespace(status_code=204, text=""))

    assert api.set_port(53503) is True
