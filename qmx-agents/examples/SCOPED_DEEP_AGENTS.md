# Scoped Deep Agents comparison

This is an opt-in local comparison of released Deep Agents 0.7.21, LangChain
1.4.3, LangChain Core 1.6.6 and LangGraph 1.2.12. The actor base is
`71518e4ef72733ca43ce06e0f1c31ef9b35b1277` with the shared grant repair
`29f75aa6dabcb6101487d07e1171f475be6aa25e`. It implements the explicitly
authorized comparison packet, not a default switch or canonical actor/Task join.

The preflight verdict is **reuse COMP-QMA-DAEMON**, its existing RequestRuntime,
ProductSession admission, AuthoritativeJournal and effect receipts. CORE and
WIRE retain their contracts. The dependency inventory, daemon specification and
ADR-0028 already own these responsibilities; no authority mismatch calls for a
new component. No package pin, operation schema, public wire contract, memory
backend, scheduler, server or native session owner changes.

The host can supply `deep_agent=DeepAgentSelection("app-reader", "analyst:1")`
to the existing trusted `DaemonProcess.configure_agent_requests` composition
seam. Selection names one existing catalog profile and role. Paired clients and
model output cannot choose it. Other roles continue with LangChain `create_agent`.
This comparison adds a Python composition argument; it does not add a JSON
configuration field or UI selector. The parent integrates that argument with its
Study/composition lane. Role model-call ceilings include summary calls.

At the selected inference node, `create_deep_agent` replaces `create_agent` once.
There is no outer agent loop. Deterministic workflow reads still call the owner
operation through admission, without a model. Native Codex/Claude agent-session
providers are refused by the inference adapter and retain native session/tool
ownership. Inference adapters use the existing single-call text codec.

The SDK harness profile sets `GeneralPurposeSubagentProfile(enabled=False)`;
`subagents=[]` alone is insufficient. Shell execution, delegation, file mutation,
directory listing/search and manual compaction tools are excluded. Deep Agents
requires `read_file` in FilesystemMiddleware even with no skill library. It is
therefore visible, but the mandatory host scope middleware permits only exact
selected snapshot paths; an empty snapshot refuses every read. The backend is
the SDK's virtual StateBackend, with no host filesystem or sandbox capability.
Skills still use the existing snapshot importer, SDK parser and progressive
loader. Their bytes and selection are pinned independently from grants.

Same-name SDK middleware replacement narrows FilesystemMiddleware to `read_file`,
disables tool/human eviction, and supplies released summarization middleware
with an injected summary model. Every model/summary call reserves its allowance
in the QMA journal before dispatch. The default summary retry is disabled through
the model's public Runnable `with_retry` interface. An unknown summary or inference
consumes budget; an explicitly admitted retry is another call, never exactly-once
inference. Tool reservations include the built-in read and survive checkpoint
replay. Existing operation intent/observed receipts remain the effect authority.

DeepAgentState stores message deltas rather than the full message list at every
checkpoint. The candidate uses public LangGraph `get_state()` to reconstruct
messages for host call identity; reading raw checkpoint `channel_values` fails
between snapshots. No custom delta reducer or second checkpoint database was
added. Summary history offload stays in virtual graph state/checkpoint projection,
not an admitted memory record, and is outside the model-readable snapshot paths.

Offline contract evidence is in `test_deep_agent_comparison.py` and
`test_deep_agent_actor.py`. It compares the same skill/read/final journey;
refuses built-ins, host paths, traversal, malformed offsets, native sessions and
changed snapshots; bounds models, summary calls and tools; cancels accepted
reads cooperatively; refuses unknown effects; and reuses observed receipts.
Actual daemon/socket disk reopen also resumes an incomplete selected specialist
with a separately reserved retry allowance. Existing actor tests prove separate
effect namespaces and a deterministic operation with zero model calls.

Recommendation: retain this as a bounded opt-in candidate. The identical injected
journey used three provider calls and one operation callback under both factories.
One local observation recorded 68 versus 75 journal events and approximately
0.54 versus 1.22 seconds; these are fixture/SDK overhead observations, not a
statistical benchmark or real-model quality evidence. Summarization adds a useful
SDK capability, but it needs headroom inside the total role allowance. Exact
release pins matter because harness profile APIs are beta. This does not justify
a default switch without representative authenticated inference evidence under
separate user authorization, or production endurance/cancellation guarantees.

Before enabling SDK subagents, the parent must supply the adopted canonical join
contract: owner/execution/child identity, Task/JobHandle cardinality, frozen
catalog/mapping revisions and CT47 attribution. A leaf adapter must intersect
parent/child/current grants, prohibit recursive children, preserve distinct effect
namespaces, propagate cancellation/owner loss/late completion and unknown effect
reconciliation, and charge every child model/summary/tool call to the parent
budget. The current candidate exposes no task tool and supplies none of that
unadopted canonical authority. Remote hosting, live provider auth/spend, memory
provider selection, UI and deployment remain outside this comparison.

Official versioned API sources used for the implementation:

- [Deep Agents 0.7.21 graph and factory](https://github.com/langchain-ai/deepagents/blob/deepagents%3D%3D0.7.21/libs/deepagents/deepagents/graph.py)
- [Deep Agents 0.7.21 harness profiles](https://github.com/langchain-ai/deepagents/blob/deepagents%3D%3D0.7.21/libs/deepagents/deepagents/profiles/harness/harness_profiles.py)
- [LangChain 1.4.3 agent factory](https://github.com/langchain-ai/langchain/blob/langchain%3D%3D1.4.3/libs/langchain_v1/langchain/agents/factory.py)
- [LangChain 1.4.3 summarization](https://github.com/langchain-ai/langchain/blob/langchain%3D%3D1.4.3/libs/langchain_v1/langchain/agents/middleware/summarization.py)
- [LangGraph 1.2.12 state graph](https://github.com/langchain-ai/langgraph/blob/1.2.12/libs/langgraph/langgraph/graph/state.py)

Context7 was also queried for discovery. Its unversioned examples differed from
the released source layout and could not establish the exact API. Downloaded
official sources, SHA256 hashes, installed import provenance, test commands,
red/green logs and independent review are delivered with the comparison bundle.
