# Release Checklist

Use this checklist before publishing a GitHub release.

## Local Checks

```bash
python -m ruff check . --no-cache
python -m pytest
python -m repoinsight.cli version
python -m repoinsight.cli scan --path .
python -m repoinsight.cli profile --path . --json
python -m repoinsight.cli doctor --path .
python -m repoinsight.cli workflow "Analyze this project for open-source readiness" --path . --no-llm
```

## Git Checks

```bash
git status --short
```

Confirm these files and directories are not included in the commit:

- `.env`
- `reports/`
- `.pytest_cache/`
- `.ruff_cache/`
- `__pycache__/`
- `.venv/`
- local database, vector index, or cache files

## GitHub Checks

- README is complete.
- `README.zh-CN.md` is aligned with the English README.
- `LICENSE` exists.
- GitHub Actions CI exists.
- `CHANGELOG.md` is updated.
- `SECURITY.md` exists.
- `CONTRIBUTING.md` exists.
- Issue templates exist.
- No real API keys or local generated reports are tracked.
