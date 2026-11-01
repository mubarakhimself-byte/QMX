## Ship calendars for every market and check opening per market (C-03)

Phase 4, the MIS on This PC. Part C slice C-03, Part C `DEVOPS-CLOCKS.md`, Level 0 AD-43. Ruling 29 (every market now). Real step none. Done when CME, index-break and 24/7 calendars with funding clocks exist as data packages beside the forex one, the engine's `market_open` precheck checks a market's own calendar, and the zone-mismatch weeks are tested.

**Depends on.** C-02.

**Files.**

- [ ] Create `extensions/qmf-calendar-cme/`, `extensions/qmf-calendar-indices/` and `extensions/qmf-calendar-crypto247/`.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/triggers/preflight.py` (the check takes a `market_id`).
- [ ] Create `qmx-agents/packages/qmx-engine/tests/test_preflight_calendar.py`.

**Build.**

- [ ] Write the three calendar packages as versioned data with a maximum age, and the per-market precheck. Storage stays in UTC and market-tied jobs run in the market's zone.

**You see.**

- [ ] A crypto workflow no longer waits for Monday.

**Verify, unit.**

- [ ] Crypto is open on Saturday. CME has its daily break. Every rule holds across 8 to 29 March and 25 October to 1 November 2026. Run `uv run pytest extensions qmx-agents/packages/qmx-engine/tests/test_preflight_calendar.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The precheck for BTC perp on a Saturday. Save `c03-crypto.log`. Pass when it reads open.
- [ ] Lane 3. The precheck for a CME future across its daily break. Save `c03-cme.log`. Pass when it reads shut for the break and open around it.
- [ ] Lane 4. Every calendar rule on each day of 8 to 29 March and 25 October to 1 November 2026. Save `c03-mismatch.log`. Pass when each open and close lands at the market's own zone time.
- [ ] Lane 5. A crypto workflow's trigger fired on a Saturday on a throwaway folder. Save `c03-trigger.log`. Pass when it runs and does not wait for Monday.
- [ ] Lane 6. The shipped forex preflight tests. Save `c03-forex.log`. Pass when they pass unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Microseconds for one precheck.
- [ ] Probe. Lane 4's checks in a loop.
- [ ] Baseline. The forex precheck at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case, on clocks and zones. The blast-radius fact is that the forex calendar's shipped tests pass unchanged.

@merge

## Give apps that declare it a read-only market root (C-05b)

Phase 4, the MIS on This PC. Part C slice C-05b, mini-app core change 4 of Level 0 AD-33. Rulings 46 and 53. Real step none. Done when the supervisor hands `QMX_MARKET_ROOT` to an app whose manifest declares `data_reads = ["market"]`, writes there stay refused, and every other app gets the environment it gets today.

**Depends on.** Nothing. Appendix C keeps it from running beside other supervisor edits.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (the app environment, `:598-632`).
- [ ] Create `qmx-agents/packages/qmx-apps/tests/test_data_reads.py`.

**Build.**

- [ ] Pass the read-only root to declaring apps only. The bootstrap's audit hook keeps refusing writes there.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] An app declaring `data_reads = ["market"]` sees the root and reads a partition. An app without it gets today's environment. A write under the root is refused by the bootstrap's audit hook. Run `uv run pytest qmx-agents/packages/qmx-apps/tests/test_data_reads.py -q` and `uv run pytest qmx-agents/packages/qmx-apps/tests -q` unchanged.

**Verify, live.**

@lane1
- [ ] Lane 2. A fixture app declaring the market read. Save `c05b-read.log`. Pass when it reads one partition through `QMX_MARKET_ROOT`.
- [ ] Lane 3. A fixture app without it. Save `c05b-none.log`. Pass when its environment equals the parent's.
- [ ] Lane 4. The declaring app writes a file under the root. Save `c05b-write.log`. Pass when the write is refused.
- [ ] Lane 5. The declaring app opens `..` from the root and writes there. Save `c05b-escape.log`. Pass when the write is refused.
- [ ] Lane 6. The shipped apps suite at the parent and the head. Save `c05b-apps.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds to start a declaring app.
- [ ] Probe. Lane 2 against lane 3, interleaved.
- [ ] Baseline. Lane 3's start.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that `data_reads` was only logged before (`qmx_apps/supervisor.py:700`), so an app that never declared it sees no change.

@merge

## Write the host's facts into every app volume (C-05c)

Phase 4, the MIS on This PC. Part C slice C-05c, mini-app core change 5 of Level 0 AD-33, Part C AD-307. Rulings 46 and 53. Real step none. Done when the host writes `road/host/facts.json`, the holdout seal and the trading profile included, into each supervised app's volume before the app starts and on every change.

**Depends on.** Nothing. Appendix C keeps it from running beside other supervisor edits.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (a facts hook the host passes in, called before start) and `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (composes the facts, the Settings `[data]` holdout among them).
- [ ] Create `qmx-agents/packages/qmx-apps/tests/test_host_facts.py`.

**Build.**

- [ ] Write the facts file with the fields of Part C `CONTRACTS.md` section 5. Only the host writes under `road/`.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] The file exists before the app's first heartbeat. A Settings change to `[data] holdout` rewrites it. An app's own write under `road/` is still refused. Run `uv run pytest qmx-agents/packages/qmx-apps/tests/test_host_facts.py -q` and the shipped road tests with `uv run pytest qmx-agents/packages/qmx-apps/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Start a fixture app on a throwaway folder. Save `c05c-before.log`. Pass when the facts file exists before its first heartbeat.
- [ ] Lane 3. Change `[data] holdout` in Settings while the app runs. Save `c05c-holdout.log`. Pass when the file is rewritten with the new seal.
- [ ] Lane 4. The app writes under `road/`. Save `c05c-road.log`. Pass when the write is refused.
- [ ] Lane 5. Read the facts on This PC. Save `c05c-profile.log`. Pass when the trading profile reads off.
- [ ] Lane 6. The shipped road tests at the parent and the head. Save `c05c-roadtests.log`. Pass when they pass unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds from a Settings change to the rewritten file.
- [ ] Probe. Lane 3.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that the bootstrap still refuses app writes under `road/` (`qmx_apps/bootstrap.py:99-100`).

@merge

## Move the reading blocks into one shared package and record readings (C-08)

Phase 4, the MIS on This PC. Part C slice C-08, Part C `MIS.md`, Level 0 AD-40, lead's call LC-A0-09. Rulings 48, 50 and 55 (indicators first, models later, an MIS that needs no training). Real step none. Done when `qmn/src/qmn/mis` lives in `packages/qmf-readings` with its logic unchanged, every importer is repointed, the reading runner writes records through Part B's writer with `source` and `machine`, and the golden replay agrees across unit, QMB and runner.

**Depends on.** A11, B8.

**Files.**

- [ ] Create `packages/qmf-readings/` by moving `qmn/src/qmn/mis/` with its tests, and add the reading runner and the reading record.
- [ ] Repoint every importer of `qmn.mis` to `qmf.readings`. At `c93407ca` a grep finds them in `qmn/src/qmn/host/`, `qmn/src/qmn/replay/` and `qmn/src/qmn/seats/host.py` (CHECKED), beside `regime_register.py:60-61`. Then delete `qmn/src/qmn/mis/` in this PR.

**Build.**

- [ ] Move the labelers unchanged in logic. Rename the volatility buckets from "regime" to "volatility state" in names and words (LC-A0-20, his word to veto). "Regime" now means trend against range.
- [ ] Write the runner and the record with every field of Part C `CONTRACTS.md` section 7.

**You see.**

- [ ] Nothing yet.

**Verify, unit.**

- [ ] The moved labelers' tests pass. The runner over a recorded day writes records with every field of section 7, `source` and `machine` included. The golden replay compares unit, QMB and runner values per reading id and version. Run `uv run pytest packages/qmf-readings -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The moved labelers' tests in their new home. Save `c08-moved.log`. Pass when every test that passed in `qmn` passes in `qmf-readings`.
- [ ] Lane 3. The runner over a recorded day. Save `c08-records.log`. Pass when every record carries every field of section 7.
- [ ] Lane 4. The golden replay through the unit, QMB and the runner. Save `c08-golden.log`. Pass when the three agree per reading id and version.
- [ ] Lane 5. Grep the repo for `qmn.mis`. Save `c08-importers.log`. Pass when none is left.
- [ ] Lane 6. `uv run pytest qmn/tests -q -k "not slow"` at the parent and the head. Save `c08-qmn.log`. Pass when the head fails nothing the parent passes.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the runner over one recorded day.
- [ ] Probe. Lane 3.
- [ ] Baseline. The same labelers called from `qmn` at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is Level 0 item 5's caller scan, every caller of the moved code is repointed in this PR, with no compatibility layer left.

@merge

## Run the MIS as an app on This PC (C-09)

Phase 4, the MIS on This PC. Part C slice C-09, Part C `MIS.md`, AD-307 and AD-313, Level 0 AD-40. Rulings 11, 48 and 55 (defaults for every class now, room for his models). Real step none. Done when the `mis` app configures, answers `status`, publishes the bar, session, day and cross-market readings of the default packs from Library history, writes the board, skips months the host facts mark sealed, and stopping it changes no unit.

**Depends on.** C-05a, C-05b, C-05c, C-08, C-03, B15, A13b.

**Files.**

- [ ] Create `qmx-agents/apps/mis/` with `app.toml` (`data_reads = ["market"]`, `[breaker] restart = "backoff"`), `server.py`, `pyproject.toml`, `uv.lock` and `tests/`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` (one click enables `mis`) and `tools/test_all.py` (the app's tests run in `just ci`).

**Build.**

- [ ] Write the app and its default packs. The packs bind C-08's moved labelers and A13b's statistic blocks by entry id, so no reading has a second copy. New readings and models run in shadow and go live only with his yes.

**You see.**

- [ ] The copilot can show the MIS readings for the markets he has data for, each with its freshness word. The MIS tab is the UI session's.

**Verify, unit.**

- [ ] Configured on two fixture markets, it publishes records for each reading the markets' data levels allow and none for the rest. With the host facts' `holdout` on from a month, no record lands for that month or later. Stopping it changes no unit. Run `uv run pytest qmx-agents/apps/mis/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Configure the app on two fixture markets with different data levels. Save `c09-publish.log`. Pass when each market gets exactly the readings its levels allow.
- [ ] Lane 3. Seal the last fixture month in Settings. Save `c09-sealed.log`. Pass when no record lands for that month or later.
- [ ] Lane 4. The dummy's QMB run with the MIS on and then stopped. Save `c09-standalone.log`. Pass when the two trade lists are identical.
- [ ] Lane 5. The board artifact after one round. Save `c09-board.log`. Pass when it lands with each market's readings and their freshness.
- [ ] Lane 6. Crash the app. Save `c09-restart.log`. Pass when it starts again by back-off and keeps publishing.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for one round over the fixture markets.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is that a unit stands alone, so stopping the MIS changes no trade (Level 0 AD-2).

@merge

## Let agents read instrument facts and reading history (C-24)

Phase 4, the MIS on This PC. Part C slice C-24, Part C `CONTRACTS.md` section 12, Level 0 AD-31, R1-C-03. Rulings 8 and 44 (agents and the copilot read, in the slow lane). Real step none. Done when `instrument_get` and `readings_query` sit in the new core toolsets `instrument` and `readings` on the default copilot surface, and agents read readings only through `readings_query`.

**Depends on.** C-02, C-08, A8, B8.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py` (two `domain_fn` rows, and `instrument` and `readings` join `CORE_TOOLSETS`) and `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py` (the two functions).
- [ ] Create `qmx-agents/packages/qmx-tools/tests/test_read_rows.py` and a surface test in `qmx-agents/packages/qma-harness/tests/`.

**Build.**

- [ ] Write the two rows. `readings_query` needs a time window, includes the open month, pages by cursor and says where the data stops.

**You see.**

- [ ] The copilot can tell him what the MIS read for a market last week, and the facts of any instrument.

**Verify, unit.**

- [ ] `instrument_get` returns the version in force at an instant. `readings_query` over fixture `journal-readings` partitions returns rows in the window, pages by cursor, and a window past the data answers `data_ends_at`. A copilot chat's surface lists both rows. `qmx-tools/tests/test_tools.py:374-376` is unchanged, because both rows sit in new toolsets. Run `uv run pytest qmx-agents/packages/qmx-tools/tests/test_read_rows.py qmx-agents/packages/qma-harness/tests -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. `instrument_get` for EURUSD at two instants either side of a record change. Save `c24-instrument.log`. Pass when each answers the version in force then.
- [ ] Lane 3. `readings_query` over a week of fixture readings, paged. Save `c24-readings.log`. Pass when the pages join into exactly the window's rows.
- [ ] Lane 4. A window past the data. Save `c24-ends.log`. Pass when it answers `data_ends_at` with the last instant.
- [ ] Lane 5. Ask the copilot on `haiku` "what did the volatility state read on EURUSD last week?" Save `c24-copilot.log`. Pass when it calls `readings_query` with a window and quotes values with their freshness.
- [ ] Lane 6. A query without a window. Save `c24-nowindow.log`. Pass when it is refused.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for one page of a week's readings.
- [ ] Probe. Lane 3.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that the harness serves a new core toolset only because A8 derives the domain groups from the catalog (`qma-harness/src/qma/harness/tools.py:668`).

@merge
