# Review: rubric walker (good-spine checklist)

Reviewer gate of `bmad-architecture`, run in sequence by the part's agent (no sub-agents allowed by the brief), against `ARCHITECTURE-SPINE.md` and its area files. `lint_spine.py` reported 0 findings before this pass.

**Verdict.** The spine fixes the divergence points the slices would hit (operation shapes, tags, the store's two writers, the route's verbs, the keys document, the reading record) and covers the operational envelope (placements, setup, updates, alarms, healing, regions). Two inherited decisions are tightened without being surfaced, and three rules need one more line each to be enforceable.

## Findings

| # | Severity | Finding | Fix |
| --- | --- | --- | --- |
| RW-1 | High | AD-313 puts tick-tier market-state readings (tick rate, depth, order-flow pressure) in the node, while Level 0 AD-40 gives market-state readings to the `mis` app. That is a refinement of an inherited decision and must be surfaced, not silently applied | add CF-6 to "Conflicts with the parent" |
| RW-2 | High | AD-308 refuses two units on one symbol of a netting account; the catalogue's proof for UT-14 and Level 0's risk table say "one virtual position per unit; the venue nets". Stricter than the parent, not surfaced | add CF-7, and name the rule a placeholder for the risk session (it already says so) |
| RW-3 | Medium | AD-314 and the conventions key a reading series by source, reading, market, instrument and machine, but not by tier; a reading with two tiers (spread at tick and bar) would get two series from two sources under one reading id, inviting double counting | add the tier to the series key and say each (reading, tier) pair has one writer kind |
| RW-4 | Medium | AD-303's outbox holds a change "while a node is down"; if direct calls bypass it while the node is up, an earlier queued `pause` can land after a later direct `resume` | every `manage` change passes the outbox, in order |
| RW-5 | Medium | AD-307 writes `road/host-facts.json`; the road folder is copied whole into a move snapshot (`qmx_apps/supervisor.py:1076-1079`), so stale facts could travel to a new home | write `road/host/facts.json` before the app starts and on every change, so the new home's host overwrites it first |
| RW-6 | Low | The Stack row for keyring says "as locked"; a pin needs its number | `qmx-agents/uv.lock` pins keyring 25.7.0 |
| RW-7 | Low | AD-305 does not say what happens to the dead node's deployments after a take-over; they name the old identity and would be refused | the take-over re-issues them from This PC for the new identity |

## Checked and fine

- Every AD carries Binds, Prevents and Rule; ids ascend from AD-301.
- No new AD weakens an inherited one except the two surfaced above (CF-1 to CF-5 already listed the others).
- Deferred items cannot let two slices diverge: the board relay (C-22) has a declared fallback; the prune is out of scope with a rule for when it comes.
- The brownfield code is ratified where it works (organs, step runner, door, routes) and contradicted only with a cited line.
