---
id: SCN-0034
title: Home and Copilot stay independent rail destinations
type: scenario
status: ratified
component: COMP-QMA-WIRE
depends_on: []
decisions: [DEC-0470, DEC-0471]
sources: [DEC-0470, SRC-27]
generated: 2026-09-25
verified: 2026-09-25
stale_after: 90d
---

# SCN-0034: Home and Copilot stay independent rail destinations

Home is work/attention/resume. Copilot is conversation. They are not the same destination (DEC-0470).

This scenario is specification of intended behavior, not inspect proof. Pairing, qmb host, list_mailbox, cancel_job, PUT /artifacts/stage, and Svelte chrome are absent at integration@34c148be (DEC-0507). Class/test existence is not e2e (DEC-0286).

## Given

Zero opened apps. Platform rail shows Home, Copilot, Library, Authoring above the divider.

## When

Operator opens Home, then Copilot, then Authoring, then a headless pack with no pane (DEC-0471).

## Then

Home lists running jobs, unknown, failed, and resume of an existing `psess:` or JobHandle. Copilot shows sessions, messages, preview tabs. Authoring is reachable with no app open. Headless pack produces a JobHandle with no navigation pane. Shared `SessionList` / `ConversationPane` components do not merge the destinations. No third `ProductSessionProfile`.

## Worked numbers

Destination count above the divider is four named product destinations plus Settings chrome. Opened-app icons stay below the divider.
