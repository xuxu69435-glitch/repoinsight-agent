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

v0.3 does not modify source files. The Agent can use safe local file, search,
report, Git inspection, and whitelist command primitives. Its only write-capable
tool creates Markdown reports under `project_root/reports`.

Before pushing to GitHub, make sure `.env`, local reports, caches, virtual
environments, and generated indexes are not tracked.
