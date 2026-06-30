"""LangChain Agent builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from repoinsight.agent.prompts import SYSTEM_PROMPT
from repoinsight.agent.tools import create_repo_tools
from repoinsight.config import AppConfig


def build_agent(project_root: Path, config: AppConfig) -> Any:
    """Build a LangChain Agent bound to the selected project root."""
    model_kwargs: dict[str, Any] = {
        "api_key": config.openai_api_key,
        "model": config.openai_model,
        "temperature": config.temperature,
    }
    if config.openai_base_url:
        model_kwargs["base_url"] = config.openai_base_url

    model = ChatOpenAI(**model_kwargs)
    return create_agent(
        model=model,
        tools=create_repo_tools(project_root),
        system_prompt=SYSTEM_PROMPT,
    )
