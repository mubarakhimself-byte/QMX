"""Nothing that reads journals writes a `bot` or a `strategy` (Part B B15, R0-17).

Every write path B15 adds runs once against one real Library: the harvester's round with its
`trade` projection, the judge's paper scoring and the round's `maintenance-result`, and an agent's
`notes_write`. The store then holds exactly the kinds those paths are for.
"""

# pyright: reportMissingTypeStubs=false

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from qmf.core import is_refusal
from qmf.data.journal_envelope import JournalStream, JournalWorld, RowFacts
from qmf.data.journal_writer import JournalWriter, WriterScope
from qmx_host.market_data import MarketDoor
from qmx_host.records import Cadence, Harvester, Projection, Records, append_roots
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

_REAL = datetime.now(UTC)  # ambient-scan: allow (the store freezes by the real month)
OPENED = datetime(_REAL.year, _REAL.month, 1, tzinfo=UTC)


def test_the_journal_write_paths_land_trades_paper_runs_notes_and_results_only(
    tmp_path: Path,
) -> None:
    home = tmp_path / "QMX"
    root = home / "apps" / "practice-node" / "data" / "journal"
    closed = OPENED + timedelta(hours=9)
    scope = WriterScope(JournalStream.UNIT, "dummy", JournalWorld.PAPER, "this-pc", "node", "b")
    opened = JournalWriter.open(
        root, scope, clock=lambda: int(closed.timestamp()) * 1_000_000_000, boot_epoch_id="b1"
    )
    assert not is_refusal(opened)
    body: dict[str, object] = {
        "closing_deal_id": "t1.close",
        "trade_id": "t1",
        "side": "short",
        "opened_at": int(OPENED.timestamp()) * 1_000_000_000,
        "closed_at": int(closed.timestamp()) * 1_000_000_000,
        "money": "20.00",
        "r": "1.0",
    }
    facts = RowFacts(
        ts_recv=0,
        clock_ok=True,
        unit_id="dummy",
        market_id="fx.eurusd",
        venue="conformance",
        account="demo-1",
    )
    assert not is_refusal(opened.value.append("trade", body, facts))
    opened.value.close()
    context = DomainContext(root=home)
    store = context.library.store
    harvest = Harvester(
        lambda: append_roots(home),
        MarketDoor(root=home / "market"),
        home / "records",
        journals_open=True,
    )
    job = Records(
        harvest,
        Cadence,
        clock=lambda: OPENED + timedelta(days=1),
        projection=Projection(store, home / "records"),
        store=store,
    )

    counts = job.round()
    domain_functions(context)["research"]["notes_write"](
        title="A look at t1", text="One short, 1.0 R.", note_kind="analysis", receipts=["c1"]
    )
    kinds = sorted(
        kind for (kind,) in store.catalog.db.execute("SELECT kind FROM objects").fetchall()
    )
    context.control.close()

    assert (counts.partitions, counts.trades, counts.paper_runs) == (1, 1, 1)
    assert kinds == ["artifact", "note", "paper-run", "trade"]
    assert not {"bot", "strategy"} & set(kinds)
