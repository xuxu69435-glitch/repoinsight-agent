from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from repoinsight.tools import command_tools
from repoinsight.tools.command_tools import MAX_OUTPUT_CHARS, run_safe_command


def test_run_safe_command_executes_allowed_command(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "test_sample.py").write_text(
        "def test_sample():\n    assert True\n",
        encoding="utf-8",
    )

    result = run_safe_command(str(project), "python -m pytest", timeout_seconds=60)

    assert result["allowed"] is True
    assert result["timed_out"] is False
    assert result["exit_code"] == 0


def test_run_safe_command_returns_structured_rejection(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    result = run_safe_command(str(project), "npm install")

    assert result["allowed"] is False
    assert result["exit_code"] is None
    assert "Command is not allowed" in result["stderr"]


def test_run_safe_command_clamps_timeout(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    seen: dict[str, Any] = {}

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen["timeout"] = kwargs["timeout"]
        seen["shell"] = kwargs["shell"]
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(command_tools.subprocess, "run", fake_run)

    result = run_safe_command(str(project), "pytest", timeout_seconds=999)

    assert seen["timeout"] == 300
    assert seen["shell"] is False
    assert result["timeout_seconds"] == 300
    assert result["stdout"] == "ok"


def test_run_safe_command_truncates_long_output(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    long_stdout = "x" * (MAX_OUTPUT_CHARS + 10)
    long_stderr = "y" * (MAX_OUTPUT_CHARS + 20)

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout=long_stdout,
            stderr=long_stderr,
        )

    monkeypatch.setattr(command_tools.subprocess, "run", fake_run)

    result = run_safe_command(str(project), "pytest")

    assert len(result["stdout"]) == MAX_OUTPUT_CHARS
    assert len(result["stderr"]) == MAX_OUTPUT_CHARS
    assert result["stdout_truncated"] is True
    assert result["stderr_truncated"] is True


def test_run_safe_command_returns_timeout_result(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"], stderr="busy")

    monkeypatch.setattr(command_tools.subprocess, "run", fake_run)

    result = run_safe_command(str(project), "pytest", timeout_seconds=1)

    assert result["allowed"] is True
    assert result["exit_code"] is None
    assert result["timed_out"] is True
    assert "Command timed out after 1 seconds." in result["stderr"]
