# Grounding: what crosses between the node, the host and him

Commit `50c83a4e`. Proof scripts are in `D:/Temp/audit/ground-start/`. Levels are the system prompt's. Nothing was changed, the host was not booted, and no real credential was read.

## 1. What this area is and how it really works

The node writes every row itself into append-only files in its own folder, and never waits for the host. Once a minute the host's records job (`qmx_host/records.py`) reads those files, files them into the machine's market store, and on This PC turns trade rows into Library `trade` items and `paper-run` scores. The storage under it is older October code (`qmf-data` series store, the door, the one-writer stream store) and it works. Alarms leave from the node itself by ntfy and Healthchecks, using an alarm list parsed from `qmn/FAILURES.md`. Deep logs leave from the host through the engine's one exporter to OpenObserve, and the local files stay on disk. The MIS is a mini app that starts by itself and does nothing until something calls its `configure` operation, and nothing does. His click goes through `qmx_host/promote.py`, which checks the lifecycle table in `qml/lifecycle/machine.py`, builds a deployment document, and sends it through the node link's outbox, which only `deploy` and `withdraw` use (`promote.py:375`, `:448`). The host itself runs from the source checkout, but apps run from wheels built by `uv sync --no-editable` (`supervisor.py:527`), so an app cannot see anything outside its packages. `tools/first_real_start.py` drives all of this over REST and prints one line per fact, and the server path (`connect_node.py`, C-17) is the same steps over SSH, so far run only against a simulated host.

## 2. What must not break

- A write to a live stream fsyncs before the node acts. One writer per stream. Readers never change the files. Guarded by `test_harvest.py`, `test_records.py` (13 tests).
- A QMB run fails at `close()` when a reason has no code. Keep this: it protects evidence. Nothing in `qmb/tests` or `qmn/tests` pins it by the words "closed list" (searched), so a repair needs a test that does.
- Repeated click, same op id, same answer: `test_promote.py`. Node side: `test_a_direct_call_gets_an_op_id_and_a_repeated_op_id_answers_its_first_answer`, ran, 1 passed.
- Only `operator` passes promote. `draft` to `paper` is refused. The lifecycle table stays as it is. The refusal is correct behaviour and must stay.
- Script's REST-only rule, refusal before reading a credential, convergence on rerun: `tools/tests/test_first_real_start.py`, ran, 14 passed.
- `enable_first_party` starts each app at every host start: `test_first_party_node.py`, ran, 5 passed.
- The C-38 env test (`tools/tests/test_app_env_data.py`) builds real wheel envs. It is the right home for install checks.
- Deep logs never touch trading. A failed post drops and counts, by design (`app_logs.py:8-10`, DEVOPS-CLOCKS.md section 4).
- The MIS never reaches the order path. A unit trades with the MIS stopped (MIS.md section 10).

## 3. Problems

### A. The node's journal dies silently, and its trades never reach the Library (seams-3, p0b-4, p34-1, p34-10)

- **Real cause, journal.** `journal.py:376` and `:305` set `_refused` for a text with no code. `journal.py:259` then drops every later row. `append` returns None, `_Journal.append` (`runtime.py:1297`) ignores it, and only `close()` reports it, which the node never calls. Design JR-13 says a refusal becomes "no new entries" while exits go. That half was never built.
- **Worse than filed.** My census runs every text the order path, guard and reconciler can write through the real table. It found 3 of 32 Blocked and guard texts with no code: `runtime.py:1007`, `:1186`, `:2301`. Add `:1609`, which reaches the journal through `Unprotected`, not `Blocked`. So four texts, not two. Seams proved `:2301` by running it, and `:1609` is the same result by the table. I did not walk whether `:1007` and `:1186` reach the journal. Level 4 for the census (`census.py`), level 2 for those two.
- **Real cause, trades.** `RunJournal._facts` (`journal.py:247`) sets no account. `records.py:527` and `:567` return None without one. Ran `p34/p1_trade_account.py`: as written, trades=0 paper_runs=0, with the account set, trades=1 paper_runs=1.
- **Around it.** `open_live` has one caller (`runtime.py:2421`), which holds `deployment.account_id`. Account is not in the partition key, so no series moves. Backtest worlds are not projected. Readers of the rows: `Projection`, `journal_query`, promote's calibration harvest (p5d traced its identity, it does not use account).
- **Safety fact.** The field only adds to a row, and the proof's control run shows the rest of the path already works once it is set. Level 4.
- **Shape.** One place, `RunJournal`. `open_live` takes `account`. It also becomes tolerant: on a live journal, a text with no code writes the row with one new appended code (design: "closed and appendable"), so an unlisted word costs a label and not the journal. `open` (QMB) stays strict. Add the four texts to `_REASON_WORDS`. Expose a real write failure as a read-only property, and have `guard.check` (`runtime.py:2269`) answer "the node journal could not be written", which already maps to `health_stop` and stops entries only. The status word stops saying Trading. Exits are not touched.
- **Proof.** Real writer to real records job with no patch: trade and paper-run land (fails today). Then one entry blocked with each of the four texts: rows keep landing. Then the census as a test, so a new text with no code fails CI. Replace the hand-written accounts at `test_harvest.py:95-103` and `test_no_bot_writes.py:47-54` with rows from the real writer (p34-10).
- **Order, files, size.** First of all, because everything about records rests on it. `qmb/results/journal.py`, `qmn/app/runtime.py`, two test files. About 60 product lines, 60 test.
- **Whose.** Ours. `cross_unit_hook` is plumbing around a placeholder.

### B. Phone alarms off on an installed node, and the class around it (chief-2)

- **Real cause.** `alerts.py:251` climbs to `parents[3]`, which in a wheel is `Lib`. `qmn/FAILURES.md` is not in the wheel. `alarms.py:708-710` turns off every sender, including Healthchecks, with one stderr line. Ran `alarm_wheel.py`: refused, `push: None`.
- **The class, searched in full.** I read every `__file__` and `parents[` in `qmn`, `qmb`, `qml`, `qmf-*`, the extensions, and the three apps, and searched `qmn/app`, `venue`, `time` and the app servers for relative paths and `.md` or `.toml`. Result: **this is the only one on a running app's path.** The others are not reached by an installed app: `failures_gate.py:677` (a CI gate), `bench/baselines.py:146` (bench only), `containment_limit.py:830` and `qa_debt_matrix.py:149` (old node, C-20's list), `qmb/doors/cli/host.py:54` (a command line, checks the path exists first), `regime_train.py:2079` (never-run code, has a fallback), `qmf/core/_bench.py:49` (bench). `seats/admission.py`, `runtime_risk_gate.py` and `failures_gate.py:405` climb only inside the package. `proto_runtime.py:17` is C-38's fix and is right. The apps' own `packs.json` and `app.toml` live in the app folder the supervisor installs. Level 2 for this search, since no app env was run.
- **Around it.** `load_alert_allow_list`, `failures_gate.py:508`, `readiness.py`, `qa_debt_matrix.py:607` (names the path as text), `qmn/tests/test_qmn_failures_gate.py`.
- **Safety fact.** `uv_build` carries every non-Python file under `src/qmn`, as `openapi-91.pb` shows. With the register inside the package and the two path functions pointed there, the wheel layout loads it and `attach` returns a real `PushSender`. Level 4 (`alarm_wheel.py`, on a copied layout). The real wheel build is the long run below.
- **Shape.** Move the file to `qmn/src/qmn/observability/FAILURES.md`. Change `default_failures_path` and `_failures_root`. Add one read to `NODE_READS` in `test_app_env_data.py`. Also put "alarms off" in the node's `status` reasons, because silent off is the real failure and stderr reaches nobody. Do not split `_off`, it is one place.
- **Proof.** Built env loads the register, and a push reaches a loopback ntfy.
- **Order, files, size.** Early, alone or with C. About 20 lines. Whose: ours.

### C. Deep logs (known-10, known-11, known-12, triage-9)

- **Real causes, all run in `logs.py`.** known-10: `record_of` lets `RecursionError` out, `run()` catches only `OSError, ValueError` (`app_logs.py`, the `run` method), the task ends, and the cursor was not saved, so a restart dies on the same line. known-12: `log_of` takes the body from `message` or `kind`, supervisor lines carry `event`, so every one reads `app_log` at INFO. triage-9: `telemetry.py:458` builds the body above its `try` and the thread has no guard, confirmed raising. `_sent` protects shipped lines, but heartbeats and spans go through the same post.
- **known-11 is half right.** The doctor row is red until restart because `dropped` only grows (`doctor_line`). That is a defect. "Waiting lines are lost" is the module's stated design, the local files keep them, and I would not change it.
- **Safety fact.** All of this sits off the trading path: the exporter has its own thread and timeout. Level 2. TN-28's check covers it.
- **Shape.** `record_of`: also catch `RecursionError` and send the line as text. Move `event` to `message`, and map a short list of supervisor events to `error`, inside `record_of`, so the mini-app core is untouched. `run()`: catch `Exception`, since a shipper that ends is worse than one that logs. `telemetry.py`: move one line inside the `try`. Doctor: red only when the last post failed, still naming the count. The engine package changes by one line, and it is the exporter, not the workflow core.
- **Proof.** A 200,000-deep line ships as text and the next line still ships. A `breaker_open` line reads as an error in OpenObserve. Outage then recovery leaves the doctor green with the drop count shown.
- **Files, size.** `app_logs.py`, `telemetry.py`. About 30 lines. Same PR as B.

### D. A new alarm address on a running node (p5a-12)

- **Real cause.** `server.py:953-956` reads `NODE_KEYS` once. `rotate_keys` rebuilds from the same text. The node "never reads a key store" (`server.py:376`).
- **My call.** Do not build a way to pass keys into a running node. Sending secrets as tool arguments adds a risk for something that happens rarely, and `_rotate` (`connect_node.py:410-415`) already restarts at the next safe moment and says so. Change the plan's C-30 pass line to match, and delete the no-op re-registration only if that test goes with it. What goes wrong today: a changed address waits until he is flat. Worth one line of plan, not code.
- **Size.** About 10 lines. Whose: ours.

### E. The MIS (p34-2, p34-3, p34-4)

- **Real cause.** p34-2 is right that nothing calls `configure`, but **calling it is not enough**. `mis_core.py:573` defaults `source` to the record's venue, and `MarketData._keys` looks in `<source>/<symbol>/bar-m1`. Ran `mis_real.py` with the record C-34 really lands: configure accepts it, a round publishes **0 readings, silently**. With `source` naming where the bars are: 4 readings. The node will not fill that folder either. `append_series` has no product caller (searched), `Recording.add` writes a `bar` journal row, and the design's "recorder writes series rows" was never built.
- **Second limit.** Only EURUSD and XAUUSD have records, and only after sign-in (p5d-5). So before his demo sign-in there is nothing to configure from.
- **p34-3.** `server.py:64` has no guard. Proof stands from p34; I did not rerun it.
- **Around it.** `readings_query`, five templates, the board. The relay reads the board file and falls back safely (TR:49).
- **Safety fact.** The MIS is not on the order path, so wrong or empty configuration costs only readings. Level 2, with the invariant in MIS.md and p34's "units stand alone" check.
- **Shape.** One small host job beside `VenueRecords.round` (`venue_records.py:412`), This PC only. For each `instrument` on Library main, find which source in the store holds `bar-m1` for its symbol, and call `configure` with an op id that is the fingerprint of that list, so repeats do nothing. A market with no bars is named in `status`, not silently empty. That meets MIS.md's "This PC configures its own instance". `rounds()` gets a guard and records its last error in `status`.
- **p34-4.** Not this pass. The missing readings are block work, and some of what they need sits in the never-run regime code (p34-14). **Do not delete p34-14 before someone decides this.** Cross-market has nowhere to run yet.
- **Proof.** On a real host: a download lands, the job runs, `readings_query` answers, then one read error and the next round still publishes.
- **Order, files, size.** After A. `venue_records.py` or a small new file, `host.py` wiring, `apps/mis/server.py`, `mis_core.py` status. About 100 lines plus a test. Whose: ours, MIS third in his order of care.

### F. Recording at scale, and the "why" answer (p34-5, p34-6, p34-7, p34-8)

- **The trap that shapes all of this.** `Projection._paper` (`records.py:736-741`, `:769-773`) scores only the rows it is handed and overwrites the score when it differs. Today it is handed the whole history, so it is right. **Any repair that hands it fewer rows silently rewrites a paper score with fewer trades.** p34-6 and p34-8 both walk into this if done separately. Level 2, by reading.
- **Real cause, p34-8.** `read_committed` re-parses every rotation file (`journal_reader.py:60`), and `Harvester.round` hands every line on (`records.py:399`). Measured in SPOT-CHECKS: at 1,000,000 rows, 30 to 39 s and about 3.3 GB every minute for one new row.
- **Real cause, p34-6.** `Records.round:1376` projects only harvester lines; `Pull` commits to the door and returns counts.
- **One repair for both.** `Projection` reads `trade` and `lifecycle` partitions from the market store, not from stream lines. The store holds local and pulled rows alike and every month, and a round tells it which keys it committed. Only the harvester then needs bounding: rotation files are 8 MB and the writer only appends to the last (`jsonl.py:53`, `:264`), so a stream remembers the first file holding an unfrozen month and reads from there. The open month is still rewritten whole, as the design says.
- **Safety fact.** Older rotation files never change. Level 2. Unproven by running. The proof is that same million-row run after the repair, plus a test that a second round scores the same as the first.
- **p34-5, journal side only.** `minute` is registered (`node.py:49`) and nothing writes it. The place is `Recording` with `FeedKeeper.pump`, which see every quote and hold the market writer. **Trap:** `journals.py:279` matches a minute by the row's write time, so a row written at the close of 08:00 reads as 08:01. Write it so the two agree. Fees and slippage stay out, they belong with the cost work.
- **p34-7.** `journals.py:321` adds the tail file. Small, at G-SERVER.
- **Order, files, size.** After A. `records.py`, `journal_reader.py`, `feed_keeper.py`, `journals.py`. About 200 lines. p34-7 and the Pull trigger can wait for the server gate.

### G. Promote's edges (p5d-1, p5d-2, p5d-3)

- **p5d-1, confirmed and repair proved.** `tool_timeout` is not in `WAITING_CODES` (`node_link.py:69`). With it added in memory (`proof_waiting.py`): first click 200 queued, one move, one deployment. Same click again: accepted, still one. A new click: refused `paper to paper`, still one. Today the second click makes two. Level 4 on the rig's fake node.
- **Understated.** The real supervisor **stops the app** on that timeout (`supervisor.py:1195`), and a stopped app stays down (`:1009-1015`). So the retry reads `not_running` and keeps waiting until the node returns. See New defects.
- **Safety fact.** Only deploy and withdraw use the outbox, and each carries a stable op id that the node answers with its first answer. Level 4 for the node's memo (the test named above), level 2 for the two callers. `test_node_link_refused.py:126` and `test_promote.py:88`, `:563` pin today's wording and change with it.
- **p5d-3.** A deploy refused later leaves paper with nothing running, and the table has no way back. **Leave the table alone.** In `_admit`, when the market already reads the target and the node says it holds no live deployment for it, deploy again without recording a move, pointing at the existing move. If the node cannot answer, refuse as today.
- **p5d-2.** `host_route.py:311` wraps `files_missing` as `app_refused` and `:299` keeps it. A waiting code must be neither wrapped nor kept. Bites at G-SERVER only, with C-19.
- **Proof.** The p5d scripts, turned around. Real node stalled past 30 s: one deployment after it returns.
- **Order, files, size.** Any time after A. `node_link.py`, `promote.py`, then `host_route.py` at the server gate. About 60 lines plus tests.

### H. Agents and the Library's main line (p5d-6, triage-3), before any live account

- **p5d-6.** `tools.py:1093-1096`. A row naming the wired credential must name its venue. Three lines, and flip `test_a_row_with_no_venue_is_never_checked`. It takes his own hand edit to trigger, so grade stands. Cheap enough to do with G.
- **triage-3.** `_his_click` (`service.py:1582`) guards only `unit`. **Two doors, not one.** `account` is class `record` (`account.schema.json:4`), so a passed `publish = auto` run fast-forwards it onto main (`landing.py`) without passing `_his_click`. Widening that function alone closes half.
- **Safety fact for the wait.** The node proves the world itself (`runtime.py:2408`) and refuses a live lane on a non-demo binding, and a paper lane sends nothing to the venue. So a forged account record cannot reach real money while only demo is bound. A wrong instrument record can still distort size on demo. Level 2.
- **Shape.** Promote reads account, venue and instrument from main at `promote.py:353`, `:519`, `:568`. Add one rule at that seam: it accepts only versions written by the host's C-34 path or by him. That closes both doors in one place and touches neither the landing rule nor the store. Unproven; check that versions carry a usable writer before planning it.
- **Size.** About 40 lines. Gate: before any live account.

### I. First start (plan-check-1, seams-1, p5c-1, seams-13, p5c-2, p5c-3, p5c-4, whole-repo-1, whole-repo-2)

**What the script's job becomes.** Today it says "prove the dummy trades on his demo." By his word the foundation comes first and the dummy does not skip the judge, so that job is gone. **New job: prove that this machine's node is ready to receive a unit, on his real folder.** It stops there. A unit reaches a node by passing the judge and his click, and the script does not make that happen. Showing that agents can build and backtest a unit belongs to QMB and the copilot, not here.

| Step | Still right? | Change |
| --- | --- | --- |
| Code landed | Right intent, wrong branch | `--landed-on`, default `engine/base`. FOR-HIM's default matches his words this morning. Local `engine/base` is 732 commits behind origin, which does not matter since the gate reads the origin ref |
| Folder found | Right | None |
| Practice node Ready | Right | Rests on the install wait and p5c-3 below |
| Demo session ready | Right, waits for G-DEMO | `ctid` against `traderId` stays unproven until a real token |
| Test trade with stop | Right | Shares proofs with C-15 |
| Passport landed | Right | None |
| Dummy deployed | **Wrong as written** | Becomes `--unit <id>`. With none named it prints one plain line, "no unit has passed the judge yet, so nothing was deployed", and that is **not** a FAIL. The `DUMMY` lookup goes |
| Node journal rows | Right | None |
| Test trade rows | Right | None |

- **Real causes.** `landed_refusal` (`:566-575`) hard-codes main. `_deployed` (`:472`) assumes a tested dummy, while `land_dummy` (`first_start.py:656`) puts a draft and the table is correct to refuse it. `_deployed` reads once (`:489-497`) and passes at `compiling`. `enable_first_party` (`first_start.py:624-627`) stops at the first refusal, node last.
- **Rehearsal.** Keep its two fixture rows, labelled, but only for a run that passes `--unit`, so the deploy crossing stays proved. They must never again stand behind an all-PASS on the plain path.
- **seams-13, p5c-2.** Poll the node's `deployments` row past `compiling` until `warming up`, `trading`, `waiting`, or `refused` (`Phase`, `runtime.py:1708`), within `--trade-s`. A refused row is a FAIL with the node's own words. The fake host in `test_first_real_start.py` must learn to turn a row to refused.
- **p5c-3.** Each app gets its own try in the loop; the loop names who failed and carries on. Same thread as known-2, the uv wait with no limit (`supervisor.py:527`). Do them together: a hung install stops the same loop.
- **whole-repo-1, 2.** Three `# ambient-scan: allow` markers, since this script really is a composition root, and 9 small type fixes. `test_ambient_scan.py` stays red until the two `tools/lanes` files get the same.
- **Plan lines to change.** C-14 You see (PC:3787), C-14 lane 5, and C-20's gate (PC:4169), which waits on an all-PASS `c14-real.log` and no longer implies any unit traded. The planner must say what C-20 waits on instead.
- **Safety fact.** The script talks only REST, so changing what it checks cannot change the product. Level 4 for today's behaviour (14 tests, real throwaway git repositories for the landing gate).
- **Proof.** Rehearsal on a fresh folder with no fixtures: every line PASS, and the "no unit" line. Rehearsal with `--unit` and fixtures, then a node that refuses: FAIL. Host start with QMB broken: node still up.
- **Order, files, size.** p5c-3 and known-2 early, with B. The script's changes last, after A to E, because nothing should run it on real keys before then. `tools/first_real_start.py`, its test, `owner_lane_c14.py`, `first_start.py`, `supervisor.py`. About 60 net lines in the script, 80 for the rest. Note the audit's "about 400 lines" for cluster 1 included dummy warm-up and history, which this no longer needs for the script to end.

### J. The uncommitted edit (settled)

- **How the host stores it.** `qmx_control/server.py:67-70`, `keyring.set_password("qmx/control-token", "control-token", token)`. On Windows, keyring's backend keeps it under the service name and moves the previous value to `user@service` whenever anything writes that service again (`keyring/backends/Windows.py`; I checked this file's hash against its RECORD, because RESUME says a review tripwire was cut out of it).
- **Proof.** `bearer.py` runs keyring's real backend over an in-memory store, read by both versions of the script:

| Step | keyring reads | Script at this commit | With the edit |
| --- | --- | --- | --- |
| Host mints it | right | right | right |
| Written again, same user | right | right | right |
| Another user writes this service | right | **wrong value** | **wrong value** |
| That user deleted | right | **none** | right |

- **Verdict.** The edit is correct as far as it goes and harmless. It is half of keyring's rule, because keyring also compares `UserName`. No product code writes that service under another user (searched), so neither failing row can happen today. **Do not carry it as is.** If this reader is kept, read `UserName` from the struct it already declares and follow the same rule, about 4 lines. UTF-16 decoding is right (win32ctypes source, level 3). The reader itself has **never run on a real entry**: `owner-c14-bearer.log` is 0 bytes. See long runs.

### K. Stacks (settled)

**Nothing is needed in git.** `build/us-c14` equals its origin at `50c83a4e`, and `build/us-c35` equals its origin at `f9607cd4`, which is its direct ancestor, 4 commits down. A branch from `build/us-c14` holds C-35, C-29, C-38 and C-14. `build/us-c15` and `build/us-c19` are empty leftovers with no commits of their own. What a builder must know:

1. **RESUME is wrong on one point.** It says PR 327's blocker has its "proven cause fixed" in `50c83a4e`. That commit fixes a heartbeat lock. The blocker the review named, the uv wait with no limit, is still at head (`supervisor.py:527`). Carry it as open.
2. **C-14's four commits, 1,542 lines, have never been reviewed**, and PR 328's body is a placeholder. The first repair's reviewer must cover them, or they land unread by anyone.
3. The edit in `D:/QMX-worktrees/bld-us-c14` is not on the branch. A new branch does not carry it. Per J, leave it out.
4. The base is red before any repair: ambient-scan, root types, the known test reds. Use `audit-ship/tests/SUMMARY.txt` as the parent's baseline.
5. Do not edit a venv file. uv's hardlinks reach every env, which is how the tripwire happened.

### L. Servers, later gate (plan-check-4, p5c-5, C-19)

- **plan-check-4.** True. Cards today: `ctrader-app`, `signature`, `openobserve`, `sign-in`, on top of Tailscale and the password window (`prs/c17.md`). R:30 allows keys in their own window. `signature` can go: the host's own sign route already answers it, as `first_real_start.py:_signature` shows. Tailscale, password and approval I did not walk.
- **p5c-5.** `connect_logs.py:515` exits 3 with no programs. `_openobserve` (`connect_node.py:1259`) then returns a card, and `first_waiting` shows the first card, so it comes before sign-in. The node trades without it, so the order is wrong regardless. Shape: install both pinned programs in that step. If that cannot run, it says so and does not hold the sign-in card.
- **C-19.** Still wanted, as planned: `app_updates.py`, `safe_to_restart`'s two skipped checks, and the rerun that never upgrades (`connect_node.py:335`). p5d-2 and p34-7 belong in the same gate. `build/us-c19` holds nothing, start fresh.
- **Size.** About 150 lines for the cards, C-19 as the plan sizes it. Nothing here touches This PC's path.

## 4. Corrections to the audit

- **seams-3 understated.** Four texts have no code, not two.
- **seams-1, p5c-1.** True facts, wrong remedy for today. The refusal is right. Their "labelled shortcut" and FOR-HIM item 2's default ("yes, by one labelled route") are closed by his words in SEEDS. The repair is to the script.
- **plan-check-1.** True, but no longer a must on today's order, since the script's real run moved behind the foundation. A must on the day he runs it, and a small repair.
- **p34-2 understated.** Calling `configure` alone publishes nothing.
- **p5d-1 understated.** The node is stopped as well. Its "one word" repair does hold.
- **known-11 half overstated.** Dropped batches are the design. Only the doctor row is a defect.
- **triage-3.** Worst case bounded by the node's own check, and there is a second door.
- **Cluster 1's size** of 400 lines falls, since warm-up history no longer has to serve the script.
- **RESUME's claim on PR 327** is wrong, see K.

## 5. What "works" means here

1. A wheel-built node env loads the alarm list, and a real alarm reaches a loopback ntfy. Status says so when alarms are off.
2. The real node blocks an entry with each of the four texts, and rows keep landing on disk and in the store.
3. A real node trade travels writer, harvester, Library: one `trade`, one `paper-run`, unchanged by a second and third round (JR-08, JR-16).
4. Host start on a fresh folder with QMB broken: the node still starts, and the failure is named (OP-01).
5. A real download, the configure job, a round, `readings_query` answers, then a read error and the next round still publishes. The MIS stopped: a unit still enters (MIS-01).
6. A deploy stalled past 30 s against a real node: one deployment once it returns, and a click after a refused deploy deploys again.
7. The script on a fresh rehearsal folder with no fixtures: all PASS and the plain "no unit" line. With a refused unit: FAIL in the node's words.
8. OpenObserve stopped, then back, with a pathological log line: the doctor returns to green and trading never noticed (TN-28).

## 6. PR clusters, in order

1. **The node's records are true.** A. Everything else rests on it. Real connection test included.
2. **What reaches him.** B, C, D's plan line. Small.
3. **A start cannot hang or stop halfway.** p5c-3 with known-2.
4. **Promote's edges.** G, plus p5d-6.
5. **The MIS publishes.** E, without p34-4.
6. **Recording holds up over months.** F. Projection from the store first.
7. **The script's new job.** I and J. Last, with the plan lines changed.
8. **Later gates.** Live: triage-3, C-21. Servers: L, p5d-2, p34-7.

Shared files with other areas: `qmn/app/runtime.py` (node truth repairs), `supervisor.py`. A and the node cluster should agree who goes first.

## 7. New defects

- **A 30 second stall stops the trading node for good.** `supervisor.py:1191-1196` calls `self.stop(app_id)` on a tool timeout, and `stop` cancels healing ("a stopped app stays down", `:1010`), though the node's manifest asks `restart = "backoff"` (`app.toml:26`). What goes wrong: one slow call during open trades leaves the node down until the next host start, with only broker-side stops working and no alarm from the node. `should`, level 2, I did not run it. Whose: the mini-app core, his. The reason to touch it is the node's own intent, that it heals itself. Shape: an app that opted into back-off goes down the healing path on a timeout. Check against his three-error breaker first.
- **Bars the node records cannot be read as bars.** No product code calls `append_series`, so the node's `journal-market` `bar` rows never become `bar-m1` partitions, and the MIS on a node machine finds nothing. `should`, level 2 for the search, level 4 for 0 readings. Node bars are 15-minute today (seams-5), so settle this with that repair.
- **`real_bearer` ignores `UserName`.** `leave`, see J.

## 8. Set aside for him

Nothing new. FOR-HIM item 2 is closed by his words this morning and should come off his list. Item 1 no longer blocks a repair: I assumed `engine/base` as the option's default, and he can name another branch by flag.

## 9. Needs a long run

Each after `source D:/QMX-worktrees/audit-ship/tools/env.sh`.

- Real wheel env baseline for B: from the audit copy, `timeout 900 "$AUDIT_ROOT_ENV" -m pytest tools/tests/test_app_env_data.py -q -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-start/env`. It builds envs and calls uv, so run it where the orchestrator allows uv.
- Promote and records suites for G and A: from `qmx-agents/packages/qmx-host`, `timeout 600 "$AUDIT_AGENTS_ENV" -m pytest tests/test_promote.py tests/test_node_link.py tests/test_node_link_refused.py tests/test_harvest.py tests/test_records.py -q -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-start/host`.
- The bearer reader on a real entry. `evidence/c14/owner-lanes.md` names it: `owner_lane_c14.py bearer <wt> 18941`, on a throwaway entry outside `qmx/`. The audit's guard blocks it by design. It writes to the real Credential Manager, so it belongs to a builder's owner lane, never the audit.

## 10. Not reached

- Whether `runtime.py:1007` and `:1186` really reach the journal. The repair covers them either way.
- Whether Library versions carry a writer usable for H's rule.
- p34-4's block-by-block census.
- The Tailscale, password and approval parts of C-17's walk, and C-19 beyond reading its plan section.
- The stop-on-timeout defect was read, not run.

Principles that changed a call: `blast-radius` sent me to the keyring source and to `_paper`, which is what p34-6 and p34-8 would have broken. `subtract-before-you-add` removed the dummy step, and kept p5a-12 and known-11's loss as no-code. `prove-it-works` turned p34-2 from "call configure" into a run that published 0. `codebase-design` chose one seam for F and for H.
