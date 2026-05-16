"""Mutable working state for the agent."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class PendingEdit:
    file_path: str
    old_string: str
    new_string: str
    approved: bool = False
    applied: bool = False


@dataclass
class AgentState:
    scratchpad: str = ""
    pending_edits: List[PendingEdit] = field(default_factory=list)
    locked_files: set = field(default_factory=set)
    iteration_count: int = 0
    last_error: Optional[str] = None
    plan: List[Dict] = field(default_factory=list)

    def lock(self, path: str):
        self.locked_files.add(path)

    def unlock(self, path: str):
        self.locked_files.discard(path)

    def is_locked(self, path: str) -> bool:
        return path in self.locked_files

    def add_edit(self, edit: PendingEdit):
        self.pending_edits.append(edit)

    def approve_edit(self, index: int):
        if 0 <= index < len(self.pending_edits):
            self.pending_edits[index].approved = True

    def reset(self):
        self.scratchpad = ""
        self.pending_edits.clear()
        self.locked_files.clear()
        self.iteration_count = 0
        self.last_error = None
        self.plan.clear()
