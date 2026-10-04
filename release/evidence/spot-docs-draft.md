# Draft documentation patch: recorded spot backend and governed read

Status: DRAFT, 2026-10-04. This is a reviewed local synthetic infrastructure
candidate, not canonical ratification or live release acceptance. The parent
coordinates the shared daemon startup lane. No canonical docs, CTs, registry
values or gap status are changed by this patch.

## Proposed addition to docs/components/qmf-venue.md

A credential-free spot normalizer exists in `qmf.venue.spot`. It admits explicitly
active, non-contract BASE/QUOTE spot metadata with decimal-string TICK_SIZE
precision and separate amount/cost limits. Binary floats are refused. It uses
no CCXT/Hummingbot runtime and makes no network calls. Only `qmn.venue` consumes
it. This does not establish a CT-18 live spot capability or classify cTrader CFDs
as deliverable spot FX. Other precision modes and fee currencies remain future.

## Proposed addition to docs/components/trading-node.md

`qmn.venue.spot_paper.SpotPaperAccount` owns a local deterministic simulation
ledger. It is not vendor-demo paper, a fourth VenueClientKind, a Book/BMS sizing
implementation or CT-32 evidence. It has no exchange sockets or credentials.
Balances, quote fees, remaining reservations, stable client IDs, FIFO admission
indices/times, snapshot, audit and retained query view commit in one SQLite
transaction. Derived decimals preserve additional digits. Delayed events cannot
fill orders before their admission. FIFO survives restart independently of client
ID spelling. Retries preserve exact payloads; cancel releases reservations once.

The local ownership key is (provider connection, venue, account), excluding node
placement. Native OS locking proves one writer only on one machine/shared
canonical root. It does not prove distributed fencing across servers or roots.
Different accounts have independent policy, fee, budget, ledger and reservation
state. A restarted writer verifies policy/market/account/seed identity and clears
price readiness. Storage failure blocks mutations until reopen/reconciliation.
No remote submission UNKNOWN outcome is fabricated by the local terminal states.

Simulation state format 2 records admission indices/times. Format-1 candidate
state is refused; no unsafe automatic FIFO/time reconstruction is performed.
Preserve any old databases as historical fixtures and use a fresh synthetic
root. The format-1 retained query projection is marked `retained` and contains an
`audit_seq`; it makes no writer-liveness assertion. The query is a QMN-owned
projection, not a new production money contract or CT-13 journal.

## Proposed addition to docs/components/qmf-data.md

`qmn.venue.spot_recorded.RecordedSpotSource` admits synthetic ticks through the
real SourceObservationBoundary and immutable CT-10 replay archive. Complete raw
bid/ask/liquidity/sequence/time provenance is retained. Replay freshly verifies
the receipt, then checks pinned source/venue/market, synthetic license, precision,
raw time and foreign bid against CT-10 before execution. Archive receipt and
observation fingerprints are distinct. Corrections append and cross-world reads
remain refused. Synthetic observations cannot validate trading edge.

Public-source recordings are refused by this producer until the existing CT-15
authority and explicit license are bound. This slice does not change the existing
intake locking modules; the governed-QMB lane owns their platform repair. Historical
paging, live source selection and exchange-specific sequence bridging remain future.

## Proposed addition to docs/components/qma-daemon.md

Normal `python -m qma.daemon` startup installs `qmn.spot.paper.query@1` when the
OS-owned operator-config.json contains a `spot_paper_queries` instance mapping.
The existing enabled `trading-readonly:positions` contribution provides the read
adapter. Each binding pins package/config revision, provider connection, venue,
account, policy reference and an absolute simulation SQLite path. The daemon
opens the retained QMN projection with mode=ro and query_only, never imports QMN
execution, constructs a writer or obtains an order callback.

The existing paired CT-40 open_product_session, grant_product_session and
start_mission route is used. The descriptor is published into the daemon's host
operation roster only when configured. An enabled pack is not a grant. Existing
ProductSessionService dispatch checks hashes, contribution/instance, grant scope,
expiry/revocation and accepted-work binding. A session account_scope token pins
the full host scope/policy/path, so changing the host binding while accidentally
reusing a revision cannot retarget an existing session/grant. Raw payload keys
must exactly match account/provider/venue before canonical validation; an extra
path or operation field cannot be dropped into a successful query. Restart
restores the existing session/grants. There is no new memory/checkpoint namespace.

No submit/cancel/transfer tool is installed for models, including paper. The
native agent tool manifest remains unchanged. There is no new listener, CLI,
MCP service or UI. The supported read doors are library/in-process and the
existing paired QMA wire. The default bundled trading-readonly pack has one
instance; a binding selects one account for that instance, not an unbounded
account browser. Multiple QMN accounts remain independent backend objects.

An explicit `host_retry_attempt_ceiling` in the same OS-owned config is admitted
through the existing governed registry when spot bindings are installed. No
ceiling/default is invented. Missing ceiling leaves existing read admission
fail-closed. An example operator config fragment is:

```json
{
  "host_retry_attempt_ceiling": 1,
  "spot_paper_queries": {
    "pack:trading-readonly": {
      "config_revision": 7,
      "package_version": "0.1.0",
      "provider_connection_id": "conn:recorded",
      "venue_id": "recorded:crypto",
      "account_id": "a",
      "policy_ref": "policy:a:1000",
      "state_db_path": "C:/operator-owned/paper/account-key/paper.sqlite"
    }
  }
}
```

Those counts/revisions are fixture/operator choices, not canonical defaults.
Keep the existing research_corpus_root_path and other independently configured
host keys. Client requests cannot supply paths, configuration or host ceilings.

## Proposed addition to docs/lenses/ops/runbook.md

Use the repository's declared Python 3.14 dependencies, with source paths pinned
to the reviewed checkout. `tools/spot-paper-check.ps1` checks 13 Python files,
runs focused tests and separate seed/verify processes from the QMN-owned
`qmn/examples/spot_paper_journey.py`. Its EvidenceRoot must be outside the Git
worktree because the existing research-corpus startup policy rejects Git roots.
Keep JSON reports, archive/observation references and audit sequences. These are
simulation evidence, not trading-edge or live readiness evidence.

Stop/reopen the writer with identical state identity and inspect retained balances,
orders and reservations before a fresh same-feed snapshot. Do not delete lock
files to force ownership. Abrupt process exit releases the OS lock but is not
power-loss certification. Do not reuse format-1 state under format 2. The daemon
reads last committed retained state even when the QMN writer is stopped; READY
on that retained view must not be presented as current feed/writer liveness.

## Proposed addition to docs/lenses/testing/fixtures-and-scenarios.md

Focused fixtures cover precision/minimum notional, quote fees, reservations,
partial/full fills, cancel/retry, delayed pre-admission ticks, restart FIFO,
per-account policy/state isolation, same-root writer exclusion, storage rollback,
CT-10 readback consistency and granted read scope. Real paired WebSocket tests
exercise operator opening/granting, no-grant/retarget/extra-key/execution denials,
revocation, restart, changed host binding, and a separate normal daemon module
entrypoint restoring and querying the actual retained ledger. No credentials,
live exchange, paid provider or provisioning is used.

## Proposed addition to docs/architecture/overview.md

Reuse COMP-QMF-VENUE for metadata, COMP-QMF-DATA for CT-10, COMP-QMN for the
simulation ledger/query projection and COMP-QMA-DAEMON for governed read dispatch.
No new COMP/CT or global node infrastructure is introduced. QML strategy meaning,
QMB compute/CT-32 and Book/BMS risk ownership remain unchanged. Existing intake
locking remains owned by the parallel governed-QMB lane. No live spot capability,
deliverable spot FX, distributed fencing, venue UNKNOWN reconciliation, unattended
paper week or release gate is certified by this candidate.
