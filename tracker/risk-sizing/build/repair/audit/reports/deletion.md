About 251,000 of the 565,000 lines of product Python could go: about 55,000 now, about 41,000 after his first real start, and about 155,000 after the demo evidence C-20 waits for (78,000 of those need his word first, because no plan section covers them), plus about 42,000 lines of tests that go whole with them.

Nothing here was deleted. Every number is at commit `50c83a4e`. Lines are lines in the file, as in the brief's table.

| Group | Code lines | Test lines that go whole (more touch it) | Why it can go | When | What breaks if this is wrong |
| --- | --- | --- | --- | --- | --- |
| Old QMB door: the `qmb` command, bot runner, orchestrator, old data, analysis and study code, the 2,734-line re-export sheet | 63,840 | 6,985 (up to 29,000 more) | The QMB app's 9 jobs, the node, the MIS, the host and the templates ask by name for only 32,147 of QMB's 95,987 lines. A copy without the rest loaded all 9 jobs and passed the new unit runner tests | After demo, on his word | A QMB feature with no job yet is lost until rebuilt, such as an optimiser or robustness method. `release/launcher.py` stops working until it calls the host directly |
| Old node shell, C-20's list: `host`, `seats`, `promotion`, `paper`, `doors`, `bench`, `deploy`, most of `observability` | 47,507 | 11,767 (11,416 more) | Nothing he runs reaches it. Only the deploy recipes, one CI lane and tests do. The node passes its runtime and stop-on-every-order tests without it | After demo (C-14 real, C-15) | The SQS gate lives only here (see below). Otherwise an import error at start, loud and at once |
| Live lanes: `scripts/live` (not the two smoke scripts) | 40,660 | 177 | Build-time checks. No product code, CI step or remaining plan section runs them | After first real start | He loses a ready rerun if something at start needs re-proving. The product is untouched |
| Old node leftovers C-20 does not list: parts of `qmn` `data`, `ledger`, `order`, `venue`, `config`, `protection`, plus `replay`, `reconcile` | 29,160 | 6,366 (15,801 more) | Their only callers are in the old shell or in re-export lines. A copy of `qmn` with just 21,496 of its 97,031 lines passes the same node tests | After demo, with C-20 | A new-node path my two test files missed fails loudly on import. The long run below narrows this |
| Probes: `scripts/probes` (keep the FINDINGS files) | 21,364 | 3,435 | One-off measurements from the rebuild. Their answers are written down. CI never runs them | Now, after moving one file a live lane imports | He cannot re-measure the same way. The product is untouched |
| QMB usage examples: `qmb/examples` | 14,305 | 1,590 | Run only by their own test, and they show the old door | After demo, with the old door | Nothing but a human or agent reading one |
| `qmf-indicators` and `qmf-structure` packages | 13,979 | 9,027 (3,470 more) | The only code that imports them reads their version number for display. QML says outright it never imports them. Jobs and unit tests ran with neither loaded. The dictionary has its own blocks | Now, on his word | Their ideas are lost if the dictionary does not hold them all. Keep in git history at least. TA-Lib install also falls away, apart from the golden tool's own |
| QML and QMF usage examples | 10,166 | 1,973 | Only tests run them. No agent or person is pointed at them, and many teach the bot, not the unit | Now | A reader loses a sample |
| The retired factory: `adws` | 8,883 | 307 | Nothing outside it imports it. Only the justfile starts it | Now | Bare `pytest` at the root points at it, so `testpaths` must change in the same step |
| Hermes dump scripts in a planning folder | 300 | 0 | Throwaway, and ruling US:350 says those logs are not read raw | Now | Nothing |

The import graph alone calls only 641 lines "reached from nothing". The dead weight is hidden another way: package `__init__` files import everything so that names can be re-exported. Python loads it all, while nothing asks for it. So the script also builds a thin graph that follows each name to the file that defines it, and I tested what that graph claimed on scratch copies.

**The lever.** `reports/deletion-reach.py` writes `D:/Temp/audit/deletion/reach.tsv`, one row per module. Totals: reached from product 393,671; only from CI and hand tools 54,361; only from tests 65,386; `unknown` because of a load by name nearby 21,178; a script a person might run 19,994; factory only 8,506; example apps only 878; nothing 641; test files 302,792. Workflow templates and dictionary blocks loaded by folder count as reached.

## The old node shell, exactly

- Real count: `host` 26,482, `seats` 3,872, `promotion` 3,249, `paper` 2,788, `doors` 2,014, `bench` 2,291, `deploy` 5,203 Python and 1,150 other. That is 45,899 for the seven, and 47,507 with the rest of `observability`.
- What in the new code imports it: only `qmn/observability/__init__.py`, which `qmn/app/alarms.py` loads and which pulls in `health`, `logging` and `metrics`. C-20 already covers this. `qmn/app`, `qmx_host` and `tools/first_real_start.py` import nothing else in the list.
- What stands in the way, in order:
  1. The evidence: `c14-real.log` and `c15-demo.log` reading all PASS.
  2. The SQS gate. Its only home is `qmn/host/runtime_risk_gate.py`, and ruling RC:320 says SQS stays. See plan-check-2, and "Set aside".
  3. `qmn/capital` imports `paper` demotion. The kill line stays for the risk session, so repoint it as C-20 says. It then has no caller but its test.
  4. C-20's list of readers misses `tools/release_gate.py:169` and `release/install.py:341`, which demand deploy files in every bundle (deletion-11).
  5. 58 test files mix old and new names and must be repointed or cut.
- C-20's move of `StandDownTrigger` and `allocate_writer_ids` is not needed. Only old tests use them (deletion-12).
- His ruling 27 is about right. The new node needs about 21,500 lines of `qmn`. So about 76,000 of 97,000 can go, not the 47,000 C-20 says. That also answers "about 97,000 is too much".

## What `scripts` and `adws` are for

- `scripts/live`: the live lanes the build ran for each section. Still edited on 4 November (C-28), though the plan names none of them.
- `scripts/probes`: measurements taken before building. Done.
- `scripts/data`: the one-shot old-tick import into the Library. Keep until his data has landed; 1,434 lines.
- `adws`: the retired factory. To detach it: the `adws` suite in `tools/test_all.py`, the factory recipes in `justfile`, `pyproject.toml` lines 1-23, 229, 257-263, 331, `DEPENDENCIES.md:92-101`, `.env.sample:4`, `.gitignore:44-45`, `queue/`. Keep `test-all`, `ci` and the node recipes import until C-20.

## Duplicates

Only what I read in both places.

- Contained file helpers: `qmb/orchestrator/paths.py` and `qmf/readings/_files.py`, same bodies, about 230 lines. The second says it is a copy. Keep `qmf/readings/_files.py`; the other goes with the old door.
- Version graph helpers: `qml/declaration/versioning.py` and `qmf/risk/versioning.py`, same bodies, about 80 lines. Keep the QML one. The risk copy waits for the risk session.
- Workflow template scripts: 12,425 repeated lines of byte-identical files, such as 35 copies of `render_and_grade.py`. This is by design, not slop: a run holds only its own folder, and `test_templates.py` checks each copy against `_shared` (`TEMPLATES.md:91`). Keep them.
- Finding calendars: `qmb/data/gap_check.py:880` and `qmn/time/calendars.py:313`. The node's says it finds them "as QMB finds them". This is one rule used twice, recently fixed by C-38. Leave it.

## What must stay

- **Workflow engine.** All of it is reached, 46,600 lines with its templates. The only parts no production path uses are `ledger/memo.py` (103) and the fake Library for tests (504, labelled so). Nothing to cut.
- **Mini-app core.** All reached but `road/check.py` (198) and `bundle.py` (96), only tests use those. Leave them. Understand the intent first, as he asked.
- **Library.** Keep everything. Note with care: `qmx_library/search.py` (292) and `curator.py` (57) are called only by tests. That looks like work not yet wired up rather than dead code, so someone should look before anyone cuts it.
- **Local-first stack.** `qmx_home`, `qmx_hub`, `qmx_remote`, `qmx_broker` and the host are all reached.
- **QML.** The core and all dictionary blocks. `qml/host` and `qml/unit/upgrade.py` (579) are only tested, leave them. **MIS** and its readings, including the regime training (9,802 lines, no running caller), which he wants for the Lab later.
- **Also stay.** Calendar extensions, found by folder and easy to mistake for dead. `qmn/venue/ccxt_client.py` and `qmn/probes/hyperliquid_testnet`, which wait for G-WALLET. `qmx_control/lab.py`, `qma/console.py` (until the UI lands), `qmx_host/feed_relay.py`. `tools/first_real_start.py`, `tools/dictionary`, `examples/apps`. All of `qmf-risk`, which belongs to the risk session.
- **The order.** Nothing is deleted before its replacement passes. The groups marked "now" have nothing to replace them because nothing uses them, but he lands the stack himself, so they still wait for him.

## What I could not settle

- **A second wave.** Once the old node and old QMB are gone, about 12,800 lines of `qmf-data`, `qmf-risk` and `qmf-registry` have no caller by name. They sit under the Library and the risk session and I did not run this. Not counted above.
- **The release bundle.** `release/` starts the host through the old `qmb` command and its README still names `qmn.host.supervise`. Whether the bundle is still how he installs, I could not tell. The first real start does not use it. I assumed it stays and needs repointing.
- **Test counts are estimates.** A test "goes whole" when everything it imports from its own package is dead. Tests that touch both are the numbers in brackets. Of 49,642 lines of QMB tests, 13,616 touch nothing old. Of `qa/tests`, about 27,600 lines test living code and stay. His question whether 40,000 lines is too much is not answered by reach.
- **A graph cannot see use.** Reached does not mean useful. I only say what nothing reaches. Static reach may also miss a load whose name is built at run time; those read `unknown`.
- **How far my proof reaches.** Scratch copies passed `test_app_runtime.py`, `test_protection_every_order.py`, `test_unit_runner.py`, `test_unit_handler.py`, and loaded all QMB jobs and the MIS core. The rest is below. No host booted, no broker reached.

## Needs a long run

Run from the audit copy, with the copies under `D:/Temp/audit/deletion/` left in place. A test that fails on import of an old name is one to repoint, not proof the node needs it.

```bash
source D:/QMX-worktrees/audit-ship/tools/env.sh; cd D:/QMX-worktrees/audit-head; export OVERLAY_DIRS=D:/Temp/audit/deletion/ov1 PYTHONPATH="$PYTHONPATH;D:/Temp/audit/deletion"; "$AUDIT_ROOT_ENV" -m pytest qmn/tests/test_app_*.py -q -n 4 -p ovcheck -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/deletion/long1
source D:/QMX-worktrees/audit-ship/tools/env.sh; cd D:/QMX-worktrees/audit-head; export PYTHONPATH="$PYTHONPATH;D:/Temp/audit/deletion"; "$AUDIT_ROOT_ENV" -m pytest qmb/tests/test_behaviour_check.py qmb/tests/test_fidelity.py qmb/tests/test_futures_rolls.py qmb/tests/test_realism.py qmb/tests/test_run_journal.py qmb/tests/test_windowed_reader.py -q -n 4 -p ovcheckb -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/deletion/long2
```

## Set aside for him

- Does the old QMB door go after the demo, given that no plan section covers it and it may hold methods he wants kept? I assumed it stays until he says, and counted it as "could go".
- Do `qmf-indicators` and `qmf-structure` count as seeds to keep, now the dictionary has its own blocks? I assumed they stay until he says, and counted them as "could go".
- The SQS gate has no place in the new node, and C-20 removes the only one. I assumed `runtime_risk_gate.py` stays until the risk session places it, which leaves that file's 1,969 lines out of the cut for now.
