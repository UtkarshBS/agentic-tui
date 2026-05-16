"""Tests for code-aware chunking."""
import pytest
from pathlib import Path
from rag.chunker import Chunker


def test_python_chunking():
    code = """
def foo():
    pass

class Bar:
    def baz(self):
        pass
"""
    chunker = Chunker(chunk_size=500, overlap=50)
    chunks = chunker.chunk_file(Path("test.py"), code)
    types = {c.chunk_type for c in chunks}
    assert "function" in types or "class" in types


def test_generic_chunking():
    chunker = Chunker(chunk_size=100, overlap=10)
    chunks = chunker.chunk_file(Path("readme.md"), "# Hello\n" * 50)
    assert len(chunks) > 0
    assert all(c.chunk_type == "other" for c in chunks)
