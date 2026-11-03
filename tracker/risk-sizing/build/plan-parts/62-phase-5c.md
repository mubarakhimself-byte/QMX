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

## Keep agents out of every grants folder (C-25)

Phase 5, the trading node and external connections. Added by the validation of 2026-11-03. BACKLOG "MUST FIX BEFORE C-17" (C-05e review HIGH). Built fact. `secret_paths()` drops the glob rules (`qmx_home/classes.py:119, 244`), and the agent file guard has no globs (`qma/harness/guard.py:438`), so an agent can read a grant under `data/apps/<app>/data/grants/`. Real step none. Done when an agent file read of any `data/apps/*/data/grants/*` path is refused on every role.

**Depends on.** C-05e.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-home/src/qmx_home/classes.py` (`secret_globs`), `qmx-agents/packages/qma-harness/src/qma/harness/guard.py` (`_secret` matches the globs) and the agent file tool in `qmx-agents/packages/qma-harness/src/qma/harness/tools.py` (`:918`).
- [ ] Create `qmx-agents/packages/qma-harness/tests/test_guard_secret_globs.py`.

**Build.**

- [ ] Carry the glob rules through `secret_paths()` and match them in the guard.

**You see.**

- [ ] Nothing new. A chat asked to open a grant is refused with one plain sentence.

**Verify, unit.**

- [ ] Reads of `data/apps/trading-node/data/grants/x` and `data/apps/other/data/grants/y` are refused, and a normal data file is allowed. Run `uv run --project qmx-agents pytest packages/qma-harness/tests/test_guard_secret_globs.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A throwaway folder with a fixture grant, a chat asked to read it. Save `c25-refused.log`. Pass when the read is refused and the grant's value never appears.
- [ ] Lane 3. The same through a workflow agent step. Save `c25-step.log`. Pass when it is refused.
- [ ] Lane 4. A case-folded and a `..` variant of the path. Save `c25-variants.log`. Pass when both are refused.
- [ ] Lane 5. A grant read through the copilot's terminal tool. Save `c25-terminal.log`. Pass when it is refused.
- [ ] Lane 6. Every path `secret_paths()` returned at the parent. Save `c25-parent.log`. Pass when each is still refused.
@menu

**Verify, perf.**

- [ ] Metric. Microseconds per guarded read.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses adversarial and edge-case, on path tricks. The blast-radius fact is that every path `secret_paths()` returned before still refuses.

@merge

## Set up a trading node on a server with the same checked steps (C-17)

Phase 5, the trading node and external connections. Part C slice C-17, Part C `NETWORKING.md` and AD-306, Level 0 AD-4, AD-44 and AD-45. Rulings 27 (Linux because servers are VPSs) and 35, and his words "A server can be a server." The server lane waits for G-SERVER. Done when the kind's server placement runs the shipped server steps, then chrony, the node and MIS apps, keys entered in the server's own window, the round trip and a self-test, the server's OpenObserve binds its Tailscale address, and the route, the node link and a run pass work across two real hosts.

**Depends on.** C-11, C-12a, C-12b, C-12c, C-12d, C-13, C-05d, C-05e, C-25, C-26.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` (server steps) and `qmx-agents/packages/qmx-host/deploy/openobserve.service` (`ZO_HTTP_ADDR`).
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_logs.py`. `monitoring_script` (`:475-508`) copies the unit files word for word, so it gains a render step that writes each server's own address.
- [ ] Edit `qmx-agents/packages/qmx-host/deploy/otelcol.service`. Its `OO_OTLP_ENDPOINT=http://127.0.0.1:5080` (`:26`) breaks once OpenObserve binds only the tailnet address.
- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` and `qmx-agents/packages/qmx-control/src/qmx_control/service.py` (`app_runtime`). `home_of` answers `pc` on a server (`supervisor.py:1333-1338`, BACKLOG C-06), and must answer its place name.
- [ ] Reuse these without editing them. `qmx_host/connect_compute.py` `server_of` (`:425`), `server_row` (`:244`) and the fake SSH seam `Ports.shell` (`:182-193`).
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_connect_node_server.py` and `tools/lanes/two_hosts.py`.

**Build.**

- [ ] Write the server steps rerun-safe, and the two-host lane script. Reuse `qmx_control.node.setup_steps` (`node.py:758-795`) and the compute kind's SSH, then add the new steps for chrony, OpenObserve and the apps. Every node step in `connect_node.py` today uses the local supervisor (`_apps` at `:192`, `_ask` at `:228`), and the host route has no install, sign or start verb (`host_route.py:45`). Adding one would be a spine amendment. So apps are installed over SSH against the server host's own loopback `/api/apps`, `/api/apps/{id}/publish` and `/start` (`service.py:1726, 1793`) with `trust=first_party`, and the PR body says how his signature reaches the server's road.
- [ ] The MIS joins `APP_FOLDERS` (`connect_node.py:73`; `qmx-agents/apps/mis` exists).
- [ ] The keys window writes `<server home>/vault/trading-node-keys` at mode 0600, read by `vault_secrets` (`host.py:1004-1030`). It is written before the node is enabled, because `NODE_KEYS` is read once at start (`server.py:208`).
- [ ] The round trip runs on the server over SSH. `_round_trip` (`:428`) measures from This PC.

**You see.**

- [ ] "London-1, Ready" on his PC, with its clock, its round trip to cTrader and its passport, once he rents and names a server and enters its keys in its own window.

**Verify, unit.**

- [ ] The steps rerun safely against a fake SSH runner. Run `uv run --project qmx-agents pytest packages/qmx-host/tests/test_connect_node_server.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The server steps against a fake SSH runner, killed and rerun at each step. Save `c17-steps.log`. Pass when every run converges on one place row.
- [ ] Lane 3. `tools/lanes/two_hosts.py` with two hosts on This PC (two loopback ports, two throwaway homes), each started as `python -m qmx_host serve --home <h> --port <p> --role server --place <n>` (`__main__.py:82-104`). Save `c17-twohosts.log`. Pass when heartbeats, `apps.ask status`, a queued pause, a PC-minted run pass reading data, and a deployment whose files reach the second home through the hub and stage before `deploy` all pass.
- [ ] Lane 4. The `openobserve.service` rendered by `monitoring_script`. Save `c17-bind.log`. Pass when `ZO_HTTP_ADDR` names the Tailscale address and never `0.0.0.0`.
- [ ] Lane 5. After G-SERVER, `tools/lanes/two_hosts.py` against his server in `/srv/qmx/check/c17/` as user `qmx`. Save `c17-server.log`. Pass when every check passes and the throwaway folder is removed after.
- [ ] Lane 6. A move snapshot of a node volume sent toward the second home. Save `c17-grants.log`. Pass when no file from `data/grants/` arrives.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for the two-host lane.
- [ ] Probe. Lane 3.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on cross-machine links. The blast-radius fact is Part C `BLAST-RADIUS.md` C9, a run pass minted on This PC parses at a server holding the same pairing key and is refused by an unpaired one. The reviewer also notes that a host pass is a shared HMAC, so any holder of the pairing key can mint any `from` and `principal`, `operator` included (`qmx_engine/service/forward.py:90-140`, lows B16). C-28 closes that before any live account.

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

**Depends on.** C-14, C-15, C-12d, C-12b, C-12c, C-13.

**Gate evidence.** The coordinator dispatches C-20 only when `c14-real.log` and `c15-demo.log` both exist and read all PASS. The Depends line alone is not enough, because "traded on demo" is evidence from G-DEMO, not a stacked PR.

**Files.**

- [ ] Delete `qmn/src/qmn/host/`, `qmn/src/qmn/seats/`, `qmn/src/qmn/promotion/`, `qmn/src/qmn/paper/`, `qmn/src/qmn/doors/`, `qmn/src/qmn/bench/` and `qmn/deploy/`, and every file in `qmn/src/qmn/observability/` except `liveness.py`, `alerts.py` and `_refuse.py`. `alerts.py:24` and `liveness.py:20` import `_refuse`. Rewrite `observability/__init__.py` (it imports health, logging and metrics at `:29,56,70`) to export only the kept three. `qmn/FAILURES.md` stays, because `alerts.py:249-251` reads it.
- [ ] Move the kept names into `qmn/src/qmn/app/`. Move `StandDownTrigger` (`qmn/host/_supervision.py:121`) and `allocate_writer_ids` (`boot_ceremony.py:448`). `CrashLoopFold` and `BootAttemptStamp` already moved in C-13 (`app/healing.py:97,116`). Delete `SafePointSnapshot` (`_supervision.py:623`), whose only user is a host test.
- [ ] Repoint and delete tests in `qmn/tests/`, including `test_qmn_time.py:19`, `test_qmn_roster.py:37` and `test_qmn_hygiene.py:23-34` (which also reads `qmn/deploy`).
- [ ] Repoint the kill line and bench fold, which still import Book paper's demotion (`qmn/src/qmn/capital/kill_line.py:38`, `qmn/src/qmn/capital/bench_fold.py:32`). Their only callers are in the old shell (`host/failure_campaign.py:74`, `golden_scenarios.py:86-92`).
- [ ] Edit `justfile`, which imports `./qmn/deploy/justfile-recipes/node.just` (CHECKED), so it still parses once `qmn/deploy/` is gone.
- [ ] Edit the other readers of `qmn/deploy`, which are `.github/workflows/qmn-ubuntu-24.04.yml:58-76`, `pyproject.toml:498`, `tools/build_release.py:264`, `release/install.py:454`, `tools/coverage_report.py:59`, `tools/tests/test_release_install.py:320,360-361`, `tools/tests/test_no_ip_literals.py:24` and `tools/backend-source-provenance.py:17`.
- [ ] Create `tools/import_scan.py`.

**Build.**

- [ ] Move callers first, then delete in the same PR, with no compatibility layer. The new node never calls the kill line. It acts through `PLACEHOLDER_KILL_EFFECTS` (`protection/effect_matrix.py:137`, `runtime.py:2078`), which the risk session replaces. After the cut a kill-line breach still acts through that labelled placeholder. No new entries for that binding, exits and broker stops untouched, a risk stop waiting for his resume (LC-X0-09).

**You see.**

- [ ] Nothing changes in what he uses, and about 47,000 fewer lines of old node code remain.

**Verify, unit.**

- [ ] `uv run pytest qmn/tests/test_protection_every_order.py -q` passes before and after. `python tools/import_scan.py` at the head shows no importer of a deleted module.

**Verify, live.**

@lane1
- [ ] Lane 2. `test_protection_every_order.py` at the parent and the head. Save `c20-protection.log`. Pass when it passes at both.
- [ ] Lane 3. `python tools/import_scan.py` at the head. Save `c20-imports.log`. Pass when no importer of a deleted module remains.
- [ ] Lane 4. Call `qmn.capital.apply_kill_line_breach` on a fixture binding. Save `c20-killline.log`. Pass when the package holds SUSPEND_NEW only (no FLATTEN), exits and broker stops are untouched, and resume needs the operator's signature (`kill_line.py:59`).
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

## Refuse the host's own pass in every app manifest (C-27)

Phase 5, the trading node and external connections. Added by the validation of 2026-11-03. BACKLOG TOP "his host bearer is reachable by an app manifest". Built fact. the bearer counts as `operator` (lows.md, B16 notes), so an app that declares it can promote to live. Real step none. Done when a manifest naming `qmx/CONTROL-TOKEN`, in any letter case, is refused on every role.

**Depends on.** C-05d.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py` (`:352-358`, the secret-name check is case-folded and the host's own names are refused).
- [ ] Create `qmx-agents/packages/qmx-apps/tests/test_manifest_host_secrets.py`.

**Build.**

- [ ] Add the refusal and its test.

**You see.**

- [ ] An app that asks for the host's own pass fails to install, with one plain sentence.

**Verify, unit.**

- [ ] `qmx/CONTROL-TOKEN`, `QMX/control-token` and the pairing key's name are each refused, and an app's own key is allowed. Run `uv run --project qmx-agents pytest packages/qmx-apps/tests/test_manifest_host_secrets.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. Install a fixture app that names the bearer on a throwaway folder. Save `c27-refused.log`. Pass when the install is refused and the app never starts.
- [ ] Lane 3. The same on a server-role throwaway home. Save `c27-server.log`. Pass when it is refused.
- [ ] Lane 4. Every shipped app manifest. Save `c27-shipped.log`. Pass when each still installs.
- [ ] Lane 5. A manifest naming the pairing key's name. Save `c27-pairing.log`. Pass when it is refused.
- [ ] Lane 6. A manifest naming its own app key. Save `c27-own.log`. Pass when it installs.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds per manifest check.
- [ ] Probe. Lane 4.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses adversarial and edge-case, on name tricks. The blast-radius fact is that every shipped app still installs.

@merge

## Give each host its own pass key (C-28)

Phase 5, the trading node and external connections. Added by the validation of 2026-11-03. lows B16. Built fact. one shared HMAC key mints and verifies every pass (`qmx_engine/service/forward.py:90-120`, `qmx_host/host_route.py:180-186`), so any paired machine can mint a pass that claims to come from This PC as `operator`. Real step none. Done when a pass that claims `operator` or `from = pc` verifies only if This PC's own key signed it, and each server's passes verify only with that server's key.

**Depends on.** C-17.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/service/forward.py` (a key per host, chosen by the pass's `from`) and `qmx-agents/packages/qmx-host/src/qmx_host/host_route.py` (pairing hands each server its own key, and This PC keeps every server's verify key).
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` (pairing writes the per-host key into that machine's store) and create `qmx-agents/packages/qmx-host/tests/test_host_pass_keys.py`.

**Build.**

- [ ] Write the per-host keys and re-pair the two-host lane on them. A shared-key pass is refused after the change.

**You see.**

- [ ] Nothing new. Pairing a server reads the same.

**Verify, unit.**

- [ ] A server's key cannot mint a pass that claims `pc` or `operator`. This PC's pass verifies at the server. A pass from an unpaired key is refused. Run `uv run --project qmx-agents pytest packages/qmx-host/tests/test_host_pass_keys.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. `tools/lanes/two_hosts.py` with per-host keys. Save `c28-twohosts.log`. Pass when every C-17 check still passes.
- [ ] Lane 3. The second home mints a pass claiming `pc` as `operator`. Save `c28-forged.log`. Pass when This PC refuses it.
- [ ] Lane 4. A pass signed with the old shared key. Save `c28-oldkey.log`. Pass when it is refused.
- [ ] Lane 5. After G-SERVER, the same forged pass from his server's throwaway folder. Save `c28-server.log`. Pass when it is refused.
- [ ] Lane 6. Re-pair the second home after a key change. Save `c28-repair.log`. Pass when its passes verify again and the old key is refused.
@menu

**Verify, perf.**

- [ ] Metric. Microseconds per pass verify.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses adversarial and edge-case, on forged passes. The blast-radius fact is Part C `BLAST-RADIUS.md` C9, rewritten. A pass minted on This PC verifies at a server, and a pass minted on a server cannot claim This PC.

@merge

## Deploy only the markets he chose, and show a refused deploy (C-29)

Phase 5, the trading node and external connections. Added by the validation of 2026-11-03. BACKLOG C-23 findings. Built facts. the node runs every market of a unit and ignores `deployment.markets` and `deployment.starting` (`qmn/src/qmn/app/runtime.py:1725`), so promote refuses `multi_market_live` and `already_deployed` (`qmx_host/promote.py:369, :441`), and `NodeLink.flush` settles a refused queued deploy silently (`node_link.py:450-468`). Real step none. Done when one market's promote deploys that market only, a second deployment of one version on another market works, and a refused queued deploy shows on his deploy row with its reason.

**Depends on.** C-23, C-12d.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py` (read `deployment.markets` and `deployment.starting`), `qmx-agents/packages/qmx-host/src/qmx_host/node_link.py` (a refused deploy lands as a refused deploy row) and `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` (drop the two refusals once the node reads the fields).
- [ ] Create `qmn/tests/test_app_deploy_markets.py` and `qmx-agents/packages/qmx-host/tests/test_node_link_refused.py`.

**Build.**

- [ ] Write the node's market read, the refused-deploy row, and remove the two stopgap refusals in the same PR.

**You see.**

- [ ] A unit promoted onto EURUSD alone trades EURUSD alone. A deploy the node refused reads "Refused" with its reason on the deployment.

**Verify, unit.**

- [ ] A two-market unit deployed on one market opens on that market only. A refused queued deploy lands a refused row. Run `uv run pytest qmn/tests/test_app_deploy_markets.py -q` and `uv run --project qmx-agents pytest packages/qmx-host/tests/test_node_link_refused.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. The dummy promoted onto XAUUSD only, on the conformance venue. Save `c29-onemarket.log`. Pass when no EURUSD order is sent.
- [ ] Lane 3. The same version deployed again on EURUSD. Save `c29-second.log`. Pass when both deployments trade their own market.
- [ ] Lane 4. A queued deploy the node refuses. Save `c29-refused.log`. Pass when the deployment row reads refused with the node's reason.
- [ ] Lane 5. A promote onto a demo account with `starting` set. Save `c29-starting.log`. Pass when the unit starts from that state.
- [ ] Lane 6. A restart of the node during a one-market deployment. Save `c29-restart.log`. Pass when it comes back on that market only.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from his click to the first bar on the chosen market.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on a deploy trading markets he did not choose. The blast-radius fact is that promote's click-only rule is unchanged, and only his click deploys.

@merge

## Let alarms read the market calendar and new keys (C-30)

Phase 5, the trading node and external connections. Added by the validation of 2026-11-03. BACKLOG C-18 findings. Built facts. the node starts its alarm senders with `no_calendar` (`qmn/src/qmn/app/server.py:209`), so `open_at` reads every market as shut and only protection escalation and a long clock hold push (`alarms.py:477`). `NODE_KEYS` is read once at start (`server.py:208`), so a new ntfy or Healthchecks key needs a restart. Real step none. Done when a risk stop inside an open session pushes once, a stale feed on a Saturday sends nothing, and `rotate_keys` re-reads the alarm senders.

**Depends on.** C-18, C-12d.

**Files.**

- [ ] Edit `qmn/src/qmn/app/server.py` (pass the calendars from `qmn/src/qmn/time/calendars.py`), `qmn/src/qmn/app/alarms.py` (`open_at` reads them) and `qmn/src/qmn/app/operations.py` (`rotate_keys` re-reads the senders, `:477`).
- [ ] Create `qmn/tests/test_app_alarms_calendar.py`.

**Build.**

- [ ] Wire the calendar and the key re-read.

**You see.**

- [ ] His phone buzzes for a risk stop during London hours, and stays quiet for a stale feed at the weekend.

**Verify, unit.**

- [ ] A risk stop on a Tuesday at 10:00 London pushes once. A stale forex feed on Saturday sends nothing. After `rotate_keys` the sender uses the new key. Run `uv run pytest qmn/tests/test_app_alarms_calendar.py -q`.

**Verify, live.**

@lane1
- [ ] Lane 2. A risk stop on the conformance venue inside an open session, with a stub ntfy endpoint. Save `c30-open.log`. Pass when one message arrives.
- [ ] Lane 3. The same at a weekend clock. Save `c30-weekend.log`. Pass when nothing is sent for a stale feed.
- [ ] Lane 4. Rotate the ntfy key while the node runs. Save `c30-rotate.log`. Pass when the next alarm uses the new key without a restart.
- [ ] Lane 5. A risk stop one minute after Friday's forex close. Save `c30-close.log`. Pass when the stale-feed alarm stays quiet and the risk stop still pushes.
- [ ] Lane 6. The Healthchecks key rotated. Save `c30-liveness.log`. Pass when pings continue on the new key.
@menu

**Verify, perf.**

- [ ] Metric. Milliseconds per `open_at` read.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lens edge-case, on session boundaries. The blast-radius fact is that the alert publisher's closed push list is unchanged (`qmn/src/qmn/observability/alerts.py:45-49`).

@merge

## Build the deliberate path to bind a live account (C-21)

Phase 5, the trading node and external connections. Part C slice C-21, Part C AD-307, Level 0 AD-45, lead's call LC-X0-08 (two soaks shown, never enforced). Ledger CC-11 and CC-13. No live account is ever bound in this program. Real step none. Done when the connect dialog's "bind a live account" steps turn chats and agent steps off first and set `[host] trading_profile = true`, the node keeps a live-capable grant only then, and the binding card shows the two soaks.

**Depends on.** C-17, C-18, C-12d, C-25, C-27, C-28, C-29, C-30.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/connect_node.py` (the bind-live steps; today it has only `on_this_pc` at `:568` and the alarms at `:702`).
- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/trading_profile.py` (refusals for chats and agent steps) and `qmx-agents/packages/qmx-host/tests/test_trading_profile.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/host.py`. Chat routes mount unconditionally (`:1150`), and the host facts hard-code `chats` and `agent_steps` to True (`:1672-1673`). This PC's refusal of the profile already exists (`:1666`).
- [ ] Edit `qmx_host/promote.py`, `qmx_host/host_route.py` and `qmx_host/node_link.py`. The trading-profile check (`host.py:1184-1188`) needs `place == name`, so This PC never sees a server's profile, and every live-world move answers `trading_profile_off` (`promote.py:360-365`). The server's profile must reach This PC through the node link.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py:55-76`, which has no `host` section (BACKLOG C-05c).
- [ ] Edit `qmn/src/qmn/app/runtime.py` (`:2273-2276, 2283`) and `qmn/src/qmn/app/server.py` (`:50`, WORLD is DEMO). Keeping or discarding a live-capable grant, and reading the host facts on every reconcile tick (AD-307), is node code. First add a test that pins today's demo-only gate (C-12c review L1), then change it.
- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/runner.py` (`placed()`, `:215-242`) so an agent step placed on a home in the trading profile is refused. This is a workflow-engine change, so it waits for his go (ruling 49; see `VALIDATION-2026-11-03.md`).

**Build.**

- [ ] Write the steps and the refusals. Every test uses a fixture grant and a fixture account. Going live is his click.
- [ ] The soak card's "time done" comes from the first demo deploy row of the binding's account (24 hours) and of the unit version (one week). Nothing enforces either.

**You see.**

- [ ] "Bind a live account" ends with the soak card, and going live stays his click.

**Verify, unit.**

- [ ] With the profile on, a chat route is not mounted and an agent step placed there is refused. This PC refuses the setting. A live-capable grant is discarded when the host facts say off and kept when on. Run `uv run --project qmx-agents pytest packages/qmx-host/tests/test_trading_profile.py -q`.

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
