# Voice-call requirements ledger (operator <-> Aurelius, early Oct 2026)

Sources (raw line numbers refer to these files):
- **T1** = `voice-thread-01a0f5f6-1002-7116-96dd-75a022c06059.txt` (1741 lines). Several calls across ~3 days:
  audit debrief + day plan (L18-418), "is this the final way" (L430-483), personal/career call (L495-1145, SKIPPED),
  backend-first / acceptance-runner call (L1158-1738).
- **T2** = `voice-thread-01a1006a-f46e-7416-8c11-a666e17b207b.txt` (1407 lines). Several calls Sat-Sun:
  QMA read-only audit kickoff (L18-93), agentic architecture pick-up (L104-168), Sunday frustration + mature-SDK pivot
  (L180-807), LangGraph/Deep Agents/memory/Hermes/BMAD overnight-seed call (L819-1403).

Caveats:
- Rolling transcript windows repeat; deduped. Some user turns start mid-utterance in the source ("…sion-based",
  T2 L668; "…is something maybe I'm requesting", T2 L1105) — the start of those utterances is not recoverable.
- Personal education/career/health content (T1 L495-1145) intentionally not recorded.
- Aurelius statements (counts of tests passing, "SDK integrated", "134 focused tests pass", epic numbers) are
  claims only, NOT evidence anything was built. Quotes are verbatim fragments (<20 words), speech-recognition errors kept.
- Recognition fixes used: "Langraf/Lang graph" = LangGraph, "Lang fuse" = Langfuse, "BMod" = BMAD, "Demyon" = daemon,
  "get BB" = getbb.app, "goal mod" = Codex goal mode, "Q&A" = QA.

---

## 1. Operator requirements ledger

### 1A. Product goal / release

| ID | Src | Requirement (plain words) | Quote |
|---|---|---|---|
| R-001 | T1 L129 | First user goal: operator runs his own first mini app and his own copilot inside QMX. | "running my first mini app myself, you know, my own copilot in QMX" |
| R-002 | T1 L171 | End goal (day 1): fix audited issues then repackage everything as an installable release. | "We fix the issues ... Then we repackage the entire thing into a release" |
| R-003 | T1 L171 | Release must install fresh out of the box; GitHub or website, operator indifferent. | "install it fresh out of the box from GitHub or from a website" |
| R-004 | T1 L171 | Operator should not have to stitch pieces together manually. | "connect one piece onto another, that really is a bit tiring" |
| R-005 | T1 L226 | Startup experience after normal install must be reviewed (was discussed day before). | "We shall look at how it starts up, seriously" |
| R-006 | T1 L171 | Trading expected achievable "before the weekend". | "trading can be achieved probably before the weekend" |
| R-007 | T1 L1233 | SUPERSEDES R-002 as sequencing: backend must work in code first; release is NOT the way to attack this. | "finishing a whole release, I don't think is the right way" |
| R-008 | T1 L1233 | Once core backend works, UI + release are "way simpler". | "the UI and making a release, I think is way simpler, if the core backend works" |
| R-009 | T2 L185 | With UI done, there is "no excuse" for not having a working platform; find what is wrong / unbuilt. | "there is literally no excuse anymore for us to not have a working platform" |
| R-010 | T2 L281/309 | Finish before Monday; operator starts testing Monday. | "I want today over this before Monday" |
| R-011 | T2 L903 | Overnight run target: wake up to roughly "80%" of a working QMX (operator flags number as fake). | "I want to wake up tomorrow to almost... around 80% of our working QMX" |
| R-012 | T2 L590 | "Make it work first" — functional platform precedes cleanup/refactor. | "change works first, that's the goal, okay?" |

### 1B. Backend / database / API / ingestion (no-UI proof)

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-020 | T1 L1200 | Priority = stability of backend, database and APIs (not the UI). | "what I want is stability in the backend, database and APIs" |
| R-021 | T1 L1200 | Codex's backend work is the biggest risk; UI assembly Claude can handle alone. | "the biggest issue right now is Codex's work" |
| R-022 | T1 L1233 | Backend focus especially on mini-app introduction (operator recalls ~Epic 60; check BMAD epics/docs). | "Especially with the introduction of mini apps. That was around Epic 60" |
| R-023 | T1 L1233 | Sequence: make code work -> fewer bugs -> connect everything -> external access. | "we make sure that okay, we can now connect everything together" |
| R-024 | T1 L1233 | All of this proven WITHOUT the UI. | "All this has to happen without the UI" |
| R-025 | T1 L1233 | Backend must create databases/storage for mini apps. | "Creating of databases for mini apps, stuff like that" |
| R-026 | T1 L1233 | Ingestion in and out: reach external world and populate/control things internally. | "Ingestion. So in and out, okay?" |
| R-027 | T1 L1233 | Prove the code actually works, not just tests passing. | "Not with tests rather. But, making sure that the code bloody works" |
| R-028 | T1 L1303 | Preserve existing code; patch and stitch independent pieces rather than rewrite ("like compiling"). | "can't we just maybe, patch and uh stitch them together properly" |
| R-029 | T1 L1303 | Classify what is right/wrong/works/doesn't in existing code before changing it. | "given the code we have, what is right, what is wrong, what works" |
| R-030 | T1 L1452 | QMB/QMD need full backtest run-throughs, with dummy data, run by code not tokens. | "we need to run an entire backtest run through ... we are going to have to create dummy stuff" |
| R-031 | T1 L1452 | Test runs should be non-token-intensive scripts left running (DevOps-style testing outside codebase). | "these things are not token intensive, so we write code ... and let it run" |
| R-032 | T1 L1514 | Run independent test lanes in parallel (QML is broad). | "we can test all of them in parallel, if I'm not mistaken" |
| R-033 | T1 L1558 | QMX runs ML and ordinary Python code; that must be tested too. | "QMX can run ML and uh normal Python code. That also needs to be tested" |
| R-034 | T1 L1558 | Docs + BMAD output (4 months of re-architecture) are the authority on scope, more than operator recall. | "the documentation and uh the BMAD output will give you more than what I can" |
| R-035 | T2 L903 | Database, DevOps and API layer under-considered; every change regresses it, esp. for mini apps and agents. | "database, the DevOps, and the API layer, that part hasn't been considered a lot" |
| R-036 | T2 L460 | Dead-code audit required: no commented-out or abandoned code bloating the codebase. | "eight thousand lines of code, yet ... only two thousand are being used" |
| R-037 | T2 L528 | Dead-code audit is global across the whole backend, not just QMA. | "I want it to be globally like... in the entire backend" |
| R-038 | T2 L590 | Integrate skills for refactoring parts of codebase — but only after platform works. | "some parts of this code base might need some refactoring" |
| R-039 | T2 L971 | Cleaner codebase architecture needed; use skills to improve it. | "We need to improve this codebase architecture" |

### 1C. Paper trading / external connections / DevOps / observability

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-050 | T1 L274 | After live platform, leave it paper trading overnight; agent runs DevOps (logging, monitoring). | "tonight we can leave it paper trading and maybe I leave you ... running DevOps" |
| R-051 | T1 L274 | Identify and wire external connections the system needs. | "we look at external connections we need" |
| R-052 | T1 L1303 | Paper trading is "very big"; recover the original week-long paper soak from pre-mini-app epics. | "a whole week paper trading, whereby we were meant to have an agent do logging" |
| R-053 | T1 L1303 | A separate monitoring agent watches logs/observability (not the trading agent). | "Not the one doing it, but like monitoring, the logs and all that" |
| R-054 | T1 L1303 | External access needs API keys; operator hasn't thought about how; mock data suspected. | "the agents were generating a lot of mock data, to be honest" |
| R-055 | T1 L1558 | Paper week must not stall work: runs in background while UI and release ship. | "paper trading can run, like, in the background" |
| R-056 | T1 L1558 | Gate: confirm pre-live paths and mini apps work and combine before paper runs. | "if we confirm that things before live trading work" |
| R-057 | T2 L668 | Own tracing and logging preferred; Langfuse suggested. | "I would prefer we have our own tracing and logging ... Lang fuse" |
| R-058 | T2 L903 | Operator believes LangSmith is in place for logging, observability and traces (unconfirmed). | "here I think we have LangSmith, uh, for logging and observability" |

### 1D. QA process

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-070 | T1 L274 | Combining pieces properly is a distinct problem; changes the audit approach. | "making sure it is combining properly. So that is another problem" |
| R-071 | T1 L274 | QA phase: an agent looks at the UI and tries to break the application. | "an agent is looking at the UI trying to break the application" |
| R-072 | T1 L274 | Considering TestSprite for QA. | "Am I thinking of using test sprite?" |
| R-073 | T2 L629 | Integration QA across whole platform: how QMA integrates everywhere. | "across the entire platform, how does QMA integrate?" |

### 1E. Agentic system (QMA) — SDK choice

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-080 | T2 L47 | First QMA task: understand what exists — architecture, code, docs, docwork — via local Codex agent. | "get to know what is actually there, um how it works, how it's intended" |
| R-081 | T2 L89 | Spawn agents to go faster; finish before 1 PM. | "spawn up agents, okay? ... I want to finish before 1 PM" |
| R-082 | T2 L105 | Agentic architecture is "one of the last remaining pieces" of the puzzle. | "one of the last remaining pieces of this big puzzle" |
| R-083 | T2 L138 | Feed the QMA and Mini Apps transcripts before deciding; they clarify intent. | "I give you the transcript. For QMA and mini apps" |
| R-084 | T2 L140 | Transcripts are huge; use external/sub agents to process them. | "these transcripts are very big. You might need external agents" |
| R-085 | T2 L183 | Build the SDK fully (operator complains it stopped midway). | "I gave you a task to build the SDK, and you did stop midway" |
| R-086 | T2 L668 | Study mature SDKs (LangGraph, LangChain, Mastra, Vercel) by default before deep work. | "before you start doing a lot of deep work, you look at what these guys did" |
| R-087 | T2 L668 | RULING-grade: opt out of bespoke QMA engine; use an existing mature SDK. | "I think we are going to use... an external SDK" |
| R-088 | T2 L668 | Candidate stack: LangChain (company) + LangGraph + LangMem integrated "in-house"; LangChain best out-of-box. | "I think LangChain would be the best for this" |
| R-089 | T2 L668 | Do a cost-benefit analysis of the SDK switch. | "cost benefit analysis for that" |
| R-090 | T2 L668 | Context7 + SDK agent guides would have let agents build QMA quickly. | "if I just gave you... um... context seven" |
| R-091 | T2 L708 | Scratch-built QMF/QML made sense; scratch-built agentic system does not (traces, permissions, memory). | "the agentic system, you know, building it from scratch is going to take time" |
| R-092 | T2 L821 | Explain LangChain, LangMem, Deep Agents, LangGraph; LangGraph depth "can bite you" if misused. | "if you use it poorly, it can bite you" |
| R-093 | T2 L971 | Look at Claude Agent SDK for dynamic workflows ("more like prompts"). | "if you look at Claude agent SDK, you can see how dynamic workflows are" |
| R-094 | T2 L971 | Prefer third-party components over building from scratch generally. | "I don't see the point of like, trying so hard to create everything from scratch" |

### 1F. Agent behaviour: permissions, unattended/remote runs

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-100 | T2 L668 | Most agents should NOT be permission-based (Claude UI struggled with permissions). | "I would prefer for these agents not to be permission-based, most of them" |
| R-101 | T2 L668 | Agent on a server runs a ~60-hour job with laptop off, without asking for permissions. | "if I left it a job that's going to take around sixty hours ... Why would it be asking" |
| R-102 | T2 L668 | Define when and how agents may ask — not "every now and then". | "We need to know when and how" |
| R-103 | T2 L668 | Model permission handling on open source: Codex (open source), Grok Build, maybe Claude Code. | "How does Codex handle permissions? Uh, I think it's open-source" |
| R-104 | T2 L903 | Agents run in a server/cloud, self-manage a scoped long-running task. | "agents to be able to work in a server or in a cloud ... they manage themselves" |
| R-105 | T2 L629 | Providers, CLI proxy running on a server somewhere, remote execution part of integration. | "we also have providers, CLI proxy, um working in server somewhere" |

### 1G. Agents, sub-agents, workflows, Deep Agents

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-110 | T2 L629 | Copilots of different types (described "yesterday"), agency, workflows must all integrate with QMA. | "I told you about the co-pilots, the different types" |
| R-111 | T2 L670 | Agents update things, call APIs, use tools and MCP apps (MCP Apps meant to be deeply integrated). | "MCP protocol has something called MCP apps" |
| R-112 | T2 L670 | Aurelius/Codex scope = core of agents; Copilot<->mini-app integration = Claude's job. | "how does the Copilot integrate together with... um... mini apps, that I think will be Claude's job" |
| R-113 | T2 L903 | Every agent node in a workflow defaults to a Deep Agent (sub-agents, skills, config built in). | "everywhere there is an agent node, in quotes, actually... uh is a deep agent" |
| R-114 | T2 L903 | Node-based editor: user builds a mini app that has an agent node in between. | "if I'm perhaps in a Node-based editor, I'm creating a mini app that... requires, um, an agent" |
| R-115 | T2 L971 | Copilot sub-agents and dynamic workflows required. | "I'm looking at copilot sub-agents. Um, what if we want dynamic workflows?" |
| R-116 | T2 L971 | Workflow kinds unbounded: research, cron-scheduled, custom-tool, etc. | "I want to create one that runs on cron jobs ... the sky is the limit" |
| R-117 | T2 L971 | Node editor needs connections between agents/workflows. | "The node-based editor might need it ... might be connections" |
| R-118 | T2 L971 | Copilot must be able to create agents, sub-agents, dedicated agents, dedicated workflow agents. | "how does now uh, the Copilot create agents or create sub agents" |
| R-119 | T2 L971 | Different agents in parallel need different tools and skills per agent (LangChain/LangGraph per-agent). | "three agents are handling... some very different things ... they need different tools" |
| R-120 | T2 L971 | External tools (Firecrawl, MCPs) available to agents. | "Firecrawl, like external tools, MCPs" |
| R-121 | T2 L971 | Copilots should leverage Hermes-style architecture; copilots are "tricky" given the UI. | "I would prefer actually, that copilots to kind of, leverage this" |

### 1H. MINI APP definition (operator's words, both threads)

| ID | Src | Requirement / definition | Quote |
|---|---|---|---|
| R-130 | T2 L971 | A mini-app agent IS basically a workflow. | "a mini app agent is basically a workflow" |
| R-131 | T2 L903 | Mini apps are built in a node-based editor; agent nodes inside are Deep Agents. | (see R-113/R-114) |
| R-132 | T1 L1233 | Mini apps have their own databases/storage and ingestion in/out. | "Creating of databases for mini apps" |
| R-133 | T1 L129 | Operator's first mini app pairs with "my own copilot". | "my first mini app myself, you know, my own copilot" |
| R-134 | T2 L1309 | A DeepSeek harness ("Cortex") is the reference for mini apps (garbled; see open threads). | "the DeepSeek harness, which is a Cortex ... that one is for the mini apps" |
| R-135 | T2 L1362 | Mini Apps transcript must lead the review — it sets the complexity level; not starting from zero. | "the one for mini apps. It will give you the level of complexity" |
| R-136 | T2 L821 | Mini-app daemon was redone/enhanced recently; don't rebuild it from repeated requests. | "redoing the mini apps Demyon ... Enhancements of the Demyon" |
| R-137 | T2 L903 | Tool rendering and agent behaviour have UI-side intentions (Claude ahead); backend must match them. | "we have, uh, a few ideas for how tools should render, how agents should work" |
| Note | T1 L1291 | Aurelius (claim): docs place mini-app construction in Epics 53-59, packs/permissions 60-65; shared daemon storage, not per-app DBs. Conflicts with R-025/R-132 literal wording. | — |

### 1I. MEMORY (long discussion, T2 L903-L1148)

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-150 | T2 L903 | Memory is tricky; must be considered from every angle. | "memory is very tricky, because now memory, you have to look at almost every angle" |
| R-151 | T2 L903 | Memory scopes to cover: per workflow, per task, per copilot session, overall Copilot. | "per workflow, or per task, per copilot session, or overall in Copilot" |
| R-152 | T2 L971 | Don't build memory ourselves — compare existing third-party memory. | "Instead of us bothering, We can compare existing things" |
| R-153 | T2 L971 | LangMem is a good example but evaluate others (Hindsight, newer providers). | "Lang Mem is a good example, but I think, memory... might require ... hindsight" |
| R-154 | T2 L971 | Study Hermes Agent's memory providers (pluggable memory) as reference. | "If you look at the Hermes agent, it has a few memory providers" |
| R-155 | T2 L971 | Navigate Hermes website, find memory section, list integrable providers. | "go to the website, the Hermes Agent, look for memory, the memory providers" |
| R-156 | T2 L971 | Hermes architecture is clean; mine its docs broadly, not only for memory. | "their architecture is so clean and clear, it's not even funny" |
| Note | T2 L1045-1148 | Aurelius findings (claims): Hermes docs list Hindsight, Mem0 + others; one external provider at a time beside built-in memory files. Hindsight LangGraph adapter has deletion/namespace-listing limits. Recommendation: LangMem extraction + QMA-controlled scope/admission/durable records; Hindsight optional; persistent specialists with fresh child contexts; explicit (not silent) promotion of knowledge to specialist/global Copilot. Current code claim: QMA scoped persistent memory; LangMem optional, live consolidation unproven. | — |

### 1J. Inference providers / subscriptions

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-170 | T2 L380 | OpenRouter acceptable as test provider instead of Codex subscription. | "Can I give you maybe open router, and you test with that" |
| R-171 | T2 L460 | Test BOTH OpenRouter and Codex subscription paths. | "you can test both actually, that would be cool" |
| R-172 | T2 L710 | Inference provisioning is the hard part with mature SDKs: Claude subscription and CLI proxy wiring. | "using a Claude subscription or using... um... the CLI proxy, we need to know how" |
| R-173 | T2 L903 | Does subscription / CLI proxy work properly? Is the API key route still viable? | "How did you handle the subscriptions, uh, the CLI proxy, does it work properly?" |

### 1K. UI (scope boundary only)

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-180 | T1 L228 | Operator wants to inspect the UI himself (hadn't looked yet). | "I haven't looked at the UI at all. So I want to see how it came out" |
| R-181 | T1 L336 | Claude pulls up and fixes the UI; component library has many issues. | "the components, component library, we are meant to have. A lot of issues" |
| R-182 | T1 L1200 | Claude's UI had ~7 demo apps; stopped for inconsistency; Claude can finish UI. | "It had like seven demo apps" |
| R-183 | T2 L530 | UI is getting a full rewrite; Claude does the backend wiring of the UI. | "the UI is going to have a bloody rewrite ... Claude will do the wiring of the backend" |
| R-184 | T2 L903 | Aurelius should look at committed UI + screenshots + Claude UI transcript for intent, not build UI. | "you look at the screenshots, you get the intention behind that" |

### 1L. Process / delegation / tooling rules

| ID | Src | Requirement | Quote |
|---|---|---|---|
| R-200 | T1 L336 | Codex runs repair packets in goal mode as fast as possible. | "we shall have goal mod, Codex to really, you know, run through them" |
| R-201 | T1 L336 | Parallel lanes: Codex = backend packets, Claude = UI. | "while Codex is running the packets ... I'll have Claude pull- up the user interface" |
| R-202 | T1 L363 | Work for local Codex must be broken down into steps. | "When I open Codex locally, I would like it to be broken down" |
| R-203 | T1 L1558 | Establish when to edit code and when not; centralized coordination of fixes. | "we need a centralized way" |
| R-204 | T1 L1617 | Blast radius must not be ignored: interconnected libraries; worktrees alone insufficient. | "the blast radius, should not be, um, ignored" |
| R-205 | T1 L1617 | Central ledger / issue tracker with triage; agents pick up issues; occasional supervisor. | "should we call it a ledger or an issue tracker?" |
| R-206 | T1 L1617 | Reference: "Finder skill from multiple cork" (likely Wayfinder; garbled). | "something like the way Finder skill from multiple cork" |
| R-207 | T1 L1655/1711 | Review the ENTIRE call, not just latest replies; produce a cleaner consolidated version. | "you might miss a few things if you just work based off- the latter responses" |
| R-208 | T2 L530 | Use multiple focused sessions; avoid one session per many tasks (context compaction degrades). | "when... Agents... their context window compacts ... performance will degrade" |
| R-209 | T2 L1105 | Aurelius acts as orchestrator/assistant: invoke BMAD skills, answer them in operator's place ("fill the shoes"). | "can't you act as if you are a human and then you respond to those skills?" |
| R-210 | T2 L1105 | Skills to use: BMAD architect, brainstorming, party mode, CIS, TDD, UX, BMAD build; study BMAD v6 site. | "you can use BMod architect, BMod brainstorming, you can use party mode" |
| R-211 | T2 L1105 | Use documentation-factory skill to update docs. | "we have another skill called documentation factory" |
| R-212 | T2 L1105 | Brain dump -> processed across multiple sessions. | "process it in another using rather multiple sessions" |
| R-213 | T2 L1186 | Overnight: don't stall on unnecessary pauses; worktrees/branches = no damage, so proceed. | "you are not doing damage. Okay?" |
| R-214 | T2 L1186 | Correction: it is BMAD *architecture*, not BMAD workflows; read BMAD itself first (link given). | "it's not BMod workflow ... It's BMod architecture" |
| R-215 | T2 L1309 | Explore websites in a real browser, clicking around like a human; web search is insufficient. | "You need to, click around, okay, look at it like a human" |
| R-216 | T2 L1309 | Keep tracking documents for the overnight work. | "I don't know if you can create documents to keep track, I would prefer that" |
| R-217 | T2 L1309 | References to study: Hermes, getbb.app, DeepSeek harness ("Cortex") for mini apps. | "get BB, the DeepSeek harness, which is a Cortex" |
| R-218 | T2 L1309 | Everything said is a SEED / vision, not a literal checklist. | "Most of what I've said, in this call is a seed" |
| R-219 | T2 L1309 | Codex budget: 60% usage left, judged enough for a working QMX. | "we are left with sixty percent usage on uh, Codex" |
| R-220 | T2 L1362 | Build forward from existing work, not from zero. | "you already know you're not starting from zero" |
| R-221 | T2 L821 | Give operator clarity on what is being done; repeated requests are checks, not rebuild orders. | "I lack a little bit of clarity, in what you're actually doing" |
| R-222 | T2 L821 | Provide Claude UI session transcript to Aurelius to align contracts. | "I should give you... um... the transcript from the Claude UI session" |
| R-223 | T1 L1452 | Aurelius must give its own technical CTO view, not just agree. | "I want you to be a little bit more technical than that ... the CTO version" |

---

## 2. Operator rulings (binding)

| ID | Src | Ruling |
|---|---|---|
| OR-01 | T1 L1233-1259 | Backend correctness first, proven at runtime without the UI; release/packaging after. Replaces "release first". |
| OR-02 | T1 L1303 | Keep and stitch existing code; do not rewrite wholesale; classify works/broken/unconnected/unverified. |
| OR-03 | T1 L1514/1555 | Adopt Aurelius's "bounded runtime acceptance runner" method, parallel isolated lanes. "your take is good. Alright, go for it" |
| OR-04 | T1 L1558 | Week-long paper soak runs in background on pinned version; doesn't block UI/release. |
| OR-05 | T1 L1617 | Fixes coordinated through one triaged issue tracker that accounts for blast radius. |
| OR-06 | T2 L530/555 | Claude owns UI wiring to backend; Aurelius/Codex own backend + agent core; Copilot<->mini-app integration = Claude. |
| OR-07 | T2 L590/605 | Make platform work FIRST; global backend dead-code audit + refactor deferred until then (but required). |
| OR-08 | T2 L668/710/724 | Stop bespoke QMA agent engine; adopt a mature SDK (LangChain/LangGraph family favoured; Mastra/Vercel compared). |
| OR-09 | T2 L668 | Most agents not permission-based; unattended long jobs run without repeated approval prompts. |
| OR-10 | T2 L903 | Workflow agent nodes default to Deep Agents. |
| OR-11 | T2 L971 | Memory: adopt/compare third-party providers (Hermes-style pluggable); don't build from scratch. |
| OR-12 | T2 L460 | Test both OpenRouter and Codex subscription provider paths. |
| OR-13 | T2 L1186 | Overnight authority: routine engineering decisions in isolated worktrees/branches without stopping to ask. |
| OR-14 | T2 L1186 | BMAD = architecture skill use (not "BMAD workflow"); read BMAD docs first. |
| OR-15 | T2 L1309 | Call content is seed/vision; research sites by browsing, not web search; keep tracking docs. |
| OR-16 | T2 L1362 | Mini Apps transcript leads; build forward on existing code. |
| OR-17 | T1 L856 | QMX stays private (stated in personal context; applies to QMX distribution). |

---

## 3. Aurelius commitments made on the calls (claims, unverified)

| ID | Src | Commitment |
|---|---|---|
| AC-01 | T1 L58/86 | Eleven repair packets (not eleven defects) for Codex; separate review pass. |
| AC-02 | T1 L184-202 | Target a complete Windows release; GitHub Releases first; mini-app/workflow/copilot as acceptance checks. |
| AC-03 | T1 L322 | Flagged: ratified UI is browser client, trading node on Ubuntu — Windows installer needs a where-services-run decision. |
| AC-04 | T1 L378-401 | Day split into 4 blocks; paste-ready Codex/Claude instructions in separate worktrees with checkpoints. |
| AC-05 | T1 L1176-1186 | Three audit journeys: agent-assisted research, QML strategy + QMB backtest, one-node paper execution. Claimed gaps in Windows research saving + saved-analysis execution. |
| AC-06 | T1 L1182 | Confirm whether Codex Review is configured. |
| AC-07 | T1 L1217 | Stability criteria: backend starts installed; APIs real + honest failures; records survive retry/restart; traceable results. |
| AC-08 | T1 L1267 | Trace mini-app transition through BMAD epics/docs; check Codex saved work against it. |
| AC-09 | T1 L1333 | Four-state classification: working / broken / implemented-but-unconnected / unverified. |
| AC-10 | T1 L1337 | Credentials via protected secret config, never pasted in chat. |
| AC-11 | T1 L1467-1479 | Build bounded runtime acceptance runner: deterministic dataset + test strategy; independently computed expected economics vs output + persisted ledger; same job via mini-app API must match; restart/retry no loss/duplication. Run by script/CI, not agent. |
| AC-12 | T1 L1527-1542 | Four parallel lanes (QML, QMB, storage+API, workflow+research), each own DB/workspace/ports/output; freeze one checkpoint. |
| AC-13 | T1 L1585 | Edit rule: no product edits during baseline; one owner per defect on branch; independent review; one integration owner; rerun checks. |
| AC-14 | T1 L1587 | Add Python and ML execution to acceptance map (docs decide scope). |
| AC-15 | T1 L1632-1640 | Issue tracker records failure, change, affected contracts/consumers, deps, checks; supervisor assigns; shared-contract changes ordered. |
| AC-16 | T1 L1680/1724 | Consolidated execution brief in chat, checked against whole call. |
| AC-17 | T2 L73 | Read-only local Codex audit of QMA vs design (execution, tools, memory, subagents, Mini Apps). |
| AC-18 | T2 L257/339 | Fix 7 older test failures; finish missing SDK connections; prove real requests, saved results, recovery; usable candidate Sunday night. |
| AC-19 | T2 L502 | Dead code: delete confirmed obsolete (Git keeps history), trace entry points/imports/plugins first; no commented-out blocks. |
| AC-20 | T2 L557 | Split backend work into focused sessions with written handoffs. |
| AC-21 | T2 L695/736 | Compare LangChain/LangGraph, Mastra, Vercel vs requirements + migration effort; recommendation + integration plan incl. subscription/CLIProxy wiring; bespoke runtime paused. |
| AC-22 | T2 L697 | 60-hour job: tools/data/limits granted at launch; continues with laptop off; pauses only on defined exception. |
| AC-23 | T2 L928-936 | Evaluate full Deep Agents for agent nodes; layered memory; inspect Claude transcript/UI read-only; morning handoff measured in journeys not %. |
| AC-24 | T2 L998 | Study Hermes docs + memory integrations, Claude Agent SDK, Deep Agents; apply architecture skills. |
| AC-25 | T2 L1133 | Act on recorded decisions; mark assumptions; never fabricate "Mubarak approved this". |
| AC-26 | T2 L1337/1390 | Review whole call, browse sites, document keep/change/test/open; results + gaps in the morning. |

Aurelius status claims worth re-verifying (not evidence): >5000 tests passing (T1 L52); daemon startup failure, substitute-bot passes, missing backtest ledger record (T1 L54); Friday 3 repairs (research saving, uploaded-artifact persistence, position recovery), 62 checks + 15 recipes (T2 L32); "integrated SDK" w/ 134 focused tests (T2 L337); LangChain loop + LangGraph finite research workflow w/ checkpoints into QMA journal; Deep Agents only skills + file-read middleware; Copilot profiles global/app/page contexts (T2 L848-869); ingestion/model paths still use refusing/test-only transports (T1 L1490); dashboard-reading monitor agent deferred (T1 L1490); OpenRouter previously explicitly restricted in code (T2 L395); LangSmith not confirmed configured (T2 L934/947).

---

## 4. Operator frustrations / corrections

| ID | Src | Frustration / correction |
|---|---|---|
| F-01 | T1 L72 | Suspects earlier QMF/QMB/QMA problems were never fixed, just turned into false positives. |
| F-02 | T1 L228 | Hasn't read Aurelius's documents; wants spoken simple breakdown, not text walls. |
| F-03 | T1 L1200 | Corrects Aurelius: UI is not the worry; backend/DB/API and Codex's work are. |
| F-04 | T1 L1233 | Corrects release-first plan: "finishing a whole release ... not the right way". |
| F-05 | T1 L1303 | Skeptical of Codex's ~19 hours of work; thinks Grok's mistakes weren't that big. |
| F-06 | T1 L1452 | "moving in circles"; Aurelius "just agreeing with me a lot"; demands real CTO take. |
| F-07 | T1 L1617 | Aurelius's fix plan ignored blast radius ("Doesn't add up to me"). |
| F-08 | T2 L19/1158 | Slow to pick up calls (minor). |
| F-09 | T2 L138 | Aurelius and Codex are "slowing us down" vs Claude finishing UI. |
| F-10 | T2 L183 | SDK build stopped midway without reason. |
| F-11 | T2 L185-199 | Confused why issues persist after Friday "working backend"; "walking in circles". |
| F-12 | T2 L281 | "getting a bit frustrated"; wants it done before Monday. |
| F-13 | T2 L530 | Aurelius tends to use one session for many tasks; compaction degrades. |
| F-14 | T2 L590 | Corrects Aurelius: global audit happens AFTER platform works, not now. |
| F-15 | T2 L668 | Building QMA from scratch "completely now useless ... just a little bit of pride". |
| F-16 | T2 L821 | Lacks clarity on what Aurelius actually does; repeated requests cause rebuild loops. |
| F-17 | T2 L1186 | "not BMod workflow ... BMod architecture"; Aurelius jumped to work packets before reading BMAD. |
| F-18 | T2 L1230/1307 | Link was already in chat / on Aurelius's computer. |
| F-19 | T2 L1309 | Don't claim understanding from a web search or landing page; browse like a human. |

---

## 5. Open threads

| ID | Src | Open item |
|---|---|---|
| O-01 | T1 L322 | Windows installer vs Ubuntu trading node vs browser UI: where services run — undecided. |
| O-02 | T1 L1291 vs L1233 | Per-mini-app databases (operator words) vs shared daemon storage (docs per Aurelius) — reconcile. |
| O-03 | T1 L1337 | Which market/broker provider + adapter for paper; credential provisioning path (keys never in chat). |
| O-04 | T1 L1303/1490 | Monitoring agent for paper week: documented but deferred; whether required for first run. |
| O-05 | T1 L307 | TestSprite adoption — evaluated, not decided. |
| O-06 | T1 L1182 | Codex Review configuration unconfirmed. |
| O-07 | T1 L1617 | Tracker tool choice ("Finder skill from multiple cork" = Wayfinder?) unresolved. |
| O-08 | T2 L695 | Final SDK choice (LangChain/LangGraph vs Mastra vs Vercel) pending comparison. Memory note says LangGraph chosen 2026-10-04 — confirm. |
| O-09 | T2 L710/934 | Claude subscription + CLIProxy wiring under a mature SDK; live subscription run unproven. |
| O-10 | T2 L395/445 | OpenRouter restriction in code; spend cap for paid test not given. |
| O-11 | T2 L947/959 | Remote/overnight execution host for unattended agents — none established; laptop must stay on. |
| O-12 | T2 L1045-1148 | Memory provider pick (LangMem vs Hindsight vs Mem0 vs others) and scope/promotion rules. |
| O-13 | T2 L903/1011 | Deep Agents as default node agent: integration with QMA job records/recovery; cron triggers + node-editor connections not provided by Deep Agents. |
| O-14 | T2 L668/934 | Tracing: Langfuse (operator ask) vs LangSmith (operator belief) — neither confirmed configured. |
| O-15 | T2 L670 | MCP Apps integration status unknown. |
| O-16 | T2 L1309 | "DeepSeek harness, which is a Cortex" for mini apps — garbled; identify the actual reference. |
| O-17 | T2 L1081-1094 | getbb.app relevance (plugin model: panels, CLI, skills) — which QMX part it informs unstated. |
| O-18 | T2 L821/903 | Claude UI session transcript + committed UI to be handed to backend agent for contracts. |
| O-19 | T2 L862/880 | Resume-without-repeating-external-action (replay protection) for LangGraph checkpoints — in progress. |
| O-20 | T2 L590 | Global dead-code audit + refactor skills: deferred, not dropped. |
| O-21 | T1 L1591 | Shipping a labelled "paper-use candidate" during the soak vs claiming soak passed. |
| O-22 | T2 L1105 | BMAD skills for overnight orchestration conflict with project rule that BMAD is planning-only and bmad-build is barred (CLAUDE.md) — reconcile. |
