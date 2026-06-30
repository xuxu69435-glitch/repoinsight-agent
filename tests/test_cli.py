from __future__ import annotations

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
                (reports_dir / "mock_report.md").write_text("# Mock Report\n", encoding="utf-8")
                return {"messages": [{"content": "Mock summary"}]}

        return FakeAgent()

    monkeypatch.setattr(cli, "build_agent", fake_build_agent)

    result = runner.invoke(cli.app, ["ask", "Analyze architecture", "--path", str(project)])

    assert result.exit_code == 0
    assert invoked["payload"]["messages"][0]["content"] == "Analyze architecture"
    assert "Agent finished." in result.output
    assert "Report directory:" in result.output
    assert "mock_report.md" in result.output
    assert "Mock summary" in result.output
