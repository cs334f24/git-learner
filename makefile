.PHONY: all test server lint

all: lint test

server:
	uv run server.py

lint:
	@uv run ruff check

lint-fix:
	@uv run ruff check

test:
	@uv run pytest
