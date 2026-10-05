---
id: ADR-0034
title: MA02 data-only Mini App candidate ownership
status: draft
type: adr
generated: 2026-10-05
verified: 2026-10-05
stale_after: 30d
depends_on: [COMP-QMA-CORE, COMP-QMA-WIRE, COMP-QMA-DAEMON]
decisions: [DEC-0305, DEC-0335, DEC-0421, DEC-0429, DEC-0440, DEC-0499, DEC-0506]
sources: [docs/architecture/dependencies.yaml, docs/architecture/stack.md, docs/components/qma-core.md, docs/components/qma-wire.md, docs/components/qma-daemon.md, docs/contracts/ct-40-qma-wire-envelope.yaml, docs/scenarios/SCN-0019-app-use-change-request.md]
---
# MA02 data-only Mini App candidate ownership

Verdict: **reuse COMP-QMA-CORE, COMP-QMA-WIRE and COMP-QMA-DAEMON**.
The operator delegated MA02 backend candidate persistence, including a named
schema/ownership extension. This draft records bounded implementation; parent
independent review and corpus ratification remain separate.

AM-03's editor_draft_head accepts graph-template editor payloads with separate
publication semantics. AD-22 RefinementProposal and ChangeRequest have different
identities and authority. None is an app-candidate DTO. ArtifactStore already
owns complete immutable CT-11 bytes and announcements; SingleSqliteWriter owns
the daemon database; ProductSessionService owns immutable profiles and context
CAS. Reuse these owners, rather than a parallel app database.

**MA02 named amendment** of the closed AD-6 projection/fold lists: add
app_candidate_state on the existing daemon SQLite class, sourced only from
app_candidate.saved, ordered by journal_seq, knowledge-time as_of_recorded_at,
with ascending journal_seq at equal instants. This is not an independent store,
not a definition-store slot 17+, and not a sixth SQLite class. No existing DEC
is superseded. Candidate content and immutable version envelopes live in the
existing artifact_store. Journal acceptance and receipts are authoritative;
SQLite is replaceable derived state only.

Core owns the versioned data-only descriptor vocabulary, wire owns additive
save_app_candidate / get_app_candidate / get_app_candidate_history contracts,
and daemon owns issuance, parent/CAS integrity, receipts and restart folding.
Current operator-owned authoring psess at its expected context_revision may
save. App-use reads only candidates tied to its immutable instance. Originating
authoring session, edit session, operator identity and optional target instance
are daemon-recorded facts; clients cannot supply them as version authority.
Session authority lock spans authorization, CAS and journal commit.

Every edit produces a version envelope including parent revision, preventing
ABA when content returns to earlier bytes. First save issues an appcand identity.
A producer/request-id pair identifies a durable receipt: identical intent
returns that receipt, changed intent refuses. Journal commit is the acceptance
barrier. Before it, failed writes leave at most unreferenced immutable artifacts.
After it, projection failure requires replay/rebuild, not a new write. Recovery
checks artifacts, fingerprints, origins, instance and complete parent chains
before replacing the projection. Missing or corrupt evidence refuses startup.

Source and asset bytes use local-complete fp1 references. Composition bytes must
be a JSON object; they remain inert data. Persistence is not catalog, operation,
renderer or publication validation. MA03 selects validation; MA04 publication.
No code evaluation/import, roster mutation, grants, network, UI, deployment,
migration or mutable app data is introduced. artifact.stage_max_bytes remains
an operator prerequisite for staged uploads. No new numeric registry default
or unresolved gap is silently filled. Existing ChangeRequest remains separate;
MA02 does not claim a mounted durable change-request workflow.

Independent review of 67eb7448 found two P2 acceptance gaps: unchecked embedded
journal receipt fingerprints and uncaught lone-surrogate UTF-8 encoding errors.
The bounded repair verifies consumed candidate/session receipts with the existing
journal owner's identity recipe before replacing candidate rows; corruption
refuses without repairing authoritative bytes. MA02's core input boundary
rejects malformed Unicode before identity serialization, preserves valid Unicode
and returns CT-04 invalid input while leaving the paired socket usable. No
identity recipe, schema version, authority, limit or publication scope changes.
