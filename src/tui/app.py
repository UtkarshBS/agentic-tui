"""Main Textual application."""
import os
import asyncio
from pathlib import Path
from textual.app import App
from core.project import Project
from core.events import EventBus
from core.logger import Logger
from core.tokenizer import Tokenizer
from llm.router import LLMRouter
from rag.vector_store import VectorStore
from rag.chunker import Chunker
from rag.embedder import NomicEmbedder
from rag.retriever import Retriever
from rag.context_builder import ContextBuilder
from rag.indexer import Indexer
from agent.orchestrator import Orchestrator
from tui.screens.main_screen import MainScreen
from tui.screens.config_screen import ConfigScreen
from tui.screens.indexer_screen import IndexerScreen
from tui.screens.diff_modal import DiffModal


def _debug(msg: str):
    with open(Path.home() / "agentic-tui-debug.log", "a") as f:
        f.write(f"{msg}\n")


class AgenticTUI(App):
    CSS_PATH = "css/layout.tcss"

    SCREENS = {
        "config": ConfigScreen,
        "indexer": IndexerScreen,
    }

    def __init__(self, project_root: str = "."):
        self.project = Project.from_path(Path(project_root).resolve())
        self.events = EventBus()
        self.logger = Logger(self.project.root / "data" / "cache" / "logs")
        self.tokenizer = Tokenizer()

        # RAG
        store_path = self.project.root / "data" / "vector_store" / "embeddings.sqlite"
        self.vector_store = VectorStore(store_path)
        self.chunker = Chunker(chunk_size=1500, overlap=150)
        self.embedder = NomicEmbedder()
        self.retriever = Retriever(self.vector_store, self.embedder)
        self.context_builder = ContextBuilder(max_chars=32000)

        # LLM
        self.llm_router = LLMRouter(default_provider=os.getenv("DEFAULT_PROVIDER", "kimi"))

        # Agent
        self.orchestrator = Orchestrator(
            project=self.project,
            llm_router=self.llm_router,
            retriever=self.retriever,
            context_builder=self.context_builder,
            event_bus=self.events,
            logger=self.logger,
            tokenizer=self.tokenizer,
            max_iterations=15,
        )
        planner_llm = self.llm_router.get()
        self.orchestrator.set_planner_llm(planner_llm)

        # Indexer
        self.indexer = Indexer(self.project, self.vector_store, self.chunker, self.embedder)

        # Wire events
        self.events.subscribe("agent:stream", self._on_agent_stream)
        self.events.subscribe("agent:tool_call", self._on_tool_call)
        self.events.subscribe("agent:tool_result", self._on_tool_result)
        self.events.subscribe("agent:plan", self._on_agent_plan)

        super().__init__()

    async def on_mount(self):
        main = MainScreen(self.project.root)
        self.push_screen(main)

    async def on_main_screen_user_message(self, event: MainScreen.UserMessage):
        _debug(f"[App] received UserMessage: {event.text[:50]}")
        # Get the active screen (which is MainScreen) and cast it
        main = self.screen
        await self._handle_user_message(main, event.text)

    async def _handle_user_message(self, main: MainScreen, text: str):
        _debug(f"[App] _handle_user_message START: {text[:50]}")
        _debug("[App] got main screen")
        main.add_chat_user(text)
        _debug("[App] added user message")
        
        provider = os.getenv("DEFAULT_PROVIDER", "kimi")
        model = os.getenv("LMSTUDIO_MODEL", "default")
        main.add_chat_system(f"[debug] Using provider: {provider}, model: {model}")
        main.set_status(model=f"{provider}/{model}", index="thinking")
        _debug("[App] status set")

        _debug("[App] about to call orchestrator.run()")
        try:
            response = await self.orchestrator.run(text)
            _debug(f"[App] orchestrator returned: {response[:100] if response else 'None'}")
            main.add_chat_assistant(response)

            edits = self.orchestrator.get_pending_edits()
            for edit in edits:
                if not edit["approved"]:
                    main.add_chat_system(f"Pending edit in {edit['file_path']}")

        except Exception as e:
            _debug(f"[App] ERROR: {e}")
            import traceback
            with open(Path.home() / "agentic-tui-debug.log", "a") as f:
                traceback.print_exc(file=f)
            main.add_chat_assistant(f"Error: {str(e)}")
            self.logger.log("error", {"message": str(e)})

        _debug("[App] setting status to idle")
        main.set_status(index="idle")

    def _on_agent_stream(self, payload):
        def update():
            try:
                main = self.screen
                main.add_chat_assistant(payload.get("content", ""))
            except Exception as e:
                _debug(f"[App] Stream update error: {e}")
        self.call_from_thread(update)

    def _on_tool_call(self, payload):
        def update():
            try:
                main = self.screen
                main.add_tool_call(payload.get("name", "?"), payload.get("arguments", ""))
            except Exception as e:
                _debug(f"[App] Tool call update error: {e}")
        self.call_from_thread(update)

    def _on_tool_result(self, payload):
        def update():
            try:
                main = self.screen
                main.add_chat_tool(payload.get("name", "?"), payload.get("result", ""))
            except Exception as e:
                _debug(f"[App] Tool result update error: {e}")
        self.call_from_thread(update)

    def _on_agent_plan(self, payload):
        def update():
            try:
                main = self.screen
                plan = payload.get("plan", [])
                main.add_chat_system(f"Plan: {len(plan)} steps")
            except Exception as e:
                _debug(f"[App] Plan update error: {e}")
        self.call_from_thread(update)

    def on_indexer_screen_start_index(self, event: IndexerScreen.StartIndex):
        asyncio.create_task(self._run_index())

    async def _run_index(self):
        screen = self.query_one(IndexerScreen)
        screen.set_progress(0, 100)
        
        def on_progress(current, total):
            screen.set_progress(current, total)
        
        # Create new indexer with progress callback
        from rag.indexer import Indexer
        indexer = Indexer(self.project, self.vector_store, self.chunker, self.embedder, progress_callback=on_progress)
        
        try:
            await indexer.full_index()
            self.retriever._rebuild_bm25()
            screen.finish()
            main = self.query_one(MainScreen)
            main.set_status(index="ready")
        except Exception as e:
            screen.query_one("#indexer-label").update(f"Error: {e}")
            import traceback
            with open(Path.home() / "agentic-tui-debug.log", "a") as f:
                traceback.print_exc(file=f)

    def action_approve_edit(self, index: int):
        asyncio.create_task(self._approve_edit(index))

    async def _approve_edit(self, index: int):
        result = await self.orchestrator.approve_and_apply(index)
        main = self.screen
        main.add_chat_system(result)

    def action_show_diff(self, edit_index: int):
        edits = self.orchestrator.get_pending_edits()
        if 0 <= edit_index < len(edits):
            e = edits[edit_index]
            self.push_screen(DiffModal(
                e["file_path"],
                e["preview_old"],
                e["preview_new"],
                edit_index,
            ))

    def on_diff_modal_dismiss(self, result):
        if result and result.get("action") == "approve":
            asyncio.create_task(self._approve_edit(result["index"]))


def main():
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    app = AgenticTUI(root)
    app.run()


if __name__ == "__main__":
    main()