# Independent quality-series composition review

2026-10-04. Read-only review of the memory checkpoint `831dd36911402bce3586b3ff340fee22f33ef5e1`, the ten reviewed quality commits applied through `19f35af9b0b651987798a3fc0d31fbc6852ffd67`, and the integrator's current local gate/dependency/coverage delta. No candidate runtime or original checkout was edited, no suites were duplicated, and no hosted workflow, mutation campaign, provider, credential, trading, publication or deployment action was performed by this reviewer.

**Verdict: approve the bounded quality-series composition and inspected local integration delta. No remaining actionable composition or gate-semantics blocker found.** A formatting issue observed during review was corrected by the integrator and its initial failure retained. This approves the reviewed changes; it does not establish hosted CI, full mutation strength, broad component readiness or whole-backend acceptance.

## Exact quality-series preservation

Independent `git show <commit> --pretty=format: | git patch-id --stable` checks matched all ten pairs:

| Reviewed source | Applied candidate | Stable patch ID |
|---|---|---|
| `1edfcc95` | `3b2a67e3` | `f0d11f17510c4606ed9b4c02cb30e03c3d0741d8` |
| `4305d239` | `d9e7c967` | `35b9fcddf486994388b5a1308f3ed542a87ad01f` |
| `05ecaf0e` | `eff44617` | `1446cb615f8c133637bb4a246e84b5ad95a5718a` |
| `f2aaaf9f` | `10788e61` | `6b676b721bf94d180692a39f4260e37c9fb3d7c3` |
| `0fb836aa` | `314f2634` | `bad1005541031fe9fa9114fa80c1c27499f0ade8` |
| `bd707db9` | `5696103a` | `ff726188f8bbc65f2614c30107f5f4b8b16dff16` |
| `8574ea26` | `c1a7e30d` | `df8d5127d08e3bf4dd75b1aff763f2b718e03f6d` |
| `c4dba14a` | `0986b4e5` | `fe8eaddd0e1719bf2c4e4507f04b16bd2d519927` |
| `4eb37335` | `432d4539` | `e7f56f8e1db9c9f04c41da9e63c51170ef076343` |
| `47b15d4e` | `19f35af9` | `235b9c5e148d1d5b442736cff59c15e189d3aede` |

The source head is exactly `47b15d4eed5763935b68f8cafc547f7b94c89279`, based on `bf3c6b59`. Comparing all paths changed by that source series against candidate tracked HEAD returned zero differences. The broader `.github`, `tools`, and `qa` comparison differs only by the previously accepted integrator and spot runner additions. The current local delta is separately inspected below; it is not silently represented as part of the source-quality commit.

The quality lane's approved deletion remains limited to the previously reviewed unreferenced workspace metadata alias and the superseded readiness helper. The new inline workflow verdict is the executed canonical body; its tests read and execute that body. There is no additional dead-code deletion, private-QMB cleanup or blanket protocol/import/registration pruning in this integration.

## Gate semantics and shared integration delta

**Mandatory results stay fail-closed.** Both Ubuntu and Windows backend and agent matrices use `fail-fast: false`. Existing `check` and `agents` aggregate contexts require successful mandatory prerequisite job results, refuse missing/malformed/cancelled/skipped/failed results and use an always-running inline verdict without checkout/network setup. Tier-1 steps have explicit `!cancelled()` and successful-sync conditions, allowing independent evidence after an earlier failure while preserving the failed job result. The local extra/no-sync delta changes installation/execution setup, not these conditions or failure handling. It adds no `continue-on-error` or missing-result exemption.

**The optional-memory CI prerequisite is closed in configuration.** Nested sync now explicitly selects all workspace members and `memory-extraction` under the frozen lock. Each of the five nested Poe invocations uses `uv run --no-sync`, retaining the test-only extra. The root default runtime groups and dependency graph remain unchanged. The new readiness regression parses the actual workflow sync command and asserts that every nested `uv run` retains the installed environment. It verifies this concrete boundary; it is not a hosted execution or clean-install claim. The read-only memory review's proposed setup is implemented without skipping the extraction tests.

**Dependency boundary remains exact.** The daemon allowlist adds only `deepagents` and `PyYAML`, already declared and pinned in the reviewed native/skills ancestry. `assert_package_deps_within` still requires exact equality: undeclared edges and missing required entries both refuse. Core and wire allowlists are unchanged; QMA's QMB and QMF venue import bans remain unchanged. The corresponding expected-set assertion is reconciled rather than deleted or weakened. This fixes stale metadata against actual reviewed functionality and grants no new execution or venue authority. Optional extraction metadata remains a separately explicit packaging seam rather than silently becoming mandatory runtime dependencies.

**Coverage measures real subprocess source and preserves policy.** Nested `patch = ["subprocess"]` matches the existing parent workspace coverage setting. QMA still targets only the three shipped source roots, enables branch measurement and enforces the aggregate 80% threshold. The existing nested source-inventory/per-package reporter remains unchanged; root package 80% and exact/chrono 100% branch floors, security zeros and dead-code ratchet are unchanged. Instrumenting real daemon/worker subprocesses broadens measurement of executed code; it does not insert fabricated counters, add tests/examples to product scope or relax a floor.

The integration runner assigns a fresh absolute `COVERAGE_FILE` inside each GUID evidence directory before invoking pytest. Combined JSON reports also go to that evidence directory. This prevents an earlier run's coverage database from being treated as this run's data. The `quality` selection's `--no-cov` is appropriate for its focused regression roster: it makes no product coverage claim. Full `qma` selection retains source-root branch coverage and the unchanged 80% pytest gate. A passing aggregate is still distinct from separately running the inventory/per-package reporter.

**Mutation changes retain their honest limits.** The copied quality series uses pinned Mutmut-compatible staging, captures both command statuses, requests a full `--all true` listing, and refuses malformed, duplicate, incomplete, out-of-scope or unclassified results. The core 68% kill-rate floor is preserved. QMN survivors remain advisory as already specified; successful command status and classified coverage of every declared module are required. No new mutation count/kill rate is claimed from tests of the gate itself. Hosted scheduling/cancellation and a real full mutation campaign remain unverified.

**Documentation repair is non-runtime.** The illustrative memory patch now uses documented zero-context hunks so later appended handoff text does not invalidate its context. Independent `git apply --reverse --check --unidiff-zero` passes against current integrated files. This draft is an additive documentation/manifest record; it does not claim a canonical documentation publication or a migration. `git diff --check` also passes for the inspected local delta.

## Evidence inspected and resolved finding

* `evidence/quality-a4988763b4b14833819e0f0c540a7f83`: **181 passed, 1 skipped, exit 0**. Exact skip: mutation-staging symlink creation is unavailable on this Windows host. The skip remains visible; hosted POSIX/symlink execution is separate evidence.
* `evidence/barriers-reconciled.txt`: **85 passed**. This is the barrier suite total, not a claim that 85 independent defects were fixed.
* Final locked-overlay memory roster remains **94 passed, no skips**, as recorded in `composition-memory-review.md`. No model/embedding/provider operation was performed by this reviewer.
* Local lint and strict type evidence passes. Initial `format-quality-combined.txt` reports the newly edited readiness test would be reformatted. The reviewer reported this before acceptance; the integrator applied root Ruff normalization. Final `format-quality-combined-final.txt` reports **9 files already formatted**. The initial red log is preserved; behavior did not change.
* Full QMA run `evidence/qma-8ae624d1a1b440dba37ed38fe815df58` was still active when this review was finalized. Its command identity records tracked HEAD `19f35af9` plus the eight local modified files and runner hash. No final test/coverage outcome is inferred from progress output. Integrator must record its completed result and reconcile every remaining failure/skip.

The inspected uncommitted paths are `.github/workflows/battery.yml`, two memory draft/documentation files, daemon dependency-barrier constants and their test, nested coverage config, integration runner, and readiness regression. These are integrator-owned shared joins; provider routing, runtime process composition, memory implementation and UI remain unchanged by this delta.

## Acceptance limits and handoff

Hosted Linux/Windows matrix execution, real workflow cancellation verdicts, generated full mutation scope/current kill rate, Windows workstation packaging, isolated installed-wheel behavior, security/scanner corpus acceptance and remote endurance remain separate work. Existing documentation records CI-mirror/Poe task-list drift and general Linux typing risks. Recorded component red gates are not cleared by focused quality tests. The combined milestone must pin a final commit, record final full-QMA evidence and retain current QMN/QMB/backend limits; successful QMA counts do not certify the whole backend.

Working-tree byte identities reviewed after formatter correction:

| File | SHA-256 |
|---|---|
| `.github/workflows/battery.yml` | `CA170E1BEDD3720D1A76B9001752B1E59C58F3A9F3161444655DD053352ACC42` |
| `tools/tests/test_readiness_gate.py` | `DCA1F833FA3DF832C7518B5F54E0C4F88756A7A62A5BDB28843319F19503F94B` |
| `qmx-agents/packages/qma-core/src/qma/core/barriers/dependencies.py` | `A417AE69FBE254EEB2C9C6CABF7A88DD70B2672DEEB980865CAE825CCD035A40` |
| `qmx-agents/pyproject.toml` | `DE4362BD5284809B822DE37A1DC51FACAB2A6C38F4672256773C73335911B5AE` |
| `tools/backend-integration-check.ps1` | `6EE0E5FEBED54A79A72269FDEADB9C13CFE540947694F45CAFBD81118AF25BF4` |

No merge, push, hosted publication, deployment or provisioning is approved by this review.

## Final evidence addendum: completed QMA gate and coherent handoff

Read-only follow-up, 2026-10-04. This addendum supersedes the earlier pending-full-QMA statement. No suite, mutation run, type scan or hosted workflow was rerun by this reviewer. The completed artifacts, source diffs, recorded configuration and draft ledger/handoff were inspected.

**The source and evidence are coherent and ready for the bounded integration handoff. Platform acceptance remains false; coverage and full nested typing remain red.** The integrator can checkpoint the reviewed composition and its accurate remaining-work handoff without representing these red gates as passing.

Full QMA `evidence/qma-8ae624d1a1b440dba37ed38fe815df58` records **2,049 passed, zero failed/skipped tests**, one upstream warning, in **290.03 seconds**. The process exit is **1** because aggregate coverage is **78.98048815609475%**, below the unchanged **80%** requirement. Separately, the tracked-source/per-package gate records daemon coverage **77.54%** (37,577 / 48,460 combined line-and-branch units), also below 80%. A successful test inventory is not a successful quality gate.

Independent inspection of the recorded coverage JSON against `git ls-files` found **287 tracked QMA source files and zero absent files**. The previous unmeasured entrypoint issue is resolved: daemon `__main__.py` records **35/61 covered statements** and **4/12 covered branches**. Remaining uncovered behavior is real coverage debt; no source exclusion, counter substitution or floor change was used to hide it. The coverage JSON and stdout hashes independently match the final summary:

| Artifact | SHA-256 |
|---|---|
| `pytest.txt` | `CCB6A3601AB467927EEFE76480D6B9A6F05C375877A2F9547BF99D9D60A89A14` |
| `coverage.json` | `BAA73C9BE56C081D91145E32E2F44F5453B641F48C8FD7C2269D5DBE5B5DEECA` |

The explicit reconstructed strict QMA source scan records **601 files analyzed, 68 errors, zero warnings**, using `evidence/types-qma-combined.json`; its diagnostics are preserved in `types-qma-combined-result.json`. These errors concern nine existing files, not a passing nested strict gate:

| File under `qmx-agents/packages` | Errors |
|---|---:|
| `qma-daemon/tests/test_daemon_process.py` | 55 |
| `qma-daemon/tests/test_local_proxy_broker_egress.py` | 4 |
| `qma-daemon/src/qma/daemon/taskgraph/outbox.py` | 2 |
| `qma-daemon/tests/test_task_graph_outbox.py` | 2 |
| `qma-core/src/qma/core/ports/qmb.py` | 1 |
| `qma-core/tests/test_qmb_door.py` | 1 |
| `qma-daemon/src/qma/daemon/artifacts/store.py` | 1 |
| `qma-daemon/tests/test_epic73_cancel_wire.py` | 1 |
| `qma-daemon/tests/test_stage_artifact_restart.py` | 1 |

The source scan and its absolute candidate/dependency paths are recorded; it is not a claim about a fresh hosted frozen environment. Its **68 errors** are distinct from the quality lane's historical **four root-workspace typing errors** in QMB native-research/private-test seams. Likewise, zero errors in focused owned-change checks never implied full source typing was green. Remaining annotation/fixture fixes must preserve runtime validation, authority and unknown-outcome behavior rather than globally suppressing rules.

Full QMA lint passes. The integrator normalized five files: the two reviewed barrier-delta files and three inherited formatter failures (`provider_config.py`, `test_daemon_process.py`, `test_experiment_spec_persistence.py`). Final `evidence/format-qma-combined-final.txt` reports **634 files already formatted**. Their displayed diffs contain only line wrapping/blank-line normalization; `record-qma-gate.py` compares the three inherited files' ASTs against `19f35af9`, and `_docwork/backend-qma-composition-gate-draft.json` records the successful AST equality assertion. No source behavior changed after the 2,049-test execution. Earlier formatting failures remain retained. Repeating the whole suite solely for these verified formatting changes is unnecessary.

The current zero-context memory draft passes read-only reverse validation with `--unidiff-zero`; whitespace checking passes. Updated `_docwork/backend-integration-ledger-draft.md` and `_docwork/backend-integration-handoff-draft.md` accurately distinguish test success from red coverage/types and retain broader QMB/QMN/native/CT47/actor/workflow/endurance limits. `_docwork/backend-qma-composition-gate-draft.json` ties the results to recorded source state, runner hash, paths and artifact hashes. The work is reviewable for a final isolated candidate commit; no protected merge, push, deploy or whole-platform approval follows from this handoff.
