# MeetingMuse

Your favourite calendar bot 🗓️

A smart meeting scheduling assistant built with LangGraph and LangChain, designed to help you manage your calendar through natural conversation.

## Requirements

- Python >= 3.13
- Poetry (for dependency management)

## Installation

### 1. Install Poetry

First, install Poetry if you haven't already:

```bash
# On macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

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
poetry shell
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
- **Dependency Injection**: Clean, testable architecture

## Project Structure

```
meetingmuse/
├── src/meetingmuse/
│   ├── config/          # Configuration management
│   ├── models/          # State and data models
│   ├── nodes/           # LangGraph conversation nodes
│   ├── services/        # Business logic services
│   ├── utils/           # Utility functions (logging, etc.)
│   └── prompts/         # LLM prompts
├── tests/               # Test suite
└── docs/                # Documentation
```

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