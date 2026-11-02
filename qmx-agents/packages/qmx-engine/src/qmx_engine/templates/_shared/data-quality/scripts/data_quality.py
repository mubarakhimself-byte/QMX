"""The `data-quality` block's one step: a landed month counted against its market's calendar.

Its input is `{"in": {...}}` with `series` (the series key, `source/subject/kind/variant`),
`month` (`YYYY-MM`), `calendar` (a shipped calendar's ref, such as `fx-24x5@1`), and
optionally `confirmed_empty` (the hours, `YYYY-MM-DDTHH`, that a retry and a second source both
found empty), `gap_minutes` (the shortest run of missing open minutes listed as a gap, 5 by
default), `card` (the series' `dataset` card fields, whose clock and seams the report repeats)
and `root` (the market-data store; by default the door's own under the run's QMX folder).

It reads the month through the door's `materialise`, which verifies the copy, and prints the
report: the missing open minutes, each gap with its minutes, each empty open hour and whether it
is confirmed, each clock jump with its minutes, whether the month is frozen, and whether it
should be held open. An empty open hour is a fetch failure until a retry and a second source
agree (LD-01), so a month that holds one is named here while it stays unfrozen. A script
decides; no agent step reads the month.
"""

import json
import os
import sys
import tomllib
from pathlib import Path

from qmf.core import is_refusal
from qmf.data.importers.quality import (
    GAP_MINUTES,
    check_month,
    confirmed_hours,
    open_at_of,
    partition_stamps,
)
from qmf.data.series import SeriesKey
from qmx_host.market_data import MarketDoor, Placement

from qmx_engine.triggers.preflight import shipped_calendars
from qmx_engine.workers.zones import home_of

FAILURE = "[QMX_FAILURE]"


def fail(why: str) -> None:
    print(f"{FAILURE} {why}")
    raise SystemExit(0)


given = json.load(sys.stdin).get("in") or {}
given = next((v for v in (given if isinstance(given, list) else [given]) if "series" in v), None)
if not isinstance(given, dict):
    fail("the data-quality block needs a series, a month and its calendar")
series = str(given.get("series") or "")
month = str(given.get("month") or "")
calendar_ref = str(given.get("calendar") or "")
calendar = shipped_calendars().get(calendar_ref)
if calendar is None:
    fail(f"no shipped calendar is named {calendar_ref!r}")
confirmed = confirmed_hours(given.get("confirmed_empty") or [])
if isinstance(confirmed, str):
    fail(f"confirmed_empty: {confirmed}")
gap_minutes = given.get("gap_minutes", GAP_MINUTES)
if isinstance(gap_minutes, bool) or not isinstance(gap_minutes, int) or gap_minutes < 1:
    fail(f"gap_minutes is a whole number of minutes, not {gap_minutes!r}")
parts = series.split("/")
try:
    year, number = (int(part) for part in month.split("-"))
except ValueError:
    fail(f"the month {month!r} is not YYYY-MM")
if len(parts) != 4:
    fail(f"the series {series!r} is not source/subject/kind/variant")
source, subject, kind, variant = parts
key = SeriesKey.try_create(source, subject, kind, year, number, "" if variant == "-" else variant)
if is_refusal(key):
    fail(f"the partition key was refused: {key.context}")
if given.get("root"):
    root, data = Path(str(given["root"])), {}
else:
    home = home_of(Path(os.environ["QMX_WORK_SHARED"]))
    settings_file = home / "settings.toml"
    settings = tomllib.loads(settings_file.read_text("utf-8")) if settings_file.is_file() else {}
    data = settings.get("data") if isinstance(settings.get("data"), dict) else {}
    root = Path(str(data.get("root") or home / "market"))
opened = MarketDoor.open(root, data, placement=Placement(str(data.get("placement") or "pc")))
if is_refusal(opened):
    fail(f"the market-data door did not open: {opened.context}")
door = opened.value
state = door.series_store().state(key.value)
if state is None:
    fail(f"the door holds no month {key.value.text}")
copied = door.materialise(
    [state.fingerprint], into=Path(os.environ.get("QMX_WORK") or ".") / "quality"
)
if is_refusal(copied):
    fail(f"the month could not be read: {copied.context}")
report = check_month(
    partition_stamps(copied.value[0]),
    start_ms=key.value.start_ns // 1_000_000,
    end_ms=key.value.end_ns // 1_000_000,
    open_at=open_at_of(calendar),
    gap_minutes=gap_minutes,
    confirmed=confirmed,
)
copied.value[0].unlink(missing_ok=True)
card = given.get("card") if isinstance(given.get("card"), dict) else {}
print(
    json.dumps(
        {
            "series": series,
            "month": month,
            "calendar": calendar_ref,
            "frozen": state.frozen,
            "hold": report.hold,
            **report.as_json(),
            "source_clock": card.get("source_clock"),
            "seams": card.get("seams", []),
        },
        sort_keys=True,
    )
)
