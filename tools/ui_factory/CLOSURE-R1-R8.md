# R1–R8 closure — UI factory repair 2026-09-27

Factory worktree: `C:/Users/Mubarak/Desktop/QMX-worktrees/ui-factory`
Reviewed SHA: `c6717df7100eba3594043bad296fdcbe69ef01fb`
Did not edit `_bmad-output/planning-artifacts/epics-UI-2026-09-27.md` or other agents' story files.

## Commands

```
uv run python -m pytest tools/tests/test_ui_factory_validate.py \
  tools/tests/test_ui_factory_evidence.py \
  tools/tests/test_ui_factory_merge.py \
  tools/tests/test_ui_factory_quality.py \
  tools/tests/test_ui_factory_skylos.py -q
python tools/ui_factory_cli.py lifecycle --mode synthetic
python tools/ui_factory_cli.py setup
```

Unit tests: **32 passed, 1 skipped** (Skylos CLI absent on Windows).

Synthetic lifecycle (local): `ok=true` at
`C:/Users/Mubarak/Desktop/QMX-worktrees/_ui-factory/lifecycle/lifecycle.json`

Live Grok workflow `ui-factory-lifecycle` (`wf_01a0e25fde9476a2948261c0819cccbd`):
agent spawn succeeded; quality `--user-facing` without Reticle returned `passed=false` `exit_code=1`.
`inspect-evidence --user-facing` on that artifact: `ok=false` reason `Reticle evidence missing`.
Evidence: `C:/Users/Mubarak/Desktop/QMX-worktrees/_ui-factory/lifecycle/evidence-neg/quality-ft-reticle-neg.json`
(`reticle_verdict=missing`, command `exit_code=0`). That red result is the R2 negative control, not a factory crash.

Live GitHub named-check wait is **not** a promotion success unless `ci-wait` reports `simulated=false` and required names green on the exact SHA.

## Map

| ID | Fix | Files | Proof |
|---|---|---|---|
| R1 | User-facing requires UI profiles without a file list. Product host is `apps/qmx-ui`. Fixture cannot satisfy product CI. Workflow passes git-changed files + story hash. | `quality.py`, `config.json`, `ui-quality.yml`, `ui-epic-build.rhai` | `test_user_facing_without_files_still_requires_ui`; UI quality job exits 1 if `apps/qmx-ui` missing |
| R2 | `run_profiles` and `evaluate_promotion` require Reticle `act_and_wait`/`assert` yes. Forced yes blocked. | `quality.py`, `evidence.py`, `merge_gate.py` | lifecycle `reticle_blocked`; `test_user_facing_without_reticle_is_not_ok`; `test_forced_reticle_cannot_promote` |
| R3 | `as_int` preserves 0. Content fingerprint. Observed toolchain. Profile identity. Pytest summary counts. Safe log names. | `evidence.py`, `gitops.py`, `quality.py` | `test_exit_zero_survives_round_trip`; `test_pytest_summary_populates_counts` |
| R4 | Occupied destination merges in place. No unowned `--force` temp. Named CI on exact SHA; simulate cannot promote. | `merge_gate.py`, `ci_wait.py` | `test_occupied_destination_merges_in_place`; `test_named_ci_ignores_unrelated_success`; `test_simulated_ci_separated_from_live` |
| R5 | State root from main checkout sibling `QMX-worktrees/_ui-factory`. `record-unit` / quality persist units. | `paths.py`, `cli.py`, `state.py` | lifecycle `resumed`; doctor state under `_ui-factory` |
| R6 | Required metadata includes sources/components/design. Unfinished FEAT/story deps wait. Cycles detected. `run-selected --ids` validates. | `validate_inputs.py`, `cli.py` | existing validate tests + `test_backend_wait_on_unmerged_feat` |
| R7 | `setup_ready` vs `runtime_ready`. Node 24 is not runtime-ready. MCP unknown unless probed evidence file. Fixture host ≠ product host. | `doctor.py`, `cli.py` | setup output `runtime_ready: false`, `mcp ... unknown` |
| R8 | `lifecycle --mode synthetic` plus Grok workflow `ui-factory-lifecycle`. Fixture app is FACTORY-TEST, not product chrome. Live CI is separate. | `lifecycle.py`, `ui-factory-lifecycle.rhai` | lifecycle.json; workflow journal |

## Distinctions

- **Local:** pytest, lifecycle CLI, occupied merge in a temp git repo.
- **Simulated:** `ci-wait --simulate` returns incomplete and cannot promote.
- **Live:** Grok workflow agent; GitHub named checks on a real SHA when `gh run list` sees them.
