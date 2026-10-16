---
title: System-prompt design
type: grilling
mode: HITL
status: open
blocked_by: [copilot-roster-and-freedom, role-to-model-table, session-homes, mubarak-standing-orders-skill]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. B29 was missed today (26 section C); still owed."
---

## Question

How system prompts are derived from the methodology per home and role, what layers they have, and what stays out of them because a hook or a script enforces it.

## Why it matters

Never designed (B29). He asked about meta prompts in XML. Research 31 has a five-layer design he has never seen. BMad's warning applies: bloated instruction files add cost without gain. Money and gates must not be prompt text.

## Recommended answer

Layers: (1) the constitution's ten rules, (2) the home row (what this session is for, what loads), (3) the role row (what this worker does and may not do), (4) the task brief in pstack's shape (GOAL, SCOPE, CONTEXT, ACCEPTANCE, VERIFY, TIMEBOX, FORBIDDEN, REPORT, STANDING), (5) the operator-mode standing orders. XML tags separate the layers. Anything a hook or script enforces is stated once as a fact, not as an instruction. Each layer is generated from the tables, never hand-edited.

## What the session does

Show him research 31's five layers first (easy win from BACKLOG). Grill on tone (terse and evidence-led for money-path roles) and on the XML shape. Output: the prompt compiler spec and three rendered examples (Lab worker, Portfolio copilot, scanner).

## Unblocks

Feeds the build plan.

## Sources

`BACKLOG.md` B29; `01-bmad.md` ideas 16 (small context) and the activation order; `02-pocock-pstack.md` orchestrate brief, writing-for-agents; `06` red team "one plain copilot".
