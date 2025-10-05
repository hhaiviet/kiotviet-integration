.PHONY: help install dev-install test lint format clean run

help:
	@echo "Available commands:"
	@echo "  install       Install production dependencies"
	@echo "  dev-install   Install development dependencies"  
	@echo "  test          Run tests"
	@echo "  lint          Run linters"
	@echo "  format        Format code"
	@echo "  clean         Clean temporary files"
	@echo "  run           Run the application"

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	ruff check src/
	mypy src/
	black --check src/ tests/

format:
	black src/ tests/
	ruff check --fix src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .coverage htmlcov/ dist/ build/

run:
	python -m src.cli.main
