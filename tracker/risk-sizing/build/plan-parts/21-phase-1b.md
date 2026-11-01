## Write the indicator family of the first content wave (A13a)

Phase 1, QML and the dictionary in depth. Part A slice A13a, Part A AD-114 and `4-dictionary.md` section 5, Level 0 AD-19. Ruling 13 (directions, ground first, no cap) and ledger D-06. The grounding brief every A13 builder follows is Appendix F. Real step none on his folder until he lands it. Done when MetaTrader's built-in indicators and the census gaps are entries with sources, every one computable from bars and quotes has code with golden tests, and a start lands the family once.

**Depends on.** A12.

**Files.**

- [ ] Create the entries as `qmx.entry/1` documents in `qml/catalogue-seed/wave-1/indicators/`, each with its sources, an exact quote under 15 words and a date.
- [ ] Create the block sources under `qml/src/qml/blocks/stdlib/<entry>/1/` for every computable entry, the golden fixtures in `qml/tests/golden/indicators/` (from TA-Lib through `tools/dictionary/golden_talib.py`, or a published table), and `qml/tests/test_wave1_indicators.py`.
- [ ] Create `tools/dictionary/land_seed.py`, which lands a seed folder's entries as drafts once per store, keyed by fingerprint, and edit `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` to run it for every folder under `qml/catalogue-seed/wave-1/`.

**Build.**

- [ ] Write every indicator research 36 section 3 and research 45 section 3 list, with no cap. At least CCI, Parabolic SAR, Williams %R, Awesome and Accelerator, Alligator, DeMarker, MFI, OBV, A/D, RVI, Force, Bulls and Bears, TRIX, ATR, MACD, Bollinger, ADX, Stochastic, VWAP and session range. "Too many" is never a reason to stop.

**You see.**

- [ ] The dictionary has every indicator a MetaTrader trader expects, each with working code.

**Verify, unit.**

- [ ] The entry checker and the corpus gate give zero errors. The status script's counts for the family go in the PR body. Every golden test passes, with warm-up values missing and not zero. Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The status script over the family. Save `a13a-status.log`. Pass when it reports zero checker errors and no entry claims `native` without a source.
- [ ] Lane 3. The family's golden tests. Save `a13a-golden.log`. Pass when every value is within its golden tolerance.
- [ ] Lane 4. Start the host twice on a throwaway folder. Save `a13a-land.log`. Pass when the family's drafts land once.
- [ ] Lane 5. `blocks_match` on 20 sentences taken from the family's sources. Save `a13a-match.log`. Pass when each maps to an entry or comes back as an append request, and no entry was made silently.
- [ ] Lane 6. The cut-against-full and no-future tests for every new block. Save `a13a-future.log`. Pass when every block passes both.
@menu

**Verify, perf.**

- [ ] Metric. Median microseconds per update for each new block over a week of M1.
- [ ] Probe. A4's bounds lane run on the new blocks.
- [ ] Baseline. A4's blocks' medians.
- [ ] Rule. Fails when any block's last-tenth median is more than 1.5 times its first-tenth median (`update_time_growth_tolerance`).

**Review gate.** Lens verification-gap, on the golden values and the sources. The blast-radius fact is that the corpus gate in `tools/ci.py` covers the new entries.

@merge

## Write statistics as readings in the first content wave (A13b)

Phase 1, QML and the dictionary in depth. Part A slice A13b, `4-dictionary.md` section 5, Level 0 AD-40 (every reading is a catalogue block with a reading card). Rulings 13 and 55 (an MIS core that needs no training). Real step none on his folder until he lands it. Done when Hurst, variance ratio, efficiency ratio, half-life and change points, and the models research 45 names, are entries, and every one computable from bars has code with golden tests. These are the blocks the MIS app's default packs bind by entry id in C-09, so the MIS never holds a second copy.

**Depends on.** A13a, which brings the seed landing.

**Files.**

- [ ] Create the entries in `qml/catalogue-seed/wave-1/statistics/`, each with its reading card (tier, clock, measures, data level and fallback, lag, minimum sample, valid classes, three outputs, health word).
- [ ] Create the block sources under `qml/src/qml/blocks/stdlib/<entry>/1/`, the golden fixtures in `qml/tests/golden/statistics/` from a published table or a reference run named in the fixture, and `qml/tests/test_wave1_statistics.py`.

**Build.**

- [ ] Write Hurst, variance ratio, efficiency ratio, half-life and change points with code, and HMM and GARCH as `specified` entries with their sources. Write every further statistic the sources use, with no cap.

**You see.**

- [ ] The dictionary can name the state of a market in numbers a trader knows, each with its freshness and its fallback.

**Verify, unit.**

- [ ] The entry checker and the corpus gate give zero errors. The status counts go in the PR body. Every golden test passes. Each reading card's minimum sample is honoured, with the value missing below it. Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The status script over the family. Save `a13b-status.log`. Pass when it reports zero checker errors.
- [ ] Lane 3. The family's golden tests. Save `a13b-golden.log`. Pass when every value is within its tolerance.
- [ ] Lane 4. Each block on a series shorter than its minimum sample. Save `a13b-minsample.log`. Pass when each answers missing with its health word and never a number.
- [ ] Lane 5. Start the host twice on a throwaway folder. Save `a13b-land.log`. Pass when the family's drafts land once.
- [ ] Lane 6. A random walk and a trending fixture through Hurst and the variance ratio. Save `a13b-sanity.log`. Pass when the random walk reads near 0.5 and 1 and the trend reads above both, within the fixture's stated bounds.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds per update for each new statistic on a year of H1.
- [ ] Probe. Lane 3's inputs run through each block.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens verification-gap. The blast-radius fact is that the corpus gate covers the new entries.

@merge

## Write the markets beyond forex in the first content wave (A13c)

Phase 1, QML and the dictionary in depth. Part A slice A13c, `4-dictionary.md` section 5. Rulings 13, 29 (futures designed now, "spoiled for choice") and 40 (order flow as data, placeholders behind a seam). Real step none on his folder until he lands it. Done when market profile, the futures calendar, perps fields, and index and metals clocks are entries, mostly `specified`, with code where bars and quotes feed them.

**Depends on.** A13a, which brings the seed landing.

**Files.**

- [ ] Create the entries in `qml/catalogue-seed/wave-1/beyond-fx/`.
- [ ] Create block sources under `qml/src/qml/blocks/stdlib/<entry>/1/` for the computable ones (market profile from bars, session clocks), golden fixtures in `qml/tests/golden/beyond-fx/`, and `qml/tests/test_wave1_beyond_fx.py`.

**Build.**

- [ ] Write every concept research 45 section 3 lists for futures, indices, metals, energy and crypto perps, with each class's meaning where a word means different things across classes. Order-flow entries declare their data level honestly, with broker-side estimates labelled as estimates.

**You see.**

- [ ] The dictionary speaks futures, indices, metals and perps, not only forex.

**Verify, unit.**

- [ ] The entry checker and the corpus gate give zero errors. The status counts go in the PR body. Every golden test passes. Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The status script over the family. Save `a13c-status.log`. Pass when it reports zero checker errors.
- [ ] Lane 3. Every multi-class word's meaning table. Save `a13c-meanings.log`. Pass when each lists a meaning or `not_assessed` for all nine classes.
- [ ] Lane 4. Every order-flow entry's data level. Save `a13c-levels.log`. Pass when each names its level, its fallback chain, and "estimate" where it comes from broker ticks.
- [ ] Lane 5. Start the host twice on a throwaway folder. Save `a13c-land.log`. Pass when the family's drafts land once.
- [ ] Lane 6. The market-profile block against its golden fixture. Save `a13c-golden.log`. Pass when it is within tolerance.
@menu

**Verify, perf.**

- [ ] Metric. Seconds to land the family on a throwaway folder.
- [ ] Probe. Lane 5.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens verification-gap. The blast-radius fact is that the corpus gate covers the new entries.

@merge

## Write the exit and halt families of the first content wave (A13d)

Phase 1, QML and the dictionary in depth. Part A slice A13d, `4-dictionary.md` section 5, Level 0 AD-24 (the risk socket). Rulings 13 and ledger R-04 (exit maths is the risk session's, the unit owns its exits). Real step none on his folder until he lands it. Done when time-varying targets, unrealised-profit caps, give-back from peak, account-level halts and probability exits are entries, the computable ones have code that passes A15's slot contracts later, and grid, martingale and averaging have honest trader faces.

**Depends on.** A13a, which brings the seed landing.

**Files.**

- [ ] Create the entries in `qml/catalogue-seed/wave-1/exits-and-halts/`.
- [ ] Create block sources under `qml/src/qml/blocks/stdlib/<entry>/1/` for the computable exits and halts, golden fixtures in `qml/tests/golden/exits-and-halts/`, and `qml/tests/test_wave1_exits.py`.

**Build.**

- [ ] Write every exit and halt research 35 found missing, with probability exits as `specified`. These are dictionary entries, not placeholders, and whether units may use grid or martingale families is the risk session's.

**You see.**

- [ ] The dictionary holds the exits traders use, ready for the risk session to choose from.

**Verify, unit.**

- [ ] The entry checker and the corpus gate give zero errors. The status counts go in the PR body. Each computable exit's golden test passes, and an exit fires only for a position it is given. Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The status script over the family. Save `a13d-status.log`. Pass when it reports zero checker errors.
- [ ] Lane 3. The family's golden tests. Save `a13d-golden.log`. Pass when every value is within tolerance.
- [ ] Lane 4. Each computable exit fed a fixture position. Save `a13d-amend.log`. Pass when no exit widens a stop.
- [ ] Lane 5. Start the host twice on a throwaway folder. Save `a13d-land.log`. Pass when the family's drafts land once.
- [ ] Lane 6. Read the grid, martingale and averaging entries' trader faces. Save `a13d-honest.log`. Pass when each states its known failure mode with a source.
@menu

**Verify, perf.**

- [ ] Metric. Seconds to land the family on a throwaway folder.
- [ ] Probe. Lane 5.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses verification-gap and edge-case. The blast-radius fact is that the corpus gate covers the new entries.

@merge

## Give the risk socket its contract tests and its rip-out list (A15)

Phase 1, QML and the dictionary in depth. Part A slice A15, Part A AD-116 and `CONTRACTS.md` section 4.3, Level 0 AD-15 and AD-24. Ruling 15 and ledger R-02 and U-04 (every risk and sizing point and the placeholder list written down). Real step none. Done when any risk-session block must pass the four slot contracts, and one query lists every published unit and binding that uses a placeholder.

**Depends on.** A6, A11.

**Files.**

- [ ] Edit `qml/src/qml/blocks/api.py` (the slot protocols).
- [ ] Create `qml/tests/test_socket_contracts.py`, `tools/qml/placeholders.py` and `tools/tests/test_placeholders.py`.

**Build.**

- [ ] Write the contract tests for the sizer, the exit block, the halt and the cross-unit hook, and the rip-out query over published units.

**You see.**

- [ ] The risk session gets a list, not a hunt. `build/RISK-SIZING-PLACEHOLDERS.md` names each item the query finds.

**Verify, unit.**

- [ ] The dummy's placeholder blocks pass the slot tests. A sizer returning a float, or a size above the minimum-lot rule's output, fails them. The query lists the dummy's five placeholder bindings. Run `uv run pytest qml/tests -q` and `uv run pytest tools/tests/test_placeholders.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The slot tests on the dummy's placeholder blocks. Save `a15-slots.log`. Pass when all pass.
- [ ] Lane 3. A sizer returning a float, and one returning a size above the minimum-lot rule's output. Save `a15-badsizer.log`. Pass when both fail with the contract named.
- [ ] Lane 4. The rip-out query on a throwaway folder with the dummy published. Save `a15-ripout.log`. Pass when it lists the dummy's five placeholder bindings.
- [ ] Lane 5. A fake risk-session sizer block that is not a placeholder. Save `a15-realblock.log`. Pass when it passes the slot tests and the query no longer lists that binding.
- [ ] Lane 6. Compare the query's output for the dummy with `build/RISK-SIZING-PLACEHOLDERS.md`. Save `a15-list.log`. Pass when every binding the query lists is in the file.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the rip-out query over 1,000 published fixture units.
- [ ] Probe. Lane 4 on a generated store.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses verification-gap and edge-case, on the money path. The blast-radius fact is that the dummy still checks with zero errors after the slot protocols change.

@merge
