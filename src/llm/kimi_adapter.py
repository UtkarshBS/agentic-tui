"""Moonshot Kimi API adapter."""
import os
import httpx
from typing import Optional
from .base import BaseLLM, LLMResponse


class KimiAdapter(BaseLLM):
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("KIMI_MODEL", "kimi-latest")
        self.api_key = os.getenv("KIMI_API_KEY", "")
        self.base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0,
        )

    def model_id(self) -> str:
        return f"kimi/{self.model}"

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
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        resp = await self.client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        message = choice["message"]

        tool_calls = []
        if message.get("tool_calls"):
            for tc in message["tool_calls"]:
                tool_calls.append({
                    "id": tc["id"],
                    "type": tc["type"],
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"],
                    }
                })

        return LLMResponse(
            content=message.get("content", ""),
            tool_calls=tool_calls,
            usage=data.get("usage", {}),
        )
