import json
import re

from expense.model import LineIn

class InferenceError(Exception):
    pass

def build_prompt(categories: list[str]) -> str:
    names = ", ".join(categories)
    return (
        "Read this bill photo. Return a JSON array of line items. "
        "Each object has date (YYYY-MM-DD or null), description, amount, "
        f"paid_with, and category. category must be one of: {names}. "
        "Use one object per line item. "
        "Skip subtotal, total, and change lines. "
        "List tax, tip, and fees as their own items. "
        "Copy the amount as printed, including any currency symbol. "
        "Use null when paid_with or the amount is not shown. "
        "Do not wrap the array in prose."
    )

def parse_model_json(text: str) -> list[LineIn]:
    body = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", body, re.S)
    if fenced:
        body = fenced.group(1).strip()
    data = json.loads(body)
    if not isinstance(data, list):
        raise ValueError("not an array")
    lines = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("array item is not an object")
        lines.append(LineIn(
            date=item.get("date"),
            description=str(item.get("description") or ""),
            amount=item.get("amount"),
            paid_with=item.get("paid_with"),
            category=item.get("category"),
        ))
    return lines

def extract_lines(complete, *, image_path: str, categories: list[str]) -> list[LineIn]:
    prompt = build_prompt(categories)
    last = "unreadable"
    for _ in range(2):
        try:
            return parse_model_json(complete(prompt, image_path))
        except (ValueError, json.JSONDecodeError) as exc:
            last = str(exc)
    raise InferenceError(last)
