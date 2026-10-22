"""The core plugin's agents, ported from `qmx_agents/agents/` (DEL1): they parse as Claude plugin
agents, name only tools the catalog serves, and none can reach `delegate`."""

from __future__ import annotations

from qmx_control.catalog import rows

from qma.harness.home import PLUGIN_DIR
from qma.harness.tools import tool_name


def header(text: str) -> dict[str, str]:
    _, front, body = text.split("---", 2)
    assert body.strip(), "an agent needs a system prompt below its header"
    return {
        key.strip(): value.strip()
        for key, value in (line.split(":", 1) for line in front.strip().splitlines())
    }


def test_every_core_agent_parses_and_names_only_catalog_tools_without_delegate() -> None:
    agents = {
        path.stem: header(path.read_text(encoding="utf-8"))
        for path in sorted((PLUGIN_DIR / "agents").glob("*.md"))
    }
    known = {tool_name(row.toolset, row.op) for row in rows() if row.agent}
    tools = {name: [t.strip() for t in found["tools"].split(",")] for name, found in agents.items()}

    assert sorted(agents) == ["app-builder", "data-analyst", "overnight-builder", "researcher"]
    assert all(found["name"] == name and found["description"] for name, found in agents.items())
    assert {name: [t for t in named if "delegate" in t] for name, named in tools.items()} == {
        name: [] for name in agents
    }
    assert {
        name: [t for t in named if t.startswith("mcp__") and t not in known]
        for name, named in tools.items()
    } == {name: [] for name in agents}
