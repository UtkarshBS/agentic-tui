"""Progress screen for RAG indexing."""
from textual.screen import Screen
from textual.widgets import ProgressBar, Label, Button
from textual.containers import Vertical


class IndexerScreen(Screen):
    DEFAULT_CSS = """
    IndexerScreen {
        align: center middle;
    }
    #indexer-progress {
        width: 60;
    }
    """

    BINDINGS = [("escape", "pop_screen", "Back")]

    def __init__(self):
        self._running = False
        super().__init__()

    def compose(self) -> None:
        with Vertical(id="indexer-progress"):
            yield Label("Indexing codebase...", id="indexer-label")
            yield ProgressBar(total=100, show_eta=False, id="indexer-bar")
            yield Button("Start Index", variant="success", id="start-index")
            yield Button("Back", variant="primary", id="back")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "start-index":
            self._start_index()
        else:
            self.app.pop_screen()

    def _start_index(self):
        if self._running:
            return
        self._running = True
        self.query_one("#indexer-label", Label).update("Indexing in progress...")
        bar = self.query_one("#indexer-bar", ProgressBar)
        bar.update(total=100, progress=0)
        self.post_message(self.StartIndex())

    def set_progress(self, current: int, total: int):
        bar = self.query_one("#indexer-bar", ProgressBar)
        pct = int((current / max(total, 1)) * 100)
        bar.update(progress=pct)

    def finish(self):
        self._running = False
        self.query_one("#indexer-label", Label).update("Indexing complete!")
        self.query_one("#indexer-bar", ProgressBar).update(progress=100)

    class StartIndex:
        pass

    def action_pop_screen(self):
        self.app.pop_screen()