"""LangGraph workflow nodes."""

from __future__ import annotations

from typing import Any

from repoinsight.agent.schemas import (
    AnalysisReport,
    EvidenceItem,
    Finding,
    ProjectSummary,
    Recommendation,
)
from repoinsight.analyzers.project_detector import detect_project
from repoinsight.tools.file_tools import read_file
from repoinsight.tools.git_tools import git_diff, git_status
from repoinsight.tools.report_tools import write_structured_report
from repoinsight.workflow.state import RepoInsightState

KEY_FILES = ("README.md", "README.zh-CN.md", "package.json", "pyproject.toml", "requirements.txt")


def profile_node(state: RepoInsightState) -> dict[str, Any]:
    """Detect the project profile without LLM or command execution."""
    try:
        return {"profile": detect_project(state["project_root"])}
    except Exception as exc:
        return {"errors": [f"profile_node failed: {exc}"]}


def plan_node(state: RepoInsightState) -> dict[str, Any]:
    """Generate a deterministic analysis plan."""
    plan = [
        "Inspect project profile",
        "Review key configuration files",
        "Check git status",
        "Collect dependency and script evidence",
        "Generate structured report",
    ]
    if not state["no_llm"]:
        return {
            "plan": plan,
            "warnings": [
                "LLM workflow analysis is not implemented yet; deterministic analysis was used."
            ],
        }
    return {"plan": plan}


def evidence_node(state: RepoInsightState) -> dict[str, Any]:
    """Collect deterministic repository evidence without builds or LLM calls."""
    evidence: list[dict[str, Any]] = []
    warnings: list[str] = []
    project_root = state["project_root"]
    profile = state.get("profile")

    if profile is None:
        try:
            profile = detect_project(project_root)
        except Exception as exc:
            return {"errors": [f"evidence_node profile collection failed: {exc}"]}

    evidence.append(
        {
            "kind": "project_profile",
            "summary": "Deterministic project profile collected.",
            "data": profile,
        }
    )

    status = git_status(project_root)
    evidence.append({"kind": "git_status", "summary": _command_summary(status), "data": status})
    if status.get("exit_code") not in (0, None):
        warnings.append("git status returned a non-zero exit code.")
    if status.get("exit_code") is None and status.get("stderr"):
        warnings.append("git status could not complete; see evidence.")

    diff_stat = git_diff(project_root, stat_only=True)
    evidence.append(
        {
            "kind": "git_diff_stat",
            "summary": _command_summary(diff_stat),
            "data": diff_stat,
        }
    )
    if diff_stat.get("exit_code") not in (0, None):
        warnings.append("git diff --stat returned a non-zero exit code.")

    for relative_path in KEY_FILES:
        try:
            file_result = read_file(project_root, relative_path, max_chars=4000)
        except (FileNotFoundError, IsADirectoryError, PermissionError, ValueError):
            continue
        except Exception as exc:
            warnings.append(f"Could not read {relative_path}: {exc}")
            continue
        evidence.append(
            {
                "kind": "key_file",
                "summary": f"Read key file {relative_path}.",
                "file_path": file_result["path"],
                "truncated": file_result["truncated"],
                "content": file_result["content"],
            }
        )

    return {"evidence": evidence, "warnings": warnings}


def analyze_node(state: RepoInsightState) -> dict[str, Any]:
    """Generate a deterministic AnalysisReport from workflow evidence."""
    profile = state.get("profile") or {}
    warnings: list[str] = []
    if not state["no_llm"]:
        warnings.append(
            "LLM workflow analysis is not implemented yet; deterministic analysis was used."
        )

    report = AnalysisReport(
        title="RepoInsight Workflow Analysis Report",
        task=state["task"],
        project_summary=_project_summary_from_profile(profile),
        executive_summary=_executive_summary(profile),
        findings=_build_findings(profile, state.get("evidence", [])),
        recommendations=_build_recommendations(profile, state.get("evidence", [])),
        evidence_files=_safe_string_list(profile.get("evidence_files", [])),
        limitations=[
            "Workflow ran in deterministic mode and did not perform deep semantic code analysis.",
            "No build or test commands were executed by the workflow.",
        ],
        next_steps=[
            "Review the generated Markdown and JSON reports.",
            "Run targeted tests or builds separately if deeper validation is needed.",
        ],
    )
    return {"report": report.model_dump(), "warnings": warnings}


def report_node(state: RepoInsightState) -> dict[str, Any]:
    """Write structured Markdown and JSON reports under project_root/reports."""
    report = state.get("report")
    if report is None:
        return {"errors": ["report_node failed: missing AnalysisReport data."]}
    try:
        result = write_structured_report(
            state["project_root"],
            "workflow_analysis_report.json",
            report,
        )
    except Exception as exc:
        return {"errors": [f"report_node failed: {exc}"]}
    return {
        "markdown_report_path": result["markdown_report_path"],
        "json_report_path": result["json_report_path"],
    }


def _project_summary_from_profile(profile: dict[str, Any]) -> ProjectSummary:
    return ProjectSummary(
        project_types=_safe_string_list(profile.get("project_types", [])),
        languages=_safe_string_list(profile.get("languages", [])),
        frameworks=_safe_string_list(profile.get("frameworks", [])),
        package_managers=_safe_string_list(profile.get("package_managers", [])),
        entry_points=_paths_from_items(profile.get("entry_points", [])),
        key_config_files=_paths_from_items(profile.get("config_files", [])),
    )


def _executive_summary(profile: dict[str, Any]) -> str:
    project_types = _join(profile.get("project_types", []))
    languages = _join(profile.get("languages", []))
    frameworks = _join(profile.get("frameworks", []))
    if not project_types:
        return "RepoInsight could not confidently identify the project type."
    summary = f"Detected project type: {project_types}. Languages: {languages or 'Unknown'}."
    if frameworks:
        summary += f" Frameworks/tools: {frameworks}."
    return summary


def _build_findings(profile: dict[str, Any], evidence: list[dict[str, Any]]) -> list[Finding]:
    findings = [
        Finding(
            title="Detected project profile",
            category="project-profile",
            description=_executive_summary(profile),
            confidence=float(profile.get("confidence", 0.0) or 0.0),
            evidence=[
                EvidenceItem(
                    file_path=file_path,
                    summary="Project detector evidence file.",
                )
                for file_path in _safe_string_list(profile.get("evidence_files", []))[:5]
            ],
        )
    ]

    entry_points = _paths_from_items(profile.get("entry_points", []))
    if entry_points:
        findings.append(
            Finding(
                title="Detected key entry points",
                category="architecture",
                description=f"Likely entry points: {_join(entry_points)}.",
                confidence=0.75,
                evidence=[
                    EvidenceItem(file_path=path, summary="Detected entry point.")
                    for path in entry_points[:5]
                ],
            )
        )
    else:
        findings.append(
            Finding(
                title="No obvious entry points detected",
                category="architecture",
                description="The deterministic detector did not find common entry point filenames.",
                confidence=0.4,
            )
        )

    scripts = profile.get("scripts", [])
    if scripts:
        script_names = [str(item.get("name", "")) for item in scripts if isinstance(item, dict)]
        findings.append(
            Finding(
                title="Detected project scripts",
                category="automation",
                description=f"Detected scripts: {_join(script_names)}.",
                confidence=0.8,
                evidence=[
                    EvidenceItem(
                        file_path="package.json",
                        summary="Scripts parsed from package.json.",
                    )
                ],
            )
        )
    else:
        findings.append(
            Finding(
                title="No package scripts detected",
                category="automation",
                description="No package.json scripts were found by the project detector.",
                confidence=0.6,
            )
        )

    findings.append(_git_status_finding(evidence))
    return findings


def _git_status_finding(evidence: list[dict[str, Any]]) -> Finding:
    git_evidence = next((item for item in evidence if item.get("kind") == "git_status"), None)
    if not git_evidence:
        return Finding(
            title="Git status was not collected",
            category="git",
            description="No git status evidence was available.",
            confidence=0.2,
        )
    data = git_evidence.get("data", {})
    stdout = str(data.get("stdout", "")).strip()
    stderr = str(data.get("stderr", "")).strip()
    description = stdout or stderr or "git status completed without output."
    return Finding(
        title="Git status summary",
        category="git",
        description=description[:1000],
        confidence=0.7 if data.get("allowed") else 0.3,
        evidence=[
            EvidenceItem(
                command="git status",
                summary=git_evidence.get("summary", "git status evidence collected."),
                raw_excerpt=(stdout or stderr)[:1200] or None,
            )
        ],
    )


def _build_recommendations(
    profile: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> list[Recommendation]:
    recommendations = [
        Recommendation(
            title="Review detected project metadata",
            priority="medium",
            description="Confirm that the detected project profile matches the repository intent.",
            suggested_steps=["Check key config files and entry points listed in the report."],
            related_findings=["Detected project profile"],
        )
    ]
    if not profile.get("frameworks"):
        recommendations.append(
            Recommendation(
                title="Document technology stack",
                priority="low",
                description="The deterministic workflow did not identify a framework.",
                suggested_steps=["Add or update README technology stack notes."],
            )
        )
    if any(item.get("kind") == "git_status" for item in evidence):
        recommendations.append(
            Recommendation(
                title="Review Git working tree before publishing",
                priority="medium",
                description=(
                    "Use the Git status evidence to decide whether the repository is ready."
                ),
                suggested_steps=["Review untracked or modified files before release."],
                related_findings=["Git status summary"],
            )
        )
    return recommendations


def _command_summary(result: dict[str, Any]) -> str:
    command = result.get("command", "command")
    exit_code = result.get("exit_code")
    if result.get("timed_out"):
        return f"{command} timed out."
    return f"{command} finished with exit code {exit_code}."


def _paths_from_items(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    paths: list[str] = []
    for item in items:
        if isinstance(item, dict) and item.get("path"):
            paths.append(str(item["path"]))
        elif isinstance(item, str):
            paths.append(item)
    return paths


def _safe_string_list(items: Any) -> list[str]:
    if not isinstance(items, list):
        return []
    return [str(item) for item in items if item]


def _join(items: Any) -> str:
    values = _safe_string_list(items)
    return ", ".join(values)
