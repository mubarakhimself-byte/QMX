# 39. Architecture rerun (2026-10-18 evening)

Written by the architect (Opus 5.5), headless, with the BMad architecture skill in amend mode. No sub-agents; the reviewer gate ran inline. Nothing committed and nothing shipped: this pass is input for planning and for later shipping with poteto-mode.

**Inputs read:** `26` rulings 1-104 (latest wins); `alignment/A`, `B`, `C` (every mismatch and chat-only item); `AUDIT-2026-10-18.md`; `RECOLLECTION-2026-10-18.md`; `37d` (all 142 rows) with `37a`, `37b`, `37c`; `34`, `35`, `36`, `38`; the three architectures and `UI-HANDOFF.md`; merged code on `origin/engine/base` = `132169c7` (read with `git show`, `git grep`, `git ls-tree`).

**Files changed (all under `tracker/qma-v2/`):**
- `architecture/workflow-engine/`: `ARCHITECTURE-SPINE.md` (AD-38 to AD-49 appended; AD-4, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 28, 29, 30, 33, 34, 35, 36, 37 amended in place; ids stable), `SOLUTION-DESIGN.md` (§7, §17, §18, §20, §24 rows; new §26), `HARNESS-REQUESTS.md` (HG3 narrowed per 36; new round HG4 with 38's numbering fixed), `OPEN-DECISIONS.md` (D, E, F framed; G added; 0, 2, 3, 4 closed), `DOC-CHANGES.md` (rows 33-39), `PLAIN-WORDS.md`, `.memlog.md`.
- `architecture/lab-and-pods/`: spine AD-12, AD-13, AD-14 amended, AD-18 appended; `LLD.md` (two lines); `OPEN-DECISIONS.md` (OPEN-7; OPEN-5 note); `.memlog.md`.
- `architecture/library-and-data/`: spine AD-3 (kinds `persona`, `agent`; template `slots`), AD-9 and AD-18 (`agent` is a lifecycle kind), AD-20 appended, two Deferred rows; `.memlog.md`.
- `UI-HANDOFF.md`: §1 row 5, §3 pool bullet, §7 browser line, §9 rows 3 and 15 rewritten; §10 (37c), §11 (37d) and §12 (this pass) added.
- `lint_spine.py`: 0 findings on all three spines after every batch.

---

## 1. Summary

1. **Routing (ruling 98, my call): A + B + D together.** One model router per host (the relay QMA v2 already runs in-process on loopback) fronts every CLI the harness launches. It sends each request by model id down one of four lanes: **plan** (Claude ids from a Claude plan home, forwarded byte for byte to Anthropic with the CLI's own sign-in, never stored or logged), **GPT** (as built), **key** (Anthropic-wire third-party models with a leased key) and **chat** (an in-house chat-completions translator for OpenCode Go and similar). So his Opus copilot on the plan, a Codex-style GPT main, or a Kimi main can each run sub-agent 1 on Kimi and sub-agent 2 on Qwen in one chat, with thinking, tools and logs intact; `delegate` v2 adds full helper chats with their own transcripts. Copilot and workflows route the same way. Engine AD-38, AD-39, AD-41; §2.
2. **No QMX usage caps** (settled). The $5 budget, the 0.5 share, harness `max_turns`, the engine's runaway guard, agent turn and tool-call caps and run wall-time timeouts all go. What stays needs no usage number: no-progress timeouts with a warning and grace, a loop signature (the same call with the same result again and again), repeated error signatures, zero-token runs, a crash-loop counter. Providers' limits are the only limits; host capacity queues or spills work and never refuses it. Engine AD-40, AD-16, AD-9; §3.
3. **Hermes: all 142 rows validated** (no top-N): 119 ADOPT, 18 ADAPT, 4 DEFER, 1 REJECT (§4). The adopted rows land in twelve new engine ADs and amendments, chosen so one design solves several problems: the router solves mixed providers, OpenCode, several GPT accounts and per-sub-agent thinking at once; the model registry solves wire, multimodal routing, chunk sizing and compaction at once; the desktop host solves the app owner, Docker start, crash loops and the dead-man switch at once.
4. **Every alignment mismatch has an outcome** (§5): resolved in the architecture, rejected with a reason, or deferred with an owner. **36's three criticals and its should-fixes are applied** (§6.1); **34's SPEC-GAP and LATER-PACKET rows are resolved** (§6.2).
5. **Plainly, about "the backend is almost done":** the engine core, triggers, ledger, templates and the harness are built and merged; the pool, the router lanes, the vault, the Library, the Hub, Contabo, script isolation, `delegate` v2, memory, the multimodal layer, the browser and the desktop host are designed, not built (§9).
6. **Open operator calls, kept minimal** (§10): D, E, F (parked for him, now framed), G (grant the HG4 harness rows outside the pool exception), the fifth quant lens, and which burst provider to pay for when Contabo overflows.

---

## 2. The routing decision

### 2.1 The problem

Ruling 92: a main agent on a subscription (Claude plan or Codex) with sub-agents on different APIs (Kimi, Qwen, DeepSeek, GLM, MiniMax), thinking mode, tool calling and the DevOps layer intact, for the copilot **and** workflows. The old AD-29 said "the Claude plan is never mixed into a relayed chat" and AD-12 said "plan traffic takes no hop", which forbids it. One Claude Code process has one base URL and one credential [retrieved 38 §2.3], and sub-agent model ids reach the wire unchanged [retrieved: EP1 evidence `check-ep1-model-ids.log`], so a sub-agent can name `kimi/k3` but only reaches Kimi if its base URL routes by model id.

### 2.2 Options weighed

| Option | What it gives | What it costs | Verdict |
| --- | --- | --- | --- |
| **A** plan lane in the router | the stock Task tool, plugin agents and the CLI's own helpers on any provider under a plan main; per-request routing; best traces (every request with session and agent id) | the plan bearer transits a QMX process on loopback; reverses DESIGN's "no QMX process in the plan path" | **in**, with the rules below |
| **B** `delegate` v2 | full helper chats on any profile, own transcript, steer, durable completions, Claude helpers under a non-plan main, external CLIs | not the stock Task tool; each helper is a CLI process (RAM) | **in** |
| **C** Hermes or LiteLLM behind the relay | LiteLLM could route; Hermes cannot (it serves an agent, not a model) | a second pool, key store and control plane | **out** |
| **D** key-provider main (Kimi or GLM copilot) | native mixed sub-agents with no plan in the path | Claude only as a helper | **in** (the router gives it for free) |
| **E** CLIProxyAPI or claude-code-router | breadth | cloaking, login import, user ban reports; a second control plane | **out** (ruling 99) |
| **F/F′** opencodex, verbatim or as an upstream | breadth, chat-completions translation | keys leave the keyring, upgrade drift, a third party in the path | **out** (ruling 99: not even a hybrid) |

### 2.3 Why A + B + D, from each angle

- **Function.** B and D alone leave the stock Task tool, plugin agents and the Claude Code Workflow helpers Claude-only whenever the main is on the plan, which is his daily copilot. That fails ruling 92 for the copilot, and his stance is that "the SDK limit is a problem to solve, not a wall" (C-63). A alone gives no full helper chats, no Claude helper under a Kimi main and no external CLIs. Together they cover every row of the table in SOLUTION-DESIGN §26.1.
- **Plan allowance and billing.** 37d §6.5: a third-party app **holding** a Claude OAuth token gets extra-usage billing, not the Max allowance. In A no QMX code holds the token: the unmodified CLI holds its own `/login`, sends its own bearer, and the router forwards the bytes unchanged. Anthropic documents this pattern: with a base URL set and no gateway credential, "a saved claude.ai login remains the active credential, so its usage limits and billing apply", and a gateway that passes the traffic on "must forward the OAuth capability in anthropic-beta" [retrieved in 38 §2.1 from code.claude.com llm-gateway]. So the plan allowance applies and the settled rule "plan traffic passes through the unmodified CLI untouched" holds.
- **Terms.** The developer bar targets apps that offer Claude login to other users, route requests on behalf of users, or store and intermediate tokens; cloaking and pooling are what it targets [retrieved 38 §2.1-2.2]. A serves one person, his own unmodified CLI, one account at a time, no storing, no rewriting, no cloaking, and never swaps a token between accounts. The literal word "intermediate" is the remaining exposure; ruling 38 says risks are aligned and not to re-raise them, ruling 98 hands the call to me, and a per-account kill switch keeps it his to turn off.
- **Failure.** The router already lives inside `qma.serve` [retrieved `relay.py`: binds 127.0.0.1, in-process]. A router crash is a harness crash, which the desktop host restarts (AD-48); A adds no new single point of failure. If the boot canary fails, the plan lane stays off and plan chats launch as built.
- **Security.** The plan lane is same-host loopback only; plan bytes never cross the tailnet; a central router has no plan lane; every non-plan lane runs the built egress stop as a canary, so a Claude token that leaks into a third-party request fails closed with a `black` item. No header value is logged.
- **Blast radius.** Only provider contracts change (launch env, relay lanes, profiles, pool); chats, permissions, the money gate and the launcher's other behaviour stay as built (C-60). §7 lists what it touches.
- **Cost of building.** A is about one relay mode on code that exists (grants, egress stop, quirks, journal); B is a rebuild of the `delegate` call path on existing Child chats; D needs only the registry. All three share the pool and the registry, so building them together costs less than building any two separately and retrofitting the third.

### 2.4 The rules that make A safe

1. Plan lane only for Claude ids on a grant minted for a plan home launch on the same host; loopback only.
2. Bytes unchanged both ways: the body byte for byte and every header except the router's own `x-qmx-grant`, which is removed so it never leaves the machine (`anthropic-beta`, `cache_control`, system order, SSE pings, rate-limit headers and error bodies pass unchanged).
3. The router reads `model` and the streamed usage; it logs no header value and keeps nothing past the hop.
4. Never swaps a token between Claude accounts: account choice is which plan home launches the chat (AD-12).
5. Every non-plan lane drops the incoming bearer, then runs the egress stop; a Claude token there fails closed.
6. Canary P1 runs at every boot with echo upstreams; failure keeps the lane off.
7. Settings `router.plan_lane: on | off` per Claude account.

### 2.5 Edge cases the routing must survive

- A Claude id on a Kimi-main chat: refused by the router with a message that names `delegate`; the copilot uses `delegate` to a plan profile.
- A sub-agent naming an unknown id: 400, the CLI reports a failed sub-agent, the parent continues.
- A provider without tools or vision behind a sub-agent that needs them: the router refuses the request naming the missing capability; workflow roles never resolve to it (AD-13).
- Thinking signatures: each sub-agent's conversation stays on one model; a provider fallback inside a conversation drops earlier thinking blocks (Pi rule; AD-39).
- DeepSeek's 400 on unknown non-`claude` ids and Qwen Token Plan's `auto`: the registry maps QMX ids to native ids.
- Kimi Code's User-Agent rule: never rewritten (request overrides cannot touch it).
- Ollama Cloud with no prompt cache: full resends accepted, fewer and larger chunks, spans marked `uncached`.
- A plan 401 through the plan lane: forwarded unchanged, the CLI's recovery runs, the pool benches that account and asks him to sign in again.
- A workflow on Contabo: Contabo's router has its own plan lane only for Contabo's own plan homes (signed in there by him); burst placements use Contabo's router without a plan lane.

### 2.6 What he believed that is not so (C-77, said plainly)

- "We already built our own load balancer; we shall have to delete that code": no pool was ever built [retrieved `core/ladder.py:28` logs "skipped: no pool"]; nothing is deleted.
- "Hermes lets sub-agents use different models": Hermes pins the sub-agent model globally (no per-task model), and its Anthropic OAuth path bills extra-usage credits, not the Max allowance [37d §1.2, §6.5]. QMX's design does more than Hermes here.
- "Hermes as a provider over RPC": Hermes serves an agent, not a model; it fits only as a `cli` delegate target (AD-41).

---

## 3. The caps removal design

**Principle (settled):** QMX never refuses, pauses or ends work on a usage number of its own. The providers' limits are the only limits. Per-account configuration (strategy, share, ceilings he sets himself) lives in the UI, CLIProxyAPI-like in capability, not look, and is empty by default.

**The `max_turns`-type question, decided on that principle:** a turn count, a tool-call count, a token count and a wall time are all usage numbers, so none has a default anywhere (harness `max_turns` 50, engine `agent.max_turns` 12 and `max_tool_calls` 200, `timeout.agent.run` 1,800 s and `timeout.script.run` 600 s all go). An agent that is genuinely stuck or looping is stopped by detection that needs no usage number:

| Detector | Trigger | Action |
| --- | --- | --- |
| No progress | no tool call, turn, log line or chunk event past `timeout.idle` (300 s agent, 600 s script with no output and no CPU), or `timeout.in_tool` (1,200 s) while a tool call is open; sleep-aware clock | warning at 80 % through the steer channel, interrupt, 120 s grace, `stalled`, then the ladder |
| Loop signature | the same tool call (name and argument digest) with the same result digest 5 times in a row, or 8 turns with no new result and no output change | one tool-less summary turn, `stalled(loop)`, then the ladder |
| Repeat error | the same node fails twice with one signature | doctor; a third time parks |
| Zero tokens | a run with no events and no tokens past `timeout.idle` while not in a recorded wait | watchdog line, ladder |
| Crash loop | a run interrupted by engine restarts three times | park |

Idle thresholds are liveness, not usage: a turn that is producing anything never trips them. A `limits` block he writes himself is honoured as a pause he can resume; none ships.

**Fan-out end to end (his playlist, Firecrawl and macro case):** expansion never asks; chunks are sized from each model's window; chunks run up to host capacity (RAM-derived sessions and chat slots) on `contabo`, spill to burst rows, and queue otherwise; a provider 429 or 402 cools one account and the next chunk takes another; finished chunk memos stand through restarts; nothing in QMX counts tokens, turns or time against a ceiling. SOLUTION-DESIGN §26.13 S2 and S3 walk both cases; live check E43 proves a two-chunk 600k-token run and a six-hour run end `passed` with no pause.

**Every limit, its fate and its code location:** SOLUTION-DESIGN §26.3.

---

## 4. Hermes validation: all 142 rows of 37d

Verdicts: **ADOPT 119, ADAPT 18, DEFER 4, REJECT 1** (142). ADOPT names the landing AD and the change; ADAPT says how it differs from Hermes; DEFER names the owner; REJECT says why. "Lands in" uses engine AD numbers unless a spine is named.

| Id | Verdict | Lands in | Backend change | UI landing | Refactor / rebuild, or why and owner |
| --- | --- | --- | --- | --- | --- |
| H-01 | ADOPT | AD-41, AD-38 | one `resolve_child_runtime` function; `delegate` takes `role/model/profile/effort` | helper row shows provider, model, effort | refactor `delegate(profile, prompt)` signature (H26) |
| H-02 | ADOPT | AD-41 | handle at once, batches of 10, no ceiling, results between parent turns | live dock | **rebuild** the blocking call path (`harness.py:425`) |
| H-03 | ADOPT | AD-41 | `list`, `steer`, `stop` on the same tool; `missed_steer` reported | Steer "queued", "steer did not land" | new |
| H-04 | ADOPT | AD-4, AD-41 | one correction turn with errors verbatim, then raw text `schema_valid: false` | schema badge on result | extend `nodes/agent.py` (already needs `output_schema_ref`) |
| H-05 | ADOPT | AD-41, AD-42 | up to 8 images forwarded; describer when the child has no vision | image chips on helper rows | new |
| H-06 | ADAPT | AD-41, AD-15, Library AD-6 | live transcript per child as a Library trace blob with a manifest | open helper transcript | Hermes prunes after 7 days; QMX keeps the item (archive, never delete) and drops only the transient blob after `transient_retention` |
| H-07 | ADOPT | AD-41, AD-24 | child processes in the child's Job object or container; hand-off to parent; `orphaned_processes` on the result | processes block in the dock | new |
| H-08 | ADOPT | AD-16 | progress-based stall: 80 % warning through steer, interrupt, 120 s grace, `stalled` | `stalled` badge | extend `watchdog.py`; fits the no-caps rule (no usage number) |
| H-09 | ADOPT | AD-41 | completions table in `control.db`: stored before announce, claimed once, `unknown` if owner died | "Turn lost during restart" never loses a result | new |
| H-10 | ADOPT | AD-41, AD-43 | children inherit tools only; deny list (delegate, clarify, home/operator memory, send, schedule) | none | written once as a deny list |
| H-11 | ADAPT | AD-4, AD-41 | depth as a setting, default 1; `orchestrator` role may delegate | none | Hermes' one-shot "2 children" cap rejected (a usage cap); depth is structure, kept |
| H-12 | ADOPT | AD-49, Library AD-20 | worktree per child, result reports `path, branch, commits, dirty`, prune with proof | branch chip, "changes ready to merge" | new |
| H-13 | ADOPT | AD-12, AD-38 | lease per `(session, provider)`; same provider shares the parent's pool | account alias on helper rows | pool not built (L2) |
| H-14 | ADOPT | AD-39 | wire is a model-row field; `/anthropic` suffix used only as an onboarding hint | none | refactor the `wire` row flag into the model row |
| H-15 | ADOPT | AD-13 | none: role candidate lists already give each node its own ladder | none | built (`roles.py`) |
| H-16 | ADOPT | AD-38, AD-28 | `model_scope` on every grant and pass, enforced on every lane (H14) | none | designed; now on every lane |
| H-17 | ADOPT | AD-13 | auxiliary roles `titler, compactor, curator, vision_describer, transcriber, video_analyst, goal_judge, reviewer, background_review` | warning when an auxiliary role is on another provider | add rows to the role table |
| H-18 | ADOPT | AD-10 | triggers apply `role_pins` and `effort_pin`; agents cannot change them | pins on the trigger form | code fix (B-60; stored but unread at `triggers/rows.py:10`) |
| H-19 | ADOPT | AD-11, AD-21 | per-node role override for one run, `user` principal only, recorded on `run_created` | "run with…" picker | new |
| H-20 | ADAPT | AD-46 | Mixture of Agents as an engine template (references without tools, one acting aggregator) | template card | the relay virtual-model form rejected: one engine owns control flow |
| H-21 | ADOPT | AD-41 | `delegate` target kind `cli` (Codex CLI, Kimi Code, OpenCode CLI); missing binary fails | helper row shows "CLI" | new; Kimi Code's own CLI keeps its User-Agent rule |
| H-22 | ADOPT | AD-38 | none: QMA v2 already wraps a foreign runtime (Claude Code) the same way; the GPT lane is this shape | none | confirmation only |
| H-23 | ADAPT | AD-12 | strategies `least_used` (default for background), `round_robin`, `fill_first`, `reset_window`, `random`; `priority`, `background_priority` | Accounts page | Hermes' default `fill_first` rejected (settled: not fill-first) |
| H-24 | ADOPT | AD-12, AD-40 | classifier-driven 429/402/401/entitlement rules; provider `reset_at` wins | cooldown with reset time | pool not built |
| H-25 | ADOPT | AD-12 | cooldowns keyed `(account, model)` | per-model cooldown chip | new |
| H-26 | ADOPT | AD-12 | move back at turn start when the bench lifts; explicit switch cancels | "moved back" line | designed |
| H-27 | ADOPT | AD-12, AD-17 | dead OAuth reported once, out of rotation; status reads are peeks | "sign in again" | new |
| H-28 | ADOPT | AD-12, AD-28 | GPT refresh under a cross-process file lock; never older over newer | none | new; never for Claude (the CLI owns its login) |
| H-29 | ADOPT | AD-28 | reference-only secrets (ref and fingerprint) | key list shows fingerprints | designed |
| H-30 | ADOPT | AD-39 | `KeyProvider` → data profiles with the listed fields | provider form | **refactor** `profiles.py` (H29) |
| H-31 | ADOPT | AD-39 | per-model capability table feeding router, chunker, compaction, multimodal, roles | capability chips | new |
| H-32 | ADOPT | AD-39 | wire per model (OpenCode, Nous dual-wire) | wire shown per model | **refactor** the row flag (UI-HANDOFF §9 row 3 rewritten) |
| H-33 | ADOPT | AD-39 | live catalog merged with a curated fallback list | model picker refresh | new |
| H-34 | ADOPT | AD-39, AD-12 | provider usage hook feeds `least_used` and `reset_window` | per-account readings | partial (plan meter HG2) |
| H-35 | ADOPT | AD-40 | one closed error classifier with hints for pool and ladder | failure card by class | new (same as H-117) |
| H-36 | ADOPT | AD-39 | one-token "Test" on the pinned wire | Test button | new |
| H-37 | ADOPT | AD-39 | request overrides per provider and role, merged one level deep; never User-Agent | advanced provider fields | extends `strip_fields`/`cache_markers` |
| H-38 | ADAPT | AD-19 | mini-app model calls through `Harness.complete` under the app's grant | none | a generic local pass-through port for any app rejected: one more door; apps get `llm_complete` instead |
| H-39 | ADOPT | AD-19 | `llm_complete(role, schema)` for mini apps, trust-gated, audited | app usage on its card | new (needs H3) |
| H-40 | ADOPT | AD-39 | effort clamp shown as sent | effort pill `Ultra→Max` | partial |
| H-41 | ADAPT | AD-43 | answers per context: engine `deny` at once, copilot waits | Approvals settings | Hermes "smart" LLM approver rejected for money and MANAGE |
| H-42 | ADOPT | AD-43 | destructive-shell floor after the money gate | floor shown read-only | harness change (H31) |
| H-43 | ADOPT | AD-43 | never-allow globs on normalised commands, Settings-editable | Rules page | today code-defined (`money.py:717`) |
| H-44 | ADOPT | AD-43 | optional attended timeout, fail-closed, not a denial; engine deny at once | "expired, re-run from here" | partial (`unattended_ask_seconds`) |
| H-45 | ADOPT | AD-43 | suggestions mined from his approvals, never destructive, never auto-applied | "suggested" rows | new |
| H-46 | ADOPT | AD-43 | secret in an outbound command body; invisible or bidi Unicode | refusal reason shown | harness change (H31) |
| H-47 | ADOPT | AD-43, AD-24 | NT device and UNC paths refused | none | harness change (H31) |
| H-48 | ADOPT | AD-24, AD-25 | container tiers need no per-command prompts; the container is the boundary | none | already consistent |
| H-49 | ADOPT | AD-43, AD-18 | context-file and persona scan at load; his own files warn and load | warning chip | new |
| H-50 | ADOPT | AD-43, AD-48 | supply-chain advisory check in the doctor at start | banner | new |
| H-51 | ADAPT | AD-43 | money and risk/sizing keys locked against agents; his explicit unlock | lock icon | Hermes' managed scope pins against the user; QMX has one user, so it pins against agents |
| H-52 | ADOPT | AD-36, AD-24 | env passthrough only for declared tool keys; credential files read-only | none | designed |
| H-53 | ADOPT | AD-43, AD-44 | one SSRF guard (private, CGNAT, metadata, redirects re-checked) | none | partial |
| H-54 | ADOPT | AD-43, AD-44 | one website blocklist for every URL tool and the browser | blocklist in Settings | designed |
| H-55 | ADAPT | AD-44 | site-login vault: masked, filled into the page, never seen by the model, TOTP | Passwords & Logins page | logins only; card and payment fills rejected (prohibited); broker logins rejected (money boundary) |
| H-56 | ADAPT | UI-HANDOFF §11 | none | confirm on clear/new/reset | under archive-never-delete "clear" archives; UI only |
| H-57 | ADOPT | AD-43 | first-run import of `~/.claude` permissions, MCP servers, skills by digest | import card | new |
| H-58 | ADOPT | AD-10 | none: pre-dispatch validation → `blocked_config`, zero tokens | none | built (`triggers/preflight.py`) |
| H-59 | ADOPT | AD-10 | spend-neutral re-run at 5, 15, 30 min when the model was unreachable before any call | "retrying at" line | new |
| H-60 | ADOPT | AD-10 | quota hold with one early retry for sparse schedules | held-until line | built (`triggers/quota.py`); check the sparse rule |
| H-61 | ADOPT | AD-17, AD-10 | failure streak becomes one incident nudge | incident row | partial (`failure_streak` built) |
| H-62 | ADOPT | AD-10 | `[QMX_FAILURE]` / `[QMX_SILENT]` first-line script contract | silent and failed badges | new |
| H-63 | ADOPT | AD-10 | delivery field `delivered | unverified | failed | none`; empty payload fails closed | "passed" and "delivered" apart | new |
| H-64 | ADOPT | AD-10 | create a trigger paused with a reason in one write | paused badge with reason | new |
| H-65 | ADOPT | AD-7, AD-10 | none: a fire keeps its identity until output and delivery recorded | none | designed |
| H-66 | ADOPT | AD-10 | none: `after` trigger plus `continuity` | none | built |
| H-67 | ADOPT | AD-47 | heartbeat as session state, trigger kind `session` | heartbeat card | new (H34) |
| H-68 | ADAPT | AD-47 | `loop` fixed or self-paced, ends on `LOOP_COMPLETE`, `--times`, `--until` | loop card | Hermes' default `max_ticks` budget rejected (AD-40); `--times` is his choice |
| H-69 | ADAPT | AD-47 | `goal` with a judge and a completion contract | goal card | the default turn budget rejected (AD-40); no-progress detection stops a stuck goal |
| H-70 | ADOPT | AD-46 | templates gain a `slots` schema and guided fill; install only suggests | template fill-in | Library AD-3 `slots` |
| H-71 | ADOPT | AD-46 | one Suggestions source set; dismissals latch | Suggestions list | new |
| H-72 | ADOPT | AD-10 | `event`, `webhook`, `session` trigger kinds | trigger form | forward migration of the kind check (`ledger/migrations.py:35`) |
| H-73 | DEFER | AD-10 Deferred | none now | none | managed cron provider; owner: engine, when a serverless placement must own a schedule |
| H-74 | ADOPT | AD-48 | keep the PC awake while a turn or run is in flight | setting | new |
| H-75 | ADOPT | AD-26 | copilot `background_review` fork after qualifying turns; `/refine` | "learned" chips | probe P-FK first (H37) |
| H-76 | ADOPT | AD-46, Library AD-3 | skills, templates, blueprints share one lifecycle | lifecycle badges | designed in parts |
| H-77 | ADOPT | AD-46 | `/learn` from a folder, a URL or a chat | "learn a skill" action | new |
| H-78 | ADOPT | AD-46 | curator workflow: usage, stale 14 d, archive 30 d, pins and trigger refs protected, consolidation off | stale and archived states | new; archive, never delete |
| H-79 | ADOPT | AD-46 | skill lint and `requires_tools` activation | lint findings | new |
| H-80 | ADOPT | UI-HANDOFF §11 row 25, AD-18 | none: reads memory rows and skills over time | Memory Graph | UI only |
| H-81 | ADAPT | AD-18 | operator-scope memory proposals from copilot chats staged for his accept | Memory page | workflows keep writing without asking (ruling 57); only the operator scope stages |
| H-82 | ADOPT | AD-19, AD-44 | `app.toml [app]` declares desktop apps; availability gates tools | app availability chip | new |
| H-83 | ADOPT | AD-45 | transcript directives and one registry | inline widgets | new |
| H-84 | ADOPT | AD-45 | `::preview` sandboxed frame with capped talk-back | interactive explainers | new |
| H-85 | ADOPT | AD-45 | one contribution registry for core and mini apps | UI shell | UI session builds it |
| H-86 | ADOPT | AD-19 | `[settings]` form, `[capabilities]` delta consent, kill list, state outside the install | app settings and consent | new |
| H-87 | ADOPT | AD-4 | exactly one terminator, `expected_run_id`, stranded detection | none | mostly designed |
| H-88 | ADOPT | AD-4 | default output schema for build agents (`changed_files … residual_risk`) | result card fields | new |
| H-89 | ADOPT | AD-49 | `reconcile` template with a neutral third agent; hotspot flag | reconcile card | new |
| H-90 | ADOPT | AD-46 | completion contracts as `rule` nodes in build templates | checks on the run card | new |
| H-91 | ADAPT | AD-16 | a warning at 90 % applies only to a limit he wrote, then one summary turn | "near your limit" line | no default iteration budget (AD-40) |
| H-92 | ADOPT | AD-45 | file paths in replies become artifact chips | artifact chips | new |
| H-93 | ADOPT | AD-25 | `sandbox_python` with a `qmx` tool stub; only `print()` returns | none | new (H8) |
| H-94 | DEFER | Deferred (engine) | none now | none | trajectory export; owner: the Lab ML packet when traces become training data |
| H-95 | ADOPT | AD-44 | real-profile snapshot by SQLite online backup, pinned, deleted when off | "close your browser to refresh" | new |
| H-96 | ADOPT | AD-44 | take-over lease with an epoch; screen inside the sandbox | Take over / Hand back | new |
| H-97 | ADOPT | AD-44 | browser provider interface; private URLs local | provider choice in Settings | new |
| H-98 | ADOPT | AD-33, AD-43 | standard, bounded, unrestricted mapped to manifests | mode on the manifest editor | designed |
| H-99 | ADOPT | AD-33 | screenshot eviction in batches; ~1,500 tokens each | none | new |
| H-100 | ADOPT | AD-44 | labelled cursor overlay per agent | cursor labels | new |
| H-101 | ADOPT | AD-44 | WebM recording as a trace artifact | play recording | new |
| H-102 | ADOPT | AD-44 | CDP supervisor (dialogs, `closed_by`, frame cap, reconnect limit) | none | new |
| H-103 | ADOPT | AD-48, AD-30 | immutable install tree, one data volume | none | new |
| H-104 | ADAPT | AD-30 | one supervisor on Contabo (systemd units), containers only per attempt | Machines list | Hermes' s6-in-one-container replaced by host systemd, which AD-25 already names |
| H-105 | ADAPT | Library AD-3 (`agent` kind) | an agent profile is a Library `agent` item (folder): persona, pins, skills, packs, routines, home machine; one writer | agent page | git-distribution of profiles deferred; export strips keys |
| H-106 | ADAPT | Library AD-3, AD-41 | backend shape of the Bots roster: `agent` items, routines as triggers, @mention = delegate to that agent | Bots roster (UI-HANDOFF §11 row 10) | organogram meaning (who the Lab, Portfolio and hub agents are) is methodology work later (B26, B30) |
| H-107 | ADOPT | AD-30 | device names, `name@machine` | Machines list | partial |
| H-108 | ADOPT | AD-49 | worktree per agent, chat follows the agent | branch chip | new |
| H-109 | ADOPT | AD-49, Library AD-20 | shadow-git checkpoint before destructive edits; single-file restore | restore action | new |
| H-110 | ADOPT | next plan's dev workflow (not runtime) | linked dependency trees in `D:\QMX-worktrees` worktrees; worker images share one deps layer | none | process, not an AD; also used by AD-49 |
| H-111 | ADOPT | AD-35 | recap on resume in another surface | recap strip | new |
| H-112 | ADOPT | AD-42 | `@file`, `@folder`, `@url` with line ranges, size handling and sensitive-path blocking | composer references | new |
| H-113 | DEFER | AD-28 Deferred | none now | none | secret-source plugins (1Password and the like); owner: vault, when he asks |
| H-114 | REJECT | — | — | — | content-free metrics shared with a maintainer; QMX has no outside metrics recipient, and its metrics stay local (AD-15, Prometheus/Loki on Contabo) |
| H-115 | ADOPT | AD-15 | correlation ids across router journal rows, harness hooks and engine spans | trace links | designed (H16) |
| H-116 | ADOPT | AD-15 | prompt-surface snapshot test per chat kind and node kind in CI | none | new |
| H-117 | ADOPT | AD-40 | the one classifier (same as H-35) | failure card by class | new |
| H-118 | ADOPT | AD-34 | engine-built re-seed for the compaction fallback | `compacted` marker | new |
| H-119 | ADAPT | AD-16 | one tool-less summary turn when the loop detector or a limit he wrote stops an agent | summary shown on `stalled` | no default `max_turns` exists to trigger it (AD-40) |
| H-120 | ADOPT | AD-16, AD-48 | crash-loop counter per run; active-turn marker for copilot chats | safe-mode banner | partial (`harness.py:254`) |
| H-121 | ADOPT | AD-34, AD-39 | compaction point per window: 0.40 at 512k and above, 0.75 below | none | new |
| H-122 | ADOPT | AD-16, AD-34 | a fallback re-runs preflight and the chunk plan | none | new |
| H-123 | ADOPT | AD-23 | derived indexes rebuilt, corrupt files quarantined | doctor line | new |
| H-124 | ADOPT | AD-28 | one run-scope context value that fails closed | none | new |
| H-125 | ADOPT | AD-16 | sleep-aware watchdog clock | none | new |
| H-126 | ADOPT | AD-15 | "waiting on model, first token" state | status line | new |
| H-127 | ADOPT | AD-21 | reconnect snapshot, honest terminal status, idempotent mutations | every window shows the same state | partial |
| H-128 | ADOPT | AD-34 | `ToolDef.available()`, timeouts; results over `inline_limit` spill to artifacts, never silently cut | none | new |
| H-129 | ADOPT | AD-43 | Unicode tag characters stripped from MCP results | none | new (H31) |
| H-130 | ADOPT | AD-19 | `qmx app check` as doctor and publish gate | app check report | new |
| H-131 | ADOPT | AD-19, AD-35 | activation split, lazy MCP servers | none | new (H32) |
| H-132 | ADOPT | AD-35 | tool-search probe first; bridge only if needed | none | probe-gated |
| H-133 | DEFER | Deferred (engine) | none now | none | LSP for builder chats; owner: the builder packet once the copilot builder works |
| H-134 | ADOPT | AD-42 | `doc_read` with a scanned-PDF warning and SQLite preview; full papers for research templates | "reading" chip | new (closes M-14 with alphaXiv as a declared tool) |
| H-135 | ADOPT | AD-10, AD-17 | trigger incidents given logic | incident rows | partial (`incident_id` stored, unread) |
| H-136 | ADOPT | AD-10 | `service.explain_trigger` | "why didn't it fire" panel | new |
| H-137 | ADOPT | AD-48, AD-15 | dead-man switch outside the engine; health gauges; absent-series alerts | engine health badge | new |
| H-138 | ADAPT | AD-48 | snapshot every store before a migration step (keep 3) | none | the backup exit-code contract deferred: data and backups are held (ruling 91) |
| H-139 | ADOPT | AD-25, AD-28 | egress deny list with CGNAT plus one tailnet address; fail closed | none | designed |
| H-140 | ADOPT | AD-48 | event-loop watchdog, restart-loop breaker, safe mode | safe-mode banner | new |
| H-141 | ADOPT | AD-18, Library AD-3 | `persona` item slot and Hindsight binding rules | persona box in Settings | the persona's text is methodology work with him later (B29) |
| H-142 | ADOPT | AD-28 | single-use pairing code for a new placement | pairing card | new |

---

## 5. Alignment resolution: every mismatch and chat-only item of parts A, B and C

### 5.1 Part A (Friday morning): mismatches M-1 to M-18

| Id | Item | Outcome | Where |
| --- | --- | --- | --- |
| A M-1 | MT5 click-through denied by AD-33 | **Resolved.** Agents may set up strategies in his installed MT5 and cTrader on a pinned demo account; live and order tickets stay blocked; money gate first | engine AD-33, AD-44; SD §24, §26.7; E46 |
| A M-2 | 50 % cap and $5 survive | **Resolved.** No usage caps of any kind; harness budgets unset by default (H28); engine defaults removed; UI row 15 rewritten; SD §7.4, §17 rewritten | AD-9, AD-16, AD-40; SD §26.3; UI-HANDOFF §9.15. BACKLOG and UI-NOTES lines: owner planning lead (audit edits) |
| A M-3 | "Plugins are the contract to mini apps" has no load path | **Resolved.** App tools are namespaced rows in the `qmx` MCP server per the session's pack set; skills as Library skills; widgets as directives; agents as delegate targets; plugin lock untouched; Lab AD-14 wording aligned | AD-19, AD-35, AD-45; Lab AD-14; H32 |
| A M-4 | Funnel template does not match "pour in garbage, mostly automated" | **Resolved in design.** Plain names, playlist and saved-collection intake without asking, chunked fan-out, cron or monitor trigger, visual pass, browser-based Instagram and TradingView rows | AD-46, AD-42, AD-44; SD §26.9; template packet |
| A M-5 | Output methodology has no architecture | **Resolved (contract).** Directives, previews with talk-back, grade before display, one registry; screen-by-screen methodology later with him | AD-45 |
| A M-6 | Copilot browser and shared watching not designed | **Resolved.** Browser pack for the copilot and workflows, logged-in snapshot, leases, take-over with epoch, HUD; plain journeys still go to him first (ruling 30) | AD-44; H35; UI-HANDOFF §12 rows 10-11 |
| A M-7 | Board "fewest iterations" levers not live | **Resolved.** Lab AD-18 | Lab AD-18 |
| A M-8 | Methodology, organogram, prompts owed | **Deferred**, owner: operator with the planning lead (B26-B29, ruling 82). Dependencies named: the autonomy row (AD-35), the persona text (AD-18), the explainer screens (AD-45), the Bots roster meaning (Library `agent` kind) | 39 §10 |
| A M-9 | Five-quant journeys only in archived files; fifth lens unconfirmed | **Deferred**, owner: methodology session for the journeys file; the fifth lens is an open operator call; nothing is built on it | 39 §10; engine Deferred |
| A M-10 | Mini-app "does it work and render" and DevOps outside the spine | **Resolved.** `qmx app check` (manifest, contract tests, shadow run on haiku, render check in four prop states), health, logs, incidents, usage; Lab dependency through `app_op`; self-feed only through a declared edge | AD-19 |
| A M-11 | Builder covers workflows only | **Resolved in design.** One lifecycle for skills, templates, blueprints; `/learn`; skill lint; `agent` kind for agents as folders; methodology builder content later | AD-46; Library AD-3 |
| A M-12 | Model-agnostic code residue (`claude/fable`, Kimi test default) | **Resolved as a code item** in the next plan's hygiene step; AD-13 already says no Fable and haiku tests | AD-13; DOC-CHANGES 35 |
| A M-13 | MIS versions in the Lab | **Deferred**, owner: risk session | Lab OPEN-7 |
| A M-14 | alphaXiv and full-paper reading | **Resolved.** `doc_read` gives full papers; alphaXiv joins as a declared tool key (`qmx/tool/alphaxiv`) | AD-42, AD-36 |
| A M-15 | Combining packs mid-session | **Resolved.** Pack set on the session record, `tools/list_changed` (probe P-PK), fallback at next turn on the same session | AD-35; H32 |
| A M-16 | Portfolio backend | **Deferred**, owner: risk session (unchanged); Portfolio stays human-driven | Lab AD-11, AD-12 |
| A M-17 | Traces-first principle | **Resolved.** One rule in the builder | AD-22 |
| A M-18 | Stale `session-homes` ticket | **Deferred (process)**, owner: planning lead's Wayfinder refresh | — |

Chat-only items of part A: 1 (MT5) → M-1; 2 (copilot browses as him while he watches) → AD-44; 3 (apps consuming their own output; apps depending on the Lab) → AD-19; 4 (does the app work and render) → AD-19 `qmx app check`; 5 (widgets in chat, preview modes) → AD-45; 6 (fifth quant) → open call; 7 (journeys are situational; copilot always present) → AD-35 combined sessions, journeys file deferred to methodology; 8 (strategies from papers) → AD-42 and M-14; 9 (the lead's reading of why he iterated on WF1/WF2) → **rejected as a ratified claim**: templates follow his own line-883 criticism (plain names, AD-46); 10 (traces before graph) → AD-22; 11 ("don't just accept my ambiguity") → methodology, deferred.

### 5.2 Part B (Friday afternoon and evening): mismatches 1 to 15

| Id | Item | Outcome | Where |
| --- | --- | --- | --- |
| B 1 | QMX-side caps still exist | **Resolved** (as A M-2) | AD-40 |
| B 2 | Default pool strategy fill-first; copilot account not protected | **Resolved.** `least_used` default; copilot account `background_priority: last` | AD-12; SD §7.3 |
| B 3 | GPT capped at one account | **Resolved.** Any number of GPT sign-in homes; plan logins per machine; plan sign-in on Contabo and an owned Amp runner closed yes | AD-12, AD-28; H33; engine OPEN 3 closed |
| B 4 | OpenCode excluded | **Resolved.** In-house chat lane (H12); OpenCode Zen and Go as data profiles with wire per model | AD-38, AD-39 |
| B 5 | Template names and template A's limits | **Resolved in design** (as A M-4) | AD-46; SD §26.9 |
| B 6 | Fable in the strong ladder | **Resolved as a code item** | AD-13 |
| B 7 | Test defaults (OpenRouter first); ruling 105 missing | **Resolved** in the architecture (AD-11, SD E21); code item; ruling 105 is the planning lead's edit to 26 | AD-11; DOC-CHANGES 38 |
| B 8 | Q1 reading never confirmed | **Resolved by the latest-wins reading:** agents start runs inside an enabled scope any time; a new recurring schedule waits for his one yes (ruling 80 is later than Q1) | Lab AD-13; Lab OPEN-5 note |
| B 9 | Desktop app has no owner | **Resolved.** AD-48 owns supervision, startup, health; the shell framework is a probe in the desktop packet | AD-48 |
| B 10 | QMX cannot yet create workflows through the copilot | **Resolved in design:** the builder is core, its own packet, E42 | AD-22 |
| B 11 | Ticks outside the Library | **Deferred**, owner: the deeper data study (ruling 91); the reason is written for him | Library Deferred |
| B 12 | 10 GB tick history has no backup | **Deferred** (data held, settled), owner: the data study; the risk stays named | engine Deferred |
| B 13 | Engine decisions D, E, F unasked | **Framed** for him (36 verdicts applied to the framing); see §10 | engine OPEN-DECISIONS |
| B 14 | Which UI build holds the Library he described | **Resolved on the backend** (every kind he named is in the roster); the build check goes to the UI session | Library Deferred; UI-HANDOFF §12 row 19 |
| B 15 | UI-HANDOFF caps row | **Resolved** | UI-HANDOFF §9.15 |

Chat-only items of part B: 1 (non-loaded accounts; copilot account) → AD-12; 2 (fan-out scale end to end) → AD-40, AD-34, SD §26.13 S2-S3; 3 (QMX must create workflows) → AD-22; 4 ("we have hooks" as the workflow guard) → AD-43 (his rules guard every engine chat; hook scripts are `script` nodes on bus events, no second hook system); 5 (which UI build) → B 14; 6 (central/dependent/independent map only in a published page) → **deferred (process)**, owner planning lead (README index); 7 (tick backup) → B 12; 8 (the lead's terms claims: GPT rotation, GLM coding plan) → **rejected** by rulings 38 and 100; "GPT capacity one" removed.

### 5.3 Part C (Friday night to today): mismatches M-1 to M-20

| Id | Item | Outcome | Where |
| --- | --- | --- | --- |
| C M-1 | Plan main with API sub-agents forbidden by AD-29 | **Resolved:** A + B + D | AD-38, AD-29, AD-41; §2 |
| C M-2 | Background cap and $5 | **Resolved** | AD-40; H28 |
| C M-3 | Fable in the ladder | **Resolved** (code item) | AD-13 |
| C M-4 | Test model default | **Resolved** (code item; E21) | AD-11 |
| C M-5 | Templates "should work"; 10 of 31 break | **Resolved in design:** manifest `tier` and `network` per script, five network templates declared, `capture.py` to the container, three refused templates fixed by the narrowed scan; the packet is done only when all 31 pass | AD-24, AD-36, AD-46; E48 |
| C M-6 | Compaction and chunk sizing per model | **Resolved:** registry window; 0.40 at 512k and above, 0.75 below | AD-34, AD-39 |
| C M-7 | Hooks, caching and tool lists | **Resolved in the request:** H2 per 36 C1, H19 in HG3 (his call D); H21 deferred with a size cap | HARNESS-REQUESTS HG3 |
| C M-8 | Inbox and waits | **Resolved:** the cap path that wrote `needs_you` goes (AD-40); time waits wake by themselves (AD-10, B-63 in the plan); H2 first | AD-10, AD-40 |
| C M-9 | Is the runaway guard a cap? | **Resolved:** yes, it goes; only stuck and loop detection stay | AD-16, AD-40 |
| C M-10 | Live CLI bypass; proposal actions | **Resolved:** CLI test-only (already AD-11); proposal actions a closed enum | AD-11, AD-17 |
| C M-11 | Provider-hosted harness scope | **Resolved by the architect:** allowed as a leaf attempt with key accounts | AD-30; engine OPEN 2 closed |
| C M-12 | Central proxy (Theo's model) | **Resolved:** one router per host; key traffic may centralise on Contabo; plan bytes never leave their machine | AD-38, AD-28 |
| C M-13 | Ruling wording gaps in 26 | **Deferred (process)**, owner planning lead; the substance is listed in DOC-CHANGES 38 | — |
| C M-14 | Coding plans and multimodal | **Resolved:** `use` default `any`; multimodal layer | AD-39, AD-42 |
| C M-15 | Provider wire per model | **Resolved** | AD-39 |
| C M-16 | One monitoring view across copilot and workflows | **Resolved** | AD-15; H36 |
| C M-17 | Stale orientation and tickets | **Deferred (process)**, owner planning lead (33, MAP, tickets `probe-e24-mixed-providers`, `central-relay-ruling-75`, the data tickets) | — |
| C M-18 | Memory not built, provider not chosen | **Resolved by the architect:** the built-in provider ships first; Hindsight is an optional adapter under binding rules; a memory packet in the next plan | AD-18 |
| C M-19 | Merge base (`engine/base` lacks HP2 and two fixes) | **Not architecture.** His merge click stays in the HANDOFF | — |
| C M-20 | Ruling 95 split holds only for top-level chats | **Resolved** (as C M-1) | AD-38 |

Chat-only items of part C: 1 (Chinese models more than Claude) → AD-13 `key → gpt → plan`, AD-39 windows, AD-34 compaction and no-cache handling; 2 (the SDK limit is solvable) → AD-38; 3 (harness stays, provider contracts change) → AD-38 rule and HG4 "pool exception" rows; 4 (per-sub-agent thinking and tools) → AD-29 `@effort`, AD-39; 5 (one monitoring view) → AD-15; 6 ("the backend is almost done") → §9 here, plainly; 7 (his false premises in ruling 99) → §2.6 here and DOC-CHANGES 38; 8 (Hermes as a provider over RPC) → **closed**: Hermes serves an agent, not a model; at most a `cli` delegate target (AD-41); 9 (no build planning while design agents run) → process, owner planning lead; 10 (the Firecrawl worked example) → SD §26.13 S3; 11 (terms note and input types per row) → **adapted**: input types are the model row's capabilities; a terms note is a free-text field he may fill, never gating (AD-39); 12 (TTS and programmatic integration out; Telegram, SOUL.md, plugin groups in) → TTS out; programmatic integration out as a product surface (only H-127's reconnect snapshot is used inside QMX); Telegram later (ruling 34, Deferred); SOUL.md → the `persona` item (AD-18); plugin groups → automation = templates and blueprints (AD-46), media = multimodal layer (AD-42), web = browser pack (AD-44).

---

## 6. Reviews and triage applied

### 6.1 Study 36 (criticals and should-fixes)

| Item | Applied as |
| --- | --- |
| C1 PowerShell and Monitor missing; H2 named the wrong SDK option | AD-24 lists `Bash`, `PowerShell`, `Monitor`, `Write`, `Edit`, `NotebookEdit`, `WebFetch`; H2 rewritten to the SDK `tools` list with a deny-form fallback; no hook-deny alternative; E35 runs with his real Settings |
| C2 the "hit needs a verb" rule undefined | AD-36 defines the predicate on the input words; `name_money_act_called` lives in `qma-core` next to `name_money_act`; E36 gains `send_order`, `post_order`, a key named `mode` |
| C3 10 of 31 templates break | AD-24 manifest `tier` and `network` per script; five network templates declared; `capture.py` to the container with `yt-dlp` in the worker image; narrowed prose surfaces fix t7, dm and ma; the packet finishes only when all 31 pass (E48) |
| S1 AppContainer claims and E33 rows | AD-24 labels the read, credential and loopback rows [remembered]; self-contained script runtime; E33 rows added |
| S2 one AppContainer profile for all runs | per-attempt profiles |
| S3 Docker on WSL2 weaker than gVisor | AD-25: model-written code defaults to `contabo` (`runsc`); the PC tier is a fallback with no kernel-escape protection, stated |
| S4 "Docker is off" means waiting | start Docker Desktop, then spill to `contabo`, then wait (in AD-24 and in decision E's framing) |
| S5 credential deny-list fail-open | `qmx/tool/<name>` namespace, casefolded, fail-closed broker classing |
| S6 scan bypasses | AD-36 says the scan is a lint and names the three structural layers; non-literal `getattr`/`setattr` refused; non-Python files to the container; host literals checked against the gate's broker list; missed phrasings recorded |
| S7 four redaction paths | sandbox tool results, Library blob contents, memo rows from the redacted payload, stream carry-over buffer; values under 12 characters refused |
| S8 HG3 not minimal | HG3 rows rewritten: H18 close only, H20 and H21 deferred, H23 and H25 dropped, H24 labelling only |
| S9 plain-words over-claim | PLAIN-WORDS and AD-22 name the copilot-shell gap |
| S10 spec-gap code unbudgeted | SOLUTION-DESIGN §26.15 adds a "2b spec-gap code" step; the runaway rows drop with the guard |
| S11 $5 per Background chat | removed (AD-40, H28) |
| S12 the 2M-token default is a fixed cap | obsolete: no guard exists (AD-40) |
| S13 proposal actions chosen by a model | closed enum per proposal type; labels from the action; no "start a paper pod" action (AD-17) |
| N1-N7 | N1 audit hook called a tripwire; N2 set-of-files equality and a runtime hash check; N3 runtime libraries and `yt-dlp` placement; N4 encoded keys an accepted miss; N5 noted (H2 first); N6 obsolete (no pause); N7 holds |

### 6.2 Study 34: SPEC-GAP (26 rows) and LATER-PACKET (15 rows)

SPEC-GAP, settled by 35 and checked again here:
- **Stand as 35 settled them** (code in the hardening plan or the "2b" step): B-15 port names, B-18 event keys, B-24 and B-87 `required` edges, B-27 subworkflows, B-68 enable derived from triggers, B-76 block folders in the bundle, B-78, B-80 and L-84 run context in the script env, B-82 replay fork, B-12 layer diagram, B-14 port kinds, B-23 join words, B-83 typed artifacts, L-20 no clocks in core (holds in code), L-26 `pinData` in the hash, L-42 `WorkerPort.run(job, emit)`, L-23 no Fable in the ladder.
- **Changed by this pass:** B-88 human points are proposals with a closed action enum (AD-17); B-16 agent caps now have no default at all (AD-4, AD-40).
- **Obsolete with the runaway guard (AD-40):** B-38 and L-49 guard numbers, B-49 cache reads in the guard, L-48 wall time across waits, L-46 degrade width.

LATER-PACKET, mapped to packets (SOLUTION-DESIGN §25 and §26.15): B-20 nested fan-out; B-28 and B-32 gate folding (its `resume` now lifts only a pause at a limit he wrote); B-35 chunk retry; B-41 subworkflow child export (Library L11); B-46 and B-81 grader `llm` mode; B-47 `pinData`; B-52 frozen memory snapshot (memory packet, built-in provider first); B-64 engine host chat routes (Appendix G L1); B-34 doctor verdicts (L13); B-40 ledger-derived run state; B-58 verify closed by EP13. **Obsolete:** B-33 "raise the guard and resume" (no guard; gate folding covers his own limits) and B-36 "degrade knows the cheapest candidate" (degrade is gone; the classifier's hints and role ladders cover the doctor's choice).

---

## 7. Blast radius of each changed decision

| Decision | Code it touches (engine/base) | Templates | UI | Other ADs |
| --- | --- | --- | --- | --- |
| AD-38 router lanes | `qma/harness/relay.py` (new plan lane, chat lane, registry resolve), `launch.py` (plan launch env), `profiles.py`, `harness.py` (grants for plan launches), `money.py` untouched | none directly; every agent node can now name third-party sub-agents | live dock, model picker, per-account switch | AD-12, AD-13, AD-28, AD-29, AD-39, AD-41, AD-15 |
| AD-39 model registry | `profiles.py` refactor to data, `roles.py` (capability checks), `core/partitions.py` (window from the registry, not `context_window`), `nodes/agent.py` (compaction point) | role ladders regenerate | provider and model pages | AD-13, AD-34, AD-42 |
| AD-40 no caps | `launch.py:221-261, 518-519` (`Budgets`, `parse_budgets`), `harness.py:362-385` (`BackgroundCap`, `needs_you`), `qmx_engine/settings.py`, `admission.py`, `core/ladder.py` (runaway code), `nodes/agent.py:193-255` (tool-call cap), `watchdog.py` (loop signature) | all 31 set their own `runaway` block today [36 S10]; the blocks are removed or read as `limits` once | Settings budget rows, run cards | AD-9, AD-16, AD-28 (pass), AD-34, Lab AD-12, AD-13 |
| AD-12 pool | new `pool.py`; `admission.py` (share default gone); `settings.py` (strategy) | none | Accounts page | AD-9, AD-38, AD-28 |
| AD-41 `delegate` v2 | `tools.py:388` `delegate_def`, `harness.py:425` `_delegate` (rebuild), `control.db` completions table | engine agents with `via: delegate` | live dock | AD-4, AD-15, AD-49 |
| AD-42 multimodal | harness turn routes, composer, new roles | template A visual pass | composer chips | AD-13, AD-39, AD-41 |
| AD-43 permissions | `money.py` deny rules made data (gate unchanged and first), harness asks (`chat.py:24`) | none | Rules page | AD-4, AD-22, AD-33 |
| AD-44 browser and desktop | new browser pack, Cua pack manifests, tool rows for Interactive chats | template A intake rows | browser pane, take-over, HUD, Passwords page | AD-33, AD-19 |
| AD-33 MT5/cTrader demo | Cua manifest schema, driver account check | none | manifest editor | AD-44, money gate |
| AD-45 output | UI registry; `render-and-grade` stays | every template's `schemas/output.json` may gain directive output | chat renderer | AD-19 |
| AD-46 lifecycle and names | `templates/catalog.py`, every template folder id, `a-fill-the-library/scripts/intake.py` and README, Library kinds | all 31 (ids and titles) | template fill-in, Suggestions | Library AD-3, AD-22 |
| AD-19 / AD-35 pack load path | `qmx` MCP server tool listing, control session record | MA template | combined sessions | Lab AD-14 |
| AD-24 / AD-36 / AD-37 (36 fixes) | `definition/lint.py`, `qma-core` descriptors (`name_money_act_called`), `workers/local.py`, script runtime, `ledger/memo.py`, Library adapter | t7, dm, ma, a, rv, db, t4, rs1, rs4, t3 | none | AD-25 |
| AD-48 desktop host | new `qmx-desktop` package | none | startup card, safe mode, windows | AD-3, AD-24 |
| AD-16 stuck detector | `watchdog.py`, `core/ladder.py` | none | `stalled` badges | AD-40 |

---

## 8. Scenarios and edge cases

SOLUTION-DESIGN §26.13 walks fifteen scenarios (helpers on Kimi and Qwen under Opus, a 300-video playlist, the Firecrawl pipeline, 429 mid-chunk, 402, a plan 401, a crash mid-chunk, mixed providers where one lacks tools, an image to a text-only model, all Kimi and GLM accounts exhausted, the PC offline, Contabo unreachable, his copilot account busy, MT5 demo set-up, a 2FA wall). Further failure paths checked in this pass:

| Case | Behaviour |
| --- | --- |
| Restart while a `delegate` v2 child runs | its completion is stored before announce; at restart the child reads `unknown` if its process died, else it resumes and delivers once |
| Account exhausted while the copilot is mid-turn | the CLI receives the provider's 429 unchanged (plan lane) or the router rotates the key (key lane); the copilot shows "retry when the limit resets at HH:mm" |
| His only Claude account benched by a 401 | engine roles fall to the next candidate (key or GPT); copilot chats on that account show "sign in again"; no workflow waits on him |
| Router boot canary fails | plan lane off on every Claude account, one `black` item; everything else runs |
| A model row is wrong (claims vision, refuses images) | the router's first 400 classifies `model_entitlement` or `content`, benches that capability on that model for the account, and the multimodal layer sends a description instead |
| Two agents edit one template folder | each has its own worktree (AD-49); the second merge goes to `reconcile` or a merge-conflict view |
| A chunk's model changes mid-run (fallback to a 128k model from a 1M one) | the planner re-plans the unstarted chunks for the new window; finished chunk memos stand (AD-34) |
| Machine offline mid-chunk on a burst placement | the attempt reads `unknown` after the heartbeat loss; the model call is retried once elsewhere (duplicate spend accepted, AD-8) |
| He sets `router.plan_lane: off` | new plan chats launch with no base URL; sub-agents naming third-party ids fail with "use delegate"; existing chats keep their launch until restarted |

---

## 9. Built, designed, new (checked against `origin/engine/base` 132169c7)

| Area | State |
| --- | --- |
| Engine core: definition, validation, core, ledger, memo, replay basics, nodes (script, rule, loop, join, wait, llm, agent, grader deterministic, monitor, subworkflow, trigger, doctor, fake provider), triggers (cron, interval, manual, after, catch-up, quota hold, preflight, claims), inbox, explain, drafts, versions, tests, local worker, 31 templates | **built** |
| Harness: chats, permissions, money gate, relay key lane and GPT lane, blocking `delegate`, plan usage meter, HG1 grants (H0, H15, H16, H17) | **built** |
| Account pool, router plan lane, chat lane, model registry and data profiles, several GPT accounts | **designed** (AD-12, AD-38, AD-39); **not built** ("skipped: no pool") |
| No-caps settings | **designed** (AD-40); code still holds every cap listed in SOLUTION-DESIGN §26.3 |
| Stuck detector (loop signature, sleep-aware clock, grace) | idle watchdog **built**; the rest **designed** |
| Vault, run passes, central relay, Contabo node, Hub, Library | **designed**; the engine runs on `ports/library_fake.py` |
| Script isolation (zones, AppContainer, manifest tiers), money scan predicate, redaction seams | **designed** (AD-24, AD-36, AD-37) |
| Memory | **designed** (AD-18); `memory/__init__.py` holds one docstring |
| Copilot builder skill | **placeholder** file (`qmx_agents/skills/build-workflow/SKILL.md`) |
| Mini-app archive | `apps_archive` **stub** (`qmx_control/service.py:1017`) |
| `delegate` v2, multimodal layer, permissions floor and rules, browser pack, take-over, HUD, output directives, skills lifecycle and curator, copilot loops, desktop host, worktrees | **new in this pass** (AD-41 to AD-49) |
| Trigger kinds `event`, `webhook`, `session` | **designed**; the kind check allows only `cron, interval, manual, after` (`ledger/migrations.py:35`) |

---

## 10. Open operator calls (only these)

1. **D. Grant HG3, narrowed** (H2 first). Recommend yes. Framed in engine OPEN-DECISIONS D.
2. **E. Edited and model-written scripts never run bare on the PC** (Docker started by QMX, then Contabo, then wait). Recommend yes. OPEN-DECISIONS E.
3. **F. A money scan that fails closed with no allow-list**, with 36's predicate and narrowed surfaces. Recommend yes. OPEN-DECISIONS F.
4. **G. Grant the HG4 harness rows outside the pool exception** (`delegate` v2, attachments, permission floor and rules, pack sets, session loops, browser and HUD tools for the copilot, background review fork). Recommend yes. OPEN-DECISIONS G.
5. **The fifth quant lens.** Unresolved; nothing is built on it.
6. **Which burst provider to pay for, and when** (money). Only when Contabo's four sessions overflow too often.

Named dependencies, not calls today: the methodology, the system prompts, the persona text and the explainer screens (B26-B29, ruling 82), done with him later; the data study (ruling 91) before any data or backup design. Not architecture: his merge click from `engine/base` into `rebuild/base` (C M-19) and the planning lead's edits to 26, 33, MAP, BACKLOG and UI-NOTES.

---

## 11. Reviewer gate and what is not done

**Gate (run inline; no sub-agents were allowed):** `lint_spine.py` 0 findings on all three spines; a rubric walk and two lenses (security and money boundary; operator-alignment) recorded in `architecture/workflow-engine/reviews/review-2026-10-18-rerun-gate.md`, with the clear fixes applied.

**Not done in this pass (owners named):**
- The HLD and LLD companions of Lab and Library were not re-projected beyond the lines named above; the spines win where they differ (owner: the next architecture or planning pass).
- `PLAIN-WORDS.md` for Lab and Library and the explainer page for him were not rewritten (owner: planning lead, with the explainer format he asked for).
- 26 (ruling 105 and wording gaps), 33, MAP, BACKLOG, UI-NOTES and the 38 banner were left to the planning lead (DOC-CHANGES rows 36 and 38).
- No probe ran: P1, P2, P3, P5, P7, P-PK, P-FK and E33 are build-time gates.
