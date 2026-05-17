# Pre-PR Checklist

Run all steps from the project root before pushing or opening a PR.

```bash
# 1. Format (auto-fix)
conda run -n solve-it ruff format src/

# 2. Lint (auto-fix)
conda run -n solve-it ruff check --fix src/

# 3. Verify clean
conda run -n solve-it ruff format --check src/
conda run -n solve-it ruff check src/

# 4. Unit tests
conda run -n solve-it pytest tests/unit/ -v -m "not integration"

# 5. Docs (catches broken links)
conda run -n solve-it mkdocs build --strict
```

All five must pass before pushing.
