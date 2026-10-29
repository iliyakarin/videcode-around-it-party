import sys
from pathlib import Path

_pkg = Path("/opt/personal-expense")
if _pkg.is_dir() and str(_pkg) not in sys.path:
    sys.path.insert(0, str(_pkg))

from . import tools

SCHEMA = {
    "name": "record_expense",
    "description": (
        "Call this for every user photo of a bill. Pass the local image path. "
        "Reply to the user with the reply field and do not describe the bill yourself."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {"type": "string"},
            "message_date": {"type": "string", "description": "YYYY-MM-DD the photo was sent"},
        },
        "required": ["image_path"],
    },
}


def register(ctx):
    ctx.register_tool(
        name="record_expense",
        toolset="expense",
        schema=SCHEMA,
        handler=tools.record_expense,
    )
    ctx.register_hook("pre_gateway_dispatch", tools.on_photo)
