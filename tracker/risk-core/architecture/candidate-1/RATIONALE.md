# Candidate 1: rationale

Fable, candidate 1, 6 Nov 2026. Fork sides: F-A (a) learner plus applier with modes; F-B (a) one guard package above the position. Read-only everywhere but this folder. Nothing committed. **[judgment]** marks my opinion.

## Alternatives weighed and what I rejected

**One organ for every moving number, or two.** The shipped motion engine both learns and applies (a calibrated number steps one notch when flat, G8 3.9). I split it: the learner writes a recommendation into status, the applier moves the in-force value in the number's mode. Rejected: keeping learn-and-apply in the block. It leaves `authority` a label with no reader (G8 3.10) and makes the level ladder, the cost cell and a brake threshold three different ways to move a number. One applier gives one way, one receipt, one freeze rule.

**Refresh at anchors (F-A b) as the whole answer.** I keep it as the default mode. The fa_sim shows the applier's `live` mode buys almost nothing on X4-39 for a single healthy unit (under 0.3 % of the cushion per cost event) and nothing on X4-60. What (a) buys is not growth: a number that must change between anchors for safety (a cost cell that turns the admission gate, an SQS threshold) has a mode that says so, and the receipt shows it. Rejected as a reason to pick (b): "fewer parts". Both sides need the applier organ; (b) is (a) with two modes removed and three ledger ids fewer. If he wants (b), set every preset's modes to `off` or `at_anchor` and the organ does not change.

**Halt slots inside the unit (F-B b).** Rejected for the first increment. Halts read account and trades ports and refuse at compile (R05), so (b) needs the compiler to feed cross-unit facts into the unit, and then every unit on an account carries its own copy of the portfolio brakes with no shared rank table. The guard runs every brake above the position in one place, with one rank table and one fact set, and both hosts call it, so backtest and live agree by construction. What would flip me: a unit that must carry its brakes between hosts with no guard version, which no scenario in X4's mandatory set asks for.

**Where the exit rank lives.** Decided: two tiers. The unit's own exits order themselves by the profile's `exit_set.order` (checked at compile, safest first). The guard's one rank table ranks controls: operator, protection, forced flat, kill, brake, the unit's exit, a modifier, an accelerator. Rejected: the guard re-ranking the unit's exits, because a unit must stand alone for its own close on the node (G2 ruling 11), and the guard never blocks a close in any case.

**A new package or a new module in `qml`.** The guard goes in `qmf-risk/guard`, the package G12 says stays and has no deletion planned. Rejected: `qml` (the unit must not depend on account facts) and `qmn/app` (QMB needs it too).

**Status in the R22 snapshot or beside it.** Status lives in its own file `data/deployments/<id>/risk-status.json` beside R22's unit snapshot, stamped with the spec fingerprint. Rejected: inside the snapshot, because the snapshot rule cold-starts logic state on a fingerprint change and the profile's own state must survive a logic change and die on a profile change (X1 collision 1).

**Levels as a number under the applier.** The size level is a status field with its own mode: cuts write it at once (a state transition), the climb raises it in `at_flat`. Rejected: levels as a brake, because a level is a multiplier the sizer reads, and a brake is a transition with a reason.

**R net of costs.** Rejected again, as the funnel ruled: R stays the planned loss at the disaster stop; `net_r` sits beside it; brakes, the money ledger and the gate read `net_r`. His B9 reservation stands.

**What I added beyond the funnel.** A `safe_region` fallback for the sizer (X1-H04, Simplex): when projected open risk leaves the region the fixed-fraction sizer takes over for a dwell. It is one row and one branch in the sizer adapter, and it is the named way back when the horizon sizer's inputs go stale. Also the `foreign` scope in the account numbers (DP33) as a fact the guard counts, since agent positions on the demo account move the balance the guard reads.

**What I would cut first if told to cut more.** The retune share cap and dead band (fork ids), the `live` mode (keep `off`, `at_anchor`, `at_flat`), the news window's measured-impact learning (keep the calendar tier), and the morning card's agent-written glance. None of those changes a contract.
