# QMN domain identity and admission evidence

Candidate: `release/rc-2026-10-01` in the local Ubuntu workspace. This evidence
covers the bounded repairs to audit findings QM 01–05. It does not establish a
deployed incident, a production composition path, or live trading exposure.

## Repairs and remaining limits

- **QM 01:** Book-minted place-order parameters now use identity format 2 and
  include the admitted instrument and buy/sell side. The venue encoder derives
  side from that identity and refuses a contradictory side. The live client
  checks command venue against its pinned venue and, when a session account is
  bound, checks account id and role against that session. Historical format-1
  parameter identity remains readable. The supplied native symbol id and
  cTrader account id still have no pinned mapping object tying them to the
  command's instrument/account; this part of the audit finding remains open.
- **QM 02:** Before a place-order command is minted, venue, account id, and role
  must exactly match the immutable target on the admitted intent. A mismatch
  refuses before submission. This checks the node-owned context against the
  admitted target; it does not establish an end-to-end production caller.
- **QM 03:** Snapshot freshness now refuses a decision time earlier than the
  snapshot frontier. Equal, forward-within-bound, and stale-after-bound controls
  remain in the existing test.
- **QM 04:** Snapshot mint now refuses an SQS baseline whose environment
  differs from the snapshot environment, or whose venue differs from its
  instrument venue. There is no snapshot-level expected consumer binding, so
  that additional comparison remains unavailable at this factory boundary.
- **QM 05:** The Book door no longer defaults absent position state to false.
  Hosted dispatch requires a binding virtual ledger, checks open positions by
  instrument, and prevents duplicate same-instrument entries within one
  dispatch batch. The current ledger has no decision-frontier stamp or durable
  pending-order reservation lifecycle. Admission is therefore not safe to
  describe as fully frontier-bound across concurrent or subsequent dispatches;
  QM 05 remains open for those cases.

The integrated proof is still open: no production Book/KSA caller of
`consume_signal_snapshot` was established. `SeatDispatchReceipt.hops` still
describes the declared route and does not prove BMS capital, SQS, KSA, or
position enforcement ran. Replay still does not reapply a complete admission
transcript. Do not use this record to claim a complete recorded-frontier through
order-path proof.

The trading node remains the ratified Ubuntu/systemd node. Windows placement is
not established by this work; no Windows service or installed Windows
acceptance was run. No broker, provider, credential, or trading operation was
performed.

## Verification

Baseline desired-contract checks were run before the MIS repairs with:

```text
uv run --no-sync pytest -q qmn/tests/test_qmn_mis_signal_snapshot.py -k 'environment_key or freshness_bound'
```

The demo SQS baseline was accepted by a live snapshot and a future snapshot
frontier was accepted at decision time. Result: **2 failed, 1 passed**. Those
are the intended contract failures; both pass after the repair.

Final targeted domain command:

```text
uv run --no-sync pytest -q qmn/tests/test_qmn_mis_signal_snapshot.py qmn/tests/test_qmn_order_door.py qmn/tests/test_qmn_seat_tunnel.py qmn/tests/test_qmn_runtime_risk_gate.py qmn/tests/test_qmn_encode.py packages/qmf-venue/tests/test_commands_ct19.py packages/qmf-venue/tests/test_encode_ct19.py
```

Result: **150 passed**. Static checks on the changed QMN and qmf-venue source
and test files: Ruff passed; Pyright reported 0 errors, 0 warnings, and 0
informations.

The broader command `uv run --no-sync pytest -q qmn/tests
packages/qmf-venue/tests` reached **1,412 passed, 7 skipped, 1 failed**. Its
single failure is the unrelated documentation assertion
`test_qmn_seat_containment_limit.py::test_release_and_security_docs_state_the_v1_limit_honestly`:
the shared modified corpus is missing ten GAP-0054 phrases/mentions. The exact
missing literals were sent to the docs owner for reconciliation.
