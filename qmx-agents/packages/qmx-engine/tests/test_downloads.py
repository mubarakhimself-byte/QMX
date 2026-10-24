"""The feed and the downloaders as workflows: a silent second fire, one file per partition (W14).

Both are run on the real engine. The feed's `monitor` node decides whether a fire happens at all,
so the test runs the same source twice and reads the second run's monitor output. A partition is
written by the store under one key, so the partition test drives the store's own `commit` twice
with the same month; the downloaders reach the same writer through the market-data door, which
their landing proof exercises with the real script.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from flows import kinds, run_folder
from pydantic import JsonValue
from qmf.core import is_ok
from qmf.data.series import SeriesKey, SeriesStore
from qmx_ledger.journal import fingerprint

from qmx_engine.ledger.events import Event
from qmx_engine.templates.catalog import PACK

FEED = PACK / "feed"
OCTOBER = int(datetime(2026, 10, 1, 9, 0, tzinfo=UTC).timestamp() * 1000)
MONTH_NOW = datetime(2026, 10, 15, tzinfo=UTC)


def feed_inputs(tmp_path: Path) -> JsonValue:
    """A local RSS file the feed can read with no network at all."""
    items = "".join(
        f"<item><title>{title}</title>"
        f"<link>file:///{(tmp_path / f'{title}.html').as_posix()}</link>"
        f"<pubDate>Thu, 01 Oct 2026 09:00:00 +0000</pubDate></item>"
        for title in ("one",)
    )
    source = tmp_path / "feed.xml"
    source.write_text(f"<?xml version='1.0'?><rss><channel>{items}</channel></rss>", "utf-8")
    (tmp_path / "one.html").write_text("<html><body>one text</body></html>", "utf-8")
    return {
        "source": {
            "name": "a local feed",
            "method": "rss",
            "url": source.as_posix(),
            "lands_as": "source",
            "collection": "local",
        }
    }


def output(events: list[Event], node_id: str) -> dict[str, Any]:
    """The finished node's output ports, as the ledger records them."""
    found = next(
        event.data["outputs"]
        for event in events
        if event.kind == "node_finished" and event.data["node_id"] == node_id
    )
    return cast("dict[str, Any]", found)


def test_an_unchanged_feed_source_ends_the_second_fire_silent(tmp_path: Path) -> None:
    inputs = feed_inputs(tmp_path)
    home = tmp_path / "home"

    _, first = run_folder(FEED, home, inputs)
    second_outcome, second = run_folder(FEED, home, inputs)

    seen = output(first, "watch")["changed"]
    assert len(seen["value"]["items"]) == 1
    assert kinds(first, "land").count("node_started") == 1
    assert output(second, "watch") == {"silent": {"hash": fingerprint(seen["value"])}}
    assert kinds(second, "land") == []
    assert second_outcome.status == "passed"


def test_a_new_item_is_fetched_once_and_claimed_by_its_url(tmp_path: Path) -> None:
    _, events = run_folder(FEED, tmp_path / "home", feed_inputs(tmp_path))

    landed = output(events, "land")["main"]

    assert landed["status"] == "landed"
    assert landed["collection"] == "local"
    assert landed["landed"] == [f"file:///{(tmp_path / 'one.html').as_posix()}"]
    assert landed["held"] == []


def test_two_runs_on_one_partition_key_write_one_file(tmp_path: Path) -> None:
    store = SeriesStore(tmp_path / "series", wall=lambda: MONTH_NOW)
    built = SeriesKey.try_create("dukascopy", "EURUSD", "ticks", 2026, 10)
    assert is_ok(built)
    key = built.value
    rows = [
        (OCTOBER, 1_084_500, 1_084_520, 0.25, 0.25),
        (OCTOBER + 60_000, 1_084_510, 1_084_530, 1.0, 1.0),
    ]

    one = store.commit(key, rows)
    two = store.commit(key, rows)

    assert is_ok(one) and is_ok(two)
    assert (one.value.rows, two.value.rows) == (2, 2)
    assert one.value.fingerprint == two.value.fingerprint
    assert not two.value.frozen
    assert (one.value.attempts, two.value.attempts) == (1, 2)
    assert sorted(path.name for path in store.folder(key).glob("*.parquet")) == ["open.parquet"]
