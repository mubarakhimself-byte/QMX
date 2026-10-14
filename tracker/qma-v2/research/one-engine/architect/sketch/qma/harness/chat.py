"""One chat: one `ClaudeSDKClient`, one CLI process while live, one reader task.

Identity. The chat's qmx-control session id is passed to the SDK as `session_id` until the
chat's first `ResultMessage`, and as `resume` afterwards. The SDK transcript, the qmx-control
block log and the chat record share one key, so there is no mapping table. Once a chat has
started, a missing transcript is an error, not a fresh start.

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

An Interactive chat waits for the answer with no timeout, as Claude Code does. An unattended
chat (`launch.unattended`) waits at most `unattended_ask_seconds` (settings.toml [budgets],
UI-editable), then rejects with "the operator did not answer in time" and marks the block
expired. So an unattended ask can never pin a CLI and its chat slot forever (A16, B2).

Prompts. Who wrote the text is in its type. `OperatorText` is what the operator typed;
slash commands and `@path` work, as in Claude Code. `InjectedText` is anything QMA built
from news, files or tool output. A non-Interactive chat launches with
`verbatim_prompts=True` (launch.verbatim), so neither kind can dispatch a slash command,
a `/skill` or an `@path` read there. An Interactive chat is never verbatim, so it refuses
`InjectedText` outright. `OperatorText` means "came through the turn route", which any
holder of the bearer can call (B19, noted).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from qma.harness.launch import ChatConfig, ConfigChange

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeSDKClient
    from claude_agent_sdk.types import PermissionResultAllow, PermissionResultDeny, ToolPermissionContext
    from qmx_broker.service import BrokerService
    from qmx_control.service import ControlService

    from qma.harness.home import ChatRecord, QmxHome, SessionId
    from qma.harness.launch import TestMode
    from qma.harness.procs import AgentProcessCap
    from qma.harness.profiles import Profiles
    from qma.harness.project import Delta
    from qma.harness.relay import Relay
    from qma.harness.tools import Delegate, DomainWritePolicy, VettedServers
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
    """Allow and remember, for built-in tools and QMX tools that do not ask. QMA appends the
    CLI's suggested rule to `settings.toml [claude]` (`home.remember_rule`, one writer) and
    returns it to the CLI with destination "session" for this process. Not offered for
    asking QMX tools."""


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
An ask whose process ended (restart, reap) or whose unattended wait ran out is `expired`,
shown with "re-run from here". `invalid` means the answer does not fit the ask: AllowAlways
on a QMX tool whose effect asks (those approvals are one-shot and bound to arguments), or
Answers to a tool ask."""


@dataclass(frozen=True)
class Quote:
    """The warning that must come before a cache-resetting or work-stopping change (01 req 6).

    `apply` accepts only the id of a quote this chat issued, so no code path can switch
    provider or model without the warning having been produced first. `epoch` is the chat's
    turn counter when quoted; a quote from an older epoch is refused, so a warning cannot be
    reused after the context grew.
    """

    id: str
    session_id: SessionId
    old: ChatConfig
    new: ChatConfig
    recomputed_tokens: int
    """Context tokens the next request sends uncached, from the last turn's usage."""
    background_tasks: int
    """Background Bash and sub-agent tasks running when quoted. A relaunch stops them, so
    the warning names them, and `apply` refuses if more are running than were quoted."""
    warning: str | None
    """None when the change keeps the cache and stops nothing (a permission-mode change)."""
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
        A plan chat refuses while `UsageLedger.hard_stop()` gives a reason (overage or
        `credits_required`). A Background chat refuses when `BackgroundCap.allows` is False.
        Connect if Cold, write turn "running", then `client.query(prompt.text)`. While a
        turn runs, the SDK queues the message (streaming input), like typing into Claude Code."""
        raise NotImplementedError

    async def interrupt(self) -> None:
        """`client.interrupt()`. Background Bash and sub-agents keep running, as in Claude Code;
        `stop_task(task_id)` stops one."""
        raise NotImplementedError

    def answer(self, ask: AskId, answer: Answer) -> AnswerStatus:
        raise NotImplementedError

    def quote(self, change: ConfigChange) -> Quote:
        """Every change goes through a quote, so there is one path. The new model is checked
        with `profiles.resolve_model` here, so a change the relay would refuse never gets a
        quote. `warning` names the uncached tokens and any running background tasks."""
        raise NotImplementedError

    async def apply(self, quote_id: str) -> None:
        """Look the quote up in this chat's own table; refuse an unknown id, a stale epoch, or
        more running background tasks than quoted (`QuoteStale`). Run
        `launch.classify_change` steps: SET_MODE and SET_MODEL use the native client setters;
        RELAUNCH closes and connects with the new options and `resume=session_id` at a turn
        boundary. Write the new config to the chat record, then a block that names the change."""
        raise NotImplementedError

    def live(self) -> AsyncIterator[Delta]:
        """Live deltas for this chat and its native sub-agents. Dropped on disconnect."""
        raise NotImplementedError

    async def close(self) -> None:
        """Disconnect, stop this chat's launcher tree (`procs.stop_chat`), revoke its relay
        grant, drop its grants. Pending asks become `expired`. Idempotent."""
        raise NotImplementedError

    @property
    def idle_seconds(self) -> float:
        """Seconds since the last message, or 0 while a turn or a background task runs.
        `Harness` reaps only idle chats, so a background sub-agent is never killed by reaping."""
        raise NotImplementedError

    # --- private, sketched for the reader ---

    async def _connect(self) -> ClaudeSDKClient:
        """In order, each step able to refuse before any prompt goes out:
        1. `procs.alive(session_id)`: an old CLI for this chat is still running -> refuse.
        2. `home.parse_claude_settings` -> `home.code_settings` (LaunchRefused on a bad key).
        3. `launch.assert_scrubbed(os.environ)`.
        4. Launch: PlanLaunch after `home.plan_auth_method` reports the subscription method
           (LaunchRefused otherwise), or RelayedLaunch with
           `relay.grant(session_id, profile, unattended=launch.unattended(kind))`.
        5. `launch_env` -> `tool_defs` / `build_server(grants)` / `gate_rules` ->
           `build_options(cli_path=launcher, settings=..., setting_sources=[], ...)`.
        6. `ClaudeSDKClient(options).connect()`. The launcher has already put the CLI under
           the OS limits.
        7. `get_server_info()` and `get_mcp_status()`: the plugins must be exactly the QMX
           plugin and the MCP servers exactly `qmx` plus the vetted ones. Anything else
           (a plugin or mod someone installed into a home, a server that appeared) closes the
           chat with a `needs_you` block, before the first prompt.
        A relaunch revokes the old grant first."""
        raise NotImplementedError

    async def _read(self, client: ClaudeSDKClient) -> None:
        """for message in client.receive_messages(): for fact in project(message): route it.
        Block -> control.sessions_append (InChild -> child session, created once); `project`
        has already redacted `sk-ant-` tokens.
        Delta -> live queues.
        TurnUsage -> run journal `model_call`, for plan chats only; relayed chats are counted
        once, at the relay (A12).
        Limits -> UsageLedger; if the ledger now gives a hard stop or the plan crosses the
        background cap, call `on_plan_limits`.
        TurnEnded -> record turn "idle", and `started=True` on the first one."""
        raise NotImplementedError

    async def _can_use_tool(
        self, tool_name: str, tool_input: dict[str, object], context: ToolPermissionContext
    ) -> PermissionResultAllow | PermissionResultDeny:
        """Park a future under a new AskId, write the `permission` block (tool, input, the
        rule that matched, and `context.suggestions` as the "always" choices unless the tool
        is an asking QMX tool), await the answer (bounded only for unattended chats), write
        the resolution block. AllowOnce on an asking QMX tool records
        `Grant(tool, args_digest(tool, final_input))` unless `TestMode.grants` is off."""
        raise NotImplementedError


@dataclass(frozen=True)
class ChatDeps:
    """What a chat borrows from the harness. Passed in, never imported as globals."""

    home: QmxHome
    control: ControlService
    broker: BrokerService
    profiles: Profiles
    relay: Relay
    mcp: VettedServers
    domain_write: DomainWritePolicy
    budgets: Mapping[str, float]
    """settings.toml [budgets]: unattended_ask_seconds, max_turns, max_budget_usd."""
    ledger: UsageLedger
    cap: BackgroundCap
    procs: AgentProcessCap
    delegate: Delegate
    test: TestMode
    on_plan_limits: Callable[[], Awaitable[None]]
    """Called when the plan crosses the background cap or hits a hard stop. The harness
    interrupts its Background chats, or every plan chat on a hard stop. A chat never reaches
    into other chats itself."""
