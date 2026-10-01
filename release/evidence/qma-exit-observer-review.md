# QMA child exit observer bounded review

Candidate `83e05a03a8c0c5a62eaaed82667bdbe981e9fe31`: CHANGES REQUIRED. Observer increment only; current worker authority implementation is separate and remains unapproved.

Independent `/tmp/review_qma_observer.py` uses actual BacktestingService and JobHandleService. Injecting a typed terminal-completion refusal with a transport exit code 0 leaves the job RUNNING, while the observer thread exits and retains no failure/result. Transport wait returning True or None likewise silently ends observation with the job QUEUED. These transport values are intentionally hostile controls, not provider execution. `_start_exit_observer` discards observe_outcome's Result and silently returns on invalid exit code.

Source ordering adds a second unresolved risk: submit starts observation before record_coordinated_run. A fast child can terminalize the job before launch evidence is recorded; if that append refuses, the public placement returns refusal despite already launched/possibly completed effects. No independent fast-child fault proof is claimed here; source ownership/order requires correction and a held-out actual test.

Retain truthful observer failure/reconciliation state through existing JobHandle UNKNOWN/diagnostic authority as appropriate; never abandon a live job silently. Coordinate launch evidence, observer attachment, current attempt and terminal/cancellation handling under coherent service ownership. Check complete/observe Results and preserve retryable evidence uncertainty. SQLite operations already marshal through its dedicated writer thread, so this finding is not a raw SQLite cross-thread connection violation. Mutable service/job/occupancy state still needs serialized transitions and shutdown/restart observer ownership.

Actual child/socket GET_JOB positive, failed ledger/artifact readback, fast-child ordering, cancellation/UNKNOWN/restart and double-terminal controls remain pending corrected candidate. Earlier ee78 real loopback/installed-QMB test was independently run, but it does not approve this observer increment. Product/test source untouched; exact script and findings sent execution/root. Root-only Git.

## 1d0f5e79 corrective review

Candidate `1d0f5e79592c90d1c07bc1f4efd9edc5c6f9b9c8`: original persistent terminal-completion failure retains an active observer, known exit code and failure; True/None wait values now produce UNKNOWN with retained diagnostic rather than silently abandon a queued handle. Launch ledger append is attempted before observer attachment. These bounded corrections pass original controls, but CHANGES REQUIRED remains.

Independent `/tmp/review_qma_unknown_write.py` injects typed failure in the actual JobHandleService UNKNOWN transition after wait returns None. Observer exits while handle remains RUNNING; failure survives only in `_observer_failures` memory. The exception/invalid-code branches unconditionally return after the refused transition. Retain the observed uncertainty cause and retry durable UNKNOWN persistence or persist an owned reconciliation record consumed on restart; do not silently abandon the only observer after a failed uncertainty write. Also handle queued-start failure coherently. Exact repro sent execution/root. No raw SQLite cross-thread claim: the dedicated writer marshals SQL, and JobHandle compare-and-set uses its store lock.

Full current worker authority, restart observer reattachment, actual terminal artifact verification and cancellation/second-pack journeys remain separately pending. No product edits or Git mutations.

Reviewer focused backtesting-door suite: **10 passed**; held-out UNKNOWN persistence failure remains blocking.
