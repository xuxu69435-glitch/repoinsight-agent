# RepoInsight Agent

RepoInsight Agent is a local repository analysis Agent built on LangChain. Users
provide a local project path and an analysis goal. The Agent can inspect the
directory tree, search code, read key text files, and generate Markdown and JSON
reports under `project_root/reports`.

Current status: v0.5 LangChain Agent runtime with structured reports, Project
Detector, safe command execution, and Git analysis tools. LangGraph is not
implemented yet.

## Current Features

- Typer CLI with Rich output.
- LangChain Agent runtime through `langchain.agents.create_agent`.
- OpenAI or OpenAI-compatible chat model configuration.
- Deterministic project profile detection without an API key.
- Python, Node.js, React, Vue, Vite, Next.js, TypeScript, and JavaScript hints.
- Parsing for `package.json`, `pyproject.toml`, and `requirements.txt`.
- Entry point, package manager, script, dependency, and config file detection.
- Safe project path validation.
- Directory scanning with ignored dependency and build folders.
- UTF-8 text file reading with path containment checks.
- Code search through `rg` when available, with a Python fallback.
- Safe whitelist command execution for selected test, build, and Git commands.
- Git status, diff, and oneline log analysis tools.
- Structured analysis reports backed by a Pydantic `AnalysisReport` schema.
- Markdown and JSON report writing under `project_root/reports`.
- JSON reports for UI integration, regression testing, and evaluation.
- Pytest coverage for the basic tools and Agent wiring.

## Installation

```bash
python -m pip install -e ".[dev]"
```

Python 3.11 or newer is required.

## Configuration

Copy the example environment file and fill in your API key:

```bash
cp .env.example .env
```

Required:

```text
OPENAI_API_KEY=your_api_key_here
```

Optional:

```text
OPENAI_BASE_URL=
OPENAI_MODEL=gpt-4.1-mini
```

Set `OPENAI_BASE_URL` when using an OpenAI-compatible provider such as DeepSeek
or another compatible service. Do not commit real API keys.

## CLI Examples

```bash
repoinsight version
repoinsight scan --path ./some-project
repoinsight profile --path ./some-project
repoinsight profile --path ./some-project --json
repoinsight ask "Analyze this project architecture" --path ./some-project
repoinsight ask "Analyze this project and generate a structured report" --path ./some-project
repoinsight ask "Run pytest and analyze failures" --path ./some-project
repoinsight ask "Analyze current git diff and write a code review report" --path ./some-project
repoinsight ask "Run pnpm build and analyze bundle warnings" --path ./some-project
```

You can also run the module directly:

```bash
python -m repoinsight.cli version
python -m repoinsight.cli scan --path .
python -m repoinsight.cli profile --path .
python -m repoinsight.cli profile --path . --json
python -m repoinsight.cli ask "Analyze this project architecture" --path .
python -m repoinsight.cli ask "Analyze this project and generate a structured report" --path .
python -m repoinsight.cli ask "Run pytest and analyze failures" --path .
python -m repoinsight.cli ask "Analyze current git diff and write a code review report" --path .
python -m repoinsight.cli ask "Run pnpm build and analyze bundle warnings" --path .
```

The `ask` command validates the project path, creates the LangChain Agent,
allows it to call repository tools, and prints the report directory, generated
Markdown/JSON report paths when returned, and a short answer preview.

The `profile` command does not require `OPENAI_API_KEY`. It does not call an LLM,
run commands, or write reports.

## Current Capabilities

- Can read the project directory structure.
- Can read UTF-8 text files inside the selected project root.
- Can search code inside the selected project root.
- Can inspect Git status, diff, diff statistics, and oneline history.
- Can run selected safe test and build commands.
- Can analyze test, build, and Git output in Markdown reports.
- Can detect project profile without an API key.
- Can identify likely entry points, scripts, package managers, dependencies, and
  key config files.
- Can generate paired Markdown and JSON reports from one structured schema.
- Can generate Markdown reports under `reports/*.md` for compatibility.
- Does not run arbitrary shell commands.
- Does not install dependencies.
- Does not modify source files.

## Tool Safety

RepoInsight tools only access files inside the validated `project_root`. The
Agent never receives an absolute `project_root` argument; tools are bound to the
selected root in Python closures. Path guards reject traversal attempts such as
`../secret.txt`.

The Agent can only execute explicit whitelist commands through `shell=False`.
Allowed commands are:

- `git status`
- `git diff`
- `git diff --stat`
- `git log --oneline`
- `pytest`
- `python -m pytest`
- `npm test`
- `npm run test`
- `npm run build`
- `pnpm test`
- `pnpm run test`
- `pnpm build`
- `pnpm run build`
- `yarn test`
- `yarn build`

Dangerous commands and shell syntax are rejected, including `rm`, `del`,
`rmdir`, `format`, `curl`, `wget`, `powershell`, `bash`, `sh`, `cmd`, `chmod`,
`chown`, `sudo`, `git commit`, `git push`, `git reset`, `git clean`, and
package installation commands such as `npm install` or `pnpm install`.

The only write-capable Agent tools are report writers. `write_markdown_report`
only writes `.md` files under `project_root/reports`; the structured report tool
writes paired `.md` and `.json` files under the same directory. Source files are
never modified by RepoInsight tools.

File listing and search ignore common dependency, cache, build, and IDE folders
such as `.git`, `node_modules`, `.venv`, `__pycache__`, `dist`, `build`,
`.next`, `.idea`, and `.vscode`.

Project profile detection reads only limited-size configuration files and checks
entry point existence with bounded depth. It does not execute commands, call an
LLM, or modify files.

Structured reports are generated from the same `AnalysisReport` object. The
Markdown renderer is for humans; the JSON writer is for later Web UI work,
regression tests, and Agent evaluation.

## Roadmap

- v0.1: project skeleton, CLI, file tools, search tools, report tools.
- v0.2: LangChain Agent integration.
- v0.3: safe command execution and Git analysis tools.
- v0.4: Project Detector and repository profile.
- v0.5: Structured Markdown + JSON reports.
- v0.6: LangGraph workflow.
- v1.0: stable open-source release.
