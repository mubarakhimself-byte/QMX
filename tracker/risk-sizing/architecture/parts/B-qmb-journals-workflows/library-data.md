# The Library's data, as units, QMB and journals see it

Part B, sub-area 4. Decisions: spine AD-212 (additions only), AD-209 (journal partitions), AD-202 (materialise on QMB's behalf). Shapes: `CONTRACTS.md` §3 and §5. Slices: `BUILD-SLICES.md` B3, B9, B16.

**In plain words.** The Library is QMX's centre and stays as built. This part adds a few new kinds of record (tries, study specs, verdicts and their cards) and a few optional fields to kinds that exist. Each data card says which clock its source used, where its cadence or timestamp unit changed, and how a futures series was stitched, so a backtest never mixes two meanings without saying so.

His words: "everything that a workflow produces is meant to be stored in the library" (T2:325); "Just know the data will be there." (T3:903); "We have a library, we should use it." (T3:903). STATE midday ruling 51: the Library was hard to build, so its core is not to be damaged.

Ledger rows that bind: L-01, L-02, L-03, L-04 (seed, consistent), L-06, L-07 (seed; terms settled), CC-03.

## 1. Verdict: core, changed only by addition

Kept as built (Level 0 AD-29): one writer, archive never delete, governed drafts, refs and edges, the market-data door, dataset cards, the outbox. `bot` and `strategy` stay live kinds; nothing in this part writes them.

## 2. What this part adds

| Addition | Class | Fields (main) | Why |
| --- | --- | --- | --- |
| `try` (new kind) | record | kind, run id, family, unit, study, tester, principal, place, state, links | every try counted, one item each (AD-207) |
| `study-spec` (new) | record, versioned | claim card, markets, windows, record needed, preset, shrinkage estimator, holdout, cost and fill rules, `allow_gaps`, motion, origin | rules before results; the UI-editable run config |
| `verdict` (new) | record | per market and overall outcome, effective tries, preset, judge, checker and tester versions | scripts decide |
| `baseline-card` (new) | record | frozen record in R, cone, cost and fill assumptions, trade rate, readings range | decay check |
| `proposal-card` (new) | record | what waits for his click, evidence, try count, placeholders | his click decides |
| `death-certificate` (new) | record | typed cause, classifier version, explanation | the funnel's fail branch |
| `forecast` (new) | record | market, call, horizon, confidence, written at, scored at, score | WF-11 |
| `backtest-result` v2 | record | run fields, status, measures, labels; blob slots `trades`, `equity`, `journal/*`, `daily_r`, `slices`, `receipts`; page tabs "Journal", "Slices", "Who ran it" | AD-204 |
| `note` v2 | record | `about` (links), `note_kind`, `receipts`, `window`, `sources_marked`, `expires`, `author` | agents' only write (AD-211) |
| `paper-run` v2 | record | unit, market, account, node, started and ended, status, record in R, sequential score, journal links | a unit's paper lane (Level 0 AD-39) |
| `trade` v2 | record | unit, market id, machine, trace id, MAE and MFE in R, costs split, equity before, session, streak, placeholders, `r_missing`, `gap_through_stop` | the round-trip record for paper, demo, live (LC-A0-11) |
| `dataset` v2 | record | `source_clock`, `seams` (timestamp unit, cadence), `stitching` and `rolls` for futures series, `calendar` (instrument record pin) | LD-03, LD-04, LD-16, QB-05 |

Every amended kind raises its `schema_version` by one; every new field is optional, so items already landed stay valid. A replica that has not been updated refuses only objects at the newer version, by name, and the outbox keeps them until it catches up (`qmx_library/store.py:2436-2441`, `outbox.py:208-213`, CHECKED).

**Page tabs are data.** Library AD-33 gives every kind a card and a page in its schema file (CHECKED: `backtest-result.schema.json` declares tabs Summary, Equity, Trades, Robustness, Data used, Comparable runs, History). The tabs this part adds are lines in kind files, which the UI renders; no UI code is written (ruling 45).

## 3. Data-card rules for the cases this part owns

| Case | Rule | Where it runs | Check |
| --- | --- | --- | --- |
| LD-01 an empty Dukascopy hour after the bot wall | an empty hour inside the instrument's open calendar is a fetch failure until a retry and a second source agree (the broker's own trendbars through the view-only read, E2, or another vendor for crypto) | the shared data-quality check, called by downloaders and the daily data review | a fixture month with one empty open hour stays unfrozen and is named in the review |
| LD-03 a source changes its timestamp unit | a per-file stamp check at import: the magnitude of the first and last stamps says milliseconds, microseconds or nanoseconds; a change mid-series is a seam written on the card | `qmf-data` importers and the download templates' scripts | a Binance file in microseconds after 1 Jan 2025 lands with the seam on the card |
| LD-04 a cadence change | the card's `seams` lists cadence changes; any result whose window crosses one names it in its bundle | the importer; QMB's open step reads the card | a run across Hyperliquid's 2026-06-17 book change lists the seam |
| LD-05 an upstream file replaced | a new checksum is a new card version; results pin the version they read (built: `dataset.replaced`, `corrections`) | as built | as built |
| LD-06 the Library is empty | a run with no data refuses at open, naming each missing month and the download template that fetches it | the lander's open step | a run on an empty home refuses with the template name |
| LD-08 reads not tied to a study | QMB reads always carry the run id and study (the core materialises them); agent market reads carry the chat principal and an optional study, and the door logs every read | the lander; the market rows | a run's materialise call appears in the door's log with its run id |
| LD-09 recording fills the disk | ticks stop first, journals last; the journal hot path has its own floor | the writer library's floor; the recorder (Part C) | a near-full disk fixture: tick commits refused, journal appends still accepted |
| LD-11 a backup makes a live writer wait | the journal hot path appends and never renames onto a file a backup may read; backups copy closed partitions and the open month's last complete file; the store's rename retry stays as the last guard (`series.py:166-179`) | the writer library; backup rounds (built) | a held read handle on a store file while a journal append and a month roll run: the append returns within a setting (default 50 ms) |
| LD-12 one market from two sources differs | a cross-source offset check keyed by the market id lands `offset` rows in the market journal | the daily data review's script | Dukascopy gold against a broker's gold: a measured median gap appears |
| LD-14 two agents edit one item | branch and merge, as built (PR 195) | as built | as built |
| LD-15 the SQLite reset bug | one writer per database file, as built; journals never use SQLite | as built | as built |
| LD-16 history stamped in UTC, the broker in GMT+2 or +3 | every card states its `source_clock`; conversion to UTC happens once at import | importers | a broker export in GMT+2 lands in UTC with the card saying so |
| LD-17 a save replayed twice | the outbox is idempotent by intended object id (built); a run's open and close are idempotent by run id | as built; the lander | a replayed close lands nothing new |
| QB-05 continuous futures | the card records the stitching method and roll dates; QMB replays contract by contract | the futures importer (when a route exists) and QMB | a two-contract fixture card lists its roll |

LD-07 (the Library away while a node trades) is handled by Part C's deployment snapshots (Level 0 AD-38); LD-02 and LD-13 by Part C's calendars and instrument records, which this part's checks read. LD-10 (licences) stays on the card and is never raised with him.

## 4. Materialising a run's data (AD-202)

The core, not QMB, reads the market-data door: the lander's open step calls `materialise` with the run's partition fingerprints and the study's holdout choice, into the run folder of the tester's volume. A long read is a handle written by a child process, as built (`qmx_host/market_data.py:11-14`, CHECKED). A tester therefore cannot read a sealed month, cannot read outside its study, and cannot skip the read log.

## 5. What must not break

`qmx-library/tests` (every kind test, `test_store.py`, `test_store_versions.py`, `test_outbox.py`); the registry migration into `bot` and `strategy` (`qmx_library/migrate/from_registry.py:32-33`); the 28 shipped test lines that compare the kind check's first problem's message (Level 0 `blast-radius.md` item 6; Part A changes the check to return every problem with the first as its head).

## 6. Growth seams

A kind is a schema file; a checker is named in it (Level 0 AD-29). A new data-card rule is a field plus the importer that fills it. A new source is a downloader template plus a card.
