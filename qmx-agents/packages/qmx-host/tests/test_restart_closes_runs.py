"""A host restart closes the runs it left open, before any app can run a leftover request.

Nothing waits for a run once its host has gone, so at the next start each `opened` try this machine
left with no close fails with the words "host restarted", and its queued request goes. The lander
and the store are real. No app starts, because the fail comes before the apps do.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from qmx_apps.supervisor import JOB_QUEUE
from qmx_apps.volume import Volume
from qmx_engine.ledger import redact
from qmx_judge.landing import RESULT_KIND, Lander
from qmx_judge.tries import TRY_KIND, try_item
from qmx_library.principal import MAIN, Principal
from qmx_library.store import Store

from qmx_host.first_start import land_dummy
from qmx_host.host import LanderLibrary, QmbRun, fail_stranded_runs

OPERATOR = Principal("operator")
WINDOW = {"start": "2025-03-01", "end": "2025-04-01"}


def a_run(home: Path, store: Store, machine: str) -> QmbRun:
    library = LanderLibrary(store)
    lander = Lander(
        library,
        writer="operator",
        machine=machine,
        provides_of=lambda _app, _version: {RESULT_KIND},
        clock=lambda: datetime(2026, 11, 6, 9, 0, tzinfo=UTC),
        family_of=library.family_of,
    )
    return QmbRun(
        lander,
        library,
        lambda app, run_id: Volume(home, app).root / "data" / "runs" / run_id,
        dict,
        home / "market",
        cast("object", None),  # pyright: ignore[reportArgumentType]
    )


def queued(home: Path, name: str, run_id: str) -> Path:
    queue = Volume(home, "qmb").root / JOB_QUEUE
    queue.mkdir(parents=True, exist_ok=True)
    request = queue / f"{name}.request.json"
    request.write_text(
        json.dumps({"job": "jobs/backtest.py", "inputs": {"run_id": run_id}}), "utf-8"
    )
    return request


def test_an_opened_try_with_no_close_fails_at_host_start(tmp_path: Path) -> None:
    home = tmp_path / "home"
    with Store.open(tmp_path / "library", redactor=redact) as store:
        unit = land_dummy(store)
        assert unit is not None
        inputs = {"unit": unit, "window": WINDOW}
        run = a_run(home, store, "pc")
        left = run.lander.open("qmb", "1.0.0", "jobs/backtest.py", inputs, "agent:chat")
        check = run.lander.open("qmb", "1.0.0", "jobs/behaviour_check.py", inputs, "agent:chat")
        done = run.lander.open("qmb", "1.0.0", "jobs/backtest.py", inputs, "agent:chat")
        elsewhere = a_run(home, store, "pc-2").lander.open(
            "qmb", "1.0.0", "jobs/backtest.py", inputs, "agent:chat"
        )
        assert left and check and done and elsewhere
        run.lander.fail(done, "already over", status="failed")
        laid = Volume(home, "qmb").root / "data" / "runs" / left.run_id / "in"
        (laid / "bars" / "fx.eurusd").mkdir(parents=True)
        (laid / "bars" / "fx.eurusd" / "bid.csv").write_text("timestamp\n", "utf-8")
        (laid / "request.json").write_text(json.dumps({"window": WINDOW, "kind": "backtest"}))
        own, other = queued(home, "1", left.run_id), queued(home, "2", elsewhere.run_id)

        stranded = fail_stranded_runs(home, run)
        tries = len(store.with_field(TRY_KIND, "kind", "run"))
        again = fail_stranded_runs(home, run)

        closing = store.head(try_item(left.run_id, "failed"), MAIN)
        assert closing is not None
        row = store.get(OPERATOR, closing[0]).fields
        result = store.get(OPERATOR, str(cast("list[str]", row["links"])[1])).fields
        assert sorted(stranded) == sorted([left.run_id, check.run_id])
        assert row["state"] == "failed"
        assert (result["status"], result["reason"], result["kind"]) == (
            "failed",
            "host restarted",
            "backtest",
        )
        assert result["window"] == WINDOW
        report = store.head(check.run_id, MAIN)
        assert report is not None
        checked = store.get(OPERATOR, report[0]).fields
        assert (checked["status"], checked["behaviour"]) == (
            "failed",
            {"reason": "host restarted"},
        )
        assert (own.exists(), other.exists()) == (False, True)
        assert not (laid / "bars").exists()
        assert store.head(try_item(elsewhere.run_id, "failed"), MAIN) is None
        assert again == []
        assert len(store.with_field(TRY_KIND, "kind", "run")) == tries
