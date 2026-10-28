import json

import pytest

import hermes_plugin
from expense.reply import ASK_PHOTO, INFERENCE_FAILED, SHEETS_UNAVAILABLE
from hermes_plugin import tools


@pytest.fixture(autouse=True)
def fresh_state(monkeypatch):
    monkeypatch.setattr(tools, "_ready", False)
    monkeypatch.setattr(tools, "_client", None)


def _reply(args):
    return json.loads(tools.record_expense(args))["reply"]


def test_register_only_registers_tool(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("register must not bootstrap")

    monkeypatch.setattr(tools, "GoogleSheets", boom)
    monkeypatch.setattr(tools, "bootstrap", boom)
    calls = []

    class Ctx:
        def register_tool(self, **kwargs):
            calls.append(kwargs)

    hermes_plugin.register(Ctx())
    assert [c["name"] for c in calls] == ["record_expense"]
    assert tools._ready is False


def test_ask_photo_when_image_path_missing():
    assert _reply({}) == ASK_PHOTO


def test_bootstrap_failure_replies_unavailable_and_retries(monkeypatch, caplog):
    monkeypatch.setenv("SPREADSHEET_ID", "sheet")
    attempts = []

    def flaky(_sheet_id):
        attempts.append(1)
        if len(attempts) == 1:
            raise RuntimeError("no creds")
        return object()

    monkeypatch.setattr(tools, "GoogleSheets", flaky)
    monkeypatch.setattr(tools, "bootstrap", lambda client: ["Other"])
    monkeypatch.setattr(tools, "handle_message", lambda **kw: "saved")

    assert _reply({"image_path": "/tmp/bill.jpg"}) == SHEETS_UNAVAILABLE
    assert "expense bootstrap failed" in caplog.text
    assert tools._ready is False
    assert _reply({"image_path": "/tmp/bill.jpg"}) == "saved"
    assert tools._ready is True
    assert len(attempts) == 2


def test_bootstraps_once_after_success(monkeypatch):
    monkeypatch.setenv("SPREADSHEET_ID", "sheet")
    built = []
    monkeypatch.setattr(tools, "GoogleSheets", lambda _id: built.append(1) or object())
    monkeypatch.setattr(tools, "bootstrap", lambda client: ["Other"])
    monkeypatch.setattr(tools, "handle_message", lambda **kw: "ok")
    _reply({"image_path": "a.jpg"})
    _reply({"image_path": "b.jpg"})
    assert len(built) == 1


def test_inference_failed_when_handle_raises(monkeypatch, caplog):
    monkeypatch.setattr(tools, "_ready", True)
    monkeypatch.setattr(tools, "_client", object())

    def boom(**kwargs):
        raise FileNotFoundError("no model")

    monkeypatch.setattr(tools, "handle_message", boom)
    assert _reply({"image_path": "/tmp/bill.jpg"}) == INFERENCE_FAILED
    assert "record_expense failed" in caplog.text


def test_handle_message_runs_under_lock(monkeypatch):
    monkeypatch.setattr(tools, "_ready", True)
    monkeypatch.setattr(tools, "_client", object())
    held = []

    def check(**kwargs):
        held.append(tools._lock.locked())
        return "ok"

    monkeypatch.setattr(tools, "handle_message", check)
    _reply({"image_path": "a.jpg"})
    assert held == [True]
