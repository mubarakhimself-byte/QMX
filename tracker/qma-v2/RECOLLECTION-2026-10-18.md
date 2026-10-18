# Recollection, 2026-10-18

I compared today's part of the planning-lead transcript with the files on disk. The transcript is `5efecf49-2c39-4a71-bfb7-8ce9c1e6d0dd.jsonl`, lines 2839-3343 (0-based). Line numbers below point into that file.

Files compared: 26 (rulings 92-104), 34, 35, 36, 37a, 37b, 37c, 38, `HANDOFF-2026-10-18.md`, `RERUN-WORKFLOW.md` and `AUDIT-2026-10-18.md`. I did not read 37d, because it is being written now. Any Hermes gap below may already be closed there.

Some points the audit already flags: the haiku test rule missing from 26, the F′ banner on 38, and RERUN-WORKFLOW being stale. I repeat them only where they matter here.

## 1. GAPS (said today, not on disk)

### Hermes: his questions and scenarios

1. **His list in 3131 survives only in RERUN-WORKFLOW, which the audit says to archive.** He said: "Simlink for shared tools… Shared helpers"; "Git work trees… the logic for Git work trees and the workflows"; "the terminal user interface… we don't need that"; "We need the desktop app"; "Even security, they have it… nothing much you are missing". None of this is in rulings 92-104, and the HANDOFF step 2 topic list leaves it out. Session storage, LSP, tool search and document extraction are also missing from HANDOFF step 2. 37b and 37c do not cover shared helpers through symlinks, or git worktrees for workflows. **Where it goes:** add it to ruling 102 and to HANDOFF step 2 before RERUN-WORKFLOW is archived.
2. **Topics from 2972 that ruling 93 drops.** He named "connecting to Telegram, the sol.md" (SOUL.md), "programmatic integration… I don't think we need it", "streaming TTS, okay, don't need that", "relay", and the built-in plugin groups "automation, media, and web". Ruling 93 has none of these. **Where it goes:** ruling 93, as a short scope note: SOUL.md and the plugin groups are in; TTS and programmatic integration are out.
3. **No limit on how much each agent reads (3131).** He said "Enhance the search… sub-agent… 1 million context window… Don't limit". Only the stale RERUN-WORKFLOW records this. Ruling 102 covers "no top-N cap" on ideas, not reading depth. **Where it goes:** ruling 102, one line.
4. **The Hermes docs mirror already exists, and HANDOFF does not say so.** The mirror agent was stopped at 3185, but `research/sources/hermes-docs/` holds 455 files. The audit lists it; HANDOFF step 2 tells the next lead only to look for 37d. He also said (3131) "We have the documentation script… scrapped off the bloody internet, but I think I lost it". Nothing records that, or that the mirror may be partial. **Where it goes:** HANDOFF step 2: "use the mirror; check it is complete; commit it".
5. **His scenarios in 2972 behind ruling 92.** He asked how thinking mode, tool calling, sub-agents and DevOps hold when sub-agent 1 runs on Kimi and sub-agent 2 on Qwen, "this also transfers all the way to workflows". The reply at 3020 named two gaps that no file records:
   - there is no per-sub-agent effort or thinking control (only per chat, HP12);
   - there is no single monitoring view across copilot and workflows.

   38 covers routing, and 37c covers engine monitoring, but neither names these two. **Where it goes:** the architecture pass input (HANDOFF step 3), or 34 as SPEC-GAP rows.
6. **Why he wants this (3032).** He said: "the Chinese models, because I'm going to use them way more than I use Claude… there is no point in which we should limit them". Also: "the harness still remains the same. So what we are replacing is like the contracts that give us ability to connect to the other providers". And: "at the low level, we are cutting off the issues that would come at a higher level… We fix one thing, then the rest we just adopt". The low-level-fix idea is reflected in 38 §5. His priority (third-party models used most) and "harness stays, only the provider contracts change" appear in no ruling. **Where it goes:** ruling 95 or 99. It changes how the architect weighs option A.
7. **Hermes as a provider over RPC (3032).** He said "Hermes… RPC… use it as a provider… one centralized pool… not install the whole bloody thing". 38 §3 answers that Hermes cannot be a transparent provider, only a delegate target. That answer was never put to him in plain words as a closed point, and no ruling records it. **Where it goes:** ruling 99, one clause.
8. **Hermes UI for the UI session (3131, 3281).** He said "their browser is one of the best… HUD mode… the desktop application is brilliant". Ruling 102 has this. 37c §12 covers the TUI and desktop app but not HUD mode, and `UI-HANDOFF.md` has none of it yet. HANDOFF step 7 plans it. **Nothing missing beyond the pending step 7.**

### Engine-run backlog

9. **Open decisions D, E and F have not been asked or recorded.** D is granting HG3, E is "Docker needed", F is a money scan with no allow-list. 35 and 36 record them, along with 36's verdicts: a smaller HG3, Docker auto-start then Contabo with gVisor, and fail-closed once the rule is fixed. They were presented at 2960 and 3108 and "put to you properly after the review" was promised. They never reached him. HANDOFF "Open items" does not list them. **Where it goes:** HANDOFF step 9 (his calls).
10. **36 S11, the $5 cap per background chat (3108).** The assistant said this goes against his no-spend-cap rule. It is only in 36, and HANDOFF step 8 hygiene does not list it. The audit lists `background_cap 0.5` but not `max_budget_usd 5.0`. **Where it goes:** HANDOFF step 8.
11. **The EP14/TP4 review gate (screenshots and video), 2880.** It was "still open on your side". The stack was then merged. No file says whether he reviewed it or waived it. Low items say the TP4 screenshot is stale and the video does not film the run. **Where it goes:** a line in 33 state-of-play.
12. **Duplicate work (3181).** He said "pick a hustle, dude. Now that's just wastage". HANDOFF records this. **Nothing missing.**
13. **BACKLOG.md and lows.md themselves.** 34 triaged everything up to the "Added after the morning of 2026-10-18" heading, plus the Fable-ladder line under it. lows.md ends with TP4 lines that 34 already counts. **Nothing missing.** The audit's edits (superseded rows on one Max, the 50% cap and CLIProxy) are in the tracker's BACKLOG.md, not the engine one.

### Minor

14. **Line 2839:** "we are going to be replacing Fable with Opus 5.5. I don't have the usage anymore". Ruling 87 covers this. **Nothing missing.**

## 2. MISCAPTURED

1. **38 §1 (line 94), §5 (line 359), §6 (lines 384, 396), §8 item 3.** These say coding-plan rows are `use: interactive` only and never leased to unattended work. His answer (3220): "No, for the coding plans… Don't limit yourself". Ruling 100 reverses 38 here. The audit flags only the F′ part of 38. **Fix:** add a banner covering both F′ and interactive-only.
2. **Ruling 98 and HANDOFF step 3.** These say "BMad architect persona Winston" and "the BMad architecture skill". His words (3220): "a skill under BMAD that uses something called party mode… a persona… Wilson… an architect… the agent can look at all these angles on its own". He named party mode, meaning the architect persona in a roundtable, not the architecture skill. The intent is the same (the architect decides A versus B/D), but the tool differs. **Fix:** decide which one is meant, or note both.
3. **Ruling 101.** It says "The lead holds the workflow in this session". In the same answer (3220) he said "let me start a fresh session… the agent I'm starting to replace you is not going to need any skills". He did say "continue here" earlier, at 3159. Ruling 104 fixes the outcome, but 101 reads as if he kept this session. **Fix:** reword 101 to "no poteto-mode and no skills, for the lead and its successor".
4. **Ruling 99.** It records "load balancer stays in-house" but keeps his premise unstated. He said (3220) "we already built our own load balancer… we shall have to delete that code". The reply (3269) corrected this: the pool was never built (the ladder logs "no pool"), so nothing gets deleted. Only 38 §4 holds that correction. **Fix:** add the correction to 99.
5. **Ruling 100.** It says "NOT restricted to interactive use". His words were "Interactive, no problem. Interactive, I don't know, cause… most of these models are multimodal". 100 is a fair reading. The lead's condition at 3269 was a terms note on each provider row, and each row declaring which input types it accepts. That condition is nowhere on disk, and he never ratified it. **Fix:** record it as the lead's proposal in HANDOFF step 3.
6. **RERUN-WORKFLOW** (top line and step 2) says opencodex is his preference, the workflow runs in this session, and rulings run 1-97. This is all overtaken. The audit already says to archive it. Listed here only because gap 1 depends on moving its Hermes list first.

## 3. OPEN QUESTIONS NOBODY ANSWERED

1. **His old Hermes docs scrape (3131):** "We have the documentation script. I don't know where". Nobody looked for it. The reply only said "drop its path".
2. **Option A account risk.** 38 §8 item 2 notes that `ocx claude` already routes his plan traffic through opencodex today, which is the risk Anthropic's terms describe. It was mentioned at 3215. He did not respond, and nobody asked whether he still uses it.
3. **Decisions D, E and F** (gap 9).
4. **Whether he reviewed or waived the EP14/TP4 gate** (gap 11). Also whether an Opus review replaced the Fable review he asked for after TP4. At 2880 the assistant assumed it was off, and he never confirmed.
5. **The merge from `engine/base` into `rebuild/base`, and the red `just ci` test.** At 2929 the assistant said "you'll need to decide on that before landing". He merged the PRs, and the decision was never put to him. HANDOFF lists the merge as his click but does not ask about the red test.
6. **3260: "I still need your opinion on the answers".** This was answered at 3269. **Answered.**
7. **3260: "Can you read another session's transcript?"** This was answered at 3269. **Answered.**

## 4. FRIDAY LINKS

| Today's point | Line | Where the earlier decision lives |
|---|---|---|
| "I told you to look at the Hermes agent… a few days ago" and "do I need to give you the link again?" | 2972 | `research/methodology/25-hermes-n8n-loadbalancer.md` (Hermes URLs, provider runtime, credential pools) |
| "this is why I really wanted to use the CLI proxy" | 3032 | Ruling 26 (10-16, several accounts, CLIProxyAPI-like) and ruling 90 (10-17). The 10-13 "CLIProxy rejected" row is in the tracker's `BACKLOG.md` line 145. |
| "Claude remains Claude… I thought this is how we were doing earlier" | 3032 | `research/one-engine/architect/DESIGN.md` lines 316, 322, 346 ("plan traffic takes no hop", "no proxy for plan traffic"). This is a 10-14 file, not Friday's. |
| "GPT we use the signing in… We already tested the logic and it works" | 3032 | The harness program (HP) GPT lane: DESIGN.md and its SIGNOFF. No ruling records "tested and works"; it rests on the HP run record in `D:\QMX-worktrees\qma-ship\`. |
| Replace Fable with Opus | 2839 | Ruling 87 (26 §J, 10-16 night) |
| "rerun the workflows we ran last time while planning and architecture" | 2839, 2972 | `WORKFLOW-SHIP-PREP.md` and the 10-16 night pass (27b, 27c, 27d), the files the audit says to archive |
| Hermes-style mini apps "created and monitored by the copilot" | 2972 | `14-folders-miniapps-browser.md` and ruling 80 |
| Voice mode later | 2972 | Ruling 85 |
| DevOps: logging, observability, monitoring | 2972, 3020 | `30-data-and-devops.md` §5 (Prometheus, Loki) |
| Skills curated "the same thing we did for templates" | 3260 | Template rulings in 26 §G-J. The cards are in 15-17 (stale per the audit) and the built TP1-TP4 templates. |
| "we might be contradicting ourselves" | 3260 | HANDOFF Orient item 1 lists the reversals (rulings 26, 39, 51, 87, 90) |
| Compaction at 40% (questioned by 37a) | 3064 | AD-34 in `architecture/workflow-engine/ARCHITECTURE-SPINE.md` |
| "I'm not technical", wants explainer pages, under 40% context | 3131, 3159 | Memory only (operator profile, output-as-explainers). No tracker file holds them. |
