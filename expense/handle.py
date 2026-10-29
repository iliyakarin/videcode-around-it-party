from expense.extract import InferenceError, extract_lines
from expense.normalize import normalize
from expense.reply import ASK_PHOTO, INFERENCE_FAILED, NOTHING, SHEETS_UNAVAILABLE, format_reply
from expense.sheets import append_lines, bootstrap


def _links(client, lines):
    url_for = getattr(client, "tab_url", None)
    if not callable(url_for):
        return None
    return {line.category: url_for(line.category) for line in lines}


def handle_message(*, image_paths, message_date, sheets_ready, client, complete) -> str:
    if not image_paths:
        return ASK_PHOTO
    if not sheets_ready:
        return SHEETS_UNAVAILABLE
    try:
        categories = bootstrap(client)
    except Exception:
        return SHEETS_UNAVAILABLE
    saved = []
    unsaved = []
    for path in image_paths:
        try:
            incoming = extract_lines(complete, image_path=path, categories=categories)
        except InferenceError:
            if saved or unsaved:
                return format_reply(saved, unsaved, _links(client, saved)) + "\n" + INFERENCE_FAILED
            return INFERENCE_FAILED
        if not incoming:
            continue
        normalized = [normalize(line, categories=categories, message_date=message_date) for line in incoming]
        result = append_lines(client, normalized)
        saved.extend(result.saved)
        unsaved.extend(result.unsaved)
        if result.unsaved:
            break
    if not saved and not unsaved:
        return NOTHING
    return format_reply(saved, unsaved, _links(client, saved))
