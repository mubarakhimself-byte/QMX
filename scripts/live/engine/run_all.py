"""Rerun every engine check, unattended, and print one PASS or FAIL table (EP14).

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/run_all.py [--only NAME ...]`

Every `e*.py` and `x*.py` check in this folder runs as its own process, in plan order (EP2 to
EP14), each with all its lanes. A check passes when it exits 0. Each check's own lane logs are
written with the prefix `<ENGINE_LOG_PREFIX>run-all-`, so no other PR's evidence is overwritten,
and its console output goes to `evidence/ep14/<prefix>run-all-<check>.log`. The table lands in
`evidence/ep14/<ENGINE_LOG_PREFIX>ep14-run-all.log`.

The ship home's `settings.toml` is hashed before the run and after every check. If a check
changes it, that check fails and the run stops there. Checks that need a plan model take the lane
lock themselves (`common.plan_harness`), so this script never holds it.

Standard library only, so `test_run_all.py` runs it with any Python.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

HERE: Final = Path(__file__).resolve().parent
AGENTS: Final = HERE.parents[2] / "qmx-agents"
STORE: Final = Path("D:/QMX-worktrees/qma-ship/engine")
SHIP_SETTINGS: Final = Path("D:/QMX-worktrees/qma-ship/home/settings.toml")
CHECK_TIMEOUT_S: Final = 2700.0

PLAN_ORDER: Final = (
    "ep2_lanes",
    "x03_validate",
    "x04_ledger",
    "e01_determinism",
    "e02_replay",
    "e03_chunks",
    "x06_joins_loops",
    "x07_nodes",
    "e14_script_env",
    "e04_unknown_outcome",
    "x08_watchdog",
    "e11_ladder",
    "e12_inbox",
    "x09_explain",
    "e07_lifecycle",
    "e10_library",
    "e21_real_tests",
    "e09_roles",
    "x10_llm schema",
    "x10_llm cache",
    "x10_llm ask",
    "x10_llm doctor",
    "x10_llm perf",
    "x11_agent_chunks",
    "e05_pause",
    "e04b_agent_unknown",
    "e06_catchup",
    "x12_scheduler",
    "x13_doors",
    "x14_hello",
)
"""Each entry is a check's file stem and the arguments it runs with. `x10_llm` takes one mode per
process. A check file missing from this list still runs, after these, with no arguments."""


@dataclass(frozen=True, slots=True)
class Check:
    stem: str
    args: tuple[str, ...]

    @property
    def name(self) -> str:
        return " ".join((self.stem, *self.args))

    @property
    def slug(self) -> str:
        return "-".join((self.stem, *self.args))


@dataclass(frozen=True, slots=True)
class Result:
    check: Check
    verdict: str
    seconds: float
    evidence: tuple[Path, ...]


def checks(folder: Path) -> list[Check]:
    found = {p.stem for p in folder.glob("[ex]*.py")}
    planned = [Check(stem, tuple(args)) for stem, *args in (e.split() for e in PLAN_ORDER)]
    ordered = [c for c in planned if c.stem in found]
    known = {c.stem for c in planned}
    return ordered + [Check(stem, ()) for stem in sorted(found - known)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def child_env(prefix: str) -> dict[str, str]:
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("ANTHROPIC", "CLAUDE")) and name != "NODE_USE_SYSTEM_CA"
    }
    return env | {"ENGINE_LOG_PREFIX": prefix, "PYTHONIOENCODING": "utf-8"}


def written(evidence: Path, prefix: str, since: float) -> tuple[Path, ...]:
    """The lane logs a check wrote: files under `evidence` named with the run's prefix."""
    return tuple(
        sorted(
            p for p in evidence.rglob(f"{prefix}*") if p.is_file() and p.stat().st_mtime >= since
        )
    )


def run_one(
    check: Check, folder: Path, out: Path, evidence: Path, prefix: str, timeout: float
) -> Result:
    capture = out / f"{prefix}{check.slug}.log"
    began, wall = time.monotonic(), time.time() - 1
    command = [sys.executable, str(folder / f"{check.stem}.py"), *check.args]
    with capture.open("wb") as sink:
        process = subprocess.Popen(
            command,
            cwd=AGENTS if AGENTS.is_dir() else folder,
            env=child_env(prefix),
            stdout=sink,
            stderr=subprocess.STDOUT,
        )
        try:
            code = process.wait(timeout)
            verdict = "PASS" if code == 0 else f"FAIL exit {code}"
        except subprocess.TimeoutExpired:
            kill = ["taskkill", "/F", "/T", "/PID", str(process.pid)]
            subprocess.run(kill, capture_output=True, check=False)
            process.wait(30)
            verdict = f"FAIL timeout after {timeout:.0f} s"
    lanes = tuple(p for p in written(evidence, prefix, wall) if p != capture)
    return Result(check, verdict, time.monotonic() - began, (capture, *lanes))


def table(results: list[Result], skipped: list[Check]) -> list[str]:
    lines = [f"{'check':<24} {'verdict':<28} {'s':>7}  evidence"]
    for r in results:
        paths = [str(p) for p in r.evidence]
        lines.append(f"{r.check.name:<24} {r.verdict:<28} {r.seconds:>7.1f}  {paths[0]}")
        lines.extend(f"{'':<62}{p}" for p in paths[1:])
    lines.extend(f"{c.name:<24} {'FAIL not run':<28} {0:>7.1f}" for c in skipped)
    return lines


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(prog="run_all.py")
    cli.add_argument(
        "--checks", type=Path, default=HERE, help="the folder of e*.py and x*.py checks"
    )
    cli.add_argument("--evidence", type=Path, default=STORE / "evidence")
    cli.add_argument(
        "--guard", type=Path, default=SHIP_SETTINGS, help="the file no check may change"
    )
    cli.add_argument("--timeout", type=float, default=CHECK_TIMEOUT_S, help="seconds per check")
    cli.add_argument(
        "--only", nargs="*", default=None, help="check names to run, as the table prints them"
    )
    args = cli.parse_args(argv)
    out = args.evidence / "ep14"
    out.mkdir(parents=True, exist_ok=True)
    own = os.environ.get("ENGINE_LOG_PREFIX", "")
    prefix = f"{own}run-all-"
    todo = [c for c in checks(args.checks) if args.only is None or c.name in args.only]
    guarded = sha(args.guard)
    report = out / f"{own}ep14-run-all.log"
    began = time.monotonic()

    def say(line: str) -> None:
        print(line, flush=True)
        with report.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    report.write_text("", encoding="utf-8")
    say(f"run_all: {len(todo)} checks; guarding {args.guard} sha256 {guarded}")
    results: list[Result] = []
    for index, check in enumerate(todo):
        say(f"{time.strftime('%H:%M:%S')} running {check.name}")
        result = run_one(check, args.checks, out, args.evidence, prefix, args.timeout)
        now = sha(args.guard)
        if now != guarded:
            result = Result(
                check, f"FAIL changed {args.guard.name}", result.seconds, result.evidence
            )
        results.append(result)
        say(f"{time.strftime('%H:%M:%S')} {result.verdict} {check.name} in {result.seconds:.1f} s")
        if now != guarded:
            say(f"STOP: {check.name} changed {args.guard} (sha256 {now}); no further check runs")
            skipped = todo[index + 1 :]
            break
    else:
        skipped = []
    failed = [r.check.name for r in results if r.verdict != "PASS"] + [c.name for c in skipped]
    for line in table(results, skipped):
        say(line)
    passed = len(results) - len(failed) + len(skipped)
    say(f"{passed} PASS, {len(failed)} FAIL in {time.monotonic() - began:.0f} s")
    if failed:
        say(f"FAILED: {', '.join(failed)}")
    say(f"{args.guard.name} sha256 after: {sha(args.guard)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
