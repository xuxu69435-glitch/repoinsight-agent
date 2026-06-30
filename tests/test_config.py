from __future__ import annotations

from repoinsight.config import DEFAULT_OPENAI_MODEL, load_config


def test_load_config_uses_default_model_without_environment(monkeypatch) -> None:
    for name in [
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "OPENAI_TEMPERATURE",
    ]:
        monkeypatch.delenv(name, raising=False)

    config = load_config(load_env=False)

    assert config.openai_api_key is None
    assert config.openai_base_url is None
    assert config.openai_model == DEFAULT_OPENAI_MODEL
    assert config.temperature == 0


def test_load_config_reads_openai_model_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "custom-model")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_TEMPERATURE", "0.2")

    config = load_config(load_env=False)

    assert config.openai_api_key == "test-key"
    assert config.openai_base_url == "https://example.test/v1"
    assert config.openai_model == "custom-model"
    assert config.temperature == 0.2
