"""RAG search tool exposed to agent."""
from rag.retriever import Retriever
from tools.base import ToolRegistry


def register_rag_tools(registry: ToolRegistry, retriever: Retriever):
    @registry.register(description="Semantic search over the codebase.")
    async def semantic_search(query: str, top_k: int = 8) -> str:
        try:
            results = await retriever.search(query, top_k=top_k)
            lines = []
            for r in results:
                lines.append(f"\n--- {r['file_path']} (lines {r['start_line']}-{r['end_line']}) [{r.get('chunk_type','?')}] ---")
                lines.append(r["content"])
            return "\n".join(lines) if lines else "No relevant code found."
        except Exception as e:
            return f"Error: {e}"
