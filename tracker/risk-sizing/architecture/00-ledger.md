# 00. Decision ledger, 20 to 31 October

Written 2026-10-31 by agent P1 of the midday program, from a full read of his words. It lists every ruling, seed, request, correction and owed item he gave since 20 October, deduplicated, with the newest word winning. The architecture fold reads this file first, then the area files. It designs nothing.

## How to read this

**Sources read in full.** `operator/transcript-2026-10-20-to-28.md` (T1), `operator/transcript-2026-10-29-to-30.md` (T2), `operator/transcript-2026-10-30-to-31.md` (T3), `operator/2026-10-27-review-dictation.md` (D27, the same text as T1:1574 and T1:1613), `operator/2026-10-28-router-system1-system2.md` (D28, identical to T1:1903, checked by script), `operator/2026-10-28-discussion-notes.md`, `seeds.md`, `RISK-SIZING-PACK.md`, `STATE.md`. Read as inputs: `research/43-convergence.md` (sections 1 to 8, appendix B and the fold), `research/52-fable-read-of-the-whole-run.md`, `research/53-fable-next-steps.md`.

**Citations.** `T3:1264` is line 1264 of T3, the line that holds his message text (the header line plus one). Every quote in the "His words" column was checked by script against the cited line (see the last section). Quotes are his dictation as it arrived, slips included.

**Status.**
- RULED. His ruling, recorded in `STATE.md` or given as a direct answer. Binding.
- SEED. His idea to expand, reject or improve. Not a decision.
- LEAD'S CALL. A call the lead made from his words, recorded in `STATE.md` or a research file. Binding until he vetoes it.
- OWED. Something he asked for that does not exist yet.
- SUPERSEDED by X. A later item replaces it. Kept so nobody revives it.

**Where it lives now.** `STATE mid rN` is `STATE.md` "Operator round 2026-10-31 midday" ruling N. `STATE mid lead-13` is "The lead's answer to ruling 13" there. `STATE am rN` is the 31 Oct morning round. `STATE Q1` to `Q6` are "His answers to Fable's six questions". `STATE 27 Oct`, `STATE 28 Oct`, `STATE 29/30` and `STATE run` are the rounds of those names; `STATE corr N` is "Operator corrections" item N. `seeds §X`, `PACK §N`, `43 §N` and `MEM file` are sections of `seeds.md`, `RISK-SIZING-PACK.md`, research 43 and the memory folder. "Chat only" means no file holds it.

**Order.** A cross-cutting section first (rules every area obeys), then the areas in his priority (QML first, the trading node second, the MIS third), then the rest, then process. Inside an area the rows run from what the architecture must honour (rulings) to what it may use (seeds) to what is dead (superseded).

---

## 0. Cross-cutting rules every area obeys

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| CC-01 | Foundation first. Design the smallest set of parts that is complete and solid, so QMX grows on top without rework. Same pattern as mini apps, the Lab and the pods. The same approach later for risk and sizing. Never call it "minimal viable". | "it's like building a house on a very strong foundation" (T3:1264); "And don't use that word" (T3:1264) | 31 Oct | RULED | STATE mid r6; MEM foundation-first-design.md |
| CC-02 | Design for complexity, not a complex system. Handle the hard cases (the 95th percentile) with few parts that are easy to maintain and explain. Lead's wording, which he delegated: "capable at the edges, simple at the core". | "Design for complexity means design a system that can handle very hard edge cases" (T1:1177); "design for complexity and don't design a complex system" (T2:1208); "Design for complexity. Yes, very much." (T3:1105) | 24 Oct to 31 Oct | RULED | STATE corr 1; STATE run "His proposal for the architecture step"; standing order 6 |
| CC-03 | Not a blank slate. Ground on what is built and stacked before proposing anything. Never casually remove shipped backend work. | "you are not building from a blank slate" (T3:903); "I don't want to just mess around, okay, and remove a lot of the things we've been shipping" (T1:828) | 24 Oct, 31 Oct | RULED | STATE am r1; STATE corr 7; standing order 16 |
| CC-04 | Nothing is out of scope, but every proposal names what it touches and how. | "just because you're handling units doesn't mean anything is really out of scope or blocked" (T1:828) | 24 Oct | RULED | STATE corr 7 |
| CC-05 | Code first, numbers later. Everything QMX must be able to do as a system ships now; numbers (thresholds, sizing maths, pass marks, portfolio optimisation) ship as editable defaults or templates. | "I want to first get the things that need to be coded out of the way" (T2:6) | 29 Oct | RULED | STATE 29/30; standing order 5 |
| CC-06 | Local first. Everything runs on his PC alone first. Servers stand in or extend, never replace. | "needs to first be able to work on my machine locally before it is deployed on a server" (T1:1574); "if something is to run on external compute and external storage, it should first run on my machine" (T2:1148) | 27 Oct, 30 Oct | RULED | STATE 27 Oct "Local first"; rulings 136 to 139; MEM pc-home-servers-substitute.md |
| CC-07 | Nothing capped. Freedom to build any trading algorithm, up to portfolio optimisation. No lookback limit. Defaults are never cages. The ideas themselves may be expanded. | "No limits, okay? That's why nothing is capped." (T3:1105); "I don't want to limit QMX in any way, shape, or form" (T1:1574) | 27 Oct, 31 Oct | RULED | STATE Q6; STATE 27 Oct "Unbounded by default" |
| CC-08 | Plain Python is always possible beside QML. QML, the unit and the schemas are a standard for agents and never stop a human or a mini app. | "it doesn't mean that normal Python is off entirely" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Unbounded by default" |
| CC-09 | Design for agents. Agents run QMX through workflows, skills and hooks; a copilot may remake parts. | "Stop designing for humans, start looking at agents." (T1:1574) | 27 Oct | RULED | STATE 27 Oct |
| CC-10 | Determinism over agent judgement. What an agent produces is checked by a script, compiler, linter or test. | "Favor determinism over non-determinism. That's the whole point of QML" (T3:903) | 31 Oct | RULED | STATE am r5; standing order 18 |
| CC-11 | Only he promotes. Nothing enters live without him, no variant, no unit, including market versions agents work on. The only automatic move is a risk rule stopping a unit, logged and monitored. | "nothing actually ever enters live without me" (T1:1574) | 27 Oct, confirmed 31 Oct | RULED | STATE 27 Oct Q3; STATE Q6 |
| CC-12 | Units stand alone. If the router or MIS is slow, down or offline, a unit keeps trading when its own conditions, the pair and the broker allow. | "why should the unit stop trading?" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Router"; standing order 10 |
| CC-13 | QMX cannot touch money by design. Brokers sign in on their own web pages; his cTrader credentials sit in Windows Credential Manager. The "real-money key" topic is dropped for good. | "there is no way in which anything in QMX really touches money" (T3:903) | 31 Oct | RULED | STATE am r9; STATE Q6 |
| CC-14 | Windows is first-class. Do not design for Linux only unless the design truly needs it. (The trading node itself runs on Linux; see N-03.) | "I would prefer using Windows than sorting WSL" (T3:903) | 31 Oct | RULED | STATE am r7; standing order 19 |
| CC-15 | Works out of the box for a newcomer who was not in the planning. Low-stress deploy. Freedom to build anything, which is why mini apps and workflows exist. | "factor in the logic of a person who has no clue how it's built or it's meant to be building" (T3:1102) | 31 Oct | RULED (recorded as "new seed" in STATE Q5; he gave it as a direct instruction) | STATE Q5 |
| CC-16 | Layer the architecture. A high-level map of the biggest parts and how they connect first, then one pass per part with its own seed, ideation and architecture, one area per file. Connection points get their own design. | "Let's first look at the high level architecture." (T3:904); "I don't think one file is enough" (T3:903) | 31 Oct | RULED | STATE am r2, r3; standing order 17 |
| CC-17 | Prove in practice, with real parts. No throwaway prototype. The proof is a dummy unit on the real template, any strategy the lead picks, shown working. | "I can't wait 2 days for you just to code something and throw it away." (T3:1264); "you are smart enough to conjure up any strategy you want" (T3:1264) | 31 Oct midday | RULED | STATE mid r1 |
| CC-18 | Technical depth "as if building a Bloomberg terminal", on a small piece, since most pieces are built. | "as if you're building a Bloomberg terminal" (T2:1148) | 30 Oct | RULED | STATE run "Architecture bar" |
| CC-19 | A trader's lens on every QML step. Questions any trader knows are never asked as open. | "even me as a newbie trader, I already know what they mean" (T2:845) | 30 Oct | RULED | STATE run "No rush" |
| CC-20 | Positioning. When generating strategies is nearly free, judging them is the product. QMX is his own platform, not for sale. | "I don't think really building QMX to be sold, it's really mine" (T1:1177) | 24 Oct | RULED | STATE corr 10 |
| CC-21 | News trading is out for now. | "For now, let's put news out." (T3:903) | 31 Oct | RULED | STATE am r13 |
| CC-22 | QMX has two faces. Algo-facing (QMB, QML, QMF, QMN) and human-facing (copilot, workflows, Lab, pods, mini apps); agents sit between. The unit lives on the algo face with agents as its users. | "we have human usable and algorithmic usable or agentic usable" (T1:444) | 20 Oct | SEED | seeds §"System split" |
| CC-23 | Three lenses, none a cage. Agents and code; traders of each instrument; creators who build anything in plain Python. Copy what MT5, cTrader and NinjaTrader do well. | "I also want you to think through the lens of traders" (T1:783) | 24 Oct | SEED | wayfinder/MAP.md notes |
| CC-24 | Every part serves a logical purpose, without "every part must prove itself" machinery. | "it needs to serve a logical thing" (T1:264); "Okay, don't make this so complex." (T1:1177) | 20 Oct, 24 Oct | RULED (the machinery is rejected) | STATE corr 1 |

---

## 1. QML (priority one)

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| Q-01 | QML comes first. A small mistake in it is very costly; give it more care than any other part. | "QML is very important, please." (T3:1264); "a small mistake in there is very costly" (T3:1264) | 30 Oct, 31 Oct | RULED | STATE mid r10; STATE run "No rush" |
| Q-02 | QML is a library like React. Nothing assumed, everything certain. It gets its own pass. | "because you are building a bloody library, okay? Like React, JS. You can't assume anything here." (T3:904) | 31 Oct | RULED | STATE am r3 |
| Q-03 | QML is upgraded into the library agents use to build units: build, test, promote and monitor. Deep modules (a small simple surface, the depth inside), JSON schemas, simple mental models. | "I think QML deserves an upgrade." (T1:1211); "library is the right word" (T1:1211) | 24 Oct | RULED | STATE corr 3; seeds §"Corrections (operator, 2026-10-25)" |
| Q-04 | QML is not new. Much exists in the current code; the dictionary was not catered for fully. Build on it. | "QML is not new, okay?" (T3:1264) | 31 Oct | RULED | STATE mid r12 |
| Q-05 | Agents write units through deterministic checks, a compiler, linter or test runner in the spirit of pytest or React Doctor. Check what QML already has (it may exist). | "we can't rely on agents checking their own work" (T3:903); "React has, is it React Doctor?" (T3:903) | 31 Oct | RULED | STATE am r5 |
| Q-06 | Agents get feedback while they write, the way Claude Code gets a linter error through a hook. QMA v2 runs on the Claude Agent SDK. No false positives. | "the same way you yourself, when you write code, you can receive a linter error or something" (T3:1264); "we have to make sure there are no false positives" (T3:1264) | 31 Oct | RULED | STATE mid r12 |
| Q-07 | Deep modules is why QML looks the way it does. Designing for agents means designing out ambiguity. QML exists so agents do not just write Python. | "when you're designing for agents, you have to consider a lot of ambiguity to be sorted out" (T2:1000); "QML is a library so that we don't just write Python" (T2:788) | 30 Oct | RULED | STATE run "His calls on research 34 and 35" |
| Q-08 | The gold mine session's intent for QML is a key seed: where the dictionary was meant to end and how QML was meant to be built. Do not set it aside. | "the goldmine session had a lot more to say of the intentionality of where the dictionary was meant to end" (T3:903) | 31 Oct | RULED (as a seed that must be used) | STATE am r18; research 39 |
| Q-09 | How agents write a unit and know it is correct: MCP, tools, what? | "Is it via MCP, via what?" (T3:903) | 31 Oct | OWED | STATE am r5; chat only for the answer |
| Q-10 | The language is not assumed. QML was built for cTrader in Python; research what each platform uses (C# and .NET came up) before choosing. His earlier doubt about Python for the live path. | "we need to also know whether it's going to be Python, Golang, or I don't know which language" (T3:903); "I don't think Python will be suitable, depending." (T2:55) | 29 Oct, 31 Oct | OWED (the platform research agent was stopped; research 31 measured the network as the limit at 1-minute speed) | STATE am r6; 43 §7 item 1 |
| Q-11 | Logic is the answer to "what exactly do you trade?", about 60% of a unit. What constitutes logic is QML's to define. | "makes up around 60% of the entire thing" (T1:2051) | 28 Oct | SEED | discussion notes 28 Oct; 43 §3.1 |
| Q-12 | The first-principles question: a bot is a set of if-else rules, so how do those rules tune themselves, and what exactly tunes? | "how do we make sure that those if-else statements can self-tune?" (T2:788) | 30 Oct | OWED (answered in 43 §3.1 in words, never shown in code; see U-05) | STATE run "Missed by the run"; 43 §3.1 |
| Q-13 | Hybrids, tribrids, quadbrids: combining several things, or several bots, into one edge. | "hybrids, tribrids, quadbrids, whatever" (T1:264) | 20 Oct | SEED | research 39; 43 §4 "Hybrids are build-time composition" |
| Q-14 | Entries and exits are variant axes inside QML's broad structure. | "exits become variant, entry become variant" (T1:1177) | 24 Oct | SUPERSEDED in part by R-04 (exit maths goes to the risk session; the unit still owns its exits) | seeds §"Corrections" |
| Q-15 | Lead's call on the unit's written form: a declared skeleton of named slots, each filled by a tested code block, compiled once into the factory QML already runs. Not a JSON graph interpreted per quote. | (lead) | 30 Oct | LEAD'S CALL | 43 §3.1; 53 §3.2 |

## 2. The dictionary

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| D-01 | The dictionary is rebuilt in form; all 239 entries and their ideas are kept as seeds, never lost. His 26 Aug "permanent" meant never lose them and never leave them in limbo. | "it needs to be most likely be redone, most of it" (T2:788); "the dictionary needs a rebuild, an entire thing" (T2:219) | 29 Oct, 30 Oct | LEAD'S CALL from his words (he called it "a direction, not a rule" on 31 Oct) | STATE run research 44 row; 43 §3.2 |
| D-02 | A concrete proposal of how the dictionary is rebuilt, shown to him. 43 §3.2 holds one; it was never put in front of him in his register. | "you really haven't rebuilt the dictionary or haven't proposed how it's going to be rebuilt" (T3:1105) | 31 Oct | OWED | STATE Q6; 43 §3.2; 53 §2 item 4 |
| D-03 | Why it exists. A cross-trader vocabulary: whatever a source mentions is already known or gets appended, so building agents are never confused. Broad in entries and exits, with room to expand. | "if someone from a source mentions anything, we already know what it is, okay? Or if it's new, we can append it" (T2:788) | 30 Oct | RULED (as intent) | STATE run "Missed by the run" |
| D-04 | It expands far beyond FX (indices added 29 Oct); how it expands is code to plan and build. | "239 is very small" (T2:1000) | 30 Oct | RULED | STATE run "His calls on research 34 and 35"; research 45 |
| D-05 | Who expands it: the lead decides, and gives the expanders directions. Ground first; do not limit them. | "you tell them to ground themselves first. Don't limit them, okay?" (T3:1264) | 31 Oct | RULED | STATE mid r13 |
| D-06 | The lead's answer to D-05. Builders build the form (schema, checks, authoring tools) as code. The first content wave (porting the 239, then families beyond forex) is a packet in the same build, done by builders with a grounding brief and no cap. Later growth goes through the same authoring door the copilot and QMA agents use. | (lead) | 31 Oct | LEAD'S CALL | STATE mid lead-13 |
| D-07 | Market context in the dictionary is the trader's sense (price action, technical analysis, fundamentals when used), and it is what the MIS measures. | "market context. Okay, when you are looking at a chart, a market chart, you have to have market context" (T2:788) | 28 Oct, 30 Oct | RULED | STATE run "Missed by the run"; discussion notes 28 Oct |
| D-08 | The Hermes work in `Desktop\Stats` (with `.hermes\orchestration`) and `Desktop\strats` is the source; the old `Documents\Claude\QMX-discussion` vault is old and weak, used only for risk and sizing ideas. | "The folder you're meant to be looking at is stats, not struts with an A" (T1:1574); "The pillars are in the stats folder" (T2:908); "The documents QMX version is very old." (T2:908) | 27 Oct, 30 Oct | RULED | STATE run "Seeds, 2026-10-30 (later the same day)" |
| D-09 | The gold mine and the paper trail are seeds: read them, expand them, propose new things on top. | "take those things as seeds and expand" (T2:1003); "Those ideas are very important, by the way." (T2:1000) | 30 Oct | RULED | STATE run "His calls on research 34 and 35"; research 39, 40, 41 |
| D-10 | The dictionary was GPT's idea: a good start, not sacred. Keep it free; defaults never a cage. | "the dictionary was GPT's idea, not mine" (T1:1211); "don't drop anything. Yeah, add defaults, but keep it free" (T1:1574) | 24 Oct, 27 Oct | RULED | STATE corr 3; STATE 27 Oct Q8 |
| D-11 | Review the 239 entries in place, or rebuild them. | (asked by agents, 30 Oct) | 30 Oct | SUPERSEDED by D-01 | 43 §3.2 |

## 3. The unit

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| U-01 | A unit replaces the trading bot. One complete algorithm with no separations: entry, exits, its own self-calibrating risk and sizing, its condition needs, session profile, baseline and journals, tested as one. | "Unit is literally a replacement of a trading bot. It's just a self-configuring trading bot. Simple as that." (T2:788); "I agree with Fibble on number one" (T3:1105) | 24 Oct to 31 Oct | RULED | STATE corr 2; STATE Q6 |
| U-02 | What "it works" means. Does a unit actually make sense as a self-optimizing thing that leans on very few parts, unlike a bot that leaned on many? Not a feature checklist. | "does a unit actually make sense?" (T3:1145); "A unit, it is self-optimizing, it's relying on very few things" (T3:1145); "So the proof tests make no sense to me." (T3:1145) | 31 Oct | RULED | chat only (T3:1145); STATE Q2 note |
| U-03 | The unit is a template. | "we need the unit in terms of a template" (T3:904) | 31 Oct | RULED | STATE am r3 |
| U-04 | Placeholders for sizing and exits, clearly labelled, on backtest and demo alike. The risk session later gets the list of placeholders to rip out. | "placeholders, I think is the right word" (T3:1087) | 31 Oct | RULED | STATE Q1 |
| U-05 | The proof uses a placeholder unit and market. What is tested is the system for a daily user: can agents build units, can they backtest them. He builds better units himself later. | "Can they build units rather? Can they, you know, backtest them?" (T3:1093); "you are smart enough to conjure up any strategy you want" (T3:1264) | 31 Oct | RULED | STATE Q2; STATE mid r1 |
| U-06 | How a unit configures itself, shown concretely. The thing he needs most, asked since 27 Oct, still not shown in code. | "I actually haven't seen how they are going to self-configure." (T1:1574); "I think that is one of the things I need most right now" (T1:1574) | 27 Oct | OWED | STATE 27 Oct "Account guard and pod"; 53 §3.2 |
| U-07 | The weak spots are the lead's to solve, in its own way, and to report in a line (two speeds of tuning, placeholders that cannot show tuning, the picking trap). | "So what I'm saying is try maybe solving the weak spots in your own way." (T3:1264) | 31 Oct | RULED | STATE mid r2 |
| U-08 | "A unit is one data document" or "like JSON" was his analogy, not the design. | "I mean, my analogy made sense, but it's an analogy." (T3:903) | 31 Oct | RULED (correction) | STATE am program; supersedes the literal reading of 43 F3 |
| U-09 | The same unit on the same pair at 1m and 5m is one idea, and the two are correlated: one bet, not two. | "that's just correlation. I don't think it's different" (T2:1000) | 30 Oct | RULED | STATE run "His calls on research 34 and 35" |
| U-10 | "Two different bots with the same logic" on 1m and 5m. | "So you are telling me I can have two different bots with the same bloody logic?" (T1:484) | 20 Oct | SUPERSEDED by U-09 | seeds §"Registry" (stale line) |
| U-11 | System 1 grows into System 2. System 1 trades by market context (a mean-reverting scalper); System 2 adds a specific instrument (a EURUSD scalper), more specific amplification, sniping, and "the end goal of QMX". Before live, System 2 can change or enhance the logic per market. | "So what we are seeing is that system one grows into system two." (T1:1999); "It's as if system two is the end goal of QMX." (T2:135); "system two before live can work if we are changing or enhancing different logics for different markets" (T1:1903) | 28 Oct, 29 Oct | SEED (the idea); the names are settled as explanation names, see U-13 | STATE 28 Oct; discussion notes 28 Oct |
| U-12 | Path A. A System 2 version is earned from a record the System 1 unit built on that market; it never appears from thin air. Every System 2 has a System 1 parent by default. | "there is already a history, a track, a paper trail" (T2:219); "it should have a system one parent by default" (T1:2051) | 28 Oct, 29 Oct | RULED (Path A); SEED (the default parent) | STATE 29/30 |
| U-13 | System 1 and System 2 are explanation names only. Never raise them again. He will think about "market settings" and "market version" himself; the lead supports both halves in the design without asking. | "system one and system two were never any definition under QMX" (T2:788) | 30 Oct, 31 Oct | RULED (names); LEAD'S CALL (support both halves) | STATE am r17; 43 §3.1 |
| U-14 | Same logic on a new instrument, timeframe or broker makes a sibling unit. | "So a new instrument, time frame broker makes a sibling unit. I think, yeah, it's viable like that." (T1:1574) | 27 Oct | SUPERSEDED by U-11 and U-13 (28 Oct: an instrument joins the unit's universe; only a logic change makes a new unit; he never confirmed the change, and the names are not to be raised) | STATE 27 Oct Q1; STATE 28 Oct |
| U-15 | Lineage. Everything about a unit is saved and traceable to its source (chat session, YouTube video, blog post, copilot chat, article). Analyst lens: knowing where high performers come from narrows the search. | "We're not trying to vibe trade or vibe code here." (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Lineage and history" |
| U-16 | A unit is malleable across styles (scalper, intraday, swing). Scalper types are finite in practice but are defaults, never a cage; a custom ML model that is no scalper type must fit. | "a unit is obviously should be malleable" (T2:135); "don't drop anything. Yeah, add defaults, but keep it free" (T1:1574) | 27 Oct, 29 Oct | RULED (never a cage); SEED (malleable) | STATE 27 Oct Q8 |
| U-17 | A unit's journey before it places a trade, and which steps still run with the router, MIS, feed or PC down. | "there is also a journey in which a unit is meant to take before it places a trade" (T2:219) | 29 Oct | SEED (owed as a design item) | 43 §8 "Prototype: the steps before one trade" |
| U-18 | A source's built-in filter that matches an MIS indicator means the strategy is already specific; it hands over its own context claim. | "if it's using the same things as in those in the MIS, it means it is already specific" (T2:219) | 29 Oct | SEED | 43 §3.3 |
| U-19 | He or the copilot can attach markets to a unit by hand after watching them; those labels can help retrain the MIS. | "we can literally attach values, or we can attach" (T2:219) | 29 Oct | SEED | 43 §3.3 |
| U-20 | Sniping. A unit × pair × premium window (London and New York overlap, gold's clean moves) with its own sizing once proven; outside the window it trades normally. | "Sniping is something I want to really focus on" (T1:442) | 20 Oct | SEED | seeds §"Sniping"; 43 §4 "Sniping is a named time window" |
| U-21 | A registry of where each unit belongs: preferred markets with proof (QMB's run-on-every-bot grid) and hypothetical similar markets (post-COVID window) to test, not trade. | "we have an option which is run on every bot" (T1:442) | 20 Oct | SEED (partly absorbed by the 28 Oct universe view) | seeds §"Registry of where each bot belongs" |
| U-22 | Horizons. Scalpers first, then intraday, swing barely; eventually a spot-only system. | "eventually shall shift to a spot-only system" (T1:376) | 20 Oct | SUPERSEDED in part by X-02 (markets traded as they come); spot-only shift parked | seeds §"Horizons"; 43 §8 parked list |

## 4. The MIS (priority three)

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| M-01 | The MIS reads markets and publishes; units pick from it; no unit needs it to trade. | "What I wanted was the MIS just reads and outputs." (T1:1951); "I've been saying this over and over again" (T3:1105) | 28 Oct, 31 Oct | RULED | STATE Q6 |
| M-02 | The MIS gets defaults now and room for models he trains later. It must hold for every instrument now in scope, not only forex. He sees it as incomplete. | "Let's make defaults for the MIS. I'll train the models when I can." (T3:1264); "So the MIS itself is incomplete." (T3:1264) | 31 Oct | RULED | STATE mid r11 |
| M-03 | Priority: after QML and the trading node. | "Then I think the MIS is the other." (T3:1264) | 31 Oct | RULED | STATE mid r10 |
| M-04 | The MIS is shaped by trading style, then timeframe, then the data a market offers. Instruments matter through their data, not one by one. | "we need a trading style, firstly" (T2:219); "we are going to consider variables that each market has" (T2:219) | 29 Oct | RULED | STATE 29/30 |
| M-05 | The router only routes. It directs and gives depth of information ("this market fits your conditions"); it never switches a unit on or off. | "Neither does it switch on, nor does it switch off." (T1:1574) | 27 Oct | RULED | STATE corr 5; STATE 27 Oct "Router" |
| M-06 | The round-two router (expiring offers, load-balancer algorithms) took the analogy too literally and was over-built. | "I think you took it verbatim, and that's causing issues" (T1:1903) | 28 Oct | RULED (over-built machinery dropped) | STATE 28 Oct; 43 "Subtract first" item 4 |
| M-07 | Router speed is an architecture problem (precompute, cache), not a modelling one. | "if speed is the issue, let us figure out a way to make it faster" (T1:1177) | 24 Oct | RULED | STATE corr 5 |
| M-08 | Split: the fast part on the trading node, the planning part elsewhere (his PC). | "Actually, yeah, splitting it, I think, is the best fit." (T1:1574) | 27 Oct | RULED | STATE 27 Oct Q7 |
| M-09 | QMX workflow templates read the MIS's logs, not the MIS model directly. | "They should be using the logs from the MIS." (T3:903) | 31 Oct | RULED | STATE am r12 |
| M-10 | The MIS can be upgraded by agents as they see fit, with the user's approval; a new context term needs a new sensor. | "the MIS can be upgraded as the agent see fit, obviously with my approval" (T1:1951) | 28 Oct | RULED | 43 §3.3 |
| M-11 | Organise the MIS by instrument type (futures, currency, crypto, gold). Research which context sensing works best per class; that study can itself reveal inefficiencies, a new source of strategies. | "categorizing by instrument type" (T1:1999) | 28 Oct | SEED | discussion notes 28 Oct; research 23, 37 |
| M-12 | A scalper's MIS holds fast indicators, not an HMM, and its contents come from research, not assumption. His per-market, per-timeframe HMM was only an example. | "you are not going to put an HMM inside a scalper's MIS" (T2:219) | 29 Oct | SEED | research 22, 23; 43 §3.3 |
| M-13 | Indicators, statistical tests (Hurst, variance ratio, efficiency ratio) and models (HMM, BOCPD, MS-GARCH) are one family that measures market state; make that layer usable in the Lab too. | "we can add this to the lab" (T1:1999) | 28 Oct | SEED | discussion notes 28 Oct |
| M-14 | Several trading nodes and instruments mean several routers or one central one; models need training per instrument. Think it through. | "we also need to train for specific instruments" (T1:1574) | 27 Oct | SEED | STATE 27 Oct "Router" |
| M-15 | Fundamentals as an MIS input, from an agentic workflow with proof. | "We can write it to an agent, fundamental analysis with proof" (T1:376) | 20 Oct | SEED (later; news is out for now) | seeds §"Fundamentals as an MIS input" |
| M-16 | A correlation ledger in the router. | "we need one in the router, whether we like it or not" (T1:1574) | 27 Oct | SUPERSEDED by R-06 (book and correlation control go to the risk session; the MIS only publishes readings for it) | PACK §2.10 C5 |
| M-17 | The MIS as a router inside versus outside the unit; "does it add noise?" | "It was never meant to be part of a unit." (T1:376) | 20 Oct | SUPERSEDED by M-01 | seeds §"MIS is a router" |

## 5. Journals

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| J-01 | Journals are not one simple row shape. A journal spans instruments, brokers, accounts, platforms and trading nodes, and paper or live. Units go back to paper; paper also follows backtesting as its own phase. Design it in depth. | "The journals have one simple row shape. I disagree." (T3:903); "The journal is very important, please." (T3:903) | 31 Oct | RULED | STATE am r14 |
| J-02 | A trading journal per unit from creation through stress, paper and live. Possible fields: best instruments, timeframes, family, risk profile, pod. | "by the time a bot is whether created, whether being stress tested, it should have a journal" (T1:1177) | 24 Oct | RULED | STATE corr 6 |
| J-03 | The journal is the unit's DevOps layer: monitoring, logging, observability. Agents write in it too (analysis, proposals that render in the UI). Record trades taken, signals seen but not taken, missed trades. | "this is literally the DevOps layer for that unit" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Journal = the unit's DevOps layer" |
| J-04 | A separate router journal for market-level facts (spread, fees, slippage, sessions per instrument and broker), so unit journals do not duplicate them. Mind the data volume. | "we need to separate the journal for the router" (T1:1574) | 27 Oct | RULED | STATE 27 Oct |
| J-05 | Performance-over-time studies (unit, family, pair, as the old WF3 did) and portfolio optimisation come from journals. | "we can redesign better methods based off just journals" (T1:1574) | 27 Oct | SEED | STATE 27 Oct |
| J-06 | How agents read journals, how the Library stores them and how the UI shows them. | (30 Oct, his list of what data and journals cover) | 30 Oct | RULED (scope) | STATE run "Corrections, 30 Oct evening" |
| J-07 | The journal is "anything that can record data" and wants "most simple data schemas". | "I would prefer most simple data schemas." (T2:1148) | 27 Oct, 30 Oct | SUPERSEDED by J-01 | 43 F4 (followed the superseded words) |

## 6. QMB

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| B-01 | QMB is not live trading. Backtest and stress test are one world; live trading on the node is another. | "I hope you haven't confused QMB and live trading." (T1:1177) | 24 Oct | RULED | STATE corr 4 |
| B-02 | QMB is a tool an agent calls; it runs and waits, the way a test suite runs, and returns results the agent does not tinker with. | "It runs the same way you run your tests." (T2:135) | 29 Oct | RULED (as intent) | 43 §3.4 |
| B-03 | Professional quant level for agents, so agents never hand-roll backtest code. Base on QuantConnect LEAN CLI logic; consider Jesse; StrategyQuant's what-if scenarios can improve. | "your whole goal is building something that agents can use, but at the same time at a professional quantitative trader level" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "QMB" |
| B-04 | All instrument types supported by default. | "we need to cater for them by default" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "QMB" |
| B-05 | No lookback limit. 1990 is allowed; post-COVID is a sensible default, never a cap. | "there is no point in me being refused that" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Unbounded by default"; research 12, 14 |
| B-06 | Toss or rebuild QMB, combining LEAN, Jesse and StrategyQuant. | "Now we either toss or we rebuild QMB based off this." (T2:135) | 29 Oct | SEED, resolved by B-07 | 43 §3.4 |
| B-07 | The lead's call on B-06: rebuild the core loop around the unit (windowed reader, a runner that trades, the agent door, what-if scenarios, the judge, perps funding cost), extend results with R, keep the measuring parts that work. | (lead) | 30 Oct | LEAD'S CALL | 43 §3.4; 52 §4 QMB row |
| B-08 | Do not discuss QMB with him; understand it from the code, the docs and the 20-28 Oct session (mostly handled there). | "I don't want to talk about it. First understand it." (T2:219) | 29 Oct, 30 Oct | RULED | STATE run "Corrections, 30 Oct evening" |
| B-09 | Judging. "Judging is the product" is right. Look at how professional quants judge; do not be too strict. Judge from historical and paper trading; define when to paper trade and the sequence. Account for the old system's special ("radioactive") sizing. Make judging a skill (hooks plus deterministic scripts that call QMB). Agents judge from results and propose; they never decide by eye; proposals render in the UI. | "we don't want to be too strict" (T1:1574); "judging and improvement should come from historical and paper trading" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Judging" |
| B-10 | Iterate on strategies the way desks do, without overfitting. | "But at the same time, we need to make sure we don't overfit." (T2:135) | 29 Oct | SEED | research 26 |
| B-11 | StrategyQuant as an anchor to expand from: the what-if generator, fitness bank, QuantAnalyzer, QuantDataManager; its biggest fit is the Lab. | "I think one of the most interesting platforms we might look at is StrategyQuant." (T1:828) | 24 Oct | SEED | research 03 |
| B-12 | QMB owns the backtest door (PR 204 handed to the unit work). | (his ruling relayed in the handoff file) | 24 Oct | RULED | STATE "QMB backtest door" |
| B-13 | Recover what the old system proposed for backtesting and why it was refused; the old one may be partly better. | "the old system also had a lot of things to propose. I don't know why we refused them." (T1:1574) | 24 Oct, 27 Oct | SEED, answered (research 08, 14: he deferred them himself on 20 Aug) | research 08, 14 |

## 7. The Library and data

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| L-01 | Historical data is the Library's job, not this run's. Assume the data will be there and agents can use it (dukascopy-node exists). | "Just know the data will be there." (T3:903) | 31 Oct | RULED | STATE am r8 |
| L-02 | Recording data: use the Library; it may already be covered by the shipped data PRs. | "We have a library, we should use it." (T3:903) | 31 Oct | RULED | STATE am r11 |
| L-03 | Everything must fit the Library: router logs, journals, caches. The same compute, different positions. | "make sure that most of these things can fit into the library we have" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Router" |
| L-04 | Everything a workflow produces is stored in the Library. | "everything that a workflow produces is meant to be stored in the library" (T2:325) | 29 Oct | RULED (as fact of the design) | chat only |
| L-05 | QMX collects its own live market data across most instruments. | "should be collecting his market data, live market data" (T2:219) | 29 Oct | SEED (consistent with L-02) | 43 §3.5 |
| L-06 | Who provides data (order flow and the like) is separate from which broker executes. | "But that's mostly for brokers. In other words, trade execution." (T2:1000) | 30 Oct | RULED | STATE run "Data versus execution" |
| L-07 | Data quality and cleanliness (Dukascopy, dukascopy-node, other sources). | "in terms of data quality, data cleanliness, we might need to know" (T1:1574) | 27 Oct | SEED (researched in 12, 33); the terms questions are not his (see section "settled") | research 12, 33 |

## 8. The trading node (priority two)

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| N-01 | The trading node comes second, after QML. | "The trading node is a second tier." (T3:1264) | 31 Oct | RULED | STATE mid r10 |
| N-02 | The trading node gets its own pass. It runs on his machine first, then on a server. How units deploy from his machine, how results come back, how it is monitored, the kill switch, what is automated. The stack may change; he doubts Python covers all of it. | "How are we going to be able to deploy units from my machine?" (T3:903) | 31 Oct | RULED | STATE am r16 |
| N-03 | The node is set for Linux because most VPSs are Linux. WSL on his PC is acceptable as the fallback "if all goes south". | "It's set for Linux because most VPSs that we're going to be using work with Linux." (T3:1096); "we can go with WSL, okay? If all goes south." (T3:1096) | 31 Oct | RULED | STATE Q3 |
| N-04 | How does the node place live trades: through broker APIs, or does it need the platform app on the machine? The lead's chat answer (cTrader Open API with a web sign-in token; Hyperliquid and CCXT web APIs; only MT5's Python link and NinjaTrader need their Windows desktop apps) is to be checked in grounding. | "Is it going to place and execute trades via an API?" (T3:1096) | 31 Oct | OWED (the check) | STATE Q3 |
| N-05 | Out of the box: start a trading node, see it started, deploy with little stress. | "is it going to start as server, then show me that the server has started?" (T3:1102) | 31 Oct | RULED | STATE Q5 |
| N-06 | A server can be a server: no special machine names on his screens. | "A server can be a server." (T3:1102) | 31 Oct | RULED | STATE Q5 |
| N-07 | Setting up a node is as simple as renting a server from a provider (a wizard or one click). The UI already proposes an external compute provider setting. One node to start, maybe more later. Ground on the wrap-up PRs first. | "a trading node should be as simple as how, for example, I can set up a server from a provider" (T2:1148) | 30 Oct | RULED | STATE run "The trading node" |
| N-08 | The node exists because his laptop goes off (power cuts, Wi-Fi drops); markets now run 24/7. Network-bound speed justifies the node further. | "we are literally trading 24/7, my days. This is why we need a trading node." (T2:325); "Which means the trading node is justified more." (T3:903) | 29 Oct, 31 Oct | SEED (the reason the node exists) | STATE run "The trading node" |
| N-09 | Node = a trading server: a home for trusted units after backtest, stress test and his admission. Reuse the "connect a machine" design. Self-tests on connect (kill-switch speed, a test trade, broker and platform connections, network speed). Kill switches at several levels, some firing without his PC. | (21 to 22 Oct seeds, recorded by the lead) | 21 Oct, 22 Oct | SEED | seeds §"Trading node = a trading server" |
| N-10 | Ruling 135 (no live-trading grant on his PC) is a code fact the node pass handles technically, not a question for him. | (lead, from his 31 Oct words) | 31 Oct | LEAD'S CALL | STATE am r9 |
| N-11 | The node holds the MIS and the kill switches. | (21 Oct seed) | 21 Oct | SUPERSEDED by M-08 (only the fast part of the MIS sits on the node) | seeds §"Trading node = a trading server" |
| N-12 | The trading node "after the unit work, in its own fresh session". | (21 Oct seed) | 21 Oct | SUPERSEDED by N-02 (its own pass inside this run) | seeds §"Trading node = a trading server" |

## 9. External connections

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| X-01 | Markets first: forex, futures, metals and CFDs (indices, perps and crypto stay in scope). cTrader first, Hyperliquid second; he already has Hyperliquid accounts, so there is no country question. Crypto goes through CCXT, which is a standard and already built. | "Let's go with FX, futures, metals, of course CFDs." (T3:903); "Hyperliquid can't ban me from to be trading. I already have accounts there." (T3:903); "CCTX is a standardized version." (T3:904) | 31 Oct | RULED | STATE am r10 |
| X-02 | The April rules are scrapped. Leverage is used; futures, CFDs, perps and indices are traded as they come; swap-free or other pickiness only if risk and sizing needs it later. | "Yeah, scrap those rules, all of them." (T3:1099); "For now, let's trade them the way they come." (T3:1099) | 31 Oct | RULED | STATE Q4 |
| X-03 | Futures platforms. cTrader may not handle futures. Find a free platform or feed with order-flow data (no paid platform; check Sierra Chart's cost). Algorithms need order-flow data, not order-flow charts. | "I don't want to pay for a platform, I'm not gonna lie." (T3:1264); "They need order flow data." (T3:1264) | 31 Oct | RULED, research OWED | STATE mid r14 |
| X-04 | Explain futures and indices to him, and what trading them needs. | "Okay, you explain to me what futures, then indices." (T3:903) | 31 Oct | OWED | STATE am r10 |
| X-05 | External connections were handled a lot already (the local-first stack, cTrader, CCXT); know what you will touch. The code says cTrader is close, CCXT reads spot only, MT5 is a declaration and Hyperliquid has no code (research 52 §4). | "external connections actually was, I already told you yesterday, it was handled a lot" (T3:903) | 31 Oct | RULED (ground first); see "missed" item 9 | STATE am r1; 52 §4 |
| X-06 | What standards each platform's API tells us to use (cTrader's Open API, NinjaTrader and others), in a technical lens. | "What standards does OpenAPI versus CTrader tell us to use?" (T3:903) | 31 Oct | OWED | STATE am program step 1 |
| X-07 | Can he trade real futures on cTrader, with order flow? Hyperliquid's API and limits; what the node must hold. | "Can I trade futures on CTrader?" (T2:858) | 30 Oct | SEED, answered (research 38: no real futures on cTrader; a futures broker is needed) | research 38 |

## 10. Contracts and APIs

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| C-01 | Contracts and APIs, internal and external, across platforms. Every connection point gets its own design: who connects to whom, where, and what data crosses. | "How do they connect? Who do they connect with?" (T3:903) | 31 Oct | RULED | STATE am r2, r3 |
| C-02 | Internal contracts: QML, and the copilot and agents writing to QML, with in-loop feedback (see Q-06). | "Then, of course, we have internal contracts, QML itself, copilot or agents to QML." (T3:1264) | 31 Oct | RULED | STATE mid r12 |
| C-03 | External contracts: what the new parts need from outside, above all live trading, which is partly covered. | "what do these new additions need externally? Live trading, which I think might have been catered for a bit" (T3:1264) | 31 Oct | RULED | STATE mid r12 |
| C-04 | How a unit connects to the MIS, in code. | "How, in terms of code?" (T3:903) | 31 Oct | OWED | chat only |
| C-05 | The back end in a technical lens: high-level and low-level design, which APIs exist. | "You really not think through the back end properly in a technical lens." (T3:903) | 31 Oct | OWED | STATE am r1 |
| C-06 | The risk socket as a male and female connector: design a template now and leave it, so the risk session's result wires straight in, the way JSON can describe a whole n8n system. | "more like a male and female connector" (T2:135) | 29 Oct | RULED | PACK §4; 43 §8 "The risk socket" |
| C-07 | QMF, QML, QMN and QMA v2 will be touched in depth; the docs are out of date, so the code is the truth. | "QMF specifically, I think is going to be touched in great detail" (T2:1148); "the documentation is not up to date, okay? It's not at all." (T2:1148) | 30 Oct | RULED | STATE run "Corrections, 30 Oct evening" |

## 11. Clocks and time

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| T-01 | Clocks and time zones. Trading nodes in Singapore and London keep different local times; treat a node like a firm whose local time is the node's time. Monitoring a crypto node in Singapore and an FX node in London together must work. | "the trading node is perhaps a firm" (T3:903) | 31 Oct | RULED, design OWED | STATE am r15 |
| T-02 | Trading 24/7 means no end of day; when reviews and plans run. | "we are literally trading 24/7, my days." (T2:325) | 29 Oct | SEED | 43 §4 "Review timing in 24/7 markets" |

## 12. DevOps

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| O-01 | The DevOps layer: observability, logging and monitoring across the parts and machines, plus the back end behind it. OpenObserve was planned. | "we were planning on using OpenObserve" (T3:903) | 31 Oct | RULED, design OWED (two stacks exist: QMN's Grafana, Loki and Prometheus, and the host's OpenObserve; 53 §2 item 8) | STATE am r3 |
| O-02 | The journal is the unit's DevOps layer (J-03); the node is monitored from his PC (N-02, T-01). | (see J-03, N-02, T-01) | 27 Oct, 31 Oct | RULED | as cited |

## 13. QMA v2, the copilot and agents

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| A-01 | QMA v2 is in scope. Anything an agent under QMA can do, the copilot can already do. Ground on the recent PRs that touch QMA v2 and widen the search. | "Remember, anything that an agent under QMA can do, the copilot should already be able to do." (T3:1264) | 31 Oct | RULED | STATE mid r8 |
| A-02 | The agentic side is already built in QMA v2. The work is workflow templates on top of it, not new agents. | "Agentic stuff is already done. Look at QMAV2." (T2:1148) | 30 Oct | RULED | STATE run "Corrections, 30 Oct evening" |
| A-03 | Agents as analysts, in two families: analysis of markets and analysis of units. They must prove their analysis with something that cannot be cheated (skills, scripts, tools). | "analysis based off the markets themselves and also analysis based off the units themselves" (T2:385); "something that can be, that can't be cheated" (T2:385) | 29 Oct, 30 Oct | RULED (as seed to expand) | STATE 29/30; research 29 |
| A-04 | Analyst agents use live data and today's charts, with a landmark window, not training memory. The "model may remember past markets" worry applies only to building on history. | "They are going to be using live markets" (T2:385); "you need to give a pass, in other words, a landmark" (T2:385) | 30 Oct | RULED (correction) | 43 §4 |
| A-05 | "Agents never touch money" is moot. QMX cannot touch money by design, and QMA v2 already enforces it. | "I think this was already built in QMEV2." (T3:1105) | 31 Oct | RULED | STATE Q6 |
| A-06 | Hooks are very important: standards stop cheaper models making big mistakes. | "this is why hooks are very important in this system" (T1:1574) | 27 Oct | RULED (as intent) | STATE 27 Oct |
| A-07 | A copilot can remake most of what is designed (pods and the rest). | "a copilot might remake most of what you've done" (T1:1574) | 27 Oct | SEED | STATE 27 Oct "Unbounded by default" |
| A-08 | Agent memory is required for the strategy funnel, so failures and conditions are remembered across runs. | "Now, this is why we needed agent memory, dude." (T1:513) | 20 Oct | SEED | seeds §"Strategy funnel" |
| A-09 | Cheap workhorses do the bulk; a stronger model attempts the rewrites. The shipped default is the reverse (strong builder, cheap judge); editable. | "most of the work I've been talking about is done by cheap workhorses" (T1:513) | 20 Oct | SEED (the default is open) | 43 §5; research funnel7 finding 3 |

## 14. QMX workflows (inside the product)

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| W-01 | Build the workflow templates; they can be removed or improved later. They read the MIS's logs (M-09). | "Workflow templates, yeah, build them." (T3:903) | 31 Oct | RULED | STATE am r12 |
| W-02 | Take the workflows from the Hermes sessions ("Friendly greeting" and the gold mine, close to the old WF1 and WF2) and enhance the shipped templates, beside the new analyst workflows. Needs a real understanding of how QMA v2 runs workflows. | "It's far better to enhance them." (T2:1148) | 30 Oct | RULED | STATE run "His calls on research 34 and 35" |
| W-03 | The admission envelope is agent-driven through the workflow system: a default now, enhanced after QMX is live. | "it's mostly agent-driven" (T1:1903) | 28 Oct | RULED | STATE 28 Oct |
| W-04 | The strategy funnel as levels with branches: source, idea, build in QML, test in QMB, then pass (iterate, domain expansion), fail (why it failed, any context where its rules hold), rewrite. "Most strategies can work." The expansion workflow is designed in its own conversation. | "Think of it like levels, okay? With branches." (T1:513); "Most strategies can work." (T1:513) | 20 Oct | SEED | seeds §"Strategy funnel" |
| W-05 | Domain expansion has two kinds: bounded (development: logic and variants) and live (where the MIS points a unit). | "There is domain expansion and bounded domain expansion" (T1:1903) | 28 Oct | SEED | STATE 28 Oct |
| W-06 | Agents read that day's data and charts and work like a trading journal; an organogram of specialised analyst agents. Build now, or as a mini app. | "think of an organogram" (T2:325) | 29 Oct | SEED | 43 §3.7 |
| W-07 | Finding strategies and filtering them are two puzzle pieces; filtering is where workflows come in. | "filtering is where I think we might need workflows" (T1:1574) | 27 Oct | SEED | research 11 |
| W-08 | The MQL5 articles are used later inside QMX, through mini apps and workflows. | "it's better to use those articles when you reach inside QMX to build on top of QMX" (T1:1177) | 24 Oct | RULED | STATE corr 9 |
| W-09 | Build templates in the coding phase, or write them up in detail now (maybe the Lab's first job). | (his two options, 30 Oct) | 30 Oct | SUPERSEDED by W-01 | 43 decision 6 |

## 15. Mini apps

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| MA-01 | Look at mini apps. Units may need to be integrated in mini apps. | "units might be need to be integrated in mini apps" (T3:1102) | 31 Oct | RULED (look); SEED (integration) | STATE Q5 |
| MA-02 | Mini apps are the foundation pattern: he created them when expansion hit its limit. The same logic shapes this architecture. | "I proposed the creation of mini apps" (T3:1264) | 31 Oct | RULED (as the pattern to follow) | STATE mid r6 |
| MA-03 | A mini app may rewrite a unit's logic in plain Python, or hold an ML ensembler. | "If I want to rewrite the logic of a unit, maybe as part of a mini app" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Unbounded by default" |
| MA-04 | The Lab shipped quite well and will improve; it shares the pattern. | "If you look at the lab, I think it was shipped quite well." (T3:1264) | 31 Oct | SEED | chat only |

## 16. The UI

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| UI-01 | Write down what the UI needs, in the files that exist for it (`tracker/qma-v2/UI-NOTES.md`, `UI-HANDOFF.md`). | "If there are things to add in the UI, you write them down." (T3:1264) | 31 Oct | RULED, OWED | STATE mid r15 |
| UI-02 | The family tree in the UI has a preview (small summary) and a detailed view (journals, lineage, pairs, history, backtest results). | "we have a preview and a detailed view. So, design for both." (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Lineage and history" |
| UI-03 | The UI is judged by its design, by running it, never from its code. | "don't look at the UI in terms of code, because the code is not right. Look at it in design." (T2:1148) | 30 Oct | RULED | STATE run "Corrections, 30 Oct evening"; MEM ui-is-design-not-code.md |
| UI-04 | Agent proposals and analysis render in the UI. | "And the proposal should be rendered in the UI." (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Judging" |
| UI-05 | An external compute provider setting is already proposed in the UI settings; UI designs are not set in stone. | "in the settings in the UI, we proposed that we have an external compute provider" (T2:1148) | 30 Oct | SEED | UI-HANDOFF.md |

## 17. Risk and sizing (kept as a socket here; the content is its own session)

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| R-01 | Risk and sizing is out of this run's scope but part of the unit. Leave room for it (the socket, C-06), use placeholders (U-04), and later design it with the same foundation approach. | "risk and sizing, that's already out of scope for now, but it's part of the unit" (T3:904) | 31 Oct | RULED | STATE am r3; STATE mid r6 |
| R-02 | Write down every risk and sizing point in the files that exist for them (`RISK-SIZING-PACK.md`), including the list of placeholders to rip out. | "Risk and position sizing, you write them down in the various files you have access to." (T3:1264) | 31 Oct | RULED, OWED | STATE mid r15; STATE Q1 |
| R-03 | The risk session gets a pack of his own words, not a fresh hand-off written from scratch. | "I don't think a fresh handoff." (T2:1208) | 30 Oct | RULED (delivered as the pack) | PACK |
| R-04 | Exit methodology, stops, targets, time-varying targets, profit caps, account-wide halts and probability exits go to the risk session. The unit owns its exits; the old "exits owned outside the bot" is reversed. | "this part really should be part of the risk management and position sizing session" (T2:1000); "the unit is going to own its own exit" (T2:1000) | 30 Oct | RULED | STATE run "His calls on research 34 and 35" |
| R-05 | Combine the old relentless ("nuclear") system with the organised Book and BMS into one standard. The old one "is very good at accelerating growth, which means quantity doesn't matter, quality might matter". | "we are going to combine the old systems version and then the book version to create a standard one" (T2:1000); "quantity doesn't matter, quality might matter" (T2:1000) | 30 Oct | RULED (risk session's work) | PACK §2.2 |
| R-06 | The book and correlation control (units not stacking the same bet) belong to the risk session. | "No, I think this is under risk management operation sizing." (T2:1148) | 30 Oct | RULED | PACK §6 |
| R-07 | Size growing back after a cut, and house money: not decided. A deeper session, explained mathematically, with CUSUM and loss points explained there. | "I think in a more mathematical sense" (T1:1574) | 27 Oct | RULED (not decided; risk session) | STATE 27 Oct "Risk and sizing"; PACK §2.3, §2.5 |
| R-08 | Account guard and pod: standardise them, possibly combine; the pod is effectively the BMS; the Book is overkill. An open question he put back to Claude. | "maybe let's combine it with the pod. What do you think?" (T1:1574) | 27 Oct | SEED (risk session) | PACK §2.7, §6 |
| R-09 | At $300, two active units use the whole budget; as units are added, the numbers reconfigure themselves. | "those two bots should be able to use all the 300" (T2:219) | 29 Oct | SEED (risk session) | PACK §2.8 |
| R-10 | Self-configuration is mostly under risk and sizing. | "self-configuration is mostly under the risk management and position sizing" (T2:219) | 29 Oct | SEED | PACK §2.1 |
| R-11 | Units go back to paper at times; that is known risk practice and the journal must carry it. | "there are times whereby a unit will go back to paper trading. That is known." (T3:903) | 31 Oct | RULED (as a fact the design honours) | STATE am r14 |
| R-12 | The guards (spread quality sensor, news kill switch, account guards) work independently of the router. | "most of that should be independent of the spread quality sensor, new skill switch" (T1:1574) | 27 Oct | RULED | STATE 27 Oct "Router" |
| R-13 | "Funding" in his words is the money part of a unit (risk and sizing), not perps funding. | "the money part of a unit, the risk management and position sizing system" (T2:135) | 29 Oct | RULED (meaning) | 43 §8 parked list |

## 18. Process: how the planning run and the build work

| ID | Item | His words | Date | Status | Lives now |
| --- | --- | --- | --- | --- | --- |
| P-01 | The end goal is an orchestrator prompt that uses poteto-mode. Tonight he comes back for one thing: that prompt. Plan as much as possible first; the building agents do most of the testing and review. | "all I want to come back to is a prompt for an orchestrator to code" (T3:1264); "all I want is for you to give me a prompt that uses potato mode" (T2:24) | 29 Oct, 31 Oct | RULED | STATE mid r3 |
| P-02 | The workflow stays his: party mode with brainstorming for the solutions; CIS for his day-to-day experience; party mode again for the versions of the architecture and the foundation set; bmad-architecture is required, and Winston (the architect persona) joins party mode. No prototype skill. Blast radius sits inside the architecture step. bmad-review may serve during coding. poteto-mode runs the coding. | "I think our workflow is what we need" (T3:1264); "you can't skip BMAD architecture, you really can't" (T3:1264); "no skill cluster caters for coding more than potato mode" (T3:1264) | 31 Oct | RULED | STATE mid r4 |
| P-03 | The lead gets its own skills view from its own sub-agent and compares it with Fable's and his. | "you should either get your own version with your own sub-agent and compare" (T3:1264) | 31 Oct | RULED (this file's sibling) | STATE mid r4; `architecture/00-workflow-and-skills.md` |
| P-04 | Start with a pass through the whole conversation, then fold the architecture with the latest decisions. | "First pass through this entire conversation across maybe a workflow or two." (T3:1264) | 31 Oct | RULED (this file) | STATE mid r5 |
| P-05 | Do not keep expanding. Expansion without a base grows too big to maintain; that is why mini apps exist. | "if we spend this time just expanding, we're not going to do much" (T3:1264) | 31 Oct | RULED | STATE mid r6 (implied) |
| P-06 | The earlier sessions' designs and explainer sites may already solve much; check whether they were carried forward. | "most of the things actually might have already been solved by that transcript or the previous session" (T3:1264) | 31 Oct | RULED | STATE mid r9; 53 §2 item 2 |
| P-07 | No more Fable agents until he asks. | "And no more feeble agents, they're unnecessary at the moment." (T3:1264) | 31 Oct | RULED | STATE mid r16 |
| P-08 | Use the wayfinder skill; stop firing in many directions; use the tools at hand (context7 was added). | "I told you to use the wayfinder skill." (T3:913); "It's as if you are trying to fire in so many directions." (T3:913) | 31 Oct | RULED (the midday workflow does not name it; see contradiction 29) | STATE am "His nudge" |
| P-09 | Be efficient with agents: one agent takes several related tickets; no spawning for its own sake; one agent per job. | "If more than two things can be handled by one agent, do so." (T3:563); "All this can be done by one agent." (T1:1443) | 25 Oct, 30 Oct | RULED | MEM group-related-work-per-agent.md; MEM one-agent-per-job.md |
| P-10 | Launch agents with intent. | "I hope you are launching these agents with intent" (T2:858) | 30 Oct | RULED | STATE run |
| P-11 | Heavy reading goes to agents, never the lead's own context. | "don't do the code grounding, dude. You are going to mess up your context" (T2:1208) | 30 Oct | RULED | STATE run "He handed over the wheel" |
| P-12 | The lead drives; call BS or make the better call, since it is more technical than he is. Bring him only real ambiguity. | "you can either call BS or make a better call because you are more knowledgeable" (T2:135); "I want actual ambiguity, not things you yourself can figure out" (T1:1177); "I think you take the wheel from here on out." (T2:1208) | 24 Oct to 30 Oct | RULED | STATE corr 11 |
| P-13 | Everything he says is a seed; agents read his verbatim words, never a summary. | "verbatim might be necessary" (T2:439) | 30 Oct | RULED | STATE 29/30; standing orders 2, 3 |
| P-14 | Branches: planning on `plan/unit-system`, building on `build/unit-system`; the merge target is decided later, never `main`. | "Plan, then unit system, then build unit system." (T2:442) | 30 Oct | RULED | STATE 29/30 |
| P-15 | Research is done by the lead's sub-agents (Codex paused, not trusted for this work), through Exa; Firecrawl is nearly out of credits; the built-in browser is not trusted. | "even the research is going to be done by your sub-agents" (T3:515) | 30 Oct | RULED | STATE run "Research moves to Claude agents" |
| P-16 | Coding later goes partly to other models; "we shall see how to do this". | "I'll hand over the coding to other models precisely" (T3:515) | 30 Oct | SEED (open; see "owed" item 13) | STATE run "Research moves to Claude agents" |
| P-17 | Words for him are plain and short; he dictates; no codenames. | (standing) | standing | RULED | standing order 14 |
| P-18 | Write everything down; nothing lives only in chat. | "I think you should update it properly." (T1:1297) | 24 Oct | RULED | MEM (STATE update rule) |
| P-19 | No explainer site for the planning run; everything in chat and the files. | "No need for an explainer site." (T2:602) | 30 Oct | RULED | STATE run "Operator away" |
| P-20 | Party mode on how to build it, high level and low level, before bmad-architecture folds anything. | "Party mode has to come in. I'm proposing it comes in" (T2:709) | 30 Oct | SUPERSEDED by P-02 (now step three of his workflow) | STATE run "His proposal for the architecture step" |
| P-21 | No rush: planning may take three to four days; sloppiness is not tolerated. | "This planning and brainstorming and architecture can take up to 3 to 4 days" (T2:845) | 30 Oct | SUPERSEDED by P-01 (code tonight); "no sloppiness" stands | STATE run "No rush" |
| P-22 | Pause for him before folding the architecture. | "before you fold the bloody architecture" (T2:1208) | 30 Oct | SUPERSEDED by P-01 (plan through to the prompt; he returns only for it) | STATE run "PAUSED" |
| P-23 | Broaden before defining; "we are like taking 5% of what we are actually meant to be solving". | "I think we are like taking 5% of what we are actually meant to be solving" (T2:325) | 29 Oct | SUPERSEDED by P-05 for this run (the funnel in P-02 is the broadening) | STATE 29/30 |
| P-24 | Codex runs the research on his own time. | (29 to 30 Oct) | 29 Oct | SUPERSEDED by P-15 | STATE run |
| P-25 | Edge-case review after the architecture. | "edge case working is very important" (T1:651) | 24 Oct, 30 Oct | RULED (kept by the lead's midday program step 5 as one review and one fix round) | STATE mid program step 5 |
| P-26 | The lead's midday program: grounding (three agents) plus this ledger and skills view; funnel (party mode with brainstorming; CIS); party mode on the versions, then bmad-architecture Level 0 and the connections; bmad-architecture per part in four grouped agents; one review and one fix round; the checked build plan, the orchestrator prompt and the builder prompt, in `architecture/`. | (lead) | 31 Oct | LEAD'S CALL | STATE mid program |
| P-27 | Add the foundation stance to memory so new sessions know it. | "add it there so that any other session I begin knows that the way we handle units and stuff is foundational" (T3:1264) | 31 Oct | RULED, done | MEM foundation-first-design.md |
| P-28 | The docs are out of date; every agent that reads `docs/` is misled. A doc pass after the build, which nobody has scheduled. | "the documentation is not up to date, okay? It's not at all." (T2:1148) | 30 Oct | OWED (scheduling) | 52 §4 Docs row; 43 "Subtract first" item 7 |

---

## What he means that the lead missed or mis-heard

Each item gives his words, what was heard, and what he meant. The evidence is the cited line plus the lead's own reply around it.

1. **"It works" means the unit idea holds, not a feature list.** The lead offered eight "proof tests" (T3:1120-1128). He answered "So the proof tests make no sense to me" and asked "does a unit actually make sense?" (T3:1145). He means: a bot leaned on many parts and did not tune itself; a unit tunes itself and leans on few; show that this holds in code.
2. **"Prove it in practice" means real parts, not a throwaway.** The morning program had "small prototypes" (STATE am program step 4) and research 53 a two-day throwaway. He: "I can't wait 2 days for you just to code something and throw it away" (T3:1264). The proof is the dummy unit on the real template.
3. **"One file is not enough" means packets per area, with depth.** The lead heard "not detailed". He: "I thought it's going to be more than one file. You know, one file specifically compiling everything we have on QML" (T3:903). He builds one area per session with one builder each.
4. **"Like JSON" was an analogy.** The convergence wrote "the unit is one JSON document" (43 F3). He: "I mean, my analogy made sense, but it's an analogy." (T3:903).
5. **Journals need depth; the lead followed his older "simple" words.** 43 F4 followed "anything that can record data" (T1:1574) and "most simple data schemas" (T2:1148). His newest word is the multi-dimensional journal (T3:903, J-01).
6. **Templates read the MIS's logs, not the model.** The lead wrote that templates would use the MIS. He: "Using a direct model and then using the logs from a model are two different things. All right, so that's sloppy wording." (T3:903).
7. **"You drive" means own the technical calls.** On 31 Oct the walkthrough led with nine decisions (T3:815-837). He had said "call BS or make a better call" (T2:135) and, at midday, "You already know what I want." (T3:1264). The calls belong to the lead, logged in a line.
8. **"Nothing is set in stone" means do not close a design before grounding; it does not mean re-ask him.** He was angry at re-asked items: "I thought we were done with System 1 and System 2" (T3:903).
9. **"Already set up" means "coded and stacked", and he expects the lead to say which is which.** He: "there are already connections set up for these things" (T3:903). The code: Hyperliquid has no lines, CCXT reads spot only, MT5 is a declaration, the cTrader sign-in never ran, and the trading node was never deployed (52 §4, §8 item 4). Report "built / stacked / missing / never run" per part, never "decision for you".
10. **"The trading node was finished in the latest PRs" (T2:439) conflated two machines.** The wrap-up shipped a workflow server; the trading node is QMN, 98,000 lines, never deployed (52 §8 item 5).
11. **"Windows first" plus "Linux node" is not a contradiction.** He prefers not to manage two operating systems on his PC (T3:903), and he accepted the node on Linux because servers run Linux, with WSL on the PC only "if all goes south" (T3:1096). Design the PC side Windows-native; the node is a Linux program; WSL is the fallback for rehearsal.
12. **"Funding" is the money part of a unit.** He: "the money part of a unit, the risk management and position sizing system" (T2:135). Agents read perps funding (44 A04).
13. **"It's numbers" was him reading the lead's option back** before asking how the if-else rules self-tune (T2:788; 44 A01). It is not his answer.
14. **System 2 includes per-market logic changes.** His EMA crossover example: "changing or enhancing different logics for different markets" (T1:1903). The first convergence kept only "a market's own settings" (44 A02).
15. **"Quantity doesn't matter, quality might matter" was written backwards** as "quantity over quality" (T3:133; fixed in STATE).
16. **"Multiple experiences" is his own experience as the user** making money with units, and what gives QMX an edge over a simple bot (T2:858).
17. **"A model may remember past markets" missed his point.** He described agents reading today's live charts (T2:385). The risk applies only to agents building units on history.
18. **"Lean" was the wrong word.** He wants "keep it stupid simple" and "design for complexity, not a complex system" (T2:1208), then let the lead pick a wording that does not slide into "easy and incapable" (T2:1219).
19. **"Specialist", "terrain", "System 1/2" were never his terms.** "Terrain was not mine" (T2:788); "Specialist, what do you mean by a specialist?" (T2:788).
20. **"Market context" is the trader's sense, not an invented MIS word.** "you can't tell me market context is something that you are not understanding" (T2:788).
21. **"The MIS is incomplete" means it was never designed per instrument class.** He thinks the MIS "is mostly using HMM, BOCPD, MS, GARC" (T1:1951), but nothing fitted is live: six rule labelers and SQS run inside QMN, which never ran (52 §4 MIS row). He wants defaults that cover every class now and room for his own models (M-02).
22. **"The real-money key" was the wrong frame.** He: "QMX realistically never touches money" (T3:903). The trading grant still has to sit where orders are placed; that is a node design fact (ruling 135 in code), never a question for him (52 §5).
23. **Hyperliquid and his country.** "It's not about my country allowing it. ... I already have accounts there." (T3:903). The lead and research 38 asked it twice.
24. **Historical data is not this run's job.** "For example, data, historical data, don't cater for them." (T3:903). The data-terms questions (Dukascopy, Binance Vision) were raised to him anyway.
25. **The foundation is the mini-app pattern.** "I proposed the creation of mini apps. Mini apps came in because of the same pattern." (T3:1264). A solid core with freedom on top, not a pile of features.
26. **"Who expands the dictionary? You have to give them directions."** (T3:1264). He expects explicit grounding directions in the builder briefs, with no caps.
27. **"Look at how agents factor their code. Maybe we use hooks."** (T3:1264). The check must reach the agent while it writes, as an in-loop error with no false positives, not a review after the fact.
28. **"Wilson" is Winston, the BMad architect persona** (T3:1264). On 30 Oct "is it Marcus who's part of the party mode thing?" (T2:1219) points at the same persona (INFERRED).
29. **The Hermes notes are GPT's work, not his** ("Okay, the hammer's not mine. Those things were not mine, they were from GPT.", T2:219). They are seeds he valued, not his rulings.
30. **The 31 Oct "PRs are merged" was true after his clicks.** He merged 207 to 234 into `engine/base` between 05:13 and 05:25 UTC; only PR 204 and the old draft 25 stay open (53 lead's note). Do not ask him to "land the stack".

---

## Contradictions settled by recency

Each line: the older position, the newer one, which wins.

1. **What a unit is.** Strategy plus sizer plus record (13 Oct, Claude's baseline, never agreed) → one complete algorithm (24 Oct) → "a self-configuring trading bot" (30 Oct, T2:788) → confirmed as Fable's ruling 1 (31 Oct, T3:1105). **Wins:** one complete algorithm including its own sizing and exits, with placeholders now (U-01, U-04).
2. **Where the MIS sits.** Blocks inside the unit (20 Oct lean) → a router outside (20 Oct, T1:376) → never switches (27 Oct) → reads and outputs, units pick (28 Oct, T1:1951) → confirmed (31 Oct, T3:1105). **Wins:** M-01.
3. **Do units read the MIS?** "Bots never read the MIS" (Claude's 20 Oct restatement) → units read live data and MIS output (27 Oct, D27) → units pick the output (28 Oct). **Wins:** units pick from the MIS's output and stand alone on their own feed (M-01, CC-12).
4. **One logic on 1m and 5m.** Two bots (20 Oct, T1:484) → one correlated idea (30 Oct, T2:1000). **Wins:** U-09.
5. **New instrument.** Sibling unit (27 Oct, T1:1574) → joins the unit's universe; only a logic change makes a new unit (28 Oct, chat, never confirmed) → names settled, he will think about market settings and market version himself (31 Oct). **Wins:** the 28 Oct view as the working assumption; the design supports both halves (U-13, U-14).
6. **Journals.** "Anything that can record data" (27 Oct) and "most simple data schemas" (30 Oct) → depth across instruments, brokers, accounts, platforms, nodes, paper and live (31 Oct). **Wins:** J-01.
7. **The dictionary.** "Permanent" (26 Aug) → "needs a rebuild" (29 Oct) and "redone, most of it" (30 Oct) → "directions, not rules; you haven't proposed it" (31 Oct) → the lead's answer (31 Oct midday). **Wins:** D-01, D-02, D-06.
8. **QML.** Rebuild from scratch (13 Oct) → upgrade into the unit library (24 Oct) → "QML is not new" (31 Oct). **Wins:** Q-03, Q-04.
9. **QMB.** "Toss or rebuild" (29 Oct) → the lead's call, rebuild the core loop and keep what works (30 Oct; research 52 agrees). **Wins:** B-07.
10. **The node and the MIS.** The node holds the MIS (21 Oct seed) → fast part on the node, planning on the PC (24 Oct lead; his yes on 27 Oct). **Wins:** M-08.
11. **Operating system.** cTrader on a server needs Windows (21 Oct) → Linux works (22 Oct) → prefer Windows to WSL (31 Oct 04:05) → node on Linux, WSL as the PC fallback (31 Oct 04:55). **Wins:** N-03 for the node, CC-14 for everything else.
12. **The live key.** Ruling 135 as a decision for him (30 Oct) → dropped for good (31 Oct). **Wins:** CC-13; the node pass handles ruling 135 as code (N-10).
13. **The April rules.** No leverage, swap-free, no futures (April) → scrapped (31 Oct). **Wins:** X-02.
14. **Spot only.** "Eventually shall shift to a spot-only system" (20 Oct) → every market, traded as it comes (31 Oct). **Wins:** X-02; spot-only stays parked.
15. **Timeline.** Code all night (29 Oct) → no rush, three to four days (30 Oct) → coding this morning (31 Oct 03:11) → plan as much as possible, code tonight (31 Oct midday). **Wins:** P-01.
16. **Breadth of the planning.** Broaden first, "taking 5%" (29 Oct) → stop expanding, build the foundation (31 Oct midday). **Wins:** P-05; the funnel in his workflow is the only broadening.
17. **Proof in code.** Small prototypes after the architecture (31 Oct morning) → a two-day throwaway first (research 53) → no throwaway; real parts with a dummy unit (31 Oct midday). **Wins:** CC-17.
18. **Fable.** Advisor on the table (30 Oct) → two Fable reads (31 Oct morning) → no more Fable agents until he asks (31 Oct midday). **Wins:** P-07.
19. **The planning workflow.** The big workflow (29 to 30 Oct) → Fable's cut-down stack (research 53 §6) → his workflow stays (31 Oct midday). **Wins:** P-02.
20. **Pause before the fold.** Pause for him (30 Oct) → plan through to the prompt (31 Oct midday). **Wins:** P-01.
21. **Explainer sites.** Multi-page sites (25 and 27 Oct) → no explainer site for this run (30 Oct). **Wins:** P-19.
22. **Research tool.** Codex (29 Oct) → Claude sub-agents (30 Oct). **Wins:** P-15.
23. **The correlation ledger.** "We have one" (20 Oct) → needed in the router (27 Oct) → not inside the MIS, it may take the MIS's output (29 Oct) → the risk session's (30 Oct). **Wins:** R-06.
24. **Exits.** A variant axis inside QML (24 Oct) → exit maths to the risk session, the unit owns its exits (30 Oct) → placeholders now (31 Oct). **Wins:** R-04, U-04.
25. **Workflow templates.** Build now or write up now (30 Oct) → build them (31 Oct). **Wins:** W-01.
26. **News.** The events dimension opens news units (28 Oct) → news out for now (31 Oct). **Wins:** CC-21.
27. **"Agents never touch money" as a ruling** (28 Oct notes, Fable's list) → moot (31 Oct). **Wins:** A-05, CC-13.
28. **The router's shape.** A load balancer with its algorithms (27 Oct, his analogy) → taken too literally (28 Oct). **Wins:** M-05, M-06.
29. **Wayfinder.** Introduced (29 Oct); "it's very narrow, party mode first" (30 Oct 04:42) → "I told you to use the wayfinder skill" (31 Oct 04:08) → not named in the midday workflow. **Wins:** the 04:08 word stands and is not withdrawn; the lead uses it as the decision index, not as the driver (LEAD'S CALL, see the skills file).
30. **The risk hand-off.** `HANDOFF-RISK-SIZING.md` (27 Oct) → the pack of his own words (30 Oct). **Wins:** R-03.
31. **Where risk and sizing lives** (on the unit, in the pod, or central) and **Book versus BMS.** Not settled by recency; his statements still conflict (PACK §2.10 C1, C2). **Wins:** nobody; the risk session settles it. The socket must not presume an answer.

---

## Owed to him and not yet delivered

In the order the build needs them. Each names where it should land.

1. **The orchestrator prompt**, with the builder prompt and a build plan checked to zero problems (P-01). Lands in `architecture/`.
2. **The layered architecture folded with the latest decisions**: the Level 0 map of parts and connections, one file per part, and a contracts file (CC-16, C-01). Lands in `architecture/`.
3. **The dummy unit on the real template, shown working**, and a plain statement of what "the unit works" means in his sense (U-02, U-05, CC-17). Lands as a packet in the build plan.
4. **How a unit configures itself, shown concretely**, owed since 27 Oct (U-06, Q-12). At least one real number must move by a declared rule from the unit's own record, even with placeholder sizing (53 §3.2). Lands in the unit part file and the dummy-unit packet.
5. **A concrete dictionary rebuild proposal in his register** (D-02). 43 §3.2 is the source; one page in the QML part file.
6. **How agents write units and know they are correct** (Q-05, Q-06, Q-09): the authoring door, the deterministic check, the in-loop hook, and the plain fact that QML's conformance gate already exists (53 §2 item 3). Lands in the QML part file and the contracts file.
7. **The unit-to-MIS connection in code** (C-04). Lands in the contracts file.
8. **Journals in depth** (J-01). Lands in the journals part file.
9. **The trading node pass**: deploy from his PC, results back, monitoring, kill switch, what is automated, how orders are placed, checked against the code (N-02, N-04). Lands in the node part file.
10. **Clocks across regions and the DevOps layer**, including which observability stack wins (T-01, O-01). Lands in the node part file.
11. **MIS defaults for every instrument class in scope, with room for his models** (M-02). Lands in the MIS part file.
12. **External research still missing**: platform languages and API standards (Q-10, X-06), a free futures platform or feed with order-flow data and Sierra Chart's cost (X-03), and a plain explanation of futures and indices for him (X-04). Lands in the connections part file, with the explanation in chat.
13. **The builder model.** The orchestrator prompt must name it. His words: builders always Opus (19 Oct memory) and "I'll hand over the coding to other models" (30 Oct, P-16). Default to Opus `poteto-agent` per `CLAUDE.md` and say plainly in the prompt's notes how to switch.
14. **UI needs written into the UI files** (UI-01) and **every risk and sizing point plus the placeholder list written into the pack** (R-02, U-04).
15. **Grounding on QMA v2's recent PRs and on mini apps** (A-01, MA-01), and **a check that the 20 to 28 Oct designs and explainer sites were carried forward** (P-06).
16. **Two plain explanations owed since 24 Oct**: "tighten, never loosen belongs on the drawdown floor", and "the bot never sizes against the unit sizes itself" (STATE "Owed to the operator"). The second is now answered by U-01; say it to him in one line. The first belongs to the risk session.
17. **A one-line note at the top of `HANDOFF-RISK-SIZING.md`** saying the pack is the hand-off (53 §2 item 12).
18. **The doc pass after the build** (P-28), not yet scheduled.

Not owed, so nobody waits on it: his "Market and gaps" reply, which he said he would write himself (T1:1574); his Claude Code sign-in for the replay study in `research/29-study/` (his small item, not a blocker).

---

## Settled; never raise again

Each was answered by him or by his rulings. Raising any of them again breaks his "don't re-ask" rule.

- Where the real-money key lives, and whether QMX touches money (CC-13).
- His country, and whether Hyperliquid allows him (X-01).
- System 1 and System 2 as words; they were explanation names (U-13).
- The April rules: leverage, swap-free, futures (X-02).
- "Agents never touch money" as a rule (A-05).
- Keep the word "unit".
- Review or rebuild the 239 dictionary entries (D-01).
- One logic on 1m and 5m of one pair (U-09).
- Whether the router switches units on or off (M-05).
- Who promotes to live (CC-11).
- Local first (CC-06), nothing capped and no lookback limit (CC-07, B-05).
- News trading for now (CC-21).
- Historical data and the Dukascopy and Binance Vision terms; the Library holds the data (L-01).
- Build the workflow templates or write them up (W-01).
- WSL against Windows for the node (N-03); machine names, "a server can be a server" (N-06).
- Placeholders for sizing and exits, and a placeholder unit and market for the proof (U-04, U-05).
- Fable agents (P-07); the prototype skill and throwaway prototypes (CC-17).
- The MQL5 DeepSeek run (dropped 24 Oct; W-08).
- "Every part must prove itself" machinery (CC-24).
- Discussing QMB with him; the lead understands it from the code (B-08).
- Whether to land the stacked PRs; he merged 207 to 234 on 31 Oct.
- What R is, what "every try is counted" means, and how more brokers get one record each (answered in chat, T3:940-942).
- The "picking the luckiest market" trap. He knows overfitting ("I get this logic. I know probability of overfit.", T2:219); the lead puts the one-rule fix in the judge without asking (43 §3.1).

---

## How the quotes were checked

A script read every `"..." (Tn:line)` pair in this file and looked for the quoted text, with whitespace normalised, on the cited line of the cited transcript. The command and its result are in the agent's hand-back. Quotes the lead wrote (marked "(lead)") and quotes of agents carry no transcript citation and were not checked.
