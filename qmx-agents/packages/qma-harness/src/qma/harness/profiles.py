"""Provider profiles: which model host a chat's CLI process talks to.

Every profile runs the same engine. A profile only decides the routing environment and the
Claude home of that one process.

- A third-party base URL cannot exist without its own credential. `KeyProvider` has both as
  required fields, so the CLI never falls back to a plan login and sends a Claude token to a
  third-party host.
- The plan profile carries no secret and no URL. The CLI's own /login owns the plan token.
- No Claude or GPT model behind a key, and no router slug that could pick one.
  `resolve_model` calls `family_refusal`, so the family rule lives once; the relay runs it on
  the requested and the served model.
- Every tier is pinned on a key provider, because the CLI sends background work to the haiku
  tier and an unpinned tier fails silently on some vendors.
- A key provider's credential is a keyring reference that only the relay reads.
- `GptPlan` is GPT through the operator's ChatGPT sign-in, through the relay's GPT lane. Its
  row holds only the four tiers, each a GPT model, and its quirks are fixed.

Rows come from `settings.toml [providers]`.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from typing import Final, Literal, NewType, cast, get_args
from urllib.parse import urlsplit

ProfileName = NewType("ProfileName", str)
ModelId = NewType("ModelId", str)
BaseUrl = NewType("BaseUrl", str)
"""https, or plain http to 127.0.0.1 only when `TestMode.loopback_http_provider` is set."""
SecretRef = NewType("SecretRef", str)
"""A `qmx/<name>` OS-keyring reference. Never the secret itself."""

PLAN: Final = ProfileName("claude")
GPT: Final = ProfileName("gpt")
RESERVED: Final = frozenset({PLAN, GPT})
"""Names of the built-in kinds. A `gpt` row becomes a `GptPlan`, never a key provider."""
DELEGATE_TARGETS: Final = "delegate_targets"
"""`[providers] delegate_targets = ["kimi", ...]`: the profiles an agent may name in
`mcp__qmx_delegate__run`. Missing means none."""
NON_MODEL_ROWS: Final = frozenset({"litestream", DELEGATE_TARGETS})
"""`[providers]` keys that are not model hosts."""

type CacheMarkers = Literal["as_sent", "top_level_only"]
type AuthHeader = Literal["bearer", "x-api-key"]


@dataclass(frozen=True)
class TierMap:
    """The model each Claude Code tier alias resolves to. Total by construction."""

    opus: ModelId
    sonnet: ModelId
    haiku: ModelId
    fable: ModelId

    def get(self, alias: str) -> ModelId | None:
        return cast("ModelId | None", getattr(self, alias, None)) if alias in TIERS else None

    def models(self) -> tuple[ModelId, ...]:
        return tuple(getattr(self, tier.name) for tier in fields(self))


TIERS: Final = tuple(tier.name for tier in fields(TierMap))
TIER_ENV: Final[Mapping[str, str]] = {
    tier: f"ANTHROPIC_DEFAULT_{tier.upper()}_MODEL" for tier in TIERS
}


@dataclass(frozen=True)
class ClaudePlan:
    """The operator's one Claude Max plan, signed in through the CLI's /login."""

    name: ProfileName = PLAN


@dataclass(frozen=True)
class WireQuirks:
    """Request edits the relay applies to one provider's traffic, and nothing else. Everything
    not named here is forwarded unchanged, including `anthropic-beta`, `cache_control`, system
    order and SSE pings."""

    strip_fields: frozenset[str] = frozenset()
    """Top-level body fields that make the vendor return 400."""
    cache_markers: CacheMarkers = "as_sent"
    """`top_level_only` adds one top-level marker for a vendor that ignores block markers."""
    auth_header: AuthHeader = "bearer"


@dataclass(frozen=True)
class Quirks:
    env: Mapping[str, str] = field(default_factory=dict[str, str])
    """CLI knobs for this provider's processes, keys limited to `QUIRK_ENV_KEYS`."""
    wire: WireQuirks = field(default_factory=WireQuirks)


@dataclass(frozen=True)
class KeyProvider:
    """An Anthropic-compatible host. The CLI never talks to `base_url` directly: its base URL
    is the relay, which swaps in the key named by `credential` per request."""

    name: ProfileName
    base_url: BaseUrl
    credential: SecretRef
    tiers: TierMap
    quirks: Quirks = field(default_factory=Quirks)


GPT_QUIRKS: Final = Quirks(
    env={
        "ENABLE_TOOL_SEARCH": "false",
        "CLAUDE_CODE_MAX_RETRIES": "2",
        "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",
    }
)
"""Fixed. The ChatGPT route refuses `tool_search`, a usage-limit 429 must not be retried into
the plan limit again and again, and beta-only fields have no Responses mapping (02b D)."""


@dataclass(frozen=True)
class GptPlan:
    """GPT through the operator's ChatGPT sign-in. The CLI talks to the relay's GPT lane, which
    translates to OpenAI Responses. `Relay.grant` refuses it until the lane is open, which needs
    a stored `ProbePassed` for the current translator."""

    tiers: TierMap
    name: ProfileName = GPT
    quirks: Quirks = GPT_QUIRKS


type Profile = ClaudePlan | KeyProvider | GptPlan

QUIRK_ENV_KEYS: Final = frozenset(
    {
        "ENABLE_TOOL_SEARCH",
        "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS",
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW",
        "API_TIMEOUT_MS",
        "CLAUDE_CODE_MAX_RETRIES",
        "CLAUDE_CODE_MAX_OUTPUT_TOKENS",
    }
)

HOST_QUIRKS: Final[Mapping[str, Quirks]] = {
    "openrouter.ai": Quirks(env={"ENABLE_TOOL_SEARCH": "false"}),
    "api.meta.ai": Quirks(
        env={"ENABLE_TOOL_SEARCH": "true", "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1"},
        wire=WireQuirks(
            strip_fields=frozenset(
                {"stop_sequences", "top_k", "container", "inference_geo", "context_management"}
            )
        ),
    ),
    "api.moonshot.ai": Quirks(
        env={"ENABLE_TOOL_SEARCH": "true"}, wire=WireQuirks(cache_markers="top_level_only")
    ),
}
"""Defaults a row's own `quirks` override. OpenRouter keeps tool search off: with it on, every
chat's `qmx` tools go out deferred, and OpenRouter answers 400 "Deferred custom tools are only
supported on Anthropic models" for `moonshotai/kimi-k2.5` (HP12 check 8) and
`deepseek-v4-flash-0731` (HP1). With it off, Kimi K2.5 ran a Bash call (HP12 check 8) and
`deepseek/deepseek-v4.1-flash` answered (HP12 fix round; HP1's B1 Bash call ran with it off).
Meta and the Moonshot API are the vendors' documented
rejections, not yet probed with a key; their `true` may hit the same 400."""
KEY_QUIRKS: Final = Quirks(env={"ENABLE_TOOL_SEARCH": "true"})
"""Tool search is off by default behind a base URL."""

FORBIDDEN_ON_KEY: Final = ("claude", "anthropic", "gpt", "openai", "chatgpt", "codex")
OPENAI_REASONING_SEGMENT: Final = re.compile(r"^o\d+($|-)")
GPT_MODEL: Final = re.compile(r"gpt-\d[a-z0-9.-]*")
"""A GPT id as `/v1/models` lists them on the ChatGPT route, such as `gpt-6.1-sol`."""
ROUTER_SLUGS: Final = ("openrouter/", "@preset/", "~")
"""Prefixes that let the vendor choose the model, which could be Claude or GPT."""
SUFFIX: Final = re.compile(r"\[[^\]]*\]$")
ROW_NAME: Final = re.compile(r"[a-z0-9][a-z0-9_-]{0,39}")
SECRET_REF: Final = re.compile(r"qmx/[a-z0-9][a-z0-9_-]{0,39}")


def normalize(model: str) -> str:
    """NFKC, without format characters such as zero-width spaces, lowercase, and without a
    trailing `[1m]`-style suffix. Lookalike letters from other scripts survive, so the caller
    refuses anything that is not ASCII."""
    folded = "".join(
        char for char in unicodedata.normalize("NFKC", model) if unicodedata.category(char) != "Cf"
    )
    return SUFFIX.sub("", folded.strip()).lower()


def family_refusal(model: str) -> str | None:
    """A refusal reason when `model` may not run behind a key, or None. The relay checks the
    served model with this alone, because vendors report dated or canonical ids."""
    norm = normalize(model)
    if not norm:
        return "no model id"
    if not norm.isascii():
        return f"{model!r} is not an ASCII model id"
    if norm.startswith(ROUTER_SLUGS):
        return f"{model} lets the vendor pick the model"
    for segment in re.split(r"[/:]", norm):
        if segment == "auto":
            return f"{model} lets the vendor pick the model"
        if OPENAI_REASONING_SEGMENT.match(segment):
            return f"{model} is an OpenAI model"
        found = next((frag for frag in FORBIDDEN_ON_KEY if frag in segment), None)
        if found:
            return f"{model} is a {found} model, which never runs behind a key"
    return None


def gpt_refusal(model: str) -> str | None:
    """A refusal reason when `model` is not a GPT id, or None. The GPT lane checks the requested
    and the served model with it."""
    norm = normalize(model)
    if norm.isascii() and GPT_MODEL.fullmatch(norm):
        return None
    return f"{model!r} is not a GPT model"


def resolve_model(profile: Profile, requested: str) -> ModelId | None:
    """The one parser for a requested model id, used for `ChatConfig.model` and by the relay.
    None means refused. Behind a key or on GPT an id must be a tier alias or equal a tier model
    after normalization, and the result is that tier's pinned id, which the relay forwards."""
    norm = normalize(requested)
    match profile:
        case ClaudePlan():
            return ModelId(requested) if norm in TIERS or norm.startswith("claude-") else None
        case KeyProvider(tiers=tiers) | GptPlan(tiers=tiers):
            family = gpt_refusal if isinstance(profile, GptPlan) else family_refusal
            if norm not in TIERS and family(requested):
                return None
            alias = tiers.get(norm)
            if alias is not None:
                return alias
            pinned = {normalize(model): model for model in tiers.models()}
            return pinned.get(norm)


@dataclass(frozen=True)
class Profiles:
    """All configured profiles by name. Always holds the plan profile. A row that does not
    validate is kept in `errors` and refuses only its own name."""

    by_name: Mapping[ProfileName, Profile]
    errors: Mapping[str, str] = field(default_factory=dict[str, str])
    delegate_targets: frozenset[ProfileName] = frozenset()
    """Profiles an agent may name in `mcp__qmx_delegate__run`. UI-editable allow-list."""

    def get(self, name: str) -> Profile:
        found = self.by_name.get(ProfileName(name))
        if found is not None:
            return found
        raise ProfileError(self.errors.get(name, f"no provider is named {name!r}"))

    def delegate_refusal(self, name: str) -> str | None:
        """Why an agent may not delegate to `name`, or None."""
        if name in self.delegate_targets:
            return None
        listed = ", ".join(sorted(self.delegate_targets)) or "nothing"
        return (
            f"{name!r} is not in the delegate allow-list, [providers] {DELEGATE_TARGETS}, "
            f"which lists {listed}"
        )


class ProfileError(ValueError):
    """A settings row that cannot become a profile."""


def parse_profiles(rows: Mapping[str, object], *, allow_loopback_http: bool = False) -> Profiles:
    """`settings.toml [providers]` into typed profiles. A bad row lands in `errors`, worded
    with its row name, and never blocks the plan or another row."""
    found: dict[ProfileName, Profile] = {PLAN: ClaudePlan()}
    errors: dict[str, str] = {}
    for name, row in rows.items():
        if name in NON_MODEL_ROWS:
            continue
        try:
            found[ProfileName(name)] = (
                _gpt_plan(row) if name == GPT else _key_provider(name, row, allow_loopback_http)
            )
        except ProfileError as error:
            errors[name] = f"[providers.{name}] {error}"
    targets = rows.get(DELEGATE_TARGETS, [])
    if not isinstance(targets, list):
        errors[DELEGATE_TARGETS] = f"[providers] {DELEGATE_TARGETS} must be a list of names"
        targets = []
    named = frozenset(
        ProfileName(name) for name in cast("list[object]", targets) if isinstance(name, str)
    )
    return Profiles(found, errors, named)


def _key_provider(name: str, row: object, allow_loopback_http: bool) -> KeyProvider:
    if name in RESERVED:
        raise ProfileError("is a reserved name")
    if not ROW_NAME.fullmatch(name):
        raise ProfileError("needs a lowercase name of letters, digits, - and _")
    table = _table(row, "the row", {"base_url", "credential_ref", "tiers", "quirks"})
    base_url = _base_url(table.get("base_url"), allow_loopback_http)
    credential = table.get("credential_ref")
    if not isinstance(credential, str) or not SECRET_REF.fullmatch(credential):
        raise ProfileError("credential_ref must be a qmx/<name> keyring reference")
    tier_table = _table(table.get("tiers"), "tiers", set(TIERS))
    models: dict[str, ModelId] = {}
    for tier in TIERS:
        model = tier_table.get(tier)
        if not isinstance(model, str):
            raise ProfileError(f"tiers.{tier} must name a model; every tier is pinned")
        refusal = family_refusal(model)
        if refusal:
            raise ProfileError(f"tiers.{tier}: {refusal}")
        models[tier] = ModelId(model)
    host = urlsplit(base_url).hostname or ""
    quirks = _quirks(table.get("quirks"), HOST_QUIRKS.get(host, KEY_QUIRKS))
    return KeyProvider(
        name=ProfileName(name),
        base_url=base_url,
        credential=SecretRef(credential),
        tiers=TierMap(**models),
        quirks=quirks,
    )


def _gpt_plan(row: object) -> GptPlan:
    """`[providers.gpt]` holds only `tiers`. The quirks are fixed and the credential is the
    ChatGPT sign-in, so neither is a field."""
    tier_table = _table(_table(row, "the row", {"tiers"}).get("tiers"), "tiers", set(TIERS))
    models: dict[str, ModelId] = {}
    for tier in TIERS:
        model = tier_table.get(tier)
        if not isinstance(model, str):
            raise ProfileError(f"tiers.{tier} must name a model; every tier is pinned")
        refusal = gpt_refusal(model)
        if refusal:
            raise ProfileError(f"tiers.{tier}: {refusal}")
        models[tier] = ModelId(model)
    return GptPlan(tiers=TierMap(**models))


def _table(value: object, what: str, allowed: set[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProfileError(f"{what} must be a table")
    table = cast("dict[str, object]", value)
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise ProfileError(f"{what} has unknown keys {', '.join(unknown)}")
    return table


def _base_url(value: object, allow_loopback_http: bool) -> BaseUrl:
    if not isinstance(value, str):
        raise ProfileError("base_url must be a URL")
    parts = urlsplit(value)
    loopback = allow_loopback_http and parts.scheme == "http" and parts.hostname == "127.0.0.1"
    if not (parts.scheme == "https" or loopback) or not parts.hostname:
        raise ProfileError("base_url must be an https URL")
    if parts.query or parts.fragment or parts.username or parts.password:
        raise ProfileError("base_url must not carry a query, fragment or user")
    return BaseUrl(value.rstrip("/"))


def _quirks(value: object, defaults: Quirks) -> Quirks:
    if value is None:
        return defaults
    table = _table(value, "quirks", {"env", "wire"})
    env = _table(table.get("env", {}), "quirks.env", set(QUIRK_ENV_KEYS))
    if not all(isinstance(item, str) for item in env.values()):
        raise ProfileError("quirks.env values must be strings")
    wire = _table(
        table.get("wire", {}), "quirks.wire", {"strip_fields", "cache_markers", "auth_header"}
    )
    strip = wire.get("strip_fields", sorted(defaults.wire.strip_fields))
    if not isinstance(strip, list) or not all(
        isinstance(item, str) for item in cast("list[object]", strip)
    ):
        raise ProfileError("quirks.wire.strip_fields must be a list of field names")
    if "model" in strip or "messages" in strip:
        raise ProfileError("quirks.wire.strip_fields cannot remove model or messages")
    markers = wire.get("cache_markers", defaults.wire.cache_markers)
    if markers not in get_args(CacheMarkers.__value__):
        raise ProfileError("quirks.wire.cache_markers must be as_sent or top_level_only")
    auth = wire.get("auth_header", defaults.wire.auth_header)
    if auth not in get_args(AuthHeader.__value__):
        raise ProfileError("quirks.wire.auth_header must be bearer or x-api-key")
    return Quirks(
        env={**defaults.env, **cast("dict[str, str]", env)},
        wire=WireQuirks(
            strip_fields=frozenset(cast("list[str]", strip)),
            cache_markers=cast("CacheMarkers", markers),
            auth_header=cast("AuthHeader", auth),
        ),
    )
