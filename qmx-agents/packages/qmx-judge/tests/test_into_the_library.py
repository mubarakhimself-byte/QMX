"""The lander's records pass the real Library's kinds: the `try` kind and `backtest-result` 2."""

from __future__ import annotations

from collections.abc import Collection, Iterator, Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

import pytest
from qmf.core import fingerprint_bytes
from qmx_engine.ledger import redact
from qmx_library.port import Draft, JsonObject
from qmx_library.principal import Principal
from qmx_library.store import Store

from qmx_judge.landing import Lander, Stored
from qmx_judge.runs import Landing, parse_bundle

OPERATOR = Principal("operator")
AT = datetime(2026, 11, 1, 9, 30, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = AT

    def __call__(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now


class StoreLanding:
    """The lander's port over a real store, writing on main as the operator."""

    def __init__(self, store: Store) -> None:
        self.store = store

    def find(self, item: str) -> str | None:
        head = self.store.head(item, "main")
        return None if head is None else head[0]

    def put(
        self,
        kind: str,
        fields: Mapping[str, object],
        blobs: Mapping[str, bytes],
        *,
        item: str | None,
        title: str,
        summary: str,
        principal: str,
    ) -> Stored:
        draft = Draft(
            kind, item, title, summary, fields=cast(JsonObject, dict(fields)), blobs=dict(blobs)
        )
        return Stored(self.store.put(OPERATOR, draft, on="main", expected_head=None).object_id)

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str:
        return self.store.relate(OPERATOR, from_id, relation, to_id)


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    with Store.open(tmp_path / "library", redactor=redact, wall=Clock()) as opened:
        yield opened


def note(store: Store, item: str) -> str:
    draft = Draft("note", item, item, fields={})
    return store.put(OPERATOR, draft, on="main", expected_head=None).object_id


def only_qmb(app_id: str, version: str) -> Collection[str]:
    return {"backtest-result"}


def test_open_and_close_land_valid_records_with_three_edges(store: Store, tmp_path: Path) -> None:
    unit, study, card = note(store, "unit"), note(store, "study"), note(store, "card")
    lander = Lander(StoreLanding(store), "operator", "pc", only_qmb, Clock())
    ticket = lander.open(
        "qmb", "0.2.0", "backtest", {"unit": unit, "study": study, "seed": 7}, "operator"
    )
    assert ticket is not None
    out = tmp_path / "out"
    out.mkdir()
    (out / "equity.parquet").write_bytes(b"PAR1-equity")
    bundle = parse_bundle(
        {
            "run_id": ticket.run_id,
            "status": "finished",
            "tester": {"app": "qmb", "version": "0.2.0"},
            "measures": {"trades": 3},
            "labels": {"fidelity": "bars", "zero_trades": False},
            "files": [
                {
                    "slot": "equity",
                    "path": "equity.parquet",
                    "fp": fingerprint_bytes(b"PAR1-equity").value,
                }
            ],
            "consumed": [card],
        }
    )

    result_id = lander.close(Landing(ticket, bundle, out))
    lander.close(Landing(ticket, bundle, out))

    result = store.get(OPERATOR, result_id)
    assert (result.kind, result.fields["status"], result.fields["fidelity"]) == (
        "backtest-result",
        "finished",
        "bars",
    )
    assert result.blobs["equity"].media_type == "application/vnd.apache.parquet"
    assert [(kind, to) for _, kind, to, _, _ in store.edges_of(result_id, reverse=False)] == [
        ("consumed", card),
        ("uses", unit),
        ("tests", study),
    ]
    tries = store.with_field("try", "run_id", ticket.run_id)
    assert [store.get(OPERATOR, found).fields["state"] for found in tries] == ["opened", "landed"]


def test_a_version_1_result_still_lands_and_reads_back_unchanged(store: Store) -> None:
    v1: JsonObject = {
        "world": "backtest",
        "claim_class": "retrospective",
        "role": "confirmation",
        "fidelity": "bar-m1",
        "provenance": {"ledger_line": 7},
        "outcome": "supports",
        "memo_key": "memo-1",
    }
    draft = Draft("backtest-result", "old-run", "old", fields=v1, blobs={"report": b"{}"})

    object_id = store.put(OPERATOR, draft, on="main", expected_head=None).object_id

    assert store.get(OPERATOR, object_id).fields == v1
