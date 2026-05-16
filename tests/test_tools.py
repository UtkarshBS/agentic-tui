"""Tests for tool registry."""
import pytest
from tools.base import ToolRegistry


def test_tool_registration():
    reg = ToolRegistry()

    @reg.register(description="Add two numbers")
    def add(a: str, b: str) -> str:
        return str(int(a) + int(b))

    defs = reg.get_definitions()
    assert len(defs) == 1
    assert defs[0]["function"]["name"] == "add"


@pytest.mark.asyncio
async def test_tool_execution():
    reg = ToolRegistry()

    @reg.register()
    def greet(name: str) -> str:
        return f"Hello {name}"

    result = await reg.execute("greet", '{"name": "world"}')
    assert result == "Hello world"
