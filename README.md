# Agentic TUI

A terminal UI for agentic code editing with RAG (Retrieval-Augmented Generation). Built with [Textual](https://textual.textualize.io/) and supports Kimi, Claude, GPT-4o, and local models via Ollama.

## Features

- **Multi-provider LLM routing** -- Kimi, Anthropic, OpenAI, Ollama
- **RAG over your codebase** -- Nomic embeddings + hybrid dense/sparse retrieval
- **Agentic ReAct loop** -- plans, searches, reads, edits, validates
- **Interactive diff approval** -- preview every change before it hits disk
- **Incremental indexing** -- watches git state, re-indexes only changed files

## Quick Start

<```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API keys (or edit .env)
export KIMI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."

# 3. Launch inside a repo
cd ~/my-project
python -m agentic_tui
<```

Or use the launcher from anywhere:

<```bash
./run.sh ~/my-project
<```

## Controls

| Key | Action |
|-----|--------|
| `Ctrl+S` | Submit message |
| `Ctrl+J` | Newline in input |
| `/idx` | Open indexer screen |
| `/cfg` | Open config screen |
| `/quit` | Exit |
| `Esc` | Back from modal/screen |

## Architecture

<```
agentic_tui/
\├── config/          # Prompts, provider YAML, settings
\├── src/
\│   ├── tui/         # Textual screens & widgets
\│   ├── agent/       # ReAct orchestrator, memory, planner
\│   ├── llm/         # Provider adapters (Kimi, Claude, GPT, Ollama)
\│   ├── rag/         # Nomic embedder, chunker, vector store, retriever
\│   ├── tools/       # File, edit, shell, RAG tools exposed to LLM
\│   └── core/        # Project, events, tokenizer, logger
\└── data/            # SQLite vector store + LLM response cache
<```

## RAG Flow

1. **Chunker** splits code by AST nodes (functions/classes) with overlap
2. **NomicEmbedder** generates vectors (local fallback if no API key)
3. **VectorStore** persists in SQLite with numpy cosine search
4. **Retriever** fuses dense (embedding) + sparse (BM25) via RRF
5. **ContextBuilder** assembles top-k chunks into the LLM prompt

This keeps token usage low while giving the agent full codebase awareness.
