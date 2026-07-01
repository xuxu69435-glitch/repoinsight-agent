# Contributing

Thanks for helping improve RepoInsight Agent. Keep changes small, testable, and
within the existing safety boundaries.

## Development Setup

```bash
python -m pip install -e ".[dev]"
python -m repoinsight.cli version
```

Python 3.11 or newer is required.

## Run Checks

```bash
python -m ruff check . --no-cache
python -m pytest
python -m repoinsight.cli doctor --path .
python -m repoinsight.cli workflow "Analyze this project for open-source readiness" --path . --no-llm
```

## Issues

When opening an issue, include:

- Operating system and Python version.
- RepoInsight version from `python -m repoinsight.cli version`.
- The exact command you ran.
- Expected behavior and actual behavior.
- `doctor` output when relevant.

Do not paste real API keys, `.env` contents, private repository code, or other
secrets.

## Code Contributions

- Keep changes focused on one behavior or document set.
- Add or update tests when behavior changes.
- Preserve Windows compatibility.
- Keep `ask`, `workflow`, `profile`, `scan`, and `doctor` commands working.
- Do not introduce arbitrary shell execution.
- Do not add dependency installation commands to the whitelist without a clear
  security review.

## Files Not To Commit

Do not commit local or generated files such as:

- `.env`
- `reports/`
- `.pytest_cache/`
- `.ruff_cache/`
- `__pycache__/`
- `.venv/`
- local database or vector index files
