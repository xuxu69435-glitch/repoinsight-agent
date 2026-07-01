# Tool Safety

RepoInsight reads local repositories, so filesystem boundaries must be explicit.
The user chooses one `project_root`; tools must not read arbitrary files outside
that root.

## Why Restrict File Access

Repository analysis often happens near private configuration, credentials,
local notes, dependency caches, and unrelated projects. Path traversal checks
prevent accidental or malicious access to files outside the selected project.

## Current File Boundary

Current tools resolve the project root to an absolute directory and verify that
target files remain inside it. Attempts to read paths such as `../secret.txt`
raise a clear `PermissionError`.

Directory listing and search ignore sensitive or noisy folders such as `.git`,
`node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build`, `.next`,
`.idea`, and `.vscode`.

## Project Profile Safety

The `profile` CLI command and `detect_project_profile` Agent tool are
deterministic analyzers. They do not execute shell commands, do not call an LLM,
do not write reports, and do not modify source files.

The detector reads only limited-size configuration files such as `package.json`,
`pyproject.toml`, and `requirements.txt`. It checks common entry point paths by
existence and uses bounded-depth scanning for filenames such as `cli.py` and
`main.py`. It skips dependency, cache, build, and VCS directories.

## Structured Report Safety

Structured reports are the only new write path in v0.5. They can only write
paired Markdown and JSON files under `project_root/reports`. The JSON report is
validated against the Pydantic `AnalysisReport` schema before it is written.

Report filenames are restricted to simple `.md` or `.json` names with English
letters, digits, underscores, and hyphens. Path traversal such as
`../report.json` is rejected. Structured report writing does not modify source
files.

`project_root/reports` is the only generated report write location. Report
writers do not fall back to paths outside the selected project root. If
`reports/` or the target report file is not writable, RepoInsight reports a
clear permission error instead of silently swallowing the failure.

## Doctor Safety

The `doctor` CLI command only checks local environment and project directory
readiness. It can create a missing `reports/` directory, but it does not delete
files, modify source files, run builds, call an LLM, or read sensitive file
contents.

`doctor` checks whether `.env` exists without printing its contents. It reports
whether `OPENAI_API_KEY` is configured as yes/no and never prints the API key
value.

## Workflow Safety

The `workflow` CLI command defaults to `--no-llm`, so it does not require
`OPENAI_API_KEY`. In v0.7, `--with-llm` requires `OPENAI_API_KEY`; if the key is
missing, the CLI exits with a clear error instead of pretending that LLM
analysis succeeded.

Workflow mode does not run build commands or tests. It only collects project
profile data, Git status/diff-stat evidence through the safe Git tools, and
limited key configuration file excerpts. It does not modify source files.

The workflow LLM analyzer does not receive tools and does not directly access
the filesystem. It cannot execute commands, read additional files, or write
files. It only receives the profile, plan, and evidence already collected by the
workflow, and must return an `AnalysisReport` JSON object.

The only workflow write step is `report_node`, which writes
`reports/workflow_analysis_report.md` and
`reports/workflow_analysis_report.json`.

## Why Arbitrary Shell Commands Are Not Allowed

Arbitrary shell access can delete files, move source code, leak local data,
install untrusted dependencies, or execute scripts that were not reviewed.
RepoInsight therefore does not pass commands through a shell and does not accept
shell syntax such as pipes, redirects, command chaining, or command substitution.

Command execution uses `subprocess.run(..., shell=False)` after validating the
command string against an explicit allowlist.

## Allowed Commands

v0.3 allows only these commands:

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

These commands are enough for repository status checks, code review reports,
test failure analysis, and build output analysis.

## Rejected Commands

RepoInsight rejects dangerous commands and shell entrypoints such as `rm`, `del`,
`rmdir`, `format`, `curl`, `wget`, `bash`, `sh`, `powershell`, `cmd`, `chmod`,
`chown`, and `sudo`.

It also rejects shell control syntax including `;`, `&&`, `||`, `|`, `>`, `>>`,
`<`, backticks, and `$()`.

## Why Git Mutations Are Rejected

RepoInsight can inspect Git state, but it must not mutate it. Commands such as
`git commit`, `git push`, `git reset`, `git checkout`, and `git clean` can alter
history, lose local work, publish private code, or make the working tree harder
to reason about. v0.3 therefore allows only status, diff, diff statistics, and
oneline log inspection.

## Why Installs Are Rejected

Install commands such as `npm install`, `pnpm install`, and `yarn install` can
download and execute dependency lifecycle scripts, rewrite lockfiles, and change
the local project. v0.3 allows test and build commands only when they exactly
match the whitelist.

## Output Truncation

Command stdout and stderr are each capped at 20,000 characters. When output is
longer, RepoInsight returns the truncated text and sets `stdout_truncated` or
`stderr_truncated` to `true`. This keeps Agent context bounded while still
preserving useful evidence.

## Timeout Policy

Commands default to a 60 second timeout. Callers may request a shorter or longer
timeout, but v0.3 clamps the maximum to 300 seconds. If a command times out,
the tool returns `timed_out=true`, `exit_code=null`, and a clear timeout message
in stderr.

## Current Limitations

v0.8.0 does not modify source files. The Agent and workflow can use safe local
file, search, report, Git inspection, project profile, structured report, and
whitelist command primitives. Their only write-capable tools create reports under
`project_root/reports`.

Before pushing to GitHub, make sure `.env`, local reports, caches, virtual
environments, and generated indexes are not tracked.
