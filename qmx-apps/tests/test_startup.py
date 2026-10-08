from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from qmx_apps.errors import AppError
from qmx_apps.manifest import Definition
from qmx_apps.supervisor import Instance, Supervisor

EXAMPLE = Path(__file__).resolve().parents[2] / "examples/apps/exchange-status"


class GatedClient:
    def __init__(self, stage: str) -> None:
        self.stage = stage
        self.entered = threading.Event()
        self.release = asyncio.Event()
        self.closed = threading.Event()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.init_timeout: float | None = None

    def __call__(self, transport: object, *, init_timeout: float) -> GatedClient:
        self.init_timeout = init_timeout
        return self

    async def wait(self, stage: str) -> None:
        if stage == self.stage:
            self.entered.set()
            await self.release.wait()

    async def __aenter__(self) -> GatedClient:
        self.loop = asyncio.get_running_loop()
        await self.wait("connect")
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.closed.set()

    async def list_tools(self) -> list[Any]:
        await self.wait("tools")
        return []

    async def list_resources(self) -> list[Any]:
        await self.wait("resources")
        return []

    def unblock(self) -> None:
        assert self.loop is not None
        self.loop.call_soon_threadsafe(self.release.set)


@pytest.fixture
def startup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[tuple[Supervisor, Definition]]:
    owner = Supervisor(tmp_path)
    definition = Definition.load(EXAMPLE)

    def get_definition(app_id: str) -> Definition:
        return definition

    monkeypatch.setattr(owner, "_definition", get_definition)

    def heartbeat(instance: Instance) -> None:
        instance.heartbeat = time.monotonic()

    monkeypatch.setattr(owner, "_heartbeat", heartbeat)
    try:
        yield owner, definition
    finally:
        owner.close()


@pytest.mark.parametrize("stage", ["connect", "tools", "resources"])
def test_startup_budget_covers_connection_and_discovery(
    startup: tuple[Supervisor, Definition], monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    owner, definition = startup
    definition = replace(
        definition,
        manifest=definition.manifest.model_copy(update={"startup_timeout_seconds": 0.05}),
    )

    def get_definition(app_id: str) -> Definition:
        return definition

    monkeypatch.setattr(owner, "_definition", get_definition)
    client = GatedClient(stage)
    monkeypatch.setattr("qmx_apps.supervisor.Client", client)
    with ThreadPoolExecutor() as pool:
        starting = pool.submit(owner.start, "exchange-status")
        try:
            assert client.entered.wait(timeout=2)
            with pytest.raises(AppError) as error:
                starting.result(timeout=2)
            assert error.value.code == "start_failed"
            assert owner.status("exchange-status")["status"] == "tripped"
            assert owner.logs("exchange-status")[-1]["error_type"] == "TimeoutError"
            if stage != "connect":
                assert client.closed.is_set()
        finally:
            client.unblock()


def test_start_waits_for_readiness_and_releases_startup_deadline(
    startup: tuple[Supervisor, Definition], monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, definition = startup
    client = GatedClient("resources")
    deadlines: list[asyncio.Timeout] = []
    timeout = asyncio.timeout

    def capture_timeout(delay: float | None) -> asyncio.Timeout:
        deadline = timeout(delay)
        deadlines.append(deadline)
        return deadline

    monkeypatch.setattr("qmx_apps.supervisor.Client", client)
    monkeypatch.setattr(asyncio, "timeout", capture_timeout)
    with ThreadPoolExecutor() as pool:
        starting = pool.submit(owner.start, "exchange-status")
        try:
            assert client.entered.wait(timeout=2)
            assert not starting.done()
            client.unblock()
            assert starting.result(timeout=2)["status"] == "running"
            assert len(deadlines) == 1
            assert deadlines[0].when() is None
            assert client.init_timeout == 0
            assert definition.manifest.startup_timeout_seconds == 90
        finally:
            client.unblock()
            owner.stop("exchange-status")
    assert client.closed.is_set()
