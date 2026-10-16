---
title: Mubarak's standing orders skill
type: task
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. When written, use rulings 26-27, not the one-account and spend rules."
---

## Question

In one line: a short list of how Mubarak likes things done, loaded into every agent and pasted into every brief, so he never has to repeat himself.

## Why it matters

His rules are spread over memory files: plain short English, tables and pictures, no re-asking settled decisions, configurable means UI-editable, show where jobs run, few background agents, no API spend, money read-only. One file makes every later session cheaper. Renamed from "operator-mode skill" at his request.

## What the session does

AFK task. Mine the recent QMX sessions for patterns seen twice (pstack `automate-me`), merge with the memory files, write `mubarak-standing-orders` in the QMX skill format (under 40 lines) and a `standing-orders.md` the orchestrator pastes into every spawn. Hand back both for his one-line approval; install only after the plugin ticket closes.

## Unblocks

System-prompt design layer 5; every HITL session on this map.

## Sources

`02-pocock-pstack.md` automate-me, orchestrate; memory files `mubarak-operator-profile`, `qmx-operator-standing-rules`, `dont-reask-settled-decisions`, `chat-first-no-unprompted-docs`, `light-verification-per-pr`, `subagent-cost-rules-own-account`; correction 12.
