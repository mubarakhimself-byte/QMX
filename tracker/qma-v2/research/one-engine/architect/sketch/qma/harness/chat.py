"""One chat: one `ClaudeSDKClient`, one CLI process while live, one reader task.

Identity. The chat's qmx-control session id is passed to the SDK as `session_id` on the
first launch and as `resume` afterwards. The SDK transcript, the qmx-control block log and
the chat record share one key, so there is no mapping table and no way to resume into a
silently new session: a missing transcript is an error, not a fresh start.

Lifecycle (a small state machine, one owner):

    Cold --connect--> Live --idle reap / relaunch / close--> Cold
    Live: reader task drains `receive_messages()` forever and routes each `project()` fact.

Turn state is written to the chat record before a prompt goes out and when its
`ResultMessage` arrives. A record still "running" at boot means the outcome is unknown; the
chat shows a `needs_you` block and continues only when the operator sends the next message
(the daemon's rule, HOW "session resume").

Asks. `can_use_tool` (tool approvals and AskUserQuestion) parks a future in this chat's own
table and writes a `permission` or `question` block. The answer route resolves it. The table
is per chat, so chats never share ask state. For a QMX tool whose `Effect` asks, an
AllowOnce answer also records a `tools.Grant` for the digest of the exact final input in
this chat's own `Grants`; the tool handler consumes it.

Prompts. Who wrote the text is in its type. `OperatorText` is what the operator typed;
slash commands and `@path` work, as in Claude Code. `InjectedText` is anything QMA built
from news, files or tool output. A non-Interactive chat launches with
`verbatim_prompts=True` (launch.verbatim), so neither kind can dispatch a slash command,
a `/skill` or an `@path` read there. An Interactive chat is never verbatim, so it refuses
`InjectedText` outright.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from qma.harness.launch import ChatConfig, ConfigChange

if TYPE_CHECKING:
    import asyncio

    from claude_agent_sdk import ClaudeSDKClient
    from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext
    from qmx_broker.service import BrokerService
    from qmx_control.service import ControlService

    from qma.harness.home import ChatRecord, QmxHome, SessionId, UserTier
    from qma.harness.procs import AgentProcessCap
    from qma.harness.profiles import Profiles
    from qma.harness.project import Delta
    from qma.harness.relay import Relay
    from qma.harness.tools import Delegate, DomainWritePolicy
    from qma.harness.usage import BackgroundCap, UsageLedger


@dataclass(frozen=True)
class OperatorText:
    """Text the operator typed in the console or UI. Only the HTTP turn route makes one."""

    text: str


@dataclass(frozen=True)
class InjectedText:
    """Text QMA built from news, files, tool output or a model (a `delegate` prompt).
    Every producer of such text wraps it here at its source."""

    text: str


type Prompt = OperatorText | InjectedText


class UntrustedPrompt(ValueError):
    """`InjectedText` was sent to an Interactive chat, which is not verbatim. Raised before
    anything reaches the CLI."""


@dataclass(frozen=True)
class AskId:
    """`<session_id>.<n>`. The chat is part of the id, so the answer route needs no index."""

    session_id: SessionId
    n: int

    @classmethod
    def parse(cls, raw: str) -> AskId:
        raise NotImplementedError

    def __str__(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class AllowOnce:
    edited_input: dict[str, object] | None = None


@dataclass(frozen=True)
class AllowAlways:
    """Allow and remember, for built-in tools and QMX tools that do not ask. QMA writes the
    CLI's suggested rule into settings.json itself (one writer) and returns it to the CLI
    with destination "session" for this process. Not offered for asking QMX tools."""


@dataclass(frozen=True)
class Reject:
    message: str = ""


@dataclass(frozen=True)
class Answers:
    """Answers to an AskUserQuestion call, by question text."""

    answers: dict[str, str]


type Answer = AllowOnce | AllowAlways | Reject | Answers


type AnswerStatus = Literal["resolved", "already_answered", "expired", "invalid", "unknown"]
"""Idempotent: a second answer to the same ask is `already_answered`, not an error.
An ask whose process ended (restart, reap) is `expired`, shown with "re-run from here".
`invalid` means the answer does not fit the ask: AllowAlways on a QMX tool whose effect
asks (those approvals are one-shot and bound to arguments), or Answers to a tool ask."""


@dataclass(frozen=True)
class Quote:
    """The cost warning that must come before a cache-resetting change (01 req 6).

    `apply` accepts only the id of a quote this chat issued, so no code path can switch
    provider or model without the warning having been produced first. `epoch` is the chat's turn counter when quoted; a quote from an older
    epoch is refused, so a warning cannot be reused after the context grew.
    """

    id: str
    session_id: SessionId
    old: ChatConfig
    new: ChatConfig
    recomputed_tokens: int
    """Context tokens the next request sends uncached, from the last turn's usage."""
    warning: str | None
    """None when the change keeps the cache (a permission-mode change)."""
    epoch: int


class QuoteStale(RuntimeError):
    pass


class Chat:
    """Owned by `Harness`. Never shared across event loops."""

    session_id: SessionId
    config: ChatConfig

    def __init__(self, record: ChatRecord, deps: ChatDeps) -> None:
        raise NotImplementedError

    async def send(self, prompt: Prompt) -> None:
        """Refuse `InjectedText` with `UntrustedPrompt` unless `launch.verbatim(kind)`.
        Connect if Cold, write turn "running", then `client.query(prompt.text)`. While a
        turn runs, the SDK queues the message (streaming input), like typing into Claude
        Code. A Background chat refuses here when `BackgroundCap.allows` is False."""
        raise NotImplementedError

    async def interrupt(self) -> None:
        """`client.interrupt()`. Background Bash and sub-agents keep running, as in Claude Code;
        `stop_task(task_id)` stops one."""
        raise NotImplementedError

    def answer(self, ask: AskId, answer: Answer) -> AnswerStatus:
        raise NotImplementedError

    def quote(self, change: ConfigChange) -> Quote:
        """Every change goes through a quote, so there is one path. `warning` is None when
        `launch.resets_cache` is False (a mode change); the caller may then apply at once."""
        raise NotImplementedError

    async def apply(self, quote_id: str) -> None:
        """Look the quote up in this chat's own table; refuse an unknown id or a stale epoch
        (`QuoteStale`). Run `launch.classify_change` steps: SET_MODE
        and SET_MODEL use the native client setters; RELAUNCH disconnects and connects with
        the new options and `resume=session_id` at a turn boundary. Write the new config to
        the chat record, then a block that names the change."""
        raise NotImplementedError

    def live(self) -> AsyncIterator[Delta]:
        """Live deltas for this chat and its native sub-agents. Dropped on disconnect."""
        raise NotImplementedError

    async def close(self) -> None:
        """Disconnect, revoke this chat's relay grant, drop its grants. Pending asks become
        `expired`. Idempotent."""
        raise NotImplementedError

    @property
    def idle_seconds(self) -> float:
        """Seconds since the last message, or 0 while a turn or a background task runs.
        `Harness` reaps only idle chats, so a background sub-agent is never killed by reaping."""
        raise NotImplementedError

    # --- private, sketched for the reader ---

    async def _connect(self) -> ClaudeSDKClient:
        """Under the harness's connect lock:
        load_user_settings (refuse) -> assert_scrubbed -> Launch (PlanLaunch, or
        RelayedLaunch with `relay.grant(session_id, profile)`) -> launch_env ->
        tool_defs/build_server(grants)/gate_rules -> build_options ->
        ClaudeSDKClient(options).connect() -> procs.adopt_tree(new CLI pid), before any
        prompt. On the init message: switch off money MCP servers, record `started=True`.
        A relaunch revokes the old grant first."""
        raise NotImplementedError

    async def _read(self, client: ClaudeSDKClient) -> None:
        """for message in client.receive_messages(): for fact in project(message): route it.
        Block -> control.sessions_append (InChild -> child session, created once);
        Delta -> live queues; TurnUsage -> run journal model_call; Limits -> UsageLedger
        and, for the plan crossing the cap, interrupt Background chats via the harness;
        TurnEnded -> record turn "idle"; SessionReady -> money.money_servers check."""
        raise NotImplementedError

    async def _can_use_tool(
        self, tool_name: str, tool_input: dict[str, object], context: ToolPermissionContext
    ) -> PermissionResultAllow | PermissionResultDeny:
        """Park a future under a new AskId, write the `permission` block (tool, input, the
        rule that matched, and `context.suggestions` as the "always" choices unless the tool
        is an asking QMX tool), await the answer, write the resolution block. AllowOnce on an
        asking QMX tool records `Grant(tool, args_digest(tool, final_input))`. The wait has
        no timeout, as in Claude Code."""
        raise NotImplementedError


@dataclass(frozen=True)
class ChatDeps:
    """What a chat borrows from the harness. Passed in, never imported as globals."""

    home: QmxHome
    control: ControlService
    broker: BrokerService
    profiles: Profiles
    relay: Relay
    tier: UserTier
    domain_write: DomainWritePolicy
    ledger: UsageLedger
    cap: BackgroundCap
    procs: AgentProcessCap
    connect_lock: asyncio.Lock
    """One connect at a time, so `procs.new_child_pid` sees exactly one new child."""
    delegate: Delegate
    on_plan_limits: Callable[[], Awaitable[None]]
    """Called when the plan's five-hour use crosses the cap. The harness interrupts its
    Background chats. A chat never reaches into other chats itself."""