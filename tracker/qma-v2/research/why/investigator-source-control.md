### Source
Source control for MubarakHimself/QMX: git history read at D:/QMX-worktrees/harness-survey (origin/rebuild/base 4eac8f69), gh PR bodies, comments and reviews, in-repo docstrings and comments, test names, `rebuild/packets/P*.md`, `rebuild/reports/survival-map.md` (P05) and `rebuild/reports/p16-deletion-plan.md` (P16a). For DESIGN.md I read only commit messages and diffs. Its content belongs to the design-docs investigator.

### What I Searched
- `git log --oneline origin/rebuild/base`; `git show -s/--stat` on all listed commits (e40627c5, fd12459c, c0c781ca, 7289e13b, 5d645b67, 3512ae3d, f9a0c1d9, af932192, e2d199c3, 9eb263c9) and on aa7b68fc, af41853a, 318cbece, a80e1855, 91b88959, e27a5136, 54f159ba, 6e19f52d.
- `git log --follow` on every `qmx_agents/guards/*.py`, plus copilot.py, router.py, spec.py and tasks.py. History of native_*.py and the NATIVE* examples. `git log -S'/sign"'`, `-S'Operator-only door'`, `-S'stream_turn'`, `--all -S'subscription_required'`. `git branch -r --contains e40627c5`.
- `gh pr view` on #21, #23, #24 (closed pre-rebuild review PRs), #31, #32, #33, #35, #44, #47, #48, #49, #52, #53, #58, #59, #63. `gh pr list --state all`.
- Read in full: native_boundary.py, native_claude.py, native_composition.py, native_configuration.py, the head of native_sessions.py, qmx-agents/examples/NATIVE_AGENT_SESSIONS.md, the guards money_path, parent_surfaces and middleware modules, the head of admission.py, the heads of hooks.py and journal.py, copilot.py, qmx_control/server.py, the session parts of service.py, QMB host.py lines 90-125 and 1775-1836, and the headers of the old daemon hooks modules.
- Grep for comments in router.py and spec.py, test names in tests/test_guards.py, test_hooks.py and test_copilot.py, `CREATE TABLE` in qmx-control, and callers of `check_descriptor`, `qma.core.barriers`, `stream_turn` and `build_copilot`.

### Direct Evidence Found

**1. Money-path barrier: inherited rule, not an incident fix.**
- The guards money_path.py traces back with `--follow` to 54f159ba "story 44.5: Tool Registry act-level money-path denial" and 6e19f52d "story 40.6: default-deny parent surfaces" (Mubarak, 2026-09-01).
- The original qma-core docstring (54f159ba) says: "Act-level money-path deny-list constants (FR-Q09, FR-Q42; DEC-0315) … Nothing — configuration, plugin declaration, Role, Mission, hook, toolset, tool_adapter, check_fn, or capability rung — may widen this set or lift a match … Paper is an account role on a real venue, never a sandbox that makes an act safe."
  - That last sentence explains why the `paper_`/`live_`/`demo_` prefixes are stripped in `_normalize_act_token`.
- qma-daemon/FAILURES.md (same commit) records three failure modes:
  - FR-22: "the deny-list is code, not a setting … QMA has no execution tool at any account role, paper included."
  - FR-23: "An MCP server advertising one money-path tool is refused whole."
  - FR-24: "QMA mints no promotion command and no money-path value. A human promotes outside QMA."
- The P05 survival map (invariants table) says: "validate every resolved LangChain/MCP tool at build time and retain an invocation boundary … Agents receive read/propose tools; the operator's separate execution path signs every order. Replacing the tool registry must preserve its deny checks."
- P08 packet: "`build_agent` refuses any spec that lists such a tool. The only allowed money tool is `propose_order`. It writes a proposal for the operator to sign and never sends an order."
- PR #35 (P08, merged 2026-10-07 23:43, no reviews or comments): "A spec that resolves an order-capable tool fails before model construction; every invocation checks the barrier again … retain the closed money-act/parent-surface vocabulary without coupling the new package to old QMA refusal/wire types."
- Later changes:
  - 7289e13b (Codex, 10-08, P18) added `BrokerOrderProposalTool`: "Trusted local Portfolio writer, substituted for the broker MCP proposal."
  - c0c781ca (P14, 10-08) added the `create_order` alias and split out `check_descriptor`: "The same resolved barrier applies to LangChain and hosted MCP tools." qmx_apps/supervisor.py:473 and :671 also call it, so the barrier covers mini-app MCP tools as well, not just agents.
  - spec.py:288 comment: "Never trust a remote tool by name or annotations. Only the local concrete writer receives the proposal exception in the barrier."

**2. Admission backend: one incident-driven fix.**
- PR #35: "A native Windows probe demonstrated that `/ARTIFA~1/` bypassed artifact admission before the correction; the same probe is refused afterward. Reject short-name forms on every backend."
- admission.py:40-42 comments: "Win32 strips these suffixes, which can disguise protected paths." and "DOS short names can alias a protected directory on Windows volumes."
- Also from PR #35:
  - "Deep Agents' automatic general-purpose agent does not inherit custom middleware. Supply an explicit guarded `SubAgent`." This is echoed at spec.py:444.
  - "Use `wrap_model_call` to record successful responses before HITL can pause."
  - "Journal hooks share the router's mutable run context … Both cases have regressions observed failing before the corrections."
- `AdmissionGate.approve` docstring: "Called by the authenticated operator service, never exposed as an agent tool."
- Survival map: "A backend wrapper on `/artifacts/` and definition writes must enforce the checks even when REST/MCP bypass the agent."

**3. P20 hooks: one incident-driven fix.**
- 9eb263c9 (10-08 23:08) first version: `result = self.service.apps_test(app_id)` with the comment "A generic success flag cannot prove which immutable version was tested."
- e2d199c3 (10-09 00:47, after PR #44 opened) "Use versioned road evidence without advancing live stages" replaced that with an evidence lookup plus `apps_test(..., stage="tests")`. New comment: "apps_test advances the road. Never advance sandbox/shadow from a hook."
- PR #44 body: "explicitly pins `stage=tests` so checking tests cannot advance sandbox/shadow or trigger publication."
- PR #47 (P15): "Prevent Copilot apps_test from automatically promoting Shadow to Live: its hooks force explicit publication, so apps_publish always reaches the approval interrupt." hooks.py:78 comment: "A Copilot proof step must never activate code before publish approval."

**4. Native Claude/Codex subscription recipe: pre-rebuild, never run live, slated for replacement.**
- fd12459c and e40627c5 (Mubarak, 2026-10-04) came before the rebuild, which started with c12a5dd7 on 2026-10-07.
- NATIVE_AGENT_SESSIONS.md:
  - "This increment replaces that checkpoint's blanket refusal with a narrow supplied-text configuration."
  - "No live subscription connection, login, account-status call or model call was performed … This is a **trusted pinned native-launcher configuration**, not OS isolation."
  - "Ordinary native tools need a separate enforceable worker boundary before admission."
  - "QMX owns job identity, grants, authoritative journal and domain effects. The native harness owns its inner loop."
  - "Missing/mismatched terminal evidence leaves an unknown pending native record, preventing automatic replay or paid fallback."
  - "No live proof has been run."
- `check_environment` docstring: "Inspect variable names only. Never read credentials or silently select API auth." It raises `subscription_required` if any ANTHROPIC_*, OPENAI_API_KEY, CLAUDE_CODE_USE_BEDROCK/VERTEX/FOUNDRY, OAuth-token or proxy/CA variables are present.
- `_ClaudeSDKLifecycle` docstring: "tools=[] removes builtins; allowed_tools alone is not a security boundary. strict_mcp_config excludes discovered servers; empty setting sources and disabled hooks/auto-memory prevent user/project configuration expansion … No subagents."
- `ClaudeSessionBackend` docstring: "The review is an operator assertion after native login, not a substitute for QMX grants or an OS sandbox … No daemon configuration accepts an allow-all flag."
- `native_composition` allows exactly one operation: "Native supplied-text composition supports corpus metadata reads only."
- Survival map rows 160-165 give every native_* file the verdict "**replace**: init_chat_model + router; ModelFallbackMiddleware / ModelRetryMiddleware | P06".
- P16a plan: "Wrong model/credential routing or native-session cutover can leak credentials or lose in-flight turns."
- PR #53 (P16b proxy slice): "Kept: native-session implementations still have callers in retained daemon services and examples." The blockers it names are `domain_tools.py` (imports native_composition and native_configuration), `provider_config.py`, and `examples/native_session_proof.py`.
- Result: the native files still exist at 4eac8f69, although DESIGN §12c slice 5 was "proxy and native sessions".

**5. Old daemon is disposable as data.**
- DESIGN §12c item 4 (af41853a, 2026-10-09; commit author Codex, Co-Authored-By Claude Opus 5.5): "**No data migration.** The old daemon stores hold only test and fixture data; the operator never ran the product on real work."
- Closed pre-rebuild PRs #21, #23 and #24 (closed 2026-10-07 12:17) say the old stack never ran real inference. #24: "No actual external provider/native-session inference, connected UI, Linux execution, remote service, endurance … is established." #23: "Inference … are scripted/synthetic fixtures."

**6. qmx-control shape: OPERATIONS, sessions, the `/sign` route.**
- server.py:27: "These descriptors wire both doors; there is no second implementation to drift." MCP tools get `meta={"interrupt_on": destructive}`.
- P11 packet: "Destructive tools are flagged for `interrupt_on`."
- `/api/apps/{app_id}/sign` was added in c0c781ca (P14) with the docstring "Operator-only door: never exported as an agent MCP tool." It uses the same bearer token as every route, and `road.signing_key(token)` is derived from that token.
- The session store has only `sessions`, `blocks`, `work` and `events` tables (service.py:121-126). There is no approvals table. `sessions_append`: "Append a typed block; history is never rewritten."
- The P11 packet listed "copilot sessions: create, list, append, stream", so there is no turn or run endpoint.
- `stream_turn` and `build_copilot` are called only from qmx_agents/copilot.py, tasks.py and scripts/live/copilot_build_app.py. No REST route runs a turn or resumes an interrupt. Approvals exist only as `permission` session blocks plus LangGraph checkpoint interrupts.
- PR #32 (P11): "Library FTS/content-addressed storage and Copilot/agent integration belong to P22/P15."

**7. P06 router and spec.**
- P06 packet: "cliproxy, the default daily provider", plus the daily (cliproxy) and test (OpenRouter) profile tables. "Pin exact model ids, never `~…-latest` aliases." Keys come from `qmx/<provider>` in Credential Manager.
- 5d645b67 (Mubarak, 10-07) "rebuild: P06 default OpenRouter model tiers". 318cbece (10-07) "CLIProxy as daily provider, OpenRouter test profile".
- PR #31 (merged about 20s after creation, no reviews):
  - "The operator explicitly authorized merging with both real-key smokes deferred … Neither live smoke was run; no CLIProxy marker PASS is claimed."
  - "If it fails, inspect `upstream.claude.disable-claude-cloak-mode`."
  - "Harness profiles are model-level, process-wide startup registrations, not per-run spec arguments."
- router.py:111: "Windows credentials are authoritative; only CI may use environment keys."
- spec.py:251-252: `interrupt_on requires a checkpointer`.

**8. P07 memory.**
- PR #33: "Global writes/deletes deny by default and use an asynchronous approval hook. Automatic hooks run only for the primary agent."
- Survival map: "Primary-agent-only automatic writes and approval for global writes are new DESIGN rules … do not infer them from current `_before_memory_write` (which sets `operator_required=False`)."

**9. Old daemon hooks still in the tree** (`hooks/{ledger_gate,registry,source_bounds,timeouts}.py`).
- registry.py docstring: "Hooks are the single enforcement and control surface — never optional (AD-10; FR-Q30/FR-Q31; CT-41; DEC-0309, DEC-0339)."
- ledger_gate.py: "never discards evidence … quarantine the entry verbatim — never discard (L39; DEC-0309)." Its quarantine rule was ported into guards/experiments.py (3512ae3d, §12c item 2).
- PR #52: "the remaining old hook dispatcher cannot be removed without changing those retained callers."

**10. QMB host.py.**
- PR #49 (§12c.1) switched start/status/stop to `control_host` (`python -m qmx_control`).
- `DAEMON_SPAWN_MODULE = "qma.daemon"` (line 104) and the legacy helpers remain: "legacy helpers … remain because the out-of-scope `qmb/examples/host_lifecycle_usage.py` imports them."

### Indirect / Circumstantial Evidence
- **No PR has any review or comment.** Of the PRs I viewed, only #21, #23 and #24 have comments ("@codex review" requests). P06-P20 were self-merged by MubarakHimself within seconds of opening. Review apparently happened outside GitHub (Claude orchestrator in chat), so rationale lives in PR bodies, packets and DESIGN.
- **Authorship pattern.** Implementation commits are by "Codex <codex@openai.com>". Packet and DESIGN commits are by Mubarak or Codex, co-authored with Claude Opus 5.5. That fits the CLAUDE.md "builder agent per packet" model, though Codex rather than poteto-agent is the author here.
- **Mixed origins for the defenses.** Money-path, quarantine and admission rules descend from ratified planning IDs (AD-16, FR-Q42, DEC-0315, DEC-0309), not incidents. The incident-driven pieces are narrower: the DOS short-name bypass, apps_test advancing the road, the completed-child status at a parent approval pause (af932192, PR #47), and FastMCP `Client(existing_client)`.
- **Environment refusal looks preventive, not reactive.** check_environment is defensive "subscription only, never paid API fallback" posture designed offline. I found no live-incident commit; the native work was never run live.
- **Native sessions and CLIProxy point opposite ways.** The P06 CLIProxy route (subscription via proxy, `ChatAnthropic(base_url=...)`) was the rebuild's replacement for native SDK sessions, which carry the verdict "replace … init_chat_model + router". A Claude Agent SDK + OpenAI Agents SDK harness reverses that verdict.

### Contradictions
- **Native slice skipped.** DESIGN §12c slice 5 says delete "proxy and native sessions", but PR #53 deleted only the proxy and kept native sessions because of callers. They remain at 4eac8f69.
- **Native sessions are not a model call.** The survival map maps native sessions to "init_chat_model + router". The native doc says "Native sessions are not `BaseChatModel` instances" and the harness owns the inner loop, so the replacement is not functionally equivalent.
- **Two copies of the money-path rules.** The barrier lives both in qma-core `barriers/money_path.py` (still imported by qma-daemon `tools/registry.py` and `plugins/context.py`) and in qmx_agents.guards.money_path.
- **Doc says turns, code has none.** The P11 packet says "copilot sessions: create, list, append, stream", and PR #47 claims "Project graph messages … onto the existing session log/SSE". No control route drives a turn or resumes an approval; only library and script callers do.
- **"Operator-only" `/sign` is protected only by omission from OPERATIONS/MCP.** It shares the single bearer token with every agent-reachable REST route.
- **"Approval" means two different things.** The P08 `AdmissionGate.approve(principal="operator")` is an in-process check (principal string equals "operator"), not an authenticated route. Copilot approvals are LangGraph interrupts surfaced as `permission` blocks.

### Gaps
- No PR review threads, so why the shapes were accepted is not recorded in GitHub.
- No commit explains why the native sessions were built on 10-04 and then abandoned for CLIProxy on 10-07. The rationale is presumably in DESIGN §5.3 or transcripts.
- I did not read native_codex.py in full, the rest of native_sessions.py, or the bodies of #42 (P14), #39 (P18) and #56/#57/#60-#62 and #64-#70.
- I did not inspect DESIGN §5.7, §8, §12, §12b, COPILOT.md or the research docs (out of my source).
- Not confirmed whether anything at 4eac8f69 actually instantiates `ClaudeSessionBackend` outside tests and examples.

### Additional Leads
- 942198c1 (Codex, 2026-10-13) "QMA v2: archive the Wednesday-frame plan; add audits, research H1-H3, backlog rewrite, UI notes and the re-plan trail" mentions `subscription_required`. It is likely on plan/agent-system and is the design-docs investigator's territory.
- T3 Code checkpoint refs from 10-08 and 10-09 also contain `subscription_required`, which may hold session transcripts.
- DESIGN §5.3 (CLIProxy), §5.7 (guards), §8 (control), §12/§12b (rulings superseding the P05 JSON-RPC/AsyncSubAgent recommendations), §12c.
- COPILOT.md modes were withdrawn in a80e1855 ("hold P24 pending redesign"); P20 notes "ON HOLD (2026-10-09)".
- rebuild/research/cliproxy-video.md §C ("cloak mode").
- Planning IDs to trace in `_bmad-output`: AD-10, AD-16, FR-Q42, DEC-0309, DEC-0315, DEC-0339.
- qmx-agents/examples/NATIVE_SESSION_DOCS_DRAFT.md ("not ratified").
- scripts/dev/qma_callers.py (PR #58) gives reproducible deletion sets for the remaining old code.
- The open PR #25 is "Draft: Aurelius backend baseline (MA04) … do not merge".

Key paths:
- D:/QMX-worktrees/harness-survey/qmx-agents/packages/qmx-agents/src/qmx_agents/guards/money_path.py
- D:/QMX-worktrees/harness-survey/qmx-agents/packages/qmx-agents/src/qmx_agents/guards/admission.py
- D:/QMX-worktrees/harness-survey/qmx-agents/packages/qmx-agents/src/qmx_agents/guards/hooks.py
- D:/QMX-worktrees/harness-survey/qmx-agents/packages/qmx-agents/src/qmx_agents/guards/middleware.py
- D:/QMX-worktrees/harness-survey/qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_boundary.py
- D:/QMX-worktrees/harness-survey/qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/native_claude.py
- D:/QMX-worktrees/harness-survey/qmx-agents/examples/NATIVE_AGENT_SESSIONS.md
- D:/QMX-worktrees/harness-survey/qmx-agents/packages/qmx-control/src/qmx_control/server.py
- D:/QMX-worktrees/harness-survey/rebuild/reports/survival-map.md
- D:/QMX-worktrees/harness-survey/rebuild/reports/p16-deletion-plan.md