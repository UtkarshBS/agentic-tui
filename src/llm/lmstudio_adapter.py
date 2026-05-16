"""LM Studio local server adapter."""
import os
import httpx
import json
import re
from typing import Optional
from .base import BaseLLM, LLMResponse


class LMStudioAdapter(BaseLLM):
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("LMSTUDIO_MODEL", "qwen/qwen3.5-9b")
        self.base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        self.api_key = os.getenv("LMSTUDIO_API_KEY", "lm-studio")
        print(f"[LMStudio] init model={self.model} url={self.base_url}")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=300.0,
        )

    def model_id(self) -> str:
        return f"lmstudio/{self.model}"

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

        print(f"[LMStudio] sending request with {len(messages)} messages, tools={tools is not None}")
        print(f"[LMStudio] payload: {json.dumps(payload, indent=2)[:500]}")
        print(f"[LMStudio] FULL MESSAGES:\n{json.dumps(messages, indent=2)}")
        try:
            resp = await self.client.post("/chat/completions", json=payload)
            print(f"[LMStudio] response status: {resp.status_code}")
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

            # Parse XML tool calls from reasoning_content when structured tool_calls is empty
            if not tool_calls and message.get("reasoning_content"):
                parsed = self._parse_xml_tool_calls(message["reasoning_content"])
                if parsed:
                    tool_calls = parsed
                    print(f"[LMStudio] parsed {len(tool_calls)} tool calls from reasoning_content")

            content = message.get("content", "")
            # Qwen puts final answers in reasoning_content when content is empty
            if not content.strip() and message.get("reasoning_content") and not tool_calls:
                content = message["reasoning_content"]
                print(f"[LMStudio] using reasoning_content as content ({len(content)} chars)")

            print(f"[LMStudio] response content: {content[:200]}")
            print(f"[LMStudio] tool_calls: {len(tool_calls)}")

            return LLMResponse(
                content=content,
                tool_calls=tool_calls,
                usage=data.get("usage", {}),
            )
        except Exception as e:
            print(f"[LMStudio] ERROR: {e}")
            raise

    def _parse_xml_tool_calls(self, text: str) -> list:
        """Parse <tool_call> XML blocks that Qwen emits in reasoning_content."""
        if not text or "<tool_call>" not in text:
            return []
        
        tools = []
        blocks = re.findall(r'<tool_call>(.*?)</tool_call>', text, re.DOTALL)
        
        for block in blocks:
            func_match = re.search(r'<function=(.*?)>', block)
            if not func_match:
                continue
            func_name = func_match.group(1).strip()
            
            args = {}
            for param_match in re.finditer(r'<parameter=(.*?)>(.*?)</parameter>', block, re.DOTALL):
                key = param_match.group(1).strip()
                val = param_match.group(2).strip()
                if val.isdigit():
                    args[key] = int(val)
                elif val.lower() in ("true", "false"):
                    args[key] = val.lower() == "true"
                else:
                    args[key] = val
            
            tools.append({
                "id": f"call_{len(tools)}",
                "type": "function",
                "function": {
                    "name": func_name,
                    "arguments": json.dumps(args)
                }
            })
        
        return tools