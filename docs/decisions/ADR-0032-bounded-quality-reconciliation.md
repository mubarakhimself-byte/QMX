---
id: ADR-0032
title: Bounded documentation reconciliation and native research publication
type: adr
status: draft
depends_on: [COMP-QMB, COMP-QMF-DATA-BACKUP, COMP-OBJECT-STORAGE, COMP-DUKASCOPY, COMP-CALENDAR-FEED]
decisions: [DEC-0106, DEC-0108, DEC-0118, DEC-0145, DEC-0161, DEC-0170, DEC-0178, DEC-0198, DEC-0214, DEC-0252, DEC-0286, DEC-0380, DEC-0402, DEC-0445]
sources: [_docwork/strict-docs-reconciliation-2026-10-05.md, _docwork/ledger.yaml, docs/contracts/ct-02-time-calendar.yaml, docs/contracts/ct-07-lineage-edge.yaml, docs/contracts/ct-25-risk-journal.yaml, docs/registry/variables.yaml, qmb/src/qmb/host/research_store.py, qmb/src/qmb/host/_windows_research.py, qmb/tests/test_research_windows.py]
generated: 2026-10-05
verified: 2026-10-05
stale_after: 30d
---

# Bounded documentation reconciliation and native research publication

The local quality candidate starts at reviewed commit
`1531eecb4c057f35ede2ec7fc5085fbe1451b286`. Its scope is inherited strict-docs
failures and the Windows research-store UUID finding. This draft records the
implementation and reconciliation evidence; it adds no ratified design decision.

## Reuse and contract impact

Verdict: **reuse COMP-QMB**. The dependency inventory assigns the host persistence
adapter to QMB; the public `persist_research_blob` path already validates canonical
Stage 0 bytes and their content fingerprint. QML supplies pure serialization;
qmf-registry owns registered kinds; neither owns filesystem staging. The existing
native adapter holds no-follow directory anchors, exclusively creates a staging
object, flushes it, publishes without replacement, verifies the held identity,
and deletes only its owned object on pre-publication failure. No new component,
public signature, CT format, dependency edge or registry value is needed.

The native staging name becomes a deterministic attempt suffix, retried only on
`FileExistsError`, with the same finite attempt count as the POSIX adapter. The
name is an internal allocation detail, never research identity or evidence bytes.
Directory, reparse, sharing and permission failures still refuse. If all staging
candidates are occupied, the operation refuses without deleting or replacing
another owner's object; a later retry can succeed after a candidate is released.
This bounded availability limit is deliberate and tested. Predictability supplies
no write authority: exclusive native creation and held handles do that.

Moving entropy to an unproved composition-root exemption would retain an
unnecessary ambient dependency. Weakening the scanner, opening a colliding object,
or broadly catching access failures would obscure the real contract. The chosen
correction removes the entropy read and preserves durable no-clobber publication.

Verdict for docs: **reuse the existing component and scenario documents**. Ledger
DEC-0170 closes the personal-use ops flag; DEC-0198 / DEC-0214 name the V1 news
source; DEC-0198 / DEC-0252 split measured integrity and host-loss recovery;
DEC-0145 fills CT-25; DEC-0178 fills the prediction-linter design. Corrections
reflect those existing rulings. DEC-0286 records historical source-inspected risk types and CT-32 at integration@1b451a848d897e42f6e2c7fd9f2ea86fab7295f2, never end-to-end or performance proof. The inherited stage-state scalar is quoted without changing its historical value. Provider claims stay historical design evidence;
no current vendor, legal, provisioning, measurement or live-operation proof is
asserted. Partial scenario repairs retain their expired verification dates.

## Evidence and remaining boundary

Native regressions exercise save/reopen without entropy, occupied-file
preservation, exhausted-name refusal and recovery, fail-closed directory
collision, and cleanup after a pre-publication flush failure. Existing native
concurrent equal/conflicting publication, fresh-process reads, no-clobber,
post-publication flush refusal and ancestor/reparse containment remain required.
Focused host evidence is Windows-specific; skipped POSIX-only cases are not a
Linux execution claim. The full gate record and sequential independent review
belong in the local delivery, not in a synthetic release-green assertion.

Strict docs still fail on unreconfirmed dates and two intentional provisional
artifacts. DEC-0380 ratifies the operator paradigm while keeping the absorbed
package provisional; DEC-0402 and DEC-0445 preserve that distinction. No deletion,
ratification stamp, staleness-budget extension or check exemption closes it.
The reconciliation report names the remaining evidence needed per artifact.
Inherited QMA coverage debt is outside this slice and remains debt.

Canonical owner recovery is another lane. This candidate edits no QMA runtime
file, changes no protected branch, publishes nothing and activates no service.
The parent owns composition; the changelog and stage-state entries are additive
and may need mechanical composition with that lane's documentation.
