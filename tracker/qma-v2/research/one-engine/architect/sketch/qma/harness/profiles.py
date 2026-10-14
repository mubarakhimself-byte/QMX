"""Provider profiles: which model host a chat's CLI process talks to.

Every profile runs the same engine (the Claude Code CLI through the Agent SDK).
A profile only decides the routing environment and the Claude home of that one process.

Invariants encoded here, not checked later:
- A third-party base URL cannot exist without its own credential. `KeyProvider`
  has both as required fields, so the CLI never falls back to the plan login and
  sends the operator's Claude token to a third-party host (02a trap 7).
- The plan profile carries no secret and no URL. QMA never reads or stores the
  Claude token (hard rule 1). The CLI's own /login owns it.
- No Claude or GPT model behind a key (old V4.1 family guard, rule R4), and no router
  slug that could pick one. Enforced in `parse_profiles` and, per request, by the relay
  through `resolve_model` for the requested model and `family_refusal` for the served one.
  `resolve_model` calls `family_refusal`, so the family rule lives once.
- Every tier is pinned on a key provider. Kimi warns that partial tier maps fail
  silently (02b B), and Claude Code sends background work to the haiku tier.
- A key provider's credential is a keyring reference that only the relay reads
  (`qma.harness.relay`). It never becomes an environment value.

Rows come from `settings.toml [providers]` (UI-editable through the existing
`ControlService.settings_put`, which already forces `credential_ref`).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final, Literal, NewType

ProfileName = NewType("ProfileName", str)
ModelId = NewType("ModelId", str)
BaseUrl = NewType("BaseUrl", str)
"""An https URL, parsed once in `parse_profiles`. Plain http only for a loopback host and
only when `TestMode.loopback_http_provider` is set (S9, S21)."""
SecretRef = NewType("SecretRef", str)
"""A `qmx/<name>` OS-keyring reference. Never the secret itself."""

PLAN: Final = ProfileName("claude")
GPT: Final = ProfileName("gpt")


@dataclass(frozen=True)
class TierMap:
    """The model each Claude Code tier alias resolves to. Total by construction."""

    opus: ModelId
    sonnet: ModelId
    haiku: ModelId
    fable: ModelId


@dataclass(frozen=True)
class ClaudePlan:
    """The operator's one Claude Max plan, signed in through the CLI's /login."""

    name: ProfileName = PLAN


@dataclass(frozen=True)
class WireQuirks:
    """Request edits the relay applies to one provider's traffic, and nothing else.

    Only what a vendor documents as rejected or ignored (02b B). Everything not named
    here is forwarded unchanged, including `anthropic-beta`, `cache_control`, system
    order and SSE pings (02b C item 5).
    """

    strip_fields: frozenset[str] = frozenset()
    """Top-level body fields that make the vendor return 400. Meta: `stop_sequences`,
    `top_k`, `container`, `inference_geo`, `context_management`."""
    cache_markers: Literal["as_sent", "top_level_only"] = "as_sent"
    """Kimi ignores block-level `cache_control`; `top_level_only` moves one marker to the
    top level (02b B, Kimi caching quirk). Whether that restores cache reads is check S8."""
    auth_header: Literal["bearer", "x-api-key"] = "bearer"
    """How the vendor wants its key. Every current vendor accepts Bearer (02b table)."""


@dataclass(frozen=True)
class Quirks:
    """Per-vendor quirks as data, so a new quirk is a settings edit, not a code change."""

    env: Mapping[str, str] = field(default_factory=dict)
    """CLI knobs for this provider's processes. Keys limited to `QUIRK_ENV_KEYS`;
    routing keys can never appear here. `parse_profiles` adds ENABLE_TOOL_SEARCH="true"
    to a key row that does not set it (tool search is off by default behind a base URL,
    02a section 7)."""
    wire: WireQuirks = field(default_factory=WireQuirks)


@dataclass(frozen=True)
class KeyProvider:
    """An Anthropic-compatible host: Kimi, GLM, DeepSeek, MiniMax, Meta Muse, OpenRouter.

    The CLI never talks to `base_url` directly. Its base URL is the relay, which swaps in
    the key named by `credential` per request.
    """

    name: ProfileName
    base_url: BaseUrl
    credential: SecretRef
    tiers: TierMap
    quirks: Quirks = field(default_factory=Quirks)


GPT_QUIRKS: Final = Quirks(
    env={
        "ENABLE_TOOL_SEARCH": "false",  # tool_search is unsupported on the SIWC route (02b)
        "CLAUDE_CODE_MAX_RETRIES": "2",  # do not hammer a plan limit (translate.map_error)
        "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS": "1",  # 02b D P6
    }
)


@dataclass(frozen=True)
class GptPlan:
    """GPT through the operator's ChatGPT sign-in, via the relay's GPT lane.

    No URL or secret lives on the row. The CLI's base URL and bearer come from a relay
    grant, and `Relay.grant` refuses a GPT grant until the GPT lane is open, which needs
    a `ProbePassed` (qma.gpt.probe).
    """

    tiers: TierMap
    name: ProfileName = GPT
    quirks: Quirks = GPT_QUIRKS


type Profile = ClaudePlan | KeyProvider | GptPlan

QUIRK_ENV_KEYS: Final[frozenset[str]] = frozenset(
    {
        "ENABLE_TOOL_SEARCH",
        "CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS",  # Meta rejects unknown fields
        "CLAUDE_CODE_AUTO_COMPACT_WINDOW",  # vendor context caps
        "API_TIMEOUT_MS",
        "CLAUDE_CODE_MAX_RETRIES",
    }
)

FORBIDDEN_ON_KEY: Final[tuple[str, ...]] = ("claude", "anthropic", "gpt", "openai", "chatgpt", "codex")
"""Fragments refused in any segment of a model id behind a key."""

OPENAI_REASONING_SEGMENT: Final = r"^o\d+($|-)"
"""A segment that is an OpenAI reasoning family name (`o3`, `o4-mini`). A regex on the whole
segment, not a substring, so a future vendor id that merely contains `o3` passes."""

ROUTER_SLUGS: Final[tuple[str, ...]] = ("openrouter/", "@preset/")
"""Prefixes of ids that let the vendor choose the model. Refused, as is any segment equal to
`auto`, because the vendor could route them to Claude or GPT (A18, B15)."""


def family_refusal(profile: KeyProvider | GptPlan, model: str) -> str | None:
    """Pure. The family test alone: a refusal reason, or None.

    Normalise first: strip a trailing `[1m]`-style suffix and lowercase. Split on `/` and
    `:` into segments. KeyProvider: refused if any segment contains a `FORBIDDEN_ON_KEY`
    fragment, matches `OPENAI_REASONING_SEGMENT`, equals `auto`, or the id starts with a
    `ROUTER_SLUGS` prefix. GptPlan: refused unless the id is a GPT-family id.
    The relay checks the served model (`message_start.message.model`) with this alone,
    because vendors report dated or canonical ids that differ from the requested one
    (fix check 2.7)."""
    raise NotImplementedError


def resolve_model(profile: Profile, requested: str) -> ModelId | str | None:
    """Pure. The one parser for a requested model id, used by `quote` for `ChatConfig.model`
    and by the relay for every requested model (A28). None means refused.

    ClaudePlan: tier aliases and `claude-*` ids pass through for the CLI to resolve.
    KeyProvider and GptPlan: `family_refusal` first, then the tier test: a tier alias maps
    through `tiers`, and an id must equal a tier model after the same normalisation.
    """
    raise NotImplementedError


@dataclass(frozen=True)
class Profiles:
    """All configured profiles, keyed by name. Always contains the plan profile."""

    by_name: Mapping[ProfileName, Profile]
    delegate_targets: frozenset[ProfileName]
    """Profiles an agent may name in `mcp__qmx__delegate`. UI-editable allow-list."""

    def get(self, name: ProfileName) -> Profile:
        raise NotImplementedError


class ProfileError(ValueError):
    """A settings row that cannot become a profile. Raised at the boundary only."""


def parse_profiles(rows: Mapping[str, object], *, allow_loopback_http: bool = False) -> Profiles:
    """Parse `settings.toml [providers]` into typed profiles.

    Refuses: a base URL that is not https (plain http to 127.0.0.1 only when
    `allow_loopback_http`, which only `TestMode` sets); a credential that is not `qmx/*`;
    any tier model `resolve_model` would refuse; a `quirks.env` key outside
    `QUIRK_ENV_KEYS`; a row named `claude` or `gpt` that is not the built-in kind; a GPT row
    whose tiers are not GPT models.
    Always adds `ClaudePlan()`. Adds `GptPlan` only when a `gpt` row exists.
    """
    raise NotImplementedError
