> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 03 — Workflow engines: what QMX should build on the Claude Agent SDK

Research date: 2026-10-16. Sources were read in the built-in browser, page by page. Every claim below links to the page it came from. Where I did not verify something, I say so.

## Why this note exists

QMA v2 runs on the Claude Agent SDK. LangChain, LangGraph and Deep Agents are gone. QMX still needs a workflow system with these features: agentic, deterministic and mixed steps; loops; graphs with branches, joins, bounded cycles, human gates and checkpoints; long unattended runs; workflow memory; workflows that feed other workflows; and runs inside the Lab. It must work with any model provider. It has to live inside one Claude Max subscription, where background work may use at most about half of the spare usage. When a run hits that cap it must pause and later resume, not fail.

This note compares five systems, lists what QMX loses by leaving Deep Agents, and sketches a minimal runtime.

---

## 1. Claude Code dynamic workflows (the `Workflow` tool)

Sources:
- Docs: https://code.claude.com/docs/en/workflows
- Cookbook: https://github.com/anthropics/claude-cookbooks/blob/main/claude_agent_sdk/08_Dynamic_workflows.ipynb
- Tool schema: https://code.claude.com/docs/en/agent-sdk/typescript (sections "Workflow" input and output)
- The bundled `/workflow-authoring` skill, which is the script API reference Claude works from

### What it is

A workflow is a plain JavaScript script that Claude writes and a runtime runs in the background. The docs sum up the difference from subagents as "who holds the plan". With subagents, Claude decides each turn and every result lands in its context. With a workflow, the script decides, and intermediate results stay in script variables. Only the final return value reaches the session. (workflows page, "When to use a workflow")

### Script API

- `export const meta = { name, description, phases? }` must be the first statement and a pure literal.
- `agent(prompt, opts)` spawns one subagent with a clean context. Options: `label`, `phase`, `schema` (JSON Schema; the agent must return a validated object), `model`, `effort`, `isolation: 'worktree'`, `agentType`. It returns `null` if the agent is stopped or dies on an unrecoverable API error.
- `parallel(thunks)` is a barrier. It waits for all tasks and never rejects; failed slots become `null`.
- `pipeline(items, stage1, stage2, …)` sends each item through the stages independently, with no barrier between stages. The authoring guide says to use it by default.
- `phase(title)` groups agents for the progress view. `log(msg)` prints a narrator line.
- `args` is the JSON input passed at launch.
- `budget` has `total`, `spent()` and `remaining()`. It tracks the turn's token target from a "+500k" directive. It is a hard ceiling: once spent reaches total, `agent()` throws.
- `workflow(nameOrRef, args)` runs another saved workflow inline as a sub-step. Nesting is one level only.
- Plain JS between calls does filtering, dedup, loops and routing. The cookbook stresses that this logic costs zero tokens.

Schema handling: the runtime rejects a schema it can prove contradicts itself before the agent starts. Output that fails validation is retried up to 5 times (`MAX_STRUCTURED_OUTPUT_RETRIES`). (workflows page, "What the saved script looks like")

### Resume model

- The runtime records each agent's result in a journal (`<transcriptDir>/journal.jsonl`).
- `Workflow({scriptPath, resumeFromRunId})` replays the run in the order agents started. The longest unchanged prefix of `agent()` calls returns cached results. The first changed or failed call, and every call after it, runs again, even calls that had completed. (workflows page, "Which agents run again")
- To make replay reliable, the runtime makes `Date.now()`, `Math.random()` and a no-argument `new Date()` throw inside scripts. Timestamps have to come in through `args`.
- Resume works within the same session only. Results survive `claude --resume` of that session. A fresh session cannot relaunch the old run. (workflows page, "Resume after you leave the session")
- Stalled agents restart automatically, up to 5 times. `stallMs` sets the window per agent.

### Limits that matter for QMX

- **No mid-run user input.** A run pauses on its own only for permission prompts and usage-limit waits. The docs' advice for sign-off between stages is to run each stage as its own workflow. (workflows page, "Behavior and limits")
- The script has no filesystem, shell or `import()`. Only agents touch files.
- Concurrency defaults to 16 agents (`CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`, 1 to 256). A run is capped at 1,000 agents, and one `parallel()`/`pipeline()` call at 4,096 items.
- **Usage-limit pause does not apply to QMX's case.** A run pauses at a claude.ai usage limit and resumes after the reset only when all of these hold: the session is interactive, it is signed in with a subscription, `autoContinueAtUsageLimit` is on, the reset is under 24 hours away, and the run has waited fewer than twice. The pause does not happen under `claude -p`, the Agent SDK, background sessions or teammate sessions. In those, the agent fails. (workflows page, "When a run hits your usage limit") QMX drives Claude through the Agent SDK, so **QMX has to build pause-at-cap itself.**
- There is no scheduler. Something outside has to start a run.
- It runs Claude models only (Anthropic API, Bedrock, Google Cloud, Foundry). It is not model-agnostic.

### Launching from the SDK

Add `Workflow` to `allowed_tools` and ask for "a workflow" in plain words. The tool returns `async_launched` with `taskId`, `runId`, `scriptPath` and `transcriptDir`. Progress arrives as `TaskProgressMessage` and `TaskNotificationMessage`. Check `error` before assuming the run started. (cookbook; TS reference, "WorkflowOutput")

---

## 2. Claude Agent SDK pieces QMX would build on

- **Sessions:** `resume` by ID, `continue`, `fork`, `resumeSessionAt` (a message UUID), `persistSession: false`, and a `SessionStore` adapter that mirrors transcripts to shared storage. Sessions persist the conversation, not the filesystem; file rollback is a separate "file checkpointing" feature. https://code.claude.com/docs/en/agent-sdk/sessions
- **Subagents:** defined in code with `agents`, or as files under `.claude/agents/`. They give context isolation, parallelism, a custom prompt and a tool allowlist. A subagent can be resumed through its `agentId` within the same session. https://code.claude.com/docs/en/agent-sdk/subagents
- **Hooks:** `PreToolUse` (block or modify), `PostToolUse`, `PostToolUseFailure`, `Stop`, `StopFailure`, `SubagentStart`/`SubagentStop`, `PreCompact`, `PermissionRequest`, `TaskCreated`/`TaskCompleted`, `SessionStart`/`SessionEnd`, `Notification` and more. Many exist only in TypeScript. https://code.claude.com/docs/en/agent-sdk/hooks
- **Usage signals, the key input for a QMX budget governor** (TS reference, https://code.claude.com/docs/en/agent-sdk/typescript):
  - `SDKRateLimitEvent.rate_limit_info`: `status` (`allowed` / `allowed_warning` / `rejected`), `resetsAt`, `utilization`.
  - `SDKUsageReport.rate_limits.limits[]`: one row per plan meter, with `kind` (for example `session`, `weekly_all`, `weekly_scoped`), `percent`, `resets_at` and `severity`. It is `null` when the OAuth token lacks the `user:profile` scope.
  - The assistant error value `rate_limit` (a 429 against quota) is reported separately from `overloaded` (a 529).
  - `modelUsage` and `total_cost_usd` on the result. These are local estimates and include Workflow agents.

So QMX can read live subscription utilization and the reset time. It does not have to guess.

---

## 3. LangGraph

Sources:
- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/checkpointers
- https://docs.langchain.com/oss/python/langgraph/fault-tolerance
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/graph-api
- https://docs.langchain.com/oss/python/langgraph/use-subgraphs

- **State and reducers.** State is a typed schema. Each key has a reducer `reducer(left=current, right=update)`; a key with no reducer is overwritten. Reducers make joins safe when parallel branches write the same key.
- **Checkpoints at every super-step,** stored per `thread_id`. They enable human-in-the-loop, memory, time travel (replay and fork from any checkpoint) and fault tolerance.
- **Pending writes.** If one node in a super-step fails, the writes of the nodes that succeeded are kept, so a resume does not rerun them.
- **Durability modes:** `exit`, `async` and `sync`. `sync` writes each checkpoint before the next step starts.
- **Re-execution rule.** Checkpoints are taken at super-step boundaries. A resumed node runs again from the top of its function, so nodes must be idempotent (use idempotency keys and upserts). Changing the graph structure does not break resume of existing threads.
- **Interrupts.** `interrupt(payload)` saves state and waits with no time limit. `Command(resume=value)` continues, and the value becomes the return of `interrupt()`. Rules: don't wrap it in try/except, don't reorder interrupts inside a node, and make side effects before an interrupt idempotent. To re-prompt, keep the question in state and loop with a conditional edge rather than calling `interrupt` repeatedly inside a loop.
- **Fan-out.** `Send(node, private_state)` from a conditional edge gives map-reduce with per-item state. A `Send` can carry its own timeout.
- **Control.** `Command(update=…, goto=…, graph=PARENT, resume=…)`.
- **Bounded cycles.** `recursion_limit` caps super-steps (default 1000 since 1.0.6). Nodes can read the current step from `config["metadata"]["langgraph_step"]`.
- **Fault tolerance** (1.2+):
  - `RetryPolicy` with backoff, jitter and `retry_on`.
  - `TimeoutPolicy` with a hard `run_timeout` and an `idle_timeout` that progress or `runtime.heartbeat()` resets.
  - An `error_handler` that can route to compensation (a saga pattern).
  - `node_attempt`, so a node can switch to a fallback on retry.
- **Graceful drain** (1.2+). `RunControl.request_drain(reason)` stops the run at the next super-step boundary and saves a resumable checkpoint (`GraphDrained`). Resume with `invoke(None, config)`. A node can read `runtime.drain_requested` and skip expensive work. This is the closest LangGraph analogue to "pause at the usage cap".
- **Node caching.** `CachePolicy(key_func, ttl)` skips a node whose input is unchanged.
- **Subgraphs.** Three persistence modes: per-invocation (the default), per-thread, or stateless. Each subgraph has its own checkpoint namespace.
- **Store.** Long-term memory across threads, separate from the checkpointer and keyed by namespace.
- **Scheduling and tracing** are not part of the OSS library. Crons and webhooks come from LangSmith Deployment, and traces from LangSmith.

---

## 4. Deep Agents (what QMX used before)

Sources:
- https://docs.langchain.com/oss/python/deepagents/overview
- https://docs.langchain.com/oss/python/deepagents/memory
- https://docs.langchain.com/oss/python/deepagents/async-subagents
- https://docs.langchain.com/oss/python/deepagents/rubric
- https://docs.langchain.com/oss/python/deepagents/comparison

Deep Agents is a harness built on LangGraph. Its parts:

- **Virtual filesystem** (`ls`, `read_file`, `write_file`, `edit_file`, `delete`, `glob`, `grep`, plus `execute` with sandboxes).
  - Pluggable backends: `StateBackend`, `StoreBackend`, `FilesystemBackend`, and `CompositeBackend` with path routes such as `/memories/` → Store.
  - Declarative read/write permission rules where the first match wins.
- **Planning.** The `write_todos` tool, opt-in since v0.7 through `TodoListMiddleware`.
- **Subagents.**
  - Sync: one handoff, isolated or `fork` mode.
  - Async: launch, check, update and cancel tools; each is stateful on its own thread and talks to any Agent Protocol server.
- **Memory.**
  - `AGENTS.md` files are always loaded. Skills load by progressive disclosure.
  - Scope comes from the Store namespace: per agent (`assistant_id`), per user, or per organization.
  - Episodic memory is a search over past checkpointed threads.
  - Background consolidation runs on a cron and merges facts between conversations.
  - Concurrent writes to the same file are last-write-wins.
- **Context.** Summarization, offloading of large tool results, and automatic prompt caching on Anthropic and Bedrock.
- **HITL.** `interrupt_on={tool: True}` pauses before a named tool call.
- **Verification loop.** `RubricMiddleware(model, max_iterations)` uses a grader sub-agent that returns `satisfied`, `needs_revision`, `max_iterations_reached` or `grader_error`.
- **Model choice.** Works with any provider. Its own comparison page notes the Claude Agent SDK is tied to Claude.

## 5. LangChain posts on loops and harnesses

- **The Art of Loop Engineering** (https://www.langchain.com/blog/the-art-of-loop-engineering) describes four stacked loops:
  1. The agent loop.
  2. A verification loop: a deterministic or LLM grader checks the output against a rubric and sends back feedback.
  3. An event-driven loop: cron, webhooks or channels start runs.
  4. A hill-climbing loop: an analysis agent reads traces and rewrites prompts, tools or graders.

  A human can step in at every level, as the approver, the grader, or the reviewer of a harness change.
- **The Anatomy of an Agent Harness** (https://www.langchain.com/blog/the-anatomy-of-an-agent-harness) defines Agent = Model + Harness. The parts it lists:
  - The filesystem as the base primitive for durable state, plus git.
  - Bash and code execution.
  - Sandboxes.
  - Memory files.
  - Compaction and tool-output offloading.
  - Skills.
  - Ralph-style continuation: a hook catches the exit and re-injects the goal into a fresh context that reads state from files.
  - Planning files.
  - Self-verification through hooks that run tests.
- **How to Build a Custom Agent Harness** (https://www.langchain.com/blog/how-to-build-a-custom-agent-harness): a minimal loop plus middleware for each concern. Middleware covers deterministic logic, tools, custom state and stream handlers. The capability table includes retry and fallback, call limits, prompt caching, PII and HITL. The main idea is "task-harness fit".

---

## 6. Briefly: AutoGen GraphFlow, OpenAI Agents SDK, Hermes Agent

### AutoGen GraphFlow (experimental)

Source: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/graph-flow.html

- `DiGraphBuilder` builds sequences, fan-out, conditional edges and loops. An edge condition is a lambda over the last message, for example `"APPROVE" in msg`.
- **Activation groups** decide how a node joins its incoming edges: `all` waits for every edge, `any` fires on the first.
- A **loop exit** needs a termination condition, for example `MaxMessageTermination(10)`.
- **Execution graph vs message graph.** Edges decide order. `MessageFilterAgent` separately decides which earlier messages each node sees, for example the first user message plus the last reviewer message.
- **State.** `save_state()`/`load_state()` on agents and teams (https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/state.html). These are manual snapshots, not automatic checkpoints.

**Copy:** the all/any join semantics, and keeping "who runs next" separate from "what each node may read".

### OpenAI Agents SDK

- **Handoffs** (https://openai.github.io/openai-agents-python/handoffs/) are tools named `transfer_to_<agent>`. An `input_filter` controls how much history the next agent sees. `on_handoff` callbacks can prefetch data.
- **Guardrails** (https://openai.github.io/openai-agents-python/guardrails/):
  - Input guardrails run on the first agent, output guardrails on the final output, and tool guardrails on every call.
  - Each sets a tripwire and raises an exception.
  - **Blocking mode** (`run_in_parallel=False`) means the expensive agent never starts when the cheap check trips. This saves tokens.
- **Tracing** (https://openai.github.io/openai-agents-python/tracing/) is on by default. A trace holds spans; there is a `group_id` that links traces from one thread.

**Copy:** blocking guardrails as cheap gates, history filters at each handoff, and trace/span/group IDs.

### Hermes Agent cron

Sources: https://hermes-agent.nousresearch.com/docs/user-guide/features/cron and https://hermes-agent.nousresearch.com/docs/user-guide/features/memory

This is the most useful source for QMX's budget constraint.

- **No-agent jobs** (`no_agent=True`). A script runs on the schedule and its stdout is delivered as is, with no model and no tokens.
  - Empty stdout means a silent tick.
  - A non-zero exit sends an alert.
- **`wakeAgent` gate.** A pre-check script ends with `{"wakeAgent": false}` to skip the LLM for that tick. It can also pass `context` to the agent. The docs present this as a free way to decide whether to spend tokens. Recipes: file-change, state-diff and counter gates.
- **Quota hold.** When a subscription provider reports its usage window closed and gives a retry-after time:
  - The scheduler parks the job (`quota_hold_until`) and alerts once.
  - Missed runs are merged into one, and the next run is set to the first slot after the window.
  - Any run that reaches the model clears the hold.

  This is "pause, don't fail" at the scheduler level.
- **Retry ladder** of 5, 15 and 30 minutes, used only when no model call was made. The docs call this spend-neutral and say it cannot duplicate side effects.
- **Pre-dispatch validation.** Checks credentials, skills, delivery targets and MCP servers. On failure the status becomes `blocked_config` with one alert and no LLM call.
- **Failure handling.**
  - Incidents are deduped by a normalized error signature.
  - A `failure_streak` nudge asks the operator to fix or pause a job that keeps failing.
  - Fire identity and admission recovery: an interrupted run is marked `unknown` and never re-run automatically.
- **Chaining.**
  - `context_from=[jobs]` injects the latest completed output of upstream jobs. It does not wait for them.
  - `continuity=true` injects the job's own previous output so it can skip repeats.
  - `[SILENT]` suppresses delivery on success.
- **Safety and schedule rules.**
  - A cron run cannot create cron jobs.
  - Model pins are owned by the user; the agent cannot change them.
  - Each job can pin its own reasoning effort.
  - After downtime, a job catches up with one run, not one per missed slot.
  - Webhooks can trigger jobs too.
- **Memory.** Bounded `MEMORY.md` and `USER.md` with hard character limits. A write that would overflow returns an error instead of silently dropping entries. Only one writer per memory home.

---

## 7. Capability matrix

Legend: Yes = built in · Partial = possible with limits or manual work · No = not provided · Ext = needs an external product.

| Capability | Claude Code Workflow | LangGraph | Deep Agents | AutoGen GraphFlow | Hermes cron |
|---|---|---|---|---|---|
| Durable state / checkpoint | Partial: per-agent result journal, session-scoped | Yes: checkpoint every super-step, three durability modes, pending writes | Yes (inherits LangGraph) | Partial: manual `save_state` | Partial: job definitions and run ledger on disk; no in-run state |
| Resume | Partial: `resumeFromRunId`, longest unchanged prefix replays from cache; same session only | Yes: by `thread_id`, time travel and fork, drain then resume | Yes | Partial: reload state | Partial: interrupted run marked `unknown` and not rerun; missed slots catch up once |
| Human interrupt / gate | No: no mid-run input; split stages into separate workflows | Yes: `interrupt()` and `Command(resume)` | Yes: `interrupt_on` per tool | Partial: user-proxy style agent | No: delivery and reply only ("continuable jobs") |
| Fan-out / join | Yes: `parallel` (barrier), `pipeline` (no barrier) | Yes: `Send` plus reducers | Yes: parallel subagents, async subagents | Yes: parallel edges, `all`/`any` activation | Partial: `context_from` fan-in of latest outputs |
| Bounded cycles | Yes: JS loops, 1,000-agent cap, `budget` | Yes: conditional edges plus `recursion_limit` | Yes, plus `RubricMiddleware.max_iterations` | Yes: conditional loop plus termination condition | n/a (recurrence, not cycles) |
| Scheduled / event triggers | No | Ext: LangSmith crons and webhooks | Ext: same; consolidation runs on cron | No | Yes: cron, intervals, one-shots, webhooks |
| Memory scopes | No (script variables only) | Yes: thread (checkpointer) plus namespaced Store | Yes: agent, user, org namespaces; episodic; background consolidation | Partial: Memory/RAG components | Yes: bounded MEMORY.md/USER.md; per-job `continuity` |
| Deterministic zero-token nodes | Partial: plain JS between agents, but no I/O in the script | Yes: any Python node; node caching | Partial: middleware hooks, interpreter | Partial: custom agents | Yes: `no_agent` scripts, `wakeAgent` gate |
| Observability / traces | Yes: `/workflows`, `journal.jsonl`, transcripts, progress events | Ext: LangSmith; streaming and state history built in | Ext: LangSmith; per-subagent streams | Partial: event stream | Yes: run ledger, incidents, `cron doctor` |
| Model-agnostic | No: Claude only | Yes | Yes | Yes | Yes: per-job pins, fallback providers |
| Pause at usage cap, then resume | Partial: interactive subscription sessions only, not the SDK | Partial: drain is the mechanism; QMX supplies the trigger | Same as LangGraph | No | Yes: `quota_hold_until` |

---

## 8. What QMX loses by leaving Deep Agents / LangGraph, and must rebuild

None of these come with the Claude Agent SDK. The SDK gives sessions, subagents, hooks, the Workflow tool and usage telemetry. It does not give a graph runtime.

1. **Checkpoint after every step, keyed by thread.** QMX needs its own run store, with pending writes kept on partial failure.
2. **Resume that survives a process restart or a new session.** Workflow resume only works inside the same Claude Code session. QMX needs resume from its own store.
3. **Human interrupts inside a run** (`interrupt`/`Command(resume)`, and `interrupt_on` per tool). The Workflow tool has none.
4. **Typed state with reducers,** for safe joins from parallel branches.
5. **Send-style fan-out with per-item state and per-item timeout.**
6. **Retry, timeout (run and idle with heartbeat), and error-handler routing** for each node.
7. **Graceful drain at step boundaries,** which is the basis of pause-at-cap.
8. **Recursion and step limits** that a node can read.
9. **Node caching** by input hash.
10. **Subgraphs with chosen persistence,** plus parent and child checkpoint namespaces.
11. **Long-term Store with namespaces** (agent, user, org), episodic search over past runs, and background consolidation.
12. **Virtual filesystem backends with path routing and permission rules.** The Claude SDK works on the real disk; any routing has to be QMX's own.
13. **The rubric verification loop** with a grader on a separate, cheaper model and an iteration cap.
14. **Async subagents** that can be checked, steered and cancelled.
15. **Model-agnosticism at the graph level.** In Deep Agents any node could run any provider. In QMX that now goes through the relay, so the workflow runtime must treat the model as a node parameter, not a property of the engine.
16. **Time travel and fork from an old checkpoint** for debugging.

The SDK covers well: agent loops, tool permissions, hooks, session resume, subagent isolation, structured output, prompt caching, live rate-limit telemetry, and the Workflow tool for big fan-outs inside one Claude stage.

---

## 9. Minimal design sketch: QMX workflow runtime

The principle: **QMX owns the graph, the state and the checkpoints. Claude, through the Agent SDK or the Workflow tool, is just one kind of node executor.** That keeps the runtime model-agnostic and lets it pause at the cap without depending on interactive Claude Code behaviour.

### 9.1 Workflow definition (a data file plus code hooks)

```yaml
id: wf.backtest-sweep
version: 3                      # a bump starts new threads; old threads keep their version
state_schema:                   # typed keys, each with a reducer
  candidates: {type: list, reducer: append}
  results:    {type: map,  reducer: merge}
  verdict:    {type: str,    reducer: replace}
nodes:
  - id: load       kind: script   ref: lab/scripts/load_universe.py   # 0 tokens
  - id: gen        kind: llm      model: relay:any-cheap   schema: Candidates
  - id: run_bt     kind: script   ref: engine/backtest.py   fanout: candidates  timeout: {run: 900, idle: 120}
  - id: review     kind: agent    model: claude:opus  tools: [Read, Grep]  schema: Review
  - id: approve    kind: human    prompt: "Promote these to paper trading?"  timeout: none
  - id: report     kind: subflow  ref: wf.write-report
edges:
  - load -> gen -> run_bt -> review
  - review -> gen      when: "state.verdict == 'revise'"   # bounded cycle
  - review -> approve  when: "state.verdict == 'ok'"
  - approve -> report  when: "resume.approved"
limits: {max_steps: 50, max_cycles: {review->gen: 3}, max_agents: 40}
```

### 9.2 Node kinds

| Kind | Runs | Token cost | Notes |
|---|---|---|---|
| `script` | A Python or JS function or file in a sandboxed subprocess (Lab kernel or engine) | 0 | Deterministic. Its stdout or return value goes into state. It can return `{wake: false}` to skip the downstream LLM, as Hermes' `wakeAgent` does. |
| `rule` | An inline expression over state (routing, filters, thresholds) | 0 | Evaluated by the engine. Used for edges and gates. |
| `llm` | One model call through the relay, with a JSON schema | Low | Any provider. Validated with retries, like the Workflow tool's 5-attempt rule. |
| `agent` | A Claude Agent SDK `query()` (or relay agent) with tools, a tool allowlist and `max_turns` | High | Its session ID is stored, so it can be resumed or forked. |
| `fanout` | A modifier on any node: one task per item, then join by reducer; all/any activation as in AutoGen | Varies | For large Claude-only fan-outs a node may delegate to the `Workflow` tool, with its `runId` stored. |
| `human` | Saves the checkpoint and emits a gate to the QMX UI | 0 | No time limit by default. Resumes with the operator's value. Same rules as LangGraph `interrupt`: one per node, side effects before it must be idempotent. |
| `subflow` | Another workflow, inline or by reference | — | Has its own checkpoint namespace. This is how one workflow's output feeds another. |
| `grader` | A deterministic check or an LLM judge against a rubric | 0 or low | Produces a verdict plus feedback, which drives verification loops. |

### 9.3 State

- **Run state:** one typed object per `thread_id`. Every key has a reducer (`replace`, `append`, `merge`, `max`, or custom). Parallel branches only return partial updates, and the engine merges them with the reducers.
- **Artifacts:** large outputs (data frames, reports) go to the content-addressed Lab store. State holds only references, which keeps checkpoints small, as LangGraph's DeltaChannel does.
- **Memory scopes:**
  - `run` (this thread).
  - `workflow` (all runs of this workflow, for example "last output", which works like Hermes `continuity`).
  - `project` / `lab`.
  - `operator` (global preferences).

  Each scope is a namespaced store. Writes to shared scopes go through a consolidation step so two writers do not overwrite each other. Memory files have hard size limits; an overflow errors instead of silently truncating.
- **Cross-workflow data:** a workflow declares typed `outputs`. Another workflow declares `inputs_from: [wf.x.outputs.y]`. It reads the latest completed output, or it waits when `wait: true`. The design follows Hermes `context_from`, plus an optional wait.

### 9.4 Loop spec, the first-class object for loops

```yaml
loop:
  trigger:  {cron: "0 */6 * * *"} | {event: "lab.dataset.updated"} | {after: wf.x} | {manual: true}
  precheck: script ref returning {wake: bool, context: {...}}     # 0-token gate
  goal:     "Find parameter sets with Sharpe > 1.2 out-of-sample"
  state:    workflow-scope keys carried between iterations (best_so_far, seen_ids)
  action:   subflow wf.backtest-sweep  (policy: explore | exploit | fixed-plan)
  evidence: list of artifacts each iteration must produce (metrics.json, trades.parquet)
  feedback: grader node(s): deterministic first, LLM judge second; output = verdict + notes
  stop:     any of [goal_met, max_iterations: 10, no_progress_rounds: 2,
                    budget_exhausted, operator_stop, deadline]
  on_stop:  deliver summary | open human gate | [SILENT] if nothing new
```

This covers all four loop levels in the Loop Engineering post:
- Level 1: an `agent` node.
- Level 2: the `feedback` and `stop` fields.
- Level 3: `trigger` and `precheck`.
- Level 4: a separate "harness-improver" loop whose evidence is the run traces and whose action proposes prompt or tool diffs behind a human gate.

### 9.5 Checkpoints

- Use an append-only event log per run in SQLite: `node_started`, `node_completed{output_hash, state_delta}`, `gate_opened`, `gate_resolved`, `paused{reason}`, `resumed`.
- Take a state snapshot at every step boundary, using sync durability by default.
- A node that completed is never rerun on resume. A node that was running when the run stopped restarts from the top, so nodes must be idempotent. Side-effecting scripts get an idempotency key `run_id:node_id:attempt`.
- Pending writes: in a fan-out, finished items are kept. Only failed or unfinished items rerun. This is better than Workflow-tool replay, where one failure reruns every later agent.
- Agent nodes store their Claude `session_id`, so a resumed agent can `resume` or `fork` its session instead of starting cold.
- Time travel: from any snapshot, fork a new thread with edited state, for debugging in the Lab.
- No non-determinism inside the engine's control flow. Timestamps and randomness come in as inputs, the same rule as the Workflow runtime.

### 9.6 Budget, pause and resume

1. **Governor.** It subscribes to `SDKRateLimitEvent` and `SDKUsageReport.rate_limits.limits[]` (`percent`, `resets_at` per meter: session, weekly). It computes the headroom left for background work: `allowed = foreground_reserve_policy(percent)`. Example: background may run only while the session meter is under 50% and the weekly meter is under its pro-rata line. The exact formula is an operator setting, editable in the UI.
2. **Admission control.** Before any LLM or agent node starts, the governor answers *go* or *hold*. `script` and `rule` nodes always run. Deterministic work keeps going while LLM work waits.
3. **Drain, not kill.** When headroom runs out, the engine sets `drain_requested`. Running nodes finish (or checkpoint at their own boundary), no new LLM nodes start, and the run moves to `paused{reason: usage_cap, resume_at: resets_at}`. This works the same way as LangGraph's `RunControl.request_drain`.
4. **Hard rejections.** A `rate_limit` 429 or a `rejected` status in the middle of a node marks that node `waiting`, not failed. It keeps no partial output and reruns once the window reopens. Retries are capped, as in the Workflow tool's two-wait rule, and after the cap the run escalates to a human gate.
5. **Scheduler parking**, as Hermes `quota_hold_until` does. Triggered loops do not fire into a closed window. Missed fires merge into one, and the operator gets one alert.
6. **Per-run budgets.** Each run has `max_tokens`, `max_agents` and `max_cost_estimate` caps. Nodes can read `budget.remaining()`, so loops scale their depth to what is left, like the Workflow `budget` global.
7. **Spend-neutral retries.** A failure before any model call (network down at wake) retries quickly on a 5/15/30-minute ladder. A failure after a model call follows the node's normal retry policy.

### 9.7 Observability

- Each run is a trace, each node a span, and `group_id` is the thread, following the OpenAI model.
- Every span records model, provider, tokens, cost estimate, cache hits, duration, attempt number and wake decision.
- The run view lists phases, nodes, live progress, gates waiting for the operator, and the paused reason with a countdown to `resume_at`.
- Incident dedup by error signature and a failure-streak nudge, as in Hermes.
- Traces are stored in a form the Level-4 improver loop can read.

---

## 10. Ideas for QMX

1. **Own the graph and use Claude as an executor.** Build a small QMX engine (state, reducers, edges, checkpoints, gates) whose `agent` nodes call the Claude Agent SDK and whose `llm` nodes call the relay. Don't make the `Workflow` tool the engine: it has no human gates, resumes only within one session, runs Claude only, and its usage-limit pause does not work under the SDK.
2. **Use the `Workflow` tool as one node type for big Claude-only fan-outs** (audits, sweeps, adversarial verification). Store its `runId` and `scriptPath`, and pass the cap through `args`. Run each stage that needs sign-off as its own workflow, as the docs advise.
3. **Build the budget governor on live SDK telemetry** (`SDKRateLimitEvent`, `SDKUsageReport.rate_limits`). Background LLM work runs only while the operator-set headroom allows. At the line, drain and pause until `resets_at`. Never treat a quota rejection as a failure. Check that QMX's OAuth token has the `user:profile` scope; without it `rate_limits` is `null`.
4. **Make zero-token work explicit.** Provide `script` and `rule` nodes, plus a `precheck` that returns `{wake: false}` (Hermes' pattern). Every loop gets a cheap gate before any LLM call. Use blocking-mode guardrails (OpenAI) so a cheap check runs before an expensive agent starts.
5. **Make the loop spec a first-class object**, with trigger, precheck, goal, state, action, evidence, feedback and stop. Stop rules always include `max_iterations`, `no_progress_rounds` and `budget_exhausted`. Use loop-until-dry (two empty rounds) for open-ended discovery.
6. **Checkpoint after every step in SQLite, with pending writes.** In a fan-out, only failed items rerun. This beats Workflow replay, which reruns everything after the first failure.
7. **Require idempotent nodes.** Give side-effecting scripts an idempotency key. Document LangGraph's interrupt rules for human gates: one gate per node, no try/except around it, idempotent effects before it.
8. **Human gates are nodes that park the run with no time limit** and appear in the QMX UI. When the cap is hit too many times, or a run fails repeatedly, escalate to a gate instead of failing silently.
9. **Typed outputs and inputs between workflows** (`inputs_from`, with optional wait), plus a `continuity` flag so recurring loops see their own last output and skip repeats.
10. **Memory scopes as namespaced stores** (run, workflow, lab, operator), with hard size limits that error on overflow, one writer per scope, and a scheduled consolidation job for shared scopes.
11. **Copy AutoGen's join semantics:** `all` vs `any` activation groups on joins, and a separate "message graph" or context filter so each node sees only the inputs it needs.
12. **A verification loop as a standard pattern:** a deterministic grader first, then an LLM judge on a cheaper model, then feedback, with a capped iteration count. This is the Deep Agents rubric pattern, rebuilt on the engine.
13. **Scheduler rules from Hermes:**
    - One merged catch-up after downtime.
    - `quota_hold_until` parking.
    - Validation before dispatch, so a misconfigured job never spends tokens.
    - Incidents deduped by error signature.
    - Workflow runs cannot create schedules.
    - Model and effort pins stay under the operator's control.
14. **Run Lab workflows in the same engine:** notebook cells and node-editor nodes compile to `script`/`llm`/`agent` nodes in the same graph format, so experiments and production loops share checkpoints, budgets and traces.
15. **Traces follow the OpenAI shape** (trace, span, group), with token and cost data on every span. A Level-4 "harness improver" loop reads them and proposes prompt, tool or grader changes behind a human gate.
16. **Keep the engine deterministic.** No wall-clock time or randomness in control flow; pass them in as inputs, the same rule the Workflow runtime uses so that replay works.

### Open questions (not verified here)

- Whether the `Workflow` tool, when driven from the Agent SDK under a Max-subscription login rather than an API key, behaves exactly as documented. The cookbook uses an API key.
- Whether `SDKUsageReport` is emitted on a regular cadence or only on request. The reference marks the type experimental.
