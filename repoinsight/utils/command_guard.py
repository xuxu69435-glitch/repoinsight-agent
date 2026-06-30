"""Safety checks for allowed command execution."""

from __future__ import annotations

import ntpath
import shlex

ALLOWED_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("git", "status"),
    ("git", "diff"),
    ("git", "diff", "--stat"),
    ("git", "log", "--oneline"),
    ("pytest",),
    ("python", "-m", "pytest"),
    ("npm", "test"),
    ("npm", "run", "test"),
    ("npm", "run", "build"),
    ("pnpm", "test"),
    ("pnpm", "run", "test"),
    ("pnpm", "build"),
    ("pnpm", "run", "build"),
    ("yarn", "test"),
    ("yarn", "build"),
)

SHELL_CONTROL_TOKENS = ("&&", "||", "|", ">>", ">", "<", ";", "`", "$(")
DANGEROUS_KEYWORDS = frozenset(
    {
        "rm",
        "del",
        "rmdir",
        "format",
        "curl",
        "wget",
        "bash",
        "sh",
        "powershell",
        "cmd",
        "chmod",
        "chown",
        "sudo",
    }
)
DISALLOWED_MESSAGE = "Command is not allowed by RepoInsight safety policy."


def validate_safe_command(command: str) -> list[str]:
    """Validate a command string and return argv for shell=False execution."""
    if not command or not command.strip():
        raise ValueError("Command must not be empty.")

    if _contains_shell_control(command):
        raise ValueError(f"{DISALLOWED_MESSAGE} Shell control operators are not allowed.")

    try:
        argv = shlex.split(command, posix=False)
    except ValueError as exc:
        raise ValueError(f"{DISALLOWED_MESSAGE} Could not parse command.") from exc

    if not argv:
        raise ValueError("Command must not be empty.")

    normalized = tuple(_normalize_token(token) for token in argv)
    if any(token in DANGEROUS_KEYWORDS for token in normalized):
        raise ValueError(f"{DISALLOWED_MESSAGE} Dangerous command keyword detected.")

    if normalized not in ALLOWED_COMMANDS:
        raise ValueError(DISALLOWED_MESSAGE)

    return argv


def is_command_allowed(command: str) -> bool:
    """Return True when a command passes the RepoInsight safety policy."""
    try:
        validate_safe_command(command)
    except ValueError:
        return False
    return True


def _contains_shell_control(command: str) -> bool:
    return any(token in command for token in SHELL_CONTROL_TOKENS)


def _normalize_token(token: str) -> str:
    cleaned = token.strip().strip('"').strip("'").lower()
    base = ntpath.basename(cleaned)
    for suffix in (".exe", ".cmd", ".bat", ".ps1"):
        if base.endswith(suffix):
            return base[: -len(suffix)]
    return base
