.PHONY: help install dev-install test test-verbose test-coverage clean lint format type-check run build docs poetry-install poetry-update poetry-shell

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies with Poetry"
	@echo "  dev-install  - Install development dependencies with Poetry"
	@echo "  poetry-install - Install all dependencies (same as install)"
	@echo "  poetry-update - Update dependencies"
	@echo "  poetry-shell - Activate Poetry virtual environment"
	@echo "  test         - Run tests with pytest"
	@echo "  test-verbose - Run tests with verbose output"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black and isort"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  clean        - Clean up build artifacts and cache"
	@echo "  run          - Run the MeetingMuse CLI"
	@echo "  build        - Build the package with Poetry"
	@echo "  docs         - Generate documentation"

# Poetry dependency management
install:
	poetry install

dev-install:
	poetry install --with dev

poetry-install: install

poetry-update:
	poetry update

poetry-env:
	poetry env activate

# Testing with Poetry
test:
	poetry run pytest tests/ -v --tb=short

test-verbose:
	poetry run pytest tests/ -v --tb=long -s

test-coverage:
	poetry run pytest tests/ --cov=src/meetingmuse --cov-report=html --cov-report=term-missing

# Code quality with Poetry
lint:
	poetry run flake8 src/ tests/
	poetry run pylint src/meetingmuse/

format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

type-check:
	poetry run mypy src/meetingmuse/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .venv/

# Run application with Poetry
run:
	poetry run python src/main.py

# Build with Poetry
build: clean
	poetry build

# Documentation (if using sphinx)
docs:
	@echo "Documentation generation not yet configured"
	@echo "Run: poetry add --group dev sphinx sphinx-rtd-theme"

# Development workflow
dev-setup: dev-install
	cp .env.example .env
	@echo "Development environment set up with Poetry!"
	@echo "Please edit .env with your actual values"
	@echo "Run 'make poetry-shell' to activate the virtual environment"

# CI/CD helpers
ci-test: test-coverage lint type-check

# Quick development cycle
dev: format lint test

# Poetry-specific commands
poetry-check:
	poetry check

poetry-show:
	poetry show

poetry-env-info:
	poetry env info

# Show project info
info:
	@echo "MeetingMuse - Your favourite calendar bot!"
	@echo "Poetry version: $(shell poetry --version)"
	@echo "Python version: $(shell poetry run python --version)"
	@echo "Virtual environment: $(shell poetry env info --path)"
	@echo "Project structure:"
	@find src/ -name "*.py" | head -10

# Export requirements (for compatibility)
requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes
	poetry export -f requirements.txt --output requirements-dev.txt --with dev --without-hashes 
