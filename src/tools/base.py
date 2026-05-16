"""Tool decorator and registry."""
import json
import inspect
from typing import Callable, Dict, Any, List
from dataclasses import dataclass


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDef] = {}

    def register(self, fn: Callable = None, *, name: str = None, description: str = None):
        def decorator(f):
            nonlocal name, description
            n = name or f.__name__
            desc = description or (f.__doc__ or "").strip()
            sig = inspect.signature(f)
            props: Dict[str, Any] = {}
            required: List[str] = []
            for pname, param in sig.parameters.items():
                if pname in ("self", "cls"):
                    continue
                pschema: Dict[str, Any] = {"type": "string"}
                if param.default is not inspect.Parameter.empty:
                    pschema["default"] = param.default
                else:
                    required.append(pname)
                props[pname] = pschema
            schema = {"type": "object", "properties": props, "required": required}
            self._tools[n] = ToolDef(n, desc, schema, f)
            return f
        if fn is not None:
            return decorator(fn)
        return decorator

    def get_definitions(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
            }
            for t in self._tools.values()
        ]

    async def execute(self, name: str, arguments: str) -> Any:
        tool = self._tools.get(name)
        if not tool:
            return f"Error: tool '{name}' not found"
        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError:
            return f"Error: invalid JSON arguments for {name}"
        try:
            if inspect.iscoroutinefunction(tool.handler):
                return await tool.handler(**args)
            return tool.handler(**args)
        except Exception as e:
            return f"Error executing {name}: {e}"

    def list(self) -> List[str]:
        return list(self._tools.keys())
