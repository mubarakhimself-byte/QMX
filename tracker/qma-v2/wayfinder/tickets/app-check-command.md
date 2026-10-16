---
title: qmx app check and qmx agent info
type: task
mode: AFK
status: closed
blocked_by: [folder-format-one-shape, mini-app-data-contract]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Test before use fits ruling 23; ignore the wave 4 wording (ruling 33)."
closed: 2026-10-16
---

## Question

Build the two commands an agent or the UI runs to say "works / does not work": `qmx agent info <id>` and `qmx workflow info <id>` (everything discovered, with warnings) and `qmx app check <app-id>` (the 12-line proof, pass, fail or needs-human per line, including the render check with four prop states and screenshots).

## Why it matters

Central piece C11 in `19`. Shopify's self-review skill, VS Code's clean-room scan and Claude's `plugin validate` all exist; QMX has the road stages and budgets but no one command. Without it the copilot cannot prove an app before the install card, and D7, D8 and D9 cannot run.

## What the session does

AFK task. Specify and build: step order and stop-at-first-failure; immutable records per step through the existing road; the render check harness (load each widget with sample, empty, error and loading props; fail on console errors or failed requests; fit to slot; screenshot); the load check asserting on the Agent SDK `system/init` message; the agent eval from `evals/`. Hand back the commands and a run on one example app.

## Unblocks

Wave 4 templates (D7, D8, D9).

## Sources

`14-folders-miniapps-browser.md` §1.4 rule 5, §2.6; `05-qmx-today.md` §1 road; `19` C11.

## Resolution

Resolved. Engine AD-11: validate, then a real-model test gate before publish (ruling 23, 51); mini apps pass the same gate as packs (engine AD-19). (Map rewrite 2026-10-16.)
