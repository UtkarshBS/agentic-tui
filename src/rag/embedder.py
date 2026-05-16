"""Embedding clients: Nominal (cloud) and Ollama (local)."""
import os
import httpx
import numpy as np
from typing import List


class NomicEmbedder:
    """Nominal Atlas API embedder. Falls back to random noise if no API key."""
    def __init__(self, model: str = "nomic-embed-text-v1.5", api_key: str = None):
        self.model = model
        self.api_key = api_key or os.getenv("NOMIC_API_KEY", "")
        self.base_url = "https://api-atlas.nominal.ai/v1"
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
        self._dim = 768

    async def embed(self, texts: List[str], task_type: str = "search_document") -> np.ndarray:
        if not self.api_key:
            rng = np.random.default_rng(abs(hash(texts[0])) % (2**32) if texts else 42)
            vecs = rng.random((len(texts), self._dim)).astype(np.float32)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            return vecs / np.where(norms == 0, 1, norms)

        resp = await self.client.post(
            "/embedding/text",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "texts": texts, "task_type": task_type},
        )
        resp.raise_for_status()
        data = resp.json()
        embeddings = np.array(data["embeddings"], dtype=np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / np.where(norms == 0, 1, norms)


class OllamaEmbedder:
    """Ollama local embedding via /api/embed."""
    def __init__(self, model: str = None, base_url: str = None):
        self.model = model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
        self._dim = 768

    async def embed(self, texts: List[str], task_type: str = "search_document") -> np.ndarray:
        if not texts:
            return np.zeros((0, self._dim), dtype=np.float32)
        
        resp = await self.client.post(
            "/api/embed",
            json={"model": self.model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()
        
        embeddings = np.array(data["embeddings"], dtype=np.float32)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / np.where(norms == 0, 1, norms)
