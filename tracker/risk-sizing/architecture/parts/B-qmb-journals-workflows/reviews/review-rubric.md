# Review: rubric walker (good-spine checklist)

Run by part B's agent in sequence, as the reviewer gate allows when sub-agents are barred (`bmad-architecture/references/reviewer-gate.md`), against `ARCHITECTURE-SPINE.md` after `lint_spine.py` reported 0 findings. Fixes marked "applied" are in the spine now; the linter was rerun after them (0 findings).

**Verdict.** The spine fixes the divergence points a builder one level down would hit, ratifies the built code, and inherits Level 0 without weakening it; three gaps in the operational and data dimensions were found and closed.

| # | Checklist item | Finding | Severity | Action |
| --- | --- | --- | --- | --- |
| 1 | Fixes every real divergence point | The CT-13 store keeps its own world rooms (`live`, `replay`, `simulated`, `qmf-core/src/qmf/core/fingerprint.py:412-424`) while the envelope has seven worlds; two builders could map them differently | high | applied: AD-209 maps every hot-path stream to the `live` room and keeps the finer world in the envelope; backtest, stress and synthetic never use the hot path |
| 2 | Fixes every real divergence point | Who commits a node's closed months was open: the app cannot call its host's door | high | applied: AD-209 and AD-210, the machine's host commits sealed months from the app's volume (the records job's local half, on every machine) |
| 3 | Every Rule enforceable | AD-202 named "the principal" without its format; PR 204 stamped copilot runs as `operator` | medium | applied: the principal is the door's caller as the host names it, never rewritten |
| 4 | Every Rule enforceable | A row whose `t` is clamped past its month would sit in a partition the store's read filters out (`series.py:690`) | medium | applied: a row's partition month is the month of its `t` |
| 5 | Operational envelope covered | QMB's logging and telemetry were not stated ("storage exists, so wire the logs") | medium | applied: AD-215 keeps the app's own logs and adds per-run spans through the one telemetry switch |
| 6 | Operational envelope covered | A host restart mid-run left a ticket `opened` forever | medium | applied: AD-202 reconciles open tickets against the job queue at host start |
| 7 | Nothing under Deferred lets two units diverge | "Where the G verdict lives" is deferred to Part A, with a default home named | low | kept: the default is concrete, so B and A cannot diverge before A decides |
| 8 | Named tech verified | No new dependency; pins inherited from Level 0's CHECKED table | none | none |
| 9 | Ratifies the brownfield | The host-job pattern, the job queue, the artifact sink, the CT-13 store and the typed store are all used as built; changes are listed with their one safety fact | none | none |
| 10 | Parent inherited without weakening | Four refinements of AD-34, AD-32, C10 and C11 are surfaced in "Conflicts with the parent", none overridden silently | none | none |
| 11 | Every dimension decided, deferred or open | Deployment (homes, Windows, servers as capacity), operations (host jobs, telemetry), data (kinds, partitions), security (no tester network or keys) are each decided | none | none |
