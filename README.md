# RepoInsight Agent

RepoInsight Agent is a local repository analysis Agent built on LangChain. Users
provide a local project path and an analysis goal. The Agent can inspect the
directory tree, search code, read key text files, and generate a Markdown report
under `project_root/reports`.

Current status: v0.3 LangChain Agent runtime with safe command execution and
Git analysis tools. LangGraph is not implemented yet.

## Current Features

- Typer CLI with Rich output.
- LangChain Agent runtime through `langchain.agents.create_agent`.
- OpenAI or OpenAI-compatible chat model configuration.
- Safe project path validation.
- Directory scanning with ignored dependency and build folders.
- UTF-8 text file reading with path containment checks.
- Code search through `rg` when available, with a Python fallback.
- Safe whitelist command execution for selected test, build, and Git commands.
- Git status, diff, and oneline log analysis tools.
- Markdown report writing under `project_root/reports`.
- Pydantic schemas for structured report data.
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
repoinsight ask "Analyze this project architecture" --path ./some-project
repoinsight ask "Run pytest and analyze failures" --path ./some-project
repoinsight ask "Analyze current git diff and write a code review report" --path ./some-project
repoinsight ask "Run pnpm build and analyze bundle warnings" --path ./some-project
```

You can also run the module directly:

```bash
python -m repoinsight.cli version
python -m repoinsight.cli scan --path .
python -m repoinsight.cli ask "Analyze this project architecture" --path .
python -m repoinsight.cli ask "Run pytest and analyze failures" --path .
python -m repoinsight.cli ask "Analyze current git diff and write a code review report" --path .
python -m repoinsight.cli ask "Run pnpm build and analyze bundle warnings" --path .
```

The `ask` command validates the project path, creates the LangChain Agent,
allows it to call repository tools, and prints the report directory, report path
when found, and a short answer preview.

## Current Capabilities

- Can read the project directory structure.
- Can read UTF-8 text files inside the selected project root.
- Can search code inside the selected project root.
- Can inspect Git status, diff, diff statistics, and oneline history.
- Can run selected safe test and build commands.
- Can analyze test, build, and Git output in Markdown reports.
- Can generate Markdown reports under `reports/*.md`.
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

The only write-capable Agent tool is `write_markdown_report`, which only writes
`.md` files under `project_root/reports`.

File listing and search ignore common dependency, cache, build, and IDE folders
such as `.git`, `node_modules`, `.venv`, `__pycache__`, `dist`, `build`,
`.next`, `.idea`, and `.vscode`.

## Roadmap

- v0.1: project skeleton, CLI, file tools, search tools, report tools.
- v0.2: LangChain Agent integration.
- v0.3: safe command execution and Git analysis tools.
- v0.4: project type detection.
- v0.5: structured output reports.
- v0.6: LangGraph workflow.
- v1.0: stable open-source release.
