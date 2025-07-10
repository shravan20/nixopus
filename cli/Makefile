.PHONY: help install install-dev test test-cov lint clean format check build publish dev run

help: 
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: 
	poetry install

install-dev: 
	poetry install --with dev --no-root

test: 
	poetry run pytest

test-cov: 
	poetry run pytest --cov=core --cov=utils --cov-report=term-missing --cov-report=html

test-watch: 
	poetry run pytest-watch

lint: 
	poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: 
	poetry run black .
	poetry run isort .

check: 
	$(MAKE) lint
	$(MAKE) test

clean: 
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: 
	poetry build

publish: 
	poetry publish

dev: 
	poetry shell

run: 
	poetry run nixopus
