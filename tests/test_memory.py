"""Tests for conversation memory."""
from core.tokenizer import Tokenizer
from agent.memory import Memory


def test_memory_add_and_retrieve():
    tok = Tokenizer()
    mem = Memory(tok, max_tokens=100000)
    mem.add("user", "Hello")
    mem.add("assistant", "Hi there")
    msgs = mem.get_messages()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"


def test_memory_compression():
    tok = Tokenizer()
    mem = Memory(tok, max_tokens=100000, summary_threshold=10)
    for i in range(20):
        mem.add("user", f"Message {i}")
        mem.add("assistant", f"Response {i}")
    # Should have compressed but kept recent messages
    msgs = mem.get_messages()
    assert len(msgs) < 42
