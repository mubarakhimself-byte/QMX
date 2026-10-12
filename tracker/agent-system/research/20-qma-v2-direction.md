# 20: QMA v2 direction (operator positions + what the real pages say)

Written 2026-10-12, evening. It records two things:
- the operator's latest positions (dictated after the two-SDK study);
- what Claude found by reading the pages he linked in a browser, not through summaries.

Nothing here is re-charted onto the map yet. That happens with him, next.

---

## 1. Operator positions (latest wins)

**Name and scope**
- **QMA v2.** QMA means "Quant agents". It is a restructure, not a deletion of the name. Rebuild the agentic system cleanly.
- **Out of scope for QMA v2:**
  - the Library (a refactor comes later, possibly git-like; name the seam in code and docs);
  - QMB (to be reorganised later from its own documentation).
- **QML will change** (the proposal in the risk-and-sizing session transcript). QMF's role is unclear to him.
- **Stays as it is:**
  - the research;
  - his scenarios;
  - mini-app building;
  - the QML research;
  - the harness research.
- **Needs enhancing:** the backend API and database.
- **Mini-app runtime:** solid enough for now; may need a refactor later.

**Branching**
- Three branches: `integration` (everything that works), `staging` (ready to be used and integrated), `main` (his click only).
- Every other branch and worktree is clutter.
- The branching mechanism replaces "build beside the old one, then delete".
- Saved to memory.

**Documents**
- Old documents are archived, not deleted. They over-complicate things for agents.

**Engines**
- The Claude Agent SDK and the OpenAI Agents SDK.
- He wants Claude Code's *capabilities* (tools, sessions, hooks, sub-agents, permissions, plugins), **not the Claude Code CLI**.

**Memory**
- Use each SDK's default memory, and keep QMX's pluggable memory layer on top.

**Media**
- GPT audio and image are wanted later. Voice is a later feature.

**Plugins**
- A plugin is MCP/tools + skills + a model + hooks.
- A session loads a plugin by default.
- The organogram becomes plugins: a Lab plugin, a Portfolio plugin, and so on.
- Cross-engine idea: a plugin that lets an OpenAI-engine agent use a Claude agent, and the reverse.

**Sub-agents**
- He prefers Claude's sub-agent pattern.
- Workers on the OpenAI engine are acceptable.
- Defaults are configurable in Settings and per workflow.

**Router**
- It balances usage and resources across providers and sessions, so QMX never relies on one provider. It never balances single requests.
- Defaults pick a provider per workflow or sub-agent (for example "this workflow uses DeepSeek"), and the copilot can configure them.
- It replaces CLIProxy.

**Workflows**
- Build QMX's own graph instead of LangGraph.
- Claude's dynamic workflows are the model to copy.
- The workflow design started from n8n. Workflows and mini apps can be agentic or not.

**Compaction**
- A configurable summariser with a chosen model (Hermes-style) is fine.

**Tracing**
- Use the SDKs' tracing and logs, stored locally, never sent to OpenAI.

**Sandboxes**
- Not needed by default. Sandcastle and others exist if that changes.

**Server**
- He has a server (Contabo).
- Long-running and cron workflows run there by design. The UI configures it.
- No Amp orbs: not paid for.

**Wednesday minimum**
- The copilot works.
- He can create, run, maintain and edit mini apps and workflows, agentic and not.
- The organogram works.
- Sub-agents work.
- Server workflows work.

**Mini-apps transcript**
- A long ChatGPT-web session about how mini apps and workflows began. It isn't attached yet; he may add it for a dedicated reader later.

---

## 2. What the pages actually say

### 2.1 Claude Agent SDK ([overview](https://code.claude.com/docs/en/agent-sdk/overview))

**What it is**
- "A library that runs the Claude Code binary, with Claude Code's capabilities, such as built-in tools, permissions, sessions, and hooks."
- The CLI is a separate row in that table ("the terminal interface, built for daily interactive use").
- So QMX never shows or uses a CLI.
- Under the hood the library starts the Claude Code program as a background process per session. That process is where the RAM per session goes.

**Capabilities listed**
- built-in tools
- hooks
- sub-agents
- MCP
- permissions
- sessions
- skills, commands and memory
- plugins (loaded by local path)

**Subscription**
- The overview says third-party developers may not *offer* claude.ai login in their products.
- The help centre, updated 7 October 2026, says: "You can still use the Claude Agent SDK, claude -p, and third-party apps with your subscription limits."
  (https://support.claude.com/en/articles/15036540)
- For the operator's own QMX, signing in with his own plan is the documented case.

**New: monthly API credits** (https://support.claude.com/en/articles/17154008)
- Max 5x gets $100 a month; Max 20x gets $200.
- They cover:
  - the plain Claude API (Messages and Batches);
  - Managed Agents;
  - the Agent SDK when run with an API key from the linked Console organisation.
- They are claimed by linking one Console organisation per plan. They don't roll over. They are separate from plan limits.
- **Consequence:** Claude can also run as a plain API model inside QMX's light in-process engine, paid by plan credits, with no Claude Code process. Two Max plans give two organisations, so two keys for the router.

**System prompt** ([modifying-system-prompts](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts))
- Three choices:
  - a minimal default;
  - the `claude_code` preset, optionally with `append`;
  - a fully custom string, where "the SDK sends only what you provide".
- Python can load a large prompt from a file.
- `setting_sources=[]` keeps CLAUDE.md and user settings out.
- So QMX writes its own system prompts (XML-structured meta prompts are fine) and keeps the static part stable for caching.

**Dynamic workflows** ([blog, 2 June 2026](https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code))
- A JavaScript script with `agent()`, `parallel()` and `pipeline()`. It can choose the model and the worktree per agent, and resumes after an interruption.
- Why they exist: agentic laziness, self-preferential bias, goal drift after compaction.
- Six patterns:
  - classify-and-act
  - fan-out-and-synthesize
  - adversarial verification
  - generate-and-filter
  - tournament
  - loop until done
- Uses listed:
  - migrations
  - deep research
  - deep verification
  - sorting
  - rule adherence
  - root cause
  - triage with quarantine
  - evals
  - model routing via a classifier agent
- Saved workflows live in `~/.claude/workflows` or inside a skill as templates.
- They pair with `/loop` and `/goal`.

### 2.2 OpenAI ([agents guide](https://developers.openai.com/api/docs/guides/agents))

There are three runtimes:
- **Agents API:** OpenAI runs a managed Codex harness. It has compaction, multi-agent, programmatic tool calling and MCP.
- **Agents SDK:** runs inside your app, with your tools, storage and approvals.
- **Responses API:** raw model calls.

The Agents SDK is the QMX fit. It is provider-neutral through OpenAI-compatible endpoints (study 19 §1). Shell and file-edit tool types exist; QMX supplies the small executor that runs them on its machine (study 19 §2).

### 2.3 Amp orbs ([docs](https://ampcode.com/docs/orbs), [portals](https://ampcode.com/docs/orbs/portals), [note](https://ampcode.com/notes/putting-an-agent-in-an-orb))

**What an orb is**
- A remote machine where the agent works while the laptop is closed.
- It sleeps for free and wakes with the conversation, files and services in place.
- The thread gives you tabs:
  - a changes (diff) view;
  - a Files pane with upload;
  - a Terminal tab on a shared tmux session;
  - follow-along from phone;
  - `amp sync` to the local checkout.

**Portals**
- `.amp/services.yaml` declares long-running services: command, port, health check, environment, and links between services.
- Amp supervises them: list, status, logs, restart, stop. It also exposes an authenticated preview URL.
- A review widget lets you click an element in the running app and send a comment to the agent.
- **This is the process manager pattern for QMX mini apps.**

**Preparing the environment**
- `.agents/setup` prepares a fresh machine (idempotent), and the result is snapshotted for 24 hours.
- `.agents/resume` does quick repair work on each wake.
- `/__dev/*` endpoints log the agent in and give a `preflight` readiness report.
- All logs go to one agent inbox folder.
- 41 AGENTS.md files.
- The principle: "don't make them guess".

### 2.4 Harness, loop and graph (his three clippings)

**The layers** (beamnxw, 2026-07-25)
- Harness = the environment: context, actions, persistence, execution control, safety, observability.
- Loop = feedback. Each loop has a trigger, goal, state, action policy, evidence, feedback and stop rule. Loop on evidence, never on "the agent says it's done".
- Graph = flow: node boundaries, state schema, routing, concurrency, cycles and exits, durability.
- The graph runs inside the harness, and loops live inside the graph. Formalise stable paths only after watching traces.

**Loop vs graph** (Sumanth, 2026-08-18)
- A loop is one node in a graph.
- Start with a loop. Add a graph when you need parallel tracks, different contexts or permissions per agent, or auditable control flow.

**Quant loop** (RohOnChain, 2026-06-22)
- Six pieces:
  - automation (`/loop`, `/goal`)
  - a skill with lessons learned
  - a state file
  - a separate verifier, ideally a different model (maker-checker)
  - worktrees
  - connectors
- Five stages: ingest → signal → verify → execute → risk monitor.
- Lessons are written back to the skill: self-improvement.
- **QMX difference:** execution stays behind the money-path barrier. Agents propose; the operator signs.

---

## 3. Claude's view (for the operator to react to)

1. **Two engines behind one QMA v2 `Engine` shape is right, and simpler than I made it sound.**
   - Claude Agent SDK for Claude-Code-capability sessions, on the plan.
   - OpenAI Agents SDK for light in-process agents on any compatible provider, now including Claude by API key on the Max-plan credits.
   - RAM stops being a wall: only sessions that need Claude Code's capabilities pay the per-session process.

2. **The long-running orchestrator.**
   - It stays alive because its session is saved and resumed by ID, plus a progress/state file it reads and writes.
   - Compaction only keeps its context under the window; it is not what keeps it alive. Anthropic's own lesson: compaction alone wasn't enough, the progress file and git history were.
   - It uses a custom QMA system prompt (static, cache-friendly) and plugins, not Claude Code's coding prompt.

3. **Plugins as the unit of the organogram: yes.**
   - The Claude Agent SDK already loads plugins (skills, agents, hooks, MCP).
   - QMA v2 uses that one plugin format and writes a loader that maps it onto the OpenAI SDK, which has no plugin system.
   - The cross-engine "delegate" ships as a plugin too.

4. **QMA's own graph instead of LangGraph: agreed, with the rebuild.**
   - Workflows are graph JSON (n8n-like): nodes are code, agent loop, mini-app call or human gate; edges carry typed state.
   - A small runner checkpoints each node in SQLite and resumes.
   - Claude's six dynamic-workflow patterns ship as built-in templates. A dynamic workflow the copilot writes is saved as a graph the UI can render and re-run.
   - Risk to manage: retries, timeouts and parallel joins must be designed in, not added later.

5. **Every agent node is a loop with an evidence-based stop rule and a separate verifier.** Lessons write back to skills (with approval). That is QMX's self-improvement path.

6. **The Contabo server becomes QMX's own "orb".**
   - Setup and resume scripts.
   - Mini apps declared as supervised services with health checks and authenticated preview links.
   - One agent log inbox.
   - The UI drawer tabs (Activity, Artifacts, Diff, Terminal, Browser) already match Amp's tabs.

7. **Memory:** SDK defaults (Claude's CLAUDE.md/auto memory and memory tool; OpenAI Sessions and the sandbox "lessons" memory) behind QMX's pluggable interface.

8. **Tracing:** Claude exports OpenTelemetry natively; OpenAI's tracing gets a local exporter and is never uploaded. Both go into one QMX log store.

**Open points for the operator (asked later, through the question tool, after he reads):**
- Wednesday's first slice.
- Whether to claim the Max API credits for QMX.
- Folding `rebuild/base` into `integration` and creating `staging`.
- Which junk branches and worktrees to delete.

---

## 4. Corrections from the operator (same evening, later)

- **No API spending for Claude or Codex, ever.**
  - Claude runs only on his Max 5x subscription, through the Agent SDK signed in with his plan (the help-centre line above).
  - GPT only through his ChatGPT subscription ("Sign in with ChatGPT" for locally hosted apps; feasibility to confirm).
  - The Max API-credit idea is dropped.
  - Other providers (GLM, MiniMax, Kimi, DeepSeek and the rest) use their API keys.
- **No owned server.** He does not want to own or manage compute (no Contabo burden, no RAM ceiling). Server work runs on rented, on-demand compute from several providers, so QMX is never limited by one box.
  - P21 (`qmx-remote`) already targets several providers.
  - Amp-style "minutes" pricing is the mental model.
  - §3 point 6 ("Contabo as QMX's own orb") is withdrawn.
- **Mini apps are NOT Amp portals.** A mini app is QMX's packaged, versioned unit with ML-level complexity (see `21-miniapps-and-workflows-seeds.md`). The portal or preview idea is at most a viewing aid.
- **Vocabulary:** Claude has liberty. Graphs and loops give more depth than the original node editor. Workflows can be agentic, non-agentic or mixed. Design for the best.
- **More than one Fable sub-agent** is allowed for this architecture push.
- **He asked for direct responses to his questions throughout the day.** The architecture must answer the open questions listed in `00-session-ledger-2026-10-12.md` §2, not defer them.
