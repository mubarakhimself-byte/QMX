> STATUS 2026-10-16 (rubric walk): KEEP-AS-SOURCE. See 27-rubric-walk.md. Rulings in 26 win.

# 13 - Failure handling, supervision and RLM steps

Date: 2026-10-16. Sources were read in the built-in browser. Nothing here was run locally.

The question: QMX's own workflow engine (on the Claude Agent SDK, model-agnostic) has step kinds script, rule, model call, agent, human gate, sub-workflow and grader. It checkpoints after each step, wakes on cron or events, and runs a cheap pre-check before waking a model. Who writes it, who watches it, how does the operator hear about failures, and how do we recover a failed agent step without redoing paid work?

---

## 1. Shepherd

**Links**
- Site: https://shepherd-agents.ai/
- Paper: https://arxiv.org/abs/2605.10913 (HTML: https://arxiv.org/html/2605.10913). Yu, Chong, Nandi, Soylu, Sun, Manning, Shi. Northeastern and Stanford, 2026.
- Code: https://github.com/shepherd-agents/shepherd (MIT licence, about 2.5k stars, "early alpha", Python 3.11+, `pip install shepherd-ai`)
- Paper experiments: https://github.com/shepherd-agents/shepherd-experiments
- Docs: https://docs.shepherd-agents.ai/

**The idea.** The tagline is "your harness is just another agent." An agent's run is stored as data that a second agent (the "meta-agent", or shepherd) can read and change. Every model call, tool call and file change becomes a commit in a Git-like trace. A meta-agent can then:
- **observe** a worker by subscribing to its commits. Watching does not change the worker's run.
- **intercept** a risky action. Each action is two events: an *intent* when the worker asks for it, then an *outcome* when it happens. The supervisor can read the intent and deny it before the outcome lands.
- **fork** the worker and its sandbox together, as a copy-on-write branch.
- **revert** to any past commit. The paper says the restored state is byte-identical.
- **modify** the worker. A task is a typed Python function plus a docstring, so the supervisor can swap in a fixed version with the same signature, then resume.

**Four building blocks** (paper section 3):
| Block | What it is | What it gives |
|---|---|---|
| Task | typed function (signature + docstring become the prompt; output is type-checked) | swap or edit an agent |
| Effect | typed record of one action, split into intent and outcome | watch and block |
| Scope | the sandbox, providers and tools a task runs in; `fork`, `merge`, `discard` | try a branch, throw it away |
| Trace | persistent commit graph of all scopes | jump back to any point, replay from there |

**Reversibility tiers.** Each effect is tagged:
- *reversible* (file writes, sandbox state): rolled back natively;
- *compensable* (database writes): rolled back by a compensation handler the user writes;
- *irreversible* (model calls, emails): recorded for audit only.
This is the key point for QMX. Paid model calls cannot be undone, only recorded and reused.

**How it avoids redoing work.** Replay from a past commit rebuilds the exact state up to that point, so you only pay for the part after it (the "suffix"). Because the message prefix is byte-identical, the provider's prompt cache still hits. They measured about 95% cache-hit on Claude Haiku 4.5. Forks take about 134-143 ms whatever the image size, against about 53 s for a full copy of a 5.8 GB image.

**Three meta-agents built on it (results):**
1. *Runtime supervisor.* Two Haiku 4.5 workers code in parallel. A Sonnet 4.6 or Opus 4.7 supervisor watches both traces and has three tools: `inject` (send guidance), `handoff` (fork the leader's state to the follower) and `discard` (kill a stuck worker). On CooperBench the pair pass rate rose from 28.8% to 45.3% (Sonnet) and 54.7% (Opus), close to the 57.2% one-agent ceiling. Extra time was small: 1.4 min (Sonnet) or 4.3 min (Opus) per pair, because the supervisor only looks every few seconds.
2. *Counterfactual Replay Optimization (CRO).* This is "repair without rerunning." A proposer reads failed traces and suggests an edit. It pairs the edit with a *fix set* (examples it should fix) and a *guard set* (examples that must not get worse). Shepherd forks each old trace at the first commit the edit would change and replays only from there. CRO was best on 4 of 5 benchmarks, beating MetaHarness with 27-58% less wall-clock. On Terminal-Bench 2.0 it reached 35.2 against a baseline of 31.2, where GEPA and MetaHarness did not improve. Reuse of earlier computation rose from about 1% to over 60% during a run.
3. *Tree-GRPO for training.* The meta-agent picks a turn to fork, then runs sibling branches from it to get credit for each step. It adds 5.2 points over flat GRPO on Qwen3.5-35B-A3B. Not relevant to QMX now.

**Limits (stated by the authors, plus ours):**
- The results are a "proof of existence". They are not tuned policies and not tested broadly.
- On short tasks the supervisor can cost more tokens than the worker.
- Replay only saves money when an edit's effects stay local. If you edit something used everywhere, such as a system prompt or a shared tool, the replay is the whole run and the cache buys nothing.
- Irreversible effects (model calls, orders, messages) cannot be rolled back.
- **Windows is unsupported** (README: use WSL). OS-level permission enforcement is macOS Seatbelt or Linux Landlock only. QMX runs on Windows, so we should copy the *ideas*, not take the library as a dependency.
- The quickstart uses the `claude` CLI, but the paper says the core is model-agnostic.

**What QMX should take:** (a) store each run as an append-only list of typed step events with intent and outcome kept apart; (b) tag every step with a reversibility tier; (c) recover by forking at the first changed step and replaying only the suffix; (d) validate any fix against a fix set and a guard set before it becomes the new logic.

---

## 2. prime-agent / RLM

**Links**
- Repo: https://github.com/PrimeIntellect-ai/prime-agent (MIT licence, about 22k stars, has a Windows installer)
- Paper: "Prime Agent: A Self-Improving RLM Harness", https://arxiv.org/abs/2608.23552
- RLM paper: Zhang, Kraska, Khattab, "Recursive Language Models", https://arxiv.org/abs/2512.24601
- Key files: `prime-agent-runtime/src/rlm/repl.md` (kernel protocol), `__init__.py` (`rlm.spawn`, `collect`, `find_models`), `factory.py` (state-machine executor), `harness.py` (durable harness state). Rust crates live in `crates/` (`pa-ai`, `pa-agent`, `pa-daemon`, `pa-core`, `pa-tui`, ...).
- Related: verifiers https://github.com/PrimeIntellect-ai/verifiers (MIT) and the Environments Hub https://app.primeintellect.ai/dashboard/environments. The hub list did not load without sign-in, and I did not sign in.

**What RLM is.** A Recursive Language Model does not paste a huge input into its context. It treats the input as a *variable* in a code environment and writes code to inspect it, split it and call sub-models on the pieces. The RLM paper reports inputs up to 100x beyond the context window. Median gains over GPT-5 baselines were +26% against compaction and +13% against Claude Code, at similar cost.

**How prime-agent implements it.**
- **Persistent Python kernel.** `python -m rlm.repl` runs one long-lived Python namespace on one asyncio loop. It talks newline-delimited JSON (protocol v3): `execute`, `interrupt`, `snapshot`, `restore`, `list_names`, `shutdown`. Variables stay alive between cells, and background tasks keep running. The model's main tool is "run this Python".
- **Sub-model calls are function calls.** Inside the kernel, `await rlm.spawn(prompt, name=..., model="provider/model", thinking=...)` starts a real child agent. `rlm.collect` gets its answer, `rlm.list_subagents` shows status and staleness, and `rlm.delete_subagent` cancels it. `rlm.find_models` lists models the user has credentials for. The model can therefore loop over 500 files in code and fan work out to cheap models.
- **Kernel snapshot/restore.** The namespace is saved with `dill`, one variable at a time, with size caps. The write is atomic and a JSON manifest lists saved and skipped names. This is a checkpoint of the *working data*, not only of the chat.
- **Continual Harness.** Prompts, memories, skills and subagent specs live in `harness_state.json`, local to the session unless marked global. `/refine` makes small, evidence-backed edits and records each one as a `RefinementEvent` (trigger, changes, evidence, outcome). It never rewrites the base system prompt, and snapshots allow rollback.
- **Factory (a workflow engine inside).** `factory.py` runs a declarative state machine of subagent states (a DAG form compiles to it) with guarded transitions, joins, `foreach` fan-out and bounded re-entry. Settings we can copy:
  - failure policy per run: `fail_fast`, `continue`, or `escalate` (the default). Escalate *pauses* the run;
  - per-node retries (default 0, max 10);
  - rate-limit backoff (5 attempts, 1-60 s), detected from error text such as "429" or "usage limit";
  - budgets: `run_budget_ms`, `max_transitions`, `max_children`. Hitting one pauses the run once; resuming after that is "an explicit operator decision";
  - `resume(run_id)` first settles what already finished, then admits only states not yet started. Finished children are not rerun;
  - an event ledger, `status()` with `last_error` plus a one-line remedy, and a `watch` stream;
  - it is off by default (`/factory on`).
  - Gap: "Runs do not survive a kernel restart." The run registry is in memory. QMX must persist this.
- **Long-running features.** A daemon keeps sessions alive after the terminal closes. There are heartbeats, schedules, persistent `/goal`, and `/autonomous` within turn, token and time budgets with user quality gates. `prime-agent doctor [--fix]` repairs services.
- **Model-agnostic.** The `pa-ai` crate has one provider trait with clients for Anthropic, OpenAI, Google, Bedrock, Mistral, Azure and Prime Inference. It also has stream-failure retry and a "faux" provider for tests.
- **Safety warning (README).** It runs model-written Python with your user rights. The worker and kernel split is "not a security sandbox".
- **verifiers.** A library of tasksets, harnesses, agents and environments. A *trace* records messages, rewards, metrics, errors and one record per model call (model, usage, timing, error). Its "harness × model × runtime" split matches our "agent step = harness + model + policy".

**How it could be one QMX step kind: `rlm` (data-heavy research).**
- Use: a question over far more data than fits in context, e.g. "scan 3 years of tick files, 40 symbols, find regimes where strategy X breaks."
- Inputs: data handles (paths and query ids), a question, a model for the root, a cheap model for sub-calls, and a budget (tokens, dollars, wall-clock, max children).
- Runs: a fresh Python kernel in its own worker process, with data loaded as variables. The root model writes code and fans out sub-calls through our provider layer, not theirs, so the same budget and trace rules apply.
- Checkpoints: after each cell, a kernel snapshot plus a hash of the cell and a cached sub-call result keyed by (model, prompt hash). On retry, cached sub-calls return their saved answer and are not paid again.
- Output: a typed result plus an evidence pack (cells run, sub-call log, cost). A grader step checks it next.
- Two options: (a) reimplement the small pattern (kernel + `spawn`/`collect` + snapshot) in QMX; (b) run prime-agent as an external harness behind our step contract. Option (a) fits "API compatibility" and our own trace and budget rules better. Option (b) is quicker to try. Both are allowed by the MIT licence.
- Do not let it touch live trading paths. It runs arbitrary code, so it belongs in a research sandbox only.

---

## 3. Engine patterns

**Temporal** (https://docs.temporal.io/encyclopedia/retry-policies, https://docs.temporal.io/workflow-execution/event)
- Split: *workflow* code must be deterministic. Anything that can fail or vary (API calls, LLM calls) goes in an *activity*.
- Activities retry by default: exponential backoff from 1 s, coefficient 2.0, cap 100 s, unlimited attempts unless set, with a list of non-retryable error types.
- Workflows do *not* retry by default. Temporal's reason: a workflow failure usually means a design or input problem, and rerunning repeats the same logic at extra cost. Retry the failed activity instead.
- Replay: the event history rebuilds state after a crash. Completed activities return their recorded result and are not rerun.
- Reset: copy history up to a chosen point into a new execution and continue from there. This is how you rerun from a step after fixing code.
- Notification is not built into the engine. You alert from metrics or visibility queries, or add a failure handler in your own code.

**Inngest** (https://www.inngest.com/docs/durable-execution/durable-workflows)
- Each `step.run("id", fn)` result is saved as a checkpoint. On retry or resume the handler is replayed and finished steps return their saved result: "Doesn't run again once it succeeds." Only the failed step retries.
- `step.waitForEvent` pauses with no compute running, which suits human gates.
- Rule: code outside a step can run again on replay, so all non-deterministic work (DB, API, model calls) must be inside a step. Steps with side effects must be idempotent, because a step can succeed before its result is saved.

**Trigger.dev** (https://trigger.dev/docs/idempotency)
- Idempotency keys stop a task being *triggered* twice, for example a child started again when the parent retries. They do not make the code inside the task idempotent: on retry, `run()` starts from the top. Money-moving calls need the provider's own idempotency key.

**LangGraph** (https://docs.langchain.com/oss/python/langgraph/checkpointers)
- A checkpointer saves graph state at each super-step, per `thread_id`.
- *Pending writes*: if one node fails in a super-step, the writes from nodes that succeeded are kept. Resume does not rerun them.
- *Replay* from an old checkpoint skips the nodes before it, but nodes after it run again, *including LLM calls*.
- `update_state` writes a new checkpoint (with no edit to the old one), so you can patch state and continue. This is human repair.

**Common lesson.** Every mature engine does the same three things: (1) record each finished step's result durably; (2) on resume, return recorded results without calling again; (3) retry only the failing unit, with a policy. None of them sends you alerts by default. That is the app's job.

---

## 4. Answers for QMX

**Who writes the engine?** The engine is ordinary code in the QMX repo, not a product we buy and not something an agent invents at runtime. It is small: a step runner, a run ledger (append-only events in SQLite or Postgres), a scheduler for cron and events, the pre-check hook, and a provider layer for model-agnostic calls. Builder agents write it the same way P01-P24 shipped: one numbered packet per PR, one build and one check per PR, merged into `rebuild/base`. We copy proven patterns and do not import big frameworks: the Inngest/Temporal "saved step result" rule, LangGraph's "keep the writes of steps that succeeded", prime-agent's failure policies and budgets, and Shepherd's intent/outcome split and reversibility tiers. Shepherd is not usable as a library on Windows, and prime-agent's factory loses runs on restart, so neither can be the engine itself.

**Who monitors it?** Four layers, cheapest first. (1) *Scripts in the engine*: each step has a timeout, a budget, a retry policy and an output check (schema, grader). Most problems are caught here at no model cost. (2) *A watchdog*: a plain process on a timer that looks for stuck runs (no event for N minutes), runs over budget, repeated failures of the same step, and missed cron fires. No model needed. (3) *A "run doctor" role*: a model step that wakes only when (1) or (2) flags something. It reads the trace of the failed run, sorts the failure into "transient", "bad input", "bad output" or "logic wrong", and proposes an action. It runs on a cheap model first. It may retry or repair inside the budget, but it may not change workflow logic by itself. (4) *The copilot*: when the operator asks "what happened last night", it reads the same traces and explains in plain words. Live supervision of a running agent, Shepherd-style, is worth it only for long, costly agent steps. Shepherd's own limits note that for short tasks the supervisor can cost more than the worker.

**How is he notified?** By severity. *Urgent* (a run touching money or live trading failed, a budget was blown, a human gate is waiting on something time-sensitive): phone push plus an in-app inbox item. *Normal* (a research run failed after retries, or the doctor proposes a logic change): in-app inbox only, each item with a one-line cause, what was already tried, cost so far, and buttons such as "retry", "retry with bigger model", "skip step", "open trace" or "stop". *Routine* (successful runs, auto-recovered retries, spend): a daily digest. Each failure sends one message per run, not one per retry. A run paused by `escalate` waits in the inbox and does not ping again.

**How a failed step is retried, repaired or escalated without rerunning finished steps or re-spending money.** Every finished step writes its result to the run ledger under a key (run id + step id + hash of its inputs). On resume, the engine returns saved results and starts at the first step with no saved result. A model call is irreversible spend, so its response is cached by (model, prompt hash, params). Inside an agent or RLM step, each sub-call and tool call is also logged, so a retry of that step replays the saved prefix and the provider's prompt cache keeps the repeat cheap. The ladder is: (1) *retry* the same step with backoff for transient errors (429, timeouts, network), within a small cap; (2) *repair*, where the run doctor changes something local, such as a better prompt hint, a bigger model, more turns, or cleaned input. It forks at that step, replays only the suffix, and must pass the step's grader; (3) *escalate*, where the run pauses (prime-agent's default `escalate` policy) and the inbox item waits for him. Resume continues from the paused step. Steps with outside effects (orders, messages) carry an idempotency key, and the engine never repeats them automatically. Budgets (tokens, dollars, time, child count) are checked before each retry. When a budget runs out the run pauses. It never keeps spending.

**When to change the logic versus retry.** Retry when the cause is outside the logic: rate limits, timeouts, a flaky data source, or a one-off bad model sample. The test is that a retry or a sample with a different seed passes. Change the logic when the same step fails the same way across runs or inputs, when the grader rejects the output for the same reason twice, or when the doctor finds the step asked the wrong question or got the wrong input. Temporal says the same: a workflow-level failure usually means design or input, and rerunning repeats it. A logic change is never applied silently. The doctor writes a proposal, tests it the CRO way (fork old failed runs at the first step the edit changes, replay only from there, check a fix set of failures and a guard set of past successes), and the operator approves. The new version gets a version number, and old runs keep the version they ran with.
