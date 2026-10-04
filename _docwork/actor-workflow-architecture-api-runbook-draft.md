# Bounded actor/workflow increment — architecture, API and runbook draft

4 October 2026. Base `5acb4a6483567976be771880d57b30482da4ec6b`. This draft describes
the implemented local backend increment, not whole-platform acceptance. Canonical
documentation is unchanged; an unapplied patch accompanies this draft.

## Architecture and exact ownership

Original intent remains the requirements baseline: reusable Role specifications,
persistent Quant identity, executing Agents/Subagents, authored procedures, scoped
memory and one approachable Copilot with specialists beneath it. This increment
does not reduce that baseline to the existing corpus research example.

The optional host file `actor-workflows.json` is loaded by
`DaemonProcess.configure_agent_requests`, after existing session-scoped tool
composition and before `AgentRequestBridge` restores/starts its queue. The ordinary
entrypoint is still `python -m qma.daemon`, with the existing operator-owned
`agent_sdk` configuration. A paired client selects an installed Copilot profile;
the host route selects the Quant and workflow. Clients cannot supply roles,
instructions, providers, workflow steps, actor identity, roots or grants.

- `ActorRole` is a versioned behavior/tool ceiling, not authority. Two roles
  (analyst and reviewer) actually execute through injected providers in the tests.
- `quant:<host-name>` is a durable behavioral actor owned by the paired operator,
  recorded in the existing journal. It is different from job/child execution
  Agent IDs and graph thread IDs. It does not mint canonical Agent capabilities,
  a Task lease, trading authority or CT47 authoring admission. Catalog routes are
  not a replacement for the existing ontology/Task authority services.
- A job is the existing durable RequestRuntime record. Each workflow and child
  receives its own graph thread. New jobs receive fresh model context; bounded
  typed actor memory can be recalled under the exact host scope.
- The host authored finite workflow selects installed `normalize`, `read`,
  `agent`, and `collect` steps. `read` dispatches an existing granted domain
  operation without an LLM. A fully deterministic domain-read job is tested.
- `AgentRequestBridge` alone owns queue/worker scheduling, restart admission and
  cancellation. `StateGraph` alone owns workflow step ordering/checkpoints.
  `ToolLoopProvider`/released `create_agent` owns each child's model/tool loop.
  There is no added server, background scheduler, recursive spawn or planner.
- Per-child `effect_namespace` prevents child call-1 collisions while retaining
  the parent request as authority owner. Existing callers omit this parameter,
  preserving old effect keys and binding bytes across upgrade/replay.
- A bound callback checks actual payload keys against the current bound grant's
  `parameter_ceiling.allow_keys`, immediately before execution. The new journey
  exposed the inherited in-process ceiling gap; this focused repair also protects
  deterministic workflow reads. It does not amend or replace the grant ledger.

The catalog pins role/workflow versions and hashes all selection into the request
provider identity before acceptance. Reusing a version with different content
refuses startup. Queued jobs recover after restart with unchanged host catalog.
Catalog upgrades deliberately refuse retargeting old accepted work: drain old
jobs under their original catalog before replacing it, or retain the prior host
configuration for explicit recovery. Multi-version migration/routing is not yet
implemented. Changing an unrelated route also changes this catalog-wide pin.

Delegation is leaf-only, depth 1. Host limits cap children (up to 8), total
configured child model steps (up to 32), per-role model/tool steps (up to 8 each),
workflow nodes (up to 12), existing context/tool-result budgets, and final workflow
output (64 KiB). Existing request timeouts and bounded worker/inflight limits apply.
Explicit recovery of an unknown model call can repeat that call; configured steps
are not a monetary cap across uncertain retries. There is no automatic improvement
loop or automatic recovery of an unknown running owner.

## Mini-app and Copilot contracts

The committed base's `CopilotProfile` has `global`, `application` and `page` behavior
roles. `AgentRequestPolicy` separately selects `authoring` or `app-use` authority.
`ProductSession` supplies principal, app instance, context revision and grants.
An app/page profile must match its host-bound instance; a page profile has a page
binding. App-use cannot silently edit implementation. A skill, installed operation
or profile never grants permission. Native session adapters keep their native
harness and restricted metadata callback ownership.

An actor route may adapt an existing mini-app profile to a specialist workflow.
The actual app journey uses the live research-corpus roster, pinned snapshot,
session read grant and existing `qml.research.browse` binding. Actor tools are a
subset of the host profile's installed tools; child role tools are a subset of
the route. Current actor composition supports this existing read operation family
and inference providers. Generic resource registries, independent child providers,
native actor nodes and CT47 actor-workflow authoring are not claimed.

## Memory, sharing and lifecycle

| Scope | Current implementation and sharing | Lifecycle / remaining policy |
|---|---|---|
| Job/task | RequestRuntime snapshots, LangGraph workflow/child threads, frozen child invocation input and observed effect receipts | Durable per request; explicit interrupted retry; fresh context for a new job. A request is not automatically a canonical Task. |
| Workflow | Role/workflow definitions and child graph state are pinned. Previous ordered outputs are explicit child input. | Finite host graph; no separate globally shared workflow-memory collection or cross-workflow union. |
| Quant actor | Existing `ActorMemoryScope`, `JournalMemoryProvider`, `DurableMemory` admission. Namespace includes principal, Quant, role version, host workflow source/version and current authority binding. | Bounded typed summaries survive disk reopen and feed later jobs in that exact scope. Changed authority/source/role yields a different namespace. Cancellation/revocation fences new disclosure. |
| Mini-app | Existing `ResearchMemoryScope`: principal, application, profile, authority binding, corpus source/snapshot/locators | Existing research jobs recall scoped durable summaries. This is not every app's generic memory and does not automatically share with actor collections. |
| Copilot session | ProductSession context/authority binding and request continuity containers exist | No broad durable conversational-memory service across every page or app session is wired here. Existing native turns start fresh until canonical handoff is established. |
| Global/user | Host catalog and identity records are reusable definitions | No automatic global memory pool, cross-app recall, sharing grants or consolidation process. These policies remain work, not inferred from a Store dependency. |

The actor summaries use the existing typed memory adapter and CT43 admission gate;
they do not introduce a new memory database or journal. The SDK Store remains a
search projection. Model/tool transcripts and automatic telemetry are not an
agent-authored Ledger. Existing skills are inherited only through the exact parent
profile + ProductSession + role-version selection in `AgentExtensions.select`.
The actor lane does not parse/load another skill format or widen skill scopes.

## Actual SDK usage and the new full-harness direction

At the base and this increment:

| SDK | Actual entrypoint | Implemented boundary |
|---|---|---|
| LangChain | `tool_loop.py`: `create_agent`, `BaseChatModel`, `StructuredTool` | Bounded inference/model-tool graph over admitted host operations. |
| LangGraph | `research_workflow.py` and new `actor_workflow.py`: `StateGraph`; `graph_storage.py`: released saver adaptation | Deterministic workflow cursor and durable graph checkpoints on the authoritative journal. |
| DeepAgents | `sdk_middleware.py`: `SkillsMiddleware`, `FilesystemMiddleware`, `StateBackend` | Selected immutable skill snapshots and progressive read_file. Full `create_deep_agent` harness and AsyncSubAgentMiddleware are not used by this implementation. |
| LangMem | `memory_extraction.py`: optional `create_memory_manager` | Explicit injected-model proposals; not ordinary startup, storage ownership, global memory or autonomous learning. |

**Recommendation following the live-call clarification:** use released full
DeepAgents as the default harness for inference workflow agent nodes in the next
coherent increment, while deterministic steps remain LangGraph nodes and native
subscription adapters retain their native harness. Replace graph construction at
`ToolLoopProvider`'s `create_agent` factory; do not wrap `create_deep_agent` in a
second agent loop. It already assembles the LangChain graph.

Exact incremental seam: add a pinned host harness selection to ActorRole and the
node factory, pass the same injected `_TextActionModel`, granted `StructuredTool`
callbacks, `JournalCheckpointer`, instructions and skill seed into
`create_deep_agent`, then adapt `_TextActionModel.allowed`/`bind_tools` for the
explicitly admitted SDK tools and account for SDK summarization model calls in
the same host budget. Validate model-message/tool accounting against the full
SDK stack. Register an explicit SDK HarnessProfile rather than adopting
implicit provider defaults. The pinned 0.7.21 SDK automatically installs a general
purpose subagent unless its profile disables it. Public
`GeneralPurposeSubagentProfile(enabled=False)` plus no synchronous specs disables
`task`; leaving it active needs a real delegation budget/lifecycle adapter, not
unbounded recursion. FS permissions have allow-by-default behavior on unmatched
paths, so select a StateBackend with explicit deny/allow rules and permitted
tools; no live host filesystem/execute tool follows from harness selection.
Reuse SDK middleware by replacement/merge semantics to avoid duplicate skills.

Subsequent bounded delegation can use released `CompiledSubAgent` nodes backed by
the same granted callback/effect namespace and QMA lifecycle policy. The full
harness owns its inner planning and tool loop; it must not independently dispatch
the same host workflow steps. No new server is required for synchronous scoped
node work. The AsyncSubAgentMiddleware alternative was evaluated first: it needs
an Agent Protocol server implementing threads/runs start/get/state/cancel (HTTP or
deployment ASGI). QMA's existing transport does not implement that protocol.
Adding a competing server is unnecessary for this local bounded capability.
Invocation-scoped SDK SubAgents are not persistent Quant identities.

Evidence: Context7 `/langchain-ai/deepagents` and
`/websites/langchain_oss_python_langgraph`, installed pinned
`deepagents==0.7.21` graph/profiles source, and current official
[customization](https://docs.langchain.com/oss/python/deepagents/customization),
[backends](https://docs.langchain.com/oss/python/deepagents/backends),
[subagents](https://docs.langchain.com/oss/python/deepagents/subagents),
[async subagents](https://docs.langchain.com/oss/python/deepagents/async-subagents).
The default full-harness direction is a recommendation; no competing refactor,
dependency change or implicit provider/model creation was made in this lane.

## LangSmith / tracing status

Actual generic execution in `tool_loop.py`, `research_workflow.py` and new
`actor_workflow.py` uses `tracing_context(enabled=False, parent=False)` around graph
invocation. The executor's nonsecret `LANGSMITH_TRACING`, `LANGCHAIN_TRACING_V2`,
`LANGSMITH_ENDPOINT`, `LANGSMITH_PROJECT` flags were all unset when checked.
No credentials were inspected. No host tracing configuration or LangSmith export
integration was installed or tested. Package dependencies are not integration.
Existing QMA journal/operator observations remain distinct from hosted tracing.

## API and operator recovery

Existing paired CT40 capabilities are retained. Submit using the ordinary exact
fields: `product_session_ref`, `profile_id`, `prompt`, `idempotency_key`. The
same key/job replay returns the same request without another provider invocation.
The normal queue performs start; there is no model-selected background spawn API.

`get_agent_request` adds `activities` for an actor workflow after current ownership,
policy and grant disclosure checks. Each child has a stable activity ID, role pin,
status and, when complete, its observed result. Status vocabulary includes queued,
running, cancellation_requested, cancelled, completed, failed, interrupted and
not_started. Lost running owners project interrupted; no synthetic success is
reported. Revoked/stale authority withholds both content and activity results.

`cancel_agent_request` accepts the original exact request/session fields plus an
optional `activity_id`. A child ID must belong to that owned job. Cancelling a
live or queued child cancels its dependent finite workflow through the existing
parent cancellation owner; independent child continuation is not supported.
Already terminal child cancellation returns terminal status and does not cancel
the parent. Cancellation of owned work remains possible after disclosure grants
are revoked. Provider cancellation is cooperative; an unresponsive owner becomes
interrupted on bounded shutdown, rather than a fabricated cancelled result.

`resume_agent_request` explicitly retries an interrupted request only with unchanged
host policy/current authority. Completed effects and completed child output are
reconciled from the journal/checkpointer, not dispatched again. Pending unknown
effects refuse replay and require host reconciliation; this lane does not invent
a general repair authority. Queued requests automatically recover on restart;
running unknown requests do not.

Configure existing `agent_sdk` first, then install `actor-workflows.json` beside
`operator-config.json` in the operator runtime root. Role/workflow IDs and versions
are host-owned. Start the ordinary daemon, mint a matching ProductSession and
grant any required installed reads through existing host admission. Do not use
test state/corpus as production state. The example below references an existing
host Copilot profile named `assessment`; it supplies no credentials or grant.

```json
{
  "limits": {"max_children": 2, "max_depth": 1, "max_model_calls": 4},
  "roles": [
    {"id": "analyst", "version": "1", "instructions": "Analyze supplied evidence.", "tools": [], "max_model_calls": 2, "max_tool_calls": 1},
    {"id": "reviewer", "version": "1", "instructions": "Review the analysis for unsupported claims.", "tools": [], "max_model_calls": 2, "max_tool_calls": 1}
  ],
  "workflows": [{"id": "assessment", "version": "1", "steps": [
    {"id": "normalize", "kind": "normalize"},
    {"id": "analysis", "kind": "agent", "role": "analyst:1"},
    {"id": "review", "kind": "agent", "role": "reviewer:1"},
    {"id": "collect", "kind": "collect"}
  ]}],
  "routes": [{"profile_id": "assessment", "actor_id": "quant:research", "workflow": "assessment:1", "tools": []}]
}
```

## Ownership and evidence limits

Shared hunks are separately reviewable in process.py, daemon_bridge.py,
tool_loop.py and wire agent_request.py. Provider_config.py, domain_tools.py,
Study/projection/QMB, dependency manifests and locks are unchanged. The actor
composition narrowly reuses the existing internal `_SessionScopedBinding._binding`
resolver; parent owns moving that to a public composition seam if its shared
provider work changes it. Study lane must preserve the added composition call
after current tool binding and before bridge initialization.

This establishes local injected-provider execution, restart, scope and lifecycle
behavior. It does not establish provider auth/quality, a remote worker rollout,
60-hour unattended operation, full native tools, platform coverage gates, recursive
autonomy or an aggregate completion percentage. No UI/Cortis/Lab, paid calls,
credentials, pushes, protected merges, publication or deployment occurred.
