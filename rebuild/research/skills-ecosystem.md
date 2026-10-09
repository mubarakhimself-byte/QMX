# QMX Copilot: skills, modes, hooks (research draft)

Date: 2026-10-09. Status: draft for discussion, not ratified. Read-only research. Nothing here is a decision.

Scope: the Copilot is a LangChain Deep Agents app (Python). It builds workflows (node graphs that compile to
LangGraph), builds and edits mini apps (sandboxed, with their own data, MCP tools and UI panels), runs long
background tasks, does research, and shows artifacts and panels in the UI. Skills load through Deep Agents
`SkillsMiddleware`. Hooks are LangChain middleware.

---

## 1. Sources read

Local (read in full):
- `C:\Users\Mubarak\.claude\skills\wayfinder` -> symlink to `C:\Users\Mubarak\.agents\skills\wayfinder\` (`SKILL.md`, `agents/openai.yaml`)
- Siblings under `C:\Users\Mubarak\.agents\skills\`: `grilling`, `grill-me`, `grill-with-docs`, `to-spec`, `to-tickets`,
  `triage` (+ `AGENT-BRIEF.md`, `OUT-OF-SCOPE.md`), `handoff`, `implement`, `prototype`, `research`, `teach`,
  `wait-what`, `loop-me`, `ask-matt` (+ `PHASE-BOUNDARIES.md`), `writing-for-agents` (+ `SKILL-MECHANICS.md`)
- QMX vocabulary: `C:\Users\Mubarak\Desktop\QMX\docs\glossary.md` (copilot, Skill, Loop, mini-app, pack, money path,
  Role), `docs\decisions\ADR-0025-pack-and-grant-kit.md`, `docs\lenses\ui\screens\copilot.md`

Web (primary sources):
- Anthropic skill authoring best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Agent Skills spec: https://agentskills.io/specification ; example repo: https://github.com/anthropics/skills
- Deep Agents skills: https://docs.langchain.com/oss/python/deepagents/skills
- Deep Agents human-in-the-loop: https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
- Deep Agents async subagents: https://docs.langchain.com/oss/python/deepagents/async-subagents
- LangChain custom middleware: https://docs.langchain.com/oss/python/langchain/middleware/custom
- LangChain built-in middleware: https://docs.langchain.com/oss/python/langchain/middleware/built-in
- obra/superpowers: https://github.com/obra/superpowers (+ raw `skills/{brainstorming,systematic-debugging,writing-plans,
  verification-before-completion,using-superpowers,subagent-driven-development}/SKILL.md`)
- GitHub Spec Kit: https://github.com/github/spec-kit (README)
- Claude Code permission modes: https://code.claude.com/docs/en/permission-modes
- Codex approvals: https://learn.chatgpt.com/docs/agent-approvals-security
- Cursor plan mode: https://cursor.com/docs/agent/plan-mode
- Roo Code modes: https://docs.roocode.com/basic-usage/using-modes
- Amp modes: https://ampcode.com/news/the-dial , https://ampcode.com/news/rush-mode

Not reached: the Cursor "modes" overview page redirected to plan mode; Kilo Code was not read (it is a Roo fork, and
Roo covers the same pattern). BMAD is used here from the local install only (`bmad-*` skills in this session).

---

## 2. What each source teaches

### 2.1 Matt Pocock skills: a main flow of small skills, each with one job

How they chain (`ask-matt/SKILL.md` is the router):
- **Main flow:** `grill-with-docs` (interview, writes `CONTEXT.md` + ADRs) -> optional `prototype` detour bridged
  by `handoff` -> `to-spec` (summarise the chat into a spec, no new interview) -> `to-tickets` (tracer-bullet
  vertical slices with blocking edges) -> `implement` per ticket (drives `tdd`, ends with `code-review`), with a
  `/clear` between tickets.
- **On-ramps:** `triage` (raw incoming issues -> agent briefs), `diagnosing-bugs` (only after a red feedback
  loop exists), `wayfinder` (a huge, foggy effort).
- **Underneath:** `grilling` is the shared interview step; `domain-modeling` and `codebase-design` hold the
  vocabulary.

Patterns worth copying:
- **Wayfinder** (`wayfinder/SKILL.md`): it plans and does not build. Name the **destination** first. The map is an
  **index, not a store**: each decision lives in one ticket, and the map only links to it. Ticket types are
  research (AFK, run by a subagent), prototype (HITL), grilling (HITL, the default) and task (does work only to
  unblock a decision). **Fog of war**: a question becomes a ticket only once it can be stated sharply. Out of
  scope is a separate section, and those items never come back. One ticket per session, except research tickets,
  which run in parallel.
- **Grilling** (`grilling/SKILL.md`): a design tree worked in rounds. Each round asks the whole frontier, numbered,
  and every question carries a recommended answer. *Finding facts is the agent's job; making decisions is the
  user's job.* Fact-finding goes to subagents, and the questions that don't depend on those facts are asked now.
- **Triage AGENT-BRIEF**: briefs describe behaviour, not file paths. They state current vs desired behaviour, key
  interfaces, testable acceptance criteria, and what is out of scope.
- **loop-me** has the vocabulary QMX needs for routines: **trigger** (event or schedule), **checkpoint** (a point
  where a human decides), **push right** (put the checkpoint as late as possible), **brief** (a decision-ready
  summary, never raw output). A workflow spec is done when an implementer could build it without asking a question.
- **wait-what**: re-pitch the last message in Simplified Technical English using the glossary. This fits a
  non-technical operator well.
- **PHASE-BOUNDARIES**: decide continue / clear / handoff / subagent / compact only at a phase boundary, and in
  that order of preference.
- **writing-for-agents**: a description is a *context pointer*. Put the leading word first, one trigger per
  branch, give every step a completion criterion, phrase rules positively, and keep one source of truth.
  `SKILL-MECHANICS.md`: a model-invoked skill costs context on every turn; a user-invoked skill
  (`disable-model-invocation: true`) costs nothing but the human has to remember it. A router skill fixes that.
- `agents/openai.yaml` uses `allow_implicit_invocation: false` on most of these skills, so they are user-invoked
  by default. Only `grilling`, `prototype`, `research` and `writing-for-agents` are model-invoked.

### 2.2 Anthropic Agent Skills guidance and spec

- Frontmatter: `name` (at most 64 chars, lowercase/digits/hyphens, matches the folder) and `description` (at most
  1024 chars, says *what* and *when*). Optional: `license`, `compatibility`, `metadata`, and `allowed-tools`
  (experimental) (agentskills.io/specification).
- Progressive disclosure: about 100 tokens of metadata at startup, the body (under 5000 tokens, under 500 lines)
  when the skill fires, and resources only when needed. Keep references one level deep, and give long reference
  files a table of contents.
- Match **degrees of freedom** to how fragile the task is: high freedom for reviews, low freedom (an exact
  script) for migrations. For risky batch work, use **plan -> validate -> execute**: write a machine-checkable plan
  file, validate it with a script, then apply it.
- Write **evaluations first** (at least three scenarios, with a baseline taken without the skill). Use a
  Claude A / Claude B loop: one instance authors the skill, a fresh one tests it. Test on every model tier you
  will ship on.
- Copyable checklists for multi-step work. Prefer bundled scripts to code the model generates on the spot.

### 2.3 Deep Agents SkillsMiddleware: what it actually supports

All from docs.langchain.com/oss/python/deepagents/skills:
- Three load levels: metadata goes into the system prompt, `SKILL.md` is read with `read_file` when the skill
  fires, and resources are read when the instructions call for them.
- **Pinning** (`pinned_skills` in the run input, deepagents>=0.7.23): when a user names a skill (for example
  `/build-workflow` or a menu choice), the app pins it and the SKILL.md is appended as a HumanMessage tagged
  `lc_source="pinned_skill"`. The UI can show it as a label. The *app* parses the slash syntax; Deep Agents does
  not.
- **Skill tools** (`metadata.include_tools`, space-separated, deepagents>=0.7.22): tools stay hidden and fail as
  unknown until the skill has been read or pinned. A **resolver** `(name, runtime) -> list[BaseTool]` can map
  names to real tools at runtime, so it can return different tools per user or per context. That makes it the
  natural place to intersect with QMX grants (see H2).
- **Availability by context**: you choose the skill paths per role, tenant or request, or route `/skills/` through
  `CompositeBackend` and `StoreBackend` namespaced per user or org.
- **Read-only vs writable**: `FilesystemPermission(mode="deny")` on `/skills/approved/**`, and `mode="interrupt"` on
  writes so a human approves any skill the agent writes. A checkpointer is required.
- Skills **load once per thread**. Reloading means setting `skills_metadata: None` from `after_agent`, which
  invalidates the prompt cache. **So modes should not swap skill lists in the middle of a thread.**
- Subagents: the general-purpose subagent inherits the parent's skills. Custom subagents get only their own, and
  skill state is fully isolated between them.
- Guidance: fewer, well-scoped skills beat many overlapping ones. Make descriptions clearly different from each
  other.

### 2.4 LangChain middleware: the hook surface

- Node hooks: `before_agent`, `before_model`, `after_model`, `after_agent`. Wrap hooks: `wrap_model_call`,
  `wrap_tool_call`. Also `@dynamic_prompt`. Hooks can return `jump_to` (`end`, `tools`, `model`) and extend state
  through `state_schema`. Order: `before_*` runs first to last, `after_*` last to first, and `wrap_*` nests.
- Built-ins worth using: `HumanInTheLoopMiddleware` (`interrupt_on`, with decisions approve, edit, reject or
  respond, plus a `when` predicate), `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware`, `PIIMiddleware`
  (custom detectors), `SummarizationMiddleware`, `ModelRetry`/`ToolRetry`/`ToolError`, `ModelFallbackMiddleware`,
  `LLMToolSelectorMiddleware`, `ProviderToolSearchMiddleware`, `TodoListMiddleware`, `ContextEditingMiddleware`,
  `RubricMiddleware` (self-grade against a rubric up to N iterations; beta, deepagents>=0.6.5), and middleware
  stream `transformers` that push side-channel events (artifacts) to the UI.
- Dynamic model and dynamic tool selection are documented `wrap_model_call` patterns. Modes need both.

### 2.5 obra/superpowers: process skills with hard gates

- Main flow: `brainstorming` -> `using-git-worktrees` -> `writing-plans` -> `subagent-driven-development` or
  `executing-plans` -> `test-driven-development` -> `requesting-code-review` -> `finishing-a-development-branch`.
- `brainstorming` sorts every request into **Spike / Bounded / Architectural** and says which out loud. A
  HARD-GATE blocks any implementation action until the right approval for that path exists, and one approval
  never stands in for a later one.
- `systematic-debugging`: no fix until the root cause has been investigated. Four phases: investigate, find the
  pattern, form a hypothesis, implement.
- `verification-before-completion`: no claim of completion without fresh evidence. Its table maps each claim to
  the proof it needs. Agent reports of success must be checked against the actual diff.
- `subagent-driven-development`: a fresh subagent per task, a review after each task (spec, then quality), and
  rulings recorded in a ledger instead of stopping to ask. It stops only for four things: an irreversible action,
  a security-sensitive action, a shared side effect, or a broken plan.
- `using-superpowers` is injected at session start by a hook and forces a skill check before any reply. The
  lesson: **getting skills to trigger reliably is a harness problem (a hook) as much as a wording problem.**

### 2.6 GitHub Spec Kit: three separate entry points, each with recorded outcomes

- SDD: `constitution` once per project, then per feature `specify -> plan -> tasks -> implement -> converge`,
  repeating implement and converge until converge reports "Converged". `clarify`, checklists and analyze are
  optional extra gates.
- Bug fixing: `bug-assess -> bug-fix -> bug-test`. The verdict is verified, partial or failed. *"Missing
  verification is not a successful fix."*
- Idea assessment: `intake -> research -> define -> shape -> decide`, ending in go, needs-clarification or kill.
  Stopping with a written reason counts as a good outcome.
- Lesson for QMX: **build, fix and assess are independent processes, not phases of one pipeline.** Each one
  writes its artifacts to a known folder.

### 2.7 Modes in other agents

| Product | Modes | Mechanism | Switching |
|---|---|---|---|
| Claude Code | default (manual), acceptEdits, plan, auto, dontAsk, bypassPermissions | Permission posture. Plan mode allows reads and exploration but no source edits until the plan is approved. The approval prompt then offers which mode to continue in. | Shift+Tab cycle, `/plan` prefix, `--permission-mode`, settings default, UI selector |
| Codex | read-only, Auto (workspace-write + on-request), Full access; Default/Plan | Sandbox x approval policy | `/permissions`; Shift+Tab for Plan (issue #34073) |
| Cursor | Agent, Ask, Plan, Debug | Plan: clarifying questions, then research, then an editable markdown plan, then "Build" | Shift+Tab rotation, mode picker; it auto-suggests Plan for complex requests |
| Roo Code | Code, Ask, Architect, Debug, Orchestrator | Tool groups per mode (read, edit, command, mcp). Architect can edit only `.md` files. Orchestrator has no tools of its own and delegates with `new_task`. | Dropdown, `/mode` slash, Ctrl+. cycle, accepting a suggestion; **sticky model per mode** |
| Amp | low, medium, high, ultra (replaced smart, deep, rush) | A mode is system prompt + tools + model + effort; every mode has an "oracle" for second opinions | Ctrl+S dial, picker |

Common shape: **a mode is a bundle of (tool allowlist, approval posture, model/effort tier, prompt fragment).**
Plan-type modes end on an approval card that names the next mode. Agents may *suggest* a mode switch, and the
user accepts it.

### 2.8 Design principles for QMX (summary)

1. Skills hold *procedure and knowledge*. Hooks hold *rules that must never be skipped*. Modes hold *posture*.
   Wording alone never enforces a guardrail.
2. The process skill comes first, then domain skills (superpowers priority rule). The router skill names the next
   step.
3. Plan before you build, scaled to size: spike, bounded or architectural. Wayfinder is only for efforts that
   are too big for one session.
4. Facts are the agent's job, decisions are the operator's. Each question carries a recommended answer.
5. Push the checkpoint right. Present a **brief**, never raw output.
6. No completion claim without fresh evidence (a test run, a backtest artifact, a health probe).
7. Build, fix and assess are separate processes, each ending in a recorded verdict.
8. Keep the skill set small, with clearly different descriptions. A user-invoked skill is pinned from a slash or
   menu. Evaluations come before the prose.

---

## 3. QMX constraints this design must respect

- `ProductSessionProfile` is the closed set `{authoring, app-use}`, fixed when the session is created, with "no
  third seat" (glossary "copilot"; ADR-0025, DEC-0463). **So modes are a changeable posture *inside* a session, not
  new profiles.** App-use sessions (the in-app panel) get a narrower set of modes.
- "A skill ... is knowledge, never a capability grant" (glossary "Skill", DEC-0315). **So Deep Agents
  `include_tools` must never be the thing that grants a tool.** The resolver may only return tools that are already
  in the session's GrantRecords and allowed by the mode (H2).
- A Skill is not a **Loop**. A skill may *invoke* a Loop (a runtime-owned stopping condition, budget and
  escalation) (DEC-0312).
- **Money path** is a taint (glossary). The Copilot never places, modifies or sizes orders. The trading node owns
  live trading. Risk and sizing authority is the GitBook plus the node docs (memory: operator standing rules).
- Broker credentials live in Windows Credential Manager under `qmx/*`, and never in chat, repo or `.env` (memory:
  broker credentials location).
- Lego vision: everything has defaults and can be added, removed or edited. Configurable means editable in the UI.
  Show where each job runs, on any compute provider (memory). So modes, skills and hook thresholds must be
  editable in Settings.
- Docs lag the vision (memory: the 2026-10-04 move to LangGraph). Check the terms above against the current
  architecture before anything is ratified.

---

## 4. Copilot MODES (draft)

Five modes. Each one is a bundle: (tool allowlist, approval posture, model tier, prompt fragment, default pinned
skill). It lives in graph state (`copilot_mode`) and is enforced by H1. Model tiers are abstract (provider-agnostic):
**fast** (cheap, quick), **standard** (default), **deep** (strongest reasoning, highest effort). Each mode
remembers the model last used with it (Roo's sticky models).

| Mode | Purpose | Tools allowed | Approval posture | Model tier | Profiles |
|---|---|---|---|---|---|
| **Ask** | Quick questions, explanations, "where is X", status | Read: catalog, docs, data previews, job status, logs, web search | No interrupts. Nothing can be written. | fast (escalate to standard on long context) | authoring, app-use |
| **Plan** | Shape an idea into a Brief or Plan; research; wayfinding | Ask tools + research subagents + writes **only** to plan or brief artifacts (like Roo Architect, markdown only) | Ends on an approval card: "Approve and Build / Approve and Run / Keep planning" | standard; deep for synthesis | authoring |
| **Build** | Author or edit workflows and mini apps; fix broken ones | Plan tools + draft-namespace writes (graph drafts, sandbox app files, sandbox runs, tests, previews) | Writes inside drafts are auto-accepted (like acceptEdits). **Publish, install, grant, delete and network allowlist changes interrupt.** | standard; deep for diagnosis | authoring; app-use (that app only, change requests) |
| **Run** | Launch, monitor, steer, cancel and schedule long jobs | Ask tools + job launch/check/update/cancel (async subagents), schedule CRUD, compute-target selection | Interrupts for: spend over budget, new schedules, compute target outside the allowlist, anything touching paper accounts. **Live trading has no tool at all.** | fast for monitoring; standard for briefs | authoring, app-use |
| **Review** | Judge results, diffs and app health; adversarial second opinion | Read + evaluation tools (metrics, overfitting checks, test runners, diff viewers) + reviewer subagent | No writes. Verdicts become artifacts. | deep (an "oracle", like Amp) | authoring, app-use |

Debug is folded into Build through the pinned `fix-broken-app` skill, not a sixth mode (open question Q2).
Orchestration is not a mode either: in any mode the Copilot can start subagents, but only with tools that mode
allows. That is the Roo Orchestrator lesson, kept inside the same gate.

**How the operator switches modes:**
1. A mode picker next to the chat input, which always shows the current mode.
2. Shift+Tab to cycle, as in Claude Code, Codex and Cursor.
3. A slash prefix: `/ask`, `/plan`, `/build`, `/run`, `/review`. The app strips it and sets the mode. A slash on a
   skill name (`/build-workflow`) pins that skill and moves to the skill's home mode.
4. **Suggestion chips**: the Copilot calls `suggest_mode(target, reason)`. Moving to a less powerful mode applies at
   once. **Moving to a more powerful mode always raises an interrupt** the operator must click. The agent can never
   give itself more power.
5. The approval card at the end of Plan names the next mode (the Claude Code plan-approval pattern).
The mode is saved per `psess:`. Every switch is logged (H13).

---

## 5. Day-to-day USER STORIES

Format: story -> mode path -> skills -> hooks -> artifacts and how they render. Hook ids are from section 7.

**US-1 Create a workflow.** *As the operator, I want to say "every morning pull EURUSD and GBPUSD, compute my
regime indicator, and flag a regime change", so that I get a running workflow without wiring nodes myself.*
- Mode: Plan -> Build (-> Run to switch it on).
- Skills: `shape-idea` (bounded path) -> `build-workflow`. Then `schedule-routine` if it repeats.
- Hooks: H1, H2, H5 (publish), H7 (no "done" without a compile and a dry run), H10 (approved Brief required),
  H8, H15.
- Artifacts: a **Brief card** (inline in chat); a **Workflow canvas** preview tab showing the node graph, with a
  diff against the previous version if one exists; a **Dry-run report** (per-node pass/fail, sample outputs, and
  where it ran); a **Publish card** (approve, edit or reject).

**US-2 Build a new mini app.** *As the operator, I want a "Spread Monitor" app with its own data table, two tools
and a chart panel, so that I can watch spreads without asking the Copilot each time.*
- Mode: Plan -> Build.
- Skills: `shape-idea` (architectural path) -> `build-mini-app` (new branch).
- Hooks: H10, H1, H2, H5 (install, grant, network allowlist), H15 (rubric: panels render, tools pass contract
  tests), H7, H4.
- Artifacts: an **App Brief** (purpose, data, tools, panels, out of scope); an **App Plan** checklist; a **Live
  preview panel** (a sandboxed iframe of the app UI) beside chat; a **Contract test report**; an **Install and
  Grant card** listing each requested capability in plain words, which the operator approves one by one.

**US-3 Change an existing mini app.** *As the operator, I want to tell the Spread Monitor panel "add a 1-hour
view", so that the app changes without me opening code.*
- Mode: Build inside an app-use session (scoped to that `instance_id`).
- Skills: `build-mini-app` (change-request branch; triage-style brief).
- Hooks: H1 (app-use limits edits to this instance), H2, H5 (re-grant if new capabilities), H7, H8.
- Artifacts: a **Change brief** (current vs desired behaviour, acceptance checks); a **Before/after preview**
  (two tabs); a **Version card** with a rollback button.

**US-4 Run and watch a long task overnight.** *As the operator, I want to start a 6-hour parameter sweep before
bed and wake up to a summary, so that compute works while I sleep.*
- Mode: Run.
- Skills: `launch-long-run` -> (morning) `brief-results`.
- Hooks: H6 (compute and model budget), H5 (spend above the limit, a compute target off the allowlist), H16
  (return control right after launch), H12 (retries and provider fallback), H8, H13.
- Artifacts: a **Job card** (live progress, ETA, cost so far, **where it runs**, logs drawer, cancel and steer
  buttons) pinned in a Jobs strip; checkpoint notifications only on failure or a budget breach (push right); a
  **Morning brief** card the next day.

**US-5 Research a strategy idea.** *As the operator, I want to ask "is there an edge in fading London-open
breakouts on gold?", so that I get an honest go / needs-work / kill call before spending build time.*
- Mode: Plan (research subagents run AFK) -> optional Run (a quick backtest spike).
- Skills: `research-strategy` (Spec Kit assessment shape) + `shape-idea` spike path for a probe.
- Hooks: H1 (no publish), H7 (claims must cite a source or a run artifact), H6, H8.
- Artifacts: a **Hypothesis card** (claim, mechanism, how it could be falsified); a **Research note** (cited,
  primary sources, opened in a preview tab); a **Spike result** (equity curve plus key metrics, labelled
  "exploratory"); a **Decision card**: go, needs-clarification or kill, with the reason recorded.

**US-6 Review results.** *As the operator, I want to ask "is this backtest real or overfit?", so that I don't
promote a fake edge.*
- Mode: Review.
- Skills: `brief-results` (review branch).
- Hooks: H1 (read only), H7, H13.
- Artifacts: a **Verdict report** (metrics table, out-of-sample vs in-sample, parameter sensitivity heatmap, cost
  and slippage sensitivity, red flags in plain words) rendered as a report panel with charts, with **one** next
  action button (iterate / paper-trade request / archive).

**US-7 Fix a broken app.** *As the operator, I want to say "the Spread Monitor chart is blank", so that it gets
fixed for the real cause and proven fixed.*
- Mode: Build (pinned `fix-broken-app`).
- Skills: `fix-broken-app` (assess -> fix -> test).
- Hooks: H7 (the verdict needs the original symptom re-tested), H1, H5 (only if the fix needs new grants), H8.
- Artifacts: a **Diagnosis card** (symptom, reproduction, root cause; `failure_class` from the closed set grant,
  workflow, view, dependency or host); a **Fix diff** summary in plain words; a **Verification card** saying
  verified, partial or failed. "Failed" is shown honestly.

**US-8 Connect a broker or data source.** *As the operator, I want to connect my cTrader demo account or a new
data vendor, so that workflows can read from it.*
- Mode: Run (connection set-up), with human-only steps.
- Skills: `connect-source`.
- Hooks: H4 (credentials blocked in chat), H3 (any order-capable scope is refused), H5 (grant the connection to
  sessions), H13.
- Artifacts: a **Connection checklist** (wizard steps: what to click at the vendor, then a **secure credential form**
  that writes to Credential Manager `qmx/*`; the Copilot never sees the values); a **Health probe card** (read-only
  test call: latency, symbols visible, account type demo or live, labelled); a **Grant card**.

**US-9 Schedule a routine.** *As the operator, I want "every Sunday night, re-run my three research workflows and
send me one brief", so that the weekly review prepares itself.*
- Mode: Plan -> Run.
- Skills: `schedule-routine` (loop-me vocabulary).
- Hooks: H5 (create schedule), H6 (budget for each run), H8.
- Artifacts: a **Routine spec card** (trigger, steps, checkpoint, brief format, budget, where it runs); a
  **Schedule entry** in a Routines panel (next run, last result, pause button).

**US-10 Ask a quick question.** *As the operator, I want to ask "what did my sweep cost last week?" or "what's a
Sharpe ratio?", so that I get an answer in seconds.*
- Mode: Ask.
- Skills: none by default. `explain-plainly` if the reply doesn't land (wait-what).
- Hooks: H1, H4, H12.
- Artifacts: a plain chat answer; a small **inline table or chart** when the answer is numeric.

**US-11 Plan a huge effort.** *As the operator, I want to map "build a full portfolio-rebalancing desk", so that
we decide the route before building anything.*
- Mode: Plan across many sessions.
- Skills: `wayfind-effort` (user-invoked) -> `shape-idea` per card.
- Hooks: H10, H11 (phase boundary), H8.
- Artifacts: a **Decision Map** panel: destination, decisions so far (by name), a frontier of cards, a fog section
  and an out-of-scope section.

**US-12 Teach the Copilot a routine procedure.** *As the operator, I want to say "remember how we vetted that
data vendor, do it this way next time", so that the Copilot gets better at my way of working.*
- Mode: Build.
- Skills: `capture-skill`.
- Hooks: H14 (skill writes interrupt; `/skills/approved/` denied), H7 (three eval scenarios must pass).
- Artifacts: a **Skill draft card** (name, trigger description, steps); an **Eval result** card; it lands in
  `/skills/editable/` on approval.

---

## 6. Proposed SKILL CATALOGUE (13)

Conventions: folders follow agentskills.io. Gerund or action names. Descriptions put the leading word first and
give one trigger per branch. "UI" = user-invoked (pinned from slash or menu, `allow_implicit_invocation` false).
"MI" = model-invoked. `include_tools` lists names that the H2 resolver maps to real tools only if they are granted
and allowed by the mode.

1. **`copilot-guide`** (UI, router) - *"Which skill or mode fits what I'm trying to do. Router over the Copilot's
   skills."*
   - Steps: read the request -> map it to the main flow (shape -> build/run -> brief) or an on-ramp (fix, connect,
     research, wayfind) -> name **one** next skill and mode -> offer a chip.
   - Check: exactly one recommendation, with a reason.
   - Borrows: `ask-matt` router, SKILL-MECHANICS router skills.

2. **`shape-idea`** (MI) - *"Shape a request into an approved Brief before anything is built. Use when the
   operator asks for a new workflow, app, routine or change and no approved Brief exists."*
   - Steps: classify Spike / Bounded / Architectural out loud -> grilling rounds (frontier questions, numbered,
     each with a recommended answer; facts from subagents) -> write the Brief (goal, success checks, out of scope,
     glossary terms) -> approval card.
   - Checks: the frontier is empty; every assumption is labelled; approval is recorded. This approval unlocks H10.
   - Borrows: superpowers `brainstorming` (three paths + HARD-GATE), Pocock `grilling`, BMAD PRD-lite.

3. **`wayfind-effort`** (UI) - *"Map a huge effort as a Decision Map of cards and resolve one card per session."*
   - Steps: name the destination -> breadth-first grilling -> map (destination, notes, decisions, fog, out of
     scope) -> cards typed research (AFK), prototype, grilling or task, with blocking edges -> start research
     subagents -> stop.
   - Checks: the map is an index (no restated decisions); one HITL card per session; it ends by handing off to
     `shape-idea`/spec.
   - Borrows: Wayfinder, almost unchanged.

4. **`build-workflow`** (MI, `include_tools: graph_draft graph_validate graph_dry_run graph_publish`) -
   *"Build or edit a workflow node graph from an approved Brief. Use when a Brief asks for a pipeline, schedule
   body or automation."*
   - Steps: pick nodes from the catalog (reuse first) -> write `graph_plan.json` -> **validate** (schema, types,
     grants, compiles to LangGraph) -> dry-run on sample data -> show the canvas and the diff -> request publish.
   - Checks: the compile passes; every node in the dry run is green or explained; the plan matches the Brief's
     success checks; nothing on the money path.
   - Borrows: Anthropic plan -> validate -> execute; Spec Kit specify/plan/tasks; superpowers verification.

5. **`build-mini-app`** (MI, `include_tools: app_scaffold app_sandbox_run app_contract_test app_preview app_install_request`)
   - *"Build a new mini app or change an existing one. Use for new app requests (new branch) or app change
   requests from an app panel (change branch)."*
   - New branch: App Brief -> plan (data, tools as MCP ops, panels, requested capabilities) -> tracer-bullet slices
     (one panel + one tool + data end to end first) -> sandbox build -> contract tests -> live preview -> install and
     grant request.
   - Change branch: change brief (current vs desired, acceptance checks) -> edit -> test -> before/after preview ->
     new version with rollback.
   - Checks: contract tests green; preview renders (RubricMiddleware rubric); requested capabilities listed in
     plain words; install is not grant (pack/grant kit).
   - Borrows: `to-tickets` tracer bullets, `triage` AGENT-BRIEF, Spec Kit implement -> converge, `prototype` UI
     variants (optional).

6. **`fix-broken-app`** (MI) - *"Diagnose and fix a broken workflow or mini app. Use when the operator reports
   something blank, failing, slow or wrong."*
   - Steps: **assess** (reproduce; a red check that fails on this bug; classify `failure_class`) -> root cause
     before any fix -> **fix** (smallest change, plus a regression check) -> **test** (re-run the original symptom)
     -> verdict.
   - Checks: no fix proposed before a reproduction; verdict is verified, partial or failed; failed and partial are
     never dressed up as success.
   - Borrows: superpowers `systematic-debugging`, Pocock `diagnosing-bugs` (red loop), Spec Kit bug
     assess/fix/test.

7. **`research-strategy`** (MI, `include_tools: web_research data_preview quick_backtest`) - *"Assess a trading
   idea or market question with evidence and end in go, needs-work or kill. Use when the operator asks whether
   an edge, signal or market effect is real."*
   - Steps: intake (hypothesis card with a falsification test) -> research (subagents, primary sources, cited) ->
     define (metrics, data, costs) -> shape (the cheapest probe that could kill it) -> optional spike backtest
     (labelled exploratory) -> decide.
   - Checks: every claim cites a source or a run id; costs and slippage are included; a kill verdict is a valid
     outcome.
   - Borrows: Spec Kit idea assessment, Pocock `research`, Wayfinder research tickets.

8. **`launch-long-run`** (MI, `include_tools: job_launch job_check job_update job_cancel compute_targets`) -
   *"Launch, monitor, steer or cancel a long background job such as a sweep, backtest batch or data backfill."*
   - Steps: confirm inputs and budget -> pick and show the compute target -> launch an async subagent or job ->
     **return control at once** -> on events: notify only on failure or budget breach -> on finish, write the
     brief.
   - Checks: budget recorded before launch; the job card exists; no polling right after launch.
   - Borrows: Deep Agents async subagents, loop-me push right, superpowers continuous execution with rulings.

9. **`brief-results`** (MI) - *"Write a decision-ready brief of results: overnight jobs, backtests, routine runs, or
   a review verdict on whether a result is real."*
   - Steps: collect artifacts -> check each claim against evidence -> sanity battery (out-of-sample vs in-sample,
     parameter sensitivity, trade count, cost sensitivity, look-ahead and survivorship flags) -> verdict ->
     **one** recommended next action.
   - Checks: each number links to its artifact; red flags are in plain words; the brief fits one screen.
   - Borrows: loop-me "brief", superpowers `verification-before-completion`, the local `morning-brief` skill.

10. **`connect-source`** (MI, `include_tools: connector_catalog connector_probe secure_credential_form`) - *"Connect
    a broker account or data source and prove it works read-only."*
    - Steps: choose the connector -> human-only checklist (vendor-side clicks) -> open the **secure credential form**
      (writes to `qmx/*`; the agent never handles values) -> read-only probe -> label demo or live -> request a
      grant.
    - Checks: no credential text in chat or logs (H4); no order-capable scope requested (H3); the probe passes.
    - Borrows: Pocock `wizard` (human steps only), Wayfinder "task" ticket.

11. **`schedule-routine`** (MI, `include_tools: schedule_create schedule_update schedule_pause`) - *"Turn a
    repeating chore into a scheduled routine with a trigger, checkpoint and brief."*
    - Steps: find the loop -> trigger (event preferred to schedule) -> steps (existing workflows) -> checkpoint
      pushed right -> brief format -> budget per run -> create the schedule (interrupt).
    - Check: an implementer could build it without asking a question (loop-me definition of done).
    - Borrows: Pocock `loop-me`.

12. **`explain-plainly`** (MI) - *"Re-explain the last answer in plain words with the glossary terms. Use when
    the operator says 'wait, what?' or seems lost."*
    - Steps: give one line of context -> Simplified Technical English -> glossary terms -> one example from the
      operator's own data.
    - Check: no undefined jargon.
    - Borrows: Pocock `wait-what`, `teach` (fluency vs retention).

13. **`capture-skill`** (UI) - *"Turn a procedure we just did into a reusable skill draft with evaluations."*
    - Steps: name the repeated context -> write three eval scenarios first -> minimal SKILL.md (one level of
      references) -> test with a fresh subagent -> approval -> save to `/skills/editable/`.
    - Checks: the description says what and when and doesn't overlap existing descriptions; the evals pass.
    - Borrows: Anthropic evaluation-driven development (Claude A / Claude B), `writing-for-agents`, Deep Agents
      writable skills.

Not proposed as skills: anything that places orders (out of scope by constitution); session handoff
(`SummarizationMiddleware` plus the phase-boundary hook H11 cover it); TDD and code review internals (they live in
the factory lanes, not in the operator's Copilot).

---

## 7. HOOKS (deterministic rules as LangChain middleware)

Order matters: `before_*` runs first to last, `after_*` runs in reverse, `wrap_*` nests. Put security first.

| Id | Hook | Middleware / LangChain hook | Rule |
|---|---|---|---|
| H1 | **ModeGate** | custom; `wrap_model_call` (filter `request.tools` by mode; mode prompt fragment; sticky model) + `wrap_tool_call` (reject disallowed calls) | A tool outside the current mode's allowlist is invisible, and fails if called anyway. Moving to a more powerful mode needs an interrupt; moving to a less powerful one applies at once. |
| H2 | **GrantIntersection** | `SkillsMiddleware(tools=resolver)` + `wrap_tool_call` | Skill tools = `include_tools` intersected with session GrantRecords intersected with the mode allowlist. A skill never grants (DEC-0315). Unknown means hidden. |
| H3 | **MoneyPathFence** | custom `wrap_tool_call`, outermost | Any tool tagged `money_path`, `order`, `live_binding` or `sizing` is refused with no override; tools tagged `paper` need H5. The Copilot has no live-trading tool at all. |
| H4 | **SecretsGuard** | `PIIMiddleware` with custom detectors (API keys, tokens, account numbers) on input, output and tool results | Block or redact. If the operator pastes a credential, redact it and point to the secure form. Nothing secret goes into the journal. |
| H5 | **ApprovalGate** | `HumanInTheLoopMiddleware(interrupt_on=...)` + checkpointer | Interrupts (approve, edit or reject) for publish, install, grant, delete, schedule create, network allowlist change, spend above the limit, compute target off the allowlist, paper-account actions. The `when` predicate scopes this to risky arguments. |
| H6 | **BudgetGuard** | `ModelCallLimitMiddleware`, `ToolCallLimitMiddleware` + custom cost meter in `after_model` | Per-turn and per-job caps on model calls, tool calls and money. A breach jumps to the end with a budget brief. Thresholds are editable in Settings. |
| H7 | **EvidenceBeforeClaims** | custom `after_agent` (or `after_model` with `jump_to: model`) | If the final message claims done, fixed, passing or published and this turn has no matching verification artifact (compile, dry run, test, probe, run id), send it back with a reminder (once), then label the reply "unverified". |
| H8 | **ArtifactEmitter** | middleware `transformers` + `wrap_tool_call` | Every Brief, plan, canvas, preview, job, report or verdict is registered with a type and a `view:*` id and streamed to the UI preview tabs. No artifact exists only in chat text. |
| H9 | **SlashPin** | app layer before `invoke` (Deep Agents expects the app to parse) | `/skill-name` goes into `pinned_skills`; `/mode` sets `copilot_mode`. The UI shows the pinned skill as a label (`lc_source=pinned_skill`). |
| H10 | **PlanGate** | custom `wrap_tool_call` on Build tools | Tools that write drafts need an approved Brief id in state, except on the spike path, which writes only to a throwaway scratch area. This is the superpowers HARD-GATE as code. |
| H11 | **PhaseBoundary** | `SummarizationMiddleware` + custom `after_agent` | Near the context limit, suggest compact or handoff only at a phase boundary (after a Brief, publish or verdict), never mid-step. |
| H12 | **Resilience** | `ModelRetryMiddleware`, `ToolRetryMiddleware`, `ToolErrorMiddleware`, `ModelFallbackMiddleware` | Retry, then fall back to another provider (any compute provider). Errors come back as tool messages, not crashes. |
| H13 | **Audit** | custom `after_model` + `wrap_tool_call` | Append mode switches, approvals, tool calls (args redacted by H4) and verdicts to the journal with `caller_kind=agent`. |
| H14 | **SkillWriteControl** | `FilesystemPermission` deny on `/skills/approved/**`, `mode="interrupt"` on `/skills/editable/**`; `after_agent` sets `skills_metadata: None` when a skill was edited | Curated skills are read-only. New skills need approval and are picked up on the next run. |
| H15 | **RubricLoop** | `RubricMiddleware` (beta) | For Build outputs: self-grade against the Brief's success checks, up to N iterations, before asking the operator. |
| H16 | **ReturnAfterLaunch** | custom `after_model` (`jump_to: end` after a `job_launch` result) | After starting a background job, hand control back, as the Deep Agents async-subagent docs warn. Progress arrives as events, not polling. |

Skill-trigger reliability (the superpowers lesson): add a light `before_agent` "skill check" that, for authoring
sessions with no approved Brief, pins `shape-idea` when the message reads as a build request (a keyword and
classifier guard with a fast model). This is the deterministic version of `using-superpowers`, and it should be
editable and possible to turn off.

---

## 8. How the pieces chain (router view for `copilot-guide`)

- **Main flow:** `shape-idea` (Plan) -> approval card -> `build-workflow` or `build-mini-app` (Build) -> publish or
  install interrupt -> `launch-long-run` or `schedule-routine` (Run) -> `brief-results` (Review).
- **On-ramps:** something broken -> `fix-broken-app`; a new data or broker connection -> `connect-source`; "is this
  real?" -> `research-strategy` or `brief-results` review branch; too big for one session -> `wayfind-effort`.
- **Underneath:** `explain-plainly` at any time; `capture-skill` after any procedure that keeps coming back.
- **Context hygiene:** keep shape -> build in one thread (the Brief is a primary source). Background runs are
  separate threads. Briefs link to artifacts and never paste raw output.

---

## 9. Open questions for the operator (decisions, not facts)

- Q1. Five modes (Ask, Plan, Build, Run, Review), or merge Review into Ask with a "deep" toggle like Amp's dial?
  Recommended: keep five. Review's adversarial deep tier earns its place on overfitting calls.
- Q2. Debug as its own mode (Cursor and Roo), or a pinned skill inside Build? Recommended: a pinned skill. Fewer
  modes for a non-technical operator.
- Q3. Should the Copilot auto-pin `shape-idea` on build-like requests (the H-skill-check)? Recommended: yes,
  default on, with a Settings toggle.
- Q4. Paper-account actions in Run behind H5, or not available at all from the Copilot? Recommended: behind H5,
  because paper is pre-live evidence. Live stays absent either way.
- Q5. Do model tiers map to named providers per mode in Settings (sticky), or does the Copilot pick
  automatically? Recommended: sticky per mode, editable, with a default per tier.
