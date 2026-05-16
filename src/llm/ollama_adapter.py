"""Ollama local adapter."""
import os
import httpx
from typing import Optional
from .base import BaseLLM, LLMResponse


class OllamaAdapter(BaseLLM):
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=300.0)

    def model_id(self) -> str:
        return f"ollama/{self.model}"

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> LLMResponse:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        resp = await self.client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()

        return LLMResponse(
            content=data["message"].get("content", ""),
            usage={},
        )
