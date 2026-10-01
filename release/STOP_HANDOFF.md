# Stopped checkpoint — 2026-10-01

Work is stopped at the user's instruction. This is an **unfinished recovery checkpoint**, not an accepted release. Do not resume automatically. No new implementation, broad audit, coverage work or test battery was performed to prepare it.

## Identity and preservation

- Dedicated branch: `qmx-stop-checkpoint-2026-10-01`, existing remote `https://github.com/MubarakHimself/QMX.git`.
- Code checkpoint commit: **`bbea29d5cb470a7cc5fc48016f598e38c4e0160e`**. The branch tip adds this handoff and the file census; obtain its exact metadata commit with `git rev-parse origin/qmx-stop-checkpoint-2026-10-01`. The final response records the remotely verified tip. No later implementation is intended.
- Previous remotely verified checkpoint: `01fed525af621173cf58929801d9b58fc316d870` on `qmx-work-release-checkpoint-2026-10-01`. Subsequent local reviewed repairs through `f48d46d9b95b4f8c61b415656b1c853577e552bc` are ancestors of this checkpoint.
- Published backend: `a0e8769772e469bf54bd312cc1e27e7995e16c3b`; governing main: `c3e8ec5ef33d0b38cdf7f5dbdd48a6fc70ac33cf`; UI baseline: `f6ffaddf3f78c6c14d32daa136fadf15e7748c14`. Published pins matched the supplied audit pins on inspection. Historical BMAD/docwork support: `a14c121351bff8b379b6bb068fca2f05c976010d`, subordinate to governing main.
- Main/integration/ui-integration were not changed or repointed. Remote-tracking identities at stop: main `c3e8ec5…`, integration `a0e8769…`, ui-integration `d3c6e1234b3dbf865e78179bc262cbbe90b1cc90`. Existing local `release/rc-2026-10-01` remains `ab94506a5b4380a40e7064fbbba7ef8a40a61873`; original documentation checkout is preserved.
- Data/Execution were interrupted after stopping; Numeric/reviewer reported stopped. Two never-initialized host/review entries still displayed `pending_init` despite interruption; explicit cancellation messages were queued, and no edits/results came from them. No active editing worker remained. The old UI preview process was stopped. This host-state limitation is recorded rather than concealed.
- Exact-path staging preserved all 14 dirty source/test/report files, including incomplete code. `STOP_CHECKPOINT_FILES.json` records 54 changed files since the earlier pushed checkpoint with hashes. A bounded credential-pattern/path review found no flags; `git diff --check` passed. No full security clearance is implied.

## Completed fixes and evidence limits

Counts below are overlapping selections, **not additive**. Reports in `release/evidence` retain failing versions and exact reviewed file hashes.

| Bounded completed scope | Existing evidence | Applicability at stop |
| --- | --- | --- |
| Actual two-Bot saved-source sandbox, CT-06/33/34 persistence/fresh reopen, nonempty execution and snapshot restore; refusal storage census and zero construction | Root 2 PASS in 2.35s; Sol 2 PASS in 2.51s; `qml-two-registered-bots-recovery-review.md`, test SHA `16242094f8458f1f2097d4903f08ce576e42da299bc807de66c45c1ec6c4202d` | Same final test bytes. Bare conformance ticket remains a trusted low-level API; test-owned identity assertions do not prove product registration-ingress enforcement. |
| Shared official registered-template decoder for nonempty CT27/CT28/Book persistence | `dba74da8`: root/Sol 20 PASS; dependent resolver slice 10 PASS | Listed source hashes unchanged at stop. Admission producer changes are separate and unreviewed. |
| ATC Study computational/operational identity, versioned pending-trial recovery, ordered durable witness and exact shared sensitivity | `ba65bdf7`: root/Sol 60 PASS; Study/sensitivity reports | Listed library bytes unchanged. Normal optimization CLI/QMA ingress and Book sweep are unfinished. |
| Book/Alternative delegated input/claim/producer witness | `9521e13b`: root/Sol 25 PASS | Library/CLI slice reviewed; later QMA transport changes are not covered. |
| Signed protection ratchet and config/source/native-level identity | `7e011f97`: root/Sol 31 PASS; broader root 103 PASS | Bounded unchanged protection slice, not normal installed node/provider execution. |
| QMA INITIAL authority, explicit safe migration and outbox binding | Root/Sol 47 PASS; INITIAL review | Earlier bounded snapshot; later process/session edits require re-review. |
| QML declaration, generation, footprint, snapshot correctness and filesystem research persistence | Earlier review reports; filesystem slice 16 PASS | Reviewed slices; no final installed combined proof. |
| Runtime wheel closure/verified installation tooling | `5a5bbc77`: root/Sol 26 PASS; actual two identical 24-wheel closures | Helper bytes unchanged. Actual network-disabled Ubuntu install/lifecycle used **older product wheels** plus corrected helper, not checkpoint products. |

## Unfinished edits and failed/skipped/not-run checks

- **Retry:** six daemon session/process/example/test paths preserved. Retry6 root/Sol 59 PASS predates the last progression change; independent shared-dispatch repeated-attempt probe FAIL/P2 remains in `qma-host-retry-review.md`. Owner's latest two-module run after the repair: **11 PASS**, unreviewed. No final full typing/lint/recovery verification.
- **SQS:** `qmn/host/admission_artifacts.py`, new `sqs_baseline_producer.py` and its test preserve incomplete exact-readback/durable-recipe work. Original independent FAIL: lawful 20/40 scale5 mean refused after write; recipe verification was transient and correction annotations were not safely resolved. Latest owner **4 PASS** after edits; latest Ruff/Pyright and receipt corruption/foreign-binding/correction regressions **NOT RUN/unfinished**. Earlier 8 PASS does not validate these bytes. Old generic input reader's false derivation flag must not be promoted by assertion.
- **Optimization transport:** daemon `backtest/cli.py`, `backtest/service.py`, new transport test preserve incomplete Study result parsing/preflight. Owner 3 tests PASS before later typing-only edits; 29 door/procedure tests PASS before latest service edits. Latest Pyright rerun **NOT RUN**. No QMB Study runtime/CLI implementation or Book Study adapter was written. Existing `invoke_optimize_run` is still a single backtest trial.
- **Coverage:** immutable older `1c4c73b1e51e9194464601830e7543ecd1108b6d` root run: 5,424 PASS, 7 SKIP, aggregate **FAIL 79.00%**, QMB 76.28%, QML 77.64%, QMN 74.74%. Latest pre-correction registered-source selection: 434 PASS, **FAIL 8271/10365 = 79.797395% QML**. It returned 0 despite printing a floor failure; exact counters, not rounded 80%, determine failure. The final test correction was not coverage-rerun. No threshold/exclusion/assertion was weakened.
- Latest mutable root `poe types` had zero errors before later edits; nested/final typing and full root/nested suites are **NOT RUN for this checkpoint**. Formatting failed on nine files at old `1c4c73b1`, subsequently corrected; that historical run is not current acceptance.
- Factory skill/tooling was unavailable (**NOT RUN**); earlier factory-software test results are not substitutes. Invalid combined QA helper collection produced namespace errors; use per-epic `qa/run_qa_verify.py`, not combined `pytest qa/tests`.
- Final connected browser save/reopen, cancellation/reconnect/restart, second-pack reuse, complete normal installed QMA/worker/node execution, same-checkpoint two builds/two installs, native Windows recovery and full security: **NOT RUN**. UI shell uses recording transport; separate Claude contribution is pending. Current explicit `as_of` execution is truthfully unavailable before effects.
- External provider connectivity, credentials/paid calls/trading/operator promotion: **BLOCKED by missing authorization/access**. Local LIVE-labelled quotes and operation/provider doubles prove no external connection. Known UI `cookie@0.6.0` low advisory remains pending Claude repair/disposition. Earlier audit found no known advisory for 25 third-party installed distributions; 14 private distributions were skipped. That is not complete security verification.

## Why the release mechanisms were added or changed

These mechanisms are preserved, not improved during this checkpoint. They were added for the earlier full-release request; they do not define the newly proposed bounded objective.

| Mechanism | Concrete requirement/defect and evidence | Reuse and limits |
| --- | --- | --- |
| `release/SOURCE_MANIFEST.json` | Default checkout could contain governing docs only; backend/UI/docs came from distinct authorized refs. Records exact provenance and ownership rather than claiming main contained the implementation. Source fetch/ref inspection justified it. | Git refs/worktrees were reused, but no existing combined product provenance record was identified. It is historical metadata, not runtime configuration or acceptance. Old branch/worktree strings and some pending statements are stale; this handoff/evidence supersede them. |
| `tools/release_gate.py`, root/nested coverage gate changes | Existing `poe check`/`check-integration` covered source/static/build checks, not real installed journeys. The user required same-candidate artifacts, actual execution and visible missing Windows/security/browser results. Independent review demonstrated arbitrary incomplete inventories, untracked coverage padding and incorrectly typed trace/command acceptance; subsequent tests corrected these checks. | Existing Poe sequences/scanners/coverage machinery were retained. Added fail-closed product-evidence layer and nested scope rather than treating unit success as release acceptance. A declared PASS plus valid bytes is still not authenticated execution proof. All 17 full-release categories remain mandatory in this gate; it has not been weakened for the smaller proposed objective. |
| `tools/build_release.py`, `release/install.py`, `runtime_wheels.py` | Needed reproducible non-editable install outside checkout with mandatory packs/UI/deploy assets; editable source or stale wheels could hide missing resources/dependencies. Existing evidence: old immutable 38-artifact double build was byte-identical; actual installed economic readback and launcher lifecycle; packaging review 26 PASS; offline Ubuntu mixed installer fixture twice. | Reuses `uv build`, lock exports, pinned pnpm build and package resources. New orchestration binds a clean detached SHA, deterministic archives/hashes, validated private install snapshot and optional exact runtime wheel closure. Factory tooling excluded from product closure. Offline closure supports Linux CPython3.14/glibc>=2.34 only; old builds do not prove checkpoint install. |
| `release/launcher.py` | Needed a user-facing installed entrypoint instead of importing checkout paths or starting a second host mechanism. Installed old-snapshot start/status/stop/restart and network-disabled Ubuntu lifecycle justify the thin wrapper. | **Existing `qmb host start` is reused**; the wrapper only finds the installed executable and preserves its exit code. It does not implement a new daemon or prove browser/provider/node readiness. The wrapper is convenience packaging; direct lifecycle CLI remains usable. |

The **80% aggregate and per-package line-plus-branch coverage floor** and **100% branches for exact.py/chrono.py** came from the existing backend `pyproject.toml`/`tools/coverage_report.py` (AR-20/M1), not a new target invented to chase coverage. Tests/examples are excluded from product numerator. Source-inventory/path validation prevents unrelated files padding it. Nested QMA 80% enforcement was extended during this pass to cover shipped packages omitted by the root workspace; it is an extension of that source policy, not a separately ratified architecture decision. Coverage measures exercised source decisions, not financial correctness, connectivity or product acceptance.

## Candidate issues for stable core, mini-apps, one node and fresh install

Proposals only: no board/issues/PRs/assignments have been created. Each should be a small separately reviewed change.

1. **Finish shared retry progression.** Evidence: retry6 repeated exact attempt3 invoked callback twice; final repair only has owner 11 PASS. Pass: original work survives lawful revoke/reopen; identical repeated next attempt invokes no second callback; changed input, skipped attempt and legacy missing proof cause zero effects, with durable journal progression.
2. **Complete supported worker restart/cancel/reconnect.** Evidence: whole coupled QMA and final installed journeys pending, later service edits unreviewed. Pass: normal procedure/lease/grant starts a registered worker, records actual owned terminal/economics, reopens without duplicate execution, cancellation stays durable, reconnect and second-pack reuse work.
3. **Bind the registration host to the actual candidate/source.** Evidence: lower-level `ConformanceTicket` is only two booleans; genuine test currently checks identities itself. Pass: product host accepts source-bound conformance candidate and refuses foreign declaration/source/ticket before Registrar/storage/factory effects.
4. **Finish the typed `as_of` transport.** Evidence: currently unavailable; `qma-as-of-interface-review.md` and `as-of-input-knowability-interface-review.md` distinguish context knowledge cut, registry set, CT10 availability and journal frontier. Pass: matching approved cut works through real entrypoints; stale/future/malformed/foreign source cuts refuse before effects; restart keeps full input identity.
5. **Finish one node's durable source-derived baseline and resource composition.** Evidence: SQS review FAIL, current repair unreviewed; supervisor only supports offline REPLAY stand-down; LIVE frontier/admission/MIS/capability joins incomplete. Pass: fresh physical read recomputes pinned exact fit/calendar occurrences, corrupt/foreign/correction refs refuse with zero effects; configured actual node records terminal/protection/ledger and truthful readiness. Label local doubles; actual provider proof separately needs authorization.
6. **Integrate the reviewed mini-app UI.** Evidence: published shell uses recording transport, Claude contribution unavailable. Pass: real paired HTTP/WS journeys create/save/reopen an app, enforce current grant/Task authority, run/cancel a job, reconnect/restart and reuse a second pack. Codex must not overlap Claude UI edits.
7. **Prove one basic fresh install from this reviewed core.** Evidence: actual install exists only for earlier products, not final checkpoint. Pass: clean non-editable install outside checkout, real package/resource origins and `pip check`, launcher start/status/stop/restart, registered recorded-input trade and durable economic readback. Native Windows remains necessary if Windows is the chosen immediate target; Linux proof cannot substitute.
8. **Resolve core validation failures without padding.** Evidence: exact coverage floors still FAIL and final typing/source suites are unmeasured. Pass: meaningful behavior regressions for real missing/incorrect core paths and unchanged root/nested/source-inventory gates pass. Do not start coverage work merely because a counter is short.

Optional/later: multi-node placement/operation, full offline Windows closure/native recovery hardening, wider provider matrices, broader release security/operational hardening and final 17-lane release packaging. Full ATC/Book optimization remains unfinished scope, explicitly deferred from the immediate bounded objective rather than declared implemented: fixed total budget, actual multiple CT32 trials/whole-history recovery/sensitivity and normal CLI/QMA ingress must eventually replace the single-trial alias. No architecture, topology, financial grammar or policy threshold is silently chosen.

## Resume only after a new user instruction

Fresh machine/source recovery (existing authorized remote, no credentials changes):

```bash
git fetch origin qmx-stop-checkpoint-2026-10-01
git worktree add -b qmx-resume-core /path/to/new-worktree origin/qmx-stop-checkpoint-2026-10-01
cd /path/to/new-worktree
uv sync --locked
uv sync --project qmx-agents --locked
git show bbea29d5 --stat
```

Targeted first checks after selecting a bounded issue, not commands run for this checkpoint:

```bash
uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_two_registered_bots_recovery.py
uv run --no-sync python -m pyright qmn/src/qmn/host/admission_artifacts.py qmn/src/qmn/host/sqs_baseline_producer.py qmn/tests/test_qmn_sqs_baseline_producer.py
uv run --no-sync ruff check qmn/src/qmn/host/admission_artifacts.py qmn/src/qmn/host/sqs_baseline_producer.py qmn/tests/test_qmn_sqs_baseline_producer.py
uv run --no-sync pytest -q qmn/tests/test_qmn_sqs_baseline_producer.py qmn/tests/test_qmn_admission_artifacts.py
cd qmx-agents/packages/qma-daemon
uv run --no-sync pytest -q -p no:cacheprovider tests/test_product_session_*.py tests/test_host_retry.py tests/test_qmb_optimize_study_transport.py
```

Root fixtures/PYTHONPATH must not be confused with nested workspace namespaces; earlier incorrect QMA environment caused collection failure. Independent review must bind **new exact bytes**, not reuse old PASS reports. After core fixes, use existing `uv run poe check-integration`, nested workspace checks and clean build/install commands in `release/README.md`; do not run/deploy/merge/publish automatically.

## Not pushed

Virtual environments, caches/node_modules, generated coverage files, runtime wheelhouse, old product bundles/installations, Ubuntu container state, raw `/workspace/qmx-*.log/.json/.py` drivers/probes, independent-review archive, uploaded audit files and raw worker messages are local only. Reports and hashes are pushed, but many raw traces are not; on another machine those records cannot substitute for rerunning a selected check. Local archive includes `/workspace/qmx-independent-review-archive/qma-qmb-local-authority-diagnostics`, old bundles `/workspace/qmx-bundle-replay-{candidate,repeat}`, runtime wheels `/workspace/qmx-runtime-wheelhouse`, old installs `/workspace/qmx-installed-replay-candidate` and `/workspace/qmx-ubuntu-runtime`. No credentials/secrets, machine configuration or generated executable artifacts were included. No reviewed Claude contribution was available. Historical source-manifest local paths describe evidence provenance, not install requirements.
