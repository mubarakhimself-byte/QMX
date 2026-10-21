"""`qmx app check` on a pack's plugin view (AD-19, AD-55; H43).

Four checks, each a refusal or a list: the view parses as a plugin, every `!` shell line is
listed, no `hooks/` or `.mcp.json` is shipped, and the pack's server serves exactly the rows
`app.toml` declares.
"""

from __future__ import annotations

import json
from pathlib import Path

from qmx_apps.road.check import check


def view(root: Path, **extra: str) -> Path:
    """One pack view on disk: a manifest, one skill, one agent and one command."""
    files = {
        ".claude-plugin/plugin.json": json.dumps({"name": "pack-alpha", "version": "0.1.0"}),
        "skills/alpha-skill/SKILL.md": "---\nname: alpha-skill\n---\n\nBody.\n",
        "agents/alpha-agent.md": "---\nname: alpha-agent\n---\n\nALPHA-AGENT-OK\n",
        "commands/alpha-cmd.md": "Run the pack thing and say OK.\n",
    } | extra
    for name, body in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return root


def test_a_clean_pack_passes_with_its_rows(tmp_path: Path) -> None:
    found = check(
        view(tmp_path / "pack-alpha"),
        declared=["alpha_ping", "alpha_note"],
        served=["alpha_note", "alpha_ping"],
    )

    assert found.ok, found.refusals
    assert found.name == "pack-alpha"
    assert found.skills == ("alpha-skill",)
    assert found.agents == ("alpha-agent",)
    assert found.commands == ("alpha-cmd",)
    assert found.tools == ("alpha_note", "alpha_ping")


def test_shell_lines_are_listed_not_refused(tmp_path: Path) -> None:
    found = check(
        view(
            tmp_path / "pack-alpha",
            **{"skills/alpha-skill/SKILL.md": "---\nname: alpha-skill\n---\n\n!`git status`\n"},
        ),
        declared=["alpha_ping"],
        served=["alpha_ping"],
    )

    assert found.ok, found.refusals
    assert found.shell_lines == ("skills/alpha-skill/SKILL.md: git status",)


def test_a_pack_with_a_hooks_folder_is_refused(tmp_path: Path) -> None:
    found = check(
        view(tmp_path / "pack-alpha", **{"hooks/on_start.md": "!`curl https://x`"}),
        declared=[],
        served=[],
    )

    assert not found.ok
    assert found.refusals == (
        "hook_or_server: a pack ships no hooks and no .mcp.json; remove hooks/on_start.md",
    )


def test_a_pack_serving_tools_it_never_declared_is_refused(tmp_path: Path) -> None:
    found = check(
        view(tmp_path / "pack-alpha"), declared=["alpha_ping"], served=["alpha_ping", "alpha_send"]
    )

    assert not found.ok
    assert found.refusals == (
        "tools_differ: the server's tools differ from the declared rows (declared and not served: "
        "none; served and not declared: alpha_send)",
    )


def test_a_folder_that_is_not_a_plugin_is_refused(tmp_path: Path) -> None:
    stray = view(tmp_path / "pack-alpha", **{"README.md": "notes\n"})
    (stray / ".claude-plugin" / "plugin.json").unlink()

    found = check(stray, declared=[], served=[])

    assert not found.ok
    assert found.refusals[0].startswith("not_a_plugin: ")
    assert "found README.md" in found.refusals[1]
