# Independent Sol review — durable JobHandle host slice

Candidate: `8f98fa0d5a14e325272b41af2a22a0f409bcee06` plus queued-state correction `8d06dba9ab1e5bd27fb7d7cccd718dd5e3b8c471`.

Disposition: **changes required for durable command audit and persistence identity**. This review does not approve worker execution, accepted leases, or restoration of genuinely RUNNING jobs.

The production CT40 GET_JOB route requires a paired operator, an existing durable product session, and exact equality with the handle's originating session. The actual public two-pack/restart/reconnect control passes. Compile admissions remain QUEUED, which truthfully avoids claiming a worker lease.

Independent checks: `PYTHONPATH=qmx-agents/packages/qma-core/src:qmx-agents/packages/qma-daemon/src:qmx-agents/packages/qma-wire/src .venv/bin/python -m pytest -q -p no:cacheprovider qmx-agents/packages/qma-daemon/tests/test_epic73_cancel_wire.py qmx-agents/packages/qma-daemon/tests/test_daemon_process.py` — **11 passed**.

## Held-out failures using actual filesystem persistence

1. Submit an actual persisted Task/JobHandle, cancel it, then issue a new terminal `cancel_from_product_session` command with exact session principal, run, attempt, producer and wire identifiers. The result is Ok and contains the no-op command in `later_commands`. `TaskGraphStateService.job_handle_records()` still contains an empty list; close/recompose loses the command. This service is used by the public CT40 cancel route. The terminal branches update memory and stream without persisting the new handle. Restart therefore loses acknowledged command fencing/audit. The owner independently acknowledges this gap.

2. Directly call the durable projection's `record_job_handle` with the same task/job/owner but a different `originating_product_session_ref`, `logical_run_id` and `attempt_id`. It returns Ok. Close/recompose hydrates the changed session, run and attempt. The in-memory service's origin guard is not a persistence invariant. This is a lower-level API negative control, not a demonstrated remotely reachable exploit. Durable replacement must validate immutable handle identity independently before accepting a snapshot.

The probe reused the real daemon composition and Task Graph compiler from `test_epic73_cancel_wire.py`; no storage methods were mocked and no product source was edited. Concrete findings were sent to root and the owner. Restoration of genuine RUNNING environment/dispatch leases remains outside this bounded candidate and must be reviewed separately when implemented.
# Corrective review `ab201d014888daf1ef5b0bb378c63078f000602a`

**APPROVED for the two bounded JobHandle corrections.** Actual filesystem terminal cancel command audit now appears in the persisted projection and survives close/recompose. Direct durable replacement of session/run/attempt identity returns refusal, and restart retains the original exact identity. Projection validates the typed payload and six immutable identity fields before persistence; terminal no-op branches persist before reporting success. Genuine RUNNING lease restoration/full execution limitations remain unchanged.
Independent public cancel/daemon process/Task Graph state suite passed **23 tests** with nested qma-core/daemon/wire PYTHONPATH; prior standalone actual persistence controls also passed.
