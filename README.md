# MeetingMuse

Your favourite calendar bot 🗓️

A smart meeting scheduling assistant built with LangGraph and LangChain, designed to help you manage your calendar through natural conversation.

![compressed](https://github.com/user-attachments/assets/a6e6bd9a-3f5e-4383-b4f5-81dc87c5ccc4)



## Requirements

- Python >= 3.13
- Poetry (for dependency management)

## Installation

### 1. Install Poetry

First, install Poetry if you haven't already:

```bash
# On macOS/Linux
brew install pipx && pipx install poetry

# On Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd meetingmuse

# Install dependencies using Poetry
poetry install

# Activate the virtual environment
poetry env activate
```

### 3. Environment Configuration

Create your environment file:

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API tokens
# HUGGINGFACE_API_TOKEN=your_token_here
```

## Development

### Available Make Commands

This project includes a comprehensive Makefile for development workflow:

```bash
# Install dependencies
make install

# Install with development dependencies
make dev-install

# Run tests
make test

# Run tests with coverage
make test-coverage

# Code formatting and linting
make format
make lint
make type-check

# Run all quality checks
make quality

# Clean build artifacts
make clean
```

### Start the webserver

```shell
poetry run python -m src.main
```

### Running the Application

```bash
# Using Poetry
poetry run python src/main.py

# Or if you're in the Poetry shell
python src/main.py
```

### Development Workflow

1. **Setup**: `make dev-install`
2. **Code**: Make your changes
3. **Test**: `make test`
4. **Quality**: `make quality`
5. **Commit**: Your changes are ready!

## Architecture

MeetingMuse is built using:

- **LangGraph** (0.5.1+): For building stateful, multi-actor applications with LLMs
- **LangChain HuggingFace** (0.3.0+): For LLM integration with HuggingFace models
- **LangChain Core** (0.3.68+): Core LangChain functionality
- **Python-dotenv** (0.9.9+): Environment variable management

### Key Components

- **State Management**: TypedDict-based conversation state
- **Intent Classification**: AI-powered user intent recognition
- **Conversation Routing**: Smart conversation flow management
- **Node-based Architecture**: Modular conversation handling


## Testing

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration
```

### Testing Nodes in isolation

Each node can be tested in isolation.
sample script can be found in `tests/scripts/run_node_with_graph.py`

```python
    # this method draws the graph - if you want to visualize the graph,
    draw_graph()
    # use this method, change NodeName value to test different node.
    # NOTE: make sure that the new node is added and helper method is
    test_single_node(NodeName.COLLECTING_INFO, "I want to schedule a meeting with John Doe on 2025-08-01 at 10:00 AM for 1 hour")
```

to test the chatbot in full, use the run_node_
run using `poetry run python tests/scripts/run_chatbot.py`

use
```bash
poetry run python tests/scripts/run_node_with_graph.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run quality checks: `make quality`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request


## Author

- **thisisasl** - arjunslife@gmail.com

## License

This project is currently unlicensed.
