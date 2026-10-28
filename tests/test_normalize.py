from expense.model import LineIn
from expense.normalize import HEADER, normalize

CATS = ["Groceries", "Home", "Transport", "Restorants and fun", "Other"]

def test_header_and_known_category():
    assert HEADER == ["Date", "Description", "Amount", "Paid with", "Notes"]
    line = normalize(
        LineIn("2026-10-03", "Milk", "$4.50", "card", "Groceries"),
        categories=CATS,
        message_date="2026-10-28",
    )
    assert line.category == "Groceries"
    assert line.amount == 4.5
    assert line.notes == "$"
    assert line.paid_with == "card"
    assert line.outside_october is False
    assert line.date_from_message is False

def test_unknown_category_and_missing_amount_go_to_other():
    unknown = normalize(
        LineIn("2026-10-03", "Widget", "2", None, "Dining"),
        categories=CATS,
        message_date="2026-10-28",
    )
    assert unknown.category == "Other"
    missing = normalize(
        LineIn("2026-10-03", "Mystery", "n/a", "", "Groceries"),
        categories=CATS,
        message_date="2026-10-28",
    )
    assert missing.category == "Other"
    assert missing.amount is None
    assert missing.amount_missing is True
    assert missing.description == "Mystery"

def test_missing_date_uses_message_day_and_outside_october_is_kept():
    missing = normalize(
        LineIn(None, "Snack", "3", None, "Home"),
        categories=CATS,
        message_date="2026-10-28",
    )
    assert missing.date == "2026-10-28"
    assert missing.date_from_message is True
    outside = normalize(
        LineIn("2026-09-30", "Ticket", "12.00", None, "Transport"),
        categories=CATS,
        message_date="2026-10-28",
    )
    assert outside.date == "2026-09-30"
    assert outside.outside_october is True
    assert outside.category == "Transport"
