#!/usr/bin/env bash
set -e
PROJECT_ROOT="${1:-.}"
cd "$(dirname "$0")"
uv run agentic-tui "$PROJECT_ROOT"
