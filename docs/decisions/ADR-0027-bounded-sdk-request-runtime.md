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
it does not relabel future architecture phases as ratified. Checkpoint `768a2318`
contains the standalone request slice; a subsequent isolated increment connects
the same runtime to authenticated daemon ingress and explicit inference transport.

Architecture preflight verdict: **reuse COMP-QMA-DAEMON**. The inventory in
`architecture/dependencies.yaml`, stack and QMA core/daemon/wire specs assign
durable command admission, sole-writer storage and grant checks to the host.
Definitions-only core and wire do not own provider subprocesses. QMB remains the
backtesting owner; no QMB or venue import is added. Existing DEC-0305, DEC-0421 and
DEC-0453 supply boundaries, not historical approval of this new request protocol.

The internal `agent_request.snapshot` family stores accepted request context,
owner attempt and terminal result in the journal. Request state is a session
execution projection; no independent store, writable database or parallel grant
system is created. The first checkpoint introduced an internal API/event proposal.
The integrated increment additionally proposes optional CT-40
`submit_agent_request`, `get_agent_request` and `cancel_agent_request` methods, each
with a distinct host-advertised capability. Canonical fold-list and addable method
adoption must account for these changes before a later release merge; no new
numbered public contract or listener is minted.

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

The existing paired origin/proof, initialization and operator admission precede
the new daemon methods. Clients select a configured profile and originating
ProductSession; they cannot supply a principal, model/provider endpoint, instructions,
grant, callback or tool target. Host policy separately binds behavior role,
`authoring | app-use`, exact app/page identity, provider deployment and bounded
prompt/execution limits. Existing single-operator class identity is retained;
pairing does not create new tenant isolation. Safe owned status and cancellation
remain available after narrowing; old content disclosure is withheld.

Daemon-owned bounded background workers keep inference off the asyncio listener.
Same-conversation requests serialize. Shutdown closes admission, requests stop and
records remaining ownership interrupted before journal release; late providers
cannot append. Known undispatched queued requests and unknown running attempts
have distinct restart handling described in reference usage.

The explicit `chat-completions` transport supports text JSON or bounded UTF-8 SSE
at `/v1/chat/completions`. Optional named environment authentication resolves only
at execution; no credentials are translated and no native client is impersonated.
There are no redirects, retries, environment proxy routing or fallback. A configured
CLIProxyAPI instance is an inference endpoint, not a workflow/session database or
proof of subscription eligibility. HTTP cancellation after dispatch is unknown;
four process-wide slots bound retained blocked DNS/connect workers until teardown.

The installed `qml.research.browse@1` read binding uses the existing KnowledgeService
and real pinned corpus digests, filtered to host-allowed locators. It returns
metadata, not corpus contents or citation creation. The model receives the pinned
argument choices. Host resolves current enabled contribution/instance revision
independently, then existing ProductSession grant admission validates the operation.
Provider identity hashes deployment plus tool/source/snapshot/locator/revision
configuration so restart changes cannot reuse old wider disclosure.

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
Failures live in the daemon register FR-86..107 and wire SDK register. Reference usage is
`qmx-agents/examples/SDK_REQUEST_RUNTIME.md` and `scoped_tool_request.py`.
