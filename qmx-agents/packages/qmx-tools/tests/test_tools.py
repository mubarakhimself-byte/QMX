from __future__ import annotations

import asyncio
import json
import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import pytest
from fastmcp import Client
from qmf.core import Ok, Result
from qmf.data.store.refusals import policy_rejection
from qml.protocol import construct_bot
from qmn.doors.api import DoorRuntime
from qmx_control.library import OPERATOR
from qmx_judge.judge import spec_problems
from qmx_judge.tries import try_item
from qmx_library.kinds import Problem
from qmx_library.port import Draft
from qmx_library.principal import MAIN

from qmx_tools import DomainContext
from qmx_tools.functions import domain_functions
from qmx_tools.servers import create_server
from qmx_tools.service import Artifact, OrderProposal, unwrap

ROOT = Path(__file__).resolve().parents[4]
FIRST = 1_700_000_000_000_000_000


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
    ctx = DomainContext(root=tmp_path, market=FakeDoor())
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


RUN = "qmbr-pc-RECORDED"
TRADE = {
    "trade_id": "t1",
    "market_id": "fx.eurusd",
    "closed_at": 1_740_787_200_000_000_000,
    "money": "12.50",
    "r": "1.25",
}


def _landed_run(context: DomainContext, monkeypatch: pytest.MonkeyPatch) -> str:
    """One run as the lander leaves it: its two try rows and its result. QMB itself is never
    started here; the app's own tests start it (`qmx-agents/apps/qmb/tests`)."""
    store = context.library.store
    store.register_checker(
        "qmx.study-spec/1", lambda fields: [Problem(text) for text in spec_problems(fields)]
    )
    unit = store.put(OPERATOR, Draft("note", "u", "u", fields={}), on=MAIN, expected_head=None)
    report = json.dumps({"trades": [TRADE]}).encode()
    result = store.put(
        OPERATOR,
        Draft(
            "backtest-result",
            RUN,
            "backtest",
            fields={
                "run_id": RUN,
                "status": "finished",
                "principal": "agent:unnamed",
                "unit": unit.object_id,
                "measures": {"trades": 1, "net_money": "12.50", "total_r": "1.25"},
            },
            blobs={"report": report},
        ),
        on=MAIN,
        expected_head=None,
    ).object_id
    opened = {"kind": "run", "run_id": RUN, "unit": "u", "principal": "agent:unnamed"}
    store.put(
        OPERATOR,
        Draft("try", try_item(RUN, "opened"), "opened", fields={**opened, "state": "opened"}),
        on=MAIN,
        expected_head=None,
    )
    store.put(
        OPERATOR,
        Draft(
            "try",
            try_item(RUN, "landed"),
            "landed",
            fields={**opened, "state": "landed", "links": ["opened", result]},
        ),
        on=MAIN,
        expected_head=None,
    )

    def app_job(app_id: str, job: str, **asked: Any) -> dict[str, Any]:
        assert (app_id, job, asked["principal"]) == ("qmb", "jobs/backtest.py", "agent:unnamed")
        return {"run_id": RUN}

    monkeypatch.setattr(context.control, "app_job", app_job)
    return result


def test_all_thirteen_tools_use_engines(
    context: DomainContext, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    landed = _landed_run(context, monkeypatch)
    started = backtest["backtest_run"](
        unit="u", window={"start": "2025-03-01", "end": "2025-04-01"}
    )
    assert started["result"] == {"run_id": RUN, "status": "finished", "result_id": landed}
    status = backtest["backtest_status"](run_id=RUN)["result"]
    assert (status["state"], status["result_id"]) == ("landed", landed)
    read = backtest["backtest_results"](result_id=landed)
    assert read["summary"]["measures"]["total_r"] == "1.25"
    assert read["result"] == [TRADE]
    compared = backtest["backtest_compare"](left=landed, right=landed)
    assert (compared["same_trades"], compared["measures"]) == (True, {})
    judged = backtest["backtest_judge_run"](results=[landed])["result"]
    assert judged["says"] == (
        "Too thin to judge by the shipped preset. fx.eurusd is too thin to judge, 1 trade of "
        "the 100 needed. Behind it: 1 try, 1 effective."
    )
    assert (judged["overall"], judged["cards"]) == ("too_thin", {})
    store = context.library.store
    assert store.get(OPERATOR, judged["verdict_id"]).kind == "verdict"
    assert store.get(OPERATOR, judged["study"]).fields["origin"] == "quick"
    assert backtest["backtest_judge_run"](results=[landed])["result"] == judged
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


def test_the_backtest_reads_name_the_next_step_for_a_wrong_id(context: DomainContext) -> None:
    note = context.library.store.put(
        OPERATOR, Draft("note", "n", "n", fields={}), on=MAIN, expected_head=None
    ).object_id
    functions = domain_functions(context)["backtest"]
    with pytest.raises(ValueError, match="pass the run_id backtest_run answered"):
        functions["backtest_status"](run_id="qmbr-pc-none")
    with pytest.raises(ValueError, match="is a note; pass the result_id of a backtest"):
        functions["backtest_results"](result_id=note)
    with pytest.raises(ValueError, match="is a note; pass the result_id of a backtest"):
        functions["backtest_compare"](left=note, right=note)


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
    "server_name,count", [("data", 4), ("backtest", 5), ("research", 3), ("node", 2)]
)
def test_mcp_lists_and_calls_all_tools(
    context: DomainContext, server_name: str, count: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, dict[str, Any]] = {
        "list_instruments": {},
        "read_bars": {"symbol": "EURUSD", "timeframe": "1m"},
        "read_features": {"symbol": "EURUSD", "timeframe": "1m"},
        "calendar": {"symbol": "EURUSD", "timeframe": "1m"},
        "backtest_run": {"unit": "u", "window": {"start": "2025-03-01", "end": "2025-04-01"}},
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
    landed = _landed_run(context, monkeypatch) if server_name == "backtest" else ""
    calls.update(
        {
            "backtest_status": {"run_id": RUN},
            "backtest_results": {"result_id": landed},
            "backtest_compare": {"left": landed, "right": landed},
            "backtest_judge_run": {"results": [landed]},
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
