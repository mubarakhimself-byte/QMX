> SUPERSEDED 2026-10-12 by `tracker/qma-v2/PRD.md` (see `tracker/qma-v2/FILE-INDEX.md`). Kept for history.

# batch00 — cookbook reader notes

Repo note: all files are `claude-cookbooks`.

## PART A — INDEX

- claude-cookbooks/.claude/agents/code-reviewer.md — subagent definition (frontmatter name/description/tools) for proactive Python/Jupyter code review; shows subagent spec format.
- claude-cookbooks/.claude/commands/add-registry.md — slash command adding a notebook to registry.yaml; uses Read/Glob/Grep/Edit + asks user (HITL) for author.
- claude-cookbooks/.claude/commands/link-review.md — slash command reviewing links; allowed-tools restricts to `gh pr` bash calls; posts PR comment.
- claude-cookbooks/.claude/commands/model-check.md — slash command validating model names against a live docs URL; posts PR comment.
- claude-cookbooks/.claude/commands/notebook-review.md — slash command invoking a notebook-review skill; posts PR comment.
- claude-cookbooks/.claude/commands/review-issue.md — slash command triaging GitHub issues with classification + `AskUserQuestion` approval gate before acting.
- claude-cookbooks/.claude/commands/review-pr-ci.md — slash command (CI mode) spawning `code-reviewer` subagent via Task tool, posts `gh pr review`.
- claude-cookbooks/.claude/commands/review-pr.md — slash command (interactive) Task→code-reviewer + `AskUserQuestion` before posting review.
- claude-cookbooks/.claude/skills/cookbook-audit/SKILL.md — skill definition (name/description frontmatter + workflow + rubric); invokes a validate script w/ detect-secrets.
- claude-cookbooks/.claude/skills/cookbook-audit/style_guide.md — (not agent-relevant) prose style guide for notebook authoring.
- claude-cookbooks/capabilities/knowledge_graph/guide.ipynb — structured-output extraction pipeline (NER/relation/entity-resolution/summarize) via `messages.parse()` + Pydantic; two-model cost split; precision/recall eval.
- claude-cookbooks/capabilities/knowledge_graph/README.md — (not agent-relevant) directory index.
- claude-cookbooks/capabilities/README.md — (not agent-relevant) capabilities section index.
- claude-cookbooks/capabilities/retrieval_augmented_generation/guide.ipynb — RAG build + eval (precision/recall/F1/MRR/e2e), summary indexing, Claude re-ranking, Promptfoo evals.
- claude-cookbooks/capabilities/retrieval_augmented_generation/README.md — (not agent-relevant) directory index.
- claude-cookbooks/capabilities/text_to_sql/guide.ipynb — NL→SQL via prompting, few-shot, CoT, schema RAG, execute-and-retry self-improvement loop, Promptfoo evals.
- claude-cookbooks/capabilities/text_to_sql/README.md — (not agent-relevant) directory index.
- claude-cookbooks/CLAUDE.md — repo config: model alias IDs (opus-4-8/sonnet-5/haiku-4-5), Bedrock IDs, ruff, uv, slash commands.
- claude-cookbooks/claude_agent_sdk/00_The_one_liner_research_agent.ipynb — Agent SDK `query()` vs `ClaudeSDKClient`, WebSearch/Read tools, system prompts, memory, multimodal, buffer size.
- claude-cookbooks/claude_agent_sdk/01_The_chief_of_staff_agent.ipynb — full feature tour: CLAUDE.md memory, Bash, output styles, plan mode, slash commands, hooks, subagents via Task.
- claude-cookbooks/claude_agent_sdk/02_The_observability_agent.ipynb — connecting external MCP servers (git stdio, GitHub via docker) to the agent; tool allow/disallow scoping.
- claude-cookbooks/claude_agent_sdk/03_The_site_reliability_agent.ipynb — read+write infra agent: custom MCP server (JSON-RPC/stdio), scoped tools, PreToolUse validation hooks, HITL investigate/remediate split, skills.
- claude-cookbooks/claude_agent_sdk/04_migrating_from_openai_agents_sdk.ipynb — OpenAI Agents SDK → Claude Agent SDK primitive map (`@tool`, guardrails, sessions, resume, OTel, caching, handoffs→AgentDefinition).
- claude-cookbooks/claude_agent_sdk/05_Building_a_session_browser.ipynb — session management API: list/get/read/rename/tag/fork/delete sessions on disk; sidebar/UI pattern.
- claude-cookbooks/claude_agent_sdk/06_The_vulnerability_detection_agent.ipynb — threat-model→find→triage→report pipeline; ClaudeSDKClient multi-turn + stateless query() one-shots; quality-tier rubric; preset system prompt.
- claude-cookbooks/claude_agent_sdk/07_Hosting_the_agent.ipynb — deploying the same agent container across Docker / Modal / Kubernetes tiers; sessions, resume, auth gateway, egress lockdown, OTel.

## PART B — PATTERN NOTES

### claude-cookbooks/.claude/agents/code-reviewer.md
- Pattern: **subagent definition file** — the `.claude/agents/*.md` filesystem format a parent agent delegates to via the Task tool.
- Minimal mechanism: YAML frontmatter `name`, `description` (tells orchestrator when to invoke), `tools:` (here `Read, Grep, Glob, Bash, Bash(git status:*)` — note scoped bash tool strings like `Bash(git status:*)`), then the body is the subagent's system prompt.
- Description field explicitly says "Use this agent proactively after writing any significant code changes" — proactive-invocation cue for the orchestrator.
- Body encodes a review rubric: security/secret-exposure first, type safety, early returns, `make check`/ruff, conventional commits.
- Caveat: tool allowlist uses both coarse (`Bash`) and scoped (`Bash(git status:*)`) forms in one list.
- QMX-fit: general copilot + Lab copilot (code review inside factory lanes). LangChain/DeepAgents mapping (inferred): DeepAgents **subagent** / LangGraph subgraph with its own tool subset; the description→routing is a supervisor-router concern.

### claude-cookbooks/.claude/commands/add-registry.md
- Pattern: **custom slash command** as a prompt template; light HITL.
- Mechanism: frontmatter `allowed-tools: Read,Glob,Grep,Edit` and `description`; body is the expanded instruction. Asks the user for author GitHub username and approval before Edit (approval gate).
- QMX-fit: general copilot. Mapping (inferred): a parameterised prompt macro; no direct LangChain equivalent beyond a PromptTemplate + `interrupt` for the approval.

### claude-cookbooks/.claude/commands/link-review.md
- Pattern: slash command with tightly scoped tools.
- Mechanism: `allowed-tools: Bash(gh pr comment:*),Bash(gh pr diff:*),Bash(gh pr view:*)` — tool-string scoping limits bash to specific `gh` subcommands. Ends by posting `gh pr comment $PR_NUMBER --body`.
- QMX-fit: workflow/background (CI). Mapping (inferred): a tool with an argument allowlist; LangChain custom tool with validation.

### claude-cookbooks/.claude/commands/model-check.md
- Pattern: slash command that fetches a live doc then validates.
- Mechanism: instructs fetching `https://docs.claude.com/en/docs/about-claude/models/overview.md` as the source of allowed models; flags deprecated/internal model names; suggests `-latest` aliases.
- Cited URL: `https://docs.claude.com/en/docs/about-claude/models/overview.md`.
- QMX-fit: workflow. Mapping (inferred): a validator tool; no agent loop.

### claude-cookbooks/.claude/commands/notebook-review.md
- Pattern: slash command that defers to a named skill ("Notebook review skill").
- Mechanism: `allowed-tools` includes `Read,Glob,Grep,WebFetch` plus scoped `gh` bash; posts PR comment.
- QMX-fit: workflow. Mapping (inferred): command→skill dispatch ≈ LangGraph node calling a sub-routine.

### claude-cookbooks/.claude/commands/review-issue.md
- Pattern: **classification + HITL-approval** slash command.
- Mechanism: 8-step flow (gather via `gh issue view --json ...`, classify into 6 types, check context, draft, suggest labels, present, `AskUserQuestion` approval, then act). Actions gated behind user yes: `gh issue comment/edit/close`.
- `AskUserQuestion` is the explicit human-approval primitive before side-effectful gh writes.
- QMX-fit: general copilot. Mapping (inferred): LangGraph `interrupt()` / HITL gate before tool execution; classification = a routing node.

### claude-cookbooks/.claude/commands/review-pr-ci.md
- Pattern: **slash command orchestrating a subagent** (CI/non-interactive).
- Mechanism: `Task` tool with `subagent_type: "code-reviewer"`; passes diff + changed files; decides APPROVE/REQUEST_CHANGES/COMMENT; posts via `gh pr review --approve|--request-changes|--comment`. Template uses collapsible `<details>` sections and checkbox actionable items.
- Caveat stated: `gh pr review` produces no output on success — do not retry.
- QMX-fit: workflow/background (reviewer in factory lane). Mapping (inferred): supervisor → review subagent; verdict is a structured output.

### claude-cookbooks/.claude/commands/review-pr.md
- Pattern: interactive variant of review-pr-ci; adds `gh pr checkout` + `AskUserQuestion` before posting.
- Mechanism: same Task→code-reviewer; `AskUserQuestion` asks whether to post and which action; wraps Detailed Review in `<details>` when posting.
- QMX-fit: general/Lab copilot. Mapping (inferred): subagent + HITL interrupt.

### claude-cookbooks/.claude/skills/cookbook-audit/SKILL.md
- Pattern: **skill definition** (progressive-disclosure: SKILL.md + referenced style_guide.md + script).
- Mechanism: frontmatter `name`, `description` ("Use whenever a notebook review or audit is requested" — trigger phrasing); workflow reads `style_guide.md` first, runs `python3 validate_notebook.py <path>` which runs **detect-secrets** (custom `scripts/detect-secrets/plugins.py`, baseline `.secrets.baseline`) to scan hardcoded API keys; writes markdown to gitignored `tmp/` to save context.
- Numbers/thresholds: scoring rubric X/20 across 4 dimensions (narrative/code/technical-accuracy/actionability, 5 each). Model-name checks: use `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-opus-4-6`; never dated IDs.
- Caveat: markdown excludes outputs for cleaner review / context saving.
- QMX-fit: Lab copilot (QA/review). Mapping (inferred): a skill = reusable instruction bundle; DeepAgents/LangChain has no 1:1 but ≈ a tool that loads a prompt + runs a deterministic validator subprocess.

### claude-cookbooks/.claude/skills/cookbook-audit/style_guide.md
- (not agent-relevant) Prose/pedagogy templates (TLO/ELO intros, `%%capture`, dotenv, MODEL constant). Only reusable idea for QMX: define `MODEL` as a top constant and load keys via dotenv, never `os.environ[...] = "sk-..."`.

### claude-cookbooks/capabilities/knowledge_graph/guide.ipynb
- Patterns: **structured outputs** for schema-validated extraction; LLM-as-entity-resolver; multi-hop graph QA by serialising subgraphs; precision/recall evals; cost-tiered model split.
- Minimal mechanism: `client.messages.parse(model=..., max_tokens=..., messages=[...], output_format=PydanticModel)` returns `response.parsed_output` as a typed object (no JSON parsing). Pydantic models `Entity`/`Relation`/`ExtractedGraph`, `Cluster`/`ResolvedClusters`, `EntityProfile`. Graph in `networkx.MultiDiGraph`.
- Two models: `EXTRACTION_MODEL="claude-haiku-4-5"` (high-volume schema work), `SYNTHESIS_MODEL="claude-sonnet-4-6"` (resolution/summarisation). Also `client.messages.create(...)` for ungrounded QA; extract `.content` text block by `b.type=="text"`.
- Numbers: Message Batches API = **50% off** for ≤24h jobs; resolution prompt works on blocks of 50–100 entities; NetworkX fine to a "few hundred thousand edges".
- Caveats: resolver can drop unmatched names (→ silent node loss; fall back to singleton clusters) and **over-merge** distinct entities; resolved recall can *drop* vs raw if canonical form not in alias map (scoring artifact).
- Cited URLs: `https://docs.claude.com/en/docs/build-with-claude/prompt-caching`; `https://docs.claude.com/en/docs/build-with-claude/batch-processing`.
- QMX-fit: Lab copilot (research/analysis), Portfolio (entity/relationship over instruments/news). Mapping (inferred): structured-output extraction node; LangChain `with_structured_output` / Pydantic parser; multi-model = different LLM bindings per node.

### claude-cookbooks/capabilities/retrieval_augmented_generation/guide.ipynb
- Patterns: **RAG** (naive → summary-indexed → re-rank), **eval harness** separating retrieval metrics from end-to-end, **LLM re-ranking**, LLM-as-judge, Promptfoo for scaled evals.
- Minimal mechanism: in-memory `VectorDB` using Voyage `voyage-2` embeddings, cosine via `np.dot`; `similarity_threshold=0.75`, k=3; summary indexing embeds heading+text+summary; re-rank: ask Claude for top-k indices via `<relevant_indices>` with assistant-prefill + `stop_sequences=["</relevant_indices>"]`, `initial_k=20`→k=3.
- Numbers (basic→improved): Precision 0.43→0.44; Recall 0.66→0.69; F1 0.52→0.54; MRR 0.74→0.87; **e2e accuracy 71%→81%** (re-rank section cites 78%→85%). Eval dataset = 100 synthetic samples (question + correct chunks + answer).
- Caveats: eval runs are slow and can hit rate limits; min-3-chunk retrieval biases toward recall over precision; LLM-as-judge = Claude Sonnet.
- Cited URL: `https://docs.claude.com/en/api/rate-limits`; tool: promptfoo.dev.
- QMX-fit: Lab copilot (RAG over GitBook/wiki/docs corpus), general copilot grounding. Mapping (inferred): retriever + re-ranker nodes in a StateGraph; eval = offline grader; UNVERIFIED whether QMX wants Voyage vs other embeddings.

### claude-cookbooks/capabilities/text_to_sql/guide.ipynb
- Patterns: NL→SQL prompting ladder (basic→few-shot→CoT→schema-RAG), **execute-and-retry self-improvement loop**, schema retrieval for large DBs, multi-dimension evals.
- Minimal mechanism: prompt wraps `<schema>`/`<query>`, output in `<sql>` tags parsed by split; CoT adds `<thought_process>`; RAG embeds table/column metadata (Voyage `voyage-2`, threshold 0.3, k=10) and injects only relevant schema; self-improvement: `execute_sql_with_feedback` runs SQL, on error feeds error text back, `max_attempts=3`.
- Numbers (pass-rate / latency ms / tokens / cost): Haiku basic 83.3% → Sonnet CoT+RAG 100%; latency 1561ms→4614ms; cost $0.0023→$0.050. 3.5 Sonnet more consistent but higher latency/cost.
- Caveats: valid-but-wrong SQL is possible; evaluation across syntax/semantics/result-correctness/complexity; recency/frequency filters recommended for schema RAG freshness.
- Cited URL: promptfoo.dev.
- QMX-fit: Lab copilot (query trade/market DBs from NL), general copilot. Mapping (inferred): tool-calling loop with a DB-exec tool + retry; LangGraph loop node with error edge back to generation.

### claude-cookbooks/CLAUDE.md
- Pattern: repo-level agent memory/config (model registry + conventions).
- Mechanism/numbers: current aliases **`claude-sonnet-5`, `claude-haiku-4-5`, `claude-opus-4-8`**; never dated IDs; Bedrock IDs e.g. `anthropic.claude-opus-4-8`, `global.` prefix for global endpoints; `uv sync --all-extras`, ruff 100-col double-quote; slash commands `/notebook-review`, `/model-check`, `/link-review`.
- QMX-fit: all (config discipline). Mapping (inferred): CLAUDE.md ≈ a system/context file; DeepAgents has no exact equivalent beyond injected system prompt. NOTE for QMX: these alias IDs match the operator's global rules (opus-4-8 etc.).

### claude-cookbooks/claude_agent_sdk/00_The_one_liner_research_agent.ipynb
- Patterns: minimal **research agent**; stateless vs stateful; system-prompt specialisation; multimodal via `Read`; production module packaging.
- Minimal mechanism: `from claude_agent_sdk import ClaudeAgentOptions, query, ClaudeSDKClient`. `query(prompt=..., options=ClaudeAgentOptions(model=MODEL, allowed_tools=["WebSearch"]))` is **stateless single-turn**; `async with ClaudeSDKClient(options=...) as agent:` keeps conversation memory, `await agent.query(...)` then `async for msg in agent.receive_response()`. Options seen: `model`, `cwd`, `system_prompt`, `allowed_tools=["WebSearch","Read"]`, `max_buffer_size`. Module exposes `send_query(..., continue_conversation=True, display_result=...)`.
- Permission model: `allowed_tools` = usable without approval; other tools require approval; read-only tools (Read) allowed by default; `disallowed_tools` removes from context entirely.
- Numbers/caveats: default `max_buffer_size`=1MB (1,048,576 bytes) — base64 images overflow it; set 10MB for multimodal. Error text: "JSON message exceeded maximum buffer size".
- `MODEL="claude-opus-4-6"` used (note: notebook corpus is a slightly different model-version era than CLAUDE.md).
- Cited URLs: `https://www.anthropic.com/engineering/building-effective-agents`; `https://docs.claude.com/en/docs/claude-code/settings#tools-available-to-claude`.
- QMX-fit: general copilot (one-shot Q&A), Lab copilot (research). Mapping (inferred): `query()` ≈ stateless chain; `ClaudeSDKClient` ≈ graph + checkpointer (in-memory thread).

### claude-cookbooks/claude_agent_sdk/01_The_chief_of_staff_agent.ipynb
- Patterns (full tour): **CLAUDE.md memory**, **Bash tool** for running Python scripts, **output styles** per audience, **plan mode**, **custom slash commands**, **hooks (PostToolUse) for audit**, **subagents via Task tool**, multi-agent orchestration.
- Minimal mechanism / critical config keys:
  - `setting_sources=["project"]` **required** for the SDK to load filesystem settings (CLAUDE.md, output styles, slash commands, subagents); `["project","local"]` to also load `.claude/settings.local.json` (hooks). Default SDK runs in isolation and loads none.
  - Output style: `settings='{"outputStyle":"executive"}'` + markdown files in `.claude/output-styles/` (frontmatter name+description, name must match filename). Output styles rewrite the system prompt, dropping SWE-specific parts.
  - Plan mode: `permission_mode="plan"` — agent plans, won't act; caveat: in headless SDK it calls `ExitPlanMode()` (interactive-only), so continue with `continue_conversation=True` to execute. Plans captured from message stream / Write tool / `~/.claude/plans/` with XML `<plan>` extraction (min 200 chars).
  - Slash commands: `.claude/commands/*.md`, `$ARGUMENTS`/`$1`/`$2` params; "syntactic sugar, not new capability".
  - Hooks: scripts in `.claude/hooks/`, config in `.claude/settings.local.json` under `"hooks":{"PostToolUse":[{"matcher":"Write","hooks":[{"type":"command","command":"$CLAUDE_PROJECT_DIR/.claude/hooks/report-tracker.py"}]}]}`; run deterministically for guardrails/audit trails.
  - Subagents: add `"Task"` to allowed_tools; define `.claude/agents/*.md` (name/description/tools); orchestrator calls Task with `{description, prompt, subagent_type}`; subagent runs in separate context.
- Caveat: CLAUDE.md is context not constraint — agent prefers granular CSVs over CLAUDE.md summaries unless prompt explicitly steers to high-level numbers.
- `MODEL="claude-opus-4-6"` ("superior planning/reasoning").
- Cited URL: `https://www.anthropic.com/engineering/claude-code-best-practices`.
- QMX-fit: **general + Portfolio + workflow** (this is the richest blueprint). Mapping (inferred): subagents→DeepAgents subagents; hooks→LangGraph pre/post-tool middleware or guard nodes; plan mode→plan-then-execute graph; output styles→system-prompt middleware per persona; CLAUDE.md→injected context/store.

### claude-cookbooks/claude_agent_sdk/02_The_observability_agent.ipynb
- Patterns: **connecting external MCP servers** (stdio subprocess, docker) to the agent; tool scoping to force MCP-only behavior.
- Minimal mechanism: `mcp_servers` dict, e.g. git: `{"git":{"command":"uv","args":["run","python","-m","mcp_server_git","--repository",repo_root]}}`; GitHub: `{"github":{"command":"docker","args":["run","-i","--rm","-e","GITHUB_PERSONAL_ACCESS_TOKEN","ghcr.io/github/github-mcp-server"],"env":{...}}}`. `allowed_tools=["mcp__git"]` / `["mcp__github"]`; `disallowed_tools=["Bash","Task","WebSearch","WebFetch"]`; `permission_mode="acceptEdits"`.
- Key caveat (stated): `allowed_tools` alone only controls permission prompting, NOT availability — you **must** set `disallowed_tools` to actually restrict (else agent could use Bash + gh CLI instead of MCP).
- Numbers: git MCP ~13 tools; GitHub MCP 100+ tools. GitHub example is read-only CI analysis of facebook/react.
- Requires Docker running for GitHub MCP (containerised for isolation).
- Cited URLs: `https://modelcontextprotocol.io/docs/getting-started/intro`; `https://docs.claude.com/en/docs/claude-code/mcp`; github.com/github/github-mcp-server.
- QMX-fit: workflow/server agents (connect cTrader/MT5/CCXT/news via MCP), general copilot. Mapping (inferred): MCP servers are directly consumable by LangChain MCP adapters; `disallowed_tools` ≈ tool-filter middleware.

### claude-cookbooks/claude_agent_sdk/03_The_site_reliability_agent.ipynb
- Patterns: **read+write agent with safe write access**; **custom MCP tool server** (JSON-RPC over stdin/stdout, subprocess isolation); **PreToolUse validation hooks** that block; **HITL investigate/remediate split**; **skills** for institutional knowledge.
- Minimal mechanism:
  - MCP server registers 12 tools across Prometheus / Infrastructure / Diagnostics / Documentation; each tool = JSON Schema with rich `description` (descriptions drive tool selection more than prompt).
  - Server JSON-RPC methods: `initialize`, `notifications/initialized`, `tools/list`, `tools/call`; loop reads stdin line → dispatch → writes stdout.
  - SDK config: `mcp_servers={"sre":{"command":sys.executable,"args":[str(MCP_SERVER_PATH)]}}`; `allowed_tools=["mcp__sre__query_metrics", ...]` (pattern `mcp__{server}__{tool}`); `permission_mode="acceptEdits"`.
  - Safety layers: handler-level (path restricted to `config/`, shell cmd must start `docker-compose`/`docker`, container-name whitelist) + **PreToolUse hooks**: `hooks={"PreToolUse":[{"matcher":"mcp__sre__edit_config_file","hooks":[{"type":"command","command":"bash .../validate_pool_size.sh"}]}]}`. Non-zero hook exit **blocks** the tool call; agent sees error and adapts.
  - Skills: `ClaudeAgentOptions(skills=[".claude/skills/runbook/SKILL.md", ...])`; SKILL.md frontmatter name/description + "When to Use" + workflow.
  - Conditional tool registration: PagerDuty (4 tools) / Confluence (3 tools) appear only when env keys set; agent discovers via `tools/list`.
- Streaming: iterate `query()`; `isinstance(message, AssistantMessage)` → `TextBlock`/`ToolUseBlock`; `ResultMessage.is_error`.
- Design insight (stated): give write access via **narrow MCP tools with safety checks, not broad shell**; simple system prompt + good tool descriptions beats elaborate prompts; incident = observe→reason→act→repeat loop. `DB_POOL_SIZE` safe range 5–100.
- `MODEL="claude-opus-4-6"`.
- Cited URLs: modelcontextprotocol.io; docs.docker.com/get-docker; support.pagerduty/atlassian api-token pages.
- QMX-fit: **workflow + server agents** (long-running, remote; safe write to infra/trading-node), Portfolio (guarded actions). Mapping (inferred): MCP tool server = tools; PreToolUse hook = LangGraph `interrupt`/guard middleware or conditional edge; skills = retrievable instruction docs; investigate/remediate split = two-phase HITL graph.

### claude-cookbooks/claude_agent_sdk/04_migrating_from_openai_agents_sdk.ipynb
- Patterns: **primitive-by-primitive migration map**; custom tool via in-process MCP; guardrails as plain functions or `UserPromptSubmit` hook; sessions (in-memory + disk resume); OTel tracing; prompt caching; handoffs→subagents.
- Minimal mechanism:
  - Tool: `@tool("check_policy","<desc>",{"category":str,"amount":float})` async handler returns `{"content":[{"type":"text","text":...}]}`; bundle via `create_sdk_mcp_server(name="expense", tools=[...])` (in-process, no subprocess/network); reference as `mcp__expense__check_policy`.
  - `Agent(...)`→`ClaudeAgentOptions` field map: instructions→system_prompt, tools→mcp_servers+allowed_tools, model→model, input_guardrails→called in run fn.
  - Guardrails: plain fns before loop / on `ResultMessage.result`; or `UserPromptSubmit` hook via `HookMatcher(hooks=[fn])`, callback returns `{}` to allow or `{"decision":"block","reason":...}` to block. Caveat: when hook blocks, `ResultMessage.result` comes back **empty** (reason not surfaced) — hence plain functions preferred.
  - Events: `SystemMessage` (init), `AssistantMessage` (text/tool-use), `UserMessage` (tool-result), `ResultMessage` (last; `.result`, `.usage`, `.total_cost_usd`, `.session_id`). Final answer = `messages[-1].result`.
  - Sessions: in-memory = reuse open client; disk = capture `session_id` then `ClaudeAgentOptions(resume=session_id)` — transcript on local disk, survives restarts not machines.
  - Handoffs: `AgentDefinition(description, prompt, tools=[...])` passed as `ClaudeAgentOptions(agents={"approver":...})` + `allowed_tools=["Agent", ...]`; orchestrator **delegates and stays in control** (vs OpenAI handoff where B takes over). For true takeover use a thin Python dispatcher.
- Tracing/caching: `CLAUDE_CODE_ENABLE_TELEMETRY=1`, `OTEL_METRICS_EXPORTER=otlp`, `OTEL_EXPORTER_OTLP_ENDPOINT=...`; every tool call/API request tagged with `prompt.id`. System prompt + tool schemas cached automatically; subsequent same-prefix calls ≈ **10% of input token cost**; `usage.cache_creation_input_tokens`/`cache_read_input_tokens`.
- `OAI_MODEL="gpt-4.1"`, `CLAUDE_MODEL="claude-sonnet-4-6"`; openai-agents pinned 0.9.3.
- Cited URLs: `https://platform.claude.com/docs/en/agent-sdk/permissions`; `https://code.claude.com/docs/en/monitoring-usage`.
- QMX-fit: all — directly relevant since QMX uses LangChain not OpenAI SDK, but the tool/guardrail/session/caching primitives map across. Mapping (inferred): `@tool`+in-process MCP = LangChain tool; guardrails = input/output validators or middleware; `resume=`/session_id = checkpointer thread_id; caching = provider-level (proxy may need Anthropic beta headers — UNVERIFIED for proxy).

### claude-cookbooks/claude_agent_sdk/05_Building_a_session_browser.ipynb
- Patterns: **session persistence/management API** — the backend of a conversation sidebar (list, read, rename, tag, fork, delete) for a desktop/IDE agent product.
- Minimal mechanism (functions landed in `claude-agent-sdk` **v0.1.51**): `list_sessions(directory=, limit=, offset=)`→`SDKSessionInfo[]` (reads file stats + head/tail, no API/subprocess); `get_session_info(id, directory=)`; `get_session_messages(id, directory=, limit=, offset=)`→`SessionMessage[]` (`.type` user/assistant, `.uuid`, `.message` dict = Messages API shape); `rename_session(id, title, directory=)` (appends entry → `custom_title`); `tag_session(id, tag, directory=)` (single string, `None` clears; soft-delete via `"__hidden"`); `fork_session(source, directory=, title=, up_to_message_id=)`→ new id (copies transcript, remaps IDs, original untouched); resume fork via `ClaudeAgentOptions(resume=fork.session_id)`; `delete_session(id, directory=)` (hard delete).
- Storage: transcripts as JSONL under `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl`; same `cwd` = same bucket; all pure file ops (work whether or not agent running).
- `SDKSessionInfo` fields: session_id, summary, last_modified(ms), git_branch, cwd, custom_title, tag, first_prompt, created_at, file_size.
- Caveats: tags are single values (encode multi-axis as `"review:urgent"`); hard delete → prefer soft-delete tag; transcripts local only (sync/index for cross-host).
- `MODEL="claude-haiku-4-5"` (cheap for demo).
- Cited URLs: `https://docs.claude.com/en/agent-sdk/local-session-management`; `https://docs.claude.com/en/agent-sdk/typescript` (camelCase `listSessions`/`forkSession`).
- QMX-fit: **directly the desktop-UI session sidebar** for general/Lab/Portfolio copilots; fork = "try a different approach" branch. Mapping (inferred): maps onto LangGraph checkpointer threads + a store; fork ≈ checkpoint copy/branch; this is the UI-over-persistence layer QMX needs for its conversation history.

### claude-cookbooks/claude_agent_sdk/06_The_vulnerability_detection_agent.ipynb
- Patterns: **multi-stage pipeline** threat-model→find→triage→report; `ClaudeSDKClient` multi-turn (bootstrap+interview) vs stateless `query()` one-shots; recall-tuned find + independent triage (catch overconfidence); schema-conformant JSON output; preset system prompt with append.
- Minimal mechanism:
  - System prompt preset: `system_prompt={"type":"preset","preset":"claude_code","append":ENGAGEMENT_CONTEXT}` — keeps Claude Code default prompt (knows cwd) + appends scope context.
  - `cwd=str(TARGET_DIR)` + `allowed_tools=["Read","Grep","Glob"]` + `disallowed_tools=["Bash"]` = the entire read-only find-agent scaffold (replaces hand-rolled `while stop_reason=="tool_use"` loop + custom file tools).
  - Threat model = one `ClaudeSDKClient` session, 2 turns (bootstrap draft with open questions, then interview with owner answers) so turn 2 sees turn 1's tool results without re-sending source; writes `THREAT_MODEL.md` (`permission_mode="acceptEdits"`, allowed_tools Read/Write/Edit).
  - find/triage/report = independent `query()` calls; report uses explicit JSON Schema (all fields `required`, `null` for N/A), toolless `query(allowed_tools=[])`, strip ``` fences, `json.loads`.
- Key insight: the **quality-tier rubric** in the find prompt (report heap/stack overflow, UAF, controlled-write; note-but-skip assertion fails, stack exhaustion, null-deref) is most of the signal/noise difference.
- Safety: Claude applies real-time cyber safeguards at API layer; Cyber Verification Program (CVP) for dual-use work. Production would add Bash + `-fsanitize=address` inside a locked container; parallelise one query() per entry point via `asyncio.gather`.
- `MODEL_NAME="claude-opus-4-7"`.
- Cited URLs: `https://support.claude.com/en/articles/14604842-real-time-cyber-safeguards-on-claude`; `https://claude.com/claude-code-security`.
- QMX-fit: Lab copilot (code/security analysis, long experiments), workflow. Mapping (inferred): staged graph with one multi-turn subgraph + stateless nodes; triage-as-separate-pass = verifier node; structured report = `with_structured_output`.

### claude-cookbooks/claude_agent_sdk/07_Hosting_the_agent.ipynb
- Patterns: **deploying the same agent across 3 tiers** (Docker / Modal serverless / Kubernetes); process=session=container mental model; persistence via `resume=`+`/data`; auth gateway; egress lockdown; OTel; health/liveness.
- Minimal mechanism:
  - Agent SDK agent **is a process** (not an in-process object like OpenAI/Google ADK) → one container = one blast radius; hosting is a distributed-systems problem.
  - HTTP contract (all tiers): `GET /health → 200`; `POST /sessions/{session_id}/messages → text/event-stream`. ~100-line FastAPI `server.py`; **no auth in server** (gateway's job); server maps caller `session_id`→SDK's internal id (learned from first `ResultMessage`), persisted under `/data`, passes to `resume=` on follow-ups.
  - Tier1a ephemeral: `docker run` one prompt via env `PROMPT`, `run_once.py`→`send_query()`, exit (cron/queue/CI). Tier1b: docker-compose mounts `./sessions`→`/data` (transcripts survive restart); `CLAUDE_CONFIG_DIR` trick.
  - Tier2 Modal: `modal.Image.from_dockerfile`, `modal.Sandbox.create("serve", ..., volumes={"/data":vol}, encrypted_ports=[8000])`, per-deploy bearer token `AGENT_AUTH_TOKEN` (server enforces only when set); scale-to-zero. `modal.Volume` at `/data`; swap `SessionStore` for concurrent writers.
  - Tier3 k8s: authenticating gateway (tenant-scoped sessions, 403 cross-tenant), **pod-per-session** (gateway→Redis→pod), warm standby pool, egress lockdown (NetworkPolicy + allowlisting proxy so prompt-injected agent reaches only `api.anthropic.com`).
  - Production: hosted tool list narrowed to `WebSearch` only (no upload path; Read could leak other sessions'/env — prompt-injection risk). OTel via `OTEL_EXPORTER_OTLP_ENDPOINT`/`OTEL_SERVICE_NAME`. SessionStore mirror writes after local disk (`mirror_error` non-fatal).
- Numbers: end-to-end run ≈ $1–2 API + few cents Modal. Default hosting model `claude-sonnet-4-6` (set `MODEL=claude-opus-4-6` to match nb00).
- Caveat: server streams raw SDK message types — define a stable wire format for real APIs.
- Cited URLs: `https://platform.claude.com/docs/en/managed-agents/overview`; `https://code.claude.com/docs/en/agent-sdk/hosting` (+ /observability, /session-storage); modal.com; kind.sigs.k8s.io; Fly/E2B/Daytona/Cloudflare/Vercel sandbox snippets.
- QMX-fit: **server/background workflow agents** (long-running, remote VPS per operator rulings), general copilot backend. Mapping (inferred): QMX's "background workflow agents on a remote server" = tier2/3; session resume = checkpointer; egress lockdown + no-auth-in-agent + narrowed tools are directly relevant security patterns for a trading agent; Managed Agents is the "skip-infra" alternative to evaluate.
