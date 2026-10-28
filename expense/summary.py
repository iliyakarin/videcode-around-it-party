def _quote(name: str) -> str:
    return "'" + name.replace("'", "''") + "'"


def summary_rows(categories: list[str]) -> list[list[str]]:
    rows = [[name, f"=SUM({_quote(name)}!C:C)"] for name in categories]
    last = len(categories) + 1
    rows.append(["Total", f"=SUM(B2:B{last})"])
    return rows
