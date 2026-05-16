"""Hybrid dense + sparse retrieval."""
import bm25s
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
from rag.vector_store import VectorStore
from rag.embedder import NomicEmbedder


def _debug(msg: str):
    with open(Path.home() / "agentic-tui-debug.log", "a") as f:
        f.write(f"{msg}\n")


class Retriever:
    def __init__(self, store: VectorStore, embedder: NomicEmbedder):
        self.store = store
        self.embedder = embedder
        self._bm25_model = None
        self._bm25_corpus: List[Tuple[int, str]] = []

    def _rebuild_bm25(self):
        _debug("[Retriever] rebuilding BM25...")
        corpus = self.store.all_chunks()
        self._bm25_corpus = corpus
        if not corpus:
            self._bm25_model = None
            _debug("[Retriever] no corpus, BM25 disabled")
            return
        texts = [c[1] for c in corpus]
        self._bm25_model = bm25s.BM25()
        self._bm25_model.index(texts)
        _debug(f"[Retriever] BM25 indexed {len(texts)} documents")

    async def search(self, query: str, top_k: int = 8) -> List[Dict]:
        _debug(f"[Retriever] search called: {query[:50]}")
        if self._bm25_model is None:
            _debug("[Retriever] BM25 is None, rebuilding...")
            self._rebuild_bm25()

        # Dense
        _debug("[Retriever] getting query embedding...")
        qvec = await self.embedder.embed([query], task_type="search_query")
        _debug(f"[Retriever] query embedding shape: {qvec.shape}")
        dense = self.store.search(qvec[0], top_k=top_k * 2)
        _debug(f"[Retriever] dense results: {len(dense)}")

        # Sparse
        sparse: List[Tuple[int, float]] = []
        if self._bm25_model and self._bm25_corpus:
            _debug("[Retriever] running BM25...")
            results = self._bm25_model.retrieve([query], k=top_k * 2)
            doc_ids = results.doc_ids[0]
            scores = results.scores[0]
            for idx, doc_id in enumerate(doc_ids):
                sparse.append((self._bm25_corpus[doc_id][0], float(scores[idx]) if idx < len(scores) else 0.0))
            _debug(f"[Retriever] sparse results: {len(sparse)}")

        fused = self._rrf_fuse(dense, sparse)
        top_ids = [fid for fid, _ in fused[:top_k]]
        _debug(f"[Retriever] returning {len(top_ids)} results")
        return self.store.get_by_ids(top_ids)

    def _rrf_fuse(self, dense: List[Tuple[int, float]], sparse: List[Tuple[int, float]], k: int = 60) -> List[Tuple[int, float]]:
        scores: Dict[int, float] = {}
        for rank, (doc_id, _) in enumerate(dense):
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        for rank, (doc_id, _) in enumerate(sparse):
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)