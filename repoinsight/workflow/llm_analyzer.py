"""Mockable LLM analysis for the LangGraph workflow."""

from __future__ import annotations

import json
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from repoinsight.agent.schemas import AnalysisReport
from repoinsight.config import AppConfig


def build_workflow_llm(config: AppConfig) -> Any:
    """Build the workflow LLM client without binding repository tools."""
    model_kwargs: dict[str, Any] = {
        "api_key": config.openai_api_key,
        "model": config.openai_model,
        "temperature": config.temperature,
    }
    if config.openai_base_url:
        model_kwargs["base_url"] = config.openai_base_url
    return ChatOpenAI(**model_kwargs)


def build_llm_analysis_prompt(
    task: str,
    profile: dict[str, Any],
    plan: list[str],
    evidence: list[dict[str, Any]],
) -> str:
    """Build the workflow analysis prompt from already-collected evidence."""
    schema = AnalysisReport.model_json_schema()
    return "\n\n".join(
        [
            "You are RepoInsight workflow analyzer.",
            "You must only use the provided profile, plan, and evidence.",
            "Do not invent files, commands, dependencies, or results.",
            "Use relative paths only.",
            "If evidence is insufficient, write it in limitations.",
            "Return a valid JSON object matching the AnalysisReport schema.",
            "Do not include Markdown fences.",
            "Do not include commentary outside JSON.",
            "Task:\n" + task,
            "Profile:\n" + json.dumps(profile, ensure_ascii=False, indent=2),
            "Plan:\n" + json.dumps(plan, ensure_ascii=False, indent=2),
            "Evidence:\n" + json.dumps(evidence, ensure_ascii=False, indent=2),
            "AnalysisReport schema:\n" + json.dumps(schema, ensure_ascii=False, indent=2),
        ]
    )


def analyze_with_llm(
    task: str,
    profile: dict[str, Any],
    plan: list[str],
    evidence: list[dict[str, Any]],
    config: AppConfig,
) -> AnalysisReport:
    """Generate and validate an AnalysisReport from workflow evidence via LLM."""
    prompt = build_llm_analysis_prompt(task, profile, plan, evidence)
    llm = build_workflow_llm(config)
    response = llm.invoke(prompt)
    data = extract_json_object(_response_to_text(response))
    try:
        report = AnalysisReport.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"LLM response did not match AnalysisReport schema: {exc}") from exc

    _validate_evidence_files(report, profile, evidence)
    return report


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object returned by the workflow LLM."""
    try:
        parsed = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response was not valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON must be an object.")
    return parsed


def _response_to_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    if isinstance(response, dict) and "content" in response:
        return _content_to_text(response["content"])
    if hasattr(response, "content"):
        return _content_to_text(response.content)
    return str(response)


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                value = item.get("text") or item.get("content")
                if value is not None:
                    parts.append(str(value))
        return "\n".join(parts)
    return str(content)


def _validate_evidence_files(
    report: AnalysisReport,
    profile: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> None:
    allowed = _collect_allowed_evidence_files(profile, evidence)
    invented = [file_path for file_path in report.evidence_files if file_path not in allowed]
    if invented:
        joined = ", ".join(invented)
        raise ValueError(
            "LLM response included evidence_files not present in workflow evidence: "
            f"{joined}"
        )


def _collect_allowed_evidence_files(
    profile: dict[str, Any],
    evidence: list[dict[str, Any]],
) -> set[str]:
    allowed: set[str] = set()
    _add_profile_paths(allowed, profile)
    for item in evidence:
        file_path = item.get("file_path")
        if isinstance(file_path, str):
            allowed.add(file_path)
        data = item.get("data")
        if isinstance(data, dict):
            _add_profile_paths(allowed, data)
    return allowed


def _add_profile_paths(allowed: set[str], value: dict[str, Any]) -> None:
    _add_paths(allowed, value.get("evidence_files"))
    _add_paths(allowed, value.get("entry_points"))
    _add_paths(allowed, value.get("config_files"))


def _add_paths(allowed: set[str], value: Any) -> None:
    if not isinstance(value, list):
        return
    for item in value:
        if isinstance(item, str) and item:
            allowed.add(item)
        elif isinstance(item, dict) and item.get("path"):
            allowed.add(str(item["path"]))
