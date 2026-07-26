.PHONY: install setup-db test dev clean help

help:
	@echo "Available targets:"
	@echo "  install    - Create virtual environment and install dependencies"
	@echo "  setup-db   - Prepare data directory for SQLite database"
	@echo "  test       - Run pytest"
	@echo "  dev        - Full setup: install + setup-db + test"
	@echo "  clean      - Remove .venv and __pycache__ directories"

install:
	python3 -m venv .venv
	.venv/bin/pip install -e ".[dev]"

setup-db:
	mkdir -p data

test:
	.venv/bin/pytest

dev: install setup-db test

clean:
	rm -rf .venv
	find . -type d -name __pycache__ -exec rm -rf {} +
