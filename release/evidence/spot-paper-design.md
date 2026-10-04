# Spot paper slice: architecture preflight and ownership map

2026-10-04; baseline `ffb7590bbda1ec8d5dc126b9fdc3205c888dffac`.
This is an explicitly authorized local implementation candidate, not a ratified
live-venue architecture or proof of platform readiness.

## Inventory and reuse verdict

Read the canonical Desktop/QMX backend-assurance BACKLOG and task-7
qmx-backend-assessment.md; docs/constitution.md, architecture/dependencies.yaml,
architecture/stack.md, components/qmf-venue.md, qmb.md, qml.md,
trading-node.md; CT-10/15/18-21; registry/variables.yaml; gap-report.md;
_docwork/workbench-increment-brief.md and the CONNECT architecture spine.

* Reuse COMP-QMF-VENUE for pure spot market metadata and normalization. Only
  qmn.venue imports it. No CCXT dependency or foreign object enters qmf-core.
* Reuse COMP-QMF-DATA for immutable CT-10 replay observations via its real
  SourceObservationBoundary and EvidenceStore. Synthetic provenance is explicit.
* Reuse COMP-QMN for a bounded recorded-data execution harness. It owns balances,
  reservations, deterministic fills, fees, cancellation, reconciliation and an
  account-scoped local simulation ledger. This is infrastructure testing, not
  Book/BMS risk certification, CT-32 trading-edge evidence, vendor demo paper,
  or a fourth production VenueClientKind. Live selection stays fail-closed.
* Reuse COMP-QMA-DAEMON and existing ProductSessionService/grant dispatch for
  read-only queries with a host-injected callback. No import of QMN/QMB/venue,
  no credentials, no QMA-paper order tools and no new daemon.
* QML strategy semantics and registry ownership remain unchanged. QMB owns
  governed replay/compute; synthetic fills are not a new backtest governor.

The existing `BindingVirtualLedger` models Book-attributed virtual positions and
frozen-R money semantics; the production CT-19 command/port roster is still the
ratified cTrader/replay/conformance shape. Neither establishes deliverable spot
currency-balance/reservation semantics. This slice therefore adds an explicitly
non-production QMN simulation ledger, rather than changing those public contracts.
The strongest objection is a parallel matcher becoming a second production truth:
the boundary prevents this by exposing no live client, no fourth client selection,
no QMA execution tool and no CT-32 edge claims. The CONNECT local-matcher dead list
still governs vendor-demo paper; L20's controlled synthetic infrastructure testing
and this direct operator request authorize this fixture, not its promotion into a
production money path.

## Existing paths and cTrader assumptions

qmf.venue.{connection,ctrader,encode} plus qmn.venue.{port,live,reconnect} own
the current cTrader connection and CT-19/20 path. VenueClientKind has only
ctrader/replay/conformance; world=simulated is reserved-unusable. Demo paper
uses the vendor host in world=live. qmn.data.intake.CANONICAL_LIVE_SOURCE is
ctrader (GAP-0060 remains deferred). No existing CCXT connector was found.
QMA worker reachability already rejects ccxt and venue credentials.

The CONNECT no-CCXT/no-Hummingbot decision constrains that cTrader increment.
This user-authorized slice implements original local mechanisms without importing
either donor runtime, changing that client, or declaring a live exchange supported.

## Wider platform contract recommendation

ProviderConnectionId identifies a provider/config/credential reference independently
of AccountId; NodeId names placement, not the account. AccountPolicyRef is explicit
and per-account: a Book may supply policy but is not universally required by this
adapter harness. Account scope is (provider connection, venue, account), across node
placements. One writer may own it at a time. The local file lock proves this only
for a shared canonical root on one machine; independent servers/roots still need
an operator-owned authoritative assignment and fencing before any live capability.
Do not equate two isolated local simulated nodes with distributed lease acceptance.

Spot crypto only is executable here. Deliverable spot FX needs separately verified
provider capabilities, currency settlement, custody, jurisdiction/account classification,
minimum/precision rules and policy. cTrader CFD exposure is not deliverable spot FX.

## Bounded behavior

Explicit CCXT-style TICK_SIZE metadata, base/quote symbols, spot-only classification,
decimal strings (binary floats refused), minimum amount/cost and maximum order cost.
Quote-currency fees only. Recorded snapshot/diff sequences detect gaps, stale and
out-of-order data; reconnect invalidates readiness until an explicit same-feed snapshot.
This generic recorded sequence is not an exchange-specific Binance U/u bridge.
Orders are limit-only, fills use recorded bid/ask and one shared quantity budget per
tick. No leverage/shorting/transfers/network/order submission is available.
Retries use stable client IDs and exact payloads; changed retries refuse. Restart
restores transactions and reservations, verifies policy/market/account identity,
and invalidates prices. A weighted local admission budget models throttling; it is
not acceptance of an exchange's IP/endpoint/account rate-limit implementation.

## Donor mechanisms and source awareness

Research lane reports CCXT 4.5.85 (2026-10-01), Hummingbot v2.17.0
(2026-09-22), source SHA 9af100d6822da7d2d0291a906c730ef172284ee2.
CCXT source pin: cf4d2b22fcd77be395ee73cb79ef47690c099986.
Version claims are research inputs, not installed dependencies. CCXT is MIT licensed;
Hummingbot core is Apache-2.0. No donor code is copied or vendored. Mechanisms borrowed:
metadata separates precision from limits; reuse one limiter per owned session;
track fills/reservations independently from order terminal state; uncertain submission
is UNKNOWN/reconciliation, never timeout-as-rejection. Hummingbot direct strategy
buy/sell is not adopted. Existing QMN remains deterministic execution owner.

Pinned official mechanism references:
https://github.com/ccxt/ccxt/blob/cf4d2b22fcd77be395ee73cb79ef47690c099986/python/ccxt/pro/binance.py
(spot U/u continuity differs from derivative pu) and
https://github.com/ccxt/ccxt/blob/cf4d2b22fcd77be395ee73cb79ef47690c099986/python/ccxt/async_support/base/throttler.py
(instance-local limiter; not a cross-node account/IP budget).

Official references: https://docs.ccxt.com/docs/manual and
https://hummingbot.org/connectors/connectors/architecture/order_lifecycle/.

## Disjoint lane boundary and open decisions

New spot-specific modules/tests and this release evidence only. No UI, global
operation catalog, composition.py/process.py, provider sessions or QMB startup
contracts changed. Normal-start installation of the read bindings is a shared
composition change for the parent to review with the startup lane. Live adapter
implementation, CT-18 measured profiles, CT-19 command mapping, CT-20 UNKNOWN
reconciliation, secrets/onboarding, global node fencing and paper soak remain future
acceptance gates. No canonical gap is silently closed by this candidate.

The tested CT-10 producer admits synthetic infrastructure fixtures only. Public
recordings require binding the existing CT-15 authority and an explicit license,
and are refused here. No second native-key authority is introduced.

## Independent integration follow-up

The independent review supersedes the original additions-only/library-only
reachability limit above. process.py now installs an operator-pinned retained
QMN read through the existing paired CT-40 operation/grant/session machinery.
QMN publishes a format-1 query view atomically with simulation state format 2.
The normal module entrypoint is tested against real pairing and restored grants.
No QMB contract or shared QMF intake lock file is edited. See
spot-independent-review.md and the revised DRAFT docs patch for scope and limits.
