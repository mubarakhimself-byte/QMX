# Review: rubric walker (the good-spine checklist), with the lint pass

Run by agent A0 in sequence, as `references/reviewer-gate.md` allows when sub-agents are unavailable: the file was written first, then dropped from working context. One mind wrote and reviewed this spine, so this lens is weaker than an independent reviewer; the quick review R0 by a fresh agent is the independent check (STATE "RESUME HERE", step 2).

## Lint

`uv run .claude/skills/bmad-architecture/scripts/lint_spine.py --workspace level-0` on the final spine:

```json
{"ok": true, "spine": "ARCHITECTURE-SPINE.md", "total_findings": 0, "by_severity": {}, "findings": []}
```

It also returned 0 findings on the first draft and after the review fixes (CHECKED, three runs).

## Verdict

**Passes, after six fixes applied.** The spine fixes the divergence points the three Level 1 agents could hit, every AD carries Binds, Prevents and Rule, and every structural dimension at initiative altitude is decided, deferred or open. The six fixes came from this walk and the adversary lens and are in the spine.

## The checklist, item by item

| Item | Finding | Action |
| --- | --- | --- |
| Fixes the real divergence points for the level below, misses none | Three Level 1 agents could each define a shared shape (CT-23 format 3, reading cards, records) | **Fixed:** a conventions row names one Level 1 owner per shared shape; `01-connections.md` §5 lists one owner each |
| Every AD's rule is enforceable and prevents its divergence | AD-25's try ledger as "a family record" let two concurrent runs write one record | **Fixed:** append-only rows per run, counts at read |
| | AD-38's self-healing had no mechanism for a tripped app process (the supervisor never restarts by itself, `supervisor.py:828`, `:863`) | **Fixed:** opt-in restart with back-off (AD-33), named as a ruling-46 fix in Amended decisions |
| | AD-5 (same code) and AD-24 (the hook) disagreed: the hook ran only in the node | **Fixed:** the hook runs in whichever host drives the unit |
| Nothing under Deferred could let two units diverge | Deferred items are inside one part each (node internals to C, schemas to A and B); packet order to P2 | none |
| Named tech verified current | See `review-currency.md`: pins are the repo's; three are behind the vendors' latest and none is bumped by this spine | none |
| Ratifies, not contradicts, the brownfield code | Kept: the catalog, the Library's rules, the engine, the mini-app core, QML's seam, the node's organs. Each change to shipped code or an inherited decision is in "Amended decisions" with its reason, and the risky ones were run (`blast-radius.md`) | none |
| Covers the driving input's capabilities | Every part the brief lists has a verdict, status, owns and never owns, rules, language, Windows and Linux, local first, growth seam and cases; every one of the 267 cases and 18 risk rows is owned exactly once (CHECKED by `score.py`: 285 assigned, no duplicates) | none |
| No new AD weakens an inherited one | Five inherited decisions are amended (engine AD-31, AD-69; Lab AD-5, AD-17; Library AD-3), each named with a reason; none is weakened silently | none |
| Every dimension decided, deferred or open, incl. the operational envelope | Deployment and environments: AD-4, AD-37, AD-45 and the placements diagram. Infra and providers: servers by his cards through the connect dialog; the region study deferred to C. Operations: AD-38, AD-42, AD-43. Security: the conventions row on secrets was missing | **Fixed:** a secrets row (machine stores only, the redaction seam, the secret scan) |
| Journals had two homes for backtest calibration rows | Results carried calibration rows while the unit journal also took backtest rows | **Fixed:** a backtest run's unit journal lives inside its `backtest-result` (AD-27, AD-35) |

## Left for R0

- A0's scores for its own pick (567 of 570) are judgements; R0 should rescore a sample of the 285 rows independently.
- The unproven facts named in `blast-radius.md` "Not proven here" and in the memlog's questions.
