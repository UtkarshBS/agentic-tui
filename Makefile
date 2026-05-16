.PHONY: install sync test lint format run

install:
	uv tool install .

sync:
	uv sync --all-extras

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src tests
	uv run mypy src

format:
	uv run ruff format src tests

run:
	./run.sh .
