---
title: Methodology umbrella
type: grilling
mode: HITL
status: open
blocked_by: [methodology-builder, copilot-roster-and-freedom, trader-agent-methodology, system-prompt-design, output-methodology, decision-5-checks-bind-agents-only]
claimed_by: ""
created: 2026-10-16
rubric: "KEEP. Ruling 1; drop unit-read-adapter as a blocker while node depth stays out (ruling 14)."
---

## Rewrite (2026-10-16, map rewrite)

Still open (ruling 1). Re-blocked on the live methodology tickets only; every central contract it waited on is now an AD in the three architectures. Portfolio's purpose is not a blocker; it is recorded as pending. Handled tomorrow (ruling 82).

The text below is the earlier charting; where it disagrees with this section or with `26`, they win.

## Question

What is the methodology as an artifact, where does it live, and how does it "compile" the organogram and the workflows?

## Why it matters

The operator's words: methodology is the umbrella; it compiles the organogram and the workflows. A document cannot compile anything. Only data the engine reads can. BMad keeps its ecosystem coherent with a capability registry (`preceded-by`, `followed-by`, `required`, `outputs`) and a small verified context file, and warns that bloated instruction files add cost without gain (`01` §Q2).

## Candidates

| Candidate | What must be true |
|---|---|
| (a) A plugin-shaped file set: a constitution under 200 lines, plus data tables (capability graph with gates, autonomy table, role table, home table, output rules, memory rules) that the engine, the hub copilot and the system prompts read. | The engine reads tables, and each home loads the plugin. |
| (b) A chapter in `docs/`. | Only if nothing reads it. It would rot. |
| (c) The system prompt itself. | Never; the prompt is derived from the methodology, not the reverse (B29). |

## Recommended answer

(a). The constitution holds the ten rules that change agent behaviour (determinism boundary, money, evidence stop, roles not models, gates bound to hash, briefs not logs, memory scopes, autonomy by home, one skill format, model-agnostic at the node). The tables hold everything else. The hub copilot routes by scanning artifacts against the capability graph. Each line in the constitution must change behaviour; an audit may only shrink it.

## What the session does

Grilling to ratify the ten rules in his words. Then compile: read every closed central ticket, write the constitution and the tables, run a pre-mortem, and hand to the build-plan ticket.

## Unblocks

Build plan into QMA v2, system-prompt design.

## Sources

`01-bmad.md` §Q2 items 2, 3, 12 and ideas 3, 4, 16; `BACKLOG.md` B26-B29; the operator's 2026-10-16 words as paraphrased in the charting brief.
