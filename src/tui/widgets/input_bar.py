"""Multi-line input with slash commands."""
from textual.widgets import TextArea
from textual.message import Message


class InputBar(TextArea):
    DEFAULT_CSS = """
    InputBar {
        height: 20%;
        border: solid $secondary;
    }
    """

    BINDINGS = [
        ("ctrl+s", "submit", "Submit"),
        ("ctrl+j", "newline", "Newline"),
    ]

    def __init__(self):
        super().__init__(language="markdown", id="input-bar", show_line_numbers=False)

    def action_submit(self):
        text = self.text.strip()
        if text:
            self.post_message(self.Submitted(text))
            self.clear()

    def action_newline(self):
        self.insert("\n")

    def clear(self):
        self.text = ""

    class Submitted(Message):
        def __init__(self, text: str):
            self.text = text
            super().__init__()
