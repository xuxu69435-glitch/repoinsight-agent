# RepoInsight Agent

A LangChain + LangGraph powered local codebase analysis agent.

RepoInsight Agent analyzes a local repository from a validated project path. It
can inspect repository structure, detect the project profile, collect safe Git
and configuration evidence, and generate structured Markdown plus JSON reports
under `project_root/reports`.

Current status: v0.8.0 GitHub-ready release preparation.

## Core Features

- LangChain tool-calling agent
- LangGraph deterministic workflow
- Project profile detector
- Safe command execution with whitelist
- Git status / diff analysis
- Structured Markdown + JSON reports
- No-LLM workflow mode
- Optional LLM-enhanced workflow mode
- Doctor command for local diagnostics

## Quick Start

```bash
python -m pip install -e ".[dev]"
python -m repoinsight.cli version
python -m repoinsight.cli profile --path .
python -m repoinsight.cli workflow "Analyze this project for open-source readiness" --path . --no-llm
```

Python 3.11 or newer is required.

## API Key Configuration

Copy the example environment file when you want to use LLM-backed commands:

```bash
cp .env.example .env
```

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4.1-mini
```

- `ask` requires `OPENAI_API_KEY`.
- `workflow --with-llm` requires `OPENAI_API_KEY`.
- `workflow --no-llm` does not require an API key.
- `doctor` does not require an API key.

Do not commit real API keys.

## Command Examples

```bash
python -m repoinsight.cli version
python -m repoinsight.cli scan --path .
python -m repoinsight.cli profile --path .
python -m repoinsight.cli profile --path . --json
python -m repoinsight.cli doctor --path .
python -m repoinsight.cli workflow "Analyze this project" --path . --no-llm
python -m repoinsight.cli ask "Analyze this project architecture" --path .
```

`profile`, `doctor`, and `workflow --no-llm` are deterministic local commands.
They do not require `OPENAI_API_KEY`.

`ask` creates the LangChain Agent, lets it use the repository tools, and prints
the report directory plus returned Markdown/JSON report paths when available.

`workflow` runs the LangGraph workflow:

```text
Profile -> Plan -> Evidence -> Analyze -> Report
```

By default it uses `--no-llm`, does not call an LLM, and writes:

```text
reports/workflow_analysis_report.md
reports/workflow_analysis_report.json
```

With `--with-llm`, the workflow requires `OPENAI_API_KEY` and asks a tool-free
LLM analyzer to produce a structured `AnalysisReport` from the profile, plan,
and evidence already collected by the workflow.

## Safety Boundaries

- Agent tools can only access files inside the validated `project_root`.
- Command execution uses an explicit whitelist and `shell=False`.
- `git commit`, `git push`, `git reset`, and `git clean` are not allowed.
- `npm install`, `pnpm install`, and other install commands are not allowed.
- The only write location is `project_root/reports/`.
- LLM workflow analysis does not directly read files, execute commands, or write
  files.
- `doctor` reports whether an API key is configured, but never prints the key.

Allowed command families are limited to read-only Git inspection plus selected
test and build commands such as `python -m pytest`, `npm test`, `npm run build`,
`pnpm test`, and `yarn build`.

## Architecture

- CLI: Typer commands and Rich terminal output in `repoinsight/cli.py`.
- Tools: local file, search, report, command, and Git primitives.
- Analyzers: deterministic project profile detection.
- LangChain Agent: tool-calling agent for interactive repository questions.
- LangGraph Workflow: deterministic profile, plan, evidence, analyze, and report
  nodes.
- Reporting: Pydantic `AnalysisReport` rendered to Markdown and JSON.
- Safety Guards: project path containment, command whitelist, and report write
  checks.

## Example Output

The no-LLM workflow and LLM-enhanced workflow both write structured report
artifacts under the selected project root:

```text
reports/workflow_analysis_report.md
reports/workflow_analysis_report.json
```

A static sample report is available at `examples/reports/example_report.md`.

## Development Checks

```bash
python -m ruff check . --no-cache
python -m pytest
python -m repoinsight.cli version
python -m repoinsight.cli scan --path .
python -m repoinsight.cli profile --path . --json
python -m repoinsight.cli doctor --path .
python -m repoinsight.cli workflow "Analyze this project for open-source readiness" --path . --no-llm
```

## Project Documentation

- `docs/DESIGN.md`: implementation layers and runtime flow.
- `docs/TOOL_SAFETY.md`: safety model and command restrictions.
- `docs/RELEASE_CHECKLIST.md`: local and GitHub release checks.
- `CHANGELOG.md`: release history.
- `CONTRIBUTING.md`: contribution guide.
- `SECURITY.md`: vulnerability reporting and safety policy.

## Roadmap

- v0.8 GitHub-ready release
- v0.9 example gallery and more project detectors
- v1.0 stable CLI and packaged release

## License

MIT. See `LICENSE`.
