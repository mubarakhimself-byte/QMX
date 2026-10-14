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
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from qmx_control.models import ControlError
from qmx_control.service import SessionBlock, SessionInput
from qmx_ledger.journal import RunJournal

from qma.harness.chat import Chat, ChatDeps, Prompt
from qma.harness.home import (
    ChatRecord,
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
)
from qma.harness.procs import AgentProcessCap
from qma.harness.profiles import PLAN, ProfileError, Profiles, parse_profiles, resolve_model
from qma.harness.relay import Relay, RelayUsage, UsageSink, keyring_secret

if TYPE_CHECKING:
    from qmx_control.service import ControlService

    from qma.harness.project import Delta

UNKNOWN_OUTCOME = "the last turn ended with an unknown outcome; send a message to continue"


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


class Harness:
    def __init__(self, deps: ChatDeps) -> None:
        self._deps = deps
        self._chats: dict[SessionId, Chat] = {}

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
        4. A record left "running" gets a `needs_you` block and turns "idle"; running this
           twice changes nothing.
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
            if record.turn == "running":
                control.sessions_append(
                    record.session_id,
                    SessionBlock(type="needs_you", content={"reason": UNKNOWN_OUTCOME}),
                )
                write_record(home, replace(record, turn="idle"))
        loopback = test is not None and test.loopback_http_provider

        def profiles() -> Profiles:
            return parse_profiles(control.settings_get("providers"), allow_loopback_http=loopback)

        async def alert(chat: SessionId, reason: str) -> None:
            block = SessionBlock(type="needs_you", content={"reason": reason})
            await asyncio.to_thread(control.sessions_append, chat, block)

        relay = await Relay(
            secrets=keyring_secret,
            usage=journal_usage(home),
            alert=alert,
            profiles=profiles,
            test=test,
        ).start()
        deps = ChatDeps(
            home=home, control=control, procs=procs, launcher=LAUNCHER, relay=relay, test=test
        )
        return cls(deps)

    async def start_chat(self, spec: NewChat) -> SessionId:
        """A qmx-control session, then a chat record with `started=False`. No process yet."""
        home, control = self._deps.home, self._deps.control
        workspace = spec.workspace
        if workspace is not None and not workspace.is_dir():
            raise LaunchRefused(f"the workspace {workspace} is not a folder")
        try:
            profile = self._deps.relay.profiles().get(spec.profile)
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
        """Hand a prompt to the chat. Returns once it is sent; results stream as blocks."""
        await self._chat(chat).send(prompt)

    async def interrupt(self, chat: SessionId) -> None:
        await self._chat(chat).interrupt()

    def live(self, chat: SessionId) -> AsyncIterator[Delta]:
        return self._chat(chat).live()

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


def journal_usage(home: QmxHome) -> UsageSink:
    """One `model_call` event per upstream request in `<home>/runs/<session>/journal.jsonl`,
    the run journal `RunIndex` reads. One writer at a time, because a journal holds an
    exclusive lock file while it is open."""
    lock = asyncio.Lock()

    def append(usage: RelayUsage) -> None:
        path = home.root / "runs" / usage.session_id / "journal.jsonl"
        with RunJournal(path, usage.session_id) as journal:
            journal.append(
                "model_call",
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

    async def sink(usage: RelayUsage) -> None:
        async with lock:
            await asyncio.to_thread(append, usage)

    return sink
