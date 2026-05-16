"""File system tools."""
import re
from pathlib import Path
from core.project import Project
from tools.base import ToolRegistry

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", ".mypy_cache", ".tox", "dist", "build", ".egg-info"}

def _is_allowed(path: str) -> bool:
    return not any(part in SKIP_DIRS for part in Path(path).parts)

def register_file_tools(registry: ToolRegistry, project: Project):
    @registry.register(description="Read file contents. Path is relative to project root.")
    def read_file(path: str) -> str:
        if not _is_allowed(path):
            return "(path excluded)"
        try:
            return project.read_file(path)
        except Exception as e:
            return f"Error reading {path}: {e}"

    @registry.register(description="List directory contents.")
    def list_dir(path: str = ".") -> str:
        if not _is_allowed(path):
            return "(directory excluded)"
        try:
            target = project.root / path
            out = []
            for e in sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
                out.append(f"{'[F]' if e.is_file() else '[D]'} {e.name}")
            return "\n".join(out)
        except Exception as e:
            return f"Error: {e}"

    @registry.register(description="Regex grep over files. Returns path:line: matches.")
    def grep(pattern: str, path: str = ".", glob_pattern: str = "*") -> str:
        if not _is_allowed(path):
            return "(search path excluded)"
        try:
            target = project.root / path
            matches = []
            for fp in target.rglob(glob_pattern):
                if not fp.is_file():
                    continue
                if not _is_allowed(str(fp.relative_to(project.root))):
                    continue
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                for i, line in enumerate(text.splitlines(), 1):
                    if re.search(pattern, line):
                        rel = fp.relative_to(project.root)
                        matches.append(f"{rel}:{i}: {line.strip()}")
                        if len(matches) > 100:
                            return "\n".join(matches[:100]) + "\n... (truncated)"
            return "\n".join(matches) if matches else "No matches."
        except Exception as e:
            return f"Error: {e}"

    @registry.register(description="Glob file search.")
    def glob(pattern: str) -> str:
        try:
            hits = project.list_files(pattern)
            allowed = [h for h in hits if _is_allowed(str(h))]
            return "\n".join(str(h) for h in allowed) if allowed else "No files match."
        except Exception as e:
            return f"Error: {e}"