# Independent release gate review

Reviewer: contracts_explore (separate from implementation author). Source snapshot is mutable working tree, 2026-10-01. No gate source changes or commits. Read release/UI_INTERFACE.md: guidance correctly separates existing transport and absent runtime composition; no protocol acceptance claim follows from it.

Executed `.venv/bin/python -m pytest tools/tests/test_release_gate.py tools/tests/test_coverage_report.py -q`: **214 passed**. These are unique targeted tests, not added to another run's acceptance total.

## Actionable held-out findings

1. **P1: artifact inventory can be incomplete and gate still PASS.** Manifest artifact mapping `{"empty.txt": "b" * 64}`, candidate `"a" * 40`, and every required lane PASS with that identical inventory is accepted. There is no declared expected BOM spanning 11 root distributions, nested QMA distributions, mandatory pack/schema assets, UI assets and selected launcher. Same-SHA equality does not establish that the chosen product is installed. Require an independently declared expected inventory/roles and immutable candidate BOM, then bind evidence to it. Never infer completeness from arbitrary nonempty evidence input.

2. **P1: non-inventory files can inflate source coverage.** Heldout exact/chrono each 1/1 lines and 1/1 branches, plus expected low.py at 0/100 lines and 1/1 branches returns 4.76% package FAIL. Adding untracked `packages/qmf-core/src/qmf/core/untracked.py` at 1000/1000 lines and 1/1 branches returns `[]` (PASS). expected_sources checks omissions only; summaries still count unexpected production entries. Require exact canonical inventory membership before tallies. Reject unexpected files or exclude them explicitly with visible evidence; they must not pad coverage.

3. **P2: command/trace are truthy rather than typed or bound evidence.** Every lane with `command=True`, `trace=1` is accepted. Nonexistent `trace.log` also satisfies checks. Validate nonblank string command and an evidence reference with hash/identity and existence in the approved evidence bundle. Separate format validation from verification of actual command outcome; do not call a permissive format validator full product acceptance.

4. **P2: source identity normalization discards arbitrary prefixes.** `_source_path('/tmp/unrelated/packages/qmf-core/src/qmf/core/exact.py')` returns candidate-relative exact.py. This is convenient portability but can bind evidence from a different checkout without detecting it. Accept relative canonical paths or absolute paths beneath declared measured checkout root; normalize Windows separators explicitly and reject outside root. Bind coverage report to candidate/inventory fingerprint in gate evidence.

## Inventory observations and limits

Current `workspace_sources()` enumerates filesystem Python files rather than `git ls-files`; 472 root sources on this checkout. Heldout comparison found no filesystem-only extras in that root set. A generic git-source pattern finds 724 including nested QMA workspace, which root source floor does not cover; nested QMA coverage remains diagnostic as documented. Do not compare this cross-workspace number directly with old audit 455 or count it as root instrumented sources. The root coverage CLI must use an explicit candidate tracked inventory; nested acceptance needs its own measured scope/policy.

Current gate use of full commit SHA and matching artifact mapping correctly rejects ordinary stale-lane and mismatched artifact controls in existing tests. It does not verify that SHA exists or describes the actual built tree, or that declared hashes match files; evidence producer/BOM verification must supply those guarantees. No CI, installed acceptance, Windows, browser or security verdict was run in this review.

## Retest after root repairs

Executed targeted tests again: **219 passed** (overlapping previous 214; do not sum). Heldout untracked high-coverage file now correctly returns outside-tracked-inventory and 4.76% floor failures. CLI now uses git-tracked source inventory and rejects out-of-root measured absolute paths. Required wheel names/UI/launcher/lock/pack inventory and typed command/trace checks added; CLI checks actual file hashes and local trace existence.

Residual evidence limit: all correctly named artifacts as empty files plus an empty existing trace and matching declared empty-file hashes still yield PASS. Thus this validator binds declarations to bytes, but does not inspect wheel/pack/UI/lock formats or authenticated execution outcome. Required lanes must supply artifact-content validation and concrete trace verification; validator PASS alone is not installation acceptance. This is not evidence actual lane runners accept those empty artifacts.

Direct aggregate `pytest qa/tests` is invalid for separate epic helper namespaces: 23 collection errors, not 23 product failures. Use qa/run_qa_verify.py per-epic isolation. Targeted Epic12 static test remains one failure, host/research_store.py imports os/pathlib; this is the proposed distribution-boundary question, not an authorized blanket purity exception.
