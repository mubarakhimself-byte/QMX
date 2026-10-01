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
