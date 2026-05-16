"""OpenAI API adapter."""
import os
from typing import Optional
from openai import AsyncOpenAI
from .base import BaseLLM, LLMResponse


class OpenAIAdapter(BaseLLM):
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )

    def model_id(self) -> str:
        return f"openai/{self.model}"

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] = None,
        temperature: float = 0.2,
        stream: bool = False,
    ) -> LLMResponse:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        resp = await self.client.chat.completions.create(**kwargs)
        message = resp.choices[0].message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                })

        return LLMResponse(
            content=message.content or "",
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            } if resp.usage else {},
        )
