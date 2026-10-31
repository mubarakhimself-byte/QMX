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

**Answer:** `{schema_version, ok: true, value}` or `{schema_version, ok: false, code, message, next_step?}`. Codes: `bad_pass`, `wrong_engine`, `expired_pass`, `no_verb`, `refused_principal`, `not_home`, `not_running`, `pin_stale`, `app_refused` (the operation's own refusal is inside `value`), `budget_exceeded`.

| Verb | `args` | `value` |
| --- | --- | --- |
| `apps.ask` | `app` str, `operation` str, `arguments` object, `pin` `{pack, version}`? | the operation's answer (§2) |
| `apps.job` | `app`, `job`, `pin`?, `profile`? | the supervisor's `run_job` document (`qmx_apps/supervisor.py:986-1040`) |
| `heartbeats` | `subjects` list? | `{latest: {subject: row}, host_history: [row], clock: clock facts}`; rows as JSON, read tolerantly (unknown fields kept, never refused) |
| `data.list` | `after` watermark (`{store_sequence}`), `kinds` list?, `subjects` list?, `confirmed` list of `fp`? | `{partitions: [{key, fingerprint, bytes, frozen, born_on, committed_at}], watermark}`; `confirmed` fingerprints are recorded as held by This PC |
| `data.fetch` | `fingerprint` | the file's bytes, streamed, with `X-QMX-Fingerprint` and `X-QMX-Key` headers |

Principal rule: an `apps.ask` of an operation whose manifest approval is `manage` answers only when the pass principal is `operator`.

Matches connections §3 X1, X2, X3, X7 and §5 row "AD-46 verbs". `data.list`'s `confirmed` argument is a change (listed below).

## 2. Node operations (owner P12; V-P; every operation `state = "instance"`)

Every answer: `{ok: true, value}` or `{ok: false, code, message, next_step?}`. Every `manage` operation takes `op_id` (id) and answers its first result again for a repeat.

| Operation | Approval | Arguments | `value` |
| --- | --- | --- | --- |
| `status` | domain_write (read) | none | node state (§4) |
| `units` | domain_write (read) | `deployment_id`? | `[unit_state]` (§4) |
| `positions` | domain_write (read) | `account`? | `[{account, instrument, side, quantity exact, average_price exact, owner_tag, deployment_id?, protection: {kind, price exact, seen_at ts}?}]` |
| `journal_tail` | domain_write (read) | `after_sequence` int, `streams` list? | `{rows: [envelope records], next_sequence}` |
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
| `deployment_id` | id | minted on This PC |
| `node` | `{tag, install_id}` | the one node it names; any other node refuses it |
| `unit` | `{id, version}` | the Library unit |
| `unit_document` | object | the `qmx.unit/1` document (Part A) |
| `compiled_fingerprint` | fp | from the recorded checker-G verdict for this unit version |
| `g_verdict` | `{id, version, fingerprint}` | the verdict record (Part A) |
| `blocks` | `[{id, version, fingerprint, path}]` | the pinned block folder (Part A's loader layout) |
| `calibration` | `{values, watermark}` | calibrated numbers and the journal watermark they came from |
| `markets` | `[{market_id, instrument: {id, version, fingerprint}}]` | admitted markets |
| `account` | `{id, version, fingerprint}` | the account record |
| `snapshots` | `[record content]` | every instrument, venue and account record named above |
| `lane` | `"paper" | "live"` | world stamping per Level 0 AD-27 |
| `placeholders_acknowledged` | bool | his acknowledgement on a live lane with placeholder blocks |
| `created_by`, `created_at` | str, ts | principal and time |

The whole document is at most `deploy_max_bytes` (16 MB, a setting); past it `deploy` refuses with the size.

## 4. Node state, unit state, passport, identity (owner P12; V-S)

**Node state** (`status`, `provides.node_state`): `schema_version` `qmx.node.state/1`; `word` (Setting up, Starting, Ready, Trading, Healing, Paused, Stopped by a risk rule, Stopped by a health check); `reasons` list; `identity {install_id, tag, machine_fingerprint, minted_at, mismatch bool}`; `clock` (§5); `venues [{venue, environment, session: "ready" | "connecting" | "not_set_up" | "down", since, last_contact ts}]`; `units {trading, warming, paused, stopped}`; `kill_level`; `safe_to_restart {ok bool, reasons}`; `contracts {route, operations, deployment, reading}` versions; `build`; `disk {free_bytes, guard_bytes}`; `last {decision_per_unit, quote_per_symbol, journal_write}` (health is progress); `at`.

**Unit state**: `deployment_id`, `unit {id, version}`, `per_market [{market_id, state, warm_up {done, needed}?, last_decision ts?, last_trade ts?, today_r exact?}]`, `world`, `placeholders` list, `stand_downs` list.

**Passport**: `schema_version` `qmx.node.passport/1`; `identity`; `checks [{name, ok bool, value, at}]` for broker session, feed freshness, demo test trade with its stop placed, observed and closed, kill-switch latency, clock band, disk, image digest; `round_trip [{venue, median_ms, spread_ms, samples}]`; `grants [{venue, expires_at}]`; `agent_wallets [{address, expires_at}]`; `at`.

## 5. Host facts, clock facts, the keys document (owner P0 and P12; V-S)

**Host facts** (`road/host/facts.json` in every supervised app's volume, written only by the host, before the app starts and on change): `schema_version` `qmx.host.facts/1`, `placement`, `role` (`pc`, `node`, `server`), `trading_profile` bool, `chats` bool, `agent_steps` bool, `at`.

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
| `market_id`, `instrument` | str |
| `tier` | `tick`, `bar`, `session`, `day`, `calendar` |
| `time_base` | `clock`, `ticks`, `volume` |
| `value` | exact? |
| `percentile` | exact? (against the market's own usual for that minute of its session) |
| `word` | str? (from the reading card's words) |
| `health` | `fresh`, `stale`, `degraded`, `thin`, `shadow`, `retired` |
| `data_level`, `fallback_step` | int, int (0 when none taken) |
| `estimate` | str? (`broker-side` for cTrader order-flow estimates) |
| `inputs_received_at` | ns |
| `computed_at` | ns |
| `stale_after_s` | int |
| `corrects` | id? (a correction links the record it replaces) |

The envelope's `source` is `node` or `mis`, `machine` the writing place, `world` as Part B stamps it. The series key is (source, reading id@version, tier, market id, instrument, machine); each (reading, tier) pair has one writer kind.

## 8. The MIS app (owner P13; V-P, V-S)

`configure` (domain_write, `state = "instance"`): `{op_id, markets: [{market_id, instrument snapshot}], packs: [{id, version}], shadow: [{reading id, version}]}` answers `{configured: n, refused: [{market_id, reason}]}`. `status` (domain_write read): runner state, per-reading health, last computed per market. Provides `board` (`stale_after` per tier): `{tier, at, markets: [{market_id, states: {reading id: word}}]}`.

## 9. Records (owner P4; V-K)

Kind files `instrument.schema.json`, `venue.schema.json`, `account.schema.json`, each with `schema_version`; field lists in `RECORDS.md` §2. Snapshots inside deployments carry each record's content, id@version and fingerprint.

## 10. Alarms and liveness (owner P12; V-S)

The kept `AlertPayload` (`failure_id`, `alert_class` in the closed push list, `summary`, `correlation_id`?, `authorizes: false`) plus `node_tag`, `at`, `calendar_open` bool; delivered by the ntfy channel as one POST with `Title`, `Priority` (5 for node down and protection escalation, 4 otherwise) and the summary as body. The liveness ping is an HTTPS GET to the Healthchecks.io ping URL with no body.

## 11. Capability declaration additions (owner `packages/qmf-venue`; V-L, addable)

Per venue and order type: `protective_stop_form` (`entry-relative`, `position-trigger-after-fill`); `trigger_basis` (`mark`, `last`); `open_orders_cap`; `action_budget`; `unattended` (`allowed`, `manual_login`, `server_banned`); `needs_desktop_app` bool; `sandbox` (`demo`, `testnet`, none).

## Shapes this part consumes

| Shape | Owner | Used where | Rule |
| --- | --- | --- | --- |
| Unit document `qmx.unit/1`, its `reads` list with fallbacks | Part A | deployment `unit_document`; runtime | V-S |
| CT-23 format 3 sized intent | Part A | the order path, step 1 | V-CT |
| Reading card schema | Part A | the reading runner | V-S |
| The block loader and the pinned block folder layout | Part A | runtime compile; reading runner | V-S |
| The checker-G verdict record and compiled fingerprint | Part A | deploy refusal | V-S |
| Journal envelope and kinds; the writer library | Part B | node and MIS append stores | V-S |
| The harvest of append stores into the machine's market-data door, and the pull job | Part B | X3; the MIS node instance's bars | V-S, V-K |
| CT-18, CT-19, CT-20 | `packages/qmf-venue` | the venue-client port | V-CT |

## Matched against the master

| Master row | Status |
| --- | --- |
| C12, C13, C21, C22, C26, C27 (wording, see CF-1), C28, C29 | match |
| C23 (MIS node instance reads the store through the door's `read`) | change: apps reach the store through `QMX_MARKET_ROOT`, read-only (below) |
| C24 (MIS writes partitions `source = mis`, records, `provides.board`) | match, through Part B's writer library |
| C25 (unit reads the board) | deferred to slice C-22; fallback holds |
| X1 (operation list) | change (below) |
| X2, X4, X5, X7, X8 | match |
| X3 | change: `data.list` carries `confirmed` (below) |
| X6 | match; the known gap rechecked (`NETWORKING.md` §3) |
| X10 | match; the install path designed (`NETWORKING.md` §4) |
| E1, E3, E4, E5, E7, E9, E10, E11, E12 | match |
| E8 | change: the node's two sign-in operations named (below) |
| §5 shapes owned by Level 1 C | defined here (§1 to §9) |

## Contract changes (for the master's writer; this part does not edit `01-connections.md`)

1. **X1 operation list.** Replace `mode` with `bind` (the venue proves demo or live) and add `withdraw`, `confirm_same_node`, `sign_in_begin`, `sign_in_code`, `self_test`, `rotate_keys`. Reason: a separate mode duplicates `bind`; identity and sign-in need their own operations (CF-3).
2. **X3 confirmation.** `data.list` gains an optional `confirmed` list; the server's door pins node-born partitions until This PC lists them (CF-5). Part B builds the door change with its harvest.
3. **C23 path.** The `mis` app reads its machine's store through `QMX_MARKET_ROOT`, which the supervisor gives only to apps declaring `data_reads = ["market"]`; the door stays the only writer (CF-4).
4. **C27 wording.** On Linux the node's grant store is an owner-only file in its volume, keeping QMN's rotation rule, not QMN's systemd-credential store (CF-1).
5. **E8.** The node's trading sign-in is the operations `sign_in_begin` and `sign_in_code`, reached locally or through `apps.ask`; This PC's loopback receiver relays only the code.
6. **New row C30.** Host facts: the host writes `road/host/facts.json` into each app volume; the node reads it before keeping a live grant (spine AD-307).
7. **New row C31.** The host ships app logs from volumes into OTLP when `send_to` is on (spine AD-321).
8. **Heartbeat rows across machines** are read tolerantly; the host row gains an optional `clock` field (§5).
9. **Requested of Part B's harvest.** The open month of bar series harvested every `bars_harvest_s` (60) on a machine that runs a `mis` instance; ticks hourly; journals as Part B designs.
