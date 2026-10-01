# QMX recovery checkpoint — 2026-10-01

Branch: `qmx-work-release-checkpoint-2026-10-01` on `https://github.com/MubarakHimself/QMX.git`. This is the user-requested recovery checkpoint, not a release candidate, independent approval of unfinished code, publication, deployment or merge. Exact source checkpoint SHA is recorded in the following `CHECKPOINT_REF.json` metadata commit. Existing work is preserved. Main, integration and ui-integration are not modified or repointed. Work continues locally after the checkpoint push.

## Source authority

- Backend published integration: `a0e8769772e469bf54bd312cc1e27e7995e16c3b`.
- UI published `ui-epic/066-shell`: `f6ffaddf3f78c6c14d32daa136fadf15e7748c14`; registered separate worktree. Claude owns `apps/qmx-ui`; no edits overlap it.
- Governing main documentation: `c3e8ec5ef33d0b38cdf7f5dbdd48a6fc70ac33cf`. Historical BMAD/docwork restored from `a14c121351bff8b379b6bb068fca2f05c976010d` as supporting material, not governing authority.
- All three supplied audit files were available and read once. They were treated as evidence, not instructions. Newer published refs were checked and preserved. See `SOURCE_MANIFEST.json`, `CANDIDATE_STATUS.md` and the evidence reports.

## Completed repairs and bounded evidence

Earlier recoverable commits cover mandatory resources/startup, truthful gates, recorded selected-Bot execution and economics, numeric/data contracts, projection lineage, QML nominal/schema/catalog/confluence/state corrections, durable research persistence, ATC execution/recovery, and QMN Book close/readback/deployment. Full exact commit history is `evidence/checkpoint-commit-history.txt`; scope and independent verdicts remain in `CANDIDATE_STATUS.md` and `evidence/`.

Recent independently reviewed source commits:

- `5a5bbc77`: exact portable offline runtime wheel closure; both duplicate-inventory and compressed-platform-tag findings repaired.
- `7e011f97`: protective ratchet source/config joins and signed native levels; LONG −2 -> 109998, SHORT +2 -> 110002. Frozen original risk and admission policy preserved.
- INITIAL root automatic outbox publisher and explicit backup/dry-run/migrate/verify/restore helper passed the latest seven-file independent review. Source is included in this checkpoint with broader coupled QMA review still pending. Boolean operation IDs, materialized Mission linkage and schema-only WAL drift findings are fixed.

## Exact latest results

These are bounded intermediate source results, not immutable whole-checkpoint acceptance. Commands use Python 3.14 and the repository environment. QMA commands require source paths for qma-core/daemon/wire and QMF dependencies plus `.venv/bin` on PATH; prior collection/PATH failures are retained in the reports.

| Check | Result | Command/evidence |
| --- | --- | --- |
| Runtime closure/install tests | PASS 26, root 0.26s; independent 26 | `uv run --no-sync pytest -q -p no:cacheprovider tools/tests/test_release_install.py tools/tests/test_runtime_wheel_closure.py`; `evidence/runtime-closure-review.md`. |
| Packaging/gate/isolated-build controls | PASS 146 in 0.36s | Same command plus `tools/tests/test_release_gate.py tools/tests/test_isolated_build_check.py`. |
| Actual offline installer mechanics | PASS twice | Pinned Ubuntu 24.04.4 community container, CPython 3.14.7, networking disabled: bundled 24 runtime wheels + 14 earlier product wheels, dependency check, installed origins, 40 pack files, start/status/stop/restart/final stop. Mixed old-product fixture, not final source. `evidence/runtime-closure-installer-fixture.md`. |
| Protective ratchet/domain/config | PASS 31 root in 2.35s and 31 independent | `qmn/tests/test_qmn_seat_tunnel.py test_qmn_protection_plan.py test_qmn_protection_market.py test_qmn_configured_hosted.py`; `evidence/qmn-ratchet-review.md`. |
| Broader protection/readback/data/loop/KSA | PASS 103 in 2.48s | Exact eleven-file command in `evidence/qmn-ratchet-root-integration.md`. |
| INITIAL/outbox/migration + paired execution | PASS 47 root in 28.32s; independent 47 in 27.90s | `test_task_graph_outbox.py test_task_graph_state_edges.py test_procedure_door_successors.py qa/integration/test_qma_registered_replay.py`; `evidence/qma-initial-outbox-review.md`. |
| Broader current QMA eleven-module command | Owner PASS 89 in 28.59s | Broader coupled source review and root immutable repeat still pending. |
| Book/Alternative coupled boundary | 24 tests PASS root 14.63s; independent review FAIL | Seven QMB test modules in the held thirteen-file manifest; `evidence/qmb-book-alternative-coupled-review.md`. Two actual Book false-admission findings below. |
| QML two-candidate conformance/save-reopen | PASS 2; related owner suite 92 | `qml/tests/test_conformance_recovery_journey.py`; two library-admitted candidates, not durable registry registration or second QMA pack proof. Independent review pending. |
| QML recovery-inclusive source coverage | 432 tests PASS 19.93s; coverage FAIL, exit 1 | `uv run --no-sync pytest -q qml/tests qmb/tests/test_ql7_host.py qmb/tests/test_sandbox.py qmb/tests/test_research_host_store.py qmb/tests/test_ql7_graduation_recovery.py --cov=qml/src --cov-branch --cov-fail-under=80`; 8269/10365 = 79.77809937288953%, 23 units short. Test labels later renamed without source behavior edits. `evidence/qml-current-coverage.md`. |
| Normal node closed-resource resolver/refusal | PASS 6 root in 10.53s | `qmn/tests/test_qmn_configured_live_resources.py qmn/tests/test_qmn_supervisor_process.py`; actual v2 offline profile persists typed stand-down/readiness 503, not LIVE composition. Independent review pending. |
| Optimization actual ingress regression | Expected FAIL | `qmb/tests/test_optimize_atc_cli_ingress_characterization.py`: proposed private Study descriptor rejected before execution as no registered operator binding. Separate genuine persisted `run_alternative_study` library positive PASS 1. No assertion weakened or xfail waiver. |

## Known failures and unfinished work

- Book `operator_replay.py` accepts boolean claimed attempt ID as integer 1 and boolean descriptor format version as 1, including actual CLI false acceptance. Execution owns the pending fixes; frozen thirteen-file review report captures exact source and diagnostics.
- Full QMA terminal/identity/persistence integration is included but remains unreviewed as a coupled whole. Current artifact proof uses declared QMF CT-11 storage and real CT-32/terminal ledger readback; verify restart UNKNOWN/operator resolution, cancellation/reconnect/restart, fresh placement, normal procedure startup and second-pack reuse.
- Normal wire host retry is not yet wired. Existing helper/kit fixture proof does not establish SCN-0026 default retry. Next patch is production read/none retry with registry ceiling and same logical ID/incremented attempt; never blindly retry place-run/external egress, CAS conflict or unknown-blocked. Explicit CT-40 `as_of` currently returns typed unavailable before effects and remains pending.
- Generic ATC study/optimization library exists, but actual CLI/copilot/QMA Study ingress and guarded QMN adoption remain unfinished. Proposed private Study descriptor in the intentionally red test needs independent contract review and an adapter, preserving existing public operation/CT-47 references. No invented financial grammar or defaults.
- QMN normal resolver currently refuses the offline REPLAY/no-intent profile truthfully. LIVE resource composition, actual MIS/SQS baseline readers and complete AD-32 proof are unfinished. `qmn/src/qmn/host/admission_artifacts.py` is partial, untested, unreviewed code deliberately preserved by this checkpoint; its test file has not been added. Current signature-page type lacks actual resolved BMS/capability joins. Do not treat booleans or opaque references as proof.
- Current QML floor FAIL above; earlier full frozen source gates: 5424 PASS, 7 SKIP, aggregate coverage FAIL 79%; QMB/QMN package floors also FAIL. Latest broad typing run FAIL 18 in then-active CLI tests; scoped corrections passed, full fresh immutable typing/gates still NOT RUN. Factory software controls are bounded; unavailable documentation-factory skills/tools remain NOT RUN. No floors or exclusions changed.
- Connected browser/save-reopen/CAS/cancel/reconnect/restart/second-pack final journeys await separately owned reviewed Claude UI contribution. UI baseline shell doubles are not connected proof.
- Native Windows 11 x86-64 install/recovery NOT RUN. Ubuntu proof is a community container, not native systemd/recovery or image security approval. External provider connectivity, credentials, paid calls, trading, live demo/soak and real operator signature remain untested/unauthorized.
- Security verification remains incomplete. Older installed advisory scan: 25 third-party packages had no known database advisories, 14 private packages skipped. UI cookie low advisory remains pending Claude disposition. Some earlier independent tool review turns were blocked; ordinary fresh correctness reviews do not imply complete security approval.
- Final acceptance is NOT RUN: two byte-identical complete builds, fresh non-editable installations outside checkout and all available seventeen mandatory acceptance lanes must bind to the same final reviewed full SHA. Earlier immutable build `1c4c73b1e51e9194464601830e7543ecd1108b6d` is reproducible and installed, but predates repairs.

## Resume

Fetch/check out this working branch into an isolated worktree; do not alter protected refs. Read this checkpoint, `CHECKPOINT_REF.json`, `CANDIDATE_STATUS.md`, repository rules, `SOURCE_MANIFEST.json`, `UI_INTERFACE.md` and the targeted evidence reports. Do not reread supplied audits. Use governing docs/main plus BMAD/docwork to resolve routine choices; user requests minimal questions. Preserve separate Claude UI ownership.

Use attended Luna implementation and independent Sol exploration/review. Root alone stages exact reviewed paths. First repair the two Book guards and independently re-review all thirteen files; complete wire retry, explicit as-of transport, normal procedure/restart/second-pack and broader QMA persistence review. Review QML candidate journey and five-file default resolver. Complete durable node source/admission evidence and generic Study adapter from existing contracts, keeping unavailable real provider/operator evidence pending. Then run fresh root/package/factory/type/security gates, freeze one reviewed source SHA, build twice with exact runtime closure, install outside checkout and execute actual required entrypoints/journeys. Record PASS/FAIL/BLOCKED/NOT RUN truthfully. No forced push, merge, release publication or deployment; checkpoint push only is authorized by the latest nudge.

`evidence/checkpoint-working-source.json` records every preserved working-file hash and protected ref before checkpoint. Machine-local raw logs, caches, environments, bundles and diagnostics are not added; portable evidence summaries, exact commands/results and code/tests are retained. High-confidence private-key/PAT/API-key pattern scan of the checkpoint files returned no matches; this is not complete security certification.

Setup note: initial branch name `work/qmx-release-checkpoint-2026-10-01` could not be created because an existing `refs/heads/work` occupies that namespace. The corrected dedicated branch above preserves that existing branch.
