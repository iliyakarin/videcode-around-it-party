import re
from datetime import datetime

from expense.model import LineIn, NormalizedLine

HEADER = ["Date", "Description", "Amount", "Paid with", "Notes"]
OTHER = "Other"
SUMMARY = "Summary"
_CURRENCY = re.compile(r"[$€£]|USD|EUR|GBP")

def _amount(raw: object) -> tuple[float | None, str]:
    if raw is None:
        return None, ""
    text = str(raw).strip()
    if not text:
        return None, ""
    found = _CURRENCY.search(text)
    currency = found.group(0) if found else ""
    cleaned = re.sub(r"[^0-9.,]", "", text)
    if cleaned.count(",") == 1 and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    if cleaned in {"", "."} or cleaned.count(".") > 1:
        return None, currency
    try:
        return float(cleaned), currency
    except ValueError:
        return None, currency

def _date(raw: str | None, message_date: str) -> tuple[str, bool, bool]:
    if raw:
        try:
            parsed = datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            parsed = None
        if parsed is not None:
            outside = not (parsed.year == 2026 and parsed.month == 10)
            return parsed.isoformat(), False, outside
    return message_date, True, False

def normalize(line: LineIn, *, categories: list[str], message_date: str) -> NormalizedLine:
    amount, currency = _amount(line.amount)
    allowed = set(categories)
    category = line.category if line.category in allowed else OTHER
    if amount is None:
        category = OTHER
    when, from_message, outside = _date(line.date, message_date)
    return NormalizedLine(
        date=when,
        description=line.description,
        amount=amount,
        paid_with=line.paid_with or "",
        category=category,
        notes=currency,
        date_from_message=from_message,
        outside_october=outside,
        amount_missing=amount is None,
    )
