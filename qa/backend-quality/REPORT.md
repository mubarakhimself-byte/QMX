# Backend quality lane — 2026-10-04

This is an isolated, local review of `bf3c6b592e89917c17747eb1072203a28241e74a` (latest supplied skills/runtime checkpoint), with `1f3b98f6` available for baseline comparison. Branch: `quality/backend-ci`. No composition with pending QMB `4122420` or spot `8bee17d` was attempted. The integration lead must revalidate the composed candidate. Nothing was pushed, merged, deployed, or changed in GitHub settings.

## Ownership and initial root causes

Owned here: `.github/workflows/{battery,qmn-ubuntu-24.04,skylos}.yml`; `tools/{coverage_report,workspace_meta,mutation_gate,stage_mutation_config}.py`; their focused tests; two declarative mutation-scope TOMLs; this review/evidence directory. The unused `tools/readiness_gate.py` was removed after migrating the aggregate verdict into the actual workflow. Runtime package files, UI, canonical documentation, branch protection, authentication and Codex Review settings were excluded.

The most consequential defects were an incomplete mutation run appearing green, settings ignored by the pinned Mutmut version, tests hidden behind the first formatting/type failure, missing native Windows suites, incomplete branch/tag triggers, and coverage from another checkout being admitted on Windows. These were bounded CI/tools defects. Removing arguments or interpreting uncovered code as dead was explicitly excluded.

## Implemented checkpoints

| Commit | Result |
|---|---|
| `1edfcc95` | Remove `Member.import_name`: no live consumers; all callers use `module_name`. Existing member/structure regressions preserved. |
| `4305d239` | Fail closed on mutation command errors, missing modules, duplicate rows and unfinished/no-test/timeout results. Translate the existing scope declarations into supported Mutmut 3.3 options in disposable member manifests. |
| `05ecaf0e` | Exact first-party Node 24 action pins in all three workflows; contents-read permissions and disabled checkout credential persistence preserved. |
| `f2aaaf9f` | Require measured coverage paths to resolve inside this candidate and match its exact source inventory, including POSIX absolute and arbitrary relative paths on Windows. |
| `0fb836aa` | Native Ubuntu 24.04/Windows Server 2025 matrices for root and nested suites; frozen root/nested environments; independent mandatory steps; distinct coverage data files; main/integration push and candidate-tag coverage; include QMN in Vulture scan. |
| `8574ea26` | Correct pinned Click CLI syntax to `mutmut results --all true`, backed by execution of the actual workflow shell steps. |
| `c4dba14a` | Always evaluate aggregate prerequisite results, including cancellation; immediate runner-Python verdict without checkout/setup/network; remove redundant readiness helper. |

`bd707db9` is an intermediate cancellation approach superseded by `c4dba14a`; do not integrate it alone. Integrate the full checkpoint series or the cumulative patch.

The 80% aggregate and per-package floors, exact/chrono 100% contract floors, core mutation 68% floor, and QMN advisory survivor policy are unchanged. No exclusions or coverage padding were added. Skylos security/secrets/AI enforcement and advisory quality/dead-code policy are unchanged.

## Actual CI inventory

`ci-inventory.json` captures exact command strings, conditions, triggers, runners and tool pins directly from this candidate's TOML/YAML. The following describes their enforcement and limits.

| Workflow/jobs | Trigger and execution | Enforced versus advisory |
|---|---|---|
| Battery `backend` | Push main/integration, PR into either, `factory-candidate/**` tags; native Ubuntu 24.04 and Windows Server 2025; CPython `.python-version` = 3.14, uv 0.12.6, `uv sync --frozen` | All ten root `poe check` tasks mandatory, independently executed after successful sync; any failed step fails its job. Matrix fail-fast disabled. |
| Battery `agent-suites` | Same events and runners; independent environment under runner temp; own frozen nested lock | All five nested `poe check` tasks mandatory. Environment isolation is workflow configuration, not evidence of a locally completed nested suite. |
| Battery `check`, `agents` | Same non-scheduled events; `always()` job and step conditions; immediate inline JSON verdict | `check` requires exactly backend + agent-suites + vulture successful; `agents` requires agent-suites successful. Failure/cancellation/skipping/missing/malformed results fail. Existing aggregate context names retained. |
| Battery `vulture` | Same non-scheduled events; Ubuntu latest, Vulture 2.14, confidence 80 | Scan packages/extensions/QML/QMB/QMN/tools. Count cannot exceed committed baseline. Baseline at both supplied revisions is empty (zero findings), not a stale historical count. Broken scans fail closed. Findings still require entrypoint/API review before deletion. |
| Battery `mutation`, `mutation-qmn` | Schedule only, 02:17 UTC, Ubuntu 24.04, Mutmut 3.3.0 | Both command statuses and full classified module inventory required. Core killed fraction >=68%; QMN survivors advisory at floor zero. Unresolved statuses fail both. Schedule runs default-branch code; unmerged candidate mutation strength is unverified. |
| QMN `qmn-ubuntu-24-04` | Same push/PR/tag events; Ubuntu 24.04 only | Linux-specific QMN typing; CI-lane checks, install-labelled probe and fixture switch/rollback; upload missing artifacts only warns. This is controlled fixture evidence, not staging/live-provider evidence. |
| Skylos | Same push/PR/tag events; Python 3.12 for scanner wheels, Skylos 4.33.2 | Local scan accepts exit 0/1 as completed, rejects other exits; `cicd gate` enforces severity/category ceilings. Annotation command advisory (`|| true`); quality/dead-code count advisory, security/secrets/AI remain enforced. Nested qmx-agents excluded. No cloud upload added. |

Root sequence: `fmt-check`, `lint`, `types`, `test`, `cov-report`, `test-tools`, `money-path-scan`, `ambient-scan`, `mock-data-scan`, `secret-scan`. Root Ruff is 0.16.3 and Pyright 1.1.411. Nested sequence: `fmt-check`, `lint`, `types`, `test`, `cov-report`; nested Ruff is 0.16.5 and Pyright 1.1.411. Pytest/cov resolve through existing lockfiles. Both general typing configurations target Windows; the Linux runtime matrix does not prove Linux-specific general typing.

These are mandatory **workflow** results. Actual required-check settings were neither inspected nor changed. No merge-group event is configured; whether a merge queue needs it is unverified. `check-integration` (build-all + isolated-build), `check-release` (release evidence), `qa-verify`, and strict documentation validation remain unwired to these ordinary CI workflows. Workflow presence must not be described as complete tier-2/3 or component acceptance.

## Verification and provenance

Final focused command: `python -m pytest tools/tests/test_readiness_gate.py tools/tests/test_mutation_workflow.py tools/tests/test_mutation_gate.py tools/tests/test_stage_mutation_config.py tools/tests/test_coverage_report.py -q --no-cov`.

- **180 passed, 1 skipped**. Skip: this Windows host cannot create the manifest symlink used by a safety regression. Eight tests execute the actual nightly shell steps against a controlled CLI with the pinned upstream Click option declaration. Aggregate controls execute the actual workflow Python body and validate job/step conditions and needs. These are workflow-boundary tests, not a full mutation run or hosted scheduler simulation.
- Strict scoped Pyright: **0 errors**. Root canonical Ruff lint: **all checks passed**. `git diff --check`: clean. Exact root formatting scope: **20 inherited files** would be reformatted; new/changed tools introduce no formatting failure.
- Coverage-path controls initially reproduced two Windows false greens, then passed; **112 passed**, focused measured branch coverage **97.31%**. Mutation-gate controls: **26 passed**, **97.10%**. Staging controls: **12 passed, 1 skip**, including actual pytest selection **1 passed, 1 deselected**. Source-copy staging selected exactly core 2/9 and QMN 6/198 source modules. Full Mutmut generation/execution/kill rates remain unverified.
- Clean, separate coverage-data tools run: **619 passed, 3 failed, 2 skipped**, six canonical measured tools **98.36%**. Failures: ambient UUID call in QMB native research code; two existing QMN venue-import boundary failures. Restoring the original metadata helper before rerunning the two boundary controls reproduced both failures. These are not removed-helper regressions.
- Full root exploratory Windows run: **5,524 passed, 66 failed, 39 skipped, 7 live deselected**. Some child processes resolved task-8 editable sources; root coverage overlapped an early tooling run and included six tool modules. This run is diagnostic only, **not same-candidate acceptance**. Its mixed 76.78% coverage report and per-package deficits remain below the floor but do not establish a clean acceptance percentage. The contaminated tools run was discarded and rerun separately. No claim that coverage passes.
- Full root typing with an explicit usable interpreter: **4 errors**, all QMB native-research typing/test-private-access findings. The earlier 80-error assumption is stale. Using an unspecified interpreter produced dependency errors and was discarded. Strict docs: **25 inherited errors**, mostly expired verification dates plus provisional SCN-0017. Dates/statuses were not refreshed to fabricate verification.
- Full nested suite was not run: no available complete nested environment (`deepagents` absent). Hosted Linux/Windows matrices, hosted cancellation semantics and full Mutmut are unverified. No unknown-source installation, credentials, live provider, spending or trading used.

Raw local diagnostic logs are preserved alongside the isolated checkout in task-13: `backend-suite.txt`, `tools-suite-clean.txt`, `baseline-structure-controls.txt`, `pyright-final.json`, `format-final.txt`, `baseline-doc-lint.txt`, `mutation-workflow-red-cli.txt`, `mutation-workflow-green-cli.txt`. The report and inventory are portable; those logs are session evidence and are not committed.

## Shared-file proposals — integrator ownership

| Priority | Bounded problem and evidence | Proposed next ownership |
|---|---|---|
| High | `packages/qmf-data/src/qmf/data/intake_authority.py:55` imports `fcntl` unconditionally: 11 Windows failures before intake completion. | Runtime lead: implement or explicitly constrain the supported lock abstraction; meaningful native Windows/Linux intake tests. |
| High | `qmn/src/qmn/host/configured_runtime.py:917` rejects unsupported descriptor-relative reads on Windows: 18 tests stop at capability refusal. | Runtime lead: determine intended Windows support and preserve safe refusal; do not replace with unsafe path opens or broad skips. |
| High | QMN failure-register validation: 12 implemented configured-runtime IDs absent from FAILURES.md, causing 11 root failures including readiness cascades. | Runtime/docs lead: confirm IDs and behaviors then update register; no fabricated claims. |
| High | `qmn/ledger/protection_market.py` and `qmn/seats/dispatch.py` import `qmf.venue.ctrader` outside sanctioned `qmn.venue`. Two tooling and three root boundary failures. | Runtime lead: reconcile intended boundary/public API rather than suppress guard. |
| Medium | `qmn/deploy/ci_lane.py` install-labelled step returns success when uv is absent; existing uv invocation uses shared workspace environment/default groups. | Shared change proposed only: separate installed-wheel environment, fail closed when installer unavailable; verify declared dependencies without workspace leakage. |
| Medium | Four clear test portability artifacts: explicit fork, Windows terminate exit-code expectation, POSIX dir-fd race probe, escaped mapping-repr assertion. | Runtime/test lead: assert intended behavior through platform-supported seams; retain Windows coverage. |
| Medium | Four child traces import task-8 code and fail `_overlapped` WinError 10106; five native-store failures hide their underlying OS error. | Clean source provenance/environment first; capture actual native failure. No App Control/4551 evidence in this log. |
| Low | Private `_NANOS` in `qmb/src/qmb/data/generate.py:196` has no import/reference/registration use. | Evidence-only proposal; QMB runtime owner can remove with existing deterministic-generation regressions. |

Other root failures include stale CT-13 provenance examples, CP1252 output, ctypes structural contracts, ATC binding refusal, SinkAck identity rejection, and a supervisor timeout. Precise runtime causes for the latter three remain unresolved. No blanket deletions or unused-argument cleanup proposed. Protocol names, ctypes `_fields_`, registration/import/public API seams were preserved.

## Review and documentation handoff

Separate read-only SPEC and STANDARDS reviews of the final code checkpoint found **zero remaining code blockers**. Prior CLI and cancellation findings were fixed; both reviewers explicitly retain the hosted/full-mutation evidence limits. Findings are recorded in `REVIEWS.md`.

`canonical-documentation.patch` is **unapplied**, intended for the documentation owner after integration. It records configured CI behavior and its verification limits; leaves existing verification dates, canonical decision identities and runtime acceptance claims untouched. `ADR-DRAFT.md` is a proposal awaiting canonical ID/routing. No canonical document was edited. CI-mirror task-list drift and missing general Linux typing are remaining pipeline risks, not reasons to weaken current gates.

Official sources used: [Mutmut 3.3 implementation](https://github.com/boxed/mutmut/blob/3.3.0/mutmut/__main__.py), [checkout v5 release](https://github.com/actions/checkout/releases/tag/v5.0.0), [setup-python v6 release](https://github.com/actions/setup-python/releases/tag/v6.0.0), [upload-artifact v5 release](https://github.com/actions/upload-artifact/releases/tag/v5.0.0), [GitHub job condition semantics](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-jobs-with-conditions), [GitHub YAML anchors](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations#yaml-anchors-and-aliases). Node 24 action releases require runner >=2.327.1. Hosted Windows Server 2025 is not Windows 11 workstation release proof.
