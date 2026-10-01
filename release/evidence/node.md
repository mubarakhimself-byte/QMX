# QMN domain identity and admission evidence

Candidate: `release/rc-2026-10-01` in the local Ubuntu workspace. This evidence
covers the bounded repairs to audit findings QM 01–05. It does not establish a
deployed incident, a production composition path, or live trading exposure.

## Repairs and remaining limits

- **QM 01:** Book-minted place-order parameters include the admitted instrument,
  buy/sell side, and (when minted through the Book door) native account/symbol
  ids plus the immutable native-map fingerprint. The venue encoder derives side
  from identity, refuses malformed explicit sides, and refuses native id
  substitutions. The live client resolves the exact account/role/venue/instrument
  row from the pinned native map. Historical format-1 parameter identity remains
  readable. The runtime map must still be loaded from the approved registry
  configuration at the product composition root before it can establish
  production identity.
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
  Hosted dispatch requires the exact CT-28 `BookBindingRecord`, resolves its
  fingerprint as the binding epoch, and checks it against the admitted seat,
  BMS, account, venue, virtual ledger, and native map. It rejects ledger records
  newer than the supplied decision frontier, checks open positions, and reserves
  an instrument across later dispatch calls using the same ledger. A matching
  attributed fill clears that reservation; a typed accepted/UNKNOWN result keeps
  it; typed rejected/denied outcomes release it. The ledger now journals
  admission, submission outcome, and attributed-fill reservation transitions
  before updating reservation state, and fails closed after an append refusal or
  uncertain acknowledgment. Recovery rejects incomplete streams and requires a
  supplied committed high-water matching the recovered prefix. However, the
  QMN `QmfEntryReservationJournal` adapter now uses QMF's resumed CT-13 writer
  and checked reader to append and recover the typed transition stream. The
  production composition still has not wired this adapter to an actual Book/KSA
  caller, so QM 05 remains open across product composition and end-to-end
  restart recovery.

The shipped `python -m qmn.host.supervise` entrypoint now validates configured
root/state directories and a loopback evidence bind, serves `/healthz` while
alive, and reports `/readiness` as unavailable with `stand-down-alive` while no
venue adapter is composed. Before `READY=1`, it appends a process-start control
event to a local QMF CT-13 journal; startup refuses on storage failure. A
subprocess restart test reads back both starts from that checked journal. It
supports systemd notify/watchdog and OS stop. This establishes a provider-free
supervised process lifecycle, not a completed boot ceremony, trading readiness,
or the full QMN decision composition.

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

Latest targeted reservation and identity command:

```text
uv run --no-sync pytest -q qmn/tests/test_qmn_seat_tunnel.py qmn/tests/test_qmn_order.py qmn/tests/test_qmn_encode.py packages/qmf-venue/tests/test_commands_ct19.py packages/qmf-venue/tests/test_encode_ct19.py
```

The command reports **133 passed**. A separate checked-journal adapter and
supervised-process verification command reports **47 passed** across the
adapter, seat tunnel, order path, and supervisor process tests. Ruff passed and
Pyright reported 0 errors, 0 warnings, and 0 informations on those scoped files.

The broader command `uv run --no-sync pytest -q qmn/tests
packages/qmf-venue/tests` reached **1,412 passed, 7 skipped, 1 failed**. Its
single failure is the unrelated documentation assertion
`test_qmn_seat_containment_limit.py::test_release_and_security_docs_state_the_v1_limit_honestly`:
the shared modified corpus is missing ten GAP-0054 phrases/mentions. The exact
missing literals were sent to the docs owner for reconciliation.
