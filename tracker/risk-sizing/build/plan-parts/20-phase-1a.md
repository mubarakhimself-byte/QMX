## Decide new version or new unit by one table, and give each unit one lifecycle (A9)

Phase 1, QML and the dictionary in depth. Part A slice A9, Part A AD-115, Level 0 AD-23. Standing order 7 and ledger CC-11 (only he promotes; the judge may label tested or parked, STATE "How standing order 7 reads"). Real step none. Done when `units.identity_table` has its default rows, `qml.identity.classify` and `diff` label every edit, and `qml.lifecycle` refuses every move toward paper or live whose principal is not `operator`.

**Depends on.** A2.

**Files.**

- [ ] Create `qml/src/qml/identity/`, `qml/src/qml/lifecycle/`, `qml/tests/test_identity.py` and `qml/tests/test_lifecycle.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py` to add the `[units]` defaults (`identity_table`, `lifecycle.auto_paper` off), merged on read the way `TELEMETRY_DEFAULTS` is (`:289`, `:886`).

**Build.**

- [ ] Write the identity table's default rows (Lab AD-16's rows plus the unit edit labels), `classify` and `diff`, which take the table as data because QML imports no host.
- [ ] Write the lifecycle machine with one state per market (draft, tested, parked, paper, live, stopped, retired), its transition table and `fold`. A move out of `stopped` names the stop event it clears.

**You see.**

- [ ] What counts as a new unit is one table he can read in Settings. Nothing reaches paper or live without his click.

**Verify, unit.**

- [ ] Table-driven tests. Each default label from a pair of fixture documents, the highest result wins, and every transition by every actor is allowed or refused as the table says. Tested to paper is refused for the judge unless `lifecycle.auto_paper` is on. A `his_click` move toward paper or live whose principal is `agent:<id>` or `run:<id>` is a rejected event, and the same move with principal `operator` applies (AG-13). Admitting a second version on a live market without parking the first is refused. Run `uv run pytest qml/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The fixture document pairs through `classify`. Save `a9-labels.log`. Pass when each pair gets its expected label and the highest result wins.
- [ ] Lane 3. Every transition by every actor. Save `a9-transitions.log`. Pass when the allowed and refused moves match the table row for row.
- [ ] Lane 4. A move toward paper with principal `agent:x`, then `run:y`, then `operator`. Save `a9-principal.log`. Pass when the first two are rejected events and the third applies.
- [ ] Lane 5. Tested to paper by the judge with `lifecycle.auto_paper` off, then on. Save `a9-autopaper.log`. Pass when it is refused off and allowed on.
- [ ] Lane 6. A stop that arrives after a resume click that names an earlier stop. Save `a9-stoporder.log`. Pass when the later stop stays in force whatever the two clocks say.
@menu

**Verify, perf.**

- [ ] Metric. Microseconds for one `fold` over 1,000 events.
- [ ] Probe. Lane 3's events folded 100 times.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, because this guards his click. The blast-radius fact is that his click is principal `operator` (`qmx_engine/service/context.py:59-70`, Level 0 item 15).

@merge

## Keep a unit's behaviour through restarts and upgrades (A10)

Phase 1, QML and the dictionary in depth. Part A slice A10, cases UT-03, UT-09, UT-11, UT-19 and QML-25. Ruling 52. Real step none. Done when a restart or an upgrade never silently changes what a unit does, and every check verdict a changed rule touches is marked superseded.

**Depends on.** A5, A6.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py` (`restore_unit` cold start with a reason, `seam_check`).
- [ ] Create `qml/src/qml/environment.py`, `qml/src/qml/unit/upgrade.py` and `qml/tests/test_runtime_care.py`.
- [ ] Create `tools/qml/recheck_units.py` and its test `tools/tests/test_recheck_units.py`, where `just ci` runs it (Appendix D).

**Build.**

- [ ] Write the cold start with a reason, `seam_check`, `environment_check` with a plain-words problem, the upgrader scaffold for every schema with its "every older shape loads" test, and the re-check script that marks superseded verdicts.

**You see.**

- [ ] A restart or an upgrade never silently changes what a unit does.

**Verify, unit.**

- [ ] A snapshot from another compiled fingerprint restores cold with `cold_start {reason}`. A 5-ATR jump at the seam flags. A Python 3.13 interpreter (mocked version info) gets the plain-words problem. The re-check script on a corpus with one changed rule marks exactly the affected verdicts. Run `uv run pytest qml/tests -q` and `uv run pytest tools/tests/test_recheck_units.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Restore a snapshot taken from another compiled fingerprint. Save `a10-cold.log`. Pass when the unit starts cold with `cold_start` and its reason.
- [ ] Lane 3. Join a warm-up tail and a live head with a 5-ATR jump. Save `a10-seam.log`. Pass when `seam_check` flags it, and a 0.5-ATR join does not.
- [ ] Lane 4. Run the re-check script on a corpus with one changed rule. Save `a10-recheck.log`. Pass when exactly the affected verdicts are marked `superseded`.
- [ ] Lane 5. `environment_check` under a mocked Python 3.13. Save `a10-env.log`. Pass when it answers one plain-words problem naming the version QML needs.
- [ ] Lane 6. Load every committed version 1 document through the upgrader, and a document claiming a future version. Save `a10-upgrade.log`. Pass when the first all load and the second refuses by name.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for one `restore_unit`.
- [ ] Probe. Lane 2 repeated 100 times.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap, on the unit runtime. The blast-radius fact is that QML's shipped tests stay green with the changed `protocol/unit.py`.

@merge

## Record every instrument, venue and account as versioned facts (C-02)

Phase 1, QML and the dictionary in depth. Part C slice C-02, Part C AD-312 and `RECORDS.md` section 2, Level 0 AD-26. Rulings 28 and 29 (every market now, futures designed). It comes here because QML's numbers and checker layer D convert through these records, and QMB's realism reads them in phase 2. Real step none. Done when the `instrument`, `venue` and `account` kinds load a record per class with exactly the keys Part A reads, the CCXT public refresh template lands perp records with no keys, and the check context reads real records.

**Depends on.** A7, for the check context it switches to real records.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-library/src/qmx_library/kinds/instrument.schema.json`, `qmx-agents/packages/qmx-library/src/qmx_library/kinds/venue.schema.json` and `qmx-agents/packages/qmx-library/src/qmx_library/kinds/account.schema.json`.
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/refresh-ccxt-records/` (Hyperliquid and Binance markets, public, no keys).
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/gather.py` to read `instrument` items when they exist, keeping A7's fixture fallback and its warning.
- [ ] Create `qmx-agents/packages/qmx-library/tests/test_market_kinds.py` and a test for the template's script step.

**Build.**

- [ ] Write the three kinds with the keys of `RECORDS.md` section 2, the one class enum with underscores (`fx`, `metal`, `index_cfd`, `commodity_cfd`, `stock_cfd`, `future`, `perp`, `spot_crypto`, `stock`), `data_levels` in `qmx.data-level/1`, and `market_id`. No record carries `roll_rule`.
- [ ] Write the conversion check and the refresh template.

**You see.**

- [ ] Instrument pages for forex, gold, indices and perps in his Library, with contract unit, funding interval and data levels.

**Verify, unit.**

- [ ] A record per class loads. The key-parity test asserts the instrument kind's keys include every key of Part A's section 2.3 list and its class enum equals `RECORDS.md` section 2's. No record carries `roll_rule`. Gold at two sizes gives equal R. A pips conversion without a pip definition is refused. Run `uv run pytest qmx-agents/packages/qmx-library/tests/test_market_kinds.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Load one fixture record for each of the nine classes. Save `c02-classes.log`. Pass when all nine load and validate.
- [ ] Lane 3. The key-parity check against Part A `CONTRACTS.md` section 2.3. Save `c02-parity.log`. Pass when every key Part A reads is present under the same name and the class enums are equal.
- [ ] Lane 4. The refresh template's script step on a recorded fixture market list, offline. Save `c02-ccxt.log`. Pass when Hyperliquid and Binance perp records land with contract unit, funding interval and data levels.
- [ ] Lane 5. Check the dummy with `gather` on a folder that holds real `instrument` items. Save `c02-gather.log`. Pass when the fixture-record warning is gone and layer D reads the real records.
- [ ] Lane 6. Gold at two sizes, and a pips conversion with no pip definition. Save `c02-convert.log`. Pass when the R values are equal and the conversion is refused by name.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for one refresh of the fixture market list.
- [ ] Probe. Lane 4.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case, because sizers read these facts. The blast-radius fact is that the Library's kind loader takes new kinds as schema files with no code change (Library AD-3), so the shipped Library suite passes unchanged.

@merge

## Give the dictionary its new form and its doors (A11)

Phase 1, QML and the dictionary in depth. Part A slice A11, Part A AD-113, Level 0 AD-19. Ruling 13 (the lead's answer, the form is code built by builders) and ledger D-02. Real step none. Done when the `qmx.entry/1` model, the entry checker, the status script, the roles table, the data-level vocabulary, the one-line index and the real `blocks_*` rows exist, and agents search the dictionary before writing code.

**Depends on.** A7, A8.

**Files.**

- [ ] Create `qml/src/qml/catalogue/{entry,roles,index,datalevel}.py` and `qml/tests/test_entry.py`.
- [ ] Create `tools/dictionary/status.py` and `tools/tests/test_dictionary_status.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` (the real `blocks_find`, `blocks_get`, `blocks_check` and `blocks_match`).
- [ ] Edit the ten `entry.json` files under `qml/src/qml/blocks/stdlib/` so A4's blocks carry their full entries.

**Build.**

- [ ] Write the entry model with its three faces (trader words, machine spec, implementation), the checker, the computed status, the role-neutral roles table, the data-level vocabulary and the index.

**You see.**

- [ ] The dictionary has its new pages, and agents search them before writing code.

**Verify, unit.**

- [ ] The ten QML blocks save as entries and compute `implemented`. An entry claiming `native` with no source refuses. An unknown role names the nearest. `blocks_match` maps "RSI crosses back above 30" to `rsi-cross-back@1` and flags an unknown sentence. The corpus gate covers entries. Run `uv run pytest qml/tests -q` and `cd qmx-agents; uv run pytest packages/qmx-tools/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Save the ten QML blocks as entries on a throwaway folder and run the status script. Save `a11-status.log`. Pass when all ten compute `implemented`.
- [ ] Lane 3. An entry that claims `native` with no source. Save `a11-native.log`. Pass when the save refuses with the reason.
- [ ] Lane 4. `blocks_match` on "RSI crosses back above 30" and on a sentence no entry covers. Save `a11-match.log`. Pass when the first maps to `rsi-cross-back@1` and the second comes back as an append request.
- [ ] Lane 5. An entry with an unknown role. Save `a11-role.log`. Pass when the error names the nearest role.
- [ ] Lane 6. Ask the copilot on `haiku` "find a block for a trend filter before you write one". Save `a11-find.log`. Pass when it calls `blocks_find` and names `ema@1` before writing any code.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for one `blocks_find` over the index.
- [ ] Probe. Lane 6's query from a script, 100 times.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses verification-gap and edge-case. The blast-radius fact is that every other `component` item (mini apps' provides schemas, migrated confluences) saves exactly as today, because the entry check applies only to items marked `entry.schema = "qmx.entry/1"`.

@merge

## Port all 239 dictionary entries into the new form (A12)

Phase 1, QML and the dictionary in depth. Part A slice A12, Part A AD-114 and `4-dictionary.md` section 4, lead's call LC-A1-14 (one click publishes a collection). Ruling 13 and ledger D-01 (port every entry, lose none). Real step none on his folder until he lands it. Done when the script ports 239 entries into 239 drafts with 0 lost, a rerun changes nothing, and one host route publishes the whole collection on his click.

**Depends on.** A11.

**Files.**

- [ ] Create `qml/catalogue-seed/stats-2026-08-26/` with the four Markdown files copied from their family folders under `C:/Users/Mubarak/Desktop/Stats/dictionary/` (context, exits, locations and triggers, four files plus a README, CHECKED; 239 entries by the grounding count) and their `SOURCES.json` of fingerprints. The secret scan runs on this commit, because the folder is Hermes-era.
- [ ] Create `tools/dictionary/port_stats.py`, `tools/dictionary/roles_map.json` and `tools/tests/test_dictionary_port.py`. The test sits in the tools test folder, the only one `just ci` runs for scripts (Appendix D).
- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/publish_collection.py`, the route `POST /api/library/collections/<id>/publish` for his principal `operator` only, publishing each item in turn through the per-item publish (`qmx-library/src/qmx_library/adapter.py:277`), idempotent. Mount it in `qmx-agents/packages/qmx-host/src/qmx_host/host.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` so each start lands the port's drafts once per store, keyed by source fingerprint, as A7 lands the dummy.

**Build.**

- [ ] Freeze the source, parse every record with `resolve_dictionary_entry`, map the twelve fields to the three faces, map roles, rewrite FX-only market lines as per-class transfer status, scope the nine slug collisions by family, and land every entry as a draft in one collection.

**You see.**

- [ ] His Library holds the ported dictionary as one collection, 239 pages, all passing, waiting for one publish click. The card that asks for it is the UI session's.

**Verify, unit.**

- [ ] 239 parsed, 239 drafts, 0 lost, counted by the script. Every draft passes the entry checker at `named` or `specified`. The unmapped-role report lists any string not in the table. No entry claims `native` without a source. A rerun changes nothing. The publish route refuses any principal but `operator` and publishes each item once. Run `uv run python tools/dictionary/port_stats.py --dry-run` and `uv run pytest tools/tests/test_dictionary_port.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The port's dry run. Save `a12-dryrun.log`. Pass when it prints 239 parsed, 239 drafts, 0 lost.
- [ ] Lane 3. A real run on a throwaway folder, then the status script. Save `a12-land.log`. Pass when 239 drafts sit in one collection and each passes at `named` or `specified`.
- [ ] Lane 4. Start the host on that folder again. Save `a12-rerun.log`. Pass when nothing new lands.
- [ ] Lane 5. The publish route as `agent:x`, then as `operator`, then again as `operator`. Save `a12-publish.log`. Pass when the first is refused, the second publishes 239 items, and the third changes nothing.
- [ ] Lane 6. `tools/secret_scan.py` on the seed folder and the unmapped-role report. Save `a12-scan.log`. Pass when the scan is clean and the report's count is recorded in the PR body.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the full port into a throwaway folder, and for the collection publish.
- [ ] Probe. Lanes 3 and 5.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is that a publish through the new route runs the same per-item publish and checker as a single publish.

@merge
