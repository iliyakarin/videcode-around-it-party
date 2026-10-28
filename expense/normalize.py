from datetime import datetime

from expense.model import LineIn, NormalizedLine

HEADER = ["Date", "Description", "Amount", "Paid with", "Notes"]
OTHER = "Other"
SUMMARY = "Summary"


def _valid_thousands(int_part: str, thou_sep: str) -> bool:
    if thou_sep not in int_part:
        return int_part.isdigit()
    groups = int_part.split(thou_sep)
    if any(not g.isdigit() for g in groups):
        return False
    if len(groups) == 1:
        return True
    for i, g in enumerate(groups):
        if i == 0:
            if not g or len(g) > 3:
                return False
        elif len(g) != 3:
            return False
    return True


def _parse_number(s: str) -> float | None:
    if not s or not all(c.isdigit() or c in ".," for c in s):
        return None
    dot_count = s.count(".")
    comma_count = s.count(",")

    if dot_count == 0 and comma_count == 0:
        return float(s)

    if dot_count == 0 and comma_count == 1:
        left, right = s.split(",")
        if not left.isdigit() or not right.isdigit() or len(right) not in (1, 2):
            return None
        return float(f"{left}.{right}")

    if comma_count == 0 and dot_count == 1:
        left, right = s.split(".")
        if not left.isdigit() or not right.isdigit() or len(right) not in (1, 2):
            return None
        return float(f"{left}.{right}")

    if dot_count >= 1 and comma_count >= 1:
        last_dot = s.rfind(".")
        last_comma = s.rfind(",")
        if last_dot > last_comma:
            dec_pos, thou_sep = last_dot, ","
        else:
            dec_pos, thou_sep = last_comma, "."
        int_part = s[:dec_pos]
        frac_part = s[dec_pos + 1 :]
        if not frac_part.isdigit() or len(frac_part) not in (1, 2):
            return None
        if thou_sep in int_part and not _valid_thousands(int_part, thou_sep):
            return None
        int_part = int_part.replace(thou_sep, "")
        if not int_part.isdigit():
            return None
        return float(f"{int_part}.{frac_part}")

    return None


def _amount(raw: object) -> tuple[float | None, str]:
    if raw is None:
        return None, ""
    text = str(raw).strip()
    if not text:
        return None, ""

    negative = False
    i = 0
    if text[0] == "-":
        negative = True
        i = 1

    currency_tokens: list[str] = []
    numeric_parts: list[str] = []

    while i < len(text):
        c = text[i]
        if c.isspace():
            i += 1
            continue
        if c == "-":
            return None, " ".join(currency_tokens)
        if c.isdigit() or c in ".,":
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] in ".,"):
                j += 1
            numeric_parts.append(text[i:j])
            i = j
            continue
        j = i
        while j < len(text) and not text[j].isspace() and not text[j].isdigit() and text[j] not in ".,":
            j += 1
        if j == i:
            i += 1
            continue
        currency_tokens.append(text[i:j])
        i = j

    notes = " ".join(currency_tokens)
    if len(numeric_parts) != 1:
        return None, notes

    num = _parse_number(numeric_parts[0])
    if num is None:
        return None, notes
    if negative:
        num = -num
    return num, notes


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
