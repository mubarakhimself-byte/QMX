# QMA v2 backlog (everything outside the harness build)

This is the operator's backlog (he confirmed on 2026-10-13 04:28 that there is no other one). It replaces `tracker/agent-system/backlog.md`, which is archived.

**Rewritten 2026-10-13 evening** from his own messages in the 2026-10-12/13 planning session (full texts from the raw transcript, not the cut-off digest), the three audits in `reviews/2026-10-13-*.md`, and his evening rulings.

How to read it:
- **Now in scope, so NOT here:** the agent harness (two engines, Claude Agent SDK plus OpenAI Agents SDK; parity with vanilla Claude Code and Codex; permissions and hooks; sessions; compaction and caching; router; usage page; a temporary console) and the deletion of the old agent code.
- Each item stays until it gets its own session, slice or decision.
- **His words** are short quotes from his dictation (spelling as transcribed), with the UTC time. Dates are 10-12 unless marked 10-13.
- **Trigger** is when to pick the item up. **Easy win?** marks small, low-risk, useful items.
- Items Claude found or proposed (not his words) say so. Claude's own new ideas are only in the last section.

## Rulings that changed items here

| When (UTC) | Ruling | Effect on this file |
|---|---|---|
| 10-13 04:14 (Q1) | Publish, install, schedule and "managing" run only when he invokes them or an allow rule permits it. Money is read-only for agents, as a hook. Demo trading and click-around trials are fine for ideas he agreed. | B17, B39 |
| 10-13 04:14 (Q2) | No single golden rule. A copilot methodology is designed later. | B26-B29 |
| 10-13 04:14 (Q3) | Effort works like `/effort` in Claude Code or Codex, out of the box. | In harness scope |
| 10-13 04:14 (Q4) | One vanilla copilot. Sessions have a home (Lab project, Portfolio, general). Mini apps become plugins, not copilots. | B30, B23 |
| 10-13 04:22 | Harness first. Organogram, methodology, workflows and graphs come later. Ship through an orchestrator session, not the factory. | B21, B30, B33 |
| 10-13 evening | Exactly ONE Claude Max account. Background agents use only spare 5-hour Claude usage, default cap 50%, editable. Permission modes and hooks copied from the Claude Agent SDK, rebuilt on the OpenAI side. Computer use through what the SDKs provide (OpenAI strongest); OpenCUA dropped. Providers: Claude subscription, OpenRouter key, Meta Muse, any OpenAI- or Anthropic-compatible provider. UI wiring is a later session. Deletion follows integration → staging → main (main only by his click); QMA v2 lands in `rebuild/base` for now. | B12, B17, B6, Rejected table |

---

## A. Foundations and housekeeping

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B1 | **SQLite corruption-bug exposure** | Python 3.14.6 here bundles SQLite 3.50.4; the WAL-reset bug is fixed only in 3.51.3. qmx-control opens a connection per call, so two writers can collide (HOW-WHY G2; research 30). Fix: one writer per database file, or a newer SQLite. | Found by research 30, not his words | First harness packet | Yes |
| B2 | **GitHub CI has never run** | Every "green" so far is a local `just ci`. Run the same suites in GitHub Actions so PRs show real checks. | Found by `/how`, not his words | Early in harness shipping | Yes |
| B3 | **Pin both SDKs** | `openai-agents` is in no lockfile. `claude-agent-sdk` is pinned only by the old daemon, so deleting it drops the pin. archive/2026-10-13-two-engine/H1-sdk-facts.md has the current facts. | Found by `/how`, not his words | First harness packet | Yes |
| B5 | **Post-deletion end-to-end check** | P16 and the coming deletion remove a lot. Check what still works: mini apps, QML, QMF, QMN, `weekend-watcher`, `macro-daily-bias`. | "we need to really consider what level we are at after removing" (14:39) | After the old-code deletion lands | No |
| B6 | **Branches: `integration`, `staging`, cleanup** | His model is integration → staging → main; main moves only by his click. `integration` isn't ready, so QMA v2 lands in `rebuild/base` for now. Later: fold `rebuild/base` in, create `staging`, delete the junk (61 worktrees, 73 local branches on 10-12). Deletion only with his go, branch by branch. | "deleting is the best because I don't think we need any" (16:22) | After the harness lands | No |
| B11 | **Documentation update** | Done: the project `CLAUDE.md` QMA v2 lane note (10-13 04:24). Left: run `/documentation-factory` in change mode once the harness ships; keep docs live during shipping; the global `CLAUDE.md` bulk-worker line (still Opus 4.8; his rule is Opus or Sonnet 5.5). Ask before editing either `CLAUDE.md`. | "so the agents don't shipped from like thin air" (17:37) | After the harness ships | Partly |
| B21 | **Harness-first re-plan** | Re-run the workflow after his 04:22 change: baseline, `/how` + `/why`, harness architecture, re-plan with parallel packets. **In progress** in the 10-13 evening session: archive/2026-10-13-two-engine/H1-sdk-facts.md and archive/2026-10-13-two-engine/H2-skills-method.md written, destination set to "harness coding prompt plus deletion sequence". | "you are meant to rerun the workflow" (10-13 04:28) | Now | No |
| B24 | **Update the documentation-factory skill** | The skill was written by Claude Code a while back. Rework it with the `technical-writing` skill before its next run. | "we might use it to update our documentation factory skill" (10:34) | Before the next `/documentation-factory` run | Yes |

## B. Methodology: copilots, traders, skills, prompts

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B26 | **Copilot methodology** | How each copilot works. No single golden rule: the Lab copilot gets more freedom, Portfolio less freedom and more instruction, the general copilot combines both. "Never touch money" is a hook, not an instruction. | "the co-pilot in the lab needs more freedom" (10-13 04:14); "you can't really just have one bloody rule" (10-13 04:14) | After the harness passes, with B30 | No |
| B27 | **Trader-agent methodology** | The same thinking for agents that trade, test ideas and run workflows, not just the chat copilots. Tied to the workflows pass. | "it's not just the co-pilot methodology, it's the trader agent methodology" (10-13 04:22) | With B33 | No |
| B28 | **BMAD + Pocock skills as QMX's methodology** | Turn Matt Pocock's and BMAD's skills into QMX skills: building mini apps, day-to-day work. He wants to describe a skill roughly and have it built (for example with `automate-me`). archive/2026-10-13-two-engine/H2-skills-method.md covers how Claude Code ships QMX, not this. | "combining the Matt Pocock skills together with BMAD skills" (10-13 04:14); "give a rough picture of what I want" (10:20) | After the harness, feeds B26 and B27 | No |
| B29 | **System-prompt design** | Never designed. He asked about meta prompts in XML and wants prompts derived from the methodology. Research 31 has a five-layer prompt design he has never seen. | "Can we have system prompts as meta prompts which you can pass with XML?" (16:22) | With B26 | Partly: show him research 31 |

## C. Organogram, plugins and mini apps

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B30 | **Organogram and session homes, derived from the UI** | One vanilla copilot. A session started in a Lab project (an ML run, an experiment, a mini-app build) or in Portfolio keeps that home and context; the copilot page is a shell showing every session with a badge. The general copilot can combine Library, Lab and Portfolio. Work it out from the UI, not on paper. | "look at the UI and sort of derive it from there" (10-13 04:22); "I'm using the session in the shell" (10-13 04:14) | During or after the UI wiring session (B12) | No |
| B31 | **Plugins for Lab and Portfolio** | A plugin is tools/MCP + skills + model + hooks. Lab and Portfolio get their own plugins; a session can load one by default. | "build plugins specifically to the lab specifically to the portfolio" (15:01) | With B30 | No |
| B32 | **Agent as a folder** | Each agent defined as a folder (Eve, OKF, AGENTS.md style). He asked for Claude's take; it was never designed (research `harnesses.md` §6 has a layout). | "an agent as a folder i need your take on that" (08:54) | With B30 and B31 | No |
| B23 | **Mini-app creation design** | How mini apps get created, built, maintained and edited. They become plugins any copilot can load; no app gets its own copilot. Publish and install run only when he invokes them or a rule allows. Seeds: the mini-apps transcript (research note from agent a77ed5e). | "I want to first know how we are going to be creating mini apps" (10-13 04:14); "they can become plugins" (10-13 04:14) | After the harness, with B30 | No |
| B16 | **MCP apps** | Discussed in the UI session, never designed. | "MCP apps they were talked a lot about inside the UI" (15:01) | With B12 and B23 | No |

## D. Workflows, graphs and loops

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B33 | **Workflows / graphs / loops design pass** | Its own design pass before any workflow ships. Agentic, deterministic and mixed; outputs of one feed another; graph and loop engineering. Open question: QMX's own graph engine vs LangGraph (the planning audit calls own-engine risky). Inputs: his clippings ("Agent Harness Engineering vs. Loop Engineering vs. Graph Engineering", "Loop vs Graph Engineering", "Not Every Agent Workflow Needs AI", the loop-engineering quant clipping), the node-editor zip, a Karpathy post he said he would send, Claude's dynamic-workflows cookbook. | "it has to be thought through" (10-13 04:22); "workflows by default should be able to be agentic, non-agentic" (14:39); "graphs and loops give more depth" (17:11); "I'll give you what Andrej Kapathi talked about" (15:53) | After the harness passes | No |
| B10 | **WF1/WF2 rework** | Strategy-from-anything workflows. They change with the risk-and-sizing work in his other session. He handles it. | "WF1 and WF2 are going to change a lot" (09:07) | He says go | No |
| B13 | **Research harness and templates** | Redesign the Lab's built-in research harness (the old one combined open research and Delphi; it may have been overkill) and ship ready-made templates, OpenAI-cookbook style. Catalogue in research 22. | "might have been overkill" (08:54); "a research template is very specific" (17:20) | With B33 | No |
| B34 | **Scheduled jobs (cron), Hermes-style** | Jobs that run later on their own, locally or on a server. Scheduling asks first or needs an allow rule (Q1). | "for cron jobs, look at the Hermes agent" (10:02); "sessions that run on cron jobs that should be there by design" (15:40) | With B33 | No |
| B35 | **A Claude orchestrator that picks models** | Beyond router basics: a Claude model drives long work and picks the best model per task from usage left and strengths (for example GPT for thorough research). Defaults configurable. Must respect the 50% background cap. | "it can choose the best model for the best task" (15:40); "prefer using GPT because it's thorough" (10:34) | After router basics ship, with B33 | No |
| B36 | **Two agents editing the same thing** | When two agents edit the same files and both versions matter: use git branches and variants, and show the comparison in the UI. | "my idea was git is the best option here" (15:22) | With B33 and B42 | No |

## E. Computer use, browser and brokers

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B17 | **Computer use beyond the harness** | Agents click around cTrader, MT5 and TradingView to test agreed ideas on demo accounts; money stays read-only. Evening ruling: use what the SDKs provide (OpenAI strongest); OpenCUA dropped. **Conflict to settle:** H1 facts 8 and 16 say no subscription route has computer use (not in the Claude Agent SDK; OpenAI's ComputerTool needs an API key and is not on the ChatGPT-plan route). Keeps the old UIA checklist: how much of cTrader is drivable. | "these agents by default should have ability to click through" (10:02); "it can trade, it can test out ideas" (10-13 04:14) | After the harness; he decides the paid route | Partly: the UIA checklist |
| B37 | **Video to cTrader trial** | A sub-agent watches a trading video, then tries the idea on cTrader (demo) with computer use. | "try out what was in that video on C trader using computer use" (08:54) | After B17 | No |
| B17a | **Ruling 2026-10-14: browser control and computer use on hold** | Neither ships in the harness build. Both wait for a design that settles the permission hierarchy, concurrency when several requests use them at once, and the compute they need. With one engine there is no subscription computer use; 02b section E lists the MCP routes (Playwright everywhere, desktop control per OS). | "first hold the browser for now ... the same might go for computer use ... unless you can figure out the permissions, the in terms of hierarchy, concurrency and compute needed" (2026-10-14) | After the harness | No |
| B38 | **QMX's own browser with his logins** | A browser profile inside QMX (separate from his personal one) holding logins such as TradingView. | "trading view with my login saved" (10:02) | With B17 | No |
| B39 | **Broker and platform connections** | Connect brokers in Settings, and his local MT5 and cTrader to QMX. Agents read money, never move it. | "brokers are in settings. We need to be able to connect them" (10:02); "connection to my local MT5 or my local CTrader inside QMX" (08:39) | With B17 and Portfolio work | No |

## F. Memory and self-improvement

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B40 | **Memory bake-off** | Use the SDKs' memory by default, keep a pluggable layer (Hermes-style), let an agent in a server workflow have its own memory, then test candidates (Hindsight, Mem0, LangChain memory, plain files). Research: `rebuild/research/2026-10-12-agent-system/memory.md`. | "I want to test out a few" (08:39); "keep the pluggable layer intact here" (16:22) | After the harness | No |
| B41 | **Self-improvement** | Agents keep lessons so they don't repeat a mistake (Hermes method, RLM, OpenAI's improvement-loop cookbook with traces and evals). Revision 1 of the architecture had a `lessons` table that later revisions deleted (recover it, see B53). | "I don't want it to do the same mistake" (10:02); "build an agent improvement loop with traces, evals, and codecs" (16:22) | After B40 | No |

## G. Other QMX parts

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B8 | ~~**Strats (the Library) v2**~~ **OUT OF THIS BACKLOG (operator, 2026-10-13 night): handled in its own session.** | The Library's name is **Strats**. New version as a git-style database (content-addressed blobs, immutable versions, refs for variants; research 30). He floated Gemini for a Library agent. | "strats S T R A T" (10-13 04:28); "refactor it to know like a database of Git" (15:40); "for things like a library-based agent, it might be better" (15:22) | After the harness | No |
| B7 | ~~**QMB review and reorganisation**~~ **OUT OF THIS BACKLOG (operator, 2026-10-13 night): handled in its own session.** | The tamper-proof backtest tool, edited by many models. Dead helpers in `qmb/src/qmb/doors/cli/host.py` keep about 110k old QMA lines importable. Editing QMB needs his say. | "I feel like it has been touched a lot" (16:22) | Once QMX is in normal use | No |
| B9 | ~~**QML changes**~~ **OUT OF THIS BACKLOG (operator, 2026-10-13 night): handled in its own session.** | Proposal from the risk-and-sizing session. | "QML is going to change based off another transcript" (16:22) | His other session | No |
| B42 | **Backend API and database ready for agents** | Make the backend and database usable by agents, and check whether the mini-app runtime needs a refactor. | "make it usable for agents" (15:16) | Before workflows and mini apps (B33, B23) | No |
| B43 | **QMF refactor** | QMF will be refactored "whether I like it or not" (operator, 2026-10-13 night). Replaces the earlier read-and-explain item. | "QMF is just going to be refactored" (10-13 night) | His call on timing | No |

## H. Running elsewhere

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B44 | **Docker test on his server** | Prove the harness runs on Linux in Docker on his own server, with provider adapters kept ready so nothing gets rebuilt later. OpenRouter for remote agents. | "try it out maybe in my server on Docker" (10-13 03:55); "just make sure it can work" (10-13 03:55) | Last harness packet or right after | Partly |
| B45 | **Rented compute** | Modal, E2B, Railway, Amp orbs. Not funded yet. | "Testing them out will be later" (10-13 03:55) | When he has the money | No |
| B46 | **Long-running server sessions** | Sessions and workflows that run for days on a server, move from local to server, use buckets, and export transcript and logs automatically. A session persists; no fresh session per decision. | "you shouldn't spawn up fresh sessions every now and then" (15:40); "automatically export the transcript and the logs" (09:07) | After B44 | No |

## I. UI, voice and QA

| # | Item | What and why | His words (UTC) | Trigger | Easy win? |
|---|---|---|---|---|---|
| B12 | **UI wiring session** | Wire the SvelteKit UI on `ui-review/repair` to the QMA v2 event protocol, browser first. A later, separate session (evening ruling). Everything it must know is in `UI-NOTES.md`. | "it might first be shipped as a browser" (10:40) | After the harness event protocol merges | No |
| B14 | **Phone approvals while the PC is off** | Claude-proposed (journey J17, HOW-WHY X9), not asked for directly. He already drives sessions from his phone with Remote Control. Old wording assumed "no owned server"; he does have a server (B44), so options are his server, a small relay or push service, or Remote Control. His call. | "remote controlling from my phone" (17:52) | He decides | No |
| B15 | **Voice / conversational mode, audio, System 1 models** | Voice chat later, a nice-to-have. GPT audio and image models noted. | "another feature I wanted to ship later is voice or conversational mode" (15:22); "GPT has audio. I love that" (16:22) | Later | No |
| B47 | **QA by user journeys** | `create-verification-skill` plus many complex user journeys driving the real UI, and a fresh-install test. | "couple it together with the UI and an insane amount of complex user journeys" (10:34); "installing it fresh out of the box" (08:39) | After B12 | No |

## J. Research to recover, and ideas waiting for review

From the sub-agent fleet audit §c. He asked that the morning research be used: "All that research should be, by the way, used" (14:45).

| # | Item | What and why | Where | Trigger | Easy win? |
|---|---|---|---|---|---|
| B48 | **Unread cookbook batches** | Batches 01, 02 and 06 were killed before notes: Agent SDK dynamic workflows and hosting, 30 Managed Agents notebooks, the OpenAI Agents SDK set. | `D:/QMX-research/sources/batches/batch01.txt`, `batch02.txt`, `batch06.txt`; texts in `sources/text/` | Harness architecture pass (now) | Yes |
| B49 | **SDK migration notebooks** | **Partly done 10-13 evening:** H1 read `04_migrating_from_openai_agents_sdk`, `05_Building_a_session_browser`, `07_Hosting_the_agent` and OpenAI's `migrate-from-claude-agent-sdk`. Left: `08_Dynamic_workflows` (feeds B33). | `claude-cookbooks/claude_agent_sdk/`; H1 §3 | With B33 | Yes |
| B50 | **Vendor engineering posts** | Agent #25 read 45 pages and saved nothing: how Managed Agents was built, the multi-agent research system, harness design for long-running apps, writing tools for agents, the workflows page. | List in `tracker/agent-system/research/22-cookbooks-and-templates.md:495-497` | Harness pass (tools) and B33 | Yes |
| B51 | **Memory research** | MemoryProvider interface, scopes, Hindsight/Mem0/file bake-off plan. | `rebuild/research/2026-10-12-agent-system/memory.md` | B40 | Yes |
| B52 | **Harness research** | Hermes API modes (§2.1), Codex app-server (§3.8), agent-folder layout (§6), and the cTrader/MT5 automation options. | `harnesses.md`; `notes/harnesses/computer-use-notes.md` | B17, B32 | Yes |
| B53 | **Designs deleted by architecture revisions** | `run_scope`, the self-improvement `lessons` table, live event kinds (`tool.progress`, `terminal.*`, `cursor.*`), `trigger_fires`. | `git show 00a1d1b5:tracker/qma-v2/ARCHITECTURE.md` lines 517, 601, 637 | Live kinds now (UI-NOTES); rest with B41, B34 | Yes |
| B54 | **Caching and compaction facts** | His top priority ("Please, I beg you, focus on it a lot", 09:07). Server-side compaction, `prompt_cache_retention`, context editing, the Opus append-only rule. | `cookbooks.md` ~41-130; `archive/langchain-stack.md` | Harness pass (now) | Yes |
| B55 | **Survey reports never saved to files** | UI, August QMA, September and October code surveys, three LangGraph extraction notes. Save each hand-back to the repo before the scratchpad is cleaned. | Session export `subagents/agent-adf671f…`, `af1e4f2…`, `a06808c…`, `a5c7be9…`, `ade62be…`, `a95b593…`, `aa45fd4…` | Now (scratchpad may vanish) | Yes |
| B56 | **Contabo mentions erased by a misread** | A misread "no owned server" struck them from research 30 and 31. His 10-13 03:55 Docker answer needs them back. | Git history of research 30/31 before commit `07d378c3` | With B44 | Yes |
| B57 | **BASELINE.md** | The only output built on harness-first. **Checked 10-13 evening** fact by fact in archive/2026-10-13-two-engine/H1-sdk-facts.md; still needs its review and `/how` + `/why` inside B21. | `tracker/qma-v2/archive/2026-10-13-two-engine/BASELINE.md` | B21 (now) | - |
| B20 | **25 spin ideas** | `USER-JOURNEYS.md` §3, Claude's proposals, unreviewed by him; some were folded into the design without his say. Spin 15 (usage reserve) is now covered by his 50% ruling; spins 4, 5 and 11 were written on the "no owned server" misread. | `USER-JOURNEYS.md` §3 | After he reads them | No |
| B58 | **Fresh coverage gap list** | 13 FRs missing and 42 partial on architecture rev 3a. Use it as a lookup for later phases, not ARCHITECTURE-CHECK.md. | `AUDIT-2026-10-13.md` §B | When each later phase is planned | Yes |
| B18 | **Firecrawl Alexandria** | Catalogue of data providers for web and documentation work. Not researched yet. | His words: "Firecrawl has this new thing they call Alexandria" (10:02) | When research tools get built | Yes, research |

---

## Rejected or settled against (not backlog)

Recorded so nobody revives them.

| Idea | His words or ruling (UTC) |
|---|---|
| Run other providers' models inside Claude Code, one profile or one Claude Code session per provider | "it was a thought, okay? I wasn't proposing it as the actual design" (15:16); "spawn up a code session for each of these" (15:16, called stupid at ~1 GB per session) |
| Coding-plan subscriptions inside their own CLIs (Kimi Code, GLM, MiniMax, Muse Code) | "KPI keys only to be honest, just design based off the SDK" (15:22). Muse Code plans work only in Meta's CLI (H1 fact 19), so Muse runs on a key |
| Paying Anthropic or OpenAI API, including the $100 Max credit | "I don't want to pay for API ever" (17:11) |
| CLIProxy and disguising traffic as Claude Code | The router "was to replace the CLI proxy" (16:22) |
| Two or more Claude Max accounts in QMX | Evening ruling 10-13: exactly one. Overrides "two accounts of claude" (09:20) |
| OpenCUA for computer use | Evening ruling 10-13 |
| Codex as an engine | "Codex bloody hell is very heavy" (15:16). Its source is studied, not used (10-13 04:22) |
| Epic-factory or queue lanes for QMA v2 | "So we don't need a factory" (10-13 04:22) |
| Sandboxes by default | "I don't think we need sandboxes, really" (16:22) |
| LangSmith | "Lang Smith, I don't think we are going to use it" (10:02) |
| Grok | "I don't intend to use Grok" (15:22) |
| A fresh session per decision in long work | "you shouldn't spawn up fresh sessions every now and then" (15:40) |
| One golden rule for every copilot | "you can't really just have one bloody rule" (10-13 04:14) |

## Closed

| # | Item | Status | Reason |
|---|---|---|---|
| B4 | P16c finish and leftovers | Done 2026-10-12 | 13 PRs (#58-#70) merged. Left: qma-daemon 74,104, qma-core 23,808, qma-wire 15,435 lines, kept alive by `qmb/src/qmb/doors/cli/host.py:104`. Copying the Claude driver recipe (`native_claude.py`, `native_codex.py`, `native_sessions.py`) moves into the deletion sequence, which is now in scope. |
| B19 | His own backlog | Resolved 2026-10-13 04:28 | This file is his backlog. |
| B22 | Audit fixes before coding | Superseded 2026-10-13 | Folded into B21. Answers and seams (platform-neutral secrets and isolation) are harness work; "design computer use" moved to B17; SDK-to-PRD mapping and browser reads of cookbooks are done in H1 (Hermes not yet browsed); the ten plan mismatches belong to the old Wednesday plan, which is parked. |

---

## Claude's suggestions (not his)

| # | Suggestion | Why |
|---|---|---|
| S1 | Look at Meta Muse's computer-use guide (`dev.meta.ai/docs/computer-use.md`, unread) as a key-based route for B17 | Muse is on a key he accepts paying for; OpenAI's ComputerTool needs an OpenAI API key he refuses |
| S2 | Measure RAM per Claude session in the first live Claude packet | The ~1 GiB figure is a documented starting point, never measured on his PC; session caps depend on it |
| S3 | Pause, don't fail, background work when the 50% cap is hit, and resume after the window resets | Days-long Claude runs on Max 5x will hit windows; nothing yet survives a lock-out |
| S4 | Settle the computer-use paid route (B17) as one question with options, before any computer-use design | The evening ruling and H1's facts point in different directions |
| S5 | Reword spins 4, 5 and 11 before he reviews B20 | They assume rented-only compute, which he never said |
