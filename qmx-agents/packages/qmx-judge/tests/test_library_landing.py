"""One finished backtest lands as one `backtest-result` with its three edges (Library AD-29)."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import cast

from qmx_judge.landing import BacktestResult, Stored, land


class RecordingLibrary:
    """A Library that records what the landing step put and linked, in order."""

    def __init__(self) -> None:
        self.puts: list[dict[str, object]] = []
        self.links: list[tuple[str, str, str, str]] = []

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
        self.puts.append(
            {
                "kind": kind,
                "fields": dict(fields),
                "blobs": dict(blobs),
                "item": item,
                "title": title,
                "summary": summary,
                "principal": principal,
            }
        )
        return Stored(f"object-{len(self.puts)}")

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str:
        self.links.append((from_id, relation, to_id, principal))
        return f"{from_id}-{relation}-{to_id}"


def _result(
    *, report: bytes = b'{"ledger": 1}', outcome: str | None = "supports"
) -> BacktestResult:
    return BacktestResult(
        run_id="fp1:sha256:run-1",
        title="EURUSD breakout, August",
        summary="14 trades, net R 3.2",
        world="backtest",
        claim_class="retrospective",
        role="confirmation",
        fidelity="bar-m1",
        provenance={"ledger_line": 7, "ct32": "fp1:sha256:artifact"},
        report=report,
        outcome=outcome,
    )


def test_a_landed_result_carries_consumed_uses_and_tests(tmp_path: Path) -> None:
    library = RecordingLibrary()

    landed = land(
        _result(),
        library,
        consumed="dataset-card-v3",
        uses="bot-version-7",
        tests="hypothesis-2",
    )

    assert landed.object_id == "object-1"
    assert landed.edges == (
        ("consumed", "dataset-card-v3"),
        ("uses", "bot-version-7"),
        ("tests", "hypothesis-2"),
    )
    assert library.links == [
        ("object-1", "consumed", "dataset-card-v3", "qmb:backtest"),
        ("object-1", "uses", "bot-version-7", "qmb:backtest"),
        ("object-1", "tests", "hypothesis-2", "qmb:backtest"),
    ]
    [put] = library.puts
    assert put["kind"] == "backtest-result"
    assert put["item"] == "fp1:sha256:run-1"
    assert put["blobs"] == {"report": b'{"ledger": 1}'}
    assert put["fields"] == {
        "claim_class": "retrospective",
        "fidelity": "bar-m1",
        "outcome": "supports",
        "provenance": {"ledger_line": 7, "ct32": "fp1:sha256:artifact"},
        "role": "confirmation",
        "world": "backtest",
    }


def test_a_result_with_no_hypothesis_lands_two_edges(tmp_path: Path) -> None:
    library = RecordingLibrary()

    landed = land(_result(outcome=None), library, consumed="dataset-card-v3", uses="bot-version-7")

    assert landed.edges == (("consumed", "dataset-card-v3"), ("uses", "bot-version-7"))
    [put] = library.puts
    assert "outcome" not in cast("dict[str, object]", put["fields"])
