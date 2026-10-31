# Part B contracts: every shape this part owns or consumes

Every shape is JSON Schema 2020-12 and carries `schema_version` (Level 0 AD-6): fields may be added, meanings never change; readers read every version they support and keep reading an old version for the overlap window (setting, default 90 days). Version rules are the connections master's codes (`01-connections.md` "Version rules"): V-S shape, V-K Library kind, V-P pinned app call. Field types: `str`, `int` (exact integer), `dec` (exact decimal as a string), `ns` (int64 UTC nanoseconds), `ts` (ISO-8601 UTC text), `pin` (`id@version`), `fp` (`fp1:sha256:...`), `R` (a dec in multiples of initial risk), `money` (exact integer in the account's money digits plus currency).

## 1. The QMB contract `qmb/1` (owner: part B; carried by app manifests and jobs)

A tester app implements `qmb/1` when its `app.toml` has:

| Field | Value | Rule |
| --- | --- | --- |
| `risk` | `runs` | no tester is `money` |
| `kind` | `headless` (or `both` once a screen folder exists) | |
| `entrypoints.jobs` | one script per run kind it supports, `jobs/<kind>.py`, each `def run(inputs)` | kinds: `backtest`, `sweep`, `walk_forward`, `robustness`, `optimize`, `whatif`, `replay_check`, `behaviour_check`, `conformance`; `backtest` and `conformance` are required |
| `operations.capabilities` | `approval = "read"`, `state = "none"` | output below |
| `operations.instruments` | `approval = "read"`, `state = "none"` | output: the instrument classes and data levels it can replay (it reads no Library; the core joins this with the records) |
| `provides.backtest-result` | schema `qmx.qmb.result-bundle/1`, `lander = "qmb-run"`, no `stale_after` | namespaced by app id (`<app>/backtest-result`) |
| `capabilities.secrets`, `capabilities.network` | none | a tester needs no key and no network |

`capabilities` output (V-S, `qmx.qmb.capabilities/1`): `schema_version`, `contract` (`qmb/1`), `tester` (`app`, `version`), `run_kinds[]`, `data_levels[]` (`quotes`, `trades`, `bars`), `fill_models[]`, `cost_adapters[]`, `carry_adapters[]`, `margin_models[]`, `instrument_classes[]` (`fx`, `metal`, `index_cfd`, `commodity_cfd`, `crypto_spot`, `perp`, `future`), `whatif_scenarios[]` (each `name`, `direction`: `worsen_only` or `may_improve`).

## 2. A run: request, bundle and the landed result

### `qmx.qmb.run-request/1` (owner: the QMB contract; the core fills the fields marked core; V-S)

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | int | 1 |
| `kind` | str | one of the run kinds |
| `run_id` | str | **core**, `qmbr-<machine>-<ulid>`; the tester echoes it |
| `unit` | pin | the `unit` item version |
| `compiled_fp` | fp | **core**, from the unit's recorded G verdict |
| `study` | pin | a `study-spec` version; **core** makes an implicit one when absent |
| `markets[]` | pin | instrument record versions (Part C's records) |
| `window` | object | `start`, `end` as ts; any start allowed |
| `data[]` | object | `series_key`, `level` (`quotes`, `trades`, `bars`), `card` (dataset pin), `files[]` (**core**: run-folder paths with fp) |
| `execution` | object | `fill_model`, `cost_profile` (a Library `artifact` pin or `study_default`), `slippage`, `carry`, `margin`, each `name@version` from `capabilities` |
| `seed` | int | |
| `purpose` | str | `exploration`, `validation`, `stress`, `replay_check`, `conformance` (stress runs stamp world `stress`) |
| `motion` | str | `on`, `off`, `both` |
| `params` | object | per kind: `grid` (sweep), `split` (walk_forward), `battery[]` (robustness), `ranges`, `target`, `constraints` (optimize), `base_result`, `scenarios[]` (whatif), `deployment`, `day` (replay_check), `slice` (behaviour_check), `pack` (conformance) |
| `allow_gaps` | bool | from the study, default false |
| `model_cutoff` | object | **core**, `model`, `cutoff` (ts), from the unit's lineage (QB-11) |
| `input_dir`, `output_dir` | str | **core**, inside the tester's volume |

### `qmx.qmb.result-bundle/1` (owner: the QMB contract; left by the tester under `provides.backtest-result`; V-S)

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version`, `run_id`, `request_fp` | int, str, fp | `run_id` must equal the request's |
| `tester` | object | `app`, `version`, `contract` (`qmb/1`) |
| `status` | str | `finished` or `failed` (a tester never writes `killed`; the core does) |
| `reason` | str | when failed |
| `measures` | object | money: the 27 shipped measures; R: `trades`, `expectancy_r`, `win_rate`, `payoff_r`, `max_drawdown_r`, `mae_median_r`, `mfe_median_r`, `exit_capture`, `entry_edge_ratio` |
| `labels` | object | `zero_trades` (bool), `costs_uncalibrated` (bool), `fidelity` (`quotes`, `trades`, `bars`), `placeholders[]` (block pins with `origin: placeholder`), `data_seams[]`, `gaps[]`, `motion` |
| `files[]` | object | `slot` (`report`, `trades`, `equity`, `journal/<kind>`, `daily_r`, `slices`, `receipts`), `path` (in the output dir), `fp`, `bytes`, `rows` |
| `consumed[]` | pin | dataset card versions read |
| `versions` | object | `qmb`, `qml`, `checker`, each adapter `name@version` |

### `backtest-result` kind, `schema_version` 2 (owner: Library kind file, written only by the lander; V-K)

Fields kept: `memo_key`, `world`, `claim_class`, `role`, `fidelity`, `provenance`, `outcome`. Added (all optional, so version 1 items stay valid): `run_id`, `status` (`finished`, `failed`, `killed`), `reason`, `kind` (the run kind), `tester` (`app`, `version`), `unit` (pin), `compiled_fp`, `study` (pin), `markets[]`, `window`, `seed`, `motion`, `measures`, `labels`, `principal`, `place` (engine AD-72), `model_cutoff`, `versions`, `request_fp`. Blob slots: `report` (kept), `trades`, `equity`, `journal/*`, `daily_r`, `slices`, `receipts` (Parquet, `application/vnd.apache.parquet`). Edges: `consumed` to each card version, `uses` to the unit version, `tests` to the study spec. Page tabs added: "Journal" (blobs `journal/*`), "Slices", "Who ran it" (`principal`, `place`, `tester`, `run_id`).

## 3. The judge's records (owner: part B, `qmx-judge`; all record class; V-K)

| Kind | Fields |
| --- | --- |
| `try` | `kind` (`run`, `check`, `spec_edit`, `shortlist`, `paper_pick`, `whatif_rerun`), `state` (`opened`, `landed`, `failed`, `recorded`), `run_id`, `family` (root item id), `unit` (pin), `study` (pin), `market` (pin, optional), `tester`, `principal`, `place`, `at` (ts), `links` (the opened try, the result) |
| `study-spec` | `origin` (`written`, `quick`), `claim` (`edge`, `horizon`, `sessions[]`, `conditions[]`), `markets` (list of pins, or `admitted`), `windows[]`, `record_needed` (`trades`, or `sequential`), `preset`, `shrinkage` (`estimator`, `k` when fixed), `correlated_threshold`, `holdout` (his choice, default `off`), `cost_rule`, `fill_model`, `allow_gaps`, `motion`, `seeds[]` |
| `verdict` | `study` (pin), `results[]` (result ids), `per_market[]` (`market`, `trades`, `raw_r`, `shrunk_r`, `steps[]` each `name`, `passed`, `can_fail_on`, `cannot_fail_on`), `overall` (`pass`, `fail`, `too_thin`, `no_trades`), `effective_tries`, `preset`, `versions` (`judge`, `checker`, `tester`) |
| `baseline-card` | `unit` (pin), `verdict` (id), `record_r` (summary), `cone` (percentiles by trade count), `cost_assumptions`, `fill_assumptions`, `trade_rate`, `readings_range` (per reading: min, max, percentiles seen when earned) |
| `proposal-card` | `subject` (pin), `ask` (`paper`, `live`, `admit_market`, `drop_market`, `tighten`, `bench`), `evidence[]` (links), `verdict` (id), `tries` (count), `preset`, `placeholders[]`, `cost` (time, money where any), `made_by` (principal) |
| `death-certificate` | `unit` (pin), `cause` (from the appendable list: `no_signal`, `costs`, `overfit`, `decay`, `no_trades`, `data`, `behaviour`), `classifier_version`, `explanation` (blob), `memory_row` (id) |
| `forecast` | `market` (pin), `call` (`direction`, `state` or `range`), `horizon` (ts), `confidence` (dec), `written_at`, `written_by` (principal), `scored_at`, `score` (dec), `scorer_version` |

**The lander port** (owner: `qmx-judge`; injected into the apps supervisor; in-process, no schema on the wire): `open(app_id, version, job, inputs, principal) -> Ticket | None` (None for an app whose provides name no lander), `close(landing) -> result_id`, `fail(ticket, reason) -> result_id`. All three are idempotent by run id.

## 4. Journals (owner: part B, the writer library in `packages/qmf-data`; V-S)

### `qmx.journal.envelope/1`

| Field | Type | Rule |
| --- | --- | --- |
| `record_id` | str | `<writer_id>/<seq>`, or `<venue>:<deal id>` for `fill` |
| `stream` | str | `unit`, `market`, `node`, `readings` |
| `kind` | str | the body's kind |
| `schema_version` | int | the kind's |
| `writer_id` | str | one writer per stream (CT-13 `WriterId`) |
| `seq` | int | gapless per writer |
| `ts_venue` | ns or null | where the venue gives one (cTrader gives none) |
| `ts_recv`, `ts_write` | ns | always |
| `clock_ok` | bool | false while the machine's offset is unproven (Level 0 AD-10) |
| `clock_offset_ns` | int or null | the measured offset |
| `backfilled` | bool | true for rows written after the fact (JR-08) |
| `world` | str | `backtest`, `stress`, `paper`, `demo`, `live`, `shadow`, `synthetic` |
| `unit_id`, `unit_version` | str | for unit-journal rows |
| `market_id` | str | the QMX market id on the instrument record (Level 0 AD-26) |
| `venue`, `account`, `platform` | str | account is broker, account id and type (netting or hedging) |
| `machine` | str | the writing machine (This PC or a server's name) |
| `run_id` | str or null | a QMB run, or the node's session id |
| `trace_id` | str or null | source to trade; the client order id is the trade's trace id tagged with the node id |
| `build` | str | the writer's build |
| `links[]` | object | `rel`, `ref` (a record id, a partition key plus seq, or a Library id) |

Kind bodies are `qmx.journal.<stream>.<kind>/1`; their fields are listed in `journals.md` §3. Reason codes are a closed, appendable list (`journals.md` §3).

### Journal partitions (owner: part B; on each machine's market-data store; V-K through the store's version)

Key `journal-<stream> / <subject> / <kind> / <world>.<machine> / <yyyy>-<mm>`, the month being that of the row's `t`; columns `t` (int64 epoch milliseconds, the writer's monotonic stamp), `seq` (int64), `record` (large string, the canonical JSON); freeze `month-end` plus `[journals] settle_days`. One dataset card per journal series, `source = journal-<stream>`, `licence = own`.

## 5. Amended Library kinds (owner: part B; additive; V-K, `schema_version` raised by one)

| Kind | Added fields |
| --- | --- |
| `note` 2 | `about[]` (links), `note_kind` (`analysis`, `proposal`, `lesson`, `forecast_ref`, `disagreement`), `receipts[]` (tool call ids), `window` (`start`, `end`), `sources_marked[]`, `expires` (ts), `author` (principal) |
| `paper-run` 2 | `unit` (pin), `market` (pin), `account`, `node`, `started_at`, `ended_at`, `status` (`running`, `ended`, `stopped`), `record_r`, `sequential_score`, `journal[]` (partition keys); writer: the judge's paper scoring script |
| `trade` 2 | `unit` (pin), `market_id`, `machine`, `trace_id`, `mae_r`, `mfe_r`, `costs` (`spread`, `commission`, `swap`, `funding`, `slippage`), `equity_before`, `session`, `streak`, `placeholders[]`, `r_missing` (bool), `gap_through_stop` (bool); `world` enum unchanged; writer: the records host job |
| `dataset` 2 | `source_clock` (IANA zone or `UTC`), `seams[]` (`at`, `what`: `stamp_unit` or `cadence`, `from`, `to`), `stitching` (`method`, `rolls[]` with `at`, `from_contract`, `to_contract`), `calendar` (instrument record pin) |

## 6. The records host job (owner: part B, `qmx_host/records.py`)

Settings `[records] on`, `interval_s`, `node_retention_days`. Each round lands one Library `artifact` with `fields.type = maintenance-result` (the built maintenance shape, `qmx_host/maintenance.py:1-15`) and body `job = records`, `nodes[]` (`node`, `reached`, `partitions`, `bytes`, `oldest_unshipped`, `refusals[]`), `at`. Per node state (watermarks) lives in This PC's QMX folder beside the backup record.

## 7. Catalog rows (owner: part B; core toolsets; `<toolset>_<op>`; V-S row schemas)

| Row | Toolset | Approval | Input | Answer |
| --- | --- | --- | --- | --- |
| `backtest_run` (reshaped) | `backtest` | `domain_write` | a run request without core fields; or `study` plus `unit` only | `run_id`, `status`, and `result_id` when it finished within `[qmb] agent_wait_s` |
| `backtest_status` (reshaped) | `backtest` | `read` | `run_id` | the try rows' state, the tester, the place |
| `backtest_results` (reshaped) | `backtest` | `read` | `result_id`, `format`, a page cursor | fields, measures, labels, a page of trades |
| `backtest_compare` (reshaped) | `backtest` | `read` | two `result_id` | the parity diff |
| `judge_run` (new) | `backtest` | `domain_write` | `study`, `results[]` | `verdict` id |
| `journal_query` (new) | `research` | `read` | `stream`, `window` (required), filters, `view`, `format`, `include_backfilled` | rows, a view or a digest; "data stops at" when past it |
| `notes_write` (new) | `research` | `domain_write` | a `note` body | the note id |

All are on the default copilot surface by construction (core toolsets, `qma-harness/src/qma/harness/surface.py:484-489`), and a test pins it (Level 0 AD-31).

## 8. The mini-app core's job shapes (owner: part B; in `qmx-apps`; V-S on disk)

| Shape | Fields |
| --- | --- |
| job request file `data/jobs/<name>.request.json` | `job`; `inputs` only when given (absent today, so a request without inputs is byte-identical) |
| job answer file `data/jobs/<name>.done.json` | `ok`; `error` when not ok; `result` only when the job returned a value; `{"output": name, "data": ...}` inside `result` is saved as a leave |
| `run_job` return | as today (`app_id`, `instance_id`, `job`, `version`, `profile`) plus `result` when present and `run_id` when a lander opened the run |
| `Contract.lander` | an optional registered core name |

## 9. Shapes this part consumes

| Shape | Owner | What part B reads or writes |
| --- | --- | --- |
| Unit document `qmx.unit/1`, its pinned blocks | Part A | the lander copies them into the run folder; QMB compiles through A's loader |
| Check result and the G verdict and behaviour report | Part A | the lander requires a recorded G verdict for the compiled fingerprint; `behaviour_check` produces one |
| CT-23 format 3 sized intent; the risk socket's slots | Part A | QMB's unit runner hosts the socket in replay |
| The read surface protocol a windowed reader implements | Part A (QML) | QMB's reader serves a window, not whole history |
| Identity table, lifecycle machine | Part A | `state` journal rows record his moves; proposal cards ask for them |
| Instrument, venue and account records, calendars, the market id | Part C | QMB's execution and carry; the calendar-open check; the data-quality check |
| Stamped reading `qmx.reading/1`, the board | Part C | `signal` rows' readings; templates read reading history and the board |
| AD-46 verbs `data.list`, `data.fetch`, `apps.job`, `apps.ask` (`journal_tail`, `status`), `heartbeats` | Part C | the records host job; remote QMB jobs; the node watcher |
| Node operations and node journal writers | Part C | the node writes unit and node journal kinds through part B's writer library |
| CT-13 events, CT-19 commands, CT-20 events, CT-29 exit records | `packages/qmf-data`, `qmf-venue`, `qmf-risk` (EXISTS) | `order`, `fill` and `trade` bodies wrap them |

## 10. Matched against `01-connections.md`

| Row | Matches? | Note |
| --- | --- | --- |
| C7 copilot or agent to QMB app | yes, with change 1 | rows forward through the job path; the wait default changes |
| C8 workflow to QMB app (`app_op {app: qmb, job: backtest, pin}`) | yes, with change 2 | plus `inputs` |
| C9 the Lab to QMB app | yes | default adapter `app_op` |
| C10 QMB app to core landing | yes, with change 3 | the door is the supervisor's job path and the lander |
| C11 QMB app to market-data door | changed (change 4) | the core materialises on the run's behalf |
| C12 apps to compiled units and blocks | yes | through Part A's loader |
| C13 apps to journal writer | yes | the writer library in `qmf-data`; QMB's records in the result's blobs |
| C14 judge to Library | changed (change 11) | verdict, baseline and proposal cards land as records, not governed drafts |
| C15 templates and agents to journals, readings, records | yes | `journal_query` here; `readings_query`, `instrument_get` are Part C's rows |
| C16 agents to notes | yes | `notes_write` row, `note` 2 |
| C17 Library ref log to templates | yes | the loop guard is content (producer filter and intent key) |
| C19 downloaders to the door | yes | plus the stamp check and seams |
| X3 the pull | yes, with change 7 | a host job; watermark confirmation |
| X7 agents and the node watcher reading a node | yes | |
| §5 "Study spec, verdict, baseline card, try ledger row" | yes, with change 5 | the try ledger row is the `try` kind |
| §5 "QMB operations and the `backtest-result` extension" | changed (change 6) | jobs plus two operations; status, results, compare are core rows |
| §5 "Journal envelope and kinds" | yes | |
| §6 "The `qmb` app does not exist" | closed by slice B5 | |

## Contract changes

Proposed for the connections master's writer to fold in; part B does not edit `01-connections.md`.

1. **C7.** "the call waits up to `qmb_tool_wait_s` (default 600 s)" becomes "`[qmb] agent_wait_s`, default 240 s, below the prompt cache's five minutes (WF-07); workflows wait for the whole job". Changes LC-A0-21's number.
2. **C8.** `app_op` takes `parameters.inputs` (merged over its `in` port) and its answer carries the job's `result`; the job runs with those inputs.
3. **C10.** Door: "the apps supervisor's job path, which opens and closes the run through the lander `qmb-run` that the tester's manifest names (`qmx-judge`, absorbing PR 204's `land`)", not a `backtest_and_land` call per door.
4. **C11.** From "QMB app" to "the core lander, on the run's behalf, into the run folder of the tester's volume"; QMB reads files only.
5. **§5.** Add the row "`try` item | P3 (the lander and the judge's writers) | Library kind | Level 1 B".
6. **§5 and Level 0 AD-34.** QMB's contract is run kinds as jobs plus `capabilities` and `instruments`; `status`, `results` and `compare` are the core's `backtest` rows over the core's records.
7. **X3.** "a job on This PC" is the records host job beside backups (not an engine workflow); `data.list(after = watermark)` doubles as the confirmation of a verified copy; the node deletes confirmed partitions after `[records] node_retention_days`.
8. **AD-46 `apps.job` (Part C).** Carries `inputs` and the caller's principal; a job counts as `domain_write` for the principal rule.
9. **C22 and C24 (Part C).** Reading history rows ride the journal envelope and the journal partition layout (`journal-readings` source); the body stays Part C's `qmx.reading/1`.
10. **New row C30.** "Apps supervisor to the core lander | in-process in the host | run request in; run id and the run folder out; result bundle in on close | the `Landers` port injected by the host (NEW) | ask | V-S | a lander refusal refuses the job before it queues".
11. **C14.** Verdicts, baseline cards and proposal cards land as records (class `record`), not governed drafts: scripts write them and nothing promotes through them; his click acts on the unit's lifecycle (Part A's machine), which stays the only path toward live.
12. **C13 (Part C consumes).** The committer of a node's closed months is that machine's host (the records job's local half), reading the sealed files from the node app's volume; the node app never opens the door. The before-dispatch write stays the node's in-process append store.
