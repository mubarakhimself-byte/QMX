# Independent review: bounded recorded spot integration

Reviewed candidate `6126874409ab77561c03a1fb8df557e4f57b54ae`, base
`ffb7590bbda1ec8d5dc126b9fdc3205c888dffac`, on 2026-10-04 in an independent
clone/branch. The original checkout and branch are preserved. No UI, push,
protected merge, exchange credentials, actual orders, transfers, live exchange
calls or provisioning were used. Final commit and rerun results are delivered
in `final-validation.json` outside the checkout, avoiding a self-referential SHA.

## Findings and bounded fixes

1. **High: derived reservation precision was treated as foreign input.** A valid
   amount/price/fee product can exceed the foreign decimal input's 28-digit limit.
   A second submit or cancellation then raised rather than returning a governed
   result. Retained derived values now use the stored-value parser. A regression
   covers the second submit and cancellation after a high-precision fee.
2. **High: restart changed FIFO execution order.** Sorted JSON keys reordered
   the order dictionary by client ID. Persisted admission ordinals now determine
   both execution and query order; the restart test uses reversed lexical IDs.
3. **High: late replay could fill before admission.** An event whose timestamp
   preceded the submit time could execute a later order. Persisted admission time
   now bounds eligibility. The original three failures were reproduced against
   original source in `spot-independent-red.txt` before fixes.
4. **High: CT10 identity validation did not establish replay value consistency.**
   Replay trusted a record's raw tick separately from its verified observation.
   It now checks synthetic provenance/license, event/receipt times, bid context,
   market/adapter and decimal scale against the retained CT10 observation. A real
   archived observation with inconsistent raw event time is refused; a consistent
   archive still replays successfully. This is local synthetic CT10 evidence only.
5. **High integration gap: no normal governed daemon path.** The original query
   was reachable through the example's library callback only. Startup now loads
   optional OS-owned `spot_paper_queries` bindings for an enabled
   `trading-readonly:positions` pack instance, advertises the operation descriptor,
   and dispatches `qmn.spot.paper.query@1` through existing paired CT40
   `start_mission`, ProductSession grants and host work admission. The daemon reads
   an atomic retained SQLite projection in `mode=ro`; it imports no QMN runtime,
   writer or execution tool. Payloads cannot supply a file path or retarget scope.
   Existing session account scope pins account, policy and path independently of
   config revision. Missing retry authority remains fail-closed; an explicitly
   configured host ceiling uses the existing governed variable registry.
6. **Boundary failure: the tools directory imported QMN.** Moved the journey into
   `qmn/examples`. This resolves the original full-QMN dependency-boundary failure.
7. **Own fix review: startup error cleanup deadlocked.** The new configuration
   refusal path initially reacquired the composition gate. Cleanup now releases
   resources without reacquiring an already held gate. A real module subprocess
   test requires prompt exit with a typed refusal for an invalid configured pack.

State schema version 2 persists causal/FIFO fields and atomically writes snapshot,
audit and read projection. Version 1 is refused rather than guessing historical
admission order/times. Preserve old evidence and use a fresh synthetic state root.

## Authorization, account isolation and reachability evidence

`test_spot_daemon_binding.py` pairs through the real HTTP listener, authenticates
the WebSocket and invokes the actual RPC handlers. It proves missing grants,
execution-operation requests, revocation, wrong provider/venue/account, added
payload paths, bad retained policy/account and missing storage all refuse. A
module-entrypoint subprocess (`python -m qma.daemon`) restores an existing paired
session/grant and reads persisted state over the authenticated wire. Host retarget
with the same revision refuses reuse of the prior ProductSession. Proof artifacts
in `spot-daemon-auth-proof.json` contain outcomes, not pairing secrets.

Account A accepts the same synthetic order that account B refuses under its lower
cap. Distinct ledger, fee, reservation and policy state survive restart; each
query opens its own read connection and parses fresh data. The paired read has no
model/provider call or memory write. Native OS lock tests cover competing writers
in separate local processes, including release and reacquisition. This does not
establish fencing on different machines or across different canonical roots.

The synthetic writer remains operator infrastructure exposed through the QMN
Python API and its QMN example. This change does not invent a supervisor trading
engine or give any agent execution tools. The normal daemon path is the governed
read of that writer's retained state. No current writer/feed liveness is inferred
from a retained view. One account is selected per enabled pack instance; no UI or
account browser is added. Recorded local terminal outcomes do not prove remote
exchange UNKNOWN reconciliation. Deliverable spot FX remains future capability;
cTrader CFDs are not relabeled.

## Verification and release limit

* Original candidate focused claim reproduced: **26 passed**.
* Reviewed focused ledger, metadata, recorded source, ownership and daemon binding:
  **35 passed**; Ruff check/format and strict Pyright on 13 files pass.
* Explicit selected roster: **549 passed**, covering all qmf-venue tests,
  QMN venue selection/order/unknown and daemon grant/reachability/money-denial/
  library-query tests. The original 549 roster was not preserved, so the exact
  reconstructed roster is recorded in acceptance rather than assumed equivalent.
* Additional daemon process/session/retry/deployment/pack regression: **91 passed**.
* Separate seed/verify processes pass the retained two-account QMN journey.
* Full QMN: original **1,066 passed, 40 failed, 23 skipped**; reviewed
  **1,070 passed, 39 failed, 23 skipped**. Exact comparison has no new failures and
  resolves only the QMN import boundary failure. The 39 inherited failures include
  configured runtime/admission/frontier/readiness tests, older qmf-venue import
  boundaries and a Windows process-termination test. They are listed individually
  in `spot-full-qmn-comparison.json`. Full release acceptance remains **red**.

Missing official dependencies were installed at their repository pins into an
isolated review environment: prometheus-client 0.26.0, cryptography 50.0.1,
protobuf 7.36.0 and optuna 4.9.0. No test was disabled to bypass collection.
Existing test-defined skips are counted separately. The initial missing-dependency
collection blocker is resolved; the remaining failures are actual inherited tests.

The sole shared daemon integration file changed is
`qmx-agents/packages/qma-daemon/src/qma/daemon/process.py`, reported before edits
for parent coordination with governed QMB lane 01a1064d. It changes optional
startup binding, read operation/session/grant routing and startup cleanup. No QMB
contract, QMF intake locking, composition or lane-owned file was edited. Parent
must combine this local commit with that lane and rerun integration before release.

Canonical documentation and gap status are unchanged. `spot-docs-draft.patch`
is DRAFT and passes `git apply --check`. No CT32 edge proof, Book/BMS sizing,
distributed fencing, week-long soak, live spot capability, exchange account or
provisioning acceptance is claimed.
