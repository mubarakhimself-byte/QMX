"""Shared parts of the HP9 approval checks.

`Host` serves the qmx-control app with the harness routes on a free loopback port, in this
process and on the harness's event loop, behind a throwaway bearer that is never stored. Checks
that need `TestMode` or the fake model cannot use `qma.serve`, so they answer asks through this
host's `POST /api/approvals/{ask_id}` and read blocks from its `GET /api/events/sessions` stream.

`Answerer` watches one chat's blocks and answers each new ask through the route with whatever
its policy returns for that ask.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import secrets
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import httpx
import uvicorn
from common import SCRATCH, Log, Session, put_providers, session_blocks, throwaway_home, wait_turn
from fake_model import FakeModel, Turn
from money_lane import direct_row

ALLOW_ONCE: dict[str, Any] = {"decision": "allow_once"}
ALLOW_ALWAYS: dict[str, Any] = {"decision": "allow_always"}
PROMPT = "Run the scripted checks."


def reject(message: str = "") -> dict[str, Any]:
    return {"decision": "reject", "message": message}


Policy = Callable[[dict[str, Any]], list[dict[str, Any]]]
"""Given an ask block (`tool`, `input`, `always`, `seq`, `kind`), the answer bodies to post in
order; an empty list leaves the ask open."""


def always(*bodies: dict[str, Any]) -> Policy:
    return lambda _: list(bodies)


def in_order(*answers: list[dict[str, Any]]) -> Policy:
    """The n-th ask gets the n-th list of bodies; any later ask is rejected."""
    queue = list(answers)
    return lambda _: queue.pop(0) if queue else [reject()]


class Host:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.secret = secrets.token_urlsafe(32)
        self.server: uvicorn.Server | None = None
        self.task: asyncio.Task[None] | None = None
        self.client: httpx.AsyncClient | None = None
        self.port = 0

    async def __aenter__(self) -> Host:
        from qma.harness.routes import chat_router  # noqa: PLC0415
        from qmx_control.server import create_app  # noqa: PLC0415

        app = create_app(
            self.session.control, self.secret, extra_routers=[chat_router(self.session.harness)]
        )
        self.server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
        )
        self.task = asyncio.create_task(self.server.serve())
        while not self.server.started:
            await asyncio.sleep(0.02)
        self.port = self.server.servers[0].sockets[0].getsockname()[1]
        self.client = httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{self.port}",
            headers={"Authorization": f"Bearer {self.secret}"},
            timeout=30,
        )
        return self

    async def __aexit__(self, *_: object) -> None:
        if self.client is not None:
            await self.client.aclose()
        if self.server is not None:
            self.server.should_exit = True
        if self.task is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self.task, 10)

    @property
    def http(self) -> httpx.AsyncClient:
        if self.client is None:
            raise RuntimeError("the host is not serving")
        return self.client

    async def answer(self, ask_id: str, body: dict[str, Any]) -> str:
        reply = await self.http.post(f"/api/approvals/{ask_id}", json=body)
        return str(reply.json().get("status", f"http {reply.status_code}"))

    async def answer_without_credential(self, ask_id: str, body: dict[str, Any]) -> int:
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{self.port}") as bare:
            reply = await bare.post(f"/api/approvals/{ask_id}", json=body)
        return reply.status_code

    async def stream(
        self, chat: str, after: int = 0
    ) -> AsyncIterator[tuple[float, dict[str, Any]]]:
        """Each session event as it arrives on the SSE stream, with its `perf_counter` time."""
        params = {"subject": chat, "after": str(after)}
        async with self.http.stream(
            "GET", "/api/events/sessions", params=params, timeout=None
        ) as reply:
            async for line in reply.aiter_lines():
                if line.startswith("data:"):
                    yield time.perf_counter(), json.loads(line[5:])


@dataclass
class Answered:
    ask_id: str
    tool: str
    tool_input: dict[str, Any]
    body: dict[str, Any]
    status: str


@dataclass
class Answerer:
    host: Host
    chat: str
    policy: Policy
    log: Log | None = None
    answered: list[Answered] = field(default_factory=list[Answered])
    asks: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])
    task: asyncio.Task[None] | None = None

    def start(self) -> Answerer:
        self.task = asyncio.create_task(self._run())
        return self

    async def stop(self) -> None:
        if self.task is not None:
            self.task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.task

    async def _run(self) -> None:
        control = self.host.session.control
        seen: set[int] = set()
        while True:
            for block in await asyncio.to_thread(session_blocks, control, self.chat):
                content = block["content"]
                if content.get("state") != "asking" or block["seq"] in seen:
                    continue
                seen.add(block["seq"])
                ask = {**content, "seq": block["seq"], "kind": block["type"]}
                self.asks.append(ask)
                for body in self.policy(ask):
                    await self._post(ask, body)
            await asyncio.sleep(0.02)

    async def _post(self, ask: dict[str, Any], body: dict[str, Any]) -> None:
        ask_id = f"{self.chat}.{ask['seq']}"
        status = await self.host.answer(ask_id, body)
        self.answered.append(Answered(ask_id, ask["tool"], ask["input"], body, status))
        if self.log is not None:
            shown = json.dumps(ask["input"])[:120]
            self.log(f"  answered {ask_id} {ask['tool']} {shown} -> {body['decision']}: {status}")


def tools_asked(answerer: Answerer) -> list[str]:
    return [ask["tool"] for ask in answerer.asks]


async def fake_session(
    slug: str,
    script: list[Turn],
    *,
    tools: list[str],
    test: Any = None,
    mode: str = "default",
    workspace: Path | None = None,
    routes: dict[str, list[Turn]] | None = None,
) -> tuple[Path, FakeModel, Session]:
    """A harness on a throwaway QMX home and one key chat on the fake model. The caller closes
    the harness and stops the fake model."""
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home(slug)
    fake = FakeModel(script, routes=routes).start()
    put_providers(root, {"fake": direct_row(fake.url)})
    session = await Session.start(
        root,
        model="opus",
        workspace=workspace or SCRATCH / f"{slug}-workspace",
        title=slug,
        test=test or TestMode(loopback_http_provider=True),
        profile="fake",
        mode=mode,
        tools=tools,
    )
    return root, fake, session


async def new_chat(session: Session, title: str, workspace: Path, mode: str = "default") -> str:
    from qma.harness import NewChat  # noqa: PLC0415

    workspace.mkdir(parents=True, exist_ok=True)
    spec = NewChat(
        title=title, model="opus", workspace=workspace, profile="fake", mode=cast("Any", mode)
    )
    return await session.harness.start_chat(spec)


async def answered_turn(
    log: Log, host: Host, chat: str, policy: Policy, prompt: str = PROMPT
) -> Answerer:
    """One operator turn in `chat`, with its asks answered by `policy` through the route."""
    from qma.harness import OperatorText  # noqa: PLC0415

    session = host.session
    answerer = Answerer(host, chat, policy, log).start()
    try:
        await session.harness.send(chat, OperatorText(prompt))
        record = await wait_turn(session.home, chat)
        log(f"turn of {chat} ended: {record.turn}")
    finally:
        await answerer.stop()
    return answerer
