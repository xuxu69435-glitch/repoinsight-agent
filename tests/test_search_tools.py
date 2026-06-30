from __future__ import annotations

from pathlib import Path

from repoinsight.tools.search_tools import search_code


def test_search_code_finds_keyword(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.py").write_text("VALUE = 'needle'\n", encoding="utf-8")
    (project / "src" / "other.py").write_text("VALUE = 'haystack'\n", encoding="utf-8")

    result = search_code(str(project), "needle")

    assert result["query"] == "needle"
    assert result["matches"] == [{"file": "src/main.py", "line": 1, "text": "VALUE = 'needle'"}]


def test_search_code_ignores_node_modules(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.py").write_text("visible needle\n", encoding="utf-8")
    (project / "node_modules" / "pkg").mkdir(parents=True)
    (project / "node_modules" / "pkg" / "index.js").write_text("hidden needle\n", encoding="utf-8")

    result = search_code(str(project), "needle")

    assert [match["file"] for match in result["matches"]] == ["src/main.py"]
