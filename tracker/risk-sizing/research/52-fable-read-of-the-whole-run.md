# 52: An outside read of the whole run

Written 2026-10-31 by a Fable 5.1 reader with no stake in what the lead produced. He asked for it word for word at 2026-10-31T04:13: "What are we doing wrong? What should we be doing? [...] Where should we be going? What are we rebuilding that we are not rebuilding? Who's right, who's wrong? Who's phrasing things properly and who's phrasing things wrong? [...] What am I meaning? What am I not getting? [...] we have already almost everything we need. We just need to piece things together."

What I read, in full: the three transcripts (`operator/transcript-2026-10-20-to-28.md`, `operator/transcript-2026-10-29-to-30.md`, `operator/transcript-2026-10-30-to-31.md`), the three dictation files, `STATE.md`, `STANDING-ORDERS.md`, `wayfinder/MAP.md`, research 43 and 44, research 18 and 42 (the two code groundings), the conflicts and drift sections of `RISK-SIZING-PACK.md`. Code was read with `git show` and `git ls-tree` against `origin/engine/base` (d82be318, 26 Oct) and `origin/build/sy5` (074670ac, 29 Oct) from `C:/Users/Mubarak/Desktop/QMX`; nothing was checked out. The Stats dictionary was read on disk. No helper agent was started. One file written, this one. No commits.

Labels: **CHECKED** means I read it at the cited place (transcript timestamp, `file:line`, or a command I ran). **INFERRED** means my judgement. Transcript tags: T1 = 20-28 Oct, T2 = 29-30 Oct, T3 = 30-31 Oct, D27 and D28 = the two dictation files. Line numbers are the lines of those files.

---

## The verdict, on one screen

You are right about what the system is for. The lead is right about what the code can do today. The run went wrong where each of you stopped reading the other's layer.

You have almost everything. About 300,000 lines of Python are merged: the backtester, the strategy library, the trading node, the risk shapes, the data store, the workflow engine, the Library, the broker reads. Thirty more PRs are stacked and waiting. The planning run has produced over 1,500 ideas, 339 questions and 45 research files. That is not a shortage. That is a pile.

Three small things are missing, and they are the centre of everything. First, a unit does not exist as a thing a program can read: the Library has a unit page with no fields, and QML forbids a rule's conditions from being written down. Second, no backtest can place a trade: the only runner for agents is called `silent`. Third, nothing has ever run on your real QMX folder, not one template, not one broker sign-in, not the trading node. Until those three exist, every plan is a plan about a plan.

What the lead did wrong: it built more than you meant, three times, and you pulled it back each time. It asked you things you had settled, and things you find obvious. It fed you nine decisions when you wanted one engineer's call. It wrote one plan file for a man who builds one area per session. It fired agents without intent twice when you were watching. It never showed you the one thing you asked for most, a unit configuring itself, in code.

What you did wrong: you moved the centre of the design four times in ten days and then said "I thought we were done". You said "nothing is set in stone" and were angry when a settled thing was asked again. You asked for breadth and then complained about the pile. You sent the heart of the unit, its sizing and exits, to another session, and then found the unit hollow. You believe connections, data and the trading node are "already set up"; they are coded, stacked, and have never run. You waved away a real statistical trap as "I'm not that desperate".

What should happen now: stop researching. Land the stack on your real folder. Build one unit, as data, from one source you already have in Stats, run it through the backtester with real trades, then on the cTrader demo from your PC, and read its journal. Everything else, the market scanner, breadth, templates, the server, follows that loop once it has run end to end. Six weeks of planning has produced the right six foundations; the plan file is dense, not thin. Split it by area, strip out what you have already decided, and hand each area to a builder.

The few things only you can settle are at the end. There are six. Each has my answer.

---

## 1. What is being done wrong

### 1.1 The lead

**It built more than you meant, and you pulled it back each time.** Three clear rounds.
- The router of rounds 13 and 14: signed placement plans with an expiry, load-balancer algorithms, offers that expire. You: "I think you took it verbatim, and that's causing issues" (T1:1903, 2026-10-28T17:49, CHECKED). The lead agreed it was over-built the same evening (T1:1905).
- "Every guard and part has to prove itself" plus a placebo twin for every study (07a report, T1:1129). You: "What the hell? Okay, don't make this so complex. [...] keep it stupid simple" (T1:1177, 2026-10-24T17:36, CHECKED).
- The ten-stage judge chain in the first convergence (44 A13, CHECKED). You had already said "don't be too strict" (D27, 2026-10-27T03:03, recorded at `STATE.md:123`).
- You named the pattern yourself: "Claude built more machinery than I meant. [...] that's an issue I'm having with every Claude Code session" (T2:135, 2026-10-29T16:41, CHECKED). The lead's own third-party read said the same: "every round, Claude built more machinery than you meant, and you pulled it back to a simpler idea" (T2:77, CHECKED). Knowing it did not stop it: the first convergence still carried the ten stages.

**It asked you what you had settled, and what any trader knows.** Review 44 counts 5 misread rulings, 1 re-asked settled question and 3 misquotes in the convergence (44 count table, CHECKED). You reacted every time: "some of these are too simple [...] I want actual ambiguity, not things you yourself can figure out" (T1:1177, 2026-10-24T17:36); "question number two has been presented in a very sloppy way" (T2:788, 2026-10-30T06:11); "the questions even you are asking, so most of them, even me as a newbie trader, I already know what they mean" (T2:845, 2026-10-30T06:14); "I thought we were done with System 1 and System 2" (T3:1080, 2026-10-31T04:05). All CHECKED.

**It handed you decisions instead of making calls.** On 31 Oct the walkthrough led with nine decisions: where the live key lives, your country, two data sites' terms, a Claude sign-in (T3:990-1031, 2026-10-31T03:13, CHECKED). Four of those are either technical facts for the node pass or one-line answers. You had said, twice, "you drive" and "call BS or make a better call because you are more knowledgeable" (T2:135; T2:1219, CHECKED). Returning nine decisions read to you as abdication. It read to the lead as respect for "only he promotes". Both readings are honest; the result was a wasted morning.

**It wrote for itself, not for you.** One convergence file of 820 lines covering seven areas (43, CHECKED). You build one area per session, with one builder prompt per packet (CLAUDE.md "one pstack builder agent per numbered packet", CHECKED). You said so: "one file specifically compiling everything we have on QML, then one file [...] for agents addition, then another file perhaps compiling the MIS" (T3:1080, CHECKED). Standing order 17, "one area per file", was added only after that complaint (`STANDING-ORDERS.md:21`, CHECKED). The content of 43 is dense and mostly right (section 10 below); its shape is wrong for you.

**It fired agents without intent while you were watching.** Two agents for one visualiser: "Dude, you're wasting my tokens. All this can be done by one agent" (T1:1443, 2026-10-25T03:45, CHECKED). Three grounding agents launched in the same minute you asked for a Fable advisor: "stop the other agents. What the hell are you doing?" (T3:1134, 2026-10-31T04:14, CHECKED). And a general warning in between: "I hope you are launching these agents with intent, because I'm seeing you're just now randomly launching agents" (T2:858, 2026-10-30T06:19, CHECKED). On 30 Oct afternoon alone the task notices in the transcript show 13 agents at 283,000 to 528,000 tokens each (T3:63, 108, 167, 219, 268, 344, 412, 468, 805, 832, 863, 893, 1066, CHECKED), roughly five million tokens for one afternoon.

**It never showed you the one thing you asked for most.** "'Self-configuring' has never been shown concretely (how a unit actually configures itself). This is what he needs most" is in the lead's own state file (`STATE.md:114`, CHECKED). On 29 Oct the lead's third-party read listed it as "Your most important item was never designed" (T2:102-104, CHECKED). On 31 Oct the self-configuration demo sits in the Should column, handed to the risk session (43 Appendix B, CHECKED). Three weeks, still not shown.

**It let the words run.** The lead and its agents coined "unit" (8 Oct, `17-grounding-history` via STATE:232), "specialist", "terrain", "telescope", "finder", "envelope", "two-speed router", "brain and arm", "market settings", "market version", "claim card", "death certificate", "conveyor", "loss points", "tighten, never loosen". Several had to be retired after you asked what they meant (T2:788: "Specialist, what do you mean by a specialist?"; "Terrain was not mine"; CHECKED). Section 6 lists them.

**It read your words verbatim and still missed the meaning.** Every quote in the convergence exists word for word (44 "What held up", CHECKED), and still: "It's numbers" was you reading the lead's option back, not your answer (44 A01); "funding" meant the money part of a unit, not perps funding (44 A04); System 2 was halved (44 A02); "quantity doesn't matter, quality might matter" was written down backwards (T3:133, CHECKED). Verbatim transcripts fixed the words, not the reading.

### 1.2 The agents

- The convergence agent read its sources only in part and said so (43 "Read in part", CHECKED). The reviewer then found 49 problems (44). A convergence that has not read the transcripts cannot converge his intent.
- Agents answered in research-speak and invented nouns. The fields hold "taints and tolerations", "admission envelope", "telescope", "dark-MIS run", "hindsight-premium run". Good ideas, wrong register for a man who said "I don't like reading text" (T1:1454, CHECKED).
- Agents treated the planning method as the product. Seven expansion rounds produced about 800 ideas and 339 questions (STATE funnel3-7 rows, CHECKED). The convergence used perhaps twenty of them. The ratio is the problem, not any one round.
- Small factual slips travelled: research 10 called `Desktop\strats` empty; the lead found a 97 KB session in it (T2:915, CHECKED). Research 05 said 1,400 trades to see decay; research 08 said 240 (different tests, both presented as "the number").
- The speed numbers in research 22 come from simulated bars, labelled honestly, and were then quoted in the convergence as findings (43 §3.3, CHECKED). Honest labelling does not make a simulation a measurement.

### 1.3 You

Plainly, as you asked.

**You moved the centre four times and then said "I thought we were done".**
- The unit: strategy plus sizer plus record (13 Oct baseline, Claude's); "one complete trading algorithm with no separations" (24 Oct, `STATE.md:21`); "a unit literally is now just a trading bot" (T1:1211, 24 Oct 17:43); "It's just a self-configuring trading bot. Simple as that" (T2:788, 30 Oct). All CHECKED.
- The MIS: inside the unit as blocks (20 Oct lean); a router like a load balancer (T1:376, 20 Oct 12:20); "the router only routes [...] neither does it switch on, nor does it switch off" (D27, 27 Oct); "the MIS just reads and outputs. Then the units [...] pick the output" (T1:1951, 28 Oct 18:23); then System 1 and System 2. All CHECKED.
- One logic on 1m and 5m: "two different bots with the same bloody logic" was "the shocker of them all" (T1:484, 20 Oct 12:49); "that's just correlation. I don't think it's different" (T2:1000, 30 Oct). CHECKED.
- A new instrument makes a sibling unit: yes (D27, 27 Oct, `STATE.md:73`); joins the unit's universe (28 Oct, agreed in chat, T1:1948-1951). CHECKED.
Each move was a real improvement. But a lead cannot both carry your latest position and never re-ask it when the position changed four days ago. "Nothing is set in stone" (T1:1574; T2:788; T3:1080) and "I thought we were done" (T3:1080) cannot both bind. You have to say which words are stone.

**You asked for breadth and then complained about the pile.** "expand this as far as possible" (T1:651, 24 Oct 16:18); "the sky is the limit" (T1:828); "trust me, I think we are like taking 5% of what we are actually meant to be solving" (T2:325, 29 Oct 17:53); "No answers, broaden first" (T2:325). Then: "this is a lot of text. I'll go through it slowly by slowly" (T2:602, 30 Oct 05:30); "I'm not trusting this work" about one file (T3:1080). Both are fair feelings. Together they are a brief no lead can satisfy.

**You split the unit's heart off and then found the unit hollow.** You ruled the unit is "one complete trading algorithm" including "its own self-calibrating risk and sizing" (`STATE.md:21`, CHECKED). You then sent sizing, exits, stops, targets, the correlation control, the pod and the account guard to a separate risk session that has not run (D27 27 Oct 03:03; T2:1000 30 Oct 06:42; T2:1148 30 Oct 07:31; CHECKED). The unit planning was left with the entry rules, the journal and a "socket". That is why 43 reads as if the unit were a shell: by your scoping, it is. Research 35 found that every platform agrees on the parts of a strategy and differs only on who owns exits and size (STATE:240, CHECKED). You have put the only contested parts out of scope.

**You believe things are built that have only been coded.** "external connections actually was, I already told you yesterday, it was handled a lot"; "when you mention such a thing like Hyperliquid or crypto, there are already connections set up for these things"; "Seems like a trading node was finished in the latest PRs" (T3:1080; T2:439; CHECKED). The code: Hyperliquid has zero lines on the trunk and on the stack tip (`git grep -i -l hyperliquid` over qmb, qml, qmn, packages, qmx-agents/packages at both refs = 0, CHECKED); MT5 is a declaration only (`qmx_broker/adapters.py:59-76`, CHECKED); CCXT is a read-only spot adapter (`adapters.py:1`, `:247`, CHECKED); the cTrader demo sign-in "has not run against cTrader" (`scripts/probes/data/FINDINGS-ctrader.md:5`, CHECKED); the wrap-up PRs shipped a workflow server, not the trading node (42 §2.2 last row, CHECKED); the trading node QMN, 98,000 lines, "has never been deployed anywhere" (43 Subtract first item 8, citing r31, CHECKED). "Nothing in the stack has run on his real QMX folder" (42 "The big caveat", CHECKED). Coded and stacked is not set up.

**You waved away a real trap.** "I don't think I'll wake up when I've designed this system this carefully and just use a bot that is trading based off pure luck. I'm not that desperate" (T2:219, 29 Oct 17:25, CHECKED). Luck is not about desperation. If twenty markets each have one hundred trades and you pick the best-looking one, the best one looks like +0.23R while its true edge is +0.06R, in research 24's simulation (43 §3.1, CHECKED). Your Path A (a market's version is earned from the unit's own record there) removes "from thin air". It does not remove "I picked the best of twenty". The fix is one line and you should take it.

**Your timelines whip.** "I want the entire night to be spent coding and we finish this by the end of tomorrow" (T2:135, 29 Oct); "there is no rush [...] can take up to 3 to 4 days" (T2:845, 30 Oct); "the end goal is to start coding perhaps by today morning" (T3:932, 31 Oct). CHECKED. A lead that is told both will optimise for neither.

**Your dictation is the single biggest source of "wrong wording".** You know this ("you know how wrong wording has messed us up so far", T2:1208). Verbatim saving helped. It did not fix "funding", "It's numbers", "System 2", or "quantity doesn't matter, quality might matter". Only a short glossary that you read and sign will.

---

## 2. What should be done instead

Not the next step. The way of working.

1. **Stop expanding. The field is wide enough.** 1,500 ideas and 339 questions would feed ten systems. No more party mode, brainstorming or CIS rounds until a unit has traded on demo. Research runs only when a build packet needs a fact it does not have.

2. **Land the stack first.** Thirty open PRs, nothing run on the real folder. Every proof below waits on this. It is also the one step that needs nothing designed.

3. **Prove the unit in code before architecture.** You said it: "we need to be able to make sure that in theory, what we know can actually come out in practice" (T3:1080, CHECKED). Two prototypes, each a few hundred lines: a unit written as a document that QML compiles into the factory it already runs (`qml/src/qml/protocol/factory.py:1-6` describes that seam, CHECKED); and a QMB runner that takes that unit and produces trades with R. If those two work, the architecture is a description of what works. If they do not, the architecture would have been wrong.

4. **One area, one file, one builder.** Split 43 into the areas you named (T3:1080): QML, the unit template, the MIS, journals, external connections, the trading node and DevOps, contracts between parts, workflow templates. Each file is a builder packet: what exists (paths), what is added, what it must not break, how it is checked. Standing order 17 already says this; make it the output shape, not a rule.

5. **A signed glossary of fifteen words.** Section 6 has the list. You read it once, change what you like, and after that any agent that uses a word another way is wrong by definition. This is the only fix for dictation drift.

6. **The lead carries defaults and keeps a veto ledger.** Every technical call the lead makes is one line in a file you can scan, with "veto" as the only action. Nothing technical is asked. Only money, values and the words on your screen come to you. You asked for this on 24 Oct ("bring him only real ambiguity", `STATE.md:30`) and on 30 Oct; it was never fully honoured.

7. **The risk session runs before paper, not after.** A unit cannot trade on demo with an empty sizing socket. Either fold the first sizer and exit set into the unit build as its first packet, using `RISK-SIZING-PACK.md`, or run that session now in parallel. Do not let the reference unit wait on it a third time.

8. **Grounding is shown, not filed.** Research 18 and 42 are good; you never saw them in a form you could read. One page per part: built, stacked, missing, with file paths. Then "you didn't ground on what exists" stops being said, because it will be visible.

9. **You write ten rulings once, by typing, not dictating.** The ones you care about: what a unit is, what the MIS is for, who promotes, local first, nothing capped, agents never touch money, design for complexity not a complex system, keep "unit", exits inside the unit, the April rules. Ten sentences. After that, no re-asking and no re-opening unless you bring new information.

10. **One agent per job, launched with its brief read back to you in one line.** You ruled this on 25 Oct (`one-agent-per-job`). The 31 Oct launch of three agents while you asked for one advisor broke it. A one-line "starting X to do Y" before each launch costs nothing.

---

## 3. Where you should be going

**The destination, in plain words.** A unit is a strategy you can read, built by an agent from a source, that trades where its market conditions hold, sizes itself from its own record within limits you set, keeps a journal you can read, and goes live only when you click. QMX is the shop that finds, tests, places and watches such units, and tells luck from edge before your money goes in. You said the positioning yourself and it is the right one: "when generating strategies is nearly free, judging them is the product" (`STATE.md:29`, CHECKED).

**The first milestone.** One unit, end to end, on your PC: a source from Stats, a unit document, a backtest with real trades and R, a judge verdict, a draft card, your click, paper trades on the cTrader demo, a journal you open and understand. No MIS, no breadth, no server, no templates beyond the one chain that moves the card. When that loop has run once, every other part has something real to attach to.

**The shortest honest route from what exists** (each step names the code it starts from; order matters):

| Step | Starts from | Adds | Why first |
| --- | --- | --- | --- |
| 1. Land the stack on the real folder | 30 open PRs, `origin/build/sy5` (CHECKED) | nothing new | nothing has run on his folder; every proof waits on it |
| 2. The unit as data | `unit.schema.json` with empty `fields` (`LIB/kinds/unit.schema.json:7-10`, CHECKED); QML's factory seam and declaration; the gold mine's logic graph (`Stats/schema/strategy-dna.md` E layer, `logic/graph.yaml`, CHECKED) | fields on the unit kind; a compiler from named slots to the existing factory; lift "the bot may not size" for units (`qml/src/qml/protocol/intents.py:4-5`, CHECKED) | the first blocker on both the backtest and the live side (r31 via 43 F3) |
| 3. A backtest that trades | PR 204's door shape, `RUNNERS = {"silent"}` (`origin/build/wu4:qmb/src/qmb/host/backtest_door.py:60`, CHECKED); the typed partitions; the replay reader | a runner that trades a unit; the windowed reader (the only lookback limit); results in R with excursions | without it no judge, no tries, no proof |
| 4. The first sizer and exit set | `qmf-risk/sizing.py` (defined-unwired, DEC-0158, `:34`, CHECKED); the risk pack | the smallest honest sizer and one exit family, from the risk session | a unit with an empty socket cannot reach demo |
| 5. Paper on the PC | cTrader demo sign-in (WU8, never run); the broker read adapter; QMN's venue client and protection set (never deployed) | a feed keeper; order placement on demo; a unit journal kind and a door agents read through | the first real trades and the first real journal |
| 6. The judge and the card | `TPL/_shared/overfit-gates`, the `b` template's gates, governed drafts (`LIB/landing.py:8-11`, CHECKED) | one shared judge block; tries counted at QMB's door; the proposal card | "judging is the product" |
| 7. MIS v1 as library readings | QMN's six labelers and SQS (`qmn/src/qmn/mis/labelers.py:1-6`, CHECKED) | the labelers as a package both QMB and the runtime import; stamped history; a per-session match list | only now does placement have units to place |
| 8. Templates' doors | 45 templates, 23 drafts waiting on `qmb-door` and `trading-node` (42 §1.8, CHECKED) | the doors the drafts name | the funnel already exists as drafts |
| 9. The trading server | the connect-dialog step runner (42 §2.2); QMN or the host's trading role | a trading-server kind | only after the PC loop has run |

Steps 2 to 5 are the whole of what is truly missing. They are small in lines and central in effect. INFERRED, but every row's starting point is CHECKED.

---

## 4. What is being rebuilt that should not be, and what should be rebuilt that is not

Each piece against the code on `origin/engine/base` unless marked.

| Piece | What exists (CHECKED) | Verdict |
| --- | --- | --- |
| **QML** | 48 files, about 16,500 lines (line count command, CHECKED). Protocol, factory, declaration, parameters, versioning, ATC/PolicyPair, conformance gates layer 1 and 2 with a prediction linter (`qml/src/qml/conformance/`, CHECKED). Research 04 found its contract shape matches every platform studied (STATE:219). Last changed 7 Oct (r18 §3). | **Do not rebuild.** The 13 Oct "rebuild QML from scratch" was wrong and the lead was right to challenge it. Upgrade: a block catalogue, a unit document that compiles into the existing factory, and the Book premise lifted for units. **The deterministic check you asked for on 31 Oct already exists in shape**: the conformance gate "spawns no process, performs no I/O" and gates registration (`conformance/__init__.py:1-6`, CHECKED). Extend it; do not invent a new linter. |
| **The dictionary** (Stats) | 4 family files with `##` entries, 12 fields each, no code (`Stats/dictionary/README.md`, CHECKED). The context file has 68 entries (69 `##` headings less the coverage table, CHECKED). 239 entries in total (r34, r36). Six family folders empty. | **Rebuild the form, keep the content as seeds.** Settled by your own words (T2:219, T2:788). Not a decision. The content is not a rebuild; the form (prose to spec plus code) is new work. Build only the entries the reference unit needs first (about ten), not all 239. |
| **QMB** | 137 files, about 91,000 lines (CHECKED). Run loop, cost ports (refuse without calibration, GAP-0048), Optuna optimiser, robustness batteries, sweeps, What-If projections, exact-integer money, one landing shape, trial ledger (r18 §2, CHECKED). MCP door "scaffolded, not shipped" (`qmb/src/qmb/doors/mcp/__init__.py:1-6`, CHECKED). Only runner `silent` (PR 204). Replay reader copies all history per step. | **Do not toss.** "we either toss or we rebuild QMB" (T2:135) is wrong on the toss half. Rebuild four things: the replay reader, a runner that trades a unit, the agent door, results in R. Keep the rest. 43's second version says exactly this and is right. |
| **The MIS** | Six rule labelers plus SQS, one fitted liquidity model, a regime pipeline whose labels are volatility only, "never a direction claim" (`qmn/src/qmn/mis/regime_design.py:72-78`, CHECKED). HMM, BOCPD and MS-GARCH are listed as candidates, none trained or ratified (r18 §4). Runs only inside QMN, which never ran. | **Do not rebuild the labelers; move them.** Your "the one we are using is mostly using HMM, BOCPD, MS-GARC" (T1:1951) is wrong: nothing fitted is live. The labelers become a package both QMB and the runtime import, with stamped history. New readings (Hurst, efficiency ratio, range volatility) are additions, not a rebuild. The "regime" word clash (volatility in code, direction in your mouth) must be settled once. |
| **Journals** | A `trade` kind with `world` and `initial_risk` (`trade.schema.json`, r42 §6.1). No journal kind, no unit journal, no door for agents (r42 §1.7, CHECKED). Imported fills carry no R. | **New, and you are right that it needs depth** (T3:1080). The 27 Oct "the journal [...] it's anything that can record data" and the 30 Oct "most simple data schemas" (T2:1148) are what the agents followed; your 31 Oct correction supersedes them. Keys: unit, world (backtest, paper, demo, live), machine, account, broker. One writer per stream. |
| **The trading node (QMN)** | 203 files, about 98,000 lines (CHECKED). cTrader live client, recording loop, virtual ledger, reconcile, kill line, ratchet, KSA, news windows, SQS, seats, promotion, Book-level paper. Linux and systemd only (`qmn/deploy/systemd/templates/qmn.service.in`, r42 §3). "bot never sizes" at the seat door (`qmn/src/qmn/seats/dispatch.py:1-8`, CHECKED). Never deployed. Its own Grafana/Loki stack beside the host's OpenObserve. | **The biggest unproven piece, and the one most likely to be partly rebuilt.** Keep its protection set and venue client; they are exactly the independent guards you want. Its admission, seats, promotion and Book door clash with "the unit sizes itself" and must be rebuilt around the unit; 43 lists them as "conflicts for the fold", which hedges. Whether the node stays a separate Linux program or becomes a trading role of the Windows host is the one real architecture choice left (section 11, question 3). |
| **Broker connections** | cTrader read adapter and demo sign-in, never run (`FINDINGS-ctrader.md:5`, CHECKED). CCXT read-only spot (`adapters.py:1`). MT5 declaration only (`adapters.py:59-76`). Hyperliquid 0 lines at both refs (CHECKED). Providers: Dukascopy, Binance Vision, CCXT public, Databento key proof, Firecrawl (`qmx_broker/providers/`, CHECKED). | **Nothing to rebuild; much to finish and run.** You are wrong that these are "set up". cTrader is close. CCXT is reads, not execution. Hyperliquid does not exist. Real futures cannot be traded on cTrader at all (r38). |
| **Workflow templates** | 45 at the stack tip; 22 run, 23 are drafts waiting on `qmb-door`, `trading-node`, `sandbox` (42 §1.8, CHECKED). `b`, `l1`, `d3`, `d4`, `l4`, `rs6` are the old WF1 and WF2 shapes. No template uses an event trigger or names a skill. | **Do not rebuild; build the doors.** Your funnel already exists as drafts. "The agentic side is already done" (T2:1148) is right about the engine and wrong about the doors: no template can read a unit, a journal or the MIS today. |
| **The Library** | 39 kinds, 39 link types, governed drafts wait for your yes (`LIB/landing.py:8-11`). `unit` kind: page tabs Logic, Results, Family tree, Markets, Versions; `fields.properties` empty (`unit.schema.json:7-10`, CHECKED). | **Keep; fill the unit's fields; add a journal kind.** Your "the library exists, we should use it" (T3:1080) is right. |
| **Risk shapes** | `qmf-risk`: 24 modules, about 17,700 lines; Book, BMS, admission, exit policy, a sizing ladder "defined-unwired, no wiring is authorized" (`sizing.py:34`, CHECKED). QMN capital: kill line, ratchet, bench fold. No account guard, no daily loss limit, no house money in code (r18 §5). | **Not this run's to rebuild, but it cannot stay unwired.** The shapes exist and have never sized a trade. Your "combine the old relentless system with the Book/BMS" is the risk session's job and it must happen before paper. |
| **Engine, harness, host** | about 39,000 lines in the engine alone; 13 runnable node kinds; triggers including Library events; remote workers; the guard hook (r18 §1, r42 §1, CHECKED). | **Do not touch.** Built in the last month and the one part that is close to complete. |
| **Docs** | `docs/` last changed 27 Sep (`git log -1 main -- docs` = 03ad2f00 2026-09-27, CHECKED). Fourteen rows contradict the new intent (r18 §9). | **Should be rebuilt and is only planned as "a doc pass".** Every agent that reads `docs/` is misled. This is the rebuild nobody has scheduled. |
| **The router machinery** (rounds 13, 14) | Never built. | Correctly dropped (43 Subtract first item 4). |
| **The UI** | SvelteKit demo data, not wired, built before the engine (r42 §6.2). | Out of this run; you know. |

Summary of the two lists you asked for. **Rebuilding that should not happen:** QML from scratch (your 13 Oct call), QMB as a whole (your "toss"), the MIS models (you want to pick HMMs; the labelers exist), the agent side. **Rebuilds that are needed and not scheduled:** the docs; QMN's admission layer around the unit (hedged as "conflicts"); the dictionary's form (scheduled, fine, but only ten entries are needed first).

---

## 5. Who is right and who is wrong, point by point

| Disagreement | Verdict |
| --- | --- |
| MIS inside the unit (20 Oct lean) or outside as a router | **You were right** (T1:376). The lead agreed within the hour and the research backs it: a reading inside the unit is another setting to overfit. |
| The router "switches units on and off" (07 funnel, 09) | **You were right** (D27). The lead was wrong and fixed it on 27 Oct. |
| The load balancer taken literally (13, 14) | **You were right that it was over-built** (T1:1903). But you handed over the analogy with its algorithms ("round robin and so on [...] they're around 7", D27) and then said "you took it verbatim". Half yours. |
| System 1 grows into System 2 | **Both right**, and research 16 said it cleanest: "pooled vs per-cell, with shrinkage as the bridge" (STATE:231). A new market leans on the unit's whole record; a market with its own record leans on itself. One rule, not two systems. |
| Same logic on 1m and 5m | Your 20 Oct "two different bots" was **wrong**; your 30 Oct "that's just correlation" is **right** (T2:1000). Research 35 agrees. |
| A new instrument makes a sibling unit (Q1) | Your 27 Oct yes was **superseded by your own 28 Oct view** (a market joins the universe; only a logic change makes a new unit). The lead was right to raise the change and wrong to put "keep your 27 Oct answer" back as an option (44 A12). |
| "Wins on some instruments is luck" | **The lead and research 16 and 24 are right** about selection bias. **You are right** that Path A removes "from thin air". You are wrong to dismiss the remaining picking trap as desperation (T2:219). Take the one-rule fix. |
| "We have a correlation ledger, it's already there" (T1:444) | **You were wrong about today's code**: the name labels a lineage projection (`DOCS/lenses/observability/logging-spec.md:138` via r18 §5). **You were right about the old design**: the Intent Aggregator existed (r19). You remembered a real thing from the wrong era. The market-correlation maths exists only as a draft template. |
| "QMX never touches money, the key question is a waste of time" (T3:1080) | **Half right.** It is not a money decision for you, and "real-money key" was the wrong name. **Half wrong:** ruling 135 is in code (`BRK/adapters.py:107-172` via r42, refuses a live-capable grant on the PC) and a trading token can lose money by trading even though it cannot withdraw (r38). The process that places live orders has to run somewhere with a trading grant. That is technical, it is real, and the node pass must settle it. The lead was wrong to bring it to you as decision 1; right that it exists. |
| Windows first, not WSL (T3:1080) | **You are right about the cost** (two file systems, idle shutdown, clock, disk on C:, all found by r31). **The research is right about the fact**: QMN as written needs Linux and systemd (`qmn/deploy/systemd/`, r42 §3). This is a real architecture choice, not sloppiness: run QMN under WSL for the rehearsal only, or give the Windows host a trading role and port QMN's protection set in. Question 3 below. |
| "The dictionary already has context" (T1:2051) | **You were right**: 68 context entries (CHECKED). **The agents were right too**: the entries are prose with no way to measure them (r15, r34). Both true. |
| "Agents can code, by the end of tomorrow" (T2:135) | **You were wrong, the lead right** (T2:209). Nothing can be coded until the unit exists as data and the stack lands. |
| "Exits, stops, targets go to the risk session" (T2:1000) | **You are wrong, and the lead was wrong to accept without pushing back.** Exits are the half of a scalper's logic that decides whether it is a scalper. You said it yourself: "the logic is the entire bloody thing" (T1:2051). Sending exits out of the unit run contradicts your own ruling that the unit is one complete algorithm. |
| "The journal is simple, anything that records data" (D27) against "the shape is not thought through, design it in depth" (T3:1080) | **You contradicted yourself**; the agents followed your first instruction and your 30 Oct "most simple data schemas" (T2:1148). Your 31 Oct view is the right one. |
| "The agentic side is already done, look at QMA v2" (T2:1148) | **Right about the engine, wrong about the doors.** No template reads units, journals or the MIS; the backtest door is a silent runner (r42 §1.7). |
| "Connections are already set up for Hyperliquid and crypto" (T3:1080) | **Wrong** (zero Hyperliquid lines; CCXT reads only; MT5 declaration only). |
| "Most of QMB was handled in the earlier session" (T2:1148) | **Half right.** The comparison and the lookback bug were found (08, 12, 14). The runner that trades, results in R, and the agent door were not designed anywhere until 43. |
| The dictionary: review or rebuild (43 decision 2, first draft) | **You had settled it four times; the agent was wrong to ask** (44 A03). |
| One plan file is "not detailed" (T3:1080) | **Wrong on depth, right on shape.** 43 is 820 lines of dense, mostly correct material (section 10). It is one file for a man who builds one area per session. Split it; do not redo it. |
| "Nothing is set in stone" against "I thought we were done" | **You cannot have both.** Pick the ten rulings that are stone (section 2, item 9). |

---

## 6. Who phrases things properly, and who does not

**You phrase intent well and terms badly.** Your analogies land every time: the load balancer, the fish in a freshwater lake instead of a swamp (T2:135), the male and female connector for the risk socket (T2:135), the journal as the DevOps layer (D27), a bot as if-else statements (T2:788), QMB as a test suite that "runs and waits" (T2:135). Those are the clearest statements of intent in the whole run, and the lead built on all of them. Your coined terms do not land: "System 1" and "System 2" (you later called them explanation names, T2:788), "funding" for the money part of a unit, "tightening, never lose" for a rule Claude proposed, "MRS" for MIS.

**The lead phrases crisply and invents nouns that become false terms.** Every invented noun below had to be explained or retired.

**The agents phrase in research register with verbatim quotes and lose the context.** All 49 review findings are about context, not invented words (44 "What held up", CHECKED).

### Words that drifted (two meanings in play)

| Word | Meaning one | Meaning two | Settle as |
| --- | --- | --- | --- |
| unit | Claude's word, 8 Oct; ten definitions found (funnel3 CIS) | your "a self-configuring trading bot. Simple as that" (T2:788) | your definition, with its parts listed once |
| context | the trader's sense: price action, technical analysis, fundamentals when used (T2:788) | what the MIS measures; five meanings found (funnel3 CIS) | "market state" is what is measured; "market need" is what a unit asks for; "context" stays the trader's word |
| regime | in code: volatility buckets, "never a direction claim" (`regime_design.py:72-78`, CHECKED) | in your mouth: trending against ranging | your meaning; rename the code's buckets "volatility state" |
| node | the workflow server (`qmx node setup`, WU9) | the trading node QMN | "workflow server" and "trading server" |
| router | `qmx-router`, the LLM provider router | the trading router / MIS | keep "MIS"; never "router" for placement |
| correlation ledger | docs: a lineage projection over `enacts` edges | you: a market-correlation control | "correlation control"; the ledger name stays with lineage |
| journal | the `trade` kind per account | the unit's DevOps layer, with agents writing notes | "unit journal", "market journal", "node journal", "notes" |
| book / BMS | the Book (overkill, D27) | the BMS, and "a BMS but not the one we have now" (T2:219) | the risk session must define both once |
| paper | QMN's Book-level paper lane (DEC-0261, no per-bot paper) | per-unit paper on demo (your ruling) | "paper" = per-unit demo trading; the old lane is retired |
| funding | perps funding payments | the money part of a unit (T2:135) | "funding" = perps only; "the money part" for yours |
| workflow | a QMX workflow inside the product | the planning run | say which in full |
| self-configuring | recalculating size from a fixed rule; updating the rule's inputs from trades; changing the rules (r20) | | name all three; the first two are what ships elsewhere |
| tries | a try at QMB's door | a try counted by an agent | "counted at the door" only |
| MIS | a router that places | a scanner that reads and outputs | your 28 Oct "reads and outputs; units pick" |

### Words the lead or its agents invented

specialist, terrain, envelope, telescope, finder, two-speed router, taints and tolerations, brain and arm, market settings, market version, claim card, death certificate, conveyor, loss points (which you adopted), tighten never loosen, exam (which you called cringe), "capable at the edges, simple at the core". Four were retired after you objected (specialist, terrain, System 1/2 as terms, "lean"). The rest are still in 43.

### Your words the lead or agents misread

"It's numbers" (your reading back, taken as your answer, 44 A01); "funding" (44 A04); "System 2" (halved, 44 A02); "quantity doesn't matter, quality might matter" (reversed, T3:133); "a model may remember past markets" (your point was about live analysis, T2:385); "multiple experiences" (not found until you explained it, T2:858); "lean" (your KISS, T2:1208); "design for complexity, not a complex system" (read as a wording problem, not as "few independent parts").

### Dictation slips the agents must keep translating

caramel, KML = QML; Febble, verbal model, Fibble = Fable; KMX = QMX; MTFA = MT5 articles; CCTX = CCXT; Dukas Copy = Dukascopy; MRS = MIS; new skill switch = news kill switch; potato mode = poteto-mode; consum on R = CUSUM on R; first invalidation = fast invalidation; pressure size, operation sizing = position sizing; JSE framework = Jesse; Quant Connect Lint = LEAN. (Collected from the transcripts and `RISK-SIZING-PACK.md` §2.11, CHECKED.)

---

## 7. What you mean that the lead keeps missing

Read from your words, not the lead's summaries.

1. **"Design for complexity, not a complex system" means few independent parts.** You explain it as "a system that can handle very hard edge cases [...] the 95th percentile or so. Don't design a complex system" (T1:1177), and later "maintenance of the system [...] it can become difficult to maintain and decode" (T2:1208). You mean: each part stands alone, each is explainable, and hard cases are met by the robustness of simple parts, not by adding machinery. The lead heard a wording problem and rewrote the slogan. The test you want is: can this part be explained in three sentences, and does it still work when its neighbour is down.

2. **"Nothing is set in stone" means do not close design before research, not re-ask me.** You want the lead to carry your latest position confidently and stop you only on real ambiguity ("I want actual ambiguity, not things you yourself can figure out", T1:1177). The lead read it as permission to put choices back to you.

3. **"You drive, call BS" means own the technical calls.** "I'm not technical [...] you can either call BS or make a better call because you are more knowledgeable" (T2:135). When the lead returned nine decisions, four of them technical, you heard a secretary, not an engineer.

4. **"Ground on what is built" means show me, and build on it.** You keep saying it (T2:325, T2:385, T3:1080). Research 18 and 42 did it well. You never saw them in a form you could read, so every "we need X" sounded like the lead had not looked, even when X truly does not exist (Hyperliquid, a unit journal, a runner that trades). The miss is framing: "X is not built; the smallest step from what exists is Y", never "decision for you".

5. **QMX has two faces, and the unit is on the algo face.** "we have human usable and algorithmic usable or agentic usable. So the agents are the intermediators" (T1:444, 20 Oct 12:39). Human face: copilot, workflows, Lab, UI, mini apps. Algo face: QML, QMB, QMF, QMN, the MIS. You want the unit work firmly on the algo face, with agents as its users. The templates and analyst-agent rounds drifted to the human face.

6. **"The unit is the end" means the unit is the product.** Everything else serves it: the MIS places it, QMB proves it, the journal watches it, the node runs it, agents build it. When the lead listed the unit as one area among seven, the hierarchy was lost.

7. **"Journals are the DevOps layer" means observability, not a trade record.** Logs, metrics and traces of a unit the way a service is watched; agents read them; the UI renders them; you ask "why didn't it trade?" and get the gate that said no (D27; T2:325). The 07 funnel's "one trade record" was the wrong frame and you said so (T1:1177).

8. **System 1 to System 2 is a description of the search as the product.** A strategy is defined by the market behaviour it needs, not by an instrument; the instrument specialisation is earned from the record; "system two is the end goal of QMX" (T2:135). You are describing placement-by-proof, which is also your "judging is the product" line from another side.

9. **"Prove it in practice" means a prototype, not a plan.** "we need to first make sure that what we think can work in theory can actually be pulled off in practice" (T3:1080). You want running code before the architecture is finished. The lead planned prototypes as "Level 2, proof in code" after the architecture (`STATE.md:62`).

10. **"One file is not enough" means give me packets.** You build one area per session with one builder each. A single convergence is shaped for the lead's convenience, not for how you ship.

---

## 8. What you are not getting

Said kindly, and plainly.

1. **Selection bias is arithmetic, not desperation.** Test one logic on twenty markets, pick the best, and the best is lucky by construction. Nothing about your care or your paper trail removes it. Only a rule fixed before you look does: judge every market by the same test, count each as a try, pull thin records toward the whole. It is one line and it is not machinery.

2. **A unit cannot be complete with its sizing and exits in another session.** You defined the unit as one complete algorithm including its own risk and sizing. You then sent sizing, exits, stops, targets, the pod, the guard and correlation to a session that has not run. The unit run was left with a shell. That is why 43 felt thin at the centre. Either the risk session runs now, or its first packet is folded into the unit build.

3. **"QMX never touches money" is true of withdrawals and false of losses.** A cTrader trading token cannot move money out (r38) and can lose all of it by trading. The code that refuses a live-capable grant on your PC (`BRK/adapters.py:107-172`) is the only thing between an agent shell and your account. Keep it. The open question is only where the order-placing process runs and under which grant. That is a node-pass call, and it exists.

4. **Coded is not set up.** Nothing in the stack has run on your real folder. The cTrader sign-in has never run. The trading node has never been deployed. Hyperliquid does not exist in the code. MT5 is a name. The templates were test-run on throwaway folders. When you say "it's already set up", the agents check and find it is not, and then you say they did not ground. Both are true: the design exists, the running thing does not.

5. **The two "nodes" are different machines.** The wrap-up PRs shipped a workflow server (jobs, Library, Hub). The trading node QMN is a separate 98,000-line Linux program that places orders and has never run. "Seems like a trading node was finished in the latest PRs" (T2:439) conflates them.

6. **Breadth is not independence.** Twenty mean-reverting markets on one quiet dollar are one bet (r16). You accept this when it is said and default back to "100 instruments" when you dictate. At $300, minimum lot sizes pick your universe before any scanner does (r16): one or two units, a handful of markets. The 200-unit, 60-instrument architecture is for later.

7. **Python is not your speed problem.** The network is: about 160 ms to cTrader from your PC, under 1% of a 1-minute bar; the fan-out is 0.5 ms (r31, measured). The stack question is answered for 1-minute units. Order-flow tick scalping is impossible on cTrader in any language, because there is no trade tape (r21, r38).

8. **The lookback limit was a bug, not a rule, and it is bigger than one line.** Prices are copied at four places per step (r14). Fixing it is a real piece of work inside QMB, not a setting.

9. **Data terms matter only for live use and databases.** Dukascopy forbids databases and bots and now blocks downloads; Binance Vision forbids live execution use. For your own backtests both are fine. One line from you settles it: "my own backtests only, recordings are the main history".

10. **Agent coding speed does not apply to an unlanded stack.** Thirty PRs must land first, the unit must exist as data, and QMB must trade. Realistically that is one to two weeks of stacked PRs before the first reference unit runs on demo, after the stack lands. "By tomorrow morning" was never possible.

11. **Your dictation is the main source of the wording problem.** You know it. The only cure is a short glossary you read and sign, and ten typed rulings.

---

## 9. Piece it together

You said "we have already almost everything we need." On lines of code and on ideas, you are right. Here is the system as it exists, part by part, kept separate as you asked. **Exists** = merged on `origin/engine/base`. **Stacked** = in an open PR. **Missing** = in neither. Line counts are from `git ls-tree` plus `git show | wc -l` at `origin/engine/base` (CHECKED, rough, includes blanks and comments).

### 9.1 The parts and what each owns

| Part | Owns | Size | State |
| --- | --- | --- | --- |
| **QML** (strategy library) | the strategy contract: factory, declaration, parameters with ranges, versioning, conformance gates, the Stage 0 research mill, ATC/PolicyPair (a non-Book risk seam) | 16,500 lines | exists; says "the bot may not size" and forbids written conditions (DEC-0175); no block catalogue; no real bot beyond the example |
| **The dictionary** (Stats, outside the repo) | the trader vocabulary: 239 role-neutral entries in 4 family files; the A to I strategy record; the four pillars as views; a logic graph (`graph.yaml` with ALL, K_OF_N, sequence) | 4 files | exists as prose; no code; FX and crypto spot only; 44% of the concepts the MQL5 corpus uses (r36) |
| **The unit** | the thing itself | 0 | missing: a Library page with no fields; no document format; no compiler |
| **QMB** (backtester) | replay, cost ports, optimiser, robustness, sweeps, What-If views, results in exact money, trial ledger, one landing shape | 91,000 lines | exists; cannot trade a bot for agents (`silent` runner only); reader copies all history; results not in R; costs uncalibrated by design |
| **The MIS** (inside QMN) | six rule labelers, SQS, one fitted liquidity model, a volatility-only regime pipeline, a shadow lane | part of QMN | exists in code; has never run on a live feed; readers are the Book door and KSA, never bots |
| **Risk shapes** (`qmf-risk`, QMN capital) | Book and BMS grammar, admission, exit policy, a sizing ladder (defined, unwired), kill line, ratchet, bench, KSA, news windows | 17,700 lines plus QMN's | exists; has never sized a trade; no account guard, no daily loss limit, no house money |
| **Journals** | trades per account (`trade` kind with world and initial risk) | kind only | partial; no unit journal, no door for agents |
| **The trading node (QMN)** | cTrader live client, recording loop, virtual ledger, reconcile, seats, promotion, Book-level paper, protection set, its own observability stack | 98,000 lines | exists; Linux and systemd only; never deployed; "bot never sizes" at the seat door |
| **External connections** (`qmx-broker`, providers) | cTrader reads and demo sign-in; CCXT read-only spot; MT5 declaration; Dukascopy, Binance Vision, CCXT public, Databento, Firecrawl providers | 2,300 lines | exists; cTrader never run; Hyperliquid absent; no execution path for anything on the PC |
| **Data** (`qmf-data`, the market-data door) | typed monthly price partitions (ticks, bar-m1, fill, trades, book), the one door with per-study holdout, downloaders as workflows, old 10 GB ticks with checksums | 18,800 lines | exists; downloaders never run on the real folder; door defaults reversed by stacked PRs |
| **The workflow engine and templates** (QMA v2) | 13 node kinds, triggers including Library events, PC and remote workers, 45 templates (22 run, 23 drafts) | 39,000 lines | exists; drafts wait on `qmb-door` and `trading-node` |
| **The Library** | 39 kinds, 39 link types, governed drafts that wait for your click, branch, merge, history, Hub | 7,700 lines | exists; unit fields empty; no journal kind |
| **DevOps** | engine ledger and spans; OpenObserve deep logs (stacked, PR 232); QMN's Grafana, Loki, Prometheus | | two stacks, one never run; no unit-level observability yet |
| **Harness and copilot** | chats, guard hook, delegate, skills, packs | built | exists; no skill for markets, units, QMB or QML |
| **Contracts and docs** | `docs/` (27 Sep), CT contracts, DEC rulings | | out of date; 14 rows contradict the new intent |

### 9.2 How they connect, and what crosses each connection

This is the loop you want, drawn once, with each arrow naming what crosses it. Arrows marked **built** exist in code; **missing** do not.

```
Source (video, article, chat, Stats)
   │  text + citations                                   built: intake templates a, rs1, rs2, rs4 (run today)
   ▼
Idea record (Stats A–I; Library hypothesis/strategy kinds)
   │  a unit document: named slots, blocks by id, numbers with ranges,
   │  market needs in dictionary words, data needs, lineage           MISSING: the document, the unit fields, the compiler
   ▼
QML  ──compile──►  factory(declaration, assignment, read surfaces) → callback(instant) → intents   built: the seam
   │  intents: entry, exit (size must be allowed for units)           built, blocked: "the bot may not size"
   ▼
QMB  ◄── prices (typed partitions through the door) ── Library/data   built
   │  a run: unit + partition + costs → trades with money, R, excursions, readings seen   MISSING: runner that trades, R, receipts
   │  tries counted at the door                                        partial: trial ledger exists, no correction
   ▼
Judge  → verdict + card                                                partial: deflated-Sharpe block exists; no shared judge
   │  a governed draft waiting for his click                           built: landing to refs/drafts
   ▼
His click
   │  unit + ticked markets + account
   ▼
Trading runtime (QMN today; PC first)  ◄── feed keeper ◄── broker   MISSING: a long-lived feed on the PC; per-unit paper; demo order path
   │  paper/demo/live trades → unit journal (unit, world, machine)   MISSING: journal kind, writer, door
   │  guard verdicts (KSA, kill line, SQS, news) → node journal        built in QMN, never run
   ▼
MIS readings (library code, same in QMB and live) ─► stamped history ─► per-session match list ─► placement inside the ticked list
                                                                        partial: labelers exist inside QMN; no shared package, no history, no list
Agents ◄── journal door, reading history, forecast ledger             MISSING: every door
Templates fire on Library events (built) and call QMB (missing door) and the node (missing door)
```

What crosses each connection is small and typed: a unit document; a run request and a result with trades in R; a verdict and a card; a ticked list and an account; trade rows and guard rows; stamped readings. None of these crossing shapes exists today except the trade kind and the price partitions. That is the whole gap.

### 9.3 What is truly missing, in build order

1. Land the stack (nothing to design).
2. The unit document and its compiler into QML's factory; unit fields in the Library; "the bot may not size" lifted for units. (The gold mine's logic graph is this document's ancestor: `strategy-dna.md` E layer, `graph.yaml`, CHECKED. Say so; it is your August design coming back.)
3. A QMB runner that trades a unit; the windowed reader; results in R with excursions and the readings seen.
4. The first sizer and exit set from the risk session, as the unit's socket contents.
5. A feed keeper and a demo order path on the PC; a unit journal kind, writer and door.
6. One shared judge block; tries counted at the door; the proposal card.
7. The labelers as a shared package with stamped history and a per-session match list.
8. The doors the 23 draft templates wait for.
9. A trading-server kind on the connect dialog.

Everything in 43's six foundations maps onto 2, 3, 5, 6 and 7. The foundations are right. Their shape as one file is wrong for you. Split them into the areas above and keep them.

### 9.4 Is "we have almost everything" true?

Yes, by volume: about 300,000 lines merged, the engine complete, QMB and QMN large and detailed, the Library and data store in place, the funnel drafted, the vocabulary written. No, at the centre: the unit does not exist as a thing, no backtest trades, nothing has run on your folder. The missing pieces are small in lines. They are also the pieces every other piece attaches to, which is why the whole thing feels unassembled. Build the centre; the rest is already waiting.

---

## 10. On the convergence file (43), plainly

You said "I'm not trusting this work" (T3:1080). Here is an outsider's judgement so you can decide whether to keep it.

**What is right in it.** The six foundations (stamped trade, stamped readings, the unit as data, journals with one writer per stream, tries at the door, the instrument record) are the correct first build and match the code gaps exactly (section 9.3). The per-area option tables are honest and name the shipped files each option touches. The Subtract-first list is the right kind of thinking. The identity-by-edit-type table answers your "what makes something new" without a judgement per case. The Must column reaches a demo unit. The review (44) found every quote of yours exists word for word and every code claim it checked is right.

**What is wrong in it.** One file across seven areas. Nine decisions, four of them not yours. Decisions you had already settled asked again in the first draft. The self-configuration demo sent to the risk session. "Specialist" and "terrain" still in the text after you disowned them. Inferred numbers you never asked for, now labelled but still there. It reads to the lead; it does not read to you.

**My recommendation.** Keep it as the source. Split it into the per-area files you named, each a builder packet with: what exists (paths), what is added, what must not break, how it is checked, and which of your rulings bind it. Strip every decision you have answered. Keep the veto ledger of lead calls beside it. Do not run another convergence.

---

## 11. The few questions only you can answer

Six. Each changes the route. Each has my recommended answer.

**1. Do the unit's sizing and exits come back inside the unit build, or does the risk session stay separate?**
Recommended: separate session, but it runs now, in parallel, from `RISK-SIZING-PACK.md`, and its first deliverable is the smallest honest sizer and one exit family for the reference unit. The unit build does not reach demo without it. A backtest may use a labelled fixed-fraction stub; demo may not.

**2. What is the first reference unit, and on which market?**
Recommended: yes to one reference unit before any breadth. Use a strategy already recorded in Stats (the layout demo there is "Asian high, London reversal", `strategy-dna.md` example package, CHECKED) or one mean-reversion scalper you pick, on EURUSD 1-minute, cTrader demo, from your PC. One unit, one market, one account. Everything else waits for its first journal.

**3. For the PC rehearsal of live trading: run QMN under the Linux layer your PC already has, or give the Windows host a trading role and port QMN's protection set into it?**
This is the one real architecture choice left. Recommended: rehearse under WSL now, because it exists today and QMN needs it; decide the Windows trading role after the first paper trades, when you know what QMN's seats and Book admission must become around the unit. If WSL bites (clock, idle shutdown, disk) within the first week, switch to the Windows role. INFERRED.

**4. Your April rules (no leverage, swap-free, no futures) against the markets you added.**
Recommended: a per-unit tag, "swap-free, no leverage", honoured where a broker offers it, never a global block. The reference unit on cTrader demo is unaffected either way. This is your values; I only ask that it be one sentence, once.

**5. The words on your screens.**
Recommended: keep "unit", keep "MIS", "regime" means trending against ranging (rename the code's buckets "volatility state"), "trading server" and "workflow server", "market settings" and "market version" for the two halves of what you called System 2 unless you prefer your own words. Say yes or give your own; then they are stone.

**6. Which ten rulings are stone?**
Recommended list: a unit is one complete trading algorithm including its own sizing and exits; the MIS reads and outputs, units pick, no unit needs it to trade; only you promote, the only automatic move is a risk stop; local first, servers stand in; nothing capped; agents never touch money and never size by judgement; design for complexity, not a complex system; keep "unit"; the dictionary is rebuilt in form and kept in content; coded is not built until it has run on your folder. Type them once. After that, nobody re-asks, and you do not re-open without new information.

Not for you: your country (you have the accounts), the live-key location (a node-pass technical call), the data terms (one line: own backtests only, recordings are the history), the Claude sign-in for the replay study (do it when convenient), the dictionary (settled).

---

## Appendix: evidence index

Transcript positions used above (all CHECKED by reading the files):

| Moment | Where |
| --- | --- |
| MT5 idea-mining brief | T1:9, 2026-10-20T10:41 |
| "scorecard doesn't make sense"; the MIS noise question | T1:264, 2026-10-20T11:51 |
| MIS as load balancer, the unit as self-configuring bot | T1:376, 2026-10-20T12:20 |
| two faces of QMX; agents are the intermediators | T1:444, 2026-10-20T12:39 |
| "two different bots with the same bloody logic" | T1:484, 2026-10-20T12:49 |
| strategy funnel with branches | T1:513, 2026-10-20T12:59 |
| expand with CIS, party mode, wayfinder | T1:651, 2026-10-24T16:18 |
| three lenses: agents, traders, creators | T1:783, 2026-10-24T16:30 |
| StrategyQuant; "nothing is out of scope" | T1:828, 2026-10-24T16:45 |
| phone review: QMB not live, router only routes, "keep it stupid simple", "you're not adding much" | T1:1177, 2026-10-24T17:36 |
| QML deserves an upgrade; deep modules; the unit replaces the bot | T1:1211, 2026-10-24T17:43 |
| "note these things down" | T1:1297, 2026-10-24T17:48 |
| the lead declares the funnel converged | T1:1348, 2026-10-24T17:51 |
| "don't go to the architecture step" | T1:1374, 2026-10-24T18:41 |
| "you're wasting my tokens" | T1:1443, 2026-10-25T03:45 |
| the long 27 Oct dictation | T1:1574, 2026-10-27T03:03 (also D27) |
| "don't fold into architecture yet" | T1:1672, 2026-10-27T03:14 |
| round 2 review; System 1 and 2 introduced | T1:1903, 2026-10-28T17:49 (also D28) |
| "the MIS just reads and outputs" | T1:1951, 2026-10-28T18:23 |
| "system one grows into system two" | T1:1999, 2026-10-28T18:48 |
| "the dictionary already has context" | T1:2051, 2026-10-28T19:03 |
| session goal: code first, numbers later | T2:6, 2026-10-29T16:00 |
| "read it as a third party"; the stack question | T2:55, 2026-10-29T16:09 |
| the lead's third-party read | T2:65, 2026-10-29T16:13 |
| brain dump: Claude builds more machinery; scalper types; QMB toss or rebuild; "by the end of tomorrow" | T2:135, 2026-10-29T16:41 |
| "problems without solutions"; "I'm not that desperate"; exits and the risk session | T2:219, 2026-10-29T17:25 |
| agents as analysts; "broaden before defining"; wayfinder introduced | T2:325, 2026-10-29T17:53 |
| "a model may remember past markets is sloppy" | T2:385, 2026-10-30T04:38 |
| branches plan/unit-system and build/unit-system | T2:442, 2026-10-30T04:43 |
| "no explainer site" | T2:602, 2026-10-30T05:30 |
| QML missed; "It's numbers"; System 1/2 were explanation names | T2:788, 2026-10-30T06:11 |
| "no rush, 3 to 4 days, sloppiness won't be tolerated" | T2:845, 2026-10-30T06:14 |
| "multiple experiences" explained; "launching agents with intent" | T2:858, 2026-10-30T06:19 |
| exits to the risk session; 1m and 5m is correlation; the gold mine | T2:1000, 2026-10-30T06:42 |
| what is left after QML | T2:1125, 2026-10-30T07:20 |
| "the agentic side is already done"; the node must run on my machine; "simple data schemas" | T2:1148, 2026-10-30T07:31 |
| "lean isn't the right wording"; "you take the wheel" | T2:1208, 2026-10-30T07:35 |
| Codex paused; research to Claude agents | T3:515, 2026-10-30T10:53 |
| "be efficient with agents" | T3:737, 2026-10-30T11:01 |
| the 31 Oct walkthrough and nine decisions | T3:937, 2026-10-31T03:13 |
| the long correction: sloppy, one file, mixing areas, journals, WSL, keys, connections, layer the architecture | T3:1080, 2026-10-31T04:05 |
| "firing in so many directions"; the Fable advisor asked for | T3:1091, 2026-10-31T04:08 |
| this read requested | T3:1128, 2026-10-31T04:13 |
| "stop the other agents" | T3:1134, 2026-10-31T04:14 |

Code positions used above (all CHECKED with `git show` or `git ls-tree` at `origin/engine/base` d82be318 unless marked):

- `qml/src/qml/protocol/intents.py:1-8` ("the bot may not size")
- `qml/src/qml/declaration/confluence.py:51-61` (`FORBIDDEN_CONDITION_FIELDS`, DEC-0175)
- `qml/src/qml/conformance/__init__.py:1-6` (the conformance gate)
- `qml/src/qml/protocol/factory.py:1-6` (the factory seam)
- `qml/examples/conformant_bot/bot.py:1-9` (the only example bot; never sizes)
- `qmb/src/qmb/doors/mcp/__init__.py:1-6` (MCP door scaffolded, not shipped)
- `origin/build/wu4:qmb/src/qmb/host/backtest_door.py:60` (`RUNNERS = {"silent"}`)
- `packages/qmf-risk/src/qmf/risk/sizing.py:1-34` (sizing ladder defined-unwired, DEC-0158)
- `qmn/src/qmn/seats/dispatch.py:1-8` ("bot never sizes")
- `qmn/src/qmn/mis/labelers.py:1-6` (six rule labelers, SQS)
- `qmn/src/qmn/mis/regime_design.py:72-78` (volatility only, "never a direction claim")
- `qmx-agents/packages/qmx-library/src/qmx_library/kinds/unit.schema.json:7-10` (no fields)
- `qmx-agents/packages/qmx-broker/src/qmx_broker/adapters.py:1`, `:59-76`, `:103`, `:247` (CCXT read-only spot, MT5 declaration, cTrader adapter)
- `qmx-agents/packages/qmx-broker/src/qmx_broker/providers/` (Dukascopy, Binance Vision, CCXT public, Databento, Firecrawl, http)
- `scripts/probes/data/FINDINGS-ctrader.md:5` ("have not run against cTrader")
- `git grep -i -l hyperliquid` over qmb, qml, qmn, packages, qmx-agents/packages at `origin/engine/base` and `origin/build/sy5` = 0 files
- `git log -1 main -- docs` = 03ad2f00, 2026-09-27
- `git branch -r --sort=-committerdate`: `origin/engine/base` d82be318 (26 Oct), `origin/build/sy5` 074670ac (29 Oct), the `build/*` stack
- line counts: `git ls-tree -r --name-only origin/engine/base <path> | grep '\.py$'` piped through `git show | wc -l` for qml/src, qmb/src, qmn/src, qmf-risk, qmf-data, qmf-indicators, qmx-engine, qmx-library, qmx-broker

Stats (read on disk, CHECKED): `C:/Users/Mubarak/Desktop/Stats/dictionary/README.md` (role-neutral primitives, four family files, 12 fields, `##` entries); `context-regime-and-intermarket/context-filters-confirmations.md` (69 `##` headings, one of them the coverage table); `Stats/schema/strategy-dna.md:128-141` (four pillars as views over A to I; lenses 5 to 8; the E layer `logic/graph.yaml`).

Research files relied on where I did not re-run the check (their own CHECKED labels): 14 (four copy sites in the replay), 16 (pooled vs per-cell), 18 and 42 (groundings), 19 (Intent Aggregator), 24 (the picking simulation), 31 (WSL present, network-bound timing), 35 (strategy anatomy), 36 (44% coverage), 38 (venues), 44 (the review).
