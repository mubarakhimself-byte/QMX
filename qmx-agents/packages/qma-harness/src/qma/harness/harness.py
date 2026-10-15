"""The harness: the only object callers hold.

Process model. The QMA host process holds the harness and the relay. Each live chat is one CLI
subprocess that the SDK starts through `qma.launcher`, which has put itself under the OS limits
first. A key-provider chat's CLI reaches its provider only through the relay on loopback.
`open` kills any tree a crash left behind before anything resumes. No chat CLI starts at open;
chats connect on their first `send`.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING

from qmx_broker.service import BrokerService
from qmx_control.models import ControlError
from qmx_control.service import SessionBlock, SessionInput
from qmx_ledger.journal import RunJournal
from qmx_tools.service import DomainContext

from qma.harness.chat import Answer, AnswerStatus, AskId, Chat, ChatDeps, OperatorText, Prompt
from qma.harness.home import (
    ChatRecord,
    DoctorLine,
    QmxHome,
    SessionId,
    ensure_homes,
    list_records,
    read_record,
    session_id,
    write_record,
)
from qma.harness.launch import (
    LAUNCHER,
    ChatConfig,
    Effort,
    Interactive,
    LaunchRefused,
    PermissionMode,
    TestMode,
    assert_scrubbed,
    unattended,
)
from qma.harness.procs import AgentProcessCap
from qma.harness.profiles import (
    PLAN,
    ClaudePlan,
    ProfileError,
    Profiles,
    parse_profiles,
    resolve_model,
)
from qma.harness.relay import MESSAGES, Relay, RelayUsage, keyring_secret
from qma.harness.usage import (
    ReadingView,
    UsageLedger,
    UsagePage,
    background_cap,
    journal_path,
    token_sums,
    usage_lines,
    usage_page,
)

if TYPE_CHECKING:
    from qmx_control.service import ControlService

    from qma.harness.project import Delta, PlanFact

UNKNOWN_OUTCOME = "the last turn ended with an unknown outcome; send a message to continue"
METER_WAIT_S = 60.0


@dataclass(frozen=True)
class NewChat:
    title: str
    model: str = "opus"
    effort: Effort | None = None
    mode: PermissionMode = "default"
    workspace: Path | None = None
    """None means a fresh folder under `<qmx_home>/workspaces/`."""
    profile: str = PLAN


class UnknownChat(ControlError):
    """No chat record has this session id. The control app answers it with a 404."""

    def __init__(self, chat: str) -> None:
        super().__init__("not_found", f"No chat has the session id {chat}.", 404)


@dataclass
class PlanWatch:
    """Records each plan fact in the ledger. While the overage stop holds, every running plan
    chat is interrupted with the rule named."""

    ledger: UsageLedger = field(default_factory=UsageLedger)
    chats: dict[SessionId, Chat] = field(default_factory=dict[SessionId, Chat])
    _stops: set[asyncio.Task[None]] = field(default_factory=set[asyncio.Task[None]])

    def __call__(self, fact: PlanFact) -> None:
        self.ledger.record(fact, self.ledger.clock())
        reason = self.ledger.hard_stop()
        if reason is None:
            return
        for chat in self.chats.values():
            if chat.on_plan and chat.record.turn == "running":
                task = asyncio.create_task(chat.stop_plan(reason))
                self._stops.add(task)
                task.add_done_callback(self._stops.discard)


class Harness:
    def __init__(self, deps: ChatDeps, watch: PlanWatch) -> None:
        self._deps = deps
        self._chats = watch.chats
        self._ledger = watch.ledger
        self._meter: SessionId | None = None

    @classmethod
    async def open(
        cls, home: QmxHome, *, control: ControlService, test: TestMode | None = None
    ) -> Harness:
        """Convergent startup, safe to run after any crash. Assumes `qma.boot` already
        scrubbed this process. `test` is None except in check scripts.
        1. Refuse while the environment holds a banned name.
        2. Read the agent memory limit from settings.toml [budgets].
        3. Create the homes, then kill every CLI tree a crash left behind. A refused home
           does not stop `open`, so `/api/doctor` can name the reason; every launch re-checks.
        4. A record left "running" gets a `needs_you` block and turns "idle", and the lock
           file a crash left on its run journal goes; running this twice changes nothing.
        5. Start the relay on 127.0.0.1:0 with no grants."""
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
        broker = BrokerService(home.root)
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
                test=test,
            ).start()
        except BaseException:
            procs.close()
            raise
        watch = PlanWatch()
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
        return cls(deps, watch)

    async def start_chat(self, spec: NewChat) -> SessionId:
        """A qmx-control session, then a chat record with `started=False`. No process yet."""
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
        created = control.sessions_create(SessionInput(title=spec.title, origin="qma"))
        chat = session_id(str(created["id"]))
        if workspace is None:
            workspace = home.workspaces_dir / chat
            workspace.mkdir(parents=True, exist_ok=True)
        config = ChatConfig(
            profile=profile.name,
            model=spec.model,
            effort=spec.effort,
            mode=spec.mode,
            workspace=workspace.resolve(),
            kind=Interactive(),
        )
        write_record(home, ChatRecord(chat, config, started=False, turn="idle"))
        return chat

    async def send(self, chat: SessionId, prompt: Prompt) -> None:
        """Hand a prompt to the chat. Returns once it is sent; results stream as blocks. A plan
        chat refuses while the overage stop holds, and an unattended plan chat refuses at the
        background cap."""
        found = self._chat(chat)
        if found.on_plan:
            stop = self._ledger.hard_stop()
            if stop is not None:
                raise LaunchRefused(f"plan use is stopped: {stop}")
            if unattended(found.record.config.kind):
                budgets = await asyncio.to_thread(self._deps.control.settings_get, "budgets")
                cap = background_cap(budgets)
                if not cap.allows(self._ledger):
                    raise LaunchRefused(
                        f"the plan is at the background cap ({cap.fraction:.0%} of the five-hour "
                        "window, or a window is used up)"
                    )
        await found.send(prompt)

    async def usage(self) -> UsagePage:
        budgets = await asyncio.to_thread(self._deps.control.settings_get, "budgets")
        tokens = await asyncio.to_thread(token_sums, self._deps.home.root / "runs")
        return usage_page(self._ledger, background_cap(budgets), tokens)

    def usage_lines(self) -> list[DoctorLine]:
        return usage_lines(self._ledger)

    async def meter(self) -> ReadingView | None:
        """Read `/usage` in a plan chat kept for it, then close that chat. The reply costs no
        model call, and its five-hour reading lands in the ledger."""
        if self._meter is None:
            self._meter = await self.start_chat(NewChat(title="Plan usage meter", model="haiku"))
        chat = self._chat(self._meter)
        await self.send(self._meter, OperatorText("/usage"))
        loop = asyncio.get_running_loop()
        deadline = loop.time() + METER_WAIT_S
        while chat.record.turn == "running" and loop.time() < deadline:
            await asyncio.sleep(0.2)
        await chat.close()
        return self._ledger.reading("five_hour")

    async def interrupt(self, chat: SessionId) -> None:
        await self._chat(chat).interrupt()

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
        """Close every chat, then the relay, then release the process cap so the home can be
        opened again. Idempotent."""
        for chat in list(self._chats.values()):
            await chat.close()
        await self._deps.relay.close()
        self._deps.procs.close()

    def _chat(self, chat: SessionId) -> Chat:
        found = self._chats.get(chat)
        if found is None:
            record = read_record(self._deps.home, chat)
            if record is None:
                raise UnknownChat(chat)
            found = self._chats[chat] = Chat(record, self._deps)
        return found


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
