import unicodedata
from datetime import datetime

from expense.model import LineIn, NormalizedLine

HEADER = ["Date", "Description", "Amount", "Paid with", "Notes"]
OTHER = "Other"
SUMMARY = "Summary"


def _is_ascii_digit(ch: str) -> bool:
    return len(ch) == 1 and "0" <= ch <= "9"


def _is_ascii_digits(s: str) -> bool:
    return bool(s) and all(_is_ascii_digit(c) for c in s)


def _valid_thousands(int_part: str, thou_sep: str) -> bool:
    if thou_sep not in int_part:
        return _is_ascii_digits(int_part)
    groups = int_part.split(thou_sep)
    if any(not _is_ascii_digits(g) for g in groups):
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
    if not s or not all(_is_ascii_digit(c) or c in ".," for c in s):
        return None
    dot_count = s.count(".")
    comma_count = s.count(",")

    if dot_count == 0 and comma_count == 0:
        return float(s)

    if dot_count == 0 and comma_count == 1:
        left, right = s.split(",")
        if not _is_ascii_digits(left) or not _is_ascii_digits(right) or len(right) not in (1, 2):
            return None
        return float(f"{left}.{right}")

    if comma_count == 0 and dot_count == 1:
        left, right = s.split(".")
        if not _is_ascii_digits(left) or not _is_ascii_digits(right) or len(right) not in (1, 2):
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
        if not _is_ascii_digits(frac_part) or len(frac_part) not in (1, 2):
            return None
        if thou_sep in int_part and not _valid_thousands(int_part, thou_sep):
            return None
        int_part = int_part.replace(thou_sep, "")
        if not _is_ascii_digits(int_part):
            return None
        return float(f"{int_part}.{frac_part}")

    return None


def _is_sc_char(ch: str) -> bool:
    return unicodedata.category(ch) == "Sc"


def _valid_currency_token(token: str) -> bool:
    if len(token) == 3 and token.isascii() and token.isalpha():
        return True
    return bool(token) and all(_is_sc_char(c) for c in token)


def _amount(raw: object) -> tuple[float | None, str]:
    if raw is None:
        return None, ""
    text = str(raw).strip()
    if not text:
        return None, ""

    def fail() -> tuple[None, str]:
        return None, ""

    i = 0
    n = len(text)
    sign = 1
    pre_currencies: list[str] = []
    post_currencies: list[str] = []
    number: str | None = None

    if i < n and text[i] == "-":
        sign = -1
        i += 1

    while i < n:
        if text[i].isspace():
            i += 1
            continue
        if text[i] == "-":
            if number is not None:
                return fail()
            if pre_currencies:
                if not all(all(_is_sc_char(c) for c in tok) for tok in pre_currencies):
                    return fail()
                sign = -1
                i += 1
                continue
            if sign == -1:
                return fail()
            sign = -1
            i += 1
            continue
        if _is_ascii_digit(text[i]) or text[i] in ".,":
            if number is not None:
                return fail()
            j = i
            while j < n and (_is_ascii_digit(text[j]) or text[j] in ".,"):
                j += 1
            number = text[i:j]
            i = j
            continue
        j = i
        while (
            j < n
            and not text[j].isspace()
            and not _is_ascii_digit(text[j])
            and text[j] not in ".,"
            and text[j] != "-"
        ):
            j += 1
        token = text[i:j]
        if not token:
            i += 1
            continue
        if not _valid_currency_token(token):
            return fail()
        if number is None:
            pre_currencies.append(token)
        else:
            post_currencies.append(token)
        i = j

    if number is None:
        return fail()

    num = _parse_number(number)
    if num is None:
        return fail()

    notes = " ".join(pre_currencies + post_currencies)
    return sign * num, notes


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
