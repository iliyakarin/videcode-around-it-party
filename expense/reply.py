from expense.model import NormalizedLine

ASK_PHOTO = "Send a photo of the bill."
NOTHING = "Nothing was written. That photo did not produce any bill lines."
INFERENCE_FAILED = "Inference failed. Nothing was written."
SHEETS_UNAVAILABLE = "The spreadsheet is unavailable. Nothing was written."


def _one(line: NormalizedLine) -> str:
    amount = "" if line.amount is None else f"{line.amount:.2f}"
    text = f"sheet: {line.category}; amount: {amount}; description: {line.description}"
    if line.amount_missing:
        text += " amount was missing"
    if line.date_from_message:
        text += f" bill had no date; used {line.date}"
    if line.outside_october:
        text += f" date {line.date} is outside October 2026"
    return text


def format_reply(saved: list[NormalizedLine], unsaved: list[tuple[NormalizedLine, str]]) -> str:
    parts = [_one(line) for line in saved]
    parts.extend(f"not saved {line.category} {line.description}: {error}" for line, error in unsaved)
    return "\n".join(parts)
