"""QMX harness inside qmx-control. Public: `qmx_harness.api.Harness` only.

Module map:
    api.py           Harness facade and its domain types
    env.py           boot scrub and per-session env derivation
    engine.py        Host (ClaudeSDKClient), options, money hook, block projection
    gateway_link.py  gateway process supervision and state sync
Not sketched: store.py (harness.db: threads, approvals, usage, windows, quotes),
tools.py (ToolRegistry -> in-process `qmx` MCP server + ToolCatalogSnapshot),
approvals.py (rendezvous behind can_use_tool / defer), settings.py (settings.toml
[providers] and agent profiles -> rows; config-home settings.json writer).
"""
