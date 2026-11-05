"""B9 lanes 2 to 4: the phase-0 chain on one fresh throwaway QMX folder.

Usage, from <worktree>/qmx-agents:
    python owner-phase0.py <fresh folder under D:/Temp> <evidence folder> <bars folder>

Lane 2 (owner-b9-author.log): the first start's dummy draft passes `python -m qmx_tools.unit_check`
with zero errors and publishes as principal `operator`. Lane 3 (owner-b9-backtest.log): the
copilot's `backtest_run` row backtests the published dummy on EURUSD and XAUUSD over January to
March 2025 and lands a `backtest-result` with trades in money and R, a core run id and its try
rows. Lane 4 (owner-b9-motion.log): a script reads that result's `journal/*` blobs, counts at
least 20 closed trades on each market, finds the `calibration` row that moved
`min_trend_strength` with its old value, new value and receipt, and says what the dummy did on
one named day and why it skipped. Every check prints one PASS or FAIL line; the exit code is 1
on any FAIL.
"""

# pyright: basic

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import threading
import time
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as pq
from qmx_control.service import ControlService, WorkflowEngine
from qmx_engine.ledger import redact
from qmx_host.first_start import land_dummy
from qmx_host.host import landers, register_checkers
from qmx_library.principal import MAIN, Principal, drafts_ref
from qmx_library.store import Store
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

FOLDER, EVIDENCE, BARS = (Path(a).resolve() for a in sys.argv[1:4])
assert FOLDER.as_posix().startswith("D:/Temp/"), FOLDER
assert not FOLDER.exists(), f"{FOLDER} must be fresh"
APP = Path.cwd() / "apps" / "qmb"
OPERATOR = Principal("operator")
WINDOW = {"start": "2025-01-01", "end": "2025-04-01"}
DAY = "2025-02-12"
"""The named day, chosen before the run: a Wednesday in the middle of the window."""
CHAT = "agent:phase0"
MIN_COUNT = 20
failed = 0


class Log:
    def __init__(self, name: str) -> None:
        self.path = EVIDENCE / name
        self.lines: list[str] = []

    def say(self, line: str) -> None:
        print(line)
        self.lines.append(line)

    def check(self, ok: bool, what: str) -> bool:
        global failed
        failed += not ok
        self.say(f"{'PASS' if ok else 'FAIL'} {what}")
        return ok

    def save(self) -> None:
        self.path.write_text("\n".join(self.lines) + "\n", "utf-8")


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 11, 2, 9, 30, tzinfo=UTC)
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            self.now += timedelta(seconds=1)
            return self.now


@dataclass(frozen=True)
class Caller:
    principal: str


class Chat:
    def principal(self) -> Caller:
        return Caller(CHAT)

    def workflow_runs_list(self, workflow_id: str | None) -> list[dict[str, Any]]:
        return []


def stamp(ns: int) -> str:
    return datetime.fromtimestamp(ns / 1e9, tz=UTC).strftime("%Y-%m-%d %H:%M")


def journal_rows(store: Store, result_id: str) -> dict[str, list[dict[str, Any]]]:
    """Every journal blob of the result, parsed: kind -> envelope records, months in order."""
    view = store.get(OPERATOR, result_id)
    rows: dict[str, list[dict[str, Any]]] = {}
    for slot in sorted(s for s in view.blobs if s.startswith("journal/")):
        kind = slot.split("/")[1]
        data = store.read_blob(view.blobs[slot].blob_id)
        table = pq.read_table(io.BytesIO(data)).to_pylist()
        rows.setdefault(kind, []).extend(json.loads(r["record"]) for r in table)
    return rows


FOLDER.mkdir(parents=True)
bars = FOLDER / "bars"
bars.mkdir()
for source in BARS.glob("*-m15-*-2025-01-01-2025-04-01.csv"):
    shutil.copyfile(source, bars / source.name)

author, backtest, motion = Log("owner-b9-author.log"), Log("owner-b9-backtest.log"), Log(
    "owner-b9-motion.log"
)
control = ControlService(FOLDER / "home")
control.settings_put("qmb", {"bars": str(bars)})
control.attach_workflow_engine(cast(WorkflowEngine, Chat()))
with Store.open(FOLDER / "library", redactor=redact, wall=Clock()) as store:
    try:
        register_checkers(store)
        control.attach_library(store)
        runtime = control.app_runtime()
        runtime.attach_landers(
            landers(store, runtime, "pc", settings=lambda: control.settings_get("qmb"))
        )
        started = time.monotonic()
        runtime.install(APP, trust="first_party")
        runtime.start("qmb")
        backtest.say(f"QMB installed and started in {time.monotonic() - started:.1f} s")

        # Lane 2. The authoring door.
        draft_id = land_dummy(store)
        author.check(draft_id is not None, f"the first start landed the dummy draft {draft_id}")
        draft = store.get(OPERATOR, cast(str, draft_id))
        document = FOLDER / "dummy.json"
        document.write_text(json.dumps(draft.fields), "utf-8")
        ran = subprocess.run(
            [sys.executable, "-m", "qmx_tools.unit_check", str(document)],
            capture_output=True,
            text=True,
            check=False,
            timeout=600,
        )
        verdict = json.loads(ran.stdout.strip().splitlines()[-1])
        author.say(f"unit_check exit {ran.returncode}: verdict {verdict['verdict']}, counts {verdict['counts']}")
        author.check(
            ran.returncode == 0 and verdict["counts"]["errors"] == 0,
            "python -m qmx_tools.unit_check finds zero errors in the dummy draft",
        )
        item = draft.item
        merged = store.merge(OPERATOR, item, from_ref=drafts_ref(item), into=MAIN)
        head = store.head(item, MAIN)
        author.say(f"publish as operator: {merged.outcome}, main head {head}")
        author.check(head is not None and head[0] == draft_id, "the dummy publishes as operator")

        # Lane 3. The backtest through the copilot's row.
        context = DomainContext(root=FOLDER / "tools")
        context.control, context.library = control, control.library
        row = domain_functions(context)["backtest"]["backtest_run"]
        started = time.monotonic()
        answer = row(unit=cast(str, draft_id), window=WINDOW)["result"]
        seconds = time.monotonic() - started
        backtest.say(f"backtest_run answered in {seconds:.1f} s: {json.dumps(answer)}")
        run_id, result_id = answer.get("run_id"), answer.get("result_id")
        backtest.check(answer.get("status") == "finished", "the run finished within the wait")
        backtest.check(
            isinstance(run_id, str) and run_id.startswith("qmbr-pc-"),
            f"the core run id is {run_id}",
        )
        landed = dict(store.get(OPERATOR, cast(str, result_id)).fields)
        backtest.say(f"result {result_id}: measures {json.dumps(landed.get('measures'))}")
        backtest.check(
            landed.get("status") == "finished" and landed.get("principal") == CHAT,
            "a finished backtest-result landed, run by the chat",
        )
        view = store.get(OPERATOR, cast(str, result_id))
        report = json.loads(store.read_blob(view.blobs["report"].blob_id))
        trades = report["trades"]
        backtest.check(
            bool(trades)
            and sum(Decimal(t["money"]) for t in trades) == Decimal(landed["measures"]["net_money"])
            and sum(Decimal(t["r"]) for t in trades) == Decimal(landed["measures"]["total_r"]),
            f"{len(trades)} trades in money and R add up to the measures",
        )
        tries = sorted(
            (str(store.get(OPERATOR, i).fields["kind"]), str(store.get(OPERATOR, i).fields["state"]))
            for i in store.with_field("try", "run_id", cast(str, run_id))
        )
        backtest.check(tries == [("run", "landed"), ("run", "opened")], f"its try rows {tries}")
        checks = [
            dict(store.get(OPERATOR, i).fields)
            for i in store.with_field("test-report", "check", "qml-g/1")
        ]
        backtest.check(
            len(checks) == 1 and checks[0]["safety"]["verdict"] == "pass",
            "the unit was checked first: one qml-g/1 test-report with a passing safety verdict",
        )
        slots = sorted(s for s in view.blobs if s.startswith("journal/"))
        backtest.say(f"journal blobs: {slots}")
        backtest.check(bool(slots), "the result holds its journal/* blobs")
        backtest.say(f"report journal summary: {json.dumps(report['journal'])}")

        # Lane 4. The number that moved, read from the result's journal blobs.
        rows = journal_rows(store, cast(str, result_id))
        motion.say(f"rows by kind: {dict(sorted((k, len(v)) for k, v in rows.items()))}")
        closed = Counter(r["market_id"] for r in rows.get("trade", []))
        motion.check(
            min(closed.get(m, 0) for m in ("fx.eurusd", "metal.xauusd")) >= MIN_COUNT,
            f"at least {MIN_COUNT} closed trades on each market: {dict(closed)}",
        )
        moves = [
            r["body"]
            for r in rows.get("calibration", [])
            if r["body"]["number"] == "min_trend_strength" and r["body"]["old"] != r["body"]["new"]
        ]
        for move in moves:
            motion.say(
                f"calibration min_trend_strength {move['old']} -> {move['new']} at "
                f"{stamp(move['watermark'])}, rule {move['rule']}, read {move['read_trades']}, "
                f"statistic {move['statistic']}"
            )
        motion.check(
            bool(moves) and all(m["read_trades"]["count"] >= MIN_COUNT for m in moves),
            "a calibration row moved min_trend_strength with its old value, new value and receipt",
        )
        signals = rows.get("signal", [])
        bare = Counter(
            r["body"]["detail"].split(" after ")[0]
            for r in signals
            if not r["body"]["readings_used"]
        )
        motion.say(f"signal rows with no readings, by reason text: {dict(bare)}")
        complete = all(
            all({"reading", "version", "value", "source"} <= set(x) for x in r["body"]["readings_used"])
            for r in signals
        )
        motion.check(
            complete and set(bare) <= {"time exit"},
            f"each of {len(signals)} signal rows carries reading, version, value and source for "
            "every reading in its slot trail; only time exits, which have no slot trail, carry none",
        )

        day = [r for r in signals if stamp(r["body"]["instant"]).startswith(DAY)]
        motion.say(f"what the dummy did on {DAY} (UTC), from the journal alone:")
        for r in sorted(day, key=lambda r: (r["body"]["instant"], r["market_id"])):
            b = r["body"]
            level = "rsi_low" if b["side"] == "long" else "rsi_high"
            motion.say(
                f"  {stamp(b['instant'])} {b['market_id']} {b['side']}: {b['outcome']}"
                f"{' (' + b['reason'] + ')' if 'reason' in b else ''}, {b['detail']}; "
                f"{level} {b['numbers_in_force'].get(level)}, "
                f"min_trend_strength {b['numbers_in_force'].get('min_trend_strength')}"
            )
        for r in rows.get("trade", []):
            b = r["body"]
            if stamp(b["closed_at"]).startswith(DAY) or stamp(b["opened_at"]).startswith(DAY):
                motion.say(
                    f"  trade {b['trade_id']} {r['market_id']} {b['side']} opened "
                    f"{stamp(b['opened_at'])} closed {stamp(b['closed_at'])} by {b['exit_kind']}: "
                    f"{b['money']} money, {b['r']} R"
                )
        skipped = [r for r in day if r["body"]["outcome"] != "taken"]
        motion.check(
            bool(day) and all("reason" in r["body"] or r["body"]["outcome"] == "taken" for r in day),
            f"{len(day)} decisions on {DAY}, {len(skipped)} not taken, each with its reason code",
        )
    finally:
        control.close()
        for log in (author, backtest, motion):
            log.save()
sys.exit(1 if failed else 0)
