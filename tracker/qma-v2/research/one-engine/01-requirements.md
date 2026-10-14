# QMA v2 one-engine re-plan: the operator's intent, re-derived

Status: context-mining output, 2026-10-14. Read-only analysis. It reconstructs what the operator (Mubarak) wants from his own words, then re-derives it for ONE engine, the Claude Agent SDK, per his ruling of 2026-10-13 18:32 UTC.

The two-engine conclusions (HARNESS*.md, BASELINE.md, qma-v2/research, sketch, PROMPT-*.md, archive) were not read. Section 11 was added after the draft, from the cross-check files named there.

## 0. Sources and how to cite them

Times are UTC. Local time is UTC+3.

| Tag | What it is |
|---|---|
| EV | `tracker/qma-v2/trail/session-evening-dialog.md` (2026-10-13 15:50 to 18:37) |
| OM | `tracker/qma-v2/trail/sources/2026-10-12-13-session-operator-messages.md` |
| T1 | Full operator text and question-tool answers of session `19014dde` (the 2026-10-12/13 session). Same session as `Downloads/session-export-1791865801044.zip` `transcript.jsonl`. Read from `~/.claude/projects/C--Users-Mubarak-Desktop-QMX/19014dde-...jsonl`. |
| T2 | Session `2cf20068` (2026-10-13). It holds the 04:35 to 04:58 morning messages, the question-tool answers, and the 18:40 and 18:42 messages after the EV digest ends. |
| dialog | `tracker/qma-v2/trail/sources/2026-10-12-13-session-dialog.md` (operator plus Claude, 10-12/13). Used to see what Claude said before each correction. |
| ZR | `Downloads/session-export-1791792430617.zip` `transcript.jsonl`, title "QRMX risk management and precision sizing", 2026-10-05 to 10-12 |
| ZP | `Downloads/session-export-1791792436995.zip` `transcript.jsonl`, title "QMX product audit and status", 2026-10-07 to 10-12 (the session resumed on 10-12) |
| ZU | `Downloads/session-export-1791792438998.zip` `transcript.jsonl`, title "QMX UI audit and planning", 2026-10-01 to 10-05 |

A citation such as `T1 15:22 answer` means the question-tool answer at that time. A zip citation gives the zip tag, the line in `transcript.jsonl`, and the timestamp.

Warning for later readers. OM is truncated. The script that made it (`human.py`) cuts every message at 6,000 characters. Fifteen of his messages on 10-12 are longer than that, and the cut parts hold rulings (for example the 15:16 "design for these two" tail and the 16:22 "Can't I use my claude subscription" passage). Use T1 for full text. OM also has no question-tool answers, which hold several rulings.

## 1. Journey

**Before 10-12 (context sessions).**
- 10-01 to 10-05 (ZU). UI rebuild. He names three agent types: workflow agents, sub-agents, copilots (ZU l.3557, 10-01 19:00). "customizability is paramount" and "a box of Legos" (ZU l.5311, 10-02 10:07). He wants the app to feel like the Codex, ChatGPT and Claude desktop apps (ZU l.11717, 10-04 08:51).
- 10-07 (ZP). He wants his subscriptions, not API pricing ("I would prefer using my subscriptions", ZP l.1195, 12:51). CLIProxy is his first idea for routing accounts.
- 10-09 (ZP). He rejects modes in favour of skills (ZP l.2597, 19:23). He picks a winner per area: "For hooks and permissions, Claude wins", "Computer use, obviously, codecs", memory to Hermes (ZP l.2747, 20:14).
- 10-04 (ZU) and 10-07 to 10-12. The stack is LangChain, LangGraph and Deep Agents.

**10-12 (session 19014dde).**
- 08:13 (11:13 local). He resumes the product-audit session on his own Claude account. He wants a structured method (pstack, Pocock skills) to stop "vibe coding" (OM 08:22).
- 08:39 to 10:02. Brain dump and research pass. Copilot plus workflow agents, organogram, CFDs on cTrader, computer use, router. 10:02 gives the core mental model: the tools Claude Code has are "the baseline" for every agent. He also leans to Claude's SDK for compaction, caching and hooks (T1 10:02 tail).
- 09:20 to 09:42. "I don't want to use claude code". He wants his own agents, a router across subscriptions, and a harness that is not model-specific (OM 09:20, 09:42).
- 14:39. He pushes back on the hybrid ("Choose one. Are we using the SDK? Are we using claude code?", T1 14:39 tail). He picks option B (LangGraph base, Claude Code as a worker) with doubts.
- 15:01 to 15:16. He finds Kimi's page on running Kimi inside Claude Code with a base URL ("exactly what I wanted", OM 15:01). He rejects a Claude Code session per provider because of RAM (OM 15:16). Then he proposes two SDKs: "We designed just two: OpenAI and Anthropic" (OM 15:16, second paste). This is the origin of the two-engine plan.
- 15:22. In the question tool he picks "Two lanes" and stresses "API key compatibility" (T1 15:22 answer).
- 15:30. Claude pushes back on the OpenAI Agents SDK as engine two: it speaks OpenAI format, so Anthropic-format providers would need a translator (dialog 15:30). 15:40: he overrides that ("Literally, rebuild it in OpenAI's SDK?", OM 15:40).
- 15:53. Fresh rebuild of the whole agent system as QMA v2, old code deleted (OM 15:53).
- 16:22 (19:22 local). He clarifies what he wants from the Claude Agent SDK. He wants "a library that runs the claude code binary with claude code capabilities", not the CLI (T1 16:22 tail).
- 16:40 to 17:11. No Anthropic API, ever (OM 16:40; T1 17:11 answer).
- 17:20 to 18:03. Mine the journey, FRs, NFRs and seeds with sub-agents. Then overnight work.

**10-13 morning.**
- 03:55 to 04:22 (06:55 to 07:22 local). Answers. Platform-neutral. Console now, UI later. Money read-only. Harness first. Orchestrator like P01 to P25 (T1 03:55; T1 04:14 and 04:22 answers).
- 04:28. He ends that session because it did not rerun the workflow after the scope change (OM 04:28).
- 04:35. New session 2cf20068 audits the old one (T2 04:35).

**10-13 evening (session 2cf20068).**
- 15:50 (18:50 local). Big answer message: one Claude Max, 50% editable background cap, perms and hooks from Claude Code, UI out, computer use assumed covered by the SDKs (EV 15:50).
- 16:04. Destination = harness coding prompt plus deletion only. Sign-off = "Talk to it like Claude Code" (T2 16:04 answer).
- 16:06. Claude reports that computer use is not available on any subscription (EV 16:06).
- 17:57. Platform-neutral secrets. Opus for coding. QMX settings separate from his own Claude Code (T2 17:57 answer).
- 18:14 to 18:24. He asks how the SDK docs handle the agent guard, then asks why two harnesses at all (EV 18:14, 18:24).
- 18:28. He separates "OpenAI API" from "Sign in with ChatGPT": every provider except GPT speaks Anthropic's format (EV 18:28).
- 18:32 (21:32 local). Ruling: one SDK, the Claude Agent SDK, plus a GPT patch (EV 18:32).
- 18:37 to 18:42. The next session must do all the context work itself and "maximize that one" (EV 18:37; T2 18:40, 18:42).

## 2. Ruling ledger (latest wins)

Status key. "Current" means still in force. "2E" means it was made under the two-engine assumption and needs re-checking for one engine.

| # | When | Ruling | Quote (under 15 words) | Status |
|---|---|---|---|---|
| R1 | EV 18:32 | One engine, the Claude Agent SDK. GPT via a ChatGPT sign-in patch. | "it doesn't make sense for us to ship both engines" | Current. Supersedes R13, R14, R15, R27. |
| R2 | EV 18:28 | All providers but GPT use Anthropic's format by default. No OpenAI SDK needed. | "by default, we don't need OpenAI SDK" | Current |
| R3 | EV 18:28 | LiteLLM is optional, Claude's call. | "we can if you see it fit" | Current |
| R4 | T1 17:11 answer | Never pay for Claude or OpenAI API. | "I don't want to pay for API ever" | Current. Hard rule. |
| R5 | EV 15:50 | One Claude Max plan, no second account. | "I have one, I never said anything like two." | Current |
| R6 | EV 15:50 | Background agents may use up to 50% of a 5-hour window, editable. | "so 50%, but editable, that's okay" | Current |
| R7 | EV 15:50 | Permission modes and hooks copy Claude Code, which the SDK has built in. | "we can literally just look at clone card" ("clone card" = Claude Code) | Current. Replaces the 10-09 "no modes" for permission modes. |
| R8 | ZP l.2597, 10-09 19:23 | No behaviour modes (ask, plan, review). Use skills. | "a mod can be replaced 90% over time by a skill" | Current for behaviour modes |
| R9 | T2 16:04 answer | Destination: harness coding session plus old-code deletion. UI out. | "only harness and deleting of code. That's it." | Current |
| R10 | T2 16:04 answer | Sign-off: talk to it like Claude Code. | "Talk to it like Claude Code (Recommended)" (option he picked) | Current. The option text included "Switching that chat to an OpenRouter model also works". 2E for how OpenRouter non-Claude models run. |
| R11 | T2 16:04 answer; T1 03:55 | A temporary console now, deleted later. Real UI later. | "Give me a temporary way to talk to the agent" | Current |
| R12 | T1 04:14 answer | Money is read-only for agents. Writes need his manual invoke and allow. | "Money, okay, the agent can access, but it's a read-only." | Current. Matches FR-Q42 and DEC-0315 in the repo. |
| R13 | T1 15:22 answer | Engine shape "Two lanes" (Claude Code lane plus own API lane). | "Two lanes (Recommended)" (option he picked) | Superseded by R14, then R1 |
| R14 | OM 15:16 (second paste) | Design for two SDKs, OpenAI and Anthropic. | "We designed just two: OpenAI and Anthropic." | Superseded by R1 |
| R15 | T1 04:22 answer | Hooks: consider both Claude Code and Codex, rebuild Claude's in OpenAI. | "you can use what Claude Code has rebuilt it also in OpenAI" | Superseded by R1. 2E. |
| R16 | T1 04:22 answer | GPT on ChatGPT sign-in "won't fail". | "So, for you to say that it, what if it fails, it won't" | 2E. Under one engine GPT goes through a translator on a restricted route (EV 18:25). Still untested. |
| R17 | T1 04:22 answer | Harness first. Organogram, workflows, methodology later. | "so yes, build the harness first" | Current |
| R18 | T1 04:22 answer | Ship via an orchestrator session, packets like P01 to P25. No factory. | "So we don't need a factory" | Current (also in project CLAUDE.md) |
| R19 | T1 03:55; T2 17:57 answer | Platform-neutral: Windows, Mac, Linux. No Windows-only secret store. | "it shouldn't be built to be only a Windows-based system" | Current |
| R20 | T2 17:57 answer | QMX's agent system and his own Claude Code never interfere. | "two different systems" | Current |
| R21 | T2 17:57 answer | Money speed bump accepted for now. Trading node is a plain server. | "the threading node by default should just be a server" | Current |
| R22 | T2 17:57 answer | Coding on Opus 5.5. Fable for review only. Sonnet only for light work. | "I would really prefer just Opus" | Current. Global CLAUDE.md now says Fable only when he asks. |
| R23 | T2 17:57 answer | Settings for sub-agent limits live in a QMX settings file, shown in the UI. | "if you look at the UI, it should be there both for both SDKs" | 2E. Now one SDK. Intent (UI-editable QMX settings) stands. |
| R24 | T1 15:22 answer | QMX uses API keys via "API compatibility" (base URL plus key). | "The compatibility word is very important." | Current. Fits one engine directly. |
| R25 | T1 03:55 | Remote agents tested on OpenRouter credit. First month runs on his machine. | "I have open router, it has a few dollars here and there" | Current |
| R26 | T1 03:55 | Rented compute later. Test on his own server in Docker. | "try it out maybe in my server on Docker" | Current |
| R27 | T1 15:01 tail | GLM and Kimi inside LangChain is non-negotiable. | "this is a non-negotiable" | Superseded in form by R1 (LangChain dropped). The intent (use GLM and Kimi) stands and fits one engine. |
| R28 | T1 16:22 tail | No sandboxes. | "I really don't think we are ever going to use sandboxes" | Current, but see Q5 (10-04 he floated sandboxes for copilot-written code) |
| R29 | T1 16:22 tail | Memory: use the SDK's default, keep a pluggable layer. | "keep the pluggable layer intact" (OM 16:22) | 2E only in that "the SDK" now means Claude's |
| R30 | OM 16:22 | Old docs archived, not deleted. QMA name kept ("quant agents"). | "QMA is just quantum agents" | Current |
| R31 | EV 15:50 | Old-code deletion timing is Claude's call. | "that's not for me, actually, that's for you" | Current. Deletion only with proper branching (T2 16:04). |
| R32 | EV 18:37 | Strats and QML handled elsewhere. QMB gets its own session. QMF refactor regardless. | "Struts and KML are handled. Mark them out." | Current |
| R33 | T2 04:35; EV 16:21 | Sub-agents never spawn sub-agents. Opus default, Sonnet only tiny jobs. | "sub-agents cannot use other sub-agents" | Current |
| R34 | T2 16:04 answer | Vocabulary is Claude's to settle from the transcripts. | "this is for you to figure out" | Current |
| R35 | T1 04:14 answer | Always ask him for publish, install, scheduling and managing. | "Most of this publishing or installing and managing, everything as managing." | Current |
| R36 | T1 04:14 answer, Q3 | Thinking effort works the way Claude Code does it, out of the box. | "I like the way how claude code just works right out of the box." | Current. Originally "claude code or codex", so 2E in wording only. |
| R37 | EV 15:50 | Prompts go in chat; files only when long, indexed from chat. | "I don't like prompts as files unless it's very long." | Current |
| R38 | OM 16:22 | Branches: integration, staging, main. Others are clutter. | "those three are the major ones. The others are nonsense." | Current (integration not ready, per project CLAUDE.md) |

## 3. Mental models, in his words

- **Claude Code's tool set is the floor for every agent.** "the tools you have access to, the capabilities you can do right out of the box, that's the baseline" (OM 10:02). Repeated as "normal claude code is the best line it's just that QMX is complex" (T1 15:01 tail) and "It's literally the worst that QMX's harness can be" (T1 04:14 answer, Q3).
- **An agent is a model plus capabilities. He wants the capabilities, not the CLI.** "I don't want cloth code CLI. I want the bloody capabilities." and "An agent is just a model with capabilities" (T1 16:22 tail).
- **Hooks, not instructions, enforce rules.** "an instruction and a hook are different" (T1 04:14 answer). Hooks also tell agents where to write things: "Hooks now tell the agent, no, put it here." (OM 10:02).
- **Money is read-only.** "you never touch the money, and it's kinda impossible" (T1 04:14 answer). Withdrawals happen at the broker, so agents cannot move money.
- **Configurable means UI-editable, with defaults (Lego).** "like you're handing a box of Legos" (ZU l.5311). Sub-agents "should be configurable by default, or sorry, in the settings and by default" (T1 16:22 tail).
- **QMX is separate from his personal Claude Code.** "I can't have the same things across that makes bloody no sense" (OM 15:01). "QMX should be not interrupted by claude on my machine, and vice versa" (T2 17:57 answer).
- **Platform-neutral.** "it's not biased in any way, shape, or form" (T1 03:55).
- **API compatibility, not vendor lists.** "I'm looking at API key compatibility" (T1 15:22 answer). Every provider is a row.
- **The router balances sessions and usage, not requests.** "it's not balancing requests, it's balancing sessions" (T1 16:22 tail). It replaces CLIProxy and shows limits like T3 Code (OM 10:02).
- **Sessions persist for days.** "if a session is running for long days that session should persist" (OM 15:40). No fresh session per decision.
- **Claude orchestrates and picks models.** A Claude model drives, with access to the models it may use and their remaining usage (OM 15:40).
- **Not model-specific.** "be more free" so a new model like Fable can drop in (OM 09:42).
- **Don't reinvent the wheel.** "We really don't have to design everything from scratch" (ZP l.283). "I'm not the only one facing this problem" (T1 15:16 tail).
- **A plugin bundles tools, skills, a model and hooks.** "a plug-in under identic engineering is a combination of MCPs or tools together with skills, a model, and hooks" (OM 16:22).
- **Design for complexity, but ship the simple harness.** "You should really aim for complexity in everything." (OM 10:02). Later: "We are really just literally like piecing puzzle pieces" (T2 17:57 answer).

## 4. Seeds and vision items (backlog, not harness scope)

| Seed | Where he said it |
|---|---|
| Organogram: general copilot plus Lab and Portfolio copilots; sessions keep their home (badge) and can be resumed in the main shell; projects like Codex | OM 08:39; T1 04:14 answer (Q4); ZU l.7350 |
| Lab copilot gets more freedom, Portfolio copilot less freedom and more instruction | T1 04:14 answer (Q2) |
| Mini apps as plugins; a vanilla copilot per app; the mini-app SDK is a different thing from the agent SDK | T1 04:14 answer (Q4); ZU l.11717 |
| Copilot builds, maintains and controls mini apps, workflows, widgets and UI panels; a build mode; MCP apps idea | ZP l.283, l.342; ZU l.4873, l.12056 |
| Workflows as graphs and loops, agentic, deterministic and mixed; "build our own graph"; dynamic workflows; WF1, WF2, WF3 | OM 14:39; T1 16:22 tail; T1 17:11 answer; ZR l.1548 |
| Cron jobs (Hermes style), server and remote agents, local-to-server session moves, buckets, git for concurrent edits | OM 08:39, 15:40; T1 15:22 answer; ZP l.1459 |
| Server agents run without asking him | ZU l.8602 ("there is this assumption that we might most likely not need permission") |
| Automatic transcript and log export for server agents | OM 09:07 |
| Memory bake-off (Hindsight, Mem0, LangMem, Hermes) and self-improvement ("I don't want it to do the same mistake") | T1 08:39 tail; T1 10:02 tail; ZP l.342 |
| Copilot and trader-agent methodology from Pocock plus BMAD skills; system prompts as meta prompts | T1 04:14 answer (Q2); T1 04:22 answer; T1 16:22 tail; ZP l.2471 |
| Computer use on cTrader and MT5, browser with saved TradingView login, learn a pattern from a YouTube video | OM 08:54, 10:02 |
| cTrader MCP on by default for the copilot; charting; news | ZP l.747 |
| Firecrawl Alexandria in QMX; learning from papers | T1 10:02 tail; ZU l.10891 |
| Voice or conversational mode; "system one" models; GPT audio and images | T1 15:22 answer; OM 16:22 |
| Agent improvement loop with traces and evals (OpenAI cookbook); evals built in | OM 16:22, 15:40 |
| Library as a database or git store, refactor later | OM 10:02; T1 15:40 tail |
| QMB as a tool agents call but cannot change; own session later | T1 14:39 tail |
| Decay-spotting daily workflows; deterministic alerts instead of agents watching trade counts | ZR l.1548, l.1578 |
| Agents messaging other sessions | T1 08:39 tail |
| GPU and rented compute later; agents may need their own VMs | ZP l.1459; ZU l.5311 era (10-02 11:30); T1 03:55 |
| Deletion blast radius pre-audit before deleting code | ZP l.2324 |

## 5. Points he repeated

| Point | Count | Times |
|---|---|---|
| Use the skills, stop vibe coding, follow a structured workflow | 7 | OM 08:22, 15:28, 15:43, 17:37; T1 04:22 answer; EV 15:54, 15:59 |
| Don't assume I read your reply while agents run | 3 | ZR l.190 (10-05); OM 09:07; T2 04:38 |
| Subscriptions only, no API spend | 5 | ZP l.1195; T1 09:07 tail; OM 09:30, 16:40; T1 17:11 answer |
| API compatibility (base URL plus key) | 4 | T1 15:01 tail; T1 15:22 answer; OM 15:40; EV 18:28 |
| Claude Code is the baseline | 4 | OM 10:02; T1 15:01 tail; T1 04:14 answer; T2 16:04 answer ("I gave you a baseline") |
| QMX separate from my Claude Code | 3 | OM 09:42, 15:01; T2 17:57 answer |
| Platform-neutral | 2 | T1 03:55; T2 17:57 answer |
| Design for complexity | 5 | OM 10:02, 10:45, 16:40; OM 17:23; T2 16:04 answer |
| Read docs with a browser, not summarised pulls | 4 | T1 08:54 tail; T1 16:22 tail; OM 16:40; EV 15:50 |
| Sessions must persist; no session per decision; RAM per session | 4 | ZU l.8602; T1 10:34 tail, 15:16, 15:40 |
| Don't reinvent the wheel; copy what others did | 6 | ZP l.283, l.2597; ZU 10-04 09:19; T1 15:16 tail; OM 15:48; T1 16:22 tail |
| Codex is open source: study it, don't use it | 3 | OM 08:39, 15:48; T1 04:22 answer |
| Opus 5.5 is his daily driver | 3 | ZU l.10891; ZP l.1195; OM 08:39 |
| Limit sub-agents; none spawn their own | 4 | OM 08:13; T2 04:35; EV 15:50 ("29 sub-agents"); ZR 10-06 08:02 |
| Caching saves usage, high priority | 2 | OM 09:07; ZP l.2597 |
| Don't make me repeat myself | 5+ | OM 15:16, 17:20; T1 17:11 answer; T2 16:04 answer; EV 18:37 |

## 6. Corrections (what the agent got wrong, and the lesson)

| # | When | What the agent did | His correction | Lesson |
|---|---|---|---|---|
| C1 | OM 09:42 | Fixed routing: Claude jobs to the Claude Code engine, research sub-agents to Kimi | "you're being too specific i want to design a harness that is more free" | No hard-coded model per job. Defaults the user edits. |
| C2 | OM 09:42; T1 14:39 tail | Put Claude Code inside LangGraph as a worker | "claude code is already a harness on its own" | Don't nest one harness inside another. |
| C3 | T1 14:39 tail; T1 16:22 tail | Used "Claude Code" and "Agent SDK" as if interchangeable | "Choose one. Are we using the SDK? Are we using claude code?" | One word per thing. To him "Claude Code" means the CLI. Say "Claude Agent SDK". |
| C4 | OM 14:45 | After compaction, answered without the morning research | "can you retrieve what was going on in the research earlier today?" | After compaction, re-read the saved research before answering. |
| C5 | OM 15:16 | Said coding plans can't use the router, proposed a Claude Code profile per provider, and said it would test each because Anthropic doesn't officially support them | "you don't need to test sheets to be honest. They work" and "I wasn't proposing it as the actual design" | Vendor docs that thousands use are enough. A passing thought is not a decision. One process per session costs RAM. |
| C6 | T1 15:22 answer | Asked questions in the tool before digesting his message | "asking me questions now is a wrong move" | Digest first, then ask only real decisions. |
| C7 | OM 15:28 | Skipped how and why after the design reshaped, reported grilling as done, agreed too easily | "You are just being agreeable." | Rerun the workflow when the frame changes. Give a real opinion. Never report a step that did not run. |
| C8 | OM 15:40 | Proposed short Claude Code sessions at each workflow decision point | "that is messed up dude very messed up" | Long sessions persist. Context engineering first. |
| C9 | dialog 15:30, OM 15:40 | Claude argued the OpenAI SDK would need a translator, so "one format, not two". Then dropped the point when he pushed. | (He overrode it at 15:40. He reached the same conclusion himself at EV 18:28.) | Hold a sound technical objection until evidence, not frustration, changes it. |
| C10 | T1 16:22 tail | Said compaction only works on OpenAI models, "kept alive by compaction", read the router as request load-balancing, misread AMP | "why do you seem like you're not technical enough" | Read the real docs. The router balances sessions and usage. |
| C11 | OM 16:40 | Treated QMX mini apps like AMP portals | "I don't think that's what I meant by mini apps" | A mini app is a QMX concept at ML-level complexity. |
| C12 | T1 17:11 answer | Proposed using the $100 monthly API credit | "I don't want to pay for API ever" | Never propose Claude or OpenAI API spend. Say plainly if a subscription route is impossible. |
| C13 | T1 17:11 answer | Asked his server size as if the server were decided | "the server isn't a proposal, it wasn't, you were meant to give me a response" | When he asks for a response, respond. Don't turn musings into decisions. |
| C14 | OM 17:20, 17:23 | Designed from in-session memory, not from exported transcripts | "you orchestrate okay if there's a step that needs a lot of context" | Extract the transcripts and have sub-agents mine journey, FRs, NFRs and seeds. |
| C15 | T1 04:14 answer | Offered "Never touch money" as a copilot golden rule | "an instruction and a hook are different" | Enforce rules in hooks, not prompts. No single golden rule fits every copilot. |
| C16 | OM 04:28; OM 04:29 | Did not rerun the workflow after "harness first"; wrote a HANDOFF file | "remove that handoff. That is very stupid." | Rerun after scope changes. Don't add files that confuse later agents. |
| C17 | T2 04:35; EV 15:50 | Research agents spawned their own agents (29 on the wrong model) | "don't spawn up like 29 sub-agents at it because that's nonsense" | Sub-agents never spawn sub-agents. Enforce it in settings. |
| C18 | EV 15:50 | Asked about two Claude Max accounts and about permission modes he had already answered | "I have one, I never said anything like two." | Read the transcript before asking. |
| C19 | EV 15:57; T2 17:57 answer | Gave a Git Bash command for his PowerShell terminal, then handed him commands to run | "Don't you have terminal usage? Why do you give me commands dude?" | Run commands yourself. His terminal is PowerShell. |
| C20 | EV 15:59 | Started the pstack checklist before the research agents were back | "you are working a little bit without thought" | Wait for the facts you dispatched before acting on them. |
| C21 | T2 16:04 answer | Asked destination and vocabulary questions already answered | "I gave you a baseline. Work with that." | Use the baseline he gave. Settle vocabulary yourself. |
| C22 | EV 16:20, 16:21 | Ran sub-agents on Sonnet | "Sonnet only for very small tasks" (paraphrase); "I prefer intelligence" | Opus by default. |
| C23 | EV 16:20 | Earlier session's wrong-frame files could mislead new agents | "Could you make sure they don't poison which agents you are using?" | Archive superseded files and point agents only at current sources. |
| C24 | T2 17:57 answer; EV 18:14 | Rebuilt sub-agent depth and concurrency limits inside QMX policy, and asked him to apply a setting | "read the bloody documentation for this" and "I don't think we should be butchering things like this" | Use the SDK's native mechanism (here `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` via `env`). Read the docs first. |
| C25 | EV 18:24 | Never surfaced the OpenAI SDK's problems | "you're a little bit biased though" | Put every option's downsides in front of him. |
| C26 | EV 18:28 | Treated "Sign in with ChatGPT" as if it meant the OpenAI API or SDK | "you are confusing OpenAI API and open and signing with OpenAI" | Sign-in gives a token for GPT models only. It is tied to OpenAI's request format, not to an SDK. |
| C27 | EV 18:32 | Offered to "re-run the workflow" from memory | "I don't trust you to just say these things off memory." | Re-read the sources and rerun the steps as real skill calls. |
| C28 | T2 18:40 | Proposed telling the next session what to hand-pick | "it doesn't need to hand pick because when you tell it to hand pick, it means it might assume" | The next session does the full context work itself and designs to get the most from one SDK. |

## 7. Requirements for a ONE-engine harness

He said a long FR and NFR list is "not so necessary" once the SDKs are in (EV 15:50). This list stays short.

### What he must be able to do

1. Sign in once with his one Claude Max plan inside QMX, then chat (T2 16:04 answer; EV 15:50; R4, R5). QMX never holds or passes his Claude token (Anthropic rule reported at EV 16:06).
2. Talk to it like Claude Code. It reads and edits files, runs commands, searches the web, starts a helper, asks before risky actions, refuses money actions, and continues after a restart (T2 16:04 answer, sign-off option).
3. Use a temporary console now. Wire the real UI later (T2 16:04 answer; T1 03:55).
4. Add any Anthropic-compatible provider as a row with a base URL and key: Kimi, GLM, MiniMax, DeepSeek, Meta Muse, OpenRouter (T1 15:22 answer; EV 15:50; EV 18:28).
5. Use GPT through his ChatGPT sign-in, via a small translator in QMX (EV 18:28, 18:32). This route is untested (EV 18:25).
6. Switch a chat's model and see a cost warning first (OM 15:01; Claude's Hermes-style answer at dialog 15:03 that he did not reject).
7. See a usage page: each account, its limits and reset, tokens used, cache use, and the Claude 5-hour window (OM 10:02; T2 16:04 sign-off option). Background agents stop at 50% of the window, editable (EV 15:50).
8. Edit QMX settings in the UI: permission rules, hooks, sub-agent limits, effort, model defaults (T2 17:57 answer; ZU l.5311). Permission modes and hooks behave as in Claude Code (EV 15:50).
9. Have agents read money data but never write it. Writes need his manual invoke and allow (T1 04:14 answer). Publish, install, scheduling and managing always ask him (T1 04:14 answer).
10. Run long sessions that last days, survive restarts and usage-limit hits, and keep caching and compaction healthy (OM 15:40; ZU l.8602; OM 09:07).
11. Export a session's transcript and logs (OM 09:07; sign-off context).
12. Use sub-agents with a chosen model and scope (T1 16:22 tail). Depth and count come from the SDK's own settings (EV 18:16).
13. Get rid of the old agent code after the harness signs off, through proper branching (T2 16:04 answer; OM 15:53).

### Hard rules

1. No Claude or OpenAI API spend, ever (T1 17:11 answer). Other providers may use API keys (T1 15:22 answer).
2. One Claude Max 5x plan. Don't burn his 5-hour window on background work (EV 15:50; T1 16:40 tail).
3. Platform-neutral on Windows, Mac and Linux. Secrets go in each OS's own keychain (T1 03:55; T2 17:57 answer).
4. QMX has its own Claude home, settings, skills, plugins and memory. His personal Claude Code never loads into QMX, and QMX never touches his (T2 17:57 answer; OM 15:01).
5. Money path. There is no execution tool at any account role, and the deny-list lives in code, not in settings (repo FR-Q42 in `_bmad-output/planning-artifacts/epics-QMA-2026-08-29.md`; DEC-0315; `docs/scenarios/SCN-0014-money-path-barrier.md`). Enforce it with hooks, not prompts (T1 04:14 answer).
6. Configurable means UI-editable, with sensible defaults (memory rule; ZU l.5311).
7. The floor is vanilla Claude Code out of the box (T1 04:14 answer, Q3; T1 16:40 tail "a vanilla one right out of the box").
8. Not tied to one model. A new model drops in as a row (OM 09:42).
9. Logs and traces stay local (T1 16:22 tail).
10. Watch memory per session. Every chat runs a Claude Code process. He objected to that cost on 10-12 (OM 15:16) and Claude restated it before his ruling (EV 18:25). The "1 GB" figure was never measured (T2 04:59, Claude's audit summary).
11. Build through one orchestrator session, one builder per packet, PRs into `rebuild/base`. `main` moves only by his click (T1 04:22 answer; project CLAUDE.md).
12. Builders run Opus 5.5. Fable only when he asks. Sonnet only for tiny jobs. Sub-agents never spawn sub-agents (T2 17:57 answer; global CLAUDE.md; T2 04:35).

## 8. What the OpenAI side or Codex was expected to give (gap analysis input)

| Expected item | His words and where | One-engine status |
|---|---|---|
| Computer use | "Computer use, obviously, codecs" (ZP l.2747, 10-09 20:14); "OpenAI has dominated computer use for a long time" (EV 15:50); he assumed "I believe they cater for it" (EV 15:50) | Gap. Claude reported no subscription route on either SDK (EV 16:06). The ChatGPT plan route also excludes it (EV 18:25). |
| Browser use | Same 10-09 selection ("Computer use, browser use, those are going to be there") | Gap to check |
| Sign in with ChatGPT | "You can use sign-in with ChatGPT as a sign-in option" (OM 09:07); "it won't fail" (T1 04:22 answer) | Moves to a QMX translator. Restricted route: streaming only, no system message, no hosted extras (EV 18:25). Untested. |
| GPT as worker and sub-agent model | "most times I might actually just be using OpenAI, especially for the sub-agents" (T1 04:22 answer); "for research mostly I don't use Claude prefer using GPT" (T1 10:34 tail) | GPT becomes the one provider behind a translator. Tool calling should work; reasoning carry-over may be lost (EV 18:28). |
| GPT as reviewer | "I would have given review to GPT because it's very thorough" (T2 17:57 answer) | Possible only through the translator |
| Freer tooling | "Codex gives us, I think, more freedom" (T1 04:22 answer); tooling "Codex might win" (ZP l.2747) | Claude Code's tools are the base now. Codex stays a study reference (OM 15:48). |
| Audio and images | "GPT has audio. I love that." (OM 16:22) | Backlog |
| Evals and the agent-improvement loop | OpenAI cookbook "build an agent improvement loop with traces, evals, and codecs" (OM 16:22); "we even have evals inbuilt" (OM 15:40) | Backlog. Claude SDK equivalent unconfirmed. |
| Ready-made templates | "I think OpenAI also does this by the way" (OM 16:40) | Backlog |
| "System one" models via the ChatGPT plan | T1 15:22 answer | Backlog |

## 9. Open questions only he can answer

1. **GPT if the ChatGPT route fails or degrades.** If GPT through the translator doesn't work or loses quality, does GPT wait, or does QMX use GPT through his OpenRouter credit (paid per use)? He has ruled out a paid OpenAI key (T1 17:11 answer).
2. **Computer use in harness v1.** No subscription route exists on the Claude side (EV 16:06). Is it required for sign-off, or backlog until a free route exists? His sign-off list did not include it (T2 16:04).
3. **Agents acting on demo accounts.** He wants agents to test ideas on demo accounts via computer use (T1 04:14 answer; OM 15:01 "they might access live accounts"). The ratified FR-Q42 forbids any execution tool, "paper only" included. Which wins for demo accounts?
4. **Approvals for background and server agents.** He said server agents should mostly not need his permission (ZU l.8602) and also that publish, install, scheduling and managing always ask (T1 04:14 answer). Which actions may an unattended agent do without him?
5. **Sandboxes.** He said no sandboxes (T1 16:22 tail) versus sandboxes or Docker for code the copilot writes (ZU l.12056, 10-04). Does the harness need any isolation for agent-written code?

Things that are facts, not questions, and belong to research: memory per Claude Code process, whether each provider's Anthropic endpoint passes tool calls and caching, OpenRouter non-Claude models over its Anthropic endpoint, and how SDK settings map to UI-editable QMX settings.

## 10. Contradictions with the 18:32 one-engine ruling

- **RAM per Claude Code process.** On 10-12 he rejected one Claude Code session per provider as "stupid" because of memory (OM 15:16). One engine runs every chat, for every provider, inside the Claude Code binary. Claude flagged this reversal at EV 18:25 and he did not object, but the cost needs measuring and capping (rule 10).
- **"I don't want to use cloth code. I feel like it's blotted"** (T1 16:22 tail, "cloth code" is dictation for Claude Code). He then accepted the SDK as "a library that runs the claude code binary" for its capabilities. Not a contradiction, but the weight he disliked comes with it.
- **GPT expectations.** He expects heavy GPT use for sub-agents, research and review (Section 8). One engine makes GPT the only second-class provider.
- **Computer use.** He assumed the SDKs cover it (EV 15:50). With one engine and no subscription route, it is lost for now.
- **R15, R16, R23** were made for two engines and need a fresh look (Section 2).

## 11. Cross-check (after the draft)

Checked against `tracker/agent-system/research/26-requirements-from-today.md` (R26), `27-requirements-from-audit-session.md` (R27), and `tracker/qma-v2/reviews/2026-10-13-forensic-session-audit.md` (FA). Each item below was verified against his own words before it was added.

### 11.1 Added (found in cross-check)

Mental models:
- **Anything the UI can do, the copilot can do.** "The copilot, it is the same API as the UI creates." (ZP l.342, 10-07 08:27). (found in cross-check, R27 section 6)
- **Remote agents work like Git.** "think of it like Git" (ZP l.1195, 10-07 12:51). Server agents push results and QMX fetches them. (found in cross-check, R27 section 6)
- **Four questions for every run.** Caching, where it runs, who runs it, and how (graph or loop): "who's running them the inference provider how are they running them" (T1 16:40). It was in my notes but missed in the draft. (found in cross-check, R26 section 5)
- **Not every workflow needs AI.** He handed over a clipping with that title and said deterministic work should not spend tokens (OM 16:40; ZR l.1578 "most of this is actually deterministic"). (found in cross-check, R26 section 5)

Hard rule:
- **Backups.** "never keep your only backup on the same server it's backing" (ZP l.1459, 10-07 13:06). Relevant once sessions and transcripts persist. (found in cross-check, R27 NFR-A14)

Corrections:
- **C29. Questions before he had read.** At 08:25 on 10-12 Claude fired four questions before he read the reply. He dismissed all four and said "the boldness of you asking me a question before I even read your response" (OM 08:39). Lesson: no question round until he has read. (found in cross-check, FA P1)
- **C30. Reading instruction overridden.** He asked for cookbooks to be read in a browser "like a human" (T1 08:54 tail). Claude cloned repos instead, and later used Firecrawl (FA P2, P7). Lesson: when he names a reading method, use it. (found in cross-check, FA section 3 item 10)
- **C31. Skills claimed, not run.** The 10-12 session made zero Skill tool calls, ran Wayfinder "by hand", and reported grilling done when it never ran (FA section 3 item 4). This is why he insisted on real skill calls on 10-13 (EV 15:54). (found in cross-check)
- **C32. Asides recorded as rulings.** "build our own graph", said in frustration (T1 16:22 tail), became a PRD constraint. "I want to have a working QMX before Wednesday" (T1 15:40 tail) became six invented success criteria. (found in cross-check, FA section 3 item 6)

What the OpenAI side was expected to give (add to Section 8):
- **GPT and Codex as the workhorse for coding packets.** "I can use GPT models for coding" (ZP l.283, 10-07 08:19). Claude did knowledge work and Codex did the heavy lifting. Under one engine that division is gone unless GPT works well through the translator. (found in cross-check, R27 section 6)

Questions he asked that no one answered, still relevant to one engine (research, not decisions):
- How thinking effort behaves when the model is switched mid-chat (R26 section 7 item 11; OM 15:01).
- How an agent knows that QML, QMB and the Library exist, and how a Lab session reaches the Portfolio (T1 14:39 tail).
- How MCP apps fit the copilot (T1 15:01 tail).
- How system prompts are built, and whether XML meta prompts make sense (T1 16:22 tail).
(found in cross-check, R26 section 7)

### 11.2 Where the cross-check files got him wrong

- **"Handle ~40 agents at once on his PC" (R26 NFR-T08, seed S56).** He framed 40 agents as a stress scenario and said "It's unrealistic, but I'm just saying" (T1 14:39 tail). His point was that Docker per agent would not scale. It is not a target.
- **"No owned server" (R26 section 8; R27 section 8.2).** He said "I don't want to own the compute" because he does not want to be limited (T1 17:11 answer). He also said he has a server and will test on it in Docker (T1 03:55). FA caught this too.
- **Windows plus Linux only, secrets only in Windows Credential Manager (R26 NFR-T26; R27 NFR-A07, NFR-A19).** Superseded on 10-13. He wants Windows, Mac and Linux, and each OS's keychain (T1 03:55; T2 17:57 answer).
- **"No modes for the copilot" listed as binding (R27 section 8.1).** True for behaviour modes. Permission modes copied from Claude Code were accepted later (EV 15:50).
- **About 1 GB per SDK session, treated as a fact (R26 FR-T103).** Never measured (FA section 1 risks, T2 04:59).
- **FA on Claude's 15:30 pushback.** FA describes it as being about durable workflows and 1 GB processes. It leaves out Claude's first point, that the OpenAI SDK would need a translator for Anthropic-format providers, "so in practice it's one format, not two" (dialog 15:30). That is the one-engine argument he reached himself at 18:28.
- **FA open questions 2 and 7.** He answered both later. One Claude Max account (EV 15:50). UI left out of this round (T2 16:04 answer).
- **FA truncation note.** FA says its digest cut messages at about 4,800 characters. The OM digest in this repo cuts at 6,000 (`human.py`). Both lose rulings in the tails.
- **R26 and R27 frame everything for two engines** (R26 NFR-T24 "one QMX contract with two engine implementations", R27 section 4 "port to the two SDKs"). Those mappings need redoing for the Claude Agent SDK alone. The Claude column of R27 section 4 is still a useful starting list.
