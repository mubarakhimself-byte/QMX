# 41. Adversarial review of the architecture rerun (39)

**Opus reviewing Opus.** The rerun (`39`, commit `7046d83c`) and this review are both by Opus 5.5, so they may share blind spots. No sub-agents, no skills, no commit, no design file edited; this file is the only output.

**Ground truth used:** `git diff 4b7fbc03 7046d83c`; the three spines, SOLUTION-DESIGN (SD), HARNESS-REQUESTS (HR), OPEN-DECISIONS, UI-HANDOFF; rulings 1-104 of `26`; alignment `A`, `B`, `C`; `36`; `37d` with the Hermes mirror under `research/sources/hermes-docs/`; code on `origin/engine/base` = `132169c7`, read with `git show` and `git grep` (no checkout). Code paths below are short: `QH/` = `qmx-agents/packages/qma-harness/src/qma/harness/`, `QE/` = `qmx-agents/packages/qmx-engine/src/qmx_engine/`. Labels: [retrieved] read today, [remembered] training knowledge not checked today.

**Counts:** 4 critical, 8 high, 13 medium, 9 low.

---

## Critical

### C1. A plan-main process sends first-party-shaped requests to third-party sub-agents; the env quirks that make those providers work cannot be set per request

- **Evidence.** Today every key and GPT launch gets process-level quirks: `ENABLE_TOOL_SEARCH`, `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS`, `CLAUDE_CODE_MAX_RETRIES`, `CLAUDE_CODE_AUTO_COMPACT_WINDOW`, `API_TIMEOUT_MS`, `CLAUDE_CODE_MAX_OUTPUT_TOKENS` (`QH/profiles.py:137-146`, applied in `QH/launch.py:376-385`). They exist because of measured failures: OpenRouter answers 400 "Deferred custom tools are only supported on Anthropic models" for Kimi K2.5 and DeepSeek with tool search on (`QH/profiles.py:162-168`, HP12 check 8, HP1); the ChatGPT route refuses `tool_search`, beta fields have no Responses mapping, and a usage-limit 429 must not be retried 10 times (`GPT_QUIRKS`, `QH/profiles.py:113-121`). `38` §161 [retrieved there]: unknown model ids receive adaptive thinking, effort and `context_management` by default; `CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1` removes `context_management`, `strict`, `defer_loading` and tool search. AD-38 (spine:302) and SD §26.1 (1219-1226) route plan-main sub-agents to the key, chat and GPT lanes, yet the plan launch gets only `ANTHROPIC_BASE_URL` and `ANTHROPIC_CUSTOM_HEADERS` (SD:1226). The probe that would have caught this, `38`'s P4 (beta fields and tool search on/off), is missing from SD §26.14 (P1, P2, P3, P5, P7 only).
- **Failure.** His Opus copilot runs "have Kimi and Qwen review this" (S1). The sub-agent requests go out with deferred tools, `tool_search`, `context_management`, `strict`, 1-hour `cache_control` TTLs and the OAuth beta header, shaped for api.anthropic.com. Kimi, DeepSeek and OpenRouter 400 (already measured for two of them); a GPT sub-agent is refused by the ChatGPT route; a GPT 429 is retried 10 times into his ChatGPT window. Option A, the reason the rerun chose A+B+D, does not work for the providers he uses most. The body also carries `metadata.user_id` with his Anthropic account id and `x-claude-code-*` headers to every third-party provider.
- **Fix.** (1) Make per-provider request normalisation a router duty on every non-plan lane, keyed by the model row: strip or expand `defer_loading` and the tool-search tool, drop `context_management`, `strict`, unsupported `cache_control.ttl`, `anthropic-beta` values the row does not accept, `metadata.user_id` and `x-claude-code-*` headers from plan-origin requests. (2) Rewrite history blocks the target cannot parse (`tool_reference`, `server_tool_use`). (3) Restore P4 as a ship gate for the plan lane, run with a plan-main process, not a key-main one. (4) In SD §26.1 mark "Claude plan main → GPT helper: native" as `delegate` v2 only until P4 passes for the GPT lane. (5) State the CLI retry count under a plan main (10) and have the router answer a provider's plan-quota 429 with a non-retryable class so the CLI stops.

### C2. `delegate` v2 `cli` targets run external agent CLIs with their own shells outside every boundary the engine relies on

- **Evidence.** AD-41 (spine:320) adds target kind `cli`: "Codex CLI, Kimi Code, OpenCode CLI" over stdio; "Engine agent nodes use the same mechanism for sub-agents declared `via: delegate`." Nothing places these processes in a container. The money gate is a Claude Code PreToolUse callback (`QH/money.py:1-20`, layer 3), H2's allow-list and AD-24's "agent chats never get a host shell" are Claude Code SDK options, and the AD-43 floor is a harness gate. `QH/money.py:4-6`: against a shell under his own OS user "exactly one thing is structural: broker credential scope, when proven (check S27)". `QH/relay.py:22-23`: the relay "is not a key boundary against agent Bash, which can read `qmx/*` keyring entries".
- **Failure.** A workflow agent node delegates to Kimi Code. Kimi Code's own shell tool runs as him on the PC with no money gate, no H2 allow-list, no AppContainer: it can read the plan login, the `qmx/*` keyring (broker entries included) and his files, and can call a broker API directly. AD-24's whole layering is skipped by one tool argument. These CLIs also use their own logins (`~/.codex/auth.json`), outside the pool, the router journal and the one DevOps layer.
- **Fix.** `cli` targets run only in the `cli_inside` container mode (AD-25): container, run pass to the nearest router, no keyring, no host home, egress through the router. On the PC without Docker they are refused, never run bare. For copilot chats, list `cli` delegates under the copilot-shell known gap (AD-22) and make the first spawn per CLI an ask. Their model traffic goes through the router with a run pass so the pool and journal see it.

### C3. "Demo" is not proven, and an agent-configured EA can trade his real money later

- **Evidence.** AD-33 (spine:272) and SD §26.7 (1330-1331): the driver reads account number and server from the window, compares them with the manifest's pin, then turns algorithmic trading on; "the money gate runs first on every desktop action". AD-44 (spine:338) repeats it. The money gate matches tool names and text (`QH/money.py`); a Cua click is coordinates. Nothing says who sets the pin or that the account's trade mode is demo. Prop-firm challenge accounts typically run on broker demo servers while real money (fees, payouts) is at stake [remembered]. MT5's "Allow algorithmic trading" is terminal-wide and EA attachments persist in chart profiles [remembered].
- **Failure.** (1) The copilot builder drafts the manifest and copies the account number from the window; he clicks publish; the pin is his live or prop account and the "match" passes. (2) The agent sets up an EA on demo in his installed terminal and turns AutoTrading on; days later he logs that same terminal into his live account and the attached EA trades real money. No QMX check runs at that moment. (3) The agent itself opens File → Login (not an order ticket, so the gate has nothing to match) and switches account between the check and the toggle.
- **Fix.** (1) Demo work happens only in a separate portable MT5 or cTrader install (its own data folder) that has never held a live or prop login; the manifest names the install path, and his main terminal is in the always-deny list. (2) The pinned account list is written only by him in Settings (locked key, AD-43), never drafted by an agent. (3) Before every toggle and at every step, read the trade mode from the terminal (MQL5 `ACCOUNT_TRADE_MODE` through a read-only script, cTrader's account type), not from window text, and refuse prop-firm servers by name list. (4) At the end of the attempt turn AutoTrading off and detach EAs, and record it. (5) E46 adds: a prop-demo account refused, a mid-run login switch refused, AutoTrading off at exit.

### C4. Native sub-agents cannot pick a third-party model in the copilot without a harness launch change the rerun does not request

- **Evidence.** The only proof that a non-Claude id reaches the wire (`scripts/probes/engine/FINDINGS.md:40`, E24) used `AgentDefinition(model="kimi-k3")` passed at launch, a fake API key and a throwaway home: no OAuth, no plan main, no in-chat model choice. AD-29 (spine:248) labels it [retrieved] for the plan-main case it never tested. The `Agent` tool's own `model` parameter takes Claude aliases only [remembered]; a plan launch sets no `ANTHROPIC_DEFAULT_*_MODEL`, so an alias stays Claude. Agent definitions reach a chat only through the SDK `agents` option or plugin agents; the harness has one SHA-locked plugin and `setting_sources=[]` (`QH/home.py:16-17`). HR H7 (line 17) asks `agents` for Background chats only and is not in HG4. P1 (SD:1407) assumes "the main calls an `Agent` with `model: kimi/k3`".
- **Failure.** Ruling 92's copilot case (S1, UI-HANDOFF §12 row 1) has no mechanism: the Interactive copilot can only spawn Claude sub-agents natively, and the router's plan lane is built for traffic that never arrives. The rerun's main justification for option A over B and D alone disappears unless the launcher changes.
- **Fix.** Add a HG4 row (outside the pool exception, his grant): `NewChat.agents` for Interactive, Background and Child chats, generated from the registry (one definition per enabled model or per role, e.g. `kimi-reviewer` with `model: kimi/k3`). Rewrite P1 to call those definitions, under a real `/login`, and record whether the CLI accepts a non-Claude id under OAuth (E24 saw `unrecognized_model` on stderr even under an API key). Until it passes, S1 runs through `delegate` v2.

---

## High

### H1. The plan lane makes his copilot depend on the in-process router for the first time; "no new single point of failure" is false

- **Evidence.** 39 §2.3 "Failure" and SD:1228: a router crash is a harness crash, so A "adds no new single point of failure". Today plan chats have no base URL (`QH/launch.py:346-350`, "no QMA process is in the request path"). The relay is a uvicorn task on the host's event loop, shared with harness, control and engine (`QH/relay.py:293-296`: it runs on the host's event loop), bound to an ephemeral port (`QH/relay.py:340-343`).
- **Failure.** The uvicorn task dies, or the shared loop stalls on engine work or on parsing a multi-MB body: every plan chat's stream freezes or fails, though `qma.serve` is still up, so the desktop host's restart never fires. After a restart the port changes; any CLI that survived points at a dead port. Before the rerun, those failures could not touch the copilot.
- **Fix.** Run the router on its own thread and event loop (or process) with a fixed loopback port; health-check it from the desktop host; on failure, flip `router.plan_lane` off automatically and relaunch plan chats without a base URL (the built path) with one line to him. Add this to E49.

### H2. A plan 401 benches a healthy account and can move his copilot to another provider

- **Evidence.** 39 §2.5, SD:1228 and S6 (SD:1392): a plan 401 is forwarded, then "the pool benches that plan account", and "the copilot falls to his next Claude account, else to the next role candidate". AD-12 (spine:140): "401 refreshes once (GPT sign-in) and then benches the account". Hermes, which 39 marks ADOPT (H-24, H-27): 401 → refresh, "rotate only if refresh fails", cooldown 5 minutes; a login is marked dead only when the refresh token itself is rejected (`hermes-docs/user-guide-features/credential-pools.md:213-216, 235-241`). The Claude CLI refreshes against Anthropic's OAuth endpoint, not the base URL, so the router never sees whether the refresh worked.
- **Failure.** An expired access token (routine) or a refresh race between several CLIs sharing one plan home yields one 401; the CLI refreshes and continues; the router benches the account anyway and the copilot is moved to Kimi. With one Claude account, workflows lose Claude for the rest of the day.
- **Fix.** Never bench a plan account on a router-seen 401. Bench only on a dead-login signal from the CLI itself (its result or stream says it needs `/login`, or N consecutive 401s on new requests over minutes). Never move the copilot's main model automatically; show "sign in again" and wait.

### H3. The registry's "unknown id → 400" breaks plan chats after a CLI update

- **Evidence.** AD-38 (spine:302) "Unknown ids are refused with 400"; SD:1203 "unknown → 400, never guessed"; registry rows list `claude/opus`, `claude/sonnet`, `claude/haiku` (SD:1255). The CLI sends native, often dated ids (`claude-…`), including its own background haiku calls. Today the plan rule is a family test: any `claude-` id or tier alias (`QH/profiles.py:229-230`).
- **Failure.** The CLI auto-updates and starts sending a new id (a new haiku, a dated sonnet); the router refuses it; titles, compaction and the main turn fail on every plan chat until someone edits the registry.
- **Fix.** On the plan lane accept any `claude-*` native id by the existing family rule and journal unknown ones; apply the strict registry only to third-party ids.

### H4. Caps survive in shipped templates and in the migration rule

- **Evidence.** AD-40 (spine:314): templates ship no limits. But: every template sets a `runaway` block (34 definition files; template A: `"agents": 4, "tool_calls": 40, "wall_seconds": 5400`, `templates/a-fill-the-library/definition.json:15-16`); 28 templates set node `timeout.run_seconds`; agent nodes carry `max_turns` 4 (`a-fill-the-library/definition.json:61`, three `_shared` folders) and 20 (`pp-proposal-pack/definition.json:33`), read by `QE/nodes/agent.py:193-203`. SD §2.2 (line 109): "the old `settings.runaway` key is read as `limits` once". AD-4 (spine:92) still lists `timeout` "(run and idle)" in the node contract. SD §2.4 (line 141) still says "`agent` nodes take `max_turns` and `max_tool_calls` from Settings when they leave them out". 39 §7 names only the runaway blocks.
- **Failure.** S2's 300-video playlist through template A stops at 4 agents, 40 tool calls or 90 minutes, now relabelled "a limit he wrote". Rewriting the blocks changes every template's content hash, so `tested` drops and enabled triggers on those versions lose their tested status; published versions are immutable, so "read as `limits` once" keeps the caps live there.
- **Fix.** The caps-removal packet deletes `runaway`, node `timeout.run_seconds`, agent `max_turns` and `max_tool_calls` from all shipped templates and from the v1 schema's defaults; old documents fold `runaway` to nothing (not to `limits`), with an `info` line. Remove "run" from AD-4's `timeout` and fix SD line 141. Re-test and re-tag every shipped template in E48.

### H5. The stuck detector is not sound, so a looping run can burn a metered key to zero

- **Evidence.** AD-16 (spine:164), SD:629-644, defaults SD:964. (a) The loop signature matches "the same result digest" or "no new tool-result digest": raw digests of results that carry timings, temp paths or timestamps (a pytest run, a `ls -l`, a web search) differ every time. (b) Progress events are "a tool call, a turn, a log line, a chunk event"; an in-flight model wait is not one. Hermes, adopted as H-08, says the opposite: "An in-flight model wait still counts as progress … a slow local / long-prefill completion is not treated as stalled" (`delegation.md:365`). (c) `timeout.in_tool` 1,200 s is a wall clock on any open tool call regardless of CPU. (d) AD-47 loops and goals in copilot sessions: Hermes' backstops (`max_ticks` 100, 20-turn goal budget, `loops.md:81`, `goals.md:57`) are rejected, the replacement "no-progress detection stops a stuck goal" (H-69) cannot fire on a session that makes progress every turn, and whether AD-16 applies to sessions is unstated.
- **Failure.** An agent "fixing" a test makes a different edit each turn and gets a slightly different failure: never `stalled`. On DeepSeek or Qwen pay-as-you-go keys that is real money until the 402. A 600k-token chunk (E43's case) on a slow third-party prefill sits silent past 300 s and is killed as stalled, then retried, re-sending 600k tokens. A 30-minute backtest or training cell inside `sandbox_python` is killed at 20 minutes. A goal whose judge never says done runs on his copilot account indefinitely.
- **Fix.** (1) Hash results after the same masking as `ledger.signature` (digits, uuids, paths, timestamps). (2) Add a no-convergence detector that needs no usage number: the masked error signature of the attempt's last tool results repeating within the window. (3) Count "request in flight" (from the router journal) as progress. (4) For in-tool stalls use sandbox CPU and IO from the container, as scripts already do. (5) Adopt Hermes' goal `blocked` verdict as a pause, and say whether AD-16 runs on copilot sessions. (6) E41 adds a flailing-agent fixture.

### H6. The blast radius of AD-38 and AD-40 is much wider than §7 lists

- **Evidence.** 39 §7 lists `ladder.py`, `agent.py`, `settings.py`, `admission.py`, `watchdog.py`, `relay.py`, `launch.py`, `profiles.py`, `harness.py`. `git grep runaway` also hits `QE/runner.py:161-180, 481, 525, 696`, `core/commands.py`, `core/fold.py`, `core/ready.py`, `core/simulate.py`, `core/state.py`, `definition/model.py:73-89`, `definition/lint.py:200-206`, the v1 JSON schema (`:376-528`), `nodes/base.py`, `nodes/llm.py:122-123`, `ports/inbox.py`, `roles.py:95-110` (degrade), `templates/rv-weekly-review/scripts/lint_edits.py:11`; tests `test_ladder`, `test_agent`, `test_lint`, `test_settings`, `test_definition`, `test_watchdog`, `planted.py`, a workflow fixture; live checks `x08_watchdog.py`. Budgets also live in `qma/console.py`, `QH/usage.py:250-280` (`BackgroundCap`, `cap_note`, the usage page at `QH/harness.py:624`), `QE/ports/settings.py`, tests `test_change`, `test_console`, `test_delegate`, `test_launch`, `test_table`, `test_usage`, `test_admission`, live `s10_usage.py`, `hp11_lanes.py`, probe `p_limits.py`. AD-38 also changes `QH/home.py` (one plan home today, `home.py:5-8`; relayed `projects/` links to it), the relay's one-profile grant (`RelayGrant.profile`, `relay.py:162-170`; per-request routing is a rewrite, not "one relay mode", 39 §2.3), and `test_chat.py:1021-1032`. Template renames (AD-46) hit every test that names a template id.
- **Failure.** The caps-removal packet is budgeted as "hygiene-size" (SD:1425) and the router as "one relay mode"; the builder discovers the rest mid-PR, against the light-verification rule.
- **Fix.** Replace 39 §7's AD-38 and AD-40 rows with the file list above and resize both packets.

### H7. Two pools lease the same keys, and the same GPT account on two machines revokes itself

- **Evidence.** AD-12 (spine:140): every harness instance runs its own pool; keys reach a host through the vault (AD-28: provider keys are replicable). Nothing shares cooldowns, readings or provider concurrency between the PC's and Contabo's pools. AD-28 (spine:242): "a GPT sign-in is per machine and per account the same way"; S11 runs GPT on Contabo. Hermes: "two logins of the same account share one token family upstream, so OpenAI revokes the older one" (`credential-pools.md:126`), and shared logins should share one home "instead of each holding a copy of a single-use refresh token" (`:251-253`).
- **Failure.** The PC cools Kimi key 1 after a 429; Contabo keeps hammering it; together they exceed the provider's concurrency and both see 429 storms; `least_used` reads half the usage. He signs his ChatGPT account in on Contabo and the PC's GPT lane dies at its next refresh.
- **Fix.** Each key account and each GPT account has exactly one owning host; other hosts reach it through that host's router (central relay pattern). Or sync cooldowns and readings through the vault channel. Refuse a second machine sign-in of the same GPT account (compare account ids).

### H8. A `logged_in` browser snapshot carries his bank, payment and email sessions; the deny-list covers brokers only, and the snapshot will not decrypt on Windows as designed

- **Evidence.** AD-44 (spine:338): a snapshot of "his real profile's cookies taken by SQLite online backup", driven as a "QMX Browser profile over local CDP"; the always-deny list is broker web origins, prop firms and live trading windows (AD-33). H35 gives the copilot `logged_in` act level B4. Hermes, adopted as H-95, launches **the real browser binary** on the snapshot because that "keeps OS-encrypted cookies decryptable" (`browser.md:183-191`); Chrome on Windows binds the cookie key to its own binary [remembered].
- **Failure.** A page the agent reads injects "open the bank and…"; the agent acts with his bank, PayPal, crypto exchange or email session; nothing on the deny-list matches. Separately, on Windows the snapshot opens signed out because a different binary cannot decrypt the cookies.
- **Fix.** `logged_in` copies cookies only for sites he ticks (a per-site allow-list, default empty); banks, payment processors, crypto exchanges and mail join the always-deny list beside brokers; launch the real browser binary on the snapshot, as Hermes does; E45 adds a non-allow-listed logged-in origin refused.

---

## Medium

### M1. The plan lane is not a byte-for-byte pass-through as the relay is built
`QH/relay.py:108-109` serves only `POST /v1/messages` and `count_tokens` (else 404); headers become a dict (`relay.py:495-498`), losing repeated headers; `accept-encoding` is dropped (`HOP_BY_HOP`, `:110-124`). A plan CLI may call other base-URL paths [remembered]. **Fix:** the plan lane forwards any method and path for a plan grant, keeps the raw header list, and P1 records every path a plan CLI hits in a full session.

### M2. The plan lane removes a structural guarantee the docs still promise
`QH/relay.py:25-26` "Plan traffic never comes here … a relayed CLI runs in the relayed home, which holds no login"; `QH/profiles.py:6-8` and `money.py:1-2` say the same. Today a Claude bearer at the relay triggers `_token_bearer()` and an alert to every session (`relay.py:567-573, 765-773`), so H27 must reorder `handle()` (grant from `x-qmx-grant` first). HR line 31 still says the relay's egress stop and the launcher are "not requested, on purpose". **Fix:** say plainly in AD-38 and HR that H27 changes the egress-stop path and the launcher, list the docstrings to rewrite, and add a test that a plan-grant request never reaches `_token_bearer`.

### M3. `ChatTableFull` still refuses work and writes `needs_you`
`QH/harness.py:397-423`: with no idle chat, `send` writes `needs_you` and raises; `_delegate`'s docstring (`:425-433`) relies on that. AD-40 (5) and SD:528 say work past capacity queues and is never refused; H28 covers only budgets. **Fix:** add a harness row: `send` waits on a slot for Background and Child chats (no `needs_you`), Interactive keeps today's eviction; or state the engine's `Admission.acquire` as the only queue and keep delegate v2 children under it.

### M4. Router and CLI timeouts break the big-chunk case E43 claims
`QH/relay.py:139` `START_WAIT_S` 120 s to `message_start`; `:142` read timeout 600 s; the CLI's own `API_TIMEOUT_MS` default retries the whole request [remembered]. A 600k-token prefill on a third-party provider can exceed both, and every retry resends the full prompt. Mid-stream SSE `error` events are not classified, so the pool never rotates on them. **Fix:** per-model `first_token_timeout` in the registry, scaled to the prompt size; map mid-stream errors through the AD-40 classifier; include a slow-prefill fake upstream in E43.

### M5. The "model unreachable" re-run duplicates side effects in QMX
AD-10 (spine:128) re-runs a fire at 5, 15, 30 min "spend-neutral". Hermes' premise is that zero API calls means no side effect (`cron.md:468-480`); in QMX a fire may have run script and `irreversible_external` nodes before the first model node, and memos never cross runs (AD-7). **Fix:** resume the same run with the model node `waiting(resume_at)` on that schedule instead of a new fire.

### M6. With one Claude account, the copilot protection S13 promises does not exist
AD-11 and AD-13 send every test run and builder test to `claude/haiku` through the plan login; `background_priority: last` applies to leases, not to pinned test candidates; Max windows are shared across models [remembered]. S13 (SD:1399) says workflows "lease it only when every other candidate is closed". **Fix:** state it in S13 and UI §12: test runs and builder tests draw on his copilot window; show their share on the Accounts page (a reading, not a cap).

### M7. The overage stop is unnamed in the caps table, and plan-lane billing has no running check
`QH/usage.py:204-209` `hard_stop` (stop every plan chat when the overage rule fires) protects money, is provider-driven, and is absent from SD §26.3, so the caps packet may delete it. 39 §2.3 relies on plan-lane traffic counting against the Max allowance; P2 checks it once. **Fix:** list `hard_stop` in §26.3 as "kept: money guard"; add a standing check: if overage use rises while the five-hour window is below 100 % and the plan lane is on, turn the lane off for that account and raise one item.

### M8. The run-pass "request-rate theft alarm" has no definition
AD-28 (spine:242) and AD-40 (4): revoke a pass "sending far more requests than its run's attempts can explain". With no ceilings, nothing defines "explain"; a large chunked fan-out legitimately sends thousands. Either it never fires or it is a rate cap in disguise. **Fix:** define it on facts that need no usage number: requests from a source address outside the placement, requests for a `(run, node, attempt)` that is not open, or after the attempt ended.

### M9. The chat lane's thinking and tool translation is one line
HR H12 (line 65) and AD-38: "in-house chat-completions translator". Anthropic `thinking` blocks with `signature` have no chat-completions form; Kimi and DeepSeek thinking modes expect `reasoning_content` handed back inside a tool loop [remembered]; the CLI will echo translated thinking blocks with signatures the translator invented. P3 tests only a two-turn loop. **Fix:** specify the mapping (thinking ↔ `reasoning_content`, a translator-owned signature that the router strips on the way back, `tool_use` ↔ `tool_calls` ids) and extend P3 to a ten-turn loop with thinking on.

### M10. Native sub-agents on text-only models fail on any image tool result
AD-38 and SD:1228 refuse a request naming the missing capability. AD-42's describer covers attachments and `delegate` images, not image blocks inside a native sub-agent's own tool results (Read of a PNG, a screenshot tool). **Fix:** on key and chat lanes replace image blocks in `tool_result` with a short placeholder (or a describer call) when the row lacks `vision`, instead of refusing the whole request.

### M11. The central router serves GPT to machines he does not own
SD §26.1 (1197): Contabo's router has "key, GPT and chat lanes" for remote workers with run passes; AD-28 (spine:242): "Plan and GPT work runs only on machines he owns". A burst VM's agent would use his ChatGPT sign-in through Contabo. **Fix:** the central router has no GPT lane for passes from non-owned placements; `model_scope` on such passes excludes GPT.

### M12. "Git worktree" over a Library that is not git
Library AD-20 (Library spine:172-176) and engine AD-49, SD §26.12 (`git worktree add …`): the Library is a "content-addressed object store with git-like refs" (Library spine:6, 35, 86), not a git repository. **Fix:** say what a checkout is (a materialised folder from objects with a shadow-git checkpoint store), and keep `git worktree` for real repositories only.

### M13. Mini-app model calls and the video role depend on a harness call nobody asked for
AD-19 (spine:182) `llm_complete` through "the harness's `complete`"; AD-42 (spine:326) a native-video model "through `Harness.complete`". That is H3 (HR line 12), still "optional" and Deferred (spine:570), not in HG4. **Fix:** add H3 to HG4 (key and GPT lanes only, as written) or state the fallback (a one-turn Background chat under the app's grant).

---

## Low

- **L1.** UI-HANDOFF §1 item 6: "Compact now has no backend … leave the button out until he grants" H15; H15 was granted and built (HG1, ruling 89).
- **L2.** UI-HANDOFF §11 row 4 shows a goal as "3/20 turns", a turn budget AD-47 says does not exist.
- **L3.** Lab OPEN-DECISIONS OPEN-5 still ends "replaced by the engine's runaway guard, which never asks"; the guard is gone.
- **L4.** Engine OPEN-DECISIONS carries two D/E/F sets with different content; the older E still says edited scripts "wait with 'Docker is off'". Mark the older set superseded.
- **L5.** `max_live_chats` defaults disagree: harness `Budgets` 4 (`QH/launch.py:226`), engine `DEFAULTS` 6 (`QE/settings.py:47`), SD §26.3 "6".
- **L6.** AD-29 (spine:248) cites `check-ep1-model-ids.log` "on engine/base"; the log is not in the tree; the evidence is `scripts/probes/engine/FINDINGS.md:40`, which was an API-key launch with a fake model (see C4).
- **L7.** `CLAUDE_CODE_GATEWAY_HINT_HEADERS` and the `x-claude-code-agent-id` header (AD-15, H36) carry no retrieval label; the per-sub-agent journal depends on them. Label [remembered] and put them in P1.
- **L8.** AD-13's `key → gpt → plan` order is not in 39 §7: `QE/roles.py:86` sorts plan first and `settings.py:72` has `roles.live_order ("plan", "key")`.
- **L9.** SD E41 (line 1158) and E43 (line 1415) prove the same thing with different numbers; keep one.

---

## Hermes verdicts: 35 of 142 rows checked against the mirror

Rows sampled: H-02, 03, 04, 05, 06, 08, 10, 11, 12, 20, 23, 24, 25, 27, 28, 37, 41, 44, 46, 47, 55, 57, 59, 62, 63, 68, 69, 74, 78, 91, 95, 96, 99, 109, 142.

- **The cited Hermes behaviour exists in all 35.** Examples: batch default 10 with no hard ceiling (`delegation.md:52, 218`); one-shot runs capped at 2 children (`:559`, the basis of H-11's rejection); `fill_first` is Hermes' default (`credential-pools.md:181`); per-model Anthropic 429 cooldowns (`:230-233`); file-locked OAuth refresh (`:329`); `[CRON_FAILURE]`, `[SILENT]`, `UNVERIFIED` (`cron.md:712-727, 840, 855`); 14 and 30 day curator transitions (`curator.md:45`); pairing alphabet, 1 h TTL, 5-try lockout (`security.md:500-508`); NT device paths (`security.md:381`); MoA aggregator acts and is billed (`mixture-of-agents.md:18-21`); worktree result fields and prune-with-proof (`delegation.md:615-640`).
- **30 verdicts carry the Hermes idea over faithfully. 5 dropped the part that made it work:**
  - H-08: the in-flight model wait counts as progress in Hermes; AD-16 omits it (H5).
  - H-24 and H-27: Hermes rotates on 401 only after a failed refresh and marks a login dead only on a rejected refresh token; AD-12 benches on any 401 (H2).
  - H-59: Hermes' re-run is spend-neutral because a Hermes cron run with zero API calls has no side effects; a QMX fire can (M5).
  - H-95: Hermes launches the real browser binary so cookies decrypt; AD-44 does not (H8).
  - H-68 and H-69: Hermes' tick and turn backstops are rejected, and the stated replacement cannot stop a session that progresses every turn (H5).
- The counts in 39 §4 (119/18/4/1 = 142) add up and every row names a landing. The table is not a rubber stamp, but it adopted labels without checking that the mechanism survives the move into QMX, in about one row in seven of the sample.

## Alignment ledgers

Every mismatch in A §2 (M-1 to M-18), B §2 (1 to 15) and C §2 (M-1 to M-20), and every chat-only item in the three §3 lists, has an outcome in 39 §5 with an owner where deferred. Two outcomes are weaker than stated: A M-1 is "resolved" with a demo proof that does not hold (C3), and B 1 / C M-2 / C M-9 ("caps removed") leave the template-level caps (H4). A M-1's ledger said "he has to decide"; the brief records his decision, so taking it is correct.

## 36's criticals

C1 (PowerShell, Monitor, H2 as the SDK `tools` list), C2 (the verb predicate `name_money_act_called` in `qma-core`) and C3 (manifest `tier` and `network`, five network templates, all 31 must pass E48) are applied as 36 asked. C2 above is a new hole of the same kind as 36 C1: an agent with a host shell, reached through `cli` delegation instead of the built-in tools.

## What holds

The plan-lane rules themselves (loopback only, same host, no plan lane on a central router, bearer dropped before the egress stop on other lanes, a per-account switch, a boot canary) are the right shape. The caps principle is applied consistently in the spines' prose. Line citations into `launch.py`, `harness.py`, `ladder.py`, `migrations.py`, `tools.py` and `admission.py` were checked and are accurate.
