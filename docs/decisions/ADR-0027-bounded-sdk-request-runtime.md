---
id: ADR-0027
title: Bounded SDK request execution in the QMA host
type: adr
status: draft
depends_on: [COMP-QMA-DAEMON, COMP-QMA-CORE, COMP-QMA-WIRE]
decisions: [DEC-0305, DEC-0421, DEC-0453]
sources: [docs/components/qma-daemon.md, docs/decisions/ADR-0020-qma-agentic-system.md, docs/decisions/ADR-0024-workflows-construction-kit.md, docs/decisions/ADR-0025-pack-and-grant-kit.md]
generated: 2026-10-03
verified: 2026-10-03
stale_after: 30d
---

# Bounded SDK request execution in the QMA host

Current attended operator instruction requests working SDK code in an isolated
branch, permits local commits and forbids merge. This branch implements a bounded
request/provider/read-tool slice. This ADR proposes its canonical corpus amendment;
it does not relabel future architecture phases as ratified.

Architecture preflight verdict: **reuse COMP-QMA-DAEMON**. The inventory in
`architecture/dependencies.yaml`, stack and QMA core/daemon/wire specs assign
durable command admission, sole-writer storage and grant checks to the host.
Definitions-only core and wire do not own provider subprocesses. QMB remains the
backtesting owner; no QMB or venue import is added. Existing DEC-0305, DEC-0421 and
DEC-0453 supply boundaries, not historical approval of this new request protocol.

The internal `agent_request.snapshot` family stores accepted request context,
owner attempt and terminal result in the journal. Request state is a session
execution projection; no independent store, writable database or parallel grant
system is created. It is an additive internal API/event proposal, not a CT-40
public method or a new numbered public contract. Canonical fold-list adoption must
account for the projection before a later release merge.

Native execution narrowly reconsiders the foreign-runtime hosting cut: only an
optional supported local Codex executable is used, behind a provider protocol and
verified text-only settings. It owns no QMA authority. Installed 0.159.3 lacks
restricted read roots: this slice claims configuration-based tool denial, never
OS read isolation. No existing credential/session home is opened, no API-key
fallback is automatic, and live proof requires personal authentication and scope.

Global/application/page behavior profiles are distinct from the unchanged
`authoring | app-use` authority profiles. Host tool ceilings intersect current
product-session grants. Model output cannot supply callbacks, targets, grant IDs,
envelopes or code. Bounded read handlers receive the admitted validated payload.
Stronger context/retrieval ceilings remain a subsequent contract task.

Every turn starts fresh. Provider thread/turn IDs are evidence until authorized
canonical handoff prevents disclosure after authority narrowing. Cancellation is
intent; observed completion may win a race. Unknown provider/tool outcomes and
crashed running owners become interrupted and never replay automatically. Explicit
retry creates a new owner attempt and new tool invocation identities.

Tool observations are not durable checkpoints. Native tools/resume, remote workers,
autonomous children, persistent memory and workflow-to-agent composition are future
bounded slices. Complete architecture and phased acceptance live in the task
workspace; they are not silently implemented product claims.

Acceptance includes lifecycle/provider/tool tests, existing authority regressions,
static checks, fresh-process example readback and independent Standards/Spec review.
Live proof is separate from deterministic model and subprocess protocol fixtures.
Failures live in the owning package register FR-86..98. Reference usage is
`qmx-agents/examples/SDK_REQUEST_RUNTIME.md` and `scoped_tool_request.py`.
