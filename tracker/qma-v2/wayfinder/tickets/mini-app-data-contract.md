---
title: Mini-app data contract
type: grilling
mode: HITL
status: open
blocked_by: [plugin-unit-and-loading]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Matches ruling 9."
---

## Question

How mini apps take input from and give output to other apps, internal pieces (Lab, Library, runs, Portfolio) and external APIs or webhooks, and how a combined session may change Portfolio from app or Lab output with his approval.

## Why it matters

Correction G. The manifest already has `provides` and `feeds` schemas and artifact-by-reference between apps (`05` §1), but nothing covers webhooks in, internal reads by home, or the path from an app's output to a Portfolio proposal.

## Recommended answer

The table in `12` section (h): app to app by validated, hashed artifacts; internal reads through the control door scoped by the app's `data_reads` and home; app outputs as typed artifacts the Library indexes and workflows can `inputs_from`; external calls through the app's allow-list with keyring secrets; webhooks in through `POST /api/apps/{id}/hooks/{name}` with a signed secret, written as untrusted artifacts, starting runs only through an approved trigger; deliveries redacted and marked unverified when unconfirmed; money endpoints never on an allow-list; any Portfolio change from app or Lab output lands as a card he approves.

## What the session does

Grilling on which external services he wants first (TradingView alerts, Telegram, broker reads) and on how a Portfolio proposal card should look. Output: the contract table and the webhook route spec.

## Unblocks

Mini-app lifecycle; build plan.

## Sources

`05-qmx-today.md` §1 runtime and manifest; `12` section (h); `03-workflow-engines.md` §9.3 cross-workflow data; corrections G, 3.
