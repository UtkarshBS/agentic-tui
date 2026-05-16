# Agentic TUI

A terminal UI for agentic code editing with RAG (Retrieval-Augmented Generation). Built with [Textual](https://textual.textualize.io/) and supports Kimi, Claude, GPT-4o, and local models via LMStudio/Ollama.

## Features

- **Multi-provider LLM routing** — Kimi, Anthropic, OpenAI, LMStudio, Ollama, Mock
- **RAG over your codebase** — Ollama embeddings (nomic-embed-text) + hybrid dense/sparse retrieval
- **Agentic ReAct loop** — plans, searches, reads, edits, validates
- **Interactive diff approval** — preview every change before it hits disk
- **Incremental indexing** — re-indexes only changed files

## Quick Start

```bash
# 1. Install
pip install -e .

# 2. Set provider (pick one)
export DEFAULT_PROVIDER=kimi      # Cloud, best for agents
export DEFAULT_PROVIDER=lmstudio  # Local, set LMSTUDIO_BASE_URL
export DEFAULT_PROVIDER=ollama    # Local, set OLLAMA_BASE_URL

# 3. For RAG embeddings (local, no API key needed)
ollama pull nomic-embed-text

# 4. Launch inside a repo
cd ~/my-project
agentic-tui .
```

or use the launcher

```bash
./run.sh ~/your-project
```

## Controls

| Key      | Action                 |
| -------- | ---------------------- |
| `Ctrl+S` | Submit message         |
| `Ctrl+J` | Newline in input       |
| `/idx`   | Index codebase for RAG |
| `/cfg`   | Open config screen     |
| `/quit`  | Exit                   |
| `Esc`    | Back from modal/screen |


## Architecture

agentic_tui/
├── config/          # Prompts, provider YAML, settings
├── src/
│   ├── tui/         # Textual screens & widgets
│   ├── agent/       # ReAct orchestrator, memory, planner
│   ├── llm/         # Provider adapters (Kimi, Claude, GPT, LMStudio, Ollama)
│   ├── rag/         # Ollama/Nomic embedder, chunker, vector store, retriever
│   ├── tools/       # File, edit, shell, RAG tools exposed to LLM
│   └── core/        # Project, events, tokenizer, logger
└── data/            # SQLite vector store + LLM response cache

## RAG Flow
- Chunker splits code by AST nodes (functions/classes) with overlap
- OllamaEmbedder generates vectors locally via nomic-embed-text
- VectorStore persists in SQLite with numpy cosine search
- Retriever fuses dense (embedding) + sparse (BM25) via RRF
- ContextBuilder assembles top-k chunks into the LLM prompt

## Provider Setup

| Provider  | Env Vars                              | Notes                                |
| --------- | ------------------------------------- | ------------------------------------ |
| Kimi      | `KIMI_API_KEY`                        | Best agent performance, 200k context |
| Anthropic | `ANTHROPIC_API_KEY`                   | Claude 3.5 Sonnet                    |
| OpenAI    | `OPENAI_API_KEY`                      | GPT-4o                               |
| LMStudio  | `LMSTUDIO_BASE_URL`, `LMSTUDIO_MODEL` | Local, qwen recommended              |
| Ollama    | `OLLAMA_BASE_URL`                     | Local, for chat models               |
| Mock      | none                                  | For testing                          |

## Troubleshooting

- Empty responses: Model may put answers in reasoning_content. Use non-thinking models or cloud providers.
- Timeout: Increase timeout in LMStudio adapter or use smaller context windows.
- Indexing stuck: Check that Ollama is running (ollama list) and nomic-embed-text is pulled.
