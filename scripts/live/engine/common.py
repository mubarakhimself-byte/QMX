"""Shared setup for the engine's live checks: the PASS/FAIL log, the lane lock, throwaway homes,
and the harness opened in-process on a QMX home.

Run a check from `qmx-agents/` with the agents venv, for example
`uv run --no-sync python ../scripts/live/engine/ep2_lanes.py`. A check that runs a plan turn opens
the ship home only inside `plan_harness`, which holds `D:/QMX-worktrees/.engine-lane-lock`,
because `Harness.open` kills every CLI tree it finds for its home. No check reads the plan login
or a provider key; the harness and its relay read them in-process, as in production.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import time
from collections.abc import AsyncIterator, Callable, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

ENGINE_STORE: Final = Path("D:/QMX-worktrees/qma-ship/engine")
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
SHIP_HOME: Final = Path("D:/QMX-worktrees/qma-ship/home")
LIVE_QMA: Final = Path(__file__).resolve().parents[1] / "qma"
LOCK_WAIT_S: Final = 3600.0
LOCK_POLL_S: Final = 20.0
TURN_TIMEOUT_S: Final = 240.0

type Say = Callable[[str], None]


class Log:
    """Writes `<engine store>/evidence/<pr>/<ENGINE_LOG_PREFIX><slug>.log`. The builder's own
    runs set the prefix `owner-`; a checker's runs leave it empty."""

    def __init__(self, pr: str, slug: str) -> None:
        folder = ENGINE_STORE / "evidence" / pr
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True

    def __call__(self, line: str) -> None:
        stamped = f"{time.strftime('%H:%M:%S')} {line}"
        print(stamped.encode("ascii", "backslashreplace").decode(), flush=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(stamped + "\n")

    def check(self, name: str, ok: bool, seen: object) -> None:
        self(f"{'PASS' if ok else 'FAIL'} {name}: {seen}")
        self.passed &= ok

    def verdict(self) -> int:
        self("PASS" if self.passed else "FAIL")
        return 0 if self.passed else 1


@contextmanager
def lane_lock(say: Say) -> Iterator[None]:
    """Hold the lane lock, waiting while another lane holds it."""
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        try:
            LANE_LOCK.mkdir()
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise SystemExit("BLOCKED: the lane lock stayed held for an hour") from None
            say(f"lane lock held by another lane; retry in {LOCK_POLL_S:.0f} s")
            time.sleep(LOCK_POLL_S)
    say("lane lock taken")
    try:
        yield
    finally:
        LANE_LOCK.rmdir()
        say("lane lock released")


def throwaway_home(pr: str, slug: str) -> Path:
    """A fresh folder `homes/<pr>-<slug>` for a check that needs no model."""
    root = ENGINE_STORE / "homes" / f"{pr}-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


class _LiveQma:
    """`scripts/live/qma/common.py`, loaded on first use under another name because this module
    is `common` too. Lazy, so checks that open no harness need neither it nor its SDK import."""

    module: Any = None

    def __getattr__(self, name: str) -> Any:
        if _LiveQma.module is None:
            spec = importlib.util.spec_from_file_location("qma_live_common", LIVE_QMA / "common.py")
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load {LIVE_QMA / 'common.py'}")
            _LiveQma.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_LiveQma.module)
        return getattr(_LiveQma.module, name)


live: Any = _LiveQma()


def boot() -> None:
    """Scrub this process as `qma.serve` does, and point HOME and TMP at throwaway folders so a
    CLI started here never reads the operator's own profile."""
    live.boot()
    live.use_fake_home()


@dataclass
class Opened:
    harness: Any
    home: Any
    control: Any

    async def background(
        self, title: str, ws: Path, *, model: str, profile: str = "claude", **options: Any
    ) -> str:
        from qma.harness import Background, NewChat  # noqa: PLC0415

        new = NewChat(
            title=title, model=model, workspace=ws, profile=profile, kind=Background(), **options
        )
        return str(await self.harness.start_chat(new))

    async def inject(self, chat: str, text: str) -> None:
        from qma.harness import InjectedText  # noqa: PLC0415

        await self.harness.send(chat, InjectedText(text))

    async def wait_idle(self, chat: str, seconds: float = TURN_TIMEOUT_S) -> Any:
        return await live.wait_turn(self.home, chat, seconds)

    def blocks(self, chat: str, after: int = 0) -> list[dict[str, Any]]:
        return list(live.session_blocks(self.control, chat, after))


@asynccontextmanager
async def opened(root: Path, *, test: Any = None) -> AsyncIterator[Opened]:
    """The harness on the QMX home `root`, closed on exit. `routes.control_service` is the one
    harness submodule name used here: the public names have no way to build the ControlService
    the harness reads its settings through."""
    from qma.harness import Harness, QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    home = QmxHome(root)
    control = control_service(home)
    harness = await Harness.open(home, control=control, test=test)
    try:
        yield Opened(harness, home, control)
    finally:
        await harness.close()


@asynccontextmanager
async def plan_harness(say: Say) -> AsyncIterator[Opened]:
    """The harness on the ship home under the lane lock, with a five-hour reading in its ledger.
    Since HG2, `Harness.meter()` takes that reading itself with one haiku turn when none is held."""
    live.require_login(say)
    with lane_lock(say):
        async with opened(SHIP_HOME) as found:
            say(f"five-hour reading from Harness.meter(): {await found.harness.meter()}")
            yield found
