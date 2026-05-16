"""Abstract LLM adapter."""
from abc import ABC, abstractmethod
from typing import Any, Optional


class LLMResponse:
    def __init__(self, content: str = "", tool_calls: list[dict] = None, usage: dict = None):
        self.content = content
        self.tool_calls = tool_calls or []
        self.usage = usage or {}


class BaseLLM(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> LLMResponse:
        ...

    @abstractmethod
    def model_id(self) -> str:
        ...
