---
title: Send a long workflow to the server
type: task
mode: AFK
status: open
blocked_by: [workflow-engine-contract]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Now required: server or cloud as well as local (ruling 25)."
---

## Question

How a running or new workflow moves to his server (Docker on Linux, B44) with its checkpoint, keys and skills, runs there for days, and reports back.

## Why it matters

Correction 7: long workflows must be sendable to a server. Per-workflow model configuration often means keys, which fits remote runs. B46 asks for sessions that persist, move from local to server, and export transcripts and logs automatically. `qmx-remote` providers exist and are partly stubbed (`05` §2).

## What the session does

AFK task. Specify: a run's portable bundle (workflow folder, checkpoint, state references, settings, resolved roles); the server's engine worker; checkpoint sync and `Last-Event-ID` replay back to the UI; secrets by named opt-in only; the cap governor when the server uses a key instead of the plan; export on completion. Hand back the spec and the Docker test plan.

## Unblocks

Feeds the build plan after B44.

## Sources

`BACKLOG.md` B44, B46; `05-qmx-today.md` §2 remote runs; `03-workflow-engines.md` §9.5; correction 7.
