"""The `replay_check` run kind: replay a recorded live day and diff it decision by decision (QB-23).

The request names the ``day`` (``YYYY-MM-DD``, UTC) and carries the unit journal's ``live``
`signal` rows for it, as the node wrote them and the records job brought them home. The run's
window holds the bars the node recorded, from before the day so the unit warms up as it did
live. This tester's own `backtest` job replays the window, so the replay is the same compiled
unit through the same handler, and its `signal` rows are diffed against the live ones for the
day (`qmb.analysis.replay_diff`). The replay's journal travels with the result.
"""

from __future__ import annotations

import json
import runpy
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pyarrow.parquet as pq
from qmb.analysis.replay_diff import decision_diff

import qmb_tester as tester

type Job = Callable[[Mapping[str, object]], dict[str, object]]

_DAY_NS = 86_400 * 1_000_000_000
_SIGNAL = "journal/signal/"


def _rows(folder: Path, files: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for file in files:
        if str(file["slot"]).startswith(_SIGNAL):
            table = pq.read_table(folder / str(file["path"])).to_pylist()
            rows += [cast("dict[str, object]", json.loads(r["record"])["body"]) for r in table]
    return rows


def run(inputs: Mapping[str, object]) -> dict[str, object]:
    run_id = str(inputs["run_id"])
    folder = tester.folder(inputs)
    asked = tester.request(folder)
    if isinstance(asked, str):
        return tester.failed(run_id, asked)
    live, day = asked.get("live"), asked.get("day")
    try:
        start = int(datetime.fromisoformat(str(day)).replace(tzinfo=UTC).timestamp()) * 10**9
    except ValueError:
        return tester.failed(run_id, "a replay check names its day as YYYY-MM-DD")
    if not isinstance(live, list) or not all(
        isinstance(r, dict) for r in cast("list[object]", live)
    ):
        return tester.failed(run_id, "a replay check carries the live day's signal rows")
    backtest = cast("Job", runpy.run_path(str(Path(__file__).with_name("backtest.py")))["run"])
    replayed = cast("dict[str, object]", backtest(inputs)["data"])
    if replayed["status"] != "finished":
        return tester.failed(run_id, f"the replay: {replayed.get('reason')}")
    files = [
        f
        for f in cast("list[dict[str, object]]", replayed["files"])
        if str(f["slot"]).startswith("journal/")
    ]
    diff = decision_diff(
        cast("list[dict[str, object]]", live),
        _rows(folder, files),
        start_ns=start,
        end_ns=start + _DAY_NS,
    )
    found = diff.fields()
    return tester.leave(
        run_id,
        "finished",
        measures={"day": str(day), "matched": diff.matched, "differs": len(diff.decisions)},
        labels={"fidelity": "bars", "matches": not diff.decisions},
        files=[tester.write(folder, "report.json", {"day": str(day), **found}), *files],
        versions={"qmb": tester.TESTER["version"]},
    )
