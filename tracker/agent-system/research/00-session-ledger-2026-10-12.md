# Session ledger: QMX planning session, 2026-10-12

What the operator asked for, decided, proposed or worried about in the 2026-10-12 planning session, mapped onto this tracker.
Planning only: nothing here is a new decision.

**Source:** the session export (131 numbered messages; USER = operator, ASSISTANT = Claude). Two things are missing from the export and were taken from the session log:
- **[74a]**: a message he queued at 09:27, between [74] and [75].
- **[8q] and [124q]**: his answers to the two question-tool rounds (08:31, all dismissed; 15:22, answered in free text).

`[n]` means message n. "Latest wins" applies: where he changed his mind, the chain is shown with arrows.

**Status words:**
- **RATIFIED**: he explicitly chose it.
- **STATED POSITION**: he said it, but there was no formal pick.
- **PROPOSAL**: he floated it and may have withdrawn it.
- **REVERSED**: replaced by something later (shown with →).

---

## 1. Operator positions and requirements, by theme

### 1.1 Harness and engines

- **Claude Code is a harness in its own right.** QMX can't just run it untouched; that would be "an engine starting another engine". [84], [116] STATED POSITION
- **Claude Code can be a node inside the QMX system** (the Sandcastle pattern). He accepted this once it was explained. [84], [87] STATED POSITION
- **Chain: what runs QMX's agents.**
  - [72]: "I don't want to use claude code", it feels limited; he prefers his own agents.
  - → [87]: open to building on the Anthropic SDK if it can carry API keys and ChatGPT sign-in; feels Claude handles complexity best.
  - → [116]: "seems like B is where I am" (QMX engine as the base, Claude Code as one option per agent).
  - → [121]: "normal Claude Code is the baseline", with a profile per provider.
  - → [123]: running one Claude Code session per provider is "stupid" because of ~1 GB RAM each; it was "a thought", not the design. New proposal: design only for the two vendor formats, Anthropic and OpenAI.
  - → [124q]: picked "Two lanes" in the question tool.
  - → [131]: calls it his proposal again and asks whether Claude really agrees.
  - **Status: RATIFIED at [124q], reopened at [131].**
- **Two lanes, as picked at [124q].** RATIFIED, reopened at [131]
  - Subscription lane: his Claude plans, through Claude Code, with a cap on sessions.
  - API lane: QMX's own engine, speaking the Anthropic and OpenAI formats.
- **[131] reframes the lanes as "claude agent SDK and OpenAI Agent SDK".** At [123] he spoke of the two vendors' SDKs and formats. Which one he means (the agent SDKs or the wire formats) is unresolved; see §4. STATED POSITION
- **LangChain and LangGraph are "not fully out of scope"; we still need them.** If they don't fit the two-format design, he would design QMX's own engine instead. [123] PROPOSAL
- **He doesn't want Codex as a harness:** "slow and heavy", "too compact". He likes Codex's UI. [123], also [87] STATED POSITION
- **Engine and model are chosen per agent,** so he can move off Claude when Claude usage runs low (for example to Kimi K3 or GPT-6 Astra). This was his case for option C. [116] STATED POSITION, kept under two lanes
- **"Engine starting another engine" means QMX configures the Claude Code worker:** hooks, where it may write, approvals and limits flow from QMX. [116] STATED POSITION
- **No Docker by default.** It eats storage and RAM. Picture 40 agents at once on his PC; he prefers plain Python or a custom light sandbox. [116] STATED POSITION
- **Chain: Docker.** [48] floated running Claude Code via Docker → [116] no Docker by default. REVERSED
- **The backend (turn host, API, database) must work and be testable without the UI.** [116] STATED POSITION
- **One builder for every agent felt like a bottleneck to him.** Claude explained it is a recipe, not a queue; he left code-level comments to Claude. [116] STATED POSITION, answered at [118]
- **Deep Agents should run most workflows.** He wants each sub-agent's model and scope to be specific. [48] STATED POSITION
- **Keep `native_claude.py` and `native_codex.py`.** Claude surfaced this at [115]; he agreed that point 2 ("own shell bypasses hooks") and point 3 ("approvals wait inside Claude Code") matter. [116] STATED POSITION
- **Remove the leftover plan/do mode code.** He called keeping it "stupid". [116] STATED POSITION

### 1.2 SDKs and wire formats

- **Design for two formats only, Anthropic and OpenAI.** Every other provider (GLM, Kimi, MiniMax, DeepSeek) copies one of them. [123] PROPOSAL → [124q] RATIFIED as the API lane
- **What matters is "API key compatibility": a base URL plus a key,** exactly as Kimi's Claude Code page shows. [124q] RATIFIED
- **Chain: naming.**
  - [99]: "it's called claude code not agent SDK".
  - [116]: "choose one, please".
  - [119]: what happened to the Agent SDK research?
  - [131]: uses "claude agent SDK and OpenAI Agent SDK" himself.
  - **Status:** glossary rule RATIFIED [99, 116], but his own latest wording breaks it; see §4.
- **Redo the SDK research from the documentation** (core features, baselines, organogram, multiple scenarios) for the two SDKs, then redesign. [131] STATED POSITION, not started
- **Thinking modes and effort across the two formats and when switching model** need designing. [121], [123] STATED POSITION, open

### 1.3 Providers and accounts

- **Chain: API keys.**
  - [48]: "I'm not paying for those API prices".
  - → [76]: "not going to use API keys".
  - → [121]: GLM and Kimi by API key inside LangChain is "non-negotiable".
  - → [123]: "API keys are okay".
  - → [124q]: coding plans by "API keys only... design based off the SDK".
  - **Status: REVERSED.** Claude stays on the subscription; other providers use keys.
- **Single providers he named:** GLM, MiniMax, Kimi, DeepSeek; DeepSeek's endpoints are uncertain. [124q] RATIFIED. (Ticket 02 also lists GPT and Claude on the API lane; that is Claude's addition, see §4.)
- **Pools are a different shape:** OpenRouter, Ollama Cloud, OpenCode Go/Zen. [68], [121], [124q] STATED POSITION
- **No Grok. Gemini possibly, for a Library agent.** [124q] STATED POSITION
- **Later: "System 1" models (for example JEV) and voice/conversational mode.** [124q] PROPOSAL (parked)
- **He will mostly use Claude and GPT.** [84], [123] STATED POSITION
- **GPT through "Sign in with ChatGPT"** needs reading the docs to implement. [48], [121] STATED POSITION
- **Several subscriptions on one QMX:** for example two Claude accounts, one GPT, one Kimi. [72], [84] STATED POSITION
- **He'll buy whatever plan tier suits his work.** Don't ask about plan tiers. [123] STATED POSITION
- **Each provider has its own harness** (Kimi CLI, GLM's, MiniMax's, Codex). He knows; it doesn't change the design. [123] STATED POSITION
- **Don't limit the provider list.** Each provider is a row you can add or remove. [124q] RATIFIED

### 1.4 Router and usage limits

- **A router that load-balances across accounts and providers is the missing piece.** [72] STATED POSITION
- **Chain: what the router optimises for.** Claude proposed "cheapest model that can do it" [73] → [74a]: "I don't want just cheap I want capable". RATIFIED by correction
- **Router duties:** availability, limits, usage resets, usage counts, thinking modes and routing. [123] STATED POSITION
- **Claude gets its own routing (through Claude Code); other providers go through QMX's router.** [84], [99] STATED POSITION
- **A usage page in the T3 Code style:** tokens, who is being used, limits, a graph. Screenshot given. [87], [88] STATED POSITION
- **QMX enforces its own limits:** refuse to start a new session and show an error card. [121] STATED POSITION
- **Switching model mid-conversation is allowed, with a cost pop-up.** The old cache belongs to the old provider. Copy how OpenCode and Hermes do it. [121] STATED POSITION (Claude withdrew its "never switch" rule at [122])
- **Caching is the top priority:** "Please, I beg you, focus on it a lot". [48] STATED POSITION

### 1.5 Subscriptions and terms

- **Chain: Claude subscription route.**
  - [13]: CLIProxy for the Claude subscription.
  - → [48]: find a community way; Pi has a Claude proxy; ban risk is low outside the US.
  - → [74a]: pooling accounts is rarely banned.
  - → [84]: route Claude specifically through its own SDK, on the subscription.
  - → [116]: Claude through CLIProxy "is easy to change... we already agreed to change it".
  - **Status: REVERSED.** Claude reaches QMX only through Claude Code.
- **Pooling accounts is common and rarely punished** (Theo's video). The risk lies in the custom harness, not in pooling. [74a], [76] STATED POSITION
- **"We are not going to use API keys" for Claude.** [76] STATED POSITION. This is still the reason Claude stays on the subscription lane.
- **Coding plans:** "don't mind about it... just look at the documentation". [124q] RATIFIED (API keys only)
- **Live accounts may be used to test** (the cTrader/MT5 scenario). He won't trade live money from agents. [121] STATED POSITION

### 1.6 Organogram and copilots (main, Lab, Portfolio, mini apps)

- **Two agent types:** copilots and workflow agents. [13] STATED POSITION
- **The copilot organogram:**
  - a general copilot like Codex or Claude Code, versatile for daily use;
  - Lab: research, analysis, coding, building workflows; the heaviest;
  - Portfolio: risk, sizing, optimisation;
  - any copilot can host any conversation.

  [13] STATED POSITION; [15] "up for discussion"; [103] "might need to enhance it"
- **The Lab is about 80% of the platform:** mini apps, workflows, long experiments and research. [15] STATED POSITION
- **Portfolio is closely connected to the Lab.** [15] STATED POSITION
- **The long-running "project" thing must connect everything.** Research found it is called an "errand" in the UI. [15] STATED POSITION
- **Cross-surface reach:** from the Lab use Portfolio things; from the main chat reach both; the copilot knows which surface it is acting on. [116] STATED POSITION
- **Tools, hooks and permissions are split along the organogram.** [13] STATED POSITION
- **Copilots build, maintain, open and edit mini apps, workflows, widgets and plugins.** This was the question that started the redesign. [116] STATED POSITION
- **A lead agent on one provider with sub-agents on another,** for example a GPT research lead with Claude doing the heavy work. [99] STATED POSITION
- **He doesn't want Claude to hard-code model roles** ("research sub-agents go to Kimi" was too specific); design a freer harness. [84] STATED POSITION

### 1.7 Workflows and the Lab

- **Workflows can be deterministic, agentic, or any mix.** They have typed inputs and outputs and feed and are fed by other workflows, mini apps and widgets. [116] STATED POSITION
- **The Lab isn't only agents.** [116] STATED POSITION
- **Runs can last up to days.** [116] STATED POSITION
- **Chain: Claude in workflows.** [116]: the simplest option is no Claude in workflows → [121]: Claude often drives or orchestrates long workflows, with GPT/GLM doing the work → [123]: but not one 1 GB Claude Code session per step. STATED POSITION, open (how a Claude driver runs cheaply)
- **Dynamic workflows like Claude Code's, but saved and specified.** [123] PROPOSAL
- **WF1 and WF2 deserve their own discussion.** They are tied to the risk and sizing session. Add them to the backlog; he handles them. [48], [87] RATIFIED
- **The Lab's built-in research harness.** The August one (Open Research, Delphi) may have been overkill; maybe design a new one. Some of it is shipped; enhance it. [15], [87] STATED POSITION
- **For research leads he prefers GPT ("thorough"); Claude for heavy work.** [99] STATED POSITION

### 1.8 Tools and the Library

- **Every agent's baseline is Claude Code's own capability:** terminal, Python, files, web, CLI tools, video watching, computer use. [87] STATED POSITION
- **Hooks decide where things are written** (for example strategies), so the UI never becomes a mess. [87] STATED POSITION
- **Tools are mostly local QMX code, not MCP.** MCP is acceptable for browser and computer use. [87] STATED POSITION
- **The Library is a database.** He wants a Library v2; the UI gave a better picture of it. [87], [92], [116] STATED POSITION
- **Storage buckets and data access need design.** [87] STATED POSITION
- **Brokers connect in Settings, mostly through trading platforms.** [87] STATED POSITION
- **Browser use with logged-in sessions,** for example TradingView. [87] STATED POSITION
- **Firecrawl, including Alexandria,** for web and documentation work. [87] STATED POSITION
- **Agents must know QML, QMB, QMF and the Library exist** (tools, SDKs), read and parse data, and confirm writes landed. [116] STATED POSITION
- **Two agents must not edit the same Library item at once.** [116] STATED POSITION
- **"MCP apps" were discussed in the UI session and need more talk.** [121] STATED POSITION, open
- **Codex is open source; look at its tools.** [13] STATED POSITION

### 1.9 Memory and self-improvement

- **Memory is pluggable, like Hermes.** He wants to test several (Hindsight, Mem0, LangChain's) before choosing; different agents may need different memory. [13] STATED POSITION
- **Self-improvement: "don't repeat Wednesday's mistake".** Save specific ways of doing things, including procedures learned from computer use. He leaves the method to Claude, with Hermes as the lead reference. [87] STATED POSITION
- **Skills aren't bad; how they are shaped is the problem.** [13] STATED POSITION
- **Agent as a folder** (Eve, LLM wiki, OKF; LangChain has its own OKF-like format). He asked for Claude's take. [13], [15] STATED POSITION
- **How memory and RLM are handled under the new design.** [87], [116] STATED POSITION, open

### 1.10 Context, caching and compaction

- **Compaction in the Anthropic style, automatic.** "I wanted to have automatic compaction". [87] STATED POSITION
- **Claude has the best hooks, compaction, caching and sub-agent design.** [87] STATED POSITION
- **On a model switch, compact if the new model's window is smaller** (the Hermes pattern). [121] STATED POSITION (via Claude's summary at [122])
- **"What are you using for compaction?"** [103] STATED POSITION, answered only in passing

### 1.11 Approvals, hooks and money path

- **The money-path block is ideal.** But agents may touch live accounts to test things. [121] STATED POSITION
- **He decides approvals and tool access; Claude can handle sessions, caching, server agents and cron.** [92] RATIFIED (in map.md as who-decides)
- **No modes.** He confirmed modes were dropped "for a reason". [116] STATED POSITION (carried rule)

### 1.12 Sessions, servers and placement

- **Server agents export their transcript and logs automatically:** what happened, how and why. [48] STATED POSITION
- **Cron in the Hermes style.** [87] STATED POSITION
- **Run sessions on a Contabo Linux server** to lift the RAM ceiling: "make our own Sandcastle". [121] PROPOSAL → [124q] RATIFIED "design now, ship after local"
- **Server design must cover:**
  - logs from both SDKs (the DevOps lens);
  - buckets;
  - agents editing the same files;
  - how it all renders in the UI.

  [124q] RATIFIED
- **Other places to run:** AMP Code orbs, Railway ("might be the better one"), Modal, E2B. P17 and P21 already designed parts. [123] PROPOSAL
- **Linux runs agents smoother; Windows has the aesthetics.** He asks whether the code differs. [123] STATED POSITION, open
- **The server may be mostly a database; refactor the database for agents.** [123] PROPOSAL
- **Cap the number of Claude-based sessions,** because each uses ~1 GB RAM. [121] STATED POSITION

### 1.13 Logs and the DevOps lens

- **A DevOps lens is needed:** logs, traces, proof that writes landed. Partly to see the damage from P16. [116] STATED POSITION
- **The DevOps lens for mini apps was "talked about", never in depth.** [116] STATED POSITION, open
- **The UI hides most logs.** People "don't want to see the logs". [87] STATED POSITION
- **LangSmith is not used.** [87] STATED POSITION

### 1.14 Concurrent edits and git variants

- **When agents edit the same files, use git branches.** Both versions are often needed for comparison. [124q] RATIFIED (as a design requirement)

### 1.15 UI expectations

- **The chat should feel like this Claude Code session:** previous and running sessions, running sub-agents, tool calls, the computer-use cursor moving. [87] STATED POSITION
- **Consider the UI in every decision,** including the organogram and model selection ("everything has to make sense"). [15] STATED POSITION
- **Usage page like T3 Code** (see 1.4). [87] STATED POSITION
- **The UI ships first as a browser app** so agents can click through it; the desktop wrapper comes later. [101] RATIFIED via [102]/[103]
- **UI wiring gets its own session later.** The Lab and Portfolio backend needs material from the UI session. [103] RATIFIED
- **The right-hand panel (terminal and similar)** changes if MT5 and cTrader live inside QMX. [13] STATED POSITION
- **Hope for a working QMX "by tomorrow".** [101] STATED POSITION (aspiration)

### 1.16 Computer and browser use (cTrader, MT5)

- **Scenario:** watch a video (or have a sub-agent watch it), then try the pattern in cTrader through computer use. [15], [87] STATED POSITION
- **CFDs are not new.** cTrader was connected before. Crypto via CCXT. cTrader also gives news. Don't read the other session. [15] STATED POSITION
- **QMX-specific browser and computer use, not Claude Code's own.** Look at OpenCUA. [13], [84] STATED POSITION
- **Computer use is "a simple one":** agents should click through cTrader or MT5 by default. MT5 isn't installed. [87] STATED POSITION
- **Use those apps inside QMX** so he needn't open them separately: an all-in-one. [87] STATED POSITION

### 1.17 Skills, system prompts and plugins

- **QMX-only Claude Code settings, skills and plugins, never mixed with his personal Claude Code.** [84], [121] STATED POSITION
- **Plugins per surface:** a Lab plugin, a Portfolio plugin. [121] STATED POSITION
- **He doesn't intend to use Claude Code plugins himself; skills maybe.** [121] STATED POSITION
- **Skills and system prompts haven't been discussed yet.** [92] STATED POSITION (ticket 15)
- **Use pstack's automate-me and skill playbooks** to turn his rough descriptions into QMX skills and workflows. [97] PROPOSAL

### 1.18 QMB, QML, QMF, QMN and P16 damage

- **QMB's original intent:** a tamper-proof backtest command-line tool that agents call like a search tool. It combined Lean CLI, Jesse and others. Many models have since altered it. He will retrieve the old sessions; it ships later, once QMX is in normal use. [116] STATED POSITION
- **Find out what still works after P16:** QMA and mini apps are the most affected; QML, QMF and QMN may be too ("everything was connected"). [116] STATED POSITION
- **P16b/P16c go to Codex while its quota lasts, then a Claude session.** [13], [72] STATED POSITION (done)

### 1.19 Process and workflow rules

- **Stop vibe coding; use a structured method.** [4], [131] RATIFIED
- **Wayfinder first, not grill-me.** [13] RATIFIED
- **Install pstack.** [13], [97] RATIFIED (installed at [98])
- **Pocock organises; pstack gives depth:** how, why, architect; interrogate perhaps; technical writing; not arena or swarm. [97], [99] STATED POSITION
- **Don't follow skills to the letter: "have more freedom".** [92] RATIFIED (in map.md)
- **Order the skills; stop "randomizing".** [99] STATED POSITION (answered by workflow.md)
- **Chain: grilling and domain-modeling.**
  - [99]: Wayfinder should have grilled him.
  - → [131]: "grilling and domain modeling, I don't think we need them here".
  - **Status: PROPOSAL** (for ticket 02 at least).
- **Redo `/how` because ticket 02 was reshaped. If a step was skipped, pause and go back. Re-invoke Wayfinder for structure.** [131] STATED POSITION, not done
- **A sub-agent reads the whole session transcript to find what was missed** (this file). [131] RATIFIED
- **Decisions go through the AskUserQuestion tool, each with a recommendation.** [103] RATIFIED
- **But don't ask before he has read; don't ask when his last message isn't processed.** [13], [124q] STATED POSITION
- **"Don't assume I've read it":** when agents finish before he replies, only acknowledge. [48] RATIFIED (memory)
- **Chain: sessions.** [100]: Claude proposed a fresh session → [101]: planning stays in this same session, compacted. RATIFIED
- **Shipping runs in an external session while planning continues:** one orchestrator or one agent per slice. [103] RATIFIED
- **Chain: when shipping starts.** [92]: no code shipping now → [101]: ship each slice as soon as its decisions are made → [123]: "might just ship this today". STATED POSITION
- **Chain: parallel shipping.** [99]: sequential, parallel possible overnight ("seven tickets") → [103]: one agent or an orchestrator. STATED POSITION
- **Subagent cost rules:**
  - few subagents; Opus 5.5 or Sonnet 5.5; background only;
  - none that pause midway (the cache lasts ~10 min) [1];
  - no nested sub-agents [74a];
  - research on Opus 5.5 at medium effort [15].

  RATIFIED
- **Loosening:** "we have a lot of usage... put it to good use", because P16c is mostly waiting. [131] STATED POSITION
- **Research lives in the repo, not on D:.** [48] RATIFIED
- **Fresh research from primary sources, not the old session's summaries.** [15] RATIFIED
- **Read cookbooks and articles "like a human",** almost every article. [15] STATED POSITION (partly done, see §3)
- **Design for complexity:** handle load before it arrives, and bring up what he wouldn't consider. [87], [103] RATIFIED (map.md)
- **Answer research-shaped questions yourself; "what do you need from me?"** [121], [123] STATED POSITION
- **Give your own opinion; don't just agree.** [131] STATED POSITION
- **Update the documentation over time.** [92] STATED POSITION (backlog)
- **Reading time:** he dictates for 10-15 minutes and needs time to read. [13], [24] STATED POSITION

### 1.20 Anything else

- **Context7 was re-signed; the GitHub plugin is offline.** [15] STATED POSITION. (The GitHub MCP still fails today.)
- **Messaging between sessions:** he wants the UI session and this one to talk without him. [13] STATED POSITION (Claude said yes)
- **His Codex subscription ended on 2026-10-12;** shipping moves to Claude. [13], [72] STATED POSITION
- **"Please tell me you don't have to pay for LangChain"**; otherwise consider Mastra. [48] Answered: free (MIT) [86]

---

## 2. Questions he asked that were never answered (or got one line while he wasn't reading)

**Morning (09:00-10:10, "acknowledge only" period)**
1. "Which model goes where, how do I select, do we have defaults?" [15]. `models-routing.md` has per-role defaults (all on API keys), but they were never shown to him.
2. "Agent as a folder: your actual take?" [15]. He got an early "yes" with a caveat [16]; the promised confirmation after the Eve research never came.
3. "Can you click through the cookbooks like a human while I look?" [15]. The repos were downloaded instead; he was never told the live browsing didn't happen.
4. "How do we wire Claude Code inside QMX without it being Claude Code verbatim?" [48]/[84]. Answered in principle at [86]. The concrete plumbing (QMX's own browser and computer use, how OpenCUA compares with cua-driver) was never discussed. He asked "we need to know how you're going to build them" at [87].
5. "Do you know what it means to port all these sessions via the UI?" [68]/[72]. Answered with one paragraph on errands [71].
6. "Are we using the Agent SDK or Claude Code? Why not build our own harness with the SDK, which I'm certain allows API keys and ChatGPT sign-in?" [87]. One-line reply ("that's ticket 01") [91]. The claim that the SDK carries API keys and ChatGPT sign-in was never directly confirmed or refuted for him.
7. "How does the Claude Agent SDK handle RLM?" [87]. Never answered. At [118]: "RLM... not built yet".
8. "Bring pstack in now or for shipping?" [92]. Answered [93], then changed at [98].
9. "What are you using for compaction?" [103]. Not answered in that reply. The [120] table gives it indirectly.
10. "Find my backlog, not only the UI backlog" [103]. Promised at [104]; never done.
11. "How did huge companies handle tools and database connections?" [103]. Never answered.

**Claude's own questions that he never got to answer (dismissed or skipped)**
12. The [8q] round, all dismissed and never re-asked:
    - small first version vs the full design (graders, goal controller, curator, steward);
    - which actions always ask him;
    - effort set automatically vs a dial;
    - CLIProxy disguise on or off.
13. "What is the one rule the Copilot must never forget about how you work?" [7]. Never asked again.
14. "Change the global `~/.claude/CLAUDE.md` bulk-worker line (Opus 4.8)?" [3]. No answer, and the line still says Opus 4.8.
15. "Is the destination right?" [86]. Implicitly accepted when he typed /wayfinder [87], but never confirmed.
16. "Which accounts to begin with, how many Claude plans?" [122]. He refused the question at [123]/[124q]; the number of Claude accounts is still unknown.

**Afternoon and evening**
17. "How do we handle thinking modes when switching model mid-conversation?" [121]. Not answered. It was sent to the architect agent, which was killed.
18. "MCP apps: we were meant to talk about that more" [121]. Not answered.
19. "How are we accepting MCPs and plugins?" [121]. Half answered: QMX gets its own home folder and plugins [122].
20. "What does QMA do exactly? Is it deeper?" [123]. One line [124].
21. "Someone must have done this; look up which frameworks" [123]. One line ("Hermes does exactly that") [124].
22. "Does the code differ between Windows and Linux?" [123]. Not answered.
23. AMP Code orbs, Railway, Modal and E2B vs Contabo [123]. Not answered (architect killed).
24. "Refactor the database to be usable for agents?" [123]. Not answered.
25. "The Lab's complexity should have been handled by the mini apps?" [116]. Not answered (ambiguous dictation).
26. "Are you really agreeing with my two lanes? Give your opinion" [131]. Not answered; the session ended.
27. "Where do how and why come in? Redesign the workflow" [131]. Not answered.

---

## 3. Things he raised that are on no ticket or backlog line

| # | Item (message) | Where it should go |
|---|---|---|
| 1 | The operator's own backlog, beyond the UI backlog [103] | backlog.md, new line: "locate and merge" |
| 2 | MCP apps from the UI session [121] | ticket 18 (and 11 for rendering) |
| 3 | Thinking modes and effort per format, on model switch, auto vs dial [8q], [121], [123] | ticket 06 (router) and ticket 10 |
| 4 | DevOps lens for mini apps [116] | ticket 18; also the backlog post-deletion check |
| 5 | Database refactor for agents; the server as mostly a database [123] | ticket 09 |
| 6 | Windows vs Linux differences for agents [123] | ticket 09 |
| 7 | Run targets: Contabo, Railway, Modal, E2B, AMP orbs; P17/P21 reuse [121], [123] | ticket 09 (only ticket 02 lines 73-77 mention the server lane) |
| 8 | Live accounts used for testing [121] | ticket 07 (ticket 02 line 58 says "goes to 07"; ticket 07 not updated) |
| 9 | Provider list, pools, Gemini Library agent, no Grok, DeepSeek endpoints [121], [124q] | ticket 06 (only in ticket 02 lines 66-71; ticket 06 not updated) |
| 10 | QMX-only Claude Code home, settings, skills; Lab and Portfolio plugins [121] | ticket 15 and ticket 13 |
| 11 | Mid-conversation model switch with a cost pop-up [121] | tickets 06 and 10 (both still say one model or account per thread) |
| 12 | QMX enforces limits: refuse a new session with an error card; own usage count fills the 20-70% gap [121], [122] | ticket 05 follow-up, or ticket 06 |
| 13 | Watchdog for Claude Code sessions that freeze with no terminal [122] | ticket 09 |
| 14 | Cap on sub-agent depth (from `/how`, [115]); he agreed the findings matter [116] | ticket 03 or ticket 07 |
| 15 | Per-role model defaults and the model picker UI [15] | ticket 06 |
| 16 | Voice/conversational mode; System-1 models (JEV) [124q] | backlog, new line (later) |
| 17 | automate-me ("mubarak-mode") and pstack skill playbooks to author QMX skills [97] | ticket 15 |
| 18 | Use technical-writing to upgrade the documentation-factory skill [99] | backlog line "Documentation update" |
| 19 | Update the project `CLAUDE.md` pipeline text and the global `CLAUDE.md` bulk-worker line [3], [7], [100] | backlog, new line (today only noted in workflow.md line 38) |
| 20 | First-version scope: small core vs full machinery [7], [8q] | ticket 16 |
| 21 | The one rule the Copilot must never forget [7] | ticket 08 or ticket 15 |
| 22 | UI browser-first, desktop wrapper later [101] | backlog line "UI wiring" (not stated there) |
| 23 | Research gaps: ~20 cookbook notebooks, the Anthropic engineering posts, Codex docs on hooks, skills, automations and memories (cookbooks hand-back, [82]); live browsing [15] | new research ticket, or inputs to tickets 07, 10 and 15 |
| 24 | OpenCUA vs cua-driver [13], [84] | ticket 12 (and 04) |
| 25 | News and crypto data (cTrader news, CCXT) as agent tools [15] | ticket 04 |
| 26 | Two-SDK study from the docs: Claude Agent SDK and OpenAI Agents SDK, their core features, baselines, organogram scenarios [131] | new ticket (research), blocking a redo of ticket 02 |
| 27 | Redo `/how` (and run `/why`) on the reshaped ticket 02 [131] | ticket 02 |
| 28 | Re-run Wayfinder over the reshaped map; revise workflow.md order [131] | map.md and workflow.md |
| 29 | Glossary words promised at [127]: lane, format, provider, pool | glossary.md |
| 30 | Read the P16c final summary and carry the leftovers into the plan [111], [113] | backlog line "P16c" (trigger exists; no owner or step) |
| 31 | Sessions talking to each other (UI session and planning session) [13] | ticket 16 |
| 32 | A Claude-driven coordinator without a 1 GB session per step [121], [123] | ticket 17 |

---

## 4. Contradictions

**Between the tracker and his latest statements**
1. **`map.md` line 35:** "One ticket per session". But [101] and [103] say planning stays in this one session, compacted. Workflow.md line 48 agrees with him; the map doesn't.
2. **`map.md` line 37 and `workflow.md` line 12:** grilling and domain-modeling on every operator ticket. At [131] he says they aren't needed here.
3. **`workflow.md` line 14:** `/architect` only for tickets 04, 08, 11 and 13. It was used for ticket 02 [127], and the order of how, why and architect is now disputed [131].
4. **`workflow.md` line 38:** "BMAD: not needed". Against this:
   - the project `CLAUDE.md` makes PRD plus Architecture via BMAD mandatory;
   - Claude's own table at [98] listed `/bmad-architecture` then `/documentation-factory`;
   - he raised BMAD architecture as "thorough" at [97].
5. **`tickets/16-shipping-plan.md` line 15:** "Pocock for planning and specs, pstack for shipping". At [97] and [99] he uses pstack for planning depth too.
6. **`tickets/02-harness-choice.md`:**
   - **Line 44:** "The operator pays no API keys". Superseded by the API lane on keys ([123], [124q]).
   - **Line 48:** "Never mid-thread". Replaced at line 57, but both lines still stand.
   - **Lines 55-56:** coding plans run inside the Claude Code engine; Claude Code is the baseline with per-provider profiles. He withdrew this at [123] ("it was a thought"), and line 72 says "Coding plans: API keys only".
   - **Line 15 and line 38 (keep `native_codex.py`):** Codex as a swappable worker. At [123] he says he doesn't want Codex ("slow and heavy").
   - **Line 63:** "Two lanes: RATIFIED". At [131] he calls it his proposal and asks whether Claude really agrees. Treat it as ratified-but-reopened.
   - **Line 67:** lists "GPT, Claude" as single API-lane providers. His answer [124q] named GLM, MiniMax, Kimi and DeepSeek. Claude on an API key conflicts with "not going to use API keys" [76].
   - **Line 66 vs [131]:** "Anthropic Messages and OpenAI" formats, but [131] says "claude agent SDK and OpenAI Agent SDK". These are different things (wire format vs agent runtime), and the cookbooks research advised against the OpenAI Agents SDK as a runtime. Needs a direct question.
7. **`tickets/06-accounts-and-router.md` line 17:** "one model per thread". He wants mid-conversation switching with a cost pop-up [121].
   - Line 19 still frames the Claude proxy route as his open risk call; he says dropping CLIProxy for Claude was "already agreed" [116].
8. **`tickets/10-context-caching-compaction.md` line 16:** "Sticky account per thread". This conflicts with the switching rule above (it holds for accounts within one provider, not across providers).
9. **`tickets/07-approvals-and-hooks.md` lines 13-17:** no mention of live-account testing, although ticket 02 line 58 routes it there.
10. **`tickets/12-ctrader-screen-automation-spike.md` line 8:** "Operator runs the checklist". At [87] he expects agents to click through cTrader themselves and calls it "a simple one".
11. **`glossary.md` line 7:** never say "Agent SDK". He himself now uses "Claude Agent SDK" and "OpenAI Agent SDK" as design terms [119], [131]. The ticket 02 title (line 3) also says "Agent SDK".
12. **`map.md` line 49:** tools mostly local QMX code, not MCP. Claude's diagram at [86] put every tool behind MCP, and [71] relied on the P11 MCP tool server. Ticket 02 line 49 says in-process tools.
13. **`map.md` line 23 vs the memory index:** the memory index line "Agent-system map" says "planning-only until ticket 16"; the map says slices ship as soon as decided.
14. **`backlog.md` line 11:** "Install it selectively before shipping starts", in the same cell as "Installed 2026-10-12".
15. **`tickets/17-lab-workflow-engine.md` line 21:** "Claude not required". At [121] he says Claude may often drive long workflows. This is compatible, but the default-model question has shifted.

**Between his own statements**
16. **API keys:**
    - [48] and [76] (no API keys);
    - vs [121] (GLM and Kimi by key is non-negotiable);
    - vs [124q] ("not an API key... API key compatibility").
    
    Latest: keys for non-Claude providers, the subscription for Claude.
17. **Claude Code:** [72] (don't want it) vs [121] (it's the baseline) vs [123] (a session per provider is stupid). Latest: subscription lane only.
18. **Claude in workflows:** [116] (simplest without Claude) vs [121] (Claude often drives).
19. **Planning before shipping:** [92] (plan first, no shipping now) vs [123] ("we might just ship this today").
20. **Testing profiles:** he rejected Claude's plan to test non-Claude profiles ("you don't need to test", [123]). Yet ticket 02 line 51 still asks to measure RAM and isolation before ratifying. Those are different tests, but the line should say so.
21. **Global `~/.claude/CLAUDE.md`:** bulk-worker pinned to Opus 4.8. This conflicts with his 2026-10-12 rule of Opus 5.5 or Sonnet 5.5 only [1].

---

## 5. Claude's mistakes he called out (process lessons)

1. Never ask a question before he has read the answer [13], [8q].
2. When agents finish before he replies, only acknowledge; never act as if he read it [48].
3. A sub-agent never spawns sub-agents. Eleven helpers on one researcher burned half his usage [74a].
4. When he says stop, stop every running helper at once; don't leave old ones running [76].
5. Don't pick "cheapest". He wants capable models, so the copilot doesn't have to redo work [74a].
6. Don't hard-code model roles ("research goes to Kimi"); design a free, model-agnostic harness [84].
7. Pooling accounts isn't the ban risk; the custom harness is. Check his video before lecturing on terms [74a], [76].
8. Wayfinder without grilling is wrong: "you didn't ask me any questions" [99].
9. Don't suggest a fresh session when compaction works; he refuses to re-explain [101].
10. Use one word for one thing. Mixing "Claude Code" and "Agent SDK" confused him [99], [116].
11. "We can't use claude code verbatim": he had said so in the morning, and Claude rediscovered it as a "finding" [116].
12. After compaction, re-read the morning research before answering. One-line acknowledgements were not answers [119].
13. Don't call documented, widely used features "unsupported", and don't propose testing what the official docs show [123].
14. Don't take a passing thought ("a session per model") as a design proposal [123].
15. Don't ask trivial questions (plan tiers, account counts); answer research-shaped questions yourself [123], [124q].
16. Don't ask before his last message is fully processed into the design [124q]; Claude admitted this at [125].
17. Give your own opinion. Don't be "just agreeable" [131].
18. If a workflow step was skipped, pause and go back. Don't continue and footnote it [131].
19. Running in circles is vibe coding; keep to the structure (map, workflow) [4], [131].
20. Don't rely on old-session summaries; do the fresh research yourself [15].
21. Don't stick to a skill's letter, and don't make research tickets out of things that don't need them [92].

---

## 6. Timeline

| Time (UTC) | Phase |
|---|---|
| 08:13-08:31 | Resumed the old product-audit session. P16b found merged but small. Pocock vs pstack chosen. The premature question round was dismissed [1]-[13]. |
| 08:37-08:56 | Long dictations on the agent system and organogram. P16c prompt written for Codex. Six background researchers started [13]-[16]. |
| 09:00-09:36 | Researchers report back. Rules set: "acknowledge only", research in the repo, no nested sub-agents. Claude-subscription terms covered. Router idea. Theo's video re-read [17]-[83]. |
| 09:42-10:10 | Sandcastle; the "engine inside an engine" worry answered. Wayfinder map charted with 14 tickets; research tickets 01 and 05 fired [84]-[91]. |
| 10:15-10:45 | pstack brought in and installed. workflow.md, who-decides, backlog. Terms agreed: same session, question tool, external shipping session [92]-[104]. |
| 10:46-14:10 | Compaction; break. The P16c Claude session runs (5 of 13 PRs merged by 14:12) [105]-[111]. |
| 14:12-14:47 | `/how` on the current runtime. B vs C; he leans B. Glossary; tickets 17-18; backlog items. Revised two-engine B after re-reading the research [112]-[120]. |
| 15:01-15:24 | Kimi docs, Contabo, mid-conversation switching. Two-format proposal; two lanes, API-compatibility and design-now-ship-later picked in the question tool. Architect agent launched [121]-[125]. |
| 15:24-15:28 | `/why` skip noticed. He kills the architect and stops Claude. He demands this ledger, a redo of `/how`, a two-SDK doc study, a Wayfinder re-run and Claude's honest opinion [126]-[131]. |
