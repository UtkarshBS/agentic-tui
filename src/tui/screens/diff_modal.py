"""Side-by-side diff approval modal."""
from textual.screen import ModalScreen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Button, Label
from rich.syntax import Syntax
from rich.panel import Panel


class DiffModal(ModalScreen):
    DEFAULT_CSS = """
    DiffModal {
        align: center middle;
    }
    #diff-modal {
        width: 90%;
        height: 90%;
        border: solid $primary;
        background: $surface;
        padding: 1;
    }
    """

    def __init__(self, file_path: str, old_text: str, new_text: str, edit_index: int):
        self.file_path = file_path
        self.old_text = old_text
        self.new_text = new_text
        self.edit_index = edit_index
        super().__init__()

    def compose(self) -> None:
        with Vertical(id="diff-modal"):
            yield Label(f"Proposed edit: {self.file_path}")
            with Horizontal():
                yield Static(Panel(
                    Syntax(self.old_text, "python", theme="monokai", line_numbers=True),
                    title="Before",
                    border_style="red",
                ))
                yield Static(Panel(
                    Syntax(self.new_text, "python", theme="monokai", line_numbers=True),
                    title="After",
                    border_style="green",
                ))
            with Horizontal():
                yield Button("Approve", variant="success", id="approve")
                yield Button("Reject", variant="error", id="reject")
                yield Button("Close", variant="primary", id="close")

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "approve":
            self.dismiss({"action": "approve", "index": self.edit_index})
        elif btn_id == "reject":
            self.dismiss({"action": "reject", "index": self.edit_index})
        else:
            self.dismiss(None)
