"""AGW (engine AD-60, AD-214, probe P-PERM): an agent step that declares `Write` and `Edit` is
offered exactly those by the harness's own selection, with `Bash` and `PowerShell` denied; a file
write outside its attempt overlay is refused with a reason; and only its declared `outputs.files`
commit into the run's `work/`."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast

from fake_port import CARD, FakePort, agent, agent_files, drive, events_of
from flows import edge, folder, node
from qma.harness import AllowOnce, Harness, NewChat, PolicyCall, QmxHome, Reject, SessionId
from qma.harness.home import PLAN, ProfileName
from qma.harness.launch import Background, Home, sandbox_builtins
from qma.harness.surface import HomeSlots, Supply, build, declaration

from qmx_engine.policy import engine_policy
from qmx_engine.ports.harness_adapter import HarnessAdapter, Turn
from qmx_engine.workers.zones import RunZone

CHAT = SessionId("s1")


class Births:
    """A harness stand-in that keeps each chat's `NewChat` and launches nothing."""

    def __init__(self) -> None:
        self.specs: list[NewChat] = []

    def register_sink(self, name: str, sink: object) -> None: ...

    def register_policy(self, name: str, policy: object) -> None: ...

    async def start_chat(self, spec: NewChat) -> SessionId:
        self.specs.append(spec)
        return CHAT


def born(tmp_path: Path, tools: tuple[str, ...]) -> NewChat:
    births = Births()
    adapter = HarnessAdapter(cast(Harness, births))
    asyncio.run(
        adapter.start_chat(
            title="run:write:0:1",
            profile="claude",
            model="haiku",
            effort=None,
            workspace=tmp_path / "attempt",
            tools=tools,
        )
    )
    return births.specs[0]


def offered(tmp_path: Path, spec: NewChat) -> tuple[str, ...]:
    """The built-ins the CLI is launched with: the harness's own Surface selection, then the
    launch filter `launch.py` applies to `tools`."""
    home = QmxHome(tmp_path / "qmx", plugin_dir=tmp_path / "plugin")
    config = spec.config(ProfileName(PLAN), tmp_path / "attempt", Home())
    supply = Supply((), HomeSlots(home), {}, (), tmp_path / "spill")
    surface = build(
        Background(), Home(), (), declaration(config), supply, workspace=tmp_path / "attempt"
    )
    return sandbox_builtins(surface.builtins, {})


def test_a_step_declaring_write_and_edit_is_offered_them_and_never_a_shell(
    tmp_path: Path,
) -> None:
    spec = born(tmp_path, ("Write", "Edit"))

    assert offered(tmp_path, spec) == ("Write", "Edit")
    assert spec.permissions.deny == ("Bash", "PowerShell")
    assert dict(spec.policy_args) == {
        "tools": ["Write", "Edit"],
        "overlay": str((tmp_path / "attempt").resolve()),
    }
    assert spec.workspace == tmp_path / "attempt"


def test_a_step_that_declares_bash_keeps_it_and_only_powershell_is_denied(tmp_path: Path) -> None:
    spec = born(tmp_path, ("Bash", "Write"))

    assert offered(tmp_path, spec) == ("Bash", "Write")
    assert spec.permissions.deny == ("PowerShell",)


def ask(tool: str, overlay: Path | None, **tool_input: object) -> PolicyCall:
    args: dict[str, object] = {"tools": ["Write", "Edit", "Bash"]}
    if overlay is not None:
        args["overlay"] = str(overlay)
    return PolicyCall(CHAT, tool, dict(tool_input), args, None)


def test_a_file_write_is_allowed_only_under_the_overlay(tmp_path: Path) -> None:
    overlay = tmp_path / "attempt"
    overlay.mkdir()
    calls = [
        ask("Write", overlay, file_path=str(overlay / "result.md"), content="ok"),
        ask("Edit", overlay, file_path="notes/today.md"),
        ask("Write", overlay, file_path=str(tmp_path / "outside.md"), content="x"),
        ask("Edit", overlay, file_path="../outside.md"),
        ask("Write", overlay, content="no path"),
        ask("Bash", overlay, command="echo hi"),
        ask("PowerShell", overlay, command="Get-Date"),
        ask("Write", None, file_path=str(overlay / "result.md"), content="ok"),
    ]

    async def answers() -> list[object]:
        return [await engine_policy(call) for call in calls]

    outside = f"is refused: this step writes only under its attempt folder {overlay}."
    assert asyncio.run(answers()) == [
        AllowOnce(),
        AllowOnce(),
        Reject(f"Write {outside}"),
        Reject(f"Edit {outside}"),
        Reject(f"Write {outside}"),
        AllowOnce(),
        Reject("PowerShell is refused: this step declares only Write, Edit, Bash. Use those."),
        Reject(
            "Write is refused: steps of this workflow are read-only, so no file is written and no "
            "command runs. Answer from what you can read."
        ),
    ]


class Workspaces(FakePort):
    """A fake port that keeps the folder each chat was born in."""

    def __init__(self, *answers: Any) -> None:
        super().__init__(*answers)
        self.workspaces: list[Path] = []

    async def start_chat(self, *, workspace: Path, **rest: Any) -> str:
        self.workspaces.append(workspace)
        return await super().start_chat(workspace=workspace, **rest)


def writer(root: Path, outputs: list[dict[str, Any]]) -> Path:
    step = agent("write", tools=["Write", "Edit"]) | {"outputs": {"files": outputs}}
    built = folder(root, [node("start", "trigger"), step], {"start": {"main": [edge("write")]}}, {})
    return agent_files(built)


def test_only_the_declared_output_commits_and_the_overlay_is_gone(tmp_path: Path) -> None:
    async def turn(port: FakePort, chat: str) -> Turn:
        here = cast(Workspaces, port).workspaces[0]
        (here / "result.md").write_text("the answer", encoding="utf-8")
        (here / "extra.md").write_text("not asked for", encoding="utf-8")
        return Turn(CARD)

    port = Workspaces(turn)
    home = tmp_path / "home"
    outcome = asyncio.run(drive(writer(tmp_path / "wf", [{"path": "result.md"}]), home, port))
    events = events_of(home, outcome.run_id)
    work = RunZone.of(home, outcome.run_id).work
    committed = [e.data for e in events if e.kind == "zone_committed"]

    assert outcome.status == "passed"
    assert port.workspaces[0].name == "write.0.-.1"
    assert not port.workspaces[0].exists()
    assert sorted(p.name for p in work.iterdir() if p.is_file()) == ["result.md"]
    assert (work / "result.md").read_text(encoding="utf-8") == "the answer"
    assert [c["paths"] for c in committed] == [["result.md"]]


def test_a_read_only_step_is_born_in_its_workflow_folder_and_commits_nothing(
    tmp_path: Path,
) -> None:
    port = Workspaces(CARD)
    home = tmp_path / "home"
    built = folder(
        tmp_path / "wf",
        [node("start", "trigger"), agent("read")],
        {"start": {"main": [edge("read")]}},
        {},
    )
    outcome = asyncio.run(drive(agent_files(built), home, port))
    events = events_of(home, outcome.run_id)

    assert outcome.status == "passed"
    assert port.workspaces == [home / "workspaces" / "wf-flow"]
    assert [e for e in events if e.kind == "zone_committed"] == []
    assert port.chats[0]["tools"] == ("Read", "Grep")
