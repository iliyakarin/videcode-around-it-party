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


def _photo_paths(event) -> list[str]:
    urls = list(getattr(event, "media_urls", None) or [])
    types = list(getattr(event, "media_types", None) or [])
    paths = []
    for i, path in enumerate(urls):
        if not path:
            continue
        mime = types[i] if i < len(types) else ""
        if mime.startswith("image/") or str(path).lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            paths.append(str(path))
    return paths


def _allowed(user_id: str) -> bool:
    raw = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
    allowed = {part.strip() for part in raw.split(",") if part.strip()}
    return not allowed or user_id in allowed


async def on_photo(event=None, gateway=None, **kwargs):
    """Write each Telegram photo, reply with the sheet lines, and skip the model."""
    paths = _photo_paths(event) if event is not None else []
    source = getattr(event, "source", None)
    platform = getattr(getattr(source, "platform", None), "value", "")
    user_id = str(getattr(source, "user_id", "") or getattr(event, "user_id", "") or "")
    if not paths or platform != "telegram" or not _allowed(user_id):
        return None
    stamp = getattr(event, "timestamp", None)
    day = stamp.date().isoformat() if stamp is not None else date.today().isoformat()
    text = "\n".join(
        json.loads(record_expense({"image_path": path, "message_date": day}))["reply"]
        for path in paths
    )
    finder = getattr(gateway, "_delivery_adapter_for", None)
    adapter = finder(source) if callable(finder) else None
    if adapter is None:
        logging.error("expense photo written but no Telegram adapter")
        return {"action": "skip", "reason": "expense photo written"}
    send = adapter.send(str(source.chat_id), text, reply_to=getattr(event, "message_id", None))
    if hasattr(send, "__await__"):
        await send
    return {"action": "skip", "reason": "expense photo written"}


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
