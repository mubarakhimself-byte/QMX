## Trade the dummy unit on the node against the conformance venue (C-12a)

Phase 5, the trading node and external connections. Part C slice C-12a, Part C `NODE.md`, AD-308, Level 0 AD-5, AD-38 and AD-39, cases CA-03, EX-02 and TN-19. Rulings 27 (only the node sends orders, so the kill switch works) and 35. Real step none. Done when the node hosts the dummy through Part A's unit door and Part B's shared handler, places every order with its protection gate and journals before dispatch, and the conformance venue receives the sizer receipt's quantity.

**Depends on.** C-10, A4, A5, B5b, B8.

**Files.**

- [ ] Create `qmn/src/qmn/app/runtime.py` and `qmn/src/qmn/app/feed_keeper.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/node_link.py` (staging into `data/deployments/<deployment_id>/in/`) and `packages/qmf-venue/src/qmf/venue/encode.py` (the node's tag in cTrader's `label`, length checks).
- [ ] Edit `qmn/src/qmn/protection/effect_matrix.py` (shape only today) to carry lead's call LC-C-28's labelled placeholder values.
- [ ] Create `qmn/tests/test_app_runtime.py`, `qmn/tests/test_protection_every_order.py` and `qmn/tests/test_app_feed_keeper.py`.

**Build.**

- [ ] Write the feed keeper over the conformance venue client, `deploy` with files staged by the node link and compiled after the answer, the G fingerprint check, warm-up from the node's own recording, the order path with the protection gate, and the journal write before dispatch. The G record is a fixture `test-report` here.
- [ ] Fill the kill switch's effects with labelled placeholders, escalate-only, resume his. YELLOW stops new entries at the scope, ORANGE also cancels resting entry orders, RED also closes positions at the scope reduce-only, BLACK closes everything and pauses the node. Protection that cannot be placed after 3 tries within 2 s each closes that position reduce-only and raises the protection alarm (Part C AD-308). Both are listed in `build/RISK-SIZING-PLACEHOLDERS.md` for the risk session.

**You see.**

- [ ] On a throwaway folder against the test venue, the node card says "Trading, 1 unit".

**Verify, unit.**

- [ ] The dummy opens and closes on the conformance venue with its stop at the broker. The quantity the venue receives equals the sizer receipt's after lot rounding (CA-03). `deploy` answers before a 40 s compile. A staged file missing or with another fingerprint refuses `deploy` naming it, and a 32 MB weights fixture, twice the old limit, deploys (no size limit). A session dropped mid-book shows `book_state = rebuilding`, and no reader sees a half book until a fresh snapshot (EX-02). A socket silent past the heartbeat bound reconnects, and no entry is placed until the session is ready (TN-19). Each kill level applies its placeholder effect, carries `origin: placeholder`, and only he resumes. Run `uv run pytest qmn/tests/test_app_runtime.py qmn/tests/test_protection_every_order.py qmn/tests/test_app_feed_keeper.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Deploy the dummy to the node on a throwaway folder against the conformance venue for a recorded day. Save `c12a-trade.log`. Pass when it opens and closes with its stop at the venue on every order.
- [ ] Lane 3. Compare each sent quantity with its sizer receipt. Save `c12a-quantity.log`. Pass when every one equals the receipt's quantity after lot rounding.
- [ ] Lane 4. A deploy with a 40 s compile, one with a missing staged file, and one with a 32 MB weights file. Save `c12a-deploy.log`. Pass when the first answers before compiling, the second refuses naming the file, and the third deploys.
- [ ] Lane 5. Drop the session mid-book. Save `c12a-book.log`. Pass when readers see `book_state = rebuilding` and never a half book.
- [ ] Lane 6. Silence the socket past the heartbeat bound. Save `c12a-silent.log`. Pass when it reconnects and no entry is placed before the session is ready.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds from a closed bar to the order reaching the conformance venue.
- [ ] Probe. Lane 2.
- [ ] Baseline. QMB's handler time for the same bar in B5b's run.
- [ ] Rule. Fails when `deploy` takes 30 s or more to answer, the supervisor's call timeout.

**Review gate.** Lenses edge-case and adversarial, on order placement and protection. The blast-radius fact is that one handler serves QMB and the node, because the node's driver checks only the five hooks (`qmn/src/qmn/loop/driver.py:409-417`, Level 0 item 15).

@merge

## Reconcile with attribution and survive a network cut (C-12b)

Phase 5, the trading node and external connections. Part C slice C-12b, Part C AD-308, Level 0 AD-8 and AD-38, case TN-01. Ruling 27. Real step none. Done when the node reconciles at start and on every reconnect, tags each position mine, foreign, untagged or twin, and an unanswered send ends in UNKNOWN with no blind resend and exactly one position.

**Depends on.** C-12a.

**Files.**

- [ ] Create `qmn/src/qmn/app/reconciler.py`, `qmn/src/qmn/app/attribution.py`, `qmn/tests/test_app_attribution.py` and `qmn/tests/test_app_unknown_drill.py`.

**Build.**

- [ ] Write reconcile with the broker winning, attribution by the node's tag, and the UNKNOWN path, which reads open orders by client order id and positions by tag before anything is sent again.

**You see.**

- [ ] A position that is not the node's shows as "not ours, protected".

**Verify, unit.**

- [ ] A twin-tagged order stands the account down. An untagged position is protected and flagged. The drill (TN-01). The conformance venue drops the answer to a send, the node marks the stream UNKNOWN, reads open orders and positions, does not resend, and ends with exactly one position. Run `uv run pytest qmn/tests/test_app_attribution.py qmn/tests/test_app_unknown_drill.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The network-cut drill on the conformance venue. Save `c12b-drill.log`. Pass when the stream goes UNKNOWN, nothing is resent, and exactly one position exists after reconnect.
- [ ] Lane 3. A twin-tagged order on the account. Save `c12b-twin.log`. Pass when the account stands down with the twin alarm.
- [ ] Lane 4. An untagged position on the account at start. Save `c12b-untagged.log`. Pass when it is protected, flagged "not ours", and never adopted.
- [ ] Lane 5. Three reconnects in a row. Save `c12b-reconnects.log`. Pass when each runs one reconcile before entries resume.
- [ ] Lane 6. A position tagged by another node of his. Save `c12b-foreign.log`. Pass when it is left alone and reported.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from reconnect to entries allowed again.
- [ ] Probe. Lane 5.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on duplicates and reconnects. The blast-radius fact is that the kept reconcile and UNKNOWN organs pass their shipped `qmn` tests.

@merge

## Give each unit a paper lane and stand down safely (C-12c)

Phase 5, the trading node and external connections. Part C slice C-12c, Level 0 AD-38 (the stand-down table) and AD-39 (a paper lane per unit). Standing order 7 (the one automatic move is a risk rule stopping a unit, logged). Real step none. Done when a paper deployment sends no order and journals world `paper`, each stand-down row stops entries, keeps exits and broker stops and clears by its rule, and a risk stop lands one `lifecycle` event with `by: risk_rule` and waits for his click.

**Depends on.** C-12a.

**Files.**

- [ ] Create `qmn/src/qmn/app/paper_lane.py`, `qmn/src/qmn/app/stand_down.py`, `qmn/tests/test_app_paper_lane.py` and `qmn/tests/test_app_stand_down.py`.

**Build.**

- [ ] Write the paper lane with simulated fills and the stand-down table as data, each clearing value a named setting with Level 0 AD-38's starting default.

**You see.**

- [ ] The unit's journal shows its first paper trade.

**Verify, unit.**

- [ ] A paper deployment sends no order and journals its trades with world `paper`. Each stand-down row stops entries, keeps exits and broker stops, and clears by its rule. A risk stop lands one `lifecycle` event and waits for his click. Run `uv run pytest qmn/tests/test_app_paper_lane.py qmn/tests/test_app_stand_down.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A paper deployment of the dummy for a recorded day. Save `c12c-paper.log`. Pass when no order reaches the venue and every trade carries world `paper`.
- [ ] Lane 3. Each of the seven stand-down rows, table-driven. Save `c12c-standdown.log`. Pass when each stops entries, keeps exits and broker stops, and clears by its own rule.
- [ ] Lane 4. A risk rule firing. Save `c12c-riskstop.log`. Pass when one `lifecycle` event with `by: risk_rule` lands and entries stay stopped until a resume by `operator`.
- [ ] Lane 5. A health stop and a risk stop side by side. Save `c12c-words.log`. Pass when the status and journal use different words for each.
- [ ] Lane 6. The clock band. Save `c12c-clock.log`. Pass when entries resume only after 5 minutes inside the warn band.
@menu

**Verify, perf.**

- [ ] Metric. Seconds of a paper lane over one recorded day.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on the kill switch and stops. The blast-radius fact is that every stand-down keeps exits, broker stops and the kill switch working (Level 0 AD-38).

@merge

## Promote a unit and deploy it on his click only (C-23)

Phase 5, the trading node and external connections. Part C slice C-23, Part C AD-324 and `CONTRACTS.md` section 13, Level 0 AD-23, R1-C-01. Standing order 7 and ledger CC-11 ("nothing actually ever enters live without me"). Real step none. Done when the This PC host route `POST /api/units/promote` answers only to `operator`, records the move through the host's lifecycle writer, builds the deployment from the Library and asks `deploy` through the node link, and parks and retires ask `withdraw`.

**Depends on.** C-12a, C-12c, C-06, C-02, B13, B5b.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` (the route and the deployment builder) and `qmx-agents/packages/qmx-host/tests/test_promote.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (mounts the route beside the seal move).

**Build.**

- [ ] Write the route and the builder. A deployment names its files by fingerprint, the G `test-report`, the starting numbers (paper from the unit's defaults, live from the paper lane's last calibrated values and watermark) and the record snapshots. It is not a catalog row, so no agent can call it.

**You see.**

- [ ] "Promote to paper" on a tested unit, then the node shows the unit warming up. The button is the UI session's, and the route is ready for it.

**Verify, unit.**

- [ ] His principal promotes the dummy from tested to paper, which lands one lifecycle event and one deployment accepted on the conformance node with the G record's fingerprint and the unit's defaults. `agent:x` answers `refused_principal`. Draft to live answers `illegal_move`. A repeated op id lands nothing new. Paper to live carries the last values and watermark of fixture paper-lane calibration rows. A live move onto a live-world account on a host without the trading profile answers `trading_profile_off`, and one onto a demo account goes through. A park asks `withdraw`. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_promote.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Promote the dummy from tested to paper as `operator` on a throwaway folder with a conformance node. Save `c23-paper.log`. Pass when one lifecycle event lands and the node accepts one deployment with the G fingerprint and the unit's defaults.
- [ ] Lane 3. The same promote as `agent:x` and as `run:y`, and a draft-to-live move. Save `c23-refused.log`. Pass when the first two answer `refused_principal` and the third `illegal_move`.
- [ ] Lane 4. The same op id sent twice. Save `c23-repeat.log`. Pass when the second lands nothing new.
- [ ] Lane 5. Paper to live with fixture calibration rows, onto a demo account. Save `c23-live.log`. Pass when the deployment carries the last values and their watermark.
- [ ] Lane 6. A park of a paper unit. Save `c23-park.log`. Pass when the node is asked `withdraw` and the unit leaves the node.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from his click to the deployment accepted.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, because this is the only door toward live. The blast-radius fact is that his click is caller kind `user`, principal `operator` (`qmx_engine/service/context.py:59-70`).

@merge

## Let the node heal itself and keep risk stops through restarts (C-13)

Phase 5, the trading node and external connections. Part C slice C-13, Part C `NODE.md`, Level 0 AD-38. Ruling 35 (health checks, restarts with back-off, watchdogs, a desired state it keeps returning to). Real step none. Done when an inner supervisor restarts the runtime with back-off, 5 restarts in 10 minutes stand the node down alive, a frozen runtime exits so the supervisor restarts it with the kill level in force, and a risk stop survives every restart.

**Depends on.** C-12a, C-05a, A10.

**Files.**

- [ ] Create `qmn/src/qmn/app/healing.py` and `qmn/tests/test_app_healing.py`.
- [ ] Move `CrashLoopFold` into `qmn/src/qmn/app/healing.py` from its current module and repoint its callers in this PR, with no re-export left behind.

**Build.**

- [ ] Write the inner supervisor, the stuck detector and `safe_to_restart`, and restore each unit through `restore_unit`, which starts cold with a reason when needed (A10).

**You see.**

- [ ] The node card reads "Healing" with a line on its Heals list, then "Trading" again.

**Verify, unit.**

- [ ] An exception restarts the runtime. 5 restarts in 10 minutes stand down alive. A frozen runtime exits the process, and the supervisor restarts it with the kill level still in force. A risk stop survives a restart. Run `uv run pytest qmn/tests/test_app_healing.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Raise inside the runtime while the dummy trades on the conformance venue. Save `c13-restart.log`. Pass when the runtime restarts with back-off and trading resumes after reconcile.
- [ ] Lane 3. Five faults in 10 minutes. Save `c13-crashloop.log`. Pass when the node stands down alive and waits for his resume.
- [ ] Lane 4. Freeze the runtime. Save `c13-frozen.log`. Pass when the process exits, the supervisor restarts it, and the kill level is still in force.
- [ ] Lane 5. A restart during a risk stop. Save `c13-riskstop.log`. Pass when the stop survives and entries stay stopped.
- [ ] Lane 6. Ask for a restart while an order is in flight. Save `c13-safe.log`. Pass when `safe_to_restart` reads false until the order resolves.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from a fault to trading again.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on a heal undoing a stop. The blast-radius fact is that `CrashLoopFold`'s callers all moved in this PR, by grep.

@merge

## Bind the cTrader demo venue in the node (C-12d)

Phase 5, the trading node and external connections. Added by the validation of 2026-11-03 (`VALIDATION-2026-11-03.md`). Part C AD-306 and AD-307, Level 0 AD-37. Ruling 37. Built fact. the installed node opens with no venues (`qmn/src/qmn/app/server.py:204`, `open_node` called without `venues`), and `bind`, `sign_in_begin`, `sign_in_code` and `self_test` all answer `not_set_up` (`qmn/src/qmn/app/operations.py:467-476`). No slice built them, so no real trade is possible. Real step none; his demo sign-in is C-14's real run. Done when the installed node builds its cTrader venue from `NODE_KEYS` and a stored grant, the four operations work against a fake cTrader sign-in, `passport` returns the self-test checks, and under `QMX_STAGE=shadow` the node binds nothing.

**Depends on.** C-12c, C-13, C-11.

**Files.**

- [ ] Edit `qmn/src/qmn/app/operations.py` (real `sign_in_begin`, `sign_in_code`, `bind`, `self_test`; `passport` returns the self-test checks, `:698-713`) and `qmn/src/qmn/app/server.py` (venues from `NODE_KEYS` plus the grant; a conformance binding allowed only on a throwaway folder; nothing bound under `QMX_STAGE=shadow`).
- [ ] Create `qmn/src/qmn/app/grants.py` (the grant store, in Credential Manager as `qmx/node-<tag>-ctrader` on Windows, `data/grants/` on Linux; refresh through `qmn/src/qmn/secrets/rotation.py`; a live-capable grant discarded unless the host facts say trading profile on) and the adapter from `qmn/src/qmn/venue/live.py` `LiveCTraderClient` to the runtime's venue port.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py`. `_signed_in` (`:415`) names the session words that count as signed in, so an expired session does not unblock the self-test (C-11 review L2), and the keys step calls `rotate_keys` (C-11 review L3).
- [ ] Create `qmn/tests/test_app_grants.py` and `qmn/tests/test_app_binding.py`.

**Build.**

- [ ] The adapter passes `OrderTags` on every order, because the no-tags path writes the 75-character command fingerprint as cTrader's `clientOrderId`, past cTrader's 50 (`qmn/src/qmn/venue/live.py:931`, `packages/qmf-venue/src/qmf/venue/encode.py:522-528`; `LOOSE-ENDS.md` B1). A test sends a fake order and reads a `clientOrderId` of 50 characters or fewer.
- [ ] Write the grant store, the adapter and the four operations against a fake cTrader sign-in. No real account is touched. The demo account role stays the only one a live lane accepts (`runtime.py:2273-2276`).

**You see.**

- [ ] On the node, "cTrader demo, signed in" after his one sign-in on cTrader's own page, and a passport whose five self-test lines read ok.

**Verify, unit.**

- [ ] A fake sign-in binds a demo account, the venue reads ready in `status`, `self_test` lands all five `SELF_TEST_CHECKS` (`connect_node.py:75-81`) on the passport, an expired session keeps the self-test blocked, and `QMX_STAGE=shadow` binds nothing. Run `uv run pytest qmn/tests/test_app_grants.py qmn/tests/test_app_binding.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A throwaway folder, the installed node, a fake cTrader sign-in. Save `c12d-bind.log`. Pass when `status` reads the venue ready and a dummy-unit trade goes through `LiveCTraderClient` code to the fake, with its stop placed, seen and closed.
- [ ] Lane 3. The same folder under `QMX_STAGE=shadow`. Save `c12d-shadow.log`. Pass when no venue is bound and no grant is read.
- [ ] Lane 4. A grant refresh during a bound session. Save `c12d-refresh.log`. Pass when the new grant is stored before the old one is discarded and a second refresher is refused.
- [ ] Lane 5. A fixture live-capable grant with the host facts off. Save `c12d-livegrant.log`. Pass when it is discarded.
- [ ] Lane 6. Scan every lane output for grant values. Save `c12d-noleak.log`. Pass when none appears.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from a stored grant to the venue reading ready.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on a new order path and a new grant store. The blast-radius fact is that every QMX host keeps refusing live-capable grants in its own store (`qmx_broker/adapters.py:103-146`), unchanged.

@merge

## Make app installs pick up fresh source (C-26)

Phase 5, the trading node and external connections. Added by the validation of 2026-11-03. Built fact. a no-editable install runs stale `qmn` code after a source edit, because the wheel cache keys only on `pyproject.toml` (BACKLOG C-12a and the B14 fix round). C-14's real run and C-17's installs need the code he landed. Real step none. Done when an edit under `qmn/src` reaches a reinstalled app env without touching `pyproject.toml`.

**Depends on.** C-12a.

**Files.**

- [ ] Edit `qmn/pyproject.toml`, `qmb/pyproject.toml` and `qml/pyproject.toml` (`tool.uv.cache-keys` cover `src/**`).
- [ ] Create `tools/tests/test_app_env_fresh.py`.

**Build.**

- [ ] Add the cache keys and the test.

**You see.**

- [ ] Nothing new. An app runs the code that was landed.

**Verify, unit.**

- [ ] Edit a marker under `qmn/src`, reinstall the app env, and read the marker from the installed package. Run `uv run pytest tools/tests/test_app_env_fresh.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The trading node app installed on a throwaway folder, a source edit, a reinstall. Save `c26-fresh.log`. Pass when the installed node serves the edited code.
- [ ] Lane 3. A reinstall with no source change. Save `c26-cached.log`. Pass when the cache is reused.
- [ ] Lane 4. The same for `qmb`. Save `c26-qmb.log`. Pass when the edit reaches it.
- [ ] Lane 5. A reinstall after a `qml` source edit. Save `c26-qml.log`. Pass when the edit reaches it.
- [ ] Lane 6. The lock file before and after. Save `c26-lock.log`. Pass when `uv.lock` is unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for a reinstall with and without a source change.
- [ ] Probe. Lanes 2 and 3.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens verification-gap. The blast-radius fact is that `uv sync` at the root still resolves the same lock.

@merge

## Make app installs pick up fresh qmf source and deleted files (C-26b)

Phase 5, the trading node and external connections. Added by the loose-ends pass of 2026-11-03 (`LOOSE-ENDS.md` D1, a MUST before the first real trade; C-26 review HIGH). Built facts. the eight `qmf-*` packages (core, data, indicators, readings, registry, risk, structure, venue) keep uv's default cache keys (0 `cache-keys` in their `pyproject.toml`), and the trading-node lock installs them as wheels, so after a qmf edit a reinstalled node runs stale `qmf-risk` and `qmf-venue`, which are on the money path. A file deleted under `qmn`, `qmb` or `qml` stays in a reinstalled env, because the glob key takes the newest mtime. An app's `definition.hash` no longer pins what runs once path sources build the env (`qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py:474`). Real step none. Done when a qmf source edit and a deleted source file both reach a reinstalled app env, and the env's key covers the source it was built from.

**Depends on.** C-26.

**Files.**

- [ ] Edit `packages/qmf-core/pyproject.toml`, `qmf-data`, `qmf-indicators`, `qmf-readings`, `qmf-registry`, `qmf-risk`, `qmf-structure` and `qmf-venue` (`tool.uv.cache-keys` cover `src/**`), and the `qmn`, `qmb` and `qml` keys so a deletion changes the key (a key over the file list, not only the newest mtime).
- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` (`:474`, the env key folds in a fingerprint of every path source's files, so a changed source builds a new env).
- [ ] Edit `tools/tests/test_app_env_fresh.py`.

**Build.**

- [ ] Add the keys, the deletion rule and the env fingerprint, with tests.

**You see.**

- [ ] Nothing new. The node runs the risk and venue code that was landed.

**Verify, unit.**

- [ ] Edit a marker under `packages/qmf-risk/src`, reinstall the node env, and read the marker. Delete a fixture module under `qmn/src`, reinstall, and the import fails. An unchanged source reuses the env. Run `uv run pytest tools/tests/test_app_env_fresh.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The trading node on a throwaway folder, a `qmf-venue` edit, a reinstall. Save `c26b-qmf.log`. Pass when the installed node serves the edited code.
- [ ] Lane 3. A file deleted under `qmn/src`, a reinstall. Save `c26b-deleted.log`. Pass when the env no longer holds it.
- [ ] Lane 4. A reinstall with no change. Save `c26b-cached.log`. Pass when the env is reused.
- [ ] Lane 5. A `qmf-risk` edit reaching the QMB app env. Save `c26b-qmb.log`. Pass when the edit reaches it.
- [ ] Lane 6. The lock file before and after. Save `c26b-lock.log`. Pass when `uv.lock` is unchanged.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for a reinstall with and without a source change.
- [ ] Probe. Lanes 2 and 4.
- [ ] Baseline. C-26's lanes 2 and 3.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens verification-gap. The blast-radius fact is that `uv sync` at the root still resolves the same lock.

@merge


## Keep the node's position exact after partial fills, filled reads and reconnects (C-12e)

Phase 5, the trading node and external connections. Added by the loose-ends pass of 2026-11-03 (`LOOSE-ENDS.md` B2, B3, B4, MUSTs before the first real trade). Built facts. A partly filled entry books the unit's full size, because `Sent` carries no filled quantity (`qmn/src/qmn/app/runtime.py:540-543`), so exits and closes size from a wrong position. The reconciler treats a FILLED order with no price, or an UNKNOWN order missing from the read-back, as absent (`qmn/src/qmn/app/reconciler.py:207-220`), and cTrader's reconcile lists pending orders, not filled ones, so a filled entry outside the read-back leaves a tagged position no unit holds and the kill does not cover. After a feed reconnect the first entry can size from a quote held from before the drop, because `FeedKeeper._drop` resets the books but keeps `_quotes` (`qmn/src/qmn/app/feed_keeper.py:256, 347-352`). Real step none. Done when a partial fill books its filled size, an order resolves as absent only when no venue position carries its label (and a found one keeps the venue's position id), and no entry sizes from a quote older than the last reconnect.

**Depends on.** C-12d.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py` (`Sent` carries the filled quantity; the unit's position and every later exit read it), `qmn/src/qmn/app/reconciler.py` (`:207-220`, look up positions by the order's label before absent) and `qmn/src/qmn/app/feed_keeper.py` (`_drop` clears `_quotes`; an entry waits for a fresh quote after a reconnect).
- [ ] Create `qmn/tests/test_app_partial_fill.py`, `qmn/tests/test_app_reconcile_filled.py` and `qmn/tests/test_app_feed_reconnect.py`.

**Build.**

- [ ] Fix all three against the conformance venue and the fake cTrader. A partial fill's rest is not chased; the unit holds what filled.

**You see.**

- [ ] The node's position always matches cTrader's, including after a partial fill or a dropped feed.

**Verify, unit.**

- [ ] A fake that fills 0.03 of a 0.05 entry books 0.03, and the exit closes 0.03. A filled entry missing from the read-back is found by its label and adopted with the venue's position id. An order with no labelled position resolves absent. After a fake reconnect the first entry waits for a new quote. Run `uv run pytest qmn/tests/test_app_partial_fill.py qmn/tests/test_app_reconcile_filled.py qmn/tests/test_app_feed_reconnect.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The dummy unit on a throwaway folder against the fake cTrader with a partial fill. Save `c12e-partial.log`. Pass when the journal, `positions` and the fake's book all read the filled size.
- [ ] Lane 3. An entry the fake fills and leaves out of its pending list. Save `c12e-filled.log`. Pass when reconcile adopts it by label and the kill closes it.
- [ ] Lane 4. Drop the fake feed for 30 s while the quote moves 50 points, then restore it. Save `c12e-reconnect.log`. Pass when the first entry's stop distance comes from a quote after the restore.
- [ ] Lane 5. An UNKNOWN order with no labelled position. Save `c12e-absent.log`. Pass when it resolves absent and the market unblocks.
- [ ] Lane 6. The C-12a dummy trade, unchanged. Save `c12e-regress.log`. Pass when it trades exactly as at the parent.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for one reconcile pass with 20 orders.
- [ ] Probe. Lane 3.
- [ ] Baseline. The parent's reconcile pass.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on the money path. The blast-radius fact is that one handler serves QMB and the node, so QMB's backtest of the dummy reads exactly as at the parent.

@merge


## Encode cTrader stop amends as the price cTrader expects (C-37)

Phase 5, the trading node and external connections. Added from C-12d's review, 2026-11-03. Built fact. `encode_amend_protection` writes `stopLoss` and `takeProfit` with `_set_int` (`packages/qmf-venue/src/qmf/venue/encode.py:948-950`), but Spotware's release 91 `ProtoOAAmendPositionSLTPReq` declares both as doubles holding an absolute price. So every stop tightening and protection re-amend is refused at encode, and after three tries the order path closes the position. A stop never widens, but no unit can trail its stop on cTrader. Real step none. Done when an amend encodes `stopLoss` and `takeProfit` as the absolute price at the symbol's digits, the fake cTrader accepts a tightened stop, and the money path stays exact up to the wire.

**Depends on.** C-12d.

**Files.**

- [ ] Edit `packages/qmf-venue/src/qmf/venue/encode.py` (`:948-950`, a `_set_double` beside `_set_int` at `:336`; the level is the exact price rounded once at the symbol's digits, toward the position's side, and turned into a double only at the field write; a double that does not round-trip to the same digits is refused).
- [ ] Edit the fake cTrader in `qmn`'s tests so it reads `stopLoss` as a double, as cTrader does.
- [ ] Create `packages/qmf-venue/tests/test_encode_amend_double.py`.

**Build.**

- [ ] Fix the encoder against the release 91 proto in the repo. The place-order path's relative distances stay integers, as declared.

**You see.**

- [ ] A unit's trailing stop moves on cTrader instead of the position closing.

**Verify, unit.**

- [ ] An amend for EURUSD at 1.08345 and for XAUUSD at 2650.25 decodes back to exactly those prices as doubles. A level off the symbol's digits rounds toward the position's side. A tightened stop on the fake is accepted with no retry. Run `uv run pytest packages/qmf-venue/tests/test_encode_amend_double.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The dummy on a throwaway folder against the fake cTrader, a position opened and its stop tightened. Save `c37-tighten.log`. Pass when the amend is accepted on the first try and the position stays open.
- [ ] Lane 3. Ten tightenings in a row on one position. Save `c37-trail.log`. Pass when every one is accepted and the stop only moves toward the price.
- [ ] Lane 4. A take-profit amend. Save `c37-tp.log`. Pass when it is accepted at the exact price.
- [ ] Lane 5. A gold position's amend. Save `c37-gold.log`. Pass when the wire price has two decimals and matches the level.
- [ ] Lane 6. The C-12a dummy trade, unchanged. Save `c37-regress.log`. Pass when it trades exactly as at the parent.
@menu

**Verify, perf.**

- [ ] Metric. Microseconds per amend encode.
- [ ] Probe. Lane 3.
- [ ] Baseline. The parent's place-order encode.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap, on the money path and float exactness. The blast-radius fact is that the place-order encoder's bytes are unchanged.

@merge


## Make the node's status and kill tell the truth (C-35)

Phase 5, the trading node and external connections. Added by the loose-ends pass of 2026-11-03 (`LOOSE-ENDS.md` C1, a MUST before the first real trade, with B5 and the first part of C3 riding along because they are the same kill he sees). Built facts. The status word can read "Trading" while a risk stop or a narrow kill holds, because `_status` reads `target.level_at("all")` and lists only `repeated_fault` stand-downs (`qmn/src/qmn/app/operations.py:558-600`). A kill or pause at an `account` or `deployment_id` scope the node does not hold is accepted and does nothing. A hold at `instrument:<symbol>` never blocks an entry, because the guard checks `instrument:<market id>`, and a resume naming the symbol does not clear it. The node journals a kill rise but not his resume (`runtime.py:2060-2072`), so the watcher reads Well after 24 h though the kill may hold. Real step none. Done when the status word and reasons name every risk stop and every kill at any scope, a scope the node does not hold is refused with its reason, symbol and market id scopes mean the same market, and every resume is journalled.

**Depends on.** C-12d, C-13.

**Files.**

- [ ] Edit `qmn/src/qmn/app/operations.py` (`_status` reads every scope's level and every stand-down and risk stop; a kill, pause or resume at a scope the node does not hold answers `unknown_scope`), `qmn/src/qmn/app/runtime.py` (the guard and the resume map a symbol to its market id; the resume that lowers a kill is journalled beside the rise).
- [ ] Create `qmn/tests/test_app_status_truth.py` and `qmn/tests/test_app_kill_scopes.py`.

**Build.**

- [ ] One status word with every reason. A refused scope says which scopes the node holds.

**You see.**

- [ ] The node reads "Paused, risk stop on XAUUSD" or "Killed at EURUSD", never "Trading" while anything holds, and a kill on a market the node does not trade says so.

**Verify, unit.**

- [ ] A risk stop on one market reads in the word and the reasons. A RED at `instrument:XAUUSD` blocks an XAUUSD entry and reads in the word. A resume by symbol clears a hold set by market id. A kill at an unknown account answers `unknown_scope`. A resume journals one row. Run `uv run pytest qmn/tests/test_app_status_truth.py qmn/tests/test_app_kill_scopes.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The dummy on a throwaway folder, a risk stop forced on its market, then `status`. Save `c35-riskstop.log`. Pass when the word is not "Trading" and the reason names the market.
- [ ] Lane 3. A kill at `instrument:<symbol>`, then the next entry signal. Save `c35-symbol.log`. Pass when the entry is blocked.
- [ ] Lane 4. A kill at an account the node does not hold. Save `c35-unknown.log`. Pass when it answers `unknown_scope` and nothing changes.
- [ ] Lane 5. A kill, his resume, then the B21 watcher's read. Save `c35-resume.log`. Pass when the journal holds both rows and the watcher reads Well only after the resume.
- [ ] Lane 6. A kill at `all`, unchanged. Save `c35-all.log`. Pass when it closes everything as at the parent.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds per `status` call with 10 markets.
- [ ] Probe. Lane 2.
- [ ] Baseline. The parent's `status`.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses adversarial and edge-case, on the kill path. The blast-radius fact is that a kill at `all` acts exactly as at the parent.

@merge


## Land the venue, instrument and account records a deploy reads (C-34)

Phase 5, the trading node and external connections. Added by the loose-ends pass of 2026-11-03 (`LOOSE-ENDS.md` E1, the largest MUST before the first real trade). Built facts. promote reads `account`, `venue` and `instrument` items from the Library's main (`qmx-agents/packages/qmx-host/src/qmx_host/promote.py:355`, `:557`, `:606`), and nothing lands them there. The CCXT refresh template writes record files as run artifacts only, and no cTrader record source exists (no `ProtoOASymbolByIdReq` or account-list read in `packages/qmf-venue` or `qmn`). C-14's rehearsal tests seed items, so only his real run would find the gap. Main is moved by the operator, by an agent merge, or by the store's own engine with act `land` (`qmx-agents/packages/qmx-library/src/qmx_library/principal.py:72-74`). Real step none; his own sign-in in C-14's real run lands his real records. Done when, after a bind, the host lands one `account` record, one `venue` record and one `instrument` record per market he names, all read from cTrader by the node, with `world` as cTrader states it, and a promote of the dummy onto that account finds all three.

**Depends on.** C-12d, C-23, C-02.

**Files.**

- [ ] Edit `packages/qmf-venue/src/qmf/venue/ctrader.py` and `encode.py` (the account-list read with each account's live flag, `ProtoOATraderReq` for broker, deposit currency, leverage and position mode, and `ProtoOASymbolByIdReq` for digits, pip position, lot size and volume steps).
- [ ] Edit `qmn/src/qmn/venue/live.py` (the three reads) and `qmn/src/qmn/app/operations.py` (a `records` read operation answering the bound account's facts and each named symbol's facts, holding no secret).
- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/venue_records.py`. It maps the node's answer to the `account`, `venue` and `instrument` kinds' fields and lands them on main as the store's engine with act `land`, as a new version only when the facts changed. `world` comes from the venue's live flag, never from an argument.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` (after a passing self-test, land the records) and add a daily refresh job beside the records job.
- [ ] Create `qmn/tests/test_app_records.py` and `qmx-agents/packages/qmx-host/tests/test_venue_records.py`.

**Build.**

- [ ] cTrader only. The CCXT refresh template's run files are not landed here, because nothing binds a CCXT venue yet (`LOOSE-ENDS.md` G1); that stays in BACKLOG.
- [ ] A record carries no token, key or password, and the kinds refuse one at put.
- [ ] A demo account lands with `world: demo`. A live account read lands with `world: live`, and promote's live checks (C-21) still refuse it until his deliberate path.

**You see.**

- [ ] After his sign-in, his account, cTrader and each market he picked appear in the Library with their facts, and the promote card finds them.

**Verify, unit.**

- [ ] A fake cTrader answer lands one account record with `world: demo`, one venue record and one instrument record per named symbol, each passing its kind's checker. A second land with the same facts adds no version. A changed lot step adds one. A promote of the dummy onto the fake account builds its deployment. Run `uv run pytest qmn/tests/test_app_records.py -q` and `uv run --project qmx-agents pytest packages/qmx-host/tests/test_venue_records.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A throwaway folder, the node bound to the fake cTrader, the connect steps. Save `c34-landed.log`. Pass when main holds the three kinds with the fake's facts.
- [ ] Lane 3. A promote of the dummy onto that account. Save `c34-promote.log`. Pass when the deployment is built and its `snapshots` hold the three records.
- [ ] Lane 4. The daily refresh twice with no change. Save `c34-refresh.log`. Pass when no new version lands.
- [ ] Lane 5. The fake answering a live account. Save `c34-live.log`. Pass when it lands `world: live` and a live promote is refused `trading_profile_off`.
- [ ] Lane 6. Grep the landed records and every lane log for token, key and password values. Save `c34-noleak.log`. Pass when none appears.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from a passing self-test to the records on main, for five symbols.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses adversarial and edge-case, on authority over main and on `world`. The blast-radius fact is that no other kind lands on main by this path, and an agent still cannot land one.

@merge


## Let an installed node read its calendars and cTrader definitions, and come back after a host restart (C-38)

Phase 5, the trading node and external connections. Added from C-30's findings, his ruling of 2026-11-04 (`PLANNER-NOTE-2026-11-04.md` items 2 and 4). It lands in one PR with C-35 and C-29, on `build/us-c35`, so one builder and one reviewer take all three. Built facts. In an env built by `uv sync --no-editable`, `qmn/src/qmn/app/server.py:306-309` and `qmn/src/qmn/time/calendars.py:49` climb `parents[4]` to the env folder, so `bind` answers `definitions_missing` and `market_calendars()` is empty (`evidence/c30/findings-backlog.md`). `_market_calendar` also asks `qmb.data.gap_check.open_time` (`calendars.py:337`), whose `_EXTENSIONS` (`gap_check.py:801`, `:881`) climbs the same way, so both readers must change together. uv_build ships every file under a module's folder, and a built `qmf-calendar-forex` wheel and a built `qmx-broker` wheel were both opened and hold their data files. The trading node is not in `FIRST_APPS` (`qmx_host/first_start.py:600-602`), and `enable_first_party` reads only `first-party.json`, so after a host restart neither This PC nor a server starts the node again. Real step none. Done when, in envs built by `uv sync --no-editable`, the node finds every shipped calendar and its cTrader definitions, a bind on the fake cTrader passes, and a host restart starts the node and the MIS again on any machine where the connect steps enabled them.

**Depends on.** C-12d, C-26b.

**Files.**

- [ ] Move `openapi-91.pb`, `Spotware-LICENSE.txt` and `.gitattributes` from `qmx-agents/packages/qmx-broker/src/qmx_broker/protocol/` to `packages/qmf-venue/src/qmf/venue/protocol/` with `git mv`. `qmx-broker` already depends on `qmf-venue`, so one file serves both, and the node env gains no broker door, `ccxt` or `keyring`.
- [ ] Edit `qmn/src/qmn/app/server.py` (`:306-309`, `DEFINITIONS` beside the imported `qmf.venue` package), `qmx-agents/packages/qmx-broker/src/qmx_broker/service.py` (`:63`, `PROTOCOL_SET` the same way) and `packages/qmf-venue/tests/test_encode_amend_double.py` (`:49`).
- [ ] Edit `qmb/src/qmb/data/gap_check.py` (`:801`, `:881`). A new `calendar_files()` finds each `qmf.calendar_*` folder with `importlib.util.find_spec`, which works installed and editable and does not import the package, so `qmf.calendar_forex`'s import-time TZPATH check does not run and QMB still imports no extension. Edit `qmn/src/qmn/time/calendars.py` (`:49`, `:322`) to read the same `calendar_files()`.
- [ ] Edit `qmx-agents/apps/trading-node/pyproject.toml` and `uv.lock`, and `qmx-agents/apps/qmb/pyproject.toml` and `uv.lock` (the four `qmf-calendar-*` packages as dependencies and path sources), the four `extensions/qmf-calendar-*/pyproject.toml` (`tool.uv` `cache-keys` over `src/**`, as C-26b gave the qmf packages), and the root `pyproject.toml` and `uv.lock` (`calendar-tzdata` names all four, each with its workspace source and its `src` on the test path).
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/first_start.py` (`enable_first_party` finds an enabled app's folder in a table that includes the node; `FIRST_APPS` stays what a new folder starts with) and `connect_node.py` (`_enable`, `:523`, adds the names it started to `first-party.json` once its apps run, on both the PC and the server path).
- [ ] Create `tools/tests/test_app_env_data.py` and `qmx-agents/packages/qmx-host/tests/test_first_party_node.py`.

**Build.**

- [ ] This builds on C-30, already stacked below `build/us-c35`, whose status lines show a missing calendar.
- [ ] `qmx_engine/triggers/preflight.py:73` stays as it is, because the host runs from a checkout and the engine is his. QMB's `_FOREX_WEEK` stays too (`LOOSE-ENDS.md` A4).
- [ ] The restart fix adds no new mechanism. It is the one first-party list the host already reads at every start, and it touches no Library, replication or backup code.

**You see.**

- [ ] Signing in to cTrader works on the installed node, alarms follow market hours, and after a restart your node comes back by itself.

**Verify, unit.**

- [ ] `test_app_env_data.py` builds the node env with `uv sync --no-editable` and, from that env's Python, reads `fx-24x5@1` and `metals-24x5@1` from `market_calendars()`, loads the definitions and compiles them, and checks the file's sha256 is the pin `qmx-broker`'s test holds. It builds the QMB env and reads `open_time("metals-24x5@1")`. `test_first_party_node.py` enables the node through `_enable`, restarts a fake supervisor, and sees it started, with an existing `first-party.json` kept. Run `uv run pytest tools/tests/test_app_env_data.py -q`, `uv run --project qmx-agents pytest packages/qmx-host/tests/test_first_party_node.py packages/qmx-broker/tests/test_protocol_default.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Start a real host on a throwaway folder, install the node through the supervisor, and bind it to the fake cTrader. Save `c38-bind.log`. Pass when the answer is not `definitions_missing` and the venue reads ready.
- [ ] Lane 3. That node's `status` calendar lines. Save `c38-calendars.log`. Pass when no shipped calendar reads missing.
- [ ] Lane 4. Stop and start that host. Save `c38-restart.log`. Pass when the node and the MIS run again with no click and the node's bound venue comes back.
- [ ] Lane 5. A QMB run on a gold fixture in its installed env. Save `c38-qmb.log`. Pass when its hole count uses `metals-24x5@1`.
- [ ] Lane 6. A calendar file edited, the node reinstalled. Save `c38-fresh.log`. Pass when the edit reaches the env.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds for `market_calendars()` in the installed env.
- [ ] Probe. Lane 3.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap, on installed against checkout runs. The blast-radius fact is that `qmx-broker`'s pinned sha256 test still passes on the moved file and QMB imports no extension.

@merge


## Write the first real start as a script he runs (C-14)

Phase 5, the trading node and external connections. Part C slice C-14 (OP-02), Level 0 AD-37, R1-B-04. Ruling 37 (the sign-in waits until there is something to use it for, and only this step waits on it). The real step runs on his own folder after G-LAND and G-DEMO. Done when `tools/first_real_start.py` checks each fact and prints PASS or FAIL per line, passes in rehearsal on a throwaway folder against the conformance venue, and is ready for his real run.

**Depends on.** C-11, C-12a, C-12b, C-12c, C-12d, C-12e, C-13, C-23, C-26, C-26b, C-34, C-35, C-37, C-38, B15.

**Files.**

- [ ] Create `tools/first_real_start.py` and `tools/tests/test_first_real_start.py`.

**Build.**

- [ ] This is the PR after C-35, C-29 and C-38, which land together, so the deploy reads only the chosen market.
- [ ] Write the checks in order. Folder found, practice node Ready, demo session ready, a test trade with its stop placed, seen and closed, passport landed, and the practice node's real journal rows found in This PC's store through the records job, the open month within `[records] open_harvest_s` plus a minute.
- [ ] Give it a rehearsal mode on a throwaway folder against the conformance venue, and a real mode that refuses to run on a folder whose code he has not landed. The rehearsal installs the node through the supervisor, as his folder will, and lands its records through C-34's path rather than seeding them, because both gaps showed only on an installed node with an empty Library.
- [ ] The script talks only to the running host's REST. Node reads go through `POST /api/apps/trading-node/tools/{tool}` (`qmx_control/service.py:1879-1887`), with the bearer from Credential Manager. It imports nothing from `qmx-agents`, because the root env has no `qmx_home` or `qmx_host` and `tools/tests` runs in the root env (`tools/test_all.py:64`).
- [ ] Check the deploy through the node's `deployments` read (`operations.py:677`), never the promote answer, because `NodeLink.flush` settles a refused queued deploy silently (`node_link.py:450-468`).
- [ ] "Passport landed" means `<home>/trading-node-passport.json` (`connect_node.py:64`) holds every self-test check ok.
- [ ] "Code he has landed" means the host's source checkout (`connect_compute.source_revision`, `:139-150`) contains the commit on `origin/main` that added `tools/first_real_start.py`. There is no build stamp to compare (`/api/health` answers status, pid and read_only only, and the node's `BUILD` is the constant "0.1.0"), and he squash-merges, so stack SHAs never reach main.

**You see.**

- [ ] After he lands the stack and signs in once on cTrader's own demo page, his own practice node trades the dummy unit on his demo account.

**Verify, unit.**

- [ ] The script's checks on fixtures print one PASS or FAIL line each, and exit non-zero on any FAIL. Run `uv run pytest tools/tests/test_first_real_start.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Rehearsal on a throwaway folder against the conformance venue. Save `c14-rehearsal.log`. Pass when every line reads PASS.
- [ ] Lane 3. Rehearsal with the venue down. Save `c14-venuedown.log`. Pass when only the venue lines FAIL, each with one plain sentence, and the exit code is non-zero.
- [ ] Lane 4. Rehearsal journal timing. Save `c14-home.log`. Pass when the practice node's rows reach This PC's store within `[records] open_harvest_s` plus a minute.
- [ ] Lane 5. After G-LAND and G-DEMO, the real run on his folder. Save `c14-real.log`. Pass when every line reads PASS.
- [ ] Lane 6. Scan every output of lanes 2 to 5 for grant or token values. Save `c14-noleak.log`. Pass when none appears.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the rehearsal end to end.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and verification-gap. The blast-radius fact is that the real mode refuses a folder whose source checkout lacks the main commit that added the script.

@merge

## Prove attribution, duplicates and refresh on a cTrader demo account (C-15)

Phase 5, the trading node and external connections. Part C slice C-15, Part C `EXTERNAL.md` section 2, cases TN-01 and TN-05, R1-C-02. Ruling 37. The real probe run waits for G-DEMO. Done when the probe scripts print PASS or FAIL per mark, pass in rehearsal against the conformance venue, and are ready to prove `label` survival, repeated `clientOrderId` behaviour, attribution, the network-cut drill and the refresh drill on demo.

**Depends on.** C-14.

**Files.**

- [ ] Create `qmn/probes/ctrader_demo/` with `run.py` and one script per mark of `EXTERNAL.md` section 2.

**Build.**

- [ ] Write each mark with a rehearsal against the conformance venue and a demo run that reads its grant from the practice node's store only.

**You see.**

- [ ] Nothing new on screen. The passport gains "attribution proven on demo" and "refresh proven on demo" once the demo run passes.

**Verify, unit.**

- [ ] Each mark's rehearsal prints PASS on the conformance venue and FAIL with a reason when its fault is injected. Run `python qmn/probes/ctrader_demo/run.py --rehearsal`.

**Verify, live.**

@lane1
- [ ] Lane 2. Every mark in rehearsal. Save `c15-rehearsal.log`. Pass when every mark prints PASS.
- [ ] Lane 3. The refresh drill in rehearsal. Save `c15-refresh.log`. Pass when the new grant is stored before the old one is discarded, the session is ready again, and a second refresher is refused.
- [ ] Lane 4. The network-cut drill in rehearsal, socket closed right after a send. Save `c15-cut.log`. Pass when exactly one position exists after reconnect, with no resend.
- [ ] Lane 5. After G-DEMO, `python qmn/probes/ctrader_demo/run.py` on his demo account. Save `c15-demo.log`. Pass when every mark prints PASS.
- [ ] Lane 6. Scan the probe output for grant values. Save `c15-noleak.log`. Pass when none appears.
@menu

**Verify, perf.**

- [ ] Metric. Seconds per mark.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on duplicates and refresh. The blast-radius fact is QMN's one-refresher, store-before-discard rule (`qmn/src/qmn/secrets/rotation.py`).

@merge
