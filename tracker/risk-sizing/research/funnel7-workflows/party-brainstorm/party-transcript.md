# Party mode transcript: workflow templates around units

Run 2026-10-30 by the workflow-templates expansion agent. Skill: `bmad-party-mode`, **session mode** (one mind voices every persona, no subagents), run as an explicit `--non-interactive` party on the brief's intent until a natural close. Activation scripts ran: `resolve_customization.py` (`party_mode = session`), `resolve_config.py` (user Mubarak, English), `resolve_party.py` (`installed_agents_resolved: false`, `active: installed`). The inline cast below is the roster for the session. Per `references/party-memory.md`, an ad-hoc inline cast keeps no memlog, so this transcript is the party's only record. Speaker tags are text, not emoji (project rule).

**Voices with limits.**
- **The operator** speaks only in verbatim quotes, each tagged with its source line: `T1:n` = `operator/transcript-2026-10-20-to-28.md`, `T2:n` = `operator/transcript-2026-10-29-to-30.md`, `D27:n` = `operator/2026-10-27-review-dictation.md`. Line numbers are `grep -n` numbers. All 64 quotes were checked by script against those lines (`quotecheck.py` in the run's scratchpad: "64 quotes, 0 missing").
- **Ada**, the QMA v2 workflow engine's designer, speaks only from research 42 (`R42 §n`) and from the shipped template files at the stack tip `origin/build/sy5` (074670ac), read with `git show` by this run's parser (`tpl.py`). Where she cites a template's step or default, that is CHECKED from the definition or README.
- **Floor**, the old QMX WF1/WF2 designer, speaks only from research 19 (`R19 §n`).
- **Sol**, the GPT model that built the Hermes source workflows in August, speaks only from research 39's ledger (`R39 <row id>`). When the room asks what the record does not hold, Sol says so.

**Nothing here is a decision.** Clashes stay open. Ideas and questions carry their round tag (P1 to P12) into `workflows-field.md`.

## The room

| Tag | Name | Who |
| --- | --- | --- |
| [ENG] | Ada | Designed the QMA v2 workflow engine. Knows every node kind, trigger and landing rule. Precise, a little proud, hates "we'll need a new engine". |
| [WF] | Floor | Designed old QMX's WF1 (find and build bots) and WF2 (iterate and vary). Remembers departments, mail loops and opinion nodes. Nostalgic and defensive. |
| [SOL] | Sol | The GPT model that built the August source workflows (Friendly greeting, the gold mine). Formal, fond of pipelines with ten stages. |
| [FAC] | Priya | Quant researcher who runs a strategy factory: generation, screening, a graveyard, a weekly committee. Thinks in throughput. |
| [SQX] | Lena | StrategyQuant X power user. Genetic builder, robustness tests, QuantAnalyzer. Thousands of strategies a night. |
| [BLD] | Pip | A cheap building agent. Turns a card into a unit through QML. Literal, eager, easily confused, honest about it. |
| [OOS] | Dr. Ostrova | Judge who hates overfitting. Counts every try. Trusts no in-sample number. |
| [MKT] | Cass | A market analyst agent. Reads a day's or week's bars, the news calendar and the MIS logs. Wants to make calls. |
| [UNIT] | Cor | A unit analyst agent. Reads one unit's journal: trades taken, skipped, missed. A coroner by temperament. |
| [COST] | Penny | The token-cost-conscious operator voice. Counts calls, context and attention. Allergic to always-on agents. |
| [SKEP] | Morrow | Skeptic of agent claims. Assumes every analysis is a story until a script recomputes it. |
| [OP] | The operator | Only his own words, quoted. |

---

## P1. What is already on the shelf

**[ENG] Ada:** Before anyone invents a funnel, look at what ships. Forty-five templates at the stack tip. Twenty-two run today, twenty-three are drafts waiting on a named need (R42 §1.8). Every one that touches a backtest waits on `qmb-door`.

**[OP] The operator:** "I think WF1 and 2 are built. I'm not certain anyway." (T2:1148)

**[ENG] Ada:** Half right. The shapes are built. `b-build-and-prove` is your WF1 from idea to paper card. `d3-iterate-against-qmb` and `l4-overnight-lab-loop` are WF2. `rs6-hypotheses-from-dead-ends` is the rehab of failures. All drafts. None runs (R42 §1.8; READMEs at the tip).

**[WF] Floor:** Drafts. We had flows that ran. WF2 started from three triggers: WF1's evidence handoff, a WF3 rehab token, or an operator diagnosis request (R19 §1). Show me one of your templates that starts when another one finishes.

**[ENG] Ada:** None does. Every template trigger is cron, interval or manual. The event trigger exists, it fires when an item lands in the Library, filtered by kind, output and producer. No template uses it (R42 §1.2).

**[WF] Floor:** So the chain is broken by design.

**[ENG] Ada:** The chain is unwired, not broken. One trigger row per handoff.

**[FAC] Priya:** Then the first template I'd want isn't a builder. It's the conveyor: what fires what.

**[OP] The operator:** "It's far better to enhance them." (T2:1148)

**[SKEP] Morrow:** And nothing in those forty-five uses a skill. Not one node names one (R42 §1.3). So "judging is a skill" is a sentence, not a file.

**[ENG] Ada:** Correct. Skills can come from three places: a plugin file, a published Library skill, or a pack (R42 §7). The engine already offers whatever a node names. Nobody has written the skill.

**[BLD] Pip:** Can I ask something dumb? The builder role. Which model am I?

**[ENG] Ada:** Strong. `roles.builder` defaults to the strong tier. Triage, scanner and judge default to cheap. Reader and writer to mid. All UI-editable (`settings.py:175-188` at the tip).

**[OP] The operator:** "most of the work I've been talking about is done by cheap workhorses" (T1:513)

**[COST] Penny:** There it is. The shipped default is the opposite of his seed. Builders strong, judges cheap.

**[OOS] Dr. Ostrova:** The "judge" role there is an LLM that writes a verdict paragraph. My judge is a script. The names collide.

*Carried into the field: the conveyor template (event-trigger chain); builder-tier default vs "cheap workhorses"; the word "judge" means two things; drafts are WF1/WF2 shapes already.*

---

## P2. Intake: where ideas come from

**[OP] The operator:** "Book, bloody hell, even just me explaining." (T1:513) And: "a conversation between me and the co-pilot, or between me and any agent, a transcript per se" (T1:513)

**[SOL] Sol:** The August pipeline had ten stages: discovery, immutable inventory, deterministic extraction, visual analysis, temporal alignment, atomic claims, primitive and role mapping, graph, candidate or entry hypothesis, then QMX (R39 N1). Before that, a two-pass sort: cheap triage on metadata, then informed classification after reading (R39 H11).

**[ENG] Ada:** `a-fill-the-library` already does most of that for a video, a playlist or saved posts. Intake script, capture, save the source, prefilter, triage on the cheap role, read sections, quotes checked by a grader, an extractor agent, three sample reads and an agreement script, an audit (tip definition).

**[SOL] Sol:** Then it lacks the channel dossier. A seed video leads to the creator, the playlists, the guests, then related channels. Podcast channels "might be the actual gems" (R39 H12).

**[FAC] Priya:** In my shop the dossier is the most valuable object. You score the source, not just the item. A creator who never gives exits is a known quantity.

**[SOL] Sol:** Creator research is creator-profile evidence, never a rule of that strategy (R39 H6).

**[MKT] Cass:** What about his copilot chats? Nobody's built that intake.

**[ENG] Ada:** There is `clippings-into-research` on an interval trigger, and `feed` for rss, sitemap, page-diff, api and bulk files (R42 §1.8). No template reads a copilot transcript.

**[COST] Penny:** A chat transcript is free. No download, no vision model. Cheapest source in the building.

**[SKEP] Morrow:** And the most dangerous. A source that tells the agent what to conclude. A transcript of him enthusing about gold is not evidence that gold mean-reverts.

**[SOL] Sol:** The record agrees. Model output is interpretation. Transcripts and frames are evidence (R39 H8). His words would be evidence of his idea, not of the market.

**[BLD] Pip:** So when he says "try this on gold", I get an idea card, not a fact.

**[SOL] Sol:** Each rule pinned to a timestamp or exact location (R39 H5). The eight-part completeness checklist: location, trigger, filters, entry semantics, invalidation, exit or management, timing, scope (R39 GM 2724 entry in §2.2).

**[SQX] Lena:** SQX skips all of this. It generates from building blocks with no source. Half his ideas could come from random block combinations, scored the same way.

**[SOL] Sol:** The record has no generator without a source. Genetic algorithms were "not found" in the record (R39 GM 3261 in §2.2).

**[OP] The operator:** "hybrids, tribrids, quadbrids, whatever" (T1:264)

**[SQX] Lena:** That's a generator.

*Carried: chat and copilot transcripts as intake; channel dossier; a sourceless generator branch beside sourced ideas; his words as idea-evidence not market-evidence; "save this" capture.*

---

## P3. Building: who writes the unit

**[BLD] Pip:** Give me a card and the QML verbs and I'll build. Give me an ambiguous card and I'll invent a number and not tell you.

**[SOL] Sol:** "A bot that has ambiguity shouldn't be tested." (R39 K14)

**[OP] The operator:** "when you get less intelligent models, they're obviously going to make mistakes, big ones in fact, if you don't give them standards" (D27:9)

**[ENG] Ada:** That is what the graders are for. Deterministic only today; the LLM grader mode is planned (R42 §1.1). A script can refuse a card with holes. `l1-idea-to-first-result` has a `complete` rule node before the builder runs.

**[OOS] Dr. Ostrova:** I want blind building. The builder never sees a backtest while writing. Otherwise every "fix" is fitting.

**[ENG] Ada:** `d3` already hides the holdout from the diagnoser (`blind.py`, tip definition). Nothing hides the in-sample from the builder.

**[BLD] Pip:** If I can't see results I can't tell if I built it right.

**[OOS] Dr. Ostrova:** You check you built it right against the card. A second model re-reads the unit against the source (R39 H16). Results are not your business.

**[FAC] Priya:** In practice I split it: a builder that compiles to the spec, and a translator check that the code says what the hypothesis says. The papers call that the alignment check (R11 J6).

**[COST] Penny:** Two models per unit, then. Who pays?

**[OP] The operator:** "if I'm on a monthly subscription of Claude, I mean, the costs are not going to be that much" (T2:385)

**[COST] Penny:** The cost is the weekly limit and his attention, not dollars. A template that burns the week's limit by Wednesday is a bug.

**[WF] Floor:** We had vanilla and spiced. Vanilla was the code as it comes from the source. Spiced was the logic plus the cTrader article logic (R19 §1, operator words at `GPTR:1400`).

**[ENG] Ada:** `d4-variant-comparison` still labels variants `spiced` and `structural` (README at the tip).

**[BLD] Pip:** And when QML doesn't have the block I need?

**[SOL] Sol:** The record says nothing about that. The dictionary was designed and never populated (R39 GM 3261 in §2.2).

**[SKEP] Morrow:** Then the builder writes Python and calls it QML. Make it say so.

*Carried: blind building; alignment re-read by a second model; vanilla/spiced as the first two nodes of every family; missing-block append request; ambiguity stop as a grader; cost = limit and attention.*

---

## P4. Testing and judging

**[OP] The operator:** "a skill literally has hooks and deterministic scripts and so on and so forth, which means it can call QMB" (D27:9) And: "I don't think it should be really up to agents" (D27:9)

**[ENG] Ada:** Here's the snag. A workflow cannot declare its own hook. A pack's hooks are never written, by design (`HAR/packs.py:8`, `:44`, R42 §7). The agent step's hooks are the engine's own sink only.

**[OOS] Dr. Ostrova:** Then the "hooks" in his judging skill must be something else.

**[ENG] Ada:** Graders and script nodes are the hooks a workflow has. A grader sits between steps and fails the run. That's a hook in all but name.

**[SKEP] Morrow:** A hook the agent can't skip. A script step the agent can't skip. Fine. But a skill is something an agent calls. An agent can decide not to call it.

**[OOS] Dr. Ostrova:** Which is why judging should not be a skill the agent calls. It should be a block the workflow runs whether the agent likes it or not. The skill is for explaining the verdict.

**[OP] The operator:** "we don't want to be too strict" (D27:9)

**[SQX] Lena:** SQX's robustness tab is exactly this: walk-forward matrix, Monte Carlo, what-if on costs. You run it, it shows a grid, you pick. It never picks.

**[ENG] Ada:** `b-build-and-prove` hard-codes its gates in the README: 100 trades, walk-forward efficiency 0.5, Monte Carlo 5th percentile above zero, positive expectancy at 1.5x costs, deflated Sharpe 0.95.

**[OOS] Dr. Ostrova:** Numbers. Defaults, editable. Fine. What I care about: every screen, every child, every best-of counts as a try in the family (R11 J1). `overfit-gates` already deflates over the family, dead parents included.

**[FAC] Priya:** And the holdout is touched once, by the survivor. `d3` and `l4` do that.

**[SOL] Sol:** August's staged tests: semantic gates, screening, ablation, interactions, sensitivity, locked challenge (R39 K9). And three instruments: home pair, close analogue, adversarial (R39 K1).

**[OOS] Dr. Ostrova:** The adversarial pair. That's the only test in this room I'd fight for.

**[SKEP] Morrow:** And when the judge script has a bug, who judges the judge?

**[ENG] Ada:** `render_and_grade` checks every number in the prose against the script outputs. That's the template convention (b, d3, l4 READMEs).

**[SKEP] Morrow:** That proves the prose matches the script. Not that the script is right.

*Carried: the judge as a block the workflow runs, the skill as its explainer; hooks a workflow can actually have (graders, scripts) vs Claude hooks it can't; adversarial instrument; judge-of-the-judge; one judge block shared across templates.*

---

## P5. The pass branch: expand or stop

**[OP] The operator:** "you need to know when to expand. And when not to expand" (T1:513)

**[OP] The operator:** "(1) get the logic as is, or (2) rewrite the logic or adjust it to fit the 1 minute interval" (T1:513)

**[FAC] Priya:** Expansion is where factories die. Every new instrument is a new try. Ten instruments times four timeframes, and something will pass by luck.

**[OOS] Dr. Ostrova:** So the expansion branch inherits the parent's try count and adds its own. And it gets a fresh window the parent never saw.

**[WF] Floor:** We had WF4, "Ecological + feature mutation" (R19 §1). The vault later called it a phantom. He remembered it was real.

**[SQX] Lena:** SQX does "what-if on other markets" as a robustness test, not as a new strategy. Same unit, different market, report the matrix.

**[ENG] Ada:** `d4` already draws that line: instrument, timeframe, params and spiced stay `variant_of`; structural and model-made are `derived_from` (README).

**[OP] The operator:** "It gives us almost an impeccable placement." (T1:513)

**[MKT] Cass:** Placement needs me. Which markets were in the unit's condition when it worked? That's market analysis, not unit analysis.

**[UNIT] Cor:** And which ones it traded badly in. I'd like the expansion card to carry both: where it held, and where it broke.

**[OP] The operator:** "some domain expansions can come with sniping" (T1:513)

**[BLD] Pip:** Sniping is a timing overlay? A level? I'm confused.

**[SOL] Sol:** "sniping can be a level liquidity window it can be a trigger... can even be bloody confirmation" (his words as R39 FG 902 records them). Sniping spans several roles (R39 FG 831 entry).

**[COST] Penny:** Expansion is also the cheapest step. No new logic, just reruns. Scripts only. No agent at all unless the rewrite branch fires.

*Carried: expansion as a script-only matrix; expansion inherits tries and needs fresh windows; expansion card carries where it held and broke; sniping as an expansion overlay; old WF4 revived as expansion.*

---

## P6. The fail branch: why did it fail, and where would it hold

**[OP] The operator:** "If they fail, we need to be able to know why is it failing. So which means QMB should either provide that, or the agent should figure that out." (T1:513)

**[OP] The operator:** "do we have any context under QMX in which these rules are met?" (T1:513)

**[OOS] Dr. Ostrova:** This is the most dangerous branch in the building. Search hard enough and some context always works. The proof must come from data the search never saw.

**[UNIT] Cor:** Before "where would it hold", I want "why did it die". A failure library with causes: no trades, costs ate it, one quarter carried it, the trigger fired late. Then you count recurrences.

**[WF] Floor:** The July Coroner. Necropsies of benched bots and exam rejects, a Graveyard Index, judged on recurrence rate of known death causes (R19 §8).

**[ENG] Ada:** `rs6` mines dead ends weekly. It wakes on five or more new ones, clusters them, proposes one fixed move each: condition, slow down, invert, transplant or drop. A kept hypothesis inherits the parent family's trial count and its test data starts after every parent window (README).

**[OOS] Dr. Ostrova:** That last line is the whole branch. Keep it.

**[SQX] Lena:** "Invert" is underrated. A strategy that loses reliably is a strategy, after costs, sometimes.

**[OOS] Dr. Ostrova:** After costs it rarely is. Spread eats both sides.

**[OP] The operator:** "this is why we needed agent memory, dude" (T1:513)

**[ENG] Ada:** Templates declare memory scopes: `workflow`, `run`, `operator` (tip definitions). No template step reads or writes memory rows yet; `rs6`'s README says the "do not retry" notes need the real Library's one-writer door.

**[COST] Penny:** Memory is the cheapest thing here. A dead-end row read by a script costs nothing. It's the agent re-discovering the same failure that costs.

**[SKEP] Morrow:** And an agent "remembering" a cause it guessed is worse than no memory. Memory rows need the receipt that made them.

*Carried: failure causes as a typed list with recurrence counts; the context search's proof on unseen data; invert as a move; memory rows with receipts; rs6 as the fail-branch core.*

---

## P7. The rewrite branch and the family tree

**[OP] The operator:** "So you can bring in a Claude model, for example" (T1:513)

**[BLD] Pip:** So I do the bulk and someone smarter rewrites when I get stuck. When am I stuck?

**[FAC] Priya:** When the cheap loop plateaus. `l4` already calls a plateau after thirty trials without a better validated score, and then changes the search space by one fixed move (README).

**[OOS] Dr. Ostrova:** And the rewrite is a new version, linked to its parent. Its tries add to the family.

**[SOL] Sol:** Variants as small overlays: `replace`, `add` (R39 G1). Edit operations with an ordered stack and a result digest (R39 G2). Corrected successor as the way ambiguity gets resolved (R39 G8).

**[WF] Floor:** WF2 tracked mutation depth, rule-chain length, feature count, against "mutation sprawl" (R19 §1).

**[OP] The operator:** "It all started from one bloody idea." (T1:513)

**[UNIT] Cor:** Then every node in the tree needs its death certificate or its birth certificate. Who made it, which model, from which parent, which branch.

**[ENG] Ada:** Lineage edges already get written by a `lineage.py` script in seven templates: b, bc, d3, d4, l1, p1 and revolution-loop (tip parser). The family-tree tab exists on the unit page; the unit kind has no fields yet (R42 §6.1).

**[SQX] Lena:** SQX keeps a "databank" per run. You can re-seed the genetic builder with the best of an old databank. That's crossover across runs.

**[OP] The operator:** "hybrids, tribrids, quadbrids, whatever" (T1:264)

**[OOS] Dr. Ostrova:** Crossover across families multiplies the try count. Fine, as long as it's counted.

*Carried: plateau as the rewrite trigger; model escalation ladder; birth certificate per node; cross-run reseeding; crossover across families with combined try counts.*

---

## P8. Agents analysing markets

**[OP] The operator:** "we can have agents that can look or request for that day's data" (T2:325) And: "They can use the TA, they can use the MIS logs and the MIS itself. They can use, you know, the fundamentals" (T2:325)

**[MKT] Cass:** Finally. Give me the day's bars and the calendar and I'll tell you gold was mean-reverting in London.

**[SKEP] Morrow:** You'll tell me. Will you compute it?

**[ENG] Ada:** An agent step with the `data` toolset reads instruments, bars, features and the calendar. On trunk the door is shut by default; PR 207 opens it (R42 §1.7). A tool call cannot pass a study holdout or a run id yet.

**[OP] The operator:** "We are literally trading 24/7, my days." (T2:325)

**[MKT] Cass:** So there's no "end of day". I'd run per session close: Sydney, Tokyo, London, New York. And crypto on a rolling clock.

**[COST] Penny:** Four runs a day times fifty instruments is two hundred agent calls. No. Script first, agent only for the flagged markets. `dc-decay` already does that: the cheap explainer wakes only when a unit is flagged.

**[WF] Floor:** The Cartographer kept a living Week-Map: regime narrative, event-risk calendar, per-pair weather. Judged on calibration of weekly calls (R19 §8).

**[OP] The operator:** "think of an organogram" (T2:325) And: "agents that can specialize" (T2:325)

**[MKT] Cass:** A mean-reversion desk, a trend desk, a news desk. Each publishes calls.

**[SKEP] Morrow:** And each desk agrees with its own specialty. A mean-reversion agent finds mean reversion everywhere.

**[OOS] Dr. Ostrova:** Then score them. A dated call, scored by a script after the session. Calibration over weeks.

**[OP] The operator:** "How do we compare? Who's comparing?" (T2:385)

**[OOS] Dr. Ostrova:** The market compares. Nobody else needs to.

**[ENG] Ada:** `db-desk-brief` runs before each session today, but its node facts and MIS grid are left out (R18 §1.5). `t3` watches the calendar. `t4` runs a research desk overnight. None writes a call that a later script scores.

**[OP] The operator:** "you can consider tagging" (T2:325)

**[MKT] Cass:** Tag markets with what they did. Tag units with where they worked. Then match.

*Carried: session-close clocks instead of end of day; script-first scan, agent on flags; specialist desks with a forecast ledger; Week-Map revived; tagging markets and units; db-desk-brief extended with the MIS grid.*

---

## P9. Agents analysing units

**[OP] The operator:** "why did this unit trade this, or when it traded this" (T2:325)

**[UNIT] Cor:** Three questions per unit: why it traded, why it skipped, why it missed. The journal records signals detected but not taken, and missed trades (STATE "Journal = the unit's DevOps layer").

**[ENG] Ada:** No template can read a unit or its journal. No catalog row exists for units or journals; the unit kind has no fields (R42 §1.7).

**[UNIT] Cor:** So my whole family is a draft before it's a draft.

**[OP] The operator:** "you can't just use its QMB and the journals to decide" (T2:385)

**[UNIT] Cor:** Then what? I'd add the market side: what the market was doing when it traded. That's Cass's ledger.

**[MKT] Cass:** So unit analysis reads my calls. Two families, joined at the hip.

**[OP] The operator:** "those can be two different workflows rather" (T2:385)

**[SKEP] Morrow:** Separate families, shared data. Good. As long as Cor doesn't grade Cass.

**[OOS] Dr. Ostrova:** And a replay check: would QMB have taken the same trade on the same day? If not, the unit drifted or the feed did (R08 §2.3).

**[ENG] Ada:** `t7-trade-journal-review` slices a journal in risk units with a judge step; `dc-decay` runs CUSUM, the band and the cost tests; `dm-demo-monitor` checks fill quality. All wait on `trading-node`.

**[OP] The operator:** "it is not just as a result of the growth from QMX, but the agents would have already seen this also" (T2:325)

**[UNIT] Cor:** So my notes should reach the variant builder. A System 2 proposal carries my "why".

*Carried: traded/skipped/missed triad; replay-match check; unit analysis reads market calls; analyst notes as input to variant proposals; three journal templates waiting on the node.*

---

## P10. How agents prove what they claim

**[OP] The operator:** "We need them to be able to prove what they are producing in terms of analysis." (T2:385) And: "that can't be cheated, okay, or can't be manipulated" (T2:385)

**[SKEP] Morrow:** Separate the claim, the data and the score. Three actors, or three times.

**[OOS] Dr. Ostrova:** The claim is written before the outcome. The score is a script. The data is sealed or future.

**[ENG] Ada:** The engine already records what a step did: a ledger, run zones, spans, staged commits, run refs that never reach `main` from a test run (R18 §1.1; R42 §1.5).

**[SKEP] Morrow:** Then every number in an analysis cites a receipt: the tool call, its inputs, its output hash. A number with no receipt prints as "unproven".

**[OP] The operator:** "We also need to know in which ways they can be wrong before we define the tools." (T2:385)

**[SKEP] Morrow:** Fifteen ways are already listed: numbers never computed, wrong data, the window that tells the story, peeking at sealed months, grading its own work, sycophancy, a silent tool failure read as a result (funnel3 knot (b), F1 to F15).

**[MKT] Cass:** And if my calls are good?

**[OOS] Dr. Ostrova:** Then your calibration record says so after a few hundred calls. Not before.

**[OP] The operator:** "you need to give a pass, in other words, a landmark" (T2:385)

**[MKT] Cass:** So every analysis names its window as a field. "Since the Monday London open."

**[WF] Floor:** We had opinion nodes: subject, claim, typed evidence, confidence, author, superseded-by. And a resolver for disagreements; a breach of the formula "is not a matter of opinion" (R19 §8).

**[COST] Penny:** Proof is cheap if it's a script. Expensive if it's a second model on everything.

**[SKEP] Morrow:** Second model on disagreements only. Agreement is cheap and high-signal.

*Carried: receipts; claim/data/score as three roles; forecast ledger; landmark as a typed field; opinion nodes revived; a failure-mode replay test before choosing tools.*

---

## P11. Triggers, clocks and cost

**[ENG] Ada:** Triggers: cron with zones, interval, manual, after, webhook, event, session. One catch-up run after downtime. Templates install with triggers disabled; enabling is his click (R18 §1.2).

**[OP] The operator:** "placement is key. When are we, when is the workflow going to run" (T2:325)

**[MKT] Cass:** Session closes. Weekend for crypto. News events.

**[UNIT] Cor:** Every N closed trades. A drawdown threshold. A unit landing on paper.

**[ENG] Ada:** Those need event sources. Host jobs landing a maintenance result is stacked (PR 234). Trades landing from the node do not exist yet; `dc-decay` notes its event "every 10 closed trades" was left out for that reason (README).

**[COST] Penny:** Event triggers are the cost lever. A cron that wakes an agent to find nothing is waste. An event that fires on a real change is not.

**[ENG] Ada:** `crystallise-a-workflow` replaces a settled agent step with a script once replays agree (tip definition). That is your second lever.

**[COST] Penny:** That's the most important template nobody talks about. Agent first, script later.

**[FAC] Priya:** And the overnight loop? `l4` stops at six revolutions or two without gain or 200 trials.

**[OOS] Dr. Ostrova:** Those are caps.

**[ENG] Ada:** They're defaults in a template. Editable.

**[SKEP] Morrow:** A default no one edits is a cap.

*Carried: event sources needed (trade closed, N trades, drawdown, landing on paper); crystallise as the cost lever; loop defaults vs "nothing capped"; session-close cron set; weekly-limit awareness.*

---

## P12. Build now, write now, or let the Lab do it

**[OP] The operator:** "We either build them during the coding phase" (T2:1148) And: "the lab, that's one of the first things the lab maybe might do" (T2:1148)

**[ENG] Ada:** Writing them up is cheap; `build-workflow` already turns one line of intent into a tested draft and a publish card (R18 §1.6). A detailed card is a better line of intent.

**[FAC] Priya:** Building them now means building on doors that don't exist. Twenty-three drafts already prove that.

**[BLD] Pip:** I'd rather build from a card than from a chat. A card has the steps.

**[OP] The operator:** "the problem with workflows is that we might need skills, we might need hooks, so they need a lot of structure" (T2:1148)

**[OOS] Dr. Ostrova:** Then the judge block and the proof scripts get built in the coding phase. They are the structure. The templates can be cards.

**[SKEP] Morrow:** And cards rot. Twenty-three drafts already name doors in their READMEs that were redesigned since.

**[ENG] Ada:** A draft validates against the engine at install. A card does not validate against anything.

**[COST] Penny:** The Lab as first user is attractive. It builds the templates while it learns to build units. Same muscle.

**[OP] The operator:** "the proposal should be rendered in the UI" (D27:9)

**[ENG] Ada:** There is no in-workflow approval step. `human_gate` is planned only. Approval is the draft-and-publish card (R42 §1.1).

**[UNIT] Cor:** So every template ends on a card he clicks, and the next template is triggered by his click landing.

**[ENG] Ada:** His click publishes a draft. Publishing lands an item. An event trigger can fire on that landing. That's buildable today.

**[OP] The operator:** "the copilot can just help me understand what the workflows have done" (T2:325)

*The room breaks without agreement. Ada and Morrow are still arguing whether a card rots faster than a draft. Penny is counting calls on a napkin. Pip is asking Sol what sniping is.*

*Carried: build-now vs document-now vs Lab-first vs hybrids; his publish click as the event that fires the next template; cards validate against nothing; the judge block and proof scripts as the structure to build first; copilot explains runs.*

---

## Clashes left open

| # | Clash | Who | Round |
| --- | --- | --- | --- |
| C1 | Builder strong by default vs "cheap workhorses" | Ada vs Penny, Pip | P1 |
| C2 | Judging as a skill an agent calls vs a block the workflow always runs | Ostrova vs the operator's words | P4 |
| C3 | Hooks: his "hooks very important" vs workflows can't declare hooks | Ada vs Morrow | P4 |
| C4 | A sourceless generator branch vs every unit traced to its origin | Lena vs Sol | P2 |
| C5 | Blind building vs a builder who needs to see results | Ostrova vs Pip | P3 |
| C6 | Specialist desks vs desks biased to their own specialty | Cass vs Morrow | P8 |
| C7 | Template loop defaults vs "nothing capped" | Ada vs Ostrova, Morrow | P11 |
| C8 | Cards now vs drafts now vs Lab-first | Ada, Priya, Morrow, Penny | P12 |
| C9 | Expansion as robustness test of one unit vs as new variants | Lena vs Ada | P5 |
| C10 | "Invert" as a move vs costs on both sides | Lena vs Ostrova | P6 |
| C11 | Unit analysis reading market calls vs keeping families apart | Cor vs Morrow | P9 |
| C12 | His copilot chats as intake vs a source that steers the agent | Penny vs Morrow | P2 |
