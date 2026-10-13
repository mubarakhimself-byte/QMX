# Agent briefs used on 2026-10-13 evening

Every Agent call, in order, with its model and full prompt. Reuse these as templates; adapt paths and drop OpenAI-engine parts for the one-engine re-plan.


## 1. Verify harness facts in SDK docs | model opus | type general-purpose | 2026-10-13T15:51:50.267Z

```text
You are a primary-source researcher. Work ALONE: never use the Agent, Workflow or SendMessage tools; never spawn sub-agents. Write exactly one file (below). No git commands that write.

## Why
The operator (non-technical, owns QMX, a trading platform) is about to have a coding session build the QMX agent **harness**: QMX's own agents must work at least as well as vanilla Claude Code / Codex out of the box, on two engines: the **Claude Agent SDK (Python)** and the **OpenAI Agents SDK (Python)**. Builders will be told to read the docs themselves, so your job is NOT to summarise the SDKs. Your job is to settle the specific facts the plan depends on, with a citation for each, and to hand builders an exact reading list. Earlier research got some of this from scrapes and summaries; the operator was unhappy about that. **Read primary pages in the built-in browser** (tools `mcp__Claude_Browser__*`: navigate / get_page_text / find). Use WebFetch or Context7 only if a page won't load in the browser, and say which you used per fact. GitHub source code (raw files) counts as primary.

Existing prior research to check against (verify, correct, do not copy blindly):
- D:/QMX-worktrees/agent-system/tracker/qma-v2/BASELINE.md (parity matrix, 2026-10-13)
- D:/QMX-worktrees/agent-system/tracker/agent-system/research/01-agent-sdk-capability-audit.md, 19-two-sdk-study.md, 22-cookbooks-and-templates.md, 05-usage-limits-telemetry.md
- Local clones: D:/QMX-research/sources/repos/ (codex, openai-agents-python, maybe others)

## Facts to settle (answer each: VERIFIED / CORRECTED / UNVERIFIED, with URL or file:line, and the date of the page if shown)
Claude Agent SDK (Python):
1. Permission modes: exact names and behaviour; `can_use_tool` callback; allow/deny/ask rules syntax; whether rules come from settings files or code.
2. Hooks: which events exist in the SDK, which can block or modify input; in-code hook callbacks vs shell hooks.
3. Isolation from the user's personal Claude Code: `setting_sources` (or equivalent), `CLAUDE_CONFIG_DIR`, how to ensure no personal ~/.claude skills/agents/plugins/CLAUDE.md/memory load.
4. Auth on a **Claude Max subscription** (no API key): `claude setup-token` / `CLAUDE_CODE_OAUTH_TOKEN` / login in the SDK; what Anthropic's docs and terms say about a personal, single-user app using it. Quote the exact sentence(s).
5. Sessions: resume, fork, continue after process restart; where transcripts live; can we export them.
6. Compaction (automatic + manual) and prompt caching behaviour in the SDK; effort/thinking controls; model switch mid-session and its cache cost.
7. Sub-agents (AgentDefinition), skills, slash commands, MCP (in-process SDK MCP servers / custom tools), memory.
8. Computer use and browser: is computer use available through the Agent SDK on a subscription, or only via the API tool? What's the supported path.
9. Process model: does the Python SDK spawn the Claude Code CLI per session; any published memory figure; Windows/macOS/Linux support.
10. Usage / rate-limit info exposed to the app (rate-limit events, usage per message) so a usage page can show the 5-hour and weekly windows.

OpenAI Agents SDK (Python):
11. Sessions (SQLite etc.), long-running runs, RunState serialize/resume across restarts.
12. Human-in-the-loop approvals (`needs_approval`, interruptions), tool guardrails, hooks (RunHooks/AgentHooks) — can any of them BLOCK a tool call? What covers built-in tools like shell / apply_patch / computer?
13. Compaction: what exists (Responses API compaction, session compaction helpers) and whether it works with non-OpenAI models.
14. Non-OpenAI models: `OpenAIChatCompletionsModel`, LiteLLM, any-provider; OpenRouter specifically (base URL, tool calling, prompt caching passthrough).
15. Tracing: how to disable sending to OpenAI and add local processors.
16. Computer use: `ComputerTool`, current computer-use model name(s), what the operator gets. Also shell/apply_patch/hosted tools.
17. **Sign in with ChatGPT** for third-party apps (reportedly launched around 2026-09-29): can a personal/self-built app use a ChatGPT plan through the Agents SDK or via Codex (codex app-server / codex as a tool)? What is the legitimate route? Quote the terms.
18. Sub-agents: agents-as-tools, handoffs; MCP support; skills support if any.

Providers:
19. **Meta "Muse"** models (the operator wants them as a provider): what they are, whether there is a public API, endpoint compatibility (OpenAI-compatible? Anthropic-compatible?), availability via OpenRouter or OpenCode (Zen/Go), pricing/plans. If nothing exists by that name, say what the closest match is and flag it.
20. OpenRouter: Anthropic-compatible endpoint? usage/credits API for a usage page.

Cookbooks (the operator insisted on these):
21. From the Anthropic cookbook (github.com/anthropics/claude-cookbooks or current location) and the OpenAI cookbook (cookbook.openai.com): list the notebooks/guides relevant to: permissions & hooks, approvals, long-running agents, compaction/context management, caching, computer use, sub-agents, observability/tracing, SDK migration guides. For each: URL + one line on what pattern it shows + whether you opened it in the browser. Open at least the 8 most relevant ones and note the concrete pattern (function names) each uses.

## Output
Write D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H1-sdk-facts.md (create the folder). Structure: a 1-screen summary of what changed vs BASELINE.md; the 21 facts as a table (fact, verdict, answer in ≤3 lines, source, read-via); then "Builder reading list": the exact doc pages per harness area (engine, permissions/hooks, sessions, compaction/caching, router/providers, sub-agents/skills, computer use, tracing/export), ≤6 links per area. Plain words, short sentences. ≤350 lines. When done, reply with a 12-line summary flagging anything that breaks the plan (especially facts 4, 8, 13, 16, 17, 19).
```


## 2. Learn intended use of skills | model opus | type general-purpose | 2026-10-13T15:52:12.795Z

```text
You are a methodology researcher. Work ALONE: never use the Agent, Workflow or SendMessage tools; never spawn sub-agents. Write exactly one file (below). No git writes.

## Why
The operator ships code through Claude Code sessions. He has installed two skill sets and wants them used the way their **original creators** intend, not improvised:
- **pstack** (poteto's skills: poteto-mode with playbooks, how, why, architect, interrogate, arena, swarm, technical-writing, unslop, no-comments, create-verification-skill, show-me-your-work, figure-it-out, 24 principle-* skills, setup-pstack). He pointed at https://github.com/cursor/plugins/tree/main/pstack and https://github.com/backnotprop/pstack. Written for Cursor; poteto-mode has a "Harness" section mapping to Claude Code.
- **Matt Pocock's skills** (github.com/mattpocock/skills): wayfinder, grill-me, grilling, domain-modeling, to-spec, to-tickets, implement, tdd, triage, handoff, improve-codebase-architecture, codebase-design, prototype, diagnosing-bugs, setup-matt-pocock-skills.
Local installed copies: C:/Users/Mubarak/.claude/skills/<name>/SKILL.md (plus playbooks/, references/, scripts/). Note most have `disable-model-invocation: true`.

Read the creators' own pages in the **built-in browser** (`mcp__Claude_Browser__*`): repo READMEs, any docs/blog/video description pages they link, and the skill files on GitHub. Compare with the local copies (note version drift). Then read the local poteto-mode SKILL.md fully plus playbooks: orchestrate.md, autopilot-stack.md, autopilot-full.md, multi-phase-plan.md, feature.md, shipping.md, babysit.md, opening-a-pr.md, session-pickup.md, pause-safely.md; and the how, why, architect, create-verification-skill SKILL.md files.

## The concrete situation the recipe must fit
- A planning session (me) writes a harness plan: ~10 PR-sized units with dependencies (some parallel), into branch `rebuild/base` of the GitHub repo MubarakHimself/QMX (Python 3.14, uv workspace, `just ci` local CI, Windows 11 machine; worktrees on D:).
- The operator then pastes ONE prompt into a fresh Claude Code session = the **orchestrator**. It never writes code; it dispatches one builder sub-agent (`poteto-agent` type exists here) per PR, verifies each PR itself at the head SHA, merges into rebuild/base. Sub-agents in Claude Code CANNOT spawn sub-agents. Operator's model rules: Opus 5.5 (`model: opus`) or Sonnet 5.5 only; Fable only with his explicit OK; never the `bulk-worker` agent type (pinned to an old model). Max ~3-4 builders at once. Usage is a Claude Max 5x plan, so token-heavy skills (arena, swarm with 10 lanes) must be justified.
- A separate fresh session will wire a SvelteKit UI (browser-first) to the harness.
- pstack defaults name Cursor-only things (grok models, `control-ui`/`control-cli` from cursor-team-kit, Bugbot, Origin, `/loop`). Say what to substitute in Claude Code here (available locally: reticle, verify-ui-change, install-and-verify, agentic-tdd, audit-my-app, the built-in browser, the Monitor/ScheduleWakeup tools, `/loop`).

## Questions
1. How does each creator intend the skills to be sequenced (planning → plan → build → verify → land)? Quote short lines (<15 words) with links.
2. Which pstack playbook fits our orchestrator: Orchestrate, Autopilot-stack, Autopilot-full, or Multi-phase-plan + Shipping? Why, using the playbooks' own selection rules.
3. What exactly must the orchestrator prompt and the builder prompt contain for poteto-mode to work in Claude Code (how to "invoke" disable-model-invocation skills — typed slash command vs telling the agent to Read the SKILL.md; the /setup-pstack model rule; Harness mapping; what to do about swarm-based live verification lanes given sub-agents can't nest)?
4. Where Matt Pocock's skills fit (if at all) given decisions are already made: e.g. to-tickets for the plan format, tdd for builders, wayfinder only for fog. Be honest if they add nothing now.
5. Which verification approach builders should use for a Python backend + console with no UI yet (create-verification-skill? a control-cli substitute?), and for the UI session later.
6. Pitfalls seen in the last session: the skills were "followed in spirit" by sub-agents with their fan-out stripped and zero real Skill tool calls; Wayfinder "run by hand". Give rules that prevent this.

## Output
Write D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H2-skills-method.md: (a) one-screen recipe: the exact skill sequence for the orchestrator session, for each builder, and for the UI session; (b) paste-ready text blocks: "Method" section for the orchestrator prompt (≤40 lines) and "Method" section for the builder prompt template (≤30 lines); (c) substitutions table Cursor→Claude Code; (d) evidence (creator quotes + links, local file:line). ≤250 lines, plain words. When done, reply with a 10-line summary.
```


## 3. Map code and plan old-code deletion | model opus | type general-purpose | 2026-10-13T15:52:31.303Z

```text
You are a codebase cartographer (a pstack "/how"-style pass, done properly). Work ALONE: never use the Agent, Workflow or SendMessage tools; never spawn sub-agents. You may create ONE throwaway detached worktree and write ONE file. No commits, no pushes, no edits to existing files.

## Why
A coding session will build the new QMX agent **harness** ("QMA v2": two engines, Claude Agent SDK + OpenAI Agents SDK, one QMX-owned layer for permissions/hooks/tools, a session router across subscriptions, sessions, compaction/caching, usage page, console first, UI later). Builders need an exact map of the code they plug into and the code that will be retired. The old plan's packet 0a deleted code before anything replaced it; the operator delegated the deletion timing to us, so we need a safe, evidence-based deletion sequence.

## Setup
`git -C C:/Users/Mubarak/Desktop/QMX fetch origin` then `git -C C:/Users/Mubarak/Desktop/QMX worktree add --detach D:/QMX-worktrees/harness-survey origin/rebuild/base`. Work there (tip should be P16c PR #70, 4eac8f69 or newer). Do not run the full `just ci` (30+ min, needs a lock); targeted `uv run python -c "import ..."` or a small pytest selection is OK.

Prior maps to verify, not trust: D:/QMX-worktrees/agent-system/tracker/qma-v2/HOW-WHY.md (esp. :12-29, :401-452), D:/QMX-worktrees/agent-system/tracker/agent-system/research/24-how-why-integration-surface.md, tracker/qma-v2/BACKLOG.md items B1-B7, ARCHITECTURE.md §2.1-2.6 and §2.12.

## Questions (cite file:line for everything)
1. Workspace layout: packages, purpose in one line each, line counts (code vs tests), the uv workspace and Python version, `just ci` steps, how tests are organised, lint/type tools.
2. The integration surface the harness plugs into: qmx-control (HTTP routes for sessions/turns/events/approvals/workflows — which exist, which return not_implemented, e.g. service.py ~880-894), its database(s) and the SQLite single-writer issue (B1), how the app starts (qmb host start → qmx-control, PR #49), and the event/stream protocol the UI expects. Find the UI on branch `ui-review/repair` (worktree C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair) and note which backend endpoints/event shapes it calls.
3. The existing agent code: qmx-agents (LangChain/LangGraph/Deep Agents — what is there, who calls it), the old QMA runtime (qma-daemon, qma-core, qma-wire; P16c reduced it to ~113k lines), `native_claude.py` / `native_codex.py` / `native_sessions.py` (the only working Claude SDK recipe — summarise what's reusable), mini apps (`weekend-watcher`, `macro-daily-bias`) and how they use agents, qmx-tools, any router/accounts/usage code (P06 agents-spec-router, P07 memory provider, P08 guards, P20 hooks) that the new harness should reuse rather than rebuild.
4. Deletion sequence: for each old body of code, what keeps it alive (e.g. `qmb/src/qmb/doors/cli/host.py:104` starting the old daemon), what replaces it, and the earliest safe point (which harness unit must land first). Propose 2-3 deletion PRs with exact paths and the check that proves nothing broke. Flag anything that needs the operator's say (QMB edits need his authorisation).
5. Where the new package should live and its name (`qma2` was proposed) — any naming conflicts; what to pin (claude-agent-sdk, openai-agents current versions in lockfiles).
6. Anything that will trap builders: Windows paths, env vars (e.g. `ANTHROPIC_*` breaks the old daemon's native sessions), CI lock at D:/QMX-worktrees/.ci-lock, rclone on PATH, flaky/pre-existing failures on rebuild/base.

## Output
Write D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H3-code-map.md: summary (≤15 lines); sections per question; a "Builder quick-reference" (commands, entry points, test commands, conventions) ≤40 lines; the deletion plan table. ≤350 lines, plain words. Leave the survey worktree in place and say so. When done, reply with a 12-line summary.
```


## 4. Rebuild backlog and UI notes | model opus | type general-purpose | 2026-10-13T16:05:11.003Z

```text
You are a careful editor of a planning backlog. Work ALONE: never use the Agent, Workflow or SendMessage tools; never spawn sub-agents (nesting is technically possible here; you must not). Edit only the two files named below. No git commands that write.

## Context
QMX is the operator's trading platform. Its agent system "QMA v2" was planned in one long session (2026-10-12 08:13 UTC → 2026-10-13 04:30 UTC). On 2026-10-13 the operator ruled "harness first": ship only the agent harness now (two engines, Claude Agent SDK + OpenAI Agents SDK; parity with vanilla Claude Code/Codex; permissions/hooks; sessions; compaction/caching; router across accounts; usage page; a temporary console) plus the deletion of old agent code. Everything else is later. The operator says the backlog the last session wrote misses things he said, especially in the final hours (03:55–04:30 UTC on 2026-10-13): methodology for copilots and a "trader agent methodology", combining BMAD skills with Matt Pocock's skills as QMX's methodology, tooling, organogram derived later from the UI, workflows/graphs needing their own design pass, mini-app creation, computer use, and more.

Operator rulings 2026-10-13 evening (newest; they win): exactly ONE Claude Max account (never assume two); background agents may use only spare 5-hour Claude usage, default cap 50% editable; permission modes and hooks copied from what the Claude Agent SDK has built in and rebuilt on the OpenAI side; computer use via what the SDKs provide (OpenAI strongest), OpenCUA dropped; providers: Claude subscription, OpenRouter key, Meta "Muse" models, any OpenAI/Anthropic-compatible provider; UI wiring is a LATER session; deletion of old code follows the branching model (integration → staging → main, main only by his click; QMA v2 lands in rebuild/base for now).

## Inputs
S = C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/2cf20068-faee-4a56-b4c2-72888c00adb1/scratchpad
- S/digest/human.md: the operator's own messages. Read ALL of it; the last ~6 messages (2026-10-13 03:55 onward) in full detail.
- S/digest/dialog.md: Grep it for the 2026-10-13T03:5x–04:3x stretch to see the questions he was answering (Q1–Q4 at ~04:14, scope at ~04:15–04:22).
- Audits (decision ledger with latest-wins positions; "explicitly later" lists): D:/QMX-worktrees/agent-system/tracker/qma-v2/reviews/2026-10-13-forensic-session-audit.md (§2 and §5), 2026-10-13-planning-phase-audit.md, 2026-10-13-subagent-fleet-audit.md (§c: lost/ignored results to recover).
- Current backlog: D:/QMX-worktrees/agent-system/tracker/qma-v2/BACKLOG.md (B1–B23).
- Spin ideas: D:/QMX-worktrees/agent-system/tracker/qma-v2/USER-JOURNEYS.md §3 (25 ideas, unreviewed by him).
- UI-related material: research D:/QMX-worktrees/agent-system/tracker/agent-system/research/32-devops-and-ui-protocol.md Part B; HOW-IT-WORKS.md; anything UI the operator said.

## Tasks
1. Rewrite BACKLOG.md (same path). Keep every still-valid item and its id; mark items done or superseded with a one-line reason and date; fix stale wording (e.g. B22 "fold answers into the architecture" now belongs to the harness re-plan; B14 phone approvals; Q1-Q4 outcomes). Add every later-work item the operator raised that is missing, each with: what and why in plain words, his own words as a short quote (<15 words) with UTC timestamp, trigger (when it should be picked up), and "easy win?" Must include, if he said them: copilot methodology (Lab freedom vs Portfolio instruction, no single golden rule), trader-agent methodology, BMAD + Pocock skills as QMX methodology, system-prompt design, organogram/project homes derived from the UI, workflows/graphs/loops design pass (agentic, deterministic, mixed; graph and loop engineering), WF1/WF2, mini-app creation as plugins, computer use beyond the harness (cTrader/MT5 trials, demo accounts), memory bake-off and self-improvement, research harness/templates, Strats (the Library), QMB review, QML changes, remote/rented compute (adapters ready, Docker test), multi-provider coding-plan ideas he rejected (record as rejected, not backlog), voice/audio, phone approvals, branch cleanup, documentation-factory update, the 12 recoverable research items from the sub-agent audit §c. Group by theme with short headings. Keep it scannable: a table per theme.
2. Create D:/QMX-worktrees/agent-system/tracker/qma-v2/UI-NOTES.md: everything the future UI session must know that came up in planning (protocol decisions: keep today's 14 block kinds + SSE live channel per research 32; approvals as events; sub-agent tree; usage page T3-Code style with Claude window %; model-switch cost warning; console is temporary and gets deleted; transcript/log export button; computer-use cursor and screenshots; anything else the operator said about the UI). Each item with a source pointer. Plain words. ≤150 lines.

Do not invent items he never said; Claude's own ideas go in a separate section "Claude's suggestions (not his)". When done, reply with a 10-line summary: counts added/changed/closed, and anything you were unsure about.
```


## 5. how explorer: control plane | model sonnet | type general-purpose | 2026-10-13T16:12:21.386Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only: do not edit, create or delete any file; no git writes.

You are exploring a codebase to understand how something works. Gather facts. Trace code paths, read implementations, map components. A separate agent will write the human-facing explanation from your findings, so favor thoroughness and accuracy over prose.

Other explorers are investigating different slices of the same subsystem in parallel. Don't try to cover everything. Focus on your assigned angle and go deep.

## Question

> How does a chat session flow through QMX today (start of the app, a session, its blocks/events, approvals, the database, the MCP tool path), and exactly where would a new two-engine agent harness ("qma2": Claude Agent SDK + OpenAI Agents SDK, one QMX permission/hook layer, a turn route, approvals, a router across accounts, a usage ledger) plug in?

## Your Exploration Angle

The control plane. Code: the detached worktree D:/QMX-worktrees/harness-survey (origin/rebuild/base at 4eac8f69). Trace: (1) app start: `qmb host start` → qmx-control server; ports, home/data folder, config files, how secrets are read (look for Windows Credential Manager / keyring use, `qmx/*` labels), env vars; (2) qmx-control `service.py` and `server.py`: session create/list, `POST /api/sessions/{id}/blocks`, events paging, SSE `GET /api/events/{topic}` (polling loop, Last-Event-ID), the 14 SessionBlock kinds, the seven topics, the 501 routes (workflows ~880-894, cancel), runs/jobs tables; (3) the database: schema, every place a SQLite connection is opened, WAL settings, and the two-process issue where each qmx-tools MCP child builds its own ControlService (`qmx-tools/.../service.py:126-128`); (4) the MCP surface (52 operations over REST and MCP, `interrupt_on` meta) and how an agent would call QMX tools; (5) CI wiring a new package must join: `tools/ci.py`, `tools/test_all.py`, workspace pyproject test-ignore/ruff/pyright excludes, `justfile`. A prior map exists at D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H3-code-map.md: use it as a starting index, verify its claims against the code, and go deeper where it is thin (especially exact function signatures and data shapes a turn route and an approvals table would need).

## Exploration Instructions

Start by finding the relevant code. Use Glob to find directories and files, Grep to find key symbols, Read to understand the actual implementation. Don't guess from names. Read the code.

Follow this pattern:
1. **Find the entry point.** What triggers this behavior? A user action, an API call, a scheduled job? Find where it starts.
2. **Trace the flow.** Follow the call chain from the entry point. Read each function. Understand what data flows through and how it transforms.
3. **Map the key abstractions.** What types, interfaces, services, or classes are central? Read their definitions. Understand what they represent and why they exist.
4. **Find the boundaries.** Where does this subsystem interface with others? What goes in, what comes out?
5. **Look for the non-obvious.** Anything surprising? Anything that looks like a historical artifact? Anything a newcomer would misunderstand?

Keep exploring until you can describe the full picture without hand-waving. If you hit a part you can't trace, say so explicitly. "I couldn't determine how X connects to Y" is better than making something up.

## Output

Return your findings in this structure. Be factual and specific. Reference exact file paths, function names, type names, and line numbers where relevant.

### Components Found
### Flow
### Files Read
### Boundaries
### Non-Obvious Things
### Open Questions
```


## 6. how explorer: agent code | model sonnet | type general-purpose | 2026-10-13T16:12:34.183Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only: do not edit, create or delete any file; no git writes.

You are exploring a codebase to understand how something works. Gather facts. Trace code paths, read implementations, map components. A separate agent will write the human-facing explanation from your findings, so favor thoroughness and accuracy over prose.

Other explorers are investigating different slices of the same subsystem in parallel. Don't try to cover everything. Focus on your assigned angle and go deep.

## Question

> How does a chat session flow through QMX today (start of the app, a session, its blocks/events, approvals, the database, the MCP tool path), and exactly where would a new two-engine agent harness ("qma2": Claude Agent SDK + OpenAI Agents SDK, one QMX permission/hook layer, a turn route, approvals, a router across accounts, a usage ledger) plug in?

## Your Exploration Angle

The existing agent code the new harness replaces or reuses. Code: the detached worktree D:/QMX-worktrees/harness-survey (origin/rebuild/base at 4eac8f69). Trace: (1) the only working Claude Agent SDK recipe: `native_claude.py`, `native_codex.py`, `native_sessions.py` (where they live, how they spawn the SDK/CLI, options passed, how events are read, how sessions resume, env scrubbing, the `ANTHROPIC_*` refusal, Windows specifics, which tests cover them); (2) `qmx_agents` copilot path, especially `copilot.py:98-213` (engine events → QMX blocks) and how a copilot turn is run today (LangChain/LangGraph/Deep Agents `build_agent`), who calls it; (3) reusable non-LangChain modules: guards (`qmx_agents/guards/`), memory provider (P07), router and agent spec (P06), hooks (P20), money/broker refusal logic, usage or cost tracking if any; for each, whether it imports LangChain (transitively), its public API, and whether qma2 could import it as-is or should copy it; (4) the old QMA runtime (qma-daemon / qma-core / qma-wire): what still imports it (QMB tests, `qmn/examples/spot_paper_journey.py`, pyproject path settings, `tools/` scripts, `scripts/dev/qma_callers.py`), and what in it is worth keeping as a reference before deletion; (5) mini apps `weekend-watcher` and `macro-daily-bias`: how they invoke agents, so the deletion sequence knows what breaks. A prior map exists at D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H3-code-map.md: use it as a starting index, verify its claims, and go deeper where it is thin (exact signatures and data shapes).

## Exploration Instructions

Start by finding the relevant code. Use Glob to find directories and files, Grep to find key symbols, Read to understand the actual implementation. Don't guess from names. Read the code.

Follow this pattern:
1. **Find the entry point.** What triggers this behavior? A user action, an API call, a scheduled job? Find where it starts.
2. **Trace the flow.** Follow the call chain from the entry point. Read each function. Understand what data flows through and how it transforms.
3. **Map the key abstractions.** What types, interfaces, services, or classes are central? Read their definitions. Understand what they represent and why they exist.
4. **Find the boundaries.** Where does this subsystem interface with others? What goes in, what comes out?
5. **Look for the non-obvious.** Anything surprising? Anything that looks like a historical artifact? Anything a newcomer would misunderstand?

Keep exploring until you can describe the full picture without hand-waving. If you hit a part you can't trace, say so explicitly. "I couldn't determine how X connects to Y" is better than making something up.

## Output

Return your findings in this structure. Be factual and specific. Reference exact file paths, function names, type names, and line numbers where relevant.

### Components Found
### Flow
### Files Read
### Boundaries
### Non-Obvious Things
### Open Questions
```


## 7. why investigator: source control | model sonnet | type general-purpose | 2026-10-13T16:15:08.909Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Do not write, edit or delete any file; no git writes. Read-only git/gh commands only.

You are investigating the historical context and motivation behind a piece of code. A separate synthesizer combines your findings with other investigators' into a final answer, so gather evidence accurately rather than writing prose.

Other investigators search different sources in parallel. Don't try to cover everything. Focus on your assigned source and go deep.

## Operating Posture

Work like a careful, cautious, precise investigator. Don't produce a narrative. Surface evidence and describe it accurately, including the parts that don't fit a tidy story. The more boring and exact your output, the more useful it is. A single verbatim quote with a precise citation beats a paragraph of plausible-sounding summary.

- **Quote, don't paraphrase** when the exact wording matters.
- **Go wide before going deep.**
- **Track what you searched, not just what you found.** Record queries verbatim.
- **Resist the story.** Contradictions are the most interesting finding.
- **Consider the counterfactual.**
- **Never invent.** Label partial findings partial.

## The Question

> Why does QMX's current agent runtime have the shape it has (the LangChain/LangGraph/Deep Agents `qmx-agents` copilot; the old QMA runtime qma-daemon/qma-core/qma-wire; the native Claude Agent SDK subscription recipe; the guards, money-path admission and budgets of P08; the agents spec and OpenRouter router of P06; the memory provider of P07; the hooks of P20), and which of those reasons still bind a new two-engine harness (Claude Agent SDK + OpenAI Agents SDK, one QMX permission/hook layer) or the planned deletion of the old code?

## The Code Anchor

Repository: C:/Users/Mubarak/Desktop/QMX (GitHub MubarakHimself/QMX). Read code at the detached worktree D:/QMX-worktrees/harness-survey (origin/rebuild/base, 4eac8f69).

**Target files:** `qmx-agents/packages/qmx-agents/src/qmx_agents/guards/` (all), `qmx_agents/copilot.py` (esp. 98-213), `qmx_agents/router.py`, `qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_claude.py` and siblings `native_codex.py`, `native_sessions.py`, `qma/daemon/hooks/` (registry, ledger_gate, source_bounds, timeouts), `qma/daemon/envs/router.py`, `qmb/src/qmb/doors/cli/host.py` (~:104), `rebuild/packets/P06-agents-spec-and-router.md` and sibling packet docs.

**Key symbols:** build_agent, Copilot, guards, admission, budgets, journal, ledger_gate, native session, host start.

**Initial commits (most recent first):** 3512ae3d (P16b notebook port), f9a0c1d9 (compose guarded Copilot sessions), af932192 (child activity before parent approval), e2d199c3, 9eb263c9 (deterministic Copilot app hooks), c0c781ca (evidenced app road to live), 7289e13b (broker settings, Portfolio reads, default Copilot tools), e40627c5 (bounded native SDK subscription sessions), fd12459c (offline native SDK session lifecycle), 582720d1 (P20 hooks merge), e339ff96 (P08), 668e57ae (P07), 697b5a09 (P06), 5d645b67 (P06 OpenRouter tiers); P16 deletion PRs #49-#70.

**PR numbers:** #31 (P06), #33 (P07), #35 (P08), #44 (P20), #49-#57 (P16b slices), #58-#70 (P16c). Pull bodies and review comments with `gh pr view <n> --json title,body,comments,reviews,files` (repo MubarakHimself/QMX).

**Ticket IDs:** none known; check PR bodies for references to `rebuild/DESIGN*.md` sections (e.g. DESIGN §12c.1).

## Your Assigned Source

Source control (git history, `gh` PRs, in-repo comments, tests, packet docs under `rebuild/packets/`, ADRs if any).

Search guide: expand the seed list with `git log --follow`, pickaxe `git log -S`, `git blame`, `git show`; pull PR context with gh; `rg -n -C2 '(TODO|FIXME|HACK|NOTE)'` near targets; related tests (names encode edge cases). Pitfalls: squash-merge flatlands, misleading messages, cargo-culted patterns, bot commits, treating code as intent. The guards and admission code are defensive (money path), so also hunt for incident-driven origins: commits saying "fix", "revert", "defensive", "refuse", "money", "live", and tests encoding a past failure.

## Investigation Instructions

Gather evidence. Don't answer the question directly. Cast a wide net, read whole PRs, follow links within source control only, capture quotes verbatim with location, note absences and contradictions. Record cross-source leads (design docs, transcripts) under Additional Leads; do not chase them.

## Output Format

### Source
### What I Searched
### Direct Evidence Found (what it says, where, author and date, relevance)
### Indirect / Circumstantial Evidence (what, where, what it suggests, alternative readings)
### Contradictions
### Gaps
### Additional Leads
```


## 8. why investigator: design docs | model sonnet | type general-purpose | 2026-10-13T16:19:20.402Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Do not write, edit or delete any file; no git writes.

You are investigating the historical context and motivation behind a piece of code. A separate synthesizer combines your findings with other investigators' into a final answer, so gather evidence accurately rather than writing prose.

Other investigators search different sources in parallel (one covers git history and PRs). Don't try to cover everything. Focus on your assigned source and go deep.

## Operating Posture
Careful, cautious, precise. Surface evidence, don't narrate. Quote verbatim with precise citations. Go wide before deep. Record what you searched. Contradictions are the most interesting finding. Consider the counterfactual. Never invent; label partial findings partial.

## The Question
> Why does QMX's current agent runtime have the shape it has (the LangChain/LangGraph/Deep Agents `qmx-agents` copilot; the old QMA runtime qma-daemon/qma-core/qma-wire; the native Claude Agent SDK subscription recipe; the P08 guards, money-path admission and budgets; the P06 agents spec and OpenRouter router; the P07 memory provider; the P20 hooks; the qmx-control session/blocks/events design with no turn route and no approvals table), and which of those reasons still bind a new two-engine harness (Claude Agent SDK + OpenAI Agents SDK, one QMX permission/hook layer) or the planned deletion of the old code?

## The Code Anchor
Code at D:/QMX-worktrees/harness-survey (origin/rebuild/base 4eac8f69). Targets: qmx-agents/packages/qmx-agents/src/qmx_agents/{guards/, copilot.py, router.py, spec.py}; qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_{claude,codex,sessions}.py; qmx-agents/packages/qmx-control/src/qmx_control/service.py; qmb/src/qmb/doors/cli/host.py. PRs #31 (P06), #33 (P07), #35 (P08), #44 (P20), #49-#70 (P16 deletions).

## Your Assigned Source
Long-form design documents and recorded deliberation (this repo has no Notion/Slack MCP; its long-form record is in-repo docs and exported session transcripts):
- Design and packet docs on rebuild/base: `rebuild/` (DESIGN*.md incl. §12c.1, `rebuild/packets/P*.md`, `rebuild/COPILOT.md`, `rebuild/research/`), `docs/` (the documentation-factory knowledge base: AGENTS.md, ADRs, constitution, decision ledger, component specs for QMA/agents), `_bmad-output/` planning artifacts if any. Read via `git -C D:/QMX-worktrees/harness-survey show HEAD:<path>` or the files in that worktree.
- Planning docs on branch plan/agent-system: D:/QMX-worktrees/agent-system/tracker/ (map.md, agent-system/archive/*, agent-system/research/*, qma-v2/HOW-WHY.md, qma-v2/BASELINE.md, qma-v2/reviews/2026-10-13-forensic-session-audit.md §2 decision ledger).
- Operator deliberation: C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/2cf20068-faee-4a56-b4c2-72888c00adb1/scratchpad/digest/human.md (the operator's own words, 2026-10-12/13) — Grep it; read relevant stretches.
- Project memory notes: C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/memory/*.md (e.g. qmx-agentic-langgraph-shift.md, qmx-agent-sdk-effort.md, qmx-operator-standing-rules.md, qma-v2-harness-rulings.md).
Search for: why LangChain/LangGraph/Deep Agents were chosen (and when dropped), why the native Claude SDK recipe was bounded to subscription sessions and refuses `ANTHROPIC_*` env, why money-path admission is read-only/refusal-based, why approvals were LangGraph interrupts, why sessions are append-only blocks with events, why the old daemon was kept alive (DESIGN §12c.1), why QMB is protected (operator authorisation), and any stated constraint on deleting old code (branching model integration → staging → main; "build beside, switch, then delete"). The money-path code is defensive: hunt for incident-driven origins (a past failure, a "never again" ruling).

## Investigation Instructions
Gather evidence, don't answer. Read whole documents' relevant sections. Follow links within docs only; record cross-source leads (git commits, PRs) under Additional Leads without chasing them. Quote verbatim with file:line. Note absences and contradictions (e.g. an old doc ruling vs a newer operator ruling — record both with dates).

## Output Format
### Source
### What I Searched
### Direct Evidence Found (what it says, where, author/date, relevance)
### Indirect / Circumstantial Evidence (what, where, what it suggests, alternative readings)
### Contradictions
### Gaps
### Additional Leads
```


## 9. how explainer: harness surface | model opus | type general-purpose | 2026-10-13T16:19:42.005Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only on the codebase. Write exactly ONE file: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/how/HOW-harness-surface.md. No git writes.

You are writing an architectural explanation for a senior engineer. Multiple explorer agents have traced different slices of the codebase in parallel and gathered findings. Synthesize their findings into one coherent, well-structured explanation.

## Original Question

> How does a chat session flow through QMX today (start of the app, a session, its blocks/events, approvals, the database, the MCP tool path), and exactly where would a new two-engine agent harness ("qma2": Claude Agent SDK + OpenAI Agents SDK, one QMX permission/hook layer, a turn route, approvals, a router across accounts, a usage ledger) plug in?

## Explorer Findings

Read both files in full; they are the findings:
- D:/QMX-worktrees/agent-system/tracker/qma-v2/research/how/explorer-control-plane.md
- D:/QMX-worktrees/agent-system/tracker/qma-v2/research/how/explorer-agent-code.md
Prior index they both verified: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H3-code-map.md. SDK facts (for the plug-in points): D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H1-sdk-facts.md.

## Instructions

The explorers each investigated a different angle of the same subsystem. Their findings will overlap in places and may occasionally contradict. Reconcile them. Merge overlapping descriptions, resolve contradictions by checking the code yourself, and combine the separate slices into a unified picture.

Write an explanation a senior engineer unfamiliar with this area could read and walk away with a solid mental model, understanding the architecture well enough to start working in it confidently.

You have read-only access to the codebase (D:/QMX-worktrees/harness-survey, origin/rebuild/base 4eac8f69) to check anything, clarify a detail, or fill a gap. Use Read, Grep, and Glob as needed. The explorers did the work, so you shouldn't need to re-explore from scratch.

## Output Format

### Overview
1-2 paragraphs.
### Key Concepts
### How It Works
The core and the longest section. Walk through the flow. Prose, not pseudocode; reference files and functions. Include a mermaid diagram where a flow involves multiple components.
### Where Things Live
### Gotchas
Also add, because the reader will design against this: a final section **Plug-in points for qma2**, a table: concern (turn route, approvals table + answer route, block projection, usage ledger, router/accounts, secrets, sub-agent child sessions, money refusal, single-writer DB, CI wiring, package placement and import rules) → where it attaches in today's code (file:line) → what must be new vs reused/copied → known traps.

## Communication Style
Concrete language; say exactly which function calls which. Explain why something is complex. Don't pad simple things. Acknowledge the explorers' open questions and gaps rather than hiding them. Mark anything you inferred rather than read. ≤350 lines.
```


## 10. why investigator: source control (Opus) | model opus | type general-purpose | 2026-10-13T16:22:24.409Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Do not write, edit or delete any file; no git writes. Read-only git/gh commands only.

You are investigating the historical context and motivation behind a piece of code. A separate synthesizer combines your findings with other investigators' into a final answer, so gather evidence accurately rather than writing prose.

Other investigators search different sources in parallel (one covers design documents and transcripts). Focus on your assigned source and go deep.

## Operating Posture
Careful, cautious, precise. Surface evidence, don't narrate. Quote verbatim with precise citations. Go wide before deep. Record queries verbatim. Contradictions are the most interesting finding. Consider the counterfactual. Never invent; label partial findings partial.

## The Question
> Why does QMX's current agent runtime have the shape it has (the LangChain/LangGraph/Deep Agents `qmx-agents` copilot; the old QMA runtime qma-daemon/qma-core/qma-wire; the native Claude Agent SDK subscription recipe; the P08 guards, money-path admission and budgets; the P06 agents spec and OpenRouter router; the P07 memory provider; the P20 hooks; the qmx-control session/blocks/events design with no turn route and no approvals table), and which of those reasons still bind a new two-engine harness (Claude Agent SDK + OpenAI Agents SDK, one QMX permission/hook layer) or the planned deletion of the old code?

## The Code Anchor
Repository C:/Users/Mubarak/Desktop/QMX (GitHub MubarakHimself/QMX). Read code at D:/QMX-worktrees/harness-survey (origin/rebuild/base 4eac8f69).
**Target files:** `qmx-agents/packages/qmx-agents/src/qmx_agents/guards/` (all), `qmx_agents/copilot.py` (98-213), `qmx_agents/router.py`, `qmx_agents/spec.py`, `qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_{claude,codex,sessions,boundary}.py`, `qma/daemon/hooks/`, `qmx-agents/packages/qmx-control/src/qmx_control/service.py` (sessions, blocks, events, OPERATIONS, `/sign` operator-only route), `qmb/src/qmb/doors/cli/host.py` (~:104, :1785-1836), `rebuild/packets/P*.md`.
**Key symbols:** build_agent, stream_turn, Copilot, check_descriptor, money_path, AdmissionGate, RunJournal, ClaudeSessionBackend, check_environment, NativeSessionProvider, ControlService, sessions_append, OPERATIONS, interrupt_on.
**Initial commits (most recent first):** 3512ae3d, f9a0c1d9, af932192, e2d199c3, 9eb263c9, c0c781ca, 7289e13b, e40627c5 (bounded native SDK subscription sessions), fd12459c, 582720d1 (P20), e339ff96 (P08), 668e57ae (P07), 697b5a09 (P06), 5d645b67.
**PRs:** #31 (P06), #33 (P07), #35 (P08), #44 (P20), #49-#57 (P16b), #58-#70 (P16c). Use `gh pr view <n> --repo MubarakHimself/QMX --json title,body,comments,reviews,files`.

## Your Assigned Source
Source control: git history, gh PRs and reviews, in-repo comments, tests (names encode edge cases), packet docs under `rebuild/packets/`. Search: `git log --follow`, `git log -S`, `git blame`, `git show`; `rg -n -C2 '(TODO|FIXME|HACK|NOTE)'` near targets. Pitfalls: squash-merge flatlands, misleading messages, cargo-culted patterns, treating code as intent. The money-path and env-refusal code is defensive: hunt for incident-driven origins ("fix", "revert", "refuse", "never", "live", "money", "subscription").

## Investigation Instructions
Gather evidence; don't answer. Cast wide, read whole PRs, follow links within source control only, quote verbatim with location, note absences and contradictions. Record cross-source leads under Additional Leads without chasing them.

## Output Format
### Source
### What I Searched
### Direct Evidence Found (what it says, where, author and date, relevance)
### Indirect / Circumstantial Evidence (what, where, what it suggests, alternative readings)
### Contradictions
### Gaps
### Additional Leads
```


## 11. why investigator: design docs (Opus) | model opus | type general-purpose | 2026-10-13T16:22:39.281Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Do not write, edit or delete any file; no git writes.

You are investigating the historical context and motivation behind a piece of code. A separate synthesizer combines your findings with other investigators' into a final answer, so gather evidence accurately rather than writing prose.

Other investigators search different sources in parallel (one covers git history and PRs). Focus on your assigned source and go deep.

## Operating Posture
Careful, cautious, precise. Surface evidence, don't narrate. Quote verbatim with precise citations. Go wide before deep. Record what you searched. Contradictions are the most interesting finding. Consider the counterfactual. Never invent; label partial findings partial.

## The Question
> Why does QMX's current agent runtime have the shape it has (the LangChain/LangGraph/Deep Agents `qmx-agents` copilot; the old QMA runtime qma-daemon/qma-core/qma-wire; the native Claude Agent SDK subscription recipe; the P08 guards, money-path admission and budgets; the P06 agents spec and OpenRouter router; the P07 memory provider; the P20 hooks; the qmx-control session/blocks/events design with no turn route and no approvals table), and which of those reasons still bind a new two-engine harness (Claude Agent SDK + OpenAI Agents SDK, one QMX permission/hook layer) or the planned deletion of the old code?

## The Code Anchor
Code at D:/QMX-worktrees/harness-survey (origin/rebuild/base 4eac8f69). Targets: qmx-agents/packages/qmx-agents/src/qmx_agents/{guards/, copilot.py, router.py, spec.py}; qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_{claude,codex,sessions}.py; qmx-agents/packages/qmx-control/src/qmx_control/service.py; qmb/src/qmb/doors/cli/host.py. PRs #31, #33, #35, #44, #49-#70.

## Your Assigned Source
Long-form design documents and recorded deliberation (no Notion/Slack MCP exists; the long-form record is in-repo docs and exported transcripts):
- On rebuild/base (worktree above): `rebuild/` (DESIGN*.md incl. §12c.1, `rebuild/packets/P*.md`, `rebuild/COPILOT.md`, `rebuild/research/`), `docs/` (knowledge base: AGENTS.md, ADRs, constitution, decision ledger, component specs for agents/QMA).
- Operator deliberation: C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/2cf20068-faee-4a56-b4c2-72888c00adb1/scratchpad/digest/human.md (his own words 2026-10-12/13). Grep it; read relevant stretches.
- Current decision ledger (latest-wins): D:/QMX-worktrees/agent-system/tracker/qma-v2/reviews/2026-10-13-forensic-session-audit.md §2.
- Project memory: C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/memory/*.md.
- EVIDENCE ONLY, NOT THE PLAN: D:/QMX-worktrees/agent-system/tracker/qma-v2/archive/2026-10-13-wednesday-frame/ (superseded plan; read its SUPERSEDED.md first) and D:/QMX-worktrees/agent-system/tracker/agent-system/archive/. Cite them only as "what was said then", never as current intent.
Search for: why LangChain/LangGraph/Deep Agents were chosen and when dropped; why the native Claude recipe is bounded to subscription sessions and refuses `ANTHROPIC_*`; why money-path admission is refusal-based and proposals need operator signature; why approvals were LangGraph interrupts; why sessions are append-only blocks with events; why the old daemon was kept alive (DESIGN §12c.1); why QMB edits need operator authorisation; any stated constraint on deleting old code (branching model integration → staging → main; "build beside, switch, then delete"). Defensive code: hunt for incident-driven origins.

## Investigation Instructions
Gather evidence, don't answer. Read relevant sections fully. Follow links within docs only; record git/PR leads under Additional Leads. Quote verbatim with file:line. Record contradictions between older docs and newer operator rulings with both dates.

## Output Format
### Source
### What I Searched
### Direct Evidence Found (what it says, where, author/date, relevance)
### Indirect / Circumstantial Evidence (what, where, what it suggests, alternative readings)
### Contradictions
### Gaps
### Additional Leads
```


## 12. why synthesizer: harness rationale | model opus | type general-purpose | 2026-10-13T16:32:11.057Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only on code and git. Write exactly ONE file: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/why/WHY-harness.md. No git writes.

You are answering a "why" question about a piece of code by synthesizing findings from multiple investigators who searched different historical sources. Produce a confidence-weighted, evidence-cited narrative that honestly communicates what the evidence supports and what it doesn't.

## The Question
> Why does QMX's current agent runtime have the shape it has (the LangChain/LangGraph/Deep Agents `qmx-agents` copilot; the old QMA runtime qma-daemon/qma-core/qma-wire; the native Claude Agent SDK subscription recipe; the P08 guards, money-path admission and budgets; the P06 agents spec and OpenRouter router; the P07 memory provider; the P20 hooks; the qmx-control session/blocks/events design with no turn route and no approvals table), and which of those reasons still bind a new two-engine harness (Claude Agent SDK + OpenAI Agents SDK, one QMX permission/hook layer) or the planned deletion of the old code?

## The Code Anchor
Code at D:/QMX-worktrees/harness-survey (origin/rebuild/base 4eac8f69). Targets: qmx-agents/packages/qmx-agents/src/qmx_agents/{guards/, copilot.py, router.py, spec.py}; qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_{claude,codex,sessions,boundary}.py; qmx-agents/packages/qmx-control/src/qmx_control/{service.py, server.py}; qmb/src/qmb/doors/cli/host.py. Key symbols: build_agent, stream_turn, check_descriptor, AdmissionGate, RunJournal, ClaudeSessionBackend, check_environment, ControlService.sessions_append, OPERATIONS, interrupt_on.

## Investigator Findings
Read both in full:
- D:/QMX-worktrees/agent-system/tracker/qma-v2/research/why/investigator-source-control.md
- D:/QMX-worktrees/agent-system/tracker/qma-v2/research/why/investigator-design-docs.md

## Sources That Weren't Searched
- Issue / ticket tracker: not searched as a separate source. The repo's GitHub PRs were covered by source control; no Linear/Jira MCP exists.
- Real-time team chat: no MCP available. The closest record is the operator's exported session transcripts, covered by the design-docs investigator.
- Infrastructure observability, error tracking, product analytics: no MCP available; QMX has never run in production, so none would exist.

## Epistemics Framework
Read C:/Users/Mubarak/.claude/skills/why/references/epistemics.md in full before writing. Key rules: tiers Direct, Supported, Inferred, Speculative, Unknown; every Direct/Supported claim cited; hedge inferred and speculative claims; never cite code as evidence for its own intent; document gaps; treat any hypothesis in the question as a candidate.

## Instructions
1. Read all findings. 2. Reconcile overlaps. 3. Surface contradictions, don't pick silently. 4. Calibrate confidence. 5. Spot-check citations you are unsure of (read the cited file or run `git show`/`gh pr view --repo MubarakHimself/QMX`). 6. Don't overreach.
Note: newest operator rulings win over older design docs. The current ledger is D:/QMX-worktrees/agent-system/tracker/qma-v2/reviews/2026-10-13-forensic-session-audit.md §2 and D:/QMX-worktrees/agent-system/tracker/qma-v2/BACKLOG.md (rulings table at the top). Anything under tracker/qma-v2/archive/ is "what was said then", not current intent.

## Output Format
Use exactly: The Question; The Code in Question; What We Found ([Direct]/[Supported] bullets with citations); What We Can Reasonably Infer ([Inferred]); Competing Hypotheses; What We Don't Know; Sources Consulted (all seven categories); Confidence Summary.
Then ADD one final section for the designers who read this next: **Constraints that bind the new harness**, a table with columns: constraint, binds (harness design / deletion / both), keep / drop / re-decide, evidence tier, source. Cover at least: money-path barrier and the propose_order exemption; operator-only answer path and the shared bearer token; single journal/DB writer; subscription-only Claude with no token storage and no paid fallback; isolation of QMX's Claude home; the native-recipe lockdown versus the operator's "same tools as Claude Code" baseline (this is the sharpest conflict; state what the evidence says about why the lockdown existed and what would have to be true to lift it); approvals bound to exact content; append-only typed block log; one API with two doors (OPERATIONS); Windows path hardening; guarded sub-agents; strangler / build-beside-then-delete; QMB edit authority; no data migration; ADR-0020's ratified cut on foreign agent runtimes (still never amended). ≤300 lines.

Quality check before returning: every found-claim cited; tier-appropriate phrasing; contradictions surfaced; specific gaps named; no code cited as its own intent; calibrated tone.
```


## 13. architect runner 1 (Opus) | model opus | type general-purpose | 2026-10-13T16:35:31.481Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only everywhere except your own output folder: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/candidate-1-opus/ . No git writes. Do not write product code into the repo; your sketch files live only in your folder.

You are producing one candidate design in architect's parallel exploration. Read the **architect** skill in full first (C:/Users/Mubarak/.claude/skills/architect/SKILL.md). That's the workflow you're inside. Output a candidate design package: type sketch, function signatures, module map, and prose rationale shaped per C:/Users/Mubarak/.claude/skills/architect/references/rationale-template.md. Also screen your design against C:/Users/Mubarak/.claude/skills/architect/references/design-red-flags.md before you finish.

Apply the following discipline. The orchestrator compares candidates on these axes to pick a base.

- Caller's usage first. Write the README-style usage and two or three real call sites before the types, then derive the type sketch from them. The usage is the spec. The two must agree, so reconcile the sketch to the usage, not the reverse.
- Data structures first. Get the core types right and the code becomes obvious. Trace each dominant access pattern through the proposed structure. If the answer is "we'll add a map / index / cache later," the structure is wrong.
- Interface depth. Compare the capability hidden behind the public surface relative to the size of that surface. Prefer a simple interface that pulls complexity into the callee, even when the implementation becomes less simple. Do not put transport or wire types on the public API. Parse into domain types behind the interface.
- Shared state: if two actors might both write, ask "what happens?" If the answer isn't "nothing," default to per-actor state with a merge at the read boundary, per the **separate-before-serializing-shared-state** principle skill.
- Make boundaries visible. `not implemented` errors for bodies, `# TODO` pseudocode for tricky logic, doc comments stating intent and invariants. A reader should trace data from input to output by reading types and signatures alone.
- Encode invariants in types: hard-to-misuse types > runtime checks > prose comments, per the **encode-lessons-in-structure** principle skill.
- Validate at boundaries, trust types inside, per the **boundary-discipline** principle skill. Business logic as pure functions. The shell stays thin.
- Single source of truth per invariant. Derive instead of sync.
- Idempotent state transitions where applicable, per the **make-operations-idempotent** principle skill. Ask what happens if the operation runs twice or crashes halfway.
- Short call chains. If tracing the flow needs more than three files, flatten the hierarchy, per the **laziness-protocol** and **minimize-reader-load** principle skills.

You are one of the parallel runners, each on a different model. Produce the best design your model can make. Don't hedge against the others. Differences between candidates are the signal used to pick a base and graft. Converging on a safe-looking middle defeats the exploration.

## The task and the grounding
Read D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/FRAME.md in full: its "Task" section is your assignment (design.md, sketch/, units.md), and its "Grounding" list names the ONLY current sources (paths there are relative to D:/QMX-worktrees/agent-system/). Do NOT read the "Rubric" section. Also read the /why synthesis D:/QMX-worktrees/agent-system/tracker/qma-v2/research/why/WHY-harness.md (especially its final constraints table) and the /how synthesis D:/QMX-worktrees/agent-system/tracker/qma-v2/research/how/HOW-harness-surface.md. Never treat anything under tracker/qma-v2/archive/ as the plan.

When done, reply with a 12-line summary of your design's shape, how it resolves each "Known tension" in FRAME.md, and your unit list.
```


## 14. architect runner 2 (Fable) | model fable | type general-purpose | 2026-10-13T16:35:42.013Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only everywhere except your own output folder: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/candidate-2-fable/ . No git writes. Do not write product code into the repo; your sketch files live only in your folder.

You are producing one candidate design in architect's parallel exploration. Read the **architect** skill in full first (C:/Users/Mubarak/.claude/skills/architect/SKILL.md). That's the workflow you're inside. Output a candidate design package: type sketch, function signatures, module map, and prose rationale shaped per C:/Users/Mubarak/.claude/skills/architect/references/rationale-template.md. Also screen your design against C:/Users/Mubarak/.claude/skills/architect/references/design-red-flags.md before you finish.

Apply the following discipline. The orchestrator compares candidates on these axes to pick a base.

- Caller's usage first. Write the README-style usage and two or three real call sites before the types, then derive the type sketch from them. The usage is the spec. The two must agree, so reconcile the sketch to the usage, not the reverse.
- Data structures first. Get the core types right and the code becomes obvious. Trace each dominant access pattern through the proposed structure. If the answer is "we'll add a map / index / cache later," the structure is wrong.
- Interface depth. Compare the capability hidden behind the public surface relative to the size of that surface. Prefer a simple interface that pulls complexity into the callee, even when the implementation becomes less simple. Do not put transport or wire types on the public API. Parse into domain types behind the interface.
- Shared state: if two actors might both write, ask "what happens?" If the answer isn't "nothing," default to per-actor state with a merge at the read boundary, per the **separate-before-serializing-shared-state** principle skill.
- Make boundaries visible. `not implemented` errors for bodies, `# TODO` pseudocode for tricky logic, doc comments stating intent and invariants. A reader should trace data from input to output by reading types and signatures alone.
- Encode invariants in types: hard-to-misuse types > runtime checks > prose comments, per the **encode-lessons-in-structure** principle skill.
- Validate at boundaries, trust types inside, per the **boundary-discipline** principle skill. Business logic as pure functions. The shell stays thin.
- Single source of truth per invariant. Derive instead of sync.
- Idempotent state transitions where applicable, per the **make-operations-idempotent** principle skill. Ask what happens if the operation runs twice or crashes halfway.
- Short call chains. If tracing the flow needs more than three files, flatten the hierarchy, per the **laziness-protocol** and **minimize-reader-load** principle skills.

You are one of the parallel runners, each on a different model. Produce the best design your model can make. Don't hedge against the others. Differences between candidates are the signal used to pick a base and graft. Converging on a safe-looking middle defeats the exploration.

## The task and the grounding
Read D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/FRAME.md in full: its "Task" section is your assignment (design.md, sketch/, units.md), and its "Grounding" list names the ONLY current sources (paths there are relative to D:/QMX-worktrees/agent-system/). Do NOT read the "Rubric" section. Also read the /why synthesis D:/QMX-worktrees/agent-system/tracker/qma-v2/research/why/WHY-harness.md (especially its final constraints table) and the /how synthesis D:/QMX-worktrees/agent-system/tracker/qma-v2/research/how/HOW-harness-surface.md. Never treat anything under tracker/qma-v2/archive/ as the plan.

When done, reply with a 12-line summary of your design's shape, how it resolves each "Known tension" in FRAME.md, and your unit list.
```


## 15. arena cross-judge (Fable) | model fable | type general-purpose | 2026-10-13T17:00:05.389Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only: write exactly ONE file, D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/JUDGE.md. No git writes.

You are the cross-judge in an arena. Two candidate designs for the same task were produced independently. Score each against the rubric, criterion by criterion, then recommend a base with rationale, and name the 2-4 strongest ideas in the losing candidate worth grafting into the base.

- Task and rubric: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/FRAME.md (read all of it, including "Rubric" and "Known tensions").
- Candidate A: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/candidate-1-opus/ (design.md, units.md, sketch/).
- Candidate B: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/candidate-2-fable/ (design.md, units.md, sketch/).
- Design red flags to screen: C:/Users/Mubarak/.claude/skills/architect/references/design-red-flags.md.
- To check claims against facts: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H1-sdk-facts.md, research/how/HOW-harness-surface.md, research/why/WHY-harness.md (constraints table), BASELINE.md H1-H18 (with its Known corrections box). Code: D:/QMX-worktrees/harness-survey (read-only).

Judge as a skeptical senior engineer. Read both candidates end to end before scoring. For each rubric criterion give each candidate a 1-5 score with a one-paragraph justification citing file:line in the candidate. Then:
1. Red-flag screen per candidate (shallow module, information leakage, temporal decomposition, pass-through, split ownership, two ways to do one task, importable internals, hand-synced list).
2. Factual errors: any claim that contradicts H1-sdk-facts or the code (e.g. Claude SDK hook callbacks available in Python, can_use_tool behaviour, ChatGPT route, computer use, setting_sources isolation, per-session RAM).
3. Cost realism on a Claude Max 5x plan and a Windows 11 laptop: process count and memory per live chat, idle behaviour, how many builders' worth of work each unit is.
4. The first unit: does it really prove a live Claude turn on his subscription with the least code?
5. Recommended base, with the reason a future maintainer can extend it more easily without breaking invariants; prefer the cleaner boundary or smaller API when tied.
6. Grafts from the other candidate (what, where it goes, why).
7. Anything both candidates missed.
≤220 lines. Reply with a 10-line summary: scores per criterion, base pick, grafts.
```


## 16. interrogate reviewer A (Opus) | model opus | type general-purpose | 2026-10-13T17:10:23.955Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only: write nothing, no git writes. Return your findings as your final message.

You are an adversarial code reviewer. Find real problems in the design below: bugs, design flaws, security issues, and maintainability concerns. You are not here to be helpful or encouraging. You are here to stress-test.

## Intent
The author's stated intent:
> Give QMX one agent harness ("qma2") whose floor is vanilla Claude Code / Codex: the same tools, permission modes and rules, hooks, sub-agents, skills, project instructions, memory, compaction and caching, on two engines (Claude Agent SDK on the operator's single Claude Max subscription with no token ever stored by QMX; OpenAI Agents SDK on ChatGPT sign-in or any OpenAI-compatible API key such as OpenRouter or Meta Muse). One QMX policy point decides every tool call on both engines; money stays read-only for agents (proposals only, he signs); sessions last days, survive restarts and usage-window lockouts, and export with one action; a router balances whole sessions across accounts with background work capped at 50% of the Claude 5-hour window; a usage page shows the window; a temporary browser console lets him sign off by chatting; platform-neutral; no sandbox. It must plug into today's qmx-control (OPERATIONS registry, 14 block kinds, SSE) without adding writers to control.db, and it must be shippable as small PRs, the first proving one live Claude turn.

You are reviewing whether the design achieves this intent well. Do NOT question the intent itself.

## Under review (read all)
- D:/QMX-worktrees/agent-system/tracker/qma-v2/HARNESS.md (the design; its "Amendments" section overrides the sketch)
- D:/QMX-worktrees/agent-system/tracker/qma-v2/sketch/ (Python 3.14 type sketch: qma2/ and qmx_control/ changes)
- D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/candidate-1-opus/units.md (unit plan; HARNESS Amendment A5 splits U1 into U0/U1/U1b)
Facts to check against: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H1-sdk-facts.md, research/how/HOW-harness-surface.md (Gotchas), research/why/WHY-harness.md (constraints table), BASELINE.md (with its corrections box). Code: D:/QMX-worktrees/harness-survey (origin/rebuild/base), read-only. Ignore anything under tracker/qma-v2/archive/.

## Review rubric and code-quality lens
Read and apply: C:/Users/Mubarak/.claude/skills/interrogate/references/rubric.md and C:/Users/Mubarak/.claude/skills/interrogate/references/code-quality-review.md. Pay special attention to: can any path let an agent move money or answer its own approval; does any SDK fact used contradict H1; races between the actor, the host link and the single writer; restart and crash behaviour; Windows specifics (Job Objects, paths, env merge); whether each unit's live check actually proves its claim; hidden dependencies that break the parallel lanes.

## Instructions
For each finding: **Severity** (critical | warning | nit), **Finding** with location (file:line or symbol), **Evidence** (show reasoning), optional **Suggestion**. Reference specific code. Distinguish "broken" from "I would do it differently". No praise. Zero findings is valid.

## Output
## Findings
### 1. [Severity] Short title
**Location** / **Finding** / **Evidence** / **Suggestion**
...
```


## 17. interrogate reviewer B (Fable) | model fable | type general-purpose | 2026-10-13T17:10:33.846Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only: write nothing, no git writes. Return your findings as your final message.

You are an adversarial code reviewer. Find real problems in the design below: bugs, design flaws, security issues, and maintainability concerns. You are not here to be helpful or encouraging. You are here to stress-test.

## Intent
The author's stated intent:
> Give QMX one agent harness ("qma2") whose floor is vanilla Claude Code / Codex: the same tools, permission modes and rules, hooks, sub-agents, skills, project instructions, memory, compaction and caching, on two engines (Claude Agent SDK on the operator's single Claude Max subscription with no token ever stored by QMX; OpenAI Agents SDK on ChatGPT sign-in or any OpenAI-compatible API key such as OpenRouter or Meta Muse). One QMX policy point decides every tool call on both engines; money stays read-only for agents (proposals only, he signs); sessions last days, survive restarts and usage-window lockouts, and export with one action; a router balances whole sessions across accounts with background work capped at 50% of the Claude 5-hour window; a usage page shows the window; a temporary browser console lets him sign off by chatting; platform-neutral; no sandbox. It must plug into today's qmx-control (OPERATIONS registry, 14 block kinds, SSE) without adding writers to control.db, and it must be shippable as small PRs, the first proving one live Claude turn.

You are reviewing whether the design achieves this intent well. Do NOT question the intent itself.

## Under review (read all)
- D:/QMX-worktrees/agent-system/tracker/qma-v2/HARNESS.md (the design; its "Amendments" section overrides the sketch)
- D:/QMX-worktrees/agent-system/tracker/qma-v2/sketch/ (Python 3.14 type sketch: qma2/ and qmx_control/ changes)
- D:/QMX-worktrees/agent-system/tracker/qma-v2/research/architect/candidate-1-opus/units.md (unit plan; HARNESS Amendment A5 splits U1 into U0/U1/U1b)
Facts to check against: D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H1-sdk-facts.md, research/how/HOW-harness-surface.md (Gotchas), research/why/WHY-harness.md (constraints table), BASELINE.md (with its corrections box). Code: D:/QMX-worktrees/harness-survey (origin/rebuild/base), read-only. Ignore anything under tracker/qma-v2/archive/.

## Review rubric and code-quality lens
Read and apply: C:/Users/Mubarak/.claude/skills/interrogate/references/rubric.md and C:/Users/Mubarak/.claude/skills/interrogate/references/code-quality-review.md. Pay special attention to: can any path let an agent move money or answer its own approval; does any SDK fact used contradict H1; races between the actor, the host link and the single writer; restart and crash behaviour; Windows specifics (Job Objects, paths, env merge); whether each unit's live check actually proves its claim; hidden dependencies that break the parallel lanes.

## Instructions
For each finding: **Severity** (critical | warning | nit), **Finding** with location (file:line or symbol), **Evidence** (show reasoning), optional **Suggestion**. Reference specific code. Distinguish "broken" from "I would do it differently". No praise. Zero findings is valid.

## Output
## Findings
### 1. [Severity] Short title
**Location** / **Finding** / **Evidence** / **Suggestion**
...
```


## 18. Write harness and deletion plans | model opus | type poteto-agent | 2026-10-13T17:25:36.171Z

```text
Read the poteto-mode skill's SKILL.md in full (C:/Users/Mubarak/.claude/skills/poteto-mode/SKILL.md), including its Principles section, before any work. Then read C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/multi-phase-plan.md in full and C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/orchestrate.md in full. Read ~/.agents/pstack-models.md.

HARD LIMITS: Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents (where a playbook step wants a subagent, do it yourself and note "inline: no nested agents allowed"). Write only the two plan files named below. No git commands that write. No product code.

## Your job
You are the plan author in the Multi-phase plan playbook (you own the plan, not the code). Write TWO plan files, each in the playbook's skeleton exactly, each passing the checker:
1. D:/QMX-worktrees/agent-system/tracker/qma-v2/HARNESS-PLAN.md — the harness build program.
2. D:/QMX-worktrees/agent-system/tracker/qma-v2/DELETION-PLAN.md — the old-code deletion program that runs only after the operator signs off the harness.
Execution playbook for both: `playbooks/orchestrate.md` (a standing program run by one coordinator chat that dispatches one `poteto-agent` builder per PR on model `opus`; at most 3 builders in flight; the coordinator verifies each PR itself at the head SHA and merges into `rebuild/base`; never `main`, never `integration`). Landing: the coordinator merges verified PRs in dependency order with `gh pr merge --merge` (repo MubarakHimself/QMX).

## Sources (the ONLY current ones; paths relative to D:/QMX-worktrees/agent-system/tracker/qma-v2/)
- `HARNESS.md` — the design contract. Its Amendments (A1-A11) win over the sketch; A11 makes `research/interrogate/VERDICT.md` rules V1-V6 binding. Read both in full.
- `sketch/` — type sketch.
- `research/architect/candidate-1-opus/units.md` — the base unit list. It is NOT amended; you must apply HARNESS A5 (U0/U1/U1b split), A6, A8, A10 and VERDICT V6 (new dependency graph U0 → U1 → U1b → {U2, U4-core}; U4 parity checks after U2+U3; U4 key entry needs the operator principal; one owner of host/openai.py per wave; U1 check proves the policy point; host capacity rules; qmx-tools refused in agent MCP config).
- `research/H3-code-map.md` (builder quick-reference, CI facts, deletion plan D1-D3), `research/how/HOW-harness-surface.md`, `research/why/WHY-harness.md`, `research/H1-sdk-facts.md`, `research/H2-skills-method.md` (orchestrator/builder method blocks and Cursor→Claude Code substitutions), `BACKLOG.md`, `UI-NOTES.md`.
- Never use anything under `archive/` as the plan.

## Program facts to encode
- Repo C:/Users/Mubarak/Desktop/QMX, GitHub MubarakHimself/QMX, base branch `rebuild/base` (tip 4eac8f69 or newer). Builders work in their own worktree under `D:\QMX-worktrees\`. CI: `just ci` (~29 min) under the exclusive lock `D:\QMX-worktrees\.ci-lock`, at most two pytest workers, `ANTHROPIC_*` unset in the CI env, rclone on PATH (one test fails without it), `python -m poethepoet` (poe.exe blocked). New package `qmx-agents/packages/qma-v2` imported as `qma2`; joins `tools/ci.py`, `tools/test_all.py`, the qmx-agents workspace members/sources and the test-ignore/ruff/pyright exclude lists (H3 §9 and the control-plane explorer §5).
- Model rules: builders and verifiers `opus`. Sonnet only for very small tasks. Fable never in this program. Never the `bulk-worker` agent type. Builders never spawn sub-agents (the coordinator also sets CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1 if the operator applied it; say so as an assumption).
- Live checks (HARNESS A10): his single Claude Max plan, short prompts, every live model turn logged, stop a unit's checks at 15 Claude turns unless he raises it, model-agnostic checks on OpenRouter. Claude sign-in is done by the operator himself (`/login` in QMX's claude-home); the coordinator stops and asks him at that step.
- Live lanes: the checker requires exactly ten lanes per PR in the form "Ten lanes on `opus` at the PR head". Write them as coverage boxes the COORDINATOR runs itself inline in one boot (not ten agents; say this once in "How to read this" and in the Boot recipe). Each lane names a concrete scenario, what it saves (`Save \`<file>\`` — a console screenshot via the built-in browser for UI lanes, a text log for API lanes) and "Pass when <predicate>". Lane 1 is the regression lane against trunk. Make the lanes come from the unit's done-when, live check, BASELINE H-items and VERDICT rules; no filler.
- Perf block per PR: a real metric where one exists (time to first token, gate round-trip per tool call, host+CLI working set, cache-read ratio, compaction time, router pick latency); otherwise an absolute budget on the diff-added work, as the playbook allows.
- Review gate: PRs that change what the operator sees (the console in U1b, approval cards in U2, the OpenRouter chat in U4, the usage page and switch warning in U5, and the final sign-off PR) are review-gated: screenshots plus a short screen recording saved under `tracker/qma-v2/review/`, posted in chat, stop at merge-ready for his click. Others write the "None" form.
- The harness program ends with a SIGN-OFF unit: he signs in with Claude in the console and does the things in his own words (read and edit files, run commands, search the web, start a helper, an approval prompt, a money refusal, restart and continue, switch the chat to an OpenRouter model, see his Claude window on the usage page).
- Deletion program (DELETION-PLAN.md): build beside, switch, then delete; deletion PRs also go to `rebuild/base`. Use H3 §4 / deletion table: D1 old QMA runtime (qma-daemon, qma-core, qma-wire, their tests/examples, pyproject path settings, tools/ scripts, `qmn/examples/spot_paper_journey.py`, the unused QMB `invoke_host_*` helpers + `host.py:104` constant + their tests) — first copy the native recipe reference into `qma2` docs if U1 did not; QMB and QMN edits need the operator's explicit go, so D1 is review-gated and stops for his word. D2 (LangChain `qmx-agents` package) is BLOCKED inside this program because `qmx_remote`'s worker executors and `qmx_apps` still import it and workflows are out of scope; write D2 as a PR section whose Build re-points the remaining guard imports (journal, money) to qma2 and removes only what has no caller, and record the rest as backlog with the exact blockers. D3 (old `apps/qmx-ui`) is out of scope: record it in an appendix as backlog (UI session later; the ui-review/repair branch has never been pushed and is the only copy).
- Branching model to state in both plans: work lands in `rebuild/base`; integration → staging → main is the operator's later move; main only by his click; no branch or worktree deletion without his go.

## Method (required, logged)
- Run the multi-phase-plan steps. Step 2 (prototypes): there are none to run in a planning-only pass; Appendix A lists the probes each unit runs instead (from HARNESS A8 and VERDICT V4.5/V4.4/V5) and marks them unproven.
- Step 5: call the Skill tool for `technical-writing` and then `unslop` before finalising each file (if the Skill tool refuses, Read the SKILL.md in full and say so). How-to body, appendices for explanation. No long dashes, no curly quotes, no mid-sentence colons.
- Step 6: run `node C:/Users/Mubarak/.claude/skills/poteto-mode/scripts/check-plan.mjs <plan.md>` on each file and fix every line until it prints no problems. Note the checker expects literal markers ("git show origin/main:", "/loop 1h", "status message", the RULE sentence, "One box is one unit of work", "names the evidence", "Check a box only when its evidence exists", "playbooks/"). The pstack skills here are installed locally under C:/Users/Mubarak/.claude/skills/, not in this repo: write the "Read these from trunk" boxes so they are true here (the local skill paths), and keep the `git show origin/main:` marker on the line that re-reads the repo's own docs (e.g. `git show origin/rebuild/base:...` is fine only if the checker accepts it; test it).
- Keep each plan as short as the skeleton allows. Target: harness plan ≤ 700 lines, deletion plan ≤ 250 lines.

## Report
Reply with: both paths, the PR ids in dependency order with their parallel lanes, which are review-gated, the final checker output for each file (verbatim), every skill you used marked "Skill tool" or "Read", and anything in the sources you found contradictory.
```


## 19. Cross-model review of the trail | model fable | type general-purpose | 2026-10-13T17:44:47.232Z

```text
Do NOT use the Agent, Workflow or SendMessage tools and never spawn sub-agents. Read-only; write nothing. Return your review as your final message.

You are the cross-model reviewer required by the show-me-your-work skill (C:/Users/Mubarak/.claude/skills/show-me-your-work/SKILL.md, section "Cross-model review of the trail"; read it). The work was done by an Opus 5.5 planning session; you are a different model family. Not a redo of the work: a scan for what the operator should pay attention to.

Read:
- The decision trail: D:/QMX-worktrees/agent-system/tracker/qma-v2/trail/decisions.tsv
- The run's transcript: C:/Users/Mubarak/.claude/projects/C--Users-Mubarak-Desktop-QMX/2cf20068-faee-4a56-b4c2-72888c00adb1.jsonl (large; use Grep and Read with offset/limit; focus on the stretch from the operator's "good evening" message onward, i.e. after the three audits).
- The outputs: D:/QMX-worktrees/agent-system/tracker/qma-v2/{README.md, PROMPT-HARNESS.md, PROMPT-DELETION.md, HARNESS.md (Synthesis decision and Amendments), HARNESS-PLAN.md (Program checklist, U0, U1, SIGNOFF), DELETION-PLAN.md (header, D1 gate), research/interrogate/VERDICT.md}.
- The operator's evening instructions (verbatim in the transcript): he wanted the harness coding prompt and the deletion of old code only, the UI left out but noted, the backlog updated, skills used for real per their creators, sub-agents preferred, Opus not Sonnet for anything substantive, Fable allowed this evening, the earlier session's files kept from poisoning agents, efficient and thorough.

Flag:
- Decisions logged with weak or absent evidence; rows whose evidence path does not resolve or does not show what the row claims (spot-check several).
- Verification steps skipped or claimed without proof in the transcript.
- Choices that look risky in hindsight (premature, scope-creeping, papering over a symptom), including anything the planning session decided that was really the operator's call, or anything it asked him that it should have decided.
- Gaps between what the operator asked this evening and what was delivered.
- Anything in the prompts that would let the coding session repeat the earlier session's failures (skills imitated, Sonnet/bulk-worker use, nested agents, stale files, acting before the operator reads).

Output: a list of flags, each pointing at a specific row (ts) or transcript moment or file:line, most important first. "No flags" is valid. ≤60 lines.
```
