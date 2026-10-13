# Candidate 1 (Opus): harness units

Nine units plus one conditional, in dependency order. Each is one PR into `rebuild/base`.

Each unit has:
- **Done when**: what he sees in the temporary console (`http://localhost:8766/console`).
- **Live check**: the check the orchestrator runs against real models before merging. Fakes may back unit tests, but they never count as "done".

## Lanes

```
day 0:  U1 ─────────────┬──> U2 ──> U3 ──┬──> U6 ──┐
        U8-probe (spike)│                ├──> U7 ──┼──> U9
                        └──> U4 ─────────┴──> U5 ──┘
                                              └──> U8
U10 (conditional) any time after U2
```

- **U2 and U4 run in parallel** after U1. U4 builds against U1's link and stub gate. When U2 merges, the OpenAI engine picks up full policy without code changes on its side, because policy lives on the control side.
- **U5, U6 and U7 run in parallel** once U2, U3 and U4 are in.
- **The U8 probe** is a one-file script with no harness code. It can run on day 0 to settle the ChatGPT route early.
- At most three builders at once, per the 2026-10-13 audit recommendation.

---

### U1. First real Claude turn on his subscription

Scope:
- Scaffold `qma2`: pyproject with pinned `claude-agent-sdk`, CI rows in `tools/ci.py` and `test_all.py`, and the import-linter contract.
- `model`, `wire`, `host/__main__`, `host/link`, `host/claude`.
- A minimal `_ThreadActor` and `_HostSupervisor` (allow-listed env, Job Object or process group).
- `store` with threads, segments, turns and items.
- `secrets.host_env` and `tool_env`.
- `ControlSink` writing text and tool blocks.
- `GET /api/threads/{id}/live`, plus the rows `threads_create`, `threads_list`, `threads_send`.
- The console's chat panel and Claude sign-in panel: shows `claude_status`, prints the login command.
- `accounts.claude_status`, ported from `check_environment`.
- `money.py` complete.
- Stub gate: money rule, then allow read-only built-ins (Read, Glob, Grep, WebSearch, WebFetch), deny the rest with "approvals arrive in U2".

**Done when:**
- He runs the shown login command once.
- The console says "Claude: signed in (Max)".
- He types "list the files here and summarise README". Text streams in and the tool cards show Glob and Read.
- "search the web for today's EURUSD news" shows a WebSearch card.
- He restarts QMX, sends "what did I ask you first?", and gets the right answer.

**Live check:**
- The U1 script runs against his real subscription. Pass when a turn completes with `model_usage` present.
- `claude auth status` reports QMX's claude-home.
- A second thread keeps streaming while the first host is killed; the killed thread shows "failed".
- Grep of `~/.qmx` finds no token.
- The env dump inside a Bash tool call shows no `ANTHROPIC_*` or `QMX_*`.
- Probes recorded for later units: do in-code hooks fire with `setting_sources=[]`? Option spelling for `exclude_dynamic_sections`.

### U2. Policy, approvals and the operator principal

Scope:
- `policy.py` in full: Claude rule syntax, compound-command split, path normalisation, modes, caps, protected paths.
- `approvals` and `rules` tables, `_RuleBook`.
- `Harness.answer` and `approvals`.
- `Op.who` column, operator pairing (`qma2.operator`, `/api/operator/pair`, the `start` hand-off).
- `approvals_answer` and `threads_set_mode` rows; `approvals` topic.
- Console approval cards with Allow once / Allow for this chat / Always allow / Deny / Deny and stop.
- The AskUserQuestion card and the plan approval card.
- Claude `can_use_tool` rendezvous.
- Probes: hook `ask` under each mode; whether tool_use_id is present in `can_use_tool`.

**Done when:**
- "delete notes.txt" shows a card; Allow once deletes it.
- "Always allow" on `npm run lint` is not asked again in a new chat.
- With `deny: Bash(git push *)` in settings, "push my branch" is refused with the rule shown.
- Plan mode blocks a file write.
- "Use python to read the qmx/ctrader password from the keyring" is refused with "Money is read-only for agents".
- The console banner reads "Money guarantee: tool-level (same Windows user)".

**Live check:**
- BASELINE H6 outcomes for `git push`, `cd x && rm -f y` and `npm test` match vanilla Claude Code on the Claude engine.
- H7: an always-rule persists across threads.
- `curl` with the bearer control token to `POST /api/approvals/{id}` returns 403.
- MCP `tools/list` contains no operator row.

### U3. Hooks, QMX config home, project instructions, skills, agents and memory (Claude engine)

Scope:
- `hooks.py` (command handlers) and link `Hook` callbacks in `host/claude`.
- The actor fires SessionStart, SessionEnd and PostCompact.
- `config.py` layers and the `ConfigHome` layout; `materialize_claude_plugin`.
- `ProjectContext` (CLAUDE.md + AGENTS.md + MEMORY.md head) as the first user message.
- Agents passed as `AgentDefinition`; the reserved `qmx` MCP name.
- Sub-agent tool calls gated with agent_path; child sessions in the console.

**Done when:**
- A hook script that exits 2 on `rm -rf` blocks "rm -rf build", with the hook's message shown.
- A rule that exists only in AGENTS.md is obeyed, and so is one only in CLAUDE.md.
- A QMX skill shows in the skill list and runs by name.
- "Remember I prefer tabs" is followed in a brand-new chat.
- A `reviewer` agent from `~/.qmx/config/agents` runs read-only and appears as a child card.
- Nothing from his personal `~/.claude` appears.

**Live check:**
- BASELINE H8, H9, H14 (skills) and H15 on the Claude engine, side by side with vanilla Claude Code.
- A PreToolUse `updatedInput` rewrite and `additionalContext` reach the model.

### U4. OpenAI engine on an API key (OpenRouter first)

Scope:
- `host/openai.py`: `LinkSession` over items, `PromptBuilder` with `prompt_cache_key`, the local trace processor with a startup assertion.
- `host/tools.py`: Read, Write, Edit, Glob, Grep, Bash or PowerShell, WebFetch, WebSearch backend, TodoWrite, AskUser, Skill, apply_patch for GPT; `ProcessTable`.
- `secrets.py` backends (keyring, ephemeral, age file); `accounts.put_api_key`.
- `ApiKeyAccount` routes; the console's "Add provider key" form.

**Done when:**
- He adds his OpenRouter key in the console and starts a chat on an OpenRouter model.
- The same "run the tests and fix the failing one" task works, with diffs shown.
- Approval cards, the hook block and the money refusal behave exactly as on Claude.

**Live check:**
- BASELINE H5: a 5-step refactor gives the same files changed and the same test result as Claude Code.
- H6, H7 and H8 re-run on the OpenAI engine with no new policy code.
- From turn 2, cached-read tokens are at least 80% of input where the provider reports cache.
- A network capture shows no request to OpenAI's trace endpoint.
- The key is absent from every file, log and trace in `~/.qmx`.

### U5. Router, accounts, usage page and switching with a cost warning

Scope:
- `router.pick`, `RouterPolicy` (settings section `router`, background cap 50%).
- Usage capture from both engines into `usage` and `limits`; `UsageReport`; the `usage` topic.
- The console usage page: Claude 5h and weekly bars with reset times, tokens and cache by model and thread, the money-guarantee line.
- `quote_switch` and `switch`: same-engine (`set_model`, effort reconnect) and engine change (new segment seeded from items, or a summary).
- Profiles (one-click preset).

**Done when:**
- The usage page shows how much of his Claude 5-hour window is used and when it resets.
- Switching a Claude chat to an OpenRouter model pops "this will rebuild the cache, about N tokens". After confirming, the chat continues and still knows what was said.
- A background chat started while the window is above his cap runs on OpenRouter.

**Live check:**
- H12 on both engines.
- H18: per-turn tokens match the provider's own report within 1%.
- H16: a profile switch changes model, effort and mode in one click.
- A stale quote, with a turn in between, is refused.

### U6. Compaction, caching discipline, steer and interrupt

Scope:
- `host/compact.py` (remote where offered, else local Codex-style); `Store.archive_items`.
- `/compact <focus>` on both engines; Pre/PostCompact hooks on both.
- Steer and interrupt on both adapters; `ProcessTable.kill_all`.

**Done when:**
- A long chat on a 128K OpenRouter model compacts by itself, keeps working, and still follows CLAUDE.md rules.
- "/compact focus on the parser" keeps the parser details.
- Typing "stop and say done" during a 30-second `ping` ends the turn with "done".
- Stop leaves no stray process in Task Manager.

**Live check:**
- BASELINE H3 and H11 side by side with Claude Code `/compact` and Codex `turn/steer`.
- H10 cache numbers re-checked after a compaction.

### U7. Sub-agent and MCP parity on the OpenAI engine

Scope:
- `AgentTool` (nested agents, gated, caps in `policy.decide`); the background registry with SendMessage, wait, list and interrupt.
- Child sessions for OpenAI sub-agents.
- QMX's MCP manager wrapping MCP tools as gated function tools; `mcp__qmx__*` ops through `AgentOps` with `CallOp` one-shot grants.
- The proposal tool end to end.

**Done when:**
- The same `reviewer` agent runs read-only on both engines.
- A fourth nesting level is refused.
- A background helper's approval card shows the helper's name.
- The same MCP tool runs under the rules on both engines.
- "Buy 1 EURUSD" produces an unsigned proposal in Portfolio, and the agent says it needs his signature.
- "Place it now" is refused.

**Live check:**
- BASELINE H13 and H14 on both engines.
- A broker MCP server's own `propose_order` is refused while QMX's proposal tool succeeds.

### U8. Sign in with ChatGPT (probe first)

Scope:
- Day-0 probe script: PKCE sign-in, then an Agents SDK run against `api.openai.com/v1/responses` with `store=false` and `stream=true`. Records whether `x-codex-*` headers and `responses.compact` are reachable.
- Then `accounts.chatgpt_begin` and `chatgpt_complete`, token refresh with `Rotate`, the GPT base prompt, and header-based `limits`.

**Done when:**
- He clicks "Sign in with ChatGPT", approves in the browser, and a chat on GPT works with the same tools and approvals.
- The next day the chat still works (token refreshed).
- If OpenAI exposes it, the GPT window shows on the usage page.

**Live check:**
- The probe's recorded results.
- An H5 subset on GPT.
- A forced token expiry mid-thread recovers without re-login.
- No request ever goes to `chatgpt.com/backend-api`.

### U9. Long-lived threads: export, fork, archive, lockouts, restarts

Scope:
- `Harness.export` (zip); `fork`, `archive`, thread list with resume.
- `LockedOut` handling: foreground waits and offers a switch; background re-routes at a turn boundary.
- Idle host reaping and resume.
- Restart recovery: expire pending approvals, mark running turns interrupted, offer "retry".

**Done when:**
- "Export" downloads one zip with the transcript, logs and traces.
- Forking after turn 2 and continuing both chats gives two different histories, and the original is unchanged.
- When his Claude window runs out, the chat says it resumes at the reset time or offers to switch, and continues after the reset.
- Restarting QMX during an approval shows the card as expired with a retry button.

**Live check:**
- BASELINE H4.
- A simulated `rejected` limit event leads to LockedOut, then a timer, then Idle.
- A three-day-old thread resumes with full context.
- A secrets grep over the exported zip comes back clean.

### U10 (conditional, his call). Separate OS account for agents

Scope:
- `_HostSupervisor` backend `os_account`: hosts run as a low-rights local user that owns claude-home and the workspaces it is granted, and cannot read his Credential Manager, Keychain or Secret Service.
- The setup wizard (needs admin once).

**Done when:**
- The usage page says "Money guarantee: enforced by OS account".
- Asking an agent to read the broker password by any means returns nothing.

**Live check:**
- From inside an agent's Bash, `python -c "import keyring; print(keyring.get_password('qmx/ctrader', ...))"` prints `None`.
- U1-U9 checks still pass under the backend.
