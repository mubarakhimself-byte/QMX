from __future__ import annotations

import asyncio
import runpy
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, cast

import pytest
from fastmcp import Client
from qmb.host.library_landing import BacktestResult, Stored
from qmb.results.ct32 import as_ct32_artifact
from qmf.core import Ok, Result
from qmf.data.store.refusals import policy_rejection
from qml.protocol import construct_bot
from qmn.doors.api import DoorRuntime

from qmx_tools import DomainContext
from qmx_tools.functions import domain_functions
from qmx_tools.servers import create_server
from qmx_tools.service import Artifact, BacktestRun, OrderProposal, unwrap

ROOT = Path(__file__).resolve().parents[4]
FIRST = 1_700_000_000_000_000_000


class FakeQmbBacktest:
    """The engine's `qmb_backtest` door: one finished result and the edges it lands with."""

    def __init__(self) -> None:
        self.specs: list[dict[str, Any]] = []

    def run(self, *, spec: Mapping[str, Any]) -> Result[BacktestRun]:
        self.specs.append(dict(spec))
        return Ok(
            BacktestRun(
                result=BacktestResult(
                    run_id="fp1:sha256:recorded-run",
                    title="recorded",
                    summary="one recorded backtest",
                    world="backtest",
                    claim_class="retrospective",
                    role="confirmation",
                    fidelity="bar-m1",
                    provenance={"config_ref": "recorded"},
                    report=b'{"data_points_processed": 4}',
                    outcome="supports",
                    memo_key="recorded-memo",
                ),
                consumed="dataset-card-v3",
                uses="bot-version-7",
                tests="hypothesis-2",
            )
        )


class RecordingLanding:
    """The new Library, recording the one put and the edges the landing step writes."""

    def __init__(self) -> None:
        self.puts: list[dict[str, Any]] = []
        self.links: list[tuple[str, str, str]] = []

    def put(
        self,
        kind: str,
        fields: Any,
        blobs: Any,
        *,
        item: Any,
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
        return Stored("landed-1")

    def link(self, from_id: str, relation: str, to_id: str, *, principal: str) -> str:
        self.links.append((from_id, relation, to_id))
        return f"{from_id}-{relation}-{to_id}"


@dataclass(frozen=True)
class FakeSeries:
    series: str
    subject: str
    kind: str


@dataclass(frozen=True)
class FakeRead:
    series: str
    fingerprints: tuple[str, ...]
    rows: tuple[dict[str, object], ...]


class FakeDoor:
    """The host's market-data door, answering the tools with three series of three rows."""

    kind_of: ClassVar[dict[str, str]] = {
        "dukascopy/EURUSD/bar-1m/-": "bars",
        "derived/EURUSD/feature-1m/-": "features",
        "dukascopy/EURUSD/calendar/-": "calendar",
    }

    def instruments(self) -> Result[Any]:
        return Ok(
            tuple(
                FakeSeries(series=series, subject="EURUSD", kind=series.split("/")[2])
                for series in self.kind_of
            )
        )

    def card(self, series: str) -> Result[Any]:
        return Ok({"card": series, "digests": ["fp1:sha256:recorded"]})

    def read(self, series: str = "", **arguments: Any) -> Result[Any]:
        return Ok(
            FakeRead(
                series=series,
                fingerprints=("fp1:sha256:recorded",),
                rows=self._rows(
                    self.kind_of[series], arguments.get("start_ns"), arguments.get("end_ns")
                ),
            )
        )

    def _rows(self, kind: str, start: int | None, end: int | None) -> tuple[dict[str, object], ...]:
        return tuple(
            {"t": FIRST + i * 60_000_000_000, "value": i, "kind": kind}
            for i in range(3)
            if (start is None or FIRST + i * 60_000_000_000 >= start)
            and (end is None or FIRST + i * 60_000_000_000 <= end)
        )


class SealedDoor(FakeDoor):
    """The same door, refusing the month the test asks for the way the real one refuses."""

    def read(self, series: str = "", **arguments: Any) -> Result[Any]:
        return policy_rejection(
            "seal",
            "this month is sealed for the final look; a read into the sealed no-peek window is "
            "refused at the split-governed research door",
            months=[series],
        )


@pytest.fixture
def context(tmp_path: Path) -> DomainContext:
    ctx = DomainContext(
        root=tmp_path,
        market=FakeDoor(),
        backtest_door=FakeQmbBacktest(),
        landing=RecordingLanding(),
    )
    ctx.backtests["recorded"] = {"config_ref": "recorded"}
    qml = runpy.run_path(str(ROOT / "qml/tests/test_protocol.py"))
    ctx.bots["recorded"] = unwrap(
        construct_bot(
            qml["_silent_factory"](),
            declaration=qml["_declaration"](),
            assignment={"lookback": 20},
            read_surfaces={},
        )
    )
    ctx.node = DoorRuntime(
        boot_epoch="recorded-boot",
        composition_fp="recorded",
        knowledge_time_ns=1,
        watermark_ns=1,
        source_time_ns=1,
        receive_time_ns=1,
        evidence_channel_budget=100,
        authority_source="replicated-evidence",
    )
    return ctx


def test_a_sealed_month_is_refused_with_its_reason(tmp_path: Path) -> None:
    context = DomainContext(root=tmp_path, market=SealedDoor())
    with pytest.raises(ValueError, match="this month is sealed for the final look"):
        domain_functions(context)["data"]["read_bars"](symbol="EURUSD", timeframe="1m")


def _legacy_backtest(context: DomainContext) -> str:
    """An old-shape `backtest` artifact already in the Library, for the read tools to read."""
    qmb = runpy.run_path(str(ROOT / "qmb/tests/test_ct32_artifact.py"))
    outcome = qmb["_run"]()
    artifact = unwrap(as_ct32_artifact(outcome.performance_result))
    return context.save(
        Artifact(
            name="legacy-recorded",
            kind="backtest",
            content={
                "data_points_processed": 4,
                "filled": 1,
                "stream_order": ["eurusd"],
                "slices": [{"i": 1}, {"i": 2}],
                "performance_result": artifact,
            },
        )
    )["ref"]


def test_all_thirteen_tools_use_engines(context: DomainContext) -> None:
    functions = domain_functions(context)
    data = functions["data"]
    assert data["list_instruments"]()["result"] == [
        {"symbol": "EURUSD", "timeframe": "bar-1m", "series": "dukascopy/EURUSD/bar-1m/-"},
        {"symbol": "EURUSD", "timeframe": "feature-1m", "series": "derived/EURUSD/feature-1m/-"},
        {"symbol": "EURUSD", "timeframe": "calendar", "series": "dukascopy/EURUSD/calendar/-"},
    ]
    for name in ("read_bars", "read_features", "calendar"):
        page = data[name](symbol="EURUSD", timeframe="1m", limit=2)
        assert len(page["result"]) == 2
        assert (
            page["card"]
            == {
                "read_bars": "dukascopy/EURUSD/bar-1m/-",
                "read_features": "derived/EURUSD/feature-1m/-",
                "calendar": "dukascopy/EURUSD/calendar/-",
            }[name]
        )
        expected_kind = {"read_bars": "bars", "read_features": "features", "calendar": "calendar"}
        assert all(row["kind"] == expected_kind[name] for row in page["result"])
        instant = 1_700_000_000_000_000_000 + 60_000_000_000
        window = data[name](symbol="EURUSD", timeframe="1m", start=instant, end=instant)
        assert [row["value"] for row in window["result"]] == [1]
        assert page["next_cursor"] == 2
        last = data[name](symbol="EURUSD", timeframe="1m", cursor=2)
        assert last["result"][0]["value"] == 2
        assert last["next_cursor"] is None
    backtest = functions["backtest"]
    started = backtest["run_backtest"](spec={"config_ref": "recorded"})["result"]
    assert started["status"] == "completed"
    assert started["run_id"] == "landed-1"
    assert started["edges"] == [
        ["consumed", "dataset-card-v3"],
        ["uses", "bot-version-7"],
        ["tests", "hypothesis-2"],
    ]
    assert started["memo_key"] == "recorded-memo"
    legacy = _legacy_backtest(context)
    assert backtest["backtest_status"](run_id=legacy)["result"]["status"] == "completed"
    assert backtest["backtest_results"](run_id=legacy)["result"]["data_points_processed"] == 4
    assert (
        len(backtest["backtest_results"](run_id=legacy, response_format="detailed")["result"]) == 2
    )
    assert backtest["compare_runs"](left=legacy, right=legacy)["result"] == []
    research = functions["research"]
    assert (
        research["qml_run"](bot_ref="recorded", instants=[1_700_000_000_000_000_000])["result"][0][
            "intents"
        ]
        == []
    )
    saved = research["library_save"](
        artifact={"name": "report", "kind": "note", "content": "recorded result"}
    )["result"]
    assert context.artifact(saved["ref"]).content == "recorded result"
    assert research["library_search"](query="report")["result"][0]["ref"] == saved["ref"]
    node = functions["node"]
    assert node["node_state"]()["result"]["acts"] is False
    proposal = node["propose_order"](
        proposal={
            "account": "recorded-account",
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": "0.10",
            "reason": "operator review",
        }
    )["result"]
    assert proposal["executed"] is False
    assert proposal["status"] == "awaiting_operator_signature"
    assert context.artifact(proposal["proposal"]["ref"]).content["quantity"] == "0.10"


def test_a_backtest_lands_one_result_and_writes_no_old_backtest_item(
    context: DomainContext,
) -> None:
    door = cast("FakeQmbBacktest", context.backtest_door)
    landing = cast("RecordingLanding", context.landing)

    result = domain_functions(context)["backtest"]["run_backtest"](spec={"config_ref": "recorded"})[
        "result"
    ]

    assert door.specs == [{"config_ref": "recorded"}]
    [put] = landing.puts
    assert put["kind"] == "backtest-result"
    assert put["item"] == "fp1:sha256:recorded-run"
    assert put["fields"]["outcome"] == "supports"
    assert put["fields"]["world"] == "backtest"
    assert put["blobs"] == {"report": b'{"data_points_processed": 4}'}
    assert landing.links == [
        ("landed-1", "consumed", "dataset-card-v3"),
        ("landed-1", "uses", "bot-version-7"),
        ("landed-1", "tests", "hypothesis-2"),
    ]
    assert result["edges"] == [
        ["consumed", "dataset-card-v3"],
        ["uses", "bot-version-7"],
        ["tests", "hypothesis-2"],
    ]
    assert context.control.library_search() == []


def test_a_host_without_the_qmb_door_refuses_a_backtest(tmp_path: Path) -> None:
    context = DomainContext(root=tmp_path, market=FakeDoor())
    context.backtests["recorded"] = {"config_ref": "recorded"}

    with pytest.raises(ValueError, match="binds no qmb_backtest door"):
        domain_functions(context)["backtest"]["run_backtest"](spec={"config_ref": "recorded"})


def test_domain_refs_preserve_type_when_payloads_match(context: DomainContext) -> None:
    note = context.save(Artifact(name="note", kind="note", content={"value": 1}))
    report = context.save(Artifact(name="report", kind="report", content={"value": 1}))
    assert note["ref"] != report["ref"]
    assert context.artifact(note["ref"]).kind == "note"
    assert context.artifact(report["ref"]).kind == "report"
    assert context.artifact(note["ref"]).content == context.artifact(report["ref"]).content


def test_artifact_spill_restart_and_ref_confinement(context: DomainContext) -> None:
    context.inline_bytes = 20
    result = context.output({"payload": "x" * 100}, "large", "detailed")
    reopened = DomainContext(root=context.root)
    assert reopened.artifact(result["artifact"]["ref"]).content["payload"] == "x" * 100
    with pytest.raises(ValueError, match="artifacts"):
        reopened.artifact("../outside.json")
    saved = context.save(Artifact(name="immutable", kind="note", content="content"))
    assert saved == context.save(Artifact(name="immutable", kind="note", content="content"))
    (context.root / saved["ref"]).write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        reopened.artifact(saved["ref"])


def test_malformed_library_artifacts_have_actionable_backtest_errors(
    context: DomainContext,
) -> None:
    ref = context.save(Artifact(name="malformed", kind="backtest", content=None))["ref"]
    functions = domain_functions(context)["backtest"]
    for name in ("backtest_status", "backtest_results"):
        with pytest.raises(ValueError, match="run_id returned by run_backtest"):
            functions[name](run_id=ref)
    with pytest.raises(ValueError, match="library_search"):
        functions["compare_runs"](left=ref, right=ref)


def test_order_proposal_cannot_carry_execution_authority() -> None:
    proposal = {
        "account": "recorded",
        "symbol": "EURUSD",
        "side": "buy",
        "quantity": "0.1",
        "reason": "review",
    }
    with pytest.raises(ValueError, match="decimal string"):
        OrderProposal.model_validate({**proposal, "quantity": 0.1})
    with pytest.raises(ValueError, match="Extra inputs"):
        OrderProposal.model_validate({**proposal, "operator_signature": "invented"})


@pytest.mark.parametrize(
    "server_name,count", [("data", 4), ("backtest", 4), ("research", 3), ("node", 2)]
)
def test_mcp_lists_and_calls_all_tools(
    context: DomainContext, server_name: str, count: int
) -> None:
    calls: dict[str, dict[str, Any]] = {
        "list_instruments": {},
        "read_bars": {"symbol": "EURUSD", "timeframe": "1m"},
        "read_features": {"symbol": "EURUSD", "timeframe": "1m"},
        "calendar": {"symbol": "EURUSD", "timeframe": "1m"},
        "run_backtest": {"spec": {"config_ref": "recorded"}},
        "qml_run": {"bot_ref": "recorded", "instants": [1_700_000_000_000_000_000]},
        "library_search": {},
        "library_save": {"artifact": {"name": "note", "kind": "note", "content": "saved"}},
        "node_state": {},
        "propose_order": {
            "proposal": {
                "account": "recorded",
                "symbol": "EURUSD",
                "side": "sell",
                "quantity": "1",
                "reason": "review",
            }
        },
    }
    domain_functions(context)["backtest"]["run_backtest"](spec={"config_ref": "recorded"})
    legacy = _legacy_backtest(context)
    calls.update(
        {
            "backtest_status": {"run_id": legacy},
            "backtest_results": {"run_id": legacy},
            "compare_runs": {"left": legacy, "right": legacy},
        }
    )

    async def check() -> None:
        async with Client(create_server(server_name, context)) as client:
            listed = await client.list_tools()
            assert len(listed) == count
            for item in listed:
                result = await client.call_tool(item.name, calls[item.name])
                assert result.data is not None
                assert not result.is_error

    asyncio.run(check())
