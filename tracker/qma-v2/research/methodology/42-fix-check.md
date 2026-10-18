# 42. Fix-check of review 41 and the 40 §5 gaps (commit ea4e1c24)

**Opus checking Opus.** The rerun (39), review 41, the fix pass (ea4e1c24) and this check are all Opus 5.5, so shared blind spots are likely. No sub-agents, no skills, no commit, no design file edited.

**Ground truth:** `git diff a57e9f7c ea4e1c24`; the engine spine, SOLUTION-DESIGN (SD), HARNESS-REQUESTS (HR), OPEN-DECISIONS, PLAIN-WORDS, DOC-CHANGES, UI-HANDOFF, Library AD-20, Lab LLD and OPEN-5 as of ea4e1c24; rulings 1-104 of `26`; code on `origin/engine/base` = `132169c7` read with `git show` (no checkout). `QH/` = `qmx-agents/packages/qma-harness/src/qma/harness/`, `QE/` = `qmx-agents/packages/qmx-engine/src/qmx_engine/`.

**Counts.** 41: 28 FIXED, 5 PARTIAL, 1 NOT-FIXED (deferred on purpose), 0 REGRESSED. 40 §5: 10 FIXED, 2 PARTIAL. New findings: 2 critical, 6 high, 9 medium, 4 low. The record's "12 of 12 resolved" and R.8's "every hit rewritten" are both overstated.

---

## 1. Finding → verdict

| Finding | Verdict | Evidence (where the fix is, and what is missing) |
| --- | --- | --- |
| 41 C1 plan-main shape to third parties | FIXED | AD-50 (1)-(7) normalises per target row on key/chat/GPT lanes; AD-38 ship gate; P4 restored as a build gate run with a plan-main process (SD §26.14); GPT helper under a plan main is `delegate` v2 until P4 (AD-38, SD §26.1 table). The slow-prefill keep-alive added with it creates N3. |
| 41 C2 `cli` targets outside boundaries | FIXED | AD-41: container only, hash-pinned binary, no host home/keyring/own login, run pass through the router, `qmx-egress` with broker hosts denied, no container → spawn fails, first spawn per binary version asks; SD §26.4, HR H26, E52, UI §12 row 22. New gaps N8, N17. |
| 41 C3 demo not proven | FIXED (residual stated) | AD-33 five layers (portable QMX install, image-path deny of his terminals, his locked list, terminal-reported `ACCOUNT_TRADE_MODE` every 60 s, compiled-in guard + lint, disarm at exit); SD §24 manifest, §26.7, S14, E46; UI §12 row 12; PLAIN-WORDS. Layer 4 has a bypass (N14). |
| 41 C4 no mechanism for native third-party sub-agents | FIXED | HR H38 (`NewChat.agents` for Interactive/Background/Child, registry-generated); AD-38, AD-29 label corrected; P1 rewritten under a real `/login`. The P1-fail fallback withdraws too much (N7). |
| 41 H1 router as new SPOF | PARTIAL | Own thread/loop, fixed port, 5 s health check, flip-off and relaunch without base URL (AD-38, AD-48, SD §26.1, E49). Missing: who restarts the dead router thread ("key and GPT chats wait for the router's restart" names no restarter), when the lane turns back on, fixed-port collision (N15). |
| 41 H2 plan 401 benches healthy account | FIXED | AD-12, SD §7.3 pseudocode, §26.1, S6, UI §12 row 5 all say: forward, bench only on the CLI's own needs-login signal or 3 consecutive 401s over ≥ 5 min, copilot never moved. |
| 41 H3 unknown id → 400 breaks plan chats | FIXED | AD-38 plan lane accepts any `claude-*` by the family rule (`QH/profiles.py:230` confirmed), journals unknown ids; SD pseudocode line 1216. |
| 41 H4 caps in templates and migration | PARTIAL | Templates, schema defaults, `runaway` folding to nothing, AD-4 `timeout`, SD §2.2/§2.4/§26.3, Lab LLD, DOC-CHANGES 41: done. Cap text still live elsewhere: SD:364 "hard run timeout", SD:893 `host_harness` "attempt timeout", PLAIN-WORDS:21 "a job that runs away … pauses itself or switches to cheaper models" (see N1). |
| 41 H5 stuck detector unsound | FIXED | AD-16 masked digests, (c2) no-convergence, model request in flight counts as progress, in-tool CPU/IO, recorded waits skipped, sessions covered; AD-47 `blocked`; SD §10.3, §17, E41. The masking chosen causes false stalls (N4). |
| 41 H6 blast radius | FIXED | 39 R.4 file lists replace §7's rows; SD §26.15 resizes both packets. `roles.test_order`/`_STRONG` are not in any packet (N2). |
| 41 H7 two pools, GPT revocation | PARTIAL | Key fact exchange and one owner machine per GPT account (AD-12, SD §7.3, §26.16, E53). Missing: the router has no path to forward a GPT request to the owner host, and a PC chat's per-launch grant is not a credential Contabo's router accepts; the static "half each" concurrency split throttles a host whose peer is idle or down (N11). |
| 41 H8 logged-in snapshot | FIXED | AD-44 per-site allow-list (empty default), banks/payments/crypto/mail on always-deny, real browser binary on the snapshot; E45, P-BR, UI §12 row 10. |
| 41 M1 plan lane not byte-for-byte | FIXED | AD-38: any method and path, raw header list, only `x-qmx-grant` removed; P1 records paths. |
| 41 M2 structural guarantee | FIXED | AD-38 "What changes in the harness, plainly"; HR line 31 note; H27 lists the docstrings; test that a plan grant never reaches `_token_bearer`. |
| 41 M3 `ChatTableFull` refuses | PARTIAL | HR H28 (b) and AD-40 (5): Background/Child sends wait for a slot. This removes the guard `QH/harness.py:431-432` states ("nothing waits on a slot that only the parent could free") without replacing it: deadlock (N5). |
| 41 M4 timeouts vs big chunks | FIXED | AD-50 (8), per-row `first_token_timeout_s` (AD-39, SD §17), mid-stream errors classified, E43 slow-prefill. The keep-alive conflicts with error handling (N3); `API_TIMEOUT_MS` still bounds 1M prompts (N16). |
| 41 M5 re-fire duplicates side effects | FIXED | AD-10: same run, model node `waiting(resume_at)` at 5/15/30 min. |
| 41 M6 one Claude account | FIXED | AD-13 last sentence, S13, UI §12 row 5. |
| 41 M7 overage stop, billing | FIXED | `hard_stop` kept (SD §26.3 row, AD-40 (5)); plan-lane billing watch (AD-38); P2 checks overage. Redundancy noted (N18). |
| 41 M8 request-rate alarm undefined | PARTIAL | AD-28, AD-40 (4), SD §17, E25 and §19:1040 define the alarm on facts. SD:891 still detects by "pass rate cap" with damage bounded by "that run's token allowance", SD:1041 "pass rate caps" (N1); copilot-owned helpers have no attempt for the alarm to check (N8). |
| 41 M9 chat-lane thinking | FIXED | HR H12 specifies thinking ↔ `reasoning_content`, translator-owned signature stripped on return, id mapping; P3 ten turns with thinking. |
| 41 M10 images in tool results | FIXED | AD-42 last sentence, AD-50 (4), SD §26.1 failure paths. |
| 41 M11 central GPT for non-owned | FIXED | AD-28: GPT lane only for owned placements; non-owned passes never list GPT. |
| 41 M12 git worktree over Library | FIXED | Library AD-20 rewritten (materialised folder + shadow git), engine AD-49, SD §26.12. |
| 41 M13 `Harness.complete` unrequested | FIXED | HR H3 moved into HG4; AD-19 and AD-42 state the fallback; spine Deferred row; OPEN-DECISIONS G. |
| 41 L1 | FIXED | UI-HANDOFF §1 item 6. |
| 41 L2 | FIXED | UI-HANDOFF §11 row 4 ("3 checks so far"). |
| 41 L3 | FIXED | Lab OPEN-DECISIONS OPEN-5. |
| 41 L4 | FIXED | Engine OPEN-DECISIONS older D/E/F marked superseded. |
| 41 L5 `max_live_chats` 4 vs 6 | NOT-FIXED (deferred, acceptable) | 39 R.6 hands it to the caps packet; code still 4 (`QH/launch.py:226`) and 6 (`QE/settings.py:47`). |
| 41 L6 | FIXED | AD-29 cites `scripts/probes/engine/FINDINGS.md:40` as an API-key launch. |
| 41 L7 | FIXED | AD-15 and HR H36 labelled [remembered]; P1 records the headers. |
| 41 L8 | FIXED | 39 R.4 names `roles.py:86` and `settings.py:72`. |
| 41 L9 | FIXED | SD E41 is stuck detection only; E43 the no-caps proof. |
| 40 §5.1 held chunks stall | FIXED | AD-9: warm-first gate moves to dispatch, held work writes no `node_started`; AD-16 skips recorded waits; SD §10.3, E41. Matches `QE/nodes/agent.py:122-133` (the gate today sits inside `run`). |
| 40 §5.2 one write zone per run | FIXED | AD-51, AD-8, AD-24, SD §3.4, §26.16, E50: a retry no longer touches a sibling's files. Same-path commits create a new problem (N6). |
| 40 §5.3 number evidence | PARTIAL | AD-45 rule and E51. "Tool and script results recorded as spans" includes `sandbox_python`/`sandbox_bash` output of code the agent itself wrote, so an agent can print any number into evidence; the check stays circular (N12). |
| 40 §5.4 memo truth | FIXED | AD-7 last sentence. |
| 40 §5.5 model node declaring irreversible | FIXED | AD-8; SD §3.4 line 235. |
| 40 §5.6 past `reset_at` | PARTIAL | AD-12 `probing`, SD §7.3. A probing request answered by another 429 with a past reset flips to `probing` again and the next lease fires at once: a tight resend loop (N13). |
| 40 §5.7 his `limits` timing | FIXED | AD-16: checked each turn end and tick; `wall_seconds` active time only. |
| 40 §5.8 retention | FIXED | AD-49 retention, AD-51 overlay deletion. |
| 40 §5.9 single instance | FIXED | AD-3: OS lock on `<home>/engine.lock`, one `Scheduler` per engine object. |
| 40 §5.10 resume without the task | FIXED | AD-34 task marker and full re-send. |
| 40 §5.11 token estimate | FIXED | AD-34, AD-39 `chars_per_token` (default 3, 10 % headroom), SD §17. |
| 40 §5.12 template `runaway` | FIXED | AD-40 (2): removed. |

## 2. New findings

### Critical (settled facts violated)

**N1. QMX caps survive in six places; R.8's sweep missed them.**
- SD:364 (§5.4) "stuck: … idle timeout 600 s, hard run timeout"; SD:893 (§15) `host_harness` ends on "the attempt timeout"; SD:1034 pass "TTL = attempt timeout".
- SD:891 detects a compromised worker by "pass rate cap" and bounds damage by "that run's token allowance"; SD:1041 "pass rate caps".
- PLAIN-WORDS:21, read by him: "a job that runs away (far too many tokens, tool calls or hours) pauses itself or switches to cheaper models".
- HR:11 H2 still asks for "a per-node turn cap" and its fallback "relies on the global cap" (HR:39's rewrite says "no `max_turns`" but H2's first row is not marked superseded).
- HR:69 H28 fallback: "writes very large values into Settings … the copilot's own Background chats keep today's defaults until granted", which keeps the $5, 0.5 share and 50-turn caps.

**Fix:** rewrite SD:364, 891, 893, 1034 and 1041 to the AD-16 and AD-28 wording; rewrite PLAIN-WORDS:21 as "a stuck or looping job stops and tells you; nothing stops on how much it uses"; mark HR:11 H2 superseded by HR:39; replace H28's fallback with "none: settled 2026-10-18 (no QMX caps); H28 ships with the caps packet", since a refused H28 would keep caps.

**N2. The default-order and no-Fable facts do not hold in SD §9 or in any packet.**
- SD §9 (604-607) lists `claude/haiku → kimi`, `claude/sonnet → glm → gpt` and `claude/opus → gpt`. That puts Claude first for every role and leaves no Chinese model in the strong roles, against AD-13 (`key → gpt → plan`) and "Chinese models first-class".
- Merged code still has `_STRONG = ("claude/opus", "claude/fable", "gpt")` and `roles.test_order ("test_only", "cheap_first")` (`QE/settings.py:22, 71`). In test mode, `QE/roles.py` sorts OpenRouter first.
- DOC-CHANGES row 35 names these lines, but neither 39 R.4 nor SD §26.15 gives them to a packet.

**Fix:** rewrite §9's examples in `key → gpt → plan` order, with Kimi, GLM and DeepSeek in every tier. Give DOC-CHANGES 35's code rows to the registry packet in §26.15, with a test that no default list names Fable and that test mode resolves `claude/haiku` first.

### High

**N3. AD-50 (8)'s synthesised `message_start` conflicts with AD-50 (7), AD-40 (6) and the relay's own invariant.**
- After the router has sent 200 and a `message_start`, a provider 429, 400 (prompt too long) or 529 that arrives after 10 s can no longer carry a status or `x-should-retry: false`. It becomes an SSE `error` mid-stream, so "error bodies reach the CLI unchanged so its own recovery still matches" fails. The CLI's retry and prompt-too-long handling for a mid-stream error is unverified [remembered].
- The synthesised start carries zero usage. If the upstream's usage is not carried forward, the CLI's context accounting and auto-compaction run blind.
- The relay guarantees "nothing of a stream reaches the CLI before its `message_start` passes the family test" (`QH/relay.py` docstring). Synthesis breaks that ordering.
- The cited precedent is wrong. The GPT lane pings only after the stream has started, and it ends the stream after `START_WAIT_S` with nothing sent (`QH/relay.py:725-731`). It never synthesises a start.
- P4 forces only an instant 429.

**Fix:**
- Make keep-alive a per-row opt-in (`keepalive: true`).
- Run the family test on the swallowed upstream `message_start` before any content event goes out.
- Carry its usage into the first `message_delta`.
- Add late-429 (after 15 s) and late-prompt-too-long cases to P4 and E43, with pass = 0 CLI retries, no full resend and correct context accounting.
- Correct the citation.

**N4. Masking digits and paths in stuck digests erases progress.**
- `ledger.signature` replaces every digit run and every path (`QE/ledger/signature.py`). With that masking, a converging fixer ("5 failed" → "3 failed" → "1 failed") produces one masked signature and gets stopped as `no_convergence`.
- An agent paging through different numeric rows, or reading different files, produces "no new masked result digest" for 8 turns and gets stopped as `stalled(loop)`.
- "Error signature" of a tool result that is not an error (pytest output through `sandbox_bash`) is undefined.

These are QMX stops on legitimate work.

**Fix:**
- Give stuck digests their own narrower mask: uuids, timestamps, durations, temp paths. Keep counts, test ids and file paths.
- No-convergence needs the same failing-test set or error location and a count that does not fall.
- Define an error result as `is_error` or a non-zero exit.
- E41 adds a converging fixer and a pager, and both must not stall.

**N5. H28 (b) can deadlock the chat table.**
- `QH/harness.py:431-432` documents why a full table refuses at once: "nothing waits on a slot that only the parent could free".
- With waiting sends, a parent holding a slot inside its send can block forever on a child that waits for a slot. Two cases do this: blocking `delegate` (G's stated fallback if H26 is refused), and a v2 parent polling `list` until its child reports.
- A table full of such parents never drains. Only the loop detector, by failing the parents, would break it.

**Fix:** a child admitted for a waiting parent borrows the parent's slot, or uses a reserved child slot; a parent blocked on its child does not count against capacity. Add a test with `max_live_chats = 1` and a parent that delegates.

**N6. AD-51 same-path commits cost retries and still end last-writer-wins.**
- Chunked agent or script attempts commonly write the same scratch names (`script.py`, `out.json`). Every chunk after the first commit fails `zone_conflict`.
- Each retry re-spends model tokens, consumes `retry.max_tries` (3) and can park chunks.
- The retry then starts after the sibling's commit, so its own commit overwrites the sibling's file anyway. R.5's "nothing is silently overwritten" holds only for the first race.
- Commit atomicity on a crash between the moves and `zone_committed` is unspecified.

**Fix:**
- Commit only the paths a node declares as outputs. Undeclared overlay files stay private to the attempt and die with it.
- Validation refuses two concurrent writers of one declared path unless the path is partition-templated (`out/{partition}.json`) or declares a merge (append or keyed).
- Commit by staging plus rename under the ledger writer, and replay or roll back on resume.

**N7. The P1-fail fallback withdraws H38 for everyone, and H38 definitions are never filtered by lane.**
- H38 is also the only way a key-main (option D) or GPT-main chat names a third-party sub-agent (AD-38; SD §26.1 rows 2-3; the `Agent` tool takes Claude aliases only). Those cases do not depend on OAuth, yet AD-38, 39 R.1 and HR H38 withdraw H38 when P1 fails.
- Conversely, a plan chat whose lane is off still receives `kimi-reviewer`, and its request goes straight to api.anthropic.com and fails. The lane can be off because P0 or P2 failed, the kill switch is off, or the 5 s health flip fired mid-session.

**Fix:**
- P1 failure withdraws only plan-main third-party definitions.
- Keep H38 for key and GPT mains, gated by an API-key probe (E24's shape plus P4 under a key main).
- The generator filters each chat's definitions by its lane state and each row's `plan_main_native`.
- The flip-off relaunch regenerates them.

**N8. Copilot-owned helpers trip the misuse alarm.**
- AD-28 revokes a pass on a request "naming a `(run, node, attempt)` that is not open". A `cli` helper started from a copilot chat (AD-41, UI §12 row 22) has no engine run, so its first request revokes its own pass and raises an `urgent` item.
- CLIs also make background calls (titles, summaries) asynchronously [remembered], so "any request after that attempt ended" fires on a normal shutdown.

**Fix:**
- A pass names its owner: an attempt, or a delegate handle in `control.db`.
- The alarm checks that the owner is open.
- A stream or background call that started before the end is not misuse. This is a fact rule, not a rate.

### Medium

**N9. Probe ordering contradicts itself.**
- SD §26.15: "P0, P1, P4 and P2 run before any plan-lane code is written". But P4 tests AD-50's normaliser in the router, and P2 needs a working plan lane.
- AD-38 says instead "before the plan lane is built past its canary".

**Fix:** P0 and P1 (CLI behaviour, test router) → build router hardening, normaliser and plan lane dark → P4 and P2 → enable the lane.

**N10. The pass and fail lines are not fully exact.**
- **P0** compares only betas, tool shapes, `system` and `metadata`. List every header and body field, with an explicit exclusion list (`host`, `content-length`, `x-qmx-grant`, request ids).
- **P1** puts router egress checks in its pass line (no `metadata.user_id` at the echo), but its fail line names only CLI behaviours. A leaked field is then neither pass nor fail. Move egress checks to P4, or state that the probe router runs AD-50's identity strip.
- **P2** has the same gap: a window that does not move is neither pass nor fail. Three haiku turns may not move a coarse `utilization` fraction, and the CLI may not emit a `RateLimitEvent` per turn. Read the `anthropic-ratelimit-unified-*` response headers at the router [remembered], and make "window unchanged" a fail.
- **P4** has no method for "the CLI's assumed window", although AD-50 gates models on that number. Name the measurement, for example the auto-compact trigger point on a growing context.

**N11. The H7 cross-host gaps.** The fix needs three things:
- a router branch "GPT row whose owner is another host → forward over the tailnet with a host pass that names the originating chat";
- Contabo's router accepting that pass;
- concurrency split by exchanged live leases, with the full provider share when the peer is idle or unreachable.

**N12. AD-45 evidence must exclude model-written code.** Count fetched and read sources, and the results of declared, non-model-written scripts. Exclude tool results produced by code the attempt's own model wrote. E51 adds a printed-number case that must fail.

**N13. Probing loop.** A `probing` request answered by a 429 whose reset is absent or past is classed generic: retry once, then the generic cooldown. It never returns straight to `probing`.

**N14. AD-33 layer 4 can be bypassed inside the allowed image path.**
- `metaeditor64.exe` lives in the QMX demo install, so the image-path check admits it. Through that window the agent can compile an unguarded EA in the GUI, or edit `qmx_demo_guard.mqh` under the install's `MQL5\Include`. Both skip the driver's lint.
- Any EA can overwrite `qmx_account.json`.
- Separately, the design does not say where an agent-written EA source (full of `OrderSend`) lives, relative to AD-8 and AD-36 ("no script … may name a money act") and the PreToolUse gate.

**Fix:**
- Deny MetaEditor and compile actions to agent input; only the driver compiles.
- Hash-check the guard include and every `.ex5` at attach against the driver's builds.
- Put a driver nonce in the account script's output.
- State that EA sources are Library artifacts the driver reads by id, never text in a tool argument, with the money gate unchanged.

**N15. Router supervision is unspecified.** `qma.serve` should restart the router thread and re-run the canary. A Claude account's lane should re-enable after N healthy checks plus a canary pass. At boot, a port collision should pick the next free port and pin it in the home.

**N16. `API_TIMEOUT_MS` against 1M prompts.**
- A 1M prompt gets `first_token_timeout` 120 + 600 = 720 s, above the CLI's default `API_TIMEOUT_MS` of 600 s [remembered; whether it is a total or an idle timeout is unchecked].
- Under a plan main that is 41 M4's full resend.
- **Fix:** set `API_TIMEOUT_MS` above the largest row timeout on every launch that can hold such sub-agents, and add a 900 s case to E43.

**N17. `cli` front doors are undesigned.**
- The router speaks only Anthropic Messages on `/v1/messages`.
- Codex CLI (Responses wire) and other OpenAI-wire CLIs need inbound front doors that no AD designs, so "Codex CLI, Kimi Code, OpenCode CLI" may be an empty list at first ship.
- **Fix:** name the CLIs that qualify on day one (those that accept an Anthropic base URL) and defer the rest with an owner.

### Low

- **N18.** The plan-lane billing watch overlaps `hard_stop` rule 1 (`using_overage` already stops every plan chat, `QH/usage.py:55-56`), so "turn the lane off for that account" never acts alone. Key the watch on `overage_status` changes, or say it records the cause only.
- **N19.** AD-50's [retrieved] 400 was measured through OpenRouter only (`QH/profiles.py:162-168`); direct Moonshot and DeepSeek are unprobed ("their `true` may hit the same 400"). Narrow the claim.
- **N20.** AD-49 deletes a run's zone at run end, but an inbox `retry` on a parked run starts a new attempt that may read `work/`. Keep zones of parked runs until their item closes.
- **N21.** One H38 definition per enabled model lengthens the `Agent` tool description, and every enablement changes it on resume, which breaks the main's prompt cache. Prefer per-role definitions by default.

## 3. Build-gating probes (question 4)

- **P0:** testable. Its pass compares an incomplete field set (N10).
- **P1:** its pass and fail lines do not partition the outcomes (N10). Its fallback is incomplete:
  - It withdraws H38 for key and GPT mains too (N7).
  - It does not say how the copilot learns to use `delegate` for "have Kimi review this". Its tool description or skill must say so.
  - `delegate` v2 is itself an ungranted HG4 row. OPEN-DECISIONS G names blocking `delegate` as the last fallback, which is consistent, though slower.
- **P4:** testable per provider. It misses late errors (N3) and the window measurement (N10). It cannot run before the normaliser exists (N9).
- **P2:** "window unchanged" is undefined, and three haiku turns are likely too small to show (N10).

The "if P1 fails" path is designed for the plan-main copilot case: no plan lane, `delegate` v2, the switch hidden, engine `via: native` resolved to `via: delegate` (AD-4). It is not designed for the key and GPT main cases it removes as a side effect.

## 4. What holds

- No settled fact is broken in the spines themselves:
  - the pool stays in-house;
  - ruling 92 holds with an honest fallback;
  - wire and capabilities are per model;
  - multimodal is the default;
  - any number of GPT accounts;
  - no Fable in the spine's defaults;
  - tests run on haiku through the plan login;
  - demo work only, with the money gate first;
  - nothing ships on data (ruling 91).
- The new ADs (AD-50, AD-51, H38) match the merged code they cite: `QH/profiles.py:113-121, 148-169, 230`, `QH/home.py` `setting_sources=[]`, `QH/usage.py` `hard_stop` and `overage_rule`, `QE/nodes/agent.py:122-133`, `QE/workers/effects.py` `.snap`.
- The exceptions are N3's GPT-lane citation and N5's dropped deadlock guard.
