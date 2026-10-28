import pytest
from expense.extract import InferenceError, build_prompt, extract_lines, parse_model_json

def test_parse_array_and_fenced_json():
    raw = '[{"date":"2026-10-03","description":"Milk","amount":"4.50","paid_with":"card","category":"Groceries"}]'
    lines = parse_model_json(raw)
    assert lines[0].description == "Milk"
    fenced = "```json\n" + raw + "\n```"
    assert parse_model_json(fenced)[0].category == "Groceries"

def test_prompt_lists_categories():
    text = build_prompt(["Groceries", "Restorants and fun"])
    assert "Groceries" in text and "Restorants and fun" in text
    assert "JSON array" in text

def test_retries_once_then_raises():
    calls = {"n": 0}
    def complete(prompt, image_path):
        calls["n"] += 1
        return "not json"
    with pytest.raises(InferenceError):
        extract_lines(complete, image_path="bill.jpg", categories=["Groceries"])
    assert calls["n"] == 2
