# R1 full architecture review

Reviewer R1, 2026-11-01, per `architecture/briefs/R1-full-review.md`. Reviewed: Level 0 (spine, R0 fixes, handover, lead's calls), `01-connections.md`, and the three part folders A, B and C. Against: the edge-case catalogue and its foundation properties, the glossary, the grounding, and the code at `D:\QMX-worktrees\engine-base-read\` (`origin/engine/base` `c93407ca`).

Labels: CHECKED means the reviewer opened the path at the line, or ran the script named. INFERRED means reasoned from the documents. Scripts live in this session's scratchpad folder `...\scratchpad\r1\` (`cases.py`, `handover.py`, `br_open_month.py`).

Lenses run in sequence by the reviewer (no sub-agents): edge-case, adversarial, verification-gap (`bmad-review`), then `blast-radius` on the riskiest seams. Each finding names its lens: [E] edge case, [A] adversarial, [V] verification gap, [B] blast radius.

## Summary

1. **The design is sound at its core and mostly consistent.** Level 0 fixed all 19 R0 findings or handed them on, and every handed item is settled by name in its part (CHECKED, `handover.py`: A 21 of 21, B 26 of 26, C 36 of 36). Every code claim spot-checked is true, give or take two line numbers (Cross-part checks, check 4).
2. **Three things block a clean build order.** QMB's first end-to-end slice needs a G record that only a later slice can make (R1-B-01). Nobody builds the path from his promotion click to a deployment on the node (R1-C-01). B and C disagree on how a node's data reaches its store, and the node's recorded feed has no harvester at all (R1-B-02).
3. **One seam is unmatched across all three parts.** Part A shows a unit must be hosted through its own door (`construct_unit`), but Level 0 still says `construct_bot` accepts it unchanged, and neither B nor C names A's door. QMB and the node would each write their own wrapper, which breaks "same code in research and live" (R1-L0-02).
4. **21 catalogue cases have no Level 1 owner**, because Level 0 gave them to parts P7, P8 and P10, which no Level 1 agent covered (R1-L0-01). Most are handled in substance by A; the table lines are missing.
5. **The costliest money case has no check in any slice.** The "network cut after send shows one position" drill (TN-01) is written in `NODE.md` but no slice runs it (R1-C-02).
6. **Counts.** 40 findings: 7 High, 22 Medium, 11 Low; 11 from the adversarial lens. Every clash the parts raised is settled below, all accepted with three refinements.

---

## Findings for Level 0

Ranked most severe first. The fix round for Level 0 edits `level-0/ARCHITECTURE-SPINE.md` and `01-connections.md` (one writer).

### R1-L0-01 (High) [E] 21 catalogue cases have no Level 1 owner and no handling line

- **Where.** Level 0 "The parts": P7 (contracts), P8 (copilot and agents), P10 (mini-app core) own cases, but no Level 1 part covers those parts.
- **What is wrong.** R0-11's rule says every owned case gets a handling line in a Level 1 table, checked by script. 21 cases have none: AG-01, AG-02, AG-03, AG-04, AG-08, AG-09, AG-10, AG-13, AG-16, MA-05, CA-01 to CA-09, CA-11, CA-12. AG-13 (an agent's promotion treated as approved) and CA-03 (the four sizing layers moved in one wave, with an end-to-end sized intent test) are money cases.
- **Evidence.** CHECKED by `r1/cases.py`: the catalogue has 267 cases plus 18 for the risk session; the three part tables claim 246 of the 267 (plus RS-13 and RS-18); the 21 above appear in no part table (C mentions MA-05, CA-04, CA-06 and CA-11 only in prose). Part B took some P8 and P10 cases on its own (LC-B-19); the rest fell through.
- **Proposed fix.** Level 0 gives each case to a part in its part list, and each part adds the table line. Suggested split: A takes AG-01, AG-02, AG-03, AG-04, AG-08, AG-09, AG-16, CA-02, CA-07, CA-08, CA-09 (all already handled by AD-110, AD-111, AD-115 to AD-117, A15); A also takes AG-13 (the lifecycle transition table refuses a move toward live whose actor is not his principal, test in A9); B takes AG-10 and CA-05 and CA-12 (Library merge as built, the one error shape, reserved names); C takes CA-01 (route `schema_version` and the OpenAPI title from the host build, in slice C-06), CA-04, CA-06, CA-11, MA-05; CA-03 is shared, see R1-C-08.

### R1-L0-02 (High) [A] Units are hosted through Part A's unit door, but Level 0, B and C still assume the bot door

- **Where.** Level 0 AD-16 ("accepted by `construct_bot` unchanged"), AD-5 ("the node's loop keeps driving QMB's `run_slice` unforked"), connections C12 ("the structural `BotFactory` seam"); B AD-205 and slice B6 ("run through `run_slice` with the unit's socket"); C AD-301 and its node diagram ("compiled units over `run_slice`").
- **What is wrong.** Part A proved that `HostedBot.on_instant` sends every intent through `accept_intents`, which refuses a CT-23 format 3 intent (A `blast-radius.md` BR-A4, run). So a unit must run through A's `construct_unit` and `HostedUnit`, whose step returns intents, decision rows, calibration rows and state events. Neither B nor C mentions `construct_unit`, `HostedUnit` or `UnitStep` (CHECKED by grep over both folders). Each host would write its own run-slice handler around a unit: two adapters for one behaviour, which is exactly the AD-5 drift (motion, exits for own positions, warm-up suppression, `not_before`).
- **Evidence.** `run_slice` is host-agnostic: it drives any handler with the five hooks (`qmb/src/qmb/runloop/loop.py:780-801`; the node's driver checks only the hooks, `qmn/src/qmn/loop/driver.py:409-417`), CHECKED. Today's handlers are the Book path's (`qmb/src/qmb/host/book_handler.py`) and the node's seat host (`qmn/src/qmn/seats/host.py`), which the shell cut deletes. The node already imports QMB (`qmn/src/qmn/loop/driver.py:16`), CHECKED.
- **Proposed fix.** Level 0 amends AD-16, AD-5 and C12 to A's unit door (A's conflict row 4). One unit handler, `qmb/src/qmb/host/unit_handler.py`, wraps `HostedUnit` for `run_slice`; QMB's unit runner (slice B6) and the node runtime (slice C-12a) both import it. B owns it in B6; C consumes it.

### R1-L0-03 (Medium) [A] His principal is named `user` where the code says `operator`

- **Where.** Level 0 AD-46 and LC-X0-03 ("`manage` operations answer only to the principal `user`"); B AD-202 ("`user` for his click ... never rewritten to `operator`").
- **What is wrong.** In code the caller kind is `user` and its principal string is `operator`. Part C uses `operator` (C AD-303, CONTRACTS §1). A builder reading Level 0 would compare against `user` and refuse his own clicks.
- **Evidence.** `qmx_engine/service/context.py:59-70`: `Caller("user").principal` returns `"operator"`; the seal move checks `caller.principal != "operator"` (`qmx_host/market_data.py:1204`), CHECKED.
- **Proposed fix.** Level 0 and B read "his click: caller kind `user`, principal `operator`; an agent is `agent:<id>`, a workflow `run:<id>`".

### R1-L0-04 (Medium) [E] AD-45 says the code has two host roles; it has three

- **Where.** Level 0 AD-45, P0.
- **What is wrong and evidence.** `type Role = Literal["pc", "node", "server"]` (`qmx_host/host.py:141`), CHECKED; Part C's CF-2.
- **Proposed fix.** See clash settlement CF-2.

### R1-L0-05 (Medium) [A] The mini-app core fix list in AD-33 is one fix; the parts need six

- See clash settlement CF-4. Level 0 AD-33 becomes the one list of every core change, each with its reason and its slice.

### R1-L0-06 (Low) [V] Level 0 has no plain-words summary for him

- **Where.** Level 0 spine. Parts A, B and C each open with one ("In plain words"); Level 0 has only P13's paragraph.
- **Proposed fix.** Five plain sentences at the top of Level 0 (the core, the three apps, units stand alone, only he promotes, everything comes home to his PC). P2's final brief reuses them.

### R1-L0-07 (Low) [E] "Kernel" appears in the layer table, against the glossary

- **Where.** Level 0 Design Paradigm table rows "Kernel: authoring", "Kernel: judging and records", "Kernel: market edge".
- **What is wrong.** The glossary allows "kernel" only in the paradigm's name ("_Avoid_: kernel (used only in the architecture's paradigm name)").
- **Proposed fix.** "Core: authoring", and so on.

### R1-L0-08 (Low) [V] The master still lists the cross-machine run pass as a known gap

- **Where.** `01-connections.md` X6 and §6 ("a run pass minted on This PC fails at a server's door"); B WF-06 ("part B's templates run on This PC until it passes").
- **What is wrong.** Part C reran it: a pass minted on This PC parses at a server that holds the same pairing key, and is refused by an unpaired one (C `BLAST-RADIUS.md` C9, step 4). Only a run between two real hosts is left (slice C-17).
- **Proposed fix.** The master's X6 and §6 read "verified by parse (C9); a real two-host run in slice C-17"; B's WF-06 line follows.

---

## Findings for part A (QML, dictionary, unit)

The fix round for A edits files in `parts/A-qml-dictionary-unit/`.

### R1-A-01 (Medium) [V] The dummy unit's slowly moving number may never move in the first real runs

- **Where.** A AD-118 and `2-unit-template-numbers-lifecycle.md` §6; slice A5 (hand-fed `own_journal` of 80 trades); B9 (one-month runs); CONTRACTS §9 `min_trades` 60, `slow_cadence` every 20 closed trades.
- **What is wrong.** The derived number `rsi_low` moves every bar, so "one real number moving by its rule" holds. The calibrated number `min_trend_strength`, which is the self-calibrating idea he asked for, needs 60 closed trades before its first move. A one-month M15 run of a trend pullback on one market will close far fewer (INFERRED). The only proof of slow motion is then a hand-fed journal inside QML.
- **Proposed fix.** The dummy declares its own `min_count` on that number (a per-number setting, for example 20), and B9's check runs a window long enough on both markets to assert at least one calibration row from real trades.

### R1-A-02 (Low) [V] QML-04's test reports time per update but does not assert it

- **Where.** Slice A4 Verify ("time per update in the last tenth is reported beside the first tenth"); handover line QML-04 ("shows no growth in time per update").
- **Proposed fix.** Assert the last tenth's median time per update within a named tolerance of the first tenth's (a setting, for example 1.5 times).

### R1-A-03 (Low) [V] Slice A2 depends on A1 without reason

- **Where.** A2 "Depends on: A1 (the intent types the model names)". The unit document names no intent type (CONTRACTS §1).
- **Proposed fix.** A2 depends on nothing; A1 and A2 can land in either order.

### R1-A-04 (Low) [V] One cited line is off

- **Where.** A Conflicts row 6 and AD-117 cite `qma-harness/src/qma/harness/tools.py:668`; `DOMAIN_GROUPS` is at line 664 (CHECKED).
- **Proposed fix.** Correct the line.

### R1-A-05 (Low) [V] No slice puts the dummy unit into his Library

- **Where.** A AD-118 ("The dummy installs out of the box"); A2 ships it as a file in QML's package; B6's live lane asks the copilot to "backtest the dummy unit", which needs a `unit` item in the Library.
- **Proposed fix.** A7 lands the dummy unit on first start through the governed landing (idempotent by content), with a test that a fresh QMX folder lists it; its blocks' entries follow in A11, and the broken twins stay test fixtures.

---

## Findings for part B (QMB, journals, workflows)

The fix round for B edits files in `parts/B-qmb-journals-workflows/`.

### R1-B-01 (High) [V] The first end-to-end QMB slice needs a slice that comes later

- **Where.** B AD-202 step 1 ("checks the unit's recorded G verdict ... none recorded means a `behaviour_check` job runs first"); slice B6 (the dummy backtested end to end); slice B14 (`behaviour_check`, depends on B12 and B13).
- **What is wrong.** B6 cannot open a run without a G record, and the only producer of one is B14, four slices later. Either B6 silently skips the rule or it cannot pass. B6 also lists only A's compile and loader, not A's layer G functions (A6) or the `test-report` fields (A7).
- **Proposed fix.** Move the `behaviour_check` job into B6 (or a slice B5b before it), depending on A6 and A7; B14 keeps the other run kinds.

### R1-B-02 (High) [A][B] How a node's data reaches its machine's store is designed twice and half-built

- **Where.** B AD-209 and AD-210 (only closed months roll into partitions; the live tail by `journal_tail`); C LC-C-16, C CONTRACTS change 9 ("open month of bar series harvested every 60 s; ticks hourly; journals as Part B designs"), C AD-309 (the recorder writes bars and ticks into the node's append store), Level 0 AD-5 and X3 (the recorded feed is pulled home for the nightly replay).
- **What is wrong.** Three gaps. (1) The MIS node instance reads bars from its machine's store (C AD-313), but under B's design the current month's bars are never in the store. (2) The node's recorded feed (bars, ticks) lives in its append store, and B's records job commits only sealed journal months, so nobody commits the recorded feed; QB-23's nightly replay and `data.list` then find nothing. (3) Reading history (C AD-314) rides B's journal envelope, so current readings appear in history only a month late, which leaves `readings_query`, the board's history and the slow-lane templates blind.
- **Evidence.** The store already keeps the open month as one file replaced on each commit (`packages/qmf-data/src/qmf/data/series.py:6-9`). CHECKED by running `r1/br_open_month.py` in the scratch export: three growing commits of one open month of `bar-m1` each land as `open.parquet` with 60, 120 and 180 rows, `frozen = False`. Blast-radius step 4.
- **Proposed fix.** B's records job local half is the one harvester of every append store on its machine: sealed journal months as designed; the open month of bars and of reading history every `[records] open_harvest_s` (default 60); ticks every `[records] tick_harvest_s` (default 3,600). B owns it in B15; C consumes it.

### R1-B-03 (Medium) [A] Two ways to confirm a verified copy, and the door change has no slice

- **Where.** B AD-210 and LC-B-13 (the next `data.list` watermark is the proof); C CF-5, LC-C-32 and CONTRACTS change 2 (a `confirmed` list of fingerprints on `data.list`; the server's door pins node-born partitions until listed, "Part B builds the door change with its harvest"); B16 Files (no door change).
- **What is wrong.** Two builders would build two protocols. B16 does not build the pin that CF-5 needs, so a future prune could delete an unconfirmed partition.
- **Evidence.** The door already pins PC-born files and clears them by a list of fingerprints (`qmx_host/market_data.py:599-600`, `:603-617`), CHECKED.
- **Proposed fix.** See clash settlement CF-5: C's fingerprint list wins; B16 adds `confirmed` to its `data.list` calls and the node-born pin to the server's door.

### R1-B-04 (Medium) [V] B15 waits on the trading node for no reason, which pushes the slow lane and the MIS app behind the node

- **Where.** B15 "Depends on: B8; Part C's practice node writing through the writer library"; its Verify uses "a sealed month in a fixture app's volume". B18 depends on B15; B19 and B20 on B18; C-09 depends on "Part B's harvest".
- **What is wrong.** With B15 behind C-12, "Build and prove a unit" (B19) and the MIS app on This PC (C-09) both wait for the node's runtime, which Level 0 puts late. C's own claim that C-01 to C-09 come before the node fails.
- **Proposed fix.** Drop the node from B15's dependencies (its tests use a fixture app volume); a check on the practice node's real journal joins C-14.

### R1-B-05 (Medium) [V] B7 depends on an A slice that does not exist

- **Where.** B7 "Depends on: B6; Part A's windowed read surface"; B CONTRACTS §9 ("the read surface protocol a windowed reader implements | Part A"). No A slice builds a windowed read surface; A keeps QML's `ReadSurface.at` (A Seams table).
- **Proposed fix.** B7 builds the windowed reader in QMB against QML's kept `ReadSurface`; drop the A dependency.

### R1-B-06 (Medium) [A] The word `state` carries two meanings, and the writers of lifecycle events are unnamed

- **Where.** B `journals.md:42` (unit-journal `state` = a lifecycle change per market); A CONTRACTS §4.2 (`state_events`: warming, ready, cold_start, seam_flag) and §8 (`qmx.lifecycle/1`); B node-journal kind `lifecycle` (node starts and stops).
- **What is wrong.** A's runtime state events have no kind, so a builder puts them under `state` beside lifecycle moves. Nobody is named to write the lifecycle events: his clicks (on This PC), the judge's pass that moves draft to tested (B), the node's risk stop (C).
- **Proposed fix.** Unit-journal kinds `lifecycle` (body `qmx.lifecycle/1`, A's) and `state` (A's state events); the node journal's kind becomes `node_lifecycle`. Writers: This PC's host for his clicks, the judge for draft to tested or parked, the node for risk stops.

### R1-B-07 (Medium) [A] The journal envelope lacks the `source` field Part C relies on

- **Where.** B CONTRACTS §4 (no `source` field); C CONTRACTS §7 ("The envelope's `source` is `node` or `mis`"); Level 0 AD-27 and AD-40 (one writer per series, the key includes the source).
- **Proposed fix.** The reading body carries `source` (C §7), and B's partition subject for `journal-readings` includes source and machine. One line in each part.

### R1-B-08 (Medium) [V] B18 is not one PR

- **Where.** B18 builds eleven shared pieces (conveyor, lineage writer, death certificate, forecast ledger and scorer, receipts grader, marked sources, data-quality step, proposal card, unit-check step, calendar-open check, digest), changes four templates and removes two gate scripts.
- **Proposed fix.** Split by consumer: B18a the pieces B19 needs (unit-check step, proposal card, death certificate, lineage writer, conveyor); B18b the slow-lane pieces (receipts grader, marked sources, digest, calendar-open check, forecast ledger); B18c the surgical template fixes.

### R1-B-09 (Medium) [E] Three failed QMB runs stop QMB until someone restarts it

- **Where.** B AD-201 and mini-app-core §6 ("the breaker and its default of 3 errors ... stay as built"); B AD-204 (a failed run is a bundle with `status = failed`), but no rule says a QMB job never raises.
- **What is wrong.** The breaker adds job errors to tool errors over the whole life of the process and trips at three; a job that raises counts once. An agent looping on broken units (AG-11) would trip QMB after three bad runs, and QMB does not opt into the restart with back-off, so it stays down: a research stop nobody asked for.
- **Evidence.** `qmx_apps/bootstrap.py:203-210` counts `job_errors` on any exception; `qmx_apps/supervisor.py:797` reads it from the heartbeat and `:817` trips when `errors + job_errors >= max_errors`; a failed job raises `job_failed` (`:1032-1033`). CHECKED.
- **Proposed fix.** B states that every QMB job catches domain failures and returns a `failed` bundle (as C does for node operations, C AD-302); only a crash raises. QMB also opts into `[breaker] restart = "backoff"` (a lead's call), so a crash heals like the node and the MIS.

### R1-B-10 (Medium) [A] A slice replayed after a crash writes its decisions twice

- **Where.** B AD-208 and CONTRACTS §4 (`record_id` is `<writer_id>/<seq>`, except fills, which use the venue deal id); A AD-107 (every decision row id is fp1 over scope id, instant and ordinal, "so a rerun writes the same ids"); the node driver commits its cursor only after a whole slice (`qmn/src/qmn/loop/driver.py:70`, CHECKED).
- **What is wrong.** After a crash mid-slice the node re-runs that slice. A's row ids repeat, but B assigns new sequence numbers, so each decision, calibration and state row of that slice lands twice under different record ids. Live statistics and the calibrator's next read would see doubles.
- **Proposed fix.** For unit-journal kinds whose body carries A's `row_id`, the record id is that row id (as fills use the deal id), and the writer drops a repeat. One line in B AD-208 and CONTRACTS §4.

### R1-B-11 (Low) [E] "Data level" means two things

- **Where.** B CONTRACTS §1 `capabilities.data_levels[]` (`quotes`, `trades`, `bars`) and run-request `data[].level`; glossary "Data level" (levels 0 to 6, A's `qmx.data-level/1`).
- **Proposed fix.** B renames its field `fidelity` (the word its result labels already use).

---

## Findings for part C (node, MIS, external)

The fix round for C edits files in `parts/C-node-mis-external/`.

### R1-C-01 (High) [E] Nobody builds the path from his promotion click to a deployment

- **Where.** Level 0 AD-3, AD-23, AD-38, X1; A AD-115 (the pure lifecycle machine, slice A9); C AD-317 and CONTRACTS §3 (the deployment document, "minted on This PC"); B proposal cards (B13). CHECKED by grep: no slice in A, B or C builds the action that records his click.
- **What is wrong.** "Only he promotes" is the rule the whole lifecycle exists for, yet no slice builds (1) the This PC action, his principal only, that writes the lifecycle event for tested to paper or paper to live, and (2) the deployment builder that gathers the unit document, its pinned block folder, the G record, the calibrated starting values, the instrument, venue and account snapshots and the lane, then asks the node link to `deploy`. C-12 and C-14 test `deploy` with a document written by hand. The calibrated starting values are not defined either: a live deployment could start from defaults or from the paper lane's state, which changes what the unit trades (A AD-103).
- **Proposed fix.** C adds slice C-23 "promote and deploy" (after C-12a): a host action `units_promote`, answering only to his principal `operator`, that folds A's lifecycle, writes the event through B's writer, builds the deployment document from the Library and calls `node_link.ask(deploy)`. Rule for the starting values: paper starts from the unit's defaults (as QMB tested); live carries the paper lane's last calibrated state with its watermark (a lead's call, logged).

### R1-C-02 (High) [V] The costliest money case has no check in any slice

- **Where.** Catalogue TN-01 (an order's outcome is lost after send; "a demo drill cuts the network after send and shows one position"), one of the catalogue's five costliest cases; C `NODE.md:133` writes the drill; slices C-12 and C-15 do not run it (CHECKED by grep: "drill" appears in no C slice).
- **Proposed fix.** C-12b's Verify (R1-C-07) adds a deterministic drill on the conformance venue (the answer to a send is dropped; the node marks UNKNOWN, reads orders by client order id and positions by tag, does not resend, and ends with one position); C-15 repeats it on demo. TN-05's refresh drill on demo joins C-15 too (also in no slice).

### R1-C-03 (High) [V] The core rows `readings_query` and `instrument_get` belong to no part

- **Where.** Level 0 AD-31 lists both rows; connections C15; A consumes `instrument_get` (A CONTRACTS §12); B says they are Part C's (B CONTRACTS §10); C has no slice and no contract for either (CHECKED by grep).
- **What is wrong.** Agents reach readings only through `readings_query` (C AD-313), and the slow-lane templates (B20: shortlist, tagging, MIS check) need it.
- **Proposed fix.** C owns both: `instrument_get` in C-02, `readings_query` in C-09, row schemas in C CONTRACTS.

### R1-C-04 (Medium) [A] `apps.job` carries no inputs, so a server-homed QMB cannot run

- **Where.** C CONTRACTS §1 (`apps.job` args `app`, `job`, `pin`, `profile`); B AD-215 and CONTRACTS change 8 ("carries `inputs` and the caller's principal").
- **Proposed fix.** C adds `inputs` (optional) to `apps.job`; the principal stays in the pass.

### R1-C-05 (Medium) [A] The node link is not the only path to the practice node

- **Where.** C AD-303 ("the only code on a machine that asks a node app anything", with a per-node outbox that keeps clicks in order) against C AD-302 ("on This PC the copilot sees the practice node's operations as tools ... each `manage` one asks him first").
- **What is wrong.** On This PC a chat calls the supervisor directly through the harness (`qma-harness/src/qma/harness/tools.py:538-560` serves every running app's operations, CHECKED), so a `manage` call from a chat skips the outbox and its ordering (LC-C-38).
- **Proposed fix.** Keep the chat path (his approval prompt is his click, and the practice node holds demo grants only), and narrow AD-303's claim: the node orders every change by its own `desired` table and refuses an op id older than one it applied for the same scope.

### R1-C-06 (Medium) [E] A 16 MB cap on a deployment is an invented limit

- **Where.** C CONTRACTS §3 and LC-C-37 (`deploy_max_bytes` 16 MB, refused past it).
- **What is wrong.** Standing order 9 bars invented limits; a unit whose learned block carries weights (QML-13) can pass 16 MB, and then cannot be deployed at all.
- **Proposed fix.** The deployment document names its files by fingerprint; files the node's volume lacks reach the server ahead of `deploy` through the Library hub (X5, X10) and the host copies them into the node's volume; `deploy` refuses only a missing or mismatched file. No size setting.

### R1-C-07 (Medium) [V] C-12 is several PRs

- **Where.** C-12 builds the runtime, the reconciler, the feed keeper, attribution, the encoder's `label`, the order path with the protection gate, journal before dispatch, the paper lane and the stand-down table.
- **Proposed fix.** Split into C-12a (feed keeper, runtime and order path on the conformance venue, the stop-on-every-order test), C-12b (reconcile with attribution, the UNKNOWN drill of R1-C-02), C-12c (paper lane and stand-down table).

### R1-C-08 (Medium) [V] No test sends a sized intent end to end (CA-03)

- **Where.** Catalogue CA-03 (H, Money: "a test sends a sized intent end to end"); A1 tests format 3 in QML, B10 tests lot rounding in QMB, C-12 tests that the dummy trades. None asserts that the quantity the venue receives equals the sizer's receipt.
- **Proposed fix.** B6 and C-12a each assert that the filled or sent quantity equals the sizer receipt's quantity after lot rounding, so a door that drops the size fails the build.

### R1-C-09 (Medium) [V] Four changes to the mini-app core in one PR

- **Where.** C-05 changes the supervisor in four ways at once (restart with back-off, market root, host facts, server secret reader).
- **What is wrong.** Ruling 53 calls the mini-app core one of "two babies, handled with care". One PR per change keeps each blast radius readable.
- **Proposed fix.** Split C-05 into four PRs, each with its own test and the shipped breaker and road tests unchanged.

### R1-C-16 (Medium) [V] Two reconnect cases have handling but no test in any slice

- **Where.** EX-02 (the book is rebuilt after every reconnect before any reader sees it, C AD-309) and TN-19 (a silent socket past the heartbeat bound forces a reconnect). Both are written in the spine; no slice's Verify runs them (CHECKED by reading C-12 and C-16).
- **Proposed fix.** C-12a's Verify adds both on the conformance venue: a dropped session mid-book shows `book_state = rebuilding` until a fresh snapshot, and a silent socket past the bound reconnects with no entry until ready.

### R1-C-10 (Medium) [E] Instrument record keys and class names differ across parts

- **Where.** A CONTRACTS §2.3 (`contract_size`, `value_per_point`, `max_lot`, `day_boundary`, `roll_rule`; class `index_cfd`, `spot_crypto`, `stock`); C `RECORDS.md:22` (lot size, contract multiplier, money per point, maximum exposure, daily boundary; class `index-cfd`, `crypto-spot`, no `stock`; the roll rule on the unit, not the record); B CONTRACTS §1 (class `index_cfd`, `crypto_spot`).
- **What is wrong.** Layer C's conversions and the sizer read these records. Three spellings of one enum and two homes for the roll rule let two builders diverge on a money path. C also never names A's data-level vocabulary `qmx.data-level/1` (CHECKED by grep), which A's own review asked R1 to check.
- **Proposed fix.** C, the owner, writes `RECORDS.md` §2 as exact keys that match A §2.3, one class enum with underscores, the roll rule on the unit (C's call, since a unit picks its roll) with A §2.3 updated to drop `roll_rule`, and the data levels as `qmx.data-level/1`.

### R1-C-11 (Medium) [A] Shipped tool counts turn CI red when B and C add rows

- **Where.** B CONTRACTS §7 adds `judge_run` to the `backtest` toolset and `journal_query`, `notes_write` to `research`; C-06 adds `node_units`, `node_positions`, `node_journal_tail`, `node_passport` to `node`. Neither part names the shipped test that pins these counts (CHECKED by grep over both folders).
- **Evidence.** `qmx-tools/tests/test_tools.py:374-376` pins `data` 4, `backtest` 4, `research` 3, `node` 2 tools per server (CHECKED). Part A avoided it with new toolsets (A BR-A2).
- **What is wrong.** Ruling 52 requires every PR to keep the shipped tests green; a builder who meets this red test may "fix" it the wrong way.
- **Proposed fix.** B6, B13, B15 and C-06 each name this test as changed on purpose, with the new count in the slice's Verify line.

### R1-C-12 (Medium) [E] An agent can start a job on a money app through the host route

- **Where.** C CONTRACTS §1 principal rule (only `manage` operations need `operator`); B CONTRACTS change 8 (a job counts as `domain_write`, so an agent may start one).
- **What is wrong.** The rule guards operations, not jobs. The node declares no job today, but nothing stops a later version from declaring one, and then an agent could run it on a live node.
- **Proposed fix.** `apps.job` refuses a non-`operator` principal for an app whose manifest risk is `money`; a test in C-06.

### R1-C-13 (Low) [E] The MIS app's raw read root skips the door's holdout seal and read log

- **Where.** C AD-313 (`QMX_MARKET_ROOT`, read-only); B LD-08 (the door logs every read).
- **What is wrong.** On This PC the MIS app reads every price file outside the door, holdout months included. Readings over a sealed holdout then land in reading history, where agents read them (INFERRED; the holdout is off by default, so harm is low). Apps hold no host credential, so the door's `read` is not a way out (LC-C-14).
- **Proposed fix.** The MIS app reads the door's holdout seal from the same root and skips sealed months; a test in C-09 pins it.

### R1-C-14 (Low) [E] A live grant kept as a file in the node's volume may travel with that volume

- **Where.** C AD-306 and LC-C-11 (on Linux the grant is an owner-only file under `data/grants/` in the node's volume).
- **What is wrong.** A volume can be copied (a provider move, a restore, a backup round if one ever runs on a server). Whether any shipped copy path includes app volumes on a server was not proven here (INFERRED risk).
- **Proposed fix.** C-17's Verify adds one check: no backup, replication or road copy on a server includes `data/grants/`; or the grant file moves beside the server's vault (`<home>/vault/`), which `qmx node` already treats as owner-only (`qmx_control/node.py:79-86`, CHECKED).

### R1-C-15 (Low) [V] Small inconsistencies inside C

- The host-facts path is `road/host/facts.json` in AD-307 and LC-C-13, but `road/host-facts.json` in slice C-05.
- C-12 depends on "Part A's ... G verdict"; the record that a deploy needs is landed by B's `behaviour_check` (R1-B-01). C-12's tests use a fixture record; say so.
- C-09 is listed among the slices before the node, but depends on B15 (R1-B-04).

---

## Clash settlements

Every clash a part raised with Level 0, with a settlement, the reason, and the files the fix round edits. "L0" means `level-0/ARCHITECTURE-SPINE.md`; "L0 calls" means `level-0/LEAD-CALLS.md`; "master" means `01-connections.md`. One agent edits Level 0 and the master; one agent per part edits its folder.

**Overall verdict.** Every clash the parts raised is a code fact or a sharper rule, and each keeps the purpose of the Level 0 rule it amends. All are accepted, with three refinements: B's watermark confirmation gives way to C's fingerprint list (B-CC7); pruning a server's store waits (B-CC7); and the mini-app core fix list becomes one list in Level 0 (CF-4).

### Part A's six findings (its "Conflicts with Level 0" table and its five drift closures)

| Id | Clash | Settlement | Reason | Edits |
| --- | --- | --- | --- | --- |
| A-C1 | The Library save of a `unit` runs A to F (L0 AD-17, AD-29, LC-A0-12) | **Level 0 changes.** `put` checks shape (layer A, every problem); publish (his yes) runs A to F; `compile` runs A to F and refuses, so QMB, the node and the MIS never run an unchecked document | the shipped every-kind test saves a schema-minimal unit (`qmx-library/tests/test_view.py:110-128`, CHECKED); nothing unchecked can be published, tested or traded, which is what the rule was for | L0 AD-17 door table, AD-29; L0 calls LC-A0-12; master C2 |
| A-C2 | The `component` kind "has no writer" (L0 AD-19) | **Level 0 changes.** A component is a dictionary entry only when `entry.schema = "qmx.entry/1"`; every other component is left as today | mini apps and the registry migration already write components (A cites `qmx_control/library.py:312-330`, `migrate/from_apps.py:66-70`; the premise was false) | L0 AD-19 |
| A-C3 | Compile's object "is accepted by `construct_bot` unchanged" (L0 AD-16) | **Both change.** Level 0: units are hosted through `construct_unit` and `HostedUnit`; `construct_bot` fails closed on a unit's first sized intent. B and C: consume A's door through one shared run-slice handler (R1-L0-02) | `accept_intents` refuses format 3 (A BR-A4, run); one handler keeps AD-5 | L0 AD-16, AD-5; master C12; B spine AD-205 and slice B6; C spine AD-301 and slice C-12a |
| A-C4 | Rows "in a core toolset" (L0 AD-31) | **Level 0 changes.** Two core toolsets, `unit` and `blocks`, with seven rows; the harness derives `DOMAIN_GROUPS` from the catalog rows (one line, its reason in L0 "Amended decisions") | a shipped test counts tools per server, and the harness keeps a second roster that must agree (`qma-harness/src/qma/harness/tools.py:664`, CHECKED) | L0 AD-31 row list and Amended decisions; master C5 |
| A-C5 | "`STAGE0_NEVER_SIZES` and `refuse_invented_exits` become labels" (L0 AD-20) | **Level 0 changes.** Stage 0 stays as built for research; the unit path never calls it; the 23 old-law names leave only QML's top-level surface | shipped tests pin both refusals (A cites `qml/tests/test_research_stage0.py:100`, `test_research_collapse.py:82`); A BR-A3 ran 385 tests green | L0 AD-20 |
| A-C6 | The five drift closures (A `reviews/review-adversary.md`) | **Level 0 adopts them.** (1) The calibrator's statistics live in the unit's state; hosts feed only the trades this run or deployment closed. (2) Decision-changing compiler options enter the compiled fingerprint. (3) A move out of `stopped` names the stop it clears. (4) The judge and the Lab call `qml.identity.classify`. (5) Decision row ids are fp1 over scope, instant and ordinal | each closes a way two hosts or two parts build the same rule differently; (1) and (5) carry AD-5 and AD-13 across QMB and the node | L0 AD-22 (1), AD-16 (2), AD-23 (3, 4), AD-13 (5); B spine AD-208 takes (5) as the record id (R1-B-10) |
| A-C7 | Units of measure are QMF `UnitKind`s (L0 AD-9; the table's sixth row, not in the brief's list) | **Level 0 changes.** QML owns the measure vocabulary and maps each measure to QMF's closed `UnitKind` by one table; QMF is not amended | QMF's enum is closed and "addable in a later spine amendment" (A cites `qmf-core/src/qmf/core/exact.py:125-144`) | L0 AD-9 |

### Part B's six disagreements and twelve contract changes

| Id | Clash | Settlement | Reason | Edits |
| --- | --- | --- | --- | --- |
| B-D1 | QMB's operations include `status`, `results`, `compare` (L0 AD-34); contract change 6 | **Level 0 changes.** The QMB contract is run kinds as jobs plus `capabilities` and `instruments`; status, results and compare are the core's `backtest` rows over core records | a variant must not report its own score (QB-13, QB-24); jobs survive the 30 s call timeout (`supervisor.py:957-963`) | L0 AD-34; master §5 |
| B-D2 | QMB is kind `both` (L0 AD-34) | **Level 0 changes.** `headless` until the UI session adds its folder | the manifest refuses `both` without `ui` (`qmx_apps/manifest.py:309-310`, CHECKED); ruling 45 bars UI code | L0 AD-34, P11 |
| B-D3 | Engine changes are AGW and the `library` kind only (L0 AD-32); contract change 2 | **Level 0 changes.** Add "`app_op` passes `inputs`, carried by engine AD-64" | a job request today is `{"job": job}` only (`supervisor.py:1022`, CHECKED), so a workflow cannot say what to test; engine AD-64's own design names node inputs (ruling 49) | L0 AD-32; master C8 |
| B-D4 | C10's door is `backtest_and_land` per door; contract change 3 | **Level 0 changes.** The door is the supervisor's job path with the lander `qmb-run` (in `qmx-judge`, absorbing PR 204's `land`) | the one landing holds for every door only if it sits on the one path every door crosses | master C10; L0 AD-34 ("the core keeps PR 204's one landing function" becomes "the core lander") |
| B-D5 | C11: QMB reads the market-data door; contract change 4 | **Level 0 changes.** The core lander materialises a run's partitions into the run folder; QMB reads files only | the holdout and the read log stay in the core; QMB spawns and opens nothing | master C11 |
| B-D6 | QMB tool wait 600 s (LC-A0-21); contract change 1 | **Level 0 changes.** `[qmb] agent_wait_s` default 240 s for agent callers; workflows wait for the whole job | the prompt cache lives five minutes (WF-07); a number, so a setting | L0 calls LC-A0-21; master C7 |
| B-CC5 | Add the `try` kind row to master §5 | **Accepted** | one append-only item per try (L0 AD-25) | master §5 |
| B-CC7 | X3 is "a job on This PC"; the next `data.list` watermark confirms a verified copy; the node deletes after retention | **Partly accepted.** The pull is a host upkeep job beside backups, not an engine workflow (accepted). Confirmation uses C's `confirmed` fingerprint list on `data.list`, not the watermark (B's half rejected). Deleting confirmed partitions on the node waits for a later prune slice; this build pins and keeps | the host-job pattern is built and his rule keeps external jobs apart from agent workflows (LC-B-12); the door already confirms PC-born files by fingerprint (`market_data.py:599-617`, CHECKED), so one protocol serves both directions; a per-file list survives partial failures, a watermark does not; disk lasts months at X3's volumes (INFERRED from master X3) | master X3; L0 AD-28; B spine AD-210, LC-B-13, LC-B-27, slice B16 |
| B-CC8 | AD-46 `apps.job` carries `inputs` and the principal; a job counts as `domain_write` | **Accepted, with one guard.** C adds `inputs`; the principal rides the pass; `apps.job` refuses an agent for a `money` app (R1-C-12) | server-homed QMB needs its inputs (B AD-215) | C CONTRACTS §1; L0 AD-46 |
| B-CC9 | Reading history rides the journal envelope (`journal-readings`) | **Accepted**, with `source` in the reading body (R1-B-07) | one storage path for all a node produces (ruling 51) | master C22, C24; B CONTRACTS §4; C CONTRACTS §7 |
| B-CC10 | New master row C30: supervisor to the core lander | **Accepted as C30.** C's host-facts row becomes C31 and its log-shipping row C32 | both parts proposed "C30" (CHECKED: B CONTRACTS change 10, C CONTRACTS change 6) | master §2 |
| B-CC11 | C14: verdicts, baseline cards and proposal cards are records, not governed drafts | **Accepted** | scripts write them and nothing promotes through them; his click acts on the unit's lifecycle, which R1-C-01's promote action records | master C14 |
| B-CC12 and the "closed months committed by its own host" disagreement | The committer of a node's closed months is that machine's host | **Accepted and widened** (R1-B-02): the host's records job is the one harvester of every app's append store on its machine, sealed journal months plus the open month of bars and readings and hourly ticks | the door's single writer is the host and an app never opens it; the open month is one replaceable file (`series.py:6-9`, and `r1/br_open_month.py`, run) | master C13, C23; L0 AD-27; B spine AD-209, AD-210, slice B15 |

### Part C's CF-1 to CF-7, its extra core fixes and its contract changes

| Id | Clash | Settlement | Reason | Edits |
| --- | --- | --- | --- | --- |
| CF-1 | On Linux the grant sits in QMN's node secret store (L0 AD-37) | **Level 0 changes.** An owner-only grant file on the node's machine with QMN's one-refresher, store-before-discard rule; R1-C-14 adds the check that it never leaves the machine | QMN's store reads systemd's `CREDENTIALS_DIRECTORY` (`qmn/src/qmn/secrets/store.py:1-8`, CHECKED), and the supervisor builds an app's environment from a short allow-list (`qmx_apps/supervisor.py:598-611`, CHECKED) | L0 AD-37; master C27 |
| CF-2 | "The code's two roles" (L0 AD-45) | **Level 0 changes.** The code has three roles (`pc`, `node`, `server`); a trading server runs role `server`; this build does not use role `node`; the trading profile stays a derived rule | `qmx_host/host.py:141`, CHECKED; the shipped setup writes `server` (C cites `qmx_control/node.py:488-509`); role `server` also carries the Library service a deploy-time cache needs (R1-C-06) | L0 AD-45, P0; master §1 |
| CF-3 | X1 lists an operation `mode` | **Level 0 changes.** `bind` replaces `mode` (the venue proves demo or live); add `withdraw`, `confirm_same_node`, `sign_in_begin`, `sign_in_code`, `self_test`, `rotate_keys` | a separate mode duplicates `bind`; identity and sign-in need their own operations | master X1; L0 "Networking between machines" table row X1 |
| CF-4 | L0 AD-33 names one core fix (restart with back-off); C needs three more; B needs two | **Level 0 changes: one list of six mini-app core changes**, each surgical, each its own PR: (1) jobs take `inputs` and return `result` (B); (2) a provides contract may name a core lander (B); (3) opt-in restart with back-off (L0, C); (4) a read-only market root for apps declaring `data_reads = ["market"]` (C); (5) the host writes `road/host/facts.json` into each app volume (C); (6) a server host reads declared secrets from its owner-only vault (C) | each truly blocks a first-party app (ruling 46); the set is consistent: B touches `run_job`, `bootstrap.run_job` and the sink, C touches `Breaker`, the trip path, `environment()` and the host, so no two parts change the same function; one interaction to test is a restart after a trip, which must still let the lander fail the job that was running (B5's test, once QMB opts in, R1-B-09); the breaker default of 3 stays for apps that do not set their own | L0 AD-33 and "Amended decisions"; C slice C-05 split in four (R1-C-09); B slices B1, B5 unchanged |
| CF-5 | "The node keeps every partition until the PC confirms" (L0 AD-28), with no marker | **Level 0 changes.** The server's door pins node-born partitions until This PC lists their fingerprints as `confirmed` on `data.list`; nothing prunes in this build | the door pins only PC-born files today (`market_data.py:599-600`, CHECKED); the same fingerprint protocol serves both ways | L0 AD-28; master X3; B slice B16 builds it; C CONTRACTS §1 (kept) |
| CF-6 | Market-state readings are the `mis` app's; execution-health readings run in the node (L0 AD-40, LC-A0-02) | **Level 0 changes.** Split by tier, not by kind: every tick-tier reading on a trading machine runs in the node (`source = node`); the `mis` app runs bar, session and day tiers | only the node holds the tick stream (L0 AD-8); one writer per series still holds because the key carries source and tier | L0 AD-40, P13; L0 calls LC-A0-02; master C22, C23 |
| CF-7 | Netting: "one virtual position per unit; the venue nets" (L0 risk table, catalogue UT-14) | **Level 0 changes.** On a netting account or a Hyperliquid subaccount, at most one unit per symbol, refused at deploy and labelled a placeholder for the risk session | per-unit broker stops cannot sit on one netted position, so the old rule would leave a unit unprotected | L0 "For the risk session" table; the risk pack's netting row |
| C-CC2 | `data.list` gains `confirmed` | **Accepted** (as CF-5) | | master X3 |
| C-CC3 | C23: the MIS reads through `QMX_MARKET_ROOT` | **Accepted**, with the holdout seal honoured (R1-C-13) | apps hold no host credential (LC-C-14) | master C23 |
| C-CC5 | E8: the node's sign-in is `sign_in_begin` and `sign_in_code` | **Accepted** | the host's refusal and its tests stay as built (L0 Amended decisions, ruling 135 row) | master E8 |
| C-CC6, C-CC7 | New rows for host facts and app-log shipping | **Accepted as C31 and C32** (B-CC10) | | master §2 |
| C-CC8 | Heartbeat rows read tolerantly across machines; an optional `clock` field | **Accepted** | the heartbeat models forbid unknown fields (`qmx_engine/heartbeat.py:70`, `:85`, `:101`, CHECKED), so a newer server would break an older PC's reader | master X2; L0 AD-6 (a sentence on tolerant cross-machine reads) |
| C-CC9 | Part B harvests the open month of bars every 60 s and ticks hourly | **Accepted** (R1-B-02) | | B spine AD-209, AD-210; B slice B15 |

## Cross-part checks

### Check 1: every catalogue case handled by its owner, by name, with a check

- **Coverage by script** (`r1/cases.py`, CHECKED). 267 cases plus 18 risk rows. The three part tables claim 246 of the 267 (plus RS-13 and RS-18); none has an empty handling line; no part claims a case the catalogue lacks. 21 cases have no owner (R1-L0-01). QML-06 is claimed by A and C on purpose (A takes "the QML side", C owns the record). MIS-10 moved from C to B by the handover, as intended.
- **Handover by script** (`r1/handover.py`, CHECKED). Every handover line is settled by name in its part's spine: A 21 of 21, B 26 of 26, C 36 of 36.
- **A deterministic check per case.** 144 handling lines name no check word (test, check, refuse, probe, drill and the like); most point at an AD whose slice carries the test. The money-adjacent paths, weighted:

| Money path | Where it is checked | Gap |
| --- | --- | --- |
| Order placement and size | A1 (format 3 round-trips its size), A5 (`construct_bot` refuses a sized intent), B10 (lot rounding), C-12 (the dummy trades with its stop at the broker) | no test asserts the venue gets the sizer's quantity (R1-C-08); two run-slice handlers would drift (R1-L0-02) |
| The kill switch and kill line | C-06 (a queued `pause` applies once), C-12 (stop on every order), C-20 (the same test before and after the cut), LC-C-28 placeholder levels | none beyond the placeholder values, which are the risk session's |
| Journals that record trades | B8 (writer, refused append never silent), B15 (`r_missing`, re-projection lands nothing), B16 (resend changes nothing) | a re-run slice doubles decision rows (R1-B-10); the recorded feed and open months have no harvester (R1-B-02) |
| The unit runtime | A5, A6, A10 (warm-up, own positions only, cold start) | the shared handler is unowned (R1-L0-02) |
| Self-tuning | A5 (hand-fed journal), B9 (calibration rows in a run) | the slow number may not move in real runs (R1-A-01); a deployment's starting values are undefined (R1-C-01) |
| Reconnects and duplicates | C-15 (repeated `clientOrderId`, `label` survival), C-16 (unmapped error is UNKNOWN) | the network-cut drill (R1-C-02), the refresh drill (R1-C-02), book rebuild and silent socket (R1-C-16) are in no slice |

### Check 2: seams between parts

- **Contracts against the master.** Each part lists its contract changes rather than overriding the master, as `01-connections.md` §7 asks. All are settled above. Two collisions: both B and C proposed a row "C30" (B-CC10), and B's watermark against C's fingerprint list (B-CC7).
- **Unmatched seams.** A's unit door is consumed by nobody (R1-L0-02). `apps.job` lacks the inputs B needs (R1-C-04). The reading body's `source` has no field in B's envelope (R1-B-07). `readings_query` and `instrument_get` have no builder (R1-C-03). Instrument record keys and class names differ three ways (R1-C-10).
- **Two parts claiming one thing.** None found in ownership: B owns the harvest, C consumes it; B owns the journal kinds, A owns the lifecycle body, C owns the reading body. The words collide twice: `state` (R1-B-06) and "data level" (R1-B-11).
- **Standing alone.** No part makes a unit depend on another part being up: the board read waits behind a fallback (C-22), readings have declared fallbacks, the node trades from its deployment's snapshots and blocks, and the host on the trading path was accepted at Level 0 (AD-2, LC-A0-06). CHECKED by reading each part's runtime rules; no counter-example found.

### Check 3: the build slices, merged into one order

Each part's slices are PR-sized with files, a dependency, a check with its command, and what he sees, except B18, C-05 and C-12, which are several PRs each (R1-B-08, R1-C-09, R1-C-07). After the fixes above, one order with no slice needing a later one (a slice in brackets is a split or new slice proposed here):

1. **Ground, no dependencies.** A0, A1, A2; B1, B3, B4, B8, B17; C-01, C-02, C-04, C-05 [four PRs], C-06.
2. **QML to its first end-to-end run inside QML.** A3, A4, A5, A6, A7, A9; B2, B5; C-03, C-07.
3. **The first run he sees.** B6, with `behaviour_check` and the shared unit handler moved in (R1-B-01, R1-L0-02): the copilot backtests the dummy and a result lands with money and R.
4. **Widen QMB and the authoring doors.** A8, A10, A11, A14, A15; B7, B9, B10, B11, B12, B13, B14.
5. **The dictionary and the MIS on This PC.** A12, A13 [several PRs]; C-08; B15 [without its node dependency, R1-B-04]; C-09.
6. **The slow lane on This PC.** B18a, B18b, B18c, B19 ("Build and prove a unit"), B20.
7. **The node, late, as Level 0 asks.** C-10, C-11, C-12a, C-12b, C-12c, [C-23 promote and deploy], C-13, C-14 (his demo sign-in), C-15, C-16, C-17, C-18, C-19, C-20, C-21, C-22.
8. **Home-coming from servers.** B16 (its tests after C-06, its live lane after C-17), B21.

- **The smallest thing that runs end to end** is A5 inside QML and B6 through the platform; both are early.
- **The dummy unit is early** (A2, fixture in A4 and A5) and shows a real number moving by its rule: `rsi_low` every bar from A5 on. The slow number needs R1-A-01's fix to move in a real run.

### Check 4: code claims and blast radius

Claims spot-checked at their cited lines on `D:\QMX-worktrees\engine-base-read\`, all true unless noted:

| Claim | Where | Result |
| --- | --- | --- |
| A save of a schema-minimal item of every live kind | `qmx-library/tests/test_view.py:110-128` | true |
| The harness's second roster | `qma-harness/src/qma/harness/tools.py:664` | true, cited as `:668` (R1-A-04) |
| A job request carries only its name; `run()` takes no argument; one job at a time | `qmx_apps/supervisor.py:1022`, `bootstrap.py:195-228` | true |
| One instance per app id | `qmx_apps/supervisor.py:572` | true (cited `:570`) |
| The manifest refuses `both` without a UI folder, and an instance read | `qmx_apps/manifest.py:309-310`, `:324-327` | true |
| Breaker counts tool and job errors over the process life | `qmx_apps/supervisor.py:797`, `:817`, `:884-934` | true; the job half is new here (R1-B-09) |
| A `money` app starts only with an active signed version | `qmx_apps/supervisor.py:542-547` | true |
| Three host roles | `qmx_host/host.py:141` | true (CF-2) |
| The engine's forwarders mint a constant `operator` principal | `qmx_host/host.py:1155` | true |
| His principal string is `operator` | `qmx_engine/service/context.py:59-70` | true (R1-L0-03) |
| `app_op` composed with no placements | `qmx_engine/control_door.py:308` | true |
| The harness serves every running app's operations to chats | `qma-harness/src/qma/harness/tools.py:538-560` | true (R1-C-05) |
| QMN's secret store needs systemd credentials; apps get a short environment | `qmn/src/qmn/secrets/store.py:1-8`, `qmx_apps/supervisor.py:598-611` | true (CF-1) |
| The bootstrap refuses app writes to `road/` | `qmx_apps/bootstrap.py:93-100` | true |
| Heartbeat models forbid unknown fields | `qmx_engine/heartbeat.py:70`, `:85`, `:101` | true |
| The door pins PC-born files only, and clears them by fingerprint | `qmx_host/market_data.py:599-617` | true (CF-5) |
| Kill-on-close in the Job object | `qmx_apps/windows_job.py:35` | true |
| Shipped tool counts per server | `qmx-tools/tests/test_tools.py:374-376` | true; not named by B or C (R1-C-11) |
| `run_slice` drives any handler with the five hooks; the node imports QMB | `qmb/src/qmb/runloop/loop.py:780-801`; `qmn/src/qmn/loop/driver.py:16`, `:409-417` | true (R1-L0-02) |

**Blast radius on the riskiest seams.**

- **The node's data reaching its store (R1-B-02).** The one fact the fix is safe because of: the store keeps the open month as one file replaced on each commit, so a harvest every minute leaves one file, not one per round. Proven at step 4: `r1/br_open_month.py` in the scratch export's environment committed 60, 120 and 180 rows of one open `bar-m1` month; each landed as the same `open.parquet`, `frozen = False`. Found on the way: committing the same rows again reports `idempotent = False` although it leaves one file, unlike what `SeriesStore.commit`'s docstring says (`packages/qmf-data/src/qmf/data/series.py:429-430`); harmless here, worth a line in B15's tests.
- **The unit's run-slice handler (R1-L0-02).** Step 2: `run_slice` checks only that its handler has the five hooks; nothing in it knows bots. So one handler over `HostedUnit` serves both hosts. Not run here; B6's tests prove it.
- **The breaker and QMB's jobs (R1-B-09).** Step 2: pointed at the counting and the trip lines above. Not run.
- **Parts' own proofs.** A ran six seams at step 4 (BR-A1 to BR-A6), B ran three (jobs with inputs, the journal column, AGW's offered tools) and marked the lander at step 2, C ran nine (C1 to C9). R1 did not rerun them; their scripts are named in each part's blast-radius file.

### Check 5: over-building, under-building, words, plain sentences

- **Under-built** (the larger risk here): the promote and deploy path (R1-C-01), the shared unit handler (R1-L0-02), the harvest (R1-B-02), two core rows (R1-C-03), the money drills (R1-C-02, R1-C-16).
- **Over-built**: little. The 16 MB deployment cap is an invented limit (R1-C-06). The `file` placeholder for futures data (C AD-311) is small and earns its place (ruling 40). B's seven judging kinds come from the funnel's slow lane (ruling 44) and each has one writer; kept.
- **Words.** The glossary's words hold, with three slips: "kernel" in Level 0's table (R1-L0-07), `state` (R1-B-06) and "data level" (R1-B-11).
- **Plain sentences.** A, B and C each open with a plain-words section he could follow; Level 0 has none (R1-L0-06).

### Check 6: his rulings

| Ruling | Held? |
| --- | --- |
| QML first, with the most care | yes: A's slices come first and carry the deepest checks; A's six code-fact clashes show the care |
| QMB extensible with variants | yes: one app id per variant, the conformance pack, the default as a setting (B AD-201, AD-206) |
| Most things can be mini apps | yes: QMB, the node and the MIS are apps; the core changes are six surgical fixes (CF-4) |
| Windows first-class | yes: the practice node runs native; block fingerprints ignore line endings; QMB lowers its own priority on Windows; Linux only for live supervision and chrony |
| Local first | yes: every part runs on This PC alone; servers stand in |
| Nothing capped | one breach: the 16 MB deployment cap (R1-C-06) |
| Only he promotes | the rule holds in every machine, but the click that records it is unbuilt (R1-C-01) |
| The copilot can do what agents can | yes: every new row is on the default copilot surface by test (A AD-117, B CONTRACTS §7); C's node rows join the core `node` toolset |

### Cases found by this review (for the catalogue's next fold)

| Id | What happens | Handling | Finding |
| --- | --- | --- | --- |
| R1-NEW-1 | Three failed backtests stop QMB for good, because job errors add up over the process life and QMB has no restart | QMB jobs return failed bundles; QMB opts into restart with back-off | R1-B-09 |
| R1-NEW-2 | A slice re-run after a crash writes its decisions a second time under new record ids | the record id of a unit-journal row is its decision row id | R1-B-10 |
| R1-NEW-3 | The current month of a node's bars, readings and recorded feed never reaches its machine's store | the host harvests open months on a cadence | R1-B-02 |
| R1-NEW-4 | A shipped test pins tool counts per server, so a new row on an existing toolset turns CI red | each slice names the test and the new count | R1-C-11 |
| R1-NEW-5 | An agent starts a job on a money app through the host route, since the principal rule guards only operations | `apps.job` refuses agents for `money` apps | R1-C-12 |
| R1-NEW-6 | A live grant file inside an app volume travels when the volume is copied | a check that no copy path includes it, or the grant beside the vault | R1-C-14 |

## Decisions only he can make

None of the findings needs his money or his values. Two are words on his screens, already marked for his veto by the parts; they belong in the final brief as yes-or-no lines, not as questions now:

1. **"Regime" means trending or ranging; the old volatility buckets become "volatility state"** (Level 0 LC-A0-20, C MIS-03).
2. **The three kinds of number read "Fixed", "Follows the market", "Follows its record" on his screens** (A LC-A1-21).

Every other call above is the lead's to make and log (STATE midday ruling 2), including the calibrated starting values of a live deployment (R1-C-01) and QMB's opt-in restart (R1-B-09).
