# The frame after grounding (31 Oct, 10:35 UTC)

Written by the lead after the five grounding files landed. Every agent from here on reads this first. It does not replace his words: the binding source is `STATE.md`, section "Operator round 2026-10-31 midday", rulings 1-45, and the verbatim transcripts. Where this file and STATE.md differ, STATE.md wins.

## 1. Grounding is complete

| File | What it covers |
| --- | --- |
| `grounding/G1-algo-side.md` | QML, the dictionary, bots and the unit, QMB, the Library's data, the MIS, journals |
| `grounding/G2-agent-and-platform.md` | QMA v2 agents and copilot, hooks, workflows, mini apps, contracts, local-first stack, DevOps, clocks |
| `grounding/G3-node-and-external.md` | The trading node and the broker links |
| `research/54-futures-platforms-languages-clocks.md` | Futures and order-flow data, platform languages, clocks |
| `grounding/G4a-wrapup-session-node-library.md` | The "QMX wrap-up coordination" session: Library, local-first stack, DevOps, QMB as a tool, the node's real state |
| `grounding/G4b-qma-v2-session-agents-workflows.md` | The "QMA V2 Workflow System Design 2" session: workflows, hooks, the copilot, mini apps, QMB as a tool, MIS log homes |

Where G4a or G4b corrects G1 to G3, the G4 file wins. The method the lead now follows is `00-how-the-best-session-worked.md`.

## 2. What already exists and is built on, not rebuilt

- **Storage, compute, logs and DevOps** came from the wrap-up session: the Library as a versioned object store with an edge table (a unit kind's pages are walks along links); the local-first stack and the connect dialog for storage, compute and deep logs; one telemetry switch; OpenObserve self-hosted on his PC, agents read-only (G4a rows 43, 60, 61, 66, 307).
- **The mini-app core** (G4b Q5): an `app.toml` manifest with `[operations]` (input and output schemas, approval, reversibility, `state: none | instance`), `[provides]` and `[feeds]` contracts with `stale_after`, `[profiles]`, `[suggested_trigger]`, `[isolation]`, `[breaker]`; every app runs its own MCP server; an instance can be homed on another machine; Windows Job object or Docker; health stops logged to the app's own logs; a `money` app needs his signature to start; the copilot's `apps_admin` toolset builds apps; workflows reach an app through the `app_op` node with no engine change. No real mini app exists yet.
- **Workflows**: about 15 templates were test-run on real models; script steps write files and run Python; agent steps save to the Library; a workflow can already write a unit as JSON, check it in a script step and loop the problems back (G4b Q1, Q2).
- **The copilot** reaches the whole platform through one catalog; a new tool is one catalog row, and the copilot gets it by default (G4b Q3).
- **QML's deterministic checks** exist and pass on Windows: declaration linter, source scan, isolation and determinism run, prediction linter, look-ahead refusal (G1). No agent tool calls them yet.
- **QMB as an agent tool** is designed (engine AD-31) and its tool rows are merged; the door is PR 204, open, with a runner that makes no trades (G4a Q4, G4b Q4).
- **CCXT 4.5.85** already includes Hyperliquid with orders, positions, funding and a testnet; QMX's wrapper allows spot reads only (G4a Q6).
- **The trading node** (about 98,000 lines, built 31 Aug to 4 Oct, never traded): its cTrader client, orders, reconcile, kill switch and kill line are worth keeping; its logic runs on Windows; only supervision, the powers door and the secret store need Linux (G4a Q2).

## 3. The shape his rulings now give (rulings 24-45)

- **The core: QML, the dictionary, the unit template and its checker,** with the unit stored as a Library kind. This is where most of the depth goes: "a small mistake in there is very costly", with a broad trading lens across forex, futures, metals, CFDs, indices and crypto perps.
- **The first two mini apps: QMB and the trading node,** on the existing mini-app core. QMB is an enhanced backtester with its own screen of what ran and who ran it; storage exists, so wire the logs. The trading node is "just a server now": one click sets it up, sets up the MIS, checks that things work, monitors, and heals itself. Only the node sends orders, by design, so the kill switch works. It may start afresh, and it comes late in the build: QML, the MIS and the contracts first, then assembled into the node.
- **Fewer new internal contracts,** because the copilot and workflows reach mini apps through the doors that exist. The main new shapes are the unit document, the mini apps' operations, and the journal records.
- **Agents in the slow lane** (ruling 44): unit review, market review, a shortlist before each session, tagging units to markets, a check on the MIS, daily data review, a watcher over trading nodes. The fast lane has no agents.
- **The pods** already represent risk and sizing; risk and sizing get placeholders now and their own session later.
- **The MIS:** defaults for every instrument class, room for his models later, readings published into homes that exist (G4b Q6); the real gap is the link from the node back to the PC.
- **Futures and order flow:** placeholders, or what works in the lead's opinion, behind a ready seam; he may pay for an exchange feed later. cTrader has no exchange futures; its order-flow tools are estimates from broker ticks and depth, which QMX can compute itself (ruling 40).
- **Legacy code: surgical, not frozen** (rulings 24, 32). Change what is necessary, with the reason in one line.
- **UI: notes and design proposals only** (ruling 45). No UI code is written or edited.

## 4. The hurdles, in order of care

1. QML and the dictionary (with the unit template and its checker).
2. The trading node (its own lens).
3. QMB.
4. Futures and order-flow data.
5. The MIS.

## 5. How the rest of the run goes (provisional; the lead re-plans after each step)

1. The funnel, three agents at once, on complete inputs: solutions (party mode with brainstorming), his day-to-day experience (CIS), and the edge-case catalogue with white-label lessons.
2. Stop and talk with him before architecture (best-session habit 6), through the question tool.
3. Architecture versions and Level 0 (one agent), its quick review, one fix.
4. Level 1, three agents: QML and the dictionary with the unit and its checker; QMB, journals and workflow templates; the trading node with the MIS, external connections, DevOps and clocks.
5. One review, one fix round, one fix-check.
6. The build plan, checked, and the orchestrator and builder prompts.
