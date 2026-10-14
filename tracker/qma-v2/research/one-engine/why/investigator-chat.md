# /why investigator: the chat record (two-engine origin)

Question: why does the 2026-10-13 QMA v2 design have its shapes, and which shapes exist only because of the two-engine choice (OpenAI Agents SDK + Claude Agent SDK) or a compromise between the two? What did the operator expect from the OpenAI side and Codex?

All times are UTC (the operator's local time is UTC+3). Citations use these short names:
- **DLG** = `tracker/qma-v2/trail/sources/2026-10-12-13-session-dialog.md` (line numbers)
- **OPS** = `tracker/qma-v2/trail/sources/2026-10-12-13-session-operator-messages.md`
- **EVE** = `tracker/qma-v2/trail/session-evening-dialog.md`
- **SUB** = `tracker/qma-v2/trail/sources/2026-10-12-13-session-subagents-index.md`
- **BRF** = `tracker/qma-v2/trail/agent-briefs.md`
- **ASK** = the operator's AskUserQuestion answers, taken from the full transcript `transcript.jsonl` in `session-export-1791865801044.zip` (session 19014dde). The digests leave these answers out.

## Source

The chat record. This covers the operator's planning conversations with Claude on 2026-10-12/13 (session 19014dde, 08:13 on 10-12 to 04:30 on 10-13) and on the evening of 2026-10-13 (session 2cf20068, 15:50 to 18:37), plus the briefs Claude gave its sub-agents.

## What I Searched

- Read OPS in full (52 operator messages). Re-read in full every message the digest cut at 6,000 characters, using DLG or the raw transcript: 09:07, 09:20, 14:39, 15:01, 15:16, 15:40, 15:48 and 16:22 on 10-12.
- Read DLG lines 560-1450 and 1810-2650 in full, which cover every Claude reply from 09:09 to 17:33 on 10-12. Read the rest of the Claude replies (17:33 on 10-12 to 04:29 on 10-13) as an extract. Read DLG 3766-3939 in full. Read the agent hand-backs for Ticket 01/05, `/how` for ticket 02, the ledger, the design A/B/synthesis and the overnight reviews.
- Grep over DLG, OPS, SUB, BRF and EVE for: `two engines|two-engine|two harness|two lanes|two SDKs|both SDKs|both engines|either engine`, `translat`, `litellm`, `freedom`, `parity`, `codex`, `sign in with chatgpt|chatgpt`, `one engine`, `same tools`, `share`.
- Extracted all five AskUserQuestion results from the raw transcript with a script: 08:25, 15:17 and 16:43 on 10-12, and 03:59 and 04:15 on 10-13.
- Read EVE lines 1-120 (skipping the pasted skill bodies at 119-530) and 532-1197 in full.
- Read BRF briefs 1, 4 and 13-18. Read SUB briefs for Ticket 01, `/architect` (15:24), the Two-SDK study (15:41), the PRD merge (17:36), the plain explainer (04:15) and the Harness baseline (04:24).
- Opened HARNESS.md only to learn what each shape is called (headings and the "both engines" lines). I did not read it for motivation.
- Not read: `tracker/qma-v2/archive/`, RESUME-2026-10-14.md, decisions.tsv and the research docs (19-two-sdk-study, 01-agent-sdk-capability-audit, FRAME.md, BASELINE.md body). These belong to the documents investigator.

## Direct Evidence Found

### (1) When two engines were first proposed, by whom, and why

The phrase "two engines" names three different pairs over 36 hours. Only the third pair is the OpenAI Agents SDK + Claude Agent SDK.

**1a. First "two engines" (Claude, 10-12 09:09): Claude Code for the copilot, LangGraph for workflows.**
- **What it says:** "**What it changes:** QMX would run two engines under one UI, Claude Code for the copilot and LangGraph for workflows. The UI then needs one common event format so both look the same."
- **Where:** DLG:617
- **Author and date:** Claude, 2026-10-12 09:09:06
- **Stated reason:** the Anthropic terms (DLG:603-606). The subscription is allowed only inside unmodified Claude Code ("Not allowed: an app taking your Claude login tokens and sending requests itself"), and "Your own copilot fits that. A server farm of background agents on your subscription doesn't." Background and server agents would run on Deep Agents with cheap models, "Or GPT through Sign in with ChatGPT, which OpenAI allows for open-source and locally hosted apps" (DLG:612-614).
- **Relevance:** Claude introduced the two-engine idea, and its reason was subscription terms, not providers. GPT through ChatGPT sign-in first appears here, as Claude's suggestion and as part of the non-Claude lane.

**1b. Earlier operator seed of a vendor split (10-12 09:42).**
- **What it says:** "the harnesses this is where now things get interesting the harnesses it's more so the same split Claude has a very specific way of doing things okay and I think we can do it via SDK yeah then GPT obviously the same way just you get the idea I believe that okay DPT does its own thing ... OpenAI has almost no problems they have already literally given us the sign-in chat GPT option the problem is coming in with Claude so my proposal is that middleware where ... if I propose to use claude it now has a specific way of routing through claude so use the sDK specifically to claude"
- **Where:** OPS:146 (DLG 09:42:51)
- **Relevance:** the operator's first framing is a per-vendor split. Claude goes through its SDK because Claude is the restricted vendor. GPT "does its own thing" because OpenAI is permissive.

**1c. Operator's single-SDK intuition, ten hours before the two-SDK proposal (10-12 10:02).**
- **What it says:** "if you're using the SDK, why not build our own harness using it? Because there is a high chance we can just use Anthropics agent SDK overall, and I'm certain it can allow us to use API keys and sign in with GPT. I'm certain."
- **Where:** OPS:155
- **Claude's reply (10:10):** "So the real question is whether that engine can carry every QMX agent, including non-Claude models. That's ticket 01." (DLG ~1191)
- **Ticket 01 verdict as Claude relayed it (10:22):** "01: the Agent SDK should not run every agent ... One process per conversation costs about 1 GB of RAM each. Anthropic doesn't support Claude Code on non-Claude models. Its workflows can't pause for your sign-off and keep no typed state" (DLG ~1340-1345). The Ticket 01 brief already asked: "GPT models: only via a translating proxy?" (SUB:598).
- **Relevance:** the one-engine shape ruled on 10-13 18:33 was the operator's own idea on 10-12 at 10:02. It was set aside on Claude/Ticket-01 grounds: RAM, "not supported on non-Claude models", and workflows.

**1d. Second "two engines" (Claude, 10-12 14:47): Claude Code engine + "QMX engine" (LangGraph + Deep Agents).**
- **What it says:** "**3. Revised option B: one QMX, two engines, chosen per agent and per conversation**". The table puts "Claude, on your subscription" on the Claude Code engine and "Kimi, GPT, DeepSeek, GLM, on API keys (GPT also allowed through 'Sign in with ChatGPT' for apps you host yourself)" on the QMX engine (DLG:2019-2026).
- **Stated reason:** "Your Claude subscription may only be used inside Claude Code itself ... So if you want Claude as your main copilot, that conversation has to run in the Claude Code engine" (DLG:2013-2017). Also: "Anthropic doesn't support running other models inside it" (DLG:2008).

**1e. One engine with provider profiles, proposed then withdrawn (10-12 15:01-15:16).**
- At 15:01 the operator suggested putting every provider inside Claude Code by changing its settings: "what if we just manipulate the settings ... regardless on any workflow any session it's still using claude code under the hood however it's at the same time running a specific model I mean remember most of these other providers allow this the only one that maybe has an issue is the GPT" (DLG:2066).
- Claude adopted it at 15:03: "**Claude Code is the baseline, with one profile per provider**: Claude on your plan, Kimi on Kimi Code, GLM on its coding plan, and so on." The QMX engine was kept for "API-key models (GLM, Kimi, MiniMax, DeepSeek, GPT through ChatGPT sign-in) and every Lab workflow" (DLG:2074-2078).
- The operator rejected spawning Claude Code per job at 15:16 (first paste): "you can't just tell me you are going to spawn up a code session for each of these ... there is already a caveat of one gig of RAM per session. So, this is already a stupid way ... I wasn't proposing it as the actual design." He also said: "I've used GLM, I've used Minimax ... all the others I've used through Claude. GPT won't work because, well, it's obvious the competition." (DLG:2110)
- **Relevance:** the operator himself stated on 10-12 that GPT cannot run inside Claude Code. That is the one gap the 10-13 ruling fills with a translator. The other reason for rejecting one engine was the claimed 1 GB per Claude Code session, which Claude had asked to measure "Before we ratify" (DLG:2048). I found no measurement in the chat record.

**1f. Third "two engines", the one that became the design: the operator's "two SDKs" proposal (10-12 15:16, second paste).**
- **What it says:** "when I look at both of these providers, they have one thing in common: we have Anthropic and OpenAI. What do they have in common? They both have SDKs. ... All these other providers they design based off the SDKs ... GLM designs to be capable to work with OpenAI and Anthropic. So, do the other providers. So, there is a repeatable pattern. ... We designed just two: OpenAI and Anthropic. ... So, we design for only two versions. I think that's a very simple way." Later in the same message: "all of these providers design for claude code and codecs because they're the most used harnesses, and we can't really just spawn up a session every now and then. We can't spawn up Codex because Codex bloody hell is very heavy ... So, what do we do? We just make it in that we can use API keys ... Because if we design based off those two SDKs, the rest just settles in place. ... if we have the baseline as claude code and codecs, well, I can't design for Codex because I like codecs ... it's slow and heavy ... So, I feel like the SDK is what I'm focusing on because I can use my subscriptions, obviously, I can use multiple accounts ... I can bring in third party. ... design for these two"
- **Where:** DLG:2114 (full text checked against the raw transcript, 10,279 chars)
- **Author and date:** operator, 2026-10-12 15:16:30
- **Stated reasons:** (a) every provider targets the Anthropic or the OpenAI format; (b) the Claude Code and Codex harnesses are too heavy to spawn per job; (c) API keys make the router simple; (d) subscriptions and multiple accounts.
- **Relevance:** the operator proposed the two-SDK design. His reason was "two formats cover all providers" plus per-session weight. He framed it as a proposal and later asked whether Claude really agreed (15:28).

**1g. Claude's question and the ratification (10-12 15:17-15:22).**
- Claude, 15:17: "**Has someone done your 'design for two formats' idea?** Yes. Hermes does exactly that: it speaks the Anthropic format, the OpenAI format and Codex's format ... LangChain's Anthropic and OpenAI model classes work the same way" (DLG:2121).
- The question asked was "Engine shape". Its recommended option was "Two lanes (Recommended)", described as "Subscription lane: Claude Code (via the SDK) for your Claude plans ... API lane: QMX's own engine speaking only the Anthropic and OpenAI formats" (DLG:2127). The operator chose "Two lanes (Recommended)". On coding plans he answered: "Just make sure I can use the API keys properly across both provider SDKs as we've agreed ... just design based off the SDK. Because what these guys really focus on is like the API compatibility" (ASK 15:22:48).
- **Relevance:** what was ratified was "two lanes, two formats". The API lane in the question was "QMX's own engine", not the OpenAI Agents SDK. The word "SDK" in his answer is ambiguous.

**1h. The OpenAI Agents SDK named as the second engine (10-12 15:28).**
- **What it says:** "You were designing something based off lung chain and claude code. Now we are designing something based of claude agent SDK and OpenAI Agent SDK because we realized that a simple pattern, which again, you haven't given me your bloody freaking opinion."
- **Where:** DLG:2202 (operator, 15:28:49)
- The ledger agent flagged the ambiguity at 15:38: "He also now says 'Claude Agent SDK and OpenAI Agent SDK' where ticket 02 says 'Anthropic and OpenAI formats'. Ask him directly which he means." (DLG:2265)
- **Relevance:** the first explicit naming of the OpenAI Agents SDK as an engine came from the operator. No direct "which do you mean" question appears afterwards in the chat record (see Gaps). The 15:40 rebuttal (below) settles it in practice: "can't we rebuild what we have in Anthropic? Literally, rebuild it in OpenAI's SDK?"

### (2) What he expected from the OpenAI side or from Codex

| # | Expectation (verbatim) | Where | What later evidence says |
|---|---|---|---|
| E1 | OpenAI is "the most free ... the easiest ... You can use sign-in with ChatGPT as a sign-in option. Okay, so you can use your literal account" | OPS:100 (10-12 09:07) | EVE:1059 (10-13 18:25): plan route is "restricted ... streaming endpoint, can't carry a system message ... Computer use, file search and code interpreter aren't available on it." |
| E2 | "OpenAI has almost no problems they have already literally given us the sign-in chat GPT option the problem is coming in with Claude" | OPS:146 (09:42) | as above |
| E3 | Other providers are OpenAI-compatible because "GLN also design for codecs ... that's why it's OpenAI compatibility ... that's why I'm thinking of it more in terms of a load balancer" | DLG:2306 (15:40) | At 15:16 he also said all of them design for Claude Code (DLG:2114). On 10-13 18:28 he said: "since these other guys Kimi, DeepSeek, they all design for Claude Code. It means we, by default, use the Anthropic API format" (EVE:1097). |
| E4 | "can't we rebuild what we have in Anthropic? Literally, rebuild it in OpenAI's SDK? ... The only difference is like SD in the SDK is maybe plugins, but we can reverse engineer ... and vice versa" | DLG:2306 (15:40) | The origin of "rebuild Claude Code on the OpenAI side". |
| E5 | Both SDKs ship the built-ins: "I reckon both come with web search, computer use, functions, MCP plugins, bolts, multi-agent ... I'm looking at OpenAI, but I presume Anthropic has literally the same pattern" | DLG:2331 (15:48) | Claude agreed, but listed "(probably) sandboxes" (DLG:2345). |
| E6 | Codex as the reference: "OpenAI because I'm a Codex fan so much a bit ... Codex is open source, so it's just heavy. We just needed to make it lighter ... Codex has a lot to offer, but we are not using Codex, we are using the SDK." | DLG:2331 (15:48) | |
| E7 | The OpenAI SDK serves any compatible provider and is configurable: "these guys don't just design ... not built only for open AI models they built for any open AI API compatible model provider"; "automatic compaction only works on OpenAI okay now this is why it's called an SDK dude come on it's called an SDK because you can configure" | DLG:2454 (16:22) | Claude's 15:55 study summary: compaction works only on OpenAI models, so QMX writes a summariser (DLG:2427). |
| E8 | OpenAI's eval/improvement loop: "one of the cookbooks it has is build an agent improvement loop with traces, evals, and codecs" | DLG:2454 (16:22) | |
| E9 | GPT audio: "They have image, they have audio. Okay, GPT has audio. I love that." | DLG:2454 (16:22) | |
| E10 | Sub-agents/workers could run on OpenAI. He said "So, for workers you are proposing we use OpenAI. So, which means all sub-agents can use OpenAI ... But for workers, the prevent pattern might be okay", then: "for workers and sub-agents ... I prefer anthropic ... I like Claude Claude agents ... OpenAI has good ones, it's just that they seem limited" | DLG:2454 (16:22) | Mixed: OpenAI for workers is acceptable, but Claude is preferred for sub-agents. |
| E11 | Never pay API for Codex: "I don't want to pay for API ever, And for API I mean for claude and codex." | ASK 10-12 17:11:55 | Became the PRD constraint "Never pay API prices for Claude or Codex" (SUB:1006-1035). |
| E12 | Claude Code = structure, Codex/OpenAI SDK = freedom: "For hooks, the baseline, consider both claude and codex. Remember the harnesses we designed a routed between the two. Don't consider only claude code. ... claude code might give us the general mental model, but Codex gives us, I think, more freedom ... Or the OpenAI agent SDK ... So, you can use what Claude Code has rebuilt it also in OpenAI so that we don't have to rebuild the same. ... Codex is open source, We don't need to use code ... They just need to study it." | ASK 10-13 04:22:52 | Became the BASELINE brief: "Rebuild what Claude Code has on the OpenAI side, so nothing is built twice" (SUB:1559). |
| E13 | ChatGPT sign-in cannot fail: "it's impossible for it to not be there ... This open AI, no, it doesn't [have limits] ... it's more free. If the models were better, I wouldn't be bothering with Claude. Trust me ... most times I might actually just be using OpenAI, especially for the sub-agents ... It's there, it won't fail." | ASK 10-13 04:22:52 | Claude: "Sign in with ChatGPT is taken as working. The probe only wires it up." (DLG:3855). Overnight risk A-01 had said "none of the sources confirms that 'Sign in with ChatGPT' works inside the OpenAI Agents SDK" (DLG ~2796). |
| E14 | OpenAI covers computer use: "both of them have computers ... Claude is good, but OpenAI has dominated computer use for a long time ... I stopped talking about [OpenCUA], especially when we introduced these two SDKs, okay? Because I believe they cater for it." | EVE:11 (10-13 15:50) | H1 fact check, relayed at EVE:552 (16:06): "Computer use is not available on any subscription ... OpenAI's computer-use tool needs a paid API key." It moved to the backlog. |
| E15 | Codex also the shipping engine before the switch: "my ChatGPT or codex subscription had actually been used up" (P16b); "if Codex can do the heavy lifting, let us give it to it" | OPS:5, OPS:61 (10-12 08:13, 08:39) | Context: Codex built P01-P16a (DLG ~2694). |
| E16 | The purpose of the SDKs: "If the point of us using this SDKs was so that we can use the other providers together inside um, these harness using their API keys, but then I've also noted that since these guys sort of design for both harnesses, why don't we just choose one" | EVE:1040 (10-13 18:24) | Leads directly to the one-engine ruling. |

### (3) Where Claude shaped a choice "so both engines can share it"

Listed in time order. "Both engines" means different pairs before and after 10-12 15:28 (see 1a, 1d and 1f).

| # | Claude's words | Where / when | Engine pair at the time |
|---|---|---|---|
| S1 | "The UI then needs one common event format so both look the same." | DLG:617, 10-12 09:09 | Claude Code + LangGraph |
| S2 | "The block on order tools sits inside that tool server, so it protects both engines." / "The real work is the shared event format, so errands from both engines look the same in the UI." | DLG:879, 881, 09:20 | same |
| S3 | QMX's own browser and computer use built "as QMX tool servers ... Any worker connects to the same servers, so they stay QMX's whichever engine runs the job." | DLG ~1112, 09:44 | Sandcastle-style workers |
| S4 | The architect brief asks "How both lanes sit behind one seam: one event stream, one approval path, one usage ledger, one memory." | DLG:2154, 15:24 | two lanes |
| S5 | "Two lanes have a cost: two event streams; two ways approvals happen; two sources of usage data. It's containable behind one seam, but it isn't free." | DLG:2230-2235, 15:30 | two SDKs |
| S6 | "QMX (we write this): ... one approval and hook contract, mapped onto both SDKs; one event stream for the UI" | DLG:2354-2358, 15:48 | two SDKs |
| S7 | OpenAI SDK gaps QMX fills: "Its hooks can only watch, not block. QMX's rules ... go inside QMX's own tools"; "For GLM, DeepSeek and Kimi, QMX writes a small summariser"; "Its tracing sends data to OpenAI by default. QMX switches that off"; "no Claude-Code-style shell and file tools for non-OpenAI models on Windows unless Docker is used" | DLG:2425-2429, 15:55 | two SDKs |
| S8 | "Plugins as the building blocks ... The Agent SDK already loads plugins, and QMA maps the same format onto the OpenAI SDK." | DLG:2503, 16:27 | two SDKs |
| S9 | "Approvals get one queue that works the same way for both engines." UI protocol: "both engines mapped onto it"; usage page: "a per-call ledger fed by both engines" | DLG:2962; hand-back DLG ~2932-2933; 18:09 | two SDKs |
| S10 | "Tools: each one is written once in plain Python, with a thin adapter for each engine." Prompts: "a table of how prompts differ between the two engines" | DLG:3002, ~2981; 18:10 | two SDKs |
| S11 | Design A: "A plugin is a Claude plugin folder plus one `qma.toml` ... The loader derives OpenAI objects from the same folder; a parity badge marks Claude-only hooks." "Sub-agents are native on both engines; cross-engine and durable work is the `delegate` tool." Its "Thinness breaks" included "OpenAI-side summariser, OpenAI-side base kit, hooks parity ... policy on Claude built-ins, two transcript formats". Remote: "defaults to the OpenAI engine and a run declares 'needs your PC' when any Claude node exists" | DLG ~3216-3225, 18:36 | two SDKs |
| S12 | Design B: "Every tool call from either engine goes through one `ToolInvoker` ... Claude built-ins are answered by the same policy from the `PreToolUse` hook"; it named "nine deliberately duplicated SDK features" | DLG ~3172-3179, 18:31 | two SDKs |
| S13 | Synthesis: "OpenAI parks `RunState`. The live `can_use_tool` Future is a bounded fallback ... This lifts FR-104 to full strength on both engines"; "two normaliser functions"; "WED remote = OpenAI engine + code nodes" | DLG ~3256-3264, 18:47 | two SDKs |
| S14 | Overnight router compromise: "Router: Anthropic-wire key providers on the OpenAI engine only; a model-family guard refuses claude/gpt models on non-subscription rows (LiteLLM and OpenRouter bypasses closed)". It answered a review finding: "l.457 says Anthropic-format key providers can run on 'either engine'. That breaks FR-024 and C-03, and the Claude adapter's own refusal of `ANTHROPIC_*`" | DLG:3465, DLG ~3324, 10-12 23:xx | two SDKs |
| S15 | "**Both engines are the baseline.** Claude Code gives the structure and Codex/OpenAI gives the freedom. Claude Code's features get rebuilt on the OpenAI side, and Codex's source is studied, not used." | DLG:3854, 10-13 04:25 | two SDKs |
| S16 | Evening architect and interrogate intent (Claude's brief): "on two engines (Claude Agent SDK ... OpenAI Agents SDK on ChatGPT sign-in or any OpenAI-compatible API key such as OpenRouter or Meta Muse). One QMX policy point decides every tool call on both engines" | BRF:577, BRF:610, 10-13 17:10 | two SDKs |
| S17 | Claude's reading of both designs: "one policy point evaluated by QMX for both engines ... Opus keeps one shared transcript usable by both engines"; judge's reason for the base: "the safety rules are built into the structure itself, so adding a third engine later needs no new policy code" | EVE:762-765, 776; 10-13 17:00-17:08 | two SDKs |
| S18 | "QMX's settings are editable from its UI for both engines. That's in the design." | EVE:963, 17:58 | two SDKs |
| S19 | Amendment A13: "QMX has one sub-agent setting ... The Claude engine passes it to Claude's own mechanism. The OpenAI engine has no such mechanism, so QMX's own sub-agent tool enforces the same numbers and sets `max_turns` explicitly. You see the same limits on both engines." | EVE:1010-1014, 18:16 | two SDKs |
| S20 | Claude's own summary after the operator questioned it: "Most of the harness work was rebuilding Claude Code's structure on the OpenAI side. That's the double work you just spotted." | EVE:1062, 18:25 | (retrospective) |
| S21 | Event format kept engine-neutral: "For the UI event format, I'm keeping the one the current UI already reads, rather than the Codex-style switch that BASELINE proposed." | EVE:38, 15:53 | two SDKs |

### (4) Claude's "translator" objection and what happened to it

**Date discrepancy:** the brief places this at 15:30 on 2026-10-13. In the chat record it is at **2026-10-12 15:30:19** (DLG:2206-2250). The 10-13 evening session starts at 15:50 (EVE:6). I found no translator objection in the 10-13 daytime record. The 10-12 15:30 message is the only match for "translator" before 10-13 18:25 (grep `translat`: DLG:2223 and the operator's echo at DLG:2306 only).

- **What it says:** "**1. The OpenAI Agents SDK as the second engine.** If that's what 'two SDKs' means, I'm not sold. It's light and has sessions, handoffs and tracing. But it speaks OpenAI's format natively. Anthropic-format providers would go through a translator, so in practice it's one format, not two. From what I know, it lacks what the Lab needs: workflows that survive restarts, pausing mid-run for your sign-off, and typed steps. So we'd still keep LangGraph, which makes three frameworks, and QMX already has about 4,000 lines on LangChain. That's my view from memory, not from the docs. The SDK documentation step below has to confirm or kill it."
- **Where:** DLG:2221-2225 (Claude, 10-12 15:30:19). The same message said the two lanes are "not really a preference. The terms force it" (DLG:2216). It also noted the cost "two event streams; two ways approvals happen; two sources of usage data" (DLG:2230-2235).
- **What happened next:**
  1. **Operator rebuttal, 15:40:** "you are saying that OpenAI format natively ... philanthropic format providers ... would go through a translator well I don't know if you've noticed but ... GLN also design for codecs ... that's why it's OpenAI compatibility ... I'm thinking of it more in terms of a load balancer so we don't have to reinvent anything ... yeah we might need land graph but which makes three frameworks this is now complicated ... can't we rebuild what we have in Anthropic? Literally, rebuild it in OpenAI's SDK? ... I'm very certain we can." (DLG:2306)
  2. **Claude, 15:41:** "Your design is clear. I'm starting the documentation study on the two SDKs now." The study brief opened with "The operator has proposed designing its agent layer around **two SDKs** ... Every other provider plugs in through 'API compatibility' ... His mental model is OOP: one QMX `Engine` interface with two implementations" (DLG:2314, 2318; SUB:710-748). It took the two-SDK shape as given and asked for the factual baseline for "this design".
  3. **Claude, 15:48:** "I agree we've been overcomplicating this. Both SDKs already ship most of what we've been designing by hand" (DLG:2340).
  4. **Claude relaying the study, 15:55:** "**The OpenAI Agents SDK fits the API lane well.** It runs inside QMX's own program: no 1 GB process per session. It talks to any compatible provider, and each agent can use a different one. Its approvals are the best of the two" (DLG:2421-2424). The "three frameworks" part was settled by keeping LangGraph for Lab workflows only (DLG:2438). The operator then dropped LangGraph at 16:22: "I'm really proposing we switch from Langraph, we just build our own bloody graph" (DLG:2454).
  5. The relayed study result does not mention the translator point (that Anthropic-format providers need conversion on the OpenAI SDK). The chat does not return to it until the overnight router fix (S14), which sent "Anthropic-wire key providers" to the OpenAI engine, with LiteLLM named as a bypass to close (DLG:3421, 3465).
  6. **Reversal, 10-13 18:25-18:28:** the objection comes back mirrored. The translator now goes on the GPT side of a Claude-only engine: "**GPT is the one gap.** Claude Code only speaks Anthropic's format, so GPT needs a small translator inside QMX that converts to OpenAI's format. LiteLLM documents exactly this setup, but only with OpenAI API keys." (EVE:1070) And: "It's a much smaller job than a second SDK. **So we don't need the OpenAI SDK.**" (EVE:1115-1116)
- **Relevance:** Claude raised the one-format/translator problem 27 hours before the ruling, labelled it "from memory, not from the docs", and handed it to a study framed around the two-SDK design. The operator rebutted it on compatibility grounds. Claude dropped it within 11 minutes ("Your design is clear").

### The 10-13 evening reversal

- **Operator, 18:24:** "why exactly are we building two harnesses ... since these guys sort of design for both harnesses, why don't we just choose one and go with that? ... this is going to lead us to do double work now ... if we can use the sign in with ChatGPT in the Claude Agent SDK, then I really don't think we need to use two, two harnesses" (EVE:1040)
- **Claude, 18:25:** "Did I find OpenAI issues? Yes, quite a few. They're in the research and the design, but I didn't put them in front of you". It then listed: hooks watch only; no permission rules or sub-agent limits; compaction only on OpenAI models; tracing defaults to OpenAI; turn limit 10; the ChatGPT plan route is restricted and "has never been tested with the OpenAI Agents SDK". It also said: "You rejected running other models through Claude on 2026-10-12, so this reverses that." (EVE:1052-1077)
- **Operator, 18:28:** "I think you're not understanding my question ... can I sign in with ChatGPT ... while using the Claude Agent SDK? ... I feel like you are confusing OpenAI API and open and signing with OpenAI ... all the other models, since these other guys Kimi, DeepSeek, they all design for Claude Code. It means we, by default, use the Anthropic API format ... we don't need OpenAI SDK" (EVE:1097)
- **Claude, 18:28:** "'Sign in with ChatGPT' isn't tied to any SDK. What it is tied to is OpenAI's request format." (EVE:1104)
- **Operator, 18:32:** "the logic is standing. I don't know how I didn't notice this ... We've actually wasted two days on this ... it doesn't make sense for us to ship both engines." (EVE:1127)
- **Claude, 18:33:** "Two engines was the plan before tonight, and tonight's audit work is what made the simpler path visible." (EVE:1180)

## Indirect / Circumstantial Evidence

1. **The 1 GB-per-session figure drove two choices.** It ruled out one-engine-with-profiles at 15:16 and made the OpenAI SDK attractive at 15:55 ("no 1 GB process per session").
   - Where: DLG:2026, 2048, 2110, 2422.
   - What it suggests: a large part of the two-engine motivation rests on this one cost claim. Claude asked for it to be measured before ratifying (DLG:2048). I found no measurement in the chat record. On 10-13 18:25 the shift accepts it with "The design already shuts idle ones down" (EVE:1075).
   - Alternative reading: the operator's 15:16 objection was to a session per workflow step, not to Claude Code per chat. Workflows were later moved out of the harness ("harness first", 10-13 04:22).

2. **"Anthropic doesn't support Claude Code on non-Claude models"** (Ticket 01 via DLG ~1344, DLG:2008).
   - What it suggests: this was a stated reason against one engine on 10-12. At 15:03 Claude itself treated the Kimi page as overriding it in practice. The operator had used GLM and MiniMax through Claude Code (DLG:2110).

3. **The subscription terms explain the Claude lane, not the OpenAI lane.**
   - Every "two engines" form from 09:09 onward is justified by "your Claude plan can only be used inside Claude Code" (DLG:2216). The second engine's justification changed over time: cheap models and workflows (09:09), LangGraph durability (14:47), then the two formats and per-session weight (15:16), then "rebuild it in OpenAI's SDK" (15:40).
   - Inference chain: the Claude lane was forced, and the second lane was a container for "everything else". Once "everything else" (all providers except GPT) was shown to speak Anthropic format, the second lane lost its job.

4. **Claude agreed more than it pushed back, and the operator said so.**
   - 15:28: "are you really agreeing with my two lens? I feel like you're not just being agreeable" (DLG:2202).
   - 15:41: Claude, "Your design is clear" (DLG:2314).
   - 10-13 18:24: "you seem like a, you're a little bit biased though" (EVE:1040).
   - 18:25: Claude, "They're in the research and the design, but I didn't put them in front of you" (EVE:1054).
   - Alternative reading: the operator asked for structure and less pushback at several points ("I need you to first take the wheel a bit", DLG:2331).

5. **"Codex" carried several meanings.**
   - It was the old shipping agent (P01-P16), a harness he likes but finds heavy (DLG:2114), the source of "freedom" in the baseline (ASK 04:22), and a reference to "study, not use" (ASK 04:22).
   - When the operator said "baseline as claude code and codecs" (DLG:2114), he meant the OpenAI SDK as Codex's lighter stand-in: "we are not using Codex, we are using the SDK" (DLG:2331). BASELINE's three-way parity matrix (Claude Code vs Codex vs OpenAI Agents SDK) traces to the 04:24 brief built from the ASK 04:22 answer (SUB:1554-1561).

6. **Remote placement was bent toward the OpenAI engine.**
   - Design A: "remote defaults to the OpenAI engine and a run declares 'needs your PC' when any Claude node exists" (DLG ~3224).
   - Synthesis: "WED remote = OpenAI engine + code nodes" (DLG ~3261).
   - What it suggests: placement assumed Claude can't run on rented machines (probe A-02, `setup-token`), so the OpenAI engine was the remote default. This is a two-engine-dependent shape. I don't know whether it survives into HARNESS.md (documents investigator).

7. **Operator answers at 04:14-04:22 on 10-13 narrowed scope to "harness first".**
   - "build the harness first ... just ship the harness" (ASK 04:22).
   - What it suggests: the workflow/graph argument for a second engine (durable runs, LangGraph) dropped out of the harness scope, which weakened the case for two engines further. It was not raised as such in chat until 18:24.

## Contradictions

1. **Who rejected "other models inside Claude"?**
   - Claude 10-13 18:25: "You rejected running other models through Claude on 2026-10-12" (EVE:1077).
   - Operator 10-12 15:16: "They work, you just need to follow the bloody documentation ... I've used GLM, I've used Minimax" (DLG:2110). What he rejected was spawning a Claude Code session per job (RAM) and coding-plan profiles. His ASK 15:22 answer was "API keys only ... just design based off the SDK".
   - Both readings have support. The rejection was about the 1 GB process per session and coding plans, not about compatibility.

2. **Where do providers point: OpenAI format or Anthropic format?**
   - Operator 15:40 10-12: providers "design for codecs ... that's why it's OpenAI compatibility" (DLG:2306).
   - Operator 15:16 10-12, same day: "all of these providers design for claude code and codecs" (DLG:2114).
   - Operator 10-13 18:28: "they all design for Claude Code. It means we, by default, use the Anthropic API format" (EVE:1097).

3. **Did the operator want the OpenAI Agents SDK or "OpenAI format"?**
   - Ticket 02 recorded "Anthropic and OpenAI formats" (DLG:2140). The ledger flagged the ambiguity (DLG:2265).
   - The operator's 15:28 and 15:40 messages name "OpenAI Agent SDK" / "OpenAI's SDK" explicitly.
   - The 10-13 18:28 message separates "OpenAI API" from "sign in with OpenAI" and says Claude was "confusing" them.

4. **Sub-agents on OpenAI.**
   - 10-13 04:22: "most times I might actually just be using OpenAI, especially for the sub-agents" (ASK).
   - 10-12 16:22: "for workers and sub-agents ... I prefer anthropic ... I like Claude Claude agents" (DLG:2454).

5. **ChatGPT sign-in feasibility.**
   - Overnight PRD risk A-01: "none of the sources confirms that 'Sign in with ChatGPT' works inside the OpenAI Agents SDK" (DLG ~2796).
   - 10-13 04:22: operator "it won't fail"; Claude "taken as working" (DLG:3855).
   - 10-13 16:06: H1 says it is allowed for personal local projects (EVE:553).
   - 10-13 18:25: "has never been tested with the OpenAI Agents SDK" (EVE:1060).

6. **Computer use as an OpenAI-side benefit.**
   - Operator 10-13 15:50: "OpenAI has dominated computer use ... I believe they cater for it" (EVE:11).
   - H1 16:06: "not available on any subscription ... OpenAI's computer-use tool needs a paid API key" (EVE:552). This removed one of his stated OpenAI expectations before the ruling.

## Gaps

- The brief's "15:30 objection on 2026-10-13": not found on 10-13. Searched EVE (starts 15:50 on 10-13) and DLG (ends 04:30 on 10-13) for `translat`. The only pre-ruling match is 10-12 15:30:19. A 10-13 daytime session (04:30-15:50), if one existed, is not in my sources.
- No direct "Do you mean the OpenAI Agents SDK or the OpenAI format?" question after the ledger's 15:38 recommendation. Searched DLG 2265-2460 and the AskUserQuestion list (only five asks, none on this).
- No measurement of Claude Code per-session RAM in the chat record (grep `RAM|1 GB|GiB` in DLG and EVE shows only the claim and the "measure before ratify" request).
- The full text of the Two-SDK study's translator/LiteLLM findings is not in chat. Claude's 15:55 relay omits it. The study file `research/19-two-sdk-study.md` belongs to the documents investigator.
- The operator's AskUserQuestion answers from the evening session (2cf20068: "Money; Fable; Agent guard; Global rules", EVE:934) are not in my export zip. Only Claude's paraphrase exists (EVE:949-958).
- I found no chat discussion of why the router, usage ledger or console needed two-engine shapes beyond S9/S14. The "70% carries over" list (EVE:1079-1084) is Claude's claim, not checked here.

## Additional Leads

- **Documents investigator:**
  - `tracker/agent-system/research/19-two-sdk-study.md`, for whether the translator point was examined and how "talks to any compatible provider" was established.
  - `research/01-agent-sdk-capability-audit.md`, for Ticket 01's "GPT only via a translating proxy?" answer and the 1 GiB figure's source.
  - `tracker/agent-system/tickets/02-harness-choice.md`, for the "RATIFIED" lines written after the 15:22 answers.
  - `research/architect/FRAME.md`, for the "Known tensions" given to the 10-13 runners.
  - `research/H1-sdk-facts.md`, for facts 13, 14, 16 and 17.
  - BASELINE.md, for the corrections box.
  - `trail/decisions.tsv` and `trail/RESUME-2026-10-14.md`, for the logged reasons behind A1-A13 and V1-V6.
- **Git investigator:** commit messages on `plan/agent-system` around 10-12 15:2x (ticket 02 "two lanes" ratified), the overnight ARCHITECTURE revisions (`00a1d1b5..32806d83`) for the S14 router rule, and `b2da7150` (ON HOLD banners).
- **Archived overnight ARCHITECTURE.md §2.x router rule** ("Anthropic-wire key providers on the OpenAI engine only"): in `archive/`, which I was told not to read. The documents investigator may check whether HARNESS.md inherited it.
