"""Git analysis tools built on safe command execution."""

from __future__ import annotations

from typing import Any

from repoinsight.tools.command_tools import run_safe_command


def git_status(project_root: str) -> dict[str, Any]:
    """Return `git status` output as a structured command result."""
    return run_safe_command(project_root, "git status", timeout_seconds=30)


def git_diff(project_root: str, stat_only: bool = False) -> dict[str, Any]:
    """Return `git diff` or `git diff --stat` output."""
    command = "git diff --stat" if stat_only else "git diff"
    return run_safe_command(project_root, command, timeout_seconds=60)


def git_log_oneline(project_root: str, max_count: int = 10) -> dict[str, Any]:
    """Return recent `git log --oneline` entries, limited in Python."""
    safe_count = min(max(max_count, 1), 50)
    result = run_safe_command(project_root, "git log --oneline", timeout_seconds=30)
    if result.get("stdout"):
        lines = str(result["stdout"]).splitlines()
        result["stdout"] = "\n".join(lines[:safe_count])
        result["stdout_line_count"] = len(result["stdout"].splitlines()) if result["stdout"] else 0
    result["max_count"] = safe_count
    return result
