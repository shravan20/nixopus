.PHONY: help setup install install-dev test test-cov lint clean format check build publish dev run nixopus

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup Python environment using Poetry (create if doesn't exist, activate if exists)
	@echo "Setting up Python environment using Poetry..."
	@if command -v poetry >/dev/null 2>&1; then \
		poetry install --with dev; \
		echo "Environment setup complete!"; \
		echo "To activate the environment, run: poetry shell"; \
		echo "To run nixopus locally, use: make nixopus <command>"; \
	else \
		echo "Poetry not found. Please install Poetry first:"; \
		echo "curl -sSL https://install.python-poetry.org | python3 -"; \
		exit 1; \
	fi

install: ## Install dependencies
	poetry install

install-dev: ## Install development dependencies
	poetry install --with dev --no-root

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=core --cov=utils --cov-report=term-missing --cov-report=html

test-watch: ## Run tests in watch mode
	poetry run pytest-watch

lint: ## Run linting
	poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code with black and isort
	poetry run black .
	poetry run isort .

check: ## Run linting and tests
	$(MAKE) lint
	$(MAKE) test

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	poetry build

publish: ## Publish to PyPI
	poetry publish

dev: ## Activate development shell
	poetry shell

run: ## Run nixopus CLI (same as 'make nixopus')
	poetry run nixopus

nixopus: ## Run nixopus CLI with arguments (usage: make nixopus ARGS="command options")
	@if [ -z "$(ARGS)" ]; then \
		echo "Running nixopus with --help:"; \
		poetry run nixopus --help; \
	else \
		echo "Running nixopus $(ARGS)"; \
		poetry run nixopus $(ARGS); \
	fi

# Convenience targets for common nixopus commands
nixopus-conflict: ## Run nixopus conflict command
	poetry run nixopus conflict $(ARGS)

nixopus-preflight: ## Run nixopus preflight command
	poetry run nixopus preflight $(ARGS)

nixopus-install: ## Run nixopus install command
	poetry run nixopus install $(ARGS)

nixopus-service: ## Run nixopus service command
	poetry run nixopus service $(ARGS)

nixopus-version: ## Show nixopus version
	poetry run nixopus version
