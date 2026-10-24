"""Build the dataset from the partitions the door materialises (Lab AD-20, Lib AD-28).

The step names the series and the months it trains on. The door answers `card(series)` with each
month's fingerprint and size and `materialise(fingerprints)` copies **exactly** those partitions
into this attempt's own folder, verifying every hash on the way; a month outside the split is
refused by the door in its own words, and a sealed month never lands in a shared cache. The step
reads no cache path and no folder of its own, so what it trains on is what the door served.

Its output is the scope (slot, label, horizon, features), the partitions it read with their
fingerprints, the split windows with the purge and embargo between them, the rows, the digest of
the code that read them and the seed. That is the data lineage Lab AD-20 records on the model
item, and it is written here, by the template, so no model chooses it.
"""

import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

from qmf.core import is_refusal
from qmx_host.market_data import MarketDoor, Placement

from qmx_engine.workers.zones import home_of

FAILURE = "[QMX_FAILURE]"
DEFAULT_PURGE_BARS = 5
DEFAULT_EMBARGO_BARS = 5
DEFAULT_HORIZON_BARS = 1
DEFAULT_SEED = 7
SHA_BYTES = 1 << 20


def fail(why):
    """A step that cannot answer says why and stops; it never guesses a dataset."""
    sys.stderr.write(f"{FAILURE} {why}")
    raise SystemExit(1)


def ask(given):
    """The training ask the inputs name: the first row carrying a series and its months."""
    for value in given if isinstance(given, list) else [given]:
        if isinstance(value, dict) and value.get("series") and value.get("months"):
            return value
    return {}


def series_of(row):
    """The series key, or the four parts a dataset card carries instead."""
    if row.get("series"):
        return str(row["series"])
    parts = ("source", "subject", "kind", "variant")
    if all(row.get(part) for part in parts[:3]):
        variant = str(row.get("variant") or "-")
        return f"{row['source']}/{row['subject']}/{row['kind']}/{variant}"
    return ""


def code_digest(folder):
    """The digest of the code that read the data: every file of the template folder, by name."""
    digest = hashlib.sha256()
    for path in sorted(Path(folder).rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(path.relative_to(folder).as_posix().encode())
            digest.update(path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def partitions(door, series, months, into):
    """The partitions the door materialises for these months, read in its own order.

    Answers `(rows, paths)`: one row per month with its fingerprint and size, and the local file the
    door copied it to. A month the series does not hold, or one the door refuses, stops the step."""
    answered = door.card(series)
    if is_refusal(answered):
        return None, answered.context
    held = {str(row["month"]): row for row in answered.value.get("partitions") or []}
    asked = []
    for month in months:
        found = held.get(str(month))
        if found is None:
            return None, f"{series} holds no partition for {month}; the run asked for {months}"
        asked.append(found)
    landed = door.materialise([str(row["fingerprint"]) for row in asked], into=into)
    if is_refusal(landed):
        return None, landed.context
    rows = [
        {
            "month": str(row["month"]),
            "fingerprint": str(row["fingerprint"]),
            "bytes": int(row.get("bytes") or 0),
            "path": str(path),
        }
        for row, path in zip(asked, landed.value, strict=True)
    ]
    return rows, ""


def read_ticks(paths):
    """The ticks of every materialised partition as `(timestamp, bid, ask)` columns."""
    import pyarrow.parquet as pq  # noqa: PLC0415 (the writer is the door's, not this step's)

    columns = {"t": [], "bid": [], "ask": []}
    for path in paths:
        table = pq.read_table(path, columns=["t", "bid", "ask"])
        for name, found in columns.items():
            found.extend(table.column(name).to_pylist())
    return columns


def scored(columns, seed, epochs=200):
    """Chance and shuffled-label scores of the smallest model that could learn anything here.

    A logistic fit on the lagged mid-price changes (`chance`) and the same fit on shuffled labels
    (`shuffle`): a shuffle that scores within the tolerance of chance means the features carry no
    forward information, and one that beats it means the split leaks. numpy only, so the check
    costs nothing and needs no framework."""
    import numpy as np  # noqa: PLC0415 (numpy is the probe's only framework here)

    mid = (np.asarray(columns["bid"], dtype=np.float64) + np.asarray(columns["ask"])) / 2.0
    move = np.diff(mid)
    window = len(move) - DEFAULT_HORIZON_BARS
    features = np.stack(
        [move[lag : lag + window] for lag in range(DEFAULT_HORIZON_BARS + 5)], axis=1
    )
    labels = (move[DEFAULT_HORIZON_BARS:] > 0).astype(np.float64)
    chance = max(float(labels.mean()), 1.0 - float(labels.mean()))
    rng = np.random.default_rng(seed)
    shuffled = labels.copy()
    rng.shuffle(shuffled)
    return round(learn(features, shuffled, epochs), 4), round(chance, 4)


def learn(features, labels, epochs):
    """One logistic fit by plain gradient descent, answered as its training accuracy."""
    import numpy as np  # noqa: PLC0415 (numpy is the probe's only framework here)

    weights = np.zeros(features.shape[1])
    bias = 0.0
    for _ in range(epochs):
        logits = features @ weights + bias
        seen = 1.0 / (1.0 + np.exp(-logits))
        error = seen - labels
        weights -= 0.1 * (features.T @ error) / len(labels)
        bias -= 0.1 * float(error.mean())
    guessed = (features @ weights + bias > 0).astype(np.float64)
    return float((guessed == labels).mean())


def split_of(rows, purge, embargo):
    """Point-in-time splits: two thirds train, one sixth validation, one sixth the sealed test, with
    the purge and embargo bars dropped between them so no feature window crosses a boundary."""
    edge = len(rows) // 6
    first = edge * 4
    second = edge * 5
    return {
        "train": [0, max(0, first - purge)],
        "validation": [first + embargo, max(first + embargo, second - purge)],
        "test": [second + embargo, len(rows)],
    }


def opened(shared):
    """The door this machine's host serves, from the home's own `[data]` settings."""
    home = home_of(shared)
    settings_file = home / "settings.toml"
    settings = tomllib.loads(settings_file.read_text("utf-8")) if settings_file.is_file() else {}
    data = settings.get("data") if isinstance(settings.get("data"), dict) else {}
    root = Path(str(data.get("root") or ""))
    if str(data.get("root") or "") == "":
        fail("this home's settings name no [data] root, so the door cannot open")
    placement = Placement(str(data.get("placement") or "pc"))
    opened_door = MarketDoor.open(root, data, placement=placement)
    if is_refusal(opened_door):
        fail(f"the market-data door did not open: {opened_door.context}")
    return opened_door.value


given = json.load(sys.stdin).get("in") or []
row = ask(given)
if not row:
    fail("the run names no series and months to train on")
series = series_of(row)
if not series:
    fail(f"{row} names no series")
months = [str(month) for month in row["months"]]
into = Path(os.environ["QMX_WORK"]) / "partitions"
door = opened(Path(os.environ["QMX_WORK_SHARED"]))
landed, why = partitions(door, series, months, into)
if landed is None:
    fail(f"the door did not serve {series} for {months}: {why}")
ticks = read_ticks([Path(found["path"]) for found in landed])
rows = len(ticks["t"])
if rows < 100:
    fail(f"{series} served {rows} rows, too few to train on")
purge = int(row.get("purge_bars") or DEFAULT_PURGE_BARS)
embargo = int(row.get("embargo_bars") or DEFAULT_EMBARGO_BARS)
seed = int(row.get("seed") or DEFAULT_SEED)
shuffle_score, chance_score = scored(ticks, seed)
print(
    json.dumps(
        {
            "slot": str(row.get("slot") or "the model's slot"),
            "label": str(row.get("label") or "the next bar's direction"),
            "horizon_bars": int(row.get("horizon_bars") or DEFAULT_HORIZON_BARS),
            "features": [str(name) for name in row.get("features") or []],
            "family": str(row.get("family") or ""),
            "questions": [str(question) for question in row.get("questions") or []],
            "series": series,
            "months": [str(found["month"]) for found in landed],
            "partitions": [
                {key: found[key] for key in ("month", "fingerprint", "bytes")} for found in landed
            ],
            "rows": rows,
            "splits": split_of(rows, purge, embargo),
            "purge_bars": purge,
            "embargo_bars": embargo,
            "feature_lag_bars": DEFAULT_HORIZON_BARS,
            "seed": seed,
            "shuffle_score": shuffle_score,
            "chance_score": chance_score,
            "sealed_test": {"created": True, "touched": 0},
            "estimate_usd": 0.0,
            "code": {
                "digest": code_digest(os.environ["QMX_CODE"]),
                "folder": os.environ["QMX_CODE"],
            },
            "runs_on": {"placement": "pc", "gpu_slot": int(row.get("gpu_slot") or 0)},
        }
    )
)
