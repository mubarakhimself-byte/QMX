---
label: qma-v2:how-it-works (plain-words explainer)
created: 2026-10-13
reads: ARCHITECTURE.md revision 3a (all), START-HERE.md §5, AUDIT-2026-10-13.md (verdict, §D), the operator's answers of 2026-10-13 morning
status: planning only. Not committed. Changes nothing in ARCHITECTURE until revision 4 folds it in.
---

# How QMA v2 works, and what your new answers change

## How to read this

Each topic has three parts:
- **Today's design** is what ARCHITECTURE revision 3a says. The § number tells you where.
- **What your new answers change** is what revision 4 must say instead.
- **Open points** are things nobody has settled yet.

A few words used throughout:
- The **harness** is everything around the model: the tools it can call, the rules, the memory, the screen it talks to.
- An **engine** is the library that runs the model's think-act loop. QMA v2 has two: the Claude Agent SDK (the same loop as Claude Code) and the OpenAI Agents SDK (used for GPT and for key providers such as DeepSeek or OpenRouter).
- A **session** is one conversation with a copilot, with its own history.
- A **plugin** is a folder of tools, skills and helper-agent definitions, plus a small settings file called `qma.toml`.

Your baseline rule sits over everything below: **QMX's harness must be at least as good as a plain Claude Code or Codex session, out of the box.**

---

## 1. Tools

**Today's design (§2.1, §2.5, §2.7).**
- A tool is anything the model can call: run a backtest, read the Library, write a file.
- Every QMX tool is described once (`ToolDef`): its name, what it does, and its **effect class** (`read`, `write` or `external`). There is deliberately no "money" class.
- Every QMX tool call passes through one checkpoint, `ToolInvoker.invoke`. It checks the rules, asks you if needed, runs the tool, and writes the result into the run's evidence file.
- Claude's own built-in tools (Bash, Write, Edit) keep running. A hook checks them before and after each call (R1).
- The OpenAI engine gets a smaller kit of the same basics (read files, search, patch, shell, Python, load a skill). A "parity badge" shows where it is weaker.
- Web fetching is switched off on copilots. Reading the web goes through a separate "reader" helper with no write tools, and any session that has read untrusted text becomes **tainted**: from then on, every `external` action asks you first.

**What your new answers change.**
- **Tools follow the session's home.** A session in a Lab project gets that project's tools. A Portfolio session gets Portfolio's. The general copilot can load any of them. Today tools follow the seat's plugin; revision 4 makes the project the unit.
- **Mini apps arrive as plugins.** Loading an app plugin adds its tools to whichever copilot loaded it (see §7).
- **Web access on copilots.** Vanilla Claude Code has web search and fetch. Switching them off on copilots falls below your baseline. Proposal: keep them on, and keep the taint rule (after reading the web, outside actions ask first).
- **Computer use becomes a tool family.** You now allow agents to click around cTrader and TradingView for ideas you agreed to. That needs a design (AUDIT D.3): where it runs, a separate desktop so it never takes your mouse, screenshots treated as untrusted, and the money hook from §3.

**Open points.** Computer-use design (which driver; how it runs per operating system). Whether web tools on copilots are on by default or one allow rule away.

---

## 2. Memory

**Today's design (§2.4, §2.1).**
- Memory is whatever each engine does by default: Claude's auto memory inside QMX's own Claude home, and OpenAI's session history (`SdkDefaultMemory`).
- Each agent has a memory scope: task, workflow, session or global.
- Hard rule: records (trades, runs, Library items) never go into memory. A test checks this.

**What your new answers change.**
- **Memory gets a home too.** A Lab project should have its own project memory, the way a Claude Code project has its `CLAUDE.md` and a Codex project has its `AGENTS.md`. Portfolio has its own. The general copilot can read the memories of the homes it combines.
- **No golden rule yet.** Q2's "one rule every copilot remembers" is withdrawn for now. The methodology (Matt Pocock skills plus BMAD skills turned into QMX skills) comes later. Memory and skills slots must exist so it can be dropped in without code changes.
- **Different freedom per home.** Lab memory and prompts carry fewer instructions; Portfolio carries more.

**Open points.** A way for you to list and edit memory (FR-094, missing). "Save memory before compaction" (FR-A44, dropped from the PRD). Whether project memory is a plain file you can open, like `CLAUDE.md`. Recommend: yes, a plain file.

---

## 3. Hooks and permissions

**Today's design (§2.3, §2.5, §2.12, §3.2).**
- A **hook** is a small piece of code the harness runs automatically at a fixed moment, for example just before any tool call. Unlike a prompt instruction, the model cannot talk its way past it.
- On Claude, QMX uses three hooks: before a tool call, after it, and before compaction. Hooks from plugins that QMX did not write are stripped. On OpenAI, hooks exist only as rules in `qma.toml` (FR-030, weaker).
- The tool checkpoint applies its rules in a fixed order: a hard deny list in code, then an always-ask list from settings, then the taint rule, then any "allow for this session" or "remember" answers you gave earlier, then budgets.
- Approvals are rows in the database. They survive a crash. Only you can answer them; agents and apps get refused at that door.
- No order tool exists in any tool list. Broker credentials never enter an agent's environment.

**What your new answers change.**
- **Claude-Code-style rules: allow, ask, deny.** Replace today's scattered lists with one rules table in three columns, matched by tool name and argument pattern (for example `apps_publish` → ask, `Bash(git push*)` → deny). Today's always-ask list, sticky decisions and deny list fold into it. You edit it in the UI (your standing rule: configurable means UI-editable).
- **Publish, install and schedule happen only when you invoke them**, or when an allow rule you wrote lets them through. The default for all three is ask.
- **Money is read-only for agents, as a hook.** Today the money rule is already code, not a prompt (deny list, descriptor check, before-call hook). Revision 4 makes it one named, always-on hook, `money_read_only`, that no rule, setting or plugin can switch off. It runs on both engines, on the shell, and on computer-use clicks.
- **Demo accounts are allowed for agreed ideas.** This is new. Today no order tool exists at all. Testing on demo needs a demo-only order path, and the money hook must check, every time, that the target account is a demo account (FR-107's demo-versus-live classifier, still partial).
- **Lab gets more freedom, Portfolio less.** Each home ships its own default rules table: Lab allows more without asking; Portfolio asks more.

**Open points.** How the hook proves an account is demo (broker account flag, a list you keep, or both). How the hook stops a computer-use click on a live order ticket (screen check, or computer use only on a demo login). Whether "allow" rules can be scoped per project.

---

## 4. The organogram: copilots, sessions, projects

**Today's design (§2.4, §2.9, §6.2 Q4).**
- Three shipped plugins: general, Lab, Portfolio. Each "seat" is a plugin plus an engine and a model (`seats.<plugin>.*`).
- A session row records its surface, its target, its plugin and its parent.
- Q4 recommended one general copilot that lists every session, with Lab and Portfolio as plugins it loads.

**What your new answers change.**
- **One vanilla base copilot.** Like a plain Claude Code session: no extra methodology, just the harness. Every other copilot is this base plus a home.
- **A session has a home, and the home never changes.** Three kinds:
  - a **Lab project** (an ML experiment, another experiment, designing a mini app): the session carries that project's files, memory, tools and rules;
  - **Portfolio**: the session carries Portfolio's context;
  - **General**: can combine the Library, the Lab and Portfolio.
- **Projects work like Codex projects.** A project is a folder with its own memory file, rules, tools and list of sessions. In the data, the session row gains a `home` (kind plus project id) beside today's `plugin`.
- **The copilot page is a shell.** It lists every session with a badge for its home. Opening a Lab session there shows it, but it still runs in the Lab with Lab context. Nothing moves.
- **Mini apps get no copilot of their own.** They become plugins any copilot can load (§7).

**Open points.** Can a general session start inside a project, or only at the top level? Can a session be copied into another home (a new session that starts from a summary)? Do Lab projects map onto existing Lab folders, or new ones?

---

## 5. Sub-agents

**Today's design (§2.7, §2.10, §1.3 item 4).**
- A **sub-agent** is a helper the copilot starts for one task. It works in its own context and hands back a short result.
- Two kinds:
  - **In-session helpers** are native to each engine: Claude's `agents/*.md` files, OpenAI's agent-as-tool. Cheap and quick.
  - **`delegate`** starts a helper as its own job, on any engine and any account (for example a cheap OpenRouter model under an Opus parent). The job has a lease, so it survives a crash, and its cost shows under the parent.
- Depth limit: copilots and orchestrators may delegate; helpers may not start helpers of their own.
- A long-lived **orchestrator** (a session that runs a whole plan and hands off to a fresh session when its memory fills past 60 percent) is NEXT.

**What your new answers change.**
- Helpers inherit their parent session's home: a helper started from a Lab project sees that project's tools and rules, never more.
- Helpers inherit the money hook and the parent's rules table. A helper can never have wider permissions than its parent.
- Effort is set per helper (§8), so a cheap helper can run at low effort.

**Open points.** Default sub-agent settings per workflow (FR-087, missing). Whether Lab helpers may start their own helpers (more freedom) while Portfolio helpers may not.

---

## 6. Graphs and agentic workflows (loops and graphs)

This answers your question directly.

**Today's design (§2.7, §2.8, §2.10, §6.1 A-06, A-08).**
- A **workflow** (a graph) is a saved plan made of steps, called nodes. Some nodes are plain code with no model; some are agent steps; some are gates that wait for you.
- Eight node kinds run on Wednesday: python, tool, app call, condition, parallel, join, human gate, agent. Four more exist in the file format but run later: loop, sub-workflow, watch, command.
- After every step, the runner saves a checkpoint. After a crash it skips the finished steps and never repeats an action it already did.
- A **loop** is an agent step with a checker: the agent works, a checker judges the result, and a stop rule ends it (three attempts by default, or a budget, or "no progress for two rounds", then it asks you).
- The copilot can write, check, run, edit and rerun a workflow by itself. A step that sends something outside needs a gate before it and no automatic retries.
- The UI says "workflow" and "sub-agent". "Graph" and "loop" appear only as badges.

**What your new answers change.**
- Workflows live in a home. A workflow built in a Lab project belongs to that project. Running it from the general copilot doesn't move it.
- Scheduling a workflow is a "schedule" action: ask by default, unless your allow rule says otherwise.
- Agent steps use the same rules table and money hook as copilots. A workflow can never do what its home forbids.
- The methodology skills (later) will mostly arrive as workflow templates. The runner needs nothing new for that.

**Open points.** Loop and sub-workflow nodes are NEXT. Turning a copilot's ad hoc plan into a saved workflow (FR-064) is not designed. Templates (FR-066) are missing.

---

## 7. How mini apps get created

**Today's design (§2.4, §5 Apps row, packets 5a and S).**
- You describe an app in a paragraph. The copilot uses the `build-mini-app` skill, writes the app, and the app's own tests ("the road") check it.
- A new or agent-built app installs **disabled**. It runs only after you approve it. The install card shows what the app asks for.
- Apps never hold an engine inside them. When they need an agent they ask QMX (`QmaClient.delegate` or `run_workflow`) with their own limited app key.
- `maintain-app` fixes a broken app.

**What your new answers change.**
- **Designing a mini app is a Lab project.** The session that builds it lives in that project, with the app's files as its context.
- **A finished mini app becomes a plugin.** It ships its tools, skills and screens as a plugin folder. Any copilot can load it; no app gets its own copilot.
- **Publish and install only on your word** or your allow rule.
- Today apps and plugins install by two different paths (the road and `PluginLoader.install`). Revision 4 should merge them into one path with one capability card.

**Open points.** How an app's screen and its plugin tools are packed together. Whether loading a plugin mid-session forces a new session (see §9: today it does).

---

## 8. Thinking effort

**Today's design (§2.1 `ModelRow.effort_map`, §6.1 A-04, §6.2 Q3).**
- **Effort** is how hard the model thinks before answering. More effort: better answers, slower, costs more of your plan.
- Today: effort is set automatically per role, with a per-chat override (Q3 recommended no switch beside the chat box). Each model row maps QMX's effort words to that provider's own setting.

**What your new answers change.**
- **Effort works like `/effort` in Claude Code.** A control in every session, changeable at any moment, with sensible defaults per home and per role.
- **Effort is a per-turn setting, not part of the agent's identity.** It must not be part of the agent's fingerprint (`spec_hash`). Otherwise changing effort would look like a different agent and start a fresh session.
- **Effect on the Claude engine.** Today the design opens each Claude session with fixed options and resumes with identical ones. If the SDK cannot change effort on a live session, either it gains a mid-session setter, or effort is the one option allowed to differ on resume. A probe must settle which.
- **Effect on caching.** Changing effort leaves the cached system prompt and tool list alone. It may cost one cache miss on the conversation part (Anthropic documents this for thinking-budget changes). So: one slower, dearer turn after a change, then back to normal. Effort changes should be shown in the session as an event.
- **Effect on the OpenAI engine.** Easy: reasoning effort is set per run there.

**Open points.** The probe above. Whether workflow agent steps get a fixed effort (recommended, for repeatable runs).

---

## 9. Compaction and caching

**Today's design (§2.3, §2.4, §6.1 A-04, NFR-003, NFR-004).**
- **Compaction** is squeezing a long conversation into a summary so it fits the model's memory window. Claude compacts itself. On OpenAI, QMX uses OpenAI's compaction on OpenAI models and its own summariser on others. A hook fires just before Claude compacts, and the journal logs it.
- **Caching** means the provider remembers the start of the prompt, so repeating it is cheap and fast. The prompt has five layers. The first four (role, rules, plugin, skills index) stay byte-identical for a whole session, so they always hit the cache. Only the newest layer changes each turn.
- Packet 2 only checks that cache reads happen at all, not the 70 percent target. An approval left waiting longer than the cache lifetime loses its cache.
- Changing model mid-session compacts first, then opens a new child session (Wednesday ships only the cost estimate for this).

**What your new answers change.**
- **Compaction like Claude Code.** Automatic by default, plus a manual "compact now" with an optional note, in every session.
- **Save memory before compacting** (FR-A44 restored), so the project memory keeps what the summary drops.
- **The home's context belongs in the stable layers.** Because a session never changes home, its project context can sit in the cached layers for its whole life.
- **Loading a plugin mid-session.** Today a changed tool list counts as a new agent and starts a fresh session. With mini apps as plugins you load at any time, that is too harsh. Proposal: adding a plugin mid-session is allowed, costs one cache miss, and is logged.
- **OpenRouter** caching depends on which upstream provider serves the request, so pin the upstream for the whole session (AUDIT D.5).

**Open points.** Measuring the 70 percent cache target. Whether the OpenAI engine can add tools mid-session without a new session.

---

## 10. The router and accounts

**Today's design (§2.6, §6.1 A-16, A-20).**
- **Accounts** are rows: your Claude Max plan, ChatGPT sign-in, and API-key providers. Keys stay in the OS secret store; QMX only holds a label.
- The **router** picks an account and model when a session or step starts. It ranks by capability first, then by usage left. A session keeps its pick (sticky). The choice and the reason are recorded.
- Family guard: Claude and GPT models run on your plans only, never on paid keys.
- The override chain goes global → app → workflow → step → sub-agent.
- The ledger records usage per turn. Claude shows as percent of your window, keys show as USD.

**What your new answers change.**
- **OpenRouter** joins as a pool account (already in AUDIT D.5), mainly for remote and helper work.
- **Defaults per home and per role.** Lab and Portfolio can each set their default model and effort.
- **Effort sits beside the model.** The pick now includes effort, and the cost estimate should account for it.

**Open points.** Fix the family guard so `openai/gpt-oss-*` counts as "other" (AUDIT D.5). Several Claude accounts would need several Claude homes (FR-044, not designed). A per-role rule so routine helpers prefer OpenRouter and save your Max plan.

---

## 11. The event stream to the UI

**Today's design (§2.1 `QmaEvent`, §2.2, §4).**
- Everything that happens becomes an **event**: a small message with a session, run, agent path and kind.
- Two channels:
  - **Durable**: stored in the database and replayable after a reconnect or restart (topics such as runs, jobs, sessions, approvals).
  - **Live**: unstored, per session, for the words streaming in as the model types.
- The chat shows 14 kinds of blocks (message, tool call, permission request and so on). An update to a block is a new event carrying the whole block.
- The UI lane gets a handoff pack: the API description, recorded event samples, and the console as a reference client.

**What your new answers change.**
- Session events carry the **home** (kind, project id), so the copilot shell can show badges and filter.
- New event kinds: effort changed, compaction (manual or automatic), plugin loaded, permission rule matched (which rule allowed or denied a call).
- Computer use needs its live kinds back (`cursor.*`, screenshots), plus `tool.progress`, `terminal.*` and `diff.updated`. Revision 3 deleted them (AUDIT B.1).
- The console stays temporary (Q9). Its one-time sign-in hand-off must also work for the real UI (AUDIT D.1).

**Open points.** The exact list of live kinds. Whether the shell page subscribes to every session or only to the open one.

---

## 12. What "harness first" means

The goal: before projects, workflows and mini apps arrive, one plain copilot session in QMX can do everything a vanilla Claude Code or Codex session does, plus QMX's safety rails. The smallest set of parts:

1. **The engine loop on Claude, unchanged.** Claude Code's own loop and built-in tools (Bash, Read, Write, Edit, search, web), its native sub-agents and its skills loading. QMX adds rules around it and replaces nothing inside it (§2.3, packet 2).
2. **One vanilla base copilot.** A short system prompt and no methodology (§4 above).
3. **Sessions that survive.** Start, resume after a crash, stop, interrupt, steer mid-turn, with history kept by the engine (§2.9, packets 1b and 2).
4. **Permission rules: allow, ask, deny,** editable in the UI, plus approvals that survive a restart (§3 above; packet 1c).
5. **The money hook,** always on and impossible to switch off: money is read-only for agents (§3 above).
6. **Effort control** mid-session, like `/effort` (§8 above).
7. **Compaction** automatic plus manual, and **caching** with stable prompt layers (§9 above).
8. **Tools and MCP servers** through the one checkpoint, and **skills** loaded on demand (§2.5, §2.4).
9. **Project memory** as a plain file the copilot reads at start, like `CLAUDE.md` (§2 above).
10. **The event stream** with the 14 block kinds, live typing and a permission prompt you can answer (§4).
11. **Usage shown honestly:** percent of the Claude window, USD for keys (§2.6).
12. **One second engine** (OpenAI Agents SDK) behind the same rules, so helpers can run on OpenRouter.

**What waits until the harness passes:** project homes and the copilot shell with badges, the Lab and Portfolio freedom profiles, workflows beyond the basics, mini apps as plugins, computer use, the orchestrator, the methodology skills.

**How to check it.** A side-by-side task list: the same ten everyday tasks run in vanilla Claude Code and in a QMX base session (read a repo, edit a file, run tests, search the web, start a helper, compact, change effort, resume after a kill, deny a risky command, answer a permission prompt). QMX passes when it does each one at least as well, and also refuses a money action through the hook.
