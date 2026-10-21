"""The harness: the only object callers hold.

Process model. The QMA host process holds the harness and the relay. Each live chat is one CLI
subprocess that the SDK starts through `qma.launcher`, which has put itself under the OS limits
first. A key-provider chat's CLI reaches its provider only through the relay on loopback.
`open` kills any tree a crash left behind before anything resumes. No chat CLI starts at open;
chats connect on their first `send`.

At most `live_chat_slots` CLIs run, a number derived from the machine's RAM. This slot table is
the only counter of chat slots (AD-58); `slot_table` reads it. Background and Child chats leave
`interactive_reserve` slots for Interactive ones. A send to a Cold chat at capacity closes the
least recently used idle chat. With none idle, a Background or Child send waits for a slot, in
priority order, and an Interactive one refuses with `ChatTableFull`. A reaper closes
chats idle past `idle_reap_seconds`. A chat mid-turn or with a background task running is never
idle, and a closed chat resumes its session on the next send.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import functools
import itertools
import json
import logging
import os
import shutil
import webbrowser
from collections import Counter
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

from qmx_broker.service import BrokerService
from qmx_control.context import AttachedRef
from qmx_control.models import ControlError
from qmx_control.service import SessionBlock, SessionInput
from qmx_ledger.journal import RunJournal
from qmx_router.gpt import siwc
from qmx_router.gpt.probe import (
    ProbeFailed,
    ProbePassed,
    ProbeRun,
    run_probe,
    stored_result,
    translator_version,
)
from qmx_router.profiles import (
    GPT,
    PLAN,
    TIERS,
    ClaudePlan,
    GptPlan,
    KeyProvider,
    Profile,
    ProfileError,
    ProfileName,
    Profiles,
    gpt_refusal,
    parse_profiles,
    resolve_model,
)
from qmx_router.readings import ReadingView, UsageLedger, UsagePage, usage_page
from qmx_router.relay import (
    MESSAGES,
    GrantRefused,
    Relay,
    RelayGrant,
    RelayUsage,
    keyring_secret,
)
from qmx_tools.service import DomainContext

from qma.harness.chat import (
    Answer,
    AnswerStatus,
    AskId,
    Chat,
    ChatDeps,
    InjectedText,
    OperatorText,
    Policy,
    Prompt,
    Quote,
    RewindPoint,
    UntrustedPrompt,
    admits,
    export_chat,
    rewind_points,
    transcript,
)
from qma.harness.delegate import (
    ChildSpec,
    CliSpawn,
    DelegateRefused,
    Helpers,
    ParentBundle,
    Start,
    report_text,
)
from qma.harness.home import (
    ChatRecord,
    DoctorLine,
    QmxHome,
    SessionId,
    check_hooks,
    check_rules,
    check_secrets,
    ensure_homes,
    list_records,
    read_record,
    record_path,
    session_id,
    write_record,
)
from qma.harness.launch import (
    LAUNCHER,
    Background,
    Budgets,
    ChatConfig,
    ChatHooks,
    ChatKind,
    ChatPermissions,
    Child,
    ConfigChange,
    Effort,
    Home,
    HookSink,
    Interactive,
    JsonMap,
    LaunchRefused,
    PermissionMode,
    RelayedLaunch,
    SubAgent,
    TestMode,
    assert_scrubbed,
    background_slots,
    chat_options_refusal,
    launch_env,
    live_chat_slots,
    machine_ram_mb,
    parse_budgets,
    unattended,
)
from qma.harness.procs import AgentProcessCap
from qma.harness.surface import Surface, declaration
from qma.harness.tools import HostRead
from qma.harness.turns import TurnHandle
from qma.harness.usage import journal_path, token_sums, usage_lines

if TYPE_CHECKING:
    from qmx_control.models import Document
    from qmx_control.service import ControlService

    from qma.harness.project import Delta, PlanFact

UNKNOWN_OUTCOME = "the last turn ended with an unknown outcome; send a message to continue"
METER_WAIT_S = 60.0
METER_MODEL = "haiku"
METER_PROMPT = "Reply with the single word OK."
METER_COOLDOWN_S = 300.0
"""Claude's default. After a meter turn that brought no reading, no other runs this long, so a
turn with no rate-limit event does not cost a haiku turn on every later call (L-16)."""
REAP_TICK_S = 60.0

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewChat:
    """Every option of a chat. All but `hooks` are written on the chat record at birth, so a
    chat reloaded after a host restart launches as it started. Sinks and policies are named
    here and resolved on the harness at each launch, never stored as callables."""

    title: str
    model: str = "opus"
    effort: Effort | None = None
    mode: PermissionMode = "default"
    workspace: Path | None = None
    """None means a fresh folder under `<qmx_home>/workspaces/`."""
    profile: str = PLAN
    kind: ChatKind = field(default_factory=Interactive)
    """Background and Child chats are verbatim and bounded (`launch.verbatim`)."""
    compact_at: float | None = None
    """Background and Child only: auto-compact at this share of the context window. None
    keeps the CLI's default."""
    hooks: ChatHooks | None = None
    """Background and Child only: observe-only callbacks after the guard, held in this
    process only. A program that must keep its hooks across a restart names a `hook_sink`."""
    home: Home | None = None
    """None is `general`, or the parent's home for a Child."""
    packs: tuple[str, ...] = ()
    toolsets: tuple[str, ...] | None = None
    """QMX toolsets the chat declares; None is its home's preset, or its parent's for a Child.
    The Surface cuts them to what the host serves (AD-62)."""
    tools: tuple[str, ...] | None = None
    """Built-in tools the chat declares; None is the `claude_code` preset less what its kind
    loses; `()` with no declared toolsets is no tool at all."""
    skills: tuple[str, ...] | None = None
    """The skills filter the chat declares; None is every skill it loads."""
    agents: Mapping[str, SubAgent] = field(default_factory=dict[str, SubAgent])
    mcp_servers: Mapping[str, JsonMap] = field(default_factory=dict[str, JsonMap])
    append_system_prompt: str | None = None
    hook_sink: str | None = None
    permissions: ChatPermissions = field(default_factory=ChatPermissions)
    policy_args: JsonMap = field(default_factory=dict[str, Any])
    claude_hooks: JsonMap = field(default_factory=dict[str, Any])

    def config(self, profile: ProfileName, workspace: Path, home: Home) -> ChatConfig:
        return ChatConfig(
            profile=profile,
            model=self.model,
            effort=self.effort,
            mode=self.mode,
            workspace=workspace,
            kind=self.kind,
            compact_at=self.compact_at,
            hooks=self.hooks,
            tools=self.tools,
            home=home,
            packs=self.packs,
            toolsets=self.toolsets,
            skills=self.skills,
            agents=MappingProxyType(dict(self.agents)),
            mcp_servers=MappingProxyType(dict(self.mcp_servers)),
            append_system_prompt=self.append_system_prompt,
            hook_sink=self.hook_sink,
            permissions=self.permissions,
            policy_args=MappingProxyType(dict(self.policy_args)),
            claude_hooks=MappingProxyType(dict(self.claude_hooks)),
        )

    def __post_init__(self) -> None:
        refusal = chat_options_refusal(self.config(ProfileName(PLAN), Path(), Home()))
        if refusal is not None:
            raise LaunchRefused(refusal)
        try:
            check_hooks(self.claude_hooks)
            check_rules(self.permissions.allow, "permissions.allow")
            check_rules(self.permissions.deny, "permissions.deny")
            check_secrets(self.mcp_servers, self.policy_args, self.claude_hooks)
            json.dumps([dict(self.mcp_servers), dict(self.policy_args)])
        except (LaunchRefused, TypeError, ValueError) as error:
            raise LaunchRefused(f"a chat option cannot be stored: {error}") from None


class UnknownChat(ControlError):
    """No chat record has this session id. The control app answers it with a 404."""

    def __init__(self, chat: str) -> None:
        super().__init__("not_found", f"No chat has the session id {chat}.", 404)


class ChatTableFull(RuntimeError):
    """Every slot holds a busy chat, so an Interactive chat cannot connect. The operator gets
    this at once, with a `needs_you` block naming the busy chats, rather than a silent wait."""

    def __init__(self, cap: int, busy: tuple[SessionId, ...]) -> None:
        self.busy = busy
        super().__init__(
            f"all {cap} live chats are busy ({', '.join(busy)}); interrupt or close one"
        )


@dataclass(frozen=True)
class SlotTable:
    """`Harness.slot_table()`: chat slots are machine capacity, never usage (AD-58)."""

    capacity: int
    """`live_chat_slots`, derived from RAM."""
    reserve: int
    """Slots Background and Child chats leave for Interactive ones."""
    held: tuple[SessionId, ...]
    """Live chats and chats with a send in flight, less `delegate` children on a parent's slot."""
    unattended: tuple[SessionId, ...]
    """The Background and Child chats among `held`; at most `capacity - reserve` of them."""
    waiting: tuple[SessionId, ...]
    """Chats whose send waits for a slot, in the order they will get one."""


@dataclass
class PlanWatch:
    """Records each plan fact in the ledger. While the overage stop holds, every plan chat with
    a live CLI is ended with the rule named, whether or not a turn runs, so nothing queued in it
    reaches the model."""

    ledger: UsageLedger = field(default_factory=UsageLedger)
    chats: dict[SessionId, Chat] = field(default_factory=dict[SessionId, Chat])
    _stops: set[asyncio.Task[None]] = field(default_factory=set[asyncio.Task[None]])

    def __call__(self, fact: PlanFact) -> None:
        self.ledger.record(fact, self.ledger.clock())
        reason = self.ledger.hard_stop()
        if reason is None:
            return
        for chat in self.chats.values():
            if chat.on_plan and chat.is_live:
                task = asyncio.create_task(chat.stop_plan(reason))
                self._stops.add(task)
                task.add_done_callback(self._stops.discard)


class Harness:
    def __init__(
        self, deps: ChatDeps, watch: PlanWatch, host_reads: Mapping[str, HostRead] | None = None
    ) -> None:
        own = {"slot_table": self._slots_read, "journal": self._journal_read}
        self._deps = replace(
            deps, delegate=self._delegate, host=MappingProxyType({**(host_reads or {}), **own})
        )
        self._chats = watch.chats
        """The one table of chats, Cold and Live. Only the harness writes it."""
        self._ledger = watch.ledger
        self._metering = asyncio.Lock()
        self._admit = asyncio.Lock()
        self._sending: Counter[SessionId] = Counter()
        """Chats with a send in flight. Each holds a slot, live yet or not, and is never evicted."""
        self._waiting: dict[int, tuple[tuple[int, int], SessionId]] = {}
        """Each send waiting for a slot: its place, its serving order and its chat."""
        self._order = itertools.count()
        self._ram_mb = machine_ram_mb()
        self._hooks: dict[SessionId, ChatHooks] = {}
        """Each chat's `NewChat.hooks`, the one option the record cannot hold. Dropped when the
        chat ends through `close_chat`."""
        self._repack: set[SessionId] = set()
        """Live chats whose pack set changed: each is relaunched by resume before its next turn,
        so the new plugin list reaches the model with the context kept (H55)."""
        self._freed = asyncio.Event()
        """Set whenever a slot may have freed: a turn ended, a CLI ended or a send let go."""
        self._deps = replace(self._deps, on_free=self._freed.set)
        self._background: set[asyncio.Task[None]] = set()
        """Sends `run_turn` left running and closes `close_chat` shielded."""
        self._helpers = Helpers(self)
        """Every `delegate` helper this harness started, and the completions it owes a parent."""
        self._metered: float | None = None
        """When the last meter turn ran, on the loop clock."""
        self._reaper = asyncio.create_task(self._reap())

    @property
    def home(self) -> QmxHome:
        return self._deps.home

    def register_sink(self, name: str, sink: HookSink) -> None:
        """A hook sink chats name in `NewChat.hook_sink`. The host registers its sinks right
        after `open`, before any chat launches; a launch naming an unregistered sink is
        refused rather than run without its hooks."""
        self._deps.sinks[name] = sink

    def register_policy(self, name: str, policy: Policy) -> None:
        """A permission policy chats name in `NewChat.permissions.policy`, registered like a
        sink. It answers the chat's asks in-process."""
        self._deps.policies[name] = policy

    @property
    def control(self) -> ControlService:
        return self._deps.control

    @classmethod
    async def open(
        cls,
        home: QmxHome,
        *,
        control: ControlService,
        test: TestMode | None = None,
        host_reads: Mapping[str, HostRead] | None = None,
    ) -> Harness:
        """Convergent startup, safe to run after any crash. Assumes `qma.boot` already
        scrubbed this process. `test` is None except in check scripts.
        1. Refuse while the environment holds a banned name.
        2. Read the agent memory limit from settings.toml [budgets].
        3. Create the homes, then kill every CLI tree a crash left behind. A refused home
           does not stop `open`, so `/api/doctor` can name the reason; every launch re-checks.
        4. A record left "running" gets a `needs_you` block and turns "idle", and the lock
           file a crash left on its run journal goes; running this twice changes nothing.
        5. Start the relay on 127.0.0.1:0 with no grants.
        6. Open the relay's GPT lane only if a `ProbePassed` is stored for this translator
           version and a ChatGPT sign-in is stored.
        `host_reads` are reads the hosting process serves to `agent_tool` catalog rows by
        target, beside the harness's own."""
        assert_scrubbed(os.environ)
        limit = control.settings_get("budgets").get("agent_memory_mb")
        with contextlib.suppress(LaunchRefused):
            ensure_homes(home)
        procs = AgentProcessCap.for_platform(
            home.procs_dir, limit if isinstance(limit, int) else None
        )
        procs.kill_orphans()
        for record in list_records(home):
            Path(f"{journal_path(home, record.session_id)}.lock").unlink(missing_ok=True)
            if record.turn == "running":
                control.sessions_append(
                    record.session_id,
                    SessionBlock(type="needs_you", content={"reason": UNKNOWN_OUTCOME}),
                )
                write_record(home, replace(record, turn="idle"))
        loopback = test is not None and test.loopback_http_provider
        broker = BrokerService(
            home.root, brokers=functools.partial(control.settings_get, "brokers")
        )
        domain = DomainContext(root=home.root)
        domain.control, domain.library = control, control.library

        def profiles() -> Profiles:
            return parse_profiles(control.settings_get("providers"), allow_loopback_http=loopback)

        async def alert(chat: SessionId, reason: str) -> None:
            block = SessionBlock(type="needs_you", content={"reason": reason})
            await asyncio.to_thread(control.sessions_append, chat, block)

        try:
            relay = await Relay(
                secrets=keyring_secret,
                journal=functools.partial(UsageRows.open, home),
                alert=alert,
                profiles=profiles,
                probe_state=home.state_dir,
                test=test,
            ).start()
        except BaseException:
            procs.close()
            raise
        reason = await open_gpt_lane(relay, home)
        if reason:
            log.info("the GPT lane stays closed: %s", reason)
        watch = PlanWatch(UsageLedger(path=home.state_dir / "plan-usage.json"))
        deps = ChatDeps(
            home=home,
            control=control,
            procs=procs,
            launcher=LAUNCHER,
            relay=relay,
            broker=broker,
            domain=domain,
            on_plan_limits=watch,
            test=test,
        )
        return cls(deps, watch, host_reads)

    async def start_chat(self, spec: NewChat) -> SessionId:
        """A qmx-control session, then a chat record with `started=False` holding every
        option of `spec`. No process yet."""
        home, control = self._deps.home, self._deps.control
        workspace = spec.workspace
        if workspace is not None and not workspace.is_dir():
            raise LaunchRefused(f"the workspace {workspace} is not a folder")
        try:
            profile = (
                ClaudePlan()
                if spec.profile == PLAN
                else self._deps.relay.profiles().get(spec.profile)
            )
        except ProfileError as error:
            raise LaunchRefused(str(error)) from None
        if resolve_model(profile, spec.model) is None:
            raise LaunchRefused(f"{spec.profile} cannot run the model {spec.model!r}")
        await self._gpt_ready(profile)
        parent = spec.kind.parent if isinstance(spec.kind, Child) else None
        born = spec.home or (Home() if parent is None else self._chat(parent).record.config.home)
        created = control.sessions_create(
            SessionInput(title=spec.title, origin="qma", parent_id=parent)
        )
        chat = session_id(str(created["id"]))
        if workspace is None:
            workspace = home.workspaces_dir / chat
            workspace.mkdir(parents=True, exist_ok=True)
        config = spec.config(profile.name, workspace.resolve(), born)
        write_record(home, ChatRecord(chat, config, started=False, turn="idle"))
        if spec.hooks is not None:
            self._hooks[chat] = spec.hooks
        return chat

    async def set_packs(self, chat: SessionId, packs: tuple[str, ...]) -> None:
        """Store the chat's pack set on its record. A live chat's **tools** change at once, and
        its skills, agents, commands and pack-layer text join at the next turn, when the harness
        relaunches it by resuming the same session id with the new plugin list (H55): the CLI
        fixes plugins, skills and the prompt at connect and has no per-chat filter for a
        plugin's agents and commands. A Cold chat launches with the new set."""
        found = self._chat(chat)
        before = found.record.config.packs
        was_live = found.is_live
        await found.set_packs(tuple(packs))
        if was_live and before != tuple(packs):
            self._repack.add(chat)

    async def set_toolsets(self, chat: SessionId, toolsets: tuple[str, ...] | None) -> None:
        """Change which QMX toolsets the chat has (None is every core toolset). A live chat's
        tools change on its next model request, with no relaunch."""
        await self._chat(chat).set_toolsets(None if toolsets is None else tuple(toolsets))

    async def set_attached(self, chat: SessionId, refs: Sequence[AttachedRef]) -> None:
        """Store the chat's attached context references on its record (H49, AD-63), the one
        writer of that list. Through the chat when it is loaded, so a later write of the same
        record carries this list rather than the copy it held before; else straight to the
        file. A chat that does not exist raises `UnknownChat`."""
        entries = tuple(refs)
        found = self._chats.get(chat)
        if found is not None:
            found._write(attached=entries)  # pyright: ignore[reportPrivateUsage] - owns every chat
            return
        record = read_record(self._deps.home, chat)
        if record is None:
            raise UnknownChat(chat)
        write_record(self._deps.home, replace(record, attached=entries))

    def context_reads(self, chat: SessionId) -> Mapping[str, HostRead]:
        """The `context` toolset's reads for one chat, by catalog target. The process that holds
        the Library answers them by overriding this; a harness with no Library reads none, and a
        read with no target on the surface leaves its row off (`tools.tool_defs`)."""
        del chat
        return MappingProxyType({})

    async def _slots_read(self, _arguments: dict[str, Any]) -> Mapping[str, object]:
        return dataclasses.asdict(self.slot_table())

    async def _journal_read(self, arguments: dict[str, Any]) -> Mapping[str, object]:
        """One page of a chat's request journal, oldest first, with the offset of the next."""
        chat = session_id(str(arguments.get("session_id", "")))
        path = journal_path(self._deps.home, chat)
        if not path.is_file():
            raise KeyError(f"chat {chat} has no request journal")
        text = await asyncio.to_thread(path.read_text, encoding="utf-8")
        found = [json.loads(line) for line in text.splitlines() if line.strip()]
        offset, limit = int(arguments.get("offset", 0)), int(arguments.get("limit", 50))
        page = found[offset : offset + limit]
        end = offset + len(page)
        return {
            "rows": [
                {"seq": row["seq"], "time": row["time"], "event": row["event"], **row["payload"]}
                for row in page
            ],
            "next_offset": end if end < len(found) else None,
        }

    async def run_turn(self, chat: SessionId, prompt: Prompt, *, priority: int = 0) -> TurnHandle:
        """Send `prompt` and return the turn's handle. Returns once the prompt reached the CLI
        or waits for a slot (a `Queued` event says so). A refusal before either raises as
        `send` does; one after resolves the handle `failed` with its reason."""
        handle = TurnHandle(prompt.text)
        sent = asyncio.create_task(self._dispatch(chat, prompt, handle, priority))
        queued = asyncio.create_task(handle.queued.wait())
        try:
            await asyncio.wait({sent, queued}, return_when=asyncio.FIRST_COMPLETED)
        except BaseException:
            sent.cancel()
            raise
        finally:
            queued.cancel()
        if sent.done():
            sent.result()
            return handle

        def landed(task: asyncio.Task[None]) -> None:
            if task.cancelled():
                handle.finish(None)
            elif (error := task.exception()) is not None:
                handle.finish(None, str(error))

        sent.add_done_callback(landed)
        self._background.add(sent)
        sent.add_done_callback(self._background.discard)
        return handle

    async def send(self, chat: SessionId, prompt: Prompt, *, priority: int = 0) -> None:
        """Hand a prompt to the chat. Returns once it is sent; results stream as blocks.
        `priority` orders an unattended send among those waiting for a slot."""
        await self._dispatch(chat, prompt, None, priority)

    async def _dispatch(
        self, chat: SessionId, prompt: Prompt, handle: TurnHandle | None, priority: int
    ) -> None:
        """`send`, feeding the turn's handle when `run_turn` asked.
        `InjectedText` into an Interactive chat raises `UntrustedPrompt`. A plan chat refuses
        while the overage stop holds, with a `needs_you` block. An unattended plan chat refuses
        at a `background_cap` only when the operator wrote one. A Cold chat needs a slot first
        (`_take_slot`): an Interactive chat may take any slot, while a Background or Child chat
        leaves `interactive_reserve` of them free and waits in `priority` order."""
        found = self._chat(chat)
        kind = found.record.config.kind
        if not admits(kind, prompt):
            raise UntrustedPrompt(
                "injected text goes only to a Background or Child chat, which reads it verbatim"
            )
        prompt = await self._with_reports(chat, prompt)
        budgets = await self._budgets()
        if found.on_plan:
            stop = self._ledger.hard_stop()
            if stop is not None:
                await self._needs_you(chat, f"plan use is stopped: {stop}")
                raise LaunchRefused(f"plan use is stopped: {stop}")
            share, five_hour = budgets.background_cap, self._ledger.reading("five_hour")
            if share is not None and five_hour is not None and unattended(kind):
                used = five_hour.reading.utilization
                if used >= share:
                    raise LaunchRefused(
                        f"the five-hour window is {used:.0%} used, at or over your "
                        f"[budgets] background_cap of {share:.0%}"
                    )
        wait = not isinstance(kind, Interactive)
        await self._take_slot(chat, budgets, wait=wait, handle=handle, priority=priority)
        try:
            if chat in self._repack and found.record.turn != "running":
                self._repack.discard(chat)
                await found.close()
            await found.send(prompt, handle)
        finally:
            self._release(chat)

    def _release(self, chat: SessionId) -> None:
        self._sending[chat] -= 1
        if not self._sending[chat]:
            del self._sending[chat]
        self._freed.set()

    async def _with_reports(self, chat: SessionId, prompt: Prompt) -> Prompt:
        """The helper reports this chat has not been handed yet, in front of its next turn. They
        are claimed in the same write that carries them, so each is delivered once even across a
        restart (AD-41). The report's own header keeps it from reading as a slash command or an
        `@path` in a copilot chat."""
        rows = await self._helpers.pending(chat)
        if not rows:
            return prompt
        await self._helpers.claim(rows)
        return type(prompt)(f"{report_text(rows)}\n\n{prompt.text}")

    def _held(self) -> tuple[list[Chat], set[SessionId]]:
        """The live chats and the chats holding a slot. A `delegate` helper holds its own slot:
        its parent is not blocked on it, so nothing is lent (AD-41, AD-58)."""
        live = [found for found in self._chats.values() if found.is_live]
        return live, {found.session_id for found in live} | self._sending.keys()

    def _unattended(self, chats: set[SessionId]) -> set[SessionId]:
        return {
            sid
            for sid in chats
            if (found := self._chats.get(sid)) is not None
            and not isinstance(found.record.config.kind, Interactive)
        }

    def slot_table(self) -> SlotTable:
        """The one chat-slot reading (AD-58): what the table holds and who waits for it. The
        engine reads it to tell an attempt queued for a slot from one that stopped moving."""
        budgets = parse_budgets(self._deps.control.settings_get("budgets"))
        _, held = self._held()
        return SlotTable(
            capacity=live_chat_slots(budgets, self._ram_mb),
            reserve=budgets.interactive_reserve,
            held=tuple(sorted(held)),
            unattended=tuple(sorted(self._unattended(held))),
            waiting=tuple(chat for _, chat in sorted(self._waiting.values())),
        )

    async def _take_slot(
        self,
        chat: SessionId,
        budgets: Budgets,
        *,
        wait: bool,
        handle: TurnHandle | None = None,
        priority: int = 0,
    ) -> None:
        """Hold a slot for `chat` while a send to it runs, closing the least recently used
        idle chat when the table is full. A chat being sent to is never evicted. With no chat
        idle, `wait` waits until a slot frees; otherwise this raises `ChatTableFull`. A waiting
        (Background or Child) send also leaves `interactive_reserve` slots to Interactive chats:
        unattended chats hold at most `background_slots` between them. Waiting sends are served
        by `priority`, higher first, then by when they began to wait. A `delegate` helper holds
        its own slot, and host capacity queues it, so no parent waits on a child that waits on
        the parent's slot. Admission is one critical section, so two sends never both take the
        last slot. A waiting send wakes when a turn ends, a CLI ends or another send lets go;
        nothing polls."""
        cap = live_chat_slots(budgets, self._ram_mb)
        own = background_slots(budgets, self._ram_mb)
        place = next(self._order)
        if wait:
            self._waiting[place] = ((-priority, place), chat)
        try:
            while True:
                async with self._admit:
                    while True:
                        live, held = self._held()
                        if chat in held:
                            self._sending[chat] += 1
                            return
                        first = not wait or min(self._waiting.values())[0][1] == place
                        crowded = wait and len(self._unattended(held)) >= own
                        if first and not crowded and len(held) < cap:
                            self._sending[chat] += 1
                            return
                        idle = sorted(
                            (
                                found
                                for found in live
                                if found.idle_seconds > 0
                                and found.session_id not in self._sending
                                and (not crowded or self._unattended({found.session_id}))
                            ),
                            key=lambda found: found.idle_seconds,
                            reverse=True,
                        )
                        if not first or not idle:
                            self._freed.clear()
                            break
                        for found in idle:
                            if await found.close_if_idle(0):
                                break
                    if not wait:
                        busy = sorted(held)
                        full = ChatTableFull(cap, tuple(busy))
                        await self._needs_you(chat, str(full), busy=busy)
                        raise full
                if handle is not None:
                    handle.on_queued()
                await self._freed.wait()
        finally:
            if self._waiting.pop(place, None) is not None:
                self._freed.set()

    async def _delegate(self, parent: SessionId, op: str, arguments: str) -> str:
        """Backs the four `delegate` tools. `op` is the row's wire name and `arguments` is the
        tool call's JSON document; the answer is JSON text. Nothing here waits for a helper: the
        start returns its handle, and the answer arrives at the parent's next turn (AD-41)."""
        try:
            found: object = json.loads(arguments) if arguments.strip() else {}
        except ValueError:
            raise DelegateRefused("the delegate arguments are not JSON") from None
        if not isinstance(found, dict):
            raise DelegateRefused("the delegate arguments are one JSON object")
        given = cast("dict[str, Any]", found)
        match op:
            case "delegate_run":
                answer: object = await self._helpers.start(parent, Start.parse(given))
            case "delegate_list":
                answer = {
                    "helpers": await self._helpers.listing(parent, str(given.get("group") or ""))
                }
            case "delegate_steer":
                answer = await self._helpers.steer(
                    parent, str(given.get("handle") or ""), str(given.get("text") or "")
                )
            case "delegate_stop":
                answer = await self._helpers.stop(
                    parent, str(given.get("handle") or ""), str(given.get("reason") or "")
                )
            case _:
                raise DelegateRefused(f"{op!r} is not a delegate operation")
        return json.dumps(answer)

    @property
    def state_dir(self) -> Path:
        """Where this home keeps state that outlives a process, such as an allowed cli version."""
        return self._deps.home.state_dir

    def parent_bundle(self, parent: SessionId) -> ParentBundle:
        """What a helper copies from its parent: the chat's profile and model, where it works,
        the declaration it had at birth, its permission mode and whether it is unattended."""
        record = self._chat(parent).record
        config = record.config
        return ParentBundle(
            profile=str(config.profile),
            model=config.model,
            workspace=config.workspace,
            declared=declaration(config),
            mode=config.mode,
            unattended=unattended(config.kind),
        )

    async def provider_profiles(self) -> Profiles:
        return await asyncio.to_thread(self._deps.relay.profiles)

    async def start_helper(self, spec: ChildSpec) -> SessionId:
        """One helper chat, launched as its own Child chat. A refusal is the tool's answer, and
        nothing was spent."""
        bundle = self.parent_bundle(spec.parent)
        try:
            return await self.start_chat(
                NewChat(
                    title=spec.title,
                    model=spec.model,
                    effort=cast("Effort | None", spec.effort),
                    mode=bundle.mode,
                    workspace=spec.workspace,
                    profile=spec.profile,
                    kind=Child(spec.parent, unattended=bundle.unattended),
                    toolsets=spec.scope.toolsets,
                    tools=spec.scope.builtins,
                    skills=spec.scope.skills,
                )
            )
        except (ProfileError, LaunchRefused) as refused:
            raise DelegateRefused(f"the helper did not start: {refused}") from None

    async def helper_turn(self, child: SessionId, text: str) -> TurnHandle:
        """A helper's turn. Its prompt was written by a model, so it goes in as `InjectedText`
        and the child reads it verbatim."""
        try:
            return await self.run_turn(child, InjectedText(text))
        except (LaunchRefused, UntrustedPrompt) as refused:
            raise DelegateRefused(f"the helper did not start: {refused}") from None

    async def cli_spawn(self, spec: ChildSpec, child: SessionId) -> CliSpawn:
        """The command, environment and folder of one `cli` helper: an ordinary local process
        whose model calls reach the relay on a grant whose owner is the helper's handle,
        journalled with it (AD-28, AD-41). `[agents] cli_helper` names the binary and its
        arguments; the pinned Claude Code CLI is the default."""
        rows = await asyncio.to_thread(self._deps.control.settings_get, "agents")
        written = rows.get("cli_helper")
        if isinstance(written, list) and written and all(isinstance(part, str) for part in written):
            argv = tuple(cast("list[str]", written))
        else:
            argv = (str(LAUNCHER), "-p", "--output-format", "text")
        binary = Path(argv[0])
        try:
            info = await asyncio.to_thread(binary.stat)
        except OSError as error:
            raise DelegateRefused(f"the cli helper {binary} cannot be read: {error}") from None
        version = f"{binary.name} {info.st_size}-{int(info.st_mtime)}"
        try:
            grant = await self._deps.relay.grant(
                child, ProfileName(spec.profile), unattended=True, agent_id=spec.handle
            )
        except GrantRefused as refused:
            raise DelegateRefused(
                f"a cli helper on {spec.profile} needs a relay grant, and the relay refused it: "
                f"{refused}"
            ) from None
        env = launch_env(
            RelayedLaunch(grant),
            home=self._deps.home,
            session_id=child,
            cap=self._deps.procs.handle_name,
        )
        return CliSpawn(argv, env, spec.workspace, version)

    async def _reap(self) -> None:
        """Close every live chat idle longer than `idle_reap_seconds`, checked at a quarter of
        that period and at least once a minute. Closing is safe: the next send resumes the same
        session."""
        budgets = Budgets()
        while True:
            with contextlib.suppress(Exception):
                budgets = await self._budgets()
            await asyncio.sleep(min(REAP_TICK_S, budgets.idle_reap_seconds / 4))
            try:
                for chat in list(self._chats.values()):
                    if chat.idle_seconds > budgets.idle_reap_seconds:
                        await chat.close_if_idle(budgets.idle_reap_seconds)
            except Exception:
                log.exception("reaping idle chats failed; trying again next tick")

    async def _gpt_ready(self, profile: Profile) -> None:
        """A GPT chat starts or switches only with a stored `ProbePassed` for the translator as
        it is on disk now. Without one the lane closes, so no grant is minted either."""
        if not isinstance(profile, GptPlan):
            return
        relay, home = self._deps.relay, self._deps.home
        stored = await asyncio.to_thread(stored_result, home.state_dir, translator_version())
        if not isinstance(stored, ProbePassed):
            await relay.close_gpt_lane()
            raise LaunchRefused(
                "GPT needs a passed GPT probe for this translator version; type /login chatgpt"
            )
        if relay.gpt is None or relay.gpt.passed != stored:
            reason = await open_gpt_lane(relay, home)
            if reason:
                raise LaunchRefused(f"the GPT lane is closed: {reason}")

    async def gpt_login(
        self, *, sign_in: bool, open_page: Callable[[str], object] = webbrowser.open
    ) -> GptStatus:
        """`/login chatgpt`. Uses the stored sign-in when it still refreshes; opens OpenAI's page
        only when `sign_in` is set. Adds a `gpt` row from `/v1/models` if none exists, runs the
        GPT probe unless a pass is stored for this translator version, then opens the lane."""
        relay, home = self._deps.relay, self._deps.home
        lines: list[str] = []
        session = await chatgpt_session(relay)
        if session is not None:
            try:
                await session.access_token()
                lines.append("Signed in to ChatGPT for QMA (stored sign-in).")
                if session.store_error:
                    lines.append(f"Warning: {session.store_error}.")
            except siwc.SignInError as error:
                lines.append(f"The stored ChatGPT sign-in did not refresh: {error}")
                session = None
        if session is None:
            if not sign_in:
                return GptStatus(lane=False, consent=False, lines=tuple(lines), needs_sign_in=True)
            try:
                session = await siwc.sign_in(open_page=open_page)
            except siwc.SignInError as error:
                lines.append(f"ChatGPT sign-in failed: {error}")
                return GptStatus(lane=False, consent=False, lines=tuple(lines))
            lines.append("Signed in to ChatGPT for QMA.")
        relay.siwc = session
        profile = await self._gpt_profile(session, lines)
        if profile is None:
            return GptStatus(lane=False, consent=session.background_consent, lines=tuple(lines))
        stored = await asyncio.to_thread(stored_result, home.state_dir, translator_version())
        if isinstance(stored, ProbePassed):
            lines.append(
                f"The GPT probe passed for this translator at {stored.at:%Y-%m-%d %H:%M} UTC."
            )
        else:
            lines.append(f"Running the GPT probe on {profile.tiers.opus}...")
            result = await self.probe_gpt(session, profile, say=lines.append)
            if isinstance(result, ProbeFailed):
                lines.append(f"The GPT probe failed at {result.step}; GPT stays off.")
                return GptStatus(lane=False, consent=session.background_consent, lines=tuple(lines))
        reason = await open_gpt_lane(relay, home)
        lines.append(
            f"The GPT lane is closed: {reason}" if reason else "GPT is ready: /provider gpt."
        )
        return GptStatus(lane=not reason, consent=session.background_consent, lines=tuple(lines))

    async def _gpt_profile(self, session: siwc.SiwcSession, lines: list[str]) -> GptPlan | None:
        """The `gpt` row, written with every tier on the first GPT model `/v1/models` lists when
        the row is missing."""
        control = self._deps.control
        rows = dict(await asyncio.to_thread(control.settings_get, "providers"))
        if GPT not in rows:
            try:
                listed = await siwc.list_models(session)
            except siwc.SignInError as error:
                lines.append(f"Could not list the ChatGPT models: {error}")
                return None
            model = next((slug for slug in listed if gpt_refusal(slug) is None), None)
            if model is None:
                lines.append(f"ChatGPT lists no GPT model: {listed}")
                return None
            rows[GPT] = {"tiers": dict.fromkeys(TIERS, model)}
            await asyncio.to_thread(control.settings_put, "providers", rows)
            lines.append(f"Added the gpt provider row on {model}.")
        try:
            found = (await asyncio.to_thread(self._deps.relay.profiles)).get(GPT)
        except ProfileError as error:
            lines.append(str(error))
            return None
        return found if isinstance(found, GptPlan) else None

    async def probe_gpt(
        self,
        session: siwc.SiwcSession,
        profile: GptPlan,
        *,
        say: Callable[[str], None],
    ) -> ProbePassed | ProbeFailed:
        """Runs the GPT probe through a probe grant and stores its result."""
        home = self._deps.home
        door = ProbeDoor(self._deps.relay, home, session, profile)
        return await run_probe(
            session,
            door,
            model=profile.tiers.opus,
            state_dir=home.state_dir,
            workspace=home.workspaces_dir / "gpt-probe",
            say=say,
        )

    async def gpt_consent(self, consent: bool) -> GptStatus:
        """Store the operator's answer on background use of his ChatGPT plan. The open lane's
        own session is updated, so the next grant reads the new answer."""
        lane = self._deps.relay.gpt
        session = await chatgpt_session(self._deps.relay)
        if session is None:
            return GptStatus(lane=False, consent=False, lines=("No ChatGPT sign-in is stored.",))
        await session.set_background_consent(consent)
        state = "may" if consent else "may not"
        return GptStatus(
            lane=lane is not None,
            consent=consent,
            lines=(f"Background and helper chats {state} use your ChatGPT plan.",),
        )

    async def _budgets(self) -> Budgets:
        return parse_budgets(await asyncio.to_thread(self._deps.control.settings_get, "budgets"))

    async def _needs_you(self, chat: SessionId, reason: str, **extra: object) -> None:
        block = SessionBlock(
            type="needs_you", content=cast("Document", {"reason": reason, **extra})
        )
        await asyncio.to_thread(self._deps.control.sessions_append, chat, block)

    async def usage(self) -> UsagePage:
        tokens = await asyncio.to_thread(token_sums, self._deps.home.root / "runs")
        return usage_page(self._ledger, tokens)

    async def doctor(self) -> list[DoctorLine]:
        """The overage and extra-usage lines, the GPT lane, the relay's grant count and refusal
        counters, and the process cap report."""
        relay, cap = self._deps.relay, self._deps.procs.report()
        counts = relay.counters
        return [
            *usage_lines(self._ledger),
            await asyncio.to_thread(gpt_line, relay, self._deps.home),
            DoctorLine(
                "relay",
                True,
                f"{relay.grants} live grants; refused: bearer {counts.bearer}, egress "
                f"{counts.egress}, family {counts.family}, tier {counts.tier}; upstream errors "
                f"{counts.upstream}",
            ),
            DoctorLine(
                "agent process cap",
                cap.os_cap,
                f"OS cap {'on' if cap.os_cap else 'not available on this OS'}; limit "
                f"{cap.limit_mb or 'none'} MB; using {cap.used_mb} MB; live chats "
                f"{len(cap.chats)}; last killed {cap.last_killed or 'none'}",
            ),
        ]

    async def meter(self) -> ReadingView | None:
        """The live five-hour reading. With none in the ledger, one tool-less haiku Background
        turn writes it, because the turn's rate-limit event carries the reading and `/usage`
        no longer does (CLI 2.1.299). A turn that brought no reading runs no other for
        `METER_COOLDOWN_S`. The chat leaves the table, its record and its workspace before its
        process is awaited closed, so nothing lists it even when the close is cancelled; its
        control session stays as the audit row. While a plan window is used up or plan use is
        stopped, no turn runs and this raises `LaunchRefused`."""
        async with self._metering:
            held = self._ledger.reading("five_hour")
            if held is not None:
                return held
            stop = self._ledger.hard_stop() or (
                "a plan window is used up" if self._ledger.rejected() else None
            )
            if stop is not None:
                raise LaunchRefused(f"the plan meter will not run: {stop}")
            now = asyncio.get_running_loop().time()
            if self._metered is not None and now - self._metered < METER_COOLDOWN_S:
                return None
            self._metered = now
            sid = await self.start_chat(
                NewChat(title="Plan usage meter", model=METER_MODEL, kind=Background(), tools=())
            )
            chat = self._chat(sid)
            try:
                handle = await self.run_turn(sid, OperatorText(METER_PROMPT))
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(handle.result(), METER_WAIT_S)
            finally:
                del self._chats[sid]
                record_path(self._deps.home, sid).unlink(missing_ok=True)
                await asyncio.to_thread(
                    shutil.rmtree, self._deps.home.workspaces_dir / sid, ignore_errors=True
                )
                await asyncio.to_thread(
                    shutil.rmtree, self._deps.home.launch_dir(sid), ignore_errors=True
                )
                await chat.close()
            return self._ledger.reading("five_hour")

    async def quote(self, chat: SessionId, change: ConfigChange) -> Quote:
        """Every change goes through a quote. The new model goes through
        `profiles.resolve_model`, the parser the relay uses, so a change the relay would refuse
        never gets a quote. A switch onto the plan is refused while the overage stop holds."""
        found = self._chat(chat)
        old = found.record.config
        new = change.applied_to(old)
        try:
            profile = (
                ClaudePlan()
                if new.profile == PLAN
                else (await asyncio.to_thread(self._deps.relay.profiles)).get(new.profile)
            )
        except ProfileError as error:
            raise LaunchRefused(str(error)) from None
        if resolve_model(profile, new.model) is None:
            raise LaunchRefused(f"{new.profile} cannot run the model {new.model!r}")
        await self._gpt_ready(profile)
        stop = self._ledger.hard_stop()
        if new.profile == PLAN and old.profile != PLAN and stop is not None:
            raise LaunchRefused(f"plan use is stopped: {stop}")
        return await found.quote(new)

    async def apply(self, chat: SessionId, quote_id: str) -> Quote:
        """The quote stays server-side in its chat; a caller only names it, so it cannot forge
        one. An unknown or stale id raises `QuoteStale`. The chat keeps its slot through a
        relaunch, so no other chat takes it while the CLI restarts."""
        found = self._chat(chat)
        self._sending[chat] += 1
        try:
            return await found.apply(quote_id, plan_stop=self._ledger.hard_stop())
        finally:
            self._release(chat)

    async def interrupt(self, chat: SessionId) -> None:
        await self._chat(chat).interrupt()

    async def close_chat(self, chat: SessionId) -> None:
        """End the chat's CLI process and drop it from the table (H18). Nothing is deleted:
        the record, transcript and session stay, and the next send resumes the session. A turn
        still running ends with an unknown outcome. The close runs in a task of its own, so a
        caller cancelled meanwhile (the SDK cancels an interrupted tool call that way) still
        leaves no process behind."""
        found = self._chats.pop(chat, None)
        self._hooks.pop(chat, None)
        self._repack.discard(chat)
        if found is not None:
            closing = asyncio.ensure_future(found.close())
            self._background.add(closing)
            closing.add_done_callback(self._background.discard)
            await asyncio.shield(closing)

    async def rewind_points(self, chat: SessionId) -> list[RewindPoint]:
        self._chat(chat)
        return await asyncio.to_thread(rewind_points, transcript(self._deps.home, chat))

    async def rewind(self, chat: SessionId, message_id: str) -> None:
        """The SDK's file rewind to before one of `rewind_points`. A Cold chat takes a slot
        and connects first, as a send does. Raises `RewindRefused` mid-turn or for an id with
        no checkpoint."""
        found = self._chat(chat)
        await self._take_slot(chat, await self._budgets(), wait=False)
        try:
            await found.rewind(message_id)
        finally:
            self._release(chat)

    async def export(self, chat: SessionId) -> Path:
        """`export_chat` into `<home>/exports/`, with every provider key value redacted. The
        values are read by reference here and never leave this process."""
        found = self._chat(chat)
        relay = self._deps.relay

        def key_values() -> dict[str, str]:
            values: dict[str, str] = {}
            for profile in relay.profiles().by_name.values():
                if isinstance(profile, KeyProvider):
                    with contextlib.suppress(Exception):
                        values[profile.credential] = relay.secrets(profile.credential)
            return values

        secrets = await asyncio.to_thread(key_values)
        return await asyncio.to_thread(
            export_chat, self._deps.home, self._deps.control, found.record, secrets
        )

    def live(self, chat: SessionId) -> AsyncIterator[Delta]:
        return self._chat(chat).live()

    def answer(self, ask: AskId, answer: Answer) -> AnswerStatus:
        """Routes by `ask.session_id`. Call it on the harness's event loop only: it resolves an
        asyncio future and records a grant. A chat with no live object in this process lost
        its asks when its process ended, so they are `expired`."""
        chat = self._chats.get(ask.session_id)
        if chat is not None:
            return chat.answer(ask.n, answer)
        return "unknown" if read_record(self._deps.home, ask.session_id) is None else "expired"

    async def close(self) -> None:
        """Close every helper, then every chat, then the relay, then release the process cap so
        the home can be opened again. Idempotent."""
        self._reaper.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._reaper
        await self._helpers.shutdown()
        for chat in list(self._chats.values()):
            await chat.close()
        for task in list(self._background):
            task.cancel()
        await asyncio.gather(*self._background, return_exceptions=True)
        await self._deps.relay.close()
        self._deps.procs.close()

    def surface_digest(self, chat: SessionId) -> str | None:
        """The surface digest of the chat's latest launch (AD-62); None before it launched."""
        found = self._chats.get(chat)
        record = found.record if found is not None else read_record(self._deps.home, chat)
        return record.digests[-1] if record is not None and record.digests else None

    def surface(self, chat: SessionId) -> Surface | None:
        """What the chat's latest launch gave the model: its toolsets, tools, skills, plugins and
        the pack views it loaded (AD-62, AD-55). None before the first launch."""
        found = self._chats.get(chat)
        return None if found is None else found.surface

    def _chat(self, chat: SessionId) -> Chat:
        found = self._chats.get(chat)
        if found is None:
            record = read_record(self._deps.home, chat)
            if record is None:
                raise UnknownChat(chat)
            hooks = self._hooks.get(chat)
            if hooks is not None:
                record = replace(record, config=replace(record.config, hooks=hooks))
            reads = {**self._deps.host, **self.context_reads(chat)}
            found = self._chats[chat] = Chat(record, replace(self._deps, host=reads))
        return found


@dataclass(frozen=True)
class GptStatus:
    """What `/login chatgpt` and the consent answer report to the console."""

    lane: bool
    consent: bool
    lines: tuple[str, ...]
    needs_sign_in: bool = False


@dataclass
class ProbeDoor:
    """`qma.gpt.probe`'s door into the relay: a probe grant per run, as a relayed launch env."""

    relay: Relay
    home: QmxHome
    session: siwc.SiwcSession
    profile: GptPlan
    grants: dict[str, RelayGrant] = field(default_factory=dict[str, RelayGrant])

    async def open(self, run: ProbeRun) -> Mapping[str, str]:
        grant = await self.relay.probe_grant(run, self.session, self.profile)
        self.grants[run.run_id] = grant
        env = launch_env(RelayedLaunch(grant), home=self.home, session_id=grant.session_id, cap="")
        return {name: value for name, value in env.items() if not name.startswith("QMA_")}

    async def close(self, run: ProbeRun) -> None:
        grant = self.grants.pop(run.run_id, None)
        if grant is not None:
            await self.relay.revoke(grant)


async def chatgpt_session(relay: Relay) -> siwc.SiwcSession | None:
    """The relay's sign-in, loaded from the keyring the first time."""
    if relay.siwc is None:
        relay.siwc = await asyncio.to_thread(siwc.load)
    return relay.siwc


async def open_gpt_lane(relay: Relay, home: QmxHome) -> str:
    """Open the relay's GPT lane from what is stored, or close it. Returns why it is closed,
    or "" when open. Reads the keyring only when a pass is stored."""
    stored = await asyncio.to_thread(stored_result, home.state_dir, translator_version())
    if not isinstance(stored, ProbePassed):
        await relay.close_gpt_lane()
        return "no GPT probe has passed for this translator version"
    try:
        session = await chatgpt_session(relay)
    except Exception as error:
        await relay.close_gpt_lane()
        return f"the ChatGPT sign-in could not be read: {type(error).__name__}"
    if session is None:
        await relay.close_gpt_lane()
        return "no ChatGPT sign-in is stored"
    await relay.open_gpt_lane(stored, session)
    return ""


def gpt_line(relay: Relay, home: QmxHome) -> DoctorLine:
    lane = relay.gpt
    if lane is not None:
        session = lane.route.session
        consent = "yes" if session.background_consent else "no"
        stored = f"; {session.store_error}" if session.store_error else ""
        return DoctorLine(
            "gpt lane",
            session.store_error is None,
            f"open on {lane.passed.model}; probe passed {lane.passed.at:%Y-%m-%d %H:%M} UTC for "
            f"translator {lane.passed.translator_version}; background consent {consent}{stored}",
        )
    version = translator_version()
    match stored_result(home.state_dir, version):
        case ProbeFailed(step=step, detail=detail):
            why = f"the GPT probe failed at {step}: {detail}"
        case ProbePassed():
            why = "no ChatGPT sign-in is stored"
        case None:
            why = f"no GPT probe has passed for translator {version}; type /login chatgpt"
    return DoctorLine("gpt lane", False, f"closed: {why}")


@dataclass(frozen=True)
class UsageRows:
    """A relayed chat's usage in its run journal. A `/v1/messages` request is a `model_call`
    row and a count_tokens request a `token_count` row, so a count never reads as a model
    call. The journal's lock file stays held until `close`."""

    journal: RunJournal

    @classmethod
    def open(cls, home: QmxHome, session: SessionId) -> UsageRows:
        return cls(RunJournal(journal_path(home, session), session))

    def append(self, usage: RelayUsage) -> None:
        self.journal.append(
            "model_call" if usage.path == MESSAGES else "token_count",
            {
                "agent": "primary",
                "model": usage.model,
                "profile": usage.profile,
                "path": usage.path,
                "status": usage.status,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "cache_read_tokens": usage.cache_read_tokens,
                "cache_write_tokens": usage.cache_write_tokens,
            },
        )

    def close(self) -> None:
        self.journal.close()
