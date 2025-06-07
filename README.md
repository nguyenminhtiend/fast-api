# FastAPI Microservices

A scalable microservices architecture using FastAPI with modern Python packaging.

## 🚀 Quick Start

### Installation

```bash
# Install project in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Running the Server

```bash
# Method 1: Direct uvicorn
uvicorn app.main:app --reload --port 8000

# Method 2: Using run script
python run.py
```

### Available Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## 🛠️ Development

### Project Structure

```
fast-api/
├── app/
│   ├── main.py              # FastAPI application
│   └── core/
│       └── config.py        # Configuration settings
├── pyproject.toml          # Project dependencies and tool config
├── run.py                  # Development server runner
└── README.md
```

### Code Quality Tools

All tools are configured in `pyproject.toml`:

- **ruff** - Fast Python linter
- **black** - Code formatter
- **mypy** - Static type checker
- **pytest** - Testing framework

### Running Tools

```bash
# Install dev dependencies first
pip install -e ".[dev]"

# Format code
black .

# Lint code
ruff check .

# Type check
mypy app/

# Run tests (when available)
pytest
```

## 📚 Next Steps

1. Add database integration (PostgreSQL + SQLAlchemy)
2. Implement authentication system
3. Add more microservices
4. Set up containerization with Docker
5. Configure CI/CD pipeline
