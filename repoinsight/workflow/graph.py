"""LangGraph graph construction and runner."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from repoinsight.utils.path_guard import resolve_project_path
from repoinsight.workflow.nodes import (
    analyze_node,
    evidence_node,
    plan_node,
    profile_node,
    report_node,
)
from repoinsight.workflow.state import RepoInsightState, create_initial_state


def build_workflow() -> Any:
    """Build the RepoInsight deterministic workflow graph."""
    graph = StateGraph(RepoInsightState)
    graph.add_node("profile", profile_node)
    graph.add_node("plan", plan_node)
    graph.add_node("evidence", evidence_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "profile")
    graph.add_edge("profile", "plan")
    graph.add_edge("plan", "evidence")
    graph.add_edge("evidence", "analyze")
    graph.add_edge("analyze", "report")
    graph.add_edge("report", END)
    return graph.compile()


def run_workflow(project_root: str, task: str, no_llm: bool = True) -> dict[str, Any]:
    """Run the RepoInsight workflow and return the final state."""
    try:
        root = resolve_project_path(project_root)
    except Exception as exc:
        state = create_initial_state(project_root, task, no_llm=no_llm)
        state["errors"].append(f"Invalid project path: {exc}")
        return dict(state)

    state = create_initial_state(str(root), task, no_llm=no_llm)
    try:
        result = build_workflow().invoke(state)
    except Exception as exc:
        state["errors"].append(f"Workflow execution failed: {exc}")
        return dict(state)
    return dict(result)
