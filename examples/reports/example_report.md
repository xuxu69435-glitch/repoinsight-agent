# Example RepoInsight Report

## Summary

This is a static example report showing the shape of a RepoInsight workflow
Markdown report. Real workflow runs also write a paired JSON report.

## Findings

- The project profile identifies languages, frameworks, entry points, package
  managers, and key configuration files.
- Git evidence can include status, diff statistics, and recent history without
  mutating the repository.
- Reports should include evidence file paths whenever possible.

## Recommendations

- Run `python -m repoinsight.cli doctor --path .` before a release.
- Use `workflow --no-llm` when an API key is not available.
- Review generated Markdown and JSON reports under `reports/`.
