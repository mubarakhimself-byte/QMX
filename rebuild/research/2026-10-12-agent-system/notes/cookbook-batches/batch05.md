# Batch 05 notes

Readers' context: QMX = Windows desktop quant workbench; agent layer = LangChain v1 + LangGraph + Deep Agents (Python). Copilots: general / Lab / Portfolio / background-workflow / server. Main model Claude Opus via proxy; cheap models (DeepSeek, GPT-mini) for background. Most of this batch is OpenAI cookbook content (Responses API / Agents API / Agents SDK / AgentKit); patterns are provider-agnostic and map onto LangGraph/DeepAgents. All mappings below are MY INFERENCE.

## PART A — INDEX

- claude-cookbooks/tool_use/tool_search_with_embeddings.ipynb — Client-side semantic tool search; one `tool_search` meta-tool returns `tool_reference` blocks on demand to scale to 1000s of tools, cutting context 90%+.
- claude-cookbooks/tool_use/tool_use_with_pydantic.ipynb — Validating Claude tool-call inputs/outputs with Pydantic models (Note/Author/response schemas) for type-safe tool use.
- claude-cookbooks/tool_use/vision_with_tools.ipynb — Vision + tool use: pass a base64 image, force a structured extraction tool (`print_nutrition_info`) to emit typed JSON.
- openai-cookbook/articles/chatgpt-agents-sales-meeting-prep.md — ChatGPT workspace agents: conversational builder, connectors w/ RBAC, skills, memory, scheduled runs, sharing (end-user vs agent-owned auth).
- openai-cookbook/articles/codex_exec_plans.md — PLANS.md/AGENTS.md "ExecPlan" format: self-contained living design docs enabling Codex multi-hour (7h+) autonomous runs.
- openai-cookbook/articles/per_run_spending_controller_responses_api.md — Per-run token budget controller: reserve worst-case cost before each call, settle actual, block run on overrun; exact `Fraction` math.
- openai-cookbook/examples/agent_optimization/optimizing_agents_for_cost_and_quality.ipynb — Measured cost/quality optimization sprint: prompt/tool/payload controls, model routing, prompt caching, workflow split, evals/guardrails/judge.
- openai-cookbook/examples/agentkit/agentkit_walkthrough.ipynb — AgentKit: Agent Builder (visual multi-agent canvas), ChatKit (embeddable chat), Evals (prompt optimization + trace grading), guardrails, widgets.
- openai-cookbook/examples/agents_api/apps/data_analyst/README.md — Data analyst agent: 4 tools, tool_search + programmatic_tool_calling, read-only SQL, app-owned cross-session memory, conversation-only session (no sandbox).
- openai-cookbook/examples/agents_api/apps/document_review/README.md — Multi-agent batch review: coordinator delegates to specialist subagents, mounted skill, read-only/writable mounts, validation, HITL approval kept in app.
- openai-cookbook/examples/agents_api/apps/document_review/skills/expense-review-policy/SKILL.md — Example agent skill (frontmatter name/description) defining AP policy, decimal arithmetic rule, decision enum, output JSON schema.
- openai-cookbook/examples/agents_api/apps/github_issues/README.md — Issue-webhook → sandboxed investigation agent; clones repo, runs tests, writes report, posts comment; app posts (not agent), disposable clone.
- openai-cookbook/examples/agents_api/apps/sev_bot/README.md — SRE incident agent: Slack-triggered, read-only evidence tools + GitHub/AWS MCP, HITL rollback approval via webhook, two-level incident memory, runbooks mounted.
- openai-cookbook/examples/agents_api/apps/sev_bot/runbooks/checkout-api.md — Sample runbook text (mitigation = rollback after approval, verification thresholds). Mostly content; minor agent relevance.
- openai-cookbook/examples/agents_api/apps/slack_bot/README.md — Slack bot agent: thread→session mapping, scoped Slack tools, MCP + vault credentials (static/OAuth refresh), steer/cancel, sandbox reuse.
- openai-cookbook/examples/agents_api/README.md — Index of Agents API apps + sandbox modes; SDK surface `client.beta.agents.sessions.stream()`, executor-key auth.
- openai-cookbook/examples/agents_api/sandboxes/docker/README.md — Docker application-managed sandbox pointer (build local executor image, run, clean up). Thin.
- openai-cookbook/examples/agents_api/sandboxes/e2b/README.md — E2B sandbox app-managed + webhook-managed modes; restricted executor key only inside worker. Thin.
- openai-cookbook/examples/agents_api/sandboxes/modal/README.md — Modal sandbox app-managed + webhook-managed; shared executor base image. Thin.
- openai-cookbook/examples/agents_api/sandboxes/README.md — Sandbox provisioning overview: app-managed vs webhook-managed, provider matrix (Blaxel/Cloudflare/Daytona/E2B/Modal/AWS/etc.).
- openai-cookbook/examples/agents_api/sandboxes/webhook_managed.md — Webhook-managed sandbox lifecycle: handler provisions/reconnects on `action_required`, agent-ID filtering, cleanup rules, worker TTLs.
- openai-cookbook/examples/agents_sdk/agent_improvement_loop.ipynb — Improvement flywheel: traces → human+LLM feedback → Promptfoo evals → HALO harness-optimizer → Codex handoff; finance diligence agent.
- openai-cookbook/examples/agents_sdk/app_assistant_voice_agents.ipynb — Voice agent: triage agent + handoffs to Search/Knowledge/Account agents; VoicePipeline STT→workflow→TTS; TTS instruction tuning.

## PART B — PATTERN NOTES

### claude-cookbooks/tool_use/tool_search_with_embeddings.ipynb
- Pattern: client-side semantic **tool search** / tool discovery to scale past ~100 tools; tools treated as discoverable resources instead of all front-loaded.
- Mechanism: single meta-tool `tool_search` given to Claude; its handler runs embeddings search and returns content blocks `{"type":"tool_reference","tool_name":...}` (references, not full defs).
- Beta header REQUIRED: `extra_headers={"anthropic-beta":"advanced-tool-use-2025-11-20"}` — enables tool definitions/references in tool results.
- Model `claude-sonnet-4-6`; embeddings via `sentence-transformers/all-MiniLM-L6-v2` (384-dim, local, normalized); cosine sim = dot product of normalized vectors; `top_k` default 5.
- `tool_to_text()` flattens name+description+params to a string for embedding; `np.argsort` top-k.
- Loop: start with only `tool_search`; on `stop_reason=="tool_use"` dispatch; discovered tools usable immediately mid-conversation; `tools=TOOL_LIBRARY+[TOOL_SEARCH_DEFINITION]`.
- Numbers: "cutting context usage by 90%+"; recommended when >20 tools; demo library 8 tools (weather+finance).
- Caveats: picks lightweight model for speed/accuracy tradeoff; suggests persisting embeddings to disk, hybrid BM25+semantic, caching frequent tools.
- Cited: docs.anthropic.com/en/docs/build-with-claude/tool-use (and #tool-search), sbert.net.
- QMX-fit: Lab + general copilot (QMX will have many broker/CCXT/indicator/workflow tools). LangChain/DeepAgents mapping: a retrieval-backed tool registry / dynamic tool binding middleware; equivalent to DeepAgents tool loadout gated by a search tool rather than binding all tools to the model (INFERENCE).

### claude-cookbooks/tool_use/tool_use_with_pydantic.ipynb
- Pattern: Pydantic validation layer around tool calls for type-safety/reliability.
- Mechanism: `BaseModel` classes `Author`(name,`EmailStr`), `Note`(note,author,tags,`priority=Field(ge=1,le=5,default=3)`,is_public), `SaveNoteResponse`; `process_tool_call` constructs validated model from `tool_use.input`.
- Model `claude-opus-4-8`; standard `client.messages.create(tools=...)`; two-turn loop: assistant tool_use → `tool_result` block `{"type":"tool_result","tool_use_id":...,"content":str(resp)}` back as user.
- install `'pydantic[email]'` for EmailStr.
- Caveat: tool `input_schema` JSON must mirror Pydantic constraints (minimum/maximum/default) so model emits valid shape.
- QMX-fit: all copilots (order tickets, note/memory writes, config edits). LangChain/DeepAgents mapping: LangChain tools defined with Pydantic `args_schema`; structured output / `with_structured_output`; validate before side-effect (INFERENCE).

### claude-cookbooks/tool_use/vision_with_tools.ipynb
- Pattern: vision + forced structured extraction — image in, typed JSON out via a tool.
- Mechanism: message content list mixes `{"type":"image","source":{"type":"base64","media_type":"image/png","data":...}}` + text; tool `print_nutrition_info` with integer props all `required`; read `response.content[-1]` when `stop_reason=="tool_use"`.
- Model `claude-opus-4-8`; base64-encode file bytes.
- Caveat: comment "No tool was called. This shouldn't happen!" — model may skip tool; no fallback shown.
- QMX-fit: Lab copilot (read chart screenshots, broker UI, PDF statements/nutrition-label analog = financial docs). LangChain/DeepAgents mapping: multimodal message + structured-output tool; no special equivalent beyond tool args_schema (INFERENCE).

### openai-cookbook/articles/chatgpt-agents-sales-meeting-prep.md
- Pattern: no-code **workspace agent** (hosted, scheduled, shareable) spanning connectors; evolution of GPTs. Not QMX's stack but strong product-shape reference for scheduled background agents + skills + memory.
- Mechanisms: conversational agent builder drafts profile/apps/skill/instructions; connectors w/ RBAC; per-connector permission scoping (read-only enforceable by admin); auth modes **End-user account** vs **Agent-owned account** (service account).
- Skills: "package instructions, resources, and scripts"; built on open-source **agent skills standard** (agentskills.io), portable across products; skill builder in-product.
- Memory: persistent per-user folder for notes/drafts/outputs across sessions; NOT shared across end users; user-viewable; user can inject guidance (e.g., ignore a meeting).
- Scheduling: `Schedule` → `Add new schedule` (e.g., daily 4pm, weekly Sunday); on-demand via @-tag; starter prompts configurable.
- Sharing: shareable link, duplicate/fork, company directory listing; agent-owned connector means sharees inherit that service account's access (security caveat).
- Caveats: admin gating of agents/publishing/apps; agent-owned SharePoint access propagates to anyone shared.
- Cited: agentskills.io/home; cdn.openai.com images only.
- QMX-fit: workflow/server agents (scheduled daily briefs, recurring research). LangChain/DeepAgents mapping: scheduled LangGraph run + checkpointer (per-user thread) + store (memory folder); skills ≈ DeepAgents skills/subagent instructions (INFERENCE).

### openai-cookbook/articles/codex_exec_plans.md
- Pattern: long-horizon autonomous coding via **ExecPlan** living design docs; `AGENTS.md` defines the "ExecPlan" shorthand (arbitrary term, not trained) and when to use it.
- Mechanism: single `md` fenced block; mandatory sections `Progress`(checkboxes w/ timestamps), `Surprises & Discoveries`, `Decision Log`, `Outcomes & Retrospective`, plus Purpose/Context/Plan of Work/Concrete Steps/Validation/Idempotence/Interfaces. Self-contained for a novice; no external links; define jargon inline.
- Recommended model `gpt-5.2-codex`; reported enabling "more than seven hours from a single prompt."
- Rules: acceptance stated as observable behavior (e.g., HTTP 200 body OK), not internal attributes; resolve ambiguity autonomously; commit frequently; idempotent/safe steps; prototyping milestones to de-risk.
- Caveats: compiles-but-does-nothing failure mode warned; don't outsource decisions to reader; each revision must stay self-contained.
- Cited: github.com/openai/agents.md.
- QMX-fit: factory lanes / background workflow + server agents (maps directly to QMX's ExecPlan-style autonomy, and to epic-factory). LangChain/DeepAgents mapping: DeepAgents write-the-plan-to-file + filesystem-backed todo/progress; LangGraph durable run with checkpointer resuming from the plan file (INFERENCE).

### openai-cookbook/articles/per_run_spending_controller_responses_api.md
- Pattern: **per-run cost control** / spend guardrail distinct from org/project limits; budget one task across many model calls.
- Mechanism: `RateCard`(prices per 1M tokens, max_input/output, verified flags) + `RunBudget`(maximum, spent, pending, `_holds`, `Lock`). Flow: `ensure_active` → count input tokens (`client.responses.input_tokens.count`) → `reserve` worst-case (max input price × tokens + max_output × output price) → `create` → `actual_cost(usage)` → `settle`; overrun/uncertain → `block()` permanently.
- Exact money via `fractions.Fraction`; require `OpenAI(max_retries=0)`; `store=False`; checks `response.model`/`service_tier` match; reasoning tokens already in output total.
- Example: $0.02 ticket budget; first reply $0.01, next worst-case $0.0146 > remaining $0.01 → stop; sample prices input $4 / cached $2 / cache-write $8 / output $20 per 1M.
- Caveats: lock is single-process only (multi-worker needs shared atomic store); hosted tools (web search) add separate charges; background requests return `queued`/`in_progress` needing separate tracking; `store=False` ≠ ZDR; alerts don't stop requests.
- Cited: developers.openai.com/api/docs/pricing, .../guides/prompt-caching, .../guides/spend-limits, github.com/openai/openai-python#retries.
- QMX-fit: Portfolio/Lab/background (Opus-via-proxy on subscription — cap per-run spend on cheap-model background work; critical for cost control). LangChain/DeepAgents mapping: callback/middleware wrapping each model call (BaseCallbackHandler token accounting) + a pre-model gate in LangGraph node raising to stop (INFERENCE).

### openai-cookbook/examples/agent_optimization/optimizing_agents_for_cost_and_quality.ipynb
- Pattern: repeatable **cost/quality optimization sprint** — measure baseline, change one knob, gate on quality before accepting savings. Deterministic dry-run (no API spend) + optional live.
- Optimization knobs (ordered): baseline → prompt/output controls → tool control → context hygiene → model routing → prompt caching → cache-aware context → split workflow → processing tier. "optimize per step, not globally."
- Mechanisms (Responses API): `reasoning={"effort":"low"}`, `text={"verbosity":"low"}`, `max_output_tokens` cap (includes reasoning tokens — watch incomplete), `tool_choice.allowed_tools` (keep full stable tool list, restrict per task → preserves caching), slim tool schemas + slim payloads, `truncation="auto"`, `context_management=[{"type":"compaction","compact_threshold":20000}]`, `parallel_tool_calls`.
- Model routing tiers: nano (triage/extraction/tags), mini (routine resolution), full (high-risk). GPT-5.4 family; GPT-5.6 Luna/Terra/Sol map to nano/mini/full.
- Prompt caching: `prompt_cache_key` (e.g. `support_order_status_v1`); stable prefix first, volatile ticket data last; `previous_response_id` carries state. GPT-5.6 bills cache writes (1.25× input) + explicit breakpoint `prompt_cache_breakpoint={"mode":"explicit"}`, `prompt_cache_options` ttl="30m"; 1024-token eligibility threshold; top-level `instructions` can't hold a breakpoint.
- Workflow split: keep classify/lookup/decide/respond synchronous; move QA/tags/summaries to Batch (`/v1/responses`, `completion_window="24h"`) / flex / background (background ≠ discount).
- Evals/guardrails: hard gates (policy, action, escalation, security) before cost/latency; deterministic phrase checks + LLM `llm-rubric` judge (fixed `gpt-5.4-mini`, threshold 0.7/0.8); judge never overrides deterministic fail; inspect full trajectory not final answer.
- Numbers/formulas: `blended cost per verified resolution = total (model+tool+infra+retry+human+escalation+rework) / verified resolutions`; example 0.02/50% = 0.04 vs 0.03/90% = 0.033 per resolution; usage fields `input_tokens_details.cached_tokens`, `output_tokens_details.reasoning_tokens`.
- Caveats: dry-run numbers not a benchmark; literal-phrase checks reject paraphrases; cache misses on large prefixes add latency; over-escalation hurts; cost-only tuning removes safeguards.
- Cited: developers.openai.com docs for responses/function-calling/prompt-caching/compaction/cost-optimization/batch/flex/agent-evals/evaluation-best-practices; openai.com/index/managing-ai-investments-in-agentic-era, .../a-scorecard-for-the-ai-age.
- QMX-fit: ALL copilots + background (direct cost playbook for Opus-proxy + cheap-model split). LangChain/DeepAgents mapping: model routing = conditional LangGraph edges / per-node model binding; caching = provider cache + stable system prefix; split = separate async subgraph / background worker; judge = LangSmith/evals node (INFERENCE).

### openai-cookbook/examples/agentkit/agentkit_walkthrough.ipynb
- Pattern: end-to-end visual multi-agent build/deploy/optimize. Three sequential Agent nodes (resume extract → career gap analysis → course recommend).
- Mechanisms: **Agent Builder** drag-drop nodes, structured output (JSON schema per node), context vars `{{workflow.input_as_text}}`/`{{input.output_text}}`, reasoning `minimal`/`low`, Web Search tool node, **Guardrail** node (PII) inserted between agents, Widget output format (.widget file). Publish → versioned workflow ID.
- **ChatKit**: embeddable web component; starter template env `NEXT_PUBLIC_CHATKIT_WORKFLOW_ID`; theme via `lib/config.ts`; Widget Builder for custom result rendering. Export to **Agents SDK** (Python/JS) to self-host.
- **Evals**: single-node prompt optimization (upload dataset, Generate output, human annotations thumbs+text, model graders relevance/coverage/summary w/ 0.7 threshold, click **Optimize** to auto-rewrite prompt → **Update** back into Builder); **trace grading** across full multi-agent workflow (graders spanning nodes, e.g. output3 vs input1; conditional/loop behaviors like "escalate within 3 responses").
- Caveats: self-hosting via SDK loses integrated AgentKit benefits; examine failure examples before trusting auto-optimize.
- Cited: openai.com/index/introducing-agentkit, platform.openai.com docs (agent-builder/chatkit/evals), github.com/openai/openai-chatkit-starter-app, openai-agents-js/-python, chatkit.studio, cookbook eval_driven_system_design.
- QMX-fit: Lab copilot (mini-app/workflow building) + general (chat UI shape). LangChain/DeepAgents mapping: Agent Builder graph ≈ LangGraph StateGraph; guardrail node ≈ middleware/interrupt; structured output = with_structured_output; trace grading ≈ LangSmith evals over run traces (INFERENCE).

### openai-cookbook/examples/agents_api/apps/data_analyst/README.md
- Pattern: conversational **data analyst agent**, multi-query investigations in one session, app-owned DB access; tool_search + programmatic tool calling.
- Tools (4): `search_tables`, `search_context` (metrics/queries/docs/memories), `query_warehouse` (read-only, ≤100 rows), `save_memory` (scope personal/team, `defer_loading=True` — discovered via `tool_search`). Also `{"type":"tool_search"}` and `{"type":"programmatic_tool_calling","enabled":True}`.
- Session: `client.beta.agents.sessions.create(agent={model:"gpt-5.6-luna",instructions,reasoning:{effort:"high"},tools}, environment={"type":"none"}, input=..., stream=True)` — conversation-only, NO sandbox.
- Flow: read `agent.session.created` for `session.id`; on `agent.session.requires_action` dispatch each function call → `sessions.events.create(events=[{type:"agent.session.input.tool_result",turn_id,call_id,success,output}])`; dedup by turn+call ID. Follow-up: `sessions.stream(session_id, input, tool_handlers=handlers)` (SDK auto-dispatches handlers). Map `conversation_id`→session for continuation.
- Memory: cross-session is app-owned in `memories.json` (move to DB for multi-user); `save_memory` only on explicit user request.
- Context grounding: discover real schemas, business context (metric defs w/ filters, query_history of reviewed SQL), expose SQL; model never sees `WAREHOUSE_URL`.
- Caveats: read-only DB role + query timeout + show every query; derive analyst identity from auth not request body; narrative is a conclusion to verify against records.
- Cited: openai.com/index/inside-our-in-house-data-agent; GitHub source files.
- QMX-fit: Lab + Portfolio copilot (query market/portfolio warehouse, save corrections). LangChain/DeepAgents mapping: LangGraph agent w/ SQL tools + checkpointer (session) + store (memories.json→store); human-authored metric context = retrieved docs; interrupt not needed (read-only) (INFERENCE).

### openai-cookbook/examples/agents_api/apps/document_review/README.md
- Pattern: **multi-agent** coordinator→specialist batch review over a mounted workspace + mounted **skill**; HITL approval retained in app.
- Mechanism: `multi_agent={"enabled":True,"max_concurrent_subagents":4}`; coordinator delegates each doc to a specialist; `environment={"type":"self_hosted","workspace_directory":"/workspace","capability_directories":["/workspace/skills"]}`; specialists discover `$expense-review-policy` skill; write `/workspace/output/<stem>.json` + coordinator writes `summary.json`.
- Mounts: input + `skills/` read-only, only output writable; outputs persist on host after sandbox exits. Executor runs `codex exec-server`; only `OPENAI_EXECUTOR_API_KEY` enters sandbox (as `CODEX_API_KEY`).
- Events: `agent.session.subagent.created`, `agent.session.turn.output_text.delta`, failure events; app validates every source doc has a report (enabling multi-agent ≠ proof work delegated).
- Validation: recompute invoice total from line items (decimal); cannot prove extraction matched source → human still reviews; sample invoice should flag $900 overcharge / missing PO / changed bank details.
- Activity audit: `sessions.subagents.list` + `subagents.items.list` for `command_execution` items (null subagent = coordinator); from retained API history, not a full security audit; protect like reports.
- Caveats: instructions not to edit ≠ filesystem boundary (use disposable mounts/roles); reserved names `summary`/`review-activity`; keep approval in app — agent never pays/signs.
- QMX-fit: workflow/server agents (batch doc/statement review, compliance). LangChain/DeepAgents mapping: DeepAgents subagents + shared filesystem workspace; skill = DeepAgents skill; approval = LangGraph `interrupt` (INFERENCE).

### openai-cookbook/examples/agents_api/apps/document_review/skills/expense-review-policy/SKILL.md
- Pattern: concrete **agent skill** file (open skills standard) — frontmatter `name` + `description`, markdown body = policy/procedure.
- Mechanism: discovered as `$expense-review-policy`; prescribes exact method: read all line items, use `decimal.Decimal`, compare computed vs printed subtotal+shipping, strip separators, report exact difference; decision enum `needs_info`/`escalated`/`ready_for_approval`; mandated output JSON fields (document, document_type, policy_id `AP-104`, decision, vendor, amount, issues[plain strings], recommendation, calculation{line_items,shipping,calculated_total,difference}).
- Rule: never approve payments/sign/external actions; only coordinator writes summary.json.
- QMX-fit: Portfolio/Lab (encode risk/sizing or review policy as a skill — note QMX risk authority lives in GitBook/node docs). LangChain/DeepAgents mapping: DeepAgents SKILL.md loaded by subagent; equivalent to a system-prompt fragment + output schema contract (INFERENCE).

### openai-cookbook/examples/agents_api/apps/github_issues/README.md
- Pattern: **webhook-triggered sandboxed investigation agent** (no human opens a chat); reproduce bug, report findings, post comment.
- Mechanism: verify GitHub signature + dedup `X-GitHub-Delivery`; accept `issues.opened`; clone repo to temp dir (`GITHUB_TOKEN` via subprocess env, not in URL); session `agent={model:"gpt-5.6-sol",reasoning:{effort:"high"}}`, `environment={"type":"self_hosted","workspace_directory":"/workspace"}`; executor mounts checkout rw; agent writes `/workspace/investigation.md`; app posts comment (not an agent tool), credentials only to `https://api.github.com/`.
- Events via `sessions.stream`: `turn.output_text.delta` + failure set; read report file after turn.
- Caveats: "instructions not to edit source are not a filesystem permission boundary" → disposable clone; validate repo access before processing untrusted issue content; check actual test output before trusting diagnosis; persist delivery IDs + durable queue for retries; to extend to a fix agent add explicit approval before PR.
- QMX-fit: server/background workflow agent (maps to QMX factory lanes / CI investigation). LangChain/DeepAgents mapping: LangGraph background run triggered by webhook; disposable git worktree ≈ QMX worktree lanes; interrupt before any write (INFERENCE).

### openai-cookbook/examples/agents_api/apps/sev_bot/README.md
- Pattern: **SRE incident-response agent**, Slack-triggered, multi-agent, read-only evidence + MCP tools, **HITL rollback approval**, two-level memory, runbooks mounted. Richest HITL + MCP example in batch.
- Mechanism: session `model:"gpt-5.6-sol"`, `reasoning:{effort:"high"}`, `multi_agent={"enabled":True,"max_concurrent_subagents":3}`, tools = `configured_tools()`; `environment` self_hosted + runbooks mounted read-only at `/workspace/runbooks/<service>.md`.
- Tools: `get_service_evidence`, `recall_incidents` (auto handlers); `propose_rollback` deliberately has NO handler → stays pending for human. Read-only tools run through streaming handler.
- HITL via webhook: register project webhook for `agent.session.action_required` (+ `agent.session.failed`); on delivery verify OpenAI signature, retrieve `required_actions`, post Slack buttons; return decision with `sessions.events.create(events=[{type:"agent.session.input.tool_result",turn_id,call_id,success,output:json({"decision":"approved","executed":False})}])`. Approval records decision, never executes deploy.
- MCP: GitHub read-only `https://api.githubcopilot.com/mcp/readonly` allowlist 5 tools (`list_commits`,`get_commit`,`list_pull_requests`,`pull_request_read`,`get_file_contents`); AWS DevOps MCP `{"type":"mcp","server_label":"aws_devops","connection_origin":"service","transport":{"type":"http","server_url":...,"authorization":"Bearer ..."}}`. Agents API calls MCP directly, no app handler; if MCP can't connect session fails (no silent skip).
- Skills: AWS Agent Toolkit skills installed into image via `npx --yes skills add aws/agent-toolkit-for-aws/skills --agent codex --copy`; copied to `/workspace/.agents/skills` for auto-discovery; skills = instructions not credentials.
- Memory: within-incident (alert fingerprint→session+thread+sandbox, follow-ups retain evidence) + across-incident `recall_incidents` over `incident_memory.json` (atomic save, git-ignored, single-process not shared DB).
- Caveats: approval ≠ execution; only resolved-incident history survives restart (active threads/approvals in memory); verify PagerDuty/incident.io signatures at ingress; alert fingerprints dedup.
- Cited: github.com/github/github-mcp-server, github.com/aws/agent-toolkit-for-aws.
- QMX-fit: server/background workflow agent (ops/monitoring of the trading node + HITL for risky actions — strong analog to "liveness heartbeat" + rollback). LangChain/DeepAgents mapping: LangGraph `interrupt` for propose_rollback; MCP tools via langchain-mcp adapters; memory = store + checkpointer; subagents = DeepAgents (INFERENCE).

### openai-cookbook/examples/agents_api/apps/sev_bot/runbooks/checkout-api.md
- Mostly sample content; minor agent relevance. Shows runbook files are mounted plain markdown the agent reads for mitigation/verification; records approval but does not execute rollback; verification = error rate <1%, p95 <400ms on fresh evidence.
- QMX-fit: workflow agent (mount QMX operational runbooks read-only). LangChain/DeepAgents mapping: retrieved/mounted doc, no code equivalent (INFERENCE).

### openai-cookbook/examples/agents_api/apps/slack_bot/README.md
- Pattern: **conversational agent per Slack thread**, scoped tools, MCP + credential **vault**, steer/cancel, sandbox reuse across turns.
- Mechanism: thread key `team:channel:thread_ts` → session; Socket Mode (no public webhook); session `model:"gpt-5.6-sol"`, `reasoning:{effort:"medium"}`, `multi_agent` enabled (3 subagents), `vault_ids=[...]`; start `codex exec-server` container (`--remote`, `--environment-id`), only `CODEX_API_KEY` inside.
- Scoped app tools (4): `search_slack_messages`,`read_slack_channel`,`find_teammate`,`list_slack_files` — bound to triggering channel, not model-selected; search is recent history not whole workspace.
- Streaming: `sessions.stream(session_id, input, tool_handlers=slack_handlers(...))` — SDK runs function handlers, Agents API runs MCP tools; use `turn.item.added` + `subagent.created` to update ONE progress message.
- Steer/cancel mid-turn: `events.create(events=[{type:"agent.session.input.message",input:[{role:"user",content:[{type:"input_text",text:...}]}]}])`; cancel = `{"type":"agent.session.input.cancel"}` (ends turn not conversation).
- Vault credentials: `vaults.create` + `vaults.credentials.create(auth={"type":"static_bearer","mcp_server_url":...,"token":...})`; tool def holds only server URL. MCP servers: Notion `https://mcp.notion.com/mcp`, Google Drive `https://drivemcp.googleapis.com/mcp/v1`, GitHub `https://api.githubcopilot.com/mcp/`. OAuth refresh: `mcp_oauth` credential (client id/secret/refresh/expiry) — Agents API refreshes token, app owns initial consent.
- Caveats: shared vault = everyone using bot shares those connections (scope accordingly); Notion hosted MCP needs OAuth not integration secret; persist session/sandbox/thread maps for restart survival; add expiry policy for long-running bot.
- QMX-fit: general copilot (chat host) + Lab (investigate/prepare changes). LangChain/DeepAgents mapping: checkpointer keyed by thread; MCP adapters; `interrupt`/streaming for steer-cancel; secrets vault = external secret store (QMX uses Windows Credential Manager) (INFERENCE).

### openai-cookbook/examples/agents_api/README.md
- Pattern: index + minimal Agents API surface. Two provisioning modes: application-managed vs webhook-managed sandboxes.
- Mechanism: `client.beta.agents.sessions.create(agent={"model":"gpt-5.6-sol"}, environment={"type":"self_hosted","workspace_directory":"/workspace"})`; sandbox starts `codex exec-server` with `session.environment.id` + `.remote_url`; `AsyncOpenAI` same API with await. SDK `openai>=3.13.0`; apps need Python 3.14.
- Auth: separate restricted `OPENAI_EXECUTOR_API_KEY` needing `api.agents.environments.connect` + IP restrictions allowing sandbox outbound.
- Cited: developers.openai.com agents-api overview / self-hosted / lifecycle.
- QMX-fit: server/background workflow agents (remote long-running). LangChain/DeepAgents mapping: no direct OpenAI equivalent — but conceptually LangGraph Platform/remote deployment + sandboxed tool executor (INFERENCE).

### openai-cookbook/examples/agents_api/sandboxes/README.md
- Pattern: sandbox provisioning modes + provider matrix. App-managed (app starts/stops compute directly, no webhook) vs webhook-managed (deployed handler provisions/reconnects on OpenAI webhook). Both run agent in OpenAI cloud, connect sandbox via `codex exec-server`.
- Providers: Blaxel, Cloudflare, Daytona, DigitalOcean, Docker (app-managed only), E2B, Modal, AWS Lambda MicroVMs, OCI, Runloop, Vercel. One mode per session; deleting API session ≠ stopping provider compute.
- QMX-fit: server/background workflow agents. LangChain/DeepAgents mapping: pluggable sandbox backend for tool/code execution (INFERENCE).

### openai-cookbook/examples/agents_api/sandboxes/docker/README.md
- Thin pointer: Docker app-managed example only (build local executor image, run task, clean up container+session); no webhook controller. Agent-relevant as deployment option.
- QMX-fit: local dev of server/workflow agents on the Windows box. LangChain/DeepAgents mapping: local container tool executor (INFERENCE).

### openai-cookbook/examples/agents_api/sandboxes/e2b/README.md
- Thin: E2B app-managed + webhook-managed; `sandbox.py` installs/launches executor; workers get only restricted executor key, app creds stay out. Webhook mode resumes paused workers on connection need.
- QMX-fit: server/background agents (hosted sandbox option). LangChain/DeepAgents mapping: remote sandbox executor (INFERENCE).

### openai-cookbook/examples/agents_api/sandboxes/modal/README.md
- Thin: Modal app-managed + webhook-managed; `modal_executor.py` base image + executor command; app adds its tools/sample file; webhook controller packages shared source; only restricted executor key reaches sandbox.
- QMX-fit: server/background agents. LangChain/DeepAgents mapping: remote sandbox executor, named sandbox reconnect (INFERENCE).

### openai-cookbook/examples/agents_api/sandboxes/webhook_managed.md
- Pattern: **webhook-managed** long-running sandbox lifecycle — handler in provider account starts/reconnects sandbox; app client imports no provider SDK.
- Mechanism: create agent `client.py --create-agent`, set `OPENAI_AGENT_ID` (handler filters by agent id — ignores other agents' sessions); subscribe webhooks `agent.session.action_required` + `agent.session.failed` + signing secret `OPENAI_WEBHOOK_SECRET`; new input to offline executor triggers `environment_connection` action → handler resumes/replaces sandbox.
- Credentials: `OPENAI_API_KEY` (app+controller), `OPENAI_EXECUTOR_API_KEY` (per worker as `CODEX_API_KEY`), `OPENAI_WEBHOOK_SECRET` (controller verify). Both keys same org/project/owner.
- Lifecycle: OpenAI waits ≤5 min for executor, client 10-min HTTP timeout; workers 30-min default lifetime/timeout (can interrupt a turn — raise limits); E2B refreshes timeout on reconnect, Daytona TTL from creation; replacing a sandbox does NOT restore files or replay commands. No session-deletion webhook — must stop provider compute AND delete API session (`client.py --delete`); remove webhook before retiring controller.
- Caveats: one handler per agent id; don't let multiple handlers provision same session; "these examples do not shut down on `idle`"; need durable controller hosting + queue for production.
- Cited: developers.openai.com/.../environments/lifecycle, uv docs.
- QMX-fit: server/background workflow agents (QMX node on remote VPS — reconnect model fits a long-running node). LangChain/DeepAgents mapping: durable LangGraph deployment + checkpointer for resume; webhook = external trigger; no file persistence across sandbox replacement → rely on checkpointer/store (INFERENCE).

### openai-cookbook/examples/agents_sdk/agent_improvement_loop.ipynb
- Pattern: **agent improvement flywheel** — traces → human+LLM feedback → generated evals → optimizer → coding-agent handoff. "harness" = full contract (instructions, tools, routing, output reqs, validation). Agent = financial **diligence analyst** (quant-adjacent).
- Components: OpenAI Agents SDK agent (`SandboxAgent`, `Runner`, `Manifest`/`LocalDir`/`Dir` mounts, `UnixLocalSandboxClient`, `set_trace_processors`, `trace`, `custom_span`); models `gpt-5.5`; reasoning effort via `Reasoning(effort=...)`.
- Harness as data: `@dataclass AgentConfig`(version, system_prompt, model_settings, tool_policy, eval_metadata) — makes optimization target more than prompt wording. Required artifacts enforced: summary_answer.md, investment_memo.md, risk_register.json, open_questions.md, citations.json, evidence_table.csv.
- In-workspace validation tools: `check_evidence_coverage.py` (claims cite real files), `validate_output_contract.py` (artifacts exist/shape) — agent must run before finalizing; "if evidence conflicts, state the conflict explicitly instead of reconciling silently"; never fabricate numbers.
- Traces: custom `HaloJsonlTraceProcessor` exports SDK spans → OpenTelemetry-style JSONL (observation kinds AGENT/LLM/TOOL/CHAIN/GUARDRAIL); local exporter only (hosted ingestion may be unavailable for ZDR orgs).
- Feedback → evals: LLM generates **Promptfoo** eval defs (`scoring_method` deterministic/llm_judge/hybrid; `deterministic_assertions` limited to contains/icontains/not-contains; `llm-rubric` judge threshold 0.8). Gate run via `npx promptfoo@0.121.9 eval`.
- Optimizer **HALO** (Hierarchical Agent Loop Optimization, github.com/context-labs/halo): reasons over harness config + traces + feedback + evals + gate results → ranked harness changes → writes `codex_handoff.md` (fixed section order incl. Behavior contract/Runtime implementation/Output contract/Observability+evals). HALO uses subagents (`maximum_depth=1`, `maximum_parallel_subagents=2`, compaction model temp 1.0 — GPT-5 rejects temp 0.0).
- Operating modes: reviewed loop (human approves diff) vs closed loop (Codex automation w/ heartbeat polls for new handoffs, auto PR/merge/deploy). Human gates optional at trace review / eval refinement / PR / merge / deploy.
- Numbers: 5 default traces (~20 min run); steps 3 (agent runs) + 7 (HALO) longest.
- Caveats: live-only notebook; literal assertions miss paraphrases; humans should vet generated evals before trusting as gate; HALO/components evolving.
- Cited: promptfoo.dev, github.com/context-labs/halo.
- QMX-fit: Lab + background (self-improvement of QMX agents; finance-diligence shape ≈ QMX research/analysis; Codex-handoff ≈ QMX factory lane). LangChain/DeepAgents mapping: LangSmith traces + datasets/evaluators ≈ traces+Promptfoo; HALO ≈ a meta-optimizer subagent over LangGraph run history; checkpointer for resume; grader nodes (INFERENCE).

### openai-cookbook/examples/agents_sdk/app_assistant_voice_agents.ipynb
- Pattern: **multi-agent triage + handoff** turned into a **voice agent** (STT→workflow→TTS). Triage routes to Search/Knowledge/Account specialists.
- Mechanism (Agents SDK): `Agent(name, instructions, tools, handoffs=[...])`; built-in `WebSearchTool()`, `FileSearchTool(max_num_results=3, vector_store_ids=[...])` (RAG over OpenAI-managed vector store), custom `@function_tool` (`get_account_info`); triage uses `prompt_with_handoff_instructions(...)`; `Runner.run(agent, query)`; `trace("...")` + Traces dashboard.
- Voice: `VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent))`, `AudioInput(buffer=recording)`, stream `voice_stream_event_audio` chunks; `sounddevice` mic I/O; install `openai-agents[voice]`.
- TTS tuning: default model `gpt-4o-mini-tts`; `TTSModelSettings(instructions=...)` controls personality/tone/pronunciation/tempo/emotion; common `voice_system_prompt` added to each agent for short, plain, spoken-friendly output (1–2 sentences/step).
- Vector store setup: `client.vector_stores.create` + `vector_stores.files.create`; or platform UI.
- Caveats: naive text→voice conversion sounds robotic — must re-prompt for voice format + TTS instructions; evaluate traces before scaling.
- Cited: openai-agents-python docs (quickstart/voice/tools), cookbook responses_example + file_search_responses.
- QMX-fit: general copilot (optional voice entry point) + Lab (RAG over QMX docs via file search). LangChain/DeepAgents mapping: triage+handoff ≈ LangGraph supervisor / router edges to specialist subgraphs; FileSearchTool ≈ LangChain retriever tool over a vector store; voice = external STT/TTS wrapper, no core LangGraph change (INFERENCE). Note: QMX memory says own-SDK dropped, agents on LangChain/LangGraph; voice is "voice-if-agentic" only.
