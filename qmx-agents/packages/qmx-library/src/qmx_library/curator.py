"""The curator's retention rule for test output (Library AD-6, engine AD-46, 46 K-25).

A record item that only test-mode runs ever placed, that is older than `TEST_RECORD_DAYS` and
that no other active item cites is archived, so noisy test output leaves search. Nothing is
deleted: archiving is a move of the item's state ref, made by the store's own engine principal.
Test records that cite each other are archived together, because a citation counts only from an
item that stays.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final

from qmx_library.store import Store

TEST_RECORD_DAYS: Final = 30
"""Claude's default (`curator.test_record_days`)."""
REASON: Final = "curator: a test record nothing cites"


def stale_test_records(store: Store, *, now: datetime, days: int = TEST_RECORD_DAYS) -> set[str]:
    catalog = store.catalog
    cutoff = now - timedelta(days=days)
    stale: set[str] = set()
    rows = catalog.db.execute(
        "SELECT i.item, min(m.at) FROM items i JOIN moves m ON m.item = i.item "
        "WHERE i.state = 'active' AND m.ref LIKE 'refs/runs/%' GROUP BY i.item"
    )
    for item, first in rows.fetchall():
        objects = catalog.db.execute(
            "SELECT object_id, class FROM objects WHERE item = ?", (item,)
        ).fetchall()
        if datetime.fromisoformat(str(first)) > cutoff:
            continue
        if all(k == "record" and catalog.producer(str(o)) == "test-run" for o, k in objects):
            stale.add(str(item))
    cites = [
        (str(target), str(source))
        for target, source in catalog.db.execute(
            "SELECT DISTINCT t.item, f.item FROM relations r "
            "JOIN objects t ON t.object_id = r.to_id JOIN objects f ON f.object_id = r.from_id "
            "JOIN items i ON i.item = f.item WHERE f.item <> t.item AND i.state = 'active'"
        )
    ]
    while kept := {t for t, s in cites if t in stale and s not in stale}:
        stale -= kept
    return stale


def curate(store: Store, *, now: datetime, days: int = TEST_RECORD_DAYS) -> list[str]:
    """Archive the stale test records and return them, in item order. A second run archives
    nothing new."""
    archived = sorted(stale_test_records(store, now=now, days=days))
    for item in archived:
        store.archive(store.engine, item, REASON)
    return archived
