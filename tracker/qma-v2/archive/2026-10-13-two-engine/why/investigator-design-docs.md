### Source
Long-form design documents and recorded deliberation:
- `D:/QMX-worktrees/harness-survey` at 4eac8f69: `rebuild/DESIGN.md`, `rebuild/COPILOT.md`, `rebuild/README.md`, `rebuild/packets/P06,P07,P08,P11,P15,P16,P20,P24`, `rebuild/research/{audit-code,research-harness,ledger-chat,ledger-voice,ui-model-and-baseline-audit}.md`, `rebuild/reports/p16-deletion-plan.md`, `docs/decisions/ADR-0020/0027/0028`, `docs/constitution.md`, `docs/changelog.md`, `qmx-agents/examples/NATIVE_AGENT_SESSIONS.md`, `NATIVE_SESSION_DOCS_DRAFT.md`, and the `qmx-agents` and `qmx-control` package READMEs.
- Operator digest `.../scratchpad/digest/human.md`, covering 2026-10-12 08:13 to 2026-10-13 04:29.
- Current ledger and research on `plan/agent-system` (942198c1): `tracker/qma-v2/reviews/2026-10-13-forensic-session-audit.md`, `tracker/qma-v2/BACKLOG.md`, `trail/decisions.tsv`, `research/how/HOW-harness-surface.md`, `research/H1-sdk-facts.md`, and `tracker/agent-system/research/{01,19,20,24}`.
- Archived and superseded material, cited only as "what was said then": `archive/2026-10-13-wednesday-frame/{SUPERSEDED,HOW-WHY,review-opus}.md`.
- Memory files: `qmx-agentic-langgraph-shift`, `agent-system-map`, `qma-v2-design-session-rulings`, `branching-model-main-staging-integration`, `qmx-agent-sdk-effort`.

### What I Searched
- Grepped for: native_claude, ANTHROPIC_, subscription, Agent SDK, LangChain/LangGraph/Deep Agents, interrupt/approval, money/propose_order, delete/beside/staging/integration, host.py/DAEMON_SPAWN, hooks, OpenRouter, CLIProxy.
- Read in full: DESIGN.md, COPILOT.md, the key packets, ADR-0020/27/28, NATIVE_AGENT_SESSIONS.md, forensic audit §1–2, research 24 §1, §4, §6 and §7–10, and HOW-WHY §3 (Y01–Y45) and §4.
- The digest lines are very long. I used grep windows and read lines 54–68 directly.
- Not found: any Notion or Slack source. As far as I could tell, the docs ledger (DEC rows) does not exist as a separate file on this branch. Only ADR, AGENTS and constitution citations exist.

### Direct Evidence Found

**1. Why LangChain/LangGraph/Deep Agents were chosen (around 2026-10-04 to 2026-10-07)**
- Voice ledger, operator words, T2 L668/L708:
  - R-087 "opt out of bespoke QMA engine; use an existing mature SDK", quote "I think we are going to use... an external SDK".
  - R-088 "I think LangChain would be the best for this".
  - R-091: "the agentic system, you know, building it from scratch is going to take time".
  - F-15: building QMA from scratch was "completely now useless ... just a little bit of pride" (`rebuild/research/ledger-voice.md:99-101,288`).
- Chat ledger:
  - AG-16 (10-04) "Adopt the LangChain ecosystem" (M207).
  - AG-21 "Please don't try to invent anything" (M251).
  - AG-28 (10-06) "let the workflows that are in QMX use Deep Agents" (M432) (`ledger-chat.md:37,42,49`).
- Memory `qmx-agentic-langgraph-shift.md:11`, 2026-10-04: the operator said the agentic part "is proving to be a problem", so QMX switched to LangChain/LangGraph instead of building its own SDK.
- Audit evidence behind the switch (`rebuild/research/audit-code.md:19,177-182`, read-only Claude subagent, 2026-10-07):
  - "4,007-line `DaemonProcess` god class … 2,049 decision-ID references".
  - "three overlapping ways to reach a model".
  - "taskgraph/ … **and** LangGraph … glued by canonical_join.py … where the failing tests are".
- DESIGN.md (Claude, 2026-10-07, "approved in outline by the operator"):
  - §1 L11: the layer is "rebuilt as a thin layer on top of **LangChain Deep Agents**… QMX stops hand-building those".
  - §2 L25: "Adopt before building".
  - §2 L28-32: "Invariants survive as thin wrappers, never as a parallel runtime".
  - §3 L57 strategy: "**strangler**. New thin packages run beside the old daemon. Callers move one at a time, then old code is deleted. Code that is about to be replaced is not refactored."

**2. When they were dropped (2026-10-12)**
- Forensic audit §2.1 (`reviews/2026-10-13-forensic-session-audit.md:54`). Engines row: "Two SDKs: the Claude Agent SDK (its capabilities, never the CLI) and the OpenAI Agents SDK", ruled 15:16, 16:22 and 04:22. It supersedes "LangChain/LangGraph/Deep Agents (Oct 4)". The audit flags that this was a "**Proposal treated as settled**".
- Workflow engine row (`:57`): "Own graph and loop engine; LangGraph out" (16:22). It is flagged as a "Frustrated aside treated as ratified".
- Operator, digest L345 (around 15:38): "Now we are designing something based of claude agent SDK and OpenAI Agent SDK".
- Operator, digest L368 (16:22): "The name QMA belongs to the package being deleted. No, QMA is just quantum agents… we are just restructuring it. That's why I added the version 2."
- Current BACKLOG.md L8 puts "the agent harness (two engines…)" and "the deletion of the old agent code" in scope now.

**3. Native Claude recipe: bounded to subscription sessions, refuses `ANTHROPIC_*`**
Original author's record (Codex lane, undated, base `ecda9c06`), `qmx-agents/examples/NATIVE_AGENT_SESSIONS.md`:
- L20: Claude config is "Supplied text; dedicated native home; empty workspace; removed builtins; strict SDK MCP host callback; native subscription auth metadata".
- L28-35: "This is a **trusted pinned native-launcher configuration**, not OS isolation… Ordinary native tools need a separate enforceable worker boundary before admission: … no host home/repository/money storage/broker configuration, admin sockets…"
- L52-53: "accepts native `claude.ai` authentication in the dedicated home and rejects API/provider-token routing. QMX never reads a credential file."
- L88-89: "Missing/mismatched terminal evidence leaves an unknown pending native record, preventing automatic replay or paid fallback."
- L119: tests are fake-model only. L176-217: "No live proof has been run."

Related records:
- `NATIVE_SESSION_DOCS_DRAFT.md:27-29,56`: "QMX does not ingest native credentials or translate subscription tokens into API-provider credentials" and `paid_api_fallback: prohibited`. The file is labelled "DRAFT / NOT RATIFIED".
- ADR-0027 (draft, 2026-10-03) L40-45: native execution "narrowly reconsiders the foreign-runtime hosting cut… No existing credential/session home is opened, no API-key fallback is automatic, and live proof requires personal authentication".
- ADR-0028 (draft, 2026-10-04) L76-82: "Native Codex/Claude SDK sessions belong to `agent_session` workers, never BaseChatModel… to prevent double planning… subscription behavior remain unsupported."

Later rationale (2026-10-12/13 research, not the author's):
- `tracker/agent-system/research/01-agent-sdk-capability-audit.md:196-199`: inherited `ANTHROPIC_*` passes through unless scrubbed, and "A leaked operator variable changes who pays."
- Same file, §6 L240-252: terms say third parties may not "offer Claude.ai login". The allowed case is the unmodified binary under the user's own plan, and limits "assume ordinary, individual usage".
- `H1-sdk-facts.md:19-21,59` (Fact 4): QMX must not keep or inject a `setup-token`. The safe route is for the operator to run `/login` himself in the engine's own `CLAUDE_CONFIG_DIR`.

Operator's own words:
- 17:11: "I don't want to pay for API ever… for API I mean for claude and codex" (forensic `:66`, `:237`).
- Digest L377: "I don't plan on paying for Anthropic's API… 5x max plan… I plan on using that".
- Memory `qma-v2-design-session-rulings.md:19-21`: "No Anthropic API spend… Claude only through that subscription (the Agent SDK signed in with his plan)."
- BACKLOG.md L23 (10-13 evening): "Exactly ONE Claude Max account."

**4. Money-path admission is refusal-based, and proposals need the operator's signature**
- ADR-0020 (ratified 2026-08-29):
  - L24: "the money path is closed to agents. Nothing above a Bot touches the market (constitution L36)".
  - L34: a paper-only execution tool was rejected, which is "the ground for the AD-16/AD-28 money-path reachability barrier".
  - L50: an "act-level deny-list refuses every order, binding, sizing and promotion act at the Tool Registry".
  - L72: "refused at tool registration… not softened at runtime".
- Constitution L17: "Only a human may promote a registered artifact into the live zone… QMA-paper does not exist."
- DESIGN §5.7 L215: "order-capable tools are never in any agent's tool list. Agents can only *propose*; the operator signs in Portfolio."
- DESIGN §7.2 L270: a "Touches money" app "proposes only. Every order is signed by the operator."
- DESIGN §12 item 3 L477 (2026-10-07): "**Money-path barrier: port as is.** … small and correct… check every resolved LangChain/MCP tool at build time, and keep a check at invoke time."
- P08 L22-23: "`build_agent` refuses any spec that lists such a tool. The only allowed money tool is `propose_order`."
- Operator 2026-10-13 04:14 Q1: "Money, okay, the agent can access, but it's a read-only." It is enforced as an always-on hook (forensic `:84`, `:245`; BACKLOG L18).

**5. Why approvals were LangGraph interrupts**
- `rebuild/research/research-harness.md:308` (2026-10-07, "adopt, don't invent"): AD-20 Agent Bus maps to "Operator approval queue = HITL interrupts surfaced in UI". At `:302` the hook registry maps to `HumanInTheLoopMiddleware`.
- DESIGN §12 item 4 L478: "**Admission is an `interrupt_on` plus one backend check.** … the operator approves, before/after records are kept. The `AdmissionPipeline` hook dispatch is not ported."
- DESIGN §12b item 7 L497: "Anything with approvals uses a checkpointer."
- qmx-control README L11-12: "`interrupt_on` metadata… itself is not an authorization gate."
- Current HOW (`research/how/HOW-harness-surface.md:27,82`, 2026-10-13): "Nothing reads `meta.interrupt_on`… Approvals live in the LangGraph checkpointer, not in QMX… answered on `input()`."

**6. Sessions as append-only blocks with events, and no turn route or approvals table**
- Origin: the UI contract. `rebuild/research/ui-model-and-baseline-audit.md:160-171` says "A session is an append-only list of typed blocks (contract §7, BACKEND-REQUIREMENTS.md)… The UI shows only what the log holds… Sessions run for days… permissions are parked (10-04)."
- COPILOT.md §6 L105 (BMAD memlog): "*nothing exists until it is a file*… a crash loses nothing."
- DESIGN §8 L364 "copilot sessions: typed block log", and L366: "LangGraph Agent Server is not used. FastAPI plus in-process LangGraph is enough."
- P11 L18 lists sessions "create, list, append, stream", with no turn verb. P15 L20 maps the Copilot run onto blocks, and the operator drives it from `scripts/live/copilot_build_app.py`.
- Research 24 §1.5 (`tracker/agent-system/research/24-...:65-69`): "a route that starts a turn… none exist… an approvals record… answered on a script's stdin".
- HOW-WHY 4.2 (archived) gives the inferred reason: "Nothing in the record explains why tasks were left in memory; the inferred reason is that P15 only needed one live script process."

**7. Why the old daemon was kept alive (P16a, DESIGN §12c.1)**
- `rebuild/reports/p16-deletion-plan.md:46`: "**QMB host retirement is blocked.** `host.py:110` sets `DAEMON_SPAWN_MODULE = "qma.daemon"`… P16's import-only allowance in QMB cannot authorize this behavioral rewrite: require a separately approved caller-migration packet."
- DESIGN §12c item 1 L504-507 (Claude, 2026-10-09): the QMB CLI is rewritten to start `qmx_control`. "This is the one authorized change inside `qmb/`, limited to `qmb/src/qmb/doors/cli/` and its tests."
- §12c item 4 L515: "No data migration. The old daemon stores hold only test and fixture data."
- P16 L10-11 blast radius: "`qmb/`… Never delete anything there. You may only change an import line."
- Codex's P16b summary (pasted in the digest at L30): "**Kept:** Old experiment, graph, native-session, bus, memory, process/transport and plugin code with surviving callers or uncertain replacements."
- Research 24 §6.2 L154-155: after PR #49 the CLI delegates to qmx_control, but `host.py:104` and `_spawn_argv` remain. "PR #58 measured… that one entry point keeps about 110k of the 127k old lines alive. P16c may not edit `qmb/` beyond import lines."
- Research 24 risk 8 L234: "Only the operator can authorise that QMB edit (DESIGN.md:504-507)."
- BACKLOG B4 L159: about 113k lines remain, "kept alive by `qmb/src/qmb/doors/cli/host.py:104`".

**8. Constraints on deleting old code**
- DESIGN §3 L57 (strangler, above). P16 L25: "confirm it has zero production callers… Move any remaining callers… first." §12c item 6 L517: "Never lower thresholds."
- Operator, digest L368 (2026-10-12 16:22): "where do you build new one beside the old one? Switch over, then delete. I don't think we need to really like I told you that branching mechanism should really solve help us solve this".
- Same message: the target is "integration… staging… main", "deleting is the best because I don't think we need any", and "The old documents, we are going to archive them, not delete them".
- Forensic `:115` (Branch): "`rebuild/base` for now. `integration` isn't ready… Junk branches deleted only with his go."
- Forensic `:204` notes that the archived SHIPPING-PLAN 0a "deletes `qmx-agents/plugins/`… before anything replaces them… against Claude's own 'build beside, switch, then delete' (15:55)".
- Forensic open question 3 (`:278`) was left unanswered in that session: "Keep it until the harness passes, then delete in one PR."
- Then `trail/decisions.tsv` (2026-10-13 16:05:24): "destination is the harness coding-session prompt plus the old-code deletion sequence".
- BACKLOG L23 (10-13 evening): "Deletion follows integration → staging → main (main only by his click); QMA v2 lands in `rebuild/base` for now."
- Memory `branching-model…md:38`: "Deletion is irreversible… get his explicit go first. Never delete on inference."
- Prerequisites for deletion:
  - Research 24 risk 9 L235: "Losing the only Claude SDK recipe… Copy it first."
  - HOW-WHY F10 (archived): "`claude-agent-sdk` 0.2.163 is locked only because `qma-daemon` needs it. P16 deleting the daemon would drop the pin."
  - BACKLOG B3 confirms this.

**9. P06 router and OpenRouter**
- DESIGN §5.3 L121: "**The primary provider is CLIProxyAPI**". L151: "The test profile is OpenRouter… never the default."
- ADR-0028 L84-89: the "operator additionally authorized removal of only the historical OpenRouter host/adapter/image ban".
- Voice R-170: "Can I give you maybe open router, and you test with that."
- CLIProxy was dropped on 2026-10-12. BACKLOG L144: the router "was to replace the CLI proxy" (16:22).
- Digest L230 is a compaction summary in Claude's words, not the operator's: "CLIProxyAPI cloaking violates this" (Anthropic terms).

**10. P07 memory**
- Chat ME-04 (10-04, M306): "use the Hummus [Hermes] agent setup, so pluggable memory providers". This is ruling R-06.
- ADR-0028 L63-65: LangMem was not installed because "its store namespace is not authorization".
- Forensic `:92` (16:22): "SDK defaults first, with the pluggable layer kept (Hermes-style)."

**11. P20 hooks**
- DESIGN §11 L394-401 (operator additions, 10-07).
- Chat AG-23: "Claude Agent SDK has the best hooks" (M251).
- 2026-10-13: "Hooks now tell the agent, no, put it here" (10:02) and "an instruction and a hook are different" (04:14). The hooks baseline covers both Claude and Codex (forensic `:82`).
- BACKLOG L23: "Permission modes and hooks copied from the Claude Agent SDK, rebuilt on the OpenAI side."

### Indirect / Circumstantial Evidence
- **Reasons already graded by a prior why pass.** The archived HOW-WHY §3 (Y01–Y45) and research 24 §7–10 mark old reasons RESPECT or DROP for QMA v2.
  - Respected: one model path (Y01), one graph engine (Y02), neutral invariants (Y04), money check in QMX tool wrappers at call time (Y05), single journal writer (Y07), approval bound to exact content by the operator (Y08), `valid_path` hardening (Y09), one API with two doors (Y11), no Agent Server (Y13), recipe isolation and subscription checks (Y39, Y41), fakes in CI (Y22).
  - Dropped: CLIProxy (Y14), tier profiles (Y15), modes (Y18), the Hermes "at most one" rule (Y23), LangGraph SqliteStore (Y25), the recipe lockdown (Y40), the Codex driver (Y42).
  - These grades were made against the now-parked Wednesday PRD and should be re-grounded.
- **Incident-driven defensive code.** These come from PR bodies cited in HOW-WHY; I did not verify them in the PRs.
  - Y06 (PR #35): Deep Agents' automatic general-purpose sub-agent drops custom middleware, so it was given explicit guards. The qmx-agents README L38-39 confirms: "The general-purpose agent is explicitly defined to retain guards."
  - Y09 (PR #35): a Windows probe showed `/ARTIFA~1/` bypassed admission, so path rules were hardened.
- **Isolation and the engine choice.** Research 24 §4 L99: OpenAI Agents SDK hooks only observe, so blocking must sit in QMX tool wrappers on both engines. This suggests the P08 "middleware" placement does not carry over.
- **Security review (archived).** `review-opus.md:20-53` says one bearer token is shared by the operator, agents and mini apps, and broker credentials are readable by any same-user process. That makes the money barrier "against tool calls, not against arbitrary code". This is relevant to any two-engine harness regardless of frame.
- **Native recipe has never run live.** `trail/decisions.tsv` 16:19:51: "the only Claude SDK recipe has never run against a real model". `native-session-runtime-check.json`: `subscription_connection_verified: false`.
- **Alternative reading.** The `ANTHROPIC_*` refusal may be motivated mainly by preventing silent paid-API routing (author: "no paid fallback"). It may also be about terms compliance (later research). The author's text supports the first. Terms reasoning appears only in the 2026-10-12 research.

### Contradictions
1. **Foreign runtimes.**
   - ADR-0020 (ratified 2026-08-29, L31, L73) Cut "Host foreign agent runtimes (the Claude Agent SDK, OpenAI or LangGraph loops)" (DEC-0360) and revives it only "by a spine amendment".
   - ADR-0027/0028 (drafts, 10-03/04) and DESIGN (10-07) adopted LangChain/LangGraph and native SDKs without ratifying an amendment. ADR-0027/28 are `status: draft`.
   - The 10-12/13 ruling adopts the Claude Agent SDK and OpenAI Agents SDK. The changelog L309 still has GAP-0087 "bounded by the Cut on foreign agent runtimes".
2. **Native sessions.**
   - DESIGN §3 L48 (10-07): "Model proxy chain, `native_*` sessions, `proxy/` → **Replace** with the model router."
   - 2026-10-12/13 research says `native_claude.py` is "the only Claude SDK recipe" and must be copied before deletion (research 24 L235; BACKLOG B4).
3. **Primary provider.**
   - DESIGN §5.3 L121 (10-07): "The primary provider is CLIProxyAPI".
   - Operator 10-12 16:22: the router replaces CLIProxy (BACKLOG L144).
   - Separately, ADR-0027 L71-73 (10-03) already said "CLIProxyAPI instance is… not… proof of subscription eligibility".
4. **`propose_order`.**
   - P08 L23 (10-07): "The only allowed money tool is `propose_order`."
   - HOW-harness-surface Gotcha 9 (10-13, read in code, not run): "`check_descriptor` money gate refuses `propose_order` by name… The old code let it through only by Python type."
5. **Modes.**
   - COPILOT.md L3 and P24 L1: "operator rejected modes" (2026-10-09).
   - 2026-10-13 04:14 Q1: "copy how Claude Code handles permissions". The forensic audit (`:85`) flags this as conflicting.
   - BACKLOG L23 (10-13 evening): "Permission modes and hooks copied from the Claude Agent SDK".
6. **Recipe lockdown.**
   - The native recipe (`tools=[]`, no skills, sub-agents, plugins or hooks; NATIVE_AGENT_SESSIONS L46-47) existed because there was no enforceable worker boundary (L32-35).
   - Operator 10-12 10:02 and 10-13 04:14: the baseline is "the tools you have access to… that's the baseline", i.e. the same tools as Claude Code.
   - The reason for the lockdown (no OS isolation from money storage and broker config) is not shown as resolved anywhere.
7. **QMB edit authority.**
   - DESIGN §12c.1 (2026-10-09) authorizes editing `qmb/src/qmb/doors/cli/`.
   - P16 L10-11 and the P16c rule (per research 24 L155) forbid `qmb/` edits beyond imports.
   - So the leftover `host.py:104` survives, and research 24 L234 says only the operator can authorize the edit.
8. **Deletion timing.**
   - Archived SHIPPING-PLAN 0a deleted code first.
   - Claude 15:55 and the operator 16:22 said build beside, switch, then delete.
   - Forensic Q3 recommended keeping the old code until the harness passes, but this was never answered on record.
   - The 10-13 evening ruling ties deletion to integration → staging → main, while landing on `rebuild/base`. Whether "build beside" or "delete first" governs is not explicitly resolved.
9. **Memory provider count.**
   - P07 and DESIGN §5.4 use the Hermes rule of "at most one external provider" (from ME-04, 10-04).
   - Archived HOW-WHY Y23 marks it DROP in favour of per-agent binding. The 10-12 16:22 ruling says only "keep the pluggable layer".

### Gaps
- The P16c packet text is not in `rebuild/packets/`. The "no qmb edits beyond imports" rule for P16c comes only from research 24 L155 and PR #58 as cited there.
- NATIVE_AGENT_SESSIONS.md is undated, and the native-recipe lockdown has no operator ruling behind it. It reads as a Codex-lane safety choice under "attended operator instruction" (ADR-0027 L16).
- I found no document stating why no approvals table or turn route was built in P11/P15. Only the inference "P15 only needed one live script process" exists.
- The DEC-0341/0360 ledger text itself was not found on this branch. Only ADR, AGENTS and constitution summaries exist.
- The digest truncates messages at about 4,800 characters (forensic L8). Some operator rulings, such as the 16:22 "capabilities, not the CLI" message and the question-tool answers, are only in the raw transcript, which I did not read.
- No operator statement directly addresses whether the old LangChain `qmx-agents` code (as opposed to qma-daemon) must stay until the new harness passes.

### Additional Leads
- PR bodies to check (git/PR investigator):
  - #35: the Y06 GP-subagent guard and the Y09 `/ARTIFA~1/` admission-bypass incident.
  - #49: the QMB host migration.
  - #53: proxy/native-session slice; why the native files survived.
  - #58: the 110k-line anchor measurement.
  - #31, #33: P06/P07 live-smoke deferral.
  - #46: CI never ran on GitHub.
- `git log` of `qmx-agents/examples/NATIVE_AGENT_SESSIONS.md` and branch `native-subscription-sessions` / `task-6/native-sessions` (checkpoint `4d92bf21`), to date the recipe and its operator authorization.
- Raw transcript `transcript.jsonl` for the 2026-10-12 session, for the full 16:22 and 15:16 messages and the 04:14/04:22 question-tool answers. The forensic audit says it read them.
- `rebuild/research/2026-10-12-agent-system/{langchain-stack,memory}.md`, cited by research 01 and BACKLOG B40. I did not read them.
- `D:\Codex-Recovery\2026-10-04\integration-base.git`: the only full copy of MA02–MA05 (audit-code L15).
- `C:\Users\Mubarak\Desktop\QMX-session-for-Codex\BACKEND-REQUIREMENTS.md`: the origin of the typed-block session contract (P11 L8).
- `tracker/agent-system/research/19-two-sdk-study.md` §11 ("mismatch 1/2": two approval styles; OpenAI hooks only observe) and §13 (the LangGraph cost estimate).