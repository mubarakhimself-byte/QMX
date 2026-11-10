# Stop point A: one unit trades on paper

This is the release note for stop point A. It says what now works, what is still a placeholder, what your signature covers, and which red tests are not part of this slice.

## The line to sign

Sign the trading node at version 0.1.15. That signature records stop point A. One unit trades on paper from zero, with no broker and no judge, sizes itself, and brakes bind on any unit that declares them.

QMB, the tester app, moves to 1.0.10 in the same PR because a test file joined its folder. QMB never touches money and is not part of what you sign.

Only your hand signs. The control service's signing route is operator-only and is not an agent tool. The only signature a shipped module makes is the shipped-apps test's own, in a throwaway home.

## What now works

- A new person starts from nothing. The practice month of bars ships with QMX, the `canary` template ships with it, and a first backtest runs with no broker and no sign-in.
- One click takes a draft to paper after the safety half of G, with no judge run. The walk from an empty folder ends with one filled paper trade and a decision row written before the send.
- The unit sizes itself. The sizer answers a money amount, converts it with the account's own rate, refuses an absurd size by name, and every trade answers "why this size?" from one row.
- A broken block costs its unit its new entries, not its exits. One bad unit out of two hundred stays one card, and the other units keep trading.
- Every exit runs on every bar, side-correct, and says why it closed. Brakes are rows read from one fold, and a brake can flatten, stop, or send a unit back to paper. Only the rows that say they wait for a hand wait for you.
- No agent tool reaches promote, the kill level, the floor, or the plan hash.

## What is still a placeholder

- Every number is a labelled placeholder with a range and a reason, owned by "numbers talk". This slice does not tune one.
- The `canary` template carries no brakes, and its title and claim card say so. It is the shape a new person starts from, not a unit to trade live.
- Size and exit numbers stay fixed in this slice. The filter number `min_trend_strength` is the one number this slice proves can move. After 20 closed trades it reads 0.0001, from 0, by the built engine. Sizing and exit numbers first move in stop B.
- Nothing here is live. No broker is bound, no venue sign-in happens, and no order leaves the machine.

## The two shortfalls this slice carries

- The practice account cannot land in the Library. The Library's account kind allows a world of `demo` or `live`, and a practice account is neither. Claiming a world it is not would put a false real-tick share on the card. So K7, the walk from an empty folder to one filled paper trade, ends on the fake broker. Every practice row and card still says `world: paper` and `venue_kind: practice`, so nothing claims to be real ticks.
- A production binding path for the practice venue belongs to the release owner. The node's composition root binds a venue only through the cTrader door. Until that path exists, the practice venue is a rehearsal lane, not a shipped door.

## What your signature covers

Your signature covers the trading node at 0.1.15 and the QML that node's lock points at, including every shipped block this slice changed. It covers the paper baseline in this note. It does not approve live trading, does not turn a placeholder into a number, and does not make the practice venue a production binding.

No tool enforces this signature yet. There is no signature gate in the release tooling, so this note and the version row are the record.

## Known reds that are not this slice

These tests are red at the tip. Each is traced to a row that is already stacked, and each is queued for the sweep after stop A. The plan's Appendix E names three more baseline reds, and those remain too.

- `qmx-agents/packages/qmx-tools/tests/test_derive_bars.py::test_derived_pairs_give_the_same_bars_and_trades_as_the_ticks`. RC-11 made every exit run each bar side-correct, so a derived-pairs run closes at different bars than it used to. The test still expects the tick run's equality.
- Six R and money literal reds in `qmx-agents/apps/qmb/tests`. Four are `test_qmb_run_kinds.py::test_a_scenario_that_may_improve_is_a_counted_rerun_and_a_view_is_not`, `::test_a_six_cell_sweep_lands_six_tries_in_the_units_family`, `::test_a_worsen_only_scenario_that_improves_is_refused_with_its_reason`, and `::test_the_judge_reads_each_check_from_the_run_of_that_kind`. Two are `test_run_honesty.py::test_a_block_that_raises_lands_a_failed_result_with_its_reason` and `::test_a_stated_cost_profile_changes_money_and_not_r`. The cost-profile one fails from RC-11 up, and the raising one already fails at RC-10. All six pin old R or money literals.
- `qmx-agents/packages/qmx-host/tests/test_lifecycle.py::test_the_writer_refuses_a_move_fold_rejects_and_writes_nothing`. It pins the old refusal text, "only his click moves a unit to paper", while the shipped law now says "only his click promotes a unit to paper; a risk rule may only send it to paper".
- Three in `tools/tests/test_dictionary_port.py`: `::test_the_dry_run_ports_239_into_239_drafts_and_loses_none`, `::test_a_rerun_changes_nothing_even_on_a_crlf_checkout`, and `::test_a_slug_two_families_share_is_scoped_by_family_and_linked`. The seed `tools/dictionary/port.json` is stale.
