"""REF1's live lanes: context references (AD-63, H49) on the real harness and Library store.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/qma/e62_refs.py [--parent TREE] [lane ...]`
Lanes are `e62 run archived excerpt regression secrets processes`; none named runs every lane but
`regression`. Each writes `evidence/ref1/owner-ref1-<slug>.log` in the build store, and the script
exits 1 when a check failed.

- `e62` (lanes 2 and the perf block): the E62 Library half. A Lab-home chat on claude/haiku on the
  ship home under the lane lock, a pinned pod and the macro app's latest output attached, then a
  second harness on the same home reopens the session. Pass when both references are listed and
  the pod reads "newer version exists" after pod v8 is saved. Perf: the ms one reference resolves.
- `run` (lane 3): the copilot calls `context_add` for a run's output. Pass when the model's own
  call lands the landed artifact on the chat record.
- `archived` (lane 4, no model): an archived item attached and read. Pass when it reads
  `archived` and the text still comes back.
- `excerpt` (lane 6, no model): a very large artifact attached. Pass when the excerpt stays
  within 25 % of the window.
- `regression` (lane 1): the qmx-control, qma-harness and qmx-host suites with `-n 2` at
  `--parent` and here. Pass when head fails nothing the parent passes.
- `secrets` (lane 9) and `processes` (lane 10): as SES's.

The Library store of every lane is a throwaway folder under `homes/`, so no lane plants a pod or
an app in the ship home's Library. Only the chat records land in the ship home, as SES's did.
No key and no money act.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import importlib.util
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Final

ENGINE_LANES: Final = Path(__file__).resolve().parents[1] / "engine"
PR: Final = "ref1"
STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
PREFIX: Final = os.environ.get("ENGINE_LOG_PREFIX", "owner-")
REPO: Final = Path(__file__).resolve().parents[3]
LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
SUITES: Final = ("qmx-control", "qma-harness", "qmx-host")
POD: Final = "pod-7"
APP: Final = "macro-bias"
RUN: Final = "0192f0aa-0000-7000-8000-0000000000f1"
TURN_S: Final = 240.0


def operator() -> Any:
    """The principal that seeds a lane's Library: his own, as his store's fixture does."""
    from qmx_library.principal import Principal  # noqa: PLC0415

    return Principal("operator")


def engine_common() -> Any:
    """`scripts/live/engine/common.py` under its own name: the lane lock, the throwaway home and
    the boot, which this folder's `common.py` does not carry."""
    name = "e62_engine_common"
    spec = importlib.util.spec_from_file_location(name, ENGINE_LANES / "common.py")
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {ENGINE_LANES / 'common.py'}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


eng = engine_common()
boot, lane_lock, throwaway_home = eng.boot, eng.lane_lock, eng.throwaway_home
SHIP_HOME: Final = eng.SHIP_HOME


class Log:
    """`Log` writing to this PR's evidence folder in the build store."""

    def __init__(self, slug: str) -> None:
        folder = STORE / "evidence" / PR
        folder.mkdir(parents=True, exist_ok=True)
        self.path = folder / f"{PREFIX}{slug}.log"
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


def settings_sha() -> str:
    return hashlib.sha256((SHIP_HOME / "settings.toml").read_bytes()).hexdigest()


def clean_env(**extra: str) -> dict[str, str]:
    """No `ANTHROPIC_*` or `CLAUDE*` name and no `NODE_USE_SYSTEM_CA` reaches a child; TMP on D:."""
    banned = re.compile(r"(?i)^(anthropic|claude|node_use_system_ca)")
    keep = {name: value for name, value in os.environ.items() if not banned.match(name)}
    return keep | {"TMP": "D:/Temp", "TEMP": "D:/Temp", "PYTHONIOENCODING": "utf-8"} | extra


# -- the Library seed ------------------------------------------------------------------------


def published(store: Any, draft: Any) -> str:
    """A definition's version on `main`, the way his publish puts one there."""
    from qmx_library.principal import MAIN, drafts_ref  # noqa: PLC0415

    on = drafts_ref(str(draft.item))
    found = store.head(str(draft.item), on)
    head = None if found is None else found[0]
    commit = store.put(operator(), draft, on=on, expected_head=head)
    store.merge(operator(), commit.item, from_ref=on, into=MAIN, strategy="ff-only")
    return str(commit.object_id)


def seed_pod(store: Any, title: str) -> str:
    from qmx_library.port import Draft  # noqa: PLC0415

    return published(store, Draft("pod", POD, title=title, fields={"slots": {}}))


def seed_app(store: Any) -> tuple[str, str]:
    """The macro app and its latest landed `bias` output, as APP2a will land one."""
    from qmx_library.port import Draft  # noqa: PLC0415

    head = published(store, Draft("mini-app", APP, title="Macro bias app"))
    artifact = store.put(
        operator(),
        Draft(
            "artifact",
            None,
            title="Bias 2026-10-19",
            fields={"type": "bias", "metadata": {"producer_app": APP, "output": "bias"}},
        ),
        on="main",
        expected_head=None,
    )
    store.relate(operator(), artifact.object_id, "produced-by", head)
    return head, str(artifact.object_id)


def seed_run(store: Any, name: str = "bias", *, size: int = 20) -> tuple[str, str]:
    from qmx_library.port import Draft  # noqa: PLC0415

    run = store.put(
        operator(),
        Draft(
            "workflow-run",
            RUN,
            title="Nightly bias",
            fields={"run_id": RUN, "mode": "test", "status": "passed"},
        ),
        on="main",
        expected_head=None,
    )
    body = ("bias line\n" * (size // 10 + 1))[:size]
    artifact = store.put(
        operator(),
        Draft(
            "artifact",
            None,
            title="Bias, night one",
            fields={"type": name},
            blobs={"content": body.encode()},
        ),
        on="main",
        expected_head=None,
    )
    store.relate(operator(), artifact.object_id, "produced-by", run.object_id)
    return str(run.object_id), str(artifact.object_id)


def library(root: Path) -> Any:
    from qmx_engine.ledger import redact  # noqa: PLC0415
    from qmx_library.store import Store  # noqa: PLC0415

    return Store.open(root / "library", redactor=redact)


def ship() -> Any:
    """The ship home's harness with the recorder, as `qmx_host.serve` opens it."""
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415
    from qmx_host.sessions import RecordedHarness  # noqa: PLC0415

    home = QmxHome(SHIP_HOME)
    return home, control_service(home), RecordedHarness


async def opened(store: Any) -> Any:
    """A `RecordedHarness` on the ship home, recording into `store`. Close it to reopen."""
    home, control, recorded = ship()
    harness = await recorded.open(home, control=control)
    harness.record_into(recorder(store))
    return harness


def recorder(store: Any) -> Any:
    from qmx_host.sessions import SessionRecorder  # noqa: PLC0415

    return SessionRecorder(store)


async def chat_on(harness: Any, title: str) -> Any:
    from qma.harness import Home, NewChat  # noqa: PLC0415

    workspace = Path("D:/Temp/ref1-ws")
    workspace.mkdir(parents=True, exist_ok=True)
    return await harness.start_chat(
        NewChat(title=title, model="haiku", workspace=workspace, home=Home("lab", POD))
    )


async def say(harness: Any, chat: Any, text: str) -> Any:
    """One turn, its result, and the seconds it took."""
    from qma.harness import OperatorText  # noqa: PLC0415

    began = time.monotonic()
    handle = await harness.run_turn(chat, OperatorText(text))
    result = await asyncio.wait_for(handle.result(), TURN_S)
    return result, time.monotonic() - began


# -- lanes -----------------------------------------------------------------------------------


async def e62(log: Log, perf: Log) -> None:
    root = throwaway_home(PR, "e62")
    with library(root) as store:
        seed_pod(store, "Pod 7")
        seed_app(store)
        harness = await opened(store)
        try:
            chat = await chat_on(harness, "REF1 E62 pod and app")
            result, seconds = await say(harness, chat, "Reply with the single word ONE.")
            log(f"turn on haiku in a Lab home: {result.status} {result.text!r} in {seconds:.1f} s")
            log.check("the chat is a real Lab-home chat", result.status == "ok", result.status)
            reads = harness.context_reads(chat)
            began = time.monotonic()
            pod = await reads["context_add"]({"ref": f"@pod:{POD}"})
            elapsed = (time.monotonic() - began) * 1000
            app = await reads["context_add"]({"ref": f"@app:{APP}/bias"})
            attached = harness.record(chat).attached if harness.record(chat) else ()
            log(f"attached at the first open: {[entry.ref for entry in attached]}")
            log.check("the pinned pod resolved", pod["status"] == "ready", pod["ref"])
            log.check("the app's latest output resolved", app["artifact_id"] is not None, app)
            perf(f"PERF one reference resolved in {elapsed:.1f} ms ({pod['ref']})")
        finally:
            await harness.close()
        v8 = seed_pod(store, "Pod 8")
        hub = await opened(store)
        try:
            page = await hub.context_reads(chat)["context_list"]({})
            record = hub.record(chat)
            log(f"reopened in the hub: {page['lines']}")
            log(f"the record holds {[entry.ref for entry in record.attached] if record else None}")
            log.check(
                "both references are listed after reopening",
                [entry["ref"] for entry in page["entries"]] == [f"@pod:{POD}", f"@app:{APP}/bias"],
                [entry["ref"] for entry in page["entries"]],
            )
            log.check(
                "the pod reads newer version exists after v8",
                page["entries"][0]["note"] == "newer version exists"
                and page["entries"][0]["version_id"] != v8,
                (page["entries"][0]["note"], page["entries"][0]["version_id"]),
            )
            log.check(
                "the pod is still the version it was pinned to",
                page["entries"][0]["version_id"] == pod["version_id"],
                (page["entries"][0]["version_id"], pod["version_id"]),
            )
            log.check(
                "the app's output is the landed one",
                page["entries"][1]["artifact_id"] == app["artifact_id"],
                page["entries"][1]["artifact_id"],
            )
        finally:
            await hub.close()


async def run_lane(log: Log) -> None:
    root = throwaway_home(PR, "run")
    with library(root) as store:
        run_object, artifact = seed_run(store)
        harness = await opened(store)
        try:
            chat = await chat_on(harness, "REF1 run output by the copilot")
            prompt = (
                "Call the tool named context_add exactly once with these arguments: "
                f'{{"ref": "@run:{RUN}/bias"}}. Then call context_list. Then reply with the lines '
                "context_list returned, and nothing else."
            )
            result, seconds = await say(harness, chat, prompt)
            log(f"copilot turn in {seconds:.1f} s: {result.status} {(result.text or '')[:200]!r}")
            record = harness.record(chat)
            attached = () if record is None else record.attached
            log(f"the chat record holds {[entry.document() for entry in attached]}")
            log.check(
                "the copilot called context_add for the run's output",
                [entry.ref for entry in attached] == [f"@run:{RUN}/bias"],
                [entry.ref for entry in attached],
            )
            log.check(
                "and it resolved to the landed object",
                bool(attached) and attached[0].artifact_id == artifact,
                None if not attached else attached[0].artifact_id,
            )
            log.check(
                "the run object is the pinned version",
                bool(attached) and attached[0].version_id == run_object,
                None if not attached else attached[0].version_id,
            )
        finally:
            await harness.close()


async def archived(log: Log) -> None:
    from qmx_library.principal import state_ref  # noqa: PLC0415

    root = throwaway_home(PR, "archived")
    with library(root) as store:
        seed_pod(store, "Pod 7")
        harness = await opened(store)
        try:
            chat = await chat_on(harness, "REF1 an archived item")
            reads = harness.context_reads(chat)
            before = await reads["context_add"]({"ref": f"@pod:{POD}"})
            store.archive(operator(), POD, "superseded by pod 8")
            log(f"the item's state ref: {store.head(POD, state_ref(POD))}")
            page = await reads["context_list"]({})
            text = await reads["context_read"]({"ref": f"@pod:{POD}"})
            log(f"listed: {page['lines']}")
            log(f"read: {text['text'][:120]!r}")
            log.check("it read ready before the archive", before["status"] == "ready", before)
            log.check("it reads archived", page["entries"][0]["status"] == "archived", page)
            log.check(
                "and stays readable",
                text["text"].startswith(f"@pod:{POD} archived"),
                text["text"].splitlines()[0],
            )
        finally:
            await harness.close()


async def excerpt(log: Log) -> None:
    from qma.harness.surface import CHARS_PER_TOKEN, EXCERPT_SOFT, excerpt_budget  # noqa: PLC0415

    root = throwaway_home(PR, "excerpt")
    with library(root) as store:
        run_object, artifact = seed_run(store, "huge", size=200_000)
        harness = await opened(store)
        try:
            chat = await chat_on(harness, "REF1 a very large item")
            reads = harness.context_reads(chat)
            began = time.monotonic()
            added = await reads["context_add"]({"ref": f"@run:{RUN}/huge"})
            elapsed = (time.monotonic() - began) * 1000
            budget = excerpt_budget({})
            window_chars = 200_000 * CHARS_PER_TOKEN
            body = added["excerpt"].split("\n\n", 1)[-1]
            share = len(body) / window_chars
            log(f"artifact {artifact} holds 200,000 characters")
            log(f"its excerpt is {len(added['excerpt'])} characters")
            log(f"the window is {window_chars:,} characters; the excerpt body is {share:.3%} of it")
            log.check("the large item attached", added["artifact_id"] == artifact, added["ref"])
            log.check(
                f"the excerpt body stays within 25 % of the window ({EXCERPT_SOFT:.0%})",
                share <= EXCERPT_SOFT,
                f"{share:.3%} <= {EXCERPT_SOFT:.0%}",
            )
            log.check(
                "and the whole answer within the soft budget plus its handle",
                len(added["excerpt"]) <= budget.soft_chars + 200,
                (len(added["excerpt"]), budget.soft_chars),
            )
            log(f"PERF attaching a 200,000-character item took {elapsed:.1f} ms")
            log(f"the run object is {run_object}")
        finally:
            await harness.close()


def lane_regression(log: Log, parent: Path) -> None:
    def suite(tree: Path, package: str) -> tuple[set[str], str]:
        python = tree / "qmx-agents/.venv/Scripts/python.exe"
        done = subprocess.run(
            [str(python), "-m", "pytest", "-n", "2", "-q", "-p", "no:cacheprovider", "-rf"],
            cwd=tree / "qmx-agents/packages" / package,
            env=clean_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        out = done.stdout + done.stderr
        failed = set(re.findall(r"^(?:FAILED|ERROR) (\S+)", out, re.MULTILINE))
        summary = next((line for line in reversed(out.splitlines()) if " in " in line), "")
        return failed, summary

    for package in SUITES:
        base, base_line = suite(parent, package)
        head, head_line = suite(REPO, package)
        log(f"{package} parent: {base_line} {sorted(base)}")
        log(f"{package} head:   {head_line} {sorted(head)}")
        log.check(f"{package}: head fails nothing the parent passes", head <= base, head - base)


def lane_secrets(log: Log) -> None:
    done = subprocess.run(
        [sys.executable, "tools/secret_scan.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=clean_env(),
    )
    log(f"secret_scan exit {done.returncode}: {(done.stdout + done.stderr).strip()[-400:]}")
    log.check("secret scan is clean", done.returncode == 0, done.returncode)


def desktop_app(process: Any) -> bool:
    """The Claude desktop app or a session it runs, the operator's and never a lane's."""
    import psutil  # noqa: PLC0415

    for member in [process, *process.parents()]:
        with contextlib.suppress(psutil.Error):
            if "WindowsApps" in member.exe() and member.name().lower() == "claude.exe":
                return True
    return False


def lane_processes(log: Log) -> None:
    import psutil  # noqa: PLC0415

    names = ("claude", "qma-cli-launcher")
    left = []
    for process in psutil.process_iter(["name", "cmdline"]):
        with contextlib.suppress(psutil.Error):
            if desktop_app(process):
                continue
            line = " ".join(process.info["cmdline"] or [])
            name = (process.info["name"] or "").lower()
            if any(found in name for found in names) or ("qmx_host" in line and "qma-ship" in line):
                left.append((process.pid, name, line[:120]))
    log(f"left: {left}")
    log.check("no host, claude or launcher process is left", left == [], left)
    log.check("no lane lock is left", not LANE_LOCK.exists(), LANE_LOCK.exists())


def lane_ship(slug: str, lane: Any) -> bool:
    """A ship-home lane: the lane lock, the settings hash before and after, the lane itself."""
    log = Log(f"ref1-{slug}")
    perf = Log("ref1-perf") if lane is e62 else None
    with lane_lock(log):
        before = settings_sha()
        try:
            asyncio.run(lane(log, perf) if perf is not None else lane(log))
        finally:
            after = settings_sha()
            log.check("the ship home's settings.toml is unchanged", before == after, after[:12])
    return log.verdict() == 0


LANES: Final = ("e62", "run", "archived", "excerpt", "secrets", "processes")
LOCAL: Final = {"archived": archived, "excerpt": excerpt}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lanes", nargs="*")
    parser.add_argument("--parent", type=Path, default=Path("D:/QMX-worktrees/bld-ses"))
    args = parser.parse_args()
    boot()
    passed = True
    for name in args.lanes or LANES:
        if name == "regression":
            log = Log("ref1-regression")
            lane_regression(log, args.parent)
        elif name in ("e62", "run"):
            passed &= lane_ship(name, e62 if name == "e62" else run_lane)
            continue
        else:
            log = Log(f"ref1-{name}")
            if name in LOCAL:
                asyncio.run(LOCAL[name](log))
            elif name == "secrets":
                lane_secrets(log)
            elif name == "processes":
                lane_processes(log)
        passed &= log.verdict() == 0
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
