# QMA v2: the agent harness

This folder holds the plan for QMA v2, the rebuilt QMX agent harness. It was re-planned on 2026-10-14 for one engine, the Claude Agent SDK, plus a GPT translator for the operator's ChatGPT sign-in.

## Current files

| File | What it is |
|---|---|
| `PROMPT-HARNESS.md` | The brief for the harness coding session. The operator starts that session with the short prompt from chat. |
| `HARNESS-PLAN.md` | The harness program. It has 18 PRs: HP0 to HP2 are probes, HP3 to HP16 build the harness, and HP17 is the operator's sign-off. |
| `research/one-engine/architect/DESIGN.md` | The design contract. `SYNTHESIS.md` records how it was chosen, and `sketch/qma/` holds the type sketch. |
| `research/one-engine/interrogate/VERDICT.md` | The adversarial review and the lead's verdict. DESIGN.md applies every act-on item. |
| `PROMPT-DELETION.md`, `DELETION-PLAN.md` | The old-code deletion program, D1 to D4. It runs after HP17 and the operator's sign-off. D2 goes to the QMB session. |
| `research/one-engine/01-requirements.md` | The operator's rulings (latest wins), corrections and requirements, rebuilt from the raw transcripts. |
| `research/one-engine/02-claude-sdk-and-providers.md` | The index to the SDK research (`02a`) and to the providers, translator and policy research (`02b`). |
| `research/one-engine/03-gaps.md` | What the old OpenAI side covered that Claude does not, and the two-engine gray areas. |
| `research/one-engine/04-baseline.md` | What vanilla Claude Code gives, what QMX adds, and the acceptance checks. |
| `research/one-engine/how/`, `why/` | How the current code at origin/rebuild/base works, and why the old design had its shape. |
| `BACKLOG.md` | Everything outside the harness, in the operator's own words. |
| `UI-NOTES.md` | Notes for the later UI session. |
| `trail/decisions.tsv` | The planning decision trail. |
| `reviews/` | Three audits of the 10-12/13 session. |
| `archive/` | Superseded files, including the 2026-10-13 two-engine plan. They are evidence only, never the plan. |

## How this plan was made (2026-10-14)

1. Agents mined the raw transcripts, then researched primary sources in the built-in browser.
2. A gap analysis and a one-engine baseline followed.
3. `/how` mapped the current code, then `/why` explained the old design.
4. `/architect` ran an arena of three Opus designs: thin native, local gateway and OS boundary. An Opus judge picked thin native as the base, and the lead grafted ideas from the other two.
5. `/interrogate` ran two Opus reviewers. The lead's verdict removed one failed premise, a settings file the agent could write, and applied 30 fixes.
6. The multi-phase-plan playbook produced both plans. Both pass `check-plan.mjs` with 0 problems.
