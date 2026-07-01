from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from repoinsight import cli
from repoinsight.utils.report_guard import ReportWriteError

runner = CliRunner()


def test_doctor_runs_without_api_key(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = runner.invoke(cli.app, ["doctor", "--path", str(project)])

    assert result.exit_code == 0
    assert "RepoInsight Doctor" in result.output
    assert "Project path" in result.output
    assert "Reports writable" in result.output
    assert "OPENAI_API_KEY" in result.output
    assert "WARN" in result.output
    assert (project / "reports").is_dir()


def test_doctor_does_not_print_api_key_value(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.setenv("OPENAI_API_KEY", "secret-value")

    result = runner.invoke(cli.app, ["doctor", "--path", str(project)])

    assert result.exit_code == 0
    assert "configured: yes" in result.output
    assert "secret-value" not in result.output


def test_doctor_returns_nonzero_for_missing_project(tmp_path: Path) -> None:
    missing_project = tmp_path / "missing"

    result = runner.invoke(cli.app, ["doctor", "--path", str(missing_project)])

    assert result.exit_code != 0
    assert "Project path" in result.output
    assert "FAIL" in result.output


def test_doctor_returns_nonzero_for_unwritable_reports(
    monkeypatch,
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    def fail_ensure_reports_dir(root: Path) -> Path:
        raise ReportWriteError(
            "Reports directory is not writable: "
            f"{root / 'reports'}. Please check permissions or remove/recreate "
            "the generated reports directory."
        )

    monkeypatch.setattr(cli, "ensure_reports_dir", fail_ensure_reports_dir)

    result = runner.invoke(cli.app, ["doctor", "--path", str(project)])

    assert result.exit_code != 0
    assert "Reports directory is not writable" in result.output
    assert "FAIL" in result.output


def test_doctor_returns_nonzero_for_unwritable_workflow_report_file(
    monkeypatch,
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()

    def fail_report_file(path: Path) -> Path:
        if path.name == "workflow_analysis_report.md":
            raise ReportWriteError(
                "Report file is not writable: "
                f"{path}. Please check file permissions or choose another report filename."
            )
        return path

    monkeypatch.setattr(cli, "ensure_report_file_writable", fail_report_file)

    result = runner.invoke(cli.app, ["doctor", "--path", str(project)])

    assert result.exit_code != 0
    assert "Report file is not writable" in result.output
    assert "FAIL" in result.output
