# 44. Agentic-engineering foundations of the QMX harness

Date: 2026-10-18. Research and design input for the planning lead and the architect. Nothing here is ratified. It does not edit the architectures, 26, 39 or `UI-HANDOFF.md`; section 4 lists what the architect may fold in.

**Labels.** [retrieved] read today at the cited place (file, code ref or web page). [remembered] from training knowledge, not checked today. [inferred] reasoned here.

**Code ref.** Every code path is on `origin/engine/base` (`132169c7`) in `D:\QMX-worktrees\agent-system`, read with `git show`. Paths are relative to `qmx-agents/packages/` unless they start with `qmx-agents/`.

**Lenses applied.** Deep modules and seams (one adapter is a hypothetical seam, two is a real one; the interface is the test surface), domain language (one word per concept), data structures first, and subtract before you add.

---

## 0. In plain words (for the operator)

**What QMX's assistant is for.** QMX should behave like a research partner that knows your trading work. You bring a rough idea, a video, a paper or a hunch. It turns that into something testable, builds and runs the experiments, judges the results honestly, keeps what failed as well as what worked, and brings you only what needs your judgment. It shows you results as pictures and pages rather than walls of text. The routine work runs on its own, overnight if needed.

**Where QMX stands on the five "engineerings".**

- **Prompts (what the model is told).** The plumbing exists. The words were never designed; that is your session with the planning lead. Missing: a fixed set of named places where each layer of instructions goes, a size limit, and a test that shows exactly what each kind of agent is told.
- **Context (what the model sees at each moment).** Strong for workflows: big jobs are split into chunks, agents compact early, and memory goes in as quoted material. Weak for tools: every chat loads all 82 QMX tools at once. Your preferred Chinese models cannot use Claude's built-in tool search, so they pay for all 82 on every turn.
- **Harness (the machinery around the model).** This is QMX's strongest part: the assistant engine, the workflow engine, permissions, the money gate, sign-in handling and traces. Missing: one place that decides everything a given chat gets (tools, instructions, skills, sub-agents), instead of three places.
- **Graphs (workflows drawn as boxes and arrows).** Built and solid: one engine, a node-editor format, replay, saved results and triggers. One gap matters for trading: the "search, notice the plateau, change the search space, search again" pattern needs a loop inside a loop. The first version refuses that, so it must be checked.
- **Loops (repeat, check, decide, improve).** Built for workflows: loops with stop rules, checkers, monitors, and self-improvement that tests a challenger against a champion. Missing: a test set for the assistant itself, so a change to its instructions, skills or default model is measured before you rely on it.

**How tools work today, in one paragraph.** A QMX feature is a function in QMX's control service. One table turns it into both a web route for the screens and a tool. A second table in the assistant engine lists which of those tools the agent may use, and how risky each one is: read, research write, manage, or money proposal. The assistant engine bundles them into one tool server named `qmx` that runs inside QMX, and every chat gets that same full list. Reads run freely. Research writes follow your setting. Manage actions always ask you. Background workflow agents cannot ask anyone, so their asks are refused. A workflow step can name the tools it should use, but today that is only text in its instructions: nothing enforces it. A mini app's tools are reachable only through one general "call an app" tool, which always asks you.

**Memory and gathering context.** You chose Hindsight. It fits, as the engine that *finds* memories. QMX keeps the memories themselves in its own Library, so Hindsight can be rebuilt or swapped later without losing anything. Today the assistant's memory is tied to a working folder, not to you or to what you are working on. The change is that memory follows the *subject* (a pod, a workflow, a mini app) and you. A chat started in the Lab and continued in the hub, or a new chat about the same pod, then remembers what was learned. A separate mechanism, "context references", lets you or the assistant pull in a pod, a workflow's output, a folder, a website or a YouTube video. Each one is saved once in the Library and handed to the model as a short excerpt plus a link, so the model reads more only when it needs to.

**What a clean design looks like.** There is one catalog of tools, and each tool is one function plus one row in that catalog. Tools come in named groups called toolsets ("Library", "Lab", "this mini app", "browser"). A chat, a workflow step or a helper gets the groups it needs, and a helper never gets more than its parent. Each model gets the right discovery method: Claude's built-in search where it works, otherwise a small QMX search tool. Every tool keeps its answers short, and a big result is saved and handed over as a link. When you publish a workflow, you approve the risky tools it may use, once. After that it runs without asking.

**The changes that matter most** (section 4):
- the one catalog with toolsets;
- one place that builds what each chat gets;
- a check on tool names before provider limits break them;
- a discovery path for non-Claude models;
- a QMX skill reader for skills stored in the Library;
- approval of risky tools at publish time;
- Hindsight as the memory engine, with memory that follows the subject;
- one way to pull context in from anywhere;
- a small test set for the assistant itself.

---

## 1. Suitability: what "an extension of him" means precisely

### 1.1 Definition

**The QMX harness is suitable when it extends the operator across his whole trading-research cycle.** It turns a rough input (a video, playlist, paper, post, chart or hunch) into falsifiable hypotheses, builds and runs the experiments (strategies, components, indicators, MIS variants, ML and neural models, units and pods) against his data and the backtester, and judges them honestly. Honest judging means out-of-sample, overfitting gates, a separate checker and negative results kept. It carries survivors to paper trading. It does every mechanical step unattended and spends his attention only where his judgment or his money is involved, showing results as rendered explainers rather than text.

### 1.2 The jobs (what he hires it for)

| # | Job | Example in his words | Who does it today / by design |
|---|---|---|---|
| J1 | **Capture and intake** | "run the WF1/WF2 idea over one video, a whole playlist or my Instagram saves" | engine templates with chunked fan-out (built: 31 templates, 9 tested) |
| J2 | **Understand and extract** | "some are very short, some just hint, some are podcasts, some are useless" | `understand-extract`, `paper-read` shared blocks (built) |
| J3 | **Ideate and frame** | the copilot helps him "consider different angles"; storyboard is "vibe coding for trading" | copilot (built harness); Lab copilot and builder (designed) |
| J4 | **Build** | indicators, components, MIS versions, neural nets, units, pods: "the sky is the limit" | Lab (designed, Lab and Pods spine), copilot with code tools |
| J5 | **Experiment** | backtests, sweeps, walk-forward, robustness, training | QMB door and Lab tool rows (designed), domain tools (built) |
| J6 | **Judge honestly** | WF2's core: "iterate against QMB until real results come out, without overfitting" | overfit gates (`_shared/overfit-gates/deflated_sharpe.py`, built), graders, evidence rule (designed) |
| J7 | **Remember and reuse** | "there are scenarios whereby we might be rebuilding something another workflow already built" | Library and memory (designed), "already built" check (designed) |
| J8 | **Promote and watch** | WF-style work "ends at paper trading"; Portfolio stays human-driven | pods to paper (designed); Portfolio (human) |
| J9 | **Explain** | "I don't want to read blocks of text"; animated explainers | output directives and explainers (designed) |
| J10 | **Make new tools of work** | create workflows, mini apps, skills and templates like a builder | copilot builder skill (placeholder), engine drafts and tests (built) |
| J11 | **Operate itself** | schedules, providers, machines, health; "nothing waits for him" | engine scheduler, inbox, doctor (built); pool, placements (designed) |

### 1.3 The users

| User | Attended? | What it needs from the harness |
|---|---|---|
| **The operator** | yes | Visuals, decisions framed with a recommendation, no re-asking settled things, final say on publish, enable and money |
| **The copilot** (one assistant with a home: hub, Lab, Portfolio; the hub can do everything) | yes | Every capability of the homes it combines, his approvals, long sessions that resume anywhere |
| **Workflow agents** (agent and `llm` steps) | no | A narrow, declared surface; no asks; durable state; evidence to stop on |
| **Helpers and sub-agents** (any provider) | inherits | A subset of the parent's surface, never more; a clean context; a bounded summary back |
| **Mini apps** (as callers) | no | QMX services through the app API (Library, model calls by role), never another app's internals |
| **Scripts** | no | The same operations the UI uses, no model in the loop |

### 1.4 What "robust" means for this suitability

1. **Honest.** No number shown unchecked. Negative results are kept as assets. Every claim carries its basis: retrieved, remembered or inferred. The probabilistic-thinking clipping recommends exactly these three labels.
2. **Unattended.** A run ends on its own. A provider limit pauses and resumes it without anyone asking. A crash loses nothing (durable ledger). A stuck run is detected.
3. **Recoverable.** Archive, never delete. Every change is a version. Replay is possible, and every writer gets its own worktree.
4. **Model-agnostic in practice, not only on paper.** The same workflow runs well on Kimi, DeepSeek, GLM, GPT or Claude. Features degrade by declared capability, never by surprise.
5. **Reproducible.** Data, definition and the tool surface an agent saw are pinned and recorded.
6. **Legible.** He and the copilot can see what happened, why, and on which model, through one trace shape.
7. **Bounded blast radius.** Agents have no path to money. Keys never appear in text. Broker click-through happens only on demo accounts.
8. **Evolvable.** A new tool, model, provider, memory store or loop pattern plugs in at a named seam, with no rewrite.
9. **Spends the right budget.** QMX sets no usage caps (rulings 27, 90, 106). The scarce resources it manages are **his attention** and **each model's context window**. Most design choices below trade on those two. [inferred]

---

## 2. The five disciplines

The clipping he gave (beamnxw, "Agent Harness Engineering vs. Loop Engineering vs. Graph Engineering", 2026-07-25, Obsidian `Clippings/`) [retrieved] frames three layers as **environment → feedback → flow**. The harness builds the machinery around the model, the loop designs the repeated work-and-feedback cycle, and the graph makes the topology explicit. "The graph runs inside the harness; one or more loops live inside the graph." Prompt and context engineering sit inside the harness, at the level of a single model call. The second clipping (Sumanth, "Loop vs Graph Engineering Clearly Explained") [retrieved] adds: "A loop is one node in a graph… start with one loop, push it until you find where it breaks." Both say pick the layer **by diagnosing the failure**. QMX's version of the clipping's diagnosis table:

| Symptom in QMX | Layer | Where QMX fixes it |
|---|---|---|
| A Kimi workflow agent picks the wrong QMX tool among 82 | context + harness | toolsets (§3.3) and discovery per lane |
| An `llm` step calls Bash although it said "use no tools" | harness | the tool list each chat gets is enforced, not written as text (§3.2 F4) |
| A strategy search stalls overnight | loop | plateau, then reframe the search space, then restart (§2.5) |
| A backtest number in an explainer is wrong | loop (evidence) | grader evidence rule (designed) |
| Ten intake steps must run in order with joins | graph | engine definition (built) |
| Copilot "forgets" mid-errand after compaction | context + harness | structured notes, memory snapshot, re-seed (§2.2) |

### 2.1 Prompt engineering

**State of the art.**
- Anthropic, *Building effective agents* (2024-12-19) [retrieved]: start simple. "Tool design deserves as much care as prompt design." Error-proof the arguments (poka-yoke): requiring absolute paths removed a whole class of errors.
- Anthropic, *Effective context engineering for AI agents* (2025-09-29) [retrieved]: prompt engineering became context engineering. System prompts should sit at "the right altitude", neither brittle if-else rules nor vague guidance. Start minimal and add instructions from **observed failures**. Use a few canonical examples instead of long edge-case lists.
- *Writing effective tools for agents* (2025-09-11) [retrieved]: tool descriptions are prompts and should be prompt-engineered. Tool use examples raised complex-parameter accuracy from 72% to 90% (*Advanced tool use*, 2025-11-24) [retrieved].
- Claude 4-era prompting guidance [remembered]: be explicit and give the reason. Use XML-tagged structure for meta prompts (B29's ask). Avoid shouting in capitals, which newer models over-apply. Ask for structured output.
- Probabilistic-thinking clipping (2026-09-14) [retrieved]: every answer is one draw from a set. Shrink the set with retrieved context, and ask for retrieved, remembered and inferred labels plus permission to say "I don't know".
- Hermes *prompt assembly* [retrieved via 37a §3 and mirror `developer-guide/prompt-assembly.md`]: three tiers (stable, context, volatile). Anything that changes mid-session rides the user message as a one-shot note. The rendered prompt and `tools[]` per surface are committed as CI snapshots.

**QMX today.**
- *Built:* `qma-harness/src/qma/harness/launch.py:403` `instructions()` appends `qmx-agents/plugin/QMX.md`, the workspace `CLAUDE.md` and `AGENTS.md` to the `claude_code` preset. That `append` is the only system-text seam for copilot and agent chats.
- *Built:* the engine's `qmx-engine/src/qmx_engine/prompts.py:43` `static()` builds the engine prompt in cache order: skills names, brief, rules, schema, then payload. Recalled text is fenced as quoted material.
- *Built:* each template carries its prompts as files (`templates/<id>/prompts/*.md`), so they are versioned with the workflow.
- *Designed:* a `persona` slot (engine AD-18), a Lab layer `prompts/lab-layer.md` (Lab LLD §7), and a prompt-surface snapshot test (37d H-116, adopted in engine AD-15).
- *Researched, never used:* the five-layer prompt design in `tracker/agent-system/research/31-tools-skills-prompts-comms.md` §3.2 (L0 base, L1 role, L2 plugin, L3 index and memory, L4 live state in the newest user message).
- *Deferred by ruling 82:* methodology, system prompts and persona content (B26-B29).

**Gaps.**
1. **No named slots.** The system text is one concatenation of three files. There is no home layer, pack layer or skills index, and no per-turn state channel.
2. **A hard size ceiling nobody has budgeted.** `append` rides the CLI command line. `launch.py` `ARGV_BUDGET = 30_000` characters covers settings, the MCP config, `append` and the deny rules together, and refuses the launch when exceeded [retrieved]. B29 layers plus a skills index plus a pack listing can hit this. [inferred]
3. **Prompts have no eval.** The snapshot test, when built, shows *what* changed but not whether it got *better* (see §2.5 gap 2).
4. **Tool descriptions are not treated as prompts.** QMX tool descriptions are the control-service docstrings passed through unchanged (`tools.py:300` `_from_fastmcp`). They have no examples and no "when not to use" line, and nothing lints them.

**Recommended design (seams only; the words come later with him).**
- One `PromptSurface` render step with **named slots**, filled in this order:
  1. the fixed preset;
  2. QMX rules;
  3. persona (operator-scope Library item);
  4. home methodology (Library `methodology` item per home);
  5. pack layers (one short fragment per enabled pack, plus its toolset listing);
  6. skills index (names and one line each);
  7. frozen memory snapshot.
  Per-turn state (`<qmx_state>`: open subject, layout, ticked runs, as Lab LLD §7 already plans) and one-shot change notes go in the **user message**, never the system text.
- Engine agents keep AD-34's order (preset → skills → memory snapshot → brief → payload) through the same render step with different slot fillers.
- A **size budget per slot**, with spill to progressive disclosure: a slot over budget becomes a skill or a Library reference the model can read on demand.
- Prompt items are **Library objects** (`persona`, `methodology`, skill), so they get versions, drafts on an agent ref, the curator and replay like everything else.
- The probabilistic-thinking contract is an **output-schema field**, not prose. QMX already built it as a block: `qmx-engine/src/qmx_engine/templates/_shared/calibrate/`.
  - Each claim carries `basis` and `evidence`.
  - `k` blind checkers vote `holds`, `does not hold` or `unclear` (`prompts/sample.md`).
  - `scripts/agreement.py` turns basis plus agreement into confidence: "a remembered claim or a split vote is never more than low", and a low item "cannot be a headline" [retrieved].

  The gap is reach, not design: the block is used by some templates, not by the copilot's answers or every research template (§4 DC-12).
- **Open versus settled questions** (the clipping's "every answer is a draw from a set"). When the copilot or an agent faces an open question (a judgment, a synthesis, a recommendation), it says so. Where the stakes justify it, it shows the spread instead of one confident draw: several blind samples, ideally from different model families through the router, and how far they agree. A settled or retrieved question gets one answer with its source. [inferred from the clipping]

**Future-proof seams.** Slots are data, so B29 fills them without code. The render step is the one place to change when the CLI gains a system-prompt file option (probe below) or when a second runtime arrives. The snapshot test is the interface test of this module.

**Probe.** Is there a supported way to pass long system text by file, such as an `--append-system-prompt-file` flag or a settings route? This would escape the 30,000-character command-line ceiling on Windows. [remembered that such a flag exists in recent CLIs; not verified against the pinned CLI]

### 2.2 Context engineering

**State of the art.**
- Anthropic, *Effective context engineering* [retrieved]: context is finite, and recall degrades as it grows ("context rot"). Each token draws on an "attention budget". Aim for "the smallest set of high-signal tokens". Prefer **just-in-time retrieval** (keep identifiers, load at runtime). Three long-horizon tools: **compaction** (tool-result clearing is its light form), **structured note-taking** outside the window, and **sub-agents** with clean windows returning condensed summaries. Tools should be a "minimal viable set".
- *Code execution with MCP* (2025-11-04) [retrieved]: present tools as code or files and load definitions on demand. Intermediate data stays in the execution environment, and only results come back. Example: 150,000 to 2,000 tokens.
- *Advanced tool use* (2025-11-24) [retrieved]: Tool Search with `defer_loading` cut about 77K to 8.7K tokens. MCP-eval accuracy went from 49% to 74% (Opus 4) and from 79.5% to 88.1% (Opus 4.5). Use it past about 10 tools or 10K tokens. Programmatic tool calling cut tokens 37%.
- Agent SDK *tool search* page [retrieved today]:
  - Selection accuracy "degrades with more than 30-50 tools loaded at once", and 50 tools can use 10-20K tokens.
  - The SDK **disables tool search when `ANTHROPIC_BASE_URL` is not first-party**, "since most proxies don't forward `tool_reference` blocks". `ENABLE_TOOL_SEARCH=true` forces it on, and requests then fail on proxies or hosts that do not support those blocks.
- Hermes tool search [retrieved via 37b §2]: a search, describe and call bridge for any provider, with a short listing of deferred tools. Without the listing, models used the wrong visible tool or said a capability did not exist.
- Manus, *Context engineering for AI agents* [remembered]: optimise for KV-cache hits, mask tools rather than remove them mid-session, use the file system as context, recite goals (a todo list), and keep errors in context.

**QMX today.**
- *Built and strong for workflows:*
  - chunked fan-out by tokens per model window;
  - per-chat `compact_at` and observe-only hooks (HG1; `launch.py` `ChatHooks`, `compact_env`);
  - a cache-ordered engine prompt;
  - fenced recall;
  - `inline_limit` spill to artifacts;
  - `TodoWrite` on (`launch.py:279` `CONSTANT_ENV`);
  - auto memory per workspace (`home.py` `memory_dir`);
  - domain tools with `response_format` concise or detailed and cursors (`qmx-tools/README.md`).
- *Designed:* the memory port with snapshot and recall (AD-18), the engine-built re-seed after compaction (AD-34), and the per-session pack set with `tools/list_changed` (AD-35, probe P-PK).
- *Measured fact* (`qma-harness/src/qma/harness/profiles.py` `HOST_QUIRKS` docstring) [retrieved]: with tool search on, OpenRouter answered **400 "Deferred custom tools are only supported on Anthropic models"** for Kimi K2.5 and DeepSeek. So tool search is off for OpenRouter and for the GPT lane (`GPT_QUIRKS`). It is forced on for direct key hosts (`KEY_QUIRKS`), noted in the same file as "not yet probed with a key; their `true` may hit the same 400".

**Gaps.**
1. **The tool surface is not budgeted.** Every chat gets all 82 `qmx` tools (64 control, 10 domain, 7 broker, `delegate`; counted from `tools.py` tables) plus vetted external servers (`chat.py:1063` `_tools`). On every lane without tool search (GPT, OpenRouter and probably his Chinese key providers), all of them load every turn. The design adds Lab (17 plus reads), Library, engine, browser and per-app rows, so the count heads past 150. That is well past the "30-50" point where selection degrades. [inferred from the counts and the retrieved threshold]
2. **Results are not capped.** Control operations return whole documents. `ToolDef` has no result cap and no spill (37b §1 gap 2).
3. **Copilot chats have no structured-note discipline of their own.** Hooks and `compact_at` are refused for Interactive chats (`launch.py` `chat_options_refusal`), so a long copilot errand relies on the CLI's own compaction.
4. **Adding a pack mid-session changes the tool list.** On eager lanes that breaks the prompt cache; Manus's "mask, don't remove" lesson applies. [inferred]

**Recommended design.**
- **Toolsets cut the surface first** (§3.3): a Lab session or an intake agent sees about 15-30 tools, not 150. This is subtraction, and it is cheaper than any search bridge.
- **Discovery by lane, chosen by a capability field in the model registry** (`tool_search: native | bridge | none`):
  - `native` uses the CLI's tool search with a small `alwaysLoad` core.
  - `bridge` uses QMX's own search, describe and call tools, scoped to the session's toolsets, with a listing of every toolset in the prompt slot. The real tool name is unwrapped before the money gate, grants and spans.
  - `none` loads eagerly, and stays within budget only because of toolsets.
- **Every tool returns context-efficient results:** concise by default, a cursor, and a result cap with an artifact spill (head, tail and Library id).
- **Copilot structured notes as a skill, not harness code.** For a multi-step errand, the copilot keeps an `errand.md` (goal, done, next, decisions, anchors) in its workspace and reads it after compaction or on resume. This is Anthropic's progress-file pattern, with no harness change. [inferred]
- **Pack changes land at turn boundaries.** On eager lanes the change is announced as a one-shot note and costs one cache miss; on `native` lanes the deferred tools do not touch the cached prefix [retrieved: deferred tools are not in the initial prompt, per *Advanced tool use*].

**Future-proof seams.** The `tool_search` capability is a model-registry field, so when Moonshot, GLM or DeepSeek ship `tool_reference` support, one data row changes. The result envelope and spill live in the catalog wrapper, not in each tool. Programmatic tool calling arrives as a `callers: code` field on catalog rows plus the `rlm` or `sandbox_python` stub (§3.4), with no change to tools.

**Probe.** Does each direct key host (Moonshot, Zhipu GLM, DeepSeek, MiniMax, Ollama Cloud) accept `tool_reference` blocks through the relay with `ENABLE_TOOL_SEARCH=true`? The answer sets each row's `tool_search` value. This is the same probe 37b §2 proposed; the OpenRouter result above makes it urgent.

### 2.3 Harness engineering

**State of the art.**
- LangChain, *The anatomy of an agent harness* (via the clipping) [retrieved from the clipping]: the agent is the model plus the harness. The harness covers context injection, action surfaces, persistence, execution control, safety and observability: "Remove the model from your architecture diagram. Everything left is probably part of the harness."
- Anthropic, *Effective harnesses for long-running agents* (2025-11-26) [retrieved]:
  - an initializer session creates `init.sh`, a progress file and a first commit;
  - each later session reads the progress and the git log, runs a basic end-to-end check, works one feature, commits and updates progress;
  - a JSON feature list that agents may only flip to passing ("unacceptable to remove or edit tests").
  - The fixes target over-reach, premature "done", undocumented partial work and unverified features.
- *Building agents with the Claude Agent SDK* [remembered]: the loop is gather context, take action, verify, repeat.
- Rivet's "run the harness outside the sandbox" principle (adopted in engine AD-25).
- OpenAI's harness-engineering write-up (early 2026) [remembered]: make the repository legible to agents, use AGENTS.md as a map rather than a manual, enforce architecture mechanically with lints, and run garbage-collection agents.
- Hermes [retrieved via 37a §1]: one agent core with many doors, written flow invariants, and "prompt stability" as a rule.

**QMX today.**
- *Built:* the QMA v2 harness (`qma-harness/src/qma/harness/`). It covers:
  - isolated Claude homes with settings in code and `setting_sources=[]`;
  - a SHA-locked single plugin;
  - strict MCP config and vetted external servers;
  - the money gate as the first PreToolUse hook;
  - per-argument approvals (`Grants`);
  - the relay as the only key reader;
  - blocking `delegate`, plus Child chats that cannot spawn;
  - a doctor;
  - usage metering.
- *Built:* the workflow engine as a second harness for unattended work. It is hexagonal and talks to the harness through `HarnessPort` (`qmx-engine/src/qmx_engine/ports/harness_adapter.py`), which has a fake provider as a second adapter, so it is a real seam.
- *Designed:* the router lanes, pool, model registry, `delegate` v2, permission floor and rules, desktop host and worktrees.

**Gaps.**
1. **Surface assembly lives in three places.**
   - `chat.py:1063` `_tools` decides the tool servers.
   - `launch.py:403` `instructions` and `:452` `build_options` decide the system text, built-ins and denies.
   - `nodes/agent.py:79` `rules()` writes the engine's tool list as text.

   Nothing produces "the whole surface this chat gets" as one value, so nothing can snapshot, diff, digest or test it. B-51 and B-70 (an `llm` chat still had Claude Code tools) are this class of bug.
2. **The copilot runtime has one adapter.** Everything QMX-owned (tool catalog, prompts, skills, memory) is projected only into the Claude Code CLI. That is right today: the plan sign-in and ruling 24 depend on it. But no second consumer forces QMX's own formats to stay CLI-independent. [inferred]
3. **Legibility for agents is thin.** `QMX.md` holds about 20 lines of money and settings rules, and the only skill (`qmx-overview`) is about refusals. No agent-facing map of QMX (homes, Library kinds, Lab, pods, workflows, where things live) exists. The OpenAI write-up's "AGENTS.md as a map" point applies.
4. **There is no progress-file discipline for long copilot errands** (see §2.2 gap 3).

**Recommended design.**
- **One `Surface` module, deep, at the harness seam** (§4 DC-7).
  - Input: chat kind, home, pack set, the node's or role's declaration, and the resolved model's capabilities.
  - Output: built-in tool list, `qmx` rows, external servers, sub-agent definitions, skills filter, system text by slot, hooks, env quirks, and a **surface digest**.
  - `chat.py` and the engine's agent node both call it. The digest goes on the session record and on every agent span, so "what did the model see" is answerable and replay is exact.
- **Keep QMX-owned data in QMX formats** and treat the CLI projection as an adapter. Formats: the catalog (JSON rows), skills (agentskills.io `SKILL.md` in the Library), prompts (Library items), memory rows and traces. A second runtime (the key-lane one-shot `Harness.complete`, a `cli` delegate target, a future Codex or OpenCode runtime) then only needs a new projection. This is also what makes ruling 3 (model-agnostic) hold in practice.
- **A QMX map skill.** The bundled plugin gains a short "where things are" skill that the copilot reads on demand: homes, Library kinds, the Lab, pods, workflows and how to find tools. It is content for B26-B28; this study fixes only that the slot exists.

**Future-proof seams.**
- `HarnessPort` is already a real seam: harness and fake.
- The `Surface` module becomes the seam where new SDK features land: per-agent `skills` and `mcpServers` on `AgentDefinition` [retrieved via `research/one-engine/02a-claude-agent-sdk.md` §5], `reloadSkills`, and `setMcpServers` (TypeScript only today) [same file §15].
- The router and model registry absorb new providers as data (AD-39).

### 2.4 Graph engineering

**State of the art.**
- The clipping [retrieved]: a graph engineer decides node boundaries (deterministic function, LLM call, specialist agent or human step), state schema, routing conditions, concurrency, cycles and exits, and durability.
- The same clipping warns against "building a graph before understanding the work": start from traces, then formalise the stable paths.
- Anthropic's five workflow patterns (prompt chaining, routing, parallelisation, orchestrator-workers, evaluator-optimizer) [retrieved].
- LangGraph and Temporal: durable execution with checkpoints and interrupts [remembered; confirmed in study 13 §3 per the engine spine].
- The Hermes clipping "Not every agent workflow needs AI" [retrieved]: script-only cron, a monitor before waking the agent, and `execute_code` to keep mechanical steps out of context.

**QMX today.**
- *Built* (`qmx-engine/`):
  - one definition format `qmx.workflow/1` (n8n-shaped, `definition/model.py`);
  - a closed node-kind registry with packs as `<pack>.<name>` on a `base_kind` (`definition/registry.py`);
  - edges `one | zip | broadcast | chunk | keyed-join | cartesian`;
  - join, loop, rule, wait, subworkflow, grader, monitor and doctor nodes;
  - memo and replay, an event ledger and spans, triggers, and pinned data for tests.
- *Designed:*
  - the Lab editor's graph mode;
  - "traces first" building (AD-22: start loose, tighten from the first test traces), which is exactly the clipping's advice;
  - `human_gate` only in front of an irreversible external effect;
  - script, mixed and fully agentic workflows on one engine (ruling 52).

**Gaps.**
1. **The core quant loop may not fit v1 nesting.** v1 refuses "a loop inside a loop body" and nested fan-out (AD-5). The Build Alpha clipping's revolution loop has an inner search loop (generate, backtest, validate) and an outer loop that detects a plateau, *changes the search space* and restarts. [retrieved clipping; inferred mapping] It can probably be expressed as an outer loop whose body calls a `subworkflow` holding the inner loop, but whether validation accepts that is not checked.
2. **Node-level tool and skill declarations are not part of the graph's state contract.** An `agent` node's `parameters.tools` and `parameters.skills` are free lists turned into prompt text (`nodes/agent.py:79`, `prompts.py:43`). The validator cannot check them against an existing toolset or skill.

**Recommended design.**
- Add `toolsets` (and `skills`) to the agent node contract as **checked references**. The validator refuses an unknown toolset or skill, and preflight refuses one whose pack is disabled or unhealthy (the engine's preflight already checks "skills and apps present", SOLUTION-DESIGN §280 [retrieved]).
- Ship the revolution loop as a template and prove it on the validator (§4 DC-11). If v1 refuses it, the answer is one sanctioned shape (a loop over a subworkflow), not general nesting.

**Future-proof seams.** These are already right: `typeVersion` per kind, pack types on base kinds, `extends` overlays, and `qmx.workflow/1` as a versioned schema. New patterns (a `goal` judge, the `rlm` kernel, `claude_workflow`) arrive as kinds or pack types, not engine edits.

### 2.5 Loop engineering

**State of the art.**
- The clipping [retrieved] lists the anatomy of a loop: **trigger, goal, state and memory, action policy, evidence, feedback, stopping rule**. "Do not loop on confidence. Loop on evidence." An unbounded "keep trying" loop is "a cost leak". The loop kinds are verification, event-driven and improvement loops, a "stack of loops" (LangChain, *The art of loop engineering*).
- RohOnChain's quant-loop clipping [retrieved] names six parts: automation, skill, state file, verifier (maker and checker on different models), worktrees and connectors. Lessons are written back into skills.
- Build Alpha, *The Loop Runs While You Sleep* [retrieved]: plateau detection, then changing *hyperparameters of the search*, then restarting. Every revolution is validated the same way (noise test, walk-forward, Monte Carlo permutation). Each session's reasoning goes to a memory store. "Negative results are the most undervalued asset." "The model proposes. The pipeline decides."
- Anthropic, *Demystifying evals for AI agents* (2026-01-09) [retrieved]: tasks, trials, transcripts and outcomes; code, model and human graders; capability versus regression suites; **pass^k for consistency**; "start early with about 20-50 tasks drawn from real failures".

**QMX today.**
- *Built:*
  - the loop node with typed stops (`max_iterations` required, `predicate`, `no_progress_rounds` on a metric; `core/loops.py`);
  - a deterministic grader;
  - a monitor (no-LLM wake gate, the Hermes pattern);
  - triggers (cron, interval, after, catch-up);
  - the failure ladder and doctor node;
  - test runs with pinned data;
  - overfit gates in the shared templates.
- *Designed:*
  - champion and challenger self-improvement with replay against fix and guard sets (AD-26);
  - copilot heartbeat, loop and goal with a completion contract (AD-47);
  - the stuck and no-convergence detector (AD-16, AD-40);
  - dead-end and negative-result memory tags (AD-18);
  - the "already built" check (AD-27);
  - a background review fork for copilot turns (AD-26).

**Gaps.**
1. **"Move the box" is not a first-class pattern.** `no_progress_rounds` *stops* a loop. The Build Alpha move is to *reframe* the search (signal pool, fitness function, regime filter) and continue. AD-26 edits workflow versions between runs, not the search space inside one run.
2. **No improvement loop for the assistant itself.** AD-26 gates workflow changes with replay. Nothing gates a change to the copilot's prompts, skills, tool descriptions or default model. B29 will change exactly those. The snapshot test shows the diff, not the quality.
3. **The maker and checker on different families is labelled, not required.** AD-13 allows a same-family judge with a `same_family` label. For J6 (judge honestly), the quant clipping and the Man Group warning argue for a different-family checker by default *for validation steps*. [inferred]

**Recommended design.**
- **Revolution-loop template** (§4 DC-11): the inner subworkflow runs generate, test and validation gates (deterministic), and writes negative results to memory. The outer loop's plateau rule routes to a **reframe** agent node that edits the search spec (never the gates; the AD-26 hard limits apply) and continues. Dead ends recalled at the start stop it from re-learning them.
- **Copilot eval battery** (§4 DC-10):
  - 20-50 tasks taken from his real sessions and from known failures (B-51, B-70 class), plus engine template tests;
  - graded by code where possible and by a family-separate judge otherwise;
  - run on haiku through the plan login (ruling 105) and on one key provider;
  - pass^3 reported.
  It gates B29 prompt changes, skill publishes and default-model changes. This is the "improvement loop" for the harness layer, and it reuses the engine (the battery is a workflow).
- **Validation steps default to a different family** for the judge role in shipped quant templates. He can switch it off per workflow.

**Future-proof seams.** Stop rules are typed and data-driven. Graders are a kind with modes. The judge is a role resolved by the router. The eval battery is a workflow, so new judges, models or tasks are rows, not code. A new loop idea (say, a future `/goal` variant) lands as an AD-47 session row or a grader mode.

### 2.6 Memory and context gathering (operator addition: he chose Hindsight)

**What he asked for.** Memory that makes workflows more robust, and gives the copilot memory across sessions and homes. Start a copilot session in the Lab, continue it in the hub. Concoct context from several places: a pod, a workflow's output inside a mini app, a folder, a website, a YouTube video, "the same way a Claude Code session gathers context from anywhere".

**Three things, kept apart** (domain language; mixing them is the usual mistake):

| Term | What it is | Owner |
|---|---|---|
| **Evidence** | What happened and what was learned, as durable objects: Library `memory-row`s, artifacts, transcripts, run traces | QMX Library (backed up, versioned, archive never delete) |
| **Recall engine** | An index that finds relevant evidence for a question and can summarise it | Hindsight (his choice), behind one QMX seam |
| **Context assembly** | What goes into one model's window right now: prompt slots, the memory snapshot, recalled excerpts, attached references | the `Surface` module (§2.3) plus context references (below) |

#### 2.6.1 State of the art

- **Anthropic** [retrieved, *Effective context engineering*]: structured note-taking outside the window, just-in-time loading by handle, and sub-agents returning condensed summaries. The Claude API also has a client-side memory tool (a directory the model reads and writes) [remembered].
- **Claude Code's own memory:** `CLAUDE.md` and auto memory in a directory. QMX points it per workspace (`qma-harness/src/qma/harness/home.py` `memory_dir`, "Auto memory lives in `<qmx_home>/agent-memory/<workspace>/`… shared by every provider", `DEPARTURES`) [retrieved].
- **Hermes** [retrieved 37b §13, study 28 §2]: memory providers are single-select plugins. Scope comes from the profile, mapped per provider (Hindsight uses `bank_id_template`). The context-references feature (`@file`, `@folder`, `@url`, `@diff`, `@git`) expands inline under "Attached Context", with a soft limit at 25% of context, a hard limit at 50%, and at most 200 folder entries (`research/sources/hermes-docs/user-guide-features/context-references.md`) [retrieved]. Study 37d row H-112 already maps it to QMX.

**Hindsight** (fetched 2026-10-18 from hindsight.vectorize.io and github.com/vectorize-io/hindsight) [retrieved]:

| Aspect | What it does |
|---|---|
| **Operations** | **retain** extracts typed facts, links entities, and consolidates in the background ("returns immediately while consolidation runs in the background"). **recall** runs semantic, keyword (BM25), graph and temporal search in parallel, fuses by rank, reranks with a cross-encoder, and packs results into a token budget (`max_tokens`, default 4096; `budget` low, mid or high for search depth; filters by `types` and `tags`; optional raw chunks). No generation step is described. **reflect** is an agentic loop over a bank that returns a cited answer. |
| **Memory model** | Isolated **banks**, each with a mission, directives and disposition. World and experience facts. Observations: consolidated beliefs with evidence; contradictions are reconciled at consolidation. **Mental models**: standing questions whose answers Hindsight keeps current. **Knowledge pages**: living documents built from observations, refreshed incrementally when consolidation adds knowledge. Pages never read other pages, which prevents citation loops. |
| **Retain modes** | `concise` (default), `verbose`, `custom`, `verbatim`, and `chunks` ("store chunks as-is with no LLM call"). |
| **Interfaces** | REST, Python, TypeScript and Go SDKs, a CLI (including `hindsight fs mount`, which projects pages to disk as markdown), and a built-in MCP server. Single-bank `/mcp/<bank-id>/` pins the bank. The multi-bank mode exposes 26-29 tools, including `delete_bank`, `clear_memories` and `update_bank`. A Claude Agent SDK integration pairs MCP tools (retain, recall, reflect) with hooks that "inject relevant memories automatically before every turn" and retain afterwards. A coding-agent plugin covers Claude Code. |
| **Deployment** | Cloud, Docker (full image about 9 GB with local embedder and reranker; slim about 500 MB using external ones), Helm, pip, or embedded in Python (`hindsight-all`). Postgres with pgvector; embedded pg0 for development. Windows x86_64 supported with embedded pg0. RAM: API full 1.5-2 GB, slim 0.5-1 GB, Postgres 0.5-1 GB+. |
| **Models** | 25+ providers through `HINDSIGHT_API_LLM_PROVIDER`, any OpenAI-compatible base URL, and `claude-code` and `openai-codex` subscription modes. |
| **License and claims** | MIT. Vendor-reported LongMemEval-S 94.6% and LoCoMo 92.0%; not independently checked here. |

Study 28 (2026-10-16) recorded [retrieved 28 §3]:
- one independent study found Hindsight "the most accurate but the most expensive to serve";
- retain 0.5-2 s per batch, recall 100-600 ms;
- mental-model reads are a database read with no model call.

#### 2.6.2 What QMX has today

- **Merged code.** Nothing integrates Hindsight: `git grep -i hindsight` over `packages/*/src` on `origin/engine/base` finds nothing [retrieved].
  - The engine has `MemoryPort` with eight verbs (`snapshot`, `recall`, `check_built`, `check_dead_end`, `note`, `consolidate`, `feedback`, `search_runs`) and a `MemoryStub`: an empty snapshot, nothing recalled, `note` storing a `run`-scope Library row, and `consolidate` a logged no-op (`qmx-engine/src/qmx_engine/ports/memory.py`) [retrieved]. `qmx_engine/memory/__init__.py` is a one-line docstring.
  - The copilot has only Claude Code's auto memory per workspace folder.
- **Designs.**
  - **Engine AD-18** [retrieved]:
    - evidence lives in Library `memory-row` objects, and a provider is "only a recall index rebuilt from those objects, never evidence";
    - scopes `run | workflow | home | operator`, one writer each; `note` is the only agent write;
    - `consolidate` at run end is the only path to wider scopes; recalled text arrives fenced, never as system text;
    - the built-in provider (Library rows plus SQLite FTS5) "ships first and is the default";
    - Hindsight is optional under binding rules: one bank per scope, `memory_mode: tools` (no auto-inject), `auto_retain: false`, retain only from `consolidate` with row ids as tags, `reflect` only inside `consolidate`, local embedded mode on Contabo.
  - AD-35: a session keeps one home and resumes on any surface; its home memory scope is `refs/memory/home/<kind>`.
  - AD-26: a background-review fork of a copilot session proposes memory rows and skill drafts.
  - AD-27: "already built" is a deterministic intent-key check.
  - Rerun 39: §5 C M-18 "built-in provider ships first; Hindsight is an optional adapter"; H-141 "Hindsight binding rules".
  - 37d: H-112 (context references) and H-31/H30 (attachments on turns stored as Library artifacts).
- **Rulings.** 49: pluggable memory; Hindsight was being looked at; avoid rebuilding what another workflow built; interacts with the Library. 79: "Memory providers (Hindsight for the copilot) also give self-improvement". Today's choice makes Hindsight the chosen engine, which **moves 39's "built-in is the default, Hindsight optional"**. The architect should record that as a ruling change, not a quiet edit.

#### 2.6.3 Gaps against his ask

1. **The copilot's memory follows the folder, not the subject.**
   - Auto memory is keyed by workspace.
   - A session resumed in the hub keeps its transcript, because the session id is the same (AD-35).
   - A *new* hub session about the same pod sees nothing the Lab session learned unless it was saved to the Library by hand.
2. **AD-18's binding rules make Hindsight passive.** With `auto_retain: false` and retain only via a workflow's `consolidate`, copilot conversations never reach it. That contradicts ruling 79 and today's ask.
3. **There is no copilot retain path that respects the harness.**
   - Hindsight's own Claude Code route (plugin, hooks, MCP) cannot be used as shipped: QMX loads one SHA-locked plugin, `setting_sources=[]`, strict MCP, and Interactive chats refuse per-chat hooks (`launch.py` `chat_options_refusal`) [retrieved].
   - Exposing Hindsight's multi-bank MCP server directly would also hand agents `delete_bank` and `clear_memories`.
4. **There is no automatic recall into Interactive turns.** The harness refuses `InjectedText` into an Interactive chat (`harness.py` `send`: "injected text goes only to a Background or Child chat") [retrieved]. So "inject memories before every turn" needs either the copilot calling a recall tool, or the UI attaching recall to his own turn.
5. **Context from many places has pieces but no single mechanism.**
   - Attachments (H30), `@` references (H-112), Library reads, `doc_read`, the YouTube intake templates and app artifacts all exist in design.
   - Nothing turns "this pod, that run's output, this folder, that video" into one pinned, cited, size-capped context package that the copilot, a workflow and a helper can all use.
6. **Who pays for and serves extraction.**
   - Hindsight's retain and reflect call a model.
   - A provider key in Hindsight's environment would bypass "the relay is the only key reader" (AD-28).
   - The `claude-code` and `openai-codex` subscription modes would run his plan logins outside QMX's homes (study 28 open question 9).

#### 2.6.4 Recommended design

**One seam, two adapters.**

```text
RecallEngine                                   # the seam; MemoryPort (engine) and the copilot `memory` toolset both call it
  retain(rows: [memory-row ids + text], tags) -> op_id     # rows are already Library objects
  recall(query, tags, budget_tokens, types?) -> [Hit(row_id, text, score, refs)]
  snapshot(questions: [standing-question ids], tags) -> text + row_ids   # mental models / knowledge pages
  reflect(question, tags) -> answer + cited row_ids        # optional capability
  rebuild(from_library: scope | all) -> op_id              # the swap and repair path
adapters: Hindsight (default, his choice) · built-in FTS5 over the same rows (offline PC, tests, fallback)
```

The FTS5 adapter is kept on purpose: two adapters make the seam real. `rebuild` makes moving to Mem0, ReMe or a future engine a re-index job, never a migration. Standing questions are data (Library items), so mental models can be re-created on another engine or emulated by a scheduled summary workflow.

**Banks by writer trust, tags by subject.** [inferred; a trade-off for the architect]

| Bank | Fed by | Typical tags |
|---|---|---|
| `qmx-operator` | his preferences and curated lessons; consolidate into `operator` scope, his "remember this" | `home:*`, `topic:*` |
| `qmx-copilot` | copilot session digests and background-review rows | `session:<id>`, `home:<kind>`, `item:<library id>` for every pod, unit, app, run or subject the session touched |
| `qmx-workflows` | engine `consolidate` at run end | `workflow:<id>`, `item:<id>`, `tag:dead_end`, `tag:built`, … |

Banks isolate what different writers may pollute; workflows may write "garbage or clean", per ruling 57. Tags make memory follow the subject: recall by `item:<pod id>` finds what the Lab session, the hub session and the nightly workflow learned about that pod. AD-18's per-workflow banks are the stricter alternative; they make ruling 49's "don't rebuild what another workflow built" a multi-bank query.

**Flows.**

1. **Copilot, at session start and after compaction (cache-stable).**
   - The `Surface` memory slot gets a frozen snapshot.
   - The snapshot is built from standing questions filtered by the session's home and attached items: his preferences, the subject's current state, known dead ends for the subject, and open threads.
   - Reading mental models is a database read [retrieved 28], so a session start costs no model call.
2. **Copilot, during the turn.**
   - The `memory` toolset offers `memory_recall(query, scope?)` and `memory_note(text)`. `memory_note` writes a Library row in the session's scope; the copilot never deletes.
   - Recalled text returns as a fenced tool result (AD-18 rule).
   - Automatic per-turn recall arrives later, by one of two routes. The UI can attach a recall block to *his* turn (no harness change). Or a harness grant can allow a QMX-composed prefix on Interactive turns.
3. **Copilot retain, QMX-side, with no CLI plugin or hooks.**
   - When a turn ends (and at idle, compaction or close), a retain worker reads the session's recorded blocks from the control store.
   - It writes a **session digest** as Library `memory-row`s: decisions, findings, preferences stated, items touched. AD-37 redaction runs first.
   - It retains them into `qmx-copilot` with tags.
   - The AD-26 background-review fork feeds the same path.
   - This replaces AD-18's `auto_retain: false` for the copilot path only. Workflows keep consolidate-only.
4. **Resume elsewhere.**
   - The same session id resumes with its transcript (AD-35) and shows a recap.
   - A *new* session on the same subject recalls through `item:` tags.
   - Lab to hub, or hub to a mini app, is the same mechanism.
5. **Workflows (AD-18, unchanged in shape).**
   - The run start snapshot comes from standing questions tagged `workflow:<id>` plus dead ends.
   - `check_built` stays **deterministic on the Library intent key** (AD-27). An exact "already built" must never depend on fuzzy recall. `check_dead_end` uses recall.
   - `note` writes `run`-scope Library rows. `consolidate` at run end retains into `qmx-workflows`. `feedback` keeps the `u/f` pruning.
6. **Sub-agents and helpers.**
   - Read-only `memory_recall` within the parent's scopes and tags, if their toolset includes it.
   - They never retain into `home` or `operator` (AD-18, AD-41).
   - They return findings to the parent, whose session digest carries them.

**Local versus remote.**
- Run Hindsight on **Contabo** (always-on, near the Hub and remote runs).
- The full image's local embedder and reranker need about 2-3 GB with Postgres on a 12 GB box that also targets 4-6 agent sessions (ruling 76). That trade-off is measured in the probe; the slim image offloads embeddings and reranking to external services at a cost.
- Remote workers reach memory **through the Hub's `MemoryPort`**, never with a raw Hindsight URL in a sandbox.
- When the PC is offline, the FTS5 adapter answers from the local Library rows. Hindsight catches up by `rebuild` or a retain backlog.
- An embedded pg0 Hindsight on the PC (supported on Windows) is possible but not recommended, given his disk and the remote runs. [inferred]

**Extraction model and keys.**
- Hindsight's retain and reflect use a `memory_extractor` role resolved by the router to a cheap key-lane model.
- Hindsight points at the relay's endpoint with a long-lived service pass (the AD-28 shape), never holding a provider key itself.
- Do not use its `claude-code` or `openai-codex` subscription modes.
- `chunks` retain mode (no model call) is the option for bulk workflow evidence where extraction is not worth paying for.

**What QMX still owns** (and Hindsight never does):
- evidence (Library rows, transcripts, artifacts), backups, archive-never-delete;
- scopes and the one-writer rule;
- deterministic `check_built`;
- redaction before anything leaves for Hindsight;
- which questions are standing questions (data);
- what enters a prompt and where (slots);
- the tool surface (QMX's `memory` toolset wraps the seam; Hindsight's own MCP server is never on an agent surface);
- the curator and `u/f` pruning.

**Context references: one grammar, used everywhere.**

```text
@pod:<id>  @unit:<id>  @run:<id>[/<output>]  @app:<id>/<provides-name>  @library:<query>
@file:<path>[:a-b]  @folder:<path>  @url:<https…>  @youtube:<video|playlist>  @session:<id>  @memory:<question>
```

- Each reference resolves through a toolset, so scope and availability apply: Library reads, `doc_read` or web fetch, the YouTube transcript block of the intake templates, app artifacts through `provides`, and recall.
- Each produces **a pinned Library artifact** (content-addressed, cited) plus a **handle**.
- The model gets a capped excerpt (Hermes limits: warn at 25% of the window, refuse inline at 50%, at most 200 folder entries) and reads more just in time.
- Heavy references (a playlist, a site) run as a workflow and attach when done. They never block the turn.
- The same grammar works in four places: in his composer (H-112, H30); for the copilot itself (`context_add(ref)`); in workflow `inputs`; and in a `delegate` task, so helpers receive references, not pasted text.
- Every resolved item adds an `item:` tag to the session, so the session digest and later recall follow the subject.

#### 2.6.5 Future-proof seams

- `RecallEngine` has two adapters and a rebuild path.
- Standing questions are data.
- The reference grammar is QMX's; resolvers are toolset rows; outputs are Library artifacts.
- When Claude Code, Hindsight or a newer engine adds native auto-memory, it can feed the same session-digest rows. QMX's evidence stays the source of truth.

**Probes.**
1. A small bake-off on *his* material, the B40 plan from study 28 trimmed: Hindsight (Contabo, concise mode, a Kimi or DeepSeek extractor through the router) against the FTS5 adapter. Task families: "already built", dead end, a Lab-to-hub follow-up, and "what did we decide about pod X". Record RAM on Contabo.
2. Retain latency and cost per copilot turn digest.
3. Whether Hindsight's Anthropic-provider mode works against the relay endpoint, or whether it needs the OpenAI-compatible chat lane.

---

## 3. Tools

### 3.1 How tools work today (merged code, `origin/engine/base`)

**Where a tool comes from.**
1. A QMX capability is a method on `ControlService` (`qmx-control/src/qmx_control/service.py`), a domain function (`qmx-tools/src/qmx_tools/functions.py`: data, backtest, research, node), or a broker read or proposal (`qmx-broker/src/qmx_broker/service.py`).
2. `qmx-control/src/qmx_control/server.py:28` `OPERATIONS` is **one tuple per operation**: name, HTTP method, path, destructive. It wires **both doors** from the same row: REST for the UI and a FastMCP server (`create_mcp`) with `readOnlyHint` and `destructiveHint`. "There is no second implementation to drift." This is a good seam: the UI and agents call the same operation.
3. `qma-harness/src/qma/harness/tools.py` decides what reaches an agent.
   - `AGENT_OPERATIONS` (64 rows), `DOMAIN_EFFECTS` (10) and `BROKER_EFFECTS` (7) are explicit allow-lists. Each tool carries an `Effect`: `READ | DOMAIN_WRITE | MANAGE | PROPOSE_MONEY`, a closed enum with no money-moving member (`:56`).
   - Left-out rows are listed with a reason (`OPERATIONS_LEFT_OUT`, `DOMAIN_LEFT_OUT`).
   - `tool_defs()` (`:342`) reads the live FastMCP servers in process and wraps each tool as a `ToolDef`. A table row with no tool behind it raises.
   - `delegate_def()` (`:388`) adds `delegate(profile, prompt)`, a blocking helper chat on another provider.
4. `build_server()` (`:426`) refuses duplicate names and any money surface, wraps every **asking** tool so it first consumes a `Grant` for its exact argument digest, and calls `create_sdk_mcp_server("qmx")`. The model sees `mcp__qmx__<name>`. In-process means the CLI never holds the control token.

**What each chat gets.**

5. `qma-harness/src/qma/harness/chat.py:1063` `_tools()` builds this per launch. It is the **same set for every chat kind**: Interactive copilot, Background engine agent, and Child helper (Child minus `delegate`). Only `tools=False` (the plan meter's turn) gets none.
   - External MCP servers from `settings.toml [mcp_servers]` are vetted first: started, listed, money-checked and cached by config digest (`tools.py:737` `vet_mcp_servers`).
   - After connect, a tool the CLI loaded that vetting never saw refuses the launch.
6. `launch.py:452` `build_options()` sets:
   - built-ins = the `claude_code` preset (Bash, Read, Edit, Write, WebFetch and the rest; PowerShell turned back on for Windows);
   - `mcp_servers` = `qmx` plus the vetted servers, `strict_mcp_config=True`;
   - `plugins` = the one SHA-locked `qmx-agents/plugin/` (`home.py:70-73`);
   - `disallowed_tools` = `Agent` and `Task` for Child chats, plus the money deny rules;
   - the money gate as the first PreToolUse hook;
   - `can_use_tool` for asks.
7. Tool search per lane (`profiles.py`): the plan uses the CLI default (on); key hosts are forced `true`; GPT and OpenRouter are `false`. OpenRouter returned 400 for deferred tools on non-Anthropic models (§2.2).

**Who approves what.**

8. READ never asks. DOMAIN_WRITE follows `settings.toml [agents] domain_write` (default `allow`). MANAGE and PROPOSE_MONEY always ask, and an approval is one-shot for those exact arguments.
9. Engine agent chats are Background chats. The engine rejects every ask at once with "unattended run" (`qmx-engine/src/qmx_engine/ports/harness_adapter.py:45, :237`). **So an engine agent can never use a MANAGE tool.**

**Engine agent steps.**

10. `qmx-engine/src/qmx_engine/nodes/agent.py:79` `rules()` turns the node's `parameters.tools` into the sentence "Use only these tools: …". `prompts.py:43` turns `parameters.skills` into "Skills to apply: …". **Neither is enforced or loaded:** the chat has the full surface, and only the plugin's own skill files exist on disk. Harness request H2 (re-asked in HG3) would pass a real built-in list.

**Mini apps.**

11. Each app is its own stdio MCP server, supervised by `qmx-apps` (`qmx-apps/README.md`). Agents reach an app only through `mcp__qmx__apps_call(app_id, tool, arguments)` (`service.py:771`).
    - That tool is MANAGE, so the copilot asks him on every call and engine agents cannot call it at all.
    - The `app_op` node kind is registered but unavailable (`definition/registry.py`).
    - `apps_archive` is a stub (`service.py:1017`; alignment A-20).

**Skills.**

12. The bundled plugin ships one skill, `qmx-overview` (`qmx-agents/plugin/skills/`). Project skills are off (`home.py:669` `DEPARTURES`). The Library `skill` kind and "the skill tool" (AD-19, AD-35) are designed, but no QMX skill tool exists.

**Leftovers.**

13. `qmx-tools/src/qmx_tools/registry.py` still wraps the domain functions as **LangChain** tools ("Wrap the domain functions as LangChain tools"), although LangGraph is gone (ruling 2). The old `qma-core` plugin, operations and effect packages are on the deletion plan.

**Two effect vocabularies.** The harness `Effect` answers *who must approve*. The engine node `effect` (`none | reversible | compensable | irreversible | irreversible_external`, `definition/registry.py`) answers *can it be undone*. AD-4 says an unattended ask is rejected "except a tool call the registry marks `irreversible_external`". **No tool registry carries that field today**, so AD-4's exception has nothing to read. [inferred from both files]

### 3.2 Findings, numbered

- **F1.** One concept, three tables: a tool's REST and MCP row, its agent row, and its engine reversibility live apart. Adding a QMX tool touches `service.py` + `server.py OPERATIONS` + `tools.py` tables, and still has no toolset, result cap, availability check or reversibility.
- **F2.** No scoping: every chat gets everything. Sub-agents and helpers do not get narrower surfaces except that `delegate`, `Agent` and `Task` are removed.
- **F3.** 82 tools load eagerly on every non-tool-search lane, which covers his main providers (§2.2).
- **F4.** Engine node tool and skill lists are prompt text only.
- **F5.** Mini-app tools sit behind a single always-asking dispatcher. Engine agents cannot reach them, and ruling 10 ("reach an app without custom wiring") is unmet in code.
- **F6.** Unattended agents have no route to MANAGE tools, even ones he would approve once at publish.
- **F7.** No skill reader for Library skills.
- **F8.** Naming is mixed across the designs: `lab_*` and `pod_*` (Lab LLD), `qmb.backtest` (Lab UI tools), `app.<id>.<tool>` (AD-19), `qmx-data.read_bars` (qmx-tools README). The Anthropic and OpenAI tool-name pattern is `^[a-zA-Z0-9_-]{1,64}$` [remembered], so dotted names and long `mcp__qmx__app_<id>_<tool>` names can be refused by the provider. `qmx-tools/README.md` already notes "callable tool names use underscores for model-provider compatibility" [retrieved].
- **F9.** "Plugin" means two things: the Claude packaging format (the QMX plugin, the mini-app layout) and the Lab "plugin" that is really tool rows (alignment A-39). "Pack" means a mini app (AD-19), a capability layer such as `cua` or `qmx-lab` (engine `packs`), and a session's set (AD-35).

### 3.3 How Hermes does tools (what to borrow)

From 37b §1-2, §6, §8 and the mirror `research/sources/hermes-docs/reference/toolsets-reference.md` and `developer-guide/tools-runtime.md` [retrieved]:

- **Registry entry:** name, **toolset** (exactly one), schema, handler, `check_fn` (availability; an exception means hidden; cached), `requires_env`, `max_result_size_chars`, `execution_timeout`. Shadowing a tool from another toolset is refused without `override`. Handlers never raise; errors return as JSON.
- **Toolsets:**
  - *core* (one logical group, such as `file` or `web`);
  - *composite* (`debugging` = file + terminal + web);
  - *platform* presets (`hermes-cli`, `hermes-cron`, `hermes-webhook` = a restricted safe subset);
  - *dynamic*: `mcp-<server>` per MCP server, plugin toolsets and custom toolsets in config.

  Resolution: enabled list, or all minus disabled, then `check_fn` filtering. Some toolsets stay off even under `all` because they mutate shared state (kanban).
- **Sub-agents inherit the parent's toolsets; the model cannot widen them per call.** `delegate_task` is blocked for leaf children, and an orchestrator depth setting governs deeper trees (`user-guide-features/delegation.md` "Inherited Tool Access").
- **Tool search:** a search, describe and call bridge for any provider, a tiered listing, a catalog scoped to the session's toolsets, the real name unwrapped before hooks and approvals, and arguments validated against the real schema.
- **Skills:** progressive disclosure (`skills_list`, `skill_view`, then a reference file), conditional activation (`requires_tools`, `fallback_for_tools`) and a curator.
- **Plugins:** declared `provides_tools` must equal what is registered (checked by a doctor); consent is asked again for a capability delta on update.

### 3.4 Target design

**Domain language (one word per concept).**

| Term | Meaning | Not to be confused with |
|---|---|---|
| **Tool** | One callable a model can use, with one catalog row | an operation (the service method behind it) |
| **Toolset** | A named group of tools; **the unit of scoping** | a pack (what installs it) |
| **Pack** | An installable unit (mini app, Lab, browser, `cua`) that contributes toolsets, skills, workflows and widgets | a plugin |
| **Plugin** | Only the Claude Code packaging *format* a pack may be laid out in | a pack or toolset |
| **Surface** | Everything one chat or agent gets: toolsets resolved to tools, built-ins, servers, sub-agent definitions, skills filter, system text, hooks | a session's pack set (one input to it) |
| **Approval class** | Today's `Effect`: read, research write, manage, money proposal | reversibility |
| **Reversibility** | The engine's effect axis: none to irreversible external | approval class |
| **Grant** | Permission to run an asking tool: per call (today) or **standing**, given at publish (new) | a run pass (credentials) |

**The core data structure: one catalog row per tool.** Data structures first: every later behaviour reads this row.

```text
ToolSpec
  id              "library.search" | "lab.backtest" | "app.fx-calendar.next_events"   # catalog id, dotted
  wire_name       "library_search" | "lab_backtest" | "app_fxcal__next_events"        # ^[a-zA-Z0-9_-]+$, len(mcp__qmx__ + wire) <= 64, checked at registration
  toolset         "library" | "lab" | "app:fx-calendar" | "mcp:<server>" | "run:<run_id>"  # exactly one
  binds           control_op | domain_fn | broker | app_server_tool | agent_tool | delegate
  approval        READ | DOMAIN_WRITE | MANAGE | PROPOSE_MONEY        # today's Effect, unchanged
  reversibility   none | reversible | compensable | irreversible | irreversible_external
  description     prompt-engineered; first line = when to use; one "not for" line
  input_schema    strict JSON Schema
  examples        0-5 input examples
  result          {formats: [concise, detailed], cursor: bool, max_chars, spill: artifact}
  available       cheap check, cached per chat start (backend down, key missing, pack disabled)
  defer           auto | always_load
  callers         [model] | [model, code]           # code = callable from sandbox_python / rlm stubs; never for MANAGE or money
  contract        semver of the schema + result shape
  owner           core | pack:<id> | app:<id>@<version> | run:<run_id>
```

**Access patterns this row serves.** Trace them before building:
- (a) build a chat's surface;
- (b) gate a call (approval, reversibility, money, standing grant);
- (c) list and search for a model or the UI;
- (d) count usage for the curator and app cards;
- (e) diff two versions for consent;
- (f) record what an agent saw (surface digest).

One table answers all six. The three tables of F1 answer only (b).

**Toolsets, and how scope is resolved (one function).**

```text
surface(chat) =
    resolve(toolsets_of(chat))          # home preset ∪ pack set (copilot) | node.toolsets (engine) | role preset (helper)
  ∩ available()                          # check fns
  ∩ parent_surface                       # Child, delegate and native sub-agents: never wider than the parent
  − denied(chat_kind)                    # delegate/Agent/Task for leaves; money deny rules
```

- **Core toolsets** (proposal): `library`, `workflows` (drafts, tests, runs, triggers, inbox), `jobs` (remote runs and jobs), `data`, `backtest`, `research`, `node`, `broker_read`, `lab`, `pods`, `apps_admin`, `memory`, `skills`, `browser`, `delegate`, `settings_read`.
- **Dynamic toolsets:** `app:<id>` per enabled mini app, `mcp:<server>` per vetted external server, and `run:<run_id>` for a run's agent-made and sandbox tools.
- **Presets:** the hub loads every enabled toolset. The Lab and Portfolio homes have their own presets (data, editable in Settings, the Lego rule). Engine roles get presets too, such as `intake` = library + research + data + memory.
- **Enforcement in two places:**
  1. the `qmx` server is built **per chat from `surface(chat)`**. `chat._tools` already builds one server per chat, so this is a filter before `build_server`.
  2. the PreToolUse gate refuses any `qmx` tool outside the surface, in case a stale list reaches the CLI.

  Built-ins come from H2's `tools` list per node or role. Native sub-agents get `AgentDefinition.tools` and `mcpServers` generated from their role's toolsets (H38's generator) [SDK fields retrieved via 02a §5].

**Discovery (how a model finds tools).** The ladder is chosen per resolved model by registry data:
1. **Always:** a small eager core (`always_load`): the "find" tools, `memory`, `skills`, and the home's top few. Also a **toolset listing** in the pack-layer prompt slot (name plus one line per toolset), so the model knows what exists even when schemas are deferred. That is Hermes's measured lesson.
2. **`tool_search: native`:** the CLI's tool search defers everything else. QMX sets `alwaysLoad` on the core [SDK fact retrieved; `alwaysLoad` is "not declared on the Python TypedDicts", 02a §7, so this may need the raw config dict].
3. **`tool_search: bridge`** (built only if the probe fails *and* a real surface exceeds about 30 tools on that lane): `qmx_tool_search(query)`, `qmx_tool_describe(names)` and `qmx_tool_call(name, arguments)`.
   - Search is BM25 over id, description and parameter names, scoped to the surface.
   - The real name is unwrapped before grants, the money gate and spans.
   - Arguments are validated against the real schema.
4. **`none`:** eager. Toolsets keep it within budget.

**How a tool is added** (one path per kind):

| Kind | Steps | Checked by |
|---|---|---|
| Core QMX tool | 1 service method + 1 catalog row (the REST route, MCP tool and agent row all derive from it) | catalog doctor: declared = served, wire name valid, description lint, schema strict; prompt-surface snapshot diff in CI |
| Mini-app tool | the app's MCP server serves it; `app.toml [provides] tools` declares id, approval, reversibility and toolset; on enable it joins `app:<id>`, proxied through `qmx` as its own row | `qmx app check` (designed): declared = served, envelope contract tests |
| External MCP server | his row in Settings; vetted (as today); joins `mcp:<server>`; every tool defaults to `MANAGE` unless he marks it read-only (Hermes `trust: untrusted`) | vetting plus the money surface check (built) |
| Agent-made tool | saved as a Library `agent-tool`, `unreviewed`, in `run:<run_id>` only, running in that run's zone or sandbox | his publish moves it into a pack's toolset |
| Workflow as a tool (later) | a published workflow with an input schema may be exposed as a typed tool in its pack's toolset; the generic `workflows_run` stays | the publish card |

Before any of these, the builder skill applies Hermes's first question [retrieved 37b §1]: **skill or tool?** If the job is instructions plus existing tools, write a skill. Write a tool only for new data access, binary data, secrets or exact logic.

**Versioning.**
- Each row has a `contract` semver. Adding an optional field is a minor change. A removed field or a changed meaning is a new wire name or a major bump, and the old one is kept until no published workflow or skill references it (Library edges tell). Hermes's compatibility rule [retrieved 37b §6.6] is additive, keyword-only, with a two-version deprecation.
- Pack versions are Library objects. A new version's **added** tools, hosts or approval classes are shown as a delta at publish (AD-19).
- The **surface digest** (sorted wire names + schema hashes + system-text hash) is recorded on the session and on every agent span. A replay or an AD-26 challenger run states which surface it used. [inferred]

**How each consumer uses tools.**
- **Copilot.** Its home preset plus the pack set (AD-35) gives its toolsets. Asks reach him. Adding a pack lands at the next turn, with one note. The hub holds every enabled toolset; on lanes without search it relies on the listing plus the bridge when needed.
- **Workflow agents.** The node declares `toolsets` (checked at validation and preflight) and built-ins (H2). Asks are rejected, *except* tools covered by a **standing grant**: the publish card of a workflow or app version lists the MANAGE tools its declared toolsets contain, and his publish click grants those, for runs of that version only (§4 DC-6). That is ruling 80 (human-driven creation) followed by ruling 57 (nothing waits for him). `irreversible_external` tools keep AD-4's inbox route.
- **Helpers and sub-agents.** Surface ⊆ parent, chosen by role preset. The model can never widen it (Hermes rule, AD-41).
- **Mini apps.** Their tools are rows in the catalog. Their own code calls QMX through the app API (Library, `llm_complete`), not through agent tools. Apps reach other apps only through `app_op` or events (AD-19).
- **Scripts.** No model, so no tools. They call the same operation table through a client, the "same API as the UI" seam already in `server.py`.
- **Code mode, later.** Rows with `callers: [model, code]` appear as Python functions inside `sandbox_python` or the `rlm` kernel, so a data-heavy agent loops in code and only results reach context (*Code execution with MCP*, *Advanced tool use* PTC). Never for MANAGE or money rows.

**Skills (the companion to tools).**
- Library skills are read through two `skills` toolset rows: `skill_list` (filtered by the surface: a skill whose `requires_tools` or `requires_apps` are missing is hidden) and `skill_view(name, path?)` (progressive disclosure).
- Loads are counted for the curator (AD-46).
- The SHA-locked plugin keeps only bundled core skills.

This closes the "skill tool" that AD-19 and AD-35 assume exists. It works on every provider because it is an ordinary tool. The alternative, generating a per-session plugin folder for the native Skill tool, conflicts with the plugin lock and gives no usage counts; it stays a probe option only.

### 3.5 Migration (subtract first, then build)

| Step | What | Size | Harness grant? |
|---|---|---|---|
| M0 subtract | Remove the LangChain wrapper in `qmx-tools/src/qmx_tools/registry.py` once `git grep` shows no caller; leave `qma-core` plugin and effect packages to the deletion plan; align "plugin" to mean the packaging format only in the Lab spine's wording (architect) | small | no |
| M1 one catalog | Fold `OPERATIONS` (server), `AGENT_OPERATIONS`, `DOMAIN_EFFECTS` and `BROKER_EFFECTS` into one `ToolSpec` table with toolset, reversibility, result and availability fields. `Effect` is unchanged; `tool_defs` and `build_server` read the table | medium | yes (`tools.py` shape; the money surface check unchanged) |
| M2 toolsets and per-chat surface | `surface(chat)` in a `Surface` module; `_tools` filters by it; the gate refuses out-of-surface calls; `HarnessPort.start_chat(toolsets=…)`; the node schema gains `toolsets`; templates declare them; `rules()` stops writing tool lists as text | medium | yes (overlaps H2 and H32) |
| M3 app rows | Enabled apps' tools become `app:<id>` rows with valid wire names; `apps_call` stays for the UI and REST and leaves the agent surface | medium | yes (H32) |
| M4 checks | Catalog doctor; prompt-surface snapshot per chat and node kind (H-116); surface digest on sessions and spans | small | yes (CI plus one field) |
| M5 discovery | Probe `tool_reference` per key host; set registry `tool_search`; build the bridge only if a lane fails *and* a measured surface exceeds about 30 tools | small, or medium if the bridge is built | yes, if the bridge is built |
| M6 skills rows | `skill_list` and `skill_view` over Library skills with conditional activation and usage counts | small | yes (rows) |
| M7 standing grants | Publish card lists the MANAGE tools in the version's toolsets; `Grants` accepts a standing grant keyed to (version, tool) | medium | yes (`Grants`) and his ruling |

---

## 4. Design changes for the architect

Each change has its blast radius, the scenario it serves, and whether a probe gates it. Ordered by value.

| # | Change | Blast radius | Scenario it serves | Probe? |
|---|---|---|---|---|
| **DC-1** | **One tool catalog (`ToolSpec`)** replacing the three tables, with toolset, reversibility, result rules, availability, `callers` and contract version; REST, MCP and agent rows derive from it | `qmx_control/server.py`, `qma/harness/tools.py` table shape, engine AD-4 ask policy (now has a field to read), Lab and Library LLD tool tables re-expressed as rows | Adding a Lab tool is one method plus one row; AD-4's `irreversible_external` exception becomes implementable | no |
| **DC-2** | **Toolsets as the unit of scope**; session pack set = toolsets; `surface()` per chat; children never wider; engine nodes declare `toolsets` (checked at validate and preflight) | `chat.py _tools`, `HarnessPort.start_chat`, `qmx.workflow/1` node parameters, 31 templates, AD-35 and AD-41 wording | An overnight playlist intake on Kimi sees about 15 tools, not 82+; a helper cannot use tools its parent lacked | uses P-PK (already planned) |
| **DC-3** | **Wire-name rule:** catalog ids may be dotted; wire names match `^[a-zA-Z0-9_-]+$` with `mcp__qmx__` + name ≤ 64; linted at registration | AD-19 `app.<id>.<tool>`, Lab `qmb.*` names, app check | A mini-app tool name the Anthropic or OpenAI API would refuse never ships | **yes**: what the pinned CLI does with a dotted or over-64 MCP tool name |
| **DC-4** | **Discovery per lane from registry data** (`tool_search: native, bridge or none`), an always-on toolset listing, an `alwaysLoad` core, and the QMX bridge only where needed | `profiles.py` quirks become registry rows (AD-39), harness gate unwrap if the bridge is built | His daily copilot on a Chinese model with a dozen apps enabled still picks the right tool | **yes**: `tool_reference` on Moonshot, GLM, DeepSeek, MiniMax and Ollama Cloud through the relay |
| **DC-5** | **QMX skill rows** (`skill_list` and `skill_view` over Library skills, conditional activation, usage counts); the plugin keeps only bundled skills | harness rows, Library skill kind schema (`requires_tools`, `requires_apps`), AD-19 and AD-35 ("the skill tool") | A "macro analysis for EURUSD" skill he made with the copilot is used by a DeepSeek workflow agent the same night | optional: per-session plugin folder versus rows |
| **DC-6** | **Standing tool grants at publish:** a version's publish card lists the MANAGE tools its toolsets contain; his click grants them for that version's unattended runs only | `Grants`, engine `service.versions.publish`, UI publish card, AD-22 and AD-43 wording | A health workflow restarts an unhealthy mini app at 3 a.m. without waiting for him | no (**needs his ruling**: it extends his publish click to tool approval) |
| **DC-7** | **One `Surface` module** that produces the whole surface (tools, built-ins, servers, sub-agent definitions, skills filter, system text by slot, hooks, quirks) plus a digest; the copilot and engine both use it; snapshot-tested | `launch.py`, `chat.py`, `nodes/agent.py`, `prompts.py` | B-51 and B-70-class bugs caught in CI; "what did the agent see" answerable for any span; B29 plugs into slots | no |
| **DC-8** | **Prompt slots and budgets for B29:** persona, home methodology, pack layers and toolset listing, skills index, memory snapshot in the system text; per-turn state and one-shot change notes in the user message; per-slot size budget under the 30,000-character command-line ceiling | `Surface` render, Library `persona` and `methodology` kinds | B29's prompts drop in as data; a large methodology does not break launches on Windows | **yes**: a file route for long system text on the pinned CLI |
| **DC-9** | **Result discipline on every row:** concise by default, cursor, `max_chars` with artifact spill (head, tail, id), actionable error envelope | catalog wrapper, control service list endpoints, `qmx app check` | `workflow_runs_explain` on a 400-chunk run does not flood the copilot's window | no |
| **DC-10** | **Copilot eval battery:** 20-50 tasks from his real sessions and known failures, graded by code or a family-separate judge, run on haiku plus one key provider, pass^3 reported; gates prompt, skill and default-model changes | a new test workflow and fixtures; no product code | Switching his daily model or editing the Lab methodology is measured before he relies on it | no |
| **DC-11** | **Revolution-loop template:** inner subworkflow (generate, test, deterministic validation gates, negative results to memory), outer loop with plateau routing to a reframe agent that edits only the search spec | templates; possibly the v1 nesting rule if the validator refuses loop-over-subworkflow | Overnight strategy discovery that changes the search space when stuck and never relearns a dead end | **yes**: does validation accept a loop whose body is a subworkflow containing a loop |
| **DC-12** | **Calibration as a contract, not a block.** The built `_shared/calibrate` rule (basis, blind votes, then high, medium or low; a remembered claim never above low) becomes the default for every research template's headline claims and for copilot explainers (a confidence chip per claim). Open questions get a shown spread (k blind samples, family-separate where configured) instead of one draw | template schemas, `render-and-grade`, the copilot output-directive skill, judge role resolution | His explainers show what was checked, what was guessed and where models disagree | no |
| **DC-14** | **Hindsight as the default recall engine behind one `RecallEngine` seam** shared by `MemoryPort` and a copilot `memory` toolset. The FTS5 adapter is kept for offline, tests and fallback. Banks by writer trust (`qmx-operator`, `qmx-copilot`, `qmx-workflows`), tags by subject (`item:`, `home:`, `workflow:`, `session:`). The copilot retains QMX-side from session digests (no Hindsight plugin, hooks or raw MCP server on any surface). Standing questions (mental models) feed the memory slot. Hosted on Contabo. Extraction through the router via a `memory_extractor` role; `check_built` stays deterministic | engine AD-18 binding rules (copilot path gets auto-retain), 39 §5 C M-18 and H-141 (default moves: his choice), Library `memory-row` tags, harness rows for the `memory` toolset, Contabo capacity (AD-30), the memory packet in the next plan | A Lab session's findings about a pod are recalled by a new hub session and by that night's workflow; a workflow never re-learns a dead end | **yes**: bake-off on his material, Contabo RAM, extractor through the relay (§2.6.5); **and his ruling** recorded (Hindsight default) |
| **DC-15** | **Context references:** one `@` grammar (pod, unit, run output, app output, Library, file, folder, URL, YouTube, session, memory) resolved by toolset rows into pinned Library artifacts plus capped excerpts; the same grammar in the composer, the copilot (`context_add`), workflow inputs and `delegate` tasks; each reference tags the session with its subject | UI composer (37d H-112, H30), control turn route, Library artifacts, intake templates for YouTube and web, the `Surface` excerpt budget | "Take this pod, last night's run inside the watcher app, this folder and that video, and tell me what to try next" in one turn, with sources | no |
| **DC-13** | **Subtractions:** LangChain wrapper; prompt-text tool lists (after DC-2); `apps_call` off the agent surface (after M3); one meaning each for "plugin" and "pack" in the specs | small, spread | Less to read, fewer ways to drift | no |

**What not to do now** (subtract before you add):
- No JS or TS code-mode sandbox. The `callers` field reserves the seam.
- No general nested fan-out until a template needs it beyond DC-11.
- No MCP export of QMX's tools to outside agents. Programmatic integration is out (ruling 93 clarification); the catalog makes it a later adapter if he asks.
- No second copilot runtime. Keeping data in QMX formats (§2.3) is enough option value.

---

## 5. Future-proof seams, in one table

| What will change outside QMX | Seam that absorbs it | Real seam (two adapters) today? |
|---|---|---|
| New providers and models; longer windows; native tool search on more vendors | model registry rows (AD-39): `tool_search`, window, cache kind, capabilities | yes (plan, key, GPT lanes) |
| New agent runtimes (Codex app-server, OpenCode, Kimi Code) | `delegate` `cli` targets (AD-41); `HarnessPort` | `HarnessPort`: yes (harness and fake); `cli`: designed |
| New SDK features (per-agent skills and MCP, reloads, `setMcpServers`) | `Surface` module (DC-7) | not yet: one module to create |
| Programmatic tool calling and code mode | `ToolSpec.callers` plus the `rlm` or `sandbox_python` stub | reserved |
| MCP spec growth (long-running tasks, elicitation, MCP Apps UI) | catalog `result` and job handles; directive registry (AD-45) for UI | partial |
| Memory products (Hindsight now; Mem0, ReMe or newer later) | `RecallEngine` behind `MemoryPort` and the `memory` toolset, with `rebuild` from Library evidence (§2.6, DC-14) | becomes real with Hindsight plus FTS5 |
| New context sources (another video site, a data vendor, a new app output) | a new `@` reference kind resolved by a toolset row (DC-15) | grammar designed |
| Skill format updates (agentskills.io) | Library `skill` kind schema version | one adapter |
| New loop patterns (goal judges, plateau rules) | loop stop types, grader modes, AD-47 session rows | yes |
| New node ideas | node-kind registry, `<pack>.<name>` on base kinds, `typeVersion` | yes |
| Better evals and judges | the eval battery is a workflow; the judge is a role | designed (DC-10) |

The rule underneath all of it: **QMX owns its data in plain, versioned, QMX-defined formats** (catalog rows, Library objects, ledger events, `SKILL.md`, JSON Schema) **and projects them into whichever runtime runs the model.** Projections are thin and replaceable; the data is not. [inferred]

---

## 6. Sources

**Primary (web, retrieved 2026-10-18):**
- Anthropic, *Building effective agents* (2024-12-19), https://www.anthropic.com/engineering/building-effective-agents
- *Effective context engineering for AI agents* (2025-09-29), https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- *Writing effective tools for agents — with agents* (2025-09-11), https://www.anthropic.com/engineering/writing-tools-for-agents
- *Code execution with MCP* (2025-11-04), https://www.anthropic.com/engineering/code-execution-with-mcp
- *Introducing advanced tool use* (2025-11-24), https://www.anthropic.com/engineering/advanced-tool-use
- *Effective harnesses for long-running agents* (2025-11-26), https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- *Demystifying evals for AI agents* (2026-01-09), https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- Claude Agent SDK, *Scale to many tools with tool search*, https://code.claude.com/docs/en/agent-sdk/tool-search
- Hindsight: https://hindsight.vectorize.io/ and its pages `/developer/retain`, `/developer/retrieval`, `/developer/installation`, `/developer/knowledge-pages`, `/integrations`, `/sdks/integrations/claude-agent-sdk`, `/sdks/integrations/local-mcp`; https://github.com/vectorize-io/hindsight (MIT)

**Primary (repo, retrieved):**
- Hermes docs mirror `research/sources/hermes-docs/` (`reference/toolsets-reference.md`, `developer-guide/tools-runtime.md`, `user-guide-features/delegation.md`)
- studies 37a, 37b and 37d
- `research/one-engine/02a-claude-agent-sdk.md` (SDK facts with their own links)
- `tracker/agent-system/research/31-tools-skills-prompts-comms.md`
- the engine, Library and Lab spines and LLDs (read-only)
- 26 (rulings 1-117) and 33
- alignment A, B and C
- the code at `origin/engine/base` as cited in §3.1

**His clippings** (Obsidian `C:\Users\Mubarak\Documents\brain\brain\Clippings\`, retrieved), found in transcript `5efecf49…jsonl` lines 3 and 77:
- *Agent Harness Engineering vs. Loop Engineering vs. Graph Engineering* (@beamnxw)
- *Loop vs Graph Engineering Clearly Explained* (@Sumanth_077)
- *Not Every Agent Workflow Needs AI* (@HermesWatcher)
- *The Loop Runs While You Sleep* (@buildalpha)
- *How To Use Loop Engineering To Build A Self-Improving Quant Trading System* (@RohOnChain)
- *How to use probabilistic thinking to get better answers from AI* (@free_ai_guides)
- *Post by @karpathy* (output formats)

**Remembered, not re-checked today:**
- Manus context-engineering lessons
- OpenAI's harness-engineering write-up
- the Anthropic and OpenAI tool-name pattern and 64-character limit
- the `--append-system-prompt-file` CLI flag
- Claude 4-era prompting guidance
- *Building agents with the Claude Agent SDK*

**Probes this study adds or sharpens:**
- `tool_reference` per key host (DC-4)
- dotted and long MCP tool names on the pinned CLI (DC-3)
- a file route for long system text (DC-8)
- loop-over-subworkflow validation (DC-11)
