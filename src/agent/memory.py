"""Conversation memory with summarization."""
from typing import List, Dict, Optional
from core.tokenizer import Tokenizer


class Memory:
    def __init__(self, tokenizer: Tokenizer, max_tokens: int = 120000, summary_threshold: int = 80000):
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens
        self.summary_threshold = summary_threshold
        self.messages: List[Dict] = []
        self.summary: str = ""
        self.turn_count: int = 0

    def add(self, role: str, content: str, tool_calls: Optional[List[Dict]] = None, tool_call_id: Optional[str] = None):
        msg: Dict = {"role": role, "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if tool_call_id:
            msg["tool_call_id"] = tool_call_id
        self.messages.append(msg)
        self.turn_count += 1
        self._maybe_compress()

    def _maybe_compress(self):
        pass

    def _compress(self):
        # Simple compression: keep system, first user message, last 4 exchanges, summarize middle
        if len(self.messages) <= 6:
            return
        system = [m for m in self.messages if m["role"] == "system"]
        first_user = None
        for m in self.messages:
            if m["role"] == "user":
                first_user = m
                break
        tail = self.messages[-4:]
        middle = self.messages[len(system) + (1 if first_user else 0):-4]

        middle_text = "\n".join(f"{m['role']}: {m['content'][:500]}" for m in middle)
        new_summary = f"[Previous conversation summary]\n{self.summary}\nRecent turns:\n{middle_text}\n"
        self.summary = new_summary

        self.messages = system
        if first_user:
            self.messages.append(first_user)
        self.messages.append({"role": "system", "content": f"Conversation summary so far:\n{self.summary}"})
        self.messages.extend(tail)

    def get_messages(self) -> List[Dict]:
        return self.messages

    def clear(self):
        self.messages.clear()
        self.summary = ""
        self.turn_count = 0
