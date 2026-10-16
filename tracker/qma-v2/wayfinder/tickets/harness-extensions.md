---
title: Harness extension packets (before the engine)
type: task
mode: AFK
status: open
blocked_by: [wave1-prerequisites, decision-1-lab-self-scheduling, folder-format-one-shape, session-homes]
claimed_by: ""
created: 2026-10-16
rubric: "SUPERSEDED. The harness must not be touched; the engine runs separately (ruling 24)."
---

## Question

Specify the harness packets the engine needs, each one PR with one build and one check: a `home` field and origin on the session and on `NewChat`; structured JSON output per chat (`output_format`); a per-chat tool allow-list and `max_turns` (and a budget); an app-plugin registry of approved hashes beside the SHA-locked core, rewriting the three init checks and refusing hooks, monitors, `bin/` and in-process tools in non-core folders; REST start for background chats; packs as launch config.

## Why it matters

Review B showed the engine's `model` and `agent` steps need an API the harness does not have, that per-folder plugins clash with three harness checks, and that REST cannot start a background chat. These packets come before the engine.

## What the session does

AFK task. Write the packets in the `HARNESS-PLAN.md` checklist shape with fake-model lanes. Probes 1, 3 and 4 inform them. Hand back the packet list.

## Unblocks

The thin engine, wave 1 packet plan.

## Sources

`20-review-b` findings 2, 4, 16, 17; `21` B2, B5; `HARNESS-PLAN.md`.
