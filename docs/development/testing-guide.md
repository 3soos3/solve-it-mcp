# Testing Guide

Quick reference for running tests and quality checks.

## Minimum Before Every Push

```bash
ruff check --fix src/ tests/
black src/ tests/
pytest tests/ -q
```

If all pass: safe to push.

---

## Full Check Suite

```bash
# 1. YAML linting (if you modified workflows)
yamllint .github/workflows/

# 2. Python linting and formatting
ruff check src/ tests/
black --check src/ tests/

# 3. Tests
pytest tests/ -v --cov=src --cov-report=term-missing
```

Or use the pre-push script:

```bash
bash scripts/pre-push-check.sh
```

---

## Auto-Fix Common Issues

```bash
# Fix import ordering and style
ruff check --fix --unsafe-fixes src/ tests/

# Fix code formatting
black src/ tests/

# Remove trailing spaces from YAML files
sed -i 's/[[:space:]]*$//' .github/workflows/*.yml
```

---

## Fix Reference

| Issue | Fix Command |
|---|---|
| Import ordering | `ruff check --fix src/ tests/` |
| Code formatting | `black src/ tests/` |
| Trailing spaces in YAML | `sed -i 's/[[:space:]]*$//' .github/workflows/*.yml` |
| Test import errors | Verify `PYTHONPATH=src` (set in `pyproject.toml`) |

---

## Full Documentation

See [Local Testing Guide](local-testing.md) for the complete guide, including the pre-push script and troubleshooting tips.
