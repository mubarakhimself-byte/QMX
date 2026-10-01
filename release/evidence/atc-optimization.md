# ATC and optimization connection evidence

Date: 2026-10-01

## Verified source contracts

The governing local authority is `docs/decisions/ADR-0024-workflows-construction-kit.md`
(DEC-0436, DEC-0448), `docs/scenarios/SCN-0020-two-trading-compositions.md`, and
`docs/components/qmb.md`. ATC must remain a complete `AlternativeRunConfig` with
Book/BMS/bot keys absent and a PolicyPair; QMB evidence is tagged
`composition_class: alternative` with CT-07 lineage to its PolicyPair hash. An
ATC run must not be coerced into the Book `LedgerLine`/CT-32 path, whose current
schema requires `book_bar_fp1`.

I also checked the governing `origin/main` artifacts with `git show`:
`architecture-QMX-2026-09-23/CONTRACTS.md` and its spine are the pack-and-grant
increment and add no AccountingPolicy/RiskPolicy token semantics. The parent
2026-09-18 CONTRACTS and Workflows rider enumerate closed PolicyPair fields but
do not define how values such as `fifo`, `last-mark`, or `fixed-fraction` execute.
Those semantics remain an architecture dependency; this implementation does
not assign meanings to them.

## Changes and limits

`validate_alternative_run_config` now reparses an `AlternativeRunConfig` value
through its canonical payload. A directly constructed or replaced dataclass can
no longer bypass PolicyPair hash verification. QMN ATC seat adoption uses the
same validation and carries the immutable hash-verified PolicyPair body to its
caller. This is a typed handoff only: QMN has no guarded replay root consuming
`AtcSeatAdoption` yet, so it is not evidence that node replay applied the policy.

QMB now has `run_study_generations`, a sequential bounded generation driver. It
only advances after all trial results have been read back as exact-assignment
`PriorTrial` values through the supplied ledger-view reader. It writes no replay
or evidence, and its focused tests use an in-memory fixture only to exercise the
barrier mechanics. Execution owns the actual replay evaluator, CT-29 terminal
reader, and materializer; that evaluator is not yet available for ATC. Its
current replay design is Book-only and must not be used by ATC until a genuine
PolicyPair evaluator exists.

`E2E_ADOPTION_CLOSED` and GAP-0098 remain open. No fabricated Book records,
provider access, venue activation, or live promotion were used.

## Commands and results

Baseline before edits:

```text
uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_alternative_run_config.py qmb/tests/test_optimize_sampler.py qmb/tests/test_optimize_resume.py qmb/tests/test_optimize_objective.py qmn/tests/test_qmn_atc_seat.py
80 passed in 1.08s
```

Final focused validation:

```text
uv run --no-sync pytest -q -p no:cacheprovider qmb/tests/test_alternative_run_config.py qmb/tests/test_optimize_sampler.py qmb/tests/test_optimize_resume.py qmb/tests/test_optimize_objective.py qmb/tests/test_optimize_study_driver.py qmn/tests/test_qmn_atc_seat.py
84 passed in 1.11s

uv run --no-sync ruff check qmb/src/qmb/config/alternative.py qmb/src/qmb/optimize/study.py qmb/src/qmb/optimize/__init__.py qmb/tests/test_alternative_run_config.py qmb/tests/test_optimize_study_driver.py qmn/src/qmn/seats/alternative.py qmn/tests/test_qmn_atc_seat.py
All checks passed!
```

The 84 tests validate config/hash refusal, QMN typed data handoff and gate
behavior, existing sampler/resume/objective ports, and the new generation
barrier. They do not validate ATC replay economics or node policy application.
