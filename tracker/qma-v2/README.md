# QMA v2: the agent harness

This folder holds the plan for QMA v2, the rebuilt QMX agent harness, as re-planned on 2026-10-13.

## Current files

| File | What it is |
|---|---|
| `PROMPT-HARNESS.md` | The brief for the harness coding session. The operator starts that session with the short prompt from chat. |
| `HARNESS-PLAN.md` | The harness program: 13 PRs (U0 to SIGNOFF), each with its checks. |
| `HARNESS.md` | The design contract. Its Amendments A1 to A11 win over `sketch/`. |
| `sketch/` | The type sketch of `qma2` and of the qmx-control changes. |
| `research/interrogate/VERDICT.md` | Binding rules V1 to V6 from the adversarial review. |
| `PROMPT-DELETION.md`, `DELETION-PLAN.md` | The old-code deletion program. It runs after the harness sign-off. |
| `BASELINE.md` | Parity with vanilla Claude Code and Codex. Read its corrections box first. |
| `BACKLOG.md` | Everything outside the harness, with the operator's own words. |
| `UI-NOTES.md` | Notes for the later UI session. |
| `trail/decisions.tsv` | The planning session's decision trail. |
| `reviews/` | Three audits of the 10-12/13 session that led to this re-plan. |
| `research/` | H1 (SDK facts), H2 (how to use the skills), H3 (code map), `how/`, `why/`, `architect/`, `interrogate/`. |
| `archive/` | Superseded files. Evidence only, never the plan. |

## How this plan was made

1. Three audits of the earlier session.
2. Research: SDK facts from primary pages, the skill creators' intended usage, and a code map.
3. `/how`, then `/why`.
4. `/architect`: an arena of Opus and Fable designs, judged by Fable, with the Opus design as the base and grafts from Fable.
5. `/interrogate` with Opus and Fable reviewers.
6. The multi-phase-plan playbook. Both plans pass `check-plan.mjs` with 0 problems.
