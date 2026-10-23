"""The feed and the downloaders as workflows: a silent second fire, one file per partition (W14).

Both are run on the real engine. The feed's `monitor` node decides whether a fire happens at all,
so the test runs the same source twice and reads the second run's monitor output. The
downloaders all land through the market-data door, which is the store's one writer, so the
partition test drives that door twice with the same month.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from flows import kinds, run_folder

from qmf.core import is_refusal
from qmf.data.series import SeriesKey, SeriesStore
from qmf.data.store.engines.typed import TICK_COLUMNS, TypedWriter
from qmx_engine.templates.catalog import PACK
from qmx_host.market_data import MarketDoor
from qmx_ledger.journal import fingerprint

FEED = PACK / "feed"
SEAL = int(datetime(2024, 1, 1, tzinfo=UTC).timestamp() * 1_000_000_000)
OCTOBER = int(datetime(2026, 10, 1, 9, 0, tzinfo=UTC).timestamp() * 1000)


def feed_dir(tmp_path: Path, titles: list[str]) -> Path:
    """A local RSS file the feed can read with no network at all."""
    items = "".join(
        f"<item><title>{title}</title>"
        f"<link>file:///{(tmp_path / f'{title}.html').as_posix()}</link>"
        f"<pubDate>Thu, 01 Oct 2026 09:00:00 +0000</pubDate></item>"
        for title in titles
    )
    source = tmp_path / "feed.xml"
    source.write_text(f"<?xml version='1.0'?><rss><channel>{items}</channel></rss>", "utf-8")
    for title in titles:
        (tmp_path / f"{title}.html").write_text(f"<html><body>{title} text</body></html>", "utf-8")
    return source


def output(events: list, node_id: str) -> object:
    return next(
        event.data["outputs"]
        for event in events
        if event.kind == "node_finished" and event.data["node_id"] == node_id
    )


def test_an_unchanged_feed_source_ends_the_second_fire_silent(tmp_path: Path) -> None:
    source = feed_dir(tmp_path, ["one"])
    inputs = {
        "source": {
            "name": "a local feed",
            "method": "rss",
            "url": source.as_posix(),
            "lands_as": "source",
            "collection": "local",
        }
    }
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
    source = feed_dir(tmp_path, ["one"])
    inputs = {
        "source": {
            "name": "a local feed",
            "method": "rss",
            "url": source.as_posix(),
            "lands_as": "source",
            "collection": "local",
        }
    }

    _, events = run_folder(FEED, tmp_path / "home", inputs)
    landed = output(events, "land")["main"]

    assert landed["status"] == "landed"
    assert landed["collection"] == "local"
    assert landed["landed"] == [f"file:///{(tmp_path / 'one.html').as_posix()}"]
    assert landed["held"] == []


def test_two_runs_on_one_partition_key_write_one_file(tmp_path: Path) -> None:
    opened = MarketDoor.open(tmp_path / "store", {"seal_boundary_ns": SEAL})
    assert not is_refusal(opened)
    door = opened.value
    key = SeriesKey.try_create("dukascopy", "EURUSD", "ticks", 2026, 10).value
    staging = tmp_path / "store" / "staging"
    staged = staging / "dukascopy" / "EURUSD" / "ticks" / "-" / "2026-10.parquet"
    staged.parent.mkdir(parents=True)
    rows = [
        (OCTOBER, 1_084_500, 1_084_520, 0.25, 0.25),
        (OCTOBER + 60_000, 1_084_510, 1_084_530, 1.0, 1.0),
    ]

    TypedWriter(staged, key.text, TICK_COLUMNS).add(rows).finish()
    one = door.commit([staged], staging=staging)
    two = door.commit([staged], staging=staging)

    assert not is_refusal(one) and not is_refusal(two)
    assert (one.value[0].rows, two.value[0].rows) == (2, 2)
    assert one.value[0].fingerprint == two.value[0].fingerprint
    stored = SeriesStore(tmp_path / "store" / "series").folder(key)
    assert sorted(path.name for path in stored.glob("*.parquet")) == ["open.parquet"]
