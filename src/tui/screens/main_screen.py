"""Primary three-pane screen."""
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Header, Footer
from textual.message import Message
from tui.widgets.chat_log import ChatLog
from tui.widgets.input_bar import InputBar
from tui.widgets.file_tree import FileTree
from tui.widgets.status_bar import StatusBar
from tui.widgets.tool_call_panel import ToolCallPanel
from tui.widgets.code_block import CodeBlock
from pathlib import Path
import os


def _debug(msg: str):
    with open(Path.home() / "agentic-tui-debug.log", "a") as f:
        f.write(f"{msg}\n")


class MainScreen(Screen):
    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        super().__init__()

    def compose(self) -> None:
        yield Header(show_clock=True)
        with Horizontal(id="main-screen"):
            with Vertical(id="left-pane"):
                yield FileTree(self.project_root)
                yield Static("Shortcuts:\n/idx - index\n/cfg - config\n/quit - exit", id="shortcuts")
            with Vertical(id="center-pane"):
                yield ChatLog()
                yield InputBar()
            with Vertical(id="right-pane"):
                yield ToolCallPanel()
                yield CodeBlock("# Preview\nSelect a file to preview", title="Preview")
        yield StatusBar()
        yield Footer()

    def on_mount(self):
        provider = os.getenv("DEFAULT_PROVIDER", "kimi")
        model = os.getenv("LMSTUDIO_MODEL", "default")
        self.set_status(model=f"{provider}/{model}", index="ready")
        self.add_chat_system(f"Ready. Provider: {provider}. Type /cfg to change settings.")

    def on_input_bar_submitted(self, event: InputBar.Submitted):
        _debug(f"[MainScreen] got message: {event.text[:50]}")
        text = event.text
        if text.startswith("/"):
            self._handle_slash(text)
        else:
            _debug(f"[MainScreen] posting UserMessage")
            self.post_message(self.UserMessage(text))

    def _handle_slash(self, text: str):
        cmd = text[1:].strip().lower()
        if cmd == "quit":
            self.app.exit()
        elif cmd == "cfg":
            self.app.push_screen("config")
        elif cmd == "idx":
            self.app.push_screen("indexer")
        else:
            self.add_chat_system(f"Unknown command: /{cmd}")

    def on_file_tree_file_selected(self, event: FileTree.FileSelected):
        try:
            content = event.path.read_text(encoding="utf-8", errors="replace")
            preview = self.query_one(CodeBlock)
            preview.update_code(content, language=event.path.suffix.lstrip(".") or "text", title=str(event.path.name))
        except Exception as e:
            self.add_chat_system(f"Cannot read file: {e}")

    def add_chat_user(self, text: str):
        self.query_one(ChatLog).add_user(text)

    def add_chat_assistant(self, text: str):
        self.query_one(ChatLog).add_assistant(text)

    def add_chat_tool(self, name: str, result: str):
        self.query_one(ChatLog).add_tool(name, result)

    def add_chat_system(self, text: str):
        self.query_one(ChatLog).add_system(text)

    def add_tool_call(self, name: str, args: str):
        self.query_one(ToolCallPanel).add_call(name, args)

    def set_status(self, model: str = None, tokens: str = None, index: str = None):
        bar = self.query_one(StatusBar)
        if model:
            bar.set_provider(model.split("/")[0] if "/" in model else model, model)
        if tokens:
            bar.set_tokens(tokens)
        if index:
            bar.set_index(index)

    class UserMessage(Message):
        def __init__(self, text: str):
            self.text = text
            super().__init__()