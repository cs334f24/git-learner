.PHONY: all test server

all: test

server:
	uv run server.py

test:
	@uv run pytest
