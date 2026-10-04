# Draft documentation patch: recorded spot slice

Status: DRAFT, 2026-10-04. Review with the parent architecture/startup lane before
applying to canonical docs. Existing decisions, contracts, gap status and registry
values are not silently rewritten. No new COMP/CT is proposed by this local slice.

## Proposed addition to docs/components/qmf-venue.md

> A credential-free recorded spot metadata normalizer exists in `qmf.venue.spot`.
> It accepts CCXT-style explicit spot/non-contract/active BASE/QUOTE markets only
> with `TICK_SIZE` decimal-string metadata and separate amount/cost limits. It
> performs no network I/O and imports no CCXT/Hummingbot runtime. This does not
> extend the cTrader adapter's capabilities or establish a live spot declaration.
> Only `qmn.venue` consumes this module. Other precision modes, fee currencies,
> derivatives and unverified provider classification fail closed.

CT-18 follow-up: add a separately versioned spot declaration and measured profile
before live decode/command support. Per-market base/quote, settlement/custody class,
precisionMode, order subset and minimum/maximum limits must be explicit. Do not
cast an exchange market dictionary as a ratified CT-18 profile.

## Proposed addition to docs/components/trading-node.md

> `qmn.venue.spot_paper.SpotPaperAccount` is a local recorded-data infrastructure
> harness, not vendor-demo paper or a fourth production VenueClientKind. It has
> no sockets, credentials or live-order transport. It serializes account mutations
> under a process mutex and holds a native OS file lock on a directory keyed by
> `(provider_connection_id, venue_id, account_id)`. Node placement is excluded
> from that key. A second node targeting the same account/root is refused.
> Different accounts may have different explicit policy references and open
> notional/freshness/fee/admission limits; a Book is not hardcoded as their owner.
> This harness does not replace production Book/BMS sizing or certify CT-23 risk.
> SQLite snapshot plus simulation audit rows commit atomically. Reopening verifies
> policy/market/account/seed identity and invalidates price readiness. UNKNOWN
> real exchange effects remain outside the simulated terminal states.

Configuration additions for a future reviewed roster contract (not implemented as
operator-config keys): `provider_connection_id`, stable `account_id`, `node_id`,
`account_policy_ref`, explicit `asset_class`/settlement capabilities and an
authoritative writer assignment with fencing. Local simulation config currently
uses `AccountScope` and `PaperPolicy` values supplied by the host/harness. Shared
roots/local file locks do not establish cross-server fencing, failover or safe
independent-root ownership. Never enable live capabilities on that assumption.

CT-19/20 follow-up: define and verify limit/market amount units, client ID mapping,
fees in arbitrary assets, balance reservations, partial terminal events,
cancel/fill races, UNKNOWN after timeout/not-found and authoritative reconciliation.
Current local simulation does not claim those remote semantics. CT-21 stays
secret-reference-only; browser/manual secret entry remains user-controlled.

## Proposed addition to docs/components/qmf-data.md

> `qmn.venue.spot_recorded.RecordedSpotSource` routes recorded spot ticks through
> the real `SourceObservationBoundary` into replay-world immutable raw archives.
> Foreign prices are exact at the declared price scale; the complete input tick
> is retained in market-data provenance. Origin, writer/sequence, source/native ID,
> revision and correction linkage are explicit. The tested producer admits synthetic recordings only. Synthetic observations carry
> `synthetic-infrastructure-only` provenance and do not validate trading edge.
> Archive receipt and observation fingerprints remain distinct. Fresh QMF reads
> verify retained identity; cross-world reads remain refused.

CT-15/GAP-0060 follow-up: this recorded adapter does not resolve canonical live
source selection, durable multi-provider download key coordination, historical
paging/backfill or exchange-specific snapshot/diff bridging. The baseline Windows
`IntakeAuthority` imports `fcntl`; the separate QMB lane owns its cross-platform
repair. This slice does not alter that shared authority or certify it. Public
recordings are refused until the existing authority and source license are bound. Source-native idempotency beyond replaying
the exact retained observation needs the existing authority with a supported
platform binding, rather than a second key database in this adapter.

## Proposed addition to QMA API/operation documentation

> The explicit host installation seam `SpotQueryDoor` publishes
> `qmn.spot.paper.query@1` (owner COMP-QMN, effect read, placement node), requiring
> `provider_connection_id`, `venue_id` and `account_id`. The host binds a concrete callback,
> contribution/package version, instance/config revision and exact account scope.
> Invocation uses existing `ProductSessionService.dispatch_public_call`, including
> canonical input hashing and grant validation/revocation. Extra keys or account
> retargeting refuse before callback. It installs no submit/cancel/transfer tool,
> no venue credentials or new service. The supported door is library-only. Global
> catalog/startup wiring belongs with the parent composition lane; this is not
> HTTP/MCP acceptance or a native agent tool binding.

Mini-apps and agents can eventually consume this descriptor through the existing
host transport. Enabling a pack is not a grant. QMA-paper execution remains denied,
including simulated order intents that would dispatch a money-path action. QML
strategy semantics and QMB compute/CT-32 ownership are unchanged. Analytics read
simulation balances/orders/fees and actual QMF observation references; they must
display simulation status and must not manufacture CT-32 results from those rows.

## Proposed runbook and acceptance entries

Run the new spot tests and `tools/spot_paper_journey.py` using Python 3.14 with the
repository's existing declared dependencies. Source paths must select this checkout,
not an editable install pointing elsewhere. The journey accepts only a local output
directory and synthetic fixture phases; it performs no provider login or network
request. Retain its JSON report and source/observation/archive references. Do not
publish credentials in logs. The SQLite audit is simulation state, not CT-13 or
operator log substitution.

For restart: stop the account writer, reopen the same canonical root/account with
the same market/seed/policy identity, inspect balances/reservations/open orders,
cancel or retain them explicitly, and provide a fresh same-feed recorded snapshot
before admitting new intents. Do not delete a lock file to force takeover; the OS
releases this harness's lock on process exit. For storage failure, the writer
blocks new mutations until closed/reopened and reconciled.

Acceptance statuses: local exact arithmetic, reservations, partial fill/cancel/retry,
two account/policy isolation, same-root writer exclusion, restart and governed read
are the implemented test targets. Real exchange integration, Book/BMS sizing,
deliverable spot FX, global rate/IP limits, distributed fencing, live UNKNOWN
reconciliation, normal-start UI/API/agent binding, power-loss durability, unattended
paper week and release gates remain unsupported/unverified. Do not rename passing
fixture tests as full crypto readiness or a completed paper soak.
