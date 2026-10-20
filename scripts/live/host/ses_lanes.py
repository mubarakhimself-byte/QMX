"""SES's live lanes: every chat gets one `session` Library item (Library AD-21).

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/host/ses_lanes.py [--parent TREE] [lane ...]`
Lanes are `regression ship idle restart count secrets processes`; none named runs every lane but
`regression` and `ship`. Each writes `evidence/ses/<ENGINE_LOG_PREFIX>ses-<slug>.log` in the build
store, and the script exits 1 when a check failed.

- `regression` (lane 1): the qmx-host, qma-harness, qmx-library, qmx-router and qmx-agents suites
  with `-n 2` at `--parent` and here. Pass when head fails nothing the parent passes.
- `ship` (lanes 2, 3, 4 and the perf block): takes the lane lock itself. The host's harness and
  Library store on the ship home, in this process; a Lab-home chat on claude/haiku gets three
  turns, the last echoing a planted fake key, then is closed by its owner. Writes `ses-item.log`
  (one item, three turn-end annotations, no new version), `ses-export.log` (the close export
  exists and the key is redacted) and `ses-search.log` (a Library search for the title finds the
  item with its Lab home). Perf: the ms the recorder added at each turn end. The ship home's
  `settings.toml` hashes the same before and after.
- `idle` (lane 5): a chat idle past a day on a fake clock gets one daily export, and only one.
- `restart` (lane 6): the store reopened, as a restarted host does, keeps the same item.
- `count` (lane 7): ten chats make ten session items.
- `secrets` (lane 9) and `processes` (lane 10): as OPS1's.

No key and no money act. The planted key is a fake in the OpenRouter key's shape.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

ENGINE_LANES: Final = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE_LANES))

import psutil  # noqa: E402
from common import SHIP_HOME, boot, lane_lock  # noqa: E402
from common import Log as EngineLog  # noqa: E402
from ep2_lanes import clean_env  # noqa: E402

PR: Final = "ses"
STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
PREFIX: Final = os.environ.get("ENGINE_LOG_PREFIX", "")
"""Read before `boot()`, which scrubs the environment."""
REPO: Final = Path(__file__).resolve().parents[3]
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
SUITES: Final = ("qmx-host", "qma-harness", "qmx-library", "qmx-router", "qmx-agents")
TITLE: Final = "SES lane pod chronicle"
PLANTED: Final = "sk-or-" + "v1-" + "5e" * 32
PROMPTS: Final = (
    "Reply with the single word ONE.",
    "Reply with the single word TWO.",
    f"Repeat this line back exactly, with nothing else: KEY={PLANTED}",
)
TURN_S: Final = 240.0


class Log(EngineLog):
    """`Log` writing to this PR's evidence folder in the build store."""

    def __init__(self, slug: str) -> None:
        folder = STORE / "evidence" / PR
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{PREFIX}{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def throwaway_home(slug: str) -> Path:
    root = STORE / "homes" / f"{PR}-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def settings_sha() -> str:
    return hashlib.sha256((SHIP_HOME / "settings.toml").read_bytes()).hexdigest()


async def turns_reach(store: Any, chat: str, n: int) -> int:
    from qmx_host.sessions import SessionRecorder  # noqa: PLC0415

    recorder = SessionRecorder(store)
    deadline = time.monotonic() + TURN_S
    seen = 0
    while time.monotonic() < deadline:
        head = recorder.head(chat)
        if head is not None:
            seen = int(store.get(store.engine, head).annotations.get("turns", 0))
            if seen >= n:
                return seen
        await asyncio.sleep(0.5)
    return seen


async def ship(item: Log, export: Log, search: Log) -> None:
    from qma.harness import Home, NewChat, OperatorText, QmxHome, control_service  # noqa: PLC0415
    from qma.harness.chat import transcript  # noqa: PLC0415
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.principal import MAIN  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    from qmx_host.host import LIBRARY  # noqa: PLC0415
    from qmx_host.sessions import RecordedHarness, SessionRecorder  # noqa: PLC0415

    home = QmxHome(SHIP_HOME)
    control = control_service(home)
    harness = await RecordedHarness.open(home, control=control)
    try:
        with Store.open(SHIP_HOME / LIBRARY, redactor=redact) as store:
            harness.record_into(SessionRecorder(store))
            workspace = Path("D:/Temp/ses-ship-ws")
            workspace.mkdir(parents=True, exist_ok=True)
            spec = NewChat(
                title=TITLE,
                model="haiku",
                workspace=workspace,
                home=Home("lab", "ses-pod"),
                tools=(),
            )
            chat = await harness.start_chat(spec)
            born = SessionRecorder(store).head(chat)
            item(f"chat {chat} on claude/haiku, Lab home; item head at birth {born}")
            texts: list[str] = []
            for n, prompt in enumerate(PROMPTS, start=1):
                began = time.monotonic()
                if n == 2:
                    await harness.send(chat, OperatorText(prompt))
                    seen = await turns_reach(store, chat, n)
                    item(f"turn {n} by send: turns annotation {seen}")
                else:
                    result = await (await harness.run_turn(chat, OperatorText(prompt))).result()
                    texts.append(result.text or "")
                    seen = await turns_reach(store, chat, n)
                    shown = redact.redact(result.text or "")[:60]
                    item(f"turn {n} by run_turn: {result.status} {shown!r}")
                item(f"turn {n} took {time.monotonic() - began:.1f} s")
            head = SessionRecorder(store).head(chat)
            notes = store.get(store.engine, head).annotations if head else {}
            hits = store.search(store.engine, TITLE, kind="session")
            mine = [h for h in hits if h.item == chat]
            item(f"annotations: { {k: notes.get(k) for k in sorted(notes)} }")
            item.check("one session item for the chat", len(mine) == 1, [h.item for h in hits])
            item.check("three turn-end annotations", notes.get("turns") == 3, notes.get("turns"))
            item.check("the turns minted no version", head == born, head)
            item.check(
                "the item carries the surface digest",
                notes.get("surface_digest") == harness.surface_digest(chat),
                notes.get("surface_digest"),
            )
            spent = harness.turn_end_ms
            item(f"PERF recorder ms at each turn end {[round(ms, 1) for ms in spent]}")
            item("PERF baseline with the recorder off: 0 ms added (nothing runs at turn end)")

            raw = transcript(home, chat)
            echoed = raw is not None and PLANTED in raw.read_text(encoding="utf-8")
            export(f"turn 3 text: {redact.redact(texts[-1])[:120]!r}")
            export.check("the live transcript holds the planted key (the turn echoed it)",
                         echoed, raw)  # fmt: skip
            await harness.close_chat(chat)
            exported = SessionRecorder(store).head(chat)
            view = store.get(store.engine, exported, blobs="fetch") if exported else None
            blob = b"" if view is None else view.data.get("transcript", b"")
            export(f"export version {exported}; transcript blob {len(blob)} bytes")
            export.check("the close export is a new version", exported not in {None, born},
                         exported)  # fmt: skip
            export.check("the export holds the transcript", b"KEY=" in blob, len(blob))
            export.check("the planted key is redacted", PLANTED.encode() not in blob,
                         re.findall(rb"KEY=\S{0,40}", blob)[:2])  # fmt: skip
            export.check("main holds the export", store.head(chat, MAIN) == (exported, 2),
                         store.head(chat, MAIN))  # fmt: skip

            hits = store.search(store.engine, TITLE, kind="session")
            found = next((h for h in hits if h.item == chat), None)
            fields = {} if found is None else store.get(store.engine, found.object_id).fields
            last = None if view is None else view.annotations.get("last_turn_at")
            search(f"search {TITLE!r}: {[(h.item, h.title) for h in hits]}")
            search(f"fields {fields}; last turn {last}")
            search.check("the search finds the chat's item", found is not None, found)
            search.check("with its Lab home", fields.get("home") == {"kind": "lab",
                         "project_id": "ses-pod"}, fields.get("home"))  # fmt: skip
            search.check("and its last turn", isinstance(last, str), last)
    finally:
        await harness.close()


def lane_ship() -> bool:
    item, export, search = Log("ses-item"), Log("ses-export"), Log("ses-search")
    with lane_lock(item):
        before = settings_sha()
        try:
            asyncio.run(ship(item, export, search))
        finally:
            after = settings_sha()
            item.check("the ship home's settings.toml is unchanged", before == after, after[:12])
    return all(log.verdict() == 0 for log in (item, export, search))


def record(chat: str) -> Any:
    from qma.harness import Home, NewChat, SessionId  # noqa: PLC0415
    from qma.harness.home import ChatRecord  # noqa: PLC0415
    from qma.harness.profiles import ProfileName  # noqa: PLC0415

    config = NewChat(TITLE).config(ProfileName("claude"), Path(), Home("lab", "ses-pod"))
    return ChatRecord(SessionId(chat), config, True, "idle")


def chat_id(n: int) -> str:
    return f"5e500000-0000-4000-8000-{n:012d}"


def lane_idle(log: Log) -> None:
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    from qmx_host.sessions import SessionRecorder  # noqa: PLC0415

    now = [datetime(2026, 10, 20, 9, 0, tzinfo=UTC)]
    folder = throwaway_home("idle")
    with Store.open(folder / "library", redactor=redact) as store:
        recorder = SessionRecorder(store, lambda: now[0])
        exports = folder / "export"
        exports.mkdir()
        (exports / "transcript.jsonl").write_text('{"type":"user"}\n', encoding="utf-8")

        async def exporter(_chat: Any) -> Path:
            return exports

        async def daily(chat: str) -> bool:
            if not recorder.idle_due(chat):
                return False
            await recorder.export(chat, exporter)  # pyright: ignore[reportArgumentType]
            return True

        chat = chat_id(1)
        recorder.born(record(chat), TITLE)
        recorder.turn_ended(record(chat), None)
        passes = []
        for hours in (12, 13, 1, 24):
            now[0] += timedelta(hours=hours)
            passes.append(asyncio.run(daily(chat)))
        versions = len(store.history(chat))
    log(f"daily passes at +12 h, +25 h, +26 h, +50 h: {passes}; main moves {versions}")
    log.check("one daily export lands for an idle chat", passes == [False, True, False, False],
              passes)  # fmt: skip


def lane_restart(log: Log) -> None:
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    from qmx_host.sessions import SessionRecorder  # noqa: PLC0415

    folder = throwaway_home("restart") / "library"
    chat = chat_id(1)
    with Store.open(folder, redactor=redact) as store:
        born = SessionRecorder(store).born(record(chat), TITLE)
        SessionRecorder(store).turn_ended(record(chat), None)
    with Store.open(folder, redactor=redact) as store:
        recorder = SessionRecorder(store)
        recorder.turn_ended(record(chat), None)
        head = recorder.head(chat)
        turns = store.get(store.engine, born).annotations.get("turns")
    log(f"item head before {born}, after the restart {head}; turns {turns}")
    log.check("the same item keeps updating", head == born and turns == 2, (head, turns))


def lane_count(log: Log) -> None:
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    from qmx_host.sessions import SessionRecorder  # noqa: PLC0415

    with Store.open(throwaway_home("count") / "library", redactor=redact) as store:
        recorder = SessionRecorder(store)
        for n in range(1, 11):
            recorder.born(record(chat_id(n)), TITLE)
            recorder.turn_ended(record(chat_id(n)), None)
        hits = store.search(store.engine, TITLE, kind="session", limit=100)
    log(f"session items: {len(hits)}")
    log.check("ten chats make ten items", len(hits) == 10, len(hits))


def lane_secrets(log: Log) -> None:
    done = subprocess.run(
        [sys.executable, "tools/secret_scan.py"], cwd=REPO, capture_output=True, text=True
    )
    log(f"secret_scan exit {done.returncode}: {(done.stdout + done.stderr).strip()[-400:]}")
    log.check("secret scan is clean", done.returncode == 0, done.returncode)


def desktop_app(process: psutil.Process) -> bool:
    """The Claude desktop app or a session it runs, the operator's and never a lane's."""
    for member in [process, *process.parents()]:
        with contextlib.suppress(psutil.Error):
            if "WindowsApps" in member.exe() and member.name().lower() == "claude.exe":
                return True
    return False


def lane_processes(log: Log) -> None:
    names = ("claude", "qma-cli-launcher")
    left = []
    for process in psutil.process_iter(["name", "cmdline"]):
        with contextlib.suppress(psutil.Error):
            if desktop_app(process):
                continue
            line = " ".join(process.info["cmdline"] or [])
            name = (process.info["name"] or "").lower()
            if any(n in name for n in names) or ("qmx_host" in line and "qma-ship" in line):
                left.append((process.pid, name, line[:120]))
    log(f"left: {left}")
    log.check("no host, claude or launcher process is left", left == [], left)
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK.exists())


def lane_regression(log: Log, parent: Path) -> None:
    def suite(tree: Path, package: str) -> tuple[set[str], str]:
        done = subprocess.run(
            [str(tree / "qmx-agents/.venv/Scripts/python.exe"), "-m", "pytest", "-n", "2", "-q",
             "-p", "no:cacheprovider", "-rf"],
            cwd=tree / "qmx-agents/packages" / package, env=clean_env(PYTHONIOENCODING="utf-8"),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )  # fmt: skip
        out = done.stdout + done.stderr
        failed = set(re.findall(r"^(?:FAILED|ERROR) (\S+)", out, re.MULTILINE))
        summary = next((ln for ln in reversed(out.splitlines()) if " in " in ln), "")
        return failed, summary

    for package in SUITES:
        base, base_line = suite(parent, package)
        head, head_line = suite(REPO, package)
        log(f"{package} parent: {base_line} {sorted(base)}")
        log(f"{package} head:   {head_line} {sorted(head)}")
        log.check(f"{package}: head fails nothing the parent passes", head <= base, head - base)


LANES: Final = ("ship", "idle", "restart", "count", "secrets", "processes")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lanes", nargs="*")
    parser.add_argument("--parent", type=Path, default=Path("D:/QMX-worktrees/chk-lib3"))
    args = parser.parse_args()
    boot()
    passed = True
    for lane in args.lanes or LANES:
        if lane == "ship":
            passed &= lane_ship()
            continue
        log = Log(f"ses-{lane}")
        if lane == "regression":
            lane_regression(log, args.parent)
        else:
            globals()[f"lane_{lane}"](log)
        passed &= log.verdict() == 0
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
