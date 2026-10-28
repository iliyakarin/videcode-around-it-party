from expense.extract import InferenceError
from expense.handle import handle_message
from expense.reply import ASK_PHOTO, INFERENCE_FAILED, NOTHING, SHEETS_UNAVAILABLE
from tests.fakes import FakeSheets


def _send(fake, raw, path="bill.jpg", ready=True):
    return handle_message(
        image_paths=[path], message_date="2026-10-28", sheets_ready=ready,
        client=fake, complete=lambda prompt, image_path: raw,
    )


def test_refuses_without_photo_or_sheets():
    fake = FakeSheets(["Summary", "Groceries", "Other"], {})
    assert handle_message(
        image_paths=[], message_date="2026-10-28", sheets_ready=True,
        client=fake, complete=lambda p, i: "[]",
    ) == ASK_PHOTO
    assert handle_message(
        image_paths=["a.jpg"], message_date="2026-10-28", sheets_ready=False,
        client=fake, complete=lambda p, i: "[]",
    ) == SHEETS_UNAVAILABLE


def test_writes_a_known_category_and_reports_empty_photo():
    fake = FakeSheets(["Summary", "Groceries", "Other"], {})
    raw = '[{"date":"2026-10-03","description":"Milk","amount":"4.50","paid_with":"card","category":"Groceries"}]'
    text = _send(fake, raw)
    assert "sheet: Groceries; amount: 4.50; description: Milk" in text
    assert fake.rows["Groceries"][0][2] == "4.50"
    assert _send(fake, "[]", path="blank.jpg") == NOTHING


def test_split_missing_date_and_blank_paid_with():
    fake = FakeSheets(["Summary", "Groceries", "Transport", "Other"], {})
    raw = (
        '[{"date":"2026-10-03","description":"Milk","amount":"4.50","paid_with":"card","category":"Groceries"},'
        '{"date":null,"description":"Bus","amount":"2","paid_with":null,"category":"Transport"}]'
    )
    text = _send(fake, raw)
    assert "sheet: Groceries" in text
    assert "sheet: Transport" in text
    assert "bill had no date; used 2026-10-28" in text
    assert fake.rows["Transport"][0] == ["2026-10-28", "Bus", "2.00", "", ""]


def test_unreadable_amount_and_unknown_category_go_to_other():
    fake = FakeSheets(["Summary", "Groceries", "Other"], {})
    raw = (
        '[{"date":"2026-10-03","description":"Mystery","amount":"n/a","paid_with":null,"category":"Groceries"},'
        '{"date":"2026-09-30","description":"Ticket","amount":"12","paid_with":null,"category":"Dining"}]'
    )
    text = _send(fake, raw)
    assert "amount was missing" in text
    assert "date 2026-09-30 is outside October 2026" in text
    assert fake.rows["Other"][0][1:] == ["Mystery", "", "", ""]
    assert fake.rows["Other"][1][0:2] == ["2026-09-30", "Ticket"]


def test_new_tab_is_used_on_the_next_message():
    fake = FakeSheets(["Summary", "Groceries", "Other"], {})
    raw = '[{"date":"2026-10-03","description":"Lamp","amount":"10","paid_with":null,"category":"Home"}]'
    assert "sheet: Other" in _send(fake, raw, path="first.jpg")
    fake.add_tab("Home")
    assert "sheet: Home" in _send(fake, raw, path="second.jpg")
    assert fake.rows["Home"][0][1] == "Lamp"


def test_inference_failure_keeps_earlier_photo():
    fake = FakeSheets(["Summary", "Groceries", "Other"], {})
    raw = '[{"date":"2026-10-03","description":"Milk","amount":"4.50","paid_with":null,"category":"Groceries"}]'

    def complete(prompt, image_path):
        if image_path == "bad.jpg":
            raise InferenceError("down")
        return raw

    text = handle_message(
        image_paths=["ok.jpg", "bad.jpg"], message_date="2026-10-28",
        sheets_ready=True, client=fake, complete=complete,
    )
    assert "sheet: Groceries" in text
    assert INFERENCE_FAILED in text
    assert len(fake.rows["Groceries"]) == 1
