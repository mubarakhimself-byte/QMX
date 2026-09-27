# UI factory review — 27 September 2026

**Verdict: NOT READY for unattended product coding.** Epics/stories creation can continue separately.

Reviewed worktree: C:/Users/Mubarak/Desktop/QMX-worktrees/ui-factory
Commit: c6717df7100eba3594043bad296fdcbe69ef01fb
Installed skill: C:/Users/Mubarak/.grok/skills/run-ui-epics/SKILL.md

Primary agent inspected executable workflow, CLI, quality/evidence, merge/CI, state/scheduling/input validation, doctor and tests. Independent gpt-5.6-sol reviewer hit a usage limit without returning findings; this is a direct primary-agent review, not a completed parallel review.

## Executed verification

Five test_ui_factory test modules: **25 passed, 1 skipped** in 5.58s, using uv run --no-project --with pytest python -m pytest -q -o addopts='' with PYTHONPATH=tools. Bare Python lacked pytest. The skipped test was the Skylos Svelte coverage probe (CLI absent), not verified coverage.

Isolated probes (temporary repositories/direct calls; no QMX branches mutated):
- Workflow-style omitted files + user_facing=True selected only ['python'].
- Same SHA/story quality evidence passed first run, then failed second: exit code 0 deserialized as 1.
- ff_merge refused when the destination was already checked out, matching the installed ui-factory worktree topology.
- Fresh user-facing quality with successful stub commands and no Reticle proof returned ok=true; this is a control-flow probe, not a product test.
- CI watcher given only an unrelated successful check returned success; subprocess response was stubbed, not a live GitHub test.
- Normal output '25 passed, 1 skipped in 5.58s' parsed as no test counts.
- Default state path resolved to QMX-worktrees/QMX-worktrees/_ui-factory; saved doctor/state actually exist there, while the documented path contains session/smoke evidence.
- Worktree remained clean at reviewed SHA. No product implementation or factory launch, merge, push, active-state edit or installation performed.

## Required corrections

### R1 — P1: Normal workflow omits the inputs needed to run frontend gates

references/ui-epic-build.rhai:177–188 builds quality command without --files, --needs-backend or --story-hash. quality.py:59 onward selects UI profiles from files, so normal workflow runs Python-only even for user-facing stories. config.json:10–15 and ui-quality.yml additionally permit the synthetic test app as host fallback; approved product path apps/qmx-ui is absent.

Derive changed files from Git and carry validated story metadata, actual story hash and required capabilities through build, verify and merge. User-facing intent must require UI checks independently of a missing file list. Resolve the product package explicitly; fixture-only mode must be separate and unable to satisfy product readiness. Missing product host cannot produce a successful product CI check.

### R2 — P1: Required Reticle proof is not enforced on the real merge path

quality.py:309–313 writes blank reticle_verdict and calls evidence_ok(require_reticle=False) on fresh evidence. merge_gate.py:143–167 trusts that result and never invokes evaluate_promotion, the stricter helper tested by the suite. No production ingestion path sets an actual Reticle verdict. Workflow also trusts returned passed/exit_code and never reads its evidence_path.

Persist genuine act/assert result with journey and candidate identity and enforce required proof at the actual promotion boundary. Missing/unknown/no must block; fixture forced-yes must not count. Wire the proof into executable paths, not only prose/helpers.

### R3 — P1: Evidence round trips and validity are incorrect

evidence.py:87 uses int(item.get("exit_code") or 1), converting success 0 to failure 1. Resume/recheck falsely fails immediately. dirty_fingerprint hashes porcelain status, not content: changing an already-modified file keeps its fingerprint. Cache identity excludes requested profiles and hashes expected pin strings rather than observed toolchain. Normal test output parser returns {}; required counts are not populated for ordinary test commands, so zero/skipped required tests are not enforced.

Preserve zero, use typed schemas and actual SHA/content/lockfile/toolchain/command-profile identities, validate required check inventory and machine-readable test results. Tie evidence to immutable artifacts. On Windows log names include colon in profile:command, which can produce alternate data streams rather than portable ordinary files; encode safe filenames.

### R4 — P1: Promotion cannot work in the installed topology and CI is not a gate

merge_gate.py:66–99 always adds a second worktree on destination; ui-integration is already checked out at ui-factory, so Git refuses. Existing fixed merge temp is removed with --force without ownership/cleanliness proof, unsafe under concurrent operations. run_merge_gate merges and may push before CI; ci_wait.py only samples once, does not wait, and accepts any nonempty all-success run list without required workflow names. timeout is printed, not enforced.

Implement owned/serialized promotion compatible with occupied branches without force-removing unrelated work. Test an immutable candidate and require named checks on its exact SHA before promoting UI integration. Recheck target movement under lock. Missing/pending/failed required checks block. Preserve candidate and report on CI unavailability; no simulated result qualifies.

### R5 — P1: Resume state is disconnected from execution

paths.py derives roots from checkout-parent, yielding nested QMX-worktrees. Child checkouts can therefore diverge from documented shared state. StateStore.upsert_unit exists but no production workflow/CLI calls it; only setup/no-story writes occur. Workflow ledger stays in memory until completion. CLI resume merely lists persisted units, which execution never creates. Port/health helpers are similarly not integrated into the workflow.

Use a stable project identity and shared state root across all worktrees. Persist transitions and ownership at real execution boundaries, wire process/port leases and served-revision checks into browser steps, and recover interrupted build/verify/review/promotion without guessing completion from commit subjects alone.

### R6 — P1: Input/dependency validation is not a scheduling gate

validate_inputs.py:169–189 receives an empty merged-feature set from all CLI callers, blocks only selected backend dependency cases, and allows missing source/component/design metadata as runnable because only three fields are enforced. Non-backend prerequisites and cycles are not checked. schedule.py plans input order rather than a dependency DAG. cmd_run_selected ignores --ids in validation and returns ok=true even for invalid input.

Consume verified dependency completion from current artifacts/Git/runtime evidence as appropriate, support supplied BMAD format through an adapter without rewriting stories, enforce required metadata, detect unknown/cyclic edges, and schedule only runnable selected units. Prove completed dependencies unblock and unfinished dependencies cannot run.

### R7 — P1: Doctor claims capabilities it never probes

cli.py:51–55 and 73–75 assign MCP connected booleans without calls. doctor.py treats an out-of-pin Node as ok and only a small subset of failures as readiness blockers. Saved doctor is ready=true with Node 24.18.0 against >=22.12.0 <23.0.0, fixture as host and unmeasured MCP claims.

Distinguish installed/setup-ready/waiting-for-stories/runtime-ready. Use observed tool versions and actual Grok MCP calls (including child access) with retained evidence; otherwise report unknown. Provision approved versions locally or record a deliberate approved amendment, not a pin mismatch labeled ready.

### R8 — Closure evidence must test orchestration, not only helpers

The saved live smoke calls factory-selftest, which only prints text. It proves a workflow agent can invoke the CLI, not build -> verify -> review -> candidate -> CI -> promotion -> resume. Existing tests pass while the above defects remain. Skylos probe is skipped here and its source accepts any output containing 'secret', even the fixture filename; tighten to structured rule/location evidence and expected coverage.

Require a bounded synthetic complete lifecycle through the actual workflow. Include negative controls for R1–R7, real Svelte build/browser interaction with deliberate broken outcome, real Reticle proof, restart recovery and occupied-destination promotion. Separate local, simulated and live-CI evidence. No product epics may start as part of factory repair.

## Scope retained

Keep backend run-epics untouched. Preserve the new UI lane and useful tests, adapters and tooling. Do not recreate epics/stories or rerun Documentation Factory. Fix the factory; do not redesign QMX. External reviewer purchases remain deferred.

