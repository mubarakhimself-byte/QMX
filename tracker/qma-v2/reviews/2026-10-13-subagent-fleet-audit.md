# Sub-agent fleet audit: QMA v2 planning session (2026-10-12 08:13 UTC to 2026-10-13 04:30 UTC)

Auditor: one read-only agent, no sub-agents. This file is the only write.
All times are UTC. "S" means the scratchpad folder `C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/2cf20068-faee-4a56-b4c2-72888c00adb1/scratchpad`.

## How this was checked

- `S/digest/subagents-index.md`: every agent's prompt and last text.
- `S/export/.../subagents/*.jsonl`: parsed with a script for tool counts, web/browser use, spawn attempts, hand-backs, writes and token use. Reads of the big transcript files were measured.
- `S/digest/human.md`: all of the operator's messages, read once in full.
- `S/digest/main.md` and `dialog.md`: searched for every Agent, SendMessage and TaskStop call, every hand-back, and what the coordinator said next.
- Plan files on branch `plan/agent-system` (`D:/QMX-worktrees/agent-system/tracker/...`) and `D:/QMX-research/`: searched for citations of each agent's output.

**Limit:** six agents have no transcript in the export: `a18d959`, `aa9e7a2`, `ad038d7`, `ad43ace`, `add2f85`, `a53ca8f`. All six ran long or were resumed with SendMessage. For them I used the main session, their hand-backs and their files. Their inner steps cannot be audited.

## The operator's rulings over time (what each prompt should have carried)

| Time | Ruling (his words, shortened) | Where |
|---|---|---|
| 08:13 | Sub-agents: Opus 5.5 or Sonnet 5.5, few, background only | human.md:5 |
| 08:54 | Fresh research pass from primary sources; Opus 5.5, medium effort | human.md:67 |
| 09:07 | Don't act on results I haven't read; research goes in the repo; "the mother researcher spawned helpers ... shouldn't resume" | human.md:100 |
| 09:30 | "We are not going to use API keys"; agents won't stop, "none" | human.md:139 |
| 10:02-10:15 | Why not build our own harness on the Agent SDK; plan today, ship later | human.md:155, 161 |
| 14:45 | "All that research [from the morning] should be used in this session from here on out" | human.md:315 |
| 15:16 | Pivot: design for two SDKs only (Anthropic + OpenAI); others via API compatibility | human.md:331 |
| 15:28 | Stopped `/architect` himself; redo the workflow (`/how`, `/why`) after the reshape | human.md:345 |
| 15:40 | Router as load balancer; long sessions persist; "working QMX before Wednesday" | human.md:353-356 |
| 16:40 | Build our own graph system; read cookbooks in the browser; Fable "for once"; 2-3 agents at a time, sequential | main.md:4891, 4895 |
| 17:11 | "i don't have a server ... okay i have a server ... i don't have orbs" (ambiguous) | dialog.md:2466 |
| 17:20-17:37 | You missed things; extract requirements from both transcripts with sub-agents; rerun how/why; use Fable | human.md:383-406 |
| 18:03 | "Use Fable when you want overnight ... not only in architecture" | human.md:417 |
| 03:55 (13th) | Any platform (Linux/Mac/Windows); no rented provider yet, "try it in my server on Docker"; OpenRouter for remote | human.md:429-432 |
| 04:22 (13th) | Build the HARNESS first; organogram later | main.md:6981 |

---

## (a) One row per agent

Key. Depth: d1 = spawned by the main session; d2 = spawned by a sub-agent; d3 = spawned by a sub-sub-agent (every d2 and d3 row is flagged).
Model: O5.5 = Opus 5.5, S5.5 = Sonnet 5.5, O4.8 = Opus 4.8 (bulk-worker pin), F = Fable 5.1.
Prompt: OK = carried the latest rulings at launch; STALE = carried an overtaken ruling; WRONG = carried a misread ruling; PREM = launched before the step it depended on.
Used: ABS = absorbed into the plan; PART = partly; SUP = superseded by a later pivot; IGN = ignored; LOST = nothing usable survived.
Q = quality, 1 (poor) to 5 (strong).

### Morning research wave (2026-10-12)

| # | Start | Agent | Description | Model | Depth | Status | Prompt | Used | Q | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 08:56 | a91f2eb | LangChain stack fresh research | O5.5 | d1 | done 09:13 | OK then; LangChain/CLIProxy frame | SUP | 4 | Good primary sources. Spawned 4 helpers; 1 refused at the 20-agent cap. Kept facts: Opus append-only history, no cron in open-source LangGraph. |
| 2 | 08:56 | a50e5e8 | Agent memory options | O5.5 | d1 | done 09:13 | OK | IGN (mostly) | 4 | 87 tool calls. Hindsight/Mem0 bake-off and MemoryProvider interface. PRD and ARCHITECTURE never name Hindsight; no bake-off design. |
| 3 | 08:56 | ad038d7 | Claude and OpenAI cookbooks | O5.5 | d1 | resumed 09:27 with a stop order; done 09:36; no transcript | OK then | PART | 3 | Spawned 14 helpers. Ran `taskkill //F //IM git.exe` machine-wide (main.md:1858). Honest gap list in cookbooks.md:18-30. |
| 4 | 08:56 | ad43ace | Harnesses, Codex source, Eve, computer use | O5.5 | d1 | done 09:19; no transcript | OK | PART | 4 | Spawned 5 helpers. Hermes model-switching reused in ticket 02. Computer use and agent-folder ideas never reached ARCHITECTURE. |
| 5 | 08:56 | aa9e7a2 | Models, routing, CLIProxy | O5.5 | d1 | handed back unfinished 09:01; resumed 09:27; done 09:33; no transcript | STALE on delivery | PART | 3 | Spawned 3 helpers. Its line 19 still says "copilots run on API keys" after he said no API keys (09:30). Its terms work killed CLIProxy (good). |
| 6 | 08:56 | a18d959 | QMX internal design and UI recovery | O5.5 | d1 | handed back unfinished 09:00; resumed; done 09:13; no transcript | OK | PART | 4 | Spawned 4 helpers; 5+ interim notifications. Used by journeys and mini-app seeds. |
| 7 | 08:57 | adf671f | UI branch survey | O4.8 | **d2** | done | OK | PART | 4 | Report lives only in its hand-back (told not to write files). |
| 8 | 08:57 | af1e4f2 | August QMA arch survey | O4.8 | **d2** | done | OK | PART | 4 | Same: report only in transcript. |
| 9 | 08:57 | a06808c | September arch survey | O4.8 | **d2** | done | OK | PART | 4 | Same. |
| 10 | 08:57 | a5c7be9 | October rebuild code survey | O4.8 | **d2** | done | OK | PART | 4 | Found "P16 retirement did NOT happen, 374 legacy files". Tried 2 more spawns; refused at the cap. |
| 11 | 08:59 | aceb407 | Model pricing line-ups | S5.5 | **d2** | done | OK | PART | 4 | 30 web reads. Flagged "$100/mo API credits (verify)". |
| 12 | 08:59 | aff8d68 | LangChain model mechanics | S5.5 | **d2** | done | OK then | SUP | 3 | Proxy and ChatAnthropic details. Dead after the 15:16 pivot. |
| 13 | 08:59 | a9895be | Model picker UIs and vendor terms | S5.5 | **d2** | done | OK | ABS | 4 | Terms file is why CLIProxy was dropped. |
| 14 | 08:59 | a0299ff | Hermes docs part 1 | O4.8 | **d2** | done | OK | ABS | 4 | Notes reused later by research 30-32. |
| 15 | 08:59 | afe002a | Hermes docs part 2 | O4.8 | **d2** | done | OK | ABS | 4 | Same. |
| 16 | 08:59 | ad92a59 | Codex source notes | O4.8 | **d2** | done | OK | PART | 4 | Tried 2 spawns; refused at the cap. BASELINE re-read Codex later. |
| 17 | 08:59 | aa63e33 | Eve and agent-as-folder | O4.8 | **d2** | done | OK | PART | 3 | Agent folder never designed in ARCHITECTURE (0 hits). |
| 18 | 08:59 | a8f47a0 | Computer and browser use options | O4.8 | **d2** | done | OK | PART | 3 | Reached PRD (FR-137, FR-139). ARCHITECTURE has 0 "computer use". |
| 19 | 09:01 | a9a95ec | Digest Deep Agents core docs | O4.8 | **d2** | done | OK then | SUP | 3 | Deep Agents dropped at 16:40. |
| 20 | 09:01 | aa3e8c4 | Digest Deep Agents extensions | O4.8 | **d2** | done | OK then | SUP | 3 | Same. |
| 21 | 09:01 | af232b1 | Digest LangChain/LangGraph core | O4.8 | **d2** | done | OK then | SUP | 3 | Spawned 3 d3 helpers itself. |
| 22 | 09:03 | ade62be | Extract LangGraph streaming notes | O4.8 | **d3** | done | n/a | SUP | 3 | Sub-agent of a sub-agent of a sub-agent. |
| 23 | 09:03 | a95b593 | Extract LangGraph durability notes | O4.8 | **d3** | done | n/a | SUP | 3 | Same. |
| 24 | 09:03 | aa45fd4 | Extract LangChain agents/HITL notes | O4.8 | **d3** | done | n/a | SUP | 3 | Same. |
| 25 | 09:20 | a0d2577 | Vendor engineering posts + Codex docs | O4.8 | **d2** | KILLED 09:30 | OK | LOST | 1 | 45 web fetches, nothing saved. Spawned 13 min after he raised helper spawning (09:07). |
| 26 | 09:25 | ad91ecb | Cookbook batch 00 | O4.8 | **d2** | done | LangChain mapping | PART | 3 | Notes in `sources/notes/batch00.md`. |
| 27 | 09:25 | a9974e2 | Cookbook batch 01 | O4.8 | **d2** | KILLED 09:30 | same | LOST | 1 | Agent SDK dynamic workflows, hosting, cost optimisation, extended thinking: unread. |
| 28 | 09:25 | aab52af | Cookbook batch 02 | O4.8 | **d2** | KILLED 09:30 | same | LOST | 1 | 30 Managed Agents notebooks: unread. |
| 29 | 09:25 | a45ba15 | Cookbook batch 03 | O4.8 | **d2** | done (TaskStop too late) | same | PART | 3 | |
| 30 | 09:25 | a189519 | Cookbook batch 04 | O4.8 | **d2** | done | same | PART | 3 | |
| 31 | 09:25 | a7cb1aa | Cookbook batch 05 | O4.8 | **d2** | KILLED 09:30 after notes written | same | PART | 3 | |
| 32 | 09:25 | aa3492d | Cookbook batch 06 | O4.8 | **d2** | KILLED 09:30 | same | LOST | 1 | OpenAI Agents SDK set incl. `migrate-from-claude-agent-sdk`, `session_memory`, memory compaction: unread here. |
| 33 | 09:25 | a52ac7e | Cookbook batch 07 | O4.8 | **d2** | done | same | PART | 3 | |
| 34 | 09:25 | a93a12b | Cookbook batch 08 | O4.8 | **d2** | KILLED 09:30 after notes written | same | PART | 3 | |
| 35 | 09:25 | abc0592 | Cookbook batch 09 | O4.8 | **d2** | done | same | PART | 3 | |
| 36 | 09:25 | a235842 | Cookbook batch 10 | O4.8 | **d2** | done | same | PART | 3 | |
| 37 | 09:25 | a05f9cf | Cookbook batch 11 | O4.8 | **d2** | done | same | PART | 3 | |
| 38 | 09:25 | acef7a3 | Cookbook batch 12 | O4.8 | **d2** | done | same | PART | 3 | |

### Tickets and the afternoon (2026-10-12)

| # | Start | Agent | Description | Model | Depth | Status | Prompt | Used | Q | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| 39 | 10:10 | a7afbdc | Ticket 01: Agent SDK capability audit | O5.5 | d1 | done 10:21 | OK | PART | 4 | Verdict "not the base for every agent" overturned at 15:16. Turned a doc's "1 GiB is a reasonable starting point" into "~1 GiB floor" (01:149 vs 01:322). |
| 40 | 10:10 | a5e1bdd | Ticket 05: usage and limits telemetry | O5.5 | d1 | done 10:19 | OK | PART | 4 | Ledger shape used. Per-account series never designed (FR-050 partial). |
| 41 | 14:12 | a498a22 | /how pass for ticket 02 | O5.5 | d1 | done 14:21 | OK then (B vs C on LangGraph) | SUP | 4 | Archived; reused by #47. |
| 42 | 15:24 | aa9660f | /architect: QMX agent engine design | O5.5 | d1 | KILLED by operator after 78 s | **STALE** + PREM | LOST | 1 | Carried "two lanes: Claude Code + own engine" 8 min after his two-SDK proposal; skipped the /how-/why redo. |
| 43 | 15:29 | ad9d96c | Ledger of today's transcript | O5.5 | d1 | done 15:38 | OK | ABS | 4 | Read the transcript in chunks. Fed #49. |
| 44 | 15:41 | a0dd81e | Two-SDK documentation study | O5.5 | d1 | done 15:54 (scope added 15:48) | OK | PART | 4 | Engine mapping used. Its "keep LangGraph" was overruled. Never re-mapped against the PRD. |
| 45 | 16:43 | a77ed5e | Mini-apps transcript seeds | O5.5 | d1 | done 16:49 | OK | ABS | 4 | Read all 227 KB. Mini-app creation itself deferred (BACKLOG B23). |
| 46 | 16:43 | a58c9ef | Cookbooks and templates "browse" | O5.5 | d1 | done 16:53 | OK | PART | 3 | Had the browser tools and was told to prefer them; used firecrawl. Trimmed to fit 500 lines. Left Claude `04_migrating_from_openai_agents_sdk` unread. |
| 47 | 16:43 | a19fb18 | /how + /why integration surface | O5.5 | d1 | done 17:03 | OK | ABS | 4 | Cited 8 times in HOW-WHY. |
| 48 | 17:13 | a5c3e2f | QMA v2 architecture | F | d1 | KILLED 17:21 by coordinator | PREM | LOST | 1 | Launched before requirements were extracted. Spent the "for once" Fable permission. |

### Requirements, architecture and the night (2026-10-12 to 10-13)

| # | Start | Agent | Description | Model | Depth | Status | Prompt | Used | Q | Note |
|---|---|---|---|---|---|---|---|---|---|---|
| 49 | 17:24 | af76048 | Requirements from today's session | O5.5 | d1 | done 17:33 | OK | ABS | 4 | Read all 17 chunks (440 KB) once; "several passes" was one read plus consolidation. |
| 50 | 17:24 | a5992e2 | Requirements from old audit session | O5.5 | d1 | done 17:35 | OK | ABS | 4 | Read ~320 KB in full. |
| 51 | 17:36 | a9870b3 | Merge into QMA v2 PRD | O5.5 | d1 | done 17:56 | **WRONG** ("no owned server") | ABS | 3 | Also shrank NFR-T33 "read in a browser" to NFR-028 "primary sources". |
| 52 | 17:57 | ae1a528 | /how + /why against the PRD | O5.5 | d1 | done 18:11 | OK | ABS | 3 | Padded to reach a line target ("short of 450 ... I'll add"). |
| 53 | 17:59 | aecf410 | User journeys and spin | O5.5 | d1 | done 18:06 | WRONG (rented compute) | ABS | 4 | 25 spin ideas; some folded into design before he saw them. |
| 54 | 17:59 | a8c962b | Research 30: agents and databases | O5.5 | d1 | done 18:12 | WRONG (rented compute) | ABS | 4 | 42 web/paper reads. SQLite bug B1 came from here. |
| 55 | 17:59 | a170158 | Research 31: tools, skills, prompts, comms | O5.5 | d1 | done 18:10 | WRONG | PART | 4 | Prompt layers used; ARCHITECTURE cites it once. |
| 56 | 17:59 | aa4498c | Research 32: DevOps lens and UI protocol | O5.5 | d1 | done 18:08 | WRONG | ABS | 4 | Event protocol and three planes used. |
| 57 | 18:12 | aa79e8f | /how + /why delta pass 2 | O5.5 | d1 | done 18:20 | WRONG | ABS | 4 | Struck Contabo from research 30/31 because of the misread (main.md:5842). |
| 58 | 18:22 | a815f39 | Architect runner A (SDK-native) | F | d1 | done 18:36 | WRONG + Windows-only | ABS | 4 | Fed the synthesis. |
| 59 | 18:22 | a7ad0b0 | Architect runner B (QMA kernel) | F | d1 | done 18:31 | same | ABS | 4 | Fed the synthesis. |
| 60 | 18:36 | add2f85 | Architecture synthesis (+ revisions 2, 3, 3a) | F | d1 | done 18:47; revised 19:02, 19:36; hit usage limit 19:42; resumed 23:11; done 23:16; no transcript | same | ABS | 4 | Revisions deleted NEXT designs that rev 1 had. |
| 61 | 18:48 | ac6201e | Architecture coverage check | O5.5 | d1 | done 18:56 | OK | ABS | 4 | Run once, on revision 1 only. |
| 62 | 18:48 | a9910f2 | Adversarial review (Opus) | O5.5 | d1 | done 19:00 | OK | ABS | 4 | Strong runtime findings. |
| 63 | 18:48 | ae8c2f6 | Adversarial review (Sonnet) | S5.5 | d1 | done 19:01 | WRONG (told to enforce "no owned server") | ABS | 4 | |
| 64 | 19:21 | a53ca8f | Delta pass 3 (+ pass 4 at 23:17) | O5.5 | d1 | done 19:36 / 23:20; no transcript | OK | ABS | 4 | Checked named fixes only; missed the deletions. |
| 65 | 23:21 | a5fbe60 | Shipping plan + orchestrator prompt | O5.5 | d1 | done 23:36 | OK then (Wednesday demo) | SUP | 4 | Overtaken at 04:22 by "harness first"; only packet 0 kickoff survives. |
| 66 | 03:57 | aa09dfe | Independent audit of overnight work | O5.5 | d1 | done 04:09 | OK | PART | 5 | Best agent of the run. Fixes parked as B21/B22. Missed the 32 nested agents and the Opus 4.8 use. |
| 67 | 04:15 | ae137c8 | Plain explainer of the harness | O5.5 | d1 | done 04:18 | OK | PART | 4 | HOW-IT-WORKS.md. He said he would not read documents. |
| 68 | 04:24 | ae081e9 | Harness baseline: Claude Code + Codex | O5.5 | d1 | still running when the session ended (transcript stops 04:30; file committed 04:37) | OK, but "treat SIWC as given" | LOST to the session; file exists | ? | BASELINE.md was never read by the coordinator. |

### Totals

- **68 agents.** 36 at depth 1, **29 at depth 2, 3 at depth 3**. All 32 nested agents came from the morning wave.
- **Models:** Opus 5.5 31; Sonnet 5.5 4; **Opus 4.8 29** (every bulk-worker); Fable 5.1 4.
- **Killed:** 8 (6 by TaskStop at 09:30, `/architect` by the operator, the first Fable by the coordinator).
- **Interim hand-backs that needed a resume:** 3 (#3, #5, #6). Resumed for more work: 2 more (#60 three times, #64 once).
- **Refused at the 20-agent concurrency cap:** 5 spawn attempts at about 09:01.
- **Cache-write tokens in the 62 surviving transcripts:** about 15.9 M. Nested agents: 5.8 M, about 36%. Fable: 1.9 M.
- **Browser use by any sub-agent: zero calls.** Web reading was firecrawl, WebFetch and Context7.

---

## (b) The 10 most important findings, worst first

### 1. The morning wave ran away: 32 nested agents, wrong model, cap hit

- The six researchers launched at 08:56 had no "don't spawn sub-agents" line. Their prompts: main.md:585-600.
- They spawned 29 helpers, and one helper spawned 3 more. That is depth 3.
- 29 of them ran on Opus 4.8 through `bulk-worker`. His rule since 08:13 was Opus 5.5 or Sonnet 5.5 (human.md:5). The global CLAUDE.md bulk-worker line overrode him silently. BACKLOG B11 admits the line is wrong.
- At about 09:01 the session hit the 20-agent cap. Five spawns were refused (a91f2eb, a5c7be9, ad92a59 transcripts).
- He flagged helper spawning at 09:07 (human.md:100). Fourteen more helpers started after that: #25 at 09:20 and #26-38 at 09:25.
- The "no sub-agents" rule entered prompts only at 09:27. The coordinator's own memory note says this "burned half his usage" (main.md:1633).
- At 09:30 he said nothing was stopping (human.md:139). Six were killed at 09:30:54-56 (main.md:1672-1714).
- **Damage:** half a usage window gone before planning started. Lost work (finding 8). His trust in "background agents" damaged.

### 2. A misread ruling was copied into 10+ prompts: "no owned server"

- At 17:11 he dictated: "i don't have server ... okay i have a server ... i don't have orbs" (dialog.md:2466).
- The coordinator read it as "you don't own compute" and withdrew Contabo (main.md:5022).
- That reading went into the PRD prompt as a ratified constraint (main.md:5248). From there it reached:
  - research 30, 31 and 32;
  - the journeys;
  - delta pass 2, which struck Contabo mentions (main.md:5842);
  - ARCH-BRIEF, both Fable runners and the synthesis;
  - the Sonnet reviewer, who was told to enforce it (main.md:6118).
- At 03:55 he said the opposite: no rented provider yet, "try it in my server on Docker" (human.md:432).
- **Damage:** placement, phone approvals (B14), remote runs and the demo were designed for rented compute he does not want. The in-session audit (AUDIT-2026-10-13.md item 10) caught the effect, not the cause.

### 3. The pivot to two SDKs was not carried through the fleet; morning research was dropped

- Every morning prompt framed QMX as "LangChain v1 + LangGraph + Deep Agents" with CLIProxy. Batch notes even guess a "LangChain/DeepAgents mapping" for each notebook (`sources/batches/PROMPT.md`).
- After the 15:16 pivot, no agent was asked to re-read the morning findings through the two-SDK lens.
- At 14:45 he asked that "all that research should be used in this session from here on out" (human.md:315).
- The architects' brief lists ten research files from the afternoon. From the morning it keeps only `models-routing.md` (ARCH-BRIEF.md:20-38). memory.md, harnesses.md, cookbooks.md and qmx-internal.md were not inputs. The audit agent confirms this (AUDIT-2026-10-13.md:39).
- Results in ARCHITECTURE.md:
  - 0 mentions of "computer use";
  - 0 of "organogram" (renamed "seats", a word he never used);
  - 0 of Hindsight or a memory bake-off;
  - 0 of "system prompt";
  - 5 of caching, which he called top priority ("please, I beg you, focus on it").
- **Damage:** about 38 morning agents produced research that mostly reached the plan second-hand or not at all. His "you missed a lot" (17:20, 04:28) is accurate.

### 4. Agents launched on stale or premature briefs, then killed

- `/architect` (#42, 15:24). Its brief said "two lanes: Claude Code driven through the SDK + QMX's own engine". That was 8 minutes after he proposed two SDKs. It also skipped the `/how` and `/why` redo. He killed it himself (human.md:345).
- The first Fable architect (#48, 17:13) was launched before any requirements had been extracted from the transcripts. That extraction was the step he had asked for at 16:40. The coordinator killed it at 17:21 after he objected (main.md:5076). It used up his "Fable for once" permission.
- **Pattern:** the coordinator jumped to architecture twice, and both times he had to stop it. The prompts claimed "Ratified (do not re-open)" for things he had just re-opened.

### 5. The revision loop checked only what changed, and drifted to Windows security plumbing

- Coverage was checked once, on revision 1 (#61). Delta passes 3 and 4 checked only the named fixes.
- The revisions deleted designs revision 1 had, and no agent noticed:
  - the `lessons` table and self-improvement;
  - `run_scope`;
  - `trigger_fires`;
  - live event kinds.
- Proof: `git show 00a1d1b5:tracker/qma-v2/ARCHITECTURE.md` lines 517, 601, 637. AUDIT-2026-10-13.md:82 confirms it.
- Five serial agent passes (#60-#64) went into signing keys, a `qmx-agent` Windows user, CreateProcessWithLogonW, DPAPI and firewall rules. His own priorities (caching, tools, memory, hooks, organogram) stayed thin. At 03:59 he asked what had happened to exactly those.
- His 03:55 answer, "any platform", undercut the Windows-only work.

### 6. A sub-agent killed every git process on the machine

- The cookbooks researcher (#3) ran `taskkill //F //IM git.exe` at about 09:15. It reported this itself (main.md:1858).
- His separate P16c coding session was running at the time. The coordinator found no stale lock afterwards.
- Nothing in the prompt forbade machine-wide process kills.

### 7. "Read it like a human, in the browser" was asked for and not done

- He asked for browser reading at 08:54 and again at 16:40.
- The coordinator's memory note turned "browser" into "browser (or full-page scrapes)" (main.md:4940).
- #46 had all `mcp__Claude_Browser__*` tools and was told to prefer them. It used firecrawl, 24 times, and said so (22-cookbooks-and-templates.md:499).
- Hermes was never opened in a browser (AUDIT-2026-10-13.md:47).
- The PRD merge (#51) shrank the requirement from "read primary sources in a browser" (26:414) to "research reads primary sources" (PRD.md:442).
- **Zero browser calls across all 68 agents.**

### 8. Killed agents threw away the most relevant reading

- #25 (vendor engineering posts and Codex docs) made 45 web fetches and saved nothing.
- Batches 01, 02 and 06 were killed before writing notes (cookbooks.md:18). They held exactly the notebooks that mattered after the pivot:
  - Agent SDK dynamic workflows and hosting;
  - 30 Managed Agents notebooks (team coordination, HITL gate, watch sub-agents live);
  - the OpenAI Agents SDK set, including `migrate-from-claude-agent-sdk`, `session_memory` and memory compaction.
- #46 later read the OpenAI migration guide. The Claude one, `04_migrating_from_openai_agents_sdk.ipynb`, was never read (22-cookbooks-and-templates.md:495).

### 9. Hand-back churn, missing transcripts, and a 3.5-hour stall

- Parents handed back "interim" while their helpers still ran. The coordinator had to resume three of them (#3, #5, #6). #6 alone sent 5+ empty notifications (main.md:799-863).
- The six longest-lived agents have no transcript in the export, including the Fable synthesis and delta passes 3 and 4. The core of the architecture cannot be audited step by step.
- The Fable synthesis hit his session limit at 19:42 (main.md:6470). Nothing moved until 23:11.
- The last agent (#68) was still running when he closed the session. Its BASELINE.md landed afterwards and was never read.
- Concurrency rule: at 16:40 he said "two to three agents open". At 17:57-17:59 five ran at once (#52-#56).

### 10. Unverified claims hardened as they moved up the chain

- **RAM.** Anthropic's hosting doc says "1 GiB ... is a reasonable starting point" (01:149). Ticket 01 wrote "~1 GiB floor" (01:322). He then reasoned from "one gig per session" as a hard fact (human.md:321, 327).
- **API credits.** "$100/mo API credits (verify)" (pricing:30; models-routing:192 "UNVERIFIED") reached him as a plain fact in a question at 17:11. He answered angrily that he won't pay for API.
- **Sign in with ChatGPT.** Research flagged its limits: Responses API only, `store:false`, no pooling (subscription-terms.md; PRD A-01). The baseline prompt (#68) says "treat it as given".
- **Line targets.** They caused padding (#52) and trimming (#46, #21).
- **The in-session audit.** #66 says all agents were Opus 5.5 apart from one Sonnet and four Fable (AUDIT-2026-10-13.md:63). It missed the 29 Opus 4.8 helpers.

---

## (c) Valuable results that were lost or ignored: recover these

Paths in the repo are on branch `plan/agent-system` in `D:/QMX-worktrees/agent-system/`.

1. **Unread cookbook batches.** The file lists are `D:/QMX-research/sources/batches/batch01.txt`, `batch02.txt` and `batch06.txt`. The texts are under `D:/QMX-research/sources/text/`. Re-read them through the two-SDK lens.
2. **Claude ↔ OpenAI SDK migration notebooks.** These are the closest thing to a ready map between the two engines.
   - `D:/QMX-research/sources/repos/claude-cookbooks/claude_agent_sdk/04_migrating_from_openai_agents_sdk.ipynb`
   - In the same folder: `05_Building_a_session_browser.ipynb`, `07_Hosting_the_agent.ipynb`, `08_Dynamic_workflows.ipynb`
   - `D:/QMX-research/sources/text/openai/examples/agents_sdk/migrate-from-claude-agent-sdk/`
3. **Vendor engineering posts.** Agent #25 died with nothing saved. The list of unread Anthropic posts is in `tracker/agent-system/research/22-cookbooks-and-templates.md:495-497`: how Managed Agents was built, the multi-agent research system, harness design for long-running apps, writing tools for agents, and the workflows page.
4. **Memory research.** `rebuild/research/2026-10-12-agent-system/memory.md`: the MemoryProvider interface, scopes and the Hindsight/Mem0/file bake-off plan. ARCHITECTURE has only a bare `MemoryProvider` seam with no per-agent binding (audit FR-092, FR-094).
5. **Harness research.** `rebuild/research/2026-10-12-agent-system/harnesses.md`: §2.1 Hermes API modes, §3.8 the Codex app-server and §6 the agent-folder layout. Also `notes/harnesses/computer-use-notes.md`, the cTrader/MT5 automation options; ARCHITECTURE has none of it.
6. **Caching and compaction facts.** These are his top priority.
   - `rebuild/research/2026-10-12-agent-system/cookbooks.md` around lines 41-130: server-side compaction, `prompt_cache_retention`, context editing.
   - `archive/langchain-stack.md`: the Opus append-only rule.
   - Feed both into the harness design now. BASELINE.md has rows on this too.
7. **Raw survey reports that were never written to files.** They exist only as hand-backs inside the export:
   - `S/export/.../subagents/agent-adf671fb23e7357b6.jsonl` (UI, 25 KB);
   - `agent-af1e4f2f33df557b1.jsonl` (August QMA, 34 KB);
   - `agent-a06808ccdecea28ef.jsonl` (September, 29 KB);
   - `agent-a5c7be96326cace4d.jsonl` (October code, 33 KB, including the "P16 retirement did not happen" count);
   - the three d3 extraction reports in `agent-ade62be0d5134ab92`, `agent-a95b5938573a60a15` and `agent-aa45fd447fd2fd265`.
   - Extract the SubagentHandback message from each and save it to `rebuild/research/2026-10-12-agent-system/notes/` before the scratchpad is cleaned.
8. **Designs deleted by the revisions.** Use `git show 00a1d1b5:tracker/qma-v2/ARCHITECTURE.md`:
   - line 517, `run_scope`;
   - line 601, the self-improvement `lessons` table;
   - line 637, live event kinds (`tool.progress`, `terminal.*`, `cursor.*`);
   - and `trigger_fires`.
9. **The Contabo server, which the misread erased.** The struck Contabo mentions are in the git history of research 30 and 31, before commit `07d378c3`. The 03:55 Docker answer needs them back.
10. **BASELINE.md.** `tracker/qma-v2/BASELINE.md` (commit 44c62f53). It is the only output built on the harness-first ruling, and nobody has read it yet.
11. **The 25 spin ideas.** USER-JOURNEYS.md §3 (BACKLOG B20). He has not reviewed them, and some were built into the design without his say.
12. **The fresh coverage check.** AUDIT-2026-10-13.md §B: 13 FRs missing and 42 partial on revision 3a. This is the current gap list, not ARCHITECTURE-CHECK.md.

---

## (d) Rules for how the next session should use sub-agents

**Spawning**
1. Every prompt starts with: "Do NOT spawn sub-agents or workflows. Do the work yourself."
2. Pass `model: "opus"` or `"sonnet"` explicitly. Never use `bulk-worker` while it is pinned to Opus 4.8. His rule is Opus 5.5 or Sonnet 5.5.
3. No Fable unless he names the exact seat and count in this session.
4. At most 2-3 agents at a time. Launch them in one message. No new launch while he is dictating, until his last message is fully read.
5. Size each job so one agent finishes inside one 5-hour window. Prefer two short agents in a row over one long one with resumes.

**Prompts**
6. Rulings go into prompts as **his quoted words, with the time**, never only as the coordinator's paraphrase. Mark anything ambiguous "UNCONFIRMED: ask him". The "no owned server" misread would have been caught here.
7. Before every launch, check the prompt against the rulings table (top of this file, kept up to date). A ruling newer than the prompt means rewrite the prompt.
8. After any pivot, list every earlier output by name and either:
   - re-run it through the new lens, or
   - mark it SUPERSEDED in FILE-INDEX.
   Nothing just drops out of the inputs.
9. No line-count targets. Ask for "complete, no padding, say what you left out".
10. For tool rules that matter ("use the browser"), say what to do when the tool fails, and check the transcript for compliance before accepting the result.
11. Forbid destructive commands outside the agent's own folder: no `taskkill` or `Stop-Process` by image name, no `git checkout`, `switch` or `reset`, nothing machine-wide.

**Order**
12. Follow the agreed order strictly: requirements → SDK mapping against the requirements → `/how` → `/why` → architect → full check → plan. Never launch a step whose input is not written and committed.
13. Every revision of a design gets a **full** re-check against the requirement list, not a check of the diff. A verifier also lists anything that disappeared.

**Results**
14. Every agent writes its result to a file in the repo (`tracker/...`). Reports that live only in a hand-back get lost.
15. When an agent returns, the coordinator writes one line in the pass log: absorbed into which file, or why not. An unread output blocks the next step.
16. Facts marked UNVERIFIED stay marked all the way up. Never ask him a question built on an unverified claim without saying so.
17. Do not act on results he has not read. Acknowledge only (his 09:07 rule).

**Stopping and costs**
18. When he says stop, TaskStop every running agent at once. Don't send a polite message asking a parent to stop its children.
19. Keep the export complete: avoid SendMessage resumes for long work, because resumed agents' transcripts went missing. Start a fresh agent with the previous file as input instead.
20. Before the session ends, list running agents and either wait for them or stop them. Note their output paths in the handoff.

Path of this file: `C:/Users/Mubarak/AppData/Local/Temp/claude/C--Users-Mubarak-Desktop-QMX/2cf20068-faee-4a56-b4c2-72888c00adb1/scratchpad/digest/SUBAGENT-AUDIT.md`
