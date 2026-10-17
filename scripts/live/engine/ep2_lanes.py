"""EP2's live lanes and its perf probe, none of which needs a model.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/ep2_lanes.py [--base REV] [--base-tree DIR] [lane]`
Lanes are `regression e15 sync gates testmode clock cli secrets lock perf`; none named runs all.
`--base-tree` is a checkout of the harness base with its own synced venv. Each lane writes
`evidence/ep2/<ENGINE_LOG_PREFIX>ep2-<lane>.log` and the script exits 1 if any lane failed.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Final

from common import Log, throwaway_home

REPO: Final = Path(__file__).resolve().parents[3]
AGENTS: Final = REPO / "qmx-agents"
ENGINE: Final = AGENTS / "packages" / "qmx-engine"
HARNESS: Final = "qmx-agents/packages/qma-harness"
UV: Final = shutil.which("uv") or "uv"
GIT: Final = shutil.which("git") or "git"
SUITE_TIMEOUT_S: Final = 3600


def clean_env(**extra: str) -> dict[str, str]:
    env = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("ANTHROPIC", "CLAUDE")) and name != "NODE_USE_SYSTEM_CA"
    }
    return env | extra


def run(log: Log, command: list[str], cwd: Path, **extra: str) -> subprocess.CompletedProcess[str]:
    log(f"$ {' '.join(command)}  (in {cwd})")
    done = subprocess.run(
        command,
        cwd=cwd,
        env=clean_env(**extra),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=SUITE_TIMEOUT_S,
        check=False,
    )
    for line in (done.stdout + done.stderr).splitlines()[-25:]:
        log(f"  | {line}")
    log(f"  exit {done.returncode}")
    return done


def git(*args: str) -> str:
    return subprocess.run(
        [GIT, *args], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.strip()


def counts(output: str) -> dict[str, int]:
    summary = next(
        (line for line in reversed(output.splitlines()) if re.search(r"\d+ (passed|failed)", line)),
        "",
    )
    return {
        word: int(n) for n, word in re.findall(r"(\d+) (passed|failed|skipped|errors?)", summary)
    }


def regression(log: Log, base: str, base_tree: Path) -> None:
    diff = subprocess.run([GIT, "diff", "--quiet", base, "HEAD", "--", HARNESS], cwd=REPO)
    log.check("qma-harness byte-identical to the harness base", diff.returncode == 0, base)
    tree_head = subprocess.run(
        [GIT, "rev-parse", "HEAD"], cwd=base_tree, capture_output=True, text=True, check=True
    ).stdout.strip()
    log.check("base tree is checked out at the harness base", tree_head == base, tree_head)
    suite = [UV, "run", "--no-sync", "python", "-m", "pytest", "tests", "-q", "-n", "2"]
    suite += ["-p", "no:cacheprovider"]
    at_base = counts(run(log, suite, base_tree / HARNESS).stdout)
    at_head = counts(run(log, suite, REPO / HARNESS).stdout)
    log.check(
        "harness suite passes at base",
        at_base.get("passed", 0) > 0 and "failed" not in at_base,
        at_base,
    )
    log.check("harness suite pass counts match at head", at_head == at_base, at_head)


def planted(log: Log, slug: str, relative: str, text: str, names: list[str]) -> None:
    scratch = throwaway_home("ep2", slug) / "qmx-engine"
    shutil.copytree(ENGINE, scratch, ignore=shutil.ignore_patterns("__pycache__", ".*"))
    target = scratch / "src" / "qmx_engine" / relative
    target.write_text(target.read_text(encoding="utf-8") + text, encoding="utf-8")
    log(f"planted in {target}: {text.strip()!r}")
    rules = [sys.executable, "-m", "pytest", "tests/test_import_rules.py", "-q", "-n", "0"]
    rules += ["-p", "no:cacheprovider"]
    dirty = run(log, rules, scratch)
    shown = dirty.stdout + dirty.stderr
    log.check("the import rules fail on the planted copy", dirty.returncode == 1, dirty.returncode)
    for name in [f"qmx_engine/{relative}", *names]:
        log.check(f"the failure names {name}", name in shown, name in shown)
    clean = run(log, rules, ENGINE)
    log.check("the import rules pass on the clean head", clean.returncode == 0, clean.returncode)


def e15(log: Log) -> None:
    planted(
        log,
        "e15",
        "core/__init__.py",
        "from qma.harness.chat import Chat\n",
        ["qma.harness.chat.Chat"],
    )


def testmode(log: Log) -> None:
    text = "from qma.harness import TestMode\n_PROBE = TestMode()\n"
    planted(log, "testmode", "settings.py", text, [])


def clock(log: Log) -> None:
    planted(log, "clock", "core/__init__.py", "import time\n_NOW = time.time()\n", ["time.time"])


def sync(log: Log) -> None:
    venv = throwaway_home("ep2", "sync-venv")
    shutil.rmtree(venv)
    done = run(
        log,
        [UV, "sync", "--frozen", "--all-packages", "--all-groups"],
        AGENTS,
        UV_PROJECT_ENVIRONMENT=str(venv),
    )
    log.check(
        "uv sync --frozen --all-packages --all-groups on a clean venv", done.returncode == 0, venv
    )
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    imported = run(
        log,
        [str(python), "-c", "import qmx_engine, qmx_engine.settings; print(qmx_engine.__file__)"],
        AGENTS,
    )
    log.check(
        "import qmx_engine works in that venv", imported.returncode == 0, imported.stdout.strip()
    )


def gates(log: Log) -> None:
    for task in ("fmt-check", "lint", "types"):
        done = run(log, [UV, "run", "--no-sync", "python", "-m", "poethepoet", task], ENGINE)
        log.check(f"{task} in qmx-engine", done.returncode == 0, done.returncode)


def cli(log: Log) -> None:
    done = run(log, [sys.executable, "-m", "qmx_engine", "--help"], AGENTS)
    log.check("python -m qmx_engine --help exits 0", done.returncode == 0, done.returncode)
    log.check(
        "it prints the engine's usage",
        "usage: python -m qmx_engine" in done.stdout,
        done.stdout.splitlines()[:1],
    )


def secrets(log: Log) -> None:
    done = run(log, [UV, "run", "--no-sync", "python", "tools/secret_scan.py"], REPO)
    log.check("secret scan is clean", done.returncode == 0, done.returncode)


def lock(log: Log, base: str) -> None:
    diff = git("diff", base, "HEAD", "--", "qmx-agents/uv.lock").splitlines()
    removed = [line for line in diff if line.startswith("-") and not line.startswith("---")]
    added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
    names = [
        added[i + 1].split('"')[1]
        for i, line in enumerate(added[:-1])
        if line == "[[package]]" and added[i + 1].startswith("name = ")
    ]
    log(f"lines added {len(added)}, removed {len(removed)}")
    log.check("uv.lock removes nothing", removed == [], removed[:5])
    log.check(
        "uv.lock adds only qmx-engine and EP12's cron library",
        names in (["qmx-engine"], ["cronsim", "qmx-engine"]),
        names,
    )


def perf(log: Log) -> None:
    done = run(log, [sys.executable, "-X", "importtime", "-c", "import qmx_engine"], AGENTS)
    row = next(
        (line for line in done.stderr.splitlines() if line.rstrip().endswith("| qmx_engine")), ""
    )
    log(f"importtime row: {row.strip()}")
    cumulative_us = int(row.split("|")[1]) if row else -1
    log.check(
        "import time of qmx_engine recorded (not gated)",
        cumulative_us >= 0,
        f"{cumulative_us / 1000:.2f} ms cumulative",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/engine/hg2")
    parser.add_argument("--base-tree", type=Path, default=Path("D:/QMX-worktrees/eng-hg2"))
    parser.add_argument("lanes", nargs="*")
    args = parser.parse_args()
    base = git("rev-parse", args.base)
    lanes: dict[str, Callable[[Log], None]] = {
        "regression": lambda log: regression(log, base, args.base_tree),
        "e15": e15,
        "sync": sync,
        "gates": gates,
        "testmode": testmode,
        "clock": clock,
        "cli": cli,
        "secrets": secrets,
        "lock": lambda log: lock(log, base),
        "perf": perf,
    }
    failed: list[str] = []
    for name in args.lanes or list(lanes):
        log = Log("ep2", f"ep2-{name}")
        log(f"lane {name} at head {git('rev-parse', 'HEAD')}, harness base {base}")
        lanes[name](log)
        if log.verdict():
            failed.append(name)
    print(f"failed lanes: {failed}" if failed else "all lanes passed", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
