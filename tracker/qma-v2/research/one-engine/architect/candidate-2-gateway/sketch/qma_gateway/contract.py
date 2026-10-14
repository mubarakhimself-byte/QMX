"""The one module qmx-control may import from the gateway package.

Pure data and pure functions. No I/O, no HTTP types, no SDK types. qmx-control
(`qmx_harness`) builds a `GatewayDesired` from settings and live hosts and hands
it to the gateway process. The gateway hands back `GatewayEvent`s. Neither side
shares mutable state: the harness owns the desired state and the durable ledger,
the gateway owns in-flight streams and the ChatGPT token (per
separate-before-serializing-shared-state).

Invariants encoded here rather than checked later:

- The lane decides the credential, and the variant decides the model family.
  A `PlanRoute` can only carry a Claude model and has no URL or credential
  field, so QMA has nowhere to put a Claude token and nowhere to send one
  except the constant Anthropic host (hard rule 1).
- A `KeyModel` is parsed at the settings boundary and refuses Claude and GPT
  family ids, so "Claude or GPT on an API key" (V4.1 family guard, R4) cannot
  be expressed.
- A `GptRoute` exists only with a `ProbeReceipt`, so the translator cannot be
  routable before probes P0 to P7 pass (02b D stop rule).
- A background `LeaseGrant` may include GPT models only with a recorded
  consent, per the Sign in with ChatGPT terms (02b D item 9).
- `RouteTable` has one constructor, `build_route_table`, which rejects
  duplicate model ids. Every derived list (CLI tier pins, `/v1/models`,
  allowed sets, prices) reads the table, so no second model list exists.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import NewType

# ----------------------------------------------------------------------- ids

ModelId = NewType("ModelId", str)
"""The exact string the CLI puts in the request's `model` field."""

UpstreamModelId = NewType("UpstreamModelId", str)
"""The string the upstream expects. Equal to ModelId on the plan lane, always."""

ProviderId = NewType("ProviderId", str)
LeaseId = NewType("LeaseId", str)
ThreadId = NewType("ThreadId", str)
"""Equal to the qmx-control session id."""
AgentId = NewType("AgentId", str)
"""From the CLI's `x-claude-code-agent-id` header. Absent for the main thread."""
CredentialRef = NewType("CredentialRef", str)
"""An OS keyring label such as `qmx/provider/kimi`. Never a secret value."""
HttpsUrl = NewType("HttpsUrl", str)
"""Parsed at the settings boundary: https only, not loopback, not api.anthropic.com."""
Percent = NewType("Percent", float)
"""0.0 to 100.0, parsed at the settings boundary."""


# ----------------------------------------------------------- capabilities


class ThinkingMode(StrEnum):
    OPTIONAL = "optional"
    FORCED_ON = "forced_on"  # Kimi K2.7 Code, MiniMax M3.1, Meta Muse reject thinking off


class CacheMarkers(StrEnum):
    BLOCK = "block"  # Anthropic semantics, forward unchanged
    TOP_LEVEL_ONLY = "top_level_only"  # Kimi: block markers ignored, hoist one top-level marker
    AUTOMATIC = "automatic"  # DeepSeek: markers ignored, caching is implicit


@dataclass(frozen=True, slots=True)
class Capabilities:
    """What a route can take. Read by the gateway's request adapter and by the
    harness when it derives a session's env (for example ENABLE_TOOL_SEARCH is
    true only if every route a lease can reach supports it)."""

    context_window: int
    tool_search: bool
    server_tools: bool  # Anthropic server tools such as web_search
    count_tokens: bool
    thinking: ThinkingMode
    cache_markers: CacheMarkers


@dataclass(frozen=True, slots=True)
class Quirks:
    """Per-upstream request edits. Applied by the gateway per request, never as a
    process-wide env flag, so a Meta sub-agent's strictness never degrades the
    Claude main thread in the same CLI process."""

    strip_beta_header: bool  # drop anthropic-beta (also drops the OAuth capability)
    strip_fields: frozenset[str]  # Meta: stop_sequences, top_k, container, inference_geo, context_management


@dataclass(frozen=True, slots=True)
class Price:
    """USD per million tokens, UI-editable. Plan routes have no price."""

    input: float
    output: float
    cache_read: float
    cache_write: float


# ------------------------------------------------------------ settings rows


@dataclass(frozen=True, slots=True)
class ClaudeModel:
    """A Claude model id the operator enabled on his Max plan. Parsed so that only
    Claude-family ids construct."""

    id: ModelId
    caps: Capabilities

    @staticmethod
    def parse(raw: Mapping[str, object]) -> ClaudeModel:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class KeyModel:
    """A model served by a key provider. `parse` refuses any id whose family is
    Claude or GPT (claude-*, anthropic/*, ~anthropic/*, gpt-*, openai/*, o<digit>*),
    including OpenRouter slugs. That is the family guard, at the boundary."""

    id: ModelId
    upstream: UpstreamModelId
    caps: Capabilities
    price: Price

    @staticmethod
    def parse(raw: Mapping[str, object]) -> KeyModel:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class GptModel:
    id: ModelId
    upstream: UpstreamModelId
    caps: Capabilities

    @staticmethod
    def parse(raw: Mapping[str, object]) -> GptModel:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class ProbeReceipt:
    """Proof that probes P0 to P7 passed on this machine. Written only by the probe
    script, read-only in the UI. Expires when the translator version changes."""

    passed_at: datetime
    translator_version: str
    namespace_tools_required: bool  # P3 outcome
    reasoning_replay: bool  # P4 outcome: include=["reasoning.encrypted_content"] accepted


@dataclass(frozen=True, slots=True)
class ConsentRecord:
    """The operator's express consent for background GPT use (SIWC terms)."""

    given_at: datetime


@dataclass(frozen=True, slots=True)
class ClaudePlanRow:
    """Exactly one. No URL, no credential: the CLI's own /login owns both."""

    models: tuple[ClaudeModel, ...]


@dataclass(frozen=True, slots=True)
class KeyProviderRow:
    id: ProviderId
    base_url: HttpsUrl
    credential: CredentialRef
    quirks: Quirks
    models: tuple[KeyModel, ...]


@dataclass(frozen=True, slots=True)
class ChatGptPlanRow:
    models: tuple[GptModel, ...]
    receipt: ProbeReceipt | None  # None: the row shows in the UI, routes nothing
    background_consent: ConsentRecord | None


type ProviderRow = ClaudePlanRow | KeyProviderRow | ChatGptPlanRow


# ------------------------------------------------------------------ routes


@dataclass(frozen=True, slots=True)
class PlanRoute:
    """Claude on the Max plan. Forwarded verbatim to the constant Anthropic host
    with the CLI's own Authorization, sealed. No field can redirect it."""

    model: ModelId
    caps: Capabilities


@dataclass(frozen=True, slots=True)
class KeyRoute:
    model: ModelId
    upstream: UpstreamModelId
    provider: ProviderId
    base_url: HttpsUrl
    credential: CredentialRef
    quirks: Quirks
    caps: Capabilities
    price: Price


@dataclass(frozen=True, slots=True)
class GptRoute:
    model: ModelId
    upstream: UpstreamModelId
    caps: Capabilities
    receipt: ProbeReceipt  # not optional: no receipt, no route


type Route = PlanRoute | KeyRoute | GptRoute


@dataclass(frozen=True, slots=True)
class RouteError:
    row: str
    model: str
    reason: str  # "duplicate model id", "claude-family id on a key row", ...


class RouteTable:
    """ModelId -> Route. Built only by `build_route_table`. Immutable."""

    def resolve(self, model: ModelId) -> Route | None:
        raise NotImplementedError

    def routes(self) -> Sequence[Route]:
        raise NotImplementedError

    def plan_models(self) -> frozenset[ModelId]:
        raise NotImplementedError


def build_route_table(rows: Sequence[ProviderRow]) -> RouteTable | list[RouteError]:
    """Pure. Called by the harness whenever `settings.toml [providers]` changes.

    # TODO pseudocode
    # errors = []
    # for row in rows:
    #     match row:
    #         case ClaudePlanRow(models): routes += PlanRoute(m.id, m.caps) for m
    #         case KeyProviderRow(...):   routes += KeyRoute(...) for m
    #         case ChatGptPlanRow(models, receipt=None): skip (shown as "probe not passed")
    #         case ChatGptPlanRow(models, receipt=r):   routes += GptRoute(m.id, m.upstream, m.caps, r)
    # duplicate ModelId across all routes -> RouteError (never last-wins)
    # return errors or RouteTable(routes)
    """
    raise NotImplementedError


@dataclass(frozen=True, slots=True)
class AgentHints:
    """From the CLI's gateway hint headers (CLAUDE_CODE_GATEWAY_HINT_HEADERS=1).
    Used for attribution and the background test. Never for authorization."""

    agent_id: AgentId | None  # x-claude-code-agent-id
    agent_type: str | None  # x-claude-code-agent-type
    request_class: str | None  # x-claude-code-request-class


# ------------------------------------------------------------------ leases


class Placement(StrEnum):
    FOREGROUND = "foreground"  # a chat the operator is driving
    BACKGROUND = "background"  # unattended work; subject to the plan cap


@dataclass(frozen=True, slots=True)
class ToolCatalogSnapshot:
    """What the wire gate needs to classify a model-proposed tool_use: QMX tool
    descriptors (money metadata, parent surfaces) and the proposal tool identity.
    Built by the harness from the same registry that builds the in-process MCP
    server, so the two cannot disagree."""

    digest: str
    descriptors: Mapping[str, Mapping[str, object]]
    proposal_tools: frozenset[str]  # exact names, e.g. "mcp__qmx__propose_order"
    credential_labels: frozenset[str]  # qmx/* keyring labels, derived from [brokers] credential_refs
    protected_paths: frozenset[str]  # credential files and money state, incl. QMX's config home


@dataclass(frozen=True, slots=True)
class LeaseGrant:
    """One per live CLI process. The capability a CLI presents on every request in
    its `x-qmx-lease` header.

    The gateway stores only `secret_digest`. The secret itself exists in the
    harness's memory and in that one CLI's env, nowhere else. A Bash call inside
    that CLI can read it, which grants exactly what the CLI already has: these
    models, attributed to this thread.
    """

    lease: LeaseId
    secret_digest: bytes  # sha256(secret)
    thread: ThreadId
    placement: Placement
    models: frozenset[ModelId]  # non-empty; every member resolves in the table
    catalog: ToolCatalogSnapshot

    def carries_plan(self, table: RouteTable) -> bool:
        """True when any allowed model is a PlanRoute. Derived, never stored.
        Decides whether the CLI env omits ANTHROPIC_AUTH_TOKEN (so the CLI sends its
        own plan login, sealed by the gateway) or sets it to the lease secret (so the
        plan login never leaves the CLI at all)."""
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class GatewayDesired:
    """The whole desired state. `apply` replaces the gateway's copy wholesale, so a
    gateway restart, a settings edit and a new chat all converge the same way
    (per make-operations-idempotent)."""

    routes: RouteTable
    leases: tuple[LeaseGrant, ...]
    background_cap: Percent  # default 50.0, UI-editable (R6)
    chatgpt_background_consent: ConsentRecord | None


# ------------------------------------------------------------------ events


class PlanWindow(StrEnum):
    FIVE_HOUR = "five_hour"
    SEVEN_DAY = "seven_day"
    SEVEN_DAY_OPUS = "seven_day_opus"
    SEVEN_DAY_SONNET = "seven_day_sonnet"


class Lane(StrEnum):
    PLAN = "plan"
    KEY = "key"
    GPT = "gpt"


@dataclass(frozen=True, slots=True)
class UsageRecorded:
    """One upstream response. `request_key` is the upstream request or message id,
    so re-delivery after a link restart inserts nothing twice."""

    request_key: str
    lease: LeaseId
    thread: ThreadId
    agent: AgentId | None
    model: ModelId
    lane: Lane
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    at: datetime


@dataclass(frozen=True, slots=True)
class PlanWindowSeen:
    """Parsed from anthropic-ratelimit-unified-* response headers on every plan
    response, not only on status transitions."""

    window: PlanWindow
    utilization: Percent
    resets_at: datetime
    status: str  # allowed | allowed_warning | rejected
    at: datetime


@dataclass(frozen=True, slots=True)
class CapRefused:
    lease: LeaseId
    thread: ThreadId
    model: ModelId
    utilization: Percent
    cap: Percent
    at: datetime


@dataclass(frozen=True, slots=True)
class MoneyBlocked:
    """The wire gate replaced a model-proposed tool_use before the CLI saw it."""

    lease: LeaseId
    thread: ThreadId
    agent: AgentId | None
    model: ModelId
    tool_name: str
    act: str
    why: str
    at: datetime


@dataclass(frozen=True, slots=True)
class UpstreamFailed:
    lease: LeaseId
    thread: ThreadId
    model: ModelId
    status: int
    kind: str  # rate_limit | overloaded | auth | usage_limit | unsupported_capability | other
    at: datetime


@dataclass(frozen=True, slots=True)
class UnexpectedPath:
    """A request on a path the gateway does not serve. Only the path is recorded.
    Exists so the live check can prove token refresh never comes through here."""

    path: str
    at: datetime


type GatewayEvent = (
    UsageRecorded | PlanWindowSeen | CapRefused | MoneyBlocked | UpstreamFailed | UnexpectedPath
)
