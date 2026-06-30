"""Deterministic project profile detector."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from repoinsight.config import IGNORED_DIRECTORIES
from repoinsight.utils.path_guard import resolve_project_path

MAX_CONFIG_BYTES = 200 * 1024
MAX_ENTRY_DEPTH = 4

NODE_CONFIGS = (
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
    "next.config.mjs",
    "tsconfig.json",
)
PYTHON_CONFIGS = (
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "setup.cfg",
    "pytest.ini",
)
GENERAL_CONFIGS = (
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    ".gitignore",
    ".env.example",
    "Dockerfile",
    "docker-compose.yml",
    *PYTHON_CONFIGS,
    "package.json",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "next.config.js",
)
KNOWN_ENTRY_FILES = (
    "src/main.tsx",
    "src/main.ts",
    "src/index.tsx",
    "src/index.ts",
    "src/App.tsx",
    "src/App.vue",
    "pages/index.tsx",
    "app/page.tsx",
    "main.ts",
    "index.js",
    "main.py",
    "app.py",
    "manage.py",
)


class DependencyInfo(BaseModel):
    """Dependency discovered from a manifest file."""

    name: str
    version: str | None = None
    source: str


class ScriptInfo(BaseModel):
    """Script command discovered from package metadata."""

    name: str
    command: str
    source: str


class EntryPointInfo(BaseModel):
    """Likely project entry point."""

    path: str
    kind: str
    evidence: str


class ConfigFileInfo(BaseModel):
    """Known project configuration file."""

    path: str
    kind: str


class ProjectProfile(BaseModel):
    """Deterministic project profile."""

    root: str
    project_types: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    dependencies: list[DependencyInfo] = Field(default_factory=list)
    scripts: list[ScriptInfo] = Field(default_factory=list)
    entry_points: list[EntryPointInfo] = Field(default_factory=list)
    config_files: list[ConfigFileInfo] = Field(default_factory=list)
    evidence_files: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    notes: list[str] = Field(default_factory=list)


def detect_project(project_root: str) -> dict[str, Any]:
    """Detect project type, stack, entry points, and config files without an LLM."""
    root = resolve_project_path(project_root)
    profile = ProjectProfile(root=root.name or ".")

    _collect_config_files(root, profile)
    package_data = _read_package_json(root, profile)
    pyproject_data = _read_pyproject(root, profile)
    requirements = _read_requirements(root, profile)

    _detect_node(root, profile, package_data)
    _detect_python(root, profile, pyproject_data, requirements)
    _detect_entry_points(root, profile)
    _finalize_profile(profile)

    return profile.model_dump()


def _collect_config_files(root: Path, profile: ProjectProfile) -> None:
    for relative_path in GENERAL_CONFIGS:
        path = root / relative_path
        if path.is_file():
            _add_config(profile, relative_path, _config_kind(relative_path))


def _read_package_json(root: Path, profile: ProjectProfile) -> dict[str, Any]:
    path = root / "package.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(_read_small_text(path))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        profile.notes.append(f"Could not parse package.json: {exc}")
        return {}
    for group in ("dependencies", "devDependencies"):
        dependencies = data.get(group, {})
        if isinstance(dependencies, dict):
            for name, version in dependencies.items():
                profile.dependencies.append(
                    DependencyInfo(
                        name=str(name),
                        version=str(version),
                        source=f"package.json:{group}",
                    )
                )
    scripts = data.get("scripts", {})
    if isinstance(scripts, dict):
        for name, command in scripts.items():
            profile.scripts.append(
                ScriptInfo(name=str(name), command=str(command), source="package.json:scripts")
            )
    return data


def _read_pyproject(root: Path, profile: ProjectProfile) -> dict[str, Any]:
    path = root / "pyproject.toml"
    if not path.is_file():
        return {}
    try:
        data = tomllib.loads(_read_small_text(path))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        profile.notes.append(f"Could not parse pyproject.toml: {exc}")
        return {}

    project = data.get("project", {})
    if isinstance(project, dict):
        dependencies = project.get("dependencies", [])
        if isinstance(dependencies, list):
            for item in dependencies:
                name, version = _parse_requirement(str(item))
                profile.dependencies.append(
                    DependencyInfo(
                        name=name,
                        version=version,
                        source="pyproject.toml:project.dependencies",
                    )
                )
        optional = project.get("optional-dependencies", {})
        if isinstance(optional, dict):
            for group, dependencies in optional.items():
                if isinstance(dependencies, list):
                    for item in dependencies:
                        name, version = _parse_requirement(str(item))
                        profile.dependencies.append(
                            DependencyInfo(
                                name=name,
                                version=version,
                                source=f"pyproject.toml:project.optional-dependencies.{group}",
                            )
                        )
    return data


def _read_requirements(root: Path, profile: ProjectProfile) -> list[str]:
    path = root / "requirements.txt"
    if not path.is_file():
        return []
    try:
        lines = _read_small_text(path).splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        profile.notes.append(f"Could not parse requirements.txt: {exc}")
        return []

    requirements: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        name, version = _parse_requirement(stripped)
        requirements.append(name)
        profile.dependencies.append(
            DependencyInfo(name=name, version=version, source="requirements.txt")
        )
    return requirements


def _detect_node(root: Path, profile: ProjectProfile, package_data: dict[str, Any]) -> None:
    has_node_config = any((root / path).is_file() for path in NODE_CONFIGS)
    if not has_node_config:
        return

    _add_unique(profile.project_types, "Node.js")
    _add_unique(profile.languages, "JavaScript")
    if package_data or (root / "package.json").is_file():
        _add_unique(profile.project_types, "JavaScript")

    dependency_names = _dependency_names(profile.dependencies)
    if "react" in dependency_names:
        _add_unique(profile.frameworks, "React")
    if "vue" in dependency_names:
        _add_unique(profile.frameworks, "Vue")
    if "vite" in dependency_names or _has_any(root, ("vite.config.ts", "vite.config.js")):
        _add_unique(profile.frameworks, "Vite")
    if "next" in dependency_names or _has_any(root, ("next.config.js", "next.config.mjs")):
        _add_unique(profile.frameworks, "Next.js")
    if "typescript" in dependency_names or (root / "tsconfig.json").is_file():
        _add_unique(profile.languages, "TypeScript")

    if (root / "pnpm-lock.yaml").is_file():
        _add_unique(profile.package_managers, "pnpm")
    if (root / "package-lock.json").is_file():
        _add_unique(profile.package_managers, "npm")
    if (root / "yarn.lock").is_file():
        _add_unique(profile.package_managers, "yarn")
    if package_data and not profile.package_managers:
        _add_unique(profile.package_managers, "npm")


def _detect_python(
    root: Path,
    profile: ProjectProfile,
    pyproject_data: dict[str, Any],
    requirements: list[str],
) -> None:
    has_python_config = any((root / path).is_file() for path in PYTHON_CONFIGS)
    has_python_entry = any((root / path).is_file() for path in ("main.py", "app.py", "manage.py"))
    if not has_python_config and not has_python_entry:
        return

    _add_unique(profile.project_types, "Python")
    _add_unique(profile.languages, "Python")

    dependency_names = _dependency_names(profile.dependencies) | {
        name.lower() for name in requirements
    }
    if "fastapi" in dependency_names:
        _add_unique(profile.frameworks, "FastAPI")
    if "flask" in dependency_names:
        _add_unique(profile.frameworks, "Flask")
    if "typer" in dependency_names:
        _add_unique(profile.frameworks, "Typer CLI")
    if _has_dependency_prefix(dependency_names, "langchain"):
        _add_unique(profile.frameworks, "LangChain")
    if "pytest" in dependency_names or (root / "pytest.ini").is_file():
        _add_unique(profile.frameworks, "Pytest")

    if pyproject_data:
        build_system = pyproject_data.get("build-system", {})
        if isinstance(build_system, dict) and build_system:
            profile.notes.append("Python build-system metadata found in pyproject.toml.")


def _detect_entry_points(root: Path, profile: ProjectProfile) -> None:
    for relative_path in KNOWN_ENTRY_FILES:
        path = root / relative_path
        if path.is_file():
            _add_entry(profile, relative_path, _entry_kind(relative_path), "known entry filename")

    for path in _iter_limited_files(root, max_depth=MAX_ENTRY_DEPTH):
        relative_path = path.relative_to(root).as_posix()
        if relative_path in {entry.path for entry in profile.entry_points}:
            continue
        if path.name == "cli.py":
            _add_entry(profile, relative_path, "python-cli", "cli.py filename")
        elif path.name == "main.py":
            _add_entry(profile, relative_path, "python-main", "main.py filename")


def _finalize_profile(profile: ProjectProfile) -> None:
    if not profile.project_types:
        profile.project_types = ["unknown"]
        profile.notes.append("No known project manifest or entry point was detected.")

    profile.project_types = _sorted_unique(profile.project_types)
    profile.languages = _sorted_unique(profile.languages)
    profile.frameworks = _sorted_unique(profile.frameworks)
    profile.package_managers = _sorted_unique(profile.package_managers)
    profile.evidence_files = _sorted_unique(
        [
            *profile.evidence_files,
            *(item.path for item in profile.config_files),
            *(item.path for item in profile.entry_points),
        ]
    )
    profile.confidence = _calculate_confidence(profile)


def _calculate_confidence(profile: ProjectProfile) -> float:
    if profile.project_types == ["unknown"]:
        return 0.1
    score = 0.25
    score += min(len(profile.config_files) * 0.06, 0.24)
    score += min(len(profile.dependencies) * 0.015, 0.18)
    score += min(len(profile.frameworks) * 0.07, 0.21)
    score += min(len(profile.entry_points) * 0.05, 0.12)
    return min(round(score, 2), 1.0)


def _read_small_text(path: Path) -> str:
    if path.stat().st_size > MAX_CONFIG_BYTES:
        raise OSError(f"file exceeds {MAX_CONFIG_BYTES} bytes")
    return path.read_text(encoding="utf-8")


def _iter_limited_files(root: Path, max_depth: int) -> list[Path]:
    results: list[Path] = []

    def walk(current: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(current.iterdir(), key=lambda item: item.name.lower())
        except OSError:
            return
        for entry in entries:
            if entry.is_dir():
                if entry.name in IGNORED_DIRECTORIES or entry.is_symlink():
                    continue
                walk(entry, depth + 1)
            elif entry.is_file():
                results.append(entry)

    walk(root, 0)
    return results


def _parse_requirement(requirement: str) -> tuple[str, str | None]:
    cleaned = requirement.strip()
    cleaned = cleaned.split(";", 1)[0].strip()
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    match = re.match(r"^([A-Za-z0-9_.-]+)\s*(.*)$", cleaned)
    if not match:
        return cleaned, None
    name = match.group(1)
    version = match.group(2).strip() or None
    return name, version


def _dependency_names(dependencies: list[DependencyInfo]) -> set[str]:
    return {dependency.name.lower() for dependency in dependencies}


def _has_dependency_prefix(dependency_names: set[str], prefix: str) -> bool:
    return any(name == prefix or name.startswith(f"{prefix}-") for name in dependency_names)


def _has_any(root: Path, relative_paths: tuple[str, ...]) -> bool:
    return any((root / relative_path).is_file() for relative_path in relative_paths)


def _add_config(profile: ProjectProfile, path: str, kind: str) -> None:
    if path not in {item.path for item in profile.config_files}:
        profile.config_files.append(ConfigFileInfo(path=path, kind=kind))
        _add_unique(profile.evidence_files, path)


def _add_entry(profile: ProjectProfile, path: str, kind: str, evidence: str) -> None:
    if path not in {item.path for item in profile.entry_points}:
        profile.entry_points.append(EntryPointInfo(path=path, kind=kind, evidence=evidence))
        _add_unique(profile.evidence_files, path)


def _add_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(set(items), key=lambda value: value.lower())


def _config_kind(path: str) -> str:
    mapping = {
        "package.json": "node-package-manifest",
        "pyproject.toml": "python-project-manifest",
        "requirements.txt": "python-requirements",
        "tsconfig.json": "typescript-config",
        "vite.config.ts": "vite-config",
        "vite.config.js": "vite-config",
        "next.config.js": "next-config",
        "README.md": "documentation",
        "README.zh-CN.md": "documentation",
        "LICENSE": "license",
        ".gitignore": "git-ignore",
        ".env.example": "environment-example",
        "Dockerfile": "container-config",
        "docker-compose.yml": "container-config",
        "setup.py": "python-setup",
        "setup.cfg": "python-setup",
        "pytest.ini": "pytest-config",
    }
    return mapping.get(path, "config")


def _entry_kind(path: str) -> str:
    if path.endswith(".vue"):
        return "vue-component"
    if path.endswith((".tsx", ".jsx")):
        return "frontend-react"
    if path.endswith((".ts", ".js")):
        return "frontend"
    if path.endswith(".py"):
        return "python"
    return "entry"
