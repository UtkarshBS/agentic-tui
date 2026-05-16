"""Token counting utilities."""
import tiktoken


class Tokenizer:
    def __init__(self, model: str = "gpt-4o"):
        try:
            self._enc = tiktoken.encoding_for_model(model)
        except KeyError:
            self._enc = tiktoken.get_encoding("cl100k_base")

    def count(self, text: str) -> int:
        return len(self._enc.encode(text))

    def count_messages(self, messages: list[dict]) -> int:
        total = 0
        for m in messages:
            total += self.count(m.get("content", ""))
            if "tool_calls" in m:
                for tc in m["tool_calls"]:
                    total += self.count(tc.get("function", {}).get("arguments", ""))
        return total
