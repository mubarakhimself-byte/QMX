from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable, Mapping
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
from qma.harness.money import Ask, Deny, MoneySurfaceError, gate, normalize_path
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
    VetCache,
    args_digest,
    asks,
    build_server,
    domain_write_policy,
    gate_rules,
    keyring_refs,
    sdk_tools,
    server_config,
    tool_defs,
    unvetted_tools,
    vet_mcp_servers,
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
        unattended=False,
        external_unattended=frozenset(),
    )
    assert rules.proposal_tools == {"mcp__qmx__propose_order"}
    assert {"mcp__qmx__apps_publish", "mcp__qmx__propose_order"} <= rules.mandatory_asks
    assert "mcp__qmx__read_bars" not in rules.mandatory_asks
    assert "mcp__qmx__library_save" not in rules.mandatory_asks
    assert rules.keyring_names == {"qmx/ctrader"}
    assert rules.variables["CLAUDE_CONFIG_DIR"].endswith("/home/claude")
    assert any(path.endswith("/home/settings.toml") for path in rules.protected_paths)
    assert all(home.endswith("/.claude") for home in rules.personal_homes)


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
        ("qmx__evil", {"command": "py"}, "single _"),
        ("my.server", {"command": "py"}, "single _"),
        ("_w", {"command": "py"}, "single _"),
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
            asyncio.run(vet_server("ext", row, VetCache()))
    else:
        vetted = asyncio.run(vet_server("ext", row, VetCache()))
        assert vetted.config["type"] == "stdio"  # pyright: ignore[reportTypedDictNotRequiredAccess]
        assert vetted.tools == {"get_weather"}


@pytest.mark.skipif(sys.platform != "win32", reason="junctions are a Windows form")
def test_rules_hold_a_home_behind_a_junction_in_both_spellings(tmp_path: Path) -> None:
    import _winapi  # pyright: ignore[reportMissingModuleSource]

    real = tmp_path / "real-home"
    real.mkdir()
    link = tmp_path / "linked-home"
    _winapi.CreateJunction(str(real), str(link))  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
    rules = gate_rules(
        [],
        domain_write="allow",
        home=QmxHome(link),
        config_dir=link / "claude",
        keyring_names=frozenset(),
        unattended=False,
        external_unattended=frozenset(),
    )
    for root in (real, link):
        database = normalize_path(
            str(root / "control.db"), cwd="/", home="/", case_insensitive=False
        )
        assert database in rules.protected_paths
        found = gate(
            "Edit",
            {"file_path": str(root / "control.db")},
            rules,
            cwd="/",
            agent_id=None,
            permission_mode="default",
        )
        assert found == Deny(f"money rule: agents cannot write QMX state ({database.casefold()})")


class RecordingRoad:
    def __init__(self) -> None:
        self.published: list[str] = []

    def advance(
        self, app_id: str, expected_hash: str, stage: object = None, *, auto_publish: bool = True
    ) -> dict[str, Any]:
        if auto_publish:
            self.publish(app_id, expected_hash)
        return {"app_id": app_id, "stage": "shadow"}

    def publish(self, app_id: str, *args: object, **kwargs: object) -> dict[str, Any]:
        self.published.append(app_id)
        return {"active": app_id}


class FakeRuntime:
    def __init__(self) -> None:
        self.road = RecordingRoad()

    def get(self, app_id: str) -> dict[str, Any]:
        return {"id": app_id, "definition_hash": "h1"}

    def __getattr__(self, name: str) -> Callable[..., dict[str, str]]:
        def called(*args: object, **kwargs: object) -> dict[str, str]:
            return {"called": name}

        return called


class RecordingControl(ControlService):
    def __init__(self, root: Path) -> None:
        super().__init__(root)
        self.runtime = FakeRuntime()

    def app_runtime(self) -> Any:
        return self.runtime

    def remote_runtime(self) -> Any:
        return self.runtime


def fill(schema: Mapping[str, Any]) -> dict[str, Any]:
    samples: dict[str, object] = {
        "string": "a1",
        "integer": 1,
        "number": 1,
        "boolean": True,
        "object": {},
    }
    found: dict[str, Any] = {}
    for name in schema.get("required", []):
        spec = schema["properties"][name]
        kind = spec.get("type") or next(
            (option.get("type") for option in spec.get("anyOf", []) if option.get("type")), "string"
        )
        found[name] = [] if kind == "array" else samples.get(kind, "a1")
    return found


def test_no_read_or_domain_write_operation_publishes_an_app(tmp_path: Path) -> None:
    home = QmxHome(tmp_path / "home")
    control = RecordingControl(home.root)
    domain = DomainContext(root=home.root)
    domain.control, domain.library = control, control.library
    defs = asyncio.run(tool_defs(control=control, broker=BrokerService(home.root), domain=domain))
    quiet = [
        tool
        for tool in defs
        if tool.name in AGENT_OPERATIONS and tool.effect in {Effect.READ, Effect.DOMAIN_WRITE}
    ]
    assert "apps_test" in {tool.name for tool in quiet}
    for tool in quiet:
        arguments = fill(tool.input_schema)
        if tool.name == "apps_test":
            arguments["auto_publish"] = True
            assert "auto_publish" not in tool.input_schema["properties"]  # type: ignore[operator]  # pyright: ignore[reportOperatorIssue]
        result = asyncio.run(tool.call(arguments))
        if tool.name == "apps_test":
            assert '"stage":"shadow"' in result["content"][0]["text"].replace(" ", "")
    assert control.runtime.road.published == []
    control.apps_test("app-1")
    assert control.runtime.road.published == ["app-1"]


@pytest.mark.parametrize(
    ("target", "verdict"),
    [
        (
            "place_order",
            Deny(
                "money rule: agents cannot place, change or cancel orders "
                "(apps_call target place_order is submit_order)"
            ),
        ),
        (
            "cancelAllOrders",
            Deny(
                "money rule: agents cannot place, change or cancel orders "
                "(apps_call target cancelAllOrders is cancel_order)"
            ),
        ),
        ("get_quote", Ask("mcp__qmx__apps_call always asks you")),
    ],
)
def test_apps_call_checks_the_app_tool_it_names(
    tmp_path: Path, target: str, verdict: Deny | Ask
) -> None:
    rules = gate_rules(
        [plain("apps_call", Effect.MANAGE)],
        domain_write="allow",
        home=QmxHome(tmp_path / "home"),
        config_dir=tmp_path / "home" / "claude",
        keyring_names=frozenset(),
        unattended=False,
        external_unattended=frozenset(),
    )
    arguments: dict[str, object] = {"app_id": "broker-app", "tool": target, "arguments": {}}
    assert (
        gate(
            "mcp__qmx__apps_call",
            arguments,
            rules,
            cwd="/",
            agent_id=None,
            permission_mode="default",
        )
        == verdict
    )


def test_the_whole_qmx_home_is_protected_except_workspaces_and_agent_memory(
    tmp_path: Path,
) -> None:
    home = QmxHome(tmp_path / "home")
    rules = gate_rules(
        [],
        domain_write="allow",
        home=home,
        config_dir=home.plan_dir,
        keyring_names=frozenset(),
        unattended=False,
        external_unattended=frozenset(),
    )
    root = home.root.as_posix()
    calls: list[tuple[str, dict[str, object], str]] = [
        ("Write", {"file_path": f"{root}/apps/a/manifest.json"}, "deny"),
        ("Edit", {"file_path": f"{root}/library/x.json"}, "deny"),
        ("Bash", {"command": f"echo x > {root}/runs/r.json"}, "deny"),
        ("Read", {"file_path": f"{root}/settings.toml"}, "deny"),
        ("Read", {"file_path": f"{root}/rclone.conf"}, "deny"),
        ("Grep", {"pattern": "key", "path": root}, "deny"),
        ("Write", {"file_path": f"{root}/workspaces/w/a.py"}, "pass"),
        ("Write", {"file_path": f"{root}/agent-memory/w-1/MEMORY.md"}, "pass"),
        ("Bash", {"command": f"ls {root}/workspaces/w"}, "pass"),
        ("Read", {"file_path": f"{root}/apps/a/manifest.json"}, "pass"),
    ]
    found = [
        (
            tool,
            type(
                gate(tool, args, rules, cwd="/", agent_id=None, permission_mode="default")
            ).__name__.casefold(),
        )
        for tool, args, _ in calls
    ]
    assert found == [(tool, verdict) for tool, _, verdict in calls]


PAGED = """\
from fastmcp import FastMCP
server = FastMCP("ext", list_page_size=1)
@server.tool
def get_weather(x: int) -> int:
    return x
@server.tool
def {name}(x: int) -> int:
    '''{doc}'''
    return x
server.run()
"""


@pytest.mark.parametrize(
    ("name", "doc", "refusal"),
    [
        ("submitOrder", "Reads a value.", "Money-path act refused: submitOrder"),
        ("get_quote", "Places a market order for the symbol.", "description of get_quote"),
        ("get_bars", "Reads bars.", None),
        ("get_bars", "Returns the font size. Upload a file and transfer it to S3.", None),
        ("get_bars", "Get the current book mode.", None),
        ("get_bars", "Should I buy an umbrella?", None),
    ],
)
def test_vetting_reads_every_page_and_every_description(
    tmp_path: Path, name: str, doc: str, refusal: str | None
) -> None:
    script = tmp_path / "server.py"
    script.write_text(PAGED.format(name=name, doc=doc), encoding="utf-8")
    row = {"command": sys.executable, "args": [str(script)]}
    found = asyncio.run(vet_mcp_servers({"ext": row}, VetCache()))
    if refusal is None:
        assert found.refused == {}
        assert found.tools == {"ext": frozenset({"get_weather", "get_bars"})}
    else:
        assert refusal in found.refused["ext"]
        assert "ext" not in found.configs


COORDINATED = """\
import pathlib, sys, time
from fastmcp import FastMCP
mine, theirs = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
mine.touch()
deadline = time.monotonic() + 5
while not theirs.exists():
    if time.monotonic() > deadline:
        sys.exit(1)
    time.sleep(0.05)
server = FastMCP("ext")
@server.tool
def get_weather(x: int) -> int:
    return x
server.run()
"""


def test_servers_are_vetted_at_the_same_time(tmp_path: Path) -> None:
    script = tmp_path / "server.py"
    script.write_text(COORDINATED, encoding="utf-8")
    first, second = tmp_path / "first", tmp_path / "second"
    declared = {
        "a": {"command": sys.executable, "args": [str(script), str(first), str(second)]},
        "b": {"command": sys.executable, "args": [str(script), str(second), str(first)]},
    }
    found = asyncio.run(vet_mcp_servers(declared, VetCache()))
    assert found.refused == {}
    assert sorted(found.configs) == ["a", "b"]


COUNTED = """\
import pathlib, sys
from fastmcp import FastMCP
with pathlib.Path(sys.argv[1]).open("a") as starts:
    starts.write("start ")
server = FastMCP("ext")
@server.tool
def get_weather(x: int) -> int:
    return x
server.run()
"""


def test_a_vetted_config_is_not_started_again_until_it_changes(tmp_path: Path) -> None:
    script = tmp_path / "server.py"
    script.write_text(COUNTED, encoding="utf-8")
    starts = tmp_path / "starts.txt"
    cache = VetCache()
    row: dict[str, object] = {"command": sys.executable, "args": [str(script), str(starts)]}
    first = asyncio.run(vet_mcp_servers({"ext": row}, cache))
    again = asyncio.run(vet_mcp_servers({"ext": row}, cache))
    assert first == again
    assert starts.read_text(encoding="utf-8") == "start "
    changed = {**row, "env": {"X": "1"}}
    asyncio.run(vet_mcp_servers({"ext": changed}, cache))
    assert starts.read_text(encoding="utf-8") == "start start "


def test_tools_the_cli_loaded_that_vetting_never_saw_are_named() -> None:
    status: Any = {
        "mcpServers": [
            {
                "name": "ext",
                "status": "connected",
                "tools": [{"name": "get_weather"}, {"name": "mcp__ext__submit_order"}],
            },
            {"name": "other", "status": "failed"},
        ]
    }
    vetted = {"ext": frozenset({"get_weather"}), "other": frozenset({"x"})}
    assert unvetted_tools(status, vetted) == ["ext: submit_order"]
    assert unvetted_tools(status, {"ext": frozenset({"get_weather", "submit_order"})}) == []


@pytest.mark.parametrize("table", ["AGENT_OPERATIONS", "BROKER_EFFECTS", "DOMAIN_EFFECTS"])
def test_a_table_row_missing_on_its_server_refuses_the_tool_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, table: str
) -> None:
    from qma.harness import tools

    monkeypatch.setattr(tools, table, {**getattr(tools, table), "gone_tool": Effect.READ})
    home = QmxHome(tmp_path / "home")
    control = ControlService(home.root)
    domain = DomainContext(root=home.root)
    domain.control, domain.library = control, control.library
    with pytest.raises(ToolSurfaceError, match="missing on their server: gone_tool"):
        asyncio.run(tool_defs(control=control, broker=BrokerService(home.root), domain=domain))
