# Bounded durable memory and context

Based on `bf3c6b592e89917c17747eb1072203a28241e74a`, this lane replaces the
research request's latest-summary-only store with typed journal memory and
supersession history. It adds host-only actor memory, bounded context assembly,
and optional released SDK extraction/search. It does not complete the original
agent, learning, knowledge or agent-authored ledger vision.

## Ownership and integration

New modules: `request_runtime/durable_memory.py`, `memory_extraction.py`.
Existing runtime edit: `scoped_memory.py` only. The existing
`ResearchWorkflowProvider` already invokes its `recall` and `retain` methods,
so fresh research jobs now use typed summary history without changing the
workflow or inference loop. One existing `test_research_workflow.py` assertion
now inspects the typed journal state instead of the previous storage format.
New tests include module tests, real LangMem fake-model extraction, and a
configured daemon's paired WebSocket requests over disk close/reopen.

`process.py`, `provider_config.py`, `domain_tools.py`, `tool_loop.py`,
`research_workflow.py`, core port/gate, actor ontology and combined dependency
files are unchanged. `MEMORY_INTEGRATION_DRAFT.patch` proposes additive doc
pointers and an optional dependency extra for the integration lead. General
actor-memory composition and operator routing are the integration lead's work;
the module never infers actor identity from a thread, profile, app or session.

## Released SDK selection

LangGraph **1.2.12** `InMemoryStore` owns namespace/filter search and optional
vector ranking. It is rebuilt from authorized active canonical records for
each read. It is a disposable search projection, not durable authority. No new
SQLite/Postgres database, Store subclass, tokenizer, retrieval algorithm,
generic memory framework, background daemon or agent loop is implemented.

Optional LangMem **0.0.30** `create_memory_manager` owns extraction into typed
`ExtractedFact` proposals. Its released model signature accepts `BaseChatModel`;
this adapter requires an explicitly injected object and refuses model-name
strings. Unlike `create_memory_store_manager`, it has no storage authority.
The real SDK was exercised with a fake chat model and left the journal unchanged
until the existing `MemoryAdmissionGate` admitted the resulting candidate.
Trustcall **0.0.39** and dydantic **0.0.8** are the tested extraction dependencies.
The ordinary research path requires no new dependency beyond the base lock.

The later combined integrator accepted the reviewed patch as `4400ac05`, added
the proposed optional extra and generated the nested lock without changing any
previous package version. The repaired `MEMORY_INTEGRATION_DRAFT.patch` records
the three applied additive changes. Combined acceptance evidence is in
`_docwork/backend-integration-ledger-draft.md` at the repository root. Provision
the optional test environment with `uv sync --frozen --all-packages --extra
memory-extraction`, and run tests with `uv run --no-sync` to retain the extra.

Context7 documentation and current official docs/blog were reviewed before
selection: [LangMem launch](https://www.langchain.com/blog/langmem-sdk-launch),
[stateless extraction](https://langchain-ai.github.io/langmem/guides/extract_semantic_memories/),
[memory concepts](https://langchain-ai.github.io/langmem/concepts/conceptual_guide/),
[LangGraph persistence/Store](https://docs.langchain.com/oss/python/langgraph/persistence),
and [released PyPI package](https://pypi.org/project/langmem/0.0.30/).
Installed released source/signatures, rather than mutable examples, determined
the actual constructor and search calls. The extraction dependency emits an
upstream `Send` import deprecation warning on LangGraph 1.x; no local patch to
the SDK is made.

## Authority, records and lifecycle

`ActorMemoryScope(principal, actor_id, collection, source)` requires an explicit
host durable actor ID. `ResearchMemoryScope` retains the existing application,
profile, principal, authority revision and corpus scope. Neither is a grant.
The host must supply a live `validate` callback that checks the current owned
request/actor grants and source visibility. The request facade retains its
existing real continuation validator. Different owners, collections, source
pins or grant revisions produce separate namespaces. Regrant/migration across
bindings is deliberately unsupported.

Every record uses the existing `MemoryCandidate` and admission gate. Supported
types are `summary`, `semantic`, `episodic`, `procedural`; text is required.
Nonempty provenance, supporting artifact refs, exact source/snapshot/authority
pins and allowed locators are required. This checks declared pins; it does not
re-verify artifact possession, prove a fact true, or turn memory into knowledge
evidence. Existing `before_memory_write` hooks may refuse admission.

Each mutation appends one bounded `typed_memory` snapshot through existing
`JournalRecords` and `AuthoritativeJournal`. The snapshot contains immutable
revisions and the newest revision for each ID determines its current state.
Supersession atomically appends the predecessor's `superseded` state and an
admitted successor carrying the predecessor ref. Conflicting ID reuse refuses.
Invalidation is a durable tombstone; expiration may be explicit or an absolute
host nanosecond deadline. At `now >= expires_at_ns`, ordinary reads omit the
record even before an explicit `expired` revision. A tombstone does not erase
old journal bytes. History remains host-authorized and includes terminal states.
These lifecycle methods are host-only port calls, not installed model tools.

Exact repeated admission/terminal edits append nothing. Supersession cannot
target an inactive or foreign predecessor, and retries cannot resurrect one.
A lock shared by provider instances on the same journal prevents competing
local successors. This is a sole-writer adapter, not a distributed multiwriter
protocol. The journal append precedes state exposure; lost acknowledgment after
append is safe to retry. No persistent data outside synthetic test roots was
read, written or migrated by this lane.

## Retrieval and invocation context

Ordinary retrieval uses SDK namespace and optional exact type filtering without
embeddings. A semantic query refuses unless trusted host code explicitly injects
an `Embeddings` object and dimensions. Model names/provider initialization are
not accepted. Constructing memory, ordinary recall and configured research
requests make no extractor/embedding calls. Injected backends must be separately
reviewed and authorized before any real transmission or spend.

Only active records in the exact authorized namespace enter the projection.
The host revalidates before each document indexing call, before query execution,
and at disclosure, and rechecks canonical heads and expiration. Revocation
during an embedding prevents later document and query calls. It cannot undo a
backend call already in progress or prevent arbitrary behavior of trusted code.

`DurableMemory.context(max_bytes, max_tokens, ...)` renders whole records with
provenance/artifact refs and omits those that do not fit. It measures actual
compact UTF-8 JSON bytes; default token accounting conservatively counts bytes.
Trusted host code can inject a tokenizer for its selected model. Invalid counts
refuse. Tokenization is followed by a live head/TTL check; a changed selection
refuses disclosure. Smaller prompt budgets never delete or alter memory.
Omission is not semantic consolidation or a full conversation compactor.

The existing research facade returns one active summary projected into its
previous `summary` field with explicit memory type. Retention supersedes its
previous summary without discarding history. Its existing frozen
`delegation_input` remains invocation context, distinct from evolving canonical
memory; interrupted jobs retain that snapshot on resume.

Previous exact-scope summaries have bounded read-only compatibility. Once typed
state exists, legacy fallback stops, so an invalidated typed summary cannot
resurrect from old storage. Old legacy history is not imported into typed history;
its original journal events remain intact. No private deployment migration ran.

## Bounds and remaining work

Defaults: 64 unique record IDs, 256 revisions, 32 KiB per record, 512 KiB per
scope snapshot. Hard configuration ceilings are 128 IDs, 512 revisions, 64 KiB
per record and 1 MiB per snapshot. Capacity exhaustion refuses atomically; no
silent eviction or truncation. Journal storage retains every snapshot/event,
so these caps bound current scope state and operations, not total journal disk
growth or long-run throughput. The inherited journal reader scans the log;
no retention, pagination, performance or 60-hour endurance guarantee is claimed.

Extraction is explicitly invoked, bounded to 64 messages/32 KiB default input,
eight default candidates and one LangMem processing step with an SDK recursion
limit. Trustcall may run bounded repair graph steps for malformed output; this
is not a paid-call or provider wall-time guarantee. Real callers must use their
own authorized model/cancellation/spend policy. It proposes inserts only;
automatic updates, delete decisions and consolidation are not enabled.

Remaining richer behavior: actor selection/configuration in combined runtime,
cross-source collection retrieval, evaluated consolidation/contradiction,
automatic extraction after jobs, learned procedural changes, privacy erasure,
retention/export, quality evaluation and autonomous improvement, general
conversation/large-object compaction, knowledge indexing and the separate
agent-authored ledgers. No broad platform acceptance is claimed.

## Intent → SDK → code → evidence

| Source baseline / intended behavior | SDK mechanism and host ownership | Code / deterministic evidence |
|---|---|---|
| Original Agents 1170–1218, 1267–1277: replaceable core memory, invocation context distinct | Existing CT-43 gate/port plus Store projection; QMA sole journal writer | `durable_memory.py`; canonical-preserving budget, restart tests |
| Original Agents 1673–1708: scoped, source-bearing, superseding memory (assistant mechanism proposal) | `MemoryCandidate` typed provenance; host bindings and validation | provenance/pin denial, atomic supersession and tombstone tests |
| Original Agents 2184–2334, 3968, 4791–4824; correction 4954: memory/knowledge/agent-authored ledger distinct, reuse SDK mechanisms | LangMem stateless proposal extraction; no ledger or knowledge substitution | real released fake-model extraction, no write before gate admission |
| Original Agents 3011, 3963; Mini-apps 724, 884–1119: durable actor and separate app/session powers | Explicit host actor namespace; existing app scope preserved | actor/collection/source isolation; paired request test retains app context |
| Oct 3 brain-dump synthesis: scoped remote memory/context and long work survive UI closure | Existing journal, frozen context, current grants; no second state owner | disk reopen and interrupted-context request regressions |
| Oct 4 call/current delegation: mature SDK reuse, small coherent real backend capability, no private/provider activity | Released SDK Store/extractor, explicit optional backends, deterministic fakes | 31-test reviewed increment plus fresh-job paired socket proof; final results in evidence |

Source authority: Oct 3 task-3 `QMA-original-design-reconciliation.md` and
preserved original transcript passages were read, plus SDK skills/hooks docs and
`SKILLS_HOOKS_REUSE_REVIEW.md`. Oct 3 brain dump coverage is the preserved
`task-2/QMA-design-brief.md`, `qma-reconciliation.md`, `video-and-skills.md`
synthesis, not a claimed verbatim dictation reread. Oct 4 coverage is delegated
call clarifications/current user directions and `MATURE_AGENT_RUNTIME.md`; a
complete verbatim Oct 4 call transcript was not supplied to this lane.

See `BOUNDED_DURABLE_MEMORY_EVIDENCE.md` for final checks and independent review.
