"""Shared setup for the EP0 probes: the harness opened in-process on a QMX home, the lane lock,
the evidence log, and a reader for a chat's `model_call` rows.

Run each probe from `qmx-agents/` with the agents venv, for example
`uv run --no-sync python ../scripts/probes/engine/p_turn_end.py`. A probe that runs a plan turn
opens the ship home only while it holds `D:/QMX-worktrees/.engine-lane-lock`, because
`Harness.open` kills every CLI tree it finds for its home. No probe reads the plan login or a
provider key; the harness and its relay read them in-process, as in production.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import sys
import time
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

ENGINE_STORE: Final = Path("D:/QMX-worktrees/qma-ship/engine")
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
LOCK_WAIT_S: Final = 3600.0
LOCK_POLL_S: Final = 20.0
TRIAGE_PLAN_MODEL: Final = "haiku"
"""Appendix H: `triage` lists kimi/k3 then claude/haiku; haiku is its first plan-profile row."""
TURN_TIMEOUT_S: Final = 240.0

os.environ.setdefault("QMA_EVIDENCE_DIR", str(ENGINE_STORE / "evidence" / "ep0"))
os.environ.setdefault("QMA_LIVE_SCRATCH", str(ENGINE_STORE / "homes" / "ep0-scratch"))

LIVE_DIR: Final = Path(__file__).resolve().parents[2] / "live" / "qma"
sys.path.append(str(LIVE_DIR))
SHIP_HOME: Final = Path("D:/QMX-worktrees/qma-ship/home")


class _Live:
    """`scripts/live/qma/common.py`, loaded on first use under another name, because this
    module is `common` too. Lazy, so the journal reader's tests run without the agents venv."""

    module: Any = None

    def __getattr__(self, name: str) -> Any:
        if _Live.module is None:
            spec = importlib.util.spec_from_file_location("qma_live_common", LIVE_DIR / "common.py")
            if spec is None or spec.loader is None:
                raise ImportError(f"cannot load {LIVE_DIR / 'common.py'}")
            _Live.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_Live.module)
        return getattr(_Live.module, name)


live: Any = _Live()

# `switch_lane` and `money_lane` import `common`, which in this folder names this module, so
# their two rows are restated here.
KIMI_MODEL: Final = "moonshotai/kimi-k2.5"
OPENROUTER_ROW: Final[dict[str, Any]] = {
    "base_url": "https://openrouter.ai/api",
    "credential_ref": "qmx/openrouter",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), KIMI_MODEL),
}


def fake_key_row(url: str, **env: str) -> dict[str, Any]:
    """`money_lane.direct_row` plus extra quirk env: the fake model with tool search off."""
    return live.fake_row(url) | {"quirks": {"env": {"ENABLE_TOOL_SEARCH": "false", **env}}}


def log(slug: str) -> Any:
    """`<evidence>/<EP0_LOG_PREFIX><slug>.log`; the owner's runs use the prefix `owner-`."""
    return live.Log(os.environ.get("EP0_LOG_PREFIX", "") + slug)


@dataclass(frozen=True)
class ModelCall:
    """One `model_call` row of a chat's run journal. Plan chats write one per turn; relayed
    chats one per `/v1/messages` request."""

    seq: int
    profile: str
    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


def model_calls(journal: Path) -> list[ModelCall]:
    """Every `model_call` row in `journal`, oldest first. A line that is not a whole JSON row,
    such as one a crash cut short, is skipped."""
    if not journal.exists():
        return []
    found: list[ModelCall] = []
    for line in journal.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            if row.get("event") != "model_call":
                continue
            payload = row["payload"]
            found.append(
                ModelCall(
                    seq=int(row["seq"]),
                    profile=str(payload.get("profile", "")),
                    model=str(payload.get("model", "")),
                    input_tokens=int(payload.get("input_tokens", 0)),
                    output_tokens=int(payload.get("output_tokens", 0)),
                    cache_read_tokens=int(payload.get("cache_read_tokens", 0)),
                    cache_write_tokens=int(payload.get("cache_write_tokens", 0)),
                )
            )
        except (ValueError, KeyError, TypeError, AttributeError):
            continue
    return found


def cache_read(calls: list[ModelCall]) -> int:
    return sum(call.cache_read_tokens for call in calls)


def journal_of(home: Any, chat: str) -> Path:
    return Path(home.root) / "runs" / chat / "journal.jsonl"


@contextmanager
def lane_lock(say: Any) -> Iterator[None]:
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


def boot() -> None:
    """Scrub this process as `qmx_host` does, and point HOME and TMP at throwaway folders so a
    CLI started here never reads the operator's own profile."""
    live.boot()
    live.use_fake_home()


def throwaway_home(slug: str) -> Path:
    root = ENGINE_STORE / "homes" / f"ep0-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def workspace(slug: str) -> Path:
    path = ENGINE_STORE / "homes" / f"ep0-{slug}-ws"
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


@dataclass
class Opened:
    harness: Any
    home: Any
    control: Any

    async def background(
        self, title: str, ws: Path, *, model: str, profile: str = "claude", mode: str = "default"
    ) -> str:
        from qma.harness import NewChat  # noqa: PLC0415
        from qma.harness.launch import Background  # noqa: PLC0415

        return str(
            await self.harness.start_chat(
                NewChat(
                    title=title,
                    model=model,
                    workspace=ws,
                    profile=profile,
                    mode=mode,  # type: ignore[arg-type]
                    kind=Background(),
                )
            )
        )

    async def inject(self, chat: str, text: str) -> None:
        from qma.harness import InjectedText  # noqa: PLC0415

        await self.harness.send(chat, InjectedText(text))

    def record(self, chat: str) -> Any:
        from qma.harness.home import read_record, session_id  # noqa: PLC0415

        return read_record(self.home, session_id(chat))

    def blocks(self, chat: str, after: int = 0) -> list[dict[str, Any]]:
        return list(live.session_blocks(self.control, chat, after))

    def mark(self, chat: str) -> int:
        return int(live.last_event(self.control, chat))

    async def wait_idle(self, chat: str, seconds: float = TURN_TIMEOUT_S) -> Any:
        return await live.wait_turn(self.home, chat, seconds)

    def journal(self, chat: str) -> list[ModelCall]:
        return model_calls(journal_of(self.home, chat))


@asynccontextmanager
async def opened(root: Path, *, test: Any = None) -> AsyncIterator[Opened]:
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
async def plan_harness(say: Any) -> AsyncIterator[Opened]:
    """The harness on the ship home under the lane lock, with a five-hour reading so the
    background cap can judge a Background send. `Harness.meter()` gives no five-hour reading on
    today's CLI (its `/usage` reply lists contributors only), so when the ledger holds none, one
    Interactive plan turn on haiku seeds it from that turn's rate-limit event."""
    from qma.harness import NewChat, OperatorText  # noqa: PLC0415

    live.require_login(say)
    with lane_lock(say):
        async with opened(SHIP_HOME) as found:
            reading = await found.harness.meter()
            say(f"five-hour reading from Harness.meter(): {reading}")
            if five_hour(await found.harness.usage()) is None:
                seed = str(
                    await found.harness.start_chat(
                        NewChat(
                            title="ep0 reading",
                            model=TRIAGE_PLAN_MODEL,
                            workspace=workspace("seed"),
                        )
                    )
                )
                await found.harness.send(seed, OperatorText("Reply with the single word OK."))
                await found.wait_idle(seed)
                say("seeded the reading with one Interactive plan turn")
            say(f"five-hour reading in the ledger: {five_hour(await found.harness.usage())}")
            yield found


def five_hour(page: Any) -> Any:
    return next((view for view in page.readings if view.reading.window == "five_hour"), None)


def text_of(blocks: list[dict[str, Any]]) -> list[str]:
    return [str(b["content"].get("text", "")) for b in blocks if b["type"] == "text"]


def result_stamps() -> list[tuple[str, float]]:
    """`(chat id, perf_counter)` for every `ResultMessage` any CLI started from now on yields:
    the moment the SDK hands the harness the turn's end, which the probes take as true end."""
    import qma.harness.chat as chat_module  # noqa: PLC0415
    from claude_agent_sdk import ResultMessage  # noqa: PLC0415

    stamps: list[tuple[str, float]] = []
    base = chat_module.ClaudeSDKClient

    class Stamped(base):  # type: ignore[misc, valid-type]
        async def receive_messages(self) -> Any:
            chat = str((self.options.env or {}).get("QMA_CHAT_ID", ""))
            async for message in super().receive_messages():
                if isinstance(message, ResultMessage):
                    stamps.append((chat, time.perf_counter()))
                yield message

    chat_module.ClaudeSDKClient = Stamped
    return stamps


def launched_options() -> list[Any]:
    """The `ClaudeAgentOptions` of every CLI started from now on."""
    import qma.harness.chat as chat_module  # noqa: PLC0415

    seen: list[Any] = []
    base = chat_module.ClaudeSDKClient

    class Tap(base):  # type: ignore[misc, valid-type]
        def __init__(self, options: Any, *args: Any, **kwargs: Any) -> None:
            super().__init__(options, *args, **kwargs)
            seen.append(options)

    chat_module.ClaudeSDKClient = Tap
    return seen


def run(main: Any) -> None:
    sys.exit(asyncio.run(main()))
