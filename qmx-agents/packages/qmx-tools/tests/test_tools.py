from __future__ import annotations

import asyncio
import runpy
from pathlib import Path
from typing import Any

import pytest
from fastmcp import Client
from qmf.core import World
from qmf.data import EvidenceStore
from qml.protocol import construct_bot
from qmn.doors.api import DoorRuntime
from qmx_control.models import MemoKey

from qmx_tools import DomainContext
from qmx_tools.functions import domain_functions
from qmx_tools.servers import create_server
from qmx_tools.service import Artifact, Dataset, OrderProposal, unwrap

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def context(tmp_path: Path) -> DomainContext:
    ctx = DomainContext(root=tmp_path)
    ctx.store = unwrap(EvidenceStore(tmp_path / "market").for_world(World.REPLAY)).append_store
    assert ctx.store is not None
    for kind in ("bars", "features", "calendar"):
        rows = [
            {"t": 1_700_000_000_000_000_000 + i * 60_000_000_000, "value": i, "kind": kind}
            for i in range(3)
        ]
        receipt = unwrap(ctx.store.append_raw(rows))
        ctx.datasets.append(
            Dataset(
                kind=kind, symbol="EURUSD", timeframe="1m", fingerprint=receipt.fingerprint.value
            )
        )
    # Reuse the engine's accepted configurations and recorded-slice fixtures.
    qmb = runpy.run_path(str(ROOT / "qmb/tests/test_ct32_artifact.py"))
    ctx.backtests["recorded"] = {
        "slices": qmb["_slices"](),
        "config": qmb["_config"](),
        "handler": qmb["SilentSliceHandler"](),
    }
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


def test_all_thirteen_tools_use_engines(context: DomainContext) -> None:
    functions = domain_functions(context)
    data = functions["data"]
    assert data["list_instruments"]()["result"] == [{"symbol": "EURUSD", "timeframe": "1m"}]
    for name in ("read_bars", "read_features", "calendar"):
        page = data[name](symbol="EURUSD", timeframe="1m", limit=2)
        assert len(page["result"]) == 2
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
    ref = started["run_id"]
    assert backtest["backtest_status"](run_id=ref)["result"]["status"] == "completed"
    assert backtest["backtest_results"](run_id=ref)["result"]["data_points_processed"] == 4
    assert len(backtest["backtest_results"](run_id=ref, response_format="detailed")["result"]) == 2
    assert backtest["compare_runs"](left=ref, right=ref)["result"] == []
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


def test_backtest_memo_reuses_the_real_engine_result(
    context: DomainContext, monkeypatch: pytest.MonkeyPatch
) -> None:
    import qmx_tools.service as service_module

    original = service_module.run
    calls = 0

    def counted(**arguments: Any) -> Any:
        nonlocal calls
        calls += 1
        return original(**arguments)

    monkeypatch.setattr(service_module, "run", counted)
    context.backtest_identities["recorded"] = MemoKey(
        strategy_version="strategy-v1",
        data_snapshot="recorded-slices-v1",
        params={"lookback": 20},
        engine_version="qmb-v1",
    )
    functions = domain_functions(context)["backtest"]
    first = functions["run_backtest"](spec={"config_ref": "recorded"})
    assert functions["run_backtest"](spec={"config_ref": "recorded"}) == first
    assert calls == 1
    assert len(context.control.library_search()) == 1
    assert len(context.control.events("library")) == 1
    assert first["result"]["memo_key"]
    reopened = DomainContext(root=context.root)
    reopened.backtests = context.backtests
    reopened.backtest_identities = context.backtest_identities
    assert (
        domain_functions(reopened)["backtest"]["run_backtest"](spec={"config_ref": "recorded"})
        == first
    )
    assert calls == 1
    reopened.backtest_identities["recorded"] = context.backtest_identities["recorded"].model_copy(
        update={"engine_version": "qmb-v2"}
    )
    domain_functions(reopened)["backtest"]["run_backtest"](spec={"config_ref": "recorded"})
    assert calls == 2


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
    ref = domain_functions(context)["backtest"]["run_backtest"](spec={"config_ref": "recorded"})[
        "result"
    ]["run_id"]
    calls.update(
        {
            "backtest_status": {"run_id": ref},
            "backtest_results": {"run_id": ref},
            "compare_runs": {"left": ref, "right": ref},
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
