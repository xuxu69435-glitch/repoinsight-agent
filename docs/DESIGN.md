# Design

RepoInsight Agent is split into small layers so local tools can be tested
directly before they are exposed to the LangChain Agent runtime.

## CLI Layer

The CLI lives in `repoinsight/cli.py`. It uses Typer for commands and Rich for
readable terminal output.

Current commands:

- `version`: prints the package version.
- `scan`: validates a project path and displays a basic directory tree.
- `profile`: validates a project path and prints a deterministic project
  profile as a Rich table or JSON.
- `workflow`: runs the LangGraph workflow mode and writes structured Markdown
  and JSON reports without requiring an API key in default no-LLM mode.
- `ask`: validates a project path, creates the Agent, invokes it, and prints the
  report location plus a short answer preview.

## Tools Layer

The tools live in `repoinsight/tools`.

- `file_tools.py`: lists files and reads safe UTF-8 text files.
- `search_tools.py`: searches code with `rg` first and Python fallback second.
- `report_tools.py`: writes Markdown reports under `project_root/reports`.
- `command_tools.py`: runs whitelist commands with `shell=False`.
- `git_tools.py`: wraps Git status, diff, and oneline log inspection.
- `report_tools.py`: also exposes structured report writing that creates paired
  Markdown and JSON reports from one schema.

These functions are plain Python functions so they can be tested directly and
then wrapped as LangChain tools.

## Analyzers Layer

The analyzers live in `repoinsight/analyzers`.

- `project_detector.py`: builds a deterministic repository profile before Agent
  reasoning. It parses limited-size manifest files such as `package.json`,
  `pyproject.toml`, and `requirements.txt`, checks bounded-depth entry point
  existence, and returns project types, languages, frameworks, scripts,
  dependencies, package managers, entry points, config files, evidence files,
  confidence, and notes.

The Project Detector does not call an LLM, execute commands, or modify files.

## Reporting Layer

The reporting layer lives in `repoinsight/reporting`.

- `repoinsight/agent/schemas.py`: defines the Pydantic `AnalysisReport` schema,
  including project summary, findings, recommendations, evidence, limitations,
  and next steps.
- `markdown_renderer.py`: renders an `AnalysisReport` as readable Markdown.
- `json_writer.py`: writes an `AnalysisReport` as UTF-8 JSON under
  `project_root/reports`.
- `write_structured_report`: tool helper that writes both
  `reports/<base>.md` and `reports/<base>.json` from one validated report.

Structured JSON reports are intended for later Web UI integration, regression
testing, and Agent evaluation. Markdown reports remain the human-readable
output.

## Workflow Layer

The workflow layer lives in `repoinsight/workflow`.

- `state.py`: defines `RepoInsightState`, including project root, task, profile,
  plan, evidence, report paths, warnings, and errors.
- `nodes.py`: implements the workflow nodes.
- `graph.py`: builds and runs the LangGraph `StateGraph`.
- `prompts.py`: reserves prompt text for future mockable LLM workflow analysis.

The v0.6 graph is:

```text
START -> profile -> plan -> evidence -> analyze -> report -> END
```

The nodes are:

- `profile_node`: deterministic project profile.
- `plan_node`: deterministic analysis plan.
- `evidence_node`: project profile, Git status/diff-stat, and key config evidence.
- `analyze_node`: deterministic `AnalysisReport` generation in no-LLM mode.
- `report_node`: writes `workflow_analysis_report.md` and
  `workflow_analysis_report.json`.

Workflow mode is separate from the existing `ask` Agent mode. It is more
observable and testable, and defaults to deterministic `--no-llm` execution.

## Agent Layer

The Agent layer lives in `repoinsight/agent`.

`build_agent()` creates a LangChain Agent with `langchain.agents.create_agent`,
`ChatOpenAI`, the analyzer/file/search/report/command/Git tools, and the system
prompt from `prompts.py`.

`agent/tools.py` wraps the plain Python tools as LangChain tools. The selected
project root is bound in Python closures, so the Agent cannot supply or alter
the root path.

## Utils Layer

The utilities live in `repoinsight/utils`.

- `path_guard.py`: resolves project paths and ensures file targets stay inside
  the selected project root.
- `command_guard.py`: rejects shell syntax, dangerous commands, installs, and
  Git mutation commands before subprocess execution.
- `logger.py`: provides a shared Rich console helper.

## LangChain Integration

The LangChain Agent:

1. Validate the project path through `resolve_project_path`.
2. Call `detect_project_profile` to get a deterministic repository profile.
3. Call `list_files` when it needs more detailed repository structure.
4. Call `search_code` and `read_file` to gather evidence.
5. Optionally call Git inspection or whitelist command tools when the task needs
   test, build, or Git evidence.
6. Produce an `AnalysisReport` model.
7. Prefer `write_structured_analysis_report` to write both Markdown and JSON.
8. Fall back to `write_report` only when structured report writing fails.

The LangGraph workflow follows the same safety boundaries but controls the
analysis steps explicitly instead of letting the Agent choose tool calls.
