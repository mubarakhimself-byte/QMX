# X3 roundtable (bmad-party-mode, run headless, one agent voicing every seat)

Purpose: stress the strongest hybrids before they go to the funnel. Every seat argues from its own field. The operator's seat speaks only in his recorded words (quoted from `seeds/`), never invented ones.

## Seats

- **Dana**, risk manager at a multi-manager pod shop. Money from peak, big first step, no automatic restore.
- **Kofi**, retail scalper, 1-minute FX, gold and index CFDs, 20-40 trades a day.
- **Lena**, platform engineer (SRE, Kubernetes, resilience libraries).
- **Mubarak's voice**, from his words (M8, M10, M12, M15, M33).
- **Rui**, power-grid protection engineer.
- **Ada**, clinical-trial statistician.
- **Ilya**, sceptical quant (Kaminski-Lo, Man Group).
- **Haruki**, 24/7 crypto perps trader.

## Round 1: the fast breaker (H01, H02, H03)

- **Kofi:** "Two stops and I'm out for the day? At 30 trades I'd be out by 9 a.m. every day. Your table says I'd keep 18 % of my edge. Money at my own 1 % worst stretch I can live with."
- **Dana:** "Money, yes. Every pod rule I know is money or drawdown, never counts. But your threshold comes from the unit's own card. A card is a backtest. Backtests flatter. I'd cap the own-percentile level by a hard dollar line from his budget."
- **Ilya:** "Your sim says the money brake has almost no timing value on independent trades. Kaminski and Lo would agree: on a random walk a stop costs return. So say plainly what the brake is for: the tail and the record, not alpha."
- **Mubarak (M12):** "you can't just say that breaks that count losses fire on health units just by chance ... breaks, remember, also take into account ... first invalidation."
- **Ada:** "Loss points by size answer that. A -0.3R cut costs 0.3. A breakeven costs its fees. That is graded toxicity, the way EWOC counts only serious events."
- **Haruki:** "What's a day? My market never closes. Your window in trades fixes that for me. Keep it."
- **Amendments:** (a) the own-percentile level is clamped by a dollar ceiling from his budget (Dana) → H01 gains a clamp input; (b) H01 states its job as tail control and evidence, not alpha (Ilya); (c) the window is in trades, with a declared day only for budgets (Haruki).

## Round 2: the two-speed circuit breaker and graded demotion (H08, H11, H49)

- **Mubarak (M10):** "it helped us detect alpha decay ... It was a big break. One of the biggest, but again, it's a baseline improve it, please."
- **Ilya:** "Your own numbers: density catches a dead edge in a quarter to a half of runs at 10 a day; the trade CUSUM catches nearly all. Density is the worse sensor."
- **Ada:** "Worse at speed, better at calm. At 40 a day CUSUM alarms on more than half of bad weeks. That is why trials separate a futility look from an efficacy look. Use CUSUM to warn and cut, density to confirm."
- **Mubarak (M10):** "You can't simply say if they differ, you simply pull out. It can be a bad day ... You're meant to size down, I think, but not quickly."
- **Dana:** "We halve at the first level. We don't wait for a second key to halve."
- **Lena:** "That's the reversible step. Your graded run kept 902 of 950R after a bad week where permanent demotion kept 614. Reversible steps are cheap mistakes. Make paper the only step that needs both keys."
- **Amendments:** (a) a warning halves at once on either key (Dana); (b) the step to paper needs both keys, or one key staying past a planned look (Ada); (c) the old breaker's density is kept and named as the confirming key (his ask honoured).

## Round 3: proof and shadow (H13, H14, H12, H65)

- **Lena:** "Every new breaker in resilience4j can run METRICS_ONLY. Envoy ramps enforcement from zero. Do both."
- **Ilya:** "And the random control at the same fire rate. Without it you're measuring 'traded less'."
- **Kofi:** "Thin units can't prove anything in a month."
- **Ada:** "Then replay the brake on the unit's own holdout trades and pool the result by brake type across units of one family. Prove the brake type, then fit the unit's percentile."
- **Rui:** "In my world a protection device has a test certificate before it's energised, and its trip record is reviewed. Same thing."
- **Amendments:** (a) random-control margin is computed first on replay, then on shadow live; (b) brake types are certified per family, thresholds per unit (Ada); (c) a choke budget refuses a bench-type brake whose expected healthy fire rate is above about 5 % of days (H65).

## Round 4: restores (H15, H17, H18)

- **Dana:** "We don't restore automatically. The firm re-sizes later."
- **Mubarak (M33):** "I don't want just safety. I want something that can like perform ... the sitting duck thing."
- **Lena:** "Half-open: a few probes, judged as a group. Fail, and the wait doubles. Fail K times and it locks for a human. That's a recloser."
- **Rui:** "Eighty to ninety per cent of faults are transient. That's why reclosers exist. One shot, then lockout, is the conservative setting."
- **Kofi:** "Probe at minimum size. At $500, gold's minimum lot may already be bigger than your probe."
- **Amendments:** (a) automatic restore applies to benched and reduced states only; a HALTED state from a risk stop still waits for his resume (collision with Dana noted, kept); (b) probe size is the smallest feasible lot, else the probe runs on paper (Kofi); (c) restore never goes above baseline: accelerators belong to X2.

## Round 5: isolation and the BMS breaker (H24, H28, H29, H30, H31)

- **Mubarak (M10):** "it can isolate crypto. And everything is off for crypto ... It should kick in with the with evidence that this market should be isolated."
- **Rui:** "Selectivity: the nearest protection acts first. Instrument, then class, then the whole BMS. But money hard limits never wait for a graded delay."
- **Lena:** "Envoy never ejects more than a capped share of a cluster. If everyone looks bad, it's not the hosts."
- **Haruki:** "Crypto risk-off shows as funding and liquidations, and venues go down. 'Exchange resumed' doesn't mean liquid."
- **Kofi:** "When the broker pulls quotes, every FX pair goes 4x spread. No price move. SQS on K of N pairs catches it before any loss."
- **Dana:** "Two tells agreeing, or I've got analysts isolating the book on noise."
- **Amendments:** (a) isolation is graded: no new entries by default, reduce, flatten only at the top (Rui, Dana); (b) peer ejection capped and paired with an absolute floor (Lena); (c) unknown data is not calm: fail closed (Haruki); (d) re-entry after isolation needs spreads and fills inside collars, not a timer.

## Round 6: exits (H38-H43)

- **Mubarak (M15):** "the dynamic SLNTP system was ... replaced by the first invalidation specifically for scalpers. But then for intraday ... I think it was just moving the stop loss to break even, depending on how much you are winning."
- **Ilya:** "Breakeven is just another fixed stop. Carver says so. Nobody has tested it after costs."
- **Kofi:** "My cut is where my winners almost never go. If 90 % of winners never go below -0.4R, I cut at -0.5R."
- **Ada:** "Then test that cut against no cut and against one bar later, with costs, out of sample, and count it as a trial."
- **Haruki:** "Gaps. Weekend gaps on CFD crypto. The disaster stop is a trigger, not a fill."
- **Amendments:** (a) breakeven is off by default and earns its place per unit through the two-arm test; (b) FI cut from winners' MAE plus a named falsifying condition; (c) every exit records mechanism and outcome; (d) stops are modelled at the stressed spread.

## Round 7: the kill switch (H62)

- **Mubarak (M5):** "The kill switch has survived multiple versions ... it earned its spot ... closing a trade is never blocked."
- **Lena:** "Two meanings of stop on one node is a bug factory. Keep the kill level his. Let rules raise stand-downs in their own scope table."
- **Dana:** "Our firm kill switch is manual too. Automatic systems block entries; humans flatten."
- **Amendments:** the BMS breaker raises a stand-down at scope `all` (entries only) and may request a kill level through a card; no automatic path ever lowers anything he raised.

## What the roundtable changed

1. H01 gains a dollar clamp from his budget and a stated job (tail and evidence).
2. H11 and H49: either key halves at once; paper needs both keys or persistence past a planned look.
3. H13: proof by brake type per family, threshold per unit.
4. H15: automatic restore only for benched and reduced states; probes at the smallest feasible lot or on paper.
5. H28 and H30: graded isolation, capped share, absolute floor, fail closed on unknown data.
6. H41: breakeven off by default; on only after the two-arm test.
7. H62: rules raise stand-downs; the kill level stays his.
