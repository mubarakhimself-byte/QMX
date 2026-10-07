# QMX agent harness research: adopt, don't invent

Date: 2026-10-07. Scope: Anthropic + LangChain primary sources, RLM, CLIProxyAPI, MCP Apps, Copilot-level delegation, LangMem status.
Every claim carries a URL. "Inference:" marks my reasoning, which no source states.
Model IDs in code snippets are copied from the docs as published, not recommendations.

Source keys used below:
- [A-MARS] https://www.anthropic.com/engineering/multi-agent-research-system
- [A-CTX] https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- [A-TOOLS] https://www.anthropic.com/engineering/writing-tools-for-agents
- [A-ATU] https://www.anthropic.com/engineering/advanced-tool-use
- [A-MCPX] https://www.anthropic.com/engineering/code-execution-with-mcp
- [A-SKL] https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- [A-LRH] https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- [A-HD] https://www.anthropic.com/engineering/harness-design-long-running-apps
- [A-MA] https://www.anthropic.com/engineering/managed-agents
- [A-EVAL] https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- [A-CM] https://claude.com/blog/context-management
- [CB-CE] https://platform.claude.com/cookbook/tool-use-context-engineering-context-engineering-tools
- [CB-COMP] https://platform.claude.com/cookbook/tool-use-automatic-context-compaction
- [CB-DW] https://platform.claude.com/cookbook/claude-agent-sdk-08-dynamic-workflows
- [CB-COORD] https://platform.claude.com/cookbook/managed-agents-cma-plan-big-execute-small
- [CB-ADV] https://platform.claude.com/cookbook/managed-agents-cma-consult-an-advisor
- [CB-IDX] https://platform.claude.com/cookbook (index)
- [L-ROUTER] https://www.langchain.com/blog/how-to-build-a-model-router-in-the-harness
- [L-RLM] https://www.langchain.com/blog/how-to-use-rlms-in-deep-agents
- [DA-OV] https://docs.langchain.com/oss/python/deepagents/overview
- [DA-CUST] https://docs.langchain.com/oss/python/deepagents/customization
- [DA-SUB] https://docs.langchain.com/oss/python/deepagents/subagents
- [DA-ASYNC] https://docs.langchain.com/oss/python/deepagents/async-subagents
- [DA-DYN] https://docs.langchain.com/oss/python/deepagents/dynamic-subagents
- [DA-INT] https://docs.langchain.com/oss/python/deepagents/interpreters
- [DA-CE] https://docs.langchain.com/oss/python/deepagents/context-engineering
- [DA-BE] https://docs.langchain.com/oss/python/deepagents/backends
- [DA-LTM] https://docs.langchain.com/oss/python/deepagents/long-term-memory
- [DA-HITL] https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
- [DA-CMP] https://docs.langchain.com/oss/python/deepagents/comparison
- [LC-MW] https://docs.langchain.com/oss/python/langchain/middleware/built-in
- [LC-ANTH] https://docs.langchain.com/oss/python/integrations/middleware/anthropic
- [LC-MOD] https://docs.langchain.com/oss/python/langchain/models
- [LC-MCP] https://docs.langchain.com/oss/python/langchain/mcp
- [LC-TS] https://docs.langchain.com/oss/python/integrations/providers/typesafe
- [LG-PERS] https://docs.langchain.com/oss/python/langgraph/durable-execution (persistence content)
- [RLM-P] https://arxiv.org/abs/2512.24601 (HTML: https://arxiv.org/html/2512.24601v1)
- [RLM-GH] https://github.com/alexzhang13/rlm
- [CPA] https://github.com/router-for-me/CLIProxyAPI
- [CC-LEGAL] https://code.claude.com/docs/en/legal-and-compliance
- [SDK-OV] https://code.claude.com/docs/en/agent-sdk/overview
- [OAI-PLAN] https://help.openai.com/en/articles/20001542-using-your-chatgpt-plan-in-other-apps-and-sites
- [MCPA-OV] https://modelcontextprotocol.io/extensions/apps/overview
- [MCPA-SPEC] https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx
- [MCPA-BUILD] https://modelcontextprotocol.io/extensions/apps/build
- [FMCP-APPS] https://gofastmcp.com/apps/overview
- [LGJS-2864] https://github.com/langchain-ai/langgraphjs/pull/2864
- [LMEM-PYPI] https://pypi.org/project/langmem/ ; [LMEM-GH] https://github.com/langchain-ai/langmem
- [QMA] _bmad-output/planning-artifacts/architecture/architecture-QMA-2026-08-28/ARCHITECTURE-SPINE.md (local)

---

## A. Pattern catalogue

### A1. Orchestrator-worker research (lead agent plus parallel subagents)
- What: a lead agent plans, saves the plan to memory, and spawns 3-5 parallel subagents. Each subagent gets an objective, an output format, tool guidance and boundaries, then returns condensed findings. A separate citation pass runs at the end. Opus lead plus Sonnet workers beat solo Opus by 90.2% on Anthropic's internal research eval. It uses about 15x the tokens of a chat. [A-MARS]
- Effort scaling goes in the prompt: 1 agent with 3-10 calls for a simple query, 2-4 subagents for a comparison, more than 10 for complex research. [A-MARS]
- Cookbook recipe: patterns-agents-orchestrator-workers. [CB-IDX]
- QMX adoption: the Copilot's "research" path (literature, market regime, cross-instrument scans) and the Analysis desk. The lead agent is a Deep Agent. Workers are declarative `subagents=` with narrow tools. The delegation brief template (objective, format, tools, boundary) goes in the lead's `system_prompt`. Reserve this for breadth-first, high-value questions because of the 15x token cost. [A-MARS]

### A2. Subagent context isolation and handoff through the filesystem
- What: each subagent explores in its own window and returns 1-2k tokens [A-CTX]. Large outputs are written to an artifact store and only references go back, which avoids a "game of telephone" through the lead. [A-MARS]
- Deep Agents: the `task` tool creates a fresh context, runs autonomously and makes a single handoff. `mode: "isolated"` is the default; `"fork"` inherits the parent's history and system prompt. [DA-OV][DA-SUB]
- QMX adoption: backtest-sweep workers write result tables to `/artifacts/...` on a store backend and return a path plus a summary. The lead never reads raw tables. Isolated is the default for all workers. Use `fork` only for "continue this thread with a different model" handoffs.

### A3. Context compaction, summarization, tool-result clearing and offloading
- Anthropic splits context control into three levers [CB-CE]:
  - compaction: server-side `compact_20260112`
  - tool-result clearing: `clear_tool_uses_20250919` (beta `context-management-2025-06-27`), with `keep`, `clear_at_least` and `exclude_tools: ["memory"]`
  - memory: `memory_20250818`
- Decision rule: repeated re-fetchable tool output means clearing (cheapest). Growing dialogue means compaction. Facts needed across sessions mean memory. [CB-CE]
- Measured results:
  - context editing alone: +29% and 84% fewer tokens on a 100-turn search eval [A-CM]
  - editing plus memory: +39% [A-CM]
  - client-side compaction: 58.6% token reduction [CB-COMP]
- Claude Code's compaction keeps decisions and bugs, plus the 5 most recently accessed files [A-CTX]. Compaction is not enough for multi-session work, so pair it with progress artifacts (A10). [A-LRH]
- Deep Agents gives you this by default:
  - `SummarizationMiddleware` triggers at 85% of the model's `max_input_tokens`, keeps 10% as recent context, and writes the original transcript to `/conversation_history/`. The fallback is 170k tokens and 6 messages. [DA-CE][DA-BE]
  - Tool results over 20k tokens are offloaded to `/large_tool_results/` with a 10-line preview. [DA-CE][DA-BE]
  - Tuning knobs: `trigger=("tokens", N)` or `("fraction", x)` and `keep=("messages", N)`. [DA-CUST]
  - The on-demand `compact_conversation` tool comes from `create_summarization_tool_middleware(model, backend)`. [DA-CE]
  - Clearing equivalent: `ContextEditingMiddleware` + `ClearToolUsesEdit(trigger, keep, clear_tool_inputs, exclude_tools)`. [LC-MW]
- QMX adoption: keep the Deep Agents defaults. Add `ContextEditingMiddleware` for market-data and log tools whose output can be re-fetched. Give `SummarizationMiddleware` QMX-specific instructions: preserve run IDs, parameter sets and metric values, as recommended for domain numbers. [CB-CE]

### A4. Memory tool and long-term memory
- What: the agent writes notes outside the context window and reads them back later (NOTES.md, a to-do list, Pokemon tallies) [A-CTX]. Anthropic's memory tool is file-based, runs client-side and is stored on your own infrastructure, with commands view/create/str_replace/insert/delete/rename. [A-CM][CB-CE]
- Best practice: tell the agent "ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING ELSE", with one file per topic under `/memories/`. [CB-CE]
- Deep Agents:
  - `memory=["/AGENTS.md"]` is always loaded, and the agent can update it with `edit_file`. [DA-OV][DA-LTM]
  - Cross-thread persistence: `CompositeBackend(default=StateBackend(), routes={"/memories/": StoreBackend(namespace=...)})` plus `store=`. [DA-CUST][DA-LTM]
  - Namespace scopes: per agent `(rt.server_info.assistant_id,)`, per user `(rt.server_info.user.identity,)`, per org `(rt.context.org_id,)`. [DA-LTM]
  - Read-only memory, such as org policy, is enforced with permissions or backend policy hooks to block prompt injection through shared state. [DA-LTM]
  - LangGraph store choices: `InMemoryStore` for dev, Postgres for production. [DA-LTM][LG-PERS]
- Anthropic memory-tool parity inside LangChain: `StateClaudeMemoryMiddleware` and `FilesystemClaudeMemoryMiddleware` (default prefix `/memories`). [LC-ANTH]
- QMX adoption: give each Quant a store namespace. `/memories/quant/<id>/` is writable. `/memories/desk/` and `/memories/policy/` are read-only through `permissions=`. QMA AD-18's admission gate (propose, then admit) becomes a backend policy hook on writes to promoted paths [DA-BE]. Inference: this keeps the QMX invariant without building a memory engine.

### A5. Tool design
- Principles from [A-TOOLS]:
  - Build a few high-impact workflow tools rather than API wrappers (`search_logs`, not `read_logs`; `get_customer_context`).
  - Namespace by service and resource.
  - Return names, not UUIDs.
  - Offer a `response_format` enum (concise/detailed).
  - Paginate, filter and truncate with sensible defaults (Claude Code caps output at 25k tokens).
  - Write actionable error messages.
  - Treat tool descriptions as prompt engineering and evaluate tools with agents.
- Tool Use Examples (`input_examples`) raised complex-parameter accuracy from 72% to 90%. [A-ATU]
- A tool-testing agent that rewrote tool descriptions cut task time by 40%. [A-MARS]
- QMX adoption: wrap QMF/QMB as tools such as `backtest_run(strategy, params, window, response_format)`, `market_bars_query(symbol, tf, range, agg)` and `experiment_compare(ids, metrics)`. Never expose raw table dumps. Use names over IDs in results. Build a tool eval (A12) before adding tools.

### A6. Per-agent tool and MCP scoping, plus tool discovery
- What: give each agent only the tools it needs. With many tools, defer definitions and discover them on demand.
- Anthropic Tool Search (`defer_loading: true`, regex/BM25) saves about 85% of tokens and raised Opus 4.5 from 79.5% to 88.1% on MCP evals. Use it once you pass roughly 10 tools or 10k tokens of definitions. [A-ATU]
- Deep Agents scoping:
  - A declarative subagent's `tools` replaces the inherited set entirely. `middleware`, `skills` and `permissions` are not inherited. `model` and `interrupt_on` can be set per subagent. [DA-SUB]
  - Filesystem tools are narrowed with `FilesystemMiddleware(backend=..., tools=["read_file","ls","glob","grep"])` (deepagents>=0.7). [DA-OV][DA-CUST]
  - MCP connects through `MCPAdapter(config)` → `await adapter.list_tools()` → `tools=`, installed with `pip install "langchain[mcp]"` (beta, v1.4.0+). [LC-MCP][DA-CUST]
- Tool selection middleware: `LLMToolSelectorMiddleware(model, max_tools, always_include)` and `ProviderToolSearchMiddleware(searchable_tools)`. [LC-MW]
- QMX adoption: open one `MCPAdapter` per server group and pass each subagent only its group's tools. Examples: the Research worker gets web plus docs MCP; the Data worker gets qmf-data tools; the Lab worker gets the qmb backtest tools. The money-path barrier (QMA AD-28) holds because no execution tool is ever in any `tools=` list.

### A7. Skills (progressive disclosure)
- What: a folder holding `SKILL.md` (YAML `name` and `description`), optional references and scripts. Metadata loads at startup, the body loads on use, and deeper files load on demand. Scripts run without entering context. Skills are an open standard (agentskills.io). [A-SKL]
- Deep Agents: `skills=["/skills/"]` adds `SkillsMiddleware`. `SkillsMiddleware(backend, sources, system_prompt=...)` customizes the catalog, and `system_prompt=None` suppresses it. Subagents set their own `skills`; they are not inherited. [DA-CUST][DA-SUB]
- MCPX tie-in: agents can save working code as reusable skills. [A-MCPX]
- QMX adoption: write domain skills such as `walk-forward-validation`, `regime-detection`, `cTrader-data-quirks`, `report-tearsheet` and `create-mcp-app` (A16; the MCP Apps project ships one [MCPA-BUILD]). Route `/skills/` to a StoreBackend so the Copilot can author and admit new skills, with admission through a policy hook (AD-22).

### A8. Model routing (harness-level)
- What: classify the task once, at the start of the thread, and route to the cheapest tier that can do it. LangChain's Open SWE router cut median cost per thread 64% ($0.94 vs $2.61) with no measurable quality change (merged PRs 29.2% vs 27.3%, p=0.49). Traffic split 56% balanced, 34% fast, 10% performance. A fast-only arm failed within a day. [L-ROUTER]
- The router belongs in the harness, not a gateway, because it needs task context. Measure outcomes with evals or an A/B test before trusting it. [L-ROUTER]
- APIs:
  - `@wrap_model_call` with `handler(request.override(model=...))` for custom routing [LC-MOD]
  - `ModelRouterMiddleware(choices={"fast": ModelChoice(model, criteria), ...}, instructions=...)` from `langchain_typesafe.experimental.middleware` (experimental) [LC-TS]
  - `ModelFallbackMiddleware(first_model, *additional_models)` [LC-MW]
  - per-subagent `model=` [DA-SUB]
- Anthropic variants:
  - big model plans, small model executes: 84-98% of tokens billed at the worker rate, about 0.3-0.5x the cost of a solo frontier model at equal rigor [CB-COORD]
  - Advisor: a mid-tier agent consults a stronger model mid-turn and pays the premium only when it consults [CB-ADV]
- Open item from LangChain: subagent routing and mid-thread re-routing. Switching models discards the prompt cache. [L-ROUTER]
- QMX adoption: AD-15's four ModelClass tiers map directly to `ModelChoice` entries in `ModelRouterMiddleware`, or to a 20-line `@wrap_model_call` if the experimental package is a concern. Pin tiers per subagent: orchestrator = REASONING_HIGH, readers/extractors = FAST_CHEAP. Add `ModelFallbackMiddleware` for provider outages. Log the routing decision to LangSmith (A12).

### A9. Code execution and RLM over data
- MCPX: present tools as code and filter data in the sandbox. Example: 150k tokens down to 2k (-98.7%), and only 5 of 10,000 rows reach the model. Privacy: intermediates stay out of context. A sandbox is mandatory. [A-MCPX]
- Programmatic Tool Calling (`allowed_callers: ["code_execution_20250825"]`) cut tokens 37% and raised GIA from 46.5% to 51.2%. [A-ATU]
- RLM: the prompt or context is a variable in a persistent Python REPL. The root model writes code and calls `llm_query()` on slices (depth 1) and returns `FINAL(...)`/`FINAL_VAR(...)`. Results [RLM-P]:
  - BrowseComp+ at 6-11M tokens: RLM(GPT-5) 91.33% vs 0% for base GPT-5
  - OOLONG-Pairs: 58% vs 0.04%
  - median cost comparable; tail cost has high variance
- Deep Agents interpreter: `CodeInterpreterMiddleware` (`langchain_quickjs`) adds an `eval` tool backed by a QuickJS JavaScript REPL. Defaults: `timeout` 5s, `memory_limit` 64MB, `max_result_chars` 4000. `ptc=[...]` is a tool allowlist exposed as `tools.camelCase()`. `mode="thread"` persists REPL state across turns. [DA-INT]
- Deep Agents gives no filesystem, network or Python inside the interpreter. [DA-INT]
- Dynamic subagents: `task({description, subagentType, responseSchema})` from JS, so code-driven fan-out guarantees coverage by construction. [DA-DYN][L-RLM]
- LangChain on OOLONG-style AgNews at 128k: 0.79 with the REPL vs 0.44 without. Slower, with higher output cost. [L-RLM]
- LangChain calls its version "closer to recursive agents": subagents have tools; the paper uses plain LM calls. [L-RLM]
- Official RLM library: `pip install rlms`, class `RLM(backend, backend_kwargs, environment, environment_kwargs).completion()`. Environments: `LocalREPL`, IPython, `DockerREPL`, Modal, Daytona, E2B. Includes `llm_query_batched` and the `RLMLogger` JSONL logger. [RLM-GH]
- QMX adoption: see B5. QMX data is pandas/Polars/DuckDB-shaped, but the Deep Agents interpreter is JS-only with no I/O. The data RLM path therefore needs a Python sandbox, either a Deep Agents sandbox backend `execute` tool or `rlms` with `DockerREPL`. Inference: QuickJS is fine for orchestration fan-out, not for numerics.

### A10. Long-running harness checkpoints and progress artifacts
- Anthropic's two-part harness [A-LRH]:
  - An initializer writes `init.sh`, a JSON feature list (all marked failing), `claude-progress.txt` and the first git commit.
  - Every later session reads progress and git, runs a smoke test, does one feature, commits and updates progress.
  - JSON resists unwanted model edits better than Markdown.
- Planner/generator/evaluator with sprint contracts negotiated through files. The evaluator uses Playwright with hard thresholds per criterion. Every harness part encodes an assumption about the model, so strip parts as models improve. [A-HD]
- Production reliability [A-MARS][A-MA]:
  - resume from the failure point, never restart
  - rainbow deploys
  - a durable session log outside the harness, with `wake(sessionId)`
  - stateless "cattle" sandboxes
- LangGraph durability: checkpointers persist thread state (`PostgresSaver` for production, `SqliteSaver` for files, `InMemorySaver`, which loses data on restart) [LG-PERS]. `PatchToolCallsMiddleware` repairs dangling tool calls when a run resumes. [DA-CUST]
- QMX adoption: the unattended overnight Copilot (AD-29 continuation) runs on a `PostgresSaver` checkpointer, plus a progress artifact (`/missions/<id>/progress.json` with pass/fail per acceptance criterion), plus a separate evaluator subagent (A13). "Done" means the deterministic verifier passes, never self-report.

### A11. Human-in-the-loop interrupts
- `interrupt_on={"tool": True | False | {"allowed_decisions": [...], "when": predicate}}`. Decisions are `approve`, `edit`, `reject`, `respond`. A checkpointer and the same `thread_id` are required. Resume with `Command(resume={"decisions": [...]})`. Subagents can carry their own `interrupt_on`, and tools can call `interrupt()`. [DA-HITL][DA-CUST]
- Caveat: PTC calls from the interpreter and `task()` from JS bypass `interrupt_on`. Gate the `eval` tool itself. [DA-INT][DA-DYN]
- QMX adoption:
  - Gate any write that leaves the sandbox: `promote_strategy`, `deploy_bot`, mini-app publish, `memory/policy` writes.
  - The `when` predicate implements "approval depends on type" (memory: mini-app approval varies by type).
  - Never give an interpreter `ptc` access to a gated tool.

### A12. Evals and tracing
- Anthropic [A-MARS][A-EVAL][A-TOOLS]:
  - Start with about 20 real queries.
  - LLM-as-judge works with one rubric call scoring 0-1 plus pass/fail (factual, citation, completeness, source quality, tool efficiency).
  - Judge end state, not path.
  - Vocabulary: task, trial, grader, transcript, outcome. Report pass@k vs pass^k.
  - Begin with 20-50 tasks taken from real failures. Capability evals graduate into regression evals.
  - Track runtime, number of calls, tokens and errors per tool.
- LangChain [L-ROUTER][DA-OV]:
  - LangSmith tracing at thread level and Insights for task clustering
  - online evaluators, user feedback attached to traces, offline datasets, A/B tests
  - `RubricMiddleware(model, max_iterations)` for self-grading [LC-MW]
- QMX adoption: LangSmith (or self-hosted OTel) traces on every graph. Golden datasets built from real Copilot sessions. Code graders for numeric outcomes, such as backtest metric matches and coverage of every symbol. An LLM rubric for research reports. Track pass^k for unattended routines.

### A13. Generator/evaluator separation (adversarial verification)
- What: agents praise their own work, so a separately tuned skeptical evaluator is far easier to calibrate. It is only worth the cost at the edge of what the model can do. [A-HD]
- Dynamic workflow pattern: extract, verify per item in a clean context, run a skeptic on each confirmation, then report. 13 agents cost $3.29. [CB-DW]
- Deep Agents ships the same patterns: fan-out, classify-and-act, adversarial verification, generate-and-filter, tournament, loop-until-done. [DA-DYN]
- QMX adoption: a strategy-claim verifier. The generator proposes an edge, independent verifiers re-run out-of-sample on fresh contexts, and a skeptic tries to refute the result. This maps onto AD-10's `author_family != reviewer_family` rule through per-subagent `model=`.

### A14. Managed-agent separation (brain / hands / session)
- What: decouple the harness (brain), the sandboxes and tools (hands, `execute(name, input) → string`) and a durable event log (session). Credentials never enter sandboxes. Provisioning containers lazily cut TTFT ~60% at p50. [A-MA]
- QMX adoption: brain = Deep Agent graph. Hands = Deep Agents sandbox backends (Docker, E2B, Daytona, Modal, Runloop, LangSmith) [DA-CUST]. Session = LangGraph checkpointer plus QMX journal (AD-6). Credentials stay in the Windows Credential Manager or broker and are injected server-side into tools, never into sandbox env.

### A15. Filesystem permissions as declarative policy
- `permissions=[{operations, paths, mode}]`, first match wins, default allow. These rules do not apply to sandbox `execute`. Subagent `permissions` replace the parent's. [DA-OV][DA-SUB]
- `FilesystemBackend` needs `virtual_mode=True` to block `..`/`~` traversal; the default gives no protection. [DA-BE]
- Policy hooks: subclass a backend or wrap `BackendProtocol` and return structured `error` results instead of raising. [DA-BE]
- QMX adoption: this replaces most of the hand-rolled AD-10 hook registry for file and store writes (C table).

### A16. MCP Apps (interactive UI from tools): see section F.

---

## B. Recommended QMX agent core, built from off-the-shelf pieces

### B1. What `create_deep_agent` gives for free [DA-CUST][DA-OV]
Signature:
```
create_deep_agent(model, tools, *, system_prompt, middleware, subagents, skills, memory, permissions,
                  backend, interrupt_on, response_format, state_schema, context_schema,
                  checkpointer, store, debug, name, cache)
```
Default stack, in order:
1. `FilesystemMiddleware`: ls/read_file/write_file/edit_file/delete/glob/grep, plus `execute` on sandbox backends
2. `SubAgentMiddleware`: the `task` tool and a general-purpose subagent
3. `SummarizationMiddleware`: 85% trigger, transcript saved to `/conversation_history/`
4. `PatchToolCallsMiddleware`
5. `AsyncSubAgentMiddleware`, if configured
6. user middleware
7. harness profile extras
8. `SkillsMiddleware`
9. `AnthropicPromptCachingMiddleware` / `BedrockPromptCachingMiddleware`, automatic for Claude (`ttl="5m"`, overridable to `"1h"`)
10. `MemoryMiddleware`
11. `HumanInTheLoopMiddleware`
12. excluded-tool filter

`TodoListMiddleware` (`write_todos`) is opt-in from v0.7. [DA-OV]
Also free:
- large-result offload at 20k tokens [DA-CE]
- streaming with `stream.subagents` [DA-OV]
- `HarnessProfile` per-model prompt suffix and tool overrides via `register_harness_profile` [DA-CUST]
- structured output under `structured_response` [DA-CUST]
- `context_schema` runtime context that propagates to subagents [DA-CE]
- durable execution, HITL and checkpointing from LangGraph [DA-OV][LG-PERS]
Provider-agnostic: the operator can mix Claude and GPT per agent [DA-CMP][DA-SUB]. The Claude Agent SDK is Claude-only and leaves multi-tenancy for you to build. [DA-CMP]

### B2. Shape
```
Copilot (Deep Agent; model via ModelRouterMiddleware or @wrap_model_call; PostgresSaver; store)
 ├─ backend = CompositeBackend(
 │     default=StateBackend(),                                  # scratch, offloads, history
 │     routes={ "/memories/": StoreBackend(ns=quant/user),      # long-term memory
 │              "/skills/":   StoreBackend(ns=desk),            # admitted skills
 │              "/artifacts/": QmxArtifactBackend(read/write via policy hook),
 │              "/data/":     QmfDataBackend(read-only) })      # agent's own data view
 ├─ permissions = [deny write /memories/policy/**, deny write /data/**, ...]
 ├─ middleware = [ContextEditingMiddleware(ClearToolUsesEdit(...)), ModelFallbackMiddleware(...),
 │                ModelCallLimitMiddleware/ToolCallLimitMiddleware (budget), CodeInterpreterMiddleware(ptc=[safe read tools])]
 ├─ interrupt_on = {"promote_strategy": True, "publish_mini_app": {...,"when": by_type}, "eval": ...}
 ├─ subagents = [ research(model=fast, tools=web+docs MCP, skills=[...]),
 │                data_analyst(model=workhorse, backend=Python sandbox -> execute; RLM),
 │                lab(model=coding, tools=qmb MCP), verifier(model=other family, response_format=Verdict),
 │                CompiledSubAgent(name="backtest_pipeline", runnable=<LangGraph workflow>) ]
 └─ async subagents = [AsyncSubAgent(name="overnight_sweep", graph_id=..., url=None|remote)]
```

### B3. Thin glue QMX must add (and only this)
1. Domain tools: QMF/QMB/qmf-data wrappers that follow A5, with `response_format`, pagination and named results.
2. Custom backends: `QmfDataBackend` (read-only `BackendProtocol` over the data store) and `QmxArtifactBackend` (writes through a policy hook that does admission and journaling). [DA-BE]
3. Policy hooks (backend wrappers) for AD-22 admission, the AD-28 money-path barrier and journaling to AD-6. These are QMX invariants, not framework features.
4. Routing criteria: the ModelChoice criteria text written from QMX task analysis (A8).
5. Namespace factories: Quant/user/desk namespaces. [DA-LTM]
6. Prompts and skills: orchestrator delegation rules, effort scaling and domain skills.
7. Evals: golden tasks plus graders.
8. MCP Apps host bridge in the Copilot UI (F).

### B4. How an agent gets specific tools, MCPs and its own data
- Tools: declarative `SubAgent.tools`, which replaces inherited tools. MCP tools come from a dedicated `MCPAdapter` per server set. [DA-SUB][LC-MCP]
- Skills and instructions: `SubAgent.skills` and `system_prompt` (neither is inherited). [DA-SUB]
- Data: a route in `CompositeBackend` plus `permissions` scoped to that subagent. Subagent permissions replace the parent's. [DA-BE][DA-SUB]
- Model: `SubAgent.model`. Approval: `SubAgent.interrupt_on`. Output contract: `SubAgent.response_format`. [DA-SUB]
- Per-run identity and IDs: `context_schema`. Tools read `runtime.context`; `lc_agent_name` shows which subagent called. [DA-CE][DA-SUB]

### B5. Data-heavy path (RLM for backtests and market data)
- Option 1, recommended to try first: a `data_analyst` subagent on a sandbox backend (e.g. `DaytonaSandbox`, `E2BSandbox`, `ModalSandbox`, `LangSmithSandbox`, or a custom Docker backend implementing `SandboxBackendProtocol`). It gets `execute` and Python with pandas/DuckDB. Data is mounted read-only. The prompt is an RLM-style instruction: load the dataset as a variable, inspect shape, filter in code, call sub-LLMs only on slices, and return compact results plus an artifact path. [DA-CUST][DA-BE][RLM-P][A-MCPX]
- Option 2: wrap `rlms.RLM(environment="docker")` as a single tool `rlm_query(question, dataset_ref)`. This is paper-faithful and has its own JSONL trajectory log. [RLM-GH]
- Option 3, orchestration only: `CodeInterpreterMiddleware` plus `task()` fan-out, for example one subagent per instrument or per walk-forward fold. Coverage is guaranteed by code. [DA-DYN][L-RLM]
- Inference: QMA AD-14's "RLM kernel inside the worker's Docker container" maps to Option 1 or 2 without a custom kernel or wire.

---

## C. What NOT to build (QMA spine pieces a library already provides)

| QMA hand-rolled piece [QMA] | Off-the-shelf replacement | Keep as QMX glue |
|---|---|---|
| AD-12/13 Mission + Task Graph engine, Loop registry, Graph Template runtime | LangGraph `StateGraph` plus checkpointer; Deep Agents `task` and `CompiledSubAgent`; `write_todos` [DA-SUB][LG-PERS][DA-OV] | Acceptance criteria and verifier scripts |
| AD-29 continuation / `agent_stop`→`block_stop` | Progress artifact plus evaluator loop [A-LRH][A-HD]; LangGraph resume; cron through the LangSmith or own scheduler | The routine definitions (cron + IANA tz) |
| AD-10/11 hook registry (23 verbs × before/after, `HookResult` union) | LangChain middleware (`before_agent`, `wrap_model_call`, `wrap_tool_call`), `HumanInTheLoopMiddleware`, backend policy hooks, `permissions` [DA-CUST][DA-BE][LC-MW] | The few QMX invariants (admission, money path) as middleware or backend wrappers |
| AD-14 RLM kernel + `host_request` wire | Sandbox backend `execute`, or `rlms` DockerREPL; QuickJS interpreter for fan-out [DA-INT][RLM-GH] | Read-only data mounts |
| AD-15 Model proxy chain (ModelClass→Deployment→Credential Broker) selection logic | `init_chat_model` / `provider:model` strings, `ModelRouterMiddleware`, `@wrap_model_call`, `ModelFallbackMiddleware`, `ModelRetryMiddleware` [LC-MOD][LC-TS][LC-MW] | Tier criteria, credential lookup from Credential Manager |
| AD-16 Tool Registry + MCP adapter layer | `tools=` per agent/subagent, `MCPAdapter`, `LLMToolSelectorMiddleware`/`ProviderToolSearchMiddleware` [LC-MCP][LC-MW] | Desk/role → tool-list config |
| AD-17 ExecutionEnvironment / Docker-per-worker | Deep Agents sandbox backends (`SandboxBackendProtocolV2`) [DA-OV][DA-CUST] | Network allowlist policy |
| AD-18 MemoryProvider contract (propose/admit/recall...) | `memory=` AGENTS.md + `StoreBackend` + namespaces; Claude memory middleware [DA-LTM][LC-ANTH] | Admission policy hook |
| AD-20 Agent Bus (mailboxes) | Sync subagents (single handoff); `AsyncSubAgentMiddleware` start/check/update/cancel/list [DA-SUB][DA-ASYNC] | Operator approval queue = HITL interrupts surfaced in UI |
| AD-5 JSON-RPC daemon↔UI wire | LangGraph/Agent Server streaming API (threads, runs, streaming, webhooks, auth) [DA-CMP]; `useStream` frontend | UI contract for mini-app panels |
| AD-23 telemetry system | LangSmith tracing / OTel [L-ROUTER][DA-OV] | Domain metrics |
| Context Compiler, summarizer, large-result spill | `SummarizationMiddleware`, offload to `/large_tool_results/`, `ContextEditingMiddleware`, prompt caching [DA-CE][LC-MW] | Domain summary instructions |
| Custom skill loader | `SkillsMiddleware` (Agent Skills standard) [DA-CUST][A-SKL] | Skill content |
| Custom retry/budget logic | `ToolRetryMiddleware`, `ModelRetryMiddleware`, `ModelCallLimitMiddleware(thread_limit, run_limit)`, `ToolCallLimitMiddleware` [LC-MW] | Budget numbers (UI-editable) |

Keep as genuine QMX domain:
- the journal as evidence (AD-6), the ledgers (AD-9), the money-path barrier (AD-28) and the admission gate (AD-22)
- implemented as backend wrappers and middleware, not as a parallel runtime

Inference: the 2026-10-04 operator shift to LangGraph supersedes the QMA runtime ADs. This table says which invariants survive as glue.

---

## D. Anthropic-specific features usable from LangChain
- Prompt caching is automatic for Claude in Deep Agents. [DA-OV]
- Claude memory, text editor and bash tools have native middleware (`StateClaudeMemoryMiddleware`, `ClaudeBashToolMiddleware`, ...). [LC-ANTH]
- Server-side compaction (`compact_20260112`) and `clear_tool_uses_20250919` are Messages-API features [CB-CE]. Deep Agents uses its own summarization instead. Inference: do not stack both on one agent without testing.
- Tool Search / PTC / `input_examples` are Claude API betas (`advanced-tool-use-2025-11-20`) [A-ATU]. The LangChain equivalents are `ProviderToolSearchMiddleware` and the interpreter `ptc`. [LC-MW][DA-INT]

---

## E. CLIProxyAPI (router-for-me/CLIProxyAPI)

What it is [CPA]:
- A Go proxy exposing OpenAI (incl. Responses), Gemini and Claude-compatible endpoints.
- Upstreams include Codex (GPT) via OAuth, Claude Code via OAuth, Gemini CLI/AI Studio/Vertex, Grok and others.
- Supports multi-account round-robin load balancing, function calling, streaming and a reusable Go SDK.
- The README is heavily sponsored by API-relay and residential-proxy vendors.

How it would plug in [LC-MOD]:
- `init_chat_model(model=..., model_provider="openai", base_url="http://127.0.0.1:<port>/v1", api_key=<proxy key>)`, or `ChatAnthropic` pointed at its Claude-compatible endpoint. Each proxied model becomes one `ModelChoice` in the router.
- QMA AD-15 already restricts any such proxy to loopback with no QMA-held secrets. [QMA]

Terms-of-service facts:
- Anthropic: "OAuth authentication is intended exclusively for purchasers of Claude Free, Pro, Max, Team, and Enterprise subscription plans and is designed to support ordinary use of Claude Code and other native Anthropic applications." [CC-LEGAL]
- Anthropic again: developers building products "should use API key authentication", and Anthropic does not permit third parties "to route requests through Free, Pro, or Max plan credentials on behalf of their users". [CC-LEGAL]
- Anthropic "reserves the right to take measures to enforce these restrictions and may do so without prior notice". [CC-LEGAL]
- Advertised Pro/Max limits "assume ordinary, individual usage of Claude Code and the Agent SDK". [CC-LEGAL]
- The Agent SDK may not offer claude.ai login or rate limits for third-party products. [SDK-OV]
- Fact-based inference: routing a Claude subscription OAuth token through CLIProxyAPI into a LangChain agent is outside "ordinary use of Claude Code". It risks account action, and multi-account pooling compounds that risk. Secondary reports say server-side enforcement against non-Claude-Code OAuth use began in early 2026 (https://winbuzzer.com/2026/02/19/anthropic-bans-claude-subscription-oauth-in-third-party-apps-xcxwbn/). That claim is unverified against a primary source.
- OpenAI: ChatGPT plan usage can be shared with "eligible partner tools" through Sign in with ChatGPT and subscription sharing [OAI-PLAN]. A self-hosted proxy is not a listed partner. I did not find a primary OpenAI statement that explicitly permits or forbids proxying Codex OAuth, so treat it as unverified and grey.

Recommendation: API keys for Claude in the agent core. If the operator wants subscription use, the compliant route for Claude is the unmodified Claude Code binary (or the Agent SDK with an API key), not a proxy. [CC-LEGAL]

---

## F. MCP Apps as the way the Copilot builds, manages and renders mini apps

Spec facts [MCPA-SPEC][MCPA-OV][MCPA-BUILD]:
- Status: Stable as of 2026-01-26. Extension id `io.modelcontextprotocol/ui`. Optional and negotiated, with no core-MCP incompatibilities.
- Linkage: a tool declares `_meta.ui.resourceUri: "ui://..."`. The resource is HTML with MIME type `text/html;profile=mcp-app`, served as text or blob. The host may preload it before the call, so tool input can stream into the UI.
- `_meta.ui` fields: `csp` (connect/resource/frame domains), `permissions` (camera, mic, geolocation, clipboard-write), `domain`, `prefersBorder`, `visibility` (`["model"]`, `["app"]` or both). App-only tools are hidden from the model.
- View → host calls: `ui/initialize`, `tools/call` (same server only), `resources/read`, `ui/message`, `ui/update-model-context`, `ui/open-link`, `ui/request-display-mode` (inline/fullscreen/pip).
- Host → view notifications: `tool-input-partial`, `tool-input`, `tool-result`, `tool-cancelled`, `size-changed`, `host-context-changed` (theme, CSS variables, locale, dimensions), `ui/resource-teardown`.
- Security: views MUST render in sandboxed iframes. Default CSP is deny (`default-src 'none'`). The host enforces declared CSP, cannot loosen it, and logs every postMessage JSON-RPC message.
- Absent by design: view state persistence, view-to-view messaging, cross-server tool calls from a view, external-URL apps in the MVP.
- Server SDKs:
  - TypeScript: `registerAppTool`, `registerAppResource`, `RESOURCE_MIME_TYPE` from `@modelcontextprotocol/ext-apps/server`; client `App` with `connect()`, `ontoolresult`, `callServerTool()` [MCPA-BUILD]
  - Python: FastMCP 3.x `pip install "fastmcp[apps]"`, `app=True` tools, `FastMCPApp`, Prefab UI. Prefab has frequent breaking changes, so pin it. [FMCP-APPS]
- Host side: `@mcp-ui/client` React components, or the SDK's AppBridge (sandbox, message passing, tool proxy, CSP). `examples/basic-host` is a reference host. [MCPA-OV]
- Hosts today: Claude, Claude Desktop, VS Code Copilot, M365 Copilot, Goose, Postman, MCPJam, Archestra. [MCPA-OV]
- LangChain frontend: `experimental_useMCPApps` and `experimental_MCPApp` for `@langchain/langgraph-sdk/react` exist only in a draft, unmerged PR. Tool calls from a view route back through `mcpApps.callTool()`. [LGJS-2864]
- Skill: the `create-mcp-app` skill is published in `modelcontextprotocol/ext-apps`. [MCPA-BUILD]

Fit for QMX mini apps (inference, grounded in the facts above):
- Use it as the mini app's UI and transport contract. A mini app = an MCP server (Python FastMCP or TS) with tools, `ui://` panels and app-only tools for button actions. The Copilot is the MCP host: an `MCPAdapter` for tools, plus AppBridge/`@mcp-ui/client` in the QMX UI to render panels in sandboxed iframes. Benefits:
  - standard sandboxing and CSP
  - the same mini app renders in Claude Desktop or VS Code for free
  - an existing skill for the Copilot to scaffold apps unattended
- Building: the Copilot uses the `create-mcp-app` skill in a sandbox backend, builds a single-file HTML (vite-plugin-singlefile) and runs it against `basic-host` or QMX's own host as the "CI before live" step. HITL `publish_mini_app` gates registration. [MCPA-BUILD][DA-HITL]
- Managing: registered servers live in QMX config, and each subagent sees only its apps' tools (B4).
- Gaps QMX must fill:
  1. Persistent widget state. The spec has none, so state lives in the mini app's backend or DB and is re-read on `ui/initialize`.
  2. Dashboards outside chat. The spec targets in-conversation display; pinned dashboard placement is a QMX host decision (`displayMode` fullscreen/pip helps).
  3. App→app data flow (G3).
  4. Python Prefab instability.
  5. No merged LangGraph React support yet, so either build on AppBridge directly or track PR 2864.

---

## G. Delegation in depth (Copilot level) and app→app composition

G1. Delegation primitives (all verified):
- Sync declarative `SubAgent` [DA-SUB]:
  - required: `name`, `description`, `system_prompt`
  - optional: `mode` (`isolated` default or `fork`), `tools` (replaces inherited), `model`, `middleware`, `interrupt_on`, `skills`, `response_format`, `permissions`
  - returns one final report; stateless; no multi-message back-channel [DA-OV]
- `CompiledSubAgent(name, description, runnable=<compiled LangGraph graph>)`: yes, a Deep Agent can delegate to any compiled LangGraph workflow as a subagent through the same `task` tool. [DA-SUB]
- `AsyncSubAgent(name, description, graph_id, url?, headers?)`: a background task on an Agent Protocol server. In-process ASGI if `url` is omitted, HTTP if remote. Tools: `start_async_task`, `check_async_task`, `update_async_task`, `cancel_async_task`, `list_async_tasks`. The supervisor keeps chatting while work runs and can steer mid-task. [DA-ASYNC]
- Dynamic subagents: JS `task({description, subagentType, responseSchema})` from `CodeInterpreterMiddleware`. Hundreds of dispatches with guaranteed coverage. Bypasses HITL. [DA-DYN]
- The general-purpose subagent is auto-added. Disable it with `GeneralPurposeSubagentProfile(enabled=False)` and `subagents=[]`. [DA-SUB]
- Anthropic's equivalents and evidence: Research's lead/subagents and their weakness, where synchronous waits block steering [A-MARS]; coordinator plus cheap workers [CB-COORD]; advisor escalation [CB-ADV]; dynamic workflows of up to 16 concurrent and 1,000 agents per run, with the plan held in code [CB-DW].

G2. Copilot pattern for QMX (inference):
- Interactive turn: the Copilot uses sync subagents for quick isolated work (research, data look-ups).
- Long work (sweeps, mini-app builds, overnight missions): `AsyncSubAgent`, so the chat stays live. The UI shows `list_async_tasks` as a "jobs" panel, which matches the operator's "show where jobs run".
- Deterministic pipelines (e.g. ingest → backtest → tearsheet): a LangGraph `StateGraph` registered as a `CompiledSubAgent`. Keep LLM judgment out of fixed steps.
- Bulk coverage (every symbol, every fold): a dynamic-subagent workflow, with the `eval` tool gated.
- Escalation: `@wrap_model_call` advisor-style escalation, or a `reasoning_high` subagent consulted on irreversible decisions. [CB-ADV][LC-MOD]

G3. App→app and agent→agent output composition:
- MCP Apps forbids view-to-view and cross-server calls from a view [MCPA-SPEC]. Composition must therefore run through the host/agent or server-side.
- Pattern 1, artifact-by-reference: producers write outputs to a shared store path and return a reference; consumers read the path. [A-MARS][DA-BE]
- Pattern 2, schema contracts: `response_format` on subagents and `responseSchema` in `task()` give typed handoffs. [DA-SUB][DA-DYN]
- Pattern 3, server-side: mini app B is an MCP server whose tool takes A's artifact ref. The agent wires them in plain code (a dynamic workflow) or a LangGraph graph. [DA-DYN][DA-SUB]
- Pattern 4, `ui/update-model-context` lets a view push structured state to the agent, which can pass it to another app's tool. [MCPA-SPEC]
- Recommendation (inference): artifact refs in a typed QMX artifact store, plus JSON Schemas per mini-app output, plus agent-mediated wiring. No direct app-to-app bus.

---

## H. LangMem status
- Latest PyPI release: 0.0.30 on 2025-10-27, the 30th release. MIT licence. Python ≥3.10. [LMEM-PYPI]
- The repo is not archived. The last commits are dependency maintenance (2026-10-02 deps bump; 2026-09-09 "broadly modernize dependencies"). There has been no release in about 11 months. [LMEM-GH] (GitHub API checked 2026-10-07: archived=false.)
- APIs: `create_manage_memory_tool`, `create_search_memory_tool`, a background memory manager and LangGraph store integration. [LMEM-PYPI]
- Inference: maintained but dormant (0.0.x, no feature releases). LangChain's active memory path is Deep Agents `memory=` plus `StoreBackend`/`/memories/` [DA-LTM], and Managed Deep Agents v0.8 `/memories/agent/` and `/memories/user/` via `define_memory()` (https://www.langchain.com/blog/langsmith-managed-deep-agents-whats-new).
- Recommendation: do not build on LangMem. If background extraction is wanted, copy its pattern into a scheduled subagent writing to `/memories/`.

---

## I. Open risks and unverified items
- `ModelRouterMiddleware` is in `langchain_typesafe.experimental`. The API may change. [LC-TS]
- PTC and `task()` from the interpreter skip `interrupt_on`. A security review is required before giving the Copilot `eval`. [DA-INT][DA-DYN]
- `permissions=` does not cover sandbox `execute`. The sandbox boundary (network allowlist, read-only mounts) must carry that load. [DA-OV]
- The MCP Apps LangGraph React integration is a draft PR only. [LGJS-2864]
- LangGraph durability modes and `@task` details were not in the fetched page. Confirm before relying on idempotent side-effect replay. [LG-PERS]
- OpenAI's position on proxying Codex OAuth: no primary source found.
