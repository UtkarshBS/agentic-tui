"""Mock LLM for offline TUI testing."""
import json
import asyncio
from typing import Optional
from .base import BaseLLM, LLMResponse


class MockAdapter(BaseLLM):
    def __init__(self, model: Optional[str] = None):
        self.model = model or "mock"
        self._turn = 0

    def model_id(self) -> str:
        return "mock/default"

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> LLMResponse:
        self._turn += 1
        await asyncio.sleep(0.3)

        if self._turn == 1 and tools:
            return LLMResponse(
                content="I'll search the codebase.",
                tool_calls=[{
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "semantic_search",
                        "arguments": json.dumps({"query": "example", "top_k": 3}),
                    }
                }]
            )

        return LLMResponse(
            content="Done! Check pending edits.",
            tool_calls=[],
        )
