.PHONY: all test server

all: test

server:
	uv run app/app.py

test:
	@uv run pytest
