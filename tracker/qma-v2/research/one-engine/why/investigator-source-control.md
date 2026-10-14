# Investigator report: source control and in-repo design documents

Question: why does the 2026-10-13 QMA v2 design have its shapes, and which exist only because of the two-engine choice (OpenAI Agents SDK plus Claude Agent SDK) or a two-engine compromise? Written 2026-10-14 for the one-engine re-plan.

Path shorthand: all paths are relative to `D:/QMX-worktrees/agent-system/tracker/qma-v2/` unless absolute. Line numbers are from the working tree on `plan/agent-system` at `b611bd71`. Times are UTC. Commit times in git are +0300 (local); 19:22 +0300 is 16:22 UTC.

Tag key:
- **ENGINE-NEUTRAL**: the stated motive holds with one engine.
- **OPENAI-ONLY**: the shape exists only for the OpenAI engine.
- **TWO-ENGINE-COMPROMISE**: the shape was bent so one thing fits both engines.
- **UNCLEAR**: no stated motive found, or the motives conflict.

Where an item mixes motives, the primary tag comes first and the split is stated.

---

## Source

Source control (git history and commit messages on the local-only branch `plan/agent-system`) and in-repo design documents: `HARNESS.md`, `HARNESS-PLAN.md`, `BASELINE.md`, `BACKLOG.md`, `UI-NOTES.md`, `research/interrogate/` (VERDICT and both reviewer files), `research/architect/` (FRAME, JUDGE, candidate-1 design), `research/why/WHY-harness.md`, `research/H1-sdk-facts.md`, `reviews/2026-10-13-*.md`, `sketch/qma2/` docstrings, `trail/decisions.tsv` and `trail/RESUME-2026-10-14.md`. No GitHub PRs exist: the branch was never pushed and the GitHub MCP is down.

## What I Searched

- `git log --oneline -15`, then `git log --format='%h %ad %s' -- tracker/qma-v2` (41 commits, 2026-10-12 20:57 to 2026-10-13 21:42 +0300).
- `git show -s --format=%B` and `--stat` for b611bd71, 87398788, dde3a7d4, b2da7150, bd6ac11c, c48c48f0, 4da56ea7, df8d440a, 4556c060, 2c0cbea0, e0cc55a5, 942198c1, 44c62f53, 78d2b78f, 713534a0, 87eb3740, a178ddb1, 1e765321, cba755f7.
- `git show 713534a0` in full (the reverted morning handoff; it records the operator's two-engine answers).
- Diffs of c48c48f0 (A13), 4da56ea7 (A12) and b2da7150 (ON HOLD banner) for HARNESS.md and HARNESS-PLAN.md.
- `git diff` of the uncommitted `trail/decisions.tsv` (six 2026-10-14 rows).
- Full reads: `HARNESS.md` (335 lines), `HARNESS-PLAN.md` (704 lines), `BASELINE.md` (411 lines), `research/interrogate/VERDICT.md`, `research/architect/FRAME.md`, `JUDGE.md`, `candidate-1-opus/design.md`, `research/why/WHY-harness.md`, `trail/decisions.tsv`, `trail/RESUME-2026-10-14.md`.
- Partial reads: `sketch/qma2/{__init__,model,wire,policy,hooks}.py` and `host/{__main__,claude,openai,tools,compact}.py` docstrings; `research/H1-sdk-facts.md` fact table; reviewer-A findings 3, 4, 5, 9, 14-16, 18, 28 and reviewer-B findings 2, 8, 12; `reviews/2026-10-13-forensic-session-audit.md` §2.1, §2.2, §5; `reviews/2026-10-13-planning-phase-audit.md` §1 and §3.1; `BACKLOG.md` rulings row and Rejected table; `research/one-engine/02b-providers-translator-policy.md` section C (grep only).
- Greps over `reviews/`, `BACKLOG.md`, `README.md`, `UI-NOTES.md` for: `two engines|two-engine|both engines|OpenAI Agents SDK|second engine|one engine|other providers|Anthropic-compatible|translator`.
- Not read, by instruction: `trail/session-evening-dialog.md`, `trail/sources/`, any transcript, and `archive/` (it exists: `archive/2026-10-13-wednesday-frame/`). Not read for scope: `trail/agent-briefs.md`, `candidate-2-fable/` beyond what JUDGE quotes, `DELETION-PLAN.md`.

---

## Direct Evidence Found

### D1. Where the two engines came from (in-repo record)

- **What it says:** "**Two baselines.** Claude Code gives the structure (its mental model gets rebuilt on the OpenAI Agents SDK side). Codex/OpenAI gives the freedom. Study Codex's source; don't use it."
  **Where:** `git show 713534a0`, file `HANDOFF-2026-10-13.md` (reverted by 78d2b78f one minute later), section "Engines and platforms".
  **Author/date:** planning session, committed as git user "Codex", 2026-10-13 07:28 +0300 (04:28 UTC).
  **Relevance:** the earliest in-repo statement of the two-engine split and its division of labour: Claude gives structure, OpenAI gives freedom.

- **What it says:** "Engines | Two SDKs: the Claude Agent SDK (its capabilities, never the CLI) and the OpenAI Agents SDK. | 15:16 proposal, 16:22 ..., 04:22 | ... | **Proposal treated as settled.** At 15:28 he said "I said this is a proposal". Claude's real pushback came only at 15:30, and the study (19) came after the decision was recorded."
  **Where:** `reviews/2026-10-13-forensic-session-audit.md:54`.
  **Author/date:** independent Claude audit agent, committed in 942198c1 (2026-10-13 16:22 UTC).
  **Relevance:** the two-engine choice was flagged as a proposal treated as settled before the design work began.

- **What it says:** P3b: "It was not sold on the OpenAI Agents SDK as an engine ("one format, not two", no durable workflows)... Two lanes cost two event streams and two approval paths." Verdict: "Sound. The 1 GB point and the cost of two lanes were correct. The "translator" point was weak, since the OpenAI SDK takes any OpenAI-compatible base URL."
  **Where:** `reviews/2026-10-13-planning-phase-audit.md:50`.
  **Relevance:** someone raised a translator and the cost of two approval paths on 10-12. The audit called the translator point weak. The 18:33 ruling later adopted a translator.

- **What it says:** "**Two SDK engines** ... | **KEEP** | Required by his money rule: Claude and GPT only on subscriptions, everyone else on keys. Every provider exposes one of the two wire formats. The OpenAI SDK accepts any `base_url`, so OpenRouter, DeepSeek, GLM, Kimi and MiniMax all plug in."
  **Where:** `reviews/2026-10-13-planning-phase-audit.md:110`.
  **Relevance:** the only stated engineering reason for two engines in the repo: GPT needs a subscription route, and the key providers plug into the OpenAI SDK by `base_url`.

- **What it says:** "| Run other providers' models inside Claude Code, one profile or one Claude Code session per provider | "it was a thought, okay? I wasn't proposing it as the actual design" (15:16); "spawn up a code session for each of these" (15:16, called stupid at ~1 GB per session) |"
  **Where:** `BACKLOG.md:141` (Rejected table).
  **Relevance:** the recorded reason for keeping other providers off the Claude engine was about 1 GB of RAM per Claude Code session per provider.

- **What it says:** "This reverses his 2026-10-12 15:16 rejection of "other models on the Claude engine". He reversed it himself, so it is now settled."
  **Where:** `trail/RESUME-2026-10-14.md:22`.
  **Relevance:** the one-engine ruling directly removes the premise behind several 10-13 shapes (see D3, "engine derived from account").

- **What it says:** "operator ruled one engine (Claude Agent SDK) plus a GPT translator; two-engine plan put on hold ... | every provider except GPT speaks Anthropic format; Sign in with ChatGPT is format-bound, not SDK-bound, so a translator replaces the second SDK"
  **Where:** `trail/decisions.tsv` row `2026-10-13T18:33:25Z`.
  **Relevance:** the reason for the reversal, at commit-message grade.

### D2. The design's own statement that the frame shaped it

- **What it says:** "QMX needs one agent harness ... on two engines ... Five facts make the shape non-obvious: - The Claude SDK enforces its own structure. The OpenAI SDK has almost none: its hooks only observe, and its guardrails skip Shell and ApplyPatch (H1 fact 12)."
  **Where:** `HARNESS.md:13-16`.
  **Relevance:** the first of the five facts the design names as shape-driving is about the OpenAI SDK only.

- **What it says:** "Engines run abroad, in host processes that hold only an engine and a pipe. Policy, hooks, approvals, rules, routing and storage stay at home in qmx-control. ... - Both engines hit the same `policy.evaluate`, so behaviour is identical by construction, not by keeping two implementations in step."
  **Where:** `HARNESS.md:92-93`.
  **Relevance:** "policy at home" is justified first by cross-engine sameness. The same list gives four engine-neutral reasons (lines 94-97, see D3 "host pipe").

- **What it says:** "We accept losing Claude's native settings-file hooks and rules in exchange for hooks and rules that behave the same on both engines. QMX reads the same Claude-format files itself."
  **Where:** `HARNESS.md:295` (Tradeoffs accepted).
  **Relevance:** the clearest explicit two-engine compromise in the design. Claude's native rule and hook machinery was given up for parity.

- **What it says:** "**Engines in-process with a policy shim per adapter.** ... it is two policy evaluators that drift: Claude rules would come from settings and OpenAI rules from QMX. It does not fix the env merge, it gives no crash isolation, and agent code would share the process that holds the operator session and the DB writer. Rejected on one policy point and on separation."
  **Where:** `HARNESS.md:304`.
  **Relevance:** the rejected alternative names two motives: drift between two engines, and separation, which is engine-neutral.

- **What it says:** "Status of the current files (the evening session's guess; verify it, do not trust it)" ... "`HARNESS.md` + `sketch/` | Mostly valid. Remove the OpenAI engine (`host/openai.py`, `host/tools.py`, `host/compact.py` local compactor, OpenAI parts of A1, A3, A13, V5.1, V5.3). Add a translator component." ... "**Guessed to drop (unverified):** units U4a, U4b and U8, and the OpenAI half of U7."
  **Where:** `trail/RESUME-2026-10-14.md:29`, `:36`.
  **Relevance:** the evening session's own unverified tagging. My tags below agree on the OPENAI-ONLY items. They add TWO-ENGINE-COMPROMISE items that the note lists as "carry over" (the policy point, ProjectContext, hooks at home, engine derived from account).

### D3. Core shapes named in the brief

| Shape | Tag | Supporting line (verbatim) | Where |
|---|---|---|---|
| The policy point (one `policy.evaluate` in qmx-control for every tool call) | **TWO-ENGINE-COMPROMISE** (gray; also has engine-neutral motives) | "Both engines hit the same `policy.evaluate`, so behaviour is identical by construction, not by keeping two implementations in step." Counter-motive, engine-neutral: "Rejected on one policy point and on separation." | `HARNESS.md:93`, `:304` |
| Money gate (`money.classify` first; `Deny(MONEY)` never approvable) | **ENGINE-NEUTRAL** | "The money-path barrier is inherited planning law, not an incident fix." Also: "Money is read-only for agents, enforced by an always-on hook." | `research/why/WHY-harness.md:46`; `research/architect/FRAME.md:19` |
| Operator principal (cookie, `who=OPERATOR`, `OperatorProof`) | **ENGINE-NEUTRAL** | "**One bearer token today.** Operator, agents and mini apps share one control token, so an "operator-only" route is not operator-only. The approvals answer path needs a principal agents cannot hold." | `research/architect/FRAME.md:23` |
| CallOp grant (one-shot, gate-bound) | **ENGINE-NEUTRAL** | "Accepted only for a `tool_use_id` that just received an Allow from `Gate`, consumed once, so a host cannot reach a QMX op without passing the policy point." | `sketch/qma2/wire.py:191-193` (`CallOp` docstring) |
| Host pipe (`python -m qma2.host`, one per live thread) | **ENGINE-NEUTRAL** (mixed; one clause two-engine) | "The host is the launcher of the Claude CLI. The SDK's env merge can only merge the host's allow-listed env, which fixes Gotcha 6 without a custom transport." / "A host has no HTTP credential at all. Its pipe is its only capability" / "A crash or kill takes down one thread." | `HARNESS.md:94`, `:96`, `:97` |
| Engine derived from account (`Route = ClaudeRoute(ClaudeSubscription) \| OpenAIRoute(...)`) | **TWO-ENGINE-COMPROMISE** (it encodes the reversed 15:16 ruling) | "An engine is never chosen on its own. It is derived from the account kind (`Route`), so "Claude engine on an OpenRouter key" cannot be expressed." | `sketch/qma2/model.py:8-9`; also `HARNESS.md:101`, `:176` ("No other providers on the Claude engine (ruled out).") |
| `items` as the one canonical transcript for both engines | **TWO-ENGINE-COMPROMISE** | "**items** (harness.db) is the one canonical transcript for both engines ... It serves export, cross-engine seeding and OpenAI resume" | `HARNESS.md:102` |
| Hooks run in qmx-control, never in the engine | **TWO-ENGINE-COMPROMISE** | "Hooks never run inside an engine. ... So one hook script behaves the same everywhere" | `sketch/qma2/hooks.py:1-10`; `HARNESS.md:122`, `:295` |
| ProjectContext as the first user message on both engines | **TWO-ENGINE-COMPROMISE** | "H9 project instructions \| `config.ProjectContext` (first user message on both engines)" | `HARNESS.md:191` |
| Six-verb `Adapter` protocol | **TWO-ENGINE-COMPROMISE** | "The whole per-engine surface: six verbs. ... so the two adapters stay small and alike." | `sketch/qma2/host/__main__.py` `Adapter` docstring |
| A pending approval dies with its host | **TWO-ENGINE-COMPROMISE** (same effect with one engine) | "We accept that a pending approval dies with its host on both engines, rather than keeping OpenAI `RunState` alive across restarts. One rendezvous mechanism, and Claude can't survive it anyway." | `HARNESS.md:296` |
| `SwitchQuote` pinned to `cache_epoch` | **ENGINE-NEUTRAL** (its `ENGINE_CHANGE` kind is two-engine) | "A switch needs a `SwitchQuote` pinned to a `cache_epoch`." / `ENGINE_CHANGE = "engine_change"  # new segment on the other engine, seeded` | `HARNESS.md:167`; `sketch/qma2/model.py:444` |
| Separate `harness.db`, one writer | **ENGINE-NEUTRAL** | "A second writer connection on control.db would recreate the WAL-bug precondition." | `HARNESS.md:297` |
| UI event envelope carries `engine`; parity badge | **TWO-ENGINE-COMPROMISE** | "Both engines are normalised into it, so the UI never knows which SDK ran." / "An engine parity badge on sessions, skills and plugins ("both engines" or "Claude only")" | `UI-NOTES.md:24`, `:101` |

### D4. HARNESS.md amendments A1 to A13

| # | Decision | Tag | Motive line (verbatim) | Where |
|---|---|---|---|---|
| A1 | Closed `ToolEffect`; `MONEY_ACT` has no allow branch | **ENGINE-NEUTRAL** (one clause OPENAI-ONLY) | Judge: "the closed `ToolEffect` with `MONEY_ACT` having no allow branch ... is the best idea in either candidate." Two-engine clause: "`BUILTIN_EFFECTS` is the single table for Claude built-ins and the OpenAI kit. The kit uses Claude's tool names, so one table serves both." | `research/architect/JUDGE.md:25`; `HARNESS.md:229` |
| A2 | Proposals by identity only; remote `propose_order` is `MONEY_ACT` | **ENGINE-NEUTRAL** | "The money gate refuses `propose_order` by name. A single policy point needs an explicit, narrow proposal-only exemption." Decided: "unsigned proposals count as read-only money ... proposals-only matches ADR-0020 and DESIGN 5.7" | `research/architect/FRAME.md:24`; `trail/decisions.tsv` row 17:10:07 |
| A3 | One `ToolSpec` registry, serialised into `Spawn`; each host builds its SDK object | **TWO-ENGINE-COMPROMISE** | "the Claude host builds an SDK MCP server, the OpenAI host builds function tools. - No second list." Judge: "A defines `QmxTool` only on the OpenAI host ... and ships Claude a `qmx_tools: Sequence[Mapping]` in `Spawn` ... One control-side spec ... removes the hand-synced pair." | `HARNESS.md:239-240`; `research/architect/JUDGE.md:80` |
| A4 | `doctor()`; `settings_get/put` as OPERATOR rows; project layer `<cwd>/.qmx/`, never `<cwd>/.claude/` | **ENGINE-NEUTRAL** (the `.qmx` choice is gray in effect, see Indirect I4) | "The operator's standing rule is "configurable means UI-editable"." / "It is never `<cwd>/.claude/`, so his personal Claude Code hooks in a repo never run under QMX." | `HARNESS.md:243-244` |
| A5 | U0/U1 split; U1 = smallest path to one live Claude turn | **ENGINE-NEUTRAL** | "Neither proves a live Claude turn with the least code. ... The right U1 is A's script plus A's stub gate" | `research/architect/JUDGE.md:71` |
| A6 | Token check: no Claude token outside `claude-home/` | **ENGINE-NEUTRAL** | "The unmodified CLI's `/login` writes `claude-home/.credentials.json` by design." | `HARNESS.md:250` |
| A7 | Measure host plus CLI working set; idle reaping | **ENGINE-NEUTRAL** | "The "~1 GiB per Claude session" figure is Anthropic's hosting guidance, not a measurement." | `HARNESS.md:251` |
| A8 | Probes move to U1 (hooks with `setting_sources=[]`, `tool_use_id`, ask per mode, hook timeout) | **ENGINE-NEUTRAL** (downstream of the compromise in D3 "hooks run in control") | "Long waits always go through `can_use_tool`, never inside a hook callback." Judge: "Both should be U1 probes, not U2." | `HARNESS.md:257`; `research/architect/JUDGE.md:89` |
| A9 | Honest limits ("as of the last QMX turn"; no `attachments`; `fastapi.sse` real) | **ENGINE-NEUTRAL** | "His own Claude Code use draws from the same 5-hour window, and Claude reports limits only when the status changes." | `HARNESS.md:259` |
| A10 | Live-check budget (short prompts, 15-turn cap, OpenRouter for "a model") | **ENGINE-NEUTRAL** | "Live checks run on his one Max plan, the same window he uses himself." | `HARNESS.md:262` |
| A11 | Interrogate verdict V1-V6 binding | **UNCLEAR** (a meta rule; it inherits the V tags below) | "Every rule under "Act on" (V1 to V6) and the "Consider" items marked "do" ... amend this design and win over the sketch." | `HARNESS.md:268` |
| A12 | Platform-neutral `SecretStore` and supervisor | **ENGINE-NEUTRAL** | "QMX is not Windows-only. `SecretStore` has one interface with a backend per OS" (operator, 2026-10-13 evening) | `HARNESS.md:277`; commit 4da56ea7 |
| A13 | One `subagents` setting; Claude enforces natively, OpenAI via `AgentTool` | **TWO-ENGINE-COMPROMISE** (Claude half engine-neutral, OpenAI half OPENAI-ONLY) | "**One setting, two native mechanisms.** The user sees the same limits on both engines." Default inherited from Codex: "`max_concurrent` (default 6)" vs Claude's native "`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` (default 20)". BASELINE source of 6: "a concurrency cap (default 6, as Codex, configurable)" | `HARNESS.md:279-285`; `BASELINE.md:218` |

A-group primary counts: ENGINE-NEUTRAL 10, TWO-ENGINE-COMPROMISE 2 (A3, A13), OPENAI-ONLY 0, UNCLEAR 1 (A11).

A13 history (commit c48c48f0, 2026-10-13 18:16 UTC): the diff removed "depth and concurrency caps" from the policy chain, which had applied them in QMX on both engines (`-money(input) → PreToolUse hooks → money(updated input) → depth and concurrency caps → deny rules ...`). Trail row 18:16:26: "removed the re-implemented cap step from the Claude policy chain | operator asked how the SDK docs handle the guard; docs read in the browser show Claude enforces these natively". So before A13 the design re-implemented on Claude a cap that Claude already has natively. This is a recorded case of the two-engine frame bending the Claude side, found and partly undone one hour before the one-engine ruling.

### D5. VERDICT rules V1 to V6

Rule-level tags first, then the sub-rules that differ.

| Rule | Tag | Motive line (verbatim) | Where |
|---|---|---|---|
| V1 Agents cannot escalate or self-approve through QMX surfaces | **ENGINE-NEUTRAL** | "Opus found the two most dangerous issues no one else saw: broker secrets reachable through `run_job` (A1), and operator forgery through harness.db (A2)." | `research/interrogate/VERDICT.md:143` |
| V2 The Claude engine fails closed and cannot route around QMX policy | **ENGINE-NEUTRAL** (V2.1 and V2.5 are TWO-ENGINE-COMPROMISE) | Reviewer A3: "Under mirrored `bypassPermissions`, the call runs with no QMX decision. That includes an external broker MCP tool, which never reaches `money.classify`." | `research/interrogate/reviewer-A-opus.md:19` |
| V3 Grants, actor and link correct under concurrency and crashes | **ENGINE-NEUTRAL** (one clause OPENAI-ONLY: `LoadItems`) | "Three pairs are consensus: A8 with B5, A9 with B3, and A15 with B13." | `research/interrogate/VERDICT.md:54` |
| V4 Routing and usage tell the truth | **ENGINE-NEUTRAL** | Reviewer A14: "An OpenRouter key serves `anthropic/claude-*` and `openai/gpt-*`. ... That contradicts the operator ruling "no API for Claude or GPT"" | `research/interrogate/reviewer-A-opus.md:89` |
| V5 Parity details the baseline depends on | **TWO-ENGINE-COMPROMISE** (mixed: 4 neutral, 2 OPENAI-ONLY, 1 compromise) | Reviewer B12: "On Windows the two engines expose different shell tool names, so "rules and hook matchers written once" breaks" | `research/interrogate/reviewer-B-fable.md:58` |
| V6 The unit plan matches the design | **ENGINE-NEUTRAL** (V6.2 OPENAI-ONLY in part) | "The plan is rewritten from `HARNESS.md`, not from `candidate-1-opus/units.md`." | `research/interrogate/VERDICT.md:94` |

V-group primary counts: ENGINE-NEUTRAL 5, TWO-ENGINE-COMPROMISE 1 (V5), OPENAI-ONLY 0, UNCLEAR 0.

Sub-rules whose tag differs from their rule:

| Sub-rule | Tag | Supporting line (verbatim) | Where |
|---|---|---|---|
| V2.1 Mode mirroring: only `plan` reaches the SDK | **TWO-ENGINE-COMPROMISE** (gray) | Reviewer B2: "protected-path asks and hook `ask`s are silently auto-approved under `acceptEdits`/`bypass` on the Claude engine while the OpenAI engine asks, which breaks "identical by construction"." The money motive in A3 is engine-neutral. | `reviewer-B-fable.md:10`; `reviewer-A-opus.md:19` |
| V2.5 Claude MCP descriptors listed by QMX at segment start | **TWO-ENGINE-COMPROMISE** | "An unknown MCP tool name is denied, so the money check sees the same descriptors on both engines." Reviewer A4 title: "On the Claude engine, MCP money checks are name-only, so the two engines are not identical" | `VERDICT.md:48`; `reviewer-A-opus.md:22` |
| V3.2 clause: "`LoadItems` waits on an "items committed up to seq N" barrier" | **OPENAI-ONLY** | `LoadItems(segment)    -> items          (OpenAI resume)` | `VERDICT.md:57`; `sketch/qma2/wire.py:19` |
| V5.1 Shell family; OpenAI kit ships both `Bash` and `PowerShell` | **OPENAI-ONLY** | "On Windows the OpenAI kit ships both `Bash` (git-bash, when present) and `PowerShell`." | `VERDICT.md:82` |
| V5.3 Reasoning items stored verbatim | **OPENAI-ONLY** | "**Reasoning items are stored verbatim** with `include=["reasoning.encrypted_content"]`. U4 and U8 include a two-turn tool-using replay." | `VERDICT.md:84` |
| V5.4 Re-send ProjectContext after Claude compaction; drop MEMORY.md on Claude | **TWO-ENGINE-COMPROMISE** | Reviewer A18: "With `setting_sources=[]`, the CLI does not re-inject CLAUDE.md after `compact_boundary`. A first user message gets summarised away" | `VERDICT.md:85`; `reviewer-A-opus.md:115` |
| V5.2, V5.5, V5.6, V5.7 | ENGINE-NEUTRAL | V5.5: "**WebFetch asks per domain and WebSearch asks,** as in vanilla Claude Code." V5.7 corrects an OpenAI-only claim: ""Tool processes carry no keys" is true on the OpenAI engine." | `VERDICT.md:83`, `:86-88` |
| V6.2 Graph: "U4's parity checks run after U2 and U3"; "`host/openai.py` has one owner per wave" | **OPENAI-ONLY** (its key-entry clause is engine-neutral) | as quoted | `VERDICT.md:95-98` |

Sub-rule counts (37 sub-rules): ENGINE-NEUTRAL 31, TWO-ENGINE-COMPROMISE 3 (V2.1, V2.5, V5.4), OPENAI-ONLY 3 (V5.1, V5.3, V6.2), plus one OPENAI-ONLY clause inside V3.2.

Context for V-tags: VERDICT's own intent line frames the whole review in two-engine terms: "It runs on two engines with one QMX policy point" (`VERDICT.md:7`). Its pattern line: "No finding attacks the shape: the host process, one policy point and the actor all survive." (`VERDICT.md:144`). The reviewers were not asked whether one engine would change the shape.

### D6. HARNESS-PLAN units

| Unit | Tag | Supporting line (verbatim) | Where |
|---|---|---|---|
| U0 Scaffold | **ENGINE-NEUTRAL** (OpenAI clauses: `openai-agents==0.23.1` pin, lane 9 `import agents` check) | "Create ... `pyproject.toml` with runtime pins `claude-agent-sdk==0.2.165`, `openai-agents==0.23.1`" | `HARNESS-PLAN.md:92`, `:117` |
| U1 One live Claude turn | **ENGINE-NEUTRAL** | "U1 is the smallest path to one live Claude turn" | `HARNESS.md:248` |
| U1b Console, store, resume, operator login | **ENGINE-NEUTRAL** | "Move operator pairing into this PR (VERDICT V6.2)." / "Resume after a restart uses `segment.sdk_session_id`." | `HARNESS-PLAN.md:189`, `:191` |
| U2 Ask before risky tool calls on Claude (full `policy.decide`) | **TWO-ENGINE-COMPROMISE** (gray; money, approvals and operator parts are neutral) | Policy re-implemented in QMX with "Claude rule syntax, compound-command split, the `shell` family (V5.1), modes without `auto`" because of HARNESS tradeoff "We accept losing Claude's native settings-file hooks and rules in exchange for hooks and rules that behave the same on both engines." | `HARNESS-PLAN.md:235`; `HARNESS.md:295` |
| U4a OpenAI engine on an OpenRouter key | **OPENAI-ONLY** | "Create `.../host/openai.py` ... and `host/tools.py` (the Claude-shaped kit and `ProcessTable`)." | `HARNESS-PLAN.md:277` |
| U3 Hooks, config home, instructions, skills, agents, memory on Claude | **TWO-ENGINE-COMPROMISE** (the config home and native sub-agent limits are neutral) | "Run Claude-format command hooks in qmx-control" / "Send `ProjectContext` (CLAUDE.md plus AGENTS.md) as the first user message" | `HARNESS-PLAN.md:324`, `:326` |
| U4b Same behaviour on OpenAI | **OPENAI-ONLY** | "`tests/test_parity_openai.py` replays the U2 policy table and the U3 hook cases through a fake OpenAI model" | `HARNESS-PLAN.md:376` |
| U5 Usage and switch warning | **ENGINE-NEUTRAL** (cross-engine seeding parts two-engine) | "Probe the SDK `get_usage` control request first" / "Apply the family guard in `router.pick`, `quote_switch` and the account model list (V4.1)." | `HARNESS-PLAN.md:413`, `:415` |
| U6 Compact, steer, interrupt on both engines | **OPENAI-ONLY** (split: Claude steer/interrupt and kill-tree are neutral; ProjectContext re-send is compromise) | "Compact remotely where the provider offers it, else locally from Codex's summary prompt" | `HARNESS-PLAN.md:458`; `sketch/qma2/host/compact.py:1` ("Compaction for the OpenAI engine (H11). The Claude engine compacts natively.") |
| U7 OpenAI helpers, MCP tools, proposals | **ENGINE-NEUTRAL** (split: `AgentTool` and background registry are OPENAI-ONLY) | Neutral: "Bind each `CallOp` grant to name plus canonical args digest" / "Confine agent thread ops." OpenAI-only: "Write `AgentTool` reading `max_depth` and `max_concurrent`" | `HARNESS-PLAN.md:501-503` |
| U9 Threads alive for days | **ENGINE-NEUTRAL** (lane 6 re-route to OpenRouter assumes a second engine) | "On a lockout, a foreground thread waits and offers a switch, and a background thread re-routes at a turn boundary." | `HARNESS-PLAN.md:546`, `:560` |
| U8 Sign in with ChatGPT | **OPENAI-ONLY** (the need survives; the Agents-SDK shape does not) | "an Agents SDK run against `https://api.openai.com/v1/responses` with `store=false` and `stream=true`" | `HARNESS-PLAN.md:588` |
| SIGNOFF | **ENGINE-NEUTRAL** | "He does each action in lanes 2 to 10 himself and says in chat that the harness is signed off." | `HARNESS-PLAN.md:635` |
| U10 OS-account backend (not scheduled) | **ENGINE-NEUTRAL** | "U10, the separate OS account, is not scheduled and runs only if he asks for it there." | `HARNESS-PLAN.md:696` |

Unit primary counts (14 units): ENGINE-NEUTRAL 8, OPENAI-ONLY 4 (U4a, U4b, U6, U8), TWO-ENGINE-COMPROMISE 2 (U2, U3), UNCLEAR 0. Two of the eight neutral units (U7, U0) and one OPENAI-ONLY unit (U6) are split.

The plan's own opening states the frame: "chat with an agent that has vanilla Claude Code tools on two engines." and "The rule the program enforces is one QMX policy point for every tool call on both engines" (`HARNESS-PLAN.md:5-6`). Appendix B records two dependency choices that exist only because of `host/openai.py`: "U5, U6 and U7 in one parallel wave. They would share `host/openai.py`, which V6.2 gives one owner per wave. U7 waits for U6 instead." (`HARNESS-PLAN.md:684`) and "One U4 PR. ... U4 splits into U4a and U4b." (`:683`).

### D7. BASELINE.md: a two-engine document by construction

- **What it says:** "**QMA v2 rule:** what QMX must provide so both engines reach the baseline, and where Claude's design is rebuilt on the OpenAI side."
  **Where:** `BASELINE.md:28`. Commit 44c62f53, 2026-10-13 04:37 UTC, message "QMA v2: harness baseline (Claude Code vs Codex vs OpenAI Agents SDK parity matrix)".
  **Relevance:** every matrix row has an "OpenAI engine needs" column. RESUME says that column "becomes "not built"" (`trail/RESUME-2026-10-14.md:31`).

- **What it says:** "So the rule is: **QMX owns one copy of each piece of structure.** The Claude engine uses Claude's native version. The OpenAI engine gets a QMX rebuild of Claude's design, using Codex's code as the reference."
  **Where:** `BASELINE.md:37`.
  **Relevance:** BASELINE meant Claude's side to stay native. HARNESS later moved rules and hooks off Claude into QMX (D2). See Contradiction C5.

- **What it says:** "Anthropic-compatible endpoints from DeepSeek, GLM, Kimi and OpenRouter (research `01` §1) are a second option: run those models on the **Claude** engine and get Claude's structure for free. This trades provider-native features for harness parity. Decide per provider after H5 and H11 pass."
  **Where:** `BASELINE.md:370`. Overridden by the corrections box: "Line ~360 (other providers on the Claude engine) is rejected by the operator." (`BASELINE.md:7`).
  **Relevance:** the one-engine path was written down on the morning of 10-13 and struck the same evening. The one-engine ruling restores it.

- BASELINE H-items that are OPENAI-ONLY by their own wording: H5 ("Core tool set on the OpenAI engine", `:384`), the OpenAI half of H11 ("local summariser for non-OpenAI", `:390`), the ChatGPT refresh in H17 (`:396`), the "OpenAI trace export off" half of H18 (`:397`). H2's original shape (Codex v2 JSON-RPC, `:381`) was already dropped by the corrections box (`:9`).

---

## Indirect / Circumstantial Evidence

- **I1. What it is:** the trail starts after the two-engine choice. **Where:** `trail/decisions.tsv` first row `2026-10-13T16:05:22Z`, and row `17:50:06Z` ("rows stamped 16:05:22-26 were backfilled"). **What it suggests:** no row in the trail records why two engines were chosen. The frame was an input to every evening step (`/how`, `/why`, `/architect`, `/interrogate`, plan), not a decision taken in it. FRAME states it as given: "Two engines: Claude Agent SDK and OpenAI Agents SDK. Claude's structure ... is the target; it is native on the Claude engine and rebuilt by QMX on the OpenAI engine" (`research/architect/FRAME.md:14`). **Alternative reading:** the evening session treated the 04:22 ruling as settled and did not need to restate it.

- **I2. What it is:** the architect rubric scored cross-engine sameness. **Where:** `research/architect/FRAME.md:40`: "**One policy point.** Permission rules, approvals and hooks run through one QMX layer that behaves the same on both engines". **What it suggests:** candidates were judged partly on two-engine parity, so the winning base (candidate 1, 27 to 22) was selected under the two-engine frame. The judge's top reason for A includes "Adding a third engine is one adapter behind six verbs and no policy code." (`JUDGE.md:74`). **Alternative reading:** the same criterion also covers sub-agents and MCP tools, which are engine-neutral; candidate 1 could still win on criteria 3 and 6 alone (env merge, separation, compliance).

- **I3. What it is:** candidate 2 (Fable) ran the Claude CLI as a direct child of qmx-control, with no Python host. **Where:** `JUDGE.md:65`: "A: control + `python -m qma2.host` (~80-120 MB with SDK and pydantic) + the CLI ... B: control + the CLI. The host adds under 15% on top of the CLI." Its env scrub failed: "`engines/claude.py:67` passes `env=ctx.env | CLAUDE_ENV_INJECT` ... the SDK merges `os.environ` into the child" (`JUDGE.md:29`). **What it suggests:** with one engine the host process stays justified by the env merge, isolation and separation, not by policy sameness. The judge gives an engine-neutral alternative ("unless the `cli_path` wrapper re-execs with a clean env", `JUDGE.md:57`). **Alternative reading:** none found that weakens the env-merge reason.

- **I4. What it is:** the `.qmx/` project layer (A4) versus Claude's native `.claude/`. **Where:** `HARNESS.md:244`; judge: "Flag this for the operator; it is vocabulary he cares about." (`JUDGE.md:82`). **What it suggests:** the motive is engine-neutral (keep his personal Claude Code hooks out of QMX). But on one engine, refusing `.claude/` means QMX must load project settings, hooks, agents and skills itself instead of letting the SDK read them natively, which compounds the D2 tradeoff. **Gap:** I found no trail row saying the `.qmx` choice was put to the operator.

- **I5. What it is:** the operator's own evening wording kept the rebuild premise. **Where:** `BACKLOG.md:23`: "Permission modes and hooks copied from the Claude Agent SDK, rebuilt on the OpenAI side. Computer use through what the SDKs provide (OpenAI strongest)". **What it suggests:** computer use was expected from the OpenAI side. With one engine it has no subscription route (H1 fact 8; RESUME Gotchas "the Claude SDK has no computer use on a subscription"). This is a capability the OpenAI side was meant to cover. **Alternative reading:** H1 fact 16 already says ComputerTool is "Not available on the ChatGPT-plan route", so the OpenAI side never covered it on his accounts either.

- **I6. What it is:** the "1 GB per session" reason behind the 15:16 rejection. **Where:** `BACKLOG.md:141`; H1 fact 9: "one session = one subprocess ... Starting point "1 GiB RAM, 5 GiB disk, and 1 CPU per agent"" (`research/H1-sdk-facts.md:64`); A7: "not a measurement" (`HARNESS.md:251`). **What it suggests:** every Claude-engine thread costs one CLI process whatever its provider, so the RAM objection applied to Claude threads in the two-engine design too. The two-engine design hosted key providers on the OpenAI engine, which needs no CLI. One engine moves every key-provider thread onto a CLI process. **Alternative reading:** the 15:16 objection was to a Claude Code session *per provider*, which is not what a router picking one provider per thread does. The in-repo record does not settle which he meant.

- **I7. What it is:** research written 2026-10-14 on mixing providers on one engine. **Where:** `research/one-engine/02b-providers-translator-policy.md:113`: "One Agent SDK session runs one CLI process with one `ANTHROPIC_BASE_URL` and one credential. ... So there is no native per-subagent provider switch." **What it suggests:** BASELINE's cross-engine delegation note ("Cross-engine delegation (Claude parent, GPT child) goes through a QMX tool that starts a new thread on the other engine", `BASELINE.md:220`) has a one-engine analogue: cross-provider delegation needs a new session. **Alternative reading:** this file is post-ruling research, not evidence of 10-13 motive.

- **I8. What it is:** git authorship. **Where:** every commit on the branch is authored "Codex <codex@openai.com>". **What it suggests:** that is the configured git user (gitStatus says "Git user: Codex"), not evidence that Codex wrote the design. The trail and file headers name the planning session (Opus 5.5) and Fable runners and judge.

---

## Contradictions

- **C1.** Planning audit: "Every provider exposes one of the two wire formats. The OpenAI SDK accepts any `base_url`" (`reviews/2026-10-13-planning-phase-audit.md:110`). Versus the 18:33 ruling: "every provider except GPT speaks Anthropic format" (`trail/decisions.tsv` 18:33:25). Both can be true. The audit used the OpenAI-compatible endpoints, the ruling uses the Anthropic-compatible ones. Each picks a different engine as the common one.
- **C2.** Planning audit, P3b: "The "translator" point was weak" (`planning-phase-audit.md:50`). Versus the ruling: "a translator replaces the second SDK" (`decisions.tsv` 18:33:25).
- **C3.** BASELINE proposed key providers on the Claude engine (`BASELINE.md:370`). Its corrections box says "rejected by the operator" (`:7`). The forensic audit calls it "**Musing treated as a design.** BASELINE.md:360 revives "run those models on the Claude engine", which he called stupid at 15:16" (`forensic-session-audit.md:70`). RESUME says he "reversed it himself" (`RESUME-2026-10-14.md:22`).
- **C4.** HARNESS "What it deliberately does not do": "No other providers on the Claude engine (ruled out)." (`HARNESS.md:176`) and the `Route` invariant (`sketch/qma2/model.py:8-9`). Versus the one-engine ruling, which puts every provider on the Claude engine.
- **C5.** BASELINE planned Claude-native rules and hooks: "**Claude engine:** QMX writes rules into the session's settings and answers `can_use_tool` from the same engine." (`BASELINE.md:131`) and "**Claude engine:** native hooks; QMX only adds UI notifications." (`:171`). Versus HARNESS: "QMX passes `setting_sources=[]`, no rules, and a materialised plugin with no hooks." (`HARNESS.md:120`) and the tradeoff at `:295`. Between the morning baseline and the evening design, the Claude side moved from native to QMX-owned. The stated reason is cross-engine sameness plus the money gate on built-ins.
- **C6.** WHY: "The 10-13 04:22 ruling ("harness first") re-confirms the two engines." (`research/why/WHY-harness.md:30`). Versus the forensic audit flag "**Proposal treated as settled.**" (`forensic-session-audit.md:54`). WHY cites the audit and the flag in the same sentence, so these are recorded side by side rather than resolved.
- **C7.** Planning audit recommended the OpenAI engine in-process: "**CHANGE BASELINE back** ... Use in-process async plus one worker process" (`planning-phase-audit.md:123`). HARNESS rejected candidate 2's in-process OpenAI engine (`HARNESS.md:212`). This is moot with one engine.
- **C8.** A13 keeps QMX's `max_concurrent` default at 6 (from Codex, `BASELINE.md:218`) while Claude's native default is 20 (`HARNESS.md:280`). The value was chosen for the OpenAI side and imposed on Claude through the shared setting.

---

## Gaps

- Searched `git log -- tracker/qma-v2` (41 commits). No commit message carries a "why". Every message is a title only, apart from the revert message. The rationale lives in the trail, the HARNESS tradeoffs and alternatives, JUDGE and VERDICT.
- No PRs or review threads: the branch was never pushed, and the GitHub MCP is down.
- No trail row records the motive for two engines. The trail begins at 16:05 UTC on 10-13, after the choice (I1).
- No trail row gives per-amendment reasons for A1 to A10. The 17:09:13 row covers the base pick and one rejected graft. A1 to A10 motives come from JUDGE "Grafts from B into A" and "What both missed".
- Searched HARNESS, VERDICT, JUDGE and the trail for any assessment of which shapes depend on the engine count before 18:33 UTC. Found none apart from the evening's unverified guess in RESUME (lines 27-41).
- No record that the `.qmx` versus `.claude` choice (A4) was put to the operator, despite the judge's "Flag this for the operator" (`JUDGE.md:82`).
- No in-repo measurement of RAM per Claude CLI process. Every figure is Anthropic's hosting guidance (A7).
- The sketch has no inline `# why` comments beyond module docstrings. Docstrings repeat HARNESS text.
- No test files exist (planning-only). Appendix A: "No prototype ran, so there is no branch, SHA or artifact." (`HARNESS-PLAN.md:673`).

## Additional Leads

For the chat-record investigator (not chased here):
- 2026-10-12 15:16 UTC: "We designed just two: OpenAI and Anthropic." and the rejection of other models on Claude at about 1 GB per session (`forensic-session-audit.md:235`; `BACKLOG.md:141`). Check whether the objection was to per-provider Claude Code sessions or to any non-Claude model on the Claude engine (I6).
- 2026-10-12 15:28 to 15:30 UTC: "I said this is a proposal" and Claude's pushback ("one format, not two", two approval paths, translator) (`planning-phase-audit.md:50`).
- 2026-10-12 16:22 UTC: "I want the bloody capabilities" / "I don't want the bloody CLI" (`forensic-session-audit.md:54`, `:235`).
- 2026-10-13 04:22 UTC: "rebuilt it also in OpenAI so that we don't have to rebuild"; "Codex gives us, I think, more freedom" (`forensic-session-audit.md:236`).
- 2026-10-13 evening (18:16 UTC area): the operator's question that produced A13 ("operator asked how the SDK docs handle the guard", trail row 18:16:26), and the 18:28 and 18:33 messages that produced the ruling (trail rows 18:33:25 and 2026-10-14 07:25:43).
- `trail/agent-briefs.md` (briefs 13 to 17): how the architect runners, judge and interrogate reviewers were told about two engines. It is an extraction of session briefs, so I left it to the chat-record investigator.

Other in-repo leads (not read):
- `archive/2026-10-13-wednesday-frame/`: exists. Per the forensic audit, `ARCHITECTURE.md:383-384` had "hooks dropped on OpenAI", `ARCHITECTURE.md:34` ran OpenAI in-process, and `HOW-IT-WORKS.md:252` said the second engine is "so helpers can run on OpenRouter" (`forensic-session-audit.md:56`, `:201`; `planning-phase-audit.md:123`). Those are pre-10-13 two-engine shapes. Read them only as history.
- Commit 87eb3740 (2026-10-13 03:56 UTC, "record operator answers Q9-Q14") edits the now-archived `START-HERE.md` §5, which holds the morning answers the reverted handoff summarises.
- `tracker/agent-system/research/19-*.md` §12 (cross-engine delegation, cited at `BASELINE.md:220`) and research `01` §1 (Anthropic-compatible endpoints, cited at `BASELINE.md:370`).
