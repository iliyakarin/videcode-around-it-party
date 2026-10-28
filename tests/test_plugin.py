import json

from expense.reply import ASK_PHOTO, INFERENCE_FAILED, SHEETS_UNAVAILABLE
from hermes_plugin import tools
from tests.fakes import FakeSheets


def test_sheets_unavailable_when_not_ready():
    tools._ready = False
    tools._client = None
    result = tools.record_expense({"image_path": "/tmp/bill.jpg"})
    payload = json.loads(result)
    assert payload["reply"] == SHEETS_UNAVAILABLE


def test_ask_photo_when_image_path_missing():
    result = tools.record_expense({})
    payload = json.loads(result)
    assert payload["reply"] == ASK_PHOTO


def test_inference_failed_when_complete_raises(monkeypatch):
    tools._ready = True
    tools._client = FakeSheets(
        ["Food"],
        {"Food": ["Date", "Description", "Amount", "Paid with"]},
    )

    def boom(*args, **kwargs):
        raise FileNotFoundError("no model")

    monkeypatch.setattr("expense.llama.complete", boom)
    monkeypatch.setattr(tools, "complete", boom)
    result = tools.record_expense({"image_path": "/tmp/bill.jpg"})
    payload = json.loads(result)
    assert payload["reply"] == INFERENCE_FAILED
