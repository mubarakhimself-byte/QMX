"""One chat: one `ClaudeSDKClient`, one CLI process while live, one reader task.

Identity. The chat's qmx-control session id is the SDK session id: `resume` when its JSONL
exists, `session_id` when it does not. Once a chat has started, a missing transcript is an
error, not a fresh start. The SDK transcript, the block log and the chat record share one key.

Lifecycle, one owner:

    Cold --connect--> Live --close, or the CLI ends--> Cold

While Live, the reader task drains `receive_messages()` and routes each `project()` fact.
The CLI opens every turn with an `init` and ends it with one `ResultMessage`. A prompt typed
while a tool runs is folded into the running turn and gets no turn of its own (measured, CLI
2.1.299). A record still "running" when the harness opens, or when the CLI ends mid-turn, means
the outcome is unknown: the chat shows a `needs_you` block and continues only when the operator
sends the next message.

Asks. `can_use_tool` (tool approvals and AskUserQuestion) writes a `permission` or `question`
block and parks a future in this chat's own table under that block's seq, so an `AskId` is
unique across restarts and the answer route needs no index. The answer resolves it. AllowOnce
on an asking QMX tool records a `Grant` for the exact final input, which the tool handler
consumes. AllowAlways on any other tool saves the CLI's suggested allow rules for this
workspace and hands them back to the CLI for this process. An Interactive chat waits like
Claude Code; an unattended one waits at most `[budgets] unattended_ask_seconds`, then rejects.
The money gate runs before any of this, so no answer or remembered rule reaches a call it denied,
and an input the operator edits passes the gate again before it runs.

Prompts. Who wrote the text is in its type. `OperatorText` is what the operator typed; slash
commands and `@path` work, as in Claude Code. `InjectedText` is anything QMA built from news,
files, tool output or a model. Background and Child chats launch with `verbatim_prompts=True`,
so no prompt there dispatches a slash command or reads an `@path`. An Interactive chat is never
verbatim, so it refuses `InjectedText` outright.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import json
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, Literal, cast

from claude_agent_sdk import (
    ClaudeSDKClient,
    Message,
    PermissionResultAllow,
    PermissionResultDeny,
    PermissionUpdate,
    SystemMessage,
    TaskNotificationMessage,
    TaskStartedMessage,
    TaskUpdatedMessage,
)
from claude_agent_sdk._errors import MessageParseError
from claude_agent_sdk._internal import message_parser
from claude_agent_sdk.types import TERMINAL_TASK_STATUSES, PermissionRuleValue
from qmx_control.service import SessionBlock, SessionInput
from qmx_ledger.journal import RunJournal

from qma.harness.home import (
    ChatRecord,
    QmxHome,
    SessionId,
    code_settings,
    ensure_homes,
    parse_claude_settings,
    plan_auth_method,
    plugin_refusal,
    remember_rule,
    session_id,
    write_record,
)
from qma.harness.launch import (
    ChatConfig,
    ChatKind,
    Child,
    Launch,
    LaunchRefused,
    PlanLaunch,
    RelayedLaunch,
    Step,
    TestMode,
    assert_argv_fits,
    assert_scrubbed,
    build_options,
    classify_change,
    launch_env,
    parse_budgets,
    resets_cache,
    unattended,
    verbatim,
)
from qma.harness.money import Deny, MoneySurfaceError
from qma.harness.money import gate as money_gate
from qma.harness.profiles import PLAN
from qma.harness.project import (
    Block,
    Compacted,
    Delta,
    Here,
    InChild,
    Limits,
    Piece,
    PlanFact,
    PlanMeter,
    StreamEnded,
    Target,
    TokenGate,
    TurnEnded,
    TurnUsage,
    UnreadableLimits,
    project,
    redact,
    redacted,
)
from qma.harness.relay import GrantRefused
from qma.harness.tools import (
    SERVER,
    Grant,
    Grants,
    ToolSurfaceError,
    VetCache,
    args_digest,
    build_server,
    domain_write_policy,
    gate_rules,
    keyring_refs,
    tool_defs,
    unvetted_tools,
    vet_mcp_servers,
)
from qma.harness.usage import Totals, journal_path, plan_base, plan_row

if TYPE_CHECKING:
    from claude_agent_sdk import McpServerConfig
    from claude_agent_sdk.types import McpStatusResponse, ToolPermissionContext
    from qmx_broker.service import BrokerService
    from qmx_control.service import ControlService
    from qmx_tools.service import DomainContext

    from qma.harness.money import GateRules
    from qma.harness.procs import AgentProcessCap
    from qma.harness.relay import Relay, RelayGrant

_sdk_parse = message_parser.parse_message


def _parse(data: dict[str, Any]) -> Message | None:
    """The SDK parser raises `TypeError` and the like, not only `MessageParseError`, on some
    malformed messages, such as a `rate_limit_info` of null. Every failure becomes a
    `MessageParseError` that carries the message, so the reader can tell a rate-limit event it
    cannot read and stop the plan."""
    try:
        return _sdk_parse(data)
    except MessageParseError:
        raise
    except Exception as error:
        raise MessageParseError(f"{type(error).__name__}: {error}", data) from error


message_parser.parse_message = _parse
"""`ClaudeSDKClient.receive_messages` imports `parse_message` at each call, so this is the one
seam where a parse failure is still tied to its message."""

PLUGIN: Final = "qmx"
CLOSE_WAIT_S: Final = 10.0
MCP_SETTLE_S: Final = 30.0
"""How long a launch waits for the CLI to finish connecting the vetted external servers. The
CLI connects them after it starts and reports them `pending` until then, with no tools. A
server still pending then is switched off with a `needs_you` block, as a server that fails
vetting is, and the chat starts without it. The CLI keeps a switch-off in its own state for the
workspace, so a launch switches every vetted server it finds `disabled` back on first, and each
chat vets and settles every server afresh."""


@dataclass(frozen=True)
class OperatorText:
    """Text the operator typed in the console or UI. Only the HTTP turn route makes one."""

    text: str


@dataclass(frozen=True)
class InjectedText:
    """Text QMA built from news, files, tool output or a model. Every producer of such text
    wraps it here at its source."""

    text: str


type Prompt = OperatorText | InjectedText


class UntrustedPrompt(ValueError):
    """`InjectedText` was sent to an Interactive chat, which is not verbatim, so a slash
    command or an `@path` in it would run. Raised before anything reaches the CLI."""


def admits(kind: ChatKind, prompt: Prompt) -> bool:
    """Operator text goes to any chat. Injected text goes only to a verbatim chat."""
    return isinstance(prompt, OperatorText) or verbatim(kind)


@dataclass(frozen=True)
class AskId:
    """`<session_id>.<n>`, where n is the seq of the ask's block in the chat's block log."""

    session_id: SessionId
    n: int

    @classmethod
    def parse(cls, raw: str) -> AskId:
        chat, _, n = raw.rpartition(".")
        if not (n.isascii() and n.isdigit()):
            raise ValueError(f"{raw!r} is not an ask id")
        return cls(session_id(chat), int(n))

    def __str__(self) -> str:
        return f"{self.session_id}.{self.n}"


@dataclass(frozen=True)
class AllowOnce:
    edited_input: dict[str, Any] | None = None


@dataclass(frozen=True)
class AllowAlways:
    """Allow, and save the CLI's suggested allow rules to
    `settings.toml [claude.remembered."<workspace>"]`. Not offered for asking QMX tools."""


@dataclass(frozen=True)
class Reject:
    message: str = ""


@dataclass(frozen=True)
class Answers:
    """Answers to an AskUserQuestion call, by question text."""

    answers: dict[str, str]


type Answer = AllowOnce | AllowAlways | Reject | Answers

type AnswerStatus = Literal["resolved", "already_answered", "expired", "invalid", "unknown"]
"""A second answer to the same ask is `already_answered`. An ask whose process ended or whose
unattended wait ran out is `expired`. `invalid` is an answer that does not fit the ask:
AllowAlways on an asking QMX tool or with no rule to save, Answers to a tool ask, or a tool
answer to a question. `unknown` is an id that names no chat."""

QUESTION_TOOL: Final = "AskUserQuestion"
REJECTED: Final = "the operator rejected this call"
NOT_IN_TIME: Final = "the operator did not answer in time"
ENDED: Final = "the agent process ended before the operator answered"


@dataclass(frozen=True)
class _Expired:
    reason: str


@dataclass(frozen=True)
class _Ask:
    tool: str
    input: dict[str, Any]
    asking_qmx: bool
    """One-shot approvals bound to the exact arguments, and no "always"."""
    rules: tuple[PermissionRuleValue, ...]
    """The allow rules the CLI suggested, offered as "always"."""
    reply: asyncio.Future[Answer | _Expired]

    def fits(self, answer: Answer) -> bool:
        question = self.tool == QUESTION_TOOL
        match answer:
            case Answers():
                return question
            case Reject():
                return True
            case AllowOnce():
                return not question
            case AllowAlways():
                return not question and not self.asking_qmx and bool(self.rules)


@dataclass(frozen=True)
class Quote:
    """The warning that comes before a change. `apply` takes only the id of a quote this chat
    issued, so no change runs without its warning having been produced first. `epoch` counts
    the prompts sent to the chat when quoted, so a warning is never reused after the
    conversation grew."""

    id: str
    session_id: SessionId
    old: ChatConfig
    new: ChatConfig
    steps: tuple[Step, ...]
    recomputed_tokens: int
    """Context tokens the next request sends uncached, from the transcript's last reply."""
    background_tasks: int
    """Background Bash and sub-agent tasks running when quoted. A relaunch stops them."""
    warning: str | None
    """None when the change keeps the cache and stops nothing."""
    epoch: int


class QuoteStale(RuntimeError):
    """The quote is unknown, used, or out of date. Quote again; the routes answer 409."""


EFFORT_WAIT_S: Final = 60.0


def context_tokens(path: Path | None) -> int:
    """The main conversation's size at its last reply: that request's input, cache reads and
    writes, plus its output, which the next request also resends. 0 with no reply yet."""
    if path is None:
        return 0
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "assistant":
            continue
        if cast("dict[str, Any]", entry).get("isSidechain"):
            continue
        usage = cast("dict[str, Any]", entry).get("message", {}).get("usage")
        if isinstance(usage, dict):
            names = (
                "input_tokens",
                "cache_creation_input_tokens",
                "cache_read_input_tokens",
                "output_tokens",
            )
            return sum(int(cast("dict[str, Any]", usage).get(name) or 0) for name in names)
    return 0


def _tokens(count: int) -> str:
    return f"{round(count / 1000)}k" if count >= 1000 else str(count)


def warning(
    old: ChatConfig, new: ChatConfig, steps: tuple[Step, ...], tokens: int, tasks: int
) -> str | None:
    """ "Switching to kimi resends ~182k tokens uncached and stops 1 background task.", or None
    when the change loses no cache and stops nothing."""
    parts = []
    if resets_cache(old, new) and tokens > 0:
        parts.append(f"resends ~{_tokens(tokens)} tokens uncached")
    if Step.RELAUNCH in steps and tasks:
        parts.append(f"stops {tasks} background task{'' if tasks == 1 else 's'}")
    if not parts:
        return None
    if old.profile != new.profile:
        subject = f"Switching to {new.profile}"
    elif old.model != new.model:
        subject = f"Switching to {new.model}"
    else:
        subject = f"Setting effort to {new.effort or 'the default'}"
    return f"{subject} {' and '.join(parts)}."


def describe(config: ChatConfig) -> dict[str, Any]:
    return {
        "profile": config.profile,
        "model": config.model,
        "effort": config.effort,
        "mode": config.mode,
    }


def rule_text(rule: PermissionRuleValue) -> str:
    return f"{rule.tool_name}({rule.rule_content})" if rule.rule_content else rule.tool_name


def allow_rules(suggestions: list[PermissionUpdate]) -> tuple[PermissionRuleValue, ...]:
    return tuple(
        rule
        for update in suggestions
        if update.type == "addRules" and update.behavior == "allow"
        for rule in update.rules or []
    )


@dataclass(frozen=True)
class ChatDeps:
    """What a chat borrows from the harness. Passed in, never imported as globals."""

    home: QmxHome
    control: ControlService
    procs: AgentProcessCap
    launcher: Path
    relay: Relay
    broker: BrokerService
    domain: DomainContext
    """The domain tools' context. It shares `control`, so no second writer runs."""
    on_plan_limits: Callable[[PlanFact], None]
    """Where a plan chat's rate-limit facts and `/usage` readings go: the harness's ledger,
    which may stop every plan chat."""
    vetted: VetCache = field(default_factory=VetCache)
    """External MCP tool lists already vetted, by config digest, for this harness."""
    delegate: Callable[[SessionId, str, str], Awaitable[str]] | None = None
    """`Harness._delegate`, called with the calling chat's id, a profile and a prompt."""
    test: TestMode | None = None
    """Live checks only; None is every layer on."""

    @property
    def redaction(self) -> bool:
        return self.test is None or self.test.redaction


async def _settled(
    client: ClaudeSDKClient, servers: frozenset[str]
) -> tuple[McpStatusResponse, list[str]]:
    """`get_mcp_status()` once none of `servers` is still `pending` or `disabled`, polled for
    at most `MCP_SETTLE_S`, and the servers not up then."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + MCP_SETTLE_S
    while True:
        status = await client.get_mcp_status()
        pending = sorted(
            server["name"]
            for server in status["mcpServers"]
            if server["name"] in servers and server["status"] in {"pending", "disabled"}
        )
        if not pending or loop.time() > deadline:
            return status, pending
        await asyncio.sleep(0.2)


KEEP_OFF_POLL_S: Final = 0.5
KEEP_OFF_BACKOFF_MAX: Final = 5

log = logging.getLogger(__name__)


async def _keep_off(client: ClaudeSDKClient, servers: frozenset[str]) -> None:
    """Switch `servers` off whenever the CLI reports one connected, for the life of the chat.
    A switch-off sent while a server is still connecting reads `disabled` at once, and the
    server connects anyway when its start finishes (measured, S35), so no state is final. The
    SDK raises on its control-request timeout; the keeper logs it and polls again, and the gate
    denies the servers' tools meanwhile (`GateRules.dropped_servers`)."""
    failures = 0
    while True:
        try:
            status = await client.get_mcp_status()
            for server in status["mcpServers"]:
                if server["name"] in servers and server["status"] == "connected":
                    await client.toggle_mcp_server(server["name"], enabled=False)
            failures = 0
        except Exception as error:
            failures += 1
            log.warning("keeping %s off failed %d times: %r", sorted(servers), failures, error)
        await asyncio.sleep(KEEP_OFF_POLL_S * 2 ** min(failures, KEEP_OFF_BACKOFF_MAX))


def track_task(running: set[str], message: Message) -> None:
    """Add a task the CLI started; drop one it reports finished. A background task can end
    with only a `task_updated` whose status is terminal, so both kinds count."""
    match message:
        case TaskStartedMessage(task_id=task):
            running.add(task)
        case (
            TaskNotificationMessage(task_id=task, status=status)
            | TaskUpdatedMessage(task_id=task, status=status)
        ) if status in TERMINAL_TASK_STATUSES:
            running.discard(task)
        case _:
            pass


def transcript(home: QmxHome, chat: SessionId) -> Path | None:
    """The SDK JSONL of this chat, under any project folder of the plan home."""
    return next((home.plan_dir / "projects").glob(f"*/{chat}.jsonl"), None)


def unexpected_extensions(
    info: Mapping[str, Any] | None, status: McpStatusResponse, servers: frozenset[str]
) -> list[str]:
    """What the CLI loaded besides its built-ins, the QMX plugin and the MCP `servers` QMA
    passed. The server info lists no plugins, so a plugin shows as its `<plugin>:` commands
    and agents."""
    commands = cast("list[dict[str, Any]]", (info or {}).get("commands", []))
    agents = cast("list[dict[str, Any]]", (info or {}).get("agents", []))
    found = [
        f"command {command['name']}"
        for command in commands
        if not command.get("builtin") and not str(command["name"]).startswith(f"{PLUGIN}:")
    ]
    found += [
        f"agent {agent['name']}"
        for agent in agents
        if ":" in str(agent["name"]) and not str(agent["name"]).startswith(f"{PLUGIN}:")
    ]
    found += [
        f"MCP server {server['name']}"
        for server in status["mcpServers"]
        if server["name"] not in servers
    ]
    return found


def unexpected_plugins(init: Mapping[str, Any]) -> list[str]:
    """The CLI sends `init` only after a prompt, and a plugin that adds nothing but hooks shows
    nowhere earlier."""
    sources = [str(plugin.get("source")) for plugin in init.get("plugins", [])]
    return [
        f"plugin {source}"
        for source in sources
        if source != f"{PLUGIN}@inline" and not source.endswith("@builtin")
    ]


def installed_plugins(claude_home: Path) -> list[str]:
    """Plugins a Claude home's own files enable or install. With `setting_sources=[]` the CLI
    loads none of them (HP0 OQ5), so this refuses a plant before it can matter."""
    enabled = _json(claude_home / "settings.json").get("enabledPlugins", {})
    installed = _json(claude_home / "plugins" / "installed_plugins.json").get("plugins", {})
    names = [name for name, on in enabled.items() if on]
    names += [name for name, copies in installed.items() if copies and name not in names]
    return names


def _json(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except OSError, ValueError:
        return {}
    return cast("dict[str, Any]", loaded) if isinstance(loaded, dict) else {}


def _loaded(found: list[str]) -> str:
    found_text = ", ".join(found)
    return f"the CLI loaded {found_text} besides the QMX plugin; remove it from the Claude home"


@dataclass
class _Live:
    client: ClaudeSDKClient
    grant: RelayGrant | None
    reader: asyncio.Task[None] | None = None
    keeper: asyncio.Task[None] | None = None


@dataclass
class _Stream:
    gates: dict[Target, TokenGate] = field(default_factory=dict[Target, TokenGate])
    listeners: set[asyncio.Queue[Delta]] = field(default_factory=set[asyncio.Queue[Delta]])

    def publish(self, delta: Delta) -> None:
        if not delta.text:
            return
        for queue in self.listeners:
            queue.put_nowait(delta)

    def release(self, target: Target, pieces: list[Piece]) -> None:
        for kind, text in pieces:
            self.publish(Delta(target, kind, text))

    def close(self, target: Target) -> None:
        gate = self.gates.pop(target, None)
        if gate is not None:
            self.release(target, gate.close())

    def close_all(self) -> None:
        for target in list(self.gates):
            self.close(target)


class Chat:
    """Owned by `Harness`. Never shared across event loops."""

    def __init__(self, record: ChatRecord, deps: ChatDeps) -> None:
        self.record = record
        self._deps = deps
        self._live: _Live | None = None
        self._lock = asyncio.Lock()
        self._closing = False
        self._children: dict[str, str] = {}
        self._stream = _Stream()
        self._grants = Grants()
        self._gate: GateRules | None = None
        self._asks: dict[int, _Ask] = {}
        self._settled: dict[int, AnswerStatus] = {}
        self._usage: tuple[RunJournal, Totals] | None = None
        self._last = time.monotonic()
        self._tasks: set[str] = set()
        """Background Bash and sub-agents the CLI reported started and not yet finished."""
        self._epoch = 0
        """Prompts sent since this object was made. A quote from an older epoch is stale."""
        self._quotes: dict[str, Quote] = {}
        self._ends: list[asyncio.Future[TurnEnded | None]] = []

    @property
    def session_id(self) -> SessionId:
        return self.record.session_id

    async def send(self, prompt: Prompt) -> None:
        """Connect if Cold, write the `user` block and turn "running", then `client.query`.
        While a turn runs, the SDK queues the message, like typing into Claude Code. The
        harness has already checked that this chat admits the prompt."""
        async with self._lock:
            live = self._live or await self._connect()
            self._live = live
            self._last = time.monotonic()
            self._epoch += 1
            await self._note("user", {"text": prompt.text})
            self._write(turn="running")
            await live.client.query(prompt.text)

    async def quote(self, new: ChatConfig) -> Quote:
        """The steps, the warning and the counts `apply` will hold the chat to. The harness has
        already checked that `new` names a profile and a model the relay accepts."""
        old = self.record.config
        steps = classify_change(old, new)
        path = transcript(self._deps.home, self.session_id)
        tokens = await asyncio.to_thread(context_tokens, path)
        tasks = len(self._tasks)
        quote = Quote(
            id=uuid.uuid4().hex,
            session_id=self.session_id,
            old=old,
            new=new,
            steps=steps,
            recomputed_tokens=tokens,
            background_tasks=tasks,
            warning=warning(old, new, steps, tokens, tasks),
            epoch=self._epoch,
        )
        self._quotes[quote.id] = quote
        return quote

    async def apply(self, quote_id: str, *, plan_stop: str | None) -> Quote:
        """Run a quote this chat issued, once. Refuse an unknown or used id, a prompt sent since
        the quote, a config changed since, or more background tasks than it named. A Cold chat
        only records the new config; its next send launches with it. A relaunch and an
        `/effort` wait for the running turn's end to be refused, never cut it short.
        `plan_stop` is the overage stop's reason, which refuses a switch onto the plan."""
        async with self._lock:
            quote = self._quotes.pop(quote_id, None)
            if quote is None:
                raise QuoteStale("this chat issued no such quote, or it was used; quote again")
            if quote.epoch != self._epoch or quote.old != self.record.config:
                raise QuoteStale("the chat moved on since this quote; quote again")
            if len(self._tasks) > quote.background_tasks:
                raise QuoteStale(
                    f"{len(self._tasks)} background tasks run now and the quote named "
                    f"{quote.background_tasks}; quote again"
                )
            if quote.new.profile == PLAN and quote.old.profile != PLAN and plan_stop:
                raise LaunchRefused(f"plan use is stopped: {plan_stop}")
            live = self._live
            boundary = {Step.RELAUNCH, Step.SET_EFFORT} & set(quote.steps)
            if live is not None and boundary and self.record.turn == "running":
                raise QuoteStale("a turn is running; quote again when it ends")
            if live is not None:
                await self._run_steps(live, quote)
            self._write(config=quote.new)
            await self._note(
                "changed",
                {
                    "kind": "config",
                    "steps": [step.value for step in quote.steps],
                    "from": describe(quote.old),
                    "to": describe(quote.new),
                },
            )
            return quote

    async def _run_steps(self, live: _Live, quote: Quote) -> None:
        if Step.RELAUNCH in quote.steps:
            await self._shut()
            self.record = replace(self.record, config=quote.new)
            try:
                self._live = await self._connect()
            except BaseException:
                self.record = replace(self.record, config=quote.old)
                raise
            return
        for step in quote.steps:
            match step:
                case Step.SET_MODE:
                    await live.client.set_permission_mode(quote.new.mode)
                case Step.SET_MODEL:
                    await live.client.set_model(quote.new.model)
                case Step.SET_EFFORT:
                    await self._set_effort(live, str(quote.new.effort))

    async def _set_effort(self, live: _Live, effort: str) -> None:
        """`/effort` replies with a synthetic result and no model call (HP0 S37)."""
        self._write(turn="running")
        await live.client.query(f"/effort {effort}")
        loop = asyncio.get_running_loop()
        deadline = loop.time() + EFFORT_WAIT_S
        while self.record.turn == "running" and self._live is live:
            if loop.time() > deadline:
                raise LaunchRefused(f"/effort {effort} got no reply in {EFFORT_WAIT_S:.0f} s")
            await asyncio.sleep(0.05)

    def next_end(self) -> asyncio.Future[TurnEnded | None]:
        """Resolves with the next turn's end, or None when the process ends first."""
        end: asyncio.Future[TurnEnded | None] = asyncio.get_running_loop().create_future()
        self._ends.append(end)
        return end

    def _resolve_ends(self, ended: TurnEnded | None) -> None:
        ends, self._ends = self._ends, []
        for end in ends:
            if not end.done():
                end.set_result(ended)

    @property
    def idle_seconds(self) -> float:
        """Seconds since the CLI last spoke or a prompt went in, or 0 while the chat is Cold,
        a turn runs or a background task runs. Only an idle chat is evicted or reaped, so a
        background Bash or sub-agent is never killed by either."""
        if self._live is None or self.record.turn == "running" or self._tasks:
            return 0.0
        return time.monotonic() - self._last

    async def close_if_idle(self, at_least: float) -> bool:
        """Close the chat if it has been idle longer than `at_least` seconds, checked under the
        chat's lock so a send that got in first keeps it open. True when it closed."""
        async with self._lock:
            if self.idle_seconds <= at_least:
                return False
            await self._shut()
            return True

    async def interrupt(self) -> None:
        """Background Bash and sub-agents keep running, as in Claude Code."""
        if self._live is not None:
            await self._live.client.interrupt()

    async def stop_plan(self, reason: str) -> None:
        """The overage stop. Kills the CLI tree first, because an interrupt would let a prompt
        queued in the CLI start as a new turn (measured, HP10 check). Then the chat closes and
        writes a `needs_you` block naming the rule. The next send relaunches with `resume`."""
        async with self._lock:
            live, self._live = self._live, None
            if live is None:
                return
            self._closing = True
            try:
                await asyncio.to_thread(self._deps.procs.stop_chat, self.session_id)
                await self._end(live)
            finally:
                self._closing = False
            self._stream.close_all()
            self._write(turn="idle")
            await self._note("needs_you", {"reason": f"plan use stopped: {reason}"})

    @property
    def on_plan(self) -> bool:
        return self.record.config.profile == PLAN

    @property
    def is_live(self) -> bool:
        return self._live is not None

    async def live(self) -> AsyncIterator[Delta]:
        """Live deltas for this chat and its native sub-agents. Dropped on disconnect."""
        queue: asyncio.Queue[Delta] = asyncio.Queue()
        self._stream.listeners.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._stream.listeners.discard(queue)

    def answer(self, n: int, answer: Answer) -> AnswerStatus:
        """On the harness's event loop only. An n this process never asked belongs to an
        earlier process, so it is `expired`."""
        ask = self._asks.get(n)
        if ask is None:
            return self._settled.get(n, "expired")
        if not ask.fits(answer):
            return "invalid"
        self._settle(n, "already_answered", answer)
        return "resolved"

    def _settle(self, n: int, status: AnswerStatus, reply: Answer | _Expired) -> None:
        ask = self._asks.pop(n)
        self._settled[n] = status
        if not ask.reply.done():
            ask.reply.set_result(reply)

    async def close(self) -> None:
        """Disconnect, stop this chat's launcher tree and revoke its relay grant. Pending asks
        become `expired`. Idempotent."""
        async with self._lock:
            await self._shut()

    async def _shut(self) -> None:
        live, self._live = self._live, None
        if live is None:
            return
        self._closing = True
        try:
            await self._end(live)
        finally:
            self._closing = False

    async def _end(self, live: _Live) -> None:
        self._tasks.clear()
        self._resolve_ends(None)
        for n in list(self._asks):
            self._settle(n, "expired", _Expired(ENDED))
        if live.grant is not None:
            await self._deps.relay.revoke(live.grant)
        with contextlib.suppress(Exception):
            await asyncio.wait_for(live.client.disconnect(), CLOSE_WAIT_S)
        if live.keeper is not None:
            live.keeper.cancel()
            with contextlib.suppress(Exception, asyncio.CancelledError):
                await live.keeper
        if live.reader is not None and live.reader is not asyncio.current_task():
            live.reader.cancel()
            with contextlib.suppress(Exception, asyncio.CancelledError):
                await live.reader
        if self._usage is not None:
            journal, self._usage = self._usage[0], None
            await asyncio.to_thread(journal.close)
        await asyncio.to_thread(self._deps.procs.stop_chat, self.session_id)

    async def _connect(self) -> _Live:
        try:
            return await self._launch()
        except LaunchRefused as refused:
            await self._note("needs_you", {"reason": str(refused)})
            raise

    async def _launch(self) -> _Live:
        deps, config, chat = self._deps, self.record.config, self.session_id
        if await asyncio.to_thread(deps.procs.alive, chat):
            raise LaunchRefused("an earlier agent process of this chat is still running")
        ensure_homes(deps.home)
        tampered = await asyncio.to_thread(plugin_refusal, deps.home)
        if tampered is not None:
            raise LaunchRefused(tampered)
        planted = [
            name
            for claude_home in (deps.home.plan_dir, deps.home.relayed_dir)
            for name in await asyncio.to_thread(installed_plugins, claude_home)
        ]
        if planted:
            raise LaunchRefused(
                f"the Claude home has plugin {', '.join(planted)} installed besides the QMX "
                "plugin; remove it from the Claude home"
            )
        user = parse_claude_settings(await asyncio.to_thread(deps.control.settings_get, "claude"))
        budgets = parse_budgets(await asyncio.to_thread(deps.control.settings_get, "budgets"))
        settings = code_settings(
            user,
            launcher=deps.launcher,
            workspace=config.workspace,
            memory_dir=deps.home.memory_dir(config.workspace),
        )
        assert_scrubbed(os.environ)
        exists = transcript(deps.home, chat) is not None
        if self.record.started and not exists:
            raise LaunchRefused(
                "this chat's transcript is gone from the plan home; start a new chat"
            )
        launch = await self._routing(settings)
        grant = launch.grant if isinstance(launch, RelayedLaunch) else None
        try:
            servers, gate, vetted = await self._tools(launch, user.external_tools_unattended)
            env = launch_env(launch, home=deps.home, session_id=chat, cap=deps.procs.handle_name)
            options = build_options(
                config,
                session_id=chat,
                transcript_exists=exists,
                env=env,
                home=deps.home,
                settings_json=settings,
                launcher=deps.launcher,
                can_use_tool=self._can_use_tool,
                mcp_servers=servers,
                gate=gate,
                budgets=budgets,
                test=deps.test,
            )
            assert_argv_fits(options)
            live = _Live(ClaudeSDKClient(options), grant)
            await live.client.connect()
        except BaseException:
            if grant is not None:
                await deps.relay.revoke(grant)
            raise
        try:
            status = await live.client.get_mcp_status()
            found = unexpected_extensions(
                await live.client.get_server_info(), status, frozenset(servers)
            )
            if found:
                raise LaunchRefused(_loaded(found))
            for server in status["mcpServers"]:
                if server["name"] in vetted and server["status"] == "disabled":
                    await live.client.toggle_mcp_server(server["name"], enabled=True)
            settled, pending = await _settled(live.client, frozenset(vetted))
            gate.dropped_servers.update(pending)
            for name in pending:
                await live.client.toggle_mcp_server(name, enabled=False)
                await self._note(
                    "needs_you",
                    {
                        "reason": f"the MCP server {name} was left out: it did not finish "
                        f"connecting in {MCP_SETTLE_S:.0f} s"
                    },
                )
            if pending:
                live.keeper = asyncio.create_task(_keep_off(live.client, frozenset(pending)))
            compared = {name: tools for name, tools in vetted.items() if name not in pending}
            unvetted = unvetted_tools(settled, compared)
            if unvetted:
                raise LaunchRefused(
                    f"the CLI loaded MCP tools that vetting never saw ({', '.join(unvetted)})"
                )
        except BaseException:
            await self._end(live)
            raise
        live.reader = asyncio.create_task(self._read(live))
        return live

    async def _tools(
        self, launch: Launch, external_unattended: frozenset[str]
    ) -> tuple[dict[str, McpServerConfig], GateRules, Mapping[str, frozenset[str]]]:
        """The `qmx` server, the vetted external servers, the gate's rules and each vetted
        server's tool names. A refused external server gets a `needs_you` block and is left
        out; the chat still starts. `external_unattended` is the operator's allow-list for
        external tools in an unattended chat or mode."""
        deps = self._deps
        control = deps.control
        delegate = (
            None
            if deps.delegate is None or isinstance(self.record.config.kind, Child)
            else functools.partial(deps.delegate, self.session_id)
        )
        defs = await tool_defs(
            control=control, broker=deps.broker, domain=deps.domain, delegate=delegate
        )
        policy = domain_write_policy(await asyncio.to_thread(control.settings_get, "agents"))
        try:
            qmx = build_server(
                defs,
                grants=self._grants,
                domain_write=policy,
                enforce_grants=deps.test is None or deps.test.grants,
            )
        except (MoneySurfaceError, ToolSurfaceError) as refused:
            raise LaunchRefused(f"the QMX tools cannot start: {refused}") from None
        vetted = await vet_mcp_servers(
            await asyncio.to_thread(control.settings_get, "mcp_servers"), deps.vetted
        )
        for name, reason in vetted.refused.items():
            await self._note(
                "needs_you", {"reason": f"the MCP server {name} was refused: {reason}"}
            )
        gate = gate_rules(
            defs,
            domain_write=policy,
            home=deps.home,
            config_dir=deps.home.plan_dir
            if isinstance(launch, PlanLaunch)
            else deps.home.relayed_dir,
            keyring_names=await asyncio.to_thread(keyring_refs, control),
            unattended=unattended(self.record.config.kind),
            external_unattended=external_unattended,
        )
        self._gate = gate
        return {SERVER: qmx, **vetted.configs}, gate, vetted.tools

    async def _routing(self, settings: str) -> Launch:
        """The plan only after its login reports the subscription method. Any other profile
        through a fresh relay grant."""
        deps, config = self._deps, self.record.config
        if config.profile == PLAN:
            auth = await asyncio.to_thread(plan_auth_method, deps.home, settings)
            auth.require()
            return PlanLaunch()
        try:
            return RelayedLaunch(await deps.relay.grant(self.session_id, config.profile))
        except GrantRefused as refused:
            raise LaunchRefused(str(refused)) from None

    async def _read(self, live: _Live) -> None:
        try:
            async for message in live.client.receive_messages():
                self._last = time.monotonic()
                track_task(self._tasks, message)
                if isinstance(message, SystemMessage) and message.subtype == "init":
                    found = unexpected_plugins(message.data)
                    if found:
                        await self._note("needs_you", {"reason": _loaded(found)})
                        self._write(turn="idle")
                        return
                    self._write(turn="running")
                for fact in project(message, redact_tokens=self._deps.redaction):
                    await self._route(fact)
        except MessageParseError as error:
            if not (isinstance(error.data, dict) and error.data.get("type") == "rate_limit_event"):
                raise
            if self.on_plan:
                self._deps.on_plan_limits(
                    UnreadableLimits(f"a rate-limit event could not be read: {error}")
                )
        finally:
            if not self._closing:
                await self._lost(live)

    async def _lost(self, live: _Live) -> None:
        async with self._lock:
            if self._live is live:
                self._live = None
            self._stream.close_all()
            if self.record.turn == "running":
                await self._note(
                    "needs_you",
                    {"reason": "the agent process ended during a turn; its outcome is unknown"},
                )
                self._write(turn="idle")
            await self._end(live)

    async def _route(
        self,
        fact: Block | Delta | StreamEnded | TurnUsage | PlanFact | TurnEnded | Compacted,
    ) -> None:
        match fact:
            case Block(target=target, block=block):
                await self._append(target, block)
            case Delta(kind="tool_progress") if self._deps.redaction:
                self._stream.publish(replace(fact, text=redact(fact.text)))
            case Delta(target=target, kind="text" | "thinking" as kind, text=text) if (
                self._deps.redaction
            ):
                gate = self._stream.gates.setdefault(target, TokenGate())
                self._stream.release(target, gate.feed(kind, text))
            case Delta():
                self._stream.publish(fact)
            case StreamEnded(target=target):
                self._stream.close(target)
            case TurnEnded():
                self._stream.close(Here())
                self._write(turn="idle", started=True)
                self._resolve_ends(fact)
            case Compacted(trigger=trigger):
                await self._note("changed", {"kind": "compacted", "trigger": trigger})
            case TurnUsage() if self.on_plan:
                await self._journal_turn(fact)
            case Limits() | UnreadableLimits() | PlanMeter() if self.on_plan:
                self._deps.on_plan_limits(fact)
            case TurnUsage() | Limits() | UnreadableLimits() | PlanMeter():
                pass

    async def _journal_turn(self, turn: TurnUsage) -> None:
        """One `model_call` row per plan turn. Relayed chats are counted at the relay."""
        if self._usage is None:
            path = journal_path(self._deps.home, self.session_id)
            base = await asyncio.to_thread(plan_base, path)
            journal = await asyncio.to_thread(RunJournal, path, self.session_id)
            self._usage = (journal, base)
        journal, base = self._usage
        payload, totals = plan_row(turn, base)
        self._usage = (journal, totals)
        if payload is not None:
            await asyncio.to_thread(journal.append, "model_call", payload)

    async def _note(self, kind: str, content: dict[str, Any]) -> None:
        if self._deps.redaction:
            content = redacted(content)
        await self._append(Here(), SessionBlock.model_validate({"type": kind, "content": content}))

    async def _append(self, target: Target, block: SessionBlock) -> None:
        session = self.session_id if isinstance(target, Here) else await self._child(target)
        await asyncio.to_thread(self._deps.control.sessions_append, session, block)

    async def _child(self, target: InChild) -> str:
        child = self._children.get(target.tool_use_id)
        if child is None:
            control = self._deps.control
            created = await asyncio.to_thread(
                control.sessions_create,
                SessionInput(title="Helper agent", origin="qma", parent_id=self.session_id),
            )
            child = self._children[target.tool_use_id] = str(created["id"])
            await self._append(
                Here(),
                SessionBlock(
                    type="agents",
                    content={"tool_use_id": target.tool_use_id, "session_id": child},
                ),
            )
        return child

    def _write(self, **changes: Any) -> None:
        self.record = replace(self.record, **changes)
        write_record(self._deps.home, self.record)

    async def _can_use_tool(
        self, tool_name: str, tool_input: dict[str, Any], context: ToolPermissionContext
    ) -> PermissionResultAllow | PermissionResultDeny:
        asking_qmx = self._gate is not None and tool_name in self._gate.mandatory_asks
        rules = () if asking_qmx else allow_rules(context.suggestions)
        kind = "question" if tool_name == QUESTION_TOOL else "permission"
        content: dict[str, Any] = {"tool": tool_name, "input": tool_input, "state": "asking"}
        if context.decision_reason:
            content["reason"] = context.decision_reason
        if rules:
            content["always"] = [rule_text(rule) for rule in rules]
            content["workspace"] = str(self.record.config.workspace)
        if self._deps.redaction:
            content = redacted(content)
        # Appended on the loop, not in a thread, so the ask is in the table before any client
        # can read its seq and answer it.
        written = self._deps.control.sessions_append(
            self.session_id, SessionBlock.model_validate({"type": kind, "content": content})
        )
        n = int(cast("int", written["seq"]))
        reply: asyncio.Future[Answer | _Expired] = asyncio.get_running_loop().create_future()
        ask = self._asks[n] = _Ask(tool_name, tool_input, asking_qmx, rules, reply)
        try:
            resolved = await self._wait(n, ask)
        except asyncio.CancelledError:
            if n in self._asks:
                self._settle(n, "expired", _Expired(ENDED))
            raise
        return await self._resolve(n, ask, kind, resolved)

    async def _wait(self, n: int, ask: _Ask) -> Answer | _Expired:
        if not unattended(self.record.config.kind):
            return await ask.reply
        budgets = await asyncio.to_thread(self._deps.control.settings_get, "budgets")
        await asyncio.wait({ask.reply}, timeout=parse_budgets(budgets).unattended_ask_seconds)
        if n in self._asks:
            self._settle(n, "expired", _Expired(NOT_IN_TIME))
        return ask.reply.result()

    def _edit_refused(self, tool: str, edited: dict[str, Any]) -> str | None:
        """The money gate's reason to deny an input the operator edited, or None. The CLI ran
        the gate on the model's input only, so the edit gets the same check before it runs."""
        if self._deps.test is not None and not self._deps.test.gate_hook:
            return None
        if self._gate is None:
            return "the money gate has no rules for this chat, so the edited call is blocked"
        try:
            verdict = money_gate(
                tool,
                edited,
                self._gate,
                cwd=str(self.record.config.workspace),
                agent_id=None,
                permission_mode=self.record.config.mode,
            )
        except Exception as error:
            return f"the gate failed ({type(error).__name__}), so the edited call is blocked"
        return verdict.reason if isinstance(verdict, Deny) else None

    async def _resolve(
        self, n: int, ask: _Ask, kind: str, reply: Answer | _Expired
    ) -> PermissionResultAllow | PermissionResultDeny:
        result: PermissionResultAllow | PermissionResultDeny
        match reply:
            case _Expired(reason=reason):
                state, result = "expired", PermissionResultDeny(message=reason)
            case Reject(message=message):
                state, result = "rejected", PermissionResultDeny(message=message or REJECTED)
            case Answers(answers=answers):
                state = "answered"
                result = PermissionResultAllow(updated_input={**ask.input, "answers": answers})
            case AllowOnce(edited_input=edited) if edited is not None and (
                refused := self._edit_refused(ask.tool, edited)
            ):
                state, result = "denied", PermissionResultDeny(message=refused)
            case AllowOnce(edited_input=edited):
                final = ask.input if edited is None else edited
                if ask.asking_qmx and (self._deps.test is None or self._deps.test.grants):
                    self._grants.record(Grant(ask.tool, args_digest(ask.tool, final)))
                state, result = "allowed", PermissionResultAllow(updated_input=edited)
            case AllowAlways():
                workspace = self.record.config.workspace
                for rule in ask.rules:
                    await asyncio.to_thread(
                        remember_rule, self._deps.control, rule_text(rule), workspace
                    )
                state = "allowed_always"
                session = PermissionUpdate(
                    "addRules", rules=list(ask.rules), behavior="allow", destination="session"
                )
                result = PermissionResultAllow(updated_permissions=[session])
        await self._note(kind, {"ask": n, "state": state})
        return result
