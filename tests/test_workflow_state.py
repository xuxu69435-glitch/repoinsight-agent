from __future__ import annotations

from repoinsight.workflow.state import create_initial_state


def test_create_initial_state_contains_required_fields() -> None:
    state = create_initial_state("project", "Analyze", no_llm=True)

    assert state["project_root"] == "project"
    assert state["task"] == "Analyze"
    assert state["no_llm"] is True
    assert state["profile"] is None
    assert state["plan"] == []
    assert state["evidence"] == []
    assert state["report"] is None
    assert state["markdown_report_path"] is None
    assert state["json_report_path"] is None
    assert state["llm_used"] is False
    assert state["llm_model"] is None
    assert state["analysis_mode"] == "deterministic"


def test_create_initial_state_tracks_requested_llm_model() -> None:
    state = create_initial_state("project", "Analyze", no_llm=False, llm_model="mock-model")

    assert state["llm_used"] is False
    assert state["llm_model"] == "mock-model"
    assert state["analysis_mode"] == "llm"


def test_state_errors_and_warnings_are_accumulable() -> None:
    state = create_initial_state("project", "Analyze")

    state["errors"].append("first error")
    state["warnings"].append("first warning")

    assert state["errors"] == ["first error"]
    assert state["warnings"] == ["first warning"]
