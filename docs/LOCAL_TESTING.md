# Local Testing Guide

This document describes how to run all CI checks locally **before pushing to GitHub** to avoid failed CI runs.

## Prerequisites

1. **Python environment** with all development dependencies installed
2. **Required tools**:
   ```bash
   pip install ruff black mypy yamllint pytest pytest-cov pytest-asyncio
   ```

## Pre-Push Checklist

Run these commands in order. All must pass before pushing.

### 1. YAML Linting (Workflows)

Check all GitHub Actions workflow files:

```bash
yamllint .github/workflows/
```

**Expected output:**
- Warnings are OK (truthy values, line lengths)
- **NO ERRORS** allowed

**Common issues:**
- Trailing spaces: `sed -i 's/[[:space:]]*$//' .github/workflows/*.yml`
- Nested mappings: Ensure `permissions:`, `needs:`, etc. are on separate lines

---

### 2. Ruff Linting (Python Code)

Check Python code style and imports:

```bash
ruff check src/ tests/
```

**Auto-fix issues:**
```bash
ruff check --fix --unsafe-fixes src/ tests/
```

**Expected output:**
```
All checks passed!
```

**Common issues:**
- Import ordering: Auto-fixed by `--fix`
- Unused imports: Remove manually or let `--fix` handle it
- See `pyproject.toml` for configured ignore rules

---

### 3. Black Formatting (Python Code)

Check code formatting:

```bash
black --check src/ tests/
```

**Auto-fix issues:**
```bash
black src/ tests/
```

**Expected output:**
```
All done! ✨ 🍰 ✨
XX files would be left unchanged.
```

---

### 4. Type Checking (Optional - Non-blocking)

Check type hints:

```bash
mypy src/
```

**Note:** Type checking is `continue-on-error: true` in CI, so failures won't block merges.

**Expected output:**
- Errors are documented but won't prevent CI from passing
- Focus on fixing new errors you introduce

---

### 5. Unit Tests

Run tests locally with coverage:

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

**Quick test run (no coverage):**
```bash
pytest tests/ -q
```

**Expected output:**
```
====== X passed, Y warnings in Z.ZZs ======
```

**Common issues:**
- Import errors: Ensure `PYTHONPATH=src` is set
- Test failures: Fix failing tests before pushing
- Module not found: Check import paths use relative imports (`from utils.` not `from solveit_mcp_server.utils.`)

---

### 6. Docker Build Test

Verify Docker image builds successfully:

```bash
docker build -t test-image .
docker run --rm test-image python -c "import sys; print(f'Python {sys.version}')"
```

**Expected output:**
- Build completes without errors
- Python version prints successfully

---

## Complete Pre-Push Script

Create `scripts/pre-push-check.sh` with this content:

```bash
#!/bin/bash
set -e  # Exit on first error

echo "=== 1. YAML Linting ==="
yamllint .github/workflows/

echo "=== 2. Ruff Linting ==="
ruff check src/ tests/

echo "=== 3. Black Formatting ==="
black --check src/ tests/

echo "=== 4. Type Checking (non-blocking) ==="
mypy src/ || echo "⚠️  Type checking had errors (non-blocking)"

echo "=== 5. Unit Tests ==="
pytest tests/ -q

echo ""
echo "✅ All checks passed! Safe to push."
```

Make it executable and run:

```bash
chmod +x scripts/pre-push-check.sh
bash scripts/pre-push-check.sh
```

---

## Quick Fixes

### Auto-fix all linting issues:

```bash
# Fix import ordering and unused imports
ruff check --fix --unsafe-fixes src/ tests/

# Fix code formatting
black src/ tests/

# Remove trailing spaces from YAML files
sed -i 's/[[:space:]]*$//' .github/workflows/*.yml
```

### Verify all checks pass after fixes:

```bash
ruff check src/ tests/ && \
black --check src/ tests/ && \
echo "✅ Ready to commit and push"
```

---

## Common CI Failures and Local Testing

| CI Failure | Local Test Command | Fix |
|------------|-------------------|-----|
| YAML Linting | `yamllint .github/workflows/` | Remove trailing spaces, fix syntax |
| Ruff errors | `ruff check src/ tests/` | Run `ruff check --fix` |
| Black formatting | `black --check src/ tests/` | Run `black src/ tests/` |
| Import errors | `pytest tests/` | Fix import paths |
| Test failures | `pytest tests/ -v` | Debug failing tests |
| Docker build | `docker build -t test .` | Fix Dockerfile or dependencies |

---

## GitHub Actions Workflow Names (for reference)

- `CI - Code Quality & Tests` - Runs ruff, black, mypy, pytest
- `Docker - PR Validation` - Builds Docker image, runs security scans
- `Dependency Update Validation` - Tests dependency compatibility
- `CodeQL - Code Security Analysis` - SAST scanning
- `Security - Vulnerability Scanning` - Trivy, Bandit, secret scanning
- `License Compliance Check` - License validation

---

## Best Practices

1. **Always run local checks before pushing**
2. **Fix issues locally rather than in CI**
3. **Use `--fix` flags to auto-correct linting issues**
4. **Commit formatting fixes separately** from functional changes
5. **Use the pre-push check script** for consistency

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'config/tools/utils'"

**Solution:** Pytest is configured to automatically add `src/` to the Python path via `pyproject.toml`. If you still get import errors:

1. Ensure you're in the project root directory
2. Check that `pyproject.toml` contains `pythonpath = ["src"]` under `[tool.pytest.ini_options]`
3. Try running: `pytest tests/ --collect-only` to see if tests are discovered

### "yamllint: command not found"

**Solution:** Install yamllint:
```bash
pip install yamllint
```

### "Found 113 errors" from ruff

**Solution:** Run auto-fix:
```bash
ruff check --fix --unsafe-fixes src/ tests/
```

### Tests pass locally but fail in CI

**Possible causes:**
1. Different Python version (CI uses 3.11 and 3.12)
2. Uncommitted changes
3. Package installation differences
4. Missing dependencies

**Debug:**
```bash
# Check Python version
python --version

# Run tests exactly like CI
pytest tests/ -v --cov=src

# Check for uncommitted changes
git status
```

---

## Summary

**Minimum commands before every push:**

```bash
ruff check --fix src/ tests/
black src/ tests/
pytest tests/ -q
```

If all pass: **✅ Safe to push!**

If any fail: **❌ Fix issues first, then retry.**
