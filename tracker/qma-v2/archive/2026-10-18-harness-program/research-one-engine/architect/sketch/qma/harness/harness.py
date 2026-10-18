"""The harness: the only object callers hold.

Public surface: `open`, `start_chat`, `send`, `interrupt`, `answer`, `quote`, `apply`,
`live`, `usage`, `doctor`, `close`. Behind it: two Claude homes and settings in code, the
routing env per provider, the relay (grants, egress stop, key swap, quirks, usage tee, GPT
lane), the money gate and its posture, digest-bound approvals, the approval rendezvous, the
SDK-to-block projection, relaunch on provider or effort change, eviction, idle reaping, the
launcher and its OS limits, the background cap and the overage stop, untrusted-prompt
marking and boot reconciliation. Callers never see an SDK type, a relay URL or a key.

Process model. qmx-control's process hosts the harness and the relay. Each live chat is one
CLI subprocess that the SDK starts through `qma.launcher`, which has put itself under the OS
limits first; that subprocess is the crash and environment boundary, so there is no second
QMX host process per chat. Kill-on-close is set per OS by the launcher (Windows nested jobs,
Linux parent-death signal plus a per-chat scope, macOS a parent watch). `open` kills any
tree a crash left behind before anything resumes.

Later seam (U10, not built). This class is the seam for a separate OS-account zone. `Chat`
is internal; a runner under the agent account could host the SDK client instead, given a
`launch.Launch` and the `qmx` tools served on the relay listener, and no caller of
`Harness` would change.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from qma.harness.chat import Answer, AnswerStatus, AskId, Chat, Prompt, Quote
from qma.harness.launch import ChatKind, ConfigChange, Effort, PermissionMode
from qma.harness.profiles import ProfileName

if TYPE_CHECKING:
    from qmx_broker.service import BrokerService
    from qmx_control.service import ControlService

    from qma.harness.home import DoctorLine, QmxHome, SessionId
    from qma.harness.launch import SecretLookup, TestMode
    from qma.harness.procs import AgentProcessCap
    from qma.harness.project import Delta
    from qma.harness.relay import Relay
    from qma.harness.usage import UsagePage


@dataclass(frozen=True)
class NewChat:
    title: str
    profile: ProfileName
    model: str = "opus"
    effort: Effort | None = None
    mode: PermissionMode = "default"
    workspace: Path | None = None
    """None means a fresh folder under `<qmx_home>/workspaces/`."""
    kind: ChatKind | None = None
    """None means Interactive. Background and Child chats are verbatim (launch.verbatim)."""


class ChatTableFull(RuntimeError):
    """`max_live_chats` CLIs are live and none is idle, so no chat can connect. Nothing is
    queued: the caller gets this at once and the chat shows a `needs_you` block naming the
    busy chats. The operator closes or interrupts one, or raises the cap."""


class Harness:
    @classmethod
    async def open(
        cls,
        home: QmxHome,
        *,
        control: ControlService,
        broker: BrokerService,
        secrets: SecretLookup,
        scrubbed: tuple[str, ...],
        test: TestMode | None = None,
    ) -> Harness:
        """Convergent startup, safe to run after any crash. Assumes `qma.boot` already
        scrubbed this process (`scrubbed` is what it removed, names only, for doctor).
        `test` is None except in check scripts (`launch.TestMode`).
        1. `launch.assert_scrubbed(os.environ)`; refuse to open otherwise.
        2. Parse settings.toml [providers], [budgets], [agents] and [claude] (a bad [claude]
           does not stop `open`; each launch refuses and shows why).
        3. `home.ensure_homes`. `procs.kill_orphans`: every pid file whose process is still
           alive (pid plus start time) has its tree killed, then the file goes.
        4. For every chat record with turn "running": write a `needs_you` block "last turn
           ended with an unknown outcome", set turn "idle". Running this twice changes nothing.
        5. Start the relay (127.0.0.1:0) and the `AgentProcessCap` for this platform.
        6. Vet every declared external MCP server (`tools.vet_mcp_servers`) once per config
           hash. If no exposure report exists for this CLI version, run the probe.
        7. Open the relay's GPT lane only if a `ProbePassed` is stored for this translator
           version and a ChatGPT session exists.
        No chat CLI starts here. Chats connect on their first `send`.
        """
        raise NotImplementedError

    async def start_chat(self, spec: NewChat) -> SessionId:
        """`control.sessions_create`, then a chat record with `started=False`. No process yet."""
        raise NotImplementedError

    async def send(self, session_id: SessionId, prompt: Prompt) -> None:
        """Hand a prompt to the chat. Returns once queued; results stream as blocks.
        `InjectedText` into an Interactive chat raises `chat.UntrustedPrompt`.
        Before connecting a Cold chat at `max_live_chats` (settings.toml [budgets], default
        4), close the least recently used idle chat; if none is idle, raise `ChatTableFull`."""
        raise NotImplementedError

    async def interrupt(self, session_id: SessionId) -> None:
        raise NotImplementedError

    def answer(self, ask: AskId, answer: Answer) -> AnswerStatus:
        """Routes by `ask.session_id`. A chat that is not live returns `expired`. AllowAlways
        on an asking QMX tool returns `invalid`. Must run on the harness's event loop: the
        route is `async def`, never a threadpool handler, because it resolves an asyncio
        future and records a grant (A11)."""
        raise NotImplementedError

    def quote(self, session_id: SessionId, change: ConfigChange) -> Quote:
        raise NotImplementedError

    async def apply(self, session_id: SessionId, quote_id: str) -> None:
        """The quote stays server-side in its chat; callers only name it, so a client cannot
        forge one. Unknown or stale id raises `QuoteStale`."""
        raise NotImplementedError

    def live(self, session_id: SessionId) -> AsyncIterator[Delta]:
        raise NotImplementedError

    def usage(self) -> UsagePage:
        """Plan windows, RunIndex token sums per profile (one source per profile), the
        background cap, the overage stop, the money posture and the stored exposure report."""
        raise NotImplementedError

    async def doctor(self, *, probe: bool = False) -> list[DoctorLine]:
        """`home.doctor` lines, the stored exposure report and the money posture, the relay's
        grant count and refusal counters (bearer, egress, family), and the process cap
        report. `probe=True` (the operator asked) runs a fresh exposure probe first; a plain
        read never does (B16)."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close every chat, then the relay, then the process cap. Idempotent."""
        raise NotImplementedError

    # --- private ---

    async def _delegate(self, parent: SessionId, profile: ProfileName, prompt: str) -> str:
        """Backs `mcp__qmx__delegate`. Refuses a profile outside `Profiles.delegate_targets`.
        Refuses at once, as a tool error, when no chat slot is free; it never waits on
        capacity that only its own parent could free. Starts a Child chat (qmx-control child
        session with `parent_id`, verbatim, `unattended` copied from the parent, its own
        relay grant, the [budgets] turn and spend limits), sends `InjectedText(prompt)`
        because a model wrote it, waits for its TurnEnded, returns the last assistant text,
        then closes it."""
        raise NotImplementedError

    async def _reap(self) -> None:
        """Every minute: close chats idle longer than `idle_reap_seconds` (settings.toml
        [budgets]). Closing is safe because the next `send` resumes the same session."""
        raise NotImplementedError

    _chats: dict[SessionId, Chat]
    """The one table of live chats. Only the harness writes it."""
    _relay: Relay
    _procs: AgentProcessCap
