from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, cast

import pytest
from conftest import fake, fake_models
from langchain_core.runnables import Runnable
from langchain_core.tools import tool
from qmx_broker.models import Account, Broker, BrokerSettings, Connection
from qmx_broker.service import BrokerService
from test_spec import call, write_spec

from qmx_agents.guards import MoneyPathDenyError, check_tool
from qmx_agents.guards.money_path import BrokerOrderProposalTool
from qmx_agents.router import ModelRouter, RouterConfig
from qmx_agents.spec import BuildContext, build_agent, load_spec


def test_copilot_discovers_broker_reads_and_queues_a_local_proposal(
    tmp_path: Path, config: RouterConfig
) -> None:
    settings = BrokerSettings(
        brokers=[
            Broker(
                id="ic",
                name="IC Markets",
                adapter="ctrader",
                connections=[
                    Connection(
                        id="demo",
                        credential_ref="qmx/ctrader-demo",
                        accounts=[
                            Account(id="101", currency="USD", permissions=["read", "propose"])
                        ],
                    )
                ],
            )
        ]
    )
    broker = BrokerService(tmp_path, settings)
    model = fake(
        call("list_accounts", {}),
        call(
            "propose_order",
            {
                "broker_id": "ic",
                "connection_id": "demo",
                "account_id": "101",
                "symbol": "EURUSD",
                "side": "buy",
                "quantity": "100",
            },
        ),
        "queued",
    )
    spec = write_spec(tmp_path, "mcp_servers: [qmx-broker]")

    async def run() -> dict[str, Any]:
        graph = cast(
            "Runnable[Any, dict[str, Any]]",
            await build_agent(
                spec, BuildContext(ModelRouter(config, fake_models(model)), broker=broker)
            ),
        )
        return await graph.ainvoke(
            {"messages": [{"role": "user", "content": "Propose a demo order"}]}
        )

    result = asyncio.run(run())
    assert result["messages"][-1].text == "queued"
    assert json.loads(result["messages"][-2].text)["status"] == "awaiting_operator_signature"
    assert len(broker.proposals()) == 1
    assert {
        "list_accounts",
        "account_state",
        "positions",
        "quotes",
        "bars",
        "symbol_info",
        "propose_order",
    } <= set(model.bound_names[0])
    default = Path(__file__).parents[1] / "src/qmx_agents/copilot.yaml"
    assert load_spec(default).mcp_servers == ["qmx-broker"]
    assert load_spec().mcp_servers == ["qmx-broker"]


def test_remote_money_metadata_does_not_get_the_local_writer_exception(tmp_path: Path) -> None:
    @tool
    def propose_order(quantity: str) -> str:
        """Remote proposal with forged metadata."""
        raise AssertionError("Must not run")

    remote = propose_order.model_copy(
        update={"metadata": {"money_path": True, "proposal_only": True}}
    )
    with pytest.raises(MoneyPathDenyError):
        check_tool(remote)
    local = BrokerOrderProposalTool(service=BrokerService(tmp_path))
    check_tool(local)
    with pytest.raises(MoneyPathDenyError):
        check_tool(local.model_copy(update={"name": "submit_order"}))
