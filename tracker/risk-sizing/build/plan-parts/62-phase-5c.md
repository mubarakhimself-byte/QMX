## Trade Hyperliquid through CCXT on testnet (C-16)

Phase 5, the trading node and external connections. Part C slice C-16, Part C `EXTERNAL.md` section 3, Level 0 AD-41. Rulings 28 and 39 (Hyperliquid's link designed, CCXT handles everything). The testnet probe run waits for G-WALLET. Done when the `ccxt` venue client, `VenueClientKind.ccxt`, the position-trigger protection form, `cloid` tags, the open-order margin and the agent wallet in the keys document exist, and the client maps every CCXT error, with an unmapped one read as UNKNOWN.

**Depends on.** C-12a, C-12b.

**Files.**

- [ ] Create `qmn/src/qmn/venue/ccxt_client.py`, `qmn/tests/test_ccxt_client.py` and `qmn/probes/hyperliquid_testnet/`.
- [ ] Edit `qmn/src/qmn/venue/port.py` (the venue kind list opens to `ccxt`, `:40-45`) and `qmn/src/qmn/order/protection.py`.

**Build.**

- [ ] Write the client through the pinned CCXT class first. A native client comes only if the testnet probe fails, and that is logged as a finding, not built.

**You see.**

- [ ] A Hyperliquid testnet binding on the practice node, once he approves a testnet agent wallet on Hyperliquid's own page.

**Verify, unit.**

- [ ] The mapping against a fake exchange with CCXT's method names. An unmapped error is UNKNOWN with an alarm. Run `uv run pytest qmn/tests/test_ccxt_client.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Orders, positions and fills against a fake exchange with CCXT's method names. Save `c16-mapping.log`. Pass when each maps to the venue port's shape.
- [ ] Lane 3. An error code the client does not know. Save `c16-unknown.log`. Pass when the stream goes UNKNOWN and an alarm is raised.
- [ ] Lane 4. Every order kind the node sends. Save `c16-cloid.log`. Pass when each carries the node's `cloid` and its position-trigger protection.
- [ ] Lane 5. After G-WALLET, `python qmn/probes/hyperliquid_testnet/run.py`. Save `c16-testnet.log`. Pass when every mark of `EXTERNAL.md` section 3 prints PASS.
- [ ] Lane 6. The open-order margin on a fixture account. Save `c16-margin.log`. Pass when it matches the fixture's stated value.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds per mapped call against the fake exchange.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on a new order path. The blast-radius fact is that the cTrader client passes its shipped `qmn` tests with the venue kind list opened.

@merge

## Set up a trading node on a server with the same checked steps (C-17)

Phase 5, the trading node and external connections. Part C slice C-17, Part C `NETWORKING.md` and AD-306, Level 0 AD-4, AD-44 and AD-45. Rulings 27 (Linux because servers are VPSs) and 35, and his words "A server can be a server." The server lane waits for G-SERVER. Done when the kind's server placement runs the shipped server steps, then chrony, the node and MIS apps, keys entered in the server's own window, the round trip and a self-test, the server's OpenObserve binds its Tailscale address, and the route, the node link and a run pass work across two real hosts.

**Depends on.** C-11, C-12a, C-12b, C-12c, C-13, C-05d, C-05e.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` (server steps) and `qmx-agents/packages/qmx-host/deploy/openobserve.service` (`ZO_HTTP_ADDR`).
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_connect_node_server.py` and `tools/lanes/two_hosts.py`.

**Build.**

- [ ] Write the server steps on the shipped step runner, rerun-safe, and the two-host lane script.

**You see.**

- [ ] "London-1, Ready" on his PC, with its clock, its round trip to cTrader and its passport, once he rents and names a server and enters its keys in its own window.

**Verify, unit.**

- [ ] The steps rerun safely against a fake SSH runner. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_connect_node_server.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The server steps against a fake SSH runner, killed and rerun at each step. Save `c17-steps.log`. Pass when every run converges on one place row.
- [ ] Lane 3. `tools/lanes/two_hosts.py` with two hosts on This PC (two loopback ports, two throwaway homes). Save `c17-twohosts.log`. Pass when heartbeats, `apps.ask status`, a queued pause, a PC-minted run pass reading data, and a deployment whose files reach the second home through the hub and stage before `deploy` all pass.
- [ ] Lane 4. The rendered `openobserve.service`. Save `c17-bind.log`. Pass when `ZO_HTTP_ADDR` names the Tailscale address and never `0.0.0.0`.
- [ ] Lane 5. After G-SERVER, `tools/lanes/two_hosts.py` against his server in `/srv/qmx/check/c17/` as user `qmx`. Save `c17-server.log`. Pass when every check passes and the throwaway folder is removed after.
- [ ] Lane 6. A move snapshot of a node volume sent toward the second home. Save `c17-grants.log`. Pass when no file from `data/grants/` arrives.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the two-host lane.
- [ ] Probe. Lane 3.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on cross-machine links. The blast-radius fact is Part C `BLAST-RADIUS.md` C9, a run pass minted on This PC parses at a server holding the same pairing key and is refused by an unpaired one.

@merge

## Wake him through his phone when it matters, and ping a liveness watcher (C-18)

Phase 5, the trading node and external connections. Part C slice C-18, Part C `DEVOPS-CLOCKS.md`, Level 0 AD-42, lead's call LC-X0-10. Ruling 35 (monitoring). Real step none. Done when the kept alert publisher delivers its short list to an ntfy topic, the kept liveness ping reaches a Healthchecks.io check, both have setup cards, alarms fire only inside open calendars, and a failed send never touches trading.

**Depends on.** C-12a, C-11.

**Files.**

- [ ] Create `qmn/src/qmn/app/alarms.py` (adapters over the kept `qmn/src/qmn/observability/alerts.py` and `liveness.py`) and `qmn/tests/test_app_alarms.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` (the two setup cards, with a test send).

**Build.**

- [ ] Write the two adapters. Each destination's key sits in that machine's store. Both are on once he names a destination at setup.

**You see.**

- [ ] A test notification on his phone during setup, once he names his ntfy topic.

**Verify, unit.**

- [ ] A protection escalation reaches a stub ntfy endpoint with priority 5. A weekend stale feed sends nothing. A failed send is counted and trading continues. Run `uv run pytest qmn/tests/test_app_alarms.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A protection escalation on the conformance venue with a stub ntfy endpoint. Save `c18-escalation.log`. Pass when one message with priority 5 arrives.
- [ ] Lane 3. A stale feed on a Saturday for a forex unit. Save `c18-weekend.log`. Pass when nothing is sent.
- [ ] Lane 4. The ntfy stub refusing every send. Save `c18-failed.log`. Pass when the failures are counted and trading continues.
- [ ] Lane 5. The liveness ping to a stub Healthchecks endpoint, then stop the node. Save `c18-liveness.log`. Pass when pings arrive on cadence and stop when the node stops.
- [ ] Lane 6. The setup card's test send to the stub. Save `c18-card.log`. Pass when the stub receives one test message.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from an escalation to the stub receiving it.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that the alert publisher's closed push list is unchanged (`qmn/src/qmn/observability/alerts.py:45-49`).

@merge

## Update a server's node and MIS at a safe moment (C-19)

Phase 5, the trading node and external connections. Part C slice C-19, Level 0 AD-6 and lead's call LC-X0-15, case CA-06. Ruling 35. The server lane waits for G-SERVER. Done when a node or MIS version published on This PC installs on the server from its Library replica at a safe point, host builds update through the step runner only while `safe_to_restart`, and a contract mismatch refuses new deployments while trading goes on.

**Depends on.** C-17.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/app_updates.py` and `qmx-agents/packages/qmx-host/tests/test_app_updates.py`.

**Build.**

- [ ] Write the update job over the Library hub and the step runner, both opened by This PC.

**You see.**

- [ ] "Update London-1", with "waiting for a safe moment" while trades are open.

**Verify, unit.**

- [ ] Two homes on one machine. A version replicated to the second installs with its expected hash. A mismatched contract version refuses new deployments and keeps trading (CA-06). Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_app_updates.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Two throwaway homes on This PC, a node version published on the first. Save `c19-install.log`. Pass when the second installs it with the expected hash.
- [ ] Lane 3. A version with a mismatched contract version. Save `c19-mismatch.log`. Pass when new deployments are refused and the running unit keeps trading.
- [ ] Lane 4. An update asked while an order is in flight. Save `c19-safe.log`. Pass when it waits until `safe_to_restart` is true.
- [ ] Lane 5. After G-SERVER, the same install on his server's throwaway folder. Save `c19-server.log`. Pass when it installs with the expected hash.
- [ ] Lane 6. Roll back to the previous version. Save `c19-rollback.log`. Pass when the previous version runs and its signature still holds.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from publish to installed on the second home.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that nothing connects into This PC, since This PC opens the hub and the step runner (Level 0 AD-44).

@merge

## Cut the old node shell once the new one has traded on demo (C-20)

Phase 5, the trading node and external connections. Part C slice C-20, Part C AD-323, Level 0 AD-36, case TN-34. Ruling 27 ("We might delete a lot of code, in fact, a fresh start"). It waits for G-DEMO, because nothing is deleted before its replacement passes. Real step none. Done when the kept names have moved, their tests are repointed, `qmn.host`, `seats`, `promotion`, `paper`, `doors`, `bench`, the rest of `observability`, the deploy recipes and the Grafana stack are deleted with their tests, and the stop-on-every-order test passes before and after.

**Depends on.** C-14, C-12b, C-12c, C-13.

**Files.**

- [ ] Delete `qmn/src/qmn/host/`, `qmn/src/qmn/seats/`, `qmn/src/qmn/promotion/`, `qmn/src/qmn/paper/`, `qmn/src/qmn/doors/`, `qmn/src/qmn/bench/` and `qmn/deploy/`, and every file in `qmn/src/qmn/observability/` except `liveness.py` and `alerts.py`.
- [ ] Move the kept names into `qmn/src/qmn/app/`, repoint and delete tests in `qmn/tests/`, and repoint the kill line and bench fold, which import Book paper's demotion (`qmn/src/qmn/capital/kill_line.py:38`, `qmn/src/qmn/capital/bench_fold.py:32`).
- [ ] Edit `justfile`, which imports `./qmn/deploy/justfile-recipes/node.just` (CHECKED), so it still parses once `qmn/deploy/` is gone.
- [ ] Create `tools/import_scan.py`.

**Build.**

- [ ] Move callers first, then delete in the same PR, with no compatibility layer. After the cut a kill-line breach acts through a labelled placeholder. No new entries for that binding, exits and broker stops untouched, a risk stop waiting for his resume (LC-X0-09).

**You see.**

- [ ] Nothing changes in what he uses, and about 47,000 fewer lines of old node code remain.

**Verify, unit.**

- [ ] `uv run pytest qmn/tests/test_protection_every_order.py -q` passes before and after. `python tools/import_scan.py` at the head shows no importer of a deleted module.

**Verify, live.**

@lane1
- [ ] Lane 2. `test_protection_every_order.py` at the parent and the head. Save `c20-protection.log`. Pass when it passes at both.
- [ ] Lane 3. `python tools/import_scan.py` at the head. Save `c20-imports.log`. Pass when no importer of a deleted module remains.
- [ ] Lane 4. A kill-line breach on a fixture binding. Save `c20-killline.log`. Pass when entries stop for that binding, exits and broker stops stay, and a risk stop waits for `operator`.
- [ ] Lane 5. `just --list` at the head. Save `c20-justfile.log`. Pass when it parses and lists the recipes.
- [ ] Lane 6. Count the removed lines. Save `c20-lines.log`. Pass when the count is recorded in the PR body.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for `uv run pytest qmn/tests -q`.
- [ ] Probe. Lane 2's suite run at the parent and the head.
- [ ] Baseline. The parent's time, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, because a deletion can remove a protection. The blast-radius fact is Level 0 item 5's caller scan, every caller outside and inside `qmn` moved before the deletion.

@merge

## Build the deliberate path to bind a live account (C-21)

Phase 5, the trading node and external connections. Part C slice C-21, Part C AD-307, Level 0 AD-45, lead's call LC-X0-08 (two soaks shown, never enforced). Ledger CC-11 and CC-13. No live account is ever bound in this program. Real step none. Done when the connect dialog's "bind a live account" steps turn chats and agent steps off first and set `[host] trading_profile = true`, the node keeps a live-capable grant only then, and the release and binding cards show the two soaks.

**Depends on.** C-17, C-18.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` (the bind-live steps).
- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/trading_profile.py` (refusals for chats and agent steps) and `qmx-agents/packages/qmx-host/tests/test_trading_profile.py`.

**Build.**

- [ ] Write the steps and the refusals. Every test uses a fixture grant and a fixture account. Going live is his click.

**You see.**

- [ ] "Bind a live account" ends with the soak card, and going live stays his click.

**Verify, unit.**

- [ ] With the profile on, a chat route is not mounted and an agent step placed there is refused. This PC refuses the setting. A live-capable grant is discarded when the host facts say off and kept when on. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_trading_profile.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A throwaway server-role home with the profile on. Save `c21-profile.log`. Pass when no chat route is mounted and an agent step placed there is refused.
- [ ] Lane 3. Set the profile on This PC. Save `c21-thispc.log`. Pass when the setting is refused.
- [ ] Lane 4. A fixture live-capable grant with the host facts off, then on. Save `c21-grant.log`. Pass when it is discarded when off and kept when on.
- [ ] Lane 5. The binding card. Save `c21-soak.log`. Pass when it shows 24 hours and one week with time done, and does not block his click.
- [ ] Lane 6. Unbind. Save `c21-unbind.log`. Pass when chats and agent steps come back on that home.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the bind steps on a throwaway home.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, because agents must never work where a live key lives. The blast-radius fact is that every QMX host keeps refusing live-capable grants in its own store (`qmx_broker/adapters.py:103-146`), unchanged.

@merge

## Let the node read the MIS board, with a fallback (C-22)

Phase 5, the trading node and external connections. Part C slice C-22, Part C `MIS.md`, Level 0 AD-2 and AD-40. A Should. Standing order 10 (units stand alone). Real step none. Done when a host feed relay passes the `mis` instance's landed board to the node's `[feeds.board]`, and a unit with a placement read uses it with `stale_after` and falls back to every admitted market.

**Depends on.** C-09, C-12a.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/feed_relay.py` and `qmx-agents/packages/qmx-host/tests/test_feed_relay.py`.
- [ ] Edit the node's feed handling in `qmn/src/qmn/app/runtime.py`.

**Build.**

- [ ] Write the relay and the node's board read with its fallback.

**You see.**

- [ ] On the node, which of a unit's markets the board favours now. The node page is the UI session's, and the copilot can read it from the node's status.

**Verify, unit.**

- [ ] A landed board reaches the node. A stale board makes the unit use every admitted market. Run `uv run pytest qmx-agents/packages/qmx-host/tests/test_feed_relay.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A board landed by the MIS app on a throwaway folder with a conformance node. Save `c22-relay.log`. Pass when the node reads it within its `stale_after`.
- [ ] Lane 3. Let the board go stale. Save `c22-stale.log`. Pass when the unit uses every admitted market.
- [ ] Lane 4. Stop the MIS app. Save `c22-standalone.log`. Pass when the node keeps trading.
- [ ] Lane 5. The node's `status` operation. Save `c22-status.log`. Pass when it names the markets the board favours now.
- [ ] Lane 6. A board for a market the unit is not admitted on. Save `c22-admitted.log`. Pass when the unit ignores it.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds from a landed board to the node reading it.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case. The blast-radius fact is that a unit stands alone, so a down MIS never stops it (Level 0 AD-2).

@merge
