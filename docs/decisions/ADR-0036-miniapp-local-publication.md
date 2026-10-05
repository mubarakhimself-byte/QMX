---
id: ADR-0036
title: MA04 local data-only publication ownership
status: draft
type: adr
generated: 2026-10-06
verified: 2026-10-06
stale_after: 30d
depends_on: [COMP-QMA-CORE, COMP-QMA-WIRE, COMP-QMA-DAEMON]
decisions: [DEC-0304, DEC-0305, DEC-0335, DEC-0421, DEC-0429, DEC-0446, DEC-0452, DEC-0463, DEC-0499]
sources: [docs/components/qma-core.md, docs/components/qma-wire.md, docs/components/qma-daemon.md, docs/contracts/ct-40-qma-wire-envelope.yaml, docs/decisions/ADR-0034-miniapp-candidate-persistence.md, docs/decisions/ADR-0035-miniapp-composition-validation.md]
---
# MA04 local data-only publication ownership

Preflight verdict: reuse COMP-QMA-CORE, COMP-QMA-WIRE and COMP-QMA-DAEMON.
The operator explicitly delegated backend MA04 on accepted MA03, including the
necessary named extension. Independent review and corpus ratification are separate.
No new component, dependency edge, CT number, SDK contribution point or store class.

**MA04 named amendment** adds app_candidate.published to the existing
app_candidate.* journal family. app_candidate_publication is a rebuildable child
projection of app_candidate_state on the same sole SQLite writer. Immutable
artifact bytes and verified journal receipts are authoritative. Existing
plugin_install_records folds the committed installation; existing AtomicRoster
holds its derived miniapp_publication entry and preserves authored graphs.

The trusted bundled dev-factory host owns one data-only toolset contribution,
within the closed existing contribution vocabulary. Its existing PackUiRequest
receives the MA03 view adapter output. This is a daemon-owned data registration,
not a new executable PluginManifest or plugin SDK registration API. Candidate
origin scope remains immutable; the installed host identity is separate. A global
authoring session can compose this app; bound authoring cannot cross host scope.
App-use reads the matching installed scope and cannot edit implementation.

Publication checks current authoring/operator authority, context/candidate/active/
installed-host CAS, host permissions/dependencies and complete MA03 proof replay
plus current catalog, limits, exact dependency pins and complete referenced bytes.
Undo is a new compatible publication; it may select a prior committed candidate
version, but only candidate-head staleness is waived. Other currentness errors
refuse. No operation grant is minted, widened or bypassed; actual use still crosses
the existing current operation/grant/accepted-work gates.

Journal acceptance is the publication barrier. Artifact staging before acceptance
is inert. After acceptance, interrupted SQLite/roster/runtime projections are
reconciled from verified history. Same producer/id and exact admitted intent return
the original receipt, even after replacement or restart; changed intent refuses.
Neither a lost response nor a committed projection failure authorizes a new id.
The authority/roster locks cover validation, CAS and installation. Loader staging
precedes registration mutation; one cleanup per slot preserves LIFO unload.

The v1 DTO explicitly permits null only for initial expected_active_revision.
Publication artifact identity uses MA03's declared finite sorted UTF-8 JSON byte
recipe, including that null; operation keys use existing canonical fp1. This does
not change the general canonical null prohibition. The closed receipt schema and
historical proof/CAS replay reject corrupt or self-consistent malformed envelopes
before rebuilding projections. No DEC is superseded or ratified here.

See [MA04 contract](../../release/MA04-PUBLICATION-CONTRACT.md) and
[versioned examples](../../release/MA04-PUBLICATION-EXAMPLES.json). No ready health,
operation execution, generated code, UI implementation, external publication,
provider, trading, MA05 activity or MA06 delegation policy is inferred.
