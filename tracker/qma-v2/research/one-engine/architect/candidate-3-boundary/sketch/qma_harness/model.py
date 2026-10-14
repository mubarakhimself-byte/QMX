"""Operator-side domain types for the boundary-first harness.

Pure. No I/O, no SDK import. Everything here lives on the operator side of
the boundary. Only `route_for` output (a qma_zone_wire.ModelRoute) ever
crosses into the zone, and it carries no URL and no secret.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal, NewType

from qma_zone_wire import AskId, ModelRoute, Quirk, SdkSessionId, Seq, ThreadId, TierPins

ProfileId = NewType("ProfileId", str)
ApprovalId = NewType("ApprovalId", str)
ShareId = NewType("ShareId", str)
TurnId = NewType("TurnId", str)


@dataclass(frozen=True)
class SecretRef:
    """A name in the operator's OS keyring, always `qmx/<...>`. Never a value.
    Parsed by `SecretRef.parse`, which refuses any other prefix."""

    name: str

    @staticmethod
    def parse(raw: str) -> "SecretRef":
        raise NotImplementedError


# ---------------------------------------------------------------- providers


@dataclass(frozen=True)
class KeyModelName:
    """A model id allowed on an API key.

    The family guard (no Claude or GPT model on a key, OpenRouter slugs
    included) lives in `parse` and nowhere else. Refuses `claude*`, `gpt*`,
    `o1*`..`o9*`, `anthropic/*`, `openai/*`, `~anthropic/*`."""

    value: str

    @staticmethod
    def parse(raw: str) -> "KeyModelName":
        raise NotImplementedError


@dataclass(frozen=True)
class ClaudePlan:
    """The operator's one Claude Max plan. No URL, no secret, no key.

    There is exactly one, id "claude-plan". Its login lives in the zone,
    owned by the CLI."""

    id: ProfileId


@dataclass(frozen=True)
class KeyProvider:
    """An Anthropic-compatible provider on an API key: Kimi, GLM, DeepSeek,
    MiniMax, Meta Muse, OpenRouter, or any new row.

    `base_url` and `key` stay operator-side. The relay uses them; the zone
    never sees them. Tier names are KeyModelName, so the family guard holds by
    construction."""

    id: ProfileId
    label: str
    base_url: str  # https only, parsed at the settings boundary
    key: SecretRef
    opus: KeyModelName
    sonnet: KeyModelName
    haiku: KeyModelName
    fable: KeyModelName
    quirks: frozenset[Quirk]


@dataclass(frozen=True)
class ProbeNotRun:
    pass


@dataclass(frozen=True)
class ProbePassed:
    at: datetime
    cli_version: str


@dataclass(frozen=True)
class ProbeFailed:
    step: Literal["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    reason: str


GptProbe = ProbeNotRun | ProbePassed | ProbeFailed


@dataclass(frozen=True)
class ChatGptPlan:
    """GPT through the operator's ChatGPT sign-in, via the translator.

    The refresh token is at `token` in the operator keyring. The profile is
    usable only when `probe` is ProbePassed; `usable` is the one place that
    rule lives."""

    id: ProfileId
    models: tuple[str, ...]  # GPT slugs from /v1/models, chosen by the operator
    tiers: TierPins
    token: SecretRef
    probe: GptProbe

    def usable(self) -> bool:
        return isinstance(self.probe, ProbePassed)


ProviderProfile = ClaudePlan | KeyProvider | ChatGptPlan


def route_for(profile: ProviderProfile) -> ModelRoute:
    """Pure. ClaudePlan -> Direct(). KeyProvider and ChatGptPlan -> ViaDoor
    with the profile id, tier names and quirks. Raises for an unusable
    ChatGptPlan. This is the only producer of ModelRoute."""
    raise NotImplementedError


# ---------------------------------------------------------------- door ops


class Effect(Enum):
    """What a door op does to the world. There is no MONEY_ACT member, so a
    money-moving op cannot be registered: the type has no slot for it.

    READ           reads QMX or broker state.
    DOMAIN_WRITE   writes QMX research state (library, backtests, notes).
    MANAGE         publish, install, schedule, change settings (R35: always asks).
    PROPOSE_MONEY  writes an unsigned order proposal (always asks; signing
                   and execution belong to QMN, never to the door)."""

    READ = "read"
    DOMAIN_WRITE = "domain_write"
    MANAGE = "manage"
    PROPOSE_MONEY = "propose_money"


@dataclass(frozen=True)
class DoorPolicy:
    """The only UI-editable part of door policy. MANAGE and PROPOSE_MONEY are
    always-ask and have no field here on purpose."""

    domain_write: Literal["allow", "ask"]
    approval_wait_seconds: int


@dataclass(frozen=True)
class Execute:
    pass


@dataclass(frozen=True)
class AwaitOperator:
    approval: ApprovalId


@dataclass(frozen=True)
class Refuse:
    reason: str  # shown to the model; names the rule


DoorDecision = Execute | AwaitOperator | Refuse


@dataclass(frozen=True)
class Pending:
    pass


@dataclass(frozen=True)
class Granted:
    at: datetime


@dataclass(frozen=True)
class Denied:
    message: str


@dataclass(frozen=True)
class Expired:
    pass


@dataclass(frozen=True)
class Consumed:
    at: datetime


ApprovalState = Pending | Granted | Denied | Expired | Consumed


@dataclass(frozen=True)
class DoorApproval:
    """One-shot grant bound to the op name and the canonical args digest.
    Granted moves to Consumed when the door executes it; it cannot run twice."""

    id: ApprovalId
    thread: ThreadId
    op: str
    args_digest: str
    state: ApprovalState


@dataclass(frozen=True)
class ZoneAsk:
    """A built-in tool ask raised by the CLI inside the zone (Bash, Write...)."""

    thread: ThreadId
    ask: AskId


PendingRef = ZoneAsk | ApprovalId
"""What the operator answers. One answer route, two enforcement points:
zone asks are enforced in the zone (user experience), door approvals are
enforced by the door (authority)."""


@dataclass(frozen=True)
class AllowOnce:
    pass


@dataclass(frozen=True)
class AllowAlways:
    """Zone asks only. Recorded as a rule in the canonical user-tier settings.
    Refused for door approvals, which are always-ask."""


@dataclass(frozen=True)
class Deny:
    message: str


Answer = AllowOnce | AllowAlways | Deny


@dataclass(frozen=True)
class OperatorProof:
    """Evidence that a call came through the operator API (bearer token from
    the operator keyring). The zone account cannot read that keyring, so the
    bearer is a sound operator principal again."""

    channel: Literal["operator_api", "console"]


# ---------------------------------------------------------------- threads


@dataclass(frozen=True)
class Idle:
    pass


@dataclass(frozen=True)
class Running:
    turn: TurnId


@dataclass(frozen=True)
class Unknown:
    """The zone lost a running turn (crash, service restart). Continuation is
    blocked until the operator resumes explicitly; never a silent fresh session."""

    reason: str


@dataclass(frozen=True)
class ThreadClosed:
    pass


ThreadState = Idle | Running | Unknown | ThreadClosed


@dataclass(frozen=True)
class Share:
    """An operator-owned folder the zone account may use as a workspace.
    Granted with an owner-level ACL entry; no elevation needed."""

    id: ShareId
    path: Path
    access: Literal["read", "write"]


@dataclass(frozen=True)
class ThreadRecord:
    """One row in harness.db. The Harness is its only writer."""

    thread: ThreadId
    profile: ProfileId
    share: ShareId
    sdk_session: SdkSessionId | None
    state: ThreadState
    last_seq: Seq
    parent: ThreadId | None
    background: bool


def step(record: ThreadRecord, event: object) -> ThreadRecord:
    """Pure transition on a parsed zone event. Events with seq <= last_seq are
    no-ops, which makes replay after a reconnect idempotent."""
    raise NotImplementedError


@dataclass(frozen=True)
class MarkUnknown:
    thread: ThreadId


@dataclass(frozen=True)
class ReannounceAsk:
    thread: ThreadId
    ask: AskId


@dataclass(frozen=True)
class RepushUserTier:
    pass


Fix = MarkUnknown | ReannounceAsk | RepushUserTier


def reconcile(records: tuple[ThreadRecord, ...], hello: object, canonical_hash: str) -> tuple[Fix, ...]:
    """Pure. Convergent startup after every Hello: a Running record the zone
    no longer reports live becomes Unknown; a zone ask with no permission block
    gets one; a user-tier hash mismatch triggers a push."""
    raise NotImplementedError


# ---------------------------------------------------------------- zone status


@dataclass(frozen=True)
class AclFinding:
    """Outside-in, read by the operator side from the OS (icacls, stat, ls -le)."""

    path: Path
    zone_can_read: bool
    zone_can_write: bool
    expected: Literal["none", "read", "write"]


@dataclass(frozen=True)
class Sealed:
    checked_at: datetime


@dataclass(frozen=True)
class Leaky:
    """Shown on the usage page in plain words, the way the old design showed
    `tool_level_same_user`. The harness still runs; the operator decides."""

    acl: tuple[AclFinding, ...]
    probe: tuple[str, ...]
    loopback: tuple[str, ...]  # operator-owned loopback listeners the zone can reach


BoundaryVerdict = Sealed | Leaky


@dataclass(frozen=True)
class ZoneStatus:
    link: Literal["up", "down"]
    login: Literal["signed_in", "signed_out", "unknown"]
    plan: str | None
    boundary: BoundaryVerdict
    live_threads: int
    zone_memory_mb: int | None
    five_hour_utilization: float | None
    background_cap: float  # 0.5 by default, UI-editable
