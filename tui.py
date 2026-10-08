"""
tui.py — a terminal interface for the privacy scanner.

THE POINT OF THIS FILE
------------------------
It imports and calls the exact same `scan_url()` from app/scanner.py that
the web version uses — nothing about the actual scanning, tracker
matching, or scoring logic changes. Only the *presentation layer* is
different. This is a useful pattern to internalize: a backend's core
logic shouldn't know or care whether a web frontend, a TUI, or a plain
CLI script is driving it.

WHY TEXTUAL
------------
Textual is a modern Python TUI framework (from the same team as the
`rich` library). Unlike building directly on the low-level `curses`
module, Textual gives you:
  - A widget system (Input, Button, DataTable, etc.) instead of manually
    positioning characters on a grid.
  - CSS-like styling (the `CSS` string below) instead of raw ANSI codes.
  - Native async support — critical here, since scan_url() is an async
    function (it awaits a network request) and Textual's `@work` lets
    that run in the background without freezing the UI while it waits.
"""

import httpx
from textual import work
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static

from app.scanner import scan_url

GRADE_COLORS = {
    "A": "green",
    "B": "chartreuse3",
    "C": "yellow",
    "D": "dark_orange",
    "F": "red",
}


class PrivacyScannerApp(App):
    """A terminal app: type a URL, see its privacy score and trackers."""

    CSS = """
    Screen { align: center top; }
    #input-row { height: 3; margin: 1 2; }
    #url-input { width: 1fr; }
    #status { margin: 0 2 1 2; color: $text-muted; }
    #score-panel {
        height: auto;
        border: round $primary;
        padding: 1 2;
        margin: 0 2 1 2;
    }
    #tracker-table { margin: 0 2; height: 1fr; }
    """

    BINDINGS = [("q", "quit", "Quit"), ("ctrl+c", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="input-row"):
            yield Input(placeholder="example.com", id="url-input")
            yield Button("Scan", id="scan-btn", variant="primary")
        yield Label("Enter a URL and press Enter or click Scan.", id="status")
        yield Static("", id="score-panel")
        yield DataTable(id="tracker-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#tracker-table", DataTable)
        table.add_columns("Company", "Domain", "Category")
        self.query_one("#url-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "scan-btn":
            self._start_scan()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._start_scan()

    def _start_scan(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        status = self.query_one("#status", Label)
        if not url:
            status.update("[red]Please enter a URL.[/]")
            return
        status.update("Scanning…")
        self.query_one("#scan-btn", Button).disabled = True
        self._run_scan(url)

    @work(exclusive=True)
    async def _run_scan(self, raw_url: str) -> None:
        """
        Runs in the background via Textual's @work decorator — the UI
        stays responsive (you could still type, resize, etc.) while this
        awaits the network request inside scan_url().
        """
        target = raw_url if raw_url.startswith(("http://", "https://")) else "https://" + raw_url
        status = self.query_one("#status", Label)
        try:
            result = await scan_url(target)
        except httpx.HTTPStatusError as e:
            status.update(f"[red]That site responded with HTTP {e.response.status_code}[/]")
            self.query_one("#scan-btn", Button).disabled = False
            return
        except httpx.RequestError as e:
            status.update(f"[red]Couldn't reach that URL: {e}[/]")
            self.query_one("#scan-btn", Button).disabled = False
            return

        self._show_result(result)
        self.query_one("#scan-btn", Button).disabled = False

    def _show_result(self, result: dict) -> None:
        status = self.query_one("#status", Label)
        status.update(f"Scanned {result['url']}")

        color = GRADE_COLORS.get(result["grade"], "white")
        score_panel = self.query_one("#score-panel", Static)
        score_panel.update(
            f"[bold {color}]{result['grade']}[/bold {color}]   "
            f"Score: {result['score']}/100   "
            f"{result['tracker_count']} tracker(s) from {result['unique_companies']} "
            f"compan{'y' if result['unique_companies'] == 1 else 'ies'}"
        )

        table = self.query_one("#tracker-table", DataTable)
        table.clear()
        if not result["trackers"]:
            table.add_row("—", "No known trackers found", "—")
        else:
            for t in result["trackers"]:
                table.add_row(t["company"], t["domain"], t["category"])


if __name__ == "__main__":
    PrivacyScannerApp().run()
