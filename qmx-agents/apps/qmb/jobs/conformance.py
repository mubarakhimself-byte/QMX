"""The `conformance` run kind: replay the core's pack and leave the raw rows (Part B AD-206).

The core hands the pack in the job's inputs: each case's request and the fixture dataset's
files. Each case is laid out under `cases/<case>/in/` and traded by this tester's own `backtest`
job. The leave is one `qmx.conformance.output/1` report of each case's raw trades, fills, cash
events and holes. It carries no measure, label or hash about itself: the core fingerprints the
rows and judges them against its goldens, because a tester never reports its own score.
"""

from __future__ import annotations

import json
import runpy
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import cast

import qmb_tester as tester

OUTPUT = "qmx.conformance.output/1"
PACK = "qmx.conformance.pack/1"
LISTS = ("trades", "fills", "cash_events", "holes")

type Job = Callable[[Mapping[str, object]], dict[str, object]]


def _lay_out(root: Path, request: Mapping[str, object], fixture: Mapping[str, str]) -> None:
    inside = (root / "in").resolve()
    for path, text in fixture.items():
        target = (inside / path).resolve()
        if not target.is_relative_to(inside):
            raise ValueError(f"the pack's file {path} lies outside the case folder")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, "utf-8", newline="")
    (inside / "request.json").write_text(json.dumps(dict(request)), "utf-8")


def _replay(backtest: Job, run_id: str, root: Path) -> dict[str, object]:
    left = backtest({"run_id": run_id, "run_folder": str(root)})
    bundle = cast("dict[str, object]", left["data"])
    if bundle["status"] != "finished":
        return {"status": "failed", "reason": bundle.get("reason")}
    report = cast(
        "dict[str, object]", json.loads((root / "out" / "report.json").read_text("utf-8"))
    )
    return {"status": "finished"} | {name: report[name] for name in LISTS}


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    pack = inputs.get("pack")
    if not isinstance(pack, dict) or cast("dict[str, object]", pack).get("schema_version") != PACK:
        return tester.failed(run_id, f"a conformance run carries the core's {PACK} pack")
    asked = cast("dict[str, object]", pack)
    fixture = cast("dict[str, str]", asked["files"])
    backtest = cast("Job", runpy.run_path(str(Path(__file__).with_name("backtest.py")))["run"])
    folder = tester.folder(inputs)
    cases: dict[str, object] = {}
    for case in cast("list[dict[str, object]]", asked["cases"]):
        name = str(case["case"])
        root = folder / "cases" / name
        _lay_out(root, cast("dict[str, object]", case["request"]), fixture)
        cases[name] = _replay(backtest, f"{run_id}/{name}", root)
    report = {"schema_version": OUTPUT, "pack": asked["id"], "cases": cases}
    return tester.leave(
        run_id,
        "finished",
        files=[tester.write(folder, "report.json", report)],
        versions={"qmb": tester.TESTER["version"]},
    )
