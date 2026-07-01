"""LangGraph graph construction and runner."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from repoinsight.config import AppConfig
from repoinsight.utils.path_guard import resolve_project_path
from repoinsight.workflow.nodes import (
    analyze_node,
    evidence_node,
    plan_node,
    profile_node,
    report_node,
)
from repoinsight.workflow.state import RepoInsightState, create_initial_state

WORKFLOW_LLM_API_KEY_ERROR = (
    "OPENAI_API_KEY is required for workflow --with-llm. "
    "Use --no-llm for deterministic analysis."
)


def build_workflow(config: AppConfig | None = None) -> Any:
    """Build the RepoInsight workflow graph."""
    graph = StateGraph(RepoInsightState)
    graph.add_node("profile", profile_node)
    graph.add_node("plan", plan_node)
    graph.add_node("evidence", evidence_node)
    graph.add_node("analyze", _build_analyze_node(config))
    graph.add_node("report", report_node)

    graph.add_edge(START, "profile")
    graph.add_edge("profile", "plan")
    graph.add_edge("plan", "evidence")
    graph.add_edge("evidence", "analyze")
    graph.add_edge("analyze", "report")
    graph.add_edge("report", END)
    return graph.compile()


def run_workflow(
    project_root: str,
    task: str,
    no_llm: bool = True,
    config: AppConfig | None = None,
) -> dict[str, Any]:
    """Run the RepoInsight workflow and return the final state."""
    if not no_llm and (config is None or not config.openai_api_key):
        raise ValueError(WORKFLOW_LLM_API_KEY_ERROR)

    llm_model = config.openai_model if config else None
    try:
        root = resolve_project_path(project_root)
    except Exception as exc:
        state = create_initial_state(
            project_root,
            task,
            no_llm=no_llm,
            llm_model=llm_model,
        )
        state["errors"].append(f"Invalid project path: {exc}")
        return dict(state)

    state = create_initial_state(str(root), task, no_llm=no_llm, llm_model=llm_model)
    try:
        result = build_workflow(config=config).invoke(state)
    except Exception as exc:
        state["errors"].append(f"Workflow execution failed: {exc}")
        return dict(state)
    return dict(result)


def _build_analyze_node(config: AppConfig | None) -> Any:
    def analyze_with_config(state: RepoInsightState) -> dict[str, Any]:
        return analyze_node(state, config=config)

    return analyze_with_config
