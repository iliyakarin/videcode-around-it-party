import json
import logging
import os
import threading
from datetime import date

from expense.handle import handle_message
from expense.llama import complete
from expense.reply import ASK_PHOTO, INFERENCE_FAILED, SHEETS_UNAVAILABLE
from expense.sheets import GoogleSheets, bootstrap

_lock = threading.Lock()
_ready = False
_client = None


def _ensure_ready() -> bool:
    """Bootstrap on first use; a failure is retried on the next call. Hold _lock."""
    global _ready, _client
    if _ready:
        return True
    try:
        client = GoogleSheets(os.environ["SPREADSHEET_ID"])
        bootstrap(client)
    except Exception:
        logging.exception("expense bootstrap failed")
        return False
    _client = client
    _ready = True
    return True


def record_expense(args: dict, **kwargs) -> str:
    if not args.get("image_path"):
        return json.dumps({"reply": ASK_PHOTO})
    with _lock:
        if not _ensure_ready():
            return json.dumps({"reply": SHEETS_UNAVAILABLE})
        try:
            text = handle_message(
                image_paths=[args["image_path"]],
                message_date=str(args.get("message_date") or date.today().isoformat()),
                sheets_ready=_ready,
                client=_client,
                complete=complete,
            )
        except Exception:
            logging.exception("record_expense failed")
            return json.dumps({"reply": INFERENCE_FAILED})
    return json.dumps({"reply": text})
