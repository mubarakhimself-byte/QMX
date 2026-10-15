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

Asks. Until approvals are wired, `can_use_tool` rejects every call that would ask, so no chat
writes a file or runs a command the CLI would have asked about.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from claude_agent_sdk import ClaudeSDKClient, PermissionResultDeny, SystemMessage
from qmx_control.service import SessionBlock, SessionInput

from qma.harness.home import (
    ChatRecord,
    QmxHome,
    SessionId,
    code_settings,
    ensure_homes,
    parse_claude_settings,
    plan_auth_method,
    plugin_refusal,
    write_record,
)
from qma.harness.launch import (
    Launch,
    LaunchRefused,
    PlanLaunch,
    RelayedLaunch,
    TestMode,
    assert_argv_fits,
    assert_scrubbed,
    build_options,
    launch_env,
)
from qma.harness.money import MoneySurfaceError
from qma.harness.profiles import PLAN
from qma.harness.project import (
    Block,
    Compacted,
    Delta,
    Here,
    InChild,
    Limits,
    Piece,
    StreamEnded,
    Target,
    TokenGate,
    TurnEnded,
    TurnUsage,
    project,
    redact,
    redacted,
)
from qma.harness.relay import GrantRefused
from qma.harness.tools import (
    SERVER,
    Grants,
    ToolSurfaceError,
    VetCache,
    build_server,
    domain_write_policy,
    gate_rules,
    keyring_refs,
    tool_defs,
    unvetted_tools,
    vet_mcp_servers,
)

if TYPE_CHECKING:
    from claude_agent_sdk import McpServerConfig
    from claude_agent_sdk.types import (
        McpStatusResponse,
        PermissionResultAllow,
        ToolPermissionContext,
    )
    from qmx_broker.service import BrokerService
    from qmx_control.service import ControlService
    from qmx_tools.service import DomainContext

    from qma.harness.money import GateRules
    from qma.harness.procs import AgentProcessCap
    from qma.harness.relay import Relay, RelayGrant

FLOOR_REASON: Final = "approvals are not wired yet"
PLUGIN: Final = "qmx"
CLOSE_WAIT_S: Final = 10.0


@dataclass(frozen=True)
class OperatorText:
    """Text the operator typed in the console or UI. Only the HTTP turn route makes one."""

    text: str


type Prompt = OperatorText


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
    vetted: VetCache = field(default_factory=VetCache)
    """External MCP tool lists already vetted, by config digest, for this harness."""
    test: TestMode | None = None
    """Live checks only; None is every layer on."""

    @property
    def redaction(self) -> bool:
        return self.test is None or self.test.redaction


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

    @property
    def session_id(self) -> SessionId:
        return self.record.session_id

    async def send(self, prompt: Prompt) -> None:
        """Connect if Cold, write the `user` block and turn "running", then `client.query`.
        While a turn runs, the SDK queues the message, like typing into Claude Code."""
        async with self._lock:
            live = self._live or await self._connect()
            self._live = live
            await self._note("user", {"text": prompt.text})
            self._write(turn="running")
            await live.client.query(prompt.text)

    async def interrupt(self) -> None:
        """Background Bash and sub-agents keep running, as in Claude Code."""
        if self._live is not None:
            await self._live.client.interrupt()

    async def live(self) -> AsyncIterator[Delta]:
        """Live deltas for this chat and its native sub-agents. Dropped on disconnect."""
        queue: asyncio.Queue[Delta] = asyncio.Queue()
        self._stream.listeners.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._stream.listeners.discard(queue)

    async def close(self) -> None:
        """Disconnect, stop this chat's launcher tree and revoke its relay grant. Idempotent."""
        async with self._lock:
            live, self._live = self._live, None
            if live is None:
                return
            self._closing = True
            try:
                await self._end(live)
            finally:
                self._closing = False

    async def _end(self, live: _Live) -> None:
        if live.grant is not None:
            await self._deps.relay.revoke(live.grant)
        with contextlib.suppress(Exception):
            await asyncio.wait_for(live.client.disconnect(), CLOSE_WAIT_S)
        if live.reader is not None and live.reader is not asyncio.current_task():
            live.reader.cancel()
            with contextlib.suppress(Exception, asyncio.CancelledError):
                await live.reader
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
            servers, gate, vetted = await self._tools(launch)
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
            unvetted = unvetted_tools(status, vetted)
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
        self, launch: Launch
    ) -> tuple[dict[str, McpServerConfig], GateRules, Mapping[str, frozenset[str]]]:
        """The `qmx` server, the vetted external servers, the gate's rules and each vetted
        server's tool names. A refused external server gets a `needs_you` block and is left
        out; the chat still starts."""
        deps = self._deps
        control = deps.control
        defs = await tool_defs(control=control, broker=deps.broker, domain=deps.domain)
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
        )
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
                if isinstance(message, SystemMessage) and message.subtype == "init":
                    found = unexpected_plugins(message.data)
                    if found:
                        await self._note("needs_you", {"reason": _loaded(found)})
                        self._write(turn="idle")
                        return
                    self._write(turn="running")
                for fact in project(message, redact_tokens=self._deps.redaction):
                    await self._route(fact)
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
        self, fact: Block | Delta | StreamEnded | TurnUsage | Limits | TurnEnded | Compacted
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
            case Compacted(trigger=trigger):
                await self._note("changed", {"kind": "compacted", "trigger": trigger})
            case TurnUsage() | Limits():
                pass

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
        await self._note(
            "permission",
            {"tool": tool_name, "input": tool_input, "state": "rejected", "reason": FLOOR_REASON},
        )
        return PermissionResultDeny(message=FLOOR_REASON)
