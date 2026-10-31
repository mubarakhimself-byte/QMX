# How the "QMA V2 Workflow System Design 2" session worked

Written 2026-10-31 by grounding agent G4b, for the lead, who adopts this method (STATE midday ruling 33). It describes what the session did, from its dialogue, and ends with habits to copy. It designs nothing.

**Source.** The verbatim dialogue `operator/session-qma-v2-workflow-design-2-2026-10-18-to-29.md`, cited `S:<line>`. It runs from 18 Oct 05:49 to 22 Oct 13:03 UTC. Its tool calls are not in it, so what the session did between messages is read from what it told him and from the files it named. His verdict comes from this session's own log (`~/.claude/projects/C--Users-Mubarak-Desktop-QMX/ed09cf0c-69f1-44ab-8c6b-76992918774a.jsonl`, his message at 2026-10-31T10:05 UTC, not yet in `transcript-2026-10-30-to-31.md`).

## 1. What he said he liked (his words only)

| His words | Where | What he was reacting to |
|---|---|---|
| "That session was a perfect session, literally." | 31 Oct 10:05 log | The whole session: "The way it ran, the way it was responding, it was perfect." |
| "Good job so far." | S:1283 | The run up to then: three agents on separate jobs and CIS placed in the flow. In the same message he asked it to realign and keep its task list current, which it did next (S:1286-1313) |
| "by the time you fold it into architecture, it's bloody brilliant" | S:1273 | Open-ended generation (party mode, CIS, brainstorming) folded into architecture afterwards |
| "42 PRs in that amount of time is an impressive number" | S:2009 | The build program it planned: a checked plan and a coding prompt, run by coordinator sessions |
| "working with you is very efficient" | S:2256 | It took over the server setup in his browser and over SSH while he was still talking |
| "dude, you went far and beyond" | S:2559 | The pass after he unlocked the whole app; this is "the best point" of the session for him |
| "what you'll make is the worst it will ever be. It will only get better" | S:3188 | He handed the technical design over and stopped adding seeds |

What these share: he liked visible speed with nothing stalled, depth after he removed limits, generative breadth followed by a disciplined fold, and the lead doing hands-on work itself.

## 2. How it planned and sequenced the work

**The workflow it ran, as it recalled it when he asked (S:2568-2582).** It saved this to memory as "planning workflow that worked".

1. Orient from the handoff and the rulings file.
2. Audit the disk: every file marked useful, reference or stale (S:165-171).
3. Research primary sources fully, with no cap: all 455 Hermes docs pages saved, 142 ideas (S:272-293).
4. Deep alignment: three agents each read one third of the old transcript and sort every item by where it stands now. Then, in its words, "I sort and reason over their three lists myself" (S:395-403).
5. List what is already built before anything new, across every branch plus `docs/` and `_docwork/` (S:1459-1476).
6. Parallel studies with skills: codebase-design, domain-modeling, subtract-before-you-add, foundational thinking, blast radius (S:1235).
7. The generative funnel: party mode, brainstorming and the CIS personas go wide, filter by relevance and park the rest (S:1276-1286, S:1387).
8. Fold everything with the BMad architecture skill: lint-clean, every idea decided, what each change touches and which scenarios it covers (S:1609, S:1623-1668).
9. Re-sort the backlog against the new design (S:641-676).
10. An independent review, one fix round, then an independent fix-check (S:715-898). It named one final round as final (S:875).
11. Re-centralize: rulings recorded, the state file, the UI handoff, the archive, the Wayfinder map (S:913-972).
12. Plan and prompt: the poteto-mode plan checker at 0 problems, and a paste-ready coding prompt (S:1039, S:1866, S:1894-1902).

**The data round, four days later, ran a shorter version** (S:2947-3217). His seeds went into one file every agent reads (`51-data-round-seeds.md`, S:2949). Then an inventory of built against designed, a primary-source stack study, and the funnel with Wayfinder. Then it **stopped and discussed before any architecture**, as he asked (S:2979-2982, S:3131-3161). Only then the BMad architecture fold, review and fix.

**Grounding always came before generating.** The session never started a generative step on a partial picture. When he said generation must check "what's already on ground" (S:1456), it added an "already built" list as the funnel's first step. Every idea got tagged exists, partial or new (S:1459-1463). The funnel's counts show it: 85 of 214 ideas already existed (S:1595).

**Agents.** All Opus. At most three at once, each with a different job and its own file, in the background (S:160, S:1222). It filled the three slots with independent work (for example, the whole-app pass beside two studies, S:1224-1233) and queued the next step until a slot freed (S:1252). It committed each agent's file on the PC as it landed (S:310, S:964). It pushed only on his yes (S:20-23, S:1889-1892).

## 3. How it answered him

- **Short, plain and structured.** Bold lead-in per point, short bullets, a small table when there were counts (S:695-701). No wall of text after he said "I don't like reading blocks of text" (S:367). Most replies end with what is running and what comes next.
- **The same three-part opening every time it took stock:** where we are, what's agreed, what contradicts (S:27-66). It used the same shape again for the 21 Oct grounding recall (S:2814-2871): done, still open, your seeds, findings, how I'd run it.
- **Visual when it mattered.** "I walk you through it here in chat, visually" (S:405), and a clickable diagram for the routing design (S:622-623).
- **His dictation mapped back to him.** "Here's what I now understand, so we're on the same page. Correct anything I got wrong" (S:2370). Then one section per point he raised, in his order (S:2272-2295).
- **Plain words for codenames he could not follow.** When he asked what HG3 and HG4 were, it explained both in one sentence each and stopped using codenames (S:1060-1062, S:1054).
- **Paste-ready prompts in a code block.** After he said "I'm not going to edit that stuff", it gave him a whole new prompt in chat (S:1955-1968). When it changed a prompt it said what changed and why in two bullets (S:2529-2531).
- **Proposals marked as proposals.** "Here's my proposed addition. Nothing is changed yet" (S:1917). It applied the change only after his yes (S:1936-1939).
- **An honest take, labelled as one.** "My honest take" on switching the coordinator to DeepSeek (S:1994). A "quick take, to discuss rather than decide" on the DOE framework (S:2890). The funnel's tensions came "with my take on each" (S:3149-3155).
- **Numbers he asked for, given straight.** "Five sub-agents", then a cheaper option and the reason (S:2773-2784).

## 4. What it asked him, and what it decided alone

**It asked only what was truly his:** pushes and merges, money spent, his clicks on his own accounts and network, word choices, and deleting his files. Examples: approving a new machine on his Tailscale network (S:2248-2253), deleting old tick files once two copies exist (S:3157-3159), the two word questions, which "are there whenever you want them, and nothing waits on them" (S:1705-1707). It used the question tool for these (S:542, S:1044, S:1166).

**It settled the rest and reported it in a line.**
- "I fixed one contradiction myself" (S:970).
- "One thing I handled myself rather than ask you": a money-gate question already answered by his rulings (S:1805).
- "It's my call, as you said": how to treat the old transcript's parts (S:106).
- It corrected an agent's misleading finding instead of relaying it. The agent said Hindsight does not fit the server; the session called that misleading, because the 2 GB line was an invented budget (S:2899).

**It filtered agent questions, after one bad miss.** On 18 Oct morning it relayed an agent's questions unchecked. He was angry: most were already settled (S:367). Its reply: "I passed them on without checking them first ... From now on I check each one before it reaches you" (S:370). It then settled each one with evidence in the same message (S:374-382). From then on, agent questions reached him only after it had checked them against his rulings and the merged code. "Two of those three questions shouldn't have reached you" (S:546) shows the filter catching itself.

## 5. How it handled his nudges and corrections

- **It took each nudge as a seed and said back what it would do with it,** in a line or a short list (S:1276, S:1286, S:1459, S:1471).
- **It never restarted the whole run for a correction.** Corrections became rulings plus a targeted pass: the money ruling became one "retirement pass" (S:1064-1068); the unlock became one "whole-app" pass (S:1178-1189). It said so itself (S:2583).
- **It cut and restarted rather than steered a deep agent.** He suspected a running agent 200k tokens deep would not take a message (S:1086). It stopped that agent, checked nothing half-done was left, and started a fresh one with the full brief from the start (S:1099-1110). When the unlock widened scope a minute after a new agent started, it stopped that one too and restarted with the full scope (S:1204-1214). It still sent additions to an agent that had only just started, because the agent would pick them up at its next step (S:1459).
- **It saved each lesson as a standing rule the same turn,** and said so: no caps (S:374), "design for complexity, not a complex system" and no codenames (S:1054), the whole app unlocked (S:1205), generative steps unbounded and then "a funnel; the limit is relevance, not a count" (S:1276, S:1286), the UI is design, not code (S:1813), builders never wait on long commands (S:2792), no invented limits (S:2917).
- **When he was frustrated it owned the miss plainly and fixed it in the same message:** "You're right, and that one's on me" (S:1048), then the answers recorded and the next step running.

## 6. How it recorded rulings and files

- **His rulings went into one numbered rulings file the same day** (105-114, then 115-119, S:931, S:1170). Its state-of-play file was rewritten at each milestone and is "what a fresh session reads first" (S:2765).
- **The UI handoff got a note after every pass** that touched the UI, including banners at its top ("design, not code", "the demo design isn't final", S:1815, S:1823).
- **Stale files were moved to dated archive folders with a SUPERSEDED note, never deleted** (S:916-921, S:933-938).
- **Chat only when he asked for chat only:** "I won't write a report file" (S:205).
- **One seeds file per round,** so every agent read the same version of his words (S:2949).
- **Build programs kept their own store files:** a questions file, a backlog, an ideas file and a resume file, so nothing found was lost and the coordinator never stopped to ask (S:1921-1931).

## 7. What made him trust it

- **It checked agents' results itself before reporting them.** "I checked the spines myself" (S:620), "I checked GitHub" (S:2012), "I checked it directly" for the server email (S:2672), "I checked: every commit on integration is inside engine/base" (S:2410).
- **It did the hands-on work and left only his own clicks to him.** He logged in, it drove the server setup, he approved the machine (S:2023-2031, S:2163-2266). Passwords stayed his throughout.
- **It said exactly where it would stop and what it would not touch while he was away** (S:141-160). When he returned, nothing had moved without him. "Two hours away is fine; nothing was waiting on you" (S:2679).
- **When agents landed while he was away, it only acknowledged them** and waited to go through them with him (S:2547, S:2632, S:3185).
- **It never let the build stall on him.** The never-stop rule and the questions file replaced the coordinator that had waited two hours on one question (S:1914-1931).
- **It kept him on one page across sessions.** It offered to write his chat-only points into files so a fresh session would know them (S:2404). When context ran high it recalled the last day's work before resuming (S:2811-2871).

## 8. What went wrong in the same session (do not copy these)

| What happened | His words | The fix it made |
|---|---|---|
| Relayed agent questions unchecked, re-asking settled things | "it seems like you didn't get a bloody understanding" (S:367) | Filter every agent question first (S:370) |
| Read the old session lightly | "context alignment is key here ... Don't underestimate" (S:390) | Three-agent alignment and its own sort (S:395-403) |
| Built money and sandbox machinery he never asked for; used codenames | "you are designing a very complex system" (S:1042) | Retirement pass; plain words only (S:1048-1068) |
| Too slow, then at risk of cutting too much | "You've taken way too long"; "you might again oversimplify" (S:1071) | Remove only the two named things; keep what works (S:1074-1083) |
| Old "don't touch" locks narrowed the design | "I'm seeding ... expand on top of it" (S:1217) | Unlock pass; locks last one session (S:1205) |
| Limited generative steps to its own examples | "don't try to limit" (S:1273) | Open funnel, relevance as the only limit (S:1276-1286) |
| Looked only at recent code | "I hope you don't only look at the one that was merged today" (S:1468) | Explore every branch and package (S:1471-1476) |
| Could not recall its own workflow when asked | "We had more than that" (S:2559) | Recalled all 12 steps and saved them (S:2568-2582) |
| Read his weekly-limit point as "spend less on design" | "Our work is more important" (S:2944) | Proper agent power for design, thrift for runaway agents (S:2947) |
| Moved toward architecture while he still had seeds | "don't run the architecture yet" (S:2979) | Stop after the funnel and discuss first (S:2982) |

## 9. Habits the lead should copy

1. Ground fully before any generative step: inventory what is built, on every branch, before an idea is called new.
2. Split big reading across agents, then sort and reason over their results yourself.
3. At most three Opus agents at once, each a different job writing its own file, in the background.
4. Cut and restart a deep agent with a full brief; send additions only to one that has just started.
5. Run generative steps wide with no count limit, filter by relevance, and park the rest.
6. Stop after the funnel and talk with him before any architecture.
7. One review, one fix round, one independent fix-check; name the last round as last.
8. Check every agent claim against the code or GitHub before it reaches him.
9. Filter agent questions: only money, his accounts and clicks, his words, and deletions reach him, through the question tool.
10. Settle everything else yourself and report it in one line.
11. Turn every correction into a numbered ruling and a targeted pass, never a restart of the run.
12. Save each lesson as a standing rule the same turn, and tell him you did.
13. Answer in short bold-led bullets: done, running now, next; tables for counts.
14. Open every stock-take with where we are, what's agreed, and what contradicts.
15. Map his dictation back to him in your own words and ask him to correct it.
16. No codenames in front of him; explain any id in one plain sentence.
17. Mark proposals as proposals, and change nothing until he says yes.
18. Give paste-ready prompts in a code block, with one line on what changed and why.
19. Say where you will stop and what you will not touch before he steps away.
20. When results land while he is away, acknowledge them and wait.
21. Do the hands-on work yourself; leave him only his own logins, approvals and money.
22. Keep one seeds file per round so every agent reads the same words.
23. Archive with a note, never delete; push and merge only on his yes.
24. Never let a build wait on him: decide, log the question, keep going.
