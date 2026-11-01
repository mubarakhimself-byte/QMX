## Make journals readable by agents and him, with one harvester on every machine (B15)

Phase 3, journals, the copilot and agents. Part B slice B15, Part B AD-210 (local half) and AD-211, Level 0 AD-27, R1-B-02 and R1-B-04. Rulings 44 and 51 (agents in the slow lane read journals; the Library is the centre). Real step none. Done when the host is the one harvester of every app's append streams on its machine, `journal_query` and `notes_write` answer, `trade` and `paper-run` version 2 exist, and nothing here writes `bot` or `strategy`.

**Depends on.** B8, B13, for the judge's paper scoring.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/records.py` (the local half, by the committed reader and `born_on = node`), and edit `qmx-agents/packages/qmx-host/src/qmx_host/maintenance.py` (list the job) and `qmx-agents/packages/qmx-host/src/qmx_host/host.py` (start it beside backups).
- [ ] Create `qmx-agents/packages/qmx-tools/src/qmx_tools/journals.py`, and edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`, `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py` and `qmx-agents/packages/qmx-tools/tests/test_tools.py`, where `research` goes from 3 to 5 tools on purpose (`:374-376`).
- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/{note,paper-run,trade}.schema.json` (version 2, additive) and create `qmx-agents/packages/qmx-judge/src/qmx_judge/paper.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_harvest.py` and `qmx-agents/packages/qmx-judge/tests/test_no_bot_writes.py`.

**Build.**

- [ ] Write the harvester. Closed months commit once. Open months of bars and reading history commit every `[records] open_harvest_s` (default 60), journals too on This PC. Ticks commit every `[records] tick_harvest_s` (default 3,600). An unchanged stream is skipped by its fingerprint, because the store reports `idempotent = False` on an unchanged re-commit (`packages/qmf-data/src/qmf/data/series.py:429-430`).
- [ ] Write `journal_query`, which requires a time window, `notes_write`, the `trade` projection and the judge's paper scoring.

**You see.**

- [ ] He can ask "why didn't the dummy unit trade this morning?" and get the reason with the spread at that minute.

**Verify, unit.**

- [ ] On a fixture app volume with journal, reading and bar streams, a closed journal month commits once, the open month of bars lands as one `open.parquet` holding 60 then 120 rows after two rounds, ticks wait for their cadence, an unchanged stream is skipped, and the app's stream files are unchanged by a round. A query without a window is refused. Past the data it says where the data stops. Backfilled rows are excluded by default. A re-projected trade lands nothing new. A trade without initial risk carries `r_missing`. No write path lands `bot` or `strategy`. Every new row is on the default copilot surface. `research` lists 5 tools. Run `cd qmx-agents && uv run pytest packages/qmx-host/tests/test_harvest.py packages/qmx-tools/tests packages/qmx-judge/tests packages/qmx-library/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. Two harvest rounds over a fixture app volume. Save `b15-harvest.log`. Pass when the closed month commits once, the open month is one file with 60 then 120 rows, and ticks wait for their cadence.
- [ ] Lane 3. Hash the app's stream files before and after a round. Save `b15-untouched.log`. Pass when every hash is unchanged.
- [ ] Lane 4. Ask the copilot on `haiku` "why didn't the dummy unit trade at 08:00 on the first fixture day?" Save `b15-why.log`. Pass when it calls `journal_query` and answers with the reason code and the spread at that minute.
- [ ] Lane 5. `journal_query` without a window, then with a window past the data. Save `b15-window.log`. Pass when the first is refused and the second says where the data stops.
- [ ] Lane 6. Re-project a trade, then project one without initial risk. Save `b15-trade.log`. Pass when the first lands nothing new and the second carries `r_missing`.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for one harvest round over a fixture volume with a month of M1 bars.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. Fails when one round takes longer than `[records] open_harvest_s`, since rounds would then overlap.

**Review gate.** Lenses edge-case and verification-gap, because journals record trades. The blast-radius fact is R1's open-month run, the store keeps an open month as one file replaced on each commit (`packages/qmf-data/src/qmf/data/series.py:6-9`).

@merge

## Let a workflow's agent step write the file it was asked for and nothing else (B17)

Phase 3, journals, the copilot and agents. Part B slice B17, Part B AD-214, Level 0 AD-32, engine AD-60 and probe P-PERM of 18 Oct. Ruling 49 (the workflow engine is his, changed only with a core reason from "QMA V2 Workflow System Design 2", and AGW is one of those reasons). Real step none. Done when a step declaring `Write` and `Edit` is offered no `Bash` and no `PowerShell`, a write outside its attempt overlay is refused, only declared outputs commit, and the `library` node kind is marked unavailable.

**Depends on.** Nothing.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/policy.py` (the AGW form), `qmx-agents/packages/qmx-engine/src/qmx_engine/ports/harness_adapter.py` (policy arguments with the overlay and `disallowed_tools` for undeclared `Bash` and `PowerShell`), `qmx-agents/packages/qmx-engine/src/qmx_engine/nodes/agent.py` (commit only `outputs.files`) and `qmx-agents/packages/qmx-engine/src/qmx_engine/definition/registry.py` (`:94`).
- [ ] Create `qmx-agents/packages/qmx-engine/tests/test_agw.py` and the P-PERM rerun script `qmx-agents/packages/qmx-engine/tests/live/p_perm_rerun.py`.

**Build.**

- [ ] Build AGW as engine AD-60 designed it, and mark the `library` kind unavailable with its reason. Nothing else in the engine changes.

**You see.**

- [ ] A workflow's agent can now save the file it was asked to write, and nothing else.

**Verify, unit.**

- [ ] A step declaring `Write` and `Edit` is offered no `Bash` and no `PowerShell`. A write outside the overlay is refused. Only declared outputs commit. A definition using `library` is refused with its reason. Run `cd qmx-agents && uv run pytest packages/qmx-engine/tests/test_agw.py packages/qma-harness/tests packages/qmx-engine/tests`.

**Verify, live.**

@lane1
- [ ] Lane 2. Rerun P-PERM on the real engine launch path with `haiku`. Save `b17-pperm.log`. Pass when A3 and A3W cannot run.
- [ ] Lane 3. A workflow whose agent step declares one output file and is asked to write two. Save `b17-outputs.log`. Pass when only the declared file commits.
- [ ] Lane 4. A step that tries to write outside its overlay. Save `b17-overlay.log`. Pass when the write is refused and the step reports it.
- [ ] Lane 5. A definition that uses the `library` kind. Save `b17-library.log`. Pass when it is refused with its reason.
- [ ] Lane 6. The shipped templates that use agent steps, installed and validated at the head. Save `b17-templates.log`. Pass when each validates as at the parent.
@menu

**Verify, perf.**

- [ ] Metric. Seconds for one agent step that writes one file.
- [ ] Probe. Lane 3 on `haiku`.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** Lenses edge-case and adversarial, on what an agent may write. The blast-radius fact is Part B's run of AGW's offered tools (`R1-FIXES-X1-B.md`), a step's offered tools exclude `Bash` and `PowerShell` unless declared.

@merge

## Feed the checker's problems back to the agent while it writes (A14)

Phase 3, journals, the copilot and agents. Part A slice A14, Part A AD-117, connections C4. Midday ruling 12 (feedback like a linter error, no false positives) and ledger "missed" item 27. A Should, after its probe. Real step none. Done when a probe shows a core-plugin PostToolUse hook fires under the Agent SDK launch on Windows and Linux with its output reaching the model, and then `hooks/hooks.json` calls `python -m qmx_tools.unit_check`. If the probe fails, the PR ships only the probe and its log, and nothing else depends on it.

**Depends on.** A8.

**Files.**

- [ ] Create `qmx-agents/plugin/hooks/hooks.json` and regenerate `qmx-agents/plugin/plugin.manifest.json`.
- [ ] Create the probe `qmx-agents/packages/qma-harness/tests/live/test_unit_hook_probe.py`.

**Build.**

- [ ] Run the probe first. If it passes, ship the hook. If it fails, ship the probe with its log, log the outcome in the trail, and leave the hook out.

**You see.**

- [ ] When the copilot saves a broken unit, the problems come back to it at once, the way a linter error does, and it fixes them before he sees the draft.

**Verify, unit.**

- [ ] The probe's log shows the hook's `additionalContext` in a test chat after a Library save of a broken unit. `test_packs.py` passes. Run `cd qmx-agents && uv run pytest packages/qma-harness/tests/test_packs.py`.

**Verify, live.**

@lane1
- [ ] Lane 2. The probe on Windows with `haiku`. Save `a14-windows.log`. Pass when the hook fires after the save and its `additionalContext` reaches the model.
- [ ] Lane 3. The probe on Linux, in a throwaway folder `/srv/qmx/check/a14/` on `qmx-server` as user `qmx`. Save `a14-linux.log`. Pass when the hook fires the same way.
- [ ] Lane 4. A save of a passing unit. Save `a14-nofalse.log`. Pass when the hook adds no message.
- [ ] Lane 5. The hook's run time on the dummy. Save `a14-time.log`. Pass when it finishes inside 8 s.
- [ ] Lane 6. A chat that saves a broken unit and is told nothing else. Save `a14-loop.log`. Pass when the agent fixes every problem the hook named and the next save passes.
@menu

**Verify, perf.**

- [ ] Metric. Seconds from the save to the hook's answer.
- [ ] Probe. Lane 5.
- [ ] Baseline. None, first measure.
- [ ] Rule. Fails above 8 s (connections C4).

**Review gate.** Lenses verification-gap and edge-case, because false positives are not allowed. The blast-radius fact is that `test_packs.py` passes with the new hook in the plugin manifest.

@merge
