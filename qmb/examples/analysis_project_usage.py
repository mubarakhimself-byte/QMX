"""Reference usage — analysis.project returns canonical saved-view JSON (Story 35.1).

Executable::

    python qmb/examples/analysis_project_usage.py --operator-builder your_sources:analysis_source --runtime-root YOUR_REPLAY_ROOT

The operator builder returns an Ok containing the completed CT-32 and its
CT29ProjectionSource. This example expects two recorded closes at hours 10 and 18.
No copied in-memory trade list can stand in for that durable source.

Shows the things Story 35.1 / 35.2 / FR-W21 / FR-W22 / FR-W23 / FR-W24 / SCN-0016 pin down:

1. analysis.project filters one cited CT-32 and its CT-29 stream.
2. Durable body is {method: projection, source_ct32, source_ct29, predicate, as_of}.
3. as_of is the source CT-32 registry_as_of, never query time; fp1 is of that JSON.
4. No new CT-32, no ledger line, no ExperimentSpec, no occupancy.
5. Claim-class is projection — never admission evidence, never B-4 confirmation.
6. A citation without that JSON body is refused; a copied trade list is not a view.
7. Size / R / Book / ports / starting_capital are path-dependent refusals, not a rerun.
8. Ungoverned is a return value only; governed-without-QMA writes a source-run-dir sidecar.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypeVar

from qmb.analysis import CT29ProjectionSource, PROJECTION_SIDECAR_FILENAME, cite_projection, project
from analysis_source_usage import operator_analysis_source
from qmb.config import ResolvedRunConfig
from qmf.core.chrono import Instant
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import RefusalCategory, Result, is_ok, is_refusal

import qmb

T = TypeVar("T")
_NS = 1_700_000_000_000_000_000


def _unwrap(result: Result[T], what: str) -> T:
    if is_ok(result):
        return result.value
    raise AssertionError(f"expected {what} to construct, got {result}")


def _instant(ns: int) -> Instant:
    return _unwrap(Instant.try_create(ns), "instant")


def _at(*, hour: int) -> Instant:
    stamp = datetime(2023, 11, 15, hour, 0, tzinfo=timezone.utc)
    return _instant(int(stamp.timestamp()) * 1_000_000_000)


def main(*, source_ct32: object, source_ct29: CT29ProjectionSource) -> None:
    artifact = source_ct32
    config = source_ct29.run_config
    assert isinstance(config, ResolvedRunConfig)
    as_of = config.keys["registry_as_of"]
    assert isinstance(as_of, Instant)
    view = _unwrap(
        project(
            source_ct32=artifact,
            source_ct29=source_ct29,
            predicate={"hours": {"start": 8, "end": 16}},
            as_of=as_of,
        ),
        "projection",
    )
    body = view.body()
    assert body["method"] == "projection"
    assert set(body) == {"method", "source_ct32", "source_ct29", "predicate", "as_of"}
    assert body["as_of"] == as_of.fp1_identity()
    assert view.fingerprint == _unwrap(fingerprint(body), "fp1")
    assert view.matched_count == 1
    assert view.occupancy == "query"
    assert view.mints_ct32 is False
    assert view.mints_experiment_spec is False
    assert view.claim_class == "projection"
    assert view.is_admission_evidence is False
    assert view.b4_role is None
    print("canonical saved-view JSON")
    print("as_of is source registry_as_of")
    print("fp1 is of that JSON")
    print("query occupancy, no CT-32")
    print("claim-class is projection")

    cited = cite_projection(cite=view.fingerprint.value)
    assert is_refusal(cited) and cited.category is RefusalCategory.POLICY_REJECTION
    print("citation without a body refused")
    copied = cite_projection(body={**body, "trades": [{"pnl": 1}]})
    assert is_refusal(copied)
    print("copied trade list is not a saved view")
    query_time = project(
        source_ct32=artifact,
        source_ct29=source_ct29,
        predicate={"hours": {"start": 8, "end": 16}},
        as_of=_at(hour=12),
    )
    assert is_refusal(query_time)
    print("query-time as_of refused")

    size = project(
        source_ct32=artifact,
        source_ct29=source_ct29,
        predicate={"hours": {"start": 8, "end": 16}},
        as_of=as_of,
        starting_capital=10_000,
    )
    assert is_refusal(size) and size.category is RefusalCategory.POLICY_REJECTION
    assert size.context["axis"] == "starting_capital"
    assert "path-dependent" in str(size.context["reason"])
    print("forbidden starting_capital is path-dependent")

    assert view.home == "ungoverned"
    assert view.durable is False
    assert view.is_library_object is False
    print("ungoverned is a return value only")

    with TemporaryDirectory() as raw:
        root = Path(raw)
        governed = _unwrap(
            project(
                source_ct32=artifact,
                source_ct29=source_ct29,
                predicate={"hours": {"start": 8, "end": 16}},
                as_of=as_of,
                home="governed-without-qma",
                run_dir=root,
            ),
            "governed projection",
        )
        sidecar = root / PROJECTION_SIDECAR_FILENAME
        assert governed.durable is True
        assert governed.is_library_object is False
        assert governed.mints_ct32 is False
        assert governed.spawns_orchestrator is False
        assert sidecar.is_file()
        assert json.loads(sidecar.read_text(encoding="utf-8")) == governed.body()
        print("governed sidecar written")
        coordinated = project(
            source_ct32=artifact,
            source_ct29=source_ct29,
            predicate={"hours": {"start": 8, "end": 16}},
            as_of=as_of,
            home="coordinated",
            run_dir=root,
        )
        assert is_refusal(coordinated)
        assert coordinated.context["epic"] == "36"
        assert coordinated.context["opens_sqlite"] is False
        print("coordinated persistence is Epic 36")

    print(f"qmb {qmb.__version__}")
    print("analysis.project ok")


if __name__ == "__main__":
    artifact, source = operator_analysis_source()
    main(source_ct32=artifact, source_ct29=source)
