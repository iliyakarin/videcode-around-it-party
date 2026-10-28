from expense.model import NormalizedLine
from expense.normalize import HEADER
from expense.sheets import a1, append_lines, bootstrap
from tests.fakes import FakeSheets


def _line(category="Groceries", amount=4.5, description="Milk"):
    return NormalizedLine(
        "2026-10-03", description, amount, "card", category, "$",
        False, False, amount is None,
    )


def test_bootstrap_creates_other_header_and_summary():
    fake = FakeSheets(tabs=["Summary", "Groceries"], headers={"Groceries": ["old"]})
    categories = bootstrap(fake)
    assert categories == ["Groceries", "Other"]
    assert "Other" in fake.tabs
    assert fake.headers["Groceries"] == HEADER
    assert fake.headers["Other"] == HEADER
    assert fake.summary[0] == ["Groceries", "=SUM('Groceries'!C:C)"]
    assert fake.summary[-1][0] == "Total"


def test_append_stops_after_first_sheets_error():
    fake = FakeSheets(tabs=["Summary", "Groceries", "Other"], headers={})
    fake.fail_on = "Other"
    first = _line()
    second = _line(category="Other", amount=None, description="Mystery")
    third = _line(description="Bread")
    result = append_lines(fake, [first, second, third])
    assert result.saved == [first]
    assert result.unsaved == [(second, "down"), (third, "not attempted")]
    assert fake.rows["Groceries"] == [["2026-10-03", "Milk", "4.50", "card", "$"]]
    assert "Other" not in fake.rows


def test_a1_escapes_quotes():
    assert a1("Bob's cafe", "A1:E1") == "'Bob''s cafe'!A1:E1"
    assert a1("Restorants and fun", "A:E") == "'Restorants and fun'!A:E"
