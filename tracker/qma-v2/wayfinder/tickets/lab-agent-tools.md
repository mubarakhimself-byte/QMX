---
title: Lab pack: tools for total creative freedom
type: grilling
mode: HITL
status: closed
blocked_by: [autonomy-policy, capability-packs]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. The Lab is the core (ruling 6); check the tool list against study 23."
closed: 2026-10-16
---

## Question

The Lab pack's tool set for agents: strategies, components and units, variants, MIS versions, indicators, ML and neural nets, running workflows, with nothing asking except money and publishing outside the Lab.

## Why it matters

Correction 4: the Lab is QMX's core feature. Today agents can only run pre-registered QMB configs; no sweep, walk-forward, robustness, optimize, notebook, indicator, model or MIS tool exists (`05` gap 8; `10` §1). The operator ruled the Lab backend layer is designed during coding, so this ticket fixes the agent-facing list and effect classes only.

## Recommended answer

Namespaced `lab.*` tools: `register_config`, `backtest`, `sweep`, `walk_forward`, `robustness`, `optimize` (QMB, costs on), `notebook_append`, `data_snapshot`, `compute_where`, `indicator_create`, `component_create`, `variant_create`, `mis_version_create`, `model_train`, `model_import`, `slot_bind`, `workflow_run`, `board_run_scope`; plus `library.search` and `library.save_negative_result`. Every call is a span. In a Lab session none asks; publishing outside the Lab asks. The Lab feeds Portfolio through the funnel's gates and the proposal card.

## What the session does

Grilling on the first ten tools and the compute placement words. Output: the tool table with effect class per tool, handed to the Lab coding session.

## Unblocks

Lab overnight loop; Experimentation Board.

## Sources

`05-qmx-today.md` §2, gap 8; `10-ui-depth.md` §1; `02-pocock-pstack.md` ml4t research-operator; memory `qmx-ui-rebuild`; correction 4.

## Resolution

Resolved. Lab AD-14 (the Lab copilot's 17 tools ship as a plugin with Effects) and AD-3 (closed Lab node pack). (Map rewrite 2026-10-16.)
