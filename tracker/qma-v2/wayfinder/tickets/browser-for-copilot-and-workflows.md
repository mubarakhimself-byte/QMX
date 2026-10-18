---
title: QMX Browser, broker and leases (C6)
type: task
mode: AFK
status: closed
blocked_by: [feasibility-probes]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Ruling 30 wants the plan and user journeys explained first; wave 3 wording is stale (ruling 33)."
closed: 2026-10-16
---

## Question

The QMX Browser he signs into once, the broker that holds the single CDP connection, leases with levels B0 to B4 for the copilot, sub-agents and workflows, the watch pane, and which sites and levels he grants first.

## Why it matters

Central piece C6 in `19`. He wants to watch the copilot work in a shared browser with his logged-in profiles (YouTube playlists, TradingView), and the funnel needs TradingView pages. `14` and `18` settle the stack: a dedicated QMX Browser profile (his everyday Chrome cannot be automated or copied because of App-Bound Encryption), Playwright MCP over CDP, a broker with leases, a CDP screencast watch pane on `127.0.0.1`, Stagehand in local mode as a no-token replay layer, and a cloud backend only for isolated B1 and B2 work later. Claude in Chrome cannot be used from the Agent SDK. B17a holds the full un-hold; this is the scoped first step.

## Candidates

| Candidate | What must be true |
|---|---|
| (a) First step: the QMX Browser profile, the broker, Playwright MCP, the watch pane read-only with take-over, B1 and B3 reads for the funnel and research; one lease at a time on the logged-in profile. | Nothing posts, buys, sends or subscribes; logins and CAPTCHAs stop and ask him. |
| (b) B4 "act as me" per-action approvals; B3 for scheduled runs under a standing rule per origin. | After (a) runs clean for the funnel pilot. |
| (c) Cloud backend (Steel self-hosted) for parallel isolated leases; server-side watch pane via WebRTC. | After B44 and his explicit decision on any logged-in profile off his PC. |

## Recommended answer

(a) now, (b) when he grants it, (c) later. Levels per agent in `qmx.toml`, capped by the shared policy; origins granted separately; every action logged with a screenshot; unattended runs get B1 and B2 only unless he sets a rule.

## What the session does

Grilling on the first sites and levels, and on whether the watch pane matters before the funnel pilot. Output: the broker spec, the level table as data, the first origin grants.

## Unblocks

Wave 3 templates (RS4 at B3), the funnel's capture stage, trader-agent trials later.

## Sources

`14-folders-miniapps-browser.md` §3; `18-browser-harnesses.md`; `BACKLOG.md` B17, B17a, B38; `19` C6; corrections 9 and K.

## Resolution

Superseded. Engine AD-33 (Cua as an optional pack with a bounded manifest) replaces C6. Ruling 30's plan and journeys are owed in 'Browser and computer-use plan and journeys'. (Map rewrite 2026-10-16.)

## Note (2026-10-18)

`blocked_by` lost `decision-4-browser-first-step` when those superseded tickets moved to `../../archive/2026-10-18-wayfinder-superseded/`. This ticket was already closed.
