"""Tests for SQLite vector store."""
import pytest
import numpy as np
from pathlib import Path
from rag.vector_store import VectorStore


def test_add_and_search(tmp_path):
    db = tmp_path / "test.db"
    store = VectorStore(db, dim=4)
    store.add(
        [{"file_path": "a.py", "content": "hello", "chunk_type": "function"}],
        np.array([[1.0, 0.0, 0.0, 0.0]], dtype=np.float32),
    )
    results = store.search(np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32), top_k=1)
    assert len(results) == 1
    assert results[0][1] > 0.99
    store.close()


def test_delete_by_path(tmp_path):
    db = tmp_path / "test.db"
    store = VectorStore(db, dim=2)
    store.add([{"file_path": "x.py"}], np.array([[1.0, 0.0]], dtype=np.float32))
    store.delete_by_path("x.py")
    results = store.search(np.array([1.0, 0.0], dtype=np.float32), top_k=1)
    assert len(results) == 0
    store.close()
