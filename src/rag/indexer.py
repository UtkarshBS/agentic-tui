"""Incremental codebase indexer."""
import hashlib
from pathlib import Path
from typing import Dict, Set, Callable, Optional
from core.project import Project
from rag.chunker import Chunker
from rag.embedder import NomicEmbedder
from rag.vector_store import VectorStore


TEXT_EXTS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml", ".toml",
    ".md", ".rst", ".txt", ".sh", ".bash", ".zsh", ".go", ".rs", ".java",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt",
    ".scala", ".r", ".m", ".sql", ".html", ".css", ".scss", ".less",
    ".vue", ".svelte", ".lua", ".pl", ".pm", ".dockerfile", ".env",
    ".ini", ".cfg", ".conf", ".lock", ".gitignore",
}

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", ".mypy_cache", ".tox", "dist", "build", ".egg-info", ".gitignore", "uv.lock"}


class Indexer:
    def __init__(self, project: Project, store: VectorStore, chunker: Chunker, embedder: NomicEmbedder, progress_callback: Optional[Callable[[int, int], None]] = None):
        self.project = project
        self.store = store
        self.chunker = chunker
        self.embedder = embedder
        self.progress_callback = progress_callback
        self._hashes: Dict[str, str] = {}

    def _is_text(self, p: Path) -> bool:
        if any(part in SKIP_DIRS for part in p.parts):
            return False
        return p.suffix.lower() in TEXT_EXTS or p.name.lower() in {"dockerfile", "makefile", ".gitignore"}

    def _hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    async def full_index(self):
        self.store.clear()
        self._hashes = {}
        files = [f for f in self.project.list_files("**/*") if self._is_text(f)]
        total = len(files)
        for i, rel in enumerate(files):
            if self.progress_callback:
                self.progress_callback(i + 1, total)
            try:
                content = self.project.read_file(str(rel))
            except Exception:
                continue
            await self._index_file(rel, content)

    async def incremental_update(self):
        files = [f for f in self.project.list_files("**/*") if self._is_text(f)]
        current: Set[str] = {str(f) for f in files}

        for old in list(self._hashes.keys()):
            if old not in current:
                self.store.delete_by_path(old)
                del self._hashes[old]

        for rel in files:
            try:
                content = self.project.read_file(str(rel))
            except Exception:
                continue
            h = self._hash(content)
            key = str(rel)
            if self._hashes.get(key) != h:
                self.store.delete_by_path(key)
                await self._index_file(rel, content, h)

    async def _index_file(self, rel: Path, content: str, h: str = None):
        h = h or self._hash(content)
        self._hashes[str(rel)] = h
        chunks = self.chunker.chunk_file(rel, content)
        if not chunks:
            return
        metas = []
        texts = []
        for ch in chunks:
            metas.append({
                "file_path": ch.file_path,
                "start_line": ch.start_line,
                "end_line": ch.end_line,
                "content_hash": h,
                "content": ch.content,
                "chunk_type": ch.chunk_type,
            })
            texts.append(ch.content)
        vectors = await self.embedder.embed(texts, task_type="search_document")
        self.store.add(metas, vectors)