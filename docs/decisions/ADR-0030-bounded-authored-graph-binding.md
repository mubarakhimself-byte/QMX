---
id: ADR-0030
title: Bounded authored graph binding and prompt proposals
generated: 2026-10-04
verified: 2026-10-04
stale_after: 30d
type: adr
status: draft
depends_on: [COMP-QMA-DAEMON, COMP-QMA-CORE, COMP-QMA-WIRE]
decisions: [DEC-0305, DEC-0311, DEC-0312, DEC-0342, DEC-0421, DEC-0455]
sources: [docs/decisions/ADR-0029-controlled-canonical-request-join.md]
---
# Bounded authored graphs and prompt-led proposals

The next-capability contract identifies reusable authored execution after the
reviewed canonical join. Verdict: **reuse COMP-QMA-DAEMON**. The dependency
inventory and daemon/core/wire specifications assign definitions, compilation,
authenticated ingress, journal writes and Task/Job ownership to existing owners.
MissionCompiler/GraphTemplateCatalog already validate topology; LangGraph already
owns the request cursor. A second planner service/runtime/scheduler is unnecessary.

The chosen local candidate binds an explicit one-value path with optional one
host-selected specialist and exact operation-version pins to one canonical
Task/Job. Prompt planning selects an existing host graph; validated model output
remains data until explicit host compile and existing canonical admission. See
[the internal binding draft](../../_docwork/authored-graph-binding-v1.md) for shape,
identity, grants, effects, cancellation and certainty rules. No public CT changes,
component additions or registry values are selected; no corpus gap is silently
closed. The historical graph-engine and provider-choice gaps remain open.

Tradeoff: a typed path makes retained reads and optional specialist execution
reusable now. Arbitrary DAG fanout and partition retries remain a separate seam.
Request-only persistence can continue an observed predecessor. Canonical disk
reopen retains evidence and refuses replay because Agent leases are not rebuilt;
explicit canonical reconciliation must precede that stronger recovery claim.

This is a draft implementation amendment, not a ratified production extension.
The parent owns publication/corpus adoption. Local synthetic paired evidence and
independent review are recorded in the delivery ledger; inherited aggregate
coverage and documentation debts are not relabeled green.
