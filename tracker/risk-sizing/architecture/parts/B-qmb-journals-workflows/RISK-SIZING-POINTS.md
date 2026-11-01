# Risk and sizing points in part B

Every place risk and sizing plugs into QMB, the judge, the journals and the templates, with today's placeholder. Nothing here designs the maths; the risk session owns it (Level 0 "For the risk session"; `RISK-SIZING-PACK.md`). Placeholders are labelled blocks, shown and never refused (Level 0 AD-15).

| Plug-in point | Where in part B | Today's placeholder | What the risk session decides |
| --- | --- | --- | --- |
| The unit's risk socket in replay (sizer, exit set, halts, cross-unit hook) | QMB's unit runner hosts the socket exactly as the node does (AD-5, AD-24) | Part A's placeholder blocks: 0.5% of equity at risk at the stop, a stop beyond the last swing plus a buffer, a 2R target, a 48-bar time-out, no halts, a hook that passes every order | the blocks |
| Rounding to the lot step and the minimum lot | the unit runner (QB-08, RS-01) | round down; skip below the minimum with a reason; residue journaled in R; a test asserts every fill carries the sizer receipt's quantity after rounding, so a door that drops the size fails the build (CA-03, slices B5b and B6) | the rule for small accounts |
| A gap through the stop | the fill model's gap rule (QB-07, RS-13) | fill at the first tradable price; the loss recorded in R as it fell, never capped at 1R; `gap_through_stop` flagged on the trade | how the sizer treats gap risk |
| Margin and liquidation | QMB's margin port | values from the account and instrument records; liquidation at the record's maintenance level on mark price | margin per session (RS-09), leverage policy (RS-18) |
| Perps funding as a cost | QMB's carry adapter | funding at each funding time from recorded rates | whether funding changes size (RS-14) |
| Judging with the unit's sizer and with fixed size | the judge (AD-207) | both always shown; fixed size is the baseline | which one a verdict uses |
| Fields to replay any sizing later | the `trade` journal kind and `trade` item version 2 | equity before, session, streak, tuned values in force, `would_have` rows of stopped units, placeholders used | the replay method (RS-16, "radioactive" sizing) |
| Self-tuning of risk numbers | `calibration` rows; motion on and off in replay | no risk number moves; `applies_to_open_positions` false | which numbers may move (RS-02) |
| Trades without an initial risk | the `trade` kind's `r_missing` | flagged, never averaged as zero R (JR-15, RS-06) | R when invalidation is a condition |
| The decay check's alarm | the decay template and baseline card | informs only: OK, Watch, Alarm, with tighten-only proposal cards | the action after an alarm (RS-12, RS-17) |
| Paper after a risk stop | `paper-run` items and proposal cards | his click | whether it is automatic |
| Risk events | the `risk_event` journal kind | placeholder kinds labelled `origin: placeholder` | the real event kinds |
| Correlated exposure | the judge's correlated-market count; the MIS's dispersion reading (Part C) | counted as one record when judging; the hook passes every order | the cross-unit control (RS-03, RS-04) |
| Portfolio optimisation from journals | parked template | none | the risk session's template (ledger J-05) |
