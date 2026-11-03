"""No agent reads a mini app's grant (C-25): the class table's wildcard `secret` rules reach the
guard, so every `data/apps/*/data/grants/` folder is refused on every tool and spelling, and the
fixed secret paths stay refused."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from qmx_home import Layout, resolve

from qma.harness import QmxHome
from qma.harness.guard import Deny, GuardRules, Pass, deny_rules, guard, normalize_path
from qma.harness.tools import guard_rules

FOLDED = sys.platform in ("win32", "darwin")


@pytest.fixture
def folder(tmp_path: Path) -> tuple[Layout, GuardRules]:
    layout = resolve(tmp_path / "QMX", create=True, drives=[])
    for app, name in (("trading-node", "ctrader-node.json"), ("other", "y")):
        grants = layout.home / "apps" / app / "data" / "grants"
        grants.mkdir(parents=True)
        (grants / name).write_text('{"refresh": "fake-grant-value"}', encoding="utf-8")
    journal = layout.home / "apps" / "trading-node" / "data" / "journal"
    journal.mkdir(parents=True)
    (journal / "orders.jsonl").write_text("{}\n", encoding="utf-8")
    (layout.home / "workspaces").mkdir(exist_ok=True)
    home = QmxHome(layout.home)
    rules = guard_rules(
        [],
        domain_write="allow",
        home=home,
        config_dir=home.plan_dir,
        keyring_names=frozenset(),
        unattended=True,
        external_unattended=frozenset(),
    )
    return layout, rules


def call(
    rules: GuardRules,
    cwd: Path,
    tool: str,
    tool_input: dict[str, object],
    *,
    agent_id: str | None = None,
    mode: str = "default",
) -> Pass | Deny:
    verdict = guard(tool, tool_input, rules, cwd=str(cwd), agent_id=agent_id, permission_mode=mode)
    assert isinstance(verdict, Pass | Deny)
    return verdict


def refused(verdict: Pass | Deny) -> str:
    assert isinstance(verdict, Deny), verdict
    assert "fake-grant-value" not in verdict.reason
    return verdict.reason


@pytest.mark.parametrize(
    ("agent_id", "mode"),
    [(None, "default"), (None, "bypassPermissions"), ("sub-1", "acceptEdits")],
)
@pytest.mark.parametrize(
    "app", ["trading-node/data/grants/ctrader-node.json", "other/data/grants/y"]
)
def test_a_grant_read_is_refused_in_every_app_and_role(
    folder: tuple[Layout, GuardRules], app: str, agent_id: str | None, mode: str
) -> None:
    layout, rules = folder
    target = layout.home / "apps" / app

    verdict = call(
        rules,
        layout.home / "workspaces",
        "Read",
        {"file_path": str(target)},
        agent_id=agent_id,
        mode=mode,
    )

    assert refused(verdict).startswith(
        "guard: agents cannot read or write a mini app's grant or another secret ("
    )


def test_a_normal_app_file_is_still_read(folder: tuple[Layout, GuardRules]) -> None:
    layout, rules = folder
    data = layout.home / "apps" / "trading-node" / "data"

    for target in (data / "journal" / "orders.jsonl", data / "grantsx.json"):
        assert call(rules, layout.home, "Read", {"file_path": str(target)}) == Pass()
    grep: dict[str, object] = {"pattern": "x", "path": str(data / "journal")}
    assert call(rules, layout.home, "Grep", grep) == Pass()


def spellings(layout: Layout) -> list[tuple[str, str, str]]:
    """(cwd, path as the agent writes it, label), each naming the trading node's grant."""
    data = layout.home / "apps" / "trading-node" / "data"
    grant = data / "grants" / "ctrader-node.json"
    found = [
        (str(layout.home), str(data / "journal" / ".." / "grants" / "ctrader-node.json"), "dots"),
        (str(layout.home), grant.as_posix(), "forward"),
        (str(layout.home), str(grant).replace("/", "\\"), "back"),
        (str(data), "grants/ctrader-node.json", "relative"),
        (str(data / "journal"), "../grants/./ctrader-node.json", "relative dots"),
        (str(layout.home), "apps/trading-node/data/grants//ctrader-node.json", "double slash"),
    ]
    if FOLDED:
        found.append((str(layout.home), str(grant).upper(), "case"))
        found.append((str(layout.home), str(data / "GRANTS" / "Ctrader-Node.JSON"), "mixed case"))
    return found


def test_every_spelling_of_a_grant_is_refused_on_file_tools(
    folder: tuple[Layout, GuardRules],
) -> None:
    layout, rules = folder

    for cwd, path, label in spellings(layout):
        for tool, field in (("Read", "file_path"), ("Edit", "file_path"), ("Write", "file_path")):
            verdict = call(rules, Path(cwd), tool, {field: path, "content": "x"})
            assert isinstance(verdict, Deny), (label, tool, verdict)


def test_every_spelling_of_a_grant_is_refused_in_a_shell(
    folder: tuple[Layout, GuardRules],
) -> None:
    layout, rules = folder

    for cwd, path, label in spellings(layout):
        for tool, command in (
            ("Bash", f"cat '{path}'"),
            ("PowerShell", f'Get-Content -Path:"{path}"'),
        ):
            verdict = call(rules, Path(cwd), tool, {"command": command})
            assert isinstance(verdict, Deny), (label, tool, verdict)


def test_a_glob_in_a_tool_argument_cannot_reach_a_grant(
    folder: tuple[Layout, GuardRules],
) -> None:
    layout, rules = folder
    apps = (layout.home / "apps").as_posix()
    work = layout.home / "workspaces"

    reasons = [
        refused(call(rules, work, "Bash", {"command": f"cat {apps}/*/data/grants/*"})),
        refused(call(rules, work, "Bash", {"command": f"cat {apps}/trading-node/data/g*/*"})),
        refused(call(rules, work, "Grep", {"pattern": "refresh", "path": apps})),
        refused(call(rules, work, "Grep", {"pattern": "x", "path": f"{apps}/other/data"})),
        refused(call(rules, work, "Glob", {"pattern": f"{apps}/*/data/grants/*"})),
        refused(
            call(rules, work, "Glob", {"pattern": "../apps/*/data/grants/*", "path": str(work)})
        ),
        refused(call(rules, work, "Glob", {"pattern": "*/../../apps/*/data/grants/*"})),
        refused(call(rules, work, "Glob", {"pattern": "{x,..}/apps/*/data/grants/*"})),
    ]

    assert sum("mini app's grant" in reason for reason in reasons) == 6
    assert sum("climb out of a folder after a wildcard" in reason for reason in reasons) == 2


def test_a_network_path_to_a_grant_is_refused(folder: tuple[Layout, GuardRules]) -> None:
    layout, rules = folder
    grant = layout.home / "apps" / "trading-node" / "data" / "grants" / "ctrader-node.json"
    unc = "\\\\localhost\\" + str(grant).replace(":", "$", 1).replace("/", "\\")

    assert refused(call(rules, layout.home, "Read", {"file_path": unc})).startswith(
        "guard: agents cannot use a device or network path ("
    )


def link(at: Path, to: Path) -> None:
    """A junction on Windows, which needs no rights, else a symlink."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(to), str(at))
    else:
        at.symlink_to(to, target_is_directory=True)


def test_a_link_into_a_grants_folder_is_refused(folder: tuple[Layout, GuardRules]) -> None:
    layout, rules = folder
    work = layout.home / "workspaces"
    link(work / "door", layout.home / "apps" / "trading-node" / "data" / "grants")

    by_file = call(rules, work, "Read", {"file_path": str(work / "door" / "ctrader-node.json")})
    by_shell = call(rules, work, "Bash", {"command": "cat door/ctrader-node.json"})

    for verdict in (by_file, by_shell):
        assert refused(verdict).startswith(
            "guard: agents cannot read or write a mini app's grant or another secret ("
        )


def test_every_fixed_secret_path_is_still_refused(folder: tuple[Layout, GuardRules]) -> None:
    layout, rules = folder
    inside = [
        layout.root / "keys" / "x",
        layout.home / "vault" / "x",
        layout.home / "vault-store.json",
        layout.home / "passes" / "x",
        layout.home / "rclone.conf",
        layout.home / "rclone.conf.unreadable-20261103",
        layout.home / "claude" / ".credentials.json",
        layout.home / "claude" / ".claude.json",
        layout.home / "claude-relayed" / ".credentials.json",
        layout.home / "claude-relayed" / ".claude.json",
        layout.home / "settings.toml",
    ]

    for target in inside:
        assert isinstance(
            call(rules, layout.home / "workspaces", "Read", {"file_path": str(target)}), Deny
        ), target


def test_the_cli_deny_rules_carry_the_grants_glob(folder: tuple[Layout, GuardRules]) -> None:
    layout, rules = folder
    home = normalize_path(str(layout.home.resolve()), cwd="/", home="/", case_insensitive=False)

    found = [rule for rule in deny_rules(rules) if "grants" in rule]

    assert found == [
        f"Read(/{home}/apps/*/data/grants)",
        f"Edit(/{home}/apps/*/data/grants)",
        f"Write(/{home}/apps/*/data/grants)",
        f"Read(/{home}/apps/*/data/grants/**)",
        f"Edit(/{home}/apps/*/data/grants/**)",
        f"Write(/{home}/apps/*/data/grants/**)",
    ]
