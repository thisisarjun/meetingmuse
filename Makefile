.PHONY: help install dev-install test test-verbose test-coverage clean lint format type-check run run-server build docs poetry-install poetry-update poetry-shell

# Colors for output
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
MAGENTA := \033[35m
CYAN := \033[36m
WHITE := \033[37m
BOLD := \033[1m
RESET := \033[0m

# Default target
help:
	@echo ""
	@echo "$(BOLD)$(BLUE)MeetingMuse - Your favourite calendar bot!$(RESET)"
	@echo "$(CYAN)================================================$(RESET)"
	@echo ""
	@echo "$(BOLD)$(GREEN)Poetry & Environment:$(RESET)"
	@echo "  $(YELLOW)install$(RESET)         - Install dependencies with Poetry"
	@echo "  $(YELLOW)dev-install$(RESET)     - Install development dependencies"
	@echo "  $(YELLOW)shell$(RESET)           - Activate Poetry virtual environment"
	@echo "  $(YELLOW)update$(RESET)          - Update dependencies"
	@echo ""
	@echo "$(BOLD)$(GREEN)Testing:$(RESET)"
	@echo "  $(YELLOW)test$(RESET)            - Run tests with pytest"
	@echo "  $(YELLOW)test-verbose$(RESET)    - Run tests with verbose output"
	@echo "  $(YELLOW)test-coverage$(RESET)   - Run tests with coverage report"
	@echo ""
	@echo "$(BOLD)$(GREEN)Code Quality:$(RESET)"
	@echo "  $(YELLOW)lint$(RESET)            - Run linting checks (flake8, pylint)"
	@echo "  $(YELLOW)format$(RESET)          - Format code (black, isort)"
	@echo "  $(YELLOW)type-check$(RESET)      - Run type checking with mypy"
	@echo ""
	@echo "$(BOLD)$(GREEN)Running & Building:$(RESET)"
	@echo "  $(YELLOW)run$(RESET)             - Run the MeetingMuse CLI"
	@echo "  $(YELLOW)run-server$(RESET)      - Run the WebSocket server locally"
	@echo "  $(YELLOW)build$(RESET)           - Build the package with Poetry"
	@echo ""
	@echo "$(BOLD)$(GREEN)Maintenance:$(RESET)"
	@echo "  $(YELLOW)clean$(RESET)           - Clean up build artifacts and cache"
	@echo "  $(YELLOW)docs$(RESET)            - Generate documentation"
	@echo "  $(YELLOW)build-graph$(RESET)     - Generate graph visualization"
	@echo ""
	@echo "$(BOLD)$(GREEN)Quick Commands:$(RESET)"
	@echo "  $(YELLOW)qa$(RESET)              - Run format + lint + test"
	@echo "  $(YELLOW)dev-setup$(RESET)       - Complete development setup"
	@echo "  $(YELLOW)ci-test$(RESET)         - Run CI pipeline (coverage + lint + type-check)"
	@echo ""
	@echo "$(BOLD)$(GREEN)Debug & Development:$(RESET)"
	@echo "  $(YELLOW)debug-node$(RESET)      - Run node debugging script"
	@echo "    $(CYAN)make debug-node NODE_NAME=COLLECTING_INFO MESSAGE=\"I want to schedule a meeting\"$(RESET)"
	@echo "    $(CYAN)make debug-node NODE_NAME=HUMAN_SCHEDULE_MEETING_MORE_INFO MESSAGE=\"Schedule meeting\" INTERRUPT=1$(RESET)"
	@echo "  $(YELLOW)debug-chatbot$(RESET)   - Run chatbot debugging script"
	@echo "    $(CYAN)make debug-chatbot$(RESET) - Interactive chatbot session for testing"
	@echo ""
	@echo "$(BOLD)$(GREEN)Information:$(RESET)"
	@echo "  $(YELLOW)info$(RESET)            - Show project information"
	@echo "  $(YELLOW)poetry-show$(RESET)     - Show installed packages"
	@echo "  $(YELLOW)poetry-env-info$(RESET) - Show environment info"
	@echo ""
	@echo "$(BOLD)$(MAGENTA)Examples:$(RESET)"
	@echo "  $(CYAN)make dev-setup$(RESET)   # Set up development environment"
	@echo "  $(CYAN)make qa$(RESET)          # Quick development cycle"
	@echo "  $(CYAN)make run$(RESET)         # Start the application"
	@echo ""
	@echo "$(CYAN)================================================$(RESET)"

# Poetry dependency management
install:
	poetry install

dev-install:
	poetry install --with dev

update:
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
	# Remove unused imports and variables
	poetry run autoflake --remove-all-unused-imports --remove-unused-variables --in-place --recursive src/ tests/
	# Fix trailing whitespace and end-of-file issues
	poetry run pre-commit run trailing-whitespace --all-files
	poetry run pre-commit run end-of-file-fixer --all-files
	# Format code
	poetry run black src/ tests/
	poetry run isort src/ tests/

type-check:
	poetry run mypy src/meetingmuse/ src/server/

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

# Run WebSocket server locally
run-server:
	poetry run python -m src.meetingmuse_server.main

# Build with Poetry
build: clean
	poetry build

# Documentation & Graph generation
build-graph:
	poetry run python scripts/generate_graph.py
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
qa: format lint test


# debug scripts - make help for more info

debug-node:
	poetry run python scripts/run_node_with_graph.py --node $(NODE_NAME) --message "$(MESSAGE)" $(if $(INTERRUPT),--interrupt)

debug-chatbot:
	poetry run python scripts/run_chatbot.py

# Poetry-specific commands
poetry-check:
	poetry check

poetry-show:
	poetry show

poetry-env-info:
	poetry env info

# Show project info
info:
	@echo ""
	@echo "$(BOLD)$(BLUE)📊 MeetingMuse Project Information$(RESET)"
	@echo "$(CYAN)=====================================$(RESET)"
	@echo "$(BOLD)Poetry version:$(RESET) $(shell poetry --version)"
	@echo "$(BOLD)Python version:$(RESET) $(shell poetry run python --version)"
	@echo "$(BOLD)Virtual environment:$(RESET) $(shell poetry env info --path)"
	@echo ""
	@echo "$(BOLD)$(GREEN)📁 Project structure:$(RESET)"
	@find src/ -name "*.py" | head -10
	@echo ""

# Export requirements (for compatibility)
requirements:
	poetry export -f requirements.txt --output requirements.txt --without-hashes
	poetry export -f requirements.txt --output requirements-dev.txt --with dev --without-hashes
