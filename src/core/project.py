"""Project workspace detection and metadata."""
from pathlib import Path
from typing import Optional
import git
import os


class Project:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self._repo: Optional[git.Repo] = None
        try:
            self._repo = git.Repo(self.root, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            pass

    @classmethod
    def from_path(cls, path: Path) -> "Project":
        return cls(path)

    def is_git_repo(self) -> bool:
        return self._repo is not None

    def git_status(self) -> str:
        if not self._repo:
            return "Not a git repository"
        return self._repo.git.status("--short")

    def git_diff(self) -> str:
        if not self._repo:
            return ""
        return self._repo.git.diff()

    def list_files(self, pattern: str = "**/*") -> list[Path]:
        """List files respecting .gitignore if present."""
        files = []
        gitignore = self._load_gitignore()
        for p in self.root.glob(pattern):
            if p.is_file() and not self._is_ignored(p, gitignore):
                files.append(p.relative_to(self.root))
        return sorted(files)

    def _load_gitignore(self) -> list[str]:
        gi = self.root / ".gitignore"
        if not gi.exists():
            return []
        return [line.strip() for line in gi.read_text().splitlines() if line.strip() and not line.startswith("#")]

    def _is_ignored(self, path: Path, patterns: list[str]) -> bool:
        sp = str(path)
        for pat in patterns:
            if pat.endswith("/"):
                if pat[:-1] in sp.split(os.sep):
                    return True
            elif pat in sp or sp.endswith(pat):
                return True
        return False

    def read_file(self, rel_path: str) -> str:
        target = self.root / rel_path
        target.resolve().relative_to(self.root)  # ensure within root
        return target.read_text(encoding="utf-8", errors="replace")

    def write_file(self, rel_path: str, content: str) -> None:
        target = self.root / rel_path
        target.resolve().relative_to(self.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
