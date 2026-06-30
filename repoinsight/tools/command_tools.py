"""Safe command execution tools."""

from __future__ import annotations

import subprocess
import time
from typing import Any

from repoinsight.utils.command_guard import validate_safe_command
from repoinsight.utils.path_guard import resolve_project_path

MAX_OUTPUT_CHARS = 20_000
MAX_TIMEOUT_SECONDS = 300
DEFAULT_TIMEOUT_SECONDS = 60


def run_safe_command(
    project_root: str,
    command: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run an allowed command inside project_root with shell=False."""
    start = time.perf_counter()
    try:
        root = resolve_project_path(project_root)
        argv = validate_safe_command(command)
    except Exception as exc:
        return _result(
            command=command,
            allowed=False,
            exit_code=None,
            stdout="",
            stderr=str(exc),
            duration_seconds=time.perf_counter() - start,
            timed_out=False,
        )

    effective_timeout = _normalize_timeout(timeout_seconds)
    try:
        completed = subprocess.run(
            argv,
            cwd=root,
            capture_output=True,
            text=True,
            shell=False,
            timeout=effective_timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stderr = _coerce_output(exc.stderr)
        timeout_message = f"Command timed out after {effective_timeout} seconds."
        if stderr:
            stderr = f"{stderr}\n{timeout_message}"
        else:
            stderr = timeout_message
        return _result(
            command=command,
            allowed=True,
            exit_code=None,
            stdout=_coerce_output(exc.stdout),
            stderr=stderr,
            duration_seconds=time.perf_counter() - start,
            timed_out=True,
            timeout_seconds=effective_timeout,
        )
    except OSError as exc:
        return _result(
            command=command,
            allowed=True,
            exit_code=None,
            stdout="",
            stderr=f"Could not execute command: {exc}",
            duration_seconds=time.perf_counter() - start,
            timed_out=False,
            timeout_seconds=effective_timeout,
        )

    return _result(
        command=command,
        allowed=True,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - start,
        timed_out=False,
        timeout_seconds=effective_timeout,
    )


def _normalize_timeout(timeout_seconds: int) -> int:
    if timeout_seconds <= 0:
        return DEFAULT_TIMEOUT_SECONDS
    return min(timeout_seconds, MAX_TIMEOUT_SECONDS)


def _result(
    *,
    command: str,
    allowed: bool,
    exit_code: int | None,
    stdout: str,
    stderr: str,
    duration_seconds: float,
    timed_out: bool,
    timeout_seconds: int | None = None,
) -> dict[str, Any]:
    stdout_text, stdout_truncated = _truncate(stdout)
    stderr_text, stderr_truncated = _truncate(stderr)
    result: dict[str, Any] = {
        "command": command,
        "allowed": allowed,
        "exit_code": exit_code,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "duration_seconds": round(duration_seconds, 3),
        "timed_out": timed_out,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }
    if timeout_seconds is not None:
        result["timeout_seconds"] = timeout_seconds
    return result


def _truncate(value: str | None) -> tuple[str, bool]:
    text = value or ""
    if len(text) <= MAX_OUTPUT_CHARS:
        return text, False
    return text[:MAX_OUTPUT_CHARS], True


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
