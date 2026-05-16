"""Intent decomposition into tool-call DAG."""
import json
from typing import List, Dict
from llm.base import BaseLLM


class Planner:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def plan(self, user_intent: str, context: str = "") -> List[Dict]:
        prompt = (
            "You are a planning module. Break the following user request into a step-by-step plan.\n"
            "Each step should specify a tool call with reasoning.\n"
            "Available tools: read_file, list_dir, grep, glob, semantic_search, find_replace, run_command, git_status, git_diff\n"
            "Output ONLY a JSON array with no markdown formatting.\n\n"
            f"User request: {user_intent}\n"
            f"Context:\n{context}\n"
        )
        messages = [
            {"role": "system", "content": "You output valid JSON arrays only."},
            {"role": "user", "content": prompt},
        ]
        resp = await self.llm.chat(messages, temperature=0.1)
        try:
            raw = resp.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```", 2)[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            plan = json.loads(raw.strip())
            if isinstance(plan, dict) and "steps" in plan:
                plan = plan["steps"]
            return plan if isinstance(plan, list) else []
        except Exception:
            return []
