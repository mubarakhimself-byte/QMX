"""EP9's regression lane, its explain lane and its perf probe.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x09_explain.py [--base REV] [--trunk REV]
[--trunk-tree DIR] [lane]`
Lanes are `regression explain perf`; none named runs all. Each writes
`evidence/ep9/<ENGINE_LOG_PREFIX>ep9-<lane>.log`, and the script exits 1 if any lane failed.

- `regression` (lane 1): the harness is byte-identical to its base, and the `qmx-control` suite
  has the same failures (the known rclone one only) on the trunk (EP8's head, checked out detached
  in `--trunk-tree`, made and synced when missing) and at head, and at head passes at least the
  trunk's count (later PRs add `qmx-control` tests).
- `explain` (lane 4): `python -m qmx_engine run` parks a run whose real script fails its own
  check, then `python -m qmx_engine explain` names the node, every ladder step and the park reason.
- `perf`: one timed `explain` of a 200-node run (an in-process stub runs the script nodes, so the
  probe times `explain`, not 200 subprocesses).

No model, no key, no ship home.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from common import Log, throwaway_home
from ep2_lanes import GIT, HARNESS, REPO, UV, counts, run
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.store import Ledger
from qmx_engine.nodes.base import NodeJob, NodeResult, Ok
from qmx_engine.runner import Engine
from qmx_engine.service.api import explain_run
from qmx_engine.settings import DEFAULTS
from x07_nodes import cli, edge, events, node, run_id_of, write_folder

CONTROL: Final = "qmx-agents/packages/qmx-control"
PERF_NODES: Final = 200
KNOWN_ENVIRONMENT_FAILURES: Final = frozenset(
    {"tests/test_backup.py::test_backup_settings_and_rest_mcp_restore"}
)
"""rclone is not installed on this PC (RESUME.md, Gotchas)."""
CHECK: Final = """
    import json, sys
    numbers = json.load(sys.stdin)["in"]
    if sum(numbers or []) != 10:
        sys.exit("the totals do not add up")
    print(json.dumps(numbers))
"""


def regression(log: Log, base: str, trunk: str, tree: Path) -> None:
    diff = run(log, [GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], REPO)
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    if not tree.exists():
        run(log, [GIT, "worktree", "add", "--detach", str(tree), trunk], REPO)
        run(log, [UV, "sync", "--frozen", "--all-packages", "--all-groups"], tree / "qmx-agents")
    wanted = run(log, [GIT, "rev-parse", trunk], REPO).stdout.strip()
    found = run(log, [GIT, "rev-parse", "HEAD"], tree).stdout.strip()
    log.check("the trunk tree is checked out at the trunk", found == wanted, (found, wanted))
    suite = [UV, "run", "--no-sync", "python", "-m", "pytest", "tests", "-q", "-n", "2"]
    suite += ["-p", "no:cacheprovider"]
    trunk_out = run(log, suite, tree / CONTROL).stdout
    head_out = run(log, suite, REPO / CONTROL).stdout
    at_trunk, at_head = counts(trunk_out), counts(head_out)
    failed_trunk, failed_head = failures(trunk_out), failures(head_out)
    log.check(
        "qmx-control suite passes at the trunk but for known environment failures",
        at_trunk.get("passed", 0) > 0 and failed_trunk <= KNOWN_ENVIRONMENT_FAILURES,
        (at_trunk, sorted(failed_trunk)),
    )
    log.check(
        "qmx-control passes at least the trunk's tests at head, with the same failures",
        at_head.get("passed", 0) >= at_trunk.get("passed", 0) and failed_head == failed_trunk,
        (at_head, sorted(failed_head)),
    )


def failures(output: str) -> set[str]:
    return {line.split()[1] for line in output.splitlines() if line.startswith("FAILED ")}


def explain_lane(log: Log) -> None:
    home = throwaway_home("ep9", "explain")
    check = node("check", "script", script="scripts/check.py")
    check["retry"] = {"max_tries": 3, "backoff_seconds": [0, 0]}
    root = write_folder(
        home / "wf-logic",
        [node("start", "trigger"), check],
        {"start": {"main": [edge("check")]}},
        {"check": CHECK},
    )
    code, lines = cli(log, "run", str(root), "--home", str(home), "--inputs", "[1, 2]")
    run_id = run_id_of(lines)
    log.check("the run parks", code == 1 and "run failed:" in lines[-1], lines[-1:])
    steps = [str(e.data["step"]) for e in events(home, run_id) if e.kind == "ladder_step"]
    log(f"ladder steps in the ledger: {' '.join(steps)}")
    code, shown = cli(log, "explain", run_id, "--home", str(home))
    printed = "\n".join(shown)
    ladder = [line.split()[1].rstrip(":") for line in shown if line.startswith("  ladder ")]
    log.check("explain exits 0", code == 0, code)
    log.check(
        "explain names the run failed (parked)",
        f"run {run_id} failed (parked)" in printed,
        shown[:1],
    )
    log.check(
        "explain names the node",
        "node check: parked" in printed,
        [line for line in shown if line.startswith("node check")],
    )
    log.check("explain prints every ladder step, in order", ladder == steps and bool(steps), ladder)
    log.check(
        "explain prints the park reason with the script's own error",
        "the totals do not add up" in printed and "node check failed: script_exit" in printed,
        [line for line in shown if "park" in line],
    )


class Stub:
    def run(self, job: NodeJob) -> NodeResult:
        return Ok({"main": job.inputs.get("in") if isinstance(job.inputs, dict) else None})


def perf(log: Log) -> None:
    home = throwaway_home("ep9", "perf")
    names = [f"n{i:03d}" for i in range(PERF_NODES - 1)]
    nodes: list[dict[str, Any]] = [node("start", "trigger")]
    nodes += [node(name, "script", script="scripts/step.py") for name in names]
    connections = {a: {"main": [edge(b)]} for a, b in zip(["start", *names], names, strict=False)}
    root = write_folder(home / "wf-wide", nodes, connections, {"step": "print(1)\n"})
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: the perf folder does not run: {found}")

    async def go() -> str:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS, executors={"script": Stub()})
            outcome = await engine.start(root, found[1], mode="test", inputs=[1])
            return outcome.run_id

    run_id = asyncio.run(go())
    began = time.perf_counter()
    document = explain_run(home, run_id)
    elapsed = (time.perf_counter() - began) * 1000
    nodes_seen = document["nodes"]
    count = len(nodes_seen) if isinstance(nodes_seen, list) else 0
    log.check(f"explain covers all {PERF_NODES} nodes", count == PERF_NODES, count)
    log(f"perf: explain of a {PERF_NODES}-node run took {elapsed:.1f} ms (not gated)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/engine/hg2")
    parser.add_argument("--trunk", default="origin/engine/ep8")
    parser.add_argument("--trunk-tree", type=Path, default=Path("D:/Temp/ep9-trunk"))
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    lanes: dict[str, Callable[[Log], None]] = {
        "regression": lambda log: regression(log, args.base, args.trunk, args.trunk_tree),
        "explain": explain_lane,
        "perf": perf,
    }
    failed = 0
    for name in args.lanes or list(lanes):
        log = Log("ep9", f"ep9-{name}")
        lanes[name](log)
        failed |= log.verdict()
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
