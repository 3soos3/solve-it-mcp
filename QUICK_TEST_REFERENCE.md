# Quick Testing Reference Card

## Before Every Push - Run This:

```bash
bash scripts/pre-push-check.sh
```

---

## Manual Quick Checks (3 commands):

```bash
# 1. Fix linting
ruff check --fix src/ tests/
black src/ tests/

# 2. Run tests
PYTHONPATH=src pytest tests/ -q

# 3. Check YAML (if you modified workflows)
yamllint .github/workflows/
```

---

## Fix Common Issues:

| Issue | Fix |
|-------|-----|
| Import ordering | `ruff check --fix src/ tests/` |
| Code formatting | `black src/ tests/` |
| Trailing spaces in YAML | `sed -i 's/[[:space:]]*$//' .github/workflows/*.yml` |
| Test import errors | Add `PYTHONPATH=src` before pytest |

---

## Full Documentation:

See `docs/LOCAL_TESTING.md` for complete guide.

---

## Golden Rule:

**If it doesn't pass locally, it won't pass in CI.**

Don't push until all checks are green! ✅
