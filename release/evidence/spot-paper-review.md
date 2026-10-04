# Spot paper local review

Self-review of the isolated candidate, not independent certification. All changes
are additions; no shared composition/startup, data locking, provider-session, QMB,
QML, registry, UI or existing cTrader file is modified.

Findings resolved during review:

* QMA execution tools would contradict the existing paper-inclusive money-path
  denial. The installed seam is read-only and dispatches via ProductSessionService.
  Submit/cancel remain in the QMN local infrastructure harness, never model tools.
* A node-qualified ownership key could duplicate the same account on another
  placement. The lock key excludes node_id and includes provider/venue/account;
  native OS locks also release after abrupt process exit. Cross-server fencing
  remains unsupported, with no live client constructible.
* Price readiness could survive a restart. Reopen now verifies state/audit identity,
  reconciles remaining reservations and resets readiness before any new intent.
* Binary float conversion and ambient Decimal precision could corrupt spot costs.
  Foreign input is bounded decimal text; arithmetic runs in an explicit high
  precision context. Derived fee/reservation values retain their additional digits.
* A snapshot write without an audit write could imply successful execution.
  Both commit in one SQLite transaction; injected audit failure rolls back the
  reservation and blocks further mutations until explicit reopen.
* Filling each resting order with the whole tick's liquidity would duplicate
  volume. All orders share one recorded FIFO quantity budget per tick.
* Provider/account alone omitted venue from the governed read scope. All three
  identifiers are now required, host-pinned and checked before dispatch callback.
* Executing a copied raw tick would skip fresh evidence verification. The journey
  now calls RecordedSpotSource.replay_into over actual freshly read CT-10 receipts.
* Public-source intake without CT-15 uniqueness/license authority would create an
  unproven producer. This bounded archive producer admits synthetic recordings
  only and refuses public recordings until the existing authority/license is bound.
  The separate startup lane owns the inherited Windows lock repair.

Remaining limits: non-production fixture execution, limit orders only, quote fees,
TICK_SIZE only, no portfolio/equity/Book sizing, no venue fills/status reconciliation,
no CT-18 measured profile, no distributed fencing, no direct QMA money authority,
no normal-start HTTP/MCP/mini-app binding and no live/soak/edge certification.
Simulation audit is not a CT-13 journal or operator-log substitute. The original
replay world and canonical registry meanings are retained; no gap is closed here.
