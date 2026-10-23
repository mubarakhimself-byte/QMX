"""QMB's result files and the old `backtest` items import as one `backtest-result` (AD-29)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

from qmx_engine.ledger import redact

from qmx_library.migrate.from_qmb_results import import_qmb_results
from qmx_library.port import Draft
from qmx_library.principal import Principal
from qmx_library.store import Store

_RUN = "fp1:sha256:run-2025-10"
_CT32 = {
    "class": "qmb-run-performance-result",
    "run_id": _RUN,
    "world": "replay",
    "claim_class": "retrospective",
    "role": "confirmation",
    "fidelity": "bar-m1",
    "data_points_processed": 43_200,
    "filled": 14,
    "stream_order": ["eurusd"],
    "slices": [{"i": 1}, {"i": 2}],
    "performance_result": {"container": "qmb.results.ct32.PerformanceResult"},
}
_LEGACY = {
    "name": "trend-following, July",
    "kind": "backtest",
    "content": {
        "data_points_processed": 4_000,
        "filled": 3,
        "stream_order": ["eurusd"],
        "slices": [{"i": 1}],
    },
}


def _results(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{_RUN.replace(':', '-')}.json").write_text(
        json.dumps(_CT32, sort_keys=True), encoding="utf-8"
    )
    (root / "old-backtest.json").write_text(json.dumps(_LEGACY, sort_keys=True), encoding="utf-8")
    return root


def test_qmb_results_import_as_backtest_results_with_their_edges(tmp_path: Path) -> None:
    root = _results(tmp_path / "results")
    with Store.open(tmp_path / "library", redactor=redact) as store:
        store.put(
            Principal("operator"),
            Draft(kind="dataset", item="dataset-card-v3", title="EURUSD Aug", fields={}),
            on="main",
            expected_head=None,
        )
        store.put(
            Principal("operator"),
            Draft(kind="note", item="bot-version-7", title="Breakout", fields={}),
            on="main",
            expected_head=None,
        )

        report = import_qmb_results(
            root,
            store,
            edges={
                _RUN: {
                    "consumed": "dataset-card-v3",
                    "uses": "bot-version-7",
                    "tests": "bot-version-7",
                }
            },
        )

        assert [item.source for item in report.imported] == [
            f"{_RUN.replace(':', '-')}.json",
            "old-backtest.json",
        ]
        assert report.skipped == () and report.alarms == ()
        landed = {item.item: item for item in report.imported}
        legacy_item = (
            "qmb-result:" + hashlib.sha256((root / "old-backtest.json").read_bytes()).hexdigest()
        )
        assert set(landed) == {_RUN, legacy_item}
        assert landed[_RUN].edges == (
            ("consumed", "dataset-card-v3"),
            ("uses", "bot-version-7"),
            ("tests", "bot-version-7"),
        )
        assert landed[legacy_item].edges == ()

        view = store.get(
            Principal("operator"), store.resolve(Principal("operator"), _RUN), blobs="fetch"
        )
        assert view.kind == "backtest-result"
        assert view.fields["world"] == "replay"
        assert view.fields["fidelity"] == "bar-m1"
        provenance = cast("dict[str, object]", view.fields["provenance"])
        assert provenance["run_id"] == _RUN
        assert view.data["report"] == (root / f"{_RUN.replace(':', '-')}.json").read_bytes()
        operator = Principal("operator")
        assert [
            (kind, target)
            for _from, kind, target, _writer, _at in (
                store.edges_of(landed[_RUN].object_id, reverse=False)
            )
        ] == [
            ("consumed", store.resolve(operator, "dataset-card-v3")),
            ("uses", store.resolve(operator, "bot-version-7")),
            ("tests", store.resolve(operator, "bot-version-7")),
        ]

        again = import_qmb_results(root, store)
        assert again.imported == ()
        assert set(again.skipped) == {"old-backtest.json", f"{_RUN.replace(':', '-')}.json"}


def test_an_old_backtest_item_keeps_its_content_in_the_report_blob(tmp_path: Path) -> None:
    root = _results(tmp_path / "results")
    with Store.open(tmp_path / "library", redactor=redact) as store:
        report = import_qmb_results(root, store)

        assert report.imported
        legacy_item = next(
            item.item for item in report.imported if item.source == "old-backtest.json"
        )
        view = store.get(
            Principal("operator"), store.resolve(Principal("operator"), legacy_item), blobs="fetch"
        )
        assert view.title == "trend-following, July"
        provenance = cast("dict[str, object]", view.fields["provenance"])
        assert provenance["data_points_processed"] == 4_000
        assert json.loads(view.data["report"])["kind"] == "backtest"
