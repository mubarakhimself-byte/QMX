from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from qmx_broker.service import BrokerService
from qmx_control.server import OPERATIONS
from qmx_control.service import ControlService
from qmx_tools.functions import domain_functions
from qmx_tools.service import DomainContext

from qma.harness.home import QmxHome
from qma.harness.money import MoneySurfaceError
from qma.harness.tools import (
    AGENT_OPERATIONS,
    DOMAIN_EFFECTS,
    DOMAIN_LEFT_OUT,
    OPERATIONS_LEFT_OUT,
    Effect,
    Grant,
    Grants,
    ToolDef,
    ToolSurfaceError,
    args_digest,
    asks,
    build_server,
    domain_write_policy,
    gate_rules,
    keyring_refs,
    sdk_tools,
    server_config,
    tool_defs,
    vet_server,
)


async def nothing(arguments: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": f"ran {sorted(arguments)}"}]}


def plain(name: str, effect: Effect = Effect.READ, target: object = None) -> ToolDef:
    return ToolDef(name, name, {"type": "object"}, effect, nothing, target=target)


def test_every_control_operation_is_declared_or_left_out_by_name() -> None:
    names = {row[0] for row in OPERATIONS}
    assert set(AGENT_OPERATIONS) | set(OPERATIONS_LEFT_OUT) == names
    assert not set(AGENT_OPERATIONS) & set(OPERATIONS_LEFT_OUT)
    assert {"settings_put", "backup_weekly"} <= set(OPERATIONS_LEFT_OUT)


def test_every_destructive_operation_is_manage() -> None:
    wrong = [
        name
        for name, _, _, destructive in OPERATIONS
        if destructive and name in AGENT_OPERATIONS and AGENT_OPERATIONS[name] is not Effect.MANAGE
    ]
    assert wrong == []


def test_every_domain_function_is_declared_or_left_out_by_name() -> None:
    names = {name for group in domain_functions(MagicMock()).values() for name in group}
    assert set(DOMAIN_EFFECTS) | set(DOMAIN_LEFT_OUT) == names
    assert not set(DOMAIN_EFFECTS) & set(DOMAIN_LEFT_OUT)


def test_asks_table() -> None:
    table = {
        (effect, policy): asks(effect, policy) for effect in Effect for policy in ("allow", "ask")
    }
    assert table == {
        (Effect.READ, "allow"): False,
        (Effect.READ, "ask"): False,
        (Effect.DOMAIN_WRITE, "allow"): False,
        (Effect.DOMAIN_WRITE, "ask"): True,
        (Effect.MANAGE, "allow"): True,
        (Effect.MANAGE, "ask"): True,
        (Effect.PROPOSE_MONEY, "allow"): True,
        (Effect.PROPOSE_MONEY, "ask"): True,
    }
    assert [domain_write_policy(v) for v in ({}, {"domain_write": "ask"}, {"domain_write": 1})] == [
        "allow",
        "ask",
        "ask",
    ]


def test_s28_a_tool_with_no_effect_does_not_construct() -> None:
    with pytest.raises(TypeError, match="missing 1 required positional argument: 'call'"):
        ToolDef("read_x", "read", {}, nothing)  # type: ignore[call-arg]  # pyright: ignore[reportCallIssue, reportArgumentType]
    bad: Any = None
    with pytest.raises(TypeError, match="read_x declares no Effect"):
        ToolDef("read_x", "read", {}, bad, nothing)


def test_s28_a_tool_named_place_order_refuses_the_build() -> None:
    with pytest.raises(MoneySurfaceError, match="Money-path act refused: place_order"):
        build_server(
            [plain("read_bars"), plain("place_order")], grants=Grants(), domain_write="allow"
        )


def test_s28_a_second_propose_money_tool_refuses_the_build(tmp_path: Path) -> None:
    broker = BrokerService(tmp_path)
    real = plain("propose_order", Effect.PROPOSE_MONEY, broker.propose_order)
    impostor = plain("stage_trade", Effect.PROPOSE_MONEY, lambda: None)
    build_server([real], grants=Grants(), domain_write="allow")
    with pytest.raises(MoneySurfaceError, match="stage_trade is not the broker's propose_order"):
        build_server([real, impostor], grants=Grants(), domain_write="allow")


def test_a_duplicate_name_refuses_the_build() -> None:
    with pytest.raises(ToolSurfaceError, match="duplicate QMX tool names: read_bars"):
        build_server(
            [plain("read_bars"), plain("read_bars")], grants=Grants(), domain_write="allow"
        )


def test_an_asking_tool_runs_once_per_grant_for_its_exact_arguments() -> None:
    grants = Grants()
    [tool] = sdk_tools([plain("apps_publish", Effect.MANAGE)], grants, "allow")
    refused = asyncio.run(tool.handler({"app_id": "a"}))
    assert refused["is_error"] is True
    assert "no approval was given" in refused["content"][0]["text"]
    grants.record(
        Grant("mcp__qmx__apps_publish", args_digest("mcp__qmx__apps_publish", {"app_id": "a"}))
    )
    assert asyncio.run(tool.handler({"app_id": "b"}))["is_error"] is True
    assert asyncio.run(tool.handler({"app_id": "a"})) == {
        "content": [{"type": "text", "text": "ran ['app_id']"}]
    }
    assert asyncio.run(tool.handler({"app_id": "a"}))["is_error"] is True


def test_grants_off_and_reads_skip_the_grant() -> None:
    [manage] = sdk_tools(
        [plain("apps_publish", Effect.MANAGE)], Grants(), "allow", enforce_grants=False
    )
    [read] = sdk_tools([plain("read_bars")], Grants(), "ask")
    assert "is_error" not in asyncio.run(manage.handler({}))
    assert "is_error" not in asyncio.run(read.handler({}))


def test_args_digest_is_canonical() -> None:
    assert args_digest("t", {"b": 1, "a": [1, 2]}) == args_digest("t", {"a": [1, 2], "b": 1})
    assert args_digest("t", {"a": 1}) != args_digest("u", {"a": 1})


def test_the_real_tool_list_builds_and_derives_the_gate(tmp_path: Path) -> None:
    home = QmxHome(tmp_path / "home")
    control = ControlService(home.root)
    domain = DomainContext(root=home.root)
    domain.control, domain.library = control, control.library
    defs = asyncio.run(tool_defs(control=control, broker=BrokerService(home.root), domain=domain))
    effects = {tool.name: tool.effect for tool in defs}
    assert len(defs) == len(AGENT_OPERATIONS) + 7 + len(DOMAIN_EFFECTS)
    assert effects["propose_order"] is Effect.PROPOSE_MONEY
    assert [name for name, effect in effects.items() if effect is Effect.PROPOSE_MONEY] == [
        "propose_order"
    ]
    build_server(defs, grants=Grants(), domain_write="ask")
    rules = gate_rules(
        defs,
        domain_write="allow",
        home=home,
        config_dir=home.plan_dir,
        keyring_names=frozenset({"QMX/ctrader"}),
    )
    assert rules.proposal_tools == {"mcp__qmx__propose_order"}
    assert {"mcp__qmx__apps_publish", "mcp__qmx__propose_order"} <= rules.mandatory_asks
    assert "mcp__qmx__read_bars" not in rules.mandatory_asks
    assert "mcp__qmx__library_save" not in rules.mandatory_asks
    assert rules.keyring_names == {"qmx/ctrader"}
    assert rules.variables["CLAUDE_CONFIG_DIR"].endswith("/home/claude")
    assert any(path.endswith("/home/settings.toml") for path in rules.protected_paths)
    assert rules.personal_home.endswith("/.claude")


def test_keyring_refs_reads_names_from_three_sections(tmp_path: Path) -> None:
    control = ControlService(tmp_path)
    control.settings_put(
        "providers",
        {"kimi": {"base_url": "https://x", "credential_ref": "qmx/Kimi", "tiers": {}}},
    )
    assert keyring_refs(control) == {
        "qmx/kimi",
        "qmx/chatgpt",
        "qmx/control-token",
        "qmx/firecrawl",
    }


def test_server_config_shapes() -> None:
    assert server_config("w", {"command": "py", "args": ["s.py", 1]}) == {
        "type": "stdio",
        "command": "py",
        "args": ["s.py", "1"],
        "env": {},
    }
    assert server_config("w", {"url": "http://127.0.0.1:9/mcp"}) == {
        "type": "http",
        "url": "http://127.0.0.1:9/mcp",
    }
    for name, row, message in [
        ("qmx", {"command": "py"}, "belongs to QMX"),
        ("f", {"url": "https://x", "credential_ref": "qmx/f"}, "stored credential"),
        ("f", {}, "a command or a url"),
    ]:
        with pytest.raises(ValueError, match=message):
            server_config(name, row)


SERVER = """\
from fastmcp import FastMCP
server = FastMCP("ext")
@server.tool
def {name}(x: int) -> int:
    return x
server.run()
"""


@pytest.mark.parametrize(("tool", "refused"), [("get_weather", False), ("submitOrder", True)])
def test_vetting_starts_the_server_and_checks_its_tools(
    tmp_path: Path, tool: str, refused: bool
) -> None:
    script = tmp_path / "server.py"
    script.write_text(SERVER.format(name=tool), encoding="utf-8")
    row = {"command": sys.executable, "args": [str(script)]}
    if refused:
        with pytest.raises(MoneySurfaceError, match="Money-path act refused: submitOrder"):
            asyncio.run(vet_server("ext", row))
    else:
        assert asyncio.run(vet_server("ext", row))["type"] == "stdio"  # pyright: ignore[reportTypedDictNotRequiredAccess]
