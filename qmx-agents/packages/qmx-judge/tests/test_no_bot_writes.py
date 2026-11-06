"""Nothing that reads journals writes a `bot` or a `strategy` (Part B B15, R0-17).

Every write path B15 adds runs once against one real Library: the harvester's round with its
`trade` projection, the judge's paper scoring and the round's `maintenance-result`, and an agent's
`notes_write`. The store then holds exactly the kinds those paths are for.
"""

# pyright: reportMissingTypeStubs=false

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from qmb.execution.fill import FillKind
from qmb.host.unit_handler import UnitTrade
from qmb.results.journal import RunJournal
from qmf.core import Instant, is_refusal
from qmf.data.journal_envelope import JournalWorld
from qml.compile import CompiledUnit
from qml.unit.model import Side
from qmx_host.market_data import MarketDoor
from qmx_host.records import Cadence, Harvester, Projection, Records, append_roots
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

_REAL = datetime.now(UTC)  # ambient-scan: allow (the store freezes by the real month)
OPENED = datetime(_REAL.year, _REAL.month, 1, tzinfo=UTC)
COMPILED = cast(
    "CompiledUnit",
    SimpleNamespace(
        unit=SimpleNamespace(unit_id="dummy"),
        document_fingerprint=SimpleNamespace(value="v1"),
        plan=SimpleNamespace(
            markets=[(SimpleNamespace(market_id="fx.eurusd"), SimpleNamespace(venue="conformance"))],
            sides=[],
        ),
    ),
)
"""The four facts the real writer reads of a compiled unit."""


def test_the_journal_write_paths_land_trades_paper_runs_notes_and_results_only(
    tmp_path: Path,
) -> None:
    home = tmp_path / "QMX"
    root = home / "apps" / "practice-node" / "data" / "journal"
    closed = Instant((int(OPENED.timestamp()) + 9 * 3_600) * 1_000_000_000)
    opened = RunJournal.open_live(
        root,
        COMPILED,
        scope_id="dep-1",
        world=JournalWorld.PAPER,
        machine="this-pc",
        role="node",
        build="b",
        boot_epoch_id="b1",
        account="demo-1",
    )
    assert not is_refusal(opened)
    opened.value.at(closed)
    opened.value.append(
        UnitTrade(
            "t1",
            "fx.eurusd",
            Side.SHORT,
            Instant(int(OPENED.timestamp()) * 1_000_000_000),
            closed,
            Decimal("1.08300"),
            Decimal("1.08000"),
            Decimal("1.08600"),
            Decimal("0.10"),
            FillKind.CLOSE,
            Decimal("20.00"),
            Decimal("1.0"),
        )
    )
    assert opened.value.write_failure is None
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
