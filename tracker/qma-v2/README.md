# QMA v2: start here

QMA v2 ("Quant agents", version 2) is the rebuilt agent system of QMX. This folder is the single current home for its plan.

## Files, in reading order

| File | What it is | Status |
|---|---|---|
| `PRD.md` | Requirements: 148 FRs (81 needed for Wednesday), 39 NFRs, constraints, glossary, port list, questions | Current |
| `HOW-WHY.md` | What each requirement touches in today's code, and why that code is shaped that way | Coming next |
| `ARCHITECTURE.md` | The design, built against the PRD | After HOW-WHY |
| `ARCHITECTURE-CHECK.md` | Every FR and NFR mapped to the architecture; gaps listed | After ARCHITECTURE |
| `SHIPPING-PLAN.md` | Ordered slices with "done when" checks, for the orchestrator session | After the check |
| `FILE-INDEX.md` | Verdict on every earlier planning file (current input, reference, superseded) | Current |

## Planning order (agreed 2026-10-12; don't skip steps)

1. **Requirements:** extracted from the transcripts, then merged into `PRD.md`.
2. **`/how` and `/why`:** run against the PRD, before any design.
3. **`/architect`:** on Fable, designed twice, then synthesised.
4. **Check:** every requirement traced to the design.
5. **Shipping plan:** pstack poteto-mode multi-phase-plan.
6. **Orchestrator session:** a fresh session coordinates one agent per slice. It ships into `rebuild/base`, because `integration` isn't ready. Docs stay live as each slice lands. `main` moves only by the operator's click.

## Inputs still in use

- `tracker/agent-system/research/`:
  - `01` (Claude Agent SDK facts)
  - `05` (usage telemetry)
  - `19` (the two-SDK study)
  - `20` (direction; §4 overrides)
  - `21` (mini-app and workflow seeds)
  - `22` (cookbook templates)
  - `24` (integration surface)
  - `26` and `27` (requirement extractions)
  - `00` (ledger)
- `rebuild/research/2026-10-12-agent-system/models-routing.md`: vendor terms.

Superseded files sit in `tracker/agent-system/archive/` and `rebuild/research/2026-10-12-agent-system/archive/`. Each is stamped and kept for history.
