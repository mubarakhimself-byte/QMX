---
title: One step-by-step connect dialog for screen and copilot
type: grilling
mode: AFK
status: closed
blocked_by: [one-place-list]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

He wants compute, storage, GPU and deep logs connected from the screen "through some sort of dialogue ... one question, then another question", that "sets itself up or if something is necessary it gives me something else ... a link or ... wizards or use the QMX copilot" (`words:219`). What is the one backend behind it?

## Resolution

- **A connection kind is an ordered list of steps.** Each step is `(name, who, check, do)`, where `who` is `his` or `qmx`. A step only he can do (sign in, pay, type a key, approve) is a card. A step QMX does is a checked operation.
- **One job runs a kind's steps** on the built job runner (`HO/jobs.py`: `running`, then `finished` with a result or `stopped` with one plain line; `step` and `done` of `total`; read this session). It runs QMX's steps in order and skips every step whose `check` already passes.
  - It finishes with `{needs: <his step>}` when it reaches a step only he can do. The screen shows that card. When he is done, the same job is started again.
  - Resuming is running again; no saved state machine is needed (principle make-operations-idempotent: a rerun converges whatever a crash left behind).
- **One backend, two front ends.** The screen's cards and the copilot's walk (R145, on the wizard pattern) call the same routes, so they never diverge. The copilot reads each step's name and line and walks him through the same cards.
- **The last QMX step of every kind writes the place row with `can`**, then runs that kind's health check. Setup today does not add the server to the place list (`QX/node.py:616-652`, machines a6); this fixes that.
- **Routes:**
  - A list of kinds with what each can do (run, keep, both), for the dialog's first question (machines #7).
  - Start or rerun a connect job; read it.
  - **A write-only key route** that puts a named key into Credential Manager and never returns it, with a read that lists which names are set. It serves an R2 key, a Modal or E2B key, and the cTrader app id and secret (closes UIH §26 gap 3).
- **Runs in the card too.** The first-start card already runs jobs (`/api/first-start/jobs/{id}`, UIH §19 row 9), so the storage kind can run there for a restore on a new PC, before any host exists.
- **One kind per ticket:** [Connect a storage](connect-storage.md), [Connect a server, GPU or key-based compute](connect-compute.md), [Connect deep logs (OpenObserve) on any machine](connect-deep-logs.md).

## Evidence

- R144, R145.
- Design F1 (`design:405-412`): his steps as cards, QMX's steps as resumable checked operations, his later choices on their own screens.
- LF13 (`design:453`): setup as resumable steps with status, startable from a card.
- `align:` C3.
