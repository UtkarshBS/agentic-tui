"""Syntax highlighted code display."""
from textual.widgets import Static
from rich.syntax import Syntax
from rich.panel import Panel


class CodeBlock(Static):
    def __init__(self, code: str, language: str = "python", title: str = None):
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.panel = Panel(syntax, title=title or f"{language}")
        super().__init__(self.panel)

    def update_code(self, code: str, language: str = "python", title: str = None):
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self.panel = Panel(syntax, title=title or f"{language}")
        self.update(self.panel)
