from __future__ import annotations

import re
from typing import Any

import pytest

from qma.harness.profiles import (
    PLAN,
    BaseUrl,
    ClaudePlan,
    KeyProvider,
    ModelId,
    ProfileError,
    ProfileName,
    Quirks,
    SecretRef,
    TierMap,
    WireQuirks,
    family_refusal,
    parse_profiles,
    resolve_model,
)

KIMI = KeyProvider(
    name=ProfileName("kimi"),
    base_url=BaseUrl("https://api.moonshot.ai/anthropic"),
    credential=SecretRef("qmx/kimi"),
    tiers=TierMap(
        opus=ModelId("kimi-k3"),
        sonnet=ModelId("kimi-k3"),
        haiku=ModelId("kimi-k2.6"),
        fable=ModelId("kimi-k3"),
    ),
)
ROUTER = KeyProvider(
    name=ProfileName("openrouter"),
    base_url=BaseUrl("https://openrouter.ai/api"),
    credential=SecretRef("qmx/openrouter"),
    tiers=TierMap(*[ModelId("deepseek/deepseek-v4.1-flash")] * 4),
)


@pytest.mark.parametrize(
    ("profile", "requested", "resolved"),
    [
        (ClaudePlan(), "opus", "opus"),
        (ClaudePlan(), "haiku", "haiku"),
        (ClaudePlan(), "opus[1m]", "opus[1m]"),
        (ClaudePlan(), "claude-opus-5-5", "claude-opus-5-5"),
        (ClaudePlan(), "kimi-k3", None),
        (KIMI, "opus", "kimi-k3"),
        (KIMI, "haiku", "kimi-k2.6"),
        (KIMI, "Sonnet[1m]", "kimi-k3"),
        (KIMI, "kimi-k3", "kimi-k3"),
        (KIMI, "kimi-k3[1m]", "kimi-k3"),
        (KIMI, "KIMI-K3", "kimi-k3"),
        (KIMI, "\uff4b\uff49\uff4d\uff49-k3", "kimi-k3"),
        (KIMI, "kimi\u200b-k3", "kimi-k3"),
        (KIMI, "k\u0456mi-k3", None),
        (KIMI, "kimi-k2.7-code", None),
        (KIMI, "claude-opus-5-5", None),
        (KIMI, "claude-opus-5-5[1m]", None),
        (KIMI, "gpt-5.5", None),
        (KIMI, "o3", None),
        (KIMI, "o4-mini", None),
        (KIMI, "auto", None),
        (KIMI, "", None),
        (ROUTER, "deepseek/deepseek-v4.1-flash", "deepseek/deepseek-v4.1-flash"),
        (ROUTER, "opus", "deepseek/deepseek-v4.1-flash"),
        (ROUTER, "openrouter/auto", None),
        (ROUTER, "@preset/x", None),
        (ROUTER, "~anthropic/claude-sonnet-latest", None),
        (ROUTER, "openai/gpt-5", None),
        (ROUTER, "openai/o3", None),
        (ROUTER, "anthropic/claude-opus-5-5", None),
        (ROUTER, "deepseek/deepseek-v4.1-flash:auto", None),
        (ROUTER, "deepseek/deepseek-v4-flash-0731", None),
    ],
)
def test_resolve_model(profile: Any, requested: str, resolved: str | None) -> None:
    assert resolve_model(profile, requested) == resolved


@pytest.mark.parametrize(
    ("served", "refused"),
    [
        ("kimi-k3-20261001", False),
        ("deepseek/deepseek-v4.1-flash-20261001", False),
        ("muse-o3x", False),
        ("claude-opus-x", True),
        ("anthropic/claude-3", True),
        ("gpt-5", True),
        ("o3-pro", True),
        ("openrouter/auto", True),
        ("\u0430nthropic/\u0441laude-opus-4", True),
        ("c\u200blaude-3", True),
        ("\uff43\uff4c\uff41\uff55\uff44\uff45-x", True),
    ],
)
def test_the_family_test_alone_passes_dated_ids_of_an_allowed_family(
    served: str, refused: bool
) -> None:
    assert (family_refusal(served) is not None) is refused


OPENROUTER_ROW: dict[str, object] = {
    "base_url": "https://openrouter.ai/api/",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "deepseek/deepseek-v4.1-flash"),
}


def test_a_row_becomes_a_key_provider_with_its_host_quirks() -> None:
    profiles = parse_profiles({"openrouter": OPENROUTER_ROW, "litestream": {"db": "s3://x"}})
    assert profiles.get("claude") == ClaudePlan()
    assert profiles.get("openrouter") == KeyProvider(
        name=ProfileName("openrouter"),
        base_url=BaseUrl("https://openrouter.ai/api"),
        credential=SecretRef("qmx/openrouter"),
        tiers=TierMap(*[ModelId("deepseek/deepseek-v4.1-flash")] * 4),
        quirks=Quirks(env={"ENABLE_TOOL_SEARCH": "true"}),
    )
    assert set(profiles.by_name) == {PLAN, "openrouter"}


def test_a_row_overrides_the_host_defaults() -> None:
    row = OPENROUTER_ROW | {
        "base_url": "https://api.meta.ai",
        "quirks": {"env": {"ENABLE_TOOL_SEARCH": "false"}, "wire": {"auth_header": "x-api-key"}},
    }
    meta = parse_profiles({"meta": row}).get("meta")
    assert isinstance(meta, KeyProvider)
    assert meta.quirks == Quirks(
        env={"ENABLE_TOOL_SEARCH": "false", "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1"},
        wire=WireQuirks(
            strip_fields=frozenset(
                {"stop_sequences", "top_k", "container", "inference_geo", "context_management"}
            ),
            auth_header="x-api-key",
        ),
    )


@pytest.mark.parametrize(
    ("name", "row", "message"),
    [
        ("claude", OPENROUTER_ROW, "[providers.claude] is a reserved name"),
        ("gpt", OPENROUTER_ROW, "[providers.gpt] is a reserved name"),
        ("x", OPENROUTER_ROW | {"base_url": "http://openrouter.ai/api"}, "must be an https URL"),
        ("x", OPENROUTER_ROW | {"base_url": "http://127.0.0.1:9"}, "must be an https URL"),
        ("x", OPENROUTER_ROW | {"base_url": "https://h/?a=1"}, "must not carry a query"),
        ("x", OPENROUTER_ROW | {"credential_ref": "openrouter"}, "keyring reference"),
        ("x", OPENROUTER_ROW | {"api_key": "v"}, "unknown keys api_key"),
        ("x", OPENROUTER_ROW | {"tiers": {"opus": "m"}}, "every tier is pinned"),
        (
            "x",
            OPENROUTER_ROW | {"tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), "o3")},
            "tiers.opus: o3 is an OpenAI model",
        ),
        ("x", OPENROUTER_ROW | {"quirks": {"env": {"HTTPS_PROXY": "p"}}}, "unknown keys"),
        (
            "x",
            OPENROUTER_ROW | {"quirks": {"wire": {"strip_fields": ["model"]}}},
            "cannot remove model",
        ),
        ("x", "not a table", "the row must be a table"),
    ],
)
def test_a_bad_row_is_refused_by_name(name: str, row: object, message: str) -> None:
    profiles = parse_profiles({name: row, "openrouter": OPENROUTER_ROW})
    assert message in profiles.errors[name]
    assert isinstance(profiles.get("openrouter"), KeyProvider)
    assert profiles.get(PLAN) == ClaudePlan()
    if name != PLAN:
        with pytest.raises(ProfileError, match=re.escape(message)):
            profiles.get(name)


def test_plain_http_to_loopback_needs_the_test_switch() -> None:
    row = OPENROUTER_ROW | {"base_url": "http://127.0.0.1:8123"}
    fake = parse_profiles({"fake": row}, allow_loopback_http=True).get("fake")
    assert isinstance(fake, KeyProvider)
    assert fake.base_url == "http://127.0.0.1:8123"
    assert fake.quirks == Quirks(env={"ENABLE_TOOL_SEARCH": "true"})


def test_an_unknown_profile_is_refused() -> None:
    with pytest.raises(ProfileError, match="no provider is named 'kimi'"):
        parse_profiles({}).get("kimi")
