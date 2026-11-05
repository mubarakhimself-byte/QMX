VERDICT: REPAIR

## 1. What this part is for

This part joins the pieces of the trading system. His click on a unit records the move and sends the unit to the node with everything it needs (C-23). One node link and one host route are how a host asks a node anything, here or on a server, and a change to a node that is down waits and applies once (C-06). After sign-in, the node's own reading of cTrader becomes the account, venue and market records that promote needs (C-34). Agents get cTrader's MCP on demo accounts only (C-36) and cannot read a trading grant (C-25), and no app can name the host's own keys (C-27). The rest is plumbing that keeps it honest: logs shipped to OpenObserve (C-04), grants that never leave the machine (C-05e), server secrets (C-05d), fresh installs (C-26, C-26b), one deadlock fixed (C-33), gold prices at the right scale (C-31) and the example apps moved off his bearer (C-27a).

## 2. Counts

Files opened 86 of 86. Lines read about 12,100. Test functions read 132 (122 in whole files, 10 new in diffs). Hollow tests 0; deletable tests 3 groups, about 58 lines. Findings: must 0, should 6, leave 4. Lines that could go: 86 (28 slop, 58 tests). If he cuts the board feed (section 10), 807 more. Part size 4,896 product lines; my guess at a plain version is 4,200, labelled a guess. The extra is mostly promote's careful undo paths, which earn their place.

## 3. Paths traced

**His click to the node (C-23).** Door, principal check, fold, G report, records, deployment document, staging by fingerprint, node, then the lifecycle row. Sound for the normal case: only `operator` passes, a repeated click lands nothing, a record that fails after the deploy withdraws it. Two defects at the edges: a timed-out deploy (p5d-1), and a queued deploy the node later refuses (p5d-3).

**A change to a node that is away (C-06).** Outbox, back-off, host route, op-id memo. Works when the node is down: a queued change applies once, in order. On a server, `files_missing` is wrapped and memoised, so it never waits (p5d-2). This PC is not affected.

**An agent reaching a secret or a live account (C-25, C-36, C-27).** I ran 40 spellings through the real guard, 20 on a grant and 20 on a fixed secret. Every spelling that names a grant or the folders holding one is refused, including `cd` then `cat`, `tar`, `find -exec`, `python -c`, `xargs`, `$(...)`, PowerShell and `[IO.File]`. One case passes for both: a path decoded at runtime from base64. That is the limit of any string check and is no worse for grants, so it is not a finding. The demo check works for the `ctrader` row; a hand-made row with no venue skips it (p5d-6).

**Gold from download to backtest (C-31).** The card now states the right scale. The real host QMB run reads CSV bars, so a real backtest never reaches the typed tick reader. That reader ignores the card and reads gold at scale 5 (p5d-4).

**Node read to Library main to promote (C-34).** `world` comes only from cTrader's live flag. Volumes convert correctly to lots. The closed schema refuses a token field at put. A second land with the same facts adds no version. Only the two named markets ever land (p5d-5).

## 4. Sections

| id | origin | verdict | blast-radius fact, level | keep, fold or cut |
| --- | --- | --- | --- | --- |
| C-05e | original | met | C11 held, level 4 (ran `test_volume_grants.py`, `test_classes.py -k grants`) | - |
| C-04 | original | met | Loopback binding unchanged held, level 2 (`connect_logs.py:186-191`) | - |
| C-05d | original | met | C8 held, level 2 (`test_server_secrets.py:111` read, not run) | - |
| C-06 | original | met, with p5d-2 | Five host-pass routes held, level 2 (`door.py` `FORWARD_ROUTES` plus `HOST_PASS_ROUTES`). Homed-here local path held, level 2 (`test_node_link.py:93`) | - |
| C-23 | original | met, with p5d-1 and p5d-3 | His click is `operator` held, level 4 (9 passed, `-k "principal or forged or illegal or twice or no_agent"`) | - |
| C-22 | original | partly | A down MIS never stops a unit held, level 2 | - |
| C-26 | added | met | Root `uv sync` same lock not proved, level 2; I may not run uv | keep: stale code on the money path was real |
| C-25 | added | met | Fixed secret paths still refused held, level 4 (my matrix) | keep: agents could read a grant before |
| C-31 | added | partly | Scale 5 byte-for-byte held, level 2 (fingerprint pin at `test_download_dukascopy_scale.py:119`, made by the parent script) | keep: gold was wrong by 100 times |
| C-27a | added | met | Results without `outputs` land as before held, level 2 (`test_job_outputs.py:160`) | keep: C-27 could not land without it |
| C-27 | added | met | Every shipped app installs, level 2 (test read, not run) | keep: the bearer could promote to live |
| C-26b | added | met | Same as C-26, level 2. Departure: reinstall by changed file list instead of a key over the file list; `test_app_env_fresh.py` proves deletion | keep: qmf-risk and qmf-venue were stale |
| C-33 | added | met | Door callers answer as before held, level 2; the lock is released before every hop in `service.py` | keep: a real deadlock on enable |
| fix-research-test | fix | met | None named. Only that test file changed | keep: it repaired 2 red tests |
| C-34 | added | partly | No other kind lands by this path held, level 2 (`venue_records.py:273`, `test_venue_records.py:355`) | keep: nothing landed these records before |
| C-36 | added | partly | A row with no venue skips the check held, level 4; that fact is itself p5d-6 when the row carries his token | keep: his direct ask |

## 5. What is fine

- **Promote's principal rule.** Every caller but `operator` is refused before the body is read. A principal forged in the body is a bad request. It is no catalog row and no agent tool.
- **Promote's undo.** A lifecycle write that fails after the deploy withdraws the deployment, and says plainly when it could not.
- **Starting numbers.** Paper starts from defaults. Live reads the paper lane's last calibrated values through the real harvester, with their watermark. I traced the node's real row identity (`qmb/results/journal.py:186`, `:252`) against promote's filter and they match.
- **Node link.** Principal carried, never constant. Outbox order and op-id idempotence. Staging verifies each file by fingerprint.
- **Host route.** The pass is checked first, verbs are closed, `manage` and `money` answer only to `operator`.
- **The guard for grants (C-25).** Strong, and its test file is the best in this part.
- **Manifest refusal (C-27).** Case-folded, one table shared with the server vault. Look-alike names fail the plain-ASCII rule.
- **Grants out of backups and snapshots (C-05e).**
- **Log shipper (C-04).** Files are the queue, cursors survive restarts, drops are counted, secret-named fields and key shapes are masked, non-finite numbers do not kill the sender.
- **Article landing (C-27a).** The blob appears only after the Library landing, so an article whose landing failed is sent again. I checked `artifacts.py:_land` for this.
- **Deadlock fix (C-33).** Nothing holds the service lock across an engine hop.
- **Record landing (C-34).** `world` is never an argument. His own keys stay. Secrets are refused by a closed schema.
- **Departure I accept.** AD-324 says admitting a version parks the other in the same click; fold refuses it with "park or retire it first". One extra click, and safe.

## 6. Must and should

No `must`.

- p5d-1. A timed-out deploy reads as refused while the node may hold it; a second click leaves two deployments.
- p5d-2. On a server, a deploy waiting for files is refused for good instead of waiting.
- p5d-3. A queued deploy the node later refuses leaves the unit at paper with nothing running and no way back on that version.
- p5d-4. The wrong-scale report shows nothing unless someone hands it a card; the typed reader reads gold 100 times too small.
- p5d-5. Only EURUSD and XAUUSD get records; the settings the comments name do not exist.
- p5d-6. A row with his token and no venue skips the demo check.

Note on p5d-1: I graded it `should` because a 30 second stall is rare and only the demo-bound live lane places orders today. It should be repaired before a live bind, and the fix is one word.

## 7. Test verdict

These tests are worth having. They run real code and assert literal results; `test_guard_secret_globs.py`, `test_promote.py`, `test_app_logs.py` and `test_job_outputs.py` are good examples. None of the 132 would pass if the code returned nothing. About 58 lines are repetition (p5d-9). The largest file, `test_feed_relay.py` at 673 lines, tests a feature no real path reaches (p5d-7), so it stands or falls with his call on C-22. Two weak spots: `priced()` in the C-31 test is a reader the test invented, and `test_a_row_with_no_venue_is_never_checked` pins behaviour that should change.

## 8. Golden and reference data

Independent for prices: the C-31 gold and EURUSD first ticks come from dukascopy-node's m15 files, according to the test's docstring, a different tool from the code under test. I did not re-open those files. The EURUSD fingerprint `e9e20ec3...` comes from the parent's own script, so it proves "unchanged", not "correct", which is all it claims. `not-read.tsv` holds lock files, a README, a config and calendar data, with no golden data for this part.

## 9. Ten functions walked for edge cases

`Promoter._admit`, `Promoter._leave`, `starting`, `NodeLink.flush` with `_send`, `NodeLink.stage` with `_copy`, `HostRoute.ask`, `venue_records.land`, `demo_account`, `scale_of`, `AppLogs._ship`.

Two smaller things are true and not worth a row. A deploy stuck waiting at the head of the outbox holds later changes behind it, which is rare because promote stores the blobs itself. `harvested_calibrations` ignores `unreadable` partitions, so an unreadable month means older values.

## 10. Set aside for him

Should the market board feed (C-22) be finished or cut? It takes two small changes to work, and 807 lines go if cut. I assumed keep, unwired, as his triage already says it is safe.

## 11. Needs a long run

Run each from the folder named, after `source D:/QMX-worktrees/audit-ship/tools/env.sh`.

- `qmx-agents/packages/qmx-control`: `"$AUDIT_AGENTS_ENV" -m pytest tests/test_lock_order.py -q -p no:cacheprovider`, 500 rounds, for C-33.
- Repo root: `"$AUDIT_ROOT_ENV" -m pytest tools/tests/test_app_env_fresh.py tools/tests/test_app_env_data.py -q -p no:cacheprovider --no-cov`. It builds real envs and calls `uv`, for C-26 and C-26b.
- `qmx-agents/packages/qmx-host`: `"$AUDIT_AGENTS_ENV" -m pytest tests/test_feed_relay.py tests/test_venue_records.py -q -p no:cacheprovider`.
- `qmx-agents/packages/qmx-engine`: `"$AUDIT_AGENTS_ENV" -m pytest tests/test_download_dukascopy_scale.py -q -p no:cacheprovider`, for the scale 5 fact.

Unproven and only a real run can settle it: whether cTrader Remote MCP's `traderId` equals the `ctid` the node binds as the account id. `first_real_start.py:365` binds `str(ctid)`, and the fake was written to match. If they differ, the demo check refuses every chat with "has no account record", which is safe and visible, but C-36 would not work until mapped. His first real token decides it.

## 12. Not read

Nothing in `files.tsv`. Files outside it I read only in part, for wiring: `host.py`, `qmn/app/runtime.py`, `qmn/app/operations.py`, `qmn/app/server.py`, `qmb/host/replay.py`, `qml/lifecycle/machine.py`, `artifacts.py`.

## 13. Skills that changed a decision

- `blast-radius`: made me prove the outbox and promote edges by running them, which turned two guesses into p5d-1 and p5d-2.
- `lens-edge-case-hunter`: walking `_send`'s code set and the transition table's missing rows found p5d-1 and p5d-3.
- `lens-verification-gap`: showed `priced()` stands in for the real reader, which led to p5d-4.
- `principle-test-behavior-not-implementation`: kept me from calling the repetitive tests hollow; they can fail, so they are `leave`.
- `principle-laziness-protocol`: the three copies of the main walk, p5d-8.
- `code-review`: kept Standards and Spec apart, so a met done line and a defect could both stand.
- `principle-prove-it-works`: every level 4 proof calls the real code, and its script is under `D:/Temp/audit/p5d/`.
- `principle-minimize-reader-load`: changed nothing here.
