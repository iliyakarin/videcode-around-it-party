import os
from dataclasses import dataclass, field

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from expense.model import NormalizedLine
from expense.normalize import HEADER, OTHER, SUMMARY
from expense.summary import summary_rows

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def a1(tab: str, cells: str) -> str:
    return "'" + tab.replace("'", "''") + "'!" + cells


@dataclass
class AppendResult:
    saved: list[NormalizedLine] = field(default_factory=list)
    unsaved: list[tuple[NormalizedLine, str]] = field(default_factory=list)


def bootstrap(client) -> list[str]:
    tabs = client.list_tabs()
    if OTHER not in tabs:
        client.add_tab(OTHER)
        tabs = client.list_tabs()
    categories = [tab for tab in tabs if tab != SUMMARY]
    for tab in categories:
        if not client.read_header(tab):
            client.write_header(tab, HEADER)
    client.replace_summary(summary_rows(categories))
    return categories


def _text(value: str) -> str:
    # USER_ENTERED would evaluate a leading = + - @ as a formula.
    return "'" + value if value.startswith(("=", "+", "-", "@")) else value


def _row(line: NormalizedLine) -> list[str]:
    amount = "" if line.amount is None else f"{line.amount:.2f}"
    return [
        line.date, _text(line.description), amount,
        _text(line.paid_with), _text(line.notes),
    ]


def append_lines(client, lines: list[NormalizedLine]) -> AppendResult:
    result = AppendResult()
    pending = list(lines)
    while pending:
        line = pending.pop(0)
        try:
            client.append_row(line.category, _row(line))
        except Exception as exc:
            result.unsaved.append((line, str(exc)))
            result.unsaved.extend((later, "not attempted") for later in pending)
            break
        result.saved.append(line)
    return result


class GoogleSheets:
    def __init__(self, spreadsheet_id: str):
        creds = Credentials.from_service_account_file(
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=SCOPES
        )
        self._id = spreadsheet_id
        self._api = build("sheets", "v4", credentials=creds, cache_discovery=False)

    def list_tabs(self) -> list[str]:
        meta = self._api.spreadsheets().get(
            spreadsheetId=self._id, fields="sheets.properties(title,sheetId)"
        ).execute()
        self._gids = {}
        titles = []
        for sheet in meta["sheets"]:
            props = sheet["properties"]
            titles.append(props["title"])
            self._gids[props["title"]] = props["sheetId"]
        return titles

    def tab_url(self, tab: str) -> str:
        url = f"https://docs.google.com/spreadsheets/d/{self._id}/edit"
        gid = getattr(self, "_gids", {}).get(tab)
        return url if gid is None else f"{url}#gid={gid}"

    def read_header(self, tab: str) -> list[str]:
        res = self._api.spreadsheets().values().get(
            spreadsheetId=self._id, range=a1(tab, "A1:E1")
        ).execute()
        values = res.get("values") or []
        return values[0] if values else []

    def write_header(self, tab: str, header: list[str]) -> None:
        self._api.spreadsheets().values().update(
            spreadsheetId=self._id, range=a1(tab, "A1:E1"),
            valueInputOption="RAW", body={"values": [header]},
        ).execute()

    def add_tab(self, tab: str) -> None:
        self._api.spreadsheets().batchUpdate(
            spreadsheetId=self._id,
            body={"requests": [{"addSheet": {"properties": {"title": tab}}}]},
        ).execute()

    def replace_summary(self, rows: list[list[str]]) -> None:
        self._api.spreadsheets().values().clear(
            spreadsheetId=self._id, range=a1("Summary", "A2:B"), body={}
        ).execute()
        if rows:
            self._api.spreadsheets().values().update(
                spreadsheetId=self._id, range=a1("Summary", "A2"),
                valueInputOption="USER_ENTERED", body={"values": rows},
            ).execute()

    def append_row(self, tab: str, row: list[str]) -> None:
        self._api.spreadsheets().values().append(
            spreadsheetId=self._id, range=a1(tab, "A:E"),
            valueInputOption="USER_ENTERED", insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()
