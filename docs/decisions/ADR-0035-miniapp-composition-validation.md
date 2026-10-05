---
id: ADR-0035
title: MA03 panel composition validation ownership
status: draft
type: adr
generated: 2026-10-06
verified: 2026-10-06
stale_after: 30d
depends_on: [COMP-QMA-CORE, COMP-QMA-WIRE, COMP-QMA-DAEMON]
decisions: [DEC-0304, DEC-0305, DEC-0335, DEC-0421, DEC-0429, DEC-0440, DEC-0499, DEC-0506]
sources: [docs/components/qma-core.md, docs/components/qma-wire.md, docs/components/qma-daemon.md, docs/contracts/ct-40-qma-wire-envelope.yaml, docs/decisions/ADR-0034-miniapp-candidate-persistence.md]
---
# MA03 panel composition validation ownership

Verdict: reuse COMP-QMA-CORE, COMP-QMA-WIRE and COMP-QMA-DAEMON. The operator
explicitly delegated backend MA03, including a named contract extension.
Independent parent review and corpus ratification remain separate.

**MA03 named amendment** extends ADR-0034's app_candidate_state event family from
app_candidate.saved to app_candidate.* (saved/validated currently consumed),
preserving journal_seq ordering, equal-instant tie break, knowledge-time semantics
and the existing SQLite class. app_candidate_validation is a child projection on
the same sole writer, never a sixth SQLite class, separate database or definition
store slot. Actual immutable byte artifacts and verified journal receipts remain
authoritative. No existing DEC is superseded or newly ratified here.

Wire owns versioned composition/component props, argument/result/read-state schemas
and an adapter to its existing PackUiView. The existing schema engine gains
schema-valued additionalProperties validation for element/binding maps. Daemon
selects trusted validator identity, explicit bounded local host configuration,
scoped live declared READ adapters and immutable proofs. Core retains MA02 version
and operation identity ownership. Descriptor/grant operation mapping is shared
with the existing ProductSession grant path; validation cannot mint authority.

The ten actual documented SDK components and flat root/elements model are adopted.
Demo-generated samples and proposed 60/6 limits are excluded. No second renderer,
plugin-supplied validator, arbitrary import, URL/provider broker or UI wiring is
created. The output-state schema is a presentation contract; existing operation
owners retain actual data readiness, reference/run semantics and invocation gates.

Proofs pin exact MA02 version/content/composition/catalog/dependencies/parameters,
owner/session/context and host validator. Recovery replays successful proof against
archived contracts before rebuilding rows. Current reads reject stale evidence.
MA04 must atomically consume/recheck it before publication; MA03 performs no apply.

See [the exact release contract](../../release/MA03-COMPOSITION-CONTRACT.md) and
[examples](../../release/MA03-COMPOSITION-EXAMPLES.json) for DTOs, adapter mapping,
local configuration, bounds, replay semantics and explicit acceptance limits.
