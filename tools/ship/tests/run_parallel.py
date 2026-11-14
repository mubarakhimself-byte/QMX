"""Run the kit's tests in parallel, one test class per job, and fail if any class fails.

    cd tools
    python ship/tests/run_parallel.py [--jobs N] [pattern ...]

Every test already builds its own temp repo, remote, program folder and factory home, so classes do not share
state and can run side by side. Each class runs as its own `python -m unittest <module>.<Class>`, so a failure or
a hang is reported with the class's whole output, never hidden: the summary counts every class, prints each failing
class's output in full, and the exit is 1 when any class failed, errored or ran past `--timeout`. The slowest
classes (the chaos scenarios and the conveyor's end-to-end runs) start first. `pattern` keeps only classes whose
`module.Class` name holds it. Standard library only.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2]
SLOW_FIRST = ("test_chain_chaos", "test_chain", "test_run", "test_claims", "test_review", "test_k4", "test_ci")
SUMMARY = re.compile(r"^Ran (\d+) tests? in ([\d.]+)s", re.M)
OUTCOME = re.compile(r"^(OK|FAILED)(?: \((.*)\))?\s*$", re.M)


def classes(patterns: list[str]) -> list[str]:
    """`ship.tests.<module>.<Class>` for every class holding at least one test."""
    sys.path.insert(0, str(TOOLS))
    suite = unittest.defaultTestLoader.discover(str(TOOLS / "ship" / "tests"), top_level_dir=str(TOOLS))
    found: dict[str, None] = {}

    def walk(item) -> None:
        if isinstance(item, unittest.TestSuite):
            for sub in item:
                walk(sub)
        elif isinstance(item, unittest.loader._FailedTest):  # an import error: run the module so it is reported
            found[item.id().rsplit(".", 1)[-1]] = None
        else:
            found[f"{type(item).__module__}.{type(item).__name__}"] = None

    walk(suite)
    names = [n for n in found if not patterns or any(p in n for p in patterns)]

    def rank(name: str) -> tuple[int, str]:
        module = name.split(".")[2] if name.count(".") >= 2 else name
        return (SLOW_FIRST.index(module) if module in SLOW_FIRST else len(SLOW_FIRST), name)

    return sorted(names, key=rank)


def run_one(name: str, timeout: float) -> dict:
    began = time.monotonic()
    try:
        done = subprocess.run([sys.executable, "-m", "unittest", name], cwd=TOOLS, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=timeout)
        out, rc = done.stdout + done.stderr, done.returncode
    except subprocess.TimeoutExpired as exc:
        out = f"{exc.stdout or ''}{exc.stderr or ''}\nTIMEOUT after {timeout:.0f}s"
        rc = -1
    ran = SUMMARY.search(out)
    outcome = OUTCOME.findall(out)
    return {"name": name, "rc": rc, "out": out, "tests": int(ran.group(1)) if ran else 0,
            "seconds": time.monotonic() - began, "detail": outcome[-1][1] if outcome else ""}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--jobs", type=int, default=min(4, max(1, (os.cpu_count() or 2) // 2)))
    parser.add_argument("--timeout", type=float, default=1800, help="seconds one class may take")
    parser.add_argument("patterns", nargs="*")
    args = parser.parse_args(argv)
    names = classes(args.patterns)
    began = time.monotonic()
    results = []
    print(f"{len(names)} test classes, {args.jobs} at a time", flush=True)
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_one, n, args.timeout) for n in names]
        for future in as_completed(futures):
            got = future.result()
            results.append(got)
            mark = "ok  " if got["rc"] == 0 else "FAIL"
            print(f"{mark} {got['name']}: {got['tests']} tests in {got['seconds']:.0f}s {got['detail']}".rstrip(),
                  flush=True)
    failed = [r for r in results if r["rc"] != 0]
    for got in failed:
        print(f"\n===== {got['name']} (exit {got['rc']}) =====\n{got['out']}")
    total = sum(r["tests"] for r in results)
    print(f"\n{total} tests in {len(results)} classes, {len(failed)} classes failed, "
          f"wall time {time.monotonic() - began:.0f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
