# Long checks the grounding reports asked for, run by the orchestrator

Commit `50c83a4e`. Logs are in `D:/Temp/audit/chief/ground-long/`. Every run patches code in memory only.

| Check | Command in short | Result |
| --- | --- | --- |
| Refusals the unit repair adds, over all of QML | `pytest qml/tests -p refuse_trial`, trial on sessions, settings, limit, price, roles, exits | 1,445 passed, 1 failed. The one is `test_a_session_on_either_market_calendar_is_not_an_error`, as `reports/ground-unit.md` predicted. Point that test at `check_layers` |
| The same refusals over the QMB unit path | `pytest qmb/tests/test_unit_handler.py qmb/tests/test_run_journal.py -p refuse_trial` | 18 passed |
| The amend tests a past-entry refusal could move | `pytest qmn/tests -k amend` | 13 passed at this commit. They run no trial, so they name what to rerun after the change |
| The kill reaching unhosted positions, on the harsher conformance venue | `pytest qmn/tests/test_app_kill_scopes.py -p reach -p harsh` | 17 passed |
| Runtime and the unknown drill, with the kill sketch, the harsher venue and broker-wins | `pytest qmn/tests/test_app_runtime.py qmn/tests/test_app_unknown_drill.py -p reach -p harsh -p venuewins` | 11 passed |

| Dead weight detached, on the scratch copy | `pytest tools/tests qml/tests` in `D:/Temp/audit/ground-core/cut` | 2,047 passed, 54 failed, 8 errors. Grouped by reason in `D:/Temp/audit/chief/cut_reasons.py`. The failures that come from the detach are the ones `ground-core` K names: `test_sssf_quality_gate.py`, `test_examples.py`, `test_conformant_bot.py`, `test_scaffold.py`. All the others come from the scratch copy having no `docs/`, `release/`, `.github/` or `qmx-agents/`, which a real branch has. `test_ambient_scan.py` is the known red. R01's real proof is the whole `tools/test_all.py` on its branch |

Already covered by the whole-repo run at this commit, so not run again: `test_conformance.py` (qmx-judge, 38 passed), `test_qmb_app.py` (28 passed), the market door's tests, the promote and records suites, `test_app_env_data.py`.

## Added 5 November, after the plan reviews

The refusals the first trial did not carry, over all of QML: no stop, second exits, exits by rule, a lone `at` cadence, blocks not built, and the format bump to 2. Asked for by `plan-review-a` section 5.

- **Command.** `pytest qml/tests -q -p refuse_more`, plug at `D:/Temp/audit/plan-review-a/plug/refuse_more.py`, log at `D:/Temp/audit/chief/refuse_more_long.log`.
- **Result.** 1,446 passed, none failed, in 110 seconds. Across both trials, the only QML test that failed is the one named above. The mirror refusal (`p0a-9`) was in neither trial. The test it moves is `qml/tests/test_compile_dummy.py:272`, which R04's box rewrites with an explicit short side, and `plan-review-a` ran that rewrite.
- **Why the green can be trusted.** The same mechanism with a plug that refuses every unit (`D:/Temp/audit/chief/plugreach/refuse_all.py`) fails 12 of 12 in `qml/tests/test_compile_dummy.py`, and `refuse_more` passes the same 12. So a `-p` plug does reach the test workers and their compile path.
- **What it does not cover.** Tests outside `qml/tests`. R04's own lanes and the whole-repo run cover those. The two trials were also run apart, never together, so R04's lane 1 is the first time all refusals run as one.

Not run, and left as a first step for the builder of that repair:

- Whether Christmas reads as a hole in a real month, and the real tick rate. It needs a download.
- The login reader on a real entry. It touches the real Credential Manager, so it belongs to a builder's owner lane.
