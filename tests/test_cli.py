from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from repoinsight import cli

runner = CliRunner()


def test_ask_command_uses_mocked_agent(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    invoked: dict[str, Any] = {}

    def fake_build_agent(project_root: Path, config: Any) -> Any:
        assert project_root == project.resolve()
        assert config.openai_api_key == "test-key"

        class FakeAgent:
            def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
                invoked["payload"] = payload
                reports_dir = project_root / "reports"
                reports_dir.mkdir(exist_ok=True)
                markdown_path = reports_dir / "mock_report.md"
                json_path = reports_dir / "mock_report.json"
                markdown_path.write_text("# Mock Report\n", encoding="utf-8")
                json_path.write_text("{}", encoding="utf-8")
                return {
                    "messages": [{"content": "Mock summary"}],
                    "markdown_report_path": str(markdown_path),
                    "json_report_path": str(json_path),
                }

        return FakeAgent()

    monkeypatch.setattr("repoinsight.agent.builder.build_agent", fake_build_agent)

    result = runner.invoke(cli.app, ["ask", "Analyze architecture", "--path", str(project)])

    assert result.exit_code == 0
    assert invoked["payload"]["messages"][0]["content"] == "Analyze architecture"
    assert "Agent finished." in result.output
    assert "Report directory:" in result.output
    assert "Markdown report path:" in result.output
    assert "JSON report path:" in result.output
    assert "mock_report.md" in result.output
    assert "mock_report.json" in result.output
    assert "Mock summary" in result.output


def test_profile_command_outputs_project_profile_without_api_key(
    monkeypatch,
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = runner.invoke(cli.app, ["profile", "--path", str(project)])

    assert result.exit_code == 0
    assert "Project Profile" in result.output
    assert "Python" in result.output


def test_profile_command_outputs_json_without_api_key(monkeypatch, tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text(
        '{"dependencies": {"react": "^19.0.0"}}',
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = runner.invoke(cli.app, ["profile", "--path", str(project), "--json"])

    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert "React" in parsed["frameworks"]
    assert parsed["root"] == project.name
