"""The slow lane's doors, shared by its templates (Part B AD-213, Level 0 AD-31).

A read script loads this file by its path, because scripts run as `python -I`. It gives:

- `settings(given)`: the run's inputs with every card setting it left out taken from its `default`
  in `definition.json`, so a cron run, which brings no inputs, reads the card's numbers;
- `now()`: the run's own clock (`QMX_NOW`), never a field of the input;
- `day_window(day)`: a UTC day as a `journal_query` window, the day before the run's clock when
  `day` is left out;
- `journal(...)`: `journal_query`, the one door to the unit, market and node journals;
- `readings(...)`: `readings_query`, the one door to reading history, through the market-data
  door's holdout;
- `market_door(...)`: this machine's market-data door, for a read of its price series.

A script never opens the Library: the host holds its writer lock. So `readings` hands
`readings_query` this machine's QMX folder and a market-data door built from its `settings.toml`
`[data]`, as the `data-quality` block builds its door. The door's card names the holdout, so a
window that reaches a held-out month is refused by name and never answered empty; `readings`
returns that refusal as `refused`. Every page is answered inline, so no page spills to the
Library.
"""

import json
import os
import tomllib
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from qmf.core import is_refusal
from qmx_host.market_data import MarketDoor, Placement
from qmx_tools.functions import readings_functions
from qmx_tools.journals import journal_query

from qmx_engine.workers.zones import home_of

PAGE = 500


def home():
    return home_of(Path(os.environ["QMX_WORK_SHARED"]))


def settings(given):
    card = json.loads((Path(os.environ["QMX_CODE"]) / "definition.json").read_text("utf-8"))
    found = card.get("inputs", {}).get("properties", {})
    filled = {name: spec["default"] for name, spec in found.items() if "default" in spec}
    return filled | (given if isinstance(given, dict) else {})


def now():
    text = os.environ.get("QMX_NOW") or datetime.now(UTC).isoformat()
    moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return (moment if moment.tzinfo else moment.replace(tzinfo=UTC)).astimezone(UTC)


def iso(moment):
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def day_window(day=None):
    found = date.fromisoformat(str(day)) if day else now().date() - timedelta(days=1)
    start = datetime(found.year, found.month, found.day, tzinfo=UTC)
    return found.isoformat(), {"start": iso(start), "end": iso(start + timedelta(days=1))}


def journal(qmx_home, **ask):
    return journal_query(qmx_home, **ask)


def market_door(qmx_home):
    found = qmx_home / "settings.toml"
    stored = tomllib.loads(found.read_text("utf-8")) if found.is_file() else {}
    data = stored.get("data") if isinstance(stored.get("data"), dict) else {}
    root = Path(str(data.get("root") or qmx_home / "market"))
    opened = MarketDoor.open(root, data, placement=Placement(str(data.get("placement") or "pc")))
    if is_refusal(opened):
        raise ValueError(f"the market-data door did not open: {opened.context}")
    return opened.value


def readings(qmx_home, reading, window, markets=None, source=None):
    """Every row of one reading over `window`, page by page, or `{"refused": why}`."""

    def inline(value, name, response_format):
        return {"name": name, "result": value, "response_format": response_format}

    try:
        door = market_door(qmx_home)
        context = SimpleNamespace(root=qmx_home, market=door, output=inline)
        query = readings_functions(context)
        rows, cursor, answer = [], None, {}
        while True:
            answer = query(
                reading, window, markets=markets, source=source, limit=PAGE, cursor=cursor
            )
            rows += answer["result"]
            cursor = answer["next_cursor"]
            if cursor is None:
                break
    except ValueError as refused:
        return {"refused": str(refused)}
    kept = ("data_ends_at", "note", "holdout_from")
    return {"rows": rows, **{name: answer[name] for name in kept if name in answer}}
