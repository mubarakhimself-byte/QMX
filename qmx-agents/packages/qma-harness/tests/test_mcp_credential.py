"""A copilot chat and a workflow agent step get cTrader's Remote MCP with its token in the
`Authorization` header, read from Credential Manager at launch, only while the token's account is
a demo account record on the Library's main (C-36). The records land by C-34's own path, the host
passes its own reader, the keyring is in memory and the server is the fixture
`tools/lanes/fake_ctrader_mcp.py`. The token never reaches a chat record, a file or a log."""

from __future__ import annotations

import asyncio
import logging
import shutil
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any, override

import keyring
import pytest
from claude_agent_sdk import PermissionResultAllow
from claude_agent_sdk.types import ToolPermissionContext
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError
from qmx_apps.errors import AppError
from qmx_apps.manifest import Definition
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_host.host import account_worlds, open_store  # pyright: ignore[reportMissingTypeStubs]
from qmx_host.venue_records import land, records_of  # pyright: ignore[reportMissingTypeStubs]
from qmx_router.profiles import PLAN
from test_chat import FakeClient, blocks, gate_says, home
from test_demo_only import DEMO, LIVE, REMOTE_TOOLS, UNRECORDED, fake_url

from qma.harness import Harness, InjectedText, NewChat, OperatorText, SessionId
from qma.harness.home import QmxHome
from qma.harness.routes import control_service

__all__ = ["fake_url", "home"]

EXAMPLE = Path(__file__).resolve().parents[4] / "examples/apps/exchange-status"
LEFT_OUT = "the MCP server ctrader was refused: "


class Memory(KeyringBackend):
    priority = 1  # pyright: ignore[reportAssignmentType, reportIncompatibleMethodOverride]

    def __init__(self) -> None:
        super().__init__()
        self.held: dict[tuple[str, str], str] = {}

    @override
    def get_password(self, service: str, username: str) -> str | None:
        return self.held.get((service, username))

    @override
    def set_password(self, service: str, username: str, password: str) -> None:
        self.held[service, username] = password

    @override
    def delete_password(self, service: str, username: str) -> None:
        if self.held.pop((service, username), None) is None:
            raise PasswordDeleteError(service)


@pytest.fixture
def vault() -> Iterator[Memory]:
    before = keyring.get_keyring()
    memory = Memory()
    keyring.set_keyring(memory)
    try:
        yield memory
    finally:
        keyring.set_keyring(before)


def answer(account: str, world: str) -> dict[str, Any]:
    """A node `records` answer as C-34's node gives it, with no instruments."""
    return {
        "schema_version": "qmx.node.records/1",
        "venue": {"name": "icmarkets-ctrader", "platform": "ctrader", "sandbox": "demo"},
        "account": {"id": account, "world": world, "broker": "IC Markets"},
        "instruments": [],
        "missing": [],
    }


def launched(
    home: QmxHome,
    vault: Memory,
    url: str,
    held: str,
    body: Callable[[Harness], Awaitable[None]],
) -> None:
    """Runs `body` on a harness whose control service holds the enabled ctrader row, whose
    Library holds a demo record for 41500001 and a live one for 41500002, and whose keyring
    holds `held` as qmx/ctrader-mcp."""
    vault.set_password("qmx/ctrader-mcp", "ctrader-mcp", held)
    control = control_service(home)
    control.settings_put("mcp_servers", {"ctrader": {"url": url, "enabled": True}})

    async def main() -> None:
        with open_store(home.root, home.root / "library", serving=False, floor=0) as store:
            land(store, records_of(answer("41500001", "demo")))
            land(store, records_of(answer("41500002", "live")))
            control.attach_library(store)
            harness = await Harness.open(
                home, control=control, accounts=lambda account: account_worlds(control, account)
            )
            try:
                await body(harness)
            finally:
                await harness.close()

    asyncio.run(main())


def files_holding(root: Path, value: str) -> list[str]:
    return sorted(
        str(path.relative_to(root))
        for path in root.rglob("*")
        if path.is_file() and value.encode() in path.read_bytes()
    )


def connected_ctrader() -> list[dict[str, Any]]:
    tools = [{"name": f"mcp__ctrader__{tool}"} for tool in sorted(REMOTE_TOOLS)]
    return [{"name": "ctrader", "status": "connected", "tools": tools}]


def test_a_copilot_chat_on_a_demo_account_gets_the_header_and_no_file_or_log_holds_the_token(
    home: QmxHome,
    vault: Memory,
    fake_url: str,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    FakeClient.servers = connected_ctrader()

    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="copilot", model="haiku"))
        await harness.send(chat, OperatorText("EURUSD's last H1 bar?"))
        [client] = FakeClient.made
        assert dict(client.options.mcp_servers)["ctrader"] == {  # pyright: ignore[reportArgumentType]
            "type": "http",
            "url": fake_url,
            "headers": {"Authorization": f"Bearer {DEMO}"},
        }
        assert [kind for kind, _ in blocks(home, chat) if kind == "needs_you"] == []

    launched(home, vault, fake_url, DEMO, body)
    assert files_holding(tmp_path, DEMO) == []
    assert DEMO not in caplog.text


@pytest.mark.parametrize(
    ("held", "why"),
    [
        (LIVE, "account 41500002 is recorded as live, and agents use demo accounts only"),
        (
            UNRECORDED,
            "account 41500003 has no account record on the Library's main, and agents use demo "
            "accounts only",
        ),
    ],
)
def test_a_copilot_chat_on_any_other_account_starts_without_the_server_and_says_why(
    home: QmxHome, vault: Memory, fake_url: str, held: str, why: str
) -> None:
    async def body(harness: Harness) -> None:
        chat = await harness.start_chat(NewChat(title="copilot", model="haiku"))
        await harness.send(chat, OperatorText("EURUSD's last H1 bar?"))
        [client] = FakeClient.made
        assert "ctrader" not in dict(client.options.mcp_servers)  # pyright: ignore[reportArgumentType]
        notes = [content["reason"] for kind, content in blocks(home, chat) if kind == "needs_you"]
        assert notes == [LEFT_OUT + why]

    launched(home, vault, fake_url, held, body)


def test_a_workflow_step_naming_mcp_ctrader_gets_the_server_and_may_call_its_tools(
    home: QmxHome, vault: Memory, fake_url: str, tmp_path: Path
) -> None:
    async def body(harness: Harness) -> None:
        adapter = HarnessAdapter(harness)
        workspace = tmp_path / "step"
        step = await adapter.start_chat(
            title="run-1:read-bars",
            profile=PLAN,
            model="haiku",
            effort=None,
            workspace=workspace,
            toolsets=("mcp:ctrader",),
        )
        other = await adapter.start_chat(
            title="run-1:read-files",
            profile=PLAN,
            model="haiku",
            effort=None,
            workspace=workspace,
            tools=("Read",),
        )
        for chat, loads in ((step, connected_ctrader()), (other, [])):
            FakeClient.servers = loads
            await harness.send(SessionId(chat), InjectedText("go"))
        named, unnamed = FakeClient.made
        assert dict(named.options.mcp_servers)["ctrader"]["headers"] == {  # pyright: ignore[reportArgumentType, reportTypedDictNotRequiredAccess, reportUnknownMemberType]
            "Authorization": f"Bearer {DEMO}"
        }
        assert "ctrader" not in dict(unnamed.options.mcp_servers)  # pyright: ignore[reportArgumentType]
        assert await gate_says(named, "mcp__ctrader__get_trendbars") == "pass "
        asked = named.options.can_use_tool
        assert asked is not None
        allowed = await asyncio.wait_for(
            asked(
                "mcp__ctrader__get_trendbars",
                {"symbolId": 1, "period": "H_1"},
                ToolPermissionContext(tool_use_id="toolu_1"),
            ),
            30,
        )
        assert isinstance(allowed, PermissionResultAllow)

    launched(home, vault, fake_url, DEMO, body)


def test_no_app_manifest_may_declare_the_ctrader_mcp_token(tmp_path: Path) -> None:
    source = tmp_path / "asker"
    shutil.copytree(EXAMPLE, source, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    manifest = source / "app.toml"
    text = manifest.read_text(encoding="utf-8")
    manifest.write_text(
        text.replace("[capabilities]\n", "[capabilities]\nsecrets = { MCP = 'qmx/ctrader-mcp' }\n"),
        encoding="utf-8",
    )
    with pytest.raises(AppError) as refused:
        Definition.load(source)
    assert str(refused.value) == (
        "qmx/ctrader-mcp is the host's own cTrader MCP token, which acts on his cTrader account; "
        "no app may declare it."
    )
