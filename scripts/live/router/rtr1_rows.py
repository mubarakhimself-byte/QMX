"""RTR1 rows: the bundled registry, read and tested one row at a time.

    rtr1_rows.py list                 every provider and row, and ten load times in ms
    rtr1_rows.py plan <home>          Test claude/haiku through <home>/claude; caller holds the
                                      lane lock D:/QMX-worktrees/.engine-lane-lock
    rtr1_rows.py test <qmx_id>...     Test key rows; a row whose key is missing spends nothing
    rtr1_rows.py override <dir>       a user kimi.toml in <dir> overrides one field

Each line it prints is the log. Keys are read from the keyring by reference inside the router and
never printed. Exit 1 on any FAIL.
"""

from __future__ import annotations

import asyncio
import hashlib
import sys
import time
from pathlib import Path
from typing import Final

from qmx_router.registry import (
    RowTestResult,
    bundled,
    load,
    one_token_test,
    plan_test,
)

LANE_LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
FAILS: list[str] = []


def log(line: str) -> None:
    print(line, flush=True)


def verdict(ok: bool, line: str) -> None:
    if not ok:
        FAILS.append(line)
    log(f"{'PASS' if ok else 'FAIL'} {line}")


def show(result: RowTestResult) -> None:
    log(
        f"  {result.qmx_id}: {result.status} spent={result.spent} "
        f"output_tokens={result.output_tokens} ms={result.ms} {result.detail}"
    )


def list_rows() -> None:
    loads: list[float] = []
    for _ in range(10):
        started = time.perf_counter()
        registry = load(None)
        loads.append((time.perf_counter() - started) * 1000)
    for provider in registry.providers.values():
        log(f"{provider.name} kind={provider.kind} use={provider.use} url={provider.url or '-'}")
        for row in provider.models:
            log(
                f"  {row.qmx_id} native={row.native} wire={row.wire} window={row.window} "
                f"max_output={row.max_output} class={row.class_} tool_search={row.tool_search}"
            )
    log(f"perf registry load ms: {', '.join(f'{ms:.1f}' for ms in loads)}")
    verdict(not registry.errors, f"{len(registry.rows())} rows, errors {dict(registry.errors)}")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan(home: Path) -> None:
    if not LANE_LOCK.is_dir():
        raise SystemExit(f"BLOCKED: hold the lane lock {LANE_LOCK} first")
    settings = home / "settings.toml"
    before = sha(settings)
    log(f"settings.toml sha256 before {before}")
    cwd = home.parent / "build" / "homes" / "rtr1-plan"
    cwd.mkdir(parents=True, exist_ok=True)
    result = asyncio.run(
        one_token_test(bundled(), "claude/haiku", plan_turn=plan_test(home / "claude", cwd))
    )
    show(result)
    after = sha(settings)
    log(f"settings.toml sha256 after  {after}")
    verdict(result.status == "ok", "plan row claude/haiku answered")
    verdict(before == after, "ship home settings.toml unchanged")


def test(ids: list[str]) -> None:
    for qmx_id in ids:
        result = asyncio.run(one_token_test(bundled(), qmx_id))
        show(result)
        if result.status == "no_key":
            verdict(not result.spent, f"{qmx_id} names its missing key and spends nothing")
        else:
            verdict(result.status == "ok", f"{qmx_id} answered")


def override(folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "kimi.toml").write_text(
        '[[models]]\nqmx_id = "kimi/k3"\nmax_output = 12_345\n', encoding="utf-8"
    )
    row = load(folder).model("kimi/k3")
    log(f"  kimi/k3 max_output={row.max_output} window={row.window} class={row.class_}")
    verdict(row.max_output == 12_345, "the user value shows on the row")
    verdict(row.window == 1_000_000, "the bundled values it does not name stay")


def main(argv: list[str]) -> int:
    match argv:
        case ["list"]:
            list_rows()
        case ["plan", home]:
            plan(Path(home))
        case ["test", *ids] if ids:
            test(ids)
        case ["override", folder]:
            override(Path(folder))
        case _:
            raise SystemExit(__doc__)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
