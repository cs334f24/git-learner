.PHONY: all test server lint

DEPLOY_BIND := 127.0.0.1:8081
DEPLOY_WORKERS := 3

all: lint test

server:
	uv run server.py

lint:
	@uv run ruff check

lint-fix:
	@uv run ruff check

test:
	@uv run pytest

deploy:
	uv run --no-dev gunicorn \
	--daemon --bind $(DEPLOY_BIND) \
	--workers $(DEPLOY_WORKERS) \
	--log-syslog \
	-p /tmp/BingoMaker.pid \
	"app:create_app()"
