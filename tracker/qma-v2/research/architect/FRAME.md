# Architect Phase B frame: the QMA v2 harness

Arena Phase A. The same task goes to every runner. The rubric is for the judge and the picker; runners see only the task section and the grounding.

## Task (what each runner produces)

One candidate design package for the **QMA v2 agent harness**, written to your own folder:
- `design.md`: the rationale, shaped per `~/.claude/skills/architect/references/rationale-template.md` (Problem, Usage, Shape, Tradeoffs accepted, Alternatives considered, Open questions and risks, Next implementation step). Leave "Synthesis decision" empty.
- `sketch/`: a Python 3.14 type sketch of the new package `qma2` (to live at `qmx-agents/packages/qma-v2`): module map, dataclasses/Protocols/enums, function signatures with `raise NotImplementedError` bodies, docstrings stating intent and invariants, `# TODO` pseudocode for tricky logic. Plus the exact additions to `qmx-control` (new `OPERATIONS` rows, new tables, new routes) as signatures.
- `units.md`: the harness cut into 6-10 PR-sized units in dependency order, each with one "done when" a non-technical operator can see in a temporary console (and the live check behind it), and which units can run in parallel.

What the harness is (operator's words and rulings, latest wins):
- "The tools you have access to ... that's the baseline": every QMX agent gets at least what vanilla Claude Code / Codex give out of the box, plus QMX hooks. Sign-off = he signs in once with his Claude Max, chats, and it reads/edits files, runs commands, searches the web, starts a helper, asks before risky actions, refuses any money action, resumes after a restart; switching the chat to an OpenRouter model also works; a usage page shows how much of his Claude window is used. A temporary console is fine; the real UI is wired later in another session.
- Two engines: Claude Agent SDK and OpenAI Agents SDK. Claude's structure (permission modes and rules, hooks, sub-agents, skills, CLAUDE.md, memory, compaction, caching) is the target; it is native on the Claude engine and rebuilt by QMX on the OpenAI engine, using Codex's source as reference.
- Accounts: exactly ONE Claude Max (subscription, never API). GPT via "Sign in with ChatGPT" (probe first). Any other provider by API key and OpenAI/Anthropic compatibility: OpenRouter (he has a key), Meta Muse (api.meta.ai), GLM, Kimi, DeepSeek, MiniMax. A router balances whole sessions across accounts by usage left and capability, never mid-request; background work may use only spare Claude 5-hour window, default cap 50%, editable.
- Long-lived sessions persist (days), survive restarts and usage-window lockouts; transcripts and logs export with one action; traces stay local.
- Caching and compaction are top priority. Model or effort switch mid-chat is allowed with a cost warning.
- QMX settings, skills, agents, plugins and memory live in QMX's own config home, never his personal Claude Code folder.
- Money is read-only for agents, enforced by an always-on hook. Order proposals stay proposals that need his signature.
- Platform-neutral (Windows, macOS, Linux); no sandboxes; process separation and a secret store with a backend per OS.
Known tensions every candidate must resolve explicitly (state the choice and its cost):
- **Full Claude Code tools vs money safety.** The old native recipe stripped every built-in tool because "ordinary native tools need a separate enforceable worker boundary" (no OS isolation from money storage and broker configuration). The operator wants the same tools as Claude Code (Bash, file edits, web) and no sandboxes. With Bash, a same-user process can read keyring entries and broker credentials. Say how the design keeps money read-only anyway (e.g. broker secrets out of reach of agent processes, an operator-only signing path, deny rules plus hooks, a separate OS user as an optional backend), and which part is a real guarantee versus a speed bump.
- **One bearer token today.** Operator, agents and mini apps share one control token, so an "operator-only" route is not operator-only. The approvals answer path needs a principal agents cannot hold.
- **The money gate refuses `propose_order` by name.** A single policy point needs an explicit, narrow proposal-only exemption.
- **Importing qmx_control loads LangChain** until guards move; decide qma2's import edges.
- Out of scope now: organogram/project homes, workflows/graphs, mini apps as plugins, copilot and trader methodology, UI wiring, computer use (no subscription route offers it), rented compute (Docker test only), Strats, QMB/QML.

## Grounding (read all; these are the ONLY current sources)
1. `tracker/qma-v2/BASELINE.md` (start with its "Known corrections" box): parity matrix and the H1-H18 checks.
2. `tracker/qma-v2/research/H1-sdk-facts.md`: verified SDK and provider facts (sign-in rules, hooks subset, can_use_tool workaround, isolation, compaction limits, Meta Muse, ChatGPT route).
3. `tracker/qma-v2/research/how/HOW-harness-surface.md`: how today's code works and the plug-in points table. Details in `research/how/explorer-*.md` and `research/H3-code-map.md`.
4. `tracker/qma-v2/research/why/WHY-harness.md`: why today's shapes exist and which constraints still bind (written by the /why run).
5. `tracker/qma-v2/reviews/2026-10-13-forensic-session-audit.md` §2 (the operator's decision ledger, latest wins) and §5 (what "ship the harness" means in his words).
6. Research worth consulting: `tracker/agent-system/research/32-devops-and-ui-protocol.md` Part B (event protocol to keep), `30-agents-and-databases.md`, `31-tools-skills-prompts-comms.md`, `05-usage-limits-telemetry.md`.
7. Code: `D:/QMX-worktrees/harness-survey` (origin/rebuild/base 4eac8f69), read-only.
Superseded, evidence only, never the plan: anything under `tracker/qma-v2/archive/`.

## Rubric (judge and picker only)
1. **Coverage.** Every BASELINE H1-H18 item (as corrected) and every harness ask above has a named home (module, type, table, route) and a unit that ships it. Nothing out of scope sneaks in.
2. **One policy point.** Permission rules, approvals and hooks run through one QMX layer that behaves the same on both engines; the money rule cannot be bypassed by either engine, a sub-agent, an MCP tool or the agent answering its own approval.
3. **Fits today's code without new mess.** Uses qmx-control's `OPERATIONS` registry, today's 14 block kinds plus a live SSE channel, a single writer per SQLite file, an operator-only answer path that agents cannot reach, and a clean import graph (state how qma2 relates to qmx_control and the LangChain-tainted packages).
4. **Interface depth, no red flags** (`design-red-flags.md`): small public surface per engine adapter, no split ownership of session state, no hand-synced lists, no two ways to do one task.
5. **Ships as verifiable units.** The first unit proves a real Claude turn on his subscription (the existing recipe has never run live); each unit has a live check, not just fakes; parallel lanes are real.
6. **Compliance and facts.** No Claude token stored or injected; ChatGPT only via the allowed route; tracing local; respects every H1 fact.
