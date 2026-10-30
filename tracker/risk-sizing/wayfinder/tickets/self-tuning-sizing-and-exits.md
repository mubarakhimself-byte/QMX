---
title: The risk socket: what a unit plugs in now, what the risk session wires later
type: grilling
mode: HITL
status: open
blocked_by: [pod-guard-and-shared-budget, prototype-self-configuration]
claimed_by: ""
created: 2026-10-24
updated: 2026-10-30
covers: [L07-01, L07-02, L07-03, L07-07]
---

## Question

He wants a "male and female connector" (T2:132): the unit plugs into a socket now and the risk session wires the maths in later. What is the socket's shape? Which inputs must it expose (journal statistics, equity, budget share, lot sizes from broker facts)? What runs when the socket is empty: a fixed default, the minimum lot, or no trading? How do variables configure themselves as units are added, without him?

## Why it matters

Code first, numbers later (STATE 10-29/30). Exits are inside the unit (ruling, `STATE.md:21`), so the 24 Oct exit question is now a QML block question (lead call in MAP Notes).

## Read first

The self-configuration prototype; `HANDOFF-RISK-SIZING.md`; `research/18-grounding-today.md` §5 (the unwired sizing ladder).

## Was (24 Oct)

How a unit's sizing tunes itself from its record (tighten, never loosen?), and the exit methodology.

## How to run it

With him, live, using the `grilling` and `domain-modeling` skills. Before the session the lead converges this ticket's research into options and an explainer page (STATE planning run, step 4). Never answer for him.

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
