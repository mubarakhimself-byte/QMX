"""Retained LIVE spot quotes resolve through their CT-13/CT-10/raw joins."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from qmf.core import Instant, Instrument, Result, VenueId, World, WriterId, is_ok, is_refusal
from qmf.data import JournalAppendReceipt, JournalWriter
from qmf.data.store import EvidenceStore
from qmf.venue.ctrader import decode_market_data_price
from qmn.data.observation_sink import QmfLiveJournalSink, QmfLiveObservationSink
from qmn.ledger.protection_market import resolve_checked_live_spot_prices

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def test_spot_prices_reopen_actual_ct13_ct10_and_raw_quotes(tmp_path: Path) -> None:
    venue = _ok(VenueId.try_create("venue-market-proof"))
    instrument = _ok(Instrument.try_create(venue, "EURUSD"))
    store = EvidenceStore(tmp_path / "evidence")
    world_store = _ok(store.for_world(World.LIVE))
    writer_id = _ok(WriterId.try_create("fixture", "venue", "market-proof", "epoch-1"))
    writer = _ok(JournalWriter.resume(world_store.journal, writer_id, stream_name="market-proof"))
    observation_sink = QmfLiveObservationSink(store=store, writer=writer)
    journal_sink = QmfLiveJournalSink(
        writer=writer, journal_store=world_store.journal, evidence_store=store
    )
    observation = {
        "observation": {
            "payload": {
                "event_time_ns": 100,
                "known_at_ns": 100,
                "source": "ctrader",
                "source_native_id": "spot-1",
                "revision": "1",
                "venue_id": venue.value,
                "response_account_id": 42,
                "session_epoch": "session-1",
                "response_session_epoch": "session-1",
                "wire_kind": "spot",
            }
        },
        "raw_payload": {"bid": 108520, "ask": 108522},
    }
    ack = _ok(observation_sink.emit(observation))
    appended = _ok(
        journal_sink.append(
            {
                "event_type": "data quality",
                "event_time_ns": 100,
                "known_at_ns": 100,
                "source": "ctrader",
                "source_native_id": "spot-1",
                "revision": "1",
                "venue_id": venue.value,
                "trader_account_id": 42,
                "session_epoch": "session-1",
                "wire_kind": "spot",
                "_observation_ack": ack,
            }
        )
    )
    receipt = appended.detail["journal_append_receipt"]
    assert type(receipt) is JournalAppendReceipt
    event = receipt.event
    at = _ok(Instant.try_create(100))
    checked = _ok(
        resolve_checked_live_spot_prices(
            journal=world_store.journal,
            journal_stream="market-proof",
            evidence_store=store,
            source_event=event,
            authorized_writers=(writer_id,),
            instrument=instrument,
            expected_venue_id=venue.value,
            expected_account_id=42,
            expected_session_epoch="session-1",
            not_before=_ok(Instant.try_create(90)),
            decision_at=_ok(Instant.try_create(110)),
        )
    )
    assert checked.bid == _ok(decode_market_data_price(108520, instrument))
    assert checked.ask == _ok(decode_market_data_price(108522, instrument))
    assert is_refusal(
        resolve_checked_live_spot_prices(
            journal=world_store.journal,
            journal_stream="market-proof",
            evidence_store=store,
            source_event=event,
            authorized_writers=(writer_id,),
            instrument=instrument,
            expected_venue_id=venue.value,
            expected_account_id=43,
            expected_session_epoch="session-1",
            not_before=at,
            decision_at=_ok(Instant.try_create(110)),
        )
    )
    assert is_refusal(
        resolve_checked_live_spot_prices(
            journal=world_store.journal,
            journal_stream="market-proof",
            evidence_store=store,
            source_event=event,
            authorized_writers=(writer_id,),
            instrument=instrument,
            expected_venue_id=venue.value,
            expected_account_id=42,
            expected_session_epoch="session-1",
            not_before=_ok(Instant.try_create(101)),
            decision_at=_ok(Instant.try_create(110)),
        )
    )
    world_store.journal.close()
