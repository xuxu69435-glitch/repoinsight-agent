# Security Policy

RepoInsight Agent analyzes local repositories, so its default posture is
restricted and explicit. Please report security issues privately when possible.

## Reporting a Security Issue

Use GitHub's private vulnerability reporting or contact the maintainer through a
private channel. Include:

- A clear description of the issue.
- Steps to reproduce.
- Affected command or module.
- Expected impact.

Do not include real API keys, `.env` files, private repository contents, or
other secrets in public issues.

## Tool Execution Safety

- Tools are bound to one validated `project_root`.
- File access must remain inside that project root.
- Path traversal attempts such as `../secret.txt` are rejected.
- Report writers only write under `project_root/reports/`.
- Source files are not modified by RepoInsight tools.

## Command Whitelist

RepoInsight does not allow arbitrary shell execution. Commands are parsed and
validated before execution, then run with `shell=False`.

Allowed commands are limited to read-only Git inspection and selected test or
build commands, including:

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

## Rejected Behavior

RepoInsight rejects:

- Arbitrary shell entrypoints such as `bash`, `sh`, `cmd`, and `powershell`.
- Shell syntax such as pipes, redirects, command chaining, and substitution.
- Git mutations such as `git commit`, `git push`, `git reset`, and `git clean`.
- Dependency installation such as `npm install`, `pnpm install`, and
  `yarn install`.
- File access outside `project_root`.

## API Key Handling

`doctor` reports whether `OPENAI_API_KEY` is configured as yes/no. It does not
print the key value. Do not paste real API keys in issues, reports, logs, or
examples.
