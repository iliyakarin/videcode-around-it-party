from expense.model import NormalizedLine
from expense.reply import ASK_PHOTO, INFERENCE_FAILED, NOTHING, SHEETS_UNAVAILABLE, format_reply


def _line(**kwargs):
    base = dict(
        date="2026-10-03", description="Milk", amount=4.5, paid_with="card",
        category="Groceries", notes="$", date_from_message=False,
        outside_october=False, amount_missing=False,
    )
    base.update(kwargs)
    return NormalizedLine(**base)


def test_fixed_replies():
    assert ASK_PHOTO == "Send a photo of the bill."
    assert NOTHING.startswith("Nothing was written.")
    assert INFERENCE_FAILED == "Inference failed. Nothing was written."
    assert SHEETS_UNAVAILABLE == "The spreadsheet is unavailable. Nothing was written."


def test_saved_and_unsaved_lines():
    saved = _line(amount=None, amount_missing=True, category="Other", description="Mystery")
    outside = _line(date="2026-09-30", outside_october=True, category="Transport", description="Ticket")
    undated = _line(date_from_message=True, date="2026-10-28", description="Snack")
    text = format_reply([saved, outside, undated], [(saved, "503")])
    assert "sheet: Other; amount: ; description: Mystery" in text
    assert "amount was missing" in text
    assert "date 2026-09-30 is outside October 2026" in text
    assert "bill had no date; used 2026-10-28" in text
    assert "not saved Other Mystery: 503" in text
    linked = format_reply([saved], [], {"Other": "https://sheet.example/Other#gid=1"})
    assert linked.endswith("https://sheet.example/Other#gid=1")
