"""Directory tree with git status."""
from textual.widgets import DirectoryTree
from textual.message import Message
from pathlib import Path


class FileTree(DirectoryTree):
    DEFAULT_CSS = """
    FileTree {
        height: 1fr;
        border: solid green;
    }
    """

    def __init__(self, path: Path):
        super().__init__(path, id="file-tree")

    def on_directory_tree_file_selected(self, event):
        self.post_message(self.FileSelected(event.node, event.path))

    class FileSelected(Message):
        def __init__(self, node, path: Path):
            self.node = node
            self.path = path
            super().__init__()
