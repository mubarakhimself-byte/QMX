# Batch 07 notes — cookbook reader/extractor

Repo note: every listed file is `openai-cookbook`. Reader: one of 13 feeding the QMX findings report.

## PART A — INDEX

- openai-cookbook/examples/audio/voice_agent_evaluation.md — GPT-Live full-duplex voice-agent eval harness; crawl/walk/run modes, deterministic+LLM-judge graders, task/audio/consumption metrics. (agent-relevant: voice-if-agentic, evals)
- openai-cookbook/examples/batch_processing.ipynb — Batch API async bulk jobs (jsonl tasks, 24h window, lower price); movie categorization + image captioning. (agent-relevant: cost control / background bulk)
- openai-cookbook/examples/book_translation/translate_latex_book.ipynb — Chunk-and-translate a LaTeX book via gpt-4o; token counting, chunk grouping, ThreadPoolExecutor parallelism. (marginal: chunking + parallel fan-out pattern only)
- openai-cookbook/examples/Build_a_coding_agent_with_GPT-5.1.ipynb — Coding agent on Agents SDK with shell, apply_patch, web_search, Context7 HostedMCPTool; streamed run loop, approval gates. (agent-relevant: coding agent / copilot)
- openai-cookbook/examples/chatgpt/daily_usage_limits/docs/codex.md — Pilot guide: run a usage-budget controller via Codex + scheduled task, synthetic rehearsal then live apply. (agent-relevant: scheduled/long-running agent, HITL gating)
- openai-cookbook/examples/chatgpt/daily_usage_limits/README.md — ChatGPT Admin API usage-budget releaser (credits/USD, fixed_release policy, PATCH override); local sim → managed infra. (marginal: scheduled automation + admin API; not LLM-agent core)
- openai-cookbook/examples/chatgpt/workspace_agents/workspace-agents-api-trigger.ipynb — Fire a saved Workspace Agent from an API trigger (`agtch_` id, 202 async, idempotency/conversation keys). (agent-relevant: external trigger of managed agent)
- openai-cookbook/examples/codex/Autofix-github-actions.ipynb — (ARCHIVED) GitHub Action auto-fixes failing CI via codex-action + opens PR. (agent-relevant: CI autofix / background coding agent)
- openai-cookbook/examples/codex/build_code_review_with_codex_sdk.md — (ARCHIVED) Self-hosted Codex code review via `codex exec` headless + structured-output JSON schema, posts inline comments to GitHub/GitLab/Azure/Jenkins. (agent-relevant: reviewer, structured outputs)
- openai-cookbook/examples/codex/Build_iterative_repair_loops_with_Codex.ipynb — Closed-loop review→repair→validate agent with structured handoffs, `record.json` audit trail, stop conditions. (agent-relevant: iterative repair loop, evals, QMX factory-fit)
- openai-cookbook/examples/codex/code_modernization.md — 5-phase COBOL→modern migration via Codex CLI + ExecPlan/AGENTS.md/PLANS.md docs and parity tests. (agent-relevant: planning harness, modernization)
- openai-cookbook/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk.ipynb — (ARCHIVED) Codex CLI as MCP server (`codex mcp-server`), single + gated multi-agent orchestration via Agents SDK handoffs + Traces. (agent-relevant: multi-agent, MCP, observability)
- openai-cookbook/examples/codex/data/docs/getting_started_evals_pre_repair.ipynb — Tiny stale Evals fixture (gpt-3.5-turbo, oaieval CLI) used as repair-loop target. (fixture; marginal)
- openai-cookbook/examples/codex/data/docs/knowledge_retrieval_pre_repair.ipynb — Tiny stale function-calling retrieval fixture (gpt-4-turbo-preview, legacy functions schema). (fixture; marginal)
- openai-cookbook/examples/codex/data/docs/qdrant_embeddings_search_pre_repair.ipynb — Tiny stale Qdrant vector-search fixture (ada-002, .search vs .query_points). (fixture; marginal)
- openai-cookbook/examples/codex/iterating-development-workflows-with-codex.md — Repo "harness" convention (AGENTS/PLANS/GOALS/PROMPTS + harness/build, context, build-log) and a reusable harness-author skill + retrospective. (agent-relevant: planning harness, skills, audit discipline)
- openai-cookbook/examples/codex/jira-github.ipynb — Label-a-Jira-issue → GitHub Action runs `codex exec` → opens PR → transitions/annotates Jira via REST. (agent-relevant: event-triggered background coding agent)
- openai-cookbook/examples/codex/secure_quality_gitlab.md — (UPDATE NOTE) Codex CLI in GitLab CI emits CodeClimate code-quality JSON + post-processes SAST into ranked remediation + validated git patches. (agent-relevant: reviewer, security, structured outputs)

## PART B — PATTERN NOTES

### openai-cookbook/examples/audio/voice_agent_evaluation.md
- Pattern: continuous evaluation of a full-duplex voice agent ("GPT-Live") as prompts/tools/models evolve; voice-if-agentic.
- Two-tier architecture: `gpt-live-1` voice frontend conducts conversation and decides whether to answer directly or **delegate**; a reasoning backend does tool-calling + state updates. Two delegation modes: Responses delegation (service supplies context) vs client delegation (app supplies context).
- Three eval modes, increasing complexity: CRAWL (synthetic TTS audio, single-turn, baseline), WALK (saved recorded audio + acoustic presets, single-turn), RUN (independent simulated caller, continuous multi-turn full-duplex).
- Minimal mechanism: scenarios in `scenarios.json` with `input.text`, `input.context.summary`, `input.context.history`; evaluator-only `expected.tools.required` (ordered), `expected.procedure.steps[]` with `critical: true` to gate RUN completion.
- Grading = deterministic checks (tool calls, args, authorization, app state, audio timing) + independent LLM judge (semantic quality, partial credit). Task completion is the guiding pass/fail.
- WALK acoustic presets: `clean, noisy, telephony, background_speech, echo, packet_loss, realistic`.
- RUN: simulated caller has own GPT-Live frontend + lightweight managed Responses backend (`gpt-5.6-luna`, low effort), no tools; audio in 20ms frames, default `tick_ms`=200ms reporting interval, 400ms playback reserve.
- Numbers (one recorded run): 42.34s 24kHz stereo; task completion passed; semantic 90%; tool accuracy 50% (1 of 2 expected); delegation accuracy 100% (2 vs 1 expected); response latency 1.513s; response rate 75% (scoring artifact counted farewell twice); interruption 0%; backend `gpt-5.6-terra` 2374 in / 105 out / 2479 total tokens. Report P50/P90 across repeated runs (nondeterministic).
- Consumption tracked separately: frontend `usage.seconds` (no frontend token counts reported by API), backend input/output/reasoning/caching.
- Caveats: API emits no authoritative turn/audio-done events — completion inferred from quiet tail; a valid answer sharing an earlier caption group can time out; output audio events carry no timestamps (local playback timeline used); diagnose infra/grader vs assistant failure before treating as model failure.
- Cited URLs: https://arxiv.org/abs/2603.13686 (τ-Voice); https://developers.openai.com/cookbook/examples/realtime_eval_guide; harness https://github.com/openai/openai-cookbook/tree/main/examples/audio/duplex_voice_agent_evaluation
- QMX-fit: Portfolio/Lab copilot IF a voice front-end is ever added — otherwise the eval discipline (deterministic+judge, crawl/walk/run) maps onto any QMX agent. INFERRED.
- LangChain/DeepAgents mapping: LangGraph StateGraph for frontend↔backend delegation; evaluator = LangSmith eval dataset + custom graders; simulated caller = second graph. INFERRED.

### openai-cookbook/examples/batch_processing.ipynb
- Pattern: async bulk inference via Batch API — cost control / offload background work; not an agent loop.
- Minimal mechanism: write jsonl, one request/line `{custom_id, method:"POST", url:"/v1/chat/completions", body:{model, messages, ...}}`; `client.files.create(purpose="batch")`; `client.batches.create(input_file_id=..., endpoint="/v1/chat/completions", completion_window="24h")`; poll `client.batches.retrieve(id)` until `completed`; fetch `client.files.content(output_file_id)`.
- JSON mode via `response_format={"type":"json_object"}`; vision via `content:[{type:"text"},{type:"image_url",image_url:{url}}]`.
- Caveats: results NOT in input order — match on `custom_id`; completes within 24h (often sooner); lower price + higher rate limits.
- QMX-fit: workflow/server agent — cheap bulk background jobs (e.g. nightly tagging/summaries of news or instruments) on DeepSeek/mini models. INFERRED.
- LangChain/DeepAgents mapping: no direct equivalent in the agent loop; a background workflow node that submits+polls a batch job. INFERRED.

### openai-cookbook/examples/book_translation/translate_latex_book.ipynb
- Pattern: chunk → map → reduce over a long document; parallel fan-out. Marginal agent relevance.
- Minimal mechanism: `tiktoken.get_encoding("o200k_base")` to count tokens; split on `\n\n`; `group_chunks(max_len=15000, hard_max_len=16000)`; gpt-4o `temperature=0, top_p=1, max_tokens=15000`; few-shot sample (untranslated+translated command pair) to steer; `ThreadPoolExecutor(max_workers=5)` + `as_completed` for parallel chunks.
- Numbers: largest chunk 1211 tokens; gpt-4o 16,384 token limit; sequential run 2-3 hours (motivates the thread pool).
- Caveat: discards chunks over hard_max_len; parallel version loses ordering (acceptable here).
- QMX-fit: Lab copilot — large-doc processing (research corpus translation/summarization) with bounded parallelism. INFERRED.
- LangChain/DeepAgents mapping: map-reduce chain / parallel RunnableEach; no agent loop. INFERRED.

### openai-cookbook/examples/Build_a_coding_agent_with_GPT-5.1.ipynb
- Pattern: coding agent (scaffold + iterate app) on the OpenAI Agents SDK; apply_patch + shell + web_search + hosted MCP. Direct copilot/coding-agent template.
- Minimal mechanism: `Agent(name, model="gpt-5.1", instructions, tools=[WebSearchTool(), shell_tool, apply_patch_tool, context7_tool])`; `Runner.run_streamed(agent, input=prompt)`; iterate `result.stream_events()` on `run_item_stream_event` → `tool_call_item`/`tool_call_output_item`/`message_output_item`; `result.final_output`.
- Shell tool handshake: model proposes commands, YOUR environment executes. Classes: `ShellTool, ShellCommandRequest, ShellCommandOutput, ShellCallOutcome, ShellResult`; custom `ShellExecutor.__call__(request)` runs `asyncio.create_subprocess_shell(cmd, cwd=workspace_dir)`; raw item type `LocalShellCall` with `.action.commands`.
- apply_patch: `ApplyPatchTool`, `agents.editor.ApplyPatchOperation/ApplyPatchResult`; custom `WorkspaceEditor.create_file/update_file`; fingerprint-based `ApprovalTracker` (sha256 of type+path+diff) for per-edit approval; env `APPLY_PATCH_AUTO_APPROVE=1`, `SHELL_AUTO_APPROVE=1`.
- Hosted MCP: `HostedMCPTool(tool_config={"type":"mcp","server_label":"context7","server_url":"https://mcp.context7.com/mcp","require_approval":"never", authorization: Bearer <CONTEXT7_API_KEY>})`.
- Instructions steer apply_patch discipline: always `cat` file first, generate unified diff vs exact content, apply once, don't retry on failure, never edit via shell.
- Caveats stated: ALWAYS sandbox shell in production (arbitrary exec risky); `MaxTurnsExceeded` / dependency errors — just re-run the loop; production needs outer loop / user-input handling.
- Cited URLs: Agents SDK https://openai.github.io/openai-agents-python/ ; Responses API docs; https://context7.com/ ; https://ui.shadcn.com/blocks
- QMX-fit: general + Lab copilot (Claude-Code/Codex-like, scaffolds mini-apps, edits codebase). Strong direct analog. INFERRED.
- LangChain/DeepAgents mapping: DeepAgents built-in filesystem/shell tools + subagents; apply_patch ≈ edit tool; HostedMCPTool ≈ LangChain MCP adapter; streamed events ≈ LangGraph `astream_events`. INFERRED.

### openai-cookbook/examples/chatgpt/daily_usage_limits/docs/codex.md
- Pattern: supervised pilot of a scheduled controller agent; strong HITL/approval + synthetic-rehearsal-before-live discipline.
- Minimal mechanism: `node src/cli.mjs` subcommands `init` (flags `--pattern fixed_release --cohort selected --unit credit --interval-hours 168 --synthetic --allow-initial-reduction`), `snapshot` (prints SHA256), `approve --hash REVIEWED_SHA256`, `run` (preview) then `run --apply`, `restore`, `inspect`. Config key `initialReviewMaxAgeMinutes` (default 15-min review window); `liveWrites: true` gate; secret `CHATGPT_ADMIN_API_KEY` from runtime secret store (never printed).
- Codex invoked to run the exact command and report receipt fields (mode, users, slot, targets, attention codes) WITHOUT altering policy/approval/state, no `--apply`, no credential retrieval, no schedule creation.
- Scheduled task created as **paused**, reviewed (prompt, folder, cadence, permissions), then enabled; "only one writer per cohort"; repeat run must report `duplicate_slot`.
- Caveats: local automation needs desktop app + host up → move to managed VM/cloud (AWS) for ongoing ops; keep Codex pilot schedule disabled after transition.
- Cited URLs: https://learn.chatgpt.com/docs/automations?surface=app ; operations.md/aws.md/local.md (relative).
- QMX-fit: workflow/server agent governance template — how a non-technical operator safely pilots a scheduled background agent (preview→approve-by-hash→apply→restore). Maps to QMX operator gating. INFERRED.
- LangChain/DeepAgents mapping: LangGraph checkpointer for state + `interrupt()` for the hash-approval gate; scheduled trigger external (cron). INFERRED.

### openai-cookbook/examples/chatgpt/daily_usage_limits/README.md
- Pattern: scheduled budget-release automation over ChatGPT Admin API; cost-control ops, not an LLM agent. Marginal.
- Minimal mechanism: policy `{"pattern":"fixed_release","anchor":ISO8601,"intervalHours":168,"startCap":"500","increment":"500","ceiling":"2000"}`, `"unit":"credit"|"usd"`; REST `PATCH /v1/manage/workspaces/{WORKSPACE_ID}/usage_limits/users/{USER_ID}` host `api.chatgpt.com` body `override_monthly_usage_limit:{type:"limited", limit_amount:{unit,amount}, temporary:true}`.
- Numbers: 2,000 credits/month example, 500/week → caps 500/1000/1500/2000; `temporary:true` expires at period end; repeated run same week = same target, missed run catches up.
- Requires Node.js 24+; local demo keeps state in memory, no API key needed.
- Caveats: run ongoing on org-managed infra, not an individual's machine; credit vs USD must match workspace billing unit (controller checks reported unit).
- Cited URLs: https://chatgpt.com/public/admin/api-reference ; GitHub operations.md/api-contract.md/aws.md paths.
- QMX-fit: not core; shows admin-API + scheduled pattern relevant to QMX's own quota/cost governance for subscription proxy. INFERRED.
- LangChain/DeepAgents mapping: no direct equivalent (deterministic controller + cron). INFERRED.

### openai-cookbook/examples/chatgpt/workspace_agents/workspace-agents-api-trigger.ipynb
- Pattern: externally triggering a saved managed agent asynchronously; fire-and-verify-in-destination.
- Minimal mechanism: `POST https://api.chatgpt.com/v1/workspace_agents/{id}/trigger`; path `id` = `agtch_...`; headers `Authorization: Bearer <Workspace Agent access token>`, `Content-Type: application/json`, recommended `Idempotency-Key`; body `{input, conversation_key?}`. Returns `202 Accepted`, NO body/run-id/output.
- Auth: use Workspace Agent access token (Admin > Access tokens, Workspace Agents scope), NOT a Platform `sk-` key.
- `conversation_key` continues same agent conversation; reusing `Idempotency-Key` for same source event returns original accepted outcome (dedup), not a new run.
- Error codes: 401 wrong/expired/credential-type, 403 token owner can't trigger (not shared), 404 bad/unseen trigger id, 409 agent/channel not runnable, 202-but-no-output = instructions/app-perms/approval problem.
- Caveats: async — verify by searching the destination for the request id; auto-approve only low-risk writes, keep sensitive writes approval-gated; log request/trigger/idempotency/timestamp/status, never the token.
- Cited URLs: https://developers.openai.com/workspace-agents/trigger-runs ; .../authentication ; .../cookbook/articles/chatgpt-agents-sales-meeting-prep ; help.openai.com article 20001143.
- QMX-fit: workflow/server agent — QMX background workflows triggered by external events (form/ticket/schedule) that write to a destination; ownership split (business owns instructions, engineering owns trigger). INFERRED.
- LangChain/DeepAgents mapping: a LangGraph deployment invoked via webhook; idempotency/conversation_key ≈ thread_id + idempotent run submission. INFERRED.

### openai-cookbook/examples/codex/Autofix-github-actions.ipynb
- Pattern: background coding agent autofixes failing CI and opens a PR. ARCHIVED (insecure credential/permission layout — do not copy).
- Minimal mechanism: `on: workflow_run: workflows:["CI"] types:[completed]`; `if: workflow_run.conclusion=='failure'`; `permissions: contents: write, pull-requests: write`; step `uses: openai/codex-action@main` with `openai_api_key`, `prompt`, `codex_args: '["--config","sandbox_mode=\"workspace-write\""]'`; then `npm test`; `peter-evans/create-pull-request@v6`.
- Prompt steers minimal/surgical change: run suite, identify minimal change to pass, implement only that, stop, no unrelated refactor.
- Caveat (header): exposes API key to whole job + combines repo-controlled execution with write perms; use current autofix workflow that separates patch generation from PR publication; read-only sandbox alone doesn't protect secrets.
- Cited URLs: https://learn.chatgpt.com/docs/non-interactive-mode#example-autofix-ci-failures-in-github-actions ; https://learn.chatgpt.com/docs/github-action#security-checklist ; https://github.com/openai/codex/
- QMX-fit: workflow/server agent in the factory lane (auto-repair on red CI). INFERRED.
- LangChain/DeepAgents mapping: a CI-triggered background DeepAgent with shell+edit tools in a sandbox/worktree; no in-graph equivalent for the GH trigger. INFERRED.

### openai-cookbook/examples/codex/build_code_review_with_codex_sdk.md
- Pattern: self-hosted automated code reviewer via Codex CLI headless + structured outputs; reviewer agent. ARCHIVED (credential/permission caveat).
- Minimal mechanism: `codex exec "..." --output-schema codex-output-schema.json --output-last-message codex-output.json --sandbox read-only`; GitHub Action input `output-schema-file` / `output-file`, `sandbox: read-only`, `model: gpt-5.5`.
- Schema shape: `findings[]{title(maxLen80), body, confidence_score 0..1, priority 0..3, code_location{absolute_file_path, (relative_file_path), line_range{start,end}}}`, plus `overall_correctness` enum ("patch is correct"/"patch is incorrect"), `overall_explanation`, `overall_confidence_score`; `additionalProperties:false`, all required.
- Review prompt: reviewer persona, flag only actionable issues introduced by PR, cite file+line range, prioritize severe, give overall verdict + confidence 0-1, exact line numbers or comments rejected.
- Publishing: parse JSON with `jq`, POST inline comments to GitHub `/pulls/{n}/comments` (side RIGHT, start_line/start_side), summary to `/issues/{n}/comments`; GitLab discussions API with `position{position_type:text, base_sha,start_sha,head_sha,new_path,new_line}`; Azure DevOps Pull Request Threads API (`threadContext.filePath/rightFileStart/rightFileEnd`, `pullRequestThreadContext.changeTrackingId`); Jenkins groovy equivalent.
- Model recommendation: `gpt-5.5` for strongest review accuracy/consistency.
- Safety strategy: GH action drops sudo so Codex can't read its own OpenAI API key — isolation critical on public repos.
- Caveats: validate inline-comment anchoring per-SCM (new/modified/renamed/deleted/multi-line); if a finding can't be anchored safely, skip inline and use summary; don't treat failed Codex run as empty findings.
- Cited URLs: https://learn.chatgpt.com/docs/github-action ; .../non-interactive-mode#authenticate-in-automation ; https://chatgpt.com/codex/settings/code-review ; platform.openai.com/docs/guides/structured-outputs ; Azure PR Threads REST docs.
- QMX-fit: reviewer in the factory lane (bmad-code-review analog); structured-output verdict+confidence maps to QMX adversarial reviewer gating. INFERRED.
- LangChain/DeepAgents mapping: a reviewer subagent returning a structured-output (Pydantic/JSON-schema) verdict; publishing is a tool. INFERRED.

### openai-cookbook/examples/codex/Build_iterative_repair_loops_with_Codex.ipynb
- Pattern: closed-loop agent — produce→validate→improve. Three phases Review / Repair / Validate with structured handoffs; strongest QMX-factory analog in batch.
- Minimal mechanism: `codex exec --model {MODEL} --sandbox workspace-write --ask-for-approval never --config model_reasoning_effort={low} --output-schema {schema} --output-last-message {answer} -` (prompt via stdin). Pin CLI: `npm install -g @openai/codex@0.130.0`.
- Models: default repair `gpt-5.4-mini` (env `REPAIR_MODEL`), chat `gpt-5.5`, `REPAIR_REASONING_EFFORT=low`.
- Structured schemas: `finding{artifact,issue_type,severity,description,suggested_fix_direction}`; `fix{artifact,iteration,changes_made[],unresolved_items[],updated_artifact_path}`; `validation{overall_passed,cases[{name,passed,severity,evidence,feedback}],remaining_delta[]}`. Phase separation: review does not edit/execute; repair edits a COPY only; validation executes.
- Validation executes notebook: `jupyter nbconvert --to notebook --execute --inplace`; failures become next repair input. Business-rules contract passed in (preferred models, modernize map, reader-experience rules).
- Concurrency: `ThreadPoolExecutor(max_workers=min(3,n))` across independent cases; per-iteration `record.json` audit trail (review/repair/validation).
- Stop conditions (production loop `repair_until_done`): validation passes, max attempts reached, delta stops changing, or needs human review. Signal to watch = remaining `remaining_delta` shrinks, not that edits were made.
- Generalizations stated: protocol optimization, regulatory remediation, support-article refresh, code modernization — any change needing evidence.
- Caveats: don't assume edit worked (validation decides); keep audit trail; needs Jupyter/nbconvert on PATH.
- QMX-fit: workflow/server agent AND the factory repair lane (Skylos-repair style loop); review=reviewer, repair=coder, validate=deterministic battery. Very strong fit. INFERRED.
- LangChain/DeepAgents mapping: LangGraph cyclic StateGraph (review→repair→validate→conditional loop), structured outputs via schema, checkpointer for `record.json`/history, interrupt for the "needs human review" stop. INFERRED.

### openai-cookbook/examples/codex/code_modernization.md
- Pattern: plan-driven legacy modernization via Codex CLI; ExecPlan-centric, parity-first; planning harness.
- Minimal mechanism: `.agent/AGENTS.md` + `.agent/PLANS.md` (ExecPlan skeleton); 4 docs per pilot flow: `pilot_execplan.md` (home base: scope/why/steps/done), `pilot_overview.md` (inventory + modernization technical report), `pilot_design.md` (target service/data model/API), `pilot_validation.md` (parity test plan). Codex `/init` generates AGENTS.md.
- 5 phases: 0 set up AGENTS/PLANS; 1 pick pilot + ExecPlan; 2 inventory/discovery; 3 design+OpenAPI (`modern/openapi/pilot.yaml`)+validation+scaffold `modern/tests/pilot_parity_test.py`; 4 implement+parallel-run+parity compare; 5 templatize (`template_modernization_execplan.md`, how-to guide).
- Running example COBOL/JCL investment-portfolio system; parity = run legacy vs modern on same inputs, compare outputs. Engineers own architecture/business rules; Codex does translation/refactor/doc-sync.
- Numbers: none quantitative; one customer migrated a large monorepo feeding hundreds of Jira tickets with a separate validator reviewing+merging.
- Caveats: first-draft modules (models/repositories/services.py) have no runnable entry point — add your own runner; update ExecPlan after each chunk.
- Cited URLs: https://github.com/sentientsergio/COBOL-Legacy-Benchmark-Suite/ ; https://cookbook.openai.com/articles/codex_exec_plans ; learn.chatgpt.com/docs/agent-configuration/agents-md
- QMX-fit: Lab copilot + workflow — large migration/modernization planning; mirrors QMX's docs-first (PRD/Architecture→docs-factory→epics) discipline. INFERRED.
- LangChain/DeepAgents mapping: DeepAgents planning + filesystem tools; ExecPlan ≈ the plan/todo artifact; parity test = validation node. INFERRED.

### openai-cookbook/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk.ipynb
- Pattern: Codex CLI exposed as an MCP server, driven by Agents SDK; single-agent + gated multi-agent orchestration; observability via Traces. ARCHIVED (Codex MCP server deprecated; use Codex SDK / app server).
- Minimal mechanism: `MCPServerStdio(name="Codex CLI", params={"command":"npx","args":["-y","codex","mcp-server"]}, client_session_timeout_seconds=360000)`; exposes tools `codex()` (new conversation) + `codex-reply()` (continue). Agent writes files by calling Codex MCP with `{"approval-policy":"never","sandbox":"workspace-write"}`.
- Agents SDK: `Agent(name, instructions, model="gpt-5", mcp_servers=[...], tools=[WebSearchTool()], handoffs=[...])`; `Runner.run(agent, prompt)`; `ModelSettings(reasoning=Reasoning(effort="medium"))`; `from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX` prefixed to each agent's instructions to optimize handoffs.
- Multi-agent roles: Project Manager (only one receiving initial prompt; writes REQUIREMENTS.md/TEST.md/AGENT_TASKS.md; enforces gating — verifies artifacts exist before each handoff) → Designer → Frontend+Backend (parallel) → Tester; every specialist's `handoffs=[project_manager_agent]` set after PM construction so deliverables return for validation. `transfer_to_<agent>` handoff tools.
- Observability: Traces dashboard records prompts, tool calls, handoffs, MCP/Codex calls, execution times, file writes, errors.
- Numbers: multi-agent run ~11 minutes; produced backend/frontend/design/tests file tree.
- Caveats: extend MCP timeout for long Codex tasks; can ignore MCP event format warnings; archived — not a migration example.
- Cited URLs: https://learn.chatgpt.com/docs/mcp-server ; .../codex-sdk ; .../app-server
- QMX-fit: workflow/server + Lab copilot — gated multi-agent orchestration (PM gatekeeper pattern) mirrors QMX factory epic/story gating; Traces → QMX observability. INFERRED.
- LangChain/DeepAgents mapping: PM = orchestrator/supervisor graph; specialists = subagents; gating = conditional edges checking state/files; Traces ≈ LangSmith tracing. INFERRED.

### openai-cookbook/examples/codex/data/docs/getting_started_evals_pre_repair.ipynb
- Pattern: intentionally-stale eval fixture (repair-loop target); not an agent itself. Marginal.
- Mechanism shown (stale on purpose): `MODEL="gpt-3.5-turbo"`; text-to-SQL eval rows `{input:[system,user], ideal}`; legacy CLI `oaieval gpt-3.5-turbo spider-sql --max_samples 25`; manual log-name placeholder + `local_events` with `final_report{accuracy:0.5}`.
- Repair targets: stale model name, legacy `oaieval` CLI → current Evals API, manual placeholder removal.
- QMX-fit: only as a worked eval-authoring example (SQL grading rows). INFERRED.
- LangChain/DeepAgents mapping: eval dataset; no agent. INFERRED.

### openai-cookbook/examples/codex/data/docs/knowledge_retrieval_pre_repair.ipynb
- Pattern: stale function-calling / retrieval fixture (repair target). Marginal.
- Mechanism (stale): `GPT_MODEL="gpt-4-turbo-preview"`; local keyword-overlap `get_articles(query, top_k)`; legacy `arxiv_functions=[{name,description,parameters:{type:object,properties,required}}]` (old function schema, not current `tools`).
- Repair targets: stale model, legacy function-calling schema → current tools schema.
- QMX-fit: illustrates retrieval+tool-schema the Lab copilot would modernize. INFERRED.
- LangChain/DeepAgents mapping: a retrieval tool + tool-calling; legacy function schema ≈ old-style tool definition. INFERRED.

### openai-cookbook/examples/codex/data/docs/qdrant_embeddings_search_pre_repair.ipynb
- Pattern: stale vector-search fixture (repair target). Marginal.
- Mechanism (stale): `EMBEDDING_MODEL="text-embedding-ada-002"`; toy 4-bucket `embed()`; `LocalQdrant` with both `.search(...)` (legacy) and `.query_points(...)` (current); `query_qdrant(..., vector_name="title", top_k=3)` dot-product ranking.
- Repair targets: ada-002 → `text-embedding-3-large`; `qdrant.search` → `qdrant.query_points`.
- QMX-fit: embeddings/vector-search pattern a Lab research agent would use; shows API-migration seam. INFERRED.
- LangChain/DeepAgents mapping: vector store retriever; no agent. INFERRED.

### openai-cookbook/examples/codex/iterating-development-workflows-with-codex.md
- Pattern: repository engineering "harness" convention for durable, auditable, human-gated agent development; plus a reusable skill + retrospective loop. Skills + planning + audit discipline.
- Minimal mechanism / files: `AGENTS.md` (durable repo guidance Codex reads before work; `/init` generates), `PLANS.md` (roadmap + ordered phase plan), `GOALS.md` (outcomes/success/scope/non-goals), `PROMPTS.md` (reusable entry prompts), `harness/build/<NN>-<title>.md` (one bounded phase: status/scope/non-goals/deps/approval-gate/red-green-refactor/verification/acceptance/evidence/stop), `harness/context/phase-<NN>-<slug>-context.md` (material decisions only, materiality test), `harness/build-log.md` (append-only observed progress + verification evidence; statuses Not started/In progress/Blocked/Complete).
- Source-of-truth boundaries enforced: PLANS owns sequence, build file owns scope/acceptance, context owns discoveries, build-log owns evidence, review artifacts own findings — never duplicate across files.
- Discipline rules: read-only preflight before writes; approval summary before repo writes; red/green/refactor; observed evidence only (never convert planned commands into "passed"); credentials/commits/pushes/deploys behind separate approval; stop after selected phase.
- Skills: use `$skill-creator` to build a `harness-author` skill; install path `${CODEX_HOME:-$HOME/.codex}/skills/harness-author`; structure `SKILL.md`+`agents/openai.yaml`+`references/`+`scripts/validate_harness.py`+tests; deterministic validator rejects absolute paths/traversal/unapproved scaffolding; YAML frontmatter only `name`+`description`; lowercase-hyphenated name. `quick_validate.py` checks the skill.
- Retrospective/postmortem prompt: read-only discovery → reconstruct intended vs actual → materiality test → classify improvement owner (AGENTS vs harness vs skill vs reference vs script vs regression test vs new skill vs no change) → prioritized backlog P0-P3 → approval gate before any change → forward-testing in fresh contexts.
- Caveats: skills may mis-propose scope (example omitted PLANS.md/build-log.md) — correct before approving; "harness-only"/"planning-only" must NOT authorize implementation.
- Cited URLs: learn.chatgpt.com/docs/agent-configuration/agents-md ; developers.openai.com/cookbook/articles/codex_exec_plans#plansmd ; learn.chatgpt.com/docs/build-skills ; https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md
- QMX-fit: workflow/server + the whole factory governance; maps directly onto QMX's AGENTS.md/CLAUDE.md + BMad docs + factory build-log + operator approval gates; skill discipline mirrors QMX skills. INFERRED.
- LangChain/DeepAgents mapping: AGENTS.md ≈ system prompt/middleware; harness docs ≈ persisted state in store; build-log ≈ checkpointer history; approval gates ≈ interrupt; skills ≈ reusable subagent/tool bundles. INFERRED.

### openai-cookbook/examples/codex/jira-github.ipynb
- Pattern: event-triggered background coding agent — label Jira issue → GitHub Action runs Codex → opens PR → updates Jira. Zero-click loop.
- Minimal mechanism: Jira Automation on label change, filter label (`aswe`), POST GitHub `workflow_dispatch` with issue key/summary/cleaned description; Action `permissions: contents: write, pull-requests: write`; `pnpm add -g @openai/codex`; `codex exec --sandbox workspace-write "Implement JIRA ticket $KEY: $TITLE. $DESC"`; `git commit`; `peter-evans/create-pull-request@v6` (base main, branch `codex/<KEY>`); Jira REST `POST /rest/api/3/issue/{key}/transitions` (id 21=In Progress, 31=In Review) and `/comment` with PR link. Secrets: `OPENAI_API_KEY`/`CODEX_API_KEY`, `JIRA_BASE_URL/EMAIL/API_TOKEN`.
- Multiple labels → different workflows (bug fix vs refactor vs API stubs).
- Caveats: needs protected main + branch protection; Smart Commits can auto-close ticket on merge; (implicit: same insecure key-exposure concern as other archived examples — not flagged here).
- Cited URLs: https://github.com/openai/openai-codex ; developer.atlassian.com transitions API; support.atlassian.com smart-values.
- QMX-fit: workflow/server agent — QMX's to-kanban/queue-publish unattended lane analog (ticket → background implementation → PR). INFERRED.
- LangChain/DeepAgents mapping: external event trigger → background DeepAgent coding run in worktree; Jira transitions = tool calls. INFERRED.

### openai-cookbook/examples/codex/secure_quality_gitlab.md
- Pattern: Codex CLI in GitLab CI as reasoning layer over scanners — code-quality report + SAST post-processing + auto-remediation patches. Reviewer/security + structured outputs. UPDATE NOTE: `--full-auto` deprecated; use maintained Security CLI/CI guide.
- Minimal mechanism (quality): `npm -g i @openai/codex@latest`; `git ls-files` allowlist injected into prompt; `codex exec --full-auto "$CODEX_PROMPT"` capturing output; strict prompt forces single JSON array between `=== BEGIN_CODE_QUALITY_JSON ===`/`=== END_CODE_QUALITY_JSON ===` markers; extract via sed(ANSI strip)+awk, validate with node/`JSON.parse`, fallback `[]`; publish as GitLab `artifacts: reports: codequality:` CodeClimate JSON (fields description/check_name/fingerprint/severity[info|minor|major|critical|blocker]/location{path,lines{begin}}).
- SAST remediation (2 steps): Step1 `codex_recommendations` reads `gl-sast-report.json` → consolidates duplicates (by CWE+sink+file[:line]+route), ranks by exploitability (user input→dangerous sink, auth boundaries, internet-facing), outputs `security_priority.md` between `=== BEGIN_SECURITY_MD ===`/`END`. Step2 `codex_resolution` loops High/Critical via `jq ... select(severity=="high"|"critical")`, per-finding prompt → unified diff between `=== BEGIN_UNIFIED_DIFF ===`/`END`, validate `git apply --check -p0` or `-p1`, store `.patch`, emit `dotenv: codex.env` (`CODEX_CREATED_PATCHES`).
- Hardening: `set -euo pipefail`, JSON markers, schema validation (ajv-cli), severity whitelists, `node:24` image, skip forked MRs (no secrets), run only if `$OPENAI_API_KEY`.
- Numbers (example output): 5 raw findings → 4 consolidated; exploitability scores 0-100 (JWT 98, SQLi 95, SSRF 80, eval 72); CWE-798/89/94 + SSRF.
- Caveats (header + body): `--full-auto` deprecated; DON'T treat a failed Codex run or invalid output as empty findings; Codex sandbox may restrict `awk`/`nl`; prompt wording/schema need per-stack tuning; Codex complements (not replaces) scanners which stay source of truth.
- Cited URLs: https://github.com/openai/codex ; docs.gitlab.com/ci/testing/code_quality ; docs.gitlab.com/user/application_security/sast ; learn.chatgpt.com/docs/non-interactive-mode ; .../security/cli/ci/gitlab ; https://github.com/juice-shop/juice-shop
- QMX-fit: reviewer/security in factory lane (quality gate + auto-remediation patch), and workflow agent producing ranked, actionable reports. INFERRED.
- LangChain/DeepAgents mapping: reviewer subagent with structured output + git-apply tool; the extract/validate/fallback = deterministic post-processing node. INFERRED.
