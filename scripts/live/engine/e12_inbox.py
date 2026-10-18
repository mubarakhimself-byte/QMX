"""EP8 lanes 3 (E12) and 4: what reaches the inbox, read back from the real inbox table.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e12_inbox.py [provider|logic]`
None named runs both.

- `provider` (E12) writes `ep8-e12.log`: a node fails five times with one provider signature
  (`auth`, a 401), over one run and four operator resumes. The failing executor is a planted
  in-process stub: a real 401 needs a provider call, and the inbox only reads the failure.
- `logic` (lane 4) writes `ep8-logic-park.log`: `python -m qmx_engine run` on a folder whose script
  fails its own check as a real subprocess. The run parks; the cause is read from the ledger's park
  step, which is what `explain` will print once EP9 adds it; the inbox stays empty.

No model, no key, no ship home.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Final

from common import Log, throwaway_home
from qmx_engine.ledger.inbox_table import InboxTable, inbox_path
from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Ledger
from qmx_engine.nodes.base import Failed, NodeJob, NodeResult
from qmx_engine.ports.inbox import Item
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS
from x07_nodes import cli, edge, events, node, run_id_of, runnable, write_folder

MESSAGE: Final = "provider answered 401 Unauthorized"
CHECK: Final = """
    import json, sys
    rows = json.load(sys.stdin)["in"] or [3, 4]
    if sum(rows) != 8:
        sys.exit(f"the totals do not add up: {sum(rows)} != 8")
"""


class Unauthorized:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, job: NodeJob) -> NodeResult:
        self.calls += 1
        return Failed("auth", MESSAGE, signature("auth", MESSAGE), retryable=False)


def items(home: Path) -> list[Item]:
    if not inbox_path(home).exists():
        return []
    with InboxTable.open(home) as inbox:
        return inbox.list_items(open_only=False)


def provider(log: Log) -> None:
    home = throwaway_home("ep8", "e12")
    root = write_folder(
        home / "wf-provider",
        [node("start", "trigger"), node("call", "script", script="scripts/call.py")],
        {"start": {"main": [edge("call")]}},
        {"call": "print(1)\n"},
    )
    definition = runnable(root)
    stub = Unauthorized()

    async def go(run_id: str | None) -> Outcome:
        with Ledger.open(home) as ledger:
            engine = Engine(home, ledger, settings=DEFAULTS, executors={"script": stub})
            if run_id is None:
                return await engine.start(root, definition, mode="test", inputs=None)
            return await engine.resume(run_id)

    first = asyncio.run(go(None))
    log(f"run {first.run_id} {first.status}: {first.reason}")
    for n in range(4):
        again = asyncio.run(go(first.run_id))
        log(f"operator resume {n + 1}: {again.status}: {again.reason}")
    failures = [e for e in events(home, first.run_id) if e.kind == "node_failed"]
    found = items(home)
    for item in found:
        log(f"item {item.id} {item.category} {item.severity} count {item.count}: {item.title}")
    log.check("five failures of one provider signature", len(failures) == 5, len(failures))
    log.check("exactly one inbox item", len(found) == 1, len(found))
    log.check(
        "the item has count 5 and category provider_failure",
        [(i.count, i.category.value) for i in found] == [(5, "provider_failure")],
        [(i.count, i.category.value) for i in found],
    )


def logic(log: Log) -> None:
    home = throwaway_home("ep8", "logic-park")
    check = node("check", "script", script="scripts/check.py")
    check["retry"] = {"max_tries": 3, "backoff_seconds": [0, 0]}
    root = write_folder(
        home / "wf-logic",
        [node("start", "trigger"), check],
        {"start": {"main": [edge("check")]}},
        {"check": CHECK},
    )
    code, lines = cli(log, "run", str(root), "--home", str(home))
    found = events(home, run_id_of(lines))
    ladder = [e.data for e in found if e.kind == "ladder_step"]
    park = ladder[-1] if ladder else {}
    log(f"ladder: {' '.join(str(s['step']) for s in ladder)}")
    log(f"park step (what explain reads): {park}")
    inbox = items(home)
    log.check("the run is failed (parked)", code == 1 and "run failed:" in lines[-1], lines[-1:])
    log.check(
        "the park names the node and the script's own error",
        park.get("step") == "park"
        and "node check failed: script_exit" in str(park.get("reason"))
        and "the totals do not add up" in str(park.get("reason")),
        park.get("reason"),
    )
    log.check("no inbox item exists", inbox == [], inbox)


LANES: Final[dict[str, tuple[str, Callable[[Log], None]]]] = {
    "provider": ("ep8-e12", provider),
    "logic": ("ep8-logic-park", logic),
}


def main() -> int:
    chosen = sys.argv[1:] or list(LANES)
    failed = 0
    for name in chosen:
        slug, lane = LANES[name]
        log = Log("ep8", slug)
        lane(log)
        failed |= log.verdict()
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
