# Contracts: every shape Part C owns or consumes

Field by field, with the version rule, matched against `architecture/01-connections.md` (the master). Version rules use the master's codes: V-S (a `schema_version`, fields addable, meanings fixed, readers read every version they support and keep an old one for the 90-day overlap window), V-K (a Library kind's schema file), V-P (a call pinned to `(app, version)`), V-CT (a CT contract format version, unknown refused), V-H (both sides state contract versions on connect), V-L (a pinned library or descriptor). Types: `str`, `int`, `bool`, `ts` (ISO-8601 UTC text), `ns` (UTC nanoseconds), `exact` (QMF exact decimal text), `id` (a stable id), `fp` (`fp1:sha256:...`). A field marked `?` is optional.

## 1. The host route `POST /api/host/forward` (owner P0; V-S, V-H)

**Request** (header `X-QMX-Host-Pass` carries the pass; no bearer):

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | str | `qmx.host.forward/1` |
| `verb` | str | one of `apps.ask`, `apps.job`, `heartbeats`, `data.list`, `data.fetch` |
| `args` | object | the verb's arguments below |
| `op_id` | id? | the caller's id for this ask; a repeated id answers its first result (for `apps.ask` on `manage` operations, required) |

**Answer:** `{schema_version, ok: true, value}` or `{schema_version, ok: false, code, message, next_step?}`. Codes: `bad_pass`, `wrong_engine`, `expired_pass`, `no_verb`, `refused_principal`, `not_home`, `not_running`, `pin_stale`, `files_missing` (a deployment names files this machine's Library does not hold yet; `value` lists their fingerprints, and This PC's outbox retries), `app_refused` (the operation's own refusal is inside `value`), `budget_exceeded`.

| Verb | `args` | `value` |
| --- | --- | --- |
| `apps.ask` | `app` str, `operation` str, `arguments` object, `pin` `{pack, version}`? | the operation's answer (§2); an ask to the trading node goes through this host's node link, which stages a deployment's files first (spine AD-303) |
| `apps.job` | `app`, `job`, `inputs` object?, `pin`?, `profile`? | the supervisor's `run_job` document (`qmx_apps/supervisor.py:986-1040`), with the job's `result` once Part B's B1 adds it; `inputs` reach the job as B1 designs |
| `heartbeats` | `subjects` list? | `{latest: {subject: row}, host_history: [row], clock: clock facts}`; rows as JSON, read tolerantly (unknown fields kept, never refused) |
| `data.list` | `after` watermark (`{store_sequence}`), `kinds` list?, `subjects` list?, `confirmed` list of `fp`? | `{partitions: [{key, fingerprint, bytes, frozen, born_on, committed_at}], watermark}`; `confirmed` fingerprints are recorded as held by This PC, and the server's door unpins them; this part's route accepts the argument, and Part B's B16 builds the pin and the one `verify` call in this handler |
| `data.fetch` | `fingerprint` | the file's bytes, streamed, with `X-QMX-Fingerprint` and `X-QMX-Key` headers |

Principal rules: an `apps.ask` of an operation whose manifest approval is `manage` answers only when the pass principal is `operator`. An `apps.job` for an app whose manifest `risk` is `money` (`qmx_apps/manifest.py:175`) answers only when the pass principal is `operator`; an agent or a workflow may start jobs on every other app. The principal rides the pass and never an argument. The trading node declares no job, and a test pins that.

Matches connections §3 X1, X2, X3, X7 and §5 row "AD-46 verbs". `data.list`'s `confirmed` argument, `apps.job`'s `inputs` and its money rule are changes (listed below).

## 2. Node operations (owner P12; V-P; every operation `state = "instance"`)

Every answer: `{ok: true, value}` or `{ok: false, code, message, next_step?}`. Every `manage` operation takes `op_id` (id) and `issued_at` (ts), and answers its first result again for a repeated `op_id`. Both are required when the call passes a node link, which sets `issued_at` from its host's clock; a call that reaches the node another way (a chat on This PC, through the harness) may omit them, and the node mints the op id and stamps `issued_at` on arrival. The node applies changes in arrival order and answers `{ok: false, code: "superseded", value: {newer_op_id}}` to a change whose `issued_at` is older than the newest change it applied for the same scope, except `kill` and `flatten`, which always apply.

| Operation | Approval | Arguments | `value` |
| --- | --- | --- | --- |
| `status` | domain_write (read) | none | node state (§4) |
| `units` | domain_write (read) | `deployment_id`? | `[unit_state]` (§4) |
| `positions` | domain_write (read) | `account`? | `[{account, instrument, side, quantity exact, average_price exact, owner_tag, deployment_id?, protection: {kind, price exact, seen_at ts}?}]` |
| `journal_tail` | domain_write (read) | `after_sequence` int, `streams` list? | `{rows: [envelope records], next_sequence}`; read with Part B's committed reader, never the shipped CT-13 reader, which can cut a line the writer is still writing (Part B X1B-NEW-1) |
| `passport` | domain_write (read) | none | passport (§4) |
| `deployments` | domain_write (read) | none | `[deployment summary]` |
| `deploy` | manage | `op_id`, `deployment` (§3) | `{deployment_id, state: "accepted"}` |
| `withdraw` | manage | `op_id`, `deployment_id`, `when: "flat"` | `{state: "accepted"}` |
| `pause`, `resume` | manage | `op_id`, `scope: {all | account | deployment_id | instrument}` | `{state, open_causes: [..]}` for `resume` |
| `kill` | manage | `op_id`, `level` (YELLOW to BLACK), `scope` | `{level_in_force}` |
| `flatten` | manage | `op_id`, `scope` | `{state: "accepted", positions: n}` |
| `bind` | manage | `op_id`, `account` record snapshot, `action: "add" | "remove"` | `{world: "demo" | "live", state}` |
| `confirm_same_node` | manage | `op_id` | `{identity}` |
| `take_over` | manage | `op_id`, `old_tag`, `confirmed_gone: true` | `{adopted: [position ids]}` |
| `sign_in_begin` | manage | `op_id`, `venue: "ctrader"`, `redirect` | `{url, expires_in}` |
| `sign_in_code` | manage | `op_id`, `code` | `{accounts: [{account, is_live}], kept: bool, reason?}` |
| `self_test` | manage | `op_id`, `account` (a demo binding) | `{state: "accepted"}` |
| `rotate_keys` | manage | `op_id` | `{state: "accepted"}` |

Provides: `node_state` (`stale_after` 120), `unit_states` (`stale_after` 120). Matches connections §2 C26 and §3 X1, X7 with the operation-list change below.

## 3. The deployment document (owner P12; V-S, schema `qmx.node.deployment/1`)

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | str | `qmx.node.deployment/1` |
| `deployment_id` | id | minted on This PC by the promote action (§13), derived from its op id |
| `node` | `{tag, install_id}` | the one node it names; any other node refuses it |
| `unit` | `{id, version}` | the Library unit |
| `unit_document` | object | the `qmx.unit/1` document (Part A) |
| `compiled_fingerprint` | fp | from the recorded G result for this unit version |
| `g_record` | `{id, version, compiled_fingerprint}` | the `test-report` with `check: qml-g/1` (Part A `CONTRACTS.md` §3.3), landed by Part B's `behaviour_check` |
| `files` | `[{entry_id, version, fingerprint, path, kind: "block" \| "entry" \| "weights", bytes}]` | every file of the pinned block folder (Part A `CONTRACTS.md` §6), each a Library component's code or face or a weights blob, named, never inlined; the home's node link stages them into `data/deployments/<deployment_id>/in/` of the node's volume before `deploy`, and the node writes `lock.json` from this list |
| `starting` | `{source: "defaults" \| "paper_lane", values: {name: exact}, watermark?}` | the numbers the unit starts from: defaults on the paper lane; on the live lane the paper lane's last calibrated values and the watermark of the calibration rows they came from (spine AD-324) |
| `markets` | `[{market_id, instrument: {id, version, fingerprint}}]` | admitted markets |
| `account` | `{id, version, fingerprint}` | the account record |
| `snapshots` | `[record content]` | every instrument, venue and account record named above |
| `lane` | `"paper" \| "live"` | world stamping per Level 0 AD-27 |
| `lifecycle_event` | id | the event his click wrote (Part A `CONTRACTS.md` §8) |
| `placeholders_acknowledged` | bool | his acknowledgement on a live lane with placeholder blocks |
| `created_by`, `created_at` | str, ts | principal (`operator`) and time |

No size limit: the document holds only small JSON, and files of any size travel apart from it. `deploy` refuses a file that is missing from the staging folder or whose fingerprint differs, naming the file.

## 4. Node state, unit state, passport, identity (owner P12; V-S)

**Node state** (`status`, `provides.node_state`): `schema_version` `qmx.node.state/1`; `word` (Setting up, Starting, Ready, Trading, Healing, Paused, Stopped by a risk rule, Stopped by a health check); `reasons` list; `identity {install_id, tag, machine_fingerprint, minted_at, mismatch bool}`; `clock` (§5); `venues [{venue, environment, session: "ready" | "connecting" | "not_set_up" | "down", since, last_contact ts}]`; `units {trading, warming, paused, stopped}`; `kill_level`; `safe_to_restart {ok bool, reasons}`; `contracts {route, operations, deployment, reading}` versions; `build`; `disk {free_bytes, guard_bytes}`; `last {decision_per_unit, quote_per_symbol, journal_write}` (health is progress); `at`.

**Unit state**: `deployment_id`, `unit {id, version}`, `per_market [{market_id, state, warm_up {done, needed}?, last_decision ts?, last_trade ts?, today_r exact?}]`, `world`, `placeholders` list, `stand_downs` list.

**Passport**: `schema_version` `qmx.node.passport/1`; `identity`; `checks [{name, ok bool, value, at}]` for broker session, feed freshness, demo test trade with its stop placed, observed and closed, kill-switch latency, clock band, disk, image digest; `round_trip [{venue, median_ms, spread_ms, samples}]`; `grants [{venue, expires_at}]`; `agent_wallets [{address, expires_at}]`; `at`.

## 5. Host facts, clock facts, the keys document (owner P0 and P12; V-S)

**Host facts** (`road/host/facts.json` in every supervised app's volume, written only by the host, before the app starts and on change): `schema_version` `qmx.host.facts/1`, `placement`, `role` (`pc`, `node`, `server`), `trading_profile` bool, `chats` bool, `agent_steps` bool, `holdout` `{on bool, boundary "YYYY-MM"?, months int?}` (the Settings `[data]` default seal the market-data door applies, `qmx_host/market_data.py:1232-1255`), `at`.

**Clock facts** (heartbeat `clock`, node `status.clock`): `zone` (IANA), `offset_ms` int, `delay_ms` int, `source` str, `source_kind` (`ntp`, `chrony`, `w32time`), `synced` bool, `tzdata` str, `band` (`ok`, `warn`, `no_new_entry`, `halt`)?, `probed_at`.

**Keys document** (`qmx/trading-node-keys`, a secret, never logged): `schema_version` `qmx.node.keys/1`; `ctrader {client_id, client_secret}`?; `hyperliquid [{address, agent_key, expires_at, subaccount?}]`?; `alarms {ntfy_topic_url?, healthchecks_ping_url?}`.

## 6. The internal market event format (owner P14; V-S)

Every source is normalised by the feed keeper into one of four events. All prices `exact`; all times `ns`.

| Event | Fields |
| --- | --- |
| `print` | `market_id`, `instrument`, `venue_time`?, `receive_time`, `price`, `size`, `aggressor` (`buy`, `sell`, `unknown`), `trade_id`?, `source_level` (4 for a tape) |
| `quote` | `instrument`, `venue_time`?, `receive_time`, `bid`?, `ask`?, `bid_size`?, `ask_size`?, `filled_side` (which side this event carried; the other is the last known) |
| `book` | `instrument`, `receive_time`, `levels [{side, price, size}]`, `kind` (`snapshot`, `delta`), `book_state` (`rebuilding`, `ready`) |
| `bar` | `instrument`, `period`, `open_time`, `close_time`, OHLC, `volume`? (only from a tape), `tick_count`, `basis` (`bid`, `ask`, `mid`, `trade`), `closed` bool |

## 7. The stamped reading record (owner P13; V-S; kind `reading` under Part B's envelope)

| Field | Type |
| --- | --- |
| `reading` | `{id, version, fingerprint}` |
| `source` | `node` or `mis` |
| `machine` | the writing place |
| `market_id`, `instrument` | str |
| `tier` | `tick`, `bar`, `session`, `day`, `calendar` |
| `time_base` | `clock`, `ticks`, `volume` |
| `value` | exact? |
| `percentile` | exact? (against the market's own usual for that minute of its session) |
| `word` | str? (from the reading card's words) |
| `health` | `fresh`, `stale`, `degraded`, `thin`, `shadow`, `retired` |
| `data_level`, `fallback_step` | int (a level of Part A's `qmx.data-level/1`), int (0 when none taken) |
| `estimate` | str? (`broker-side` for cTrader order-flow estimates) |
| `inputs_received_at` | ns |
| `computed_at` | ns |
| `stale_after_s` | int |
| `corrects` | id? (a correction links the record it replaces) |

`source` and `machine` sit in the body, because Part B's envelope has no source field (R1-B-07); Part B's partition subject for `journal-readings` includes both, and `world` is stamped by Part B's envelope. The series key is (source, reading id@version, tier, market id, instrument, machine); each (reading, tier) pair has one writer kind.

## 8. The MIS app (owner P13; V-P, V-S)

`configure` (domain_write, `state = "instance"`): `{op_id, markets: [{market_id, instrument snapshot}], packs: [{id, version}], shadow: [{reading id, version}]}` answers `{configured: n, refused: [{market_id, reason}]}`. `status` (domain_write read): runner state, per-reading health, last computed per market. Provides `board` (`stale_after` per tier): `{tier, at, markets: [{market_id, states: {reading id: word}}]}`.

## 9. Records (owner P4; V-K)

Kind files `instrument.schema.json`, `venue.schema.json`, `account.schema.json`, each with `schema_version`; exact keys in `RECORDS.md` §2, which carry every key Part A's `CONTRACTS.md` §2.3 reads under the same name, and one class enum spelled with underscores. Snapshots inside deployments carry each record's content, id@version and fingerprint.

## 10. Alarms and liveness (owner P12; V-S)

The kept `AlertPayload` (`failure_id`, `alert_class` in the closed push list, `summary`, `correlation_id`?, `authorizes: false`) plus `node_tag`, `at`, `calendar_open` bool; delivered by the ntfy channel as one POST with `Title`, `Priority` (5 for node down and protection escalation, 4 otherwise) and the summary as body. The liveness ping is an HTTPS GET to the Healthchecks.io ping URL with no body.

## 11. Capability declaration additions (owner `packages/qmf-venue`; V-L, addable)

Per venue and order type: `protective_stop_form` (`entry-relative`, `position-trigger-after-fill`); `trigger_basis` (`mark`, `last`); `open_orders_cap`; `action_budget`; `unattended` (`allowed`, `manual_login`, `server_banned`); `needs_desktop_app` bool; `sandbox` (`demo`, `testnet`, none).

## 12. The core read rows `instrument_get` and `readings_query` (owner P4 and P13; V-S; connections C15)

Two `domain_fn` rows, approval `read`, each in its own new core toolset (`instrument`, `readings`), so no shipped per-server tool count moves (`qmx-tools/tests/test_tools.py:374-376`); the harness serves them once Part A's slice A8 derives its domain groups from the catalog (`qma-harness/src/qma/harness/tools.py:641`, `:668`). On the default copilot surface and every workflow step that declares the toolset. Both read This PC's own stores and never ask a node.

| Row | Arguments | Answer |
| --- | --- | --- |
| `instrument_get` | `market_id` or `{venue, symbol}`; `at` ts? (default now); `version`? | `{record: content, id, version, fingerprint, status}` for the version in force at `at`; or `{ok: false, code: "not_found", nearest: [ids]}` |
| `readings_query` | `reading` id, `version`?, `markets` list?, `tier`?, `source`?, `from` ts, `to` ts (both required), `limit` (default 200), `cursor`?, `response_format` (`concise`, `detailed`) | `{rows: [§7 records], next_cursor?, data_ends_at}`; rows come from the `journal-readings` partitions Part B's records job harvested, the open month included; a window past the data says where the data stops (`data_ends_at`) |

## 13. The promote action (owner P0; V-S; schema `qmx.units.promote/1`)

A host route on This PC, `POST /api/units/promote`, beside the seal move and answering, like it, only to the principal `operator` (`qmx_host/market_data.py:1201-1210`, CHECKED); it is not a catalog row, so no agent sees it.

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | str | `qmx.units.promote/1` |
| `op_id` | id | his click's id; a repeat answers the first result |
| `unit` | `{id, version}` | the unit version |
| `market_id` | str | the market the move is for |
| `to` | `paper`, `live`, `parked`, `retired` | the lifecycle state his click chooses |
| `clears` | id? | the stop event a move out of `stopped` clears (Part A `CONTRACTS.md` §8) |
| `node`, `account` | `{tag}`, `{id}` | where it trades (moves to `paper` or `live`) |
| `placeholders_acknowledged` | bool? | his tick when placeholders remain on a live move |

**Answer:** `{ok: true, value: {lifecycle_event_id, deployment_id?, node_answer: "accepted" | "queued"}}` or `{ok: false, code, message, next_step}`. Codes: `refused_principal`, `illegal_move` (Part A's `fold` refuses it, with its reason), `no_g_record`, `no_record`, `node_not_ready`, `trading_profile_off` (a live move onto a live-world account on a host without the trading profile), `placeholders_unacknowledged`.

## Shapes this part consumes

| Shape | Owner | Used where | Rule |
| --- | --- | --- | --- |
| Unit document `qmx.unit/1`, its `reads` list with fallbacks | Part A | deployment `unit_document`; runtime | V-S |
| `construct_unit`, `HostedUnit`, `UnitStep` (the unit door) | Part A (`CONTRACTS.md` §4.1, §4.2) | the node runtime hosts every unit through it, never `construct_bot` | V-S |
| The one shared unit handler over `run_slice` (`qmb/src/qmb/host/unit_handler.py`) | Part B (slice B5b) | the node runtime imports it; no second handler | V-S |
| CT-23 format 3 sized intent | Part A | the order path, step 1 | V-CT |
| Reading card schema | Part A | the reading runner | V-S |
| The data-level vocabulary `qmx.data-level/1` | Part A (`CONTRACTS.md` §5.2) | instrument records' `data_levels`; reading records' `data_level`; the default packs | V-S |
| The block loader and the pinned block folder layout | Part A | runtime compile; reading runner; the deployment's `files` | V-S |
| The G `test-report` and compiled fingerprint | Part A (shape), Part B (`behaviour_check` lands it) | deploy refusal; the promote action | V-S |
| The lifecycle event body and `qml.lifecycle.fold` | Part A (`CONTRACTS.md` §8, slice A9) | the node's risk stops; through Part B's writer below | V-S |
| The host lifecycle writer `qmx_host/lifecycle.py` `record_move(event) -> event_id` | Part B (`CONTRACTS.md` §3, slice B13) | the promote action records his click through it | V-S |
| The committed reader (reads LF-terminated lines, never writes) | Part B (slice B8) | `journal_tail`; any read of a live stream other than its writer's | V-S |
| Journal envelope and kinds (`lifecycle`, `state`, `node_lifecycle`, `reading`); the writer library; the row-id record id for unit-journal rows | Part B | node and MIS append stores; a re-run slice writes no double rows | V-S |
| The records job: the one harvester of every append store on its machine (sealed journal months; the open month of bars and of reading history every `[records] open_harvest_s`, 60; ticks every `[records] tick_harvest_s`, 3,600), and the pull job | Part B (slices B15, B16) | X3; the MIS node instance's bars; `readings_query` | V-S, V-K |
| CT-18, CT-19, CT-20 | `packages/qmf-venue` | the venue-client port | V-CT |

## Matched against the master

| Master row | Status |
| --- | --- |
| C12 | change, Part A's (its contract change 4): units are hosted through `construct_unit` and `HostedUnit`; the node imports Part B's one unit handler |
| C13, C21, C22, C26, C27 (wording, see CF-1), C28, C29 | match |
| C15 (`readings_query`, `instrument_get`) | defined here (§12) |
| C23 (MIS node instance reads the store through the door's `read`) | change: apps reach the store through `QMX_MARKET_ROOT`, read-only, skipping months the host facts' `holdout` seals (below) |
| C24 (MIS writes partitions `source = mis`, records, `provides.board`) | match, through Part B's writer library |
| C25 (unit reads the board) | deferred to slice C-22; fallback holds |
| X1 (operation list; the deployment) | change (below): the operation list; a deployment names its files by fingerprint; his click reaches it through the promote action (§13) |
| X2, X4, X5, X7, X8 | match |
| X3 | change: `data.list` carries `confirmed` (below) |
| X6 | match; the known gap rechecked (`NETWORKING.md` §3) |
| X10 | match; the install path designed (`NETWORKING.md` §4) |
| E1, E3, E4, E5, E7, E9, E10, E11, E12 | match |
| E8 | change: the node's two sign-in operations named (below) |
| §5 shapes owned by Level 1 C | defined here (§1 to §9) |

## Contract changes (for the master's writer; this part does not edit `01-connections.md`)

1. **X1 operation list.** Replace `mode` with `bind` (the venue proves demo or live) and add `withdraw`, `confirm_same_node`, `sign_in_begin`, `sign_in_code`, `self_test`, `rotate_keys`. Reason: a separate mode duplicates `bind`; identity and sign-in need their own operations (CF-3).
2. **X3 confirmation.** `data.list` gains an optional `confirmed` list; the server's door pins node-born partitions until This PC lists them (CF-5, accepted by R1 over Part B's watermark). Part B builds the door change in its slice B16.
3. **C23 path.** The `mis` app reads its machine's store through `QMX_MARKET_ROOT`, which the supervisor gives only to apps declaring `data_reads = ["market"]`; the door stays the only writer (CF-4); the app skips every month the host facts' `holdout` seals (R1-C-13).
4. **C27 wording.** On Linux the node's grant store is an owner-only file in its volume, keeping QMN's rotation rule, not QMN's systemd-credential store (CF-1); that folder is machine-bound: no backup sends it and no volume move carries it (spine AD-306, R1-C-14).
5. **E8.** The node's trading sign-in is the operations `sign_in_begin` and `sign_in_code`, reached locally or through `apps.ask`; This PC's loopback receiver relays only the code.
6. **New row C31** (renumbered from this part's C30, since Part B's lander row takes C30, R1 B-CC10). Host facts: the host writes `road/host/facts.json` into each app volume; the node reads it before keeping a live grant (spine AD-307); the `mis` app reads its `holdout`.
7. **New row C32** (renumbered from C31). The host ships app logs from volumes into OTLP when `send_to` is on (spine AD-321).
8. **Heartbeat rows across machines** are read tolerantly; the host row gains an optional `clock` field (§5).
9. **Part B's records job** (settled by R1, R1-B-02): it is the one harvester of every append store on its machine (sealed journal months, the open month of bars and of reading history every `[records] open_harvest_s`, default 60, ticks every `[records] tick_harvest_s`, default 3,600). Part B builds it in B15; this part consumes it.
10. **X1 deployment.** The deployment document names its files by fingerprint and holds no size limit; the node's home stages them from its own Library, which the hub (X5) fills on a server (R1-C-06).
11. **C15 rows.** `instrument_get` (toolset `instrument`) and `readings_query` (toolset `readings`), §12 (R1-C-03).
12. **AD-46 `apps.job`.** It carries optional `inputs`; the principal rides the pass; it refuses any principal but `operator` for a `money` app (R1 B-CC8, R1-C-12).
13. **X1 his click.** His promotion click on This PC is the promote action (§13): it writes the lifecycle event and asks `deploy` through the node link (R1-C-01).
