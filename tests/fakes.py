class FakeSheets:
    def __init__(self, tabs, headers):
        self.tabs = list(tabs)
        self.headers = dict(headers)
        self.summary = []
        self.rows = {}
        self.fail_on = None

    def list_tabs(self):
        return list(self.tabs)

    def read_header(self, tab):
        return list(self.headers.get(tab, []))

    def write_header(self, tab, header):
        self.headers[tab] = list(header)

    def add_tab(self, tab):
        self.tabs.append(tab)

    def replace_summary(self, rows):
        self.summary = rows

    def tab_url(self, tab):
        return f"https://sheet.example/{tab}#gid=1"

    def append_row(self, tab, row):
        if tab == self.fail_on:
            raise RuntimeError("down")
        self.rows.setdefault(tab, []).append(row)
