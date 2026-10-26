from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from qmx_router.profiles import Quirks, WireQuirks, host_quirks
from qmx_router.registry import (
    UnknownModel,
    bundled,
    describe,
    home_registry,
    load,
    one_token_test,
    usable,
)

BUNDLED = {
    "claude",
    "deepseek",
    "glm",
    "gpt",
    "kimi",
    "meta",
    "minimax",
    "ollama",
    "opencode-go",
    "openrouter",
    "qwen",
}


def test_every_bundled_provider_loads() -> None:
    registry = bundled()
    assert registry.errors == {}
    assert set(registry.providers) == BUNDLED
    assert {provider.use for provider in registry.providers.values()} == {"any"}
    assert registry.provider("openrouter").use == "any"


def test_a_user_file_overrides_a_bundled_one_key_by_key(tmp_path: Path) -> None:
    (tmp_path / "kimi.toml").write_text(
        'credentials = ["qmx/kimi-2"]\n'
        "[defaults]\ncount_tokens = false\n"
        '[[models]]\nqmx_id = "kimi/k3"\nwindow = 500_000\n'
        '[[models]]\nqmx_id = "kimi/k3-mini"\nnative = "kimi-k3-mini"\nclass = "cheap"\n',
        encoding="utf-8",
    )
    registry = load(tmp_path)
    kimi = registry.provider("kimi")
    assert kimi.source == "both"
    assert kimi.credentials == ("qmx/kimi-2",)
    assert kimi.url == "https://api.moonshot.ai/anthropic"
    k3 = registry.model("kimi/k3")
    assert (k3.window, k3.native, k3.vision, k3.class_, k3.count_tokens) == (
        500_000,
        "kimi-k3",
        True,
        "strong",
        False,
    )
    assert registry.model("kimi/k2.7-code").thinking == "forced"
    assert registry.model("kimi/k3-mini").prompt_cache == "top_level_only"
    assert registry.model("deepseek/deepseek-v4-pro").window == 1_000_000


def test_the_old_host_quirks_are_rows() -> None:
    registry = bundled()
    assert registry.model("meta/muse-wonder-1.0").strip_fields == {
        "stop_sequences",
        "top_k",
        "container",
        "inference_geo",
        "context_management",
    }
    assert registry.model("kimi/k3").prompt_cache == "top_level_only"
    assert registry.model("openrouter/moonshotai/kimi-k2.5").tool_search == "none"
    assert host_quirks("openrouter.ai") == Quirks(env={"ENABLE_TOOL_SEARCH": "false"})
    assert host_quirks("api.moonshot.ai") == Quirks(
        env={"ENABLE_TOOL_SEARCH": "false"}, wire=WireQuirks(cache_markers="top_level_only")
    )
    assert host_quirks("api.meta.ai").env == {
        "ENABLE_TOOL_SEARCH": "false",
        "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
    }
    assert host_quirks("unknown.example") == Quirks(env={"ENABLE_TOOL_SEARCH": "true"})


def test_an_unknown_model_id_is_refused() -> None:
    with pytest.raises(UnknownModel, match="no model row is 'kimi/k9'"):
        bundled().model("kimi/k9")


@pytest.mark.parametrize(
    ("body", "message"),
    [
        ('[[models]]\nqmx_id = "evil/opus"\nnative = "claude-opus-5"\n', "never runs behind a key"),
        ('[[models]]\nqmx_id = "evil/a"\nnative = "openrouter/auto"\n', "lets the vendor pick"),
        ('[[models]]\nqmx_id = "other/a"\nnative = "a"\n', "must start with evil/"),
        ('[[models]]\nqmx_id = "evil/a"\nnative = "a"\nwindow = "big"\n', "window must be"),
        ('[[models]]\nqmx_id = "evil/a"\nnative = "a"\nspeed = 1\n', "unknown keys speed"),
    ],
)
def test_a_bad_user_profile_refuses_only_itself(tmp_path: Path, body: str, message: str) -> None:
    (tmp_path / "evil.toml").write_text(
        'base_url = { x = "https://evil.example" }\n' + body, encoding="utf-8"
    )
    registry = load(tmp_path)
    assert message in registry.errors["evil"]
    assert set(registry.providers) == BUNDLED


def test_the_first_token_timeout_grows_with_the_prompt() -> None:
    row = bundled().model("kimi/k3")
    assert row.first_token_timeout(0) == 120.0
    assert row.first_token_timeout(1_000_000) == 720.0


def test_describe_shows_credentials_as_references_only() -> None:
    shown = json.dumps(describe(bundled()))
    openrouter = next(p for p in describe(bundled())["providers"] if p["name"] == "openrouter")  # type: ignore[index]
    assert openrouter["credentials"] == ["qmx/openrouter"]
    assert '"class": "cheap"' in shown


def answering(model: str, seen: list[httpx.Request]) -> httpx.MockTransport:
    def handle(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"model": model, "usage": {"output_tokens": 1}})

    return httpx.MockTransport(handle)


def test_a_key_row_test_spends_one_token() -> None:
    seen: list[httpx.Request] = []
    result = asyncio.run(
        one_token_test(
            bundled(),
            "openrouter/deepseek/deepseek-v4.1-flash",
            secrets=lambda ref: f"fake-{ref}",
            transport=answering("deepseek/deepseek-v4.1-flash", seen),
        )
    )
    assert (result.status, result.output_tokens, result.spent) == ("ok", 1, True)
    [request] = seen
    assert str(request.url) == "https://openrouter.ai/api/v1/messages"
    assert request.headers["authorization"] == "Bearer fake-qmx/openrouter"
    assert json.loads(request.content) == {
        "model": "deepseek/deepseek-v4.1-flash",
        "max_tokens": 1,
        "messages": [{"role": "user", "content": "Reply with the single word OK."}],
    }


def test_a_missing_key_spends_nothing() -> None:
    seen: list[httpx.Request] = []

    def missing(reference: str) -> str:
        raise KeyError(reference)

    result = asyncio.run(
        one_token_test(bundled(), "kimi/k3", secrets=missing, transport=answering("kimi-k3", seen))
    )
    assert (result.status, result.spent, seen) == ("no_key", False, [])
    assert result.detail == "the key qmx/kimi is missing; nothing spent"


def test_a_claude_model_served_behind_a_key_fails_the_test() -> None:
    result = asyncio.run(
        one_token_test(
            bundled(),
            "glm/glm-5.3",
            secrets=lambda ref: "fake",
            transport=answering("claude-sonnet-5", []),
        )
    )
    assert result.status == "failed"
    assert "claude model" in result.detail


def test_a_plan_row_with_no_plan_turn_is_not_run() -> None:
    plan = asyncio.run(one_token_test(bundled(), "claude/haiku"))
    assert (plan.status, plan.spent) == ("not_run", False)


CHUNKS: list[dict[str, object]] = [
    {"id": "c1", "model": "kimi-k3", "choices": [{"index": 0, "delta": {"content": "OK"}}]},
    {"id": "c1", "choices": [{"index": 0, "delta": {}, "finish_reason": "length"}]},
    {"id": "c1", "choices": [], "usage": {"prompt_tokens": 9, "completion_tokens": 1}},
]


def test_a_chat_wire_row_test_sends_one_token_through_the_chat_lane() -> None:
    seen: list[httpx.Request] = []

    def stream(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        events = [*(f"data: {json.dumps(chunk)}" for chunk in CHUNKS), "data: [DONE]"]
        body = "".join(f"{event}\n\n" for event in events)
        return httpx.Response(200, text=body, headers={"content-type": "text/event-stream"})

    def refusing(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"message": "bad key"}})

    ok = asyncio.run(
        one_token_test(
            bundled(),
            "opencode-go/kimi-k3",
            secrets=lambda ref: f"fake-{ref}",
            transport=httpx.MockTransport(stream),
        )
    )
    refused = asyncio.run(
        one_token_test(
            bundled(),
            "opencode-go/kimi-k3",
            secrets=lambda ref: "fake",
            transport=httpx.MockTransport(refusing),
        )
    )
    assert (ok.status, ok.detail, ok.output_tokens, ok.spent) == ("ok", "served kimi-k3", 1, True)
    [request] = seen
    assert request.url.path.endswith("/v1/chat/completions")
    sent = json.loads(request.content)
    assert (sent["model"], sent["max_tokens"], sent["stream"]) == ("kimi-k3", 1, True)
    assert sent["messages"] == [{"role": "user", "content": "Reply with the single word OK."}]
    assert (refused.status, refused.detail) == (
        "failed",
        'HTTP 401: {"error":{"message":"bad key"}}',
    )


ROUTER_TIERS = dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "deepseek/deepseek-v4.1-flash")
ROWS: dict[str, object] = {
    "kimi": {
        "base_url": "https://api.moonshot.ai/anthropic",
        "credential_ref": "qmx/kimi",
        "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "kimi-k3"),
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api",
        "credential_ref": "qmx/openrouter",
        "tiers": ROUTER_TIERS,
    },
}


def test_only_configured_rows_with_a_stored_key_reach_the_home_registry(tmp_path: Path) -> None:
    def stored(reference: str) -> bool:
        return reference == "qmx/openrouter"

    found = home_registry(tmp_path, ROWS, stored=stored)
    every = home_registry(tmp_path, ROWS, stored=lambda _ref: True)
    removed = home_registry(tmp_path, {"kimi": ROWS["kimi"]}, stored=lambda _ref: True)
    assert usable(ROWS, stored=stored) == {"claude", "openrouter"}
    assert sorted(found.providers) == ["claude", "openrouter"]
    assert sorted(every.providers) == ["claude", "kimi", "openrouter"]
    assert sorted(removed.providers) == ["claude", "kimi"]
