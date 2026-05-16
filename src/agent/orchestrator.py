"""ReAct-style agent loop."""
import json
from typing import List, Dict, Optional, Any
from pathlib import Path
from core.project import Project
from core.events import EventBus
from core.logger import Logger
from core.tokenizer import Tokenizer
from llm.base import BaseLLM, LLMResponse
from llm.router import LLMRouter
from rag.retriever import Retriever
from rag.context_builder import ContextBuilder
from tools.base import ToolRegistry
from tools.file_tools import register_file_tools
from tools.edit_tools import register_edit_tools
from tools.shell_tools import register_shell_tools
from tools.rag_tools import register_rag_tools
from agent.memory import Memory
from agent.state import AgentState
from agent.planner import Planner


def _debug(msg: str):
    with open(Path.home() / "agentic-tui-debug.log", "a") as f:
        f.write(f"{msg}\n")


class Orchestrator:
    def __init__(
        self,
        project: Project,
        llm_router: LLMRouter,
        retriever: Retriever,
        context_builder: ContextBuilder,
        event_bus: EventBus,
        logger: Logger,
        tokenizer: Tokenizer,
        max_iterations: int = 15,
    ):
        self.project = project
        self.router = llm_router
        self.retriever = retriever
        self.ctx_builder = context_builder
        self.events = event_bus
        self.logger = logger
        self.tokenizer = tokenizer
        self.max_iterations = max_iterations

        self.tools = ToolRegistry()
        register_file_tools(self.tools, project)
        register_edit_tools(self.tools, project)
        register_shell_tools(self.tools, project)
        register_rag_tools(self.tools, retriever)

        self.memory = Memory(tokenizer)
        self.state = AgentState()
        self.planner: Optional[Planner] = None

    def set_planner_llm(self, llm: BaseLLM):
        self.planner = Planner(llm)
    
    def get_pending_edits(self) -> List[Dict]:
        return [
            {
                "index": i,
                "file_path": e.file_path,
                "approved": e.approved,
                "applied": e.applied,
                "preview_old": e.old_string[:200],
                "preview_new": e.new_string[:200],
            }
            for i, e in enumerate(self.state.pending_edits)
        ]

    async def run(self, user_input: str, provider: Optional[str] = None, model: Optional[str] = None) -> str:
        _debug(f"[Orchestrator] run() called with: {user_input[:50]}")
        self.state.reset()
        self.memory.clear()

        _debug("[Orchestrator] getting LLM from router...")
        llm = self.router.get(provider, model)
        _debug(f"[Orchestrator] got LLM: {llm.model_id()}")

        if self.planner:
            _debug("[Orchestrator] running planner...")
            try:
                plan = await self.planner.plan(user_input)
                self.state.plan = plan
                await self.events.publish("agent:plan", {"plan": plan})
                _debug(f"[Orchestrator] plan done: {len(plan)} steps")
            except Exception as e:
                _debug(f"[Orchestrator] planner failed: {e}")

        _debug("[Orchestrator] doing RAG search...")
        rag_context = ""
        try:
            chunks = await self.retriever.search(user_input, top_k=8)
            _debug(f"[Orchestrator] RAG found {len(chunks)} chunks")
            if not chunks:
                rag_context = "(No indexed codebase context found. Run /idx to index the project.)"
            else:
                rag_context = self.ctx_builder.build(chunks)
            _debug(f"[Orchestrator] RAG context built: {len(rag_context)} chars")
        except Exception as e:
            _debug(f"[Orchestrator] RAG failed: {e}")
            import traceback
            with open(Path.home() / "agentic-tui-debug.log", "a") as f:
                traceback.print_exc(file=f)
            rag_context = f"(RAG unavailable: {e})"

        system_msg = (
            "You are an expert software engineering agent.\n"
            "Rules:\n"
            "1. Before editing, read files.\n"
            "2. Use semantic_search to find relevant code when the user mentions concepts.\n"
            "3. Use exact string matching for find_replace.\n"
            "4. Validate your changes mentally before submitting.\n"
            "5. If ambiguous, ask clarifying questions.\n"
            "6. Always provide a text response explaining what you did or found.\n"
            "7. If you use tools, summarize the results in your final response.\n"
        )
        if rag_context:
            system_msg += f"\nRelevant codebase context:\n{rag_context}\n"

        self.memory.add("system", system_msg)
        self.memory.add("user", user_input)
        _debug(f"[Orchestrator] memory has {len(self.memory.get_messages())} messages")

        final_answer = ""
        tool_results_summary = []
        
        for i in range(self.max_iterations):
            _debug(f"[Orchestrator] iteration {i+1}/{self.max_iterations}")
            self.state.iteration_count = i + 1
            await self.events.publish("agent:iteration_start", {"iteration": i + 1})

            tool_defs = self.tools.get_definitions()
            _debug(f"[Orchestrator] calling LLM with {len(tool_defs)} tools, {len(self.memory.get_messages())} messages...")

            try:
                resp = await llm.chat(self.memory.get_messages(), tools=tool_defs, temperature=0.2)
            except Exception as e:
                _debug(f"[Orchestrator] LLM call failed: {e}")
                import traceback
                with open(Path.home() / "agentic-tui-debug.log", "a") as f:
                    traceback.print_exc(file=f)
                return f"LLM error: {e}"

            content = (resp.content or "").strip()
            _debug(f"[Orchestrator] LLM responded: content={content[:100]}, tools={len(resp.tool_calls)}")

            self.logger.log("llm_response", {
                "iteration": i + 1,
                "content": resp.content,
                "tool_calls": resp.tool_calls,
                "usage": resp.usage,
            })

            if content:
                final_answer = content
                await self.events.publish("agent:stream", {"content": content})

            if not resp.tool_calls:
                _debug("[Orchestrator] no tool calls, breaking")
                break

            self.memory.add("assistant", content, tool_calls=resp.tool_calls)

            for tc in resp.tool_calls:
                name = tc["function"]["name"]
                args = tc["function"]["arguments"]
                tool_id = tc["id"]

                _debug(f"[Orchestrator] executing tool: {name}")
                await self.events.publish("agent:tool_call", {"name": name, "arguments": args})

                result = await self.tools.execute(name, args)
                result_str = str(result)
                _debug(f"[Orchestrator] tool result: {result_str[:100]}")
                self.logger.log("tool_result", {"name": name, "result": result_str[:2000]})
                tool_results_summary.append(f"{name}: {result_str[:200]}")
                self.memory.add("tool", result_str, tool_call_id=tool_id)

                if name == "find_replace":
                    try:
                        a = json.loads(args) if isinstance(args, str) else args
                        from agent.state import PendingEdit
                        self.state.add_edit(PendingEdit(a["path"], a["old_string"], a["new_string"]))
                    except Exception as e:
                        _debug(f"[Orchestrator] edit queue failed: {e}")

                await self.events.publish("agent:tool_result", {"name": name, "result": result_str[:500]})

        _debug(f"[Orchestrator] loop ended. final_answer='{final_answer[:50]}', tool_results_summary has {len(tool_results_summary)} items")
        
        if not final_answer.strip() and tool_results_summary:
            _debug("[Orchestrator] no final answer, asking model to summarize tool results")
            self.memory.add("user", "Please summarize what you found and provide a helpful response based on the tool results above.")
            try:
                resp = await llm.chat(self.memory.get_messages(), tools=None, temperature=0.2)
                final_answer = (resp.content or "").strip() or "I completed the requested actions but have no summary to provide."
                _debug(f"[Orchestrator] fallback LLM returned: {final_answer[:100] if final_answer else 'EMPTY'}")
            except Exception as e:
                _debug(f"[Orchestrator] fallback LLM failed: {e}")
                final_answer = "Here is what I found:\n\n" + "\n".join(tool_results_summary)
                _debug(f"[Orchestrator] synthesized fallback: {final_answer[:100]}")

        self.memory.add("assistant", final_answer or "Done.")
        _debug(f"[Orchestrator] returning: {final_answer[:100] if final_answer else 'Done.'}")
        return final_answer or "No response generated."

    async def approve_and_apply(self, edit_index: int):
        if edit_index < 0 or edit_index >= len(self.state.pending_edits):
            return "Invalid edit index"
        edit = self.state.pending_edits[edit_index]
        if edit.approved or edit.applied:
            return "Already approved/applied"
        edit.approved = True
        try:
            self.project.write_file(
                edit.file_path,
                self.project.read_file(edit.file_path).replace(edit.old_string, edit.new_string, 1),
            )
            edit.applied = True
            return f"Applied edit to {edit.file_path}"
        except Exception as e:
            return f"Error applying edit: {e}"

    def get_pending_edits(self) -> List[Dict]:
        return [
            {
                "index": i,
                "file_path": e.file_path,
                "approved": e.approved,
                "applied": e.applied,
                "preview_old": e.old_string[:200],
                "preview_new": e.new_string[:200],
            }
            for i, e in enumerate(self.state.pending_edits)
        ]