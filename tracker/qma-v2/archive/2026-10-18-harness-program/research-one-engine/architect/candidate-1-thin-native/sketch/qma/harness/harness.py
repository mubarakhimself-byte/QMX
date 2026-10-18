"""The harness: the only object callers hold.

Public surface: `open`, `start_chat`, `send`, `interrupt`, `answer`, `quote`, `apply`,
`live`, `usage`, `doctor`, `close`. Behind it: the Claude home and isolation, the routing
env per provider, the money gate, the approval rendezvous, the SDK-to-block projection,
relaunch on provider or effort change, idle reaping, the background cap, the GPT
translator lifecycle and boot reconciliation. Callers never see an SDK type.

Process model. qmx-control's process hosts the harness. Each live chat is one CLI
subprocess that the SDK starts; that subprocess is the crash and environment boundary, so
there is no second QMX host process per chat. If qmx-control dies, the CLI sees its stdin
close and exits (live check P3 measures how fast).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from qma.harness.chat import Answer, AnswerStatus, AskId, Chat, Quote
from qma.harness.launch import ChatKind, ConfigChange, Effort, PermissionMode
from qma.harness.profiles import ProfileName

if TYPE_CHECKING:
    from qmx_broker.service import BrokerService
    from qmx_control.service import ControlService

    from qma.harness.home import DoctorLine, QmxHome, SessionId
    from qma.harness.launch import SecretLookup
    from qma.harness.project import Delta
    from qma.harness.usage import WindowView


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
    """None means Interactive."""


class Harness:
    @classmethod
    async def open(
        cls,
        home: QmxHome,
        *,
        control: ControlService,
        broker: BrokerService,
        secrets: SecretLookup,
    ) -> Harness:
        """Convergent startup, safe to run after any crash:
        1. Parse settings.toml [providers] and [budgets]; parse settings.json (refuse on
           forbidden keys, the chat then shows why).
        2. For every chat record with turn "running": write a `needs_you` block "last turn
           ended with an unknown outcome", set turn "idle". Running this twice changes nothing.
        3. Start the GPT translator only if a `ProbePassed` is stored for this translator
           version and a ChatGPT session exists.
        No CLI process starts here. Chats connect on their first `send`.
        """
        raise NotImplementedError

    async def start_chat(self, spec: NewChat) -> SessionId:
        """`control.sessions_create`, then a chat record with `started=False`. No process yet."""
        raise NotImplementedError

    async def send(self, session_id: SessionId, text: str) -> None:
        """Hand operator text to the chat. Returns once queued; results stream as blocks.
        Before connecting a Cold chat, evict the least recently used idle chat if
        `max_live_chats` (settings.toml [budgets], default 4) is reached."""
        raise NotImplementedError

    async def interrupt(self, session_id: SessionId) -> None:
        raise NotImplementedError

    def answer(self, ask: AskId, answer: Answer) -> AnswerStatus:
        """Routes by `ask.session_id`. A chat that is not live returns `expired`."""
        raise NotImplementedError

    def quote(self, session_id: SessionId, change: ConfigChange) -> Quote:
        raise NotImplementedError

    async def apply(self, session_id: SessionId, quote_id: str) -> None:
        """The quote stays server-side in its chat; callers only name it, so a client cannot
        forge one. Unknown or stale id raises `QuoteStale`."""
        raise NotImplementedError

    def live(self, session_id: SessionId) -> AsyncIterator[Delta]:
        raise NotImplementedError

    def usage(self) -> Mapping[ProfileName, tuple[WindowView, ...]]:
        raise NotImplementedError

    def doctor(self) -> list[DoctorLine]:
        raise NotImplementedError

    async def close(self) -> None:
        """Close every chat. Idempotent."""
        raise NotImplementedError

    # --- private ---

    async def _delegate(self, parent: SessionId, profile: ProfileName, prompt: str) -> str:
        """Backs `mcp__qmx__delegate`. Refuses a profile outside `Profiles.delegate_targets`.
        Starts a Child chat (qmx-control child session with `parent_id`), sends `prompt`,
        waits for its TurnEnded, returns the last assistant text. The child counts toward
        `max_live_chats` and is closed when it ends."""
        raise NotImplementedError

    async def _reap(self) -> None:
        """Every minute: close chats idle longer than `idle_reap_seconds` (settings.toml
        [budgets]). Closing is safe because the next `send` resumes the same session."""
        raise NotImplementedError

    _chats: dict[SessionId, Chat]
    """The one table of live chats. Only the harness writes it."""
