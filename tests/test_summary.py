from expense.summary import summary_rows


def test_summary_quotes_names_and_sums_column_c():
    rows = summary_rows(["Groceries", "Restorants and fun"])
    assert rows == [
        ["Groceries", "=SUM('Groceries'!C:C)"],
        ["Restorants and fun", "=SUM('Restorants and fun'!C:C)"],
        ["Total", "=SUM(B2:B3)"],
    ]


def test_summary_escapes_single_quotes():
    rows = summary_rows(["Bob's cafe"])
    assert rows[0][1] == "=SUM('Bob''s cafe'!C:C)"
    assert rows[1] == ["Total", "=SUM(B2:B2)"]
