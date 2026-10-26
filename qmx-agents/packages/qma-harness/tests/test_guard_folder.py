"""The guard holds the whole QMX folder (design 62 J): its keys, run state and pack plugins
beside the home included, while the home's workspaces and the run zones stay writable."""

from __future__ import annotations

from pathlib import Path

import pytest
from qmx_home import Layout, resolve

from qma.harness import QmxHome
from qma.harness.guard import Deny, GuardRules, Pass, guard
from qma.harness.tools import guard_rules


@pytest.fixture
def folder(tmp_path: Path) -> tuple[Layout, GuardRules]:
    layout = resolve(tmp_path / "QMX", create=True, drives=[])
    home = QmxHome(layout.home)
    rules = guard_rules(
        [],
        domain_write="allow",
        home=home,
        config_dir=home.plan_dir,
        keyring_names=frozenset(),
        unattended=False,
        external_unattended=frozenset(),
    )
    return layout, rules


def shell(rules: GuardRules, cwd: Path, command: str) -> Pass | Deny:
    verdict = guard(
        "Bash", {"command": command}, rules, cwd=str(cwd), agent_id=None, permission_mode="default"
    )
    assert isinstance(verdict, Pass | Deny)
    return verdict


@pytest.mark.parametrize(
    "inside",
    ["keys/vault.key", "cache/run/procs/chat-1.json", "cache/plugins/research/skill.md"],
)
def test_a_shell_write_beside_the_home_is_refused(
    folder: tuple[Layout, GuardRules], inside: str
) -> None:
    layout, rules = folder
    target = (layout.root / inside).as_posix()

    verdict = shell(rules, layout.home / "workspaces", f"echo x > '{target}'")

    assert isinstance(verdict, Deny)
    assert verdict.reason.startswith("guard: agents cannot touch QMX state from a shell (")
    assert verdict.reason.casefold().endswith(f"/qmx/{inside})")


@pytest.mark.parametrize(
    "inside", ["keys/control-token", "cache/run/state/gpt-probe.json", "logs/host.log"]
)
def test_a_file_tool_write_beside_the_home_is_refused(
    folder: tuple[Layout, GuardRules], inside: str
) -> None:
    layout, rules = folder

    verdict = guard(
        "Write",
        {"file_path": str(layout.root / inside), "content": "x"},
        rules,
        cwd=str(layout.home / "workspaces"),
        agent_id=None,
        permission_mode="default",
    )

    assert isinstance(verdict, Deny)
    assert verdict.reason.startswith("guard: agents cannot write QMX state (")


@pytest.mark.parametrize(
    "inside", ["data/workspaces/wf-1/notes.md", "cache/zones/run-1/attempts/a.0.-.1/out.json"]
)
def test_the_workspaces_and_the_run_zones_stay_writable(
    folder: tuple[Layout, GuardRules], inside: str
) -> None:
    layout, rules = folder

    verdict = guard(
        "Write",
        {"file_path": str(layout.root / inside), "content": "x"},
        rules,
        cwd=str(layout.home / "workspaces"),
        agent_id=None,
        permission_mode="default",
    )

    assert isinstance(verdict, Pass)
