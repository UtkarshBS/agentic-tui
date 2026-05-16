"""Code-aware chunking."""
import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Chunk:
    file_path: str
    start_line: int
    end_line: int
    content: str
    chunk_type: str


class Chunker:
    def __init__(self, chunk_size: int = 1500, overlap: int = 150):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_file(self, file_path: Path, content: str) -> List[Chunk]:
        if file_path.suffix == ".py":
            return self._chunk_python(str(file_path), content)
        return self._chunk_generic(str(file_path), content)

    def _chunk_python(self, path: str, content: str) -> List[Chunk]:
        lines = content.splitlines(keepends=True)
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._chunk_generic(path, content)

        nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nodes.append((node.lineno, node.end_lineno, type(node).__name__))
        nodes.sort()

        covered = set()
        chunks = []
        for start, end, typ in nodes:
            s = max(0, start - 1)
            e = min(len(lines), end)
            block = "".join(lines[s:e])
            label = "function" if "Function" in typ else "class"
            if len(block) > self.chunk_size * 2:
                chunks.extend(self._slice(path, block, s, e, label))
            else:
                chunks.append(Chunk(path, s + 1, e, block, label))
            for i in range(s, e):
                covered.add(i)

        # Module-level leftovers
        remaining = []
        for i, line in enumerate(lines):
            if i not in covered:
                remaining.append((i, line))
            elif remaining:
                block = "".join(l for _, l in remaining)
                chunks.extend(self._slice(path, block, remaining[0][0], remaining[-1][0] + 1, "module"))
                remaining = []
        if remaining:
            block = "".join(l for _, l in remaining)
            chunks.extend(self._slice(path, block, remaining[0][0], remaining[-1][0] + 1, "module"))

        return sorted(chunks, key=lambda c: c.start_line)

    def _chunk_generic(self, path: str, content: str) -> List[Chunk]:
        lines = content.splitlines(keepends=True)
        return self._slice(path, content, 0, len(lines), "other")

    def _slice(self, path: str, text: str, start_line: int, end_line: int, label: str) -> List[Chunk]:
        chunks = []
        length = len(text)
        pos = 0
        while pos < length:
            end = min(pos + self.chunk_size, length)
            if end < length:
                nl = text.rfind('\n', pos, end)
                if nl != -1 and nl > pos + self.chunk_size // 2:
                    end = nl + 1
            piece = text[pos:end]
            l_start = start_line + text[:pos].count('\n')
            l_end = start_line + text[:end].count('\n')
            chunks.append(Chunk(path, l_start + 1, l_end, piece, label))
            advance = end - self.overlap
            pos = advance if advance > pos else end
        return chunks
