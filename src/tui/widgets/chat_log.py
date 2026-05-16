"""Scrollable chat history."""
from textual.widgets import Static, RichLog
from textual.app import ComposeResult
from rich.markdown import Markdown
from rich.text import Text


class ChatLog(RichLog):
    DEFAULT_CSS = """
    ChatLog {
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__(highlight=True, markup=True)

    def add_user(self, text: str):
        self.write(Text(f"\nYou: {text}\n", style="bold cyan"))

    def add_assistant(self, text: str):
        self.write(Markdown(f"\n**Agent:**\n{text}\n"))

    def add_tool(self, name: str, result: str):
        self.write(Text(f"\n[tool: {name}] {result[:300]}...", style="dim yellow"))

    def add_system(self, text: str):
        self.write(Text(f"\n{text}", style="dim"))
