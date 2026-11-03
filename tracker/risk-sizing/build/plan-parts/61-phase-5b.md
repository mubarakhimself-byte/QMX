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

## Write the first real start as a script he runs (C-14)

Phase 5, the trading node and external connections. Part C slice C-14 (OP-02), Level 0 AD-37, R1-B-04. Ruling 37 (the sign-in waits until there is something to use it for, and only this step waits on it). The real step runs on his own folder after G-LAND and G-DEMO. Done when `tools/first_real_start.py` checks each fact and prints PASS or FAIL per line, passes in rehearsal on a throwaway folder against the conformance venue, and is ready for his real run.

**Depends on.** C-11, C-12a, C-12b, C-12c, C-12d, C-13, C-23, C-26, B15.

**Files.**

- [ ] Create `tools/first_real_start.py` and `tools/tests/test_first_real_start.py`.

**Build.**

- [ ] Write the checks in order. Folder found, practice node Ready, demo session ready, a test trade with its stop placed, seen and closed, passport landed, and the practice node's real journal rows found in This PC's store through the records job, the open month within `[records] open_harvest_s` plus a minute.
- [ ] Give it a rehearsal mode on a throwaway folder against the conformance venue, and a real mode that refuses to run on a folder whose code he has not landed.
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
