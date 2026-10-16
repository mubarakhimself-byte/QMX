---
title: Feasibility probes (scripts under scripts/live, no harness edits)
type: task
mode: AFK
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Probes 1, 2, 4 and 8 assume engine-in-harness and one plan (rulings 24, 26); probes 5, 6, 7, 9, 10, 12 still useful."
---

## Question

Run review B's twelve probes as scripts, one session each, with no harness source edits: engine-in-harness spike (1), cap telemetry over one window (2), two plugins at once (3), pack relaunch (4), CDP broker (5, after decision 4), sandbox on Windows 11 Home (6), SQLite under load (7), fan-out under the slot cap (8), the QMB door timing (9, with the QMB session), relay providers with structured output (10), agent-step retry (11), the server lane (12, after B44).

## Why it matters

Each probe settles a fact a contract depends on: the `model` step's token floor, how far a turn overruns the cap, whether two plugins load, whether a hook can beat the money gate, whether Chrome can be hidden from agent Bash, whether any sandbox exists, whether one SQLite writer is enough.

## What the session does

AFK task per probe. Save each script and its log; record the measured numbers in the ticket; flag any contract line the result contradicts.

## Unblocks

Harness extensions (1, 3, 4), the thin engine (7, 8, 11), the browser (5), `rlm` and unattended L4 and Docker apps (6), the QMB door (9), relay-provider templates (10), server runs (12).

## Sources

`20-review-b` probes 1-12; `19` section 12.
