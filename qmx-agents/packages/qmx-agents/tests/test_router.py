from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx
import pytest
from conftest import (
    compiled,
    fake,
    fake_models,
    fake_secret,
    named_secret,
    no_secret,
    stored_secret,
)
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from test_spec import write_spec

from qmx_agents.router import (
    ModelRouter,
    RouterConfig,
    RunContext,
    credential,
    load_config,
    model_selector,
)
from qmx_agents.spec import BuildContext


def test_profiles_and_defaults(config: RouterConfig) -> None:
    router = ModelRouter(config)
    assert config.profile == "daily"
    assert router.selection("reasoning_high") == "cliproxy:claude-opus-5-5"
    assert router.selection("fast") == "cliproxy:gpt-6-luna"
    assert router.selection("workhorse", "test") == "openrouter:deepseek/deepseek-v4-pro-0813"
    assert router.selection("openai:explicit-model") == "openai:explicit-model"


@pytest.mark.parametrize(
    "value", ["workhorse", "tier:unknown", "openai:~latest", "openai:x-latest", "bad:x", "openai:"]
)
def test_bad_selector(value: str) -> None:
    with pytest.raises(ValueError):
        model_selector(value)


@pytest.mark.parametrize("level", ["node", "app", "workflow", "agent_node", "subagent"])
def test_override_chain(level: str, config: RouterConfig) -> None:
    primary, other = fake("primary"), fake("other")
    router = ModelRouter(config, {**fake_models(primary), "openai:exact": other})
    overrides = dict.fromkeys(
        ["node", "app", "workflow", "agent_node", "subagent"], "tier:workhorse"
    )
    index = list(overrides).index(level)
    values: dict[str, Any] = dict(list(overrides.items())[:index])
    values[level] = "openai:exact"
    ctx = RunContext(**values)
    assert router.resolve_model(ctx) is other
    assert ctx.effective_models["agent"] == "openai:exact"


def test_request_can_override_tier(tmp_path: Path, config: RouterConfig) -> None:
    primary, fast = fake("primary"), fake("fast")
    router = ModelRouter(config, {**fake_models(primary), "cliproxy:gpt-6-luna": fast})
    graph = compiled(write_spec(tmp_path), BuildContext(router))
    ctx = RunContext(request_model="tier:fast")
    result = graph.invoke({"messages": [{"role": "user", "content": "Hello"}]}, context=ctx)
    assert result["messages"][-1].content == "fast"
    assert primary.calls == 0
    assert ctx.effective_models["agent"] == "cliproxy:gpt-6-luna"


@pytest.mark.parametrize("asynchronous", [False, True])
def test_fallback_error_and_effective_model(
    tmp_path: Path, config: RouterConfig, asynchronous: bool
) -> None:
    primary, fallback = fake("unused", failures=1), fake("recovered")
    config.fallbacks = ["openai:fallback"]
    router = ModelRouter(config, {**fake_models(primary), "openai:fallback": fallback})
    ctx = BuildContext(router)
    graph = compiled(write_spec(tmp_path), ctx)
    inputs = {"messages": [{"role": "user", "content": "Hello"}]}
    result = asyncio.run(graph.ainvoke(inputs)) if asynchronous else graph.invoke(inputs)
    assert result["messages"][-1].content == "recovered"
    assert primary.calls == 1
    assert fallback.calls == 1
    assert ctx.run.effective_models["agent"] == "openai:fallback"


def test_retry_before_fallback(tmp_path: Path, config: RouterConfig) -> None:
    config.max_retries = 1
    primary = fake("retried", failures=1)
    ctx = BuildContext(ModelRouter(config, fake_models(primary)))
    graph = compiled(write_spec(tmp_path), ctx)
    result = graph.invoke({"messages": [{"role": "user", "content": "Hello"}]})
    assert result["messages"][-1].content == "retried"
    assert primary.calls == 2


@pytest.mark.parametrize(
    ("selection", "expected", "base"),
    [
        ("cliproxy:claude-opus-5-5", ChatAnthropic, "http://127.0.0.1:8317"),
        ("cliproxy:gpt-6.1-sol(high)", ChatOpenAI, "http://127.0.0.1:8317/v1/"),
        ("openrouter:deepseek/deepseek-v4-pro-0813", ChatOpenAI, "https://openrouter.ai/api/v1/"),
        ("local:my-model", ChatOpenAI, "http://127.0.0.1:8080/v1/"),
        ("anthropic:claude-opus-5-5", ChatAnthropic, "https://api.anthropic.com"),
        ("openai:gpt-6.1-sol", ChatOpenAI, "https://api.openai.com/v1/"),
    ],
)
def test_provider_clients_without_network(
    selection: str, expected: type, base: str, config: RouterConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("keyring.get_password", fake_secret)
    config.providers["local"].base_url = "http://127.0.0.1:8080/v1"
    model = ModelRouter(config).resolve(selection)
    assert isinstance(model, expected)
    if isinstance(model, ChatAnthropic):
        assert model.anthropic_api_url == base
    elif isinstance(model, ChatOpenAI):
        assert str(model.root_client.base_url) == base


def test_credentials_and_ci_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("keyring.get_password", no_secret)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("QMX_OPENROUTER_API_KEY", "fake-ci")
    with pytest.raises(ValueError, match="qmx/openrouter"):
        credential("openrouter")
    monkeypatch.setenv("CI", "true")
    assert credential("openrouter") == "fake-ci"
    monkeypatch.setattr("keyring.get_password", stored_secret)
    assert credential("openrouter") == "credential-manager"


def test_model_catalog_accounts_quotas_auth_and_paths(
    config: RouterConfig, monkeypatch: pytest.MonkeyPatch
) -> None:
    requests: list[tuple[str, str]] = []

    def get(url: str, *, headers: dict[str, str], timeout: int) -> httpx.Response:
        requests.append((url, headers["Authorization"]))
        assert timeout == 30
        payload = {"data": [{"id": "claude-opus-5-5"}, {"id": "gpt-6.1-sol"}]}
        return httpx.Response(200, json=payload, request=httpx.Request("GET", url))

    monkeypatch.setattr("httpx.get", get)
    monkeypatch.setattr("keyring.get_password", named_secret)
    router = ModelRouter(config)
    assert router.list_models() == ["claude-opus-5-5", "gpt-6.1-sol"]
    router.accounts()
    router.quotas("quota-plugin")
    assert requests == [
        ("http://127.0.0.1:8317/v1/models", "Bearer cliproxy"),
        ("http://127.0.0.1:8317/v8/management/credentials", "Bearer cliproxy-management"),
        (
            "http://127.0.0.1:8317/v8/management/plugins/quota-plugin/quota",
            "Bearer cliproxy-management",
        ),
    ]


def test_config_rejects_unknown_profile_and_secret_fields(tmp_path: Path) -> None:
    path = tmp_path / "models.yaml"
    path.write_text("profile: missing\nprofiles: {}\nproviders: {}", encoding="utf-8")
    with pytest.raises(ValueError, match="Unknown model profile"):
        load_config(path)
    data = load_config().model_dump()
    data["providers"]["cliproxy"]["api_key"] = "do-not-store"
    with pytest.raises(ValueError):
        RouterConfig.model_validate(data)


def test_override_contexts_do_not_share_results(config: RouterConfig) -> None:
    router = ModelRouter(config, fake_models(fake("ok")))
    first, second = RunContext(), RunContext()
    router.resolve_model(first)
    assert second.effective_models == {}
    assert replace(first, model="tier:coding").effective_models is first.effective_models
