from __future__ import annotations

from pathlib import Path

from repoinsight.agent.tools import create_repo_tools


def test_create_repo_tools_exposes_nine_bound_tools(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    tools = create_repo_tools(project)

    assert sorted(tool.name for tool in tools) == [
        "detect_project_profile",
        "get_git_diff",
        "get_git_log",
        "get_git_status",
        "list_project_files",
        "read_project_file",
        "run_project_command",
        "search_project_code",
        "write_markdown_report",
    ]


def test_bound_tools_can_list_read_search_and_write(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.py").write_text("ENTRY = 'repoinsight'\n", encoding="utf-8")

    tools = {tool.name: tool for tool in create_repo_tools(project)}

    listed = tools["list_project_files"].invoke({"max_depth": 3})
    assert "src/main.py" in listed["files"]

    read = tools["read_project_file"].invoke({"relative_path": "src/main.py"})
    assert read["content"] == "ENTRY = 'repoinsight'\n"

    searched = tools["search_project_code"].invoke({"query": "repoinsight"})
    assert searched["matches"] == [
        {"file": "src/main.py", "line": 1, "text": "ENTRY = 'repoinsight'"}
    ]

    written = tools["write_markdown_report"].invoke(
        {"filename": "analysis_report.md", "content": "# Report\n"}
    )
    report_path = Path(written["report_path"])
    assert report_path == project.resolve() / "reports" / "analysis_report.md"
    assert report_path.read_text(encoding="utf-8") == "# Report\n"


def test_new_agent_tools_are_available_by_name(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    tools = {tool.name: tool for tool in create_repo_tools(project)}

    assert "run_project_command" in tools
    assert "get_git_status" in tools
    assert "get_git_diff" in tools
    assert "get_git_log" in tools
    assert "detect_project_profile" in tools


def test_detect_project_profile_tool_is_bound_to_project_root(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")

    tools = {tool.name: tool for tool in create_repo_tools(project)}
    result = tools["detect_project_profile"].invoke({})

    assert "Python" in result["project_types"]
    assert any(item["path"] == "pyproject.toml" for item in result["config_files"])
