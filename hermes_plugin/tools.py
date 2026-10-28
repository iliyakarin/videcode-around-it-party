import json
import os
from datetime import date

from expense.handle import handle_message
from expense.llama import complete
from expense.reply import ASK_PHOTO, INFERENCE_FAILED
from expense.sheets import GoogleSheets, bootstrap

_ready = False
_client = None


def load() -> None:
    global _ready, _client
    try:
        _client = GoogleSheets(os.environ["SPREADSHEET_ID"])
        bootstrap(_client)
        _ready = True
    except Exception:
        _ready = False


def record_expense(args: dict, **kwargs) -> str:
    if not args.get("image_path"):
        return json.dumps({"reply": ASK_PHOTO})
    try:
        today = date.today().isoformat()
        text = handle_message(
            image_paths=[args["image_path"]],
            message_date=str(args.get("message_date") or today),
            sheets_ready=_ready,
            client=_client,
            complete=complete,
        )
        return json.dumps({"reply": text})
    except Exception:
        return json.dumps({"reply": INFERENCE_FAILED})
