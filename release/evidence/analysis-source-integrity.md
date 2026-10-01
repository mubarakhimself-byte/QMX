# Analysis projection CT-29 source integrity

`analysis.project` previously accepted an in-memory `ClosedTrade` sequence while reusing
CT-32's `ct-13:ct-29:<binding>` locator. A substituted row could therefore affect the
predicate result without being read from durable evidence.

The projection input now requires `CT29ProjectionSource`, a typed QMF JournalReader,
stream name, WriterId, binding epoch, and CT-29 result label. The projection reopens the
CT-13 stream through QMB's validated replay-position fold, hydrates close records from
checked CT-13 bodies, retains opening-side attribution from checked position witnesses,
and derives `ClosedTrade` measures from those CT-29 records. It requires the CT-32
binding locator, result world/account role, exact trade count, aggregate net profit, and
fees to match. Caller-supplied row lists, mappings, and bare cites refuse. Saved views
retain only canonical CT-32/CT-29 references and query fields.

The provider-free regression composes a real Book entry and close through CT-13, reads
the durable CT-29 record, projects it, writes the governed JSON sidecar, reopens/cites
that body, and refuses in-memory substitution, foreign stream/writer, mismatched binding,
and mismatched CT-32 economics.

Validation:

- `uv run pytest -q qmb/tests/test_analysis_project.py qmb/tests/test_analysis_source_integrity.py qmb/tests/test_analysis_project_homes.py qmb/tests/test_analysis_compare_runs.py` — 44 passed.
- `uv run ruff check qmb/src/qmb/analysis/project.py qmb/src/qmb/analysis/__init__.py qmb/tests/test_analysis_project.py qmb/tests/test_analysis_source_integrity.py qmb/tests/test_analysis_project_homes.py qmb/tests/test_analysis_compare_runs.py` — passed.
- `uv run pyright qmb/src/qmb/analysis/project.py qmb/src/qmb/analysis/__init__.py qmb/tests/test_analysis_project.py qmb/tests/test_analysis_source_integrity.py qmb/tests/test_analysis_project_homes.py qmb/tests/test_analysis_compare_runs.py` — 0 errors.

This establishes provider-free local CT-13/CT-29 readback and projection behavior. The
CLI/runtime composition must construct `CT29ProjectionSource` only from its trusted
operator-bound journal descriptor; query JSON does not construct a reader or supply
trade rows.
