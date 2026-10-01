# Independent Sol review — partial execution disposition

Candidate `c930bc5d51740e991e916d057f8c252727db60f5`. **Changes required at the handler trust boundary.** This reviews runloop identity/terminality only, not the still-active Book partial-fill implementation.

Valid typed partial-fill then NoFill then terminal-fill preserves the same resting token until terminal and counts its filled identity once. A separate single-slice end-of-input partial-fill control leaves that token resting and records one filled identity. Legacy True still means filled/terminal and False means unfilled/live. NoFill alone must never erase the order. These are order identity counts, not quantitative fill exposure accounting.

The constructor validates flags, but `_execution_disposition` trusts any already typed instance. A hostile handler returning an invalid typed instance (constructed without the dataclass constructor) with `filled='yes'` or `filled=1` is accepted as a fill; `filled=False, terminal=True` silently removes the order without a fill. Revalidate exact booleans and invariant at the public handler-result boundary, returning a typed refusal instead of trusting constructor execution. This is a boundary robustness control, not a claim that normal dataclass construction bypasses validation. Concrete controls sent to owner/root.

No product edits. Relevant verification uses `qmb/tests/test_event_slice_loop.py` and `qmb/tests/test_in_loop_warmup.py` under `.venv/bin/python -m pytest -q -p no:cacheprovider`; **28 tests passed.** Cancellation remains a slice-boundary refusal and may not fabricate terminal fills or completed economics.
# Corrective review `d1ab6a40b8a11f86887a4abe87bee3ff3020c991`

**APPROVED for the bounded disposition correction.** Repeated the actual handler controls: valid False/False stays resting, True/False fills and stays resting, True/True fills and terminates; malformed typed flags 'yes', integer1 and False/True now return typed refusals. End-of-input partial still retains one filled identity and the same resting token. Combined Node/runloop/warmup verification passed 65 tests; this does not approve Book quantitative exposure/accounting, reviewed separately.
