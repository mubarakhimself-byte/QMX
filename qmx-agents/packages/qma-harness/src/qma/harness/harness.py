"""The harness: the only object callers hold.

Process model. The QMA host process holds the harness and the relay. Each live chat is one CLI
subprocess that the SDK starts through `qma.launcher`, which has put itself under the OS limits
first. A key-provider chat's CLI reaches its provider only through the relay on loopback.
`open` kills any tree a crash left behind before anything resumes. No chat CLI starts at open;
chats connect on their first `send`.

At most `[budgets] max_live_chats` CLIs run. A send to a Cold chat at the cap closes the least
recently used idle chat, or refuses with `ChatTableFull`; nothing queues. A reaper closes chats
idle past `idle_reap_seconds`. A chat mid-turn or with a background task running is never idle,
and a closed chat resumes its session on the next send.
"""

from __future__ import annotations

import asyncio
import contextlib
import functools
import logging
import os
import shutil
import webbrowser
from collections import Counter
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

from qmx_broker.service import BrokerService
from qmx_control.models import ControlError
from qmx_control.service import SessionBlock, SessionInput
from qmx_ledger.journal import RunJournal
from qmx_tools.service import DomainContext

from qma.gpt import siwc
from qma.gpt.probe import (
    ProbeFailed,
    ProbePassed,
    ProbeRun,
    run_probe,
    stored_result,
    translator_version,
)
from qma.harness.chat import (
    Answer,
    AnswerStatus,
    AskId,
    Chat,
    ChatDeps,
    InjectedText,
    OperatorText,
    Prompt,
    Quote,
    RewindPoint,
    UntrustedPrompt,
    admits,
    export_chat,
    rewind_points,
    transcript,
)
from qma.harness.home import (
    DOCTOR_CHAT,
    ChatRecord,
    DoctorLine,
    QmxHome,
    SessionId,
    cli_version,
    ensure_homes,
    list_records,
    read_record,
    record_path,
    session_id,
    write_record,
)
from qma.harness.launch import (
    LAUNCHER,
    Budgets,
    ChatConfig,
    ChatHooks,
    ChatKind,
    Child,
    ConfigChange,
    Effort,
    Interactive,
    LaunchRefused,
    PermissionMode,
    PlanLaunch,
    RelayedLaunch,
    TestMode,
    assert_scrubbed,
    chat_options_refusal,
    launch_env,
    parse_budgets,
    unattended,
)
from qma.harness.money import (
    NON_BROKER_REFS,
    ExposureReport,
    exposure_targets,
    keyring_inventory,
    load_exposure,
    load_scope_proofs,
    money_posture,
    run_exposure_probe,
    save_exposure,
    store_names,
    unproven,
)
from qma.harness.procs import AgentProcessCap
from qma.harness.profiles import (
    GPT,
    PLAN,
    TIERS,
    ClaudePlan,
    GptPlan,
    KeyProvider,
    Profile,
    ProfileError,
    Profiles,
    gpt_refusal,
    parse_profiles,
    resolve_model,
)
from qma.harness.project import redact
from qma.harness.relay import MESSAGES, Relay, RelayGrant, RelayUsage, keyring_secret
from qma.harness.tools import DelegateRefused, keyring_refs, secret_files
from qma.harness.usage import (
    BackgroundCap,
    PostureView,
    ReadingView,
    UsageLedger,
    UsagePage,
    journal_path,
    token_sums,
    usage_lines,
    usage_page,
)

if TYPE_CHECKING:
    from qmx_control.models import Document
    from qmx_control.service import ControlService

    from qma.harness.project import Delta, PlanFact

UNKNOWN_OUTCOME = "the last turn ended with an unknown outcome; send a message to continue"
METER_WAIT_S = 60.0
METER_MODEL = "haiku"
METER_PROMPT = "Reply with the single word OK."
REAP_TICK_S = 60.0

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewChat:
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
    """Background and Child only: observe-only callbacks after the money gate."""

    def __post_init__(self) -> None:
        refusal = chat_options_refusal(self.kind, self.compact_at, self.hooks)
        if refusal is not None:
            raise LaunchRefused(refusal)


class UnknownChat(ControlError):
    """No chat record has this session id. The control app answers it with a 404."""

    def __init__(self, chat: str) -> None:
        super().__init__("not_found", f"No chat has the session id {chat}.", 404)


class ChatTableFull(RuntimeError):
    """`max_live_chats` CLIs are live and none is idle, so no chat can connect. Nothing is
    queued: the caller gets this at once and the chat shows a `needs_you` block naming the busy
    chats. The operator closes or interrupts one, or raises the cap."""

    def __init__(self, cap: int, busy: tuple[SessionId, ...]) -> None:
        self.busy = busy
        super().__init__(
            f"all {cap} live chats are busy ({', '.join(busy)}); interrupt or close one, "
            "or raise [budgets] max_live_chats"
        )


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
    def __init__(self, deps: ChatDeps, watch: PlanWatch) -> None:
        self._deps = replace(deps, delegate=self._delegate)
        self._chats = watch.chats
        """The one table of chats, Cold and Live. Only the harness writes it."""
        self._ledger = watch.ledger
        self._metering = asyncio.Lock()
        self._admit = asyncio.Lock()
        self._sending: Counter[SessionId] = Counter()
        """Chats with a send in flight. Each holds a slot, live yet or not, and is never evicted."""
        self._options: dict[SessionId, tuple[float | None, ChatHooks | None]] = {}
        """Each chat's `compact_at` and `hooks` from `NewChat`, which its record does not hold."""
        self._reaper = asyncio.create_task(self._reap())
        self.control_port: int | None = None
        """The qmx-control port, set by the server, so the exposure probe can try it."""

    @property
    def home(self) -> QmxHome:
        return self._deps.home

    @property
    def control(self) -> ControlService:
        return self._deps.control

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
        5. Start the relay on 127.0.0.1:0 with no grants.
        6. Open the relay's GPT lane only if a `ProbePassed` is stored for this translator
           version and a ChatGPT sign-in is stored."""
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
        return cls(deps, watch)

    async def start_chat(self, spec: NewChat) -> SessionId:
        """A qmx-control session, then a chat record with `started=False`. No process yet.
        `compact_at` and `hooks` stay in this harness, because the record on disk does not hold
        them, and join the chat's config when the chat is first used."""
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
        created = control.sessions_create(
            SessionInput(title=spec.title, origin="qma", parent_id=parent)
        )
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
            kind=spec.kind,
            compact_at=spec.compact_at,
            hooks=spec.hooks,
        )
        write_record(home, ChatRecord(chat, config, started=False, turn="idle"))
        if spec.compact_at is not None or spec.hooks is not None:
            self._options[chat] = (spec.compact_at, spec.hooks)
        return chat

    async def send(self, chat: SessionId, prompt: Prompt) -> None:
        """Hand a prompt to the chat. Returns once it is sent; results stream as blocks.
        `InjectedText` into an Interactive chat raises `UntrustedPrompt`. A plan chat refuses
        while the overage stop holds, and an unattended plan chat refuses at the background
        cap; each refusal also shows the chat a `needs_you` block. A Cold chat needs a slot
        first: at `max_live_chats` the least recently used idle chat closes, and with none idle
        the send raises `ChatTableFull`."""
        found = self._chat(chat)
        kind = found.record.config.kind
        if not admits(kind, prompt):
            raise UntrustedPrompt(
                "injected text goes only to a Background or Child chat, which reads it verbatim"
            )
        budgets = await self._budgets()
        if found.on_plan:
            stop = self._ledger.hard_stop()
            if stop is not None:
                await self._needs_you(chat, f"plan use is stopped: {stop}")
                raise LaunchRefused(f"plan use is stopped: {stop}")
            refusal = (
                BackgroundCap(budgets.background_cap).refusal(self._ledger)
                if unattended(kind)
                else None
            )
            if refusal is not None:
                reason = f"the background cap holds this chat: {refusal}"
                await self._needs_you(chat, reason)
                raise LaunchRefused(reason)
        await self._take_slot(chat, budgets.max_live_chats)
        try:
            await found.send(prompt)
        finally:
            self._release(chat)

    def _release(self, chat: SessionId) -> None:
        self._sending[chat] -= 1
        if not self._sending[chat]:
            del self._sending[chat]

    async def _take_slot(self, chat: SessionId, cap: int) -> None:
        """Hold a slot for `chat` while a send to it runs, closing the least recently used
        idle chat when the table is full. A chat being sent to is never evicted. Admission is
        one critical section, so two sends never both take the last slot."""
        async with self._admit:
            while True:
                live = [found for found in self._chats.values() if found.is_live]
                held = {found.session_id for found in live} | self._sending.keys()
                if chat in held or len(held) < cap:
                    self._sending[chat] += 1
                    return
                idle = sorted(
                    (
                        found
                        for found in live
                        if found.idle_seconds > 0 and found.session_id not in self._sending
                    ),
                    key=lambda found: found.idle_seconds,
                    reverse=True,
                )
                if not idle:
                    full = ChatTableFull(cap, tuple(sorted(held)))
                    await self._needs_you(chat, str(full), busy=sorted(held))
                    raise full
                for found in idle:
                    if await found.close_if_idle(0):
                        break

    async def _delegate(self, parent: SessionId, profile: str, prompt: str) -> str:
        """Backs `mcp__qmx__delegate`. Refuses a profile outside `Profiles.delegate_targets`.
        Starts a Child chat (a qmx-control child session with `parent_id`, verbatim, `unattended`
        copied from the parent, its own relay grant, the [budgets] turn and spend limits) on the
        parent's model tier, workspace and mode. Sends the prompt as `InjectedText`, because a
        model wrote it, and returns the turn's final text. A full table, the overage stop or
        the background cap refuses at once through `send`; nothing waits on a slot that only the
        parent could free. The child closes, and its grant is revoked, however this ends."""
        profiles = await asyncio.to_thread(self._deps.relay.profiles)
        refusal = profiles.delegate_refusal(profile)
        if refusal is not None:
            raise DelegateRefused(refusal)
        origin = self._chat(parent).record.config
        try:
            target = profiles.get(profile)
            child = await self.start_chat(
                NewChat(
                    title=f"Helper on {profile}",
                    model=origin.model if resolve_model(target, origin.model) else "opus",
                    mode=origin.mode,
                    workspace=origin.workspace,
                    profile=profile,
                    kind=Child(parent, unattended=unattended(origin.kind)),
                )
            )
        except (ProfileError, LaunchRefused) as refused:
            raise DelegateRefused(f"the helper did not start: {refused}") from None
        found = self._chat(child)
        end = found.next_end()
        try:
            await self.send(child, InjectedText(prompt))
            ended = await end
        except (LaunchRefused, ChatTableFull) as refused:
            raise DelegateRefused(f"the helper did not start: {refused}") from None
        finally:
            end.cancel()
            await found.close()
        if ended is None:
            raise DelegateRefused("the helper's process ended before it answered")
        text = ended.result or ""
        if self._deps.redaction:
            text = redact(text)
        if not ended.ok:
            raise DelegateRefused(f"the helper's turn failed: {text or ended.terminal_reason}")
        return text

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
        budgets = await self._budgets()
        tokens = await asyncio.to_thread(token_sums, self._deps.home.root / "runs")
        money = await asyncio.to_thread(posture_view, self._deps.home, self._deps.control)
        return usage_page(self._ledger, BackgroundCap(budgets.background_cap), tokens, money)

    async def doctor(self, *, probe: bool = False) -> list[DoctorLine]:
        """The overage and extra-usage lines, the money posture and the stored exposure report,
        the relay's grant count and refusal counters, and the process cap report. `probe=True`
        (the operator asked) runs a fresh exposure probe first; a plain read never does."""
        if probe:
            await self.probe_exposure()
        money = await asyncio.to_thread(posture_view, self._deps.home, self._deps.control)
        relay, cap = self._deps.relay, self._deps.procs.report()
        counts = relay.counters
        return [
            *usage_lines(self._ledger),
            *money.lines(),
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

    async def probe_exposure(self) -> ExposureReport:
        """Runs the exposure probe with the plan launch environment and stores its report."""
        home, control = self._deps.home, self._deps.control
        inventory = (await asyncio.to_thread(broker_inventory, control))[0]
        targets = exposure_targets(
            home.root, inventory, self.control_port, secret_files(home), Path.home() / ".claude"
        )
        env = {
            **os.environ,
            **launch_env(PlanLaunch(), home=home, session_id=DOCTOR_CHAT, cap=""),
        }
        version = await asyncio.to_thread(cli_version)
        report = await run_exposure_probe(env, targets, cli_version=version or "unknown")
        await asyncio.to_thread(save_exposure, home.state_dir, report)
        return report

    async def meter(self) -> ReadingView | None:
        """The live five-hour reading. With none in the ledger, one haiku plan turn with no
        tools writes it, because the turn's rate-limit event carries the reading and `/usage`
        no longer does (CLI 2.1.299). Its chat record and workspace are removed after the turn,
        so the chat list does not keep it. While a plan window is used up or plan use is stopped, no turn runs and
        this raises `LaunchRefused`."""
        async with self._metering:
            held = self._ledger.reading("five_hour")
            if held is not None:
                return held
            stop = self._ledger.hard_stop() or (
                "a plan window is used up" if self._ledger.rejected() else None
            )
            if stop is not None:
                raise LaunchRefused(f"the plan meter will not run: {stop}")
            sid = await self.start_chat(NewChat(title="Plan usage meter", model=METER_MODEL))
            chat = self._chat(sid)
            chat.record = replace(chat.record, config=replace(chat.record.config, tools=False))
            try:
                await self.send(sid, OperatorText(METER_PROMPT))
                loop = asyncio.get_running_loop()
                deadline = loop.time() + METER_WAIT_S
                while chat.record.turn == "running" and loop.time() < deadline:
                    await asyncio.sleep(0.2)
            finally:
                await chat.close()
                del self._chats[sid]
                record_path(self._deps.home, sid).unlink(missing_ok=True)
                await asyncio.to_thread(
                    shutil.rmtree, self._deps.home.workspaces_dir / sid, ignore_errors=True
                )
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

    async def rewind_points(self, chat: SessionId) -> list[RewindPoint]:
        self._chat(chat)
        return await asyncio.to_thread(rewind_points, transcript(self._deps.home, chat))

    async def rewind(self, chat: SessionId, message_id: str) -> None:
        """The SDK's file rewind to before one of `rewind_points`. A Cold chat takes a slot
        and connects first, as a send does. Raises `RewindRefused` mid-turn or for an id with
        no checkpoint."""
        found = self._chat(chat)
        await self._take_slot(chat, (await self._budgets()).max_live_chats)
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
        """Close every chat, then the relay, then release the process cap so the home can be
        opened again. Idempotent."""
        self._reaper.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._reaper
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
            if chat in self._options:
                compact_at, hooks = self._options[chat]
                config = replace(record.config, compact_at=compact_at, hooks=hooks)
                record = replace(record, config=config)
            found = self._chats[chat] = Chat(record, self._deps)
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


def broker_inventory(control: ControlService) -> tuple[frozenset[str], frozenset[str]]:
    """The keyring inventory, by name, and the entries known not to be broker credentials:
    the fixed ones and every provider row's `credential_ref`."""
    profiles = parse_profiles(control.settings_get("providers"))
    keys = {
        str(profile.credential).casefold()
        for profile in profiles.by_name.values()
        if isinstance(profile, KeyProvider)
    }
    return keyring_inventory(keyring_refs(control), store_names()), NON_BROKER_REFS | keys


def posture_view(home: QmxHome, control: ControlService) -> PostureView:
    """Reads names, the stored S27 proofs and the stored exposure report; runs no probe."""
    inventory, non_broker = broker_inventory(control)
    proofs = load_scope_proofs(home.state_dir)
    return PostureView(
        posture=money_posture(inventory, non_broker, proofs),
        unproven=unproven(inventory, non_broker, proofs),
        exposure=load_exposure(home.state_dir),
    )


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
