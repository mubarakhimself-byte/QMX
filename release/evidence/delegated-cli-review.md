# Independent Sol review — delegated QMA/QMB CLI identifiers

Candidates `613c6a748bc3d6a7de897e7b3e129f4e7b55f4c8` and `b32df4756305fe47696ac89e19dc276dba2ebe36`. **Changes required in actual transport serialization; no execution approval.**

The QMB parser enforces exact keys/types, duplicate JSON refusal, fixed replay semantics, matching seven dedicated environment identifiers, and no caller-selected runtime roots/policy. Independent mismatch controls for every identifier refuse; bool attempt, integer boolean semantic flags, foreign world, policy and raw-root injection refuse. Five parser/actual CLI tests pass. Valid delegated CLI currently reports typed unavailable operator_runtime, preserving no legacy fallback; it does not execute economics.

Actual BacktestingService→CliQmbDoorTransport spawn was exercised with the existing local subprocess fixture and traced environment construction without substituting results. The core-minted invocation contains attempt_id integer1, but its actual environment has no QMA_QMB_ATTEMPT_ID. `_door_env` passes that integer through `_payload_str`, which accepts strings only. Therefore the new strict QMB parser refuses a valid real delegated route (or sees unrelated inherited ambient attempt). Serialize the validated positive integer deliberately and clear/set all dedicated envelope fields without inheriting stale identifiers. Add a production-route captured-env regression, not only manually built parser environments. Findings sent to root/execution.

Registered ExperimentSpec resolution derives split data_ref in the service; this is distinct from parser authenticity and future operator-root resolution. The standalone captured service probe used the existing optional no-experiment-registry fixture to isolate the serialization fault, so it does not prove a registered CT47 chain. QMA never imports QMB; the transport carries identifiers and QMB owns runtime resolution. No product edits or provider calls.

# Corrective transport approval — `2a5a4686c906619c8d60510b5bbdea2c18cfc2ad`

Independent actual registered ExperimentSpec→BacktestingService→CliQmbDoorTransport→local child receipt positive now passes. The core-minted positive integer attempt is deliberately serialized into its dedicated environment identifier. A held-out capture supplies stale ambient values for all seven dedicated identifiers; every spawned value exactly matches the current invocation, including registered data_ref as split identity. Seven malformed attempts (missing/None, bool True/False, zero, negative, string, float) refuse before Popen. The transport remains an identifier carrier; QMB resolves its runtime, and QMA imports no QMB.

Reused independent parser controls refuse mismatched job/attempt/spec/evidence/split/environment/occupancy identifiers and bool/world/policy/raw-root injection. Focused transport+parser tests pass **15**, backtesting-door tests **8**. Held-out `/tmp/review_cli_corrected.py` invokes the actual registered service fixture and real subprocess, capturing the environment without substituting execution results; `/tmp/review_cli_controls.py` repeats strict envelope negatives.

This approves the bounded transport correction with the prior b32/613 parser contract. It does not approve the concurrently developed operator runtime, actual replay economics or complete CLI execution. No product edits.
