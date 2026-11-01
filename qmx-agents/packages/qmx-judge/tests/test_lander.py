"""The lander opens, closes and fails a run with a fake tester, and a retry writes nothing."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest
from qmf.core import fingerprint_bytes

from qmx_judge.landing import Lander, Stored
from qmx_judge.runs import BundleRefused, Landing, Ticket, parse_bundle

AT = datetime(2026, 11, 1, 9, 30, tzinfo=UTC)
INPUTS: dict[str, object] = {
    "unit": "unit-dummy@1",
    "study": "study-quick@1",
    "seed": 7,
    "window": {"start": "2026-08-01T00:00:00Z", "end": "2026-09-01T00:00:00Z"},
}


class FakeLibrary:
    """Items on main and the edge set, as the Library keeps them: one object per item, one edge
    per (from, relation, to)."""

    def __init__(self) -> None:
        self.items: dict[str, dict[str, object]] = {}
        self.edges: set[tuple[str, str, str]] = set()

    def find(self, item: str) -> str | None:
        return f"obj-{item}" if item in self.items else None

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
        assert item is not None
        self.items[item] = {"kind": kind, "fields": dict(fields), "blobs": dict(blobs)}
        return Stored(f"obj-{item}")

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str:
        self.edges.add((from_id, relation, to_id))
        return f"{from_id}-{relation}-{to_id}"

    def state(self) -> tuple[dict[str, dict[str, object]], set[tuple[str, str, str]]]:
        return ({k: dict(v) for k, v in self.items.items()}, set(self.edges))


def provides(app_id: str, version: str) -> Collection[str]:
    return {"backtest-result"} if app_id == "qmb" else set()


def lander(library: FakeLibrary) -> Lander:
    return Lander(
        library, "operator", "pc", provides, lambda: AT, mint=lambda: "01JZ0000000000000000000000"
    )


def fake_tester(ticket: Ticket, out: Path, *, status: str = "finished") -> Landing:
    """A tester that writes its report and trades files and answers one bundle."""
    out.mkdir(parents=True, exist_ok=True)
    report, trades = b'{"net_r": "3.2"}', b"PAR1-trades"
    (out / "report.json").write_bytes(report)
    (out / "trades.parquet").write_bytes(trades)
    raw: dict[str, object] = {
        "schema_version": 1,
        "run_id": ticket.run_id,
        "request_fp": "fp1:sha256:" + "a" * 64,
        "tester": {"app": "qmb", "version": "0.2.0", "contract": "qmb/1"},
        "status": status,
        "measures": {"trades": 14, "expectancy_r": "0.23"},
        "labels": {"zero_trades": False, "fidelity": "bars"},
        "files": [
            {"slot": "report", "path": "report.json", "fp": fingerprint_bytes(report).value},
            {"slot": "trades", "path": "trades.parquet", "fp": fingerprint_bytes(trades).value},
        ],
        "consumed": ["dataset-eurusd-m1@3"],
        "versions": {"qmb": "0.2.0", "qml": "0.9.0"},
    }
    if status == "failed":
        raw["reason"] = "the unit raised on its first bar"
    return Landing(ticket, parse_bundle(raw), out)


def opened(library: FakeLibrary) -> Ticket:
    ticket = lander(library).open("qmb", "0.2.0", "backtest", INPUTS, "agent:chat-1")
    assert ticket is not None
    return ticket


RUN = "qmbr-pc-01JZ0000000000000000000000"


def test_open_lands_one_opened_try_under_the_minted_run_id() -> None:
    library = FakeLibrary()

    ticket = opened(library)

    assert ticket.run_id == RUN
    assert library.items == {
        f"try-{RUN}-opened": {
            "kind": "try",
            "fields": {
                "kind": "run",
                "state": "opened",
                "run_id": RUN,
                "family": "unit-dummy@1",
                "unit": "unit-dummy@1",
                "principal": "agent:chat-1",
                "at": "2026-11-01T09:30:00+00:00",
                "links": [],
                "study": "study-quick@1",
                "tester": {"app": "qmb", "version": "0.2.0"},
            },
            "blobs": {},
        }
    }


def test_close_lands_one_result_with_three_edges_and_a_landed_try(tmp_path: Path) -> None:
    library = FakeLibrary()
    ticket = opened(library)

    result_id = lander(library).close(fake_tester(ticket, tmp_path / "out"))

    assert result_id == f"obj-{RUN}"
    assert library.edges == {
        (result_id, "consumed", "dataset-eurusd-m1@3"),
        (result_id, "uses", "unit-dummy@1"),
        (result_id, "tests", "study-quick@1"),
    }
    result = library.items[RUN]
    assert result["kind"] == "backtest-result"
    assert result["blobs"] == {"report": b'{"net_r": "3.2"}', "trades": b"PAR1-trades"}
    assert result["fields"] == {
        "run_id": RUN,
        "status": "finished",
        "kind": "backtest",
        "tester": {"app": "qmb", "version": "0.2.0"},
        "unit": "unit-dummy@1",
        "principal": "agent:chat-1",
        "world": "backtest",
        "study": "study-quick@1",
        "seed": 7,
        "window": {"start": "2026-08-01T00:00:00Z", "end": "2026-09-01T00:00:00Z"},
        "labels": {"zero_trades": False, "fidelity": "bars"},
        "fidelity": "bars",
        "measures": {"trades": 14, "expectancy_r": "0.23"},
        "request_fp": "fp1:sha256:" + "a" * 64,
        "versions": {"qmb": "0.2.0", "qml": "0.9.0"},
    }
    closing = library.items[f"try-{RUN}-closed"]["fields"]
    assert isinstance(closing, dict)
    assert (closing["state"], closing["links"]) == ("landed", [f"obj-try-{RUN}-opened", result_id])


def test_a_second_close_changes_nothing(tmp_path: Path) -> None:
    library = FakeLibrary()
    ticket = opened(library)
    landing = fake_tester(ticket, tmp_path / "out")
    first = lander(library).close(landing)
    before = library.state()

    again = lander(library).close(landing)

    assert again == first
    assert library.state() == before


def test_fail_lands_a_killed_result_with_no_measures_and_a_failed_try() -> None:
    library = FakeLibrary()
    ticket = opened(library)

    result_id = lander(library).fail(ticket, "stopped at the 2048 MB memory limit")

    fields = library.items[RUN]["fields"]
    assert isinstance(fields, dict)
    assert (fields["status"], fields["reason"]) == ("killed", "stopped at the 2048 MB memory limit")
    assert "measures" not in fields
    assert library.items[RUN]["blobs"] == {}
    assert library.edges == {
        (result_id, "uses", "unit-dummy@1"),
        (result_id, "tests", "study-quick@1"),
    }
    closing = library.items[f"try-{RUN}-closed"]["fields"]
    assert isinstance(closing, dict)
    assert closing["state"] == "failed"


def test_a_failed_bundle_lands_its_reason_and_no_measures(tmp_path: Path) -> None:
    library = FakeLibrary()
    ticket = opened(library)

    lander(library).close(fake_tester(ticket, tmp_path / "out", status="failed"))

    fields = library.items[RUN]["fields"]
    assert isinstance(fields, dict)
    assert (fields["status"], fields["reason"]) == ("failed", "the unit raised on its first bar")
    assert "measures" not in fields


def test_an_app_that_lands_no_result_gets_no_ticket() -> None:
    library = FakeLibrary()

    ticket = lander(library).open("mis", "1.0.0", "refresh", INPUTS, "operator")

    assert ticket is None
    assert library.items == {}


def test_a_file_that_does_not_match_its_fingerprint_lands_nothing(tmp_path: Path) -> None:
    library = FakeLibrary()
    ticket = opened(library)
    landing = fake_tester(ticket, tmp_path / "out")
    (tmp_path / "out" / "trades.parquet").write_bytes(b"changed after the run")

    with pytest.raises(BundleRefused) as refused:
        lander(library).close(landing)

    assert refused.value.problems == ("trades: trades.parquet does not match its fingerprint",)
    assert set(library.items) == {f"try-{RUN}-opened"}


def test_a_bundle_names_every_problem_at_once() -> None:
    with pytest.raises(BundleRefused) as refused:
        parse_bundle({"run_id": "", "status": "killed", "consumed": "dataset@1"})

    assert str(refused.value) == "run_id is the run id the core minted"
    assert refused.value.problems == (
        "run_id is the run id the core minted",
        "status is finished or failed; only the core stamps killed",
        "consumed is a list of pins",
    )
