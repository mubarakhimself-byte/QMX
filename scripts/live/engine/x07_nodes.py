"""EP7's live lanes for the runner and the local worker: real `python -m qmx_engine` runs of
workflow folders whose script, grader, monitor and subworkflow nodes run as real subprocesses, read
back from the real ledger.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x07_nodes.py [--base REV] [--trunk REV] [lane]`
Lanes are `regression monitor snapshot subworkflow grader concurrency cancel timeout perf`; none
named runs all. Each writes `evidence/ep7/<ENGINE_LOG_PREFIX>ep7-<lane>.log` and the script exits 1
if any lane failed. No lane needs a model, a key or the ship home. `e14_script_env.py` and
`e04_unknown_outcome.py` reuse the helpers here.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from itertools import pairwise
from pathlib import Path
from textwrap import dedent
from typing import Any, Final

from common import Log, throwaway_home
from ep2_lanes import AGENTS, GIT, REPO, clean_env, git
from qmx_engine.definition.model import Workflow
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS
from qmx_ledger.journal import fingerprint

HARNESS: Final = "qmx-agents/packages/qma-harness"
CHAIN: Final = (
    AGENTS / "packages" / "qmx-engine" / "tests" / "fixtures" / "workflows" / "script-chain"
)
ENGINE: Final = [sys.executable, "-m", "qmx_engine"]
PERF_NODES: Final = 100


def node(name: str, type_: str, **parameters: Any) -> dict[str, Any]:
    return {"id": name, "name": name, "type": type_, "typeVersion": 1, "parameters": parameters}


def edge(target: str) -> dict[str, Any]:
    return {"node": target, "port": "in", "map": "one"}


def write_folder(
    root: Path,
    nodes: list[dict[str, Any]],
    connections: dict[str, dict[str, list[dict[str, Any]]]],
    scripts: dict[str, str],
    **settings: Any,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    document = {
        "schema": "qmx.workflow/1",
        "id": root.name,
        "name": root.name,
        "settings": settings,
        "nodes": nodes,
        "connections": {
            source: {port: [targets] for port, targets in ports.items()}
            for source, ports in connections.items()
        },
    }
    (root / "definition.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    (root / "scripts").mkdir(exist_ok=True)
    for name, text in scripts.items():
        (root / "scripts" / f"{name}.py").write_text(dedent(text), encoding="utf-8")
    return root


def cli(log: Log, *args: str, **env: str) -> tuple[int, list[str]]:
    log(f"$ python -m qmx_engine {' '.join(args)}")
    done = subprocess.run(
        [*ENGINE, *args],
        cwd=AGENTS,
        env=clean_env(**env),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
    )
    lines = done.stdout.splitlines()
    for line in [*lines, *done.stderr.splitlines()[-10:]]:
        log(f"  | {line}")
    log(f"  exit {done.returncode}")
    return done.returncode, lines


def run_id_of(lines: list[str]) -> str:
    return lines[0].split()[1]


def events(home: Path, run_id: str) -> list[Event]:
    with Reader.open(home) as reader:
        return reader.events(run_id)


def of(found: list[Event], kind: str, node_id: str) -> list[dict[str, Any]]:
    return [e.data for e in found if e.kind == kind and e.data.get("node_id") == node_id]


def in_process(
    home: Path, root: Path, inputs: Any = None, **settings: Any
) -> tuple[Outcome, float]:
    workflow = runnable(root)

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings={**DEFAULTS, **settings})
            outcome = await engine.start(root, workflow, mode="test", inputs=inputs)
            await engine.settle()
            return outcome

    began = time.perf_counter()
    outcome = asyncio.run(go())
    return outcome, time.perf_counter() - began


def runnable(root: Path) -> Workflow:
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: the lane's folder does not run: {found}")
    return found[1]


def regression(log: Log, base: str, trunk: str) -> None:
    on_trunk = subprocess.run(
        [GIT, "cat-file", "-e", f"{trunk}:qmx-agents/packages/qmx-engine/src/qmx_engine/runner.py"],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    log.check("trunk has no runner to compare against", on_trunk.returncode != 0, trunk)
    diff = subprocess.run(
        [GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], cwd=REPO, check=False
    )
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    home = throwaway_home("ep7", "regression")
    code, lines = cli(log, "run", str(CHAIN), "--mode", "test", "--home", str(home))
    expected = f"run finished {fingerprint({'total': {'main': {'total': 20}}})}"
    log.check(
        "script-chain ends with run finished and the outputs hash",
        code == 0 and lines[-1] == expected,
        lines[-1:],
    )


def monitor(log: Log) -> None:
    home = throwaway_home("ep7", "monitor")
    root = write_folder(
        home / "wf-monitor",
        [
            node("start", "trigger"),
            node("watch", "monitor", source="scripts/feed.py"),
            node("act", "script", script="scripts/act.py"),
        ],
        {"start": {"main": [edge("watch")]}, "watch": {"changed": [edge("act")]}},
        {
            "feed": 'import json\nprint(json.dumps({"ids": ["2610.01234", "2610.01999"]}))\n',
            "act": "print('acted')\n",
        },
    )
    runs = []
    for fire in (1, 2):
        _, lines = cli(log, "run", str(root), "--home", str(home))
        found = events(home, run_id_of(lines))
        watch = of(found, "node_finished", "watch")[0]["outputs"]
        acted = len(of(found, "node_started", "act"))
        log(f"fire {fire}: watch ports {sorted(watch)}, act attempts {acted}")
        runs.append((sorted(watch), acted))
    log.check(
        "first fire is changed and the downstream node runs", runs[0] == (["changed"], 1), runs[0]
    )
    log.check(
        "second fire ends silent and no downstream node starts", runs[1] == (["silent"], 0), runs[1]
    )


SEED: Final = """
    import json, sys
    from pathlib import Path
    Path("seed.txt").write_text("v1")
    print(json.dumps(json.load(sys.stdin)["in"]))
"""
WORK: Final = """
    import json, sys
    from pathlib import Path
    counter = Path(json.load(sys.stdin)["in"])
    tries = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(tries))
    seen = {"half": Path("half.txt").exists(), "seed": Path("seed.txt").read_text()}
    if tries == 1:
        Path("half.txt").write_text("left by the failed attempt")
        Path("seed.txt").write_text("v2")
        sys.exit(1)
    print(json.dumps(seen))
"""


def snapshot(log: Log) -> None:
    home = throwaway_home("ep7", "snapshot")
    work = node("work", "script", script="scripts/work.py")
    work["retry"] = {"max_tries": 1}  # park on the first failure, so the resume is the retry
    root = write_folder(
        home / "wf-snapshot",
        [node("start", "trigger"), node("seed", "script", script="scripts/seed.py"), work],
        {"start": {"main": [edge("seed")]}, "seed": {"main": [edge("work")]}},
        {"seed": SEED, "work": WORK},
    )
    counter = home / "tries.txt"
    _, lines = cli(log, "run", str(root), "--home", str(home), "--inputs", json.dumps(str(counter)))
    run_id = run_id_of(lines)
    zone = home / "workspaces" / "wf-wf-snapshot" / "runs" / run_id
    left = sorted(p.name for p in zone.iterdir() if p.name != ".snap")
    log(f"zone after the failed attempt: {left}")
    log.check("the failed attempt left half.txt behind", "half.txt" in left, left)
    code, resumed = cli(log, "resume", run_id, "--home", str(home))
    found = events(home, run_id)
    seen = of(found, "node_finished", "work")[-1]["outputs"]["main"]
    log(f"what attempt 2 saw on start: {seen}")
    log.check(
        "the resume reran the failed node to the end",
        code == 0 and resumed[-1].startswith("run finished"),
        resumed[-1:],
    )
    log.check(
        "half.txt from the failed attempt was gone before the retry",
        seen == {"half": False, "seed": "v1"},
        seen,
    )
    log.check(
        "seed did not rerun",
        len(of(found, "node_started", "seed")) == 1,
        len(of(found, "node_started", "seed")),
    )


ECHO: Final = "import json, sys\nprint(json.dumps({'got': json.load(sys.stdin)['in']}))\n"


def subworkflow(log: Log) -> None:
    home = throwaway_home("ep7", "subworkflow")
    root = write_folder(
        home / "wf-parent",
        [
            node("start", "trigger"),
            node("call", "subworkflow", workflow="child"),
            node("after", "script", script="scripts/echo.py"),
        ],
        {"start": {"main": [edge("call")]}, "call": {"main": [edge("after")]}},
        {"echo": ECHO},
    )
    write_folder(
        root / "child",
        [node("start", "trigger"), node("echo", "script", script="scripts/echo.py")],
        {"start": {"main": [edge("echo")]}},
        {"echo": ECHO},
    )
    code, lines = cli(log, "run", str(root), "--home", str(home), "--inputs", "41")
    run_id = run_id_of(lines)
    child = f"{run_id}.call.0.1"
    created = events(home, child)[0].data
    log(f"child run {child}: parent_run_id {created['parent_run_id']}")
    log(f"child call_depth {created['call_depth']}")
    after = of(events(home, run_id), "node_finished", "after")[0]["outputs"]["main"]
    log(f"parent's next node got: {after}")
    log.check(
        "the child has its own run id and the parent's id",
        created["parent_run_id"] == run_id and child != run_id,
        created["parent_run_id"],
    )
    log.check(
        "the parent continued on the child's output",
        code == 0
        and after == {"got": {"run_id": child, "outputs": {"echo": {"main": {"got": 41}}}}},
        after,
    )


def grader(log: Log) -> None:
    home = throwaway_home("ep7", "grader")
    check = 'import json\nprint(json.dumps({"verdict": "fail", "feedback": "no citations"}))\n'
    root = write_folder(
        home / "wf-grader",
        [
            node("start", "trigger"),
            node("check", "grader", mode="deterministic", script="scripts/check.py"),
            node("ok", "script", script="scripts/note.py"),
            node("fix", "script", script="scripts/note.py"),
        ],
        {
            "start": {"main": [edge("check")]},
            "check": {"pass": [edge("ok")], "fail": [edge("fix")]},
        },
        {"check": check, "note": "print('ran')\n"},
    )
    _, lines = cli(log, "run", str(root), "--home", str(home), "--inputs", '"a draft"')
    run_id = run_id_of(lines)
    found = events(home, run_id)
    with Reader.open(home) as reader:
        verdict = next(s.verdict for s in reader.spans(run_id) if s.node_id == "check")
    branches = (len(of(found, "node_started", "ok")), len(of(found, "node_started", "fix")))
    log(f"span verdict {verdict}; attempts pass branch {branches[0]}, fail branch {branches[1]}")
    log.check("only the fail branch ran", branches == (0, 1), branches)
    log.check("the grader's span carries the verdict", verdict == "fail", verdict)


TIMED: Final = """
    import json, time
    began = time.time()
    time.sleep(1.0)
    print(json.dumps([began, time.time()]))
"""


def concurrency(log: Log) -> None:
    home = throwaway_home("ep7", "concurrency")
    names = [f"s{i}" for i in range(6)]
    root = write_folder(
        home / "wf-concurrency",
        [node("start", "trigger"), *(node(n, "script", script="scripts/timed.py") for n in names)],
        {"start": {"main": [edge(n) for n in names]}},
        {"timed": TIMED},
    )
    outcome, seconds = in_process(home, root, **{"placement.pc.concurrency": 3})
    spans = [outcome.outputs[n]["main"] for n in names]  # type: ignore[index]
    moments = sorted([(b, 1) for b, _ in spans] + [(e, -1) for _, e in spans])
    running, most = 0, 0
    for _, step in moments:
        running += step
        most = max(most, running)
    log(f"6 scripts of 1 s at concurrency 3 took {seconds:.2f} s; most at once {most}")
    log.check("at most 3 ran at once", most <= 3, most)
    log.check("the slots were used (3 at once)", most == 3, most)


SPAWNER: Final = """
    import os, subprocess, sys, time
    from pathlib import Path
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    Path(r"PIDS").write_text(f"{os.getpid()} {child.pid}")
    time.sleep(120)
"""


def alive(pid: int) -> bool:
    if sys.platform == "win32":
        found = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        return str(pid) in found.stdout
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def cancel(log: Log) -> None:
    home = throwaway_home("ep7", "cancel")
    pids_file = home / "pids.txt"
    root = write_folder(
        home / "wf-cancel",
        [node("start", "trigger"), node("long", "script", script="scripts/spawner.py")],
        {"start": {"main": [edge("long")]}},
        {"spawner": SPAWNER.replace("PIDS", str(pids_file))},
    )
    workflow = runnable(root)
    gone_after: list[float] = []

    async def go() -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger)
            run = asyncio.create_task(engine.start(root, workflow, mode="test", inputs=None))
            while not pids_file.exists() or not pids_file.read_text():
                await asyncio.sleep(0.05)
            pids = [int(p) for p in pids_file.read_text().split()]
            key = next(k for k in engine.worker.running if ":long:" in k)
            log(f"process tree {pids}; cancel {key}")
            began = time.monotonic()
            engine.worker.cancel(key)
            while any(alive(p) for p in pids) and time.monotonic() - began < 10:
                await asyncio.sleep(0.1)
            gone_after.append(time.monotonic() - began)
            log(f"alive after cancel: {[p for p in pids if alive(p)]}")
            return await run

    outcome = asyncio.run(go())
    failed = of(events(home, outcome.run_id), "node_failed", "long")
    log(f"run {outcome.status}: {outcome.reason}")
    log.check("the process tree was gone within 5 s", gone_after[0] < 5, f"{gone_after[0]:.2f} s")
    log.check("the attempt failed cancelled", [f["code"] for f in failed] == ["cancelled"], failed)


def timeout(log: Log) -> None:
    home = throwaway_home("ep7", "timeout")
    sleeper = node("sleep", "script", script="scripts/sleep.py")
    sleeper["timeout"] = {"run_seconds": 2}
    root = write_folder(
        home / "wf-timeout",
        [node("start", "trigger"), sleeper],
        {"start": {"main": [edge("sleep")]}},
        {"sleep": "import time\ntime.sleep(120)\n"},
    )
    began = time.monotonic()
    _, lines = cli(log, "run", str(root), "--home", str(home))
    took = time.monotonic() - began
    failed = of(events(home, run_id_of(lines)), "node_failed", "sleep")[0]
    log(f"node_failed code={failed['code']} retryable={failed['retryable']} after {took:.1f} s")
    log(f"effect_state={failed['effect_state']} signature={failed['signature']}")
    log.check(
        "it failed with code timeout and retryable=true",
        (failed["code"], failed["retryable"]) == ("timeout", True),
        failed["code"],
    )
    log.check(
        "signature is the timeout signature",
        failed["signature"] == signature("timeout", failed["message"]),
        failed["signature"][:12],
    )
    log.check("the run did not wait out the 120 s sleep", took < 30, f"{took:.1f} s")


def perf(log: Log) -> None:
    home = throwaway_home("ep7", "perf")
    names = [f"n{i:03d}" for i in range(PERF_NODES)]
    nodes = [
        node("start", "trigger"),
        *(node(n, "script", script="scripts/noop.py") for n in names),
    ]
    chain = ["start", *names]
    root = write_folder(
        home / "wf-perf",
        nodes,
        {a: {"main": [edge(b)]} for a, b in pairwise(chain)},
        {"noop": "print(0)\n"},
    )
    noop = root / "scripts" / "noop.py"
    env = clean_env()
    began = time.perf_counter()
    for _ in range(20):
        subprocess.run([sys.executable, "-I", str(noop)], env=env, capture_output=True, check=True)
    bare = (time.perf_counter() - began) / 20
    outcome, seconds = in_process(home, root)
    per_node = seconds / PERF_NODES
    overhead_ms = (per_node - bare) * 1000
    log(f"{PERF_NODES} no-op script nodes in a chain: {seconds:.2f} s")
    log(f"that is {per_node * 1000:.1f} ms a node")
    log(f"a bare `python -I noop.py` takes {bare * 1000:.1f} ms (mean of 20)")
    log(f"engine overhead per script node: {overhead_ms:.1f} ms (recorded, not gated)")
    log.check("the 100-node run finished", outcome.status == "passed", outcome.status)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/engine/hg2")
    parser.add_argument("--trunk", default="origin/engine/ep6")
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    base, trunk = git("rev-parse", args.base), git("rev-parse", args.trunk)
    lanes: dict[str, Callable[[Log], None]] = {
        "regression": lambda log: regression(log, base, trunk),
        "monitor": monitor,
        "snapshot": snapshot,
        "subworkflow": subworkflow,
        "grader": grader,
        "concurrency": concurrency,
        "cancel": cancel,
        "timeout": timeout,
        "perf": perf,
    }
    failed: list[str] = []
    for name in args.lanes or list(lanes):
        log = Log("ep7", f"ep7-{name}")
        log(f"lane {name} at head {git('rev-parse', 'HEAD')}, harness base {base}")
        lanes[name](log)
        if log.verdict():
            failed.append(name)
    print(f"failed lanes: {failed}" if failed else "all lanes passed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
