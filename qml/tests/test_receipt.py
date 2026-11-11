"""The size trail: one stored row answers why this size, and replays to the same quantity.

Verify, unit block's first seam. A row is stored the way a host journals it, then
``explain_size`` prints every input with its source and age and ``replay_decision`` re-runs the
sizing on those stored inputs and must give the row's own quantity, at the section's literals:
fraction 0.005, equity 100000, EURUSD's 0.0050 stop distance, and 1.00 lots.

The row hash is pinned as a literal on purpose: it is the receipt's identity, so a change to an
input, a step or a verdict the size used must change the hash loudly instead of passing. It is
read from the implementation once, when the row's shape is fixed, and again each time the stack
under it moved: when the shipped dummy's numbers each gained the reason and owner rc-23 requires,
because the receipt covers the document's risk half; when this row joined rc-31's second stream at
compiler format 9, rc-32's position count at compiler format 10, and rc-21's modifier chain at
compiler format 11. Each value after the first was read from a failing run at the tree that moved
it.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

from decimal import Decimal

from qmf.risk.unit_intent import UNIT_INTENT_FORMAT_VERSION
from qml.protocol import unit as hosted
from qml.protocol.unit import Account
from qml.receipt import explain_size, record_stored, replay_decision, row_hash, stored_row
from qml.unit.model import Side

from test_price_call import _EQUITY, _START, _dummy, _record, _sizer_2, _target, _with_sizer

_EURUSD = "fx.eurusd"
_STORED_HASH = "fp1:sha256:dba50efc20dd184e298f7810549f86ba4fcd9655c08d932235407e67db526170"
"""The receipt's identity at compiler format 11. It moved from
``fp1:sha256:01e3bd10...1bbee0`` because the row's receipt covers ``logic_fp`` and ``risk_fp``:
the joined document's numbers now carry rc-23's reason and owner, and AD-19's format bump moves
both halves by design. The size, the steps and every verdict are the same."""


def _proposal(fraction: str) -> hosted.Proposal:
    compiled = _dummy()
    record = _record("eurusd")
    target = _target()
    stop = Decimal("1.09500")
    return hosted.Proposal(
        wire={
            "contract_format_version": UNIT_INTENT_FORMAT_VERSION,
            "intent_family": "entry",
            "unit": {
                "unit_id": compiled.unit.unit_id,
                "version_ref": compiled.document_fingerprint.value,
                "compiled_fingerprint": compiled.compiled_fingerprint.value,
            },
            "instrument": {"venue": record.venue, "symbol": record.symbol},
            "market_id": _EURUSD,
            "direction": Side.LONG.value,
            "reason_code": {"code": compiled.unit.family_id, "book_family": "unit"},
            "execution_target": {
                "role": target.role.value,
                "venue_id": target.venue_id.value,
                "account_id": target.account_id,
            },
            "order": {"type": "market"},
            "protection": {"stop": str(stop), "targets": [], "time_exit_bars": 1},
            "not_before": _START.value_ns,
            "placeholder_labels": list(compiled.placeholders),
            "decision_row_id": "row-eurusd",
        },
        row=hosted.DecisionRow(
            row_id="row-eurusd",
            instant=_START,
            market_id=_EURUSD,
            side=Side.LONG,
            outcome="taken",
            slot_trail=(),
            numbers_in_force={"risk_fraction": Decimal(fraction)},
            reason="all slots hold",
        ),
        market_id=_EURUSD,
        side=Side.LONG,
        entry_price=Decimal("1.10000"),
        stop=stop,
        params={"fraction": Decimal(fraction)},
        record=record,
    )


def _sized(fraction: str) -> hosted.Priced:
    """The dummy's shipped sizer at ``fraction``, pricing one EURUSD long."""
    sizer = _sizer_2().make({"fraction": Decimal(fraction)}, {})
    return _with_sizer(_dummy(), sizer).price(_proposal(fraction), Account(_EQUITY))


def test_replay_equals_the_row() -> None:
    priced = _sized("0.005")

    assert priced.code is None, priced.row.reason
    assert priced.intent is not None
    sent = priced.intent.to_wire()["quantity"]

    body = stored_row(priced.row)

    assert sent == "1.00"
    assert body["written_before_send"] is False, "a unit mints a row; a host's journal writes it"
    assert replay_decision(body).quantity == Decimal("1.00")
    assert replay_decision(body).code is None
    assert replay_decision(body).row_hash == row_hash(body) == _STORED_HASH


def test_the_trail_prints_every_input_with_its_source_and_age() -> None:
    body = stored_row(_sized("0.005").row)

    trail = explain_size(body)

    assert trail.binding == "fixed-fraction-at-stop@2"
    assert [(step.name, step.kind, step.value, step.basis) for step in trail.steps] == [
        ("wanted", "money_at_risk", "500.000", "gross_at_stop"),
        ("approved", "quantity", "1.00", "gross_at_stop"),
    ]
    assert [seen.name for seen in trail.numbers] == ["risk_fraction"]
    assert [(seen.name, seen.value) for seen in trail.numbers] == [("risk_fraction", "0.005")]
    assert {seen.name for seen in trail.facts} == {
        "equity",
        "entry_price",
        "stop_price",
        "market.rate:USD",
        "record",
    }
    assert all(seen.source for seen in trail.facts), "every fact names where it came from"
    aged = {seen.name: seen.age_s for seen in trail.facts}
    assert [aged[name] for name in ("equity", "entry_price", "stop_price", "market.rate:USD")] == [
        "0",
        "0",
        "0",
        "0",
    ], "each fact's age is the row's instant minus its read time"
    assert aged["record"] == "", "a record is a version in force, not a reading with an age"
    assert trail.verdicts == (
        "sizer: none",
        "converter: none",
        "size_band: none",
    )
    assert trail.residue_r == "0"


def test_the_refused_row_carries_the_link_that_refused_it() -> None:
    """A refused entry has the same trail, ending at the link that said no."""
    sizer = _sizer_2().make({"fraction": Decimal("0.005")}, {})
    unit = _with_sizer(_dummy(), sizer)
    band = hosted.SizeBand(max_lots=Decimal("0.5"))

    priced = unit.price(_proposal("0.005"), Account(_EQUITY), band)

    assert priced.code == "size_band"
    assert priced.row.outcome == "skipped"
    trail = explain_size(stored_row(priced.row))
    assert trail.verdicts == (
        "sizer: none",
        "converter: none",
        "size_band: refuse (size_band)",
    )
    assert replay_decision(stored_row(priced.row)).code is None
    assert replay_decision(stored_row(priced.row)).quantity == Decimal("1.00")


def test_a_record_survives_the_row() -> None:
    """The record the row stores is the record the converter read, key for key."""
    record = _record("eurusd")

    stored = record_stored(record)

    assert stored["symbol"] == "EURUSD"
    assert stored["value_per_point"] == "100000"
    assert stored["lot_step"] == "0.01"
    assert stored["conversions"] == {}
