# X6 brainstorm intent: observability for the unit risk template

Source: `.memlog.md` in this folder (163 entries, 140 ideas). Techniques: Morphological Analysis, Concept Blending, Forced Relationships, Cross-Pollination, Trait Transfer, Evolutionary Pressure, Solution Matrix, then domain shifts (experiential, performance, failure modes, wildcards). Problem solving in `problem-solving.md`; roundtable in `roundtable.md`. The full write-up is `expansion/X6-observability.md`.

## The need

He asked how the UI shows that QMX is wrong, right, working, up, on and trading (D49), and which brake tripped (C7). Today the node reports health, not risk (G11 §0.10).

## What the session found

1. **One fold, many readers.** A `RiskState` fold over append-only journals, computed by one library, read by the guard, the UI, the phone, MCP tools and the Lab. No screen computes risk on its own.
2. **His six words as predicates** over the fold, each with inputs and a freshness limit, and UNKNOWN as a seventh state. Normal is quiet (dark cockpit); a stale fact turns grey, never green.
3. **Closed reason codes and two ledgers.** Codes at source fix the risk-stop-as-kill-switch bug; a money ledger feeds brakes and an event ledger (FI rate, scratch rate, full-stop share) feeds decay.
4. **Enforcement apart from notification.** Trips never wait for alerts. Four tiers: silent act, digest, ticket, page. Money facts may page; edge estimates open tickets; learner moves are digest lines.
5. **A wake contract for one sleeping operator.** Wake only when money is at risk now, the system cannot fix it alone, and his action changes the outcome by a deadline. The system has already done the safe thing.
6. **Alarm economics as performance telemetry.** Brake precision against a random brake, trip tax, sitting-duck meter, accelerator earned-keep, growth waterfall.
7. **Receipts for every number move**, naming learner, applier, mode and reason, with his spec kept apart from the runtime's status.
8. **Costs against assumptions per cell**, slippage from node order rows, funding and roll as their own lines.

## Hand-off

- 47 hybrids (21 solid, 21 plausible, 5 wild), 12 problems with 2-3 solutions each, 19 collisions, 7 restructure proposals and UI requests for 16 screens: `expansion/X6-observability.md`.
- New variables: `ledger/additions/X6-observability.yaml`.
