"""Assemble retrieved chunks into prompt context."""
from typing import List, Dict


class ContextBuilder:
    def __init__(self, max_chars: int = 32000):
        self.max_chars = max_chars

    def build(self, chunks: List[Dict]) -> str:
        lines = []
        used = 0
        for ch in chunks:
            header = f"\n--- {ch['file_path']} (lines {ch['start_line']}-{ch['end_line']}) [{ch.get('chunk_type','?')}] ---\n"
            block = header + ch["content"] + "\n"
            if used + len(block) > self.max_chars:
                break
            lines.append(block)
            used += len(block)
        return "".join(lines)
