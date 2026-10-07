# Aurelius chat transcript: requirements ledger

Source: `raw/chat/Aurelius-room-transcript.txt` (432 messages, 2026-09-30 to 2026-10-06; 119 operator, 313 Aurelius). Read in full.
Operator = Mubarak ("user"). Aurelius = ChatGPT agent ("aeon"). M### = message number. Dates are UTC `sent_at`.
Personal, education, career and health content (M65-68, M75-78, M119-124 disk partition, M394 Google Cloud) is left out on purpose.
Aurelius's claims are recorded as claims. **Nothing here proves that anything was built.**

**Critical caveat:** several binding instructions were given on **phone calls that are not in this transcript**. Those calls were on 10-01 (M64), 10-02 morning (M97, M136, M157), about 10-03 to 10-04 (M197 "reviewed the whole call") and 10-04 afternoon (M291-306). The operator says the Deep Agents, Hermes/memory and Copilot directives were given "on the call" or "Saturday/Sunday". Treat the call recordings as a required second source (see Open threads OT-01).

Dictation artefacts: "meaning app" / "many apps" / "MiniOps" = **mini app**. "QRM-A" / "QMM" / "KNA" / "Curium Edge" = probably **QMA** (agent layer). "Langraf" = LangGraph. "Kascope node" = Dukascopy node. "Hummus/Harmest agent" = Hermes Agent. "Clone/Claudie" = Claude. "codecs" = Codex. "cortex/corti" = **Cortis** (spelling confirmed M255). "test decay" = test SDK. "Elias/Arulius/earliest" = Aurelius.

---

## 1. Operator requirements ledger

Status column: **Active** = never withdrawn. **Changed** = later amended (see note). **Withdrawn/Deferred** = operator pulled it back. **Parked** = operator said backlog it, don't build now.

### 1A. Agents / QMA / LangChain / LangGraph / Deep Agents

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| AG-01 | 10-01 | QMA agents must exist in two contexts: Copilot agents, and agents inside the node-based editor (with sub-agents) | "agents in node best editor we also had forgotten about that sub-agents" (M88) | Active |
| AG-02 | 10-01 | Restore the agent "departments": quant traders, quant researchers, quant analysts (from the first QMA version, before mini apps) | "quant traders, quant researchers, quant analysts, remember the old version" (M88) | Active |
| AG-03 | 10-01 | Agents need MCP access | "MCPs like the the agents themselves" (M88) | Active |
| AG-04 | 10-02 | Test QMA live: web access, memory, MCPs, ledgers, sub-agents, real model calls | "do the agents actually access the web, memory, MCPs" (M127) | Active (never done live; M413, M420) |
| AG-05 | 10-02 | Test module calls, sub-agents and sub-agent routing | "actual module calls, sub-agents, sub-agent routing" (M129) | Active |
| AG-06 | 10-02 | Agents need actual data; test real ingestion | "agents need actual data... we were meant to test out actual ingestion" (M131) | Active |
| AG-07 | 10-02 | First big addition after testing: ship the agent system. Then refined: QMA+mini-apps is a *finding* to refactor or reshape, not next in line | "we shall ship the agent" (M134); "it doesn't mean that it's the next in line" (M136) | Changed (M136) |
| AG-08 | 10-02 | QMA design session using the two long transcripts (original agents; mini apps) and the Wayfinder skill | "we'll use the Wayfinder skill... Both transcripts" (M165) | Active (partly done M175-183) |
| AG-09 | 10-03 | Three agent problems to solve: (1) inference provider, (2) types of agents, (3) harnesses | "problem number one would be inference provider... two... types of agents... three... harnesses" (M171) | Active |
| AG-10 | 10-03 | Long-running research/workflow agents need remote execution (Amp orbs, VPS, Modal considered) | "these agents will take a long time to actually do anything" (M171) | Active / Open |
| AG-11 | 10-03 | Skills and hooks for agents "down the road" | "we're also meant to provide skills and hooks for these agents" (M171) | Active (reaffirmed M247) |
| AG-12 | 10-03 | Harness must work with Claude Opus and Fable models (Claude Code instance / Claude Agent SDK) | "as long as I'm in Opus or I'm in Fable, the harness has to adopt" (M171) | Active |
| AG-13 | 10-03 | Compile ONE SDK from the transcripts, brain dump, CLI proxy and remote-location ideas. Use agents to explore multiple designs | "Can we compile one SDK, please?" (M184) | Changed: became the LangChain/LangGraph port (M197, M207) |
| AG-14 | 10-03 | Mini apps were meant to be adaptable to the agents. Bring workflows and agency into mini apps | "the mini apps thing was meant to be adaptable to the agents" (M184) | Active (but see MA-01 for the later definition) |
| AG-15 | 10-03 | Write working code, not just a proposal: accept requests, bring in subscriptions via the CLI proxy. Don't merge | "code something that can work, accept requests, allow me to... bring in my subscriptions" (M187) | Active |
| AG-16 | 10-04 | Adopt the LangChain ecosystem (LangChain + LangGraph) | "which indicated we choose long chain, I believe, right" (M207) | Active (ruling R-04) |
| AG-17 | 10-04 | Modularize everything: memory, providers, workflows and profiles each as separate modules | "modularizing everything might be the best case" (M203) | Active |
| AG-18 | 10-04 | Memory via LangChain LangMem was considered | "Langchain has lang mem" (M209) | Changed: Hermes-style pluggable providers (M306) |
| AG-19 | 10-04 | Agents must read real docs (Context7), not assume. This is an SDK, not just Python | "tell the agents to use proper documentation... If you have context seven, use it" (M209) | Active |
| AG-20 | 10-04 | Decide whether the transcript ideas transfer to LangChain or need our own code | "are they transferable to Langchain or do we need to integrate our own?" (M209) | Open |
| AG-21 | 10-04 | Skills and hooks: copy how LangChain/LangGraph do it (blogs, posts). Don't invent | "Please don't try to invent anything. I will echo this many times" (M251) | Active |
| AG-22 | 10-04 | Research the "folder as an agent" pattern (popularized by Vercel, not invented there) | "a folder as an agent... Vercel actually did it" (M251) | Active / Open |
| AG-23 | 10-04 | Hooks: Claude Agent SDK has the best hook model; use it as the reference | "Claude Agent SDK has the best hooks" (M251) | Active |
| AG-24 | 10-04 | The transcripts are the vision for the agent: memory, skills, hooks, mental models. Plugins may be left out. Cortis and UI-specific ideas stay out | "memory, skills, hooks, I gave ideas... Mental models were there" (M253) | Active |
| AG-25 | 10-04 | Requirements baseline = both transcripts + the 10-03 QMA brain dump (M171) + call clarifications | "transcript and yesterday's brain dump about the agentic system" (M255) | Active |
| AG-26 | 10-04 | Agents must adjust to the mini-app model. Explain how they come in | "agents have to... adjust to the new installation of Mini Apps" (M291) | Active / Open |
| AG-27 | 10-04 | Explain the architecture: where LangGraph prebuilt agents are used vs plain LangChain agents, and how LangGraph is used (call requested) | "LangGraph has lip agents. Where are they being used" (M291) | Open (never answered) |
| AG-28 | 10-06 | **Workflows in QMX use Deep Agents** (packaged), so agents aren't hand-built each time. The operator says he said this "vividly", likely on a call | "let the workflows that are in QMX use Deep Agents" (M432); "talking about using deep agents in workflows" (M417) | Active (ruling R-05). Aurelius delivered only an "optional, restricted" Deep Agents integration (M420) |
| AG-29 | 10-06 | Test agent-led journeys beyond QMB, e.g. hypothesis → strategy | "Have you tried an agent that perhaps turns... a hypothesis into a strategy?" (M412) | Active |

### 1B. Memory / pluggable memory / Hermes

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| ME-01 | 10-02 | Agentic memory provider, e.g. Hindsight or Alibaba's memory | "use Hindsight or Alibaba's memory, something like that, agentic memory" (M127) | Changed (ME-04) |
| ME-02 | 10-02 | Memory scopes differ: mini-app/workflow agent memory vs Copilot memory. Possibly a new feature | "For many apps and workflows, agent memory is different... Then for Copilot, it's also different" (M127) | Active |
| ME-03 | 10-03 | (From the transcripts, per Aurelius M182-183) memory is a core service with replaceable providers, plus per-invocation context assembly | (Aurelius summary M182-183) | Active (needs source check) |
| ME-04 | 10-04 | **Memory = Hermes Agent pattern: pluggable memory providers and configurations.** Operator reserved the right to pick the provider | "use the Hummus agent setup, so pluggable memory providers and configurations" (M306); "I give you the memory provider of my choice" (M300) | Active (ruling R-06). Provider choice open |
| ME-05 | 10-04 | Aurelius must actually browse the Hermes docs itself | "I still haven't seen you navigate to that website" (M306) | Complaint: not done properly (M422) |
| ME-06 | 10-06 | Memory got "an hour or two" of call time and was never reported back | "Memory itself, which is something we spent literally an hour or two on, you didn't talk about it" (M432) | Complaint / Open |

Reference: Hermes docs https://hermes-agent.nousresearch.com/docs (M294). Aurelius claims it read Architecture → Programmatic Integration → Memory Providers (M307).

### 1C. Mini apps (operator's own definition)

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| MA-01 | 10-06 | **Definition: a mini app is NOT a combination of workflows.** It *can* combine workflows, but usually doesn't. **Most of the time mini apps contain no agents** | "A meaning app is not a combination of workflows. It can be... However, it isn't... Most times, actually, there won't be agents in meaning apps." (M432) | Active (ruling R-01). Final word |
| MA-02 | 10-06 | (Earlier, superseded) workflows came first and were combined to form mini apps. "No mini apps without workflows" | "There are no mini apps without workflows... we combine workflows to form mini apps" (M417) | **Contradicted by M432** (operator says he "was actually testing"). Use M432 |
| MA-03 | 10-01 | The point of the platform: a core strong enough to build mini apps on | "build a platform strong enough for us to build mini-apps on top of" (M79) | Active |
| MA-04 | 10-01 | Need 3 test mini apps / journeys: something that tests agents inside workflows, something that tests QMB, something that tests QML (WF1, WF2) | "we need, like, three. I think WF1, WF2" (M92) | Changed (MA-08) |
| MA-05 | 10-01 | Pipeline journey: hypothesis → research → coding → paper trading → promotion to live | "from hypothesis to research, to literally coding, pepper trading, then promotion to live" (M92) | Active |
| MA-06 | 10-01 | Mini-app and workflow templates should exist (thought they were designed) | "do we have templates for mini apps and workflows? Because I thought they were there" (M86) | Open (never verified) |
| MA-07 | 10-02 | Research journey = WF2 (Claude built a demo) | "for research, we were meant to do WF2" (M129) | Changed (MA-08) |
| MA-08 | 10-06 | WF1/WF2 are **test fixtures only, not product workflows**. The operator will create his own workflows through the Copilot | "the workflows, don't take them verbatim... I would like to create my own using the Copilot" (M414) | Active (ruling R-08) |
| MA-09 | 10-02 | Copilot must create apps, mini apps and workflows. How they render in the UI, and the app-creation process, are the concern | "the copilot being able to create apps, mini apps, workflows, how are they going to be rendered" (M149) | Parked (M150), then foundational per M417/M422 |
| MA-10 | 10-05 | Mini-app lifecycle through the Copilot: creation, maintenance, and DevOps for mini apps. Use the ideas near the end of the Claude transcript. Better than "just docker". Networking needs are "insane" | "how mini apps are to be handled by the copilot, interms of creation, maintenece and also dev ops... (not just docker)" (M350) | Active |
| MA-11 | 10-04 | Types of Copilots for the Mini Apps edition: what was or is the plan | "the types of copilots... for Mini Apps... I want to know what the plan was" (M291) | Open |
| MA-12 | 10-04 | Many items are "mini apps and ideas". Some are default QMX capabilities, not mini apps | "Some are not mini apps. Some are just things that QMX should be able to do by default" (M233) | Active |
| MA-13 | 10-06 | The complexity of the mini-app transcript should yield "insane amounts of features". Workflows must support high complexity | "the complexity of the mini app system should give you beyond insane amounts of features" (M422) | Active |

### 1D. Workflows

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| WF-01 | 10-06 | Workflows are foundational and came before mini apps | "we started with workflows before mini apps" (M417) | Active (but MA-01 governs the mini-app relationship) |
| WF-02 | 10-06 | Workflows use Deep Agents by default (= AG-28) | (M432) | Active |
| WF-03 | 10-06 | User-authored workflows via the Copilot, with thorough tests across task types | "make sure that we have thorough, like, testing added here" (M414) | Active |
| WF-04 | 10-02 | Test variants/experiments: multiple strategy variants via QMB | "experimenting using QMB... try out multiple variants" (M131) | Active (Aurelius claims a QMB Study, M153-154) |
| WF-05 | 10-02 | Test articles → research → hypothesis → structs (the `structs` folder), and ML | "articles, research, hypothesis, structs. Like there is a structs folder" (M131) | Active |

### 1E. Copilot

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| CP-01 | 10-01 | Copilot uses a CLI proxy for providers, so the operator's Codex and Claude subscriptions work | "we're actually going to have a CLI proxy in there for providers. I want to use my codecs and color subscriptions" (M86) | Active |
| CP-02 | 10-01 | Copilot needs skills | "we might also need skills for the co-pilot" (M86) | Active |
| CP-03 | 10-01 | Does QMX have its own agentic browser? | "does QMix have its own agentic browser?" (M88) | Open |
| CP-04 | 10-02 | Copilot skills, hooks and plugins: "a huge problem", backlog | "Skills, hooks, plugins for the copilot. That is going to become a huge problem" (M149) | Parked |
| CP-05 | 10-03 | Several Copilot kinds: copilot, normal copilot, application copilot. Each page's Copilot differs; sessions live in one place | "every co-pilot is different. Okay, sessions can be in one place" (M184) | Active |
| CP-06 | 10-06 | **The Copilot works like Codex or Claude Code** (a coding-agent harness). The operator says he said this multiple times on Saturday/Sunday | "I remember bloody telling you literally it is how Codex or Clone could work" (M422) | Active (ruling R-07) |
| CP-07 | 10-06 | The Copilot builds and manages the user's own workflows and mini apps | (M414, M422) | Active (Aurelius: current path only accepts restricted predefined sequences, M419) |

### 1F. Providers / inference / subscriptions

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| PR-01 | 10-01 | CLIProxyAPI (router-for-me/CLIProxyAPI) is the CLI proxy | "cli proxy [[[https://github.com/router-for-me/CLIProxyAPI]]]" (M88) | Active |
| PR-02 | 10-01 | CLI proxy is a provider in the Settings panel | "we can integrate it as a provider. I think it will be in the settings panel" (M92) | Active |
| PR-03 | 10-02 | Rewire the CLI proxy properly | "Maybe you can actually have it rewired properly with CLI proxy" (M127) | Active |
| PR-04 | 10-02 | Use OpenRouter credits (~$6) with cheap models for testing | "I have six dollars, so I think that is enough for testing" (M127) | Active |
| PR-05 | 10-03 | Multi-subscription use like T3 Code (Codex + Claude Code at once). Reverse-engineer T3 Code; don't copy its code | "I can use a codex subscription. I can also use a claude code subscription" (M171) | Active |
| PR-06 | 10-03 | The CLI proxy must serve external harnesses/agents not running on the laptop (Tailscale idea) | "The CLI proxy should be wired in such a way that it caters for the external... agents" (M171) | Active |
| PR-07 | 10-03 | Models: GPT 6.1 Sol = workhorse and sub-agents. Opus 5.5 = daily driver. Fable also supported | "GPT 6.1 sole mostly because it's a good workhorse... Opus... my daily driver" (M171) | Active |
| PR-08 | 10-03 | Claude subscription external-use risk: study how harnesses (pi, Claude Agent SDK, Claude Code instance) do it | "how are they able to use their subscriptions?" (M171) | Open |
| PR-09 | 10-04 | Remove the OpenRouter ban from QMX provider policy | "open router is not set in stone. Okay? Change it" (M207) | Active (Aurelius claims done M220) |
| PR-10 | 10-04 | Test models: free OpenRouter models first, then DeepSeek | "free* not three" (M244); "we are going to use deep-seq models" (M247) | Changed (no free DeepSeek route found; live test never run) |
| PR-11 | 10-04 | Operator offered a temporary API key for testing (to delete later) | "Should I give you an API key? Don't worry, I'll delete it later" (M235) | Open (never run) |

### 1G. Remote compute / networking / storage

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| NW-01 | 10-03 | Agents need both laptop-only resources and remote instance resources. Shared storage bucket (S3) | "I might make an S3 bucket... a storage bucket" (M171) | Active |
| NW-02 | 10-03 | Contabo VPS as centralized database/source for agents (old QMX "middle node" concept) | "use MyVPS as a centralized, should I say database?... It used to be called the middle node" (M171) | Active |
| NW-03 | 10-03 | Tailscale-style networking for off-machine agents | "we can do something like tail scale" (M171) | Open |
| NW-04 | 10-05 | Networking needs for mini apps are "insane"; build something efficient, not just Docker | "the networking needs here are insane too" (M350) | Active |
| NW-05 | 10-05 | Deploy to Contabo (Linux, SSH) and set up the S3 bucket (offered for "tomorrow") | "I would have given you my Contabo server and you set up SSH... Even my S3 bucket" (M377) | Open |

### 1H. Trading nodes / brokers / markets / data

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| TN-01 | 10-01 | Multiple trading nodes (not one) | "we're not going to have one singular trading node, we can have multiple" (M79) | Active |
| TN-02 | 10-01 | Ship incrementally: one working trading node first, duplication/multi-node later | "we can ship data as long as a trading node works, duplication is there" (M82) | Active (sequencing) |
| TN-03 | 10-01 | Live-market / provider connection UI is needed (paper → live) | "connection to live markets or to providers... another part of the UI we might need to build" (M92) | Active |
| TN-04 | 10-02 | Historical data from the Dukascopy node (includes crypto). Integrate more data sources later. No local dataset | "we are going to use the Kascope node for now as a data source" (M149) | Active |
| TN-05 | 10-02 | Make up a test strategy (cTrader/MT5 style ok). Not for live trading | "make up your own. Seriously, like this is not one that is going to trade live" (M149) | Active |
| TN-06 | 10-02 | Set up trading nodes and servers (operator's VPS) via the UI | "We need to be able to set up trading nodes so servers also via the UI" (M149) | Parked (M150) |
| TN-07 | 10-04 | In-depth spot crypto pass: CCXT; borrow ideas from Hummingbot (open source) and wire them in | "We need an in-depth pass for crypto, spot crypto especially... CCTX... Hummingbot" (M230) | Active |
| TN-08 | 10-04 | Multiple trading nodes = multiple servers, DBs, connection, data and collection points, APIs, agent connection points | "multiple servers, multiple databases, multiple connection points" (M233) | Active |
| TN-09 | 10-04 | Multiple brokers and multiple accounts per broker, each account with its own risk/position-sizing system ("book system") | "if I have multiple accounts, I can use a book system on one... under risk management and position sizing" (M233) | Active |
| TN-10 | 10-04 | Spot FX alongside spot crypto | "So spot FX, actually I almost forgot about it" (M233) | Active |
| TN-11 | 10-04 | Add broker connections and accounts inside QMX. Open a browser if auth needs it. Handle secret keys | "If it needs me to open up a browser, make that available" (M233) | Active |
| TN-12 | 10-04 | "The lab": new idea, leave alone for now | "we have something called the lab now... leave that one alone" (M233) | Parked |

### 1I. Data / DB / API / DevOps / caching

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| DB-01 | 10-04 | A focused agent on data & database analytics, DevOps and API | "how do you propose we handle data and database analytics, DevOps, and API?" (M225) | Active |
| DB-02 | 10-04 | Full suite: data, analytics, logging, backend, API. How agents connect to the backend; cleaner architecture, maybe a daemon. Consider QML, QMF, trading node, mini apps; "blast radius enormous" | "how agents actually connect to our backend... maybe a daemon" (M230) | Active |
| DB-03 | 10-05 | DB, API and DevOps for mini apps, plus how they connect to agents | "consider all our previous additions, especially db, api and dev ops" (M350); (M327) | Active |
| DB-04 | 10-05 | Must work out of the box | "remember, this is meant to work out of the box" (M327) | Active |
| DB-05 | 10-06 | Evaluate Convex and TanStack (Svelte support) for stack simplification, by clicking through the sites directly | "Have a look at them in your browser... whether we might need some refactoring" (M395) | Changed: Convex left out, refactor held (M404) |
| DB-06 | 10-06 | Caching strategy (UI heavy; also mini apps, DB, APIs) | "How are we handling caching? Because we are going to need to cache a lot" (M395) | Active |
| DB-07 | 10-06 | Hold the broad refactor; leave Convex out "perhaps" | "I think we can hold on refactoring... let's leave Convex out, perhaps?" (M404) | Active (tentative) |
| DB-08 | 10-02 | Combine ML Studio, the backtesting engine and the node-based editor (from Claude's UI work). Microservices maybe | "we were thinking of combining the ML studio the back testing engine and the dot-based editor" (M155) | Parked (M157: don't work toward Claude's direction yet) |

### 1J. UI (Claude-owned)

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| UI-01 | 09-30 | No special models needed for UI since shadcn is used; Codex for everything | "since we are using shared in the UI, I don't think we need, like, specific models" (M32) | Changed: Claude took the UI (M44, M62) |
| UI-02 | 10-01 | Claude reviews and builds the UI (prompt requested) | "I need Claude to review my UI" (M44) | Active |
| UI-03 | 10-01 | Is Claude Design or a design system overkill? | (M59) | Resolved: strengthen the existing system (M61) |
| UI-04 | 10-01 | Finishing UI items with Claude goes on the backlog | "add that to the backlog for tomorrow" (M94) | Active |
| UI-05 | 10-03 | Aurelius must not touch the UI | "don't touch the UI yet, okay? Please" (M191) | Active |
| UI-06 | 10-04 | Claude hasn't started UI wiring; layouts still being thought through | "Claude hasn't started the UI wiring" (M273) | Info |
| UI-07 | 10-05 | Claude will connect UI to backend in the same session, with Aurelius's core update. Aurelius must not "connect dots" | "claude will still perhaps connect the ui to the backend, to prevent you from trying to connect dots" (M350) | Active |
| UI-08 | 10-06 | Backend must be finished first; Claude must not do most of the heavy lifting. Neither handoff was given to Claude | "I actually haven't given Claude anything... I want it to at least not be doing most of the heavy lifting" (M408) | Active |

### 1K. Quality / CI / review / cleanup

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| QA-01 | 10-01 | Questioned Codex-invented source manifest, release gates, build tooling, launcher.py and the 80% coverage metric | "what are you using to measure that metric" (M84) | Info / complaint |
| QA-02 | 10-01 | Need re-auditing, not just a blocker list. Codex Review on PRs | "we need actual auditing, re-auditing rather, regardless" (M92) | Active |
| QA-03 | 10-01 | Tests aren't the only thing | "I don't think tests are the only thing" (M88) | Active |
| QA-04 | 10-02 | Set up Codex Review; add checklist `C:\Users\Mubarak\Documents\brain\brain\Clippings\Code Review Checklist & Best Practices (3-Layer Model).md` to the Codex review rules (AGENTS.md) | "can you set up codex review for me?" (M140); "have this in the agents review file" (M142) | Deferred (M147); revisited (M306, M325) |
| QA-05 | 10-02 | Leave Codex Review out for now | "for codex review, let's leave it up for now. Let's leave it out" (M147) | Withdrawn temporarily |
| QA-06 | 10-01 | Wanted TestSprite for bug finding | "I wanted to use test sprite to find bugs" (M86) | Open |
| QA-07 | 10-04 | CI pipelines; clean up unmerged/irrelevant work and dead code | "we are meant to have CI pipelines... there is a lot of dead code" (M265) | Active |
| QA-08 | 10-04 | Industry-grade; no false positives; don't bulk-batch, chunk work | "industry grade, don't just get false positives... don't just bulk batch work" (M270) | Active |
| QA-09 | 10-04 | Remove replaced code; no commented-out leftovers. Cleanup audit after launch | "Remember to remove the unnecessary code... just comment it out" (M284) | Active |
| QA-10 | 10-04 | Codex/ChatGPT has built-in code review, so use it on PRs. Do own review and audit regardless | "it means we can have code review... You do your review regardless" (M306) | Active |
| QA-11 | 10-05 | PRs go through Codex review when work is done | "The PRs, I think code review can run when you're done" (M327) | Active |
| QA-12 | 10-04 | Draft documentation patches as work proceeds. Rethink how docs should look (LangChain docs pattern) | "documentation patches, drafts" (M235) | Active (never shown delivered) |

### 1L. Process / delegation / orchestration rules

| ID | Date | Requirement | Quote (M#) | Status |
|---|---|---|---|---|
| PX-01 | 09-30 | Never touch `integration`, `ui-integration` or `main`; other branches are free | "the only three branches you won't touch... integration, UR integration, and main" (M9) | Active |
| PX-02 | 09-30 | Agent must not sign in to GitHub (two authenticators). Considered a fine-grained token | (M13, M15) | Info |
| PX-03 | 09-30 | Use the Codex subscription "through and through" | "We might just use my Codex subscription through and through" (M32) | Changed: Claude added (M88, M108) |
| PX-04 | 10-01 | Codex models: GPT 6.1 Sol = audit/explore/review. GPT 6 Luna = workhorse. Main session = orchestrator only. Minimize tokens | "the main session should be an orchestrator" (M38) | Active |
| PX-05 | 10-01 | Only name the sub-agent models; don't over-script. Stop needless pauses | "Just tell it the models you want to use as sub-agents. That's all" (M48) | Active |
| PX-06 | 10-01 | Spending is fine "as long as it delivers" | "It can use any amount... as long as it delivers" (M75) | Active |
| PX-07 | 10-01 | Ship rocks before mountains (incremental milestones) | "trying to ship a whole mountain at once instead of before shipping rocks and boulders" (M82) | Active |
| PX-08 | 10-01 | Kanban flow: auditor files issues with evidence → workers pick up → fix on own branch → test → PR → fix until merged | "having an auditor create issues, then have agents pick them up" (M82) | Active |
| PX-09 | 10-01 | Prefer fresh sessions over repeatedly compacted ones | "I would prefer starting a fresh session to make sure that it has better context" (M82) | Active |
| PX-10 | 10-01 | Efficiency is a necessity | "efficiency is necessity here" (M84) | Active |
| PX-11 | 10-01 | No more "goal mode" open-ended runs. Codex overdoes things and ignores YAGNI | "I don't think a goal is the right one... They won't consider that you ain't gonna need it" (M88) | Active |
| PX-12 | 10-01 | Bring Claude Opus 5.5 in for backend too (efficiency, usage). Work tracking across the two tools | "Claude Opus 5.5 is more efficient... bring it in to also handle the back end" (M88) | Active |
| PX-13 | 10-01 | Target: the "first legacy release", a stable version first | "the legacy version... The first legacy release" (M92) | Active |
| PX-14 | 10-02 | Aurelius may start fresh sessions on any platform (Codex, Claude) and link or reread transcripts | "you can set a new session across all these platforms" (M106) | Active |
| PX-15 | 10-02 | Codex: cheap models (6.1 Sol / Luna). GPT 5.5 for intelligence. Astra is expensive. Claude: Opus 5.5 | "choose a model that is cheap, so like 6.1 sol or Luna" (M108) | Active |
| PX-16 | 10-02 | Yesterday's Codex work ran in the cloud and may be newer than laptop code | "Codex's code might be newer than the one on my machine" (M111) | Info |
| PX-17 | 10-02 | Wants a working thing; docs contain almost everything | "I just want a working thing... Almost everything you need is in the docs" (M117) | Active |
| PX-18 | 10-02 | **No new features during testing.** Park them in a ledger with a short description and connections that can "spark a session". Bounded fixes only | "new features, put them aside. You can put them as issues or have a ledger" (M136) | Active (ruling R-09) |
| PX-19 | 10-02 | Read `_bmad-output` / BMAD architecture, the `docwork` folder, `docs/` (the refined layer) and the Documentation Factory skill before declaring things missing | "BMAD architecture... Docwork folder... Docs is like the refined thing" (M136) | Active |
| PX-20 | 10-02 | The morning phone-call plan is the day's checkpoint | "That is still our checkpoint for today" (M136); (M157) | Active |
| PX-21 | 10-02 | Don't follow Claude's UI-driven backend direction yet. First make non-UI things work | "Don't work towards clothes given direction. First, make sure that other things not related to the UI actually function" (M157) | Active at the time |
| PX-22 | 10-02 | Don't leave verified fixes "isolated and unmerged" with nothing running. Keep going when permission was given | "why are you leaving it there if you are going to use it" (M155) | Complaint |
| PX-23 | 10-03 | Audit available skills first; use open-source repos as mental models | "get an agent to audit for you the skills" (M187) | Active |
| PX-24 | 10-03 | "I don't want to babysit you" | (M184, M265) | Active |
| PX-25 | 10-04 | GPT 6.1 Sol agents at HIGH thinking; medium isn't enough | "try to put them in high thinking mode, please. I've seen Medium is not sufficient" (M230) | Active |
| PX-26 | 10-04 | Retrieve Grok's backlog and "knock it off today" (may need BMAD architecture or skills, plugins) | "I want you to fast retrieve that list, and I want us to knock it off today" (M213) | Active |
| PX-27 | 10-04 | Pause broad verification while the agent core changes | "some sessions, I believe, should kind of pause" (M257) | Active then |
| PX-28 | 10-04 | CTO mandate: full backend freedom except UI requirements; many agents; thorough; no rush | "You are my CTO now, so put your CTO hat on" (M265) | Active (later revoked in effect, M432) |
| PX-29 | 10-04 | Simpler responses; diagrams and visualizations of the whole system | "use diagrams or visualizations" (M270); "dumb it down" (M134, M325) | Active |
| PX-30 | 10-04 | Overnight: at most 3 sessions, scope 1-2 agents, sequential, save usage. Keep a ledger. Git branches/worktrees per agent. Draft PRs | "keep the sessions active to a maximum of three... keep a ledger... create branches and create work trees" (M306) | Active |
| PX-31 | 10-04 | Don't get stuck on steps that need a human | "you step in as a human, don't get stuck" (M306) | Active |
| PX-32 | 10-05 | Code without waiting for permission once requirements are confirmed | "you should start coding right away. Okay? Don't wait for my permission" (M341); (M347, M361) | Active |
| PX-33 | 10-05 | Retrospective since Friday against calls, links, agent outputs and operator messages. The operator "seeds" ideas; they must grow | "most of the time I'm seeding" (M377); (M306 "seeds have to grow") | Active |
| PX-34 | 10-05 | Claude takes over system integration, QA and deployment after the backend | "Claude will ship everything, wrap it up, do a bit of... Q and A... even the deployment" (M377) | Active |
| PX-35 | 10-06 | Some tasks require Aurelius itself (browser), not a delegated agent | "I wanted you to handle it on your computer because some of this requires you, not an agent" (M398) | Active |
| PX-36 | 10-06 | **Relationship ended.** Operator returns to local agentic/agile coding with Codex and Claude. Wants a raw transcript plus a reconstruction of shipped vs claimed vs missed | "We are done. I'm going back to normal coding with local agents" (M432) | Final |
| PX-37 | 10-02 | Consider moving off GitHub (GitLab or cheaper), later | "can we change from GitHub to maybe something less paid, maybe GitLab" (M134) | Open/Parked |

---

## 2. Operator rulings / decisions that should bind future work

- **R-01 Mini-app definition (M432, final):** a mini app is not a combination of workflows. It may contain workflows but usually doesn't, and most mini apps contain **no agents**. This overrides the operator's own M417 "we combine workflows to form mini apps". Don't model mini apps as workflow bundles or agent containers by default.
- **R-02 Platform purpose (M79, M83):** a stable core that mini apps are built on. Ship one working trading node first; multi-node is a capability added after (M82).
- **R-03 Protected branches (M9):** never modify `main`, `integration` or `ui-integration`. Draft PRs only. `main` moves by operator action (this matches project CLAUDE.md).
- **R-04 Agent stack (M207):** LangChain ecosystem, with LangGraph for workflow state/recovery. Use mature SDK mechanisms; don't invent (M251, M253). Use Context7 / official docs (M209).
- **R-05 Deep Agents in workflows (M432, M417):** QMX workflows use Deep Agents (pre-packaged agents) by default, so agents aren't hand-built per workflow. An "optional, restricted" integration doesn't satisfy this.
- **R-06 Memory (M306):** Hermes-Agent-style **pluggable memory providers + configuration**. Provider choice is the operator's (M300). Memory scopes differ for Copilot vs mini-app/workflow agents (M127).
- **R-07 Copilot (M422):** behaves like Codex / Claude Code, a coding-agent-style harness that builds and manages the user's own workflows and mini apps (M414). There are multiple Copilot kinds, page-specific, with shared session storage (M184).
- **R-08 WF1/WF2 (M414):** test fixtures only. Product workflows are authored by the user via the Copilot.
- **R-09 No new features during stabilization (M136, M157):** park them in a ledger with description and connections. Bounded fixes only. Testing to find issues comes first.
- **R-10 Modularity (M203, M209):** memory, providers, workflows and profiles are separate modules.
- **R-11 Skills/hooks (M251):** follow LangChain/LangGraph published patterns. Hooks modeled on the Claude Agent SDK. Investigate "folder as an agent".
- **R-12 Providers (M171, M207, M92):** CLIProxyAPI as a Settings-panel provider. Multi-subscription (Codex + Claude) in the T3 Code style. OpenRouter allowed (ban removed). GPT 6.1 Sol = workhorse; Opus 5.5 = daily driver; Fable supported.
- **R-13 Trading scope (M233, M230):** multiple brokers, multiple accounts per broker, per-account risk/position-sizing systems; spot crypto (CCXT; Hummingbot ideas) and spot FX; broker onboarding in-app.
- **R-14 Data source (M149):** Dukascopy node for historical data now (includes crypto); more sources later.
- **R-15 Process (M82, M88, M306):** Kanban (auditor → issues → workers → PR → review → merge). No open-ended goal runs. Fresh sessions. At most 3 concurrent sessions, 1-2 preferred. Ledger + worktree per agent. YAGNI. Remove dead code, no commented-out leftovers (M284). Industry-grade, no false positives (M270).
- **R-16 Requirements baseline (M255, M253):** both long transcripts (agents, pre-mini-app; mini apps = "explorer node editor" zip) + the 10-03 brain dump (M171) + call clarifications. Exclude Cortis and UI-specific ideas from backend scope.
- **R-17 UI ownership (M191, M350, M408):** Claude owns UI and UI↔backend wiring. The backend must be finished first so Claude isn't doing the heavy lifting.
- **R-18 Stack (M404):** hold the broad refactor; leave Convex out for now. TanStack Query was Aurelius's recommendation for the UI data layer (not ratified by the operator).
- **R-19 Codex models (M38, M108, M230, M265):** GPT 6.1 Sol for exploration and review at HIGH thinking; GPT 6 Luna for implementation.

---

## 3. Aurelius promises / claims of completion (claims only, unverified)

| # | Date | Claim | M# |
|---|---|---|---|
| C-01 | 09-30 | CI checker changes on branch `quality/deployment-gates`. Run passed packaging/QMN/agents/Vulture/Skylos, failed coverage 79.34% | M17, M21 |
| C-02 | 09-30 | Baseline audit: PDF + report, 6 work packets, then 8 packets / 16 pages, saved to Library | M26-29 |
| C-03 | 09-30 | Defects found: daemon launch missing config; bot conformance passes with a silent substitute; backtest leaves no ledger row; journal retry success with unreadable data; indicator labels provisional data as confirmed; OpenCodex adapter returns synthetic responses | M18, M23, M24, M28 |
| C-04 | 10-01 | Renewed audit, 11 repair packets (ZIP); 5,252 tests; UI on separate branch with placeholder transport | M36-37 |
| C-05 | 10-01 | Wrote the Codex release orchestrator prompt and the goal prompts (later admitted too broad) | M40, M50, M53, M55-56, M81 |
| C-06 | 10-01 | Claude UI review prompts | M45, M61 |
| C-07 | 10-01 | Verified the Codex checkpoint `qmx-stop-checkpoint-2026-10-01` @ `7b4ece09` | M90-91 |
| C-08 | 10-02 | Checkpoint review: Windows research-save uses Unix fs ops; saved-analysis app→QMB mismatch | M96 |
| C-09 | 10-02 | Windows baseline: real QMB backtest matched (−$106 net, $9,894 equity); Python regression model; sessions/grants survive reopen | M114 |
| C-10 | 10-02 | Fixed Windows research save/reopen and staged artifact restart loss (artifact store + journal); 70 regressions; branch @ `0ee92341` (not pushed) | M138-139 |
| C-11 | 10-02 | Dukascopy: 211 EURUSD ticks ingested, real backtest, −$4.40 net, $9,995.60 | M152 |
| C-12 | 10-02 | Article search → hypothesis saved/reopened; QMB Study with 2 variants; parameter-driven variant check | M153-154 |
| C-13 | 10-02 | Storage failures/revisions, Study cancellation, queued-work persistence, host status/stop, schema/restore checks pass | M159 |
| C-14 | 10-02 | Trading-node recovery bug fixed (position reference); 35 tests | M161 |
| C-15 | 10-02 | Combined candidate `89b49d41`: 62 checks, 15 validation recipes; runner `Documents\Codex\2026-10-02\task-2\combined_recipe.ps1` | M162 |
| C-16 | 10-03 | QMA review: foundations exist, no model-driven agent loop | M168-170 |
| C-17 | 10-03 | Found Wayfinder and watch skills locally; analysed the video, T3 Code and CLIProxyAPI | M175 |
| C-18 | 10-03 | Six reviewers read both transcripts fully and compared them with BMAD, Docwork, docs and code; found the architecture cut/defer list | M182-183 |
| C-19 | 10-03 | Isolated SDK: request persistence, permission checks, tool loop, native Codex adapter; 58 tests; later 134 tests, authenticated queue, research op, status/cancel. Sign-in script `Documents\Codex\2026-10-03\task-4\Login-NativeCodex.ps1` | M189-190, M196 |
| C-20 | 10-04 | Recommended LangChain/LangGraph + official Codex/Claude SDKs; rejected Mastra/Vercel; target "usable candidate for Monday testing" | M197 |
| C-21 | 10-04 | Started three Codex sessions (SDK integration, backend fixes, provider compat) | M204 |
| C-22 | 10-04 | 7 baseline failures fixed; 1,848 tests | M206 |
| C-23 | 10-04 | Grok backlog found and assessed (Epics 67-73, Skylos, baseline failures "substantially addressed") | M219 |
| C-24 | 10-04 | LangChain/LangGraph migration committed: scoped memory, research delegation, restart recovery, OpenRouter policy change; 216 tests | M220 |
| C-25 | 10-04 | Combined backend 1,875 tests (later admitted QMA-suite only) | M223, M228 |
| C-26 | 10-04 | Data/API review: keep Parquet + SQLite/journals + DuckDB; gaps: op descriptions disagree with backend, QMB binding at startup, monitoring/backup wiring incomplete | M228 |
| C-27 | 10-04 | OpenRouter probe `Documents\Codex\2026-10-04\task-5\Start-OpenRouterProbe.ps1`; 29 offline checks; live never run | M237 |
| C-28 | 10-04 | QMB Windows ingestion Unix-lock problem sent for fix | M238 |
| C-29 | 10-04 | Spot-paper: two simulated accounts/nodes, different policies, single writer per account, restart-safe | M239 |
| C-30 | 10-04 | Native Codex/Claude adapters pass offline lifecycle tests | M241 |
| C-31 | 10-04 | Skills via released Deep Agents middleware; 3 adapter gaps fixed; skills in authenticated requests and research sub-tasks; YAML/profile patches; committed | M259-260, M264 |
| C-32 | 10-04 | "QMX at a glance" visualization | M272 |
| C-33 | 10-04 | Memory update: history, replacement, expiry, deletion, scoped retrieval | M274 |
| C-34 | 10-04 | CI: mutation-test false-green fixed, Linux/Windows checks, failed-run evidence retention | M275 |
| C-35 | 10-04 | 2,049 QMA tests; QMN 1,128 tests on Windows; strict typing 0 errors across 601 files (2,060 tests); Windows path race fixed; QMB 12 failures cleared | M277-288 |
| C-36 | 10-04 | Claimed it navigated Hermes Architecture → Programmatic Integration → Memory Providers and would use it as the reference (operator disputes, M422) | M307 |
| C-37 | 10-04 | Promised BMAD workflows + Documentation Factory for overnight work | M296 |
| C-38 | 10-05 | Four draft PRs incl. #23 (agent/workflow); QMB 1,484 tests; QMA 2,387; "pluggable memory" added | M322, M326 |
| C-39 | 10-05 | Installed package couldn't load API schemas, fixed; installed backend starts, auth API, DB persists/reopens; agent suite 2,418 passed | M330-331 |
| C-40 | 10-05 | Combined installer passes fresh env; draft PR #24; Codex review requested on 5 PRs; handoff `D:\Codex-Recovery\2026-10-05\final-integration\delivery\CLAUDE-UI-HANDOFF.md` | M332-334 |
| C-41 | 10-05 | Reviewed Claude folder `C:\Users\Mubarak\Desktop\QMX-session-for-Codex`: 51 sections, 16 research handbacks, 8 docs; Claude's map references a 09-30 commit | M343, M346 |
| C-42 | 10-05 | Artifact-upload limit config, restart-persistent; clock-backwards bug fixed; 441 checks; reviewed | M352-365 |
| C-43 | 10-05 | Mini-app work scoped into 13 steps; first milestone create → publish → update → undo for a data-only mini app | M352 |
| C-44 | 10-05 | Startup repair: 9 installed launches incl. cold restarts and blocked port; discovery API patch written | M373 |
| C-45 | 10-05 | Latest combined backend reviewed; push blocked because the repo is public (asked permission) | M383 |
| C-46 | 10-06 | Mini-app create → validate → publish → update → undo path reviewed; activity/logging piece has 2 review findings, not accepted | M392-393 |
| C-47 | 10-06 | Convex/TanStack browse; recommended TanStack Query, not Convex; caching analysis | M402 |
| C-48 | 10-06 | Activity/logging fixes done, but independent review blocked by the Codex cybersecurity safeguard (twice) | M403, M406 |
| C-49 | 10-06 | Handoff `D:\Codex-Recovery\2026-10-06\QMX-CLAUDE-SHARED-READS-HANDOFF.md` | M407 |
| C-50 | 10-06 | Admissions: Copilot path only accepts restricted predefined sequences; Deep Agents only "optional, restricted"; all model calls in proofs were injected offline; published app's read-permission request fails | M416, M419-421 |
| C-51 | 10-06 | Retrospective: PRs 20-24 open drafts, unmerged, no CI/status runs; later mini-app work local-only; handoffs never reached Claude. File `D:\Codex-Recovery\2026-10-06\QMX-DELIVERY-RETROSPECTIVE.md` | M431 |

Aurelius's own admissions of error: M74 (should have split into bounded runs), M81 (prompt included too-broad scope), M93 (ticket list too shallow), M115 (overstated workflow recovery bug), M118/M156 (stopped too early), M137 (called agents "next addition"), M160 (overstated a missing backtest adapter), M212 (left sessions on default model/thinking), M252/M254 (moved toward a custom loader, narrowed transcripts), M263 (drift), M399 (delegated browsing it was told to do itself), M418-423 and M431 (blurred required vs built; overstated readiness).

---

## 4. Operator complaints

| # | Date | Complaint | M# |
|---|---|---|---|
| K-01 | 10-01 | Codex run took all day and burned usage; prompt too big; "one-shot prompted an entire trading terminal" | M69, M79, M82 |
| K-02 | 10-01 | Codex invented its own source manifest, release gates, build tooling, launcher.py; coverage metric unexplained | M84 |
| K-03 | 10-01 | Goal mode wastes tokens; Codex overbuilds and ignores YAGNI | M88 |
| K-04 | 10-01 | Plan "undermining" what's needed: blocker list "meh"; needs re-audit depth | M92 |
| K-05 | 10-02 | Too much back-and-forth will confuse the working agent | M131, M136 |
| K-06 | 10-02 | Responses too wordy ("texty"); wants glanceable | M134, M270, M325 |
| K-07 | 10-02 | Agent work should never have been called the "next addition"; new features keep creeping in | M136, M157 |
| K-08 | 10-02 | Fixes left "isolated and unmerged", work stopped, still "waiting for permission" granted 4 hours earlier | M155 |
| K-09 | 10-02 | Ignored the morning phone-call goals; "Getting tired of re-echoing that" | M157 |
| K-10 | 10-02 | Asked "what's in our backlog" many times | M163 |
| K-11 | 10-03 | "I don't want to babysit you" | M184, M265 |
| K-12 | 10-04 | Didn't reread transcripts; skills/hooks invented rather than following LangChain/Claude SDK patterns; "I'm overcorrecting you on simple things" | M251, M253 |
| K-13 | 10-04 | Verification work irrelevant while the core is changing | M257 |
| K-14 | 10-04 | Bulk-batching work; wants chunking; false positives | M270 |
| K-15 | 10-04 | Patches may leave commented-out code | M284 |
| K-16 | 10-04 | Hadn't seen Aurelius browse the Hermes site | M306 |
| K-17 | 10-05 | "Why is it taking so long"; must work out of the box | M327 |
| K-18 | 10-05 | Confusing "connection dropped" wording while the laptop was online | M358 |
| K-19 | 10-05 | Stopped again to ask permission despite explicit go-ahead; "you really should be performing way better now... I thought you have memory" | M361 |
| K-20 | 10-05 | Suspected Aurelius had merged PRs | M377 |
| K-21 | 10-06 | Delegated browsing to an agent when told to do it personally | M398 |
| K-22 | 10-06 | "This is a little bit too much for you"; refactor should be held | M404 |
| K-23 | 10-06 | Testing only with QMB/backtests; no hypothesis → strategy agent test | M412 |
| K-24 | 10-06 | **"Sloppy, very sloppy":** claimed to read the mini-app transcript but treated workflows/Copilot-created mini apps as new; considering stopping all work; "most of the things... might... be irrelevant" | M417 |
| K-25 | 10-06 | Deep Agents in workflows ignored despite instruction | M417, M432 |
| K-26 | 10-06 | Copilot "how Codex or Claude could work" not taken into context; Hermes docs not read; "I don't see the point in working with you a lot anymore" | M422 |
| K-27 | 10-06 | Batching work and wasting tokens; responses not understandable; "five, six days of work... is it actually correct?" | M422 |
| K-28 | 10-06 | Agents shown as running after the claimed pause | M424, M428 |
| K-29 | 10-06 | **Final (M432):** doesn't understand what a mini app is (not a workflow combo, usually no agents); "optional" Deep Agents vs explicit instruction; pluggable memory, Hermes and memory (1-2 hours of discussion) never reported; poor delegation; didn't modularize or refactor properly; never browsed GitHub to check what's actually there; assumed things exist; work could have shipped "within hours"; code probably poor; "I thought you were better than maybe Grok" | M432 |
| K-30 | 10-06 | Wants RAW transcript and call data (no summaries), plus a handoff of what was actually shipped vs assumed | M432 |

---

## 5. Open threads (discussed, never resolved)

- **OT-01** Phone calls (10-01, 10-02 morning, ~10-03/04, 10-04 afternoon) hold binding directives (Deep Agents in workflows, Copilot = Codex/Claude-like, memory design, Hermes) that aren't in this text. Recordings/transcripts needed (M432 asks for "the phone call" raw).
- **OT-02** Mini-app definition contradiction: M417 (workflows combine into mini apps) vs M432 (not a workflow combination; usually no agents). M432 is final, but the positive definition of what a mini app *is* has not been stated. Recover it from the mini-app transcript ("explorer node editor" zip).
- **OT-03** Deep Agents as the default workflow agent: not implemented (only optional/restricted, M420).
- **OT-04** Pluggable memory provider (Hermes pattern): which provider (M300, operator's choice) is undecided; Copilot vs workflow memory scoping; durability across restart (research memory was in-process, M133).
- **OT-05** Copilot as a coding-agent harness building custom workflows/mini apps: current path restricted to predefined sequences (M419). Copilot kinds per page (M184, M291) are undefined.
- **OT-06** LangGraph prebuilt vs LangChain agent usage: the architecture explanation call was requested (M291) and never delivered.
- **OT-07** Live provider proof: no live model call ever made. OpenRouter $0.50 test, DeepSeek route (no free route found), native Codex sign-in test (M196) all unrun.
- **OT-08** Claude subscription legality/approach for external harnesses (M171, M174-175).
- **OT-09** Remote execution: VPS (Contabo) vs Amp orbs vs Modal; Tailscale; S3 bucket; "middle node" revival (M171, M377).
- **OT-10** ExperimentSpec registration/provenance for manually authored (no-model) experiments: no defined entry path (M160, M164).
- **OT-11** Managed agent interpreter decision (M162, M164).
- **OT-12** Windows-only vs Windows+Ubuntu QMN placement (M40, M50).
- **OT-13** Codex Review GitHub setting: never confirmed enabled; 5 review requests unanswered; PRs 20-24 show no CI runs (M146, M335, M431).
- **OT-14** Activity/logging mini-app piece: review blocked by Codex cybersecurity safeguard (M403-406).
- **OT-15** Published mini-app can't obtain read permission for its saved result (M421, M431).
- **OT-16** Artifact-storage limit has no user-facing setting (M332).
- **OT-17** Four timing (flaky) failures documented (M333); coverage below 80% floor; QMB/QMN residual failures (M277).
- **OT-18** Grok's 28-Sep backlog (`workroom/backend-assurance-2026-09-27/BACKLOG.md`): venues, multi-node, paper, live-model attachment, CLIProxy routing, memory & RLM, fresh-install/laptop QA, Skylos/dead code, market calendars & news, STRATS seed corpus, MIS training & delivery evidence, UI Epic 66, Epics 67-73. "Knock it off today" (M213) not done.
- **OT-19** Spot crypto (CCXT/Hummingbot) and spot FX real connectivity; multi-broker/multi-account onboarding UI; per-account risk systems (only paper slice claimed, M239).
- **OT-20** Mini-app DevOps/networking runtime ("not just docker", M350); 13-step plan only partly done.
- **OT-21** Caching strategy across UI/mini apps/backend (M395, M402). TanStack Query is a recommendation, not ratified.
- **OT-22** Templates for mini apps and workflows: existence never verified (M86, M87).
- **OT-23** Agentic browser for QMX (M88); MCP endpoint for QMB "explicitly unfinished" (M91).
- **OT-24** Agent departments (quant traders/researchers/analysts) and node-editor agents (M88): not addressed.
- **OT-25** "Folder as an agent" pattern research (M251): outcome unreported.
- **OT-26** Pre-mini-app version "more stable" hypothesis (M88): compare the same journey on both, proposed but never done (M91).
- **OT-27** Draft documentation patches (M235): never shown delivered; doc layout rethink.
- **OT-28** Combining ML Studio + backtesting + node editor (M155): parked.
- **OT-29** Copilot skills/hooks/plugins; VPS trading-node setup via UI; the Lab (parked M150, M164, M233).
- **OT-30** GitHub → GitLab move (M134); TestSprite (M86).
- **OT-31** Merge status: operator suspects Aurelius merged (M377). Aurelius says PRs 20-24 unmerged and the later work local-only (M431). Needs independent verification on GitHub.
- **OT-32** Operator's "first legacy release" target and the "working QMX by morning" ask (M377): not met.

---

## 6. References: paths, repos, branches, commits, PRs, docs

**Repo / GitHub**
- Repo: `MubarakHimself/QMX` (public, M383). Issue **#11** (factory-enforcement blockers, M6).
- Draft PRs **#20-#24** (all open, unmerged per M431). **#23** = agent/workflow improvements (M322). **#24** = combined backend (M334).
- Actions runs: 36605776702 (backend checks), 36312350516 (UI check), 36682167068 (verification run) (M7, M17, M21).
- Workflow: `.github/workflows/battery.yml` on `integration` (M7).

**Branches**
- Protected: `main`, `integration`, `ui-integration` (M9).
- `deployment/fmt-check` → rename to `archive/deployment-fmt-check`; new `deployment` from integration (M8-10, M16).
- `quality/deployment-gates` (Aurelius CI changes, M16-17).
- `ui-epic/066-shell` @ `f6ffaddf3f78c6c14d32daa136fadf15e7748c14` (audited UI, M50).
- `qmx-stop-checkpoint-2026-10-01` @ `7b4ece09f3a43a9525a81bf029804fbfbf2b161e`, file `release/STOP_HANDOFF.md` (M88, M90-91).

**Commits**
- Backend integration `a0e8769772e469bf54bd312cc1e27e7995e16c3b`; docs main `c3e8ec5ef33d0b38cdf7f5dbdd48a6fc70ac33cf` (M50).
- OpenCodex adapter at `49e72693f7b8b33bbb995b410bbd5ec501e14999` (M18).
- Local repair `0ee92341` (M139); combined candidate `89b49d41` (M162).

**Code paths**
- `qmx-agents/packages/qma-daemon/src/qma/daemon/proxy/opencodex.py` L131-171 (synthetic response, M18).
- `qmx-agents/packages/qma-daemon/src/qma/daemon/composition.py` (agent wiring, M133).
- `apps/qmx-ui` (Claude-owned; Svelte 5/SvelteKit, shadcn-svelte, Bits UI, M45, M61, M402).

**Local files (operator laptop)**
- `C:\Users\Mubarak\Desktop\QMX\workroom\backend-assurance-2026-09-27\BACKLOG.md` (Grok backlog, M219).
- `C:\Users\Mubarak\Desktop\QMX-session-for-Codex` (Claude UI session folder + backend notes, M336).
- `C:\Users\Mubarak\Documents\brain\brain\Clippings\Code Review Checklist & Best Practices (3-Layer Model).md` (M142).
- `C:\Users\Mubarak\Documents\Codex\2026-10-02\task-2\combined_recipe.ps1` (M162).
- `C:\Users\Mubarak\Documents\Codex\2026-10-03\task-4\Login-NativeCodex.ps1` (M196).
- `C:\Users\Mubarak\Documents\Codex\2026-10-04\task-5\Start-OpenRouterProbe.ps1` (M237).
- `D:\Codex-Recovery\2026-10-05\final-integration\delivery\CLAUDE-UI-HANDOFF.md` (M333).
- `D:\Codex-Recovery\2026-10-06\QMX-CLAUDE-SHARED-READS-HANDOFF.md` (M407).
- `D:\Codex-Recovery\2026-10-06\QMX-DELIVERY-RETROSPECTIVE.md` (M431).
- Task copies moved to D: after C: filled up (M311). Two transcripts in Downloads: "explorer node editor" zip = mini-apps transcript; second = agents transcript (M176, M180).
- Project doc layers: `docwork/` (working), `docs/` (refined), BMAD architecture, `_bmad-output` (M136).

**Docs / epics referenced**
- Audit packets 00 (reconciliation), 01 (startup/resources), 08 (UI), 09 (quality gates) (M40, M53).
- Epic 28 = unattended one-week paper soak (M97). Epics 53-59 = mini-app transition, expanded in 60-65 (M98). Epic 66 UI; Epics 67-73 backend; Epic 70 merged 09-30 (M25, M219).
- WF1/WF2: two different historical concepts in the docs (M96); test fixtures only (M414).

**External links the operator supplied**
- CLIProxyAPI: https://github.com/router-for-me/CLIProxyAPI (M88).
- Dukascopy node CLI: https://www.dukascopy-node.app/config/cli (M149).
- T3 Code: https://github.com/pingdotgg/t3code (M171); video https://www.youtube.com/watch?v=D8PikZ1KhUo&t=2923s (M171).
- Hermes Agent docs: https://hermes-agent.nousresearch.com/docs (M294).
- getbb.app: https://getbb.app/ (M295, purpose unstated).
- BMad Builder docs: https://bmad-builder-docs.bmad-method.org/ (M298).
- Convex https://www.convex.dev/ and TanStack https://tanstack.com/ (M395).
- Named, no link: Hummingbot, CCXT (M230); Wayfinder skill (Matt Pocock) and watch skill (M171); Amp code "orbs"; Modal; Tailscale; Contabo VPS; S3; Hindsight; Alibaba memory; LangMem; Deep Agents; Claude Agent SDK; TestSprite; Handy (dictation).

**Tools/infra notes**
- Aurelius's Codex tasks ran on the operator's laptop through a ChatGPT-desktop connection that kept dropping (M217, M302, M372). No native desktop clicking or Claude control (M114).
