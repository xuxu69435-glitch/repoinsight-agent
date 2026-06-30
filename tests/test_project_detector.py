from __future__ import annotations

import json
from pathlib import Path

from repoinsight.analyzers.project_detector import detect_project


def test_detect_python_project(tmp_path: Path) -> None:
    project = tmp_path / "python-project"
    (project / "repoinsight").mkdir(parents=True)
    (project / "repoinsight" / "cli.py").write_text("print('cli')\n", encoding="utf-8")
    (project / "README.md").write_text("# Demo\n", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        """
[project]
name = "demo"
dependencies = [
  "typer>=0.12",
  "langchain>=1.0",
]
""".strip(),
        encoding="utf-8",
    )

    result = detect_project(str(project))

    assert "Python" in result["languages"]
    assert "Python" in result["project_types"]
    assert "Typer CLI" in result["frameworks"]
    assert "LangChain" in result["frameworks"]
    assert any(item["path"] == "pyproject.toml" for item in result["config_files"])
    assert any(item["path"] == "repoinsight/cli.py" for item in result["entry_points"])
    assert result["confidence"] > 0


def test_detect_react_vite_project(tmp_path: Path) -> None:
    project = tmp_path / "react-project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "main.tsx").write_text("import React from 'react';\n", encoding="utf-8")
    (project / "vite.config.ts").write_text("export default {}\n", encoding="utf-8")
    (project / "tsconfig.json").write_text("{}", encoding="utf-8")
    (project / "package-lock.json").write_text("{}", encoding="utf-8")
    (project / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react": "^19.0.0"},
                "devDependencies": {"vite": "^7.0.0", "typescript": "^5.0.0"},
                "scripts": {"build": "vite build", "test": "vitest"},
            }
        ),
        encoding="utf-8",
    )

    result = detect_project(str(project))

    assert "React" in result["frameworks"]
    assert "Vite" in result["frameworks"]
    assert "TypeScript" in result["languages"]
    assert "npm" in result["package_managers"]
    assert any(item["name"] == "build" for item in result["scripts"])
    assert any(item["path"] == "src/main.tsx" for item in result["entry_points"])


def test_detect_vue_vite_project(tmp_path: Path) -> None:
    project = tmp_path / "vue-project"
    (project / "src").mkdir(parents=True)
    (project / "src" / "App.vue").write_text("<template />\n", encoding="utf-8")
    (project / "package.json").write_text(
        json.dumps({"dependencies": {"vue": "^3.0.0"}, "devDependencies": {"vite": "^7.0.0"}}),
        encoding="utf-8",
    )

    result = detect_project(str(project))

    assert "Vue" in result["frameworks"]
    assert "Vite" in result["frameworks"]


def test_detect_unknown_project(tmp_path: Path) -> None:
    project = tmp_path / "unknown-project"
    project.mkdir()
    (project / "random.txt").write_text("hello\n", encoding="utf-8")

    result = detect_project(str(project))

    assert result["project_types"] == ["unknown"]
    assert result["confidence"] < 0.3
