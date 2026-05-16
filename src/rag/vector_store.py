"""SQLite-backed vector store with in-memory numpy search."""
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict


class VectorStore:
    def __init__(self, db_path: Path, dim: int = 768):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._dim = dim
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_db()
        self._vectors: np.ndarray = np.zeros((0, dim), dtype=np.float32)
        self._ids: List[int] = []
        self._load()

    def _init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                start_line INTEGER,
                end_line INTEGER,
                content_hash TEXT,
                content TEXT,
                chunk_type TEXT,
                vector BLOB
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_path ON chunks(file_path)")
        self._conn.commit()

    def _load(self):
        rows = self._conn.execute("SELECT id, vector FROM chunks").fetchall()
        if rows:
            self._ids = [r[0] for r in rows]
            self._vectors = np.array([np.frombuffer(r[1], dtype=np.float32) for r in rows])
        else:
            self._ids = []
            self._vectors = np.zeros((0, self._dim), dtype=np.float32)

    def add(self, metas: List[Dict], vectors: np.ndarray):
        assert len(metas) == len(vectors)
        for ch, vec in zip(metas, vectors):
            blob = vec.astype(np.float32).tobytes()
            cur = self._conn.execute("""
                INSERT INTO chunks (file_path, start_line, end_line, content_hash, content, chunk_type, vector)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ch["file_path"], ch.get("start_line"), ch.get("end_line"),
                  ch.get("content_hash"), ch.get("content"), ch.get("chunk_type"), blob))
            self._ids.append(cur.lastrowid)
        self._conn.commit()
        v = vectors.astype(np.float32)
        self._vectors = np.vstack([self._vectors, v]) if self._vectors.size else v

    def search(self, query_vector: np.ndarray, top_k: int = 8) -> List[Tuple[int, float]]:
        if self._vectors.shape[0] == 0:
            return []
        q = query_vector.astype(np.float32).flatten()
        scores = self._vectors @ q
        top_idx = np.argpartition(scores, -top_k)[-top_k:]
        top_idx = top_idx[np.argsort(-scores[top_idx])]
        return [(self._ids[i], float(scores[i])) for i in top_idx]

    def get_by_ids(self, ids: List[int]) -> List[Dict]:
        if not ids:
            return []
        ph = ",".join("?" * len(ids))
        rows = self._conn.execute(
            f"SELECT id, file_path, start_line, end_line, content, chunk_type FROM chunks WHERE id IN ({ph})",
            tuple(ids)
        ).fetchall()
        return [{"id": r[0], "file_path": r[1], "start_line": r[2], "end_line": r[3], "content": r[4], "chunk_type": r[5]} for r in rows]

    def all_chunks(self) -> List[Tuple[int, str]]:
        rows = self._conn.execute("SELECT id, content FROM chunks").fetchall()
        return [(r[0], r[1]) for r in rows]

    def delete_by_path(self, file_path: str):
        self._conn.execute("DELETE FROM chunks WHERE file_path = ?", (file_path,))
        self._conn.commit()
        self._load()

    def clear(self):
        self._conn.execute("DELETE FROM chunks")
        self._conn.commit()
        self._vectors = np.zeros((0, self._dim), dtype=np.float32)
        self._ids = []

    def close(self):
        self._conn.close()
