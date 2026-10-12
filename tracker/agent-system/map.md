---
label: wayfinder:map
created: 2026-10-12
---

# QMX agent system: map

## Destination

A ratified design for the QMX agent system, ready to cut into build packets and ship:
- the harness or harnesses (workers and adapters)
- the organogram (main copilot, Lab, Portfolio, mini-app copilots, workflow and server agents)
- accounts, routing and usage limits
- the baseline tool surface
- approvals and hooks
- memory
- long-running and server agents
- context (caching and compaction)
- the chat and event protocol the UI shows
- skills and system prompts
- a shipping plan: packets that can run in parallel, tracked against this map, inside usage limits

Today and the next sittings are planning only. No code ships until ticket 16.

## Notes

- **Operator:** Mubarak. Non-technical, dictates (expect transcription noise), reads plain words and diagrams rather than walls of text.
  - Give reading time: never deliver an artifact and fire questions in the same beat.
  - Don't re-ask settled decisions. Answer research-shaped questions yourself.
- **Who decides:** each ticket carries a `who-decides` line.
  - Claude decides alone and reports back on: sessions, caching and compaction, server agents and cron, the event protocol, and folder layout.
  - The operator decides: harness, organogram, tools and access, accounts, approvals, memory, skills and prompts, and the shipping plan.
  - Follow the skill's spirit, not its letter (operator, 2026-10-12).
- **Backlog** (other efforts and follow-ups, kept apart from the map): `tracker/agent-system/backlog.md`.
- **One ticket per session**, research tickets excepted. Load this map first in every session. It is the tracker that survives compaction and session switches.
- **HITL tickets:** use `/grilling` and `/domain-modeling`. Use `/codebase-design` for module and seam questions.
- **Research inputs (fresh, 2026-10-12, primary sources):** `rebuild/research/2026-10-12-agent-system/`
  - `qmx-internal.md`: the UI screen by screen, the August, September and October designs, what the code really does, and 15 contradictions between the eras
  - `langchain-stack.md`
  - `harnesses.md`: Hermes, Codex source, Eve and agent folders, computer use
  - `memory.md`
  - `models-routing.md`
  - `cookbooks.md`
  - Older studies in `rebuild/research/` are superseded where these disagree. Each new file ends with a corrections section.
- **Standing operator positions** (stated 2026-10-12, inputs to the tickets, not yet ratified decisions):
  - Every QMX agent gets at least Claude-Code-level capability: terminal, Python, files, web, CLI tools, video watching, computer use. QMX-specific rules (for example, where a strategy file is written) are enforced by hooks.
  - Design for high load and complexity before the load arrives.
  - Tools are mostly local QMX code, not MCP. MCP is acceptable for browser and computer use. The Library is a database.
  - A usage page in the style of T3 Code: tokens, cost, cache savings and limits per harness and model.
  - Cron in the Hermes style. Compaction in the Anthropic style, automatic.
  - LangSmith is not used.
  - He likes Claude's hooks, compaction, caching and sub-agent design. He is open to the Claude Agent SDK as the base harness if it can carry non-Claude models. Otherwise QMX runs LangGraph with Claude Code as a node (the Sandcastle pattern: harness = swappable agent provider).
  - The chat should feel like Claude Code or Codex: sessions, running sub-agents, tool calls and the computer-use cursor visible; logs are mostly hidden.
  - Firecrawl, including Alexandria, is wanted for web and documentation work.
- **Carried rules:**
  - No modes (2026-10-09).
  - Configurable means editable in the UI (the Lego vision).
  - The money-path barrier: agents never place orders, size trades or touch the kill switch. Money changes are drafts for his signature.
  - Risk and sizing authority is GitBook plus the node docs.
  - USD.
  - Broker credentials stay in Windows Credential Manager `qmx/*`.
- **Cost rules:**
  - Few subagents, always in the background.
  - A subagent never spawns sub-agents.
  - Research runs on Opus 5.5 at medium effort.
- **Commits:** no Claude attribution lines (standing rule from the August map).

## Decisions so far

<!-- one line per closed ticket -->

- [Claude Agent SDK as the base harness: capability audit](tickets/01-agent-sdk-capability-audit.md) — not the base for every agent; ticket 02 is option B or C; measure RAM, DeepSeek route and isolation first
- [Usage, limits and cost telemetry](tickets/05-usage-limits-telemetry.md) — local session files + documented limit events feed a `usage_call` ledger; private OAuth endpoints are off limits

## Not yet specified

- **Lab default workflows and the built-in research harness.**
  - Enhance what P10, P15 and P19 shipped.
  - Candidates from `qmx-internal.md` §c.4: the cited research pipeline, Hypothesis→Test→Learn→Mutate→Gate, experiment-tree budgets and kill criteria.
  - Waits on the WF1/WF2 rework (out of scope here) and on tickets 02 and 04.
- **Self-improvement.** "Don't repeat Wednesday's mistake": learned procedures from computer use and other work, curation, approval. Hermes is the lead reference. Graduates after ticket 08.
- **Skill catalogue.** Which skills ship by default, per copilot, and how the operator adds them. After tickets 04 and 13.
- **RLM and code-over-data in the chosen harness.** After ticket 02.
- **Mini-app copilots** and the screen-tier-3 in-app code question (`qmx-internal.md` §e item 14).
- **Embedding desktop apps inside QMX** (cTrader beside the chat) beyond what ticket 12 measures.
- **QA scenario generation per screen** (Lab and Portfolio use cases) for the post-build QA phase.

## Out of scope

- **WF1/WF2 rework.** On the operator's own backlog, tied to the risk and sizing session's changes.
- **Risk, sizing and portfolio-optimisation changes.** Handled in another session.
- **P16c, retiring the old QMA runtime.** Running in its own session.
- **UI implementation and wiring.** Its own session. This map only fixes what the UI must show (ticket 11).
