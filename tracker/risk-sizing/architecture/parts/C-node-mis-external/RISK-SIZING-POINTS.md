# Risk and sizing points in Part C

Every place in the node, the MIS, the venues and the records where risk and sizing plug in, with today's placeholder. Nothing here designs risk or sizing maths: that is the risk session's (ledger R-01, R-04). Every placeholder is an ordinary labelled block or setting (Level 0 AD-15), shown on the unit card, the promotion card, every trade row and the node page, and listed by the rip-out query. Level 0's own list ("For the risk session") stands; these are the rows Part C adds or makes concrete.

| Point | Where | Today's placeholder | What the risk session decides |
| --- | --- | --- | --- |
| Kill-switch effect per level | the kept kill switch (`qmn/src/qmn/protection/effect_matrix.py`, "shape only, no values") | YELLOW: no new entries at the scope. ORANGE: also cancel resting entry orders. RED: also close positions at the scope, reduce-only. BLACK: everything at every scope closed and the node paused. Automatic escalation is escalate-only; resume is his. All labelled `origin: placeholder` | the values and which triggers escalate how far |
| The kill line's verb | the kept kill line (`qmn/src/qmn/capital/kill_line.py`) | after the shell cut, a breach stops new entries for that binding, leaves exits and broker stops, and waits for his resume (Level 0 AD-36) | flatten or stop, and the floor's number |
| Protection that cannot be placed | the node's order path (spine AD-308) | after 3 failed placements within 2 s each, close that position reduce-only and raise a protection-escalation alarm | whether to close, hedge or alarm only |
| Two units on one symbol of a netting account | deploy preflight (spine AD-308) | refused, naming the fix (a hedging account or another account) | how shared protection and attribution work on netting accounts (RS-10) |
| The cross-unit hook before every order | the order path, step 3 | passes every order | correlation and book control; it may read the MIS's dispersion and herding readings (RS-03, R-06) |
| Account facts the sizer reads | the node's account facts per binding (equity derived as balance plus unrealised P&L on cTrader, which gives no equity field; account value on Hyperliquid), each with its time and source | equity of the bound account | the budget share per unit (R-09) |
| Leverage and margin | the account and instrument records (spine AD-312) | the node never changes a venue's leverage; it reads it into the account record; a change stands the symbol's units down until his click (RS-18) | whether the node sets leverage, and the margin rule |
| A stop past the liquidation price | the protection gate | refused at entry with a typed reason, using the record's liquidation rule and the account's leverage (a fact check, not a sizing rule) | margin and liquidation policy (RS-09) |
| Account-scope halts (a daily loss limit, RS-11) | the unit document's halts slot, run on the trading machine | empty, shown as a warning | the halts and their numbers |
| Minimum lot and rounding | the node, from the instrument record | round down to the lot step; skip below the minimum with the residue recorded in R | the rounding rule on small accounts (RS-01) |
| A gap through the stop | the node's journal | the fill at the first tradable price, the loss in R as it fell, never capped at 1R | gap risk in sizing (RS-13) |
| Funding and swaps held through their time | records (carry), readings (funding state) | recorded as costs; no rule | whether units avoid funding times (RS-14) |
| Paper after a risk stop | lifecycle (Part A) | his click | direct or by his click |
| The numbers a live deployment starts from | the promote action (spine AD-324) | paper starts from the unit's defaults; live from the paper lane's last calibrated values and watermark, the calibrator's statistics restarting there (LC-C-39) | whether sizing numbers carry from paper to live, restart, or carry full state |
| The size the venue receives | the order path; slice C-12a's test | the sent quantity equals the sizer receipt's after lot rounding (CA-03) | none: a fact check, kept |
| Decay and drift alarms | the node watcher template (Part B) | inform only | the action (RS-12, RS-17) |
| What a stopped unit would have done | the node's unit journal | would-have rows of stopped units (Part B's kind) | replaying old sizing (RS-16) |
