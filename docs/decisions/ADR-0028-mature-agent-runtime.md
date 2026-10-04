---
id: ADR-0028
title: Mature agent libraries at the admitted QMA runtime seam
type: adr
status: draft
depends_on: [COMP-QMA-DAEMON, COMP-QMA-CORE, COMP-QMA-WIRE]
decisions: [DEC-0305, DEC-0421, DEC-0453]
sources: [docs/decisions/ADR-0027-bounded-sdk-request-runtime.md, docs/components/qma-daemon.md, docs/components/qma-core.md, docs/components/qma-wire.md]
generated: 2026-10-04
verified: 2026-10-04
stale_after: 30d
---

# Mature agent libraries at the admitted QMA runtime seam

The October 4 attended operator direction replaces generic bespoke reasoning/tool
sequencing with released Python LangChain and LangGraph libraries. Implementation
is authorized in an isolated local branch; merge and push are not authorized.
Preflight verdict: reuse COMP-QMA-DAEMON, CORE definitions and WIRE contracts.
No new component, numbered contract, paid server, writable database or listener.
This branch proposal supersedes ADR-0027's ephemeral tool-observation behavior;
it does not retrospectively ratify every historical architecture suggestion.

LangChain `create_agent` owns generic model/tool routing. The existing text-provider
adapter translates one response into LangChain messages; its strict JSON codec
is transport compatibility, not a second scheduler. LangGraph `StateGraph` owns
bounded research workflow steps and checkpoints. RequestRuntime and the existing
task graph project the top-level request lifecycle, without independently
scheduling the same internal steps. Dependencies are pinned to LangChain 1.4.3
and LangGraph 1.2.12 in the daemon package and workspace lock. These are local
libraries: commercial Agent Server is unnecessary. Inherited LangSmith tracing
is explicitly disabled around graph execution; corpus and memory stay in the
local journal unless an explicitly configured inference provider receives them.

The host admits the request and its scope once. In-scope steps run unattended.
An operation outside the admitted behavior profile interrupts before corpus
retention/retrieval or inference. Resume cannot widen that scope: current profile,
context binding, grant validity, corpus pin, specialist version, complete operation
binding and immutable invocation input are revalidated. Changed authority requires
new admission. Optional CT-40 `resume_agent_request` uses its own negotiated
operator-only capability, originating-session ownership, current policy checks and
bounded queue admission. The paired client supplies only a request/session reference.
No UI code is changed. A failed or cancelled request cannot use this resume command.

The implemented workflow is supplied corpus -> isolated named specialist -> actual
`qml.research.browse@1` domain metadata operation -> persisted result and admitted
summary. This real operation is intentionally read-only. Specialist definitions are
persistent and versioned; each job owns separate graph threads. Specialist prompts
retain host Copilot restrictions and append specialist instructions. Corpus contents
are retrieved from KnowledgeService retained copies through its existing artifact
gate, limited to the trusted source/as-of set/locator manifest and byte budget.
Generated analysis is deterministic provider-fixture evidence in this branch;
there is no live inference claim or research-quality claim.

Graph cursor/checkpoints, invocation context and durable memory are separate.
JournalCheckpointer adapts the official saver semantics to the existing sole-writer
journal with pickle fallback disabled. ScopedResearchMemory stores the latest
QMX-admitted summary per principal/application/behavior-profile/authority/corpus
scope, with source provenance and supporting result reference. Current authority
is checked on every read/write; the process's existing artifact HookRegistry also
governs memory writes. Invocation memory is frozen before entering the resumable
specialist so another job's memory update cannot alter an interrupted input.
LangMem was evaluated for extraction and consolidation, not installed: its store
namespace is not authorization, it needs durable storage separately from graph
checkpoints, and its model/embedding proposals would still pass QMX admission.
Semantic retrieval, historical editing, expiration and automated learning are deferred.

Domain effects record pending intent before dispatch and observed receipts before
advancing checkpoints. Replay returns only an observed result with matching arguments
and current binding; an unreconciled pending effect stays `outcome_unknown` and is
never repeated. Unknown model outcomes may require a new inference call on explicit
resume; this is not exactly-once inference or a claim of upstream cancellation.
Handlers remain synchronous bounded host reads; cancelling cannot forcibly kill an
arbitrary host callback. Journal replay is linear and unbenchmarked for long endurance.

Native Codex/Claude SDK sessions belong to `agent_session` workers, never
BaseChatModel. Existing legacy Codex app-server text support is classified that way
to prevent double planning. Native text profiles and inference profiles can coexist;
native profiles cannot enter the inference tool graph. Official native SDK session
adapters, durable native continuation and subscription behavior remain unsupported
in this change. Human authentication/spend caps, live provider proof, remote execution
and a 60-hour endurance run are separate pending work; none is represented as complete.

The operator additionally authorized removal of only the historical OpenRouter
host/adapter/image ban. Shared money/control reachability restrictions remain.
Chat Completions explicitly supports HTTPS `openrouter.ai/api/v1/chat/completions`
on port 443, with explicit model and provider fallback disabled. No auth, call,
provider spend, automatic retry, redirect or credential fallback is enabled by this
amendment. Historical OpenRouter-cut text is superseded only for this named ban.

Module-to-transcript acceptance and official documentation evidence are maintained
in `qmx-agents/examples/MATURE_AGENT_RUNTIME.md`. Designed failures are recorded
in the daemon and wire failure registers. Verification uses deterministic providers,
real corpus/grant/journal/domain services, disk reopen, cancellation, scope denial,
changed-binding refusal, memory isolation and authenticated resume.
