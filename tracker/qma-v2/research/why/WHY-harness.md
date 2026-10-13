# WHY: the current agent runtime, and what still binds the two-engine harness

Path shorthand: **HS** = `D:/QMX-worktrees/harness-survey` (origin/rebuild/base 4eac8f69). **AS** = `D:/QMX-worktrees/agent-system` (plan/agent-system). **QA** = `HS/qmx-agents/packages/qmx-agents/src/qmx_agents`. Times are UTC and on 2026-10-12 unless marked 10-13. Newer operator rulings win. Anything under `AS/tracker/qma-v2/archive/` records only what was said at the time.

## The Question

Why does QMX's agent runtime have its current shape? That covers:
- the LangChain/LangGraph/Deep Agents `qmx-agents` copilot;
- the old QMA runtime (qma-daemon, qma-core, qma-wire);
- the native Claude Agent SDK subscription recipe;
- the P08 guards, money-path admission and budgets;
- the P06 spec and OpenRouter router, the P07 memory provider and the P20 hooks;
- the qmx-control session/blocks/events design, which has no turn route and no approvals table.

And which of those reasons still bind the new two-engine harness (Claude Agent SDK plus OpenAI Agents SDK behind one QMX permission/hook layer), or the planned deletion of the old code?

## The Code in Question

- `QA/guards/` (money_path, admission, journal, hooks, middleware), `QA/copilot.py` (`build_copilot`, `stream_turn`), `QA/router.py`, `QA/spec.py` (`build_agent`)
- `HS/qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_{claude,codex,sessions,boundary}.py` (`ClaudeSessionBackend`, `check_environment`)
- `HS/qmx-agents/packages/qmx-control/src/qmx_control/{service.py,server.py}` (`ControlService.sessions_append`, `OPERATIONS`, `interrupt_on`)
- `HS/qmb/src/qmb/doors/cli/host.py`

## What We Found

**Why LangChain/LangGraph/Deep Agents, and why they are now out**
- [Direct] The operator chose an existing SDK over a hand-built engine, around 10-04. His words: "I think LangChain would be the best for this" (R-088), "building it from scratch is going to take time" (R-091), and "Please don't try to invent anything" (AG-21). Sources: `HS/rebuild/research/ledger-voice.md:99-101,288`, `ledger-chat.md:37,42,49`, memory `qmx-agentic-langgraph-shift.md:11`.
- [Direct] A read-only code audit on 10-07 found a 4,007-line `DaemonProcess` god class and "three overlapping ways to reach a model". It also found taskgraph and LangGraph glued together "where the failing tests are" (`HS/rebuild/research/audit-code.md:19,177-182`).
- [Direct] DESIGN.md (10-07, "approved in outline by the operator") rebuilt the layer as "a thin layer on top of LangChain Deep Agents". Its rules: "Adopt before building", "Invariants survive as thin wrappers, never as a parallel runtime", and a strangler strategy where new packages run beside the old daemon (`HS/rebuild/DESIGN.md` §1 L11, §2 L25-32, §3 L57).
- [Direct] On 10-12/13 the engines became the Claude Agent SDK ("its capabilities, never the CLI") and the OpenAI Agents SDK, replacing LangChain/LangGraph/Deep Agents. LangGraph is also out as the workflow engine. Source: `AS/tracker/qma-v2/reviews/2026-10-13-forensic-session-audit.md` §2.1. The audit flags the engines row as a "Proposal treated as settled" and the LangGraph row as a "Frustrated aside treated as ratified". The 10-13 04:22 ruling ("harness first") re-confirms the two engines.

**Old QMA runtime and its deletion**
- [Direct] ADR-0020 (ratified 2026-08-29) created qma-core, qma-daemon and qma-wire, with the daemon as "the only process that runs anything and the sole writer". The same ADR **cut** "Host foreign agent runtimes (the Claude Agent SDK, OpenAI or LangGraph loops)" (DEC-0360). That cut revives "only by a spine amendment" (`HS/docs/decisions/ADR-0020*.md` Options 2 and 8, Consequences). I spot-checked this.
- [Direct] "No data migration. The old daemon stores hold only test and fixture data; the operator never ran the product on real work" (DESIGN §12c item 4, L515). The closed PRs #23 and #24 say the old stack never ran real inference.
- [Direct] The old code stays alive because `qmb/src/qmb/doors/cli/host.py:104` still sets `DAEMON_SPAWN_MODULE = "qma.daemon"`. P16 may not edit `qmb/` beyond import lines, and "only the operator can authorise that QMB edit". Sources: `HS/rebuild/reports/p16-deletion-plan.md:46`, DESIGN §12c.1 L504-507, `AS/tracker/agent-system/research/24-*.md` risk 8. BACKLOG B4 puts the remainder at about 113k lines.
- [Direct] PR #53 kept the native-session files because "native-session implementations still have callers in retained daemon services and examples". DESIGN §12c slice 5 had planned to delete them.

**Native Claude recipe**
- [Direct] Its author wrote that it is "a **trusted pinned native-launcher configuration**, not OS isolation". The doc goes on: "Ordinary native tools need a separate enforceable worker boundary before admission: read-only base, scratch workspace/native home only, provider HTTPS egress, no host home/repository/money storage/broker configuration, admin sockets or localhost/private-network control surfaces." Source: `HS/qmx-agents/examples/NATIVE_AGENT_SESSIONS.md:28-35`, spot-checked. That is the stated reason for `tools=[]`, no agents/skills/plugins and empty setting sources (same file L46-53).
- [Direct] The recipe enforces subscription only, with no paid fallback. It "rejects API/provider-token routing. QMX never reads a credential file" (L52-53). Missing terminal evidence prevents "automatic replay or paid fallback" (L88-89). The `check_environment` docstring reads "Never read credentials or silently select API auth".
- [Direct] The recipe has never run live: "No live proof has been run" (`NATIVE_AGENT_SESSIONS.md` L176-217). The runtime check records `subscription_connection_verified: false`.
- [Direct] On 10-07 DESIGN marked `native_*` for **Replace** with the model router (§3 L48). The survival map gives every `native_*` file the same verdict (rows 160-165). Research on 10-12/13 calls it "the only Claude SDK recipe… Copy it first" (research 24 risk 9).
- [Direct] Operator: "I don't want to pay for API ever… for API I mean for claude and codex" (17:11). The 10-13 evening ruling allows "Exactly ONE Claude Max account" (`AS/tracker/qma-v2/BACKLOG.md` rulings table).

**P08 guards and money path**
- [Direct] The money-path barrier is inherited planning law, not an incident fix. Sources: ADR-0020 L24, L34, L50 and L72 ("refused at tool registration… not softened at runtime"); `docs/constitution.md:17`; the qma-core docstring from commit 54f159ba ("Paper is an account role on a real venue, never a sandbox"); `qma-daemon/FAILURES.md` FR-22 to FR-24; DESIGN §12 item 3 ("port as is… small and correct"); and P08: "The only allowed money tool is `propose_order`."
- [Direct] Operator, 10-13 04:14: "Money, okay, the agent can access, but it's a read-only." He wants it enforced as an always-on hook (forensic §2.3; BACKLOG rulings).
- [Supported] The `propose_order` exemption works only by Python type. `check_tool` skips the check for the two local classes; everything else goes through `check_descriptor`, which splits names on `_` and so refuses `propose_order` by name. Sources: `QA/guards/money_path.py:240-279` (spot-checked) and the `QA/spec.py:288` comment "Never trust a remote tool by name or annotations". Code-read only in HOW Gotcha 9 (`AS/tracker/qma-v2/research/how/HOW-harness-surface.md:142`). Nobody has run it.
- [Direct] Three guard rules came from incidents (all from the PR #35 body):
  - A Windows probe showed `/ARTIFA~1/` bypassing artifact admission. Short-name forms are now rejected; see also the `admission.py:40-42` comments.
  - "Deep Agents' automatic general-purpose agent does not inherit custom middleware", so the general-purpose agent is defined explicitly with guards.
  - Journal hooks shared the router's mutable run context. The PR says regressions were "observed failing before the corrections".
- [Direct] The journal is "One serialized, append-only evidence writer per run volume" (`QA/guards/journal.py:1`). DESIGN's rule zero: "Each file has exactly one writer process" (DESIGN L314). ADR-0020 adds "one sole writer make[s] replay and audit exact" (DEC-0305).

**P06 router, P07 memory, P20 hooks**
- [Direct] P06 made CLIProxy the daily provider and OpenRouter the test profile only (DESIGN §5.3 L121, L151). Neither live smoke ran (PR #31). Operator, 16:22: the router "was to replace the CLI proxy". CLIProxy is now rejected (BACKLOG Rejected table). `router.py:111` says "Windows credentials are authoritative".
- [Direct] P07 follows the operator's "pluggable memory providers" (Hermes-style; ME-04, 10-04). The latest position: "SDK defaults first, with the pluggable layer kept" (forensic §2.3, 16:22). Global memory writes are denied by default and go through an approval hook (PR #33).
- [Direct] P20 hooks came from the operator's additions to DESIGN §11 (10-07). One incident fix came after: `apps_test` advanced the app road, so hooks now pin `stage="tests"`. Sources: commit e2d199c3, PR #44, and PR #47 ("A Copilot proof step must never activate code before publish approval"). Operator, 10-13 04:14: "an instruction and a hook are different". Hooks must cover both engines (forensic §2.3; BACKLOG: "Permission modes and hooks copied from the Claude Agent SDK, rebuilt on the OpenAI side").

**qmx-control sessions**
- [Direct] Sessions come from the UI contract. "A session is an append-only list of typed blocks… The UI shows only what the log holds… Sessions run for days" (`HS/rebuild/research/ui-model-and-baseline-audit.md:160-171`). `sessions_append` says "history is never rewritten". The store has only the `sessions`, `blocks`, `work` and `events` tables (`service.py:121-126`, spot-checked).
- [Direct] "These descriptors wire both doors; there is no second implementation to drift" (`server.py:27`). DESIGN §8 L366: "LangGraph Agent Server is not used. FastAPI plus in-process LangGraph is enough."
- [Direct] Approvals were meant to be LangGraph interrupts. "Admission is an `interrupt_on` plus one backend check" (DESIGN §12 item 4). "Anything with approvals uses a checkpointer" (§12b item 7). The qmx-control README calls `interrupt_on` metadata "not an authorization gate". The P11 packet lists sessions as "create, list, append, stream", with no turn verb.
- [Direct] The `/sign` route's docstring says "Operator-only door: never exported as an agent MCP tool". It uses the same bearer token as every other route (`server.py:93-117,178-196`, spot-checked).

## What We Can Reasonably Infer

- [Inferred] The P06-P20 rebuild seems to have had no recorded review. PRs were self-merged within seconds and none has review comments. That suggests the code and PR bodies carry more of the rationale than any deliberation does.
- [Inferred] The missing turn route and approvals table look like scope deferral, not a design decision. PR #32 put Copilot integration in P15. P15 ran the copilot from one script (`scripts/live/copilot_build_app.py`), and its approvals were answered on stdin. The archived HOW-WHY 4.2 reached the same reading: "P15 only needed one live script process". No document gives a reason.
- [Inferred] The native recipe's lockdown seems to have been the Codex lane's own safety choice. It was made under ADR-0027's draft "narrow reconsideration" of the ADR-0020 cut, and no operator ruling backs it. The author ties the lockdown to the missing worker boundary, not to Anthropic's terms.
- [Inferred] "Approval" means two unconnected things today. One is the in-process `AdmissionGate.approve(principal="operator")`, where the principal is a plain string that any caller can supply. The other is LangGraph interrupts shown as `permission` blocks. That reads as two packets landing separately, not as one design.
- [Inferred] The money barrier probably only covers tool calls. An archived review says that on `rebuild/base` an agent `Bash`/`shell` can read keyring secrets, and that REST, MCP and the sign door share one token. It concludes the barrier works "against tool calls, not against arbitrary code" (`archive/.../review-opus.md:27,49,55`). I found nothing newer that resolves this.

## Competing Hypotheses

1. **Why the native recipe was locked down.** It is probably more than one reason; none excludes the others.
   - (a) No OS worker boundary existed. This is Direct, in the author's text.
   - (b) To stay inside the ADR-0020 foreign-runtime cut that ADR-0027 only "narrowly" reopened. This is Supported (ADR-0027 L40-45).
   - (c) Anthropic terms compliance. This is Speculative as an original motive: it appears only in research written on 10-12 (`research/01` §6).
2. **Why the native sessions were dropped on 10-07 in favour of CLIProxy plus the router.**
   - (a) DESIGN wanted one model path, and Deep Agents needs a `BaseChatModel`. ADR-0028 L76-82 says native sessions are "never BaseChatModel".
   - (b) The recipe had never run live.
   - (c) CLIProxy looked cheaper. No document chooses between these.
3. **Whether `ANTHROPIC_*` refusal is about cost or terms.** The author's text supports cost: "no paid fallback". Research on 10-12 adds terms and "who pays". Both now fit the operator's ruling, so they need not compete going forward.
4. **Whether deletion waits for the harness.** The 15:55/16:22 position is "build beside, switch, then delete". Forensic open question 3 recommended "keep it until the harness passes", but the operator never answered it. BACKLOG puts deletion "in scope now".

## What We Don't Know

- Why native sessions were built on 10-04 and dropped on 10-07. No commit, PR or DESIGN line says. The raw 10-04 to 10-07 transcripts were not read.
- Whether the operator ever saw or approved the recipe lockdown. I searched the ledgers, digest, BACKLOG and forensic audit and found no ruling.
- Whether the Agent SDK can sign in with the Max subscription inside a dedicated `CLAUDE_CONFIG_DIR`. It has never run live. Likewise, BASELINE lists it UNVERIFIED that the OpenAI Agents SDK can use ChatGPT sign-in (forensic §2.2).
- What "money is read-only" means for `propose_order`, which writes a proposal into Portfolio. The 04:14 ruling does not say.
- Whether "copy how Claude Code handles permissions" (04:14) brings back permission modes. Forensic open question 1 is unanswered, though the evening BACKLOG line says "Permission modes… copied".
- The full text of DEC-0341 and DEC-0360. Only ADR, constitution and changelog summaries exist on these branches.
- No ticket tracker, team chat, observability, error tracking or analytics data exists. QMX has never run in production.
- A citation note: the design-docs investigator cited research 24 at L234-235. The same risks sit at L345-346 in the file I read, so I cite them by risk number.

## Sources Consulted

| Category | Searched? | What |
|---|---|---|
| Source control (git, PRs) | Yes | Investigator report plus my spot checks: `git -C HS rev-parse`; `money_path.py:236-279`, `spec.py:280-292`, `admission.py:84-90`, `server.py` (bearer, `/sign`), `service.py:121-126`, `journal.py:1` |
| Design docs and ADRs | Yes | Investigator report plus my reads of ADR-0020 (Options, Consequences), `NATIVE_AGENT_SESSIONS.md:25-56`, the forensic audit §2 and §6, BACKLOG rulings, Rejected and Closed tables, research 24 §6 and risks, `HOW-harness-surface.md:142,163`, archived HOW-WHY Y07/Y08/Y39/Y40 and review-opus |
| Issue / ticket tracker | Not separately | Only GitHub PRs, via source control. No Linear/Jira |
| Team chat | No MCP | The operator's session digest and ledgers stand in for it (design-docs investigator) |
| Infrastructure observability | None exists | Never run in production |
| Error tracking | None exists | Same |
| Product analytics | None exists | Same |

## Confidence Summary

- **High (Direct):**
  - the money barrier's origin and its "port as is" status;
  - subscription-only Claude and no paid API;
  - the author's own reason for the native recipe's lockdown;
  - the three incident-driven guards (short names, guarded general-purpose agent, hook stage pin);
  - the origin of the append-only blocks design;
  - one API with two doors;
  - no data migration;
  - the QMB `host.py:104` anchor;
  - ADR-0020's cut on foreign runtimes, still never amended.
- **Medium (Supported or Inferred):**
  - the missing turn route and approvals table were scope deferral;
  - the lockdown was a lane choice, never ratified;
  - the barrier stops tool calls but not arbitrary code.
- **Low or Unknown:**
  - why native sessions were dropped on 10-07;
  - whether subscription login works live;
  - what "read-only money" means for `propose_order`;
  - modes;
  - deletion timing.

---

## Constraints that bind the new harness

Keep = carry the reason forward as-is. Drop = the reason no longer holds. Re-decide = the reason holds but the current form conflicts with a newer ruling, or needs an operator call.

| Constraint | Binds | Verdict | Tier | Source |
|---|---|---|---|---|
| **Money-path barrier.** Order, sizing, binding and promotion acts are refused at tool build and again at call time. Paper counts as real. | both | **Keep.** Put it in QMX's own tool wrappers on both engines, because OpenAI hooks only observe (research 24 §4). It must also gate Claude built-ins (Bash, Write). A descriptor gate does not see them, and keyring reads by `Bash` stay open until there is process or account separation. | Direct (rule); Inferred (gap) | ADR-0020 L24-72; DESIGN §12 item 3; 10-13 04:14 ruling; review-opus (archived) |
| **`propose_order` exemption** | harness | **Re-decide.** Copying `check_descriptor` alone refuses it by name, so it needs an explicit exemption that does not depend on the name. Also ask the operator whether "read-only money" still allows proposals. | Supported (code-read, not run) | P08 L23; `money_path.py:240-242`; HOW Gotcha 9 |
| **Only the operator can answer approvals or sign; the shared bearer token** | harness | **Keep the intent, re-decide the mechanism.** Today, "operator-only" for `/sign` means only that it is left out of OPERATIONS. It takes the same token as agent-reachable routes, and `approve` checks a principal string. The harness needs an operator credential that agents and apps cannot hold. | Direct (intent); Inferred (weakness) | `server.py:93-196`; `admission.py:84-88`; review-opus L27, L337 (archived) |
| **One writer per journal/DB file** | harness | **Keep.** It now matters more: SQLite 3.50.4's WAL bug, plus one connection per call in qmx-control. | Direct | ADR-0020 DEC-0305; DESIGN L314; `journal.py:1`; BACKLOG B1 |
| **Claude by subscription only.** No token storage, no reading credential files, no paid fallback, `ANTHROPIC_*` refused, exactly one Max account. | harness | **Keep.** Copy `check_environment` before deleting it. Live login is unproven. | Direct | operator 17:11; BACKLOG evening ruling; NATIVE L52-53, L88-89; H1 Fact 4 |
| **Isolate QMX's Claude home** (its own `CLAUDE_CONFIG_DIR`, `setting_sources=[]`, never the operator's `~/.claude`) | harness | **Keep.** The isolation (Y39) is a separate question from the lockdown (Y40). | Direct | NATIVE L20; operator 15:01 ("I can't have the same things across"); forensic §2.3 |
| **Native-recipe lockdown vs. the "same tools as Claude Code" baseline** | harness | **Re-decide. This is the sharpest conflict.** The lockdown (`tools=[]`, no skills, agents, plugins or hooks) existed because there was no enforceable worker boundary (Direct, NATIVE L28-35). It was never an operator ruling. The operator's baseline (10:02, re-stated 10-13 04:14 and 04:22) is the full Claude Code toolset, and he rejected default sandboxes (16:22). Lifting it safely needs three things. First, the money barrier and hooks must gate built-in tools as well as QMX tools, on both engines. Second, broker and keyring secrets and the control token must be out of the agent process's reach: the "process separation centralised" from 03:55, or a low-rights account. Otherwise the operator must accept in writing that the barrier stops tool calls but not arbitrary code. Third, a live test must show a money refusal against `Bash` as well as tool names. | Direct (why); Inferred (lift conditions) | NATIVE L28-35, L46-53; forensic §2.1, §2.3, §6 Q5; review-opus L49-55 (archived) |
| **Approvals bound to exact content** (operator principal, content and before-hash re-checked) | harness | **Keep the rule. Replace the in-memory and LangGraph-checkpoint state with a durable approvals record and an answer route.** Today they are answered on a script's stdin. | Supported (code-read; archived Y08) | `admission.py:84-111`; research 24 §1.5 |
| **Append-only typed block log** for sessions that run for days | harness | **Keep.** Re-decide which store is the truth (blocks vs. SDK items vs. journal), and add the missing turn, cancel and approval routes. | Direct (origin); Inferred (gaps were deferral) | ui-model audit L160-171; `service.py:121-126`; research 24 §1.5 |
| **One API with two doors** (OPERATIONS feeds both REST and MCP) | harness | **Keep.** Note that `interrupt_on` meta is read by nothing and is not an auth gate. | Direct | `server.py:27`; qmx-control README L11-12; HOW L27, L82 |
| **Windows path hardening** (DOS short names, stripped suffixes) | harness | **Keep the defence and generalise it.** The 03:55 ruling makes QMX platform-neutral, so add per-OS aliasing rules. Also re-decide `router.py:111` "Windows credentials are authoritative". | Direct (incident) | PR #35; `admission.py:40-42`; forensic §2.3 Platform |
| **Guarded sub-agents** (no sub-agent may run without the parent's guards) | harness | **Keep the principle; drop the Deep Agents-specific fix.** Re-verify the principle on both SDKs' sub-agent and handoff paths. | Direct (incident) | PR #35; `spec.py:444` |
| **Strangler: build beside, switch, then delete** | deletion | **Keep.** When to delete needs one operator answer (forensic Q3 is unanswered). Old docs are archived, not deleted. Deletion goes integration → staging → main, and main moves only by his click. | Direct | DESIGN §3 L57; operator 16:22; BACKLOG evening ruling; branching memory |
| **Copy the recipe and pins before deleting** | deletion | **Keep.** `claude-agent-sdk` is pinned only by qma-daemon, and `native_claude.py` holds the only tested isolation code. | Direct | research 24 risk 9; BACKLOG B3, B4 |
| **QMB edit authority** (`host.py:104`, which keeps about 113k lines alive) | deletion | **Re-decide; operator only.** DESIGN §12c.1 authorized edits only in `qmb/.../cli/`, while P16 forbade anything beyond imports. Removing the anchor needs his explicit go. | Direct | p16-deletion-plan L46; DESIGN L504-507; research 24 risk 8 |
| **No data migration** | deletion | **Keep.** Recheck that nothing real has run since 10-09; I found no sign that it has. | Direct | DESIGN §12c item 4; PRs #23, #24 |
| **ADR-0020's ratified cut on foreign agent runtimes** (DEC-0360), never amended | both | **Re-decide formally.** Both new engines are exactly what the cut names. ADR-0027 and ADR-0028 are drafts, and the changelog's GAP-0087 still cites the cut. The operator's 10-12/13 rulings override it in practice. The spine still needs a recorded amendment so future agents don't read the cut as current law. | Direct | ADR-0020 Option 2, Consequences; ADR-0027/28 status draft; changelog L309 |
| **CLIProxy / OpenRouter test-only** (P06) | harness | **Drop.** The router now balances sessions and usage across the Claude subscription, an OpenRouter key and other compatible providers. | Direct | BACKLOG Rejected table; evening ruling; forensic §2.2 |
| **Memory "at most one external provider"** (P07) | harness | **Re-decide.** Keep the pluggable layer; SDK defaults come first. | Direct (layer); Unknown (count) | forensic §2.3 Memory; archived HOW-WHY Y23 |
| **Hooks never advance live app stages** (P20) | harness, later | **Keep** for when mini-app plugins return. Hooks are enforcement on both engines. | Direct | PR #44, #47; operator 10-13 04:14 |
| **Permission modes** | harness | **Re-decide.** The 10-09 "no modes" ruling conflicts with "copy Claude Code permissions" (04:14) and the evening BACKLOG line. | Direct (both rulings) | COPILOT.md L3; forensic §6 Q1; BACKLOG |
