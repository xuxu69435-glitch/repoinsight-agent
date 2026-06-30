# Design

RepoInsight Agent is split into small layers so local tools can be tested
directly before they are exposed to the LangChain Agent runtime.

## CLI Layer

The CLI lives in `repoinsight/cli.py`. It uses Typer for commands and Rich for
readable terminal output.

Current commands:

- `version`: prints the package version.
- `scan`: validates a project path and displays a basic directory tree.
- `ask`: validates a project path, creates the Agent, invokes it, and prints the
  report location plus a short answer preview.

## Tools Layer

The tools live in `repoinsight/tools`.

- `file_tools.py`: lists files and reads safe UTF-8 text files.
- `search_tools.py`: searches code with `rg` first and Python fallback second.
- `report_tools.py`: writes Markdown reports under `project_root/reports`.
- `command_tools.py`: runs whitelist commands with `shell=False`.
- `git_tools.py`: wraps Git status, diff, and oneline log inspection.

These functions are plain Python functions so they can be tested directly and
then wrapped as LangChain tools.

## Agent Layer

The Agent layer lives in `repoinsight/agent`.

`build_agent()` creates a LangChain Agent with `langchain.agents.create_agent`,
`ChatOpenAI`, the file/search/report/command/Git tools, and the system prompt
from `prompts.py`.

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
2. Call `list_files` to inspect repository structure.
3. Call `search_code` and `read_file` to gather evidence.
4. Optionally call Git inspection or whitelist command tools when the task needs
   test, build, or Git evidence.
5. Produce an `AnalysisReport` model.
6. Write the final Markdown report with `write_report`.
