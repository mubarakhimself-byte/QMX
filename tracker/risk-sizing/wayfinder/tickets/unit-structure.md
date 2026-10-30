---
title: What sits inside a unit, and what sits outside
type: grilling
mode: HITL
status: open
blocked_by: []
claimed_by: ""
created: 2026-10-24
updated: 2026-10-30
covers: [L01-01, L01-04, L01-06, L01-09, L01-11, L01-13, L04-09, L01-08, Q51, Q81]
---

## Question

A unit is one complete trading algorithm with no separations (ruling, `STATE.md:21`). What exactly sits inside it, which parts are frozen and which calibrate themselves? What is the smallest declaration it must carry before QMX can test, place or watch it? What does it need from QMX that it cannot compute itself, given it must stand alone? Does it carry its own session profile and its own stop rules, or does something central supply them? Does a plain-Python unit or an ML ensembler get every right a QML unit gets? If "the logic" is about 60% of a unit, what is the other 40%? What are the "multiple experiences that a unit can provide" (T2:6)?

## Why it matters

Root cause RC-A in the CIS run: what makes two units the same depends on what is inside one. The identity, trading-style, pod and prototype tickets wait on this.

## Read first

`research/funnel3/cis/glossary-draft.md` "unit" (ten definitions) and "logic"; `research/17-grounding-history.md` §1; `research/16-fable-advice-system1-context.md` §2 and §6.

## Was (24 Oct)

The structure of a unit (bot + self-configuring risk/sizing + record), what sits outside it, and how units live in pods.

## How to run it

With him, live, using the `grilling` and `domain-modeling` skills. Before the session the lead converges this ticket's research into options and an explainer page (STATE planning run, step 4). Never answer for him.

Paths are relative to `D:/QMX-worktrees/unit-plan/tracker/risk-sizing/` unless absolute. Question ids (L01-01, C1, Q1) are rows in `research/funnel3/party-brainstorm/playing-field.md` (L and C ids) and `research/funnel3/cis/cis-questions.md` (Q ids).
