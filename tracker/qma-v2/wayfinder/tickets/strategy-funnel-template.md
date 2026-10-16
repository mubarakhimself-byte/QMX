---
title: Strategy funnel template
type: grilling
mode: HITL
status: open
blocked_by: [workflow-engine-contract, strategy-pipeline-gates]
claimed_by: ""
created: 2026-10-16
rubric: "PARTLY-STALE. Becomes an engine configuration with a plain name (rulings 22, 35) ending at paper (ruling 29); not template one."
---

## Question

Template number one: "pour in garbage, out come paper-trade candidates", built fresh on QMB with overfit guards, in two halves that hand off. Which of the 16 open points in `08` §4 he settles, and the first pilot.

## Why it matters

The operator named this the first template. The old WF1, WF2, the Stats folder and `strats-video-populate` are reference only; WF2's useful core (iterate against QMB until real results come out, without overfitting) is carried whole. Sources: videos through `watch`, papers through alphaXiv and arXiv q-fin, TradingView through a QMX browser profile, notes. Population should run unattended most of the time.

## Recommended answer

Two templates. "Fill the Library" (stages 1-7) runs nightly in batches with per-run caps on items and frames. "Build and prove" (stages 8-12) runs per card from a weekly short list of 5-10 he approves. Overfit guards as scripts: data snapshot, costs on, walk-forward, untouched holdout touched once, deflated Sharpe over every variant, loop budget 3 generations x 4 children, stop after 2 with no gain. Paper: at least 2 weeks and 30 trades. Vanilla faithful to the source; spiced optional; missing exits get a house policy labelled `external_policy`; nothing deleted. Pilot: one long chart video, one reel, one X thread, one article. Full table in `12` section (d).

## What the session does

Grilling on the 16 points in `08` §4 in rounds; "yes" accepts. Output: both template folders' briefs (GOAL, SCOPE, ACCEPTANCE, VERIFY, TIMEBOX, FORBIDDEN, REPORT) and the pilot list.

## Unblocks

First templates (the rest of the set), build plan.

## Sources

`08-strategy-funnel-lineage.md` §1e, §3, §4; `11-references.md` T3; `12` section (d); corrections 9 and I.
