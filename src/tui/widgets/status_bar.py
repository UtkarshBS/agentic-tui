"""Bottom status bar."""

from textual.widgets import Static
from rich.text import Text
import os


class StatusBar(Static):
    DEFAULT_CSS = """
    StatusBar {
        height: 3;
        dock: bottom;
        background: #1a1a1a;
        color: #c0c0c0;
        content-align: center middle;
    }
    """

    def __init__(self):
        self._provider = os.getenv("DEFAULT_PROVIDER", "kimi")
        self._model = "default"
        self._tokens = "0"
        self._index = "idle"
        super().__init__()

    def set_provider(self, provider: str, model: str = None):
        self._provider = provider
        if model:
            self._model = model
        self._refresh()

    def set_tokens(self, tokens: str):
        self._tokens = tokens
        self._refresh()

    def set_index(self, status: str):
        self._index = status
        self._refresh()

    def _refresh(self):
        text = Text()
        text.append(f"  Provider: {self._provider}  ", style="bold cyan")
        text.append(f"|  Model: {self._model}  ", style="bold green")
        text.append(f"|  Tokens: {self._tokens}  ", style="bold yellow")
        text.append(f"|  Index: {self._index}  ", style="bold magenta")
        text.append("  ", style="")
        self.update(text)