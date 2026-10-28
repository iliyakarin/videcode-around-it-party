from expense.model import NormalizedLine
from expense.normalize import HEADER
from expense.sheets import _row, a1, append_lines, bootstrap
from tests.fakes import FakeSheets


def _line(category="Groceries", amount=4.5, description="Milk"):
    return NormalizedLine(
        "2026-10-03", description, amount, "card", category, "$",
        False, False, amount is None,
    )


def test_bootstrap_creates_other_header_and_summary():
    fake = FakeSheets(tabs=["Summary", "Groceries"], headers={})
    categories = bootstrap(fake)
    assert categories == ["Groceries", "Other"]
    assert "Other" in fake.tabs
    assert fake.headers["Groceries"] == HEADER
    assert fake.headers["Other"] == HEADER
    assert fake.summary[0] == ["Groceries", "=SUM('Groceries'!C:C)"]
    assert fake.summary[-1][0] == "Total"


def test_bootstrap_leaves_non_empty_header_alone():
    fake = FakeSheets(tabs=["Summary", "Groceries"], headers={"Groceries": ["old"]})
    bootstrap(fake)
    assert fake.headers["Groceries"] == ["old"]
    assert fake.headers["Other"] == HEADER


def test_row_prefixes_formula_like_text_cells():
    fake = FakeSheets(tabs=["Summary", "Groceries"], headers={})
    line = NormalizedLine(
        "2026-10-03", "=HYPERLINK(1)", -4.5, "+card", "Groceries", "@x",
        False, False, False,
    )
    append_lines(fake, [line])
    assert fake.rows["Groceries"] == [["2026-10-03", "'=HYPERLINK(1)", "-4.50", "'+card", "'@x"]]
    plain = NormalizedLine("2026-10-03", "-milk", 1, "card", "Groceries", "$", False, False, False)
    assert _row(plain)[1] == "'-milk"
    assert _row(_line())[1] == "Milk"


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
