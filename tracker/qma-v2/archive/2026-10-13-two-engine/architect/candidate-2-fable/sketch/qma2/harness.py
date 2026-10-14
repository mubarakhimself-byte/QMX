"""The facade. Everything qmx_control, the console and tests call lives on `Harness`.

Depth: ~14 methods hide two SDKs, the policy engine, approvals, the router, the store, the
supervisor and the projector. Callers never see an SDK type, a row, a Future or a process.

Ownership: `Harness` owns one `SessionActor` per open thread (session.py). All writes to a
thread's runtime state go through that actor's inbox; this facade only posts messages and
reads. Per separate-before-serializing-shared-state: no two actors share a thread.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Protocol

from qma2.accounts import Router
from qma2.approvals import ApprovalBroker, OperatorAuth
from qma2.config import ConfigHome, SettingsLayer
from qma2.secrets import SecretStore
from qma2.store import Store
from qma2.supervisor import Launcher, Supervisor  # Launcher is defined once, in supervisor.py
from qma2.types import (
    Account,
    AccountId,
    Approval,
    ApprovalAnswer,
    ApprovalId,
    Effort,
    EngineKind,
    ExportBundle,
    Json,
    ModelRef,
    OperatorProof,
    PermissionMode,
    ProbeResult,
    Segment,
    SwitchPreview,
    Thread,
    ThreadId,
    Turn,
    TurnId,
    TurnInput,
    UsageSummary,
)


class BlockSink(Protocol):
    """The UI's durable channel. qmx_control implements it with `ControlService`.

    Invariant: qma2 is the only writer of blocks for threads it owns. Blocks written by anyone
    else with the agent token (Gotcha 8) are display noise; the UI reads approval state from
    `approvals_pending`, never from `permission` blocks.
    """

    def create_session(self, title: str, parent_id: ThreadId | None) -> ThreadId: ...

    def append(self, thread_id: ThreadId, kind: str, content: Json) -> int:
        """Append one of today's 14 block kinds; returns the block seq."""
        ...

    def blocks(self, thread_id: ThreadId, after: int = 0) -> Sequence[tuple[int, str, Json]]:
        """Read back blocks for cross-engine seeding and export."""
        ...


class Harness:
    """One per qmx_control process. Construct with `open`, then `await start()`."""

    def __init__(
        self,
        *,
        home: ConfigHome,
        store: Store,
        sink: BlockSink,
        secrets: SecretStore,
        supervisor: Supervisor,
        router: Router,
        approvals: ApprovalBroker,
        operator: OperatorAuth,
    ) -> None:
        self.operator = operator  # public: routes call operator.verify / pair
        raise NotImplementedError

    @classmethod
    def open(
        cls,
        home: Path,
        *,
        sink: BlockSink,
        launcher: Launcher | None = None,
        secrets: SecretStore | None = None,
    ) -> Harness:
        """Build the object graph. No IO beyond opening the store. `home` is ~/.qmx; the
        harness uses `<home>/qma2/` (see config.ConfigHome) and never the operator's ~/.claude."""
        raise NotImplementedError

    async def start(self) -> None:
        """Convergent start (make-operations-idempotent):
        1. store.migrate()
        2. approvals.expire_orphans(): PENDING rows whose turn is not RUNNING in this process
           → EXPIRED, thread → IDLE, block `needs_you` appended once (keyed by approval id).
        3. threads with status RUNNING/WAITING from a previous process → IDLE; their last turn
           → INTERRUPTED (the engine process is gone). Nothing is replayed automatically.
        4. engines probe each enabled account lazily on first use, not here.
        Running this twice changes nothing."""
        raise NotImplementedError

    async def close(self) -> None:
        """Interrupt running turns, close engine sessions, kill process trees, stop the store
        writer. Bounded to a few seconds; a stuck engine is killed, not awaited."""
        raise NotImplementedError

    # ------------------------------------------------------------ threads

    async def thread_create(
        self,
        title: str,
        cwd: Path,
        *,
        engine: EngineKind | None = None,
        model: ModelRef | None = None,
        profile: str | None = None,
        parent_id: ThreadId | None = None,
        background: bool = False,
    ) -> Thread:
        """Create the control session (via sink) and the first segment. The router picks the
        account for the whole segment (never per request). `background=True` is refused with
        `RouterError` if the Claude window is above the account's background cap."""
        raise NotImplementedError

    async def thread_list(self, *, archived: bool = False) -> Sequence[Thread]:
        raise NotImplementedError

    async def thread_get(self, thread_id: ThreadId) -> tuple[Thread, Segment, Sequence[Approval]]:
        """Thread, its current segment, and its pending approvals."""
        raise NotImplementedError

    async def thread_archive(self, thread_id: ThreadId) -> None:
        raise NotImplementedError

    async def thread_fork(self, thread_id: ThreadId, at_turn: TurnId) -> Thread:
        """Claude: `fork_session`. OpenAI: copy items up to the turn. Blocks copied up to the
        turn's last block seq so the UI shows the branch point."""
        raise NotImplementedError

    # ------------------------------------------------------------ turns

    async def turn_start(
        self, thread_id: ThreadId, input: TurnInput, *, client_key: str | None = None
    ) -> Turn:
        """Post a turn to the thread's actor and return at once. Idempotent on
        (thread_id, client_key): a retry returns the existing turn. Blocks arrive via the
        sink; the turn's end is a `turns` row update plus a `runs`-topic event."""
        raise NotImplementedError

    async def turn_steer(self, thread_id: ThreadId, input: TurnInput, *, expected_turn: TurnId) -> None:
        """Codex precondition: refused with `StaleTurn` if `expected_turn` is not the running
        turn. Claude: mid-turn `query()`; OpenAI: stop after step, add_input, resume."""
        raise NotImplementedError

    async def turn_stop(self, thread_id: ThreadId) -> None:
        """Interrupt; the turn ends INTERRUPTED; no orphan process (supervisor kill-tree).
        No-op if nothing is running."""
        raise NotImplementedError

    async def turn_wait(self, turn_id: TurnId, *, timeout_s: float | None = None) -> Turn:
        """Used by live checks and the console. Returns the finished turn."""
        raise NotImplementedError

    # ------------------------------------------------------------ switches

    async def thread_switch(
        self,
        thread_id: ThreadId,
        *,
        model: ModelRef | None = None,
        effort: Effort | None = None,
        mode: PermissionMode | None = None,
        confirm: bool = False,
    ) -> SwitchPreview | Segment:
        """Model or effort switch mid-chat. Without `confirm`, returns the cost pop-up data when
        the cache would break or the engine changes; with it, applies the switch. Same engine:
        the segment continues (Claude `set_model`, OpenAI new ModelSettings). Different engine
        or account: a new segment seeded from the thread's blocks (TextDone + tool summaries)."""
        raise NotImplementedError

    async def compact(self, thread_id: ThreadId, focus: str = "") -> None:
        """Manual `/compact <focus>` on either engine."""
        raise NotImplementedError

    # ------------------------------------------------------------ approvals

    async def approvals_pending(self) -> Sequence[Approval]:
        raise NotImplementedError

    async def approval_answer(
        self, approval_id: ApprovalId, answer: ApprovalAnswer, proof: OperatorProof
    ) -> Approval:
        """The only answer path. `proof` is the authorisation; there is no `by=` string.
        Idempotent: a second identical answer returns the row unchanged; a different answer to
        an ANSWERED row raises `AlreadyAnswered`."""
        raise NotImplementedError

    # ------------------------------------------------------------ accounts, usage, settings

    async def accounts(self) -> Sequence[tuple[Account, Sequence[Json]]]:
        """Accounts with their latest limit snapshots and isolation label."""
        raise NotImplementedError

    async def account_add(self, account: Account, proof: OperatorProof) -> Account:
        """Secrets are never in `Account`; the console stores them in SecretStore first and
        passes `credential_ref`. Claude: `claude_home` only; sign-in is `claude /login` in
        that dir, run by the operator (see console)."""
        raise NotImplementedError

    async def account_probe(self, account_id: AccountId) -> ProbeResult:
        """Live auth check without spending a turn where the SDK allows it."""
        raise NotImplementedError

    async def usage(self, *, since: datetime | None = None) -> UsageSummary:
        raise NotImplementedError

    async def settings_get(self, layer: SettingsLayer, cwd: Path | None = None) -> Json:
        raise NotImplementedError

    async def settings_put(
        self, layer: SettingsLayer, document: Json, proof: OperatorProof, cwd: Path | None = None
    ) -> Json:
        """UI-editable settings (operator standing rule). The managed layer is code, not a file,
        and has no put. Validated by `config.Settings` at this boundary."""
        raise NotImplementedError

    async def export(self, thread_id: ThreadId, out_dir: Path) -> ExportBundle:
        raise NotImplementedError
