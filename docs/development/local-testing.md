# Local Testing Guide

Run all CI checks locally before pushing to avoid failed CI runs.

## Prerequisites

```bash
pip install ruff black mypy yamllint pytest pytest-cov pytest-asyncio
```

Or install the full dev extras:

```bash
pip install -e ".[dev]"
```

## Pre-Push Checklist

Run these commands in order. All must pass before pushing.

### 1. YAML Linting

```bash
yamllint .github/workflows/
```

No errors allowed. Warnings about truthy values and line lengths are acceptable.

**Fix trailing spaces:**

```bash
sed -i 's/[[:space:]]*$//' .github/workflows/*.yml
```

---

### 2. Python Linting

```bash
ruff check src/ tests/
```

**Auto-fix:**

```bash
ruff check --fix --unsafe-fixes src/ tests/
```

---

### 3. Code Formatting

```bash
black --check src/ tests/
```

**Auto-fix:**

```bash
black src/ tests/
```

---

### 4. Type Checking (non-blocking)

```bash
mypy src/
```

Type checking is `continue-on-error: true` in CI — failures won't block merges, but you should fix errors you introduce.

---

### 5. Unit Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

Quick run without coverage:

```bash
pytest tests/ -q
```

---

### 6. Docker Build

```bash
docker build -t test-image .
docker run --rm test-image python -c "import sys; print(sys.version)"
```

---

## Pre-Push Script

```bash
#!/bin/bash
set -e

echo "=== 1. YAML Linting ==="
yamllint .github/workflows/

echo "=== 2. Ruff ==="
ruff check src/ tests/

echo "=== 3. Black ==="
black --check src/ tests/

echo "=== 4. Type Checking (non-blocking) ==="
mypy src/ || echo "Type checking had errors (non-blocking)"

echo "=== 5. Unit Tests ==="
pytest tests/ -q

echo ""
echo "All checks passed. Safe to push."
```

Save as `scripts/pre-push-check.sh`, make it executable, and run before every push:

```bash
chmod +x scripts/pre-push-check.sh
bash scripts/pre-push-check.sh
```

---

## Minimum Commands Before Every Push

```bash
ruff check --fix src/ tests/
black src/ tests/
pytest tests/ -q
```

---

## Common CI Failures

| CI Failure | Local Command | Fix |
|---|---|---|
| YAML linting | `yamllint .github/workflows/` | Remove trailing spaces, fix syntax |
| Ruff errors | `ruff check src/ tests/` | `ruff check --fix` |
| Black formatting | `black --check src/ tests/` | `black src/ tests/` |
| Import errors | `pytest tests/` | Verify `PYTHONPATH=src` |
| Test failures | `pytest tests/ -v` | Debug failing tests |
| Docker build | `docker build -t test .` | Fix Dockerfile or dependencies |

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'config'`

Pytest is configured to add `src/` to the Python path via `pyproject.toml`. If you still see this:

```bash
# Run from the project root
cd /path/to/solve-it-mcp

# Verify pyproject.toml has:
# [tool.pytest.ini_options]
# pythonpath = ["src"]

pytest tests/ --collect-only
```

### Tests Pass Locally But Fail in CI

Common causes:

- Python version mismatch — CI uses Python 3.12
- Uncommitted changes
- Missing environment variables

```bash
python --version
pytest tests/ -v --cov=src
git status
```

---

## GitHub Actions Workflow Names

- `CI - Code Quality & Tests` — ruff, black, mypy, pytest
- `Security - Vulnerability Scanning` — Trivy, Bandit, secret scanning
- `Docker - PR Validation` — builds Docker image, runs health checks
