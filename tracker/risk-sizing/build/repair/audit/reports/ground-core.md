# Ground report: the workflow engine, the mini-app core, the templates on them, and the dead weight

Commit 50c83a4e. Levels are the system prompt's: 2 pointed at the line, 3 walked, 4 ran real code. Proofs are in `D:/Temp/audit/ground-core/`. No code was changed, and no host was booted.

## 1. What this area is and how it really works

The engine runs a workflow as a folder of a definition and the files its nodes name, and a "tested" mark belongs to the hash of those bytes (`definition/folder.py`). Scripts run as `python -I` from the run's hash-checked copy, a `rule` or `grader` chooses the path, and agent and `llm` steps only produce data. A script never opens the Library: it asks for four kinds of read and lists its writes, which the engine makes on the run's own branch and which reach `main` only when the run passes, though it can import `qmx_tools`, `qml`, `qmb` and `qmx_host`, which is how `door.py` reads journals and the market store. The `library` node is built and on (`service/runs.py:277`, commit `3d5f0a24`), so a later node can read any object by `@library:<id>` or `@run:<id>/<output>`, and the design files G4b and `workflows.md` section 1 that call it broken are out of date. A mini app is a folder with `app.toml`, stored once per hash, run in its own locked environment under `cache/envs/<hash>`, with one volume per app id, on the supervisor's single loop (`qmx_apps/supervisor.py`). Apps are asked by operation (20 s, stopped at 30 s) or by job (one at a time, as long as it takes). QMB's jobs land through a core lander the host injects, so every door crosses one try-counting path. A `money` app runs only its active signed version, and others run the active version if one was published, else the newest installed. Templates are content on all this, with shared blocks copied in, and the judge's core lives in `qmx_judge` and is pressed through the `backtest_judge_run` tool, not a workflow step. The build changed nothing in `runner.py`, `nodes/script.py` or the definition code (`git diff --stat c93407ca`), and changed the supervisor by about 400 lines and `app_op`, `policy.py` and `agent.py` by less, which by my reading are the design's named changes.

## 2. What must not break

Every other repair is checked against this list. A repair that needs to break one must say so and name his ruling.

**Engine**
| # | Promise, as built | Guarded by |
| --- | --- | --- |
| E1 | No model answer is a route. Only a `rule`, `grader` or script output read by a rule chooses a path, and rule text cannot call anything. | `test_rule.py`, 4 tests, run by me |
| E2 | A one-byte edit of any named file changes the hash, and moving a node does not. A tested mark does not survive an edit. | `test_definition.py::test_a_moved_node_keeps_the_hash_and_a_one_byte_prompt_edit_changes_it`; `template_facts.py` line 1a |
| E3 | A run runs the bytes it started with. A changed script fails `code_changed`. | `nodes/script.py:447-452`. No test found by that name; level 2 |
| E4 | A script sees no provider key, no Claude name, no plan path and no home path. It has no run timeout, only the stuck detector. | `test_script.py`, 6 tests |
| E5 | A script writes only artifacts and links, on its own run's ref, as the run, once per slot. It cannot forge a principal or an engine edge. | `test_served.py::test_a_retried_attempt_of_the_same_slot_writes_nothing_twice`, `::test_a_forged_principal_ref_or_engine_edge_is_ignored_or_refused` |
| E6 | An agent step gets only the tools it declares. File writes stay under its attempt folder, and only declared outputs leave. | `test_agw.py`, 6 tests, run by me |
| E7 | No caps: no usage budget, no tool ceiling and no money limit in the format. | `test_definition.py::test_a_usd_limit_is_not_part_of_the_format`, `test_lint.py::test_an_agent_with_no_limits_validates` |
| E8 | Templates install disabled and idempotent by hash, a draft with `meta.needs` stays a draft, and enabling is his act. | `templates/install.py`; `test_templates.py::test_every_folder_in_the_pack_validates_for_publish_and_only_its_needs_hold_it_back` |
| E9 | Run results reach `main` only when a live run passes. A killed run lands once when resumed. | `test_resume_lands.py`, 6 tests |
| E10 | A node with no `inputs` calls the old two-argument runner, so an app asked by name sees nothing new. | `test_app_op_inputs.py::test_a_node_without_inputs_calls_the_two_argument_runner` |
| E11 | The slow lane writes only artifacts on its own run and never moves a unit, a ref or an order. | `test_templates.py::test_the_slow_lane_writes_only_artifacts_on_its_own_run_and_asks_qmb_only_to_replay` |
| E12 | The engine's core imports no adapter, store, clock or randomness. | `test_import_rules.py`, 8 tests |

**Mini-app core**
| # | Promise, as built | Guarded by |
| --- | --- | --- |
| M1 | A definition is immutable. Changed bytes need a new version, and a new version needs the current head named. | `test_apps.py::test_definition_is_immutable_and_volume_has_one_owner`, `::test_new_version_and_trust_boundary`; `sup_proof.py` D, E |
| M2 | One host owns each volume. The volume belongs to the app id, so a new version keeps its data. | same test; `sup_proof.py` F. No shipped test pins that a version keeps data |
| M3 | Only declared secrets reach an app, logs are redacted, and app writes stay inside its volume. | `test_apps.py::test_only_declared_secrets_and_redacted_logs`, `::test_actual_subprocess_refuses_outside_writes` |
| M4 | Agent-written code cannot be installed at T1. | `test_apps.py::test_new_version_and_trust_boundary` |
| M5 | A `money` app runs only its active signed version, also after a crash, and publishing needs his signature. | `test_restart_backoff.py::test_a_money_app_restarts_only_its_active_signed_version`, `test_road_runtime.py::test_real_road_and_isolated_live_outputs` |
| M6 | The breaker's default is 3 errors and stays down, restart is opt-in, his stop cancels a pending restart, and no usage budget stops an app. | `test_restart_backoff.py::test_an_app_that_sets_no_restart_stays_down`, `::test_a_stop_cancels_the_pending_restart`, `test_apps.py::test_no_usage_budget_stops_an_app` |
| M7 | A job request with no inputs is byte for byte the old one, and a `run()` with no parameter runs as before. | `test_landers.py::test_an_app_with_no_lander_runs_and_lands_its_job_as_before` |
| M8 | Every door that starts a QMB job crosses the lander. A job that raises or leaves nothing fails its run, refusals come before any try opens, and a run lands once. | `test_landers.py` (6 tests), `test_job_outputs.py` (5 tests) |
| M9 | A pin is rechecked before the app sees the ask. | `test_door_pinned_app_op.py` |
| M10 | Enabled first-party apps come back at every host start. | `qmx-host/tests/test_first_party_node.py`, with a fake supervisor |
| M11 | Publishing is compare-and-swap with evidence, and rollback is a new evidenced step. | `test_road*.py` |

His word stays: the engine and core change only with a reason tied to their intent. The blocks below keep to template and core-lander content wherever the code allowed it.

## 3. The problems

### A. How a repair reaches an installed app: triage-7, known-2, and a new defect (install holds the lock)

**What the supervisor does today, by short run (`sup_proof.py`, level 4).** There are three rings, and nothing moves any of them after the first install.
- **App files.** After a repair, a host start runs the old hash (C: "runs c5ef7d84, same as old True"). An install with the same version answers `immutable_version` (D). A new version with no named head answers `head_conflict` (E). With the head named it runs the new hash and the volume data stays (F).
- **Libraries.** The environment build runs only inside `install` (`supervisor.py:469`), and `enable_first_party` (`first_start.py:623-627`) never calls it for an installed app (C: env builds unchanged). The libraries are wheels (`--no-editable`). So a repair to `qmb`, `qml`, `qmf` or `qmn` also never reaches the app. An install of the same bytes is accepted and does rerun the build (G), so a door already exists.
- **Published versions.** `start` prefers `active` (`supervisor.py:678-695`). Connect steps auto-publish non-money apps at the shadow proof (`road/__init__.py:218`), so a folder that connected a node keeps QMB and the MIS on the active version even after a new install (level 2). The node waits for his signature, which is right (M5).
- **Templates are a fourth path.** Nothing runs at host start. `python -m qmx_engine templates install` publishes a new patch beside the old one, after a test run, and his enabled trigger stays pinned to the old object (`install.py`, `control_door.py:687`, level 2).
- **The install itself: known-2.** True, and the obvious fix does not work. `subprocess.run(timeout=3)` with `capture_output` against a child that left a process holding the pipe raised only after 25.3 s, when that process ended (`pipe_proof.py`, level 4). On Windows `run` waits for the pipe after the kill.
- **The install itself: the lock.** `_install` holds the supervisor's lock across `uv sync` (`supervisor.py:443-469`). The HEAD commit fixed this for the heartbeat only. `call`, `run_job`, `status` and `_log` all take that lock. A plain call to a running app answered after 44.1 s while another app installed for 45 s (`stall_proof.py`, level 4). The node's reads and controls go through `call` (`node_link.py:322-343`, level 2). So while anything installs, his kill and flatten wait, and with known-2 they wait for ever.
- **Safety fact.** The volume belongs to the app id and a re-install of the same bytes is accepted, so an upgrade at host start loses no data and needs no new door. Level 4 for a non-money app. For a money app the signed version keeps running until he signs, by M5, level 4 from the shipped test.
- **Repair shape.** `_install_environment`: send uv's output to a file, not a pipe, run it under a kill-whole-tree wrapper, and fail by name past a generous wall limit, a setting I would default to 30 minutes. My call: a stuck install is no usage cap, so ruling 106 does not apply. `_install`: take the lock for the catalog checks and the registration, not for the build. The per-app volume lease already keeps two installs of one app apart. One helper beside `enable_first_party`, used also by `connect_node._install` and `_server_install`: at start, before an app starts, compare the shipped folder's hash and its path-source digests (`path_sources`, already there) with what is installed. Install with the head named if they differ. A non-money app with an active version then takes its road proof and publish. A money app stops at "waits for your signature". One bad app must not stop the others. Catch per app and start the old one, naming why. This meets p5c-3, so build them together with the ground-start repair. A literal table of app version to image hash in `test_shipped_apps.py`, so a PR that edits an app and forgets the version fails CI, not his next start.
- **Proof.** `sup_proof.py` C must print the new hash, and a stalled-install lane must show a call answering at once. **Order:** first of all, before any repair to `apps/*`. **Files:** `supervisor.py`, `first_start.py`, `connect_node.py`, `test_shipped_apps.py`. **Size:** about 150 lines. **Whose:** ours, inside his baby, for the reason that a repair must reach him. It breaks no promise above.

### B. Supervisor upkeep: triage-4, triage-5, triage-8

- **triage-4, restart wait.** True. Four crashes, each after 3 s of health, waited 5, 10, 20, 40 s (`sup_proof.py` H, level 4). `Healing.trips` clears only on his stop. The cause is at `supervisor.py:1032`. Shape: in `_heal`, start counting again when the instance ran longer than `backoff_max_seconds`. The doubling for a crash loop stays, so the tests in `test_restart_backoff.py` still hold. Note: those restart at once, under that bound. The second half of the finding (an error in the loop outside its `try` leaves the app never restarting) is true by reading, narrow, and worth one `try`. Size S.
- **triage-5, event rows.** True and measured. One app writes 3.1 `apps` rows and 3.1 `aggregates` rows a second, about 2.4 KB a second (`sup_proof.py` B, 10 s, WAL included, so rough). That is about 200 MB a day per app, and about 0.5 GB a day with QMB, the MIS and the node. `control.db` is in the "result" backup class (`qmx_home/classes.py:129`), so copies carry it. The finding's `git grep` pathspec matches nothing, so it proved little, but a plain search of the packages also finds no `DELETE FROM events`. Shape: two small changes. In `_serve`, keep the heartbeat and breach check at 0.25 s, but `_persist` only when status, pid or breaker change, plus a slow metrics beat. In `ControlService`, prune events by age at start, and skip the totals row when totals did not change. Safety fact: while an app runs, `status()` reads the live instance, not the row (`supervisor.py:628-631`), level 2. The UI's live metric rate is what changes, so note it for the UI session. Size S to M.
- **triage-8, answer file.** True. A tight read after the replace raised `PermissionError` in 2,943 of 3,000 rounds on this disk (`done_race.py`, level 4). At the real 0.25 s poll it is rare, which fits "seen twice". The tight loop proves the window exists, not the real rate. Shape: read and unlink at `supervisor.py:1343-1344` retry on `PermissionError` inside the existing loop. Size S.
- **Order:** with A, same file. **Whose:** ours.

### C. A sweep that traded reads as no trades: p6-1, p6-7

- **Cause, reproduced (level 4, 82 s):** `D:/Temp/audit/p6/test_sweep_verdict.py` gave 6 trades measured, verdict `no_trades`, `per_market` empty, and a death certificate landed on `main`. `jobs/sweep.py:69` writes `{"cells": rows}` with counts, while `functions.py:629` reads `body["trades"]`.
- **Around it.** `test_qmb_run_kinds.py:176` pins `cells` and must stay. The judge pools a result's trades by market and refuses overlaps (`judge.py:638`), so a numbers grid must never be flattened, because that would pool variants of one market as one record. `robustness`, `whatif` and `walk_forward` list no trades, so u2's sweep plus what-if will not trip the overlap refusal (level 2).
- **Safety fact.** u1 and u2 ask a markets-only grid (`route.py` in each), so one cell per market means no overlap and each market judged alone. Walked, level 3, with the code read at `judge.py:707-711`.
- **Shape.** `sweep.py` adds a flat `trades` list only when the grid names no numbers. `_trade` moves from `jobs/backtest.py` to `qmb_tester.py` so both jobs share it. The change lives in the QMB app, so it needs a version bump, so A must land first.
- **Proof.** Adopt the audit's test into `apps/qmb/tests/test_qmb_run_kinds.py` with literals. It is the one new test p6-7 earns, and it fails today. **Size:** about 25 lines plus the test. **Whose:** ours.

### D. One verdict, one paper, read and not copied: p6-3, p6-4, p6-5, p6-15

These are one cause. `b` has its own certificate and card blocks, built before the core's judge landed its own, and it feeds them a model's copy.
- **p6-3:** true (`classify.py:47-54`; the answer at `functions.py:364` has no steps). Fixed by removing the block.
- **p6-4:** true. The `death-certificate` block has one caller, `b`. `proposal-card` has two, so it stays for u2.
- **p6-5, needs no engine change (corrects the audit).** The core can write the row where it lands the certificate. `land_judgement` gains a port, `RecallEngine.write("home", "judge", row)`, which the host already composes (`host.py:1136`). The certificate fills its `memory_row` field (`death-certificate.schema.json:31`). Readers: `home` rows reach every chat's snapshot (`surface.py:661`), and adding the `memory` toolset to `b`'s builder gives it `memory_check`. All level 2, not run. U1(a) is not needed if that holds.
- **p6-15, needs no engine change (corrects the audit and the planner's U1(b) pick).** A script hands on `@library:<verdict_id>`, the shipped `library` node reads the real object, and the rule routes on that. `test_verdict_read.py` (level 4, real engine, fake Library): a model copy saying `pass` over a stored `fail` read `overall: fail`, took the rule's false port, and the propose step did not run. A forged id is caught by comparing `fields.unit` to the run's pin, and by the verdict's results. The read on the real store is level 2, from `test_served.py::test_a_read_is_served_while_the_hosts_store_holds_the_writer_lock`.
- **Safety fact.** The core already lands certificate and card once per verdict (`judge.py:933-960`), so removing the block loses nothing but the model's explanation, and the scorecard's writer already explains.
- **Shape.** In `b`: drop `propose` and `certify`, add the read step, and show `cards` in the scorecard. Add the same read step to u1 and u2. Remove `_shared/death-certificate` and `b/death-certificate`. **Removes** about 420 lines and adds about 60.
- **Proof.** Real QMB to real referee to real scorecard on the `world` fixture: one certificate, cause `costs` when the cost step failed. **Order:** after C. **Files:** `b`, `u1`, `u2` templates, `judge.py`, `functions.py`, `host.py`, `test_templates.py` (tests at 997 and 1023 change on purpose, because fixtures must now plant a real verdict, which also closes the p6-7 gap). **Whose:** ours, and the engine is untouched.

### E. A check with no Library treats its own blind spot as an error: p6-2 (template side), p34-9

- **Cause.** Both call `checked(None, ...)` and misread kinds only the Library can settle. The hook goes silent when any is present. The block fails on them and spends fix rounds. `ground-qmb` holds the records half.
- **Safety fact (level 4, `template_facts.py`).** With the hook's five kinds removed, the dummy on GBPUSD and on US500 is left with no errors, and a broken number on GBPUSD is left with `outside_range`. The lander still compiles with the Library before any run (`host.py` `LanderLibrary._compiled`, per the audit), so nothing unsafe gets through. The real checker was run. The lander half is level 2.
- **Shape.** One function and one name in `qmx_tools/unit_check.py` for "what a check with no Library can say". The hook and `_shared/unit-check/scripts/check.py` both call it, and a pass with deferred kinds says so in `notes`. `hooks.json` changes, so regenerate `plugin.manifest.json` (`test_packs.py` guards it).
- **Proof.** A GBPUSD unit reaches QMB through `b`'s script gate; a broken one gets feedback from the hook. **Size:** about 30 lines, plus copying the block to `b/unit-check`. **Order:** after `ground-qmb`'s record fix, which it needs to run at all. **Whose:** ours.

### F. Slow-lane words: p6-9, p6-12, p6-13

Each is one template, content only, with no engine change.
- **p6-9:** true per the audit's level 4 test (`D:/Temp/audit/p6/test_gw_kill.py`, not rerun by me). `kill_level` is read over `lookback` only (`gw read.py:121`) and resumes are ignored. Shape: read it over `held_back`, as `stand_down` already is, and let the latest row per scope decide, with GREEN clearing. Size S. It is the one that bears on money, since he reads this word.
- **p6-12:** true. `marked-sources` has no caller (`grep`, level 2). Shape: `u3` calls it as a child before `draft`. Exposure is narrow: the agent holds `blocks` only. Size S.
- **p6-13:** true by reading. `s4 read.py` puts `months` and `fingerprints` in `findings`, and the writer gets the whole thing. A guess of 30 series over 6 years at 80 bytes is about 170 KB. Shape: counts to the writer, digests only in the landed artifact. Size S.

### G. "Needs an engine change": which truly do

| Finding | Needs one? | Why |
| --- | --- | --- |
| p6-5 | No | Block D. U1(a) can go. |
| p6-15 | No | Block D, proven. U1(b) can go. |
| p6-10 forecasts | No | `moved_to_main_after` lists new artifacts with their kind, and the `library` node reads each one (level 2, not run). The market door has `read` by series (`market_data.py:367`), which `door.py` already opens. The README's "no way to name a series" is a mapping from market id to series, not an engine gap. A new scoring template, size M. Late: nothing he decides rests on it yet. |
| p6-11 sessions | No | `workflows.md` section 6 names the sessions (Sydney, Tokyo, London, New York). A card setting of name, zone and time feeds `session_start`. The half-hour cron already runs. Size S to M. The per-market almanac is a separate template. |
| p6-8 d3, d4, l1 | No | They can take `b`'s and u1's shape: `app_op` steps plus the referee. `find_by_intent` already answers "already tried" for a passed live run of the same workflow. `d3` already drives its loop by `max_iterations: 1000` with `predicate: items.stop`, so a card count works today and U1(f) can go. |
| p6-8 l4, rs6 | One small read | A script reading a family's tries or dead-end rows has no door except a model's copy. One new verb in `READS` (U1(c)) is the honest answer. Ask him once, batched. |
| U1(d), U1(e) | Not in my problems | Not traced. |
| p6-6 | No | Honest "Not judged yet" today. The builder may name `ranges` in `build.json`, and `ready.py` takes them. The judge counts each candidate. Size S. Not foundation, by his word that the dummy need not pass. |
- **Order.** Leave p6-8 and p6-10 until research starts. They are honest drafts or honest gaps (`meta.needs`, README), not cracks. The planner should not spend on them in the foundation pass.

### H. Copies: p6-14

- **Is copying part of the design? Yes.** Three facts.
- A workflow is a folder, and its hash covers what it runs (AD-2, AD-11, `folder.py:1-7`).
- `TEMPLATES.md:91` states the rule.
- `door.py` is carried on purpose: each template names it as `door_ref` so the hash covers it.

Run (level 4, `template_facts.py`): a one-line door repair changes the template's hash (1a). With the door moved out of the refs, a later change does not (1b). So p6-14's fix would let a published, tested template change behaviour with no new version, which breaks E2 in exactly the way `folder.py` exists to prevent. His "shared helpers through symlinks" (ruling note, H-110) was about dev worktrees and `node_modules`, not template scripts. `reports/deletion.md` already said "by design, not slop" about the same files, and the two audit rows disagree.
- **Verdict: `leave`, not `should`.** No repair. A fix to `door.py` is a copy loop the drift test already checks. The cost is real but small: all twelve templates get a new version and a test run, which is what the design wants. Do not count the 1,900 removable lines.

### I. p2-7: default tester

True. `run_conformance` has no door in product, and `service.py:310` hardcodes `QMB_APP`. The check refuses with "run the pack on it first", which he cannot do. Shape: a `backtest` row or host job calling `run_conformance` with a real Library port, and `run_backtest` reading the app id from `default_tester`. Careful: `"qmb@1.0.0"` is a version, and A's version bumps make it stale, so read the app id only and keep the version as what the pack proved. Size M. It matters only when a second tester exists. Keep it late, with `ground-qmb`'s data work.

### J. known-5, known-7

- **known-5:** true, `import qmx_host.connect_logs` first gives the circular `ImportError` (run, level 4), and nothing does that. `leave`.
- **known-7:** overstated. `qmx-host` depends on `qmx-tools`, which depends on `qml` (both `pyproject.toml`), so a host always has it. Only a bare `qmx-control` install could fail, and only on a units save. `leave`, or one dependency line when next touched.

### K. Dead weight: exact steps to detach

`reports/deletion.md` was right that nothing in the product needs these, and short on what the gates need. Proven on a scratch copy at `D:/Temp/audit/ground-core/cut` with the folders removed (level 4 where a run is named). `tools/ci.py` names none of them directly, and it runs `tools/test_all.py`. `.github/workflows` names them only in a comment (`skylos.yml:91`) and for `examples/apps`, which stays.
- **`adws` (retired factory).** Nothing in the product imports it. Steps: Delete `adws/` and `queue/`. `tools/test_all.py:65`, drop the row. **Missed by the audit:** delete `tools/tests/test_sssf_quality_gate.py` (6 tests fail, run). **Missed by the audit:** delete `qa/tests/epic_01/test_l3_integration.py::test_e1_i04_sssf_factory_gate_stamp_survives` (fails, run). `justfile`: lines 17-18, the recipes at 46-150, `sessions`, `phases`, `tail`, `procs`, `obs`. Keep `test-all`, `ci` and the node import. `pyproject.toml`: comments 1-23, 35-36, 59, 66, 130-131, 226-229, `[tool.mypy]` 257-263, the ruff lines at 284 and 331, and 424 (425 is `_bmad` and stays). `testpaths` must change, not vanish: with the folder gone, a bare `pytest` has no target. My expectation, not run, is that it searches the whole tree. Point it at the real suites. `DEPENDENCIES.md:92-101`, `.env.sample:4`, `.gitignore:44-45`, comments in `tools/secret_scan.py:14,42`, `tools/coverage_report.py:26`, `skylos.yml:91`. Leave `mypy`, `types-PyYAML`, `pydantic` and the others in the `dev` group for now. Removing them changes `uv.lock`, and CI runs `uv sync --frozen`. A later step, with `uv lock`.
- **`scripts/probes`.** CI names no `scripts` folder (`git grep`, empty). Steps: Delete everything except `FINDINGS*.md`, because `qmx_router/gpt/translate.py:5` cites one. One real importer: `scripts/live/server/app2b_lanes.py:35,137` imports and runs `scripts/probes/server/p_app.py`. Move `p_app.py` beside it, or drop that lane when the live lanes go. Stale words only, no failure: `scripts/live/library/e66_marks.py:15`, `qma/s18_ram.py:6`, `qma/cat_lanes.py:327`.
- **QML and QMF usage examples** (`qml/examples`, `packages/qmf-{core,data,registry,risk,venue}/examples`, `extensions/qmf-calendar-forex/examples`). Not `examples/apps` (used by `test_apps.py`, `tools/lanes/*` and `docker-nodes.yml`) and not `qmf-indicators` (another agent's). Steps: Delete the folders. Delete each package's `test_*_examples.py`, `qml/tests/test_examples.py` and `qa/tests/epic_12/test_l3_example_bot.py` (3 fail, run), which the audit named. **Missed by the audit:** delete `qml/tests/test_conformant_bot.py` (5 fail, run);  drop `extensions/qmf-calendar-forex/tests/test_registration.py::test_reference_usage_example_runs_clean` (fails, run); edit `qml/tests/test_scaffold.py:26` (fails, run); edit `qa/tests/epic_11/test_a_scaffold.py:28` (fails, run); edit `qml/tests/test_generation_gaps_unfilled.py:60,380` (reads the folder; level 2, because my scratch lacked `qmx-agents`, which caused the two failures I saw there). `packages/qmf-venue/README.md:25-26`, `extensions/qmf-calendar-forex/README.md`, `pyproject.toml:344-346`.

`qa/tests/epic_12` builds its own `_world`, so the layer gates keep other tests (level 2, `test_l1_gate.py`). Keeping them green is the safety fact.
- **Hermes scripts.** Four files in `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-16/research/`: `query_hermes_sessions.py`, `dump_goldmine_range.py`, `dump_key_msgs.py`, `dump_strats_sessions.py`. No code names them; one evidence note does (`release/evidence/setup.md:47`). Delete them.
- **Order.** All four are one PR, first in time and independent of the rest. By the system's rule he lands it and deletion is his click. It removes about 40,700 lines and about 5,700 lines of tests by the audit's counts (8,883, 21,364, 10,166, 300; 307, 3,435, 1,973), and touches no product file. **Proof:** the full `tools/test_all.py` on that branch, by the orchestrator.

## 4. Corrections to the audit

| Row | Correction |
| --- | --- |
| triage-7 | Understated. It says the shared libraries refresh. They do not: the digest check runs only inside `install`. Repairs to `qmb`, `qml`, `qmf` and `qmn` do not reach an installed app either (run). |
| known-2 | Understated. The plain `timeout=` fix does not work on Windows (run), and an install also stalls every call to every app (run). Its reach includes his kill. |
| triage-5 | Size now measured: about 200 MB a day per app, rough. I would plan it before any soak. |
| p6-14 | Wrong grade. The copies are the design; `leave`. Do not count 1,900 removable lines. |
| p6-5, p6-15 | "Needs an engine change" is wrong. Both can be done with the engine as it is. p6-15 is proven on a fake Library, and p6-5 is read, not run. The p6 report's "Set aside" for these can close. |
| p6-8 | "Each stops until a workflow can read Library rows" is true of the scripts as written, but d3, d4 and l1 can take `b`'s shape. Only l4 and rs6 want a new read. |
| known-7 | Overstated; `leave`. |
| deletion-8, deletion-9 | Their step lists miss seven test files or lines, which fail when run. The conclusion stands. |
| Design files | G4b and `workflows.md` section 1 say the `library` node has no executor and should be unavailable. It has one and works. WF-08 is closed by a build, not by refusal. Do not "fix" it. |

Confirmed as written: p6-1 (rerun), p6-2's template half, p6-3, p6-4, p6-6, triage-4 (now level 4), triage-8 (now level 4), p34-9, p2-7.

## 5. What "works" means here

Each is a real run across a real connection.

1. **A repair lands.** Install a first-party app, change its file and its version, start the host's enable path: the new hash runs and its volume data is there. A library change reaches the app's environment. A money app keeps its signed version until he signs. (MA-05, WF-09.)
2. **An install does not stall the rest.** While one app installs slowly, a running app answers a call within a second. An install with a stuck child fails by name and the host carries on.
3. **Backtest to verdict.** Real QMB job, real lander, real `backtest_judge_run`, real scorecard, for one market and for a sweep: the trades counted, one certificate or one card, the right cause. (WF-12, AG-06.)
4. **A forged copy changes nothing.** A referee step that answers `pass` over a stored `fail` routes as `fail`. (AG-06.)
5. **The script gate and hook on a market only the Library knows.** A clean unit reaches QMB, and a broken one gets its error. (AG-01, AG-11.)
6. **A crash loop and a calm crash.** Repeated crashes double the wait, and a crash after long health waits 5 s. A money app comes back on its signed version. (MA-01.)
7. **A week of apps.** One running app writes a small, steady number of rows, and the store does not grow without end.
8. **Template update beside his edit.** Reinstalling a changed template publishes a new version, leaves an enabled trigger on what he enabled, and says a new version waits. (WF-09.)

## 6. PR clusters, in order

1. **Dead weight** (block K). Independent, about 40,700 lines gone. Subtract first.
2. **The way in** (block A plus B, one file). Install path, upgrade at host start, restart wait, event rows, answer-file retry. Shares `first_start.py` with `ground-start`'s p5c-3, so plan them together. Must land before any PR that edits `apps/*`.
3. **Verdicts true** (blocks C and D). Sweep trades, one paper, core's dead-end row, read-not-copied. Bumps QMB's version.
4. **Offline check** (block E), after `ground-qmb`'s records work.
5. **Slow-lane words** (block F), p6-9 first, any time.
6. **Later, research phase:** p6-6, p6-11, p2-7, p6-10, then p6-8 with the one U1(c) question.

## 7. New defects

- **core-n1, must.** `supervisor.py:443-469`: an install holds the lock through `uv sync`, so every call to every running app waits for it, including the node's kill path, and for ever with known-2. Level 4 for the wait, level 2 for the kill route. Block A.
- **core-n2, should.** `plugin/hooks/hooks.json:10` runs a bare `python -c`. The hook works only if the first `python` on the CLI's PATH is the host's environment. On this machine a bare `python` is a Windows stub that hangs, per the audit's own rule. Under `uv run`, PATH has the environment first, which is how A14's probe passed. A host started another way would make every Write or Edit in every chat wait out the 8 s timeout and give no feedback. Level 2, unproven; I am not allowed to run a bare `python`. What would prove it: start the probe's command with the venv off PATH. Shape: the harness puts its own interpreter's folder first on the CLI's PATH.
- **core-n3, should.** `install.py:80-81` adds new disabled triggers on every published version, and `install.py:58-60` writes the shipped draft over the item's draft if it differs. So a reinstall can replace an edited draft head and pile up disabled triggers. The store keeps history, so nothing is lost. WF-09 asks for "beside". Level 2, not run.
- **core-n4, leave.** The `settings.memory.scopes` key in template definitions is read by no engine code I found (`grep` of `.snapshot(`). The memory the agent sees comes from the home's snapshot file. Harmless, and misleading to read. Level 2.

## 8. Set aside for him

- The engine's one possible change, U1(c), a script read of a family's tries. I assumed it waits for the research phase, and that U1(a), (b) and (f) are withdrawn because the engine as it is does them. He may still want them; a plain "no" to them costs nothing today.
- Whether a stuck install should be stopped at 30 minutes. I assumed yes, as a setting, because it stops no usage.

## 9. Needs a long run

Run from the audit copy. The first is the p6 report's own, to confirm M-promises before cluster 2. The second proves the examples and factory detach.

```bash
source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head/qmx-agents/packages/qmx-apps && timeout 1200 "$AUDIT_AGENTS_ENV" -m pytest tests/test_apps.py tests/test_landers.py tests/test_restart_backoff.py tests/test_road_runtime.py -q -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-core/long1
source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/Temp/audit/ground-core/cut && PYTHONPATH="$PYTHONPATH;D:/Temp/audit/ground-core/cut/qml/src" timeout 1200 "$AUDIT_ROOT_ENV" -m pytest tools/tests qml/tests -q -n 4 -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-core/long2 -c pyproject.toml --rootdir=D:/Temp/audit/ground-core/cut
```

The second will show exactly the failures named in block K and no others. `qmx-agents` is absent from the scratch copy, so `test_generation_gaps_unfilled.py`'s two failures are expected there.

## 10. Not reached

- U1(d) and U1(e): not traced, not in my problems.
- The real `library` node read on the real store for `verdict` kinds: level 2.
- Whether a template install on his folder happens on any path but the CLI and REST: I found none in `first_start.py` or `tools/`.
- A real `uv` run through the new install shape: nothing was built here. uv was patched out in my proofs, except the audit's p6 test, which installs through the supervisor as the shipped tests do.
- `test_generation_gaps_unfilled.py` on a whole-repo scratch.
- The qmx-ui's reading of app events, out of bounds.

Principles that changed a call: **subtract-before-you-add** put dead weight first and turned D into a removal; **blast-radius** moved triage-7, known-2 and p6-15 from reading to running, and overturned two of them; **codebase-design**'s deletion test settled p6-14, because the hash's reach is what the copies earn.
