---
title: MCP apps (B16)
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
---

## Question

How QMX uses MCP apps (the Model Context Protocol apps standard: interactive UI inside chat, as in Claude Desktop): which surfaces render them (hub chat, Lab copilot, mini apps), whether a mini app's widgets ship as MCP apps, and what the backend must serve. A UI topic (ruling 82); the UI session co-owns it.

## Recommended answer

Treat an MCP app as one more widget kind inside a mini-app pack (engine AD-19), rendered in the chat panel catalog; no new backend store. The UI session designs the renderer; the result is added to `UI-HANDOFF.md`.

## Unblocks

The UI-session handoff (MCP apps row), output methodology rendering.

## Sources

Ruling 82; `BACKLOG.md` B16; `UI-HANDOFF.md` section 8; engine AD-19 (mini app = pack with widgets).
