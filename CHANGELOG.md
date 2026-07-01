# Changelog

## v0.8.0

- Prepared the project for GitHub release with complete English and Chinese
  README files.
- Added GitHub Actions CI for linting, tests, and no-LLM CLI smoke checks.
- Added contribution, security, release checklist, issue template, and resume
  summary documentation.
- Kept the release focused on packaging and documentation readiness without
  adding new Agent, RAG, or vector database features.

## v0.7.1

- Stabilized local diagnostics with the `doctor` command.
- Added report directory and default workflow report file writability checks.
- Documented Ruff and pytest cache troubleshooting.

## v0.7.0

- Added a mockable LLM workflow analyzer.
- Supported optional `workflow --with-llm` mode while keeping `--no-llm` as the
  deterministic default.

## v0.6.0

- Added the LangGraph workflow runtime.
- Implemented profile, plan, evidence, analyze, and report nodes.

## v0.5.0

- Added structured reports backed by a Pydantic `AnalysisReport` schema.
- Wrote paired Markdown and JSON report outputs.

## v0.4.0

- Added Project Detector for deterministic repository profile detection.
- Detected languages, frameworks, package managers, entry points, scripts, and
  key config files.

## v0.3.0

- Added safe command execution with an explicit whitelist.
- Added Git status, diff, diff-stat, and oneline log analysis tools.

## v0.2.0

- Added LangChain Agent runtime wiring.
- Exposed local repository tools to the Agent through tool wrappers.

## v0.1.0

- Created the project skeleton.
- Added initial CLI, file tools, search tools, and report writing primitives.
