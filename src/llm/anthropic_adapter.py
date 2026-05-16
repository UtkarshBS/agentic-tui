"""Anthropic Claude adapter."""
import os
import json
import httpx
from typing import Optional
from .base import BaseLLM, LLMResponse


class AnthropicAdapter(BaseLLM):
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client = httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=120.0,
        )

    def model_id(self) -> str:
        return f"anthropic/{self.model}"

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        anthropic_tools = []
        for t in tools:
            func = t["function"]
            anthropic_tools.append({
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"],
            })
        return anthropic_tools

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> LLMResponse:
        system = ""
        clean_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                clean_messages.append(m)

        payload = {
            "model": self.model,
            "messages": clean_messages,
            "system": system,
            "temperature": temperature,
            "max_tokens": 4096,
        }
        if tools:
            payload["tools"] = self._convert_tools(tools)

        resp = await self.client.post("/v1/messages", json=payload)
        resp.raise_for_status()
        data = resp.json()

        content_text = ""
        tool_calls = []
        for block in data.get("content", []):
            if block["type"] == "text":
                content_text += block["text"]
            elif block["type"] == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block["input"]),
                    }
                })

        return LLMResponse(
            content=content_text,
            tool_calls=tool_calls,
            usage=data.get("usage", {}),
        )
