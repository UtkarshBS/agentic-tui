""""Collapsible tool execution trace."""

from textual.widgets import Static
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Group


class ToolCallPanel(Static):
    DEFAULT_CSS = """
    ToolCallPanel {
        height: 1fr;
        border: solid $warning;
        padding: 1;
    }
    """

    def __init__(self):
        self._calls = []
        super().__init__()

    def add_call(self, name: str, args: str, result: str = None):
        entry = {"name": name, "args": args, "result": result}
        self._calls.append(entry)
        self.refresh()

    def render(self):
        if not self._calls:
            return Panel("No tool calls yet.", title="Tools")

        group_items = []
        for i, call in enumerate(self._calls[-20:]):
            title = f"{i+1}. {call['name']}"
            body = f"Args: {call['args'][:200]}"
            if call.get("result"):
                body += f"\n→ : {str(call['result'])[:300]}"

            table = Table(show_header=False, box=None, padding=0)
            table.add_column(style="dim yellow")
            table.add_row(Text(body, style="dim"))
            group_items.append(Panel(table, title=title, border_style="yellow"))

        return Group(*group_items)
