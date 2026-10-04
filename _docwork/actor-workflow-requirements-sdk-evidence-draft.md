# Requirements → SDK mechanism → bounded evidence

4 October 2026. Reviewed base `5acb4a6483567976be771880d57b30482da4ec6b`.
Full platform acceptance remains separate and false. The requirement set is the
two originals + Oct3 brain dump + supplied Oct4 call/delegation clarifications,
not the corpus example alone.

## Source reconciliation and authority

Personally read the final reviewed successor handoff and current core ledger;
`SDK_SKILLS_HOOKS_EVIDENCE.md` and the prior `SKILLS_HOOKS_REUSE_REVIEW.md`;
Oct3 task-3 `QMA-original-design-reconciliation.md`; Oct3 task-2
`QMA-design-brief.md`; and preserved original passages around:

- Design-Extensible-Agents (5,084 physical lines): persistent actor/SDK/modes and
  authored loops at E:3011,3059–3084; Role/ledger correction at E:3963–3985.
  Reconciliation supplies additional detailed original citations E:1170–1218
  memory port, E:1267–1277 memory/context, E:2092–2180 durable work/outputs,
  E:4954 reference-not-framework/ledger/skills/hook correction.
- Explore-Node-Editor-Architecture (1,907 physical lines): user preservation of
  agents/subagents at M:724–739; accepted global Copilot/multiple sessions and
  app-use versus authoring correction at M:1058–1068. Reconciliation preserves
  M:884–890,1094–1119 and1538–1602 for sessions/composition/ownership.
- The current Oct4 clarification explicitly proposes full DeepAgents harness
  workflow nodes, preserves native harness ownership, QMA authority and memory
  separation, and requests an incremental fit assessment. It is new steering;
  the earlier middleware-only reuse decision is not treated as a user veto of
  the full SDK. No possession/reread of a full raw call transcript is claimed.

Original hashes independently rechecked against the preserved source inventory:
Agents `d355389ee324479966cd2a5448b89ba58e81478c054a91c52c0cc9ca217b2faf`;
Mini-apps `6c0d414143eb98a0e65e914f14270f63a35b8dd61ae66a9e52922ba0922836b7`.
Assistant implementation proposals remain mechanisms, not retroactive user speech.

## Current requirement map

| Requirement | SDK / existing mechanism | Implemented and tested here | Remaining |
|---|---|---|---|
| Reusable host Role definitions | Versioned host catalog feeding existing SDK loop | analyst/reviewer instructions/tools/budgets actually run; immutable version pin | Rich role packaging and catalogs beyond finite host config |
| Stable persistent Quant, separate executing Agent | Existing authoritative journal + ActorMemoryScope | Quant record survives disk reopen; job/child Agent and thread identities differ | Canonical ontology/Task authority ingress is not minted by this behavior catalog |
| Per-job scoped sessions | RequestRuntime, ProductSession, LangGraph thread IDs | 2 jobs share actor memory but have 4 distinct child threads; idempotent submit replay | General conversation compaction and canonical native transcript handoff |
| Mini-app adaptation and Copilot types | Existing CopilotProfile + AgentRequestPolicy + ProductSession | App-use research roster/snapshot/grant + actual paired socket path | UI stays out; broader app capabilities remain owner integrations |
| Memory separate from transcript/work ledger | Existing JournalMemoryProvider + DurableMemory/CT43 + SDK Store projection | Typed actor summaries recalled only in exact principal/Quant/role/workflow/authority scope | App-wide/session/global sharing policy, consolidation and authored Ledger |
| Inherited SDK skills/hooks | Existing AgentExtensions.select + DeepAgents SkillsMiddleware/StateBackend + LangChain middleware | Analyst reads actual skill body; reviewer has no selected read_file; callback/hook regressions retained | Broader libraries and model-native formats remain respective owners |
| Deterministic steps without model | Released LangGraph StateGraph | Actual deterministic-only granted read executes with zero provider calls | Branching/join/arbitrary code authoring not included |
| Bounded agent steps | Released LangChain create_agent | Two specialists and per-role model/tool/context budgets | Full DeepAgents node harness is the recommended next increment, not implemented |
| Child start/status/result/cancel | Existing QMA request queue/cancellation + journal child receipts | Stable child IDs, queued/running/completed/interrupted/failed states; named child cancellation via real request API | Cancellation cascades to dependent workflow; independent continuation/child providers not included |
| Restart and effect idempotency | JournalCheckpointer + JournalRecords effects | Paired socket: deterministic read + 2 child call-1 effects; disk resume repeats none; legacy crash window reuses original effect namespace | Unknown pending effects require explicit host reconciliation, no auto replay |
| Queued recovery and profile version pin | AgentRequestBridge journal recovery + catalog provider hash | Queued job survives unchanged restart; same-version mutation refuses; new catalog cannot retarget queue | Multi-version catalog draining/migration |
| Authority narrowing and stale grants | Existing session dispatch/current bound GrantRecord | Child/route/profile ceilings checked; undeclared grant payload key refused before callback; revoked grant withholds results | Shared raw in-process grant-ceiling gap outside SDK callback path needs parent follow-up |
| Available provider/resource capabilities | Existing inference capabilities and current session-scoped target resolver | Native tool provider refused before actor launch; actual live roster/snapshot/grant resolver reused | Generic resource registry and alternate child providers |
| No competing orchestration owners | QMA worker queue + LangGraph cursor + SDK child loop | Finite sequential graph, leaf depth1, no background orchestrator added | Released SDK delegation lifecycle integration when full harness is adopted |
| AsyncSubAgentMiddleware evaluated first | Current official docs + Context7 + pinned SDK source | Evaluation completed: remote Agent Protocol lifecycle required; existing QMA transport retained | Optional future genuine Agent Protocol adapter, not a made-up local ASGI transport |
| Full DeepAgents harness direction | create_deep_agent/CompiledSubAgent/HarnessProfile official SDK | Current-code recommendation and exact graph-factory seam documented | Adapter accounting/default delegation/filesystem scopes must be verified before default switch |
| LangMem | Existing optional create_memory_manager | Existing extraction ownership documented; actor memory does not silently call a model | No default extraction/global memory integration claimed |
| LangSmith | Existing tracing_context | Generic graph execution explicitly disables traces; executor flags unset | No hosted tracing integration, credentials or export |

## Focused evidence

Current dedicated actor selection: **17 passed, no skips, 43.06s**, including actual
paired socket, 2 specialist/2 job journey, deterministic-only read, original
namespace crash-window replay, queue recovery, catalog pin, stale/refusal/cancel
and native-tool-provider refusal. A fresh job after disk reopen also recalls the
retained analyst summary into a new thread. Final strict Pyright: **7 changed files
analyzed, 0 errors/warnings**,7.924s. The seven-file integration selection before the last
two tests: **104 passed, no skips,72.63s**. Independent reviewer: **128 passed,
no skips,79.79s**, eight files, then **17 passed,35.94s** and the latest restart-memory
extension independently **1 passed,18.66s**. No remaining bounded source or document
blocker was found. The final handoff records exact evidence paths and source imports.

Owned runtime and tests are actor_profiles.py, actor_workflow.py and
test_actor_workflow.py. Shared reviewed seams: process.py, daemon_bridge.py,
tool_loop.py and wire agent_request.py. Existing provider_config/domain_tools,
Study/QMB/native adapters, manifests and lock are unchanged. Exact source-first
runner/evidence is retained in task21, borrowing already pinned distributions
read-only. This is not a fresh frozen-install claim or a whole-platform gate.

The early review reproduced real defects rather than relabeling a first run as
green: missing memory now_ns, colliding child effect IDs, dropped DTO activity ID,
and the inherited parameter-ceiling gap. Fixes preserve the original journal,
SDK loader/parser, native boundary and legacy effect identities. Initial failed
setup (missing basetemp parent), strict configuration-path diagnostic and all red
test/type logs are retained, not counted as successful evidence.

No literal completion percentage, live provider quality/auth, remote 60h endurance,
whole-suite coverage, hosted CI, UI, credentials, provider spend or deployment is
inferred from these local tests.
