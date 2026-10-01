# ATC optimization library evidence

The ATC library path now evaluates registered policy code over a validated
recorded CT-10 replay source, writes each accepted transition to replay CT-13,
and exposes the final exact measures through a private versioned QMB terminal
artifact. Terminal reads re-open the CT-13 logical and physical references and
the persisted CT-07 `occurrence-of` edge to the selected PolicyPair. This path
does not emit Book, BMS, bot, CT-32, or Book-R records.

The Study driver binds every sampled parameter to one declared accounting or
risk field, derives and validates the candidate PolicyPair identity, and uses
the same interpreter code fingerprint and declared measure contract for each
candidate. Its objective names a registered measure, direction, CT-01 unit-kind,
and currency where applicable. It writes a Study trial label into every CT-13
decision and the run receipt, then persists that same label with the terminal
artifact. A complete proposal generation advances only after terminal
read-back. The regression exercises one completed ask, cancellation during the
generation, restart from the durable artifact, skipping the completed run, and
completion of the remaining ask. The selected `accepted_entry` count varies
with the tested candidate `max_gross` policy field.

Provider-free fixture verification:

- `uv run ruff check qmb/src/qmb/execution/alternative.py qmb/src/qmb/execution/alternative_terminal.py qmb/src/qmb/optimize/alternative_study.py qmb/src/qmb/optimize/__init__.py qmb/tests/test_alternative_execution.py` — passed.
- `uv run pyright qmb/src/qmb/execution/alternative.py qmb/src/qmb/execution/alternative_terminal.py qmb/src/qmb/optimize/alternative_study.py qmb/src/qmb/optimize/__init__.py qmb/tests/test_alternative_execution.py` — 0 errors.
- `uv run pytest -q qmb/tests/test_alternative_execution.py qmb/tests/test_optimize_study_driver.py qmb/tests/test_optimize_resume.py` — 32 passed.

This verifies the QMB library interfaces and local persistence round-trip. The
registered QMA/CLI Alternative request descriptor and consumer integration are
owned by the execution agent and remain separate work. External paper or live
activation is not tested; ATC adoption remains open and `E2E_ADOPTION_CLOSED`
remains false.

## CT-13-complete / terminal-missing recovery

The Study invocation now takes an operator-resolved `JournalWriter` and exact
`initial_accounting_state`. It records the original full CT-13 `WriterId` in each
trial intent before calling `execute_trial`; the callback receives that same
writer as its final argument. On a retry, a complete intent is reconciled against
the exact candidate/source/split and every expected CT-10 frontier. Recovery
reopens checked CT-13 events and their independently indexed physical rows,
verifies the interpreter/config/label/frontier and accounting-state/output
fingerprint chain, reconstructs the original run receipt, and writes the ordinary
CT-07 edge and terminal artifact. It does not invoke the interpreter again.

The retry may run under a new writer boot only when machine, role, and stream
match the operator-pinned stream. Recovery resumes the original WriterId named by
the intent; new asks use the current boot writer. Mismatched stream identity,
missing or partial frontiers, duplicate or extra labeled events, and any broken
physical-row or state-chain proof remain typed refusals. An intent created before
any CT-13 decision therefore remains blocked because the system cannot prove
whether policy execution took effect.

The regressions inject failure before intent persistence, after intent but before
the first CT-13 decision, after a full CT-13 chain but before terminal persistence,
after the CT-07 edge but before terminal JSONL, and after terminal JSONL with the
caller-visible acknowledgment lost. They check retry under a fresh writer boot,
reopened terminal and registry state, and no duplicated CT-13 decisions, terminal
artifacts, or evaluator calls.

Verification for this corrective slice:

- `uv run ruff check qmb/src/qmb/execution/alternative.py qmb/src/qmb/execution/alternative_terminal.py qmb/src/qmb/optimize/alternative_study.py qmb/tests/test_alternative_execution.py` — passed.
- `uv run pyright qmb/src/qmb/execution/alternative.py qmb/src/qmb/execution/alternative_terminal.py qmb/src/qmb/optimize/alternative_study.py qmb/tests/test_alternative_execution.py` — 0 errors.
- `uv run pytest -q qmb/tests/test_alternative_execution.py --no-cov` — 20 passed.

This library recovery contract is ready for the execution-owned operator
descriptor to supply the pinned replay stream and resume the stored WriterId.
It does not close ATC adoption or make external paper/live claims.
