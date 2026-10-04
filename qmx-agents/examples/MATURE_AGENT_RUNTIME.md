# Mature agent runtime: acceptance and operator handoff

Current generic skills/hooks increment: [SDK_SKILLS_HOOKS.md](SDK_SKILLS_HOOKS.md)
documents released SDK middleware wired through operator configuration and
authenticated daemon requests, host-scoped progressive skills, bounded parsing,
ordering, refusals and replay. The historical acceptance below remains the
earlier increment's snapshot; generic skills/hooks are core requirements and now
have this working bounded path. Their installation/improvement, general agent
authoring, broader autonomous workflows and final platform integration remain
unfinished. Native backend capabilities retain their separate native contracts.

This is a working local bounded backend increment, based on candidate
`6cb4cbbda7fd554af092e137e362e09588af3ac8`. No UI, merge, push, credentials,
provider spend or remote service was authorized. Deterministic provider fakes
exercise real admission, journal, corpus and QMX domain services. They are not
live inference proof. The implemented domain operation returns corpus metadata;
it does not backtest, write a strategy, trade, or validate scientific conclusions.

## Ownership and invocation

| Responsibility | Native/reused implementation | Glue or new bounded module | Verification |
|---|---|---|---|
| Generic reasoning/tool routing | Released LangChain `create_agent` | `tool_loop.py`: one-call text codec and granted StructuredTools | `test_langgraph_runtime.py`, existing tool-loop suite |
| Internal research cursor, checkpoint/restart/interrupt | Released LangGraph `StateGraph`, official saver semantics | `graph_storage.py` adapts existing AuthoritativeJournal | disk reopen, pending-write crash, observed receipt reuse |
| Request lifecycle, admission, top-level status | Existing RequestRuntime, ProductSessionService, durable daemon FIFO | `daemon_bridge.resume`, CT-40 explicit capability | authenticated submit/status/cancel/resume; owned scope checks |
| Source evidence retrieval | Existing KnowledgeService and artifact admission | `RetainedCorpus`: trusted bounded UTF-8 pins | supplied visible corpus only, hidden evidence absent |
| Persistent named specialist, isolated per-job agent thread | LangChain agent inside LangGraph workflow | `research_workflow.py` versioned immutable definition | distinct job thread IDs, unchanged host restrictions |
| Domain effects/receipts | Existing operation descriptor, grant evaluator, dispatch_tool | pending/observed journal receipt adapter | never repeat observed effect; unknown pending never redispatch |
| Durable scoped summary memory | Existing MemoryCandidate and MemoryAdmissionGate, existing HookRegistry | `scoped_memory.py`: latest admitted summary per exact scope | fresh-job recall, restart recall, actor/app/profile isolation, deny hook |
| Invocation context | Existing admitted prompt/profile plus retained evidence | frozen delegation_input before entering child | interrupted A -> B updates shared memory -> A resumes unchanged |
| Native Codex/Claude session workers | Official native SDKs are the selected future session boundary | execution_kind prevents inference wrapping | native fake bypass/mixed composition only; no native SDK live claim |

To opt a configured inference profile into the bounded research workflow, retain
its existing `tools: ["research_browse"]`, source/as-of set/allowed_locators and
instance_revisions configuration, then add to `agent_sdk`:

```json
"research_workflow": {
  "specialist_id": "corpus-analyst",
  "version": "1",
  "instructions": "Analyze only supplied evidence and state its limits."
}
```

Configuration is trusted operator input. Paired clients cannot choose providers,
models, grants, tools, specialist instructions or corpus roots. Application/page
behavior remains distinct from `authoring | app-use` authority. The workflow defaults to profiles with research tools. Optional `profiles` explicitly
selects host behavior profiles, including a restricted profile to interrupt before
work. Ordinary no-tools Copilots retain direct inference; a selected restricted
inference profile interrupts at the boundary. A native
session no-tools profile runs its worker directly. Native profiles with inference
tools are rejected. App-use authoring prohibitions remain existing grant policy.

The backend advertises `resume_agent_request` alongside submit/get/cancel, each
with a separate operator capability. Resume accepts only the existing reference:

```json
{"request_id":"req:existing", "product_session_ref":"psess:originating"}
```

It requires an owned interrupted request, unchanged admitted host policy/current
scope and bounded queue capacity. It may repeat an unknown model call, but cached
observed domain effects do not repeat. Pending unknown domain effects need external
reconciliation and remain interrupted. Clients must present this distinction; no
UI changes are included here. Restart never silently executes unknown running work.

## Transcript idea-to-module acceptance

Source citations are original physical line ranges established by the complete
October 3 evidence reads: `Design-Extensible-Agents (1).md` (Agents) and
`Explore-Node-Editor-Architecture.md` (Mini-apps). Their assistant architecture
proposals are evidence, not blanket acceptance. The October 4 operator direction
selects mature libraries while preserving the original reusable platform intent.

| Original idea/source | Current module and ownership | Accepted/verified here | Deferred/unsupported |
|---|---|---|---|
| Custom reusable agents/harnesses; Agents 3-7, 999 | LangChain provider/tool seam plus QMX host policy | Configured bounded analysis agents; library routing | arbitrary user harness authoring/plugins/evaluation |
| Five quant roles; Agents 999,1005-1035 | Existing declarative CopilotProfile; specialist definition | role remains instruction/profile, host behavior preserved | complete researcher/trader/developer/PM/analyst organization |
| Bot vs running Agent; Agents 3963-3968,4087-4164 | Persistent SpecialistDefinition vs isolated job threads | immutable versioned specialist, no reused job context | full bot actor ontology/routines/relationships |
| Missions broader than tasks; Agents 3968,4208-4239 | Existing mission/task graph remains host projection | one admitted request/workflow with no duplicate scheduler | mission planning/replanning and general graph authoring |
| Runtime/client boundary; Agents 3963,4002-4045 | Existing daemon/wire/paired ingress | autonomous in-scope background steps, status/cancel/resume | UI lane belongs to Claude; distributed workers |
| Extensible specialists retained; Mini-apps 715-878 | ResearchWorkflowProvider + LangChain child | named inference specialist, per-job isolation | recursive delegations and general parent/child organization |
| Memory distinct from ledger/knowledge; Agents 2184-2294 | MemoryAdmissionGate + scoped_memory; journal + KnowledgeService | provenance-bearing admitted summary, exact current authority | semantic retrieval, taxonomy, supersession/history/expiration |
| Intentional context/model coupling; Agents 3011,3698-3734 | accepted request + corpus + frozen delegation_input | bounded invocation context and stable resume | token-aware adaptive compilation/large-object RLM handles |
| Agent-wide retrospective evidence; Agents 3011,3163-3262, final corrections | journal graph checkpoints and request events | local inspectable cursor/effects/definitions/result provenance | separate agent-authored notebook, OTel trace export/evaluation |
| General hooks, not tool-only; Agents 3959-3976, final hook section | existing QMX hooks and domain grant gates | host corpus artifact and memory-write hooks retained | whole autonomous hook/policy workflow and skill review |
| Tools include reads, computation, writes; Agents 3959-3976 | public operation descriptors/dispatch_tool | actual bounded read operation, host envelope only | mutation operations and compute/sandbox tools |
| Dialogue/RLM/attached/autonomy are independent; Agents 3011,3336-3369,3976 | existing request host plus mature workflow libraries | background bounded dialogue-style inference | RLM and arbitrary execution/autonomy mode matrix |
| Generic applications beyond present mini-apps; Mini-apps 191-307,424-587,879-1050 | provider adapter and QMX operations, no UI coupling | graph/memory modules avoid trading/product UI implementation | alternative live systems/complete reusable extension catalog |
| Independent Copilot conversations; Mini-apps 879-1050, later correction | existing global/application/page profile context binding | role instructions retained; isolated graph threads; native/inference coexist | native session subscriptions and full session continuity |
| Authoring vs app-use authority; Mini-apps later correction | existing ProductSession grants and AgentRequestPolicy | existing backend tests preserve differing authority contracts | UI/backend wiring and authoring experience |
| Provider/library choice; October 4 current direction | pinned LangChain/LangGraph, worker-kind seam | generic routing/checkpoints are library-owned | official native SDK adapters, human auth and spend caps |

## LangMem evaluation

LangMem provides extraction/consolidation and memory manage/search tools. Its
namespaces separate store data, not QMX authority. A LangGraph checkpointer stores
workflow state; a BaseStore stores cross-thread memory. Neither namespaces nor
`InMemoryStore` provide durable host authorization. LangMem's examples invoke
models/embeddings and older examples use `create_react_agent`; this increment uses
current `create_agent` and enables no automatic extractor/embedding calls.

Decision: no LangMem dependency now. A later extraction adapter may propose
MemoryCandidate objects through the same host-scoped MemoryAdmissionGate, with
source provenance, current access checks, host hooks, budgets and supporting result
artifacts. LangMem would not own admission, overwrite accepted memory, turn all
history into memory, or serve as the checkpoint database. Full CT-43 memory
operations remain unsupported by the bounded latest-summary provider.

## Official sources and compatibility

Reviewed current official documentation and installed released source on October 4:

- [LangChain agents](https://docs.langchain.com/oss/python/langchain/agents): `create_agent`, custom model integration and checkpointed graph.
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview), [persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts): local library workflow, thread/checkpoint semantics, explicit resume.
- [Official Codex SDK](https://learn.chatgpt.com/docs/codex-sdk), [Claude Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview): future native worker/session boundary, never double tool loops.
- [LangMem hot path](https://github.com/langchain-ai/langmem/blob/main/docs/docs/hot_path_quickstart.md), [background memory](https://github.com/langchain-ai/langmem/blob/main/docs/docs/background_quickstart.md), [dynamic namespaces](https://github.com/langchain-ai/langmem/blob/main/docs/docs/guides/dynamically_configure_namespaces.md).
- [OpenRouter quickstart](https://openrouter.ai/docs/quickstart), [API overview](https://openrouter.ai/docs/api/reference/overview): official `/api/v1/chat/completions`. The authorized exception is exact HTTPS host/path/443 only, provider fallback false, no automatic retry/redirect.

Context7 resolved LangChain/LangGraph/LangMem and supplied the linked official
examples. Installed compatibility is LangChain 1.4.3 / LangGraph 1.2.12 /
langchain-core 1.6.6 / checkpoint 4.2.0 / prebuilt 1.1.0 on Python 3.14.7.
The workspace lock is authoritative. No commercial Agent Server or LangSmith
service is required or enabled. Inherited LangSmith tracing is disabled.

## Remaining acceptance

No official native SDK session adapter, real provider inference, native subscription
resume, credential handling, budget/spend authorization, remote provisioning or
60-hour endurance run was performed. The journal adapter replays a linear log and
has no claimed long-run throughput/retention benchmark. All installed domain tools
are read-only and host callbacks must be bounded/cooperative. Memory retains one
admitted summary per exact scope, not semantic/vector search or a learned skill.
Unknown effects require reconciliation; cancellation intent does not prove upstream
abort. Full integration must apply the parent's separate baseline corrections and
run combined checks without changing protected branches until authorized.
