.PHONY: help install install-dev lint format test test-cov clean build run docker-build docker-run pre-commit requirements requirements-upgrade docs-serve docs-build

# Default target
help:
	@echo "Available commands:"
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make requirements   - Generate requirements.txt from pyproject.toml"
	@echo "  make requirements-upgrade - Upgrade all dependencies"
	@echo "  make lint           - Run all linters"
	@echo "  make format         - Format code with ruff and black"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make docs-serve     - Serve documentation locally"
	@echo "  make docs-build     - Build documentation"
	@echo "  make clean          - Clean build artifacts"
	@echo "  make build          - Build Docker image"
	@echo "  make run            - Run server locally"
	@echo "  make docker-run     - Run server in Docker"
	@echo "  make pre-commit     - Run pre-commit hooks"
	@echo "  make security       - Run security checks"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pre-commit

# Requirements management
requirements:
	pip-compile pyproject.toml -o requirements.txt --no-emit-index-url

requirements-upgrade:
	pip-compile --upgrade pyproject.toml -o requirements.txt --no-emit-index-url

# Documentation
docs-serve:
	mkdocs serve

docs-build:
	mkdocs build --strict

# Code quality
lint:
	@echo "Running ruff linter..."
	ruff check src/
	@echo "Running ruff format check..."
	ruff format --check src/
	@echo "Running mypy type checker..."
	mypy src/ --ignore-missing-imports

format:
	@echo "Formatting with ruff..."
	ruff check --fix src/
	ruff format src/
	@echo "Formatting with black..."
	black src/

# Testing
test:
	pytest tests/ --verbose

test-cov:
	pytest tests/ --verbose --cov=src --cov-report=term-missing --cov-report=html

# Security
security:
	@echo "Running bandit security scan..."
	bandit -r src/ -ll
	@echo "Running pip-audit..."
	pip-audit --requirement requirements.txt

# Docker
docker-build:
	podman build -t solve-it-mcp:local .

docker-run:
	podman run -it --rm \
		-p 8000:8000 \
		-e MCP_TRANSPORT=http \
		-e HTTP_PORT=8000 \
		solve-it-mcp:local

docker-test:
	podman build --platform linux/amd64 -t solve-it-mcp:test .
	podman run -d --name test-container -p 8000:8000 solve-it-mcp:test
	sleep 10
	curl -f http://localhost:8000/healthz
	podman stop test-container
	podman rm test-container

# Local development
run:
	python3 src/server.py --transport http

pre-commit:
	pre-commit run --all-files

# Clean
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# CI simulation (run all checks locally)
ci: clean lint test security
	@echo "All CI checks passed!"
