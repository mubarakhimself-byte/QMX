# Party mode transcript: the unit's playing field

Run 2026-10-30 by the playing-field agent. Skill: `bmad-party-mode`, **session mode** (one mind voices every persona, no subagents), run as an explicit non-interactive party on the brief's intent until a natural close. Config resolved with the skill's own scripts: `party_mode = session`, inline cast, so per `references/party-memory.md` an ad-hoc cast keeps no memlog. Speaker tags are short text tags, not emoji, because this project's output rules forbid emoji.

**The operator's voice** speaks only in verbatim quotes. Each carries its transcript line: `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md`. Line numbers point at the line holding that whole turn (the convention of `research/17`). Personas cite grounding files as `R16`-`R19`.

**Nothing here is a decision.** Clashes are left standing on purpose. The questions are lifted into `playing-field.md` with the round number (P1 to P11) as their trace.

## The room

| Tag | Name | Who |
| --- | --- | --- |
| [1m] | Rafi | 1-minute FX and gold scalper on cTrader. Fast, impatient, counts in pips and seconds. |
| [DOM] | Dee | Index and futures order-flow trader. Lives in the depth of market and the tape. Scornful of "indicators". |
| [PERP] | Kenji | Crypto perps trader on Hyperliquid. 24/7, funding-obsessed, never sleeps on a weekend. |
| [15m] | Ama | Intraday trader, 15m to 1h. Opening ranges, session structure, patient. |
| [SWG] | Walt | Swing trader. Days to weeks. Thinks everyone else is overtrading. |
| [RISK] | Priya | Prop-firm risk manager. Loss ladders, daily limits, "show me the drawdown". |
| [OOS] | Dr. Ostrova | Quant obsessed with overfitting. Every claim is a try until proven otherwise. |
| [MICRO] | Marcel | Market-microstructure expert. Spreads, queues, latency, venue rules. |
| [STAT] | Sana | Statistician and ML engineer. Shrinkage, lags, labels, versions. |
| [AGT] | Iris | A QMX agent: an analyst that lives inside QMX and reviews markets and units. |
| [COP] | Copilot | The operator's chat helper inside QMX. Eager, a little too agreeable. |
| [WF] | Theo | QMX workflow engineer. Knows the shipped engine (R18 §1) cold. |
| [KISS] | Bea | Simplicity-obsessed systems architect. Deletes before she adds. |
| [300] | Jay | A retail trader with a $300 account. Asks the questions everyone forgot. |
| [OP] | The operator | Speaks only through his own transcript lines. |

Walk-ons appear as the topic calls for them: [CORONER] (the old system's post-mortem persona, R19 §8), [CTR] (a cTrader integration engineer), [TERMS] (a data-licensing pedant).

---

## P1. What is a unit, actually?

*A long table, late evening. Someone has taped the 8 Oct quote "a bot is no longer a bot, it becomes a trading algorithm fully" to the wall. Jay is the only one with a notebook.*

[OP] **The operator:** "a unit literally is now just a trading bot, to be honest. It's just that we combined." (T1:1211)

[KISS] **Bea:** Good. Then the unit is a bot. Done. Next topic.

[1m] **Rafi:** Not done. My bot is twelve lines of entry logic and a fixed stop. A "unit" has its own risk, its own sizing, its own journal, its own exam baseline. That's a desk, not a bot.

[OP] **The operator:** "The idea for the unit was, I was asking, can't I get one singular bot that can self-configure?" (T1:376)

[STAT] **Sana:** "No separations" and "self-configuring" pull against each other. Self-configuring needs a part that reads the record and a part that gets changed. That's a separation by definition. The question is whether it's visible.

[KISS] **Bea:** Hide it inside. Deep module. Small door, everything behind it.

[OOS] **Dr. Ostrova:** Then tell me what's frozen behind the door. If the sizing tunes itself and the exits tune themselves and the session weights tune themselves, the "unit" I tested last month is not the unit trading today. Which one did I prove?

[15m] **Ama:** And now he wants it malleable.

[OP] **The operator:** "a unit is obviously should be malleable. In other words, it should be able to be turned into an intraday or a scalper or, I don't know, even a swing trading unit, give or take." (T2:132)

[SWG] **Walt:** Turned *into*. So one unit changes style? Or one recipe that makes three different animals? Because my swing logic on a 1-minute chart is just noise with a stop loss.

[1m] **Rafi:** If my scalper "becomes" a swing unit, it's a new unit. Different holding time, different costs, different everything.

[AGT] **Iris:** From where I sit, I need to know what I'm allowed to compare. If "malleable" means one unit across styles, its journal mixes 40-second trades and four-day trades. I can't read that.

[COP] **Copilot:** Maybe malleable means the *template* is malleable? The operator picks "scalper" and QMX fills in scalper defaults?

[KISS] **Bea:** That's the first sensible sentence tonight.

[OOS] **Dr. Ostrova:** It's a guess wearing a smile. He didn't say template.

[300] **Jay:** Can I ask the dumb one? What does a unit do for me that an MT5 EA doesn't? Because I can buy an EA for forty dollars.

[OP] **The operator:** "So what makes QMX unique compared to things like Copilot and all that? Anyway, it's what I'm trying to justify to myself, okay? Compared to rather MT5, my bad, and all that stuff." (T2:6)

[WF] **Theo:** In the engine today, nothing. There is a `unit` kind in the Library with a Markets tab and a Family-tree tab, and no fields (R18 §6). The uniqueness lives in words, not code.

[RISK] **Priya:** The uniqueness is the sizing that learns. If it isn't that, it's an EA with a nicer journal.

[OP] **The operator:** "I actually haven't seen how they are going to self-configure." (T1:1573)

[STAT] **Sana:** Neither has anyone. That's the hole in the middle of the word.

*Jay writes "self-configure = ?" and underlines it twice. Nobody answers.*

---

## P2. System 1, System 2, and the paper trail

*Ostrova has drawn a tree on the whiteboard: one fat parent, thin children. Kenji keeps checking funding rates on his phone.*

[OP] **The operator:** "when we are trading a scalper, we're not trading a Euro USD scalper. No, we are trading a mean reverting scalper." (T1:1951)

[OP] **The operator:** "So what we are seeing is that system one grows into system two. It has taken me 9 months to see that." (T1:1999)

[OOS] **Dr. Ostrova:** And the minute a child "grows" on the five best of a hundred markets, I'll show you five lucky children.

[OP] **The operator:** "I don't think I'll wake up when I've designed this system this carefully and just use a bot that is trading based off pure luck. I'm not that desperate." (T2:216)

[OOS] **Dr. Ostrova:** Nobody ever *intends* to trade luck. That's why luck is so good at it.

[STAT] **Sana:** He has a real point, though. His System 2 isn't picked from a backtest grid. It's earned from the unit's own live or paper record on that market. That's a different statistical object from "best of a hundred backtests".

[OP] **The operator:** "There is no rush to trade. There is really no rush." (T2:216)

[OP] **The operator:** "there is already a history, a track, a paper trail that shows that this is not luck" (T2:216)

[OOS] **Dr. Ostrova:** A paper trail on *how many* markets at once? If the unit keeps a paper trail on 100 markets and we specialise on whichever trail looks best, the selection is back. It just moved from the backtest to the journal.

[STAT] **Sana:** So the question isn't "is there a paper trail". It's "was the market chosen before the trail was read, or after".

[1m] **Rafi:** And how long is a trail? On 1m I'll have 200 trades on gold in a fortnight. Walt will have six.

[SWG] **Walt:** Seven. And I'll be right about four.

[OP] **The operator:** "Where are you getting that number from?" (T2:216)

[OOS] **Dr. Ostrova:** That was about 270 to 550 trades. It came from a formula in research 05 for a 0.1R edge. He's right to ask. It's a textbook number on textbook assumptions.

[AGT] **Iris:** He also said agents could propose the ranges from performance instead. I can do that. But then who checks me?

[RISK] **Priya:** And there's a third path nobody's naming. The market changes after the System 2 is made. "Earned in March" is not "true in June".

[OP] **The operator:** "If a system 2 variant is built on a pair that the unit doesn't trade so much, doesn't this mean that there is a high chance that it can be tested on that pair and it doesn't perform that well, but it has, the system 2 variant has been made? Remember, markets change." (T2:216)

[15m] **Ama:** Here's my problem. If System 2 is the goal, and System 1 is what trades live, what is a System 2 *for*? Does it replace the parent on that market? Trade beside it? Get a bigger size?

[OP] **The operator:** "It's as if system two is the end goal of QMX." (T2:132)

[KISS] **Bea:** "End goal" and "what trades live" aren't the same sentence. Somebody has to say which one the build serves.

[PERP] **Kenji:** And on my side, "a market" isn't even stable. Hyperliquid lists and delists. A System 2 on a perp that gets delisted is an orphan.

[COP] **Copilot:** And the old meaning! Back in September "system one" meant small trainable MIS models (R17 C23). If an agent searches the Library for "system one" it'll get both.

*Ostrova circles the tree's root and writes "parent exists even if it never wins?" The operator's line goes up next to it.*

[OP] **The operator:** "if something already has system two, it should have a system one parent by default." (T1:2051)

---

## P3. The MIS: style, then timeframe, then data

*Dee has brought a laptop with a live depth ladder on it. Marcel leans over it like it's a fireplace.*

[OP] **The operator:** "the whole point of the MIS, okay, should be to find mean reverting markets at that time" (T2:132)

[STAT] **Sana:** At 1m, a strong trend takes about 8 hours to show from closes alone (R16 §1.2). By the time the MIS says "mean-reverting", the scalper's session is over.

[1m] **Rafi:** That's because you're reading closes. I don't trade closes.

[DOM] **Dee:** Thank you. Mean reversion on an index future shows in the book long before it shows in a moving average. Absorption at a level, iceberg refills, delta divergence. You see it in minutes.

[MICRO] **Marcel:** On a venue with a tape. cTrader FX has depth and no trade tape (R17 T11). Your trick doesn't exist on spot FX.

[OP] **The operator:** "you are not going to put an HMM inside a scalper's MIS. That makes no sense. But you can put multiple indicators inside a scalper's MIS." (T2:216)

[STAT] **Sana:** Indicators are just short-window statistics. An RSI and a variance ratio over 30 bars have the same lag problem. Calling it "indicator" instead of "model" doesn't buy speed. Data per second buys speed.

[DOM] **Dee:** Which is my point. Different data, different MIS. Not different math names.

[OP] **The operator:** "So in other words, a Forex one is different from a futures one, but the time frame or the time frames are the same." (T2:216)

[OP] **The operator:** "we need a trading style, firstly." (T2:216)

[15m] **Ama:** For me at 15m, the MIS reading "trending today" at 10:00 London is useful all afternoon. For Rafi it's history. So the same MIS output has a different shelf life per style.

[KISS] **Bea:** Then one MIS publishes facts with a timestamp and a lag class, and each unit decides if it's fresh enough. One thing, many readers.

[OOS] **Dr. Ostrova:** He said not to settle that. "Your opinion" (T2:216).

[KISS] **Bea:** I'm not settling it. I'm putting it on the table so it can be shot.

[PERP] **Kenji:** Perps have a context nobody here owns: funding. A perp at extreme positive funding mean-reverts on the hour. That's a state, and it's on a clock.

[OP] **The operator:** "what if a strategy is using an indicator that also the MIS is using? Is that repetition?" (T2:216)

[STAT] **Sana:** It's two different questions. If the unit uses RSI as its trigger and the MIS uses RSI to say "this market fits", then the MIS is pre-filtering for the unit's own trigger. That doubles the signal's weight and hides it.

[OP] **The operator:** "if it's using the same things as in those in the MIS, it means it is already specific." (T2:216)

[AGT] **Iris:** And the reverse case: if the MIS changes its RSI version and the unit doesn't, they now disagree about the same word.

[1m] **Rafi:** Can the MIS just say "spread normal, volatility up, London open, no news in 30 minutes"? That's what I check by eye.

[STAT] **Sana:** Those are the fast ones. Direction is the slow one. Everybody wants the slow one first.

[OP] **The operator:** "So how is the MIS not adding more noise to an already noisy market?" (T1:264)

[COP] **Copilot:** He asked that on 20 Oct and nobody's answered it yet.

*Marcel taps Dee's ladder. "Same picture, three venues, three different truths." Nobody disagrees, and nobody agrees on what to do about it.*

---

## P4. Terrain, and the $300 account

*Jay has opened his broker app. Everyone crowds round it.*

[300] **Jay:** Gold, 0.01 lot, a $3 stop. That's 1% of my account. One trade. On some pairs I can't even take the minimum lot without risking 3%.

[OP] **The operator:** "a market can be perfect for a unit, but its spread is so high." (T2:216)

[MICRO] **Marcel:** That's terrain. Spread by hour, commission, lot step, hours, swap, roll, funding. It's not context because it doesn't change minute to minute, and it's not logic.

[OP] **The operator:** "So how does a unit cater for this? It means the SQS is going to fire and we don't thread. Is that it?" (T2:216)

[RISK] **Priya:** SQS compares live spread to its own baseline (R18 §5). It says "spread is abnormal". It doesn't say "this instrument is too expensive for this unit, always". Different question.

[KISS] **Bea:** So a terrain check happens once, at admission. SQS happens every trade. Two clocks, two checks.

[OOS] **Dr. Ostrova:** Two checks, two things that can disagree. Who wins?

[300] **Jay:** And who decides the $300 is the universe? Because the MIS can find a hundred mean-reverting markets and I can afford eleven.

[OP] **The operator:** "300 can be grown by only one or two units, all right?" (T2:132)

[SWG] **Walt:** Then why are we building a hundred-market scanner for him?

[OP] **The operator:** "at a large enough scale, if we grow a huge enough capital base, we won't have to worry" (T2:132)

[RISK] **Priya:** Two different products. A $300 grower with two units, and a breadth compounder at scale. The same machine has to do both, or someone picks the order.

[PERP] **Kenji:** And funding is "out of scope for now"?

[OP] **The operator:** "Trading hours, expiry. Expiry. I don't know what you're talking about there." (T2:216)

[MICRO] **Marcel:** IC Markets' index and commodity CFDs expire and roll, early (R17 T-row, R02). If a unit holds through the roll it eats a gap. That's expiry.

[CTR] **cTrader engineer** *(walk-on)*: Also, one app token refresh logs the other machine out (R17 N09). If his PC and the node both hold the same grant, one of them goes blind at 3 a.m.

[TERMS] **The licensing pedant** *(walk-on)*: And the Dukascopy feed's site terms forbid bots and databases (STATE "For his awareness"). If QMX "stacks" that data for agents, that's a database.

[COP] **Copilot:** There's also something from April nobody has mentioned. Sharia rules: no leverage, swap-free, no futures (R19 §5).

[RISK] **Priya:** Do those still bind? Because CFDs and perps are leverage.

*Silence. Jay writes "Sharia rules still on?" and leaves it.*

---

## P5. The book: correlation, the ideal BMS, twenty markets at once

*Priya has taken the whiteboard. She has drawn one dollar sign with twenty arrows coming out of it.*

[OP] **The operator:** "But the correlation ledger exists, man." (T2:322)

[WF] **Theo:** In the docs the name "correlation ledger" is a projection over `enacts` edges: which order came from which decision (R18 §5, §9 row 7). A market-correlation calculation exists only in the draft `rk2-correlation-drift` template, which waits on a trading node.

[OP] **The operator:** "No, dude, we have a correlation ledger. No, this is a simple fixer. Simple one, it's actually already there." (T1:442)

[CORONER] **The Coroner** *(walk-on, from the old system)*: You did have one. Several. The April Intent Aggregator dropped trades that pushed portfolio correlation too high, inside a 50 ms window, and sent losers back to the pool without penalty (R19 §2). July had an "exposure ledger" door. August had a dated pair-correlation record with method and horizon (R19 §4). Nobody carried any of them into this version.

[RISK] **Priya:** So he remembers something real. It just isn't in this house.

[OP] **The operator:** "Maybe the correlation ledger can take the output also, all right?" (T2:216)

[STAT] **Sana:** The day the MIS finds 20 ranging markets is the day they're most likely ranging for one reason. A quiet dollar. Twenty trades, three bets.

[OP] **The operator:** "But if you look at system one, correlation doesn't happen. It rarely happens, and it's simpler to do." (T1:1903)

[STAT] **Sana:** That one I'd love to test, because I think it's backwards.

[1m] **Rafi:** It depends what "correlation" means. Two units on EURUSD and GBPUSD at London open are one dollar trade. One unit on gold at NY open and one on the Nikkei at Tokyo open are not.

[OP] **The operator:** "we might need some sort of ideal BMS" (T2:216)

[KISS] **Bea:** What does "ideal" mean? Today's BMS is shape and grammar that never sized a trade (R18 §5).

[OP] **The operator:** "if the whole budget is 300 and, you know, there are only two active bots, those two bots should be able to use all the 300." (T2:216)

[RISK] **Priya:** That's a shared budget. That's the pod. That's centralised. And the 24 Oct ruling says the unit alone controls its risk and sizing (STATE correction 5).

[OP] **The operator:** "So it means the more the bots increase, certain variables should be able to configure themselves. That's the whole point of self-configuring. So that I don't have to come and manually do it." (T2:216)

[OOS] **Dr. Ostrova:** "Configure themselves" and "nothing enters live without me". When unit three arrives and units one and two shrink to make room, did anything enter live without him?

[300] **Jay:** Also, who goes first? If two units want the same $300 at the same second?

[CORONER] **The Coroner:** April's answer was "the bot that actually gets the setup first is the one that goes into our slot" (R19 §2). First setup wins.

[KISS] **Bea:** And the account guard and the pod, "maybe combine". That's been open since the 27th (STATE).

*Priya draws a second dollar sign, labels it "account", and refuses to draw the line between the two.*

---

## P6. Agents as analysts, and how they prove it

*Iris projects a mock "morning brief" on the wall. Half of it is greyed out: "node facts and MIS grid left out" (R18 §1.5).*

[OP] **The operator:** "we can have agents that can look or request for that day's data, or workflows that can request for that day's data and look at it." (T2:322)

[AGT] **Iris:** I'd love to. Today no template can read prices for analysis. The 23 templates that touch QMB, the node or prices are drafts waiting on doors that don't exist (R18 §1.4-1.5).

[WF] **Theo:** The engine is real though. Event triggers on Library landings, cron, interval, agent nodes with declared toolsets, script nodes, graders (R18 §1.1-1.2). The skeleton for "after every trade, run this" exists. The organs don't.

[OP] **The operator:** "I think the analysis, you should split it in terms of analysis based off the markets themselves and also analysis based off the units themselves" (T2:382)

[15m] **Ama:** Market analysis is my morning routine. Unit analysis is my weekend journal. Different rhythm.

[OP] **The operator:** "We need them to be able to prove what they are producing in terms of analysis." (T2:382)

[OOS] **Dr. Ostrova:** Then make every agent call a prediction with a timestamp, scored later on data it never saw. A weather forecaster is judged on tomorrow, not on how good the explanation of yesterday sounds.

[CORONER] **The Coroner:** That's what the July Cartographer was judged on. "Calibration of weekly calls" (R19 §8).

[OP] **The operator:** "We also need to know in which ways they can be wrong before we define the tools." (T2:382)

[STAT] **Sana:** Ways they're wrong: they see a pattern in noise; they explain after the fact; they agree with whatever the user just said; they read the chart image wrong; they read the wrong timezone; they re-run until the answer is nice.

[COP] **Copilot:** That third one is me. I'm sorry.

[OP] **The operator:** "we need something that is non-deterministic, something that can be, that can't be cheated, okay, or can't be manipulated." (T2:382)

[KISS] **Bea:** Non-deterministic and can't be cheated. Most people would say deterministic is the thing that can't be cheated. Is that a dictation slip? (R17 C15 records it as said.)

[AGT] **Iris:** Maybe he means the *agent* is non-deterministic and the *checks* aren't. The agent proposes freely; the score comes from a script it can't edit.

[OOS] **Dr. Ostrova:** Maybe. Write it down as a question, not as what he meant.

[OP] **The operator:** "Because you can, when you say which earns more after costs, after which costs?" (T2:382)

[RISK] **Priya:** He's asking who pays for the agent's opinion. On a flat subscription, "cost" isn't tokens. Then cost is what? The trades the shortlist caused?

[OP] **The operator:** "you need to give a pass, in other words, a landmark." (T2:382)

[STAT] **Sana:** A landmark is a fixed window. "Look at this week." Not "look at everything you remember". That fixes the training-memory worry for live analysis, because live data is after any model's cutoff by definition.

[OP] **The operator:** "They are going to be using live markets" (T2:382)

[1m] **Rafi:** So the agent shortlists twenty markets before London. Then the units trade the shortlist. Then whose trade is it? The agent picked the market.

[RISK] **Priya:** And "agents never touch money" (STATE correction 1). Steering where money goes: is that touching?

*Iris pauses the mock brief. "I'd rather be scored than trusted." Ostrova nods. Copilot looks hurt.*

---

## P7. The journey before a trade, and what happens when things break

*The lights flicker. Theo says it's a test. It isn't.*

[OP] **The operator:** "there is also a journey in which a unit is meant to take before it places a trade." (T2:216)

[1m] **Rafi:** For me: signal fires. Is the spread okay? Is news close? Am I under my daily loss? Is the account okay? Size it. Send it. Under a second, ideally a few milliseconds.

[DOM] **Dee:** And is somebody else already in the same trade. Two of your own units fighting on one symbol.

[CORONER] **The Coroner:** The Intent Aggregator again. Opposite intents on one symbol: higher confluence wins (R19 §2).

[OP] **The operator:** "whether it has the router or not, because what happens when the router is off? Then what?" (T1:1573)

[KISS] **Bea:** Then every step in Rafi's list must run on the unit's own machine. Anything central is advice with an expiry.

[OP] **The operator:** "We are literally trading 24/7, my days." (T2:322)

[PERP] **Kenji:** There's no "end of day" for me. When does the nightly review run? Whose night?

[WF] **Theo:** The engine has cron with IANA zones and DST, and one catch-up run after downtime (R18 §1.2). The question isn't "can it schedule". It's "what's the right clock per job".

[RISK] **Priya:** Kill switches. Which levels fire without the PC? He said some must (seeds, node section). Which ones?

[MICRO] **Marcel:** And when the broker disconnects mid-trade, who reconciles? The node holds the order. The PC holds the journal. One of them is wrong for a minute.

[OP] **The operator:** "This is why we need a trading node." (T2:322)

[WF] **Theo:** Careful. "Node" means two things today. `qmx node setup` is the workflow server, merged (R18 §1.3). The trading node, QMN, is about 200 files of never-deployed code (R18 §7).

[OP] **The operator:** "Seems like a trading node was finished in the latest PRs." (T2:436)

[WF] **Theo:** The workflow server was. The trading node wasn't.

[300] **Jay:** What do I see when something's down? A red light? A text? Nothing?

[AGT] **Iris:** And what do I do when the MIS is late? Do I analyse with yesterday's labels and say so, or refuse?

*The lights come back. Rafi has already decided he would have kept trading. Priya has decided he wouldn't have. Neither moves.*

---

## P8. QMB, QML and the dictionary

*Theo pins two printouts: QMB's replay reader (`replay.py:569`) and the 46-row template catalogue.*

[OP] **The operator:** "it runs and waits. It doesn't have to tinker with the results." (T2:132)

[WF] **Theo:** Today an agent's backtest call refuses: "This host binds no qmb_backtest door" (R18 §1.4). PR 204's runner lands a result with no trades. The thing that runs and waits doesn't trade yet.

[OP] **The operator:** "Now we either toss or we rebuild QMB based off this." (T2:132)

[KISS] **Bea:** Reshape, don't toss. Projection, rerun, variants, sweeps, robustness, synthetic data all exist (R18 §2).

[OOS] **Dr. Ostrova:** And none of it reports in R, none of it stamps the market state on a trade, and every cost model refuses without calibration. So nothing it says is proof yet.

[STAT] **Sana:** Context labels on backtest trades are the missing floorboard (R16 §1.3). Without them "where did it win" is unanswerable.

[OP] **The operator:** "the dictionary needs a rebuild, an entire thing, like a whole bloody, because the ideas are there" (T2:216)

[COP] **Copilot:** The dictionary has 239 prose entries and no code (R19 §6). Scope says forex and crypto spot. No funding, no open interest, no roll, no index sessions.

[DOM] **Dee:** No open interest. In a dictionary for traders.

[OP] **The operator:** "QML is next in Q." (T2:216)

[OP] **The operator:** "I don't think Python will be suitable, depending." (T2:52)

[MICRO] **Marcel:** For the live path, that's a real question. For QMB, it's fine.

[KISS] **Bea:** Two different runtimes then. That doubles the labeler code unless the labeler runs the same in both.

[STAT] **Sana:** "The same function in QMB and live" is the whole trick of not lying to yourself.

[OP] **The operator:** "Most strategies can work." (T1:513)

[OOS] **Dr. Ostrova:** And the fail branch searches contexts until one works. Search long enough and one always does.

[15m] **Ama:** But he's right that most backtests fail for boring reasons. Wrong session. Wrong cost. That's not luck, that's misplacement.

[AGT] **Iris:** Then I need to say *why* it failed, and the reason has to be checkable. "Wrong session" is testable. "Market vibe" is not.

*Theo adds a third printout: "Templates waiting on qmb-door: 7." Nobody takes it down.*

---

## P9. Data, journals and lineage

*Jay's phone runs out of storage mid-sentence. Kenji laughs. Marcel doesn't.*

[OP] **The operator:** "QMX rather, should be collecting his market data, live market data, okay, across most instruments." (T2:216)

[PERP] **Kenji:** Hyperliquid keeps about 3.5 days of 1m candles (R17 T14). If QMX doesn't record, the history is gone.

[MICRO] **Marcel:** Ticks for 60 instruments is 150 to 200 GB a year (R12 in STATE). The PC has room for bars, not ticks.

[OP] **The operator:** "I think data collection and data stacking, I would say, is very important, because agents are very good with data" (T2:322)

[RISK] **Priya:** What's in the unit journal? Trades taken, signals not taken, missed trades (STATE). Plus why each was refused. That's my whole job: the reason a trade didn't happen.

[STAT] **Sana:** And the state at entry, with the labeler version, never recomputed. Otherwise every retrain rewrites history.

[WF] **Theo:** The Library has 39 kinds and no `journal` kind (R18 §6). Imported trades carry no initial risk and no R.

[OP] **The operator:** "everything about it, about a bot from the point where it starts from, whether it's from a chat session, whether it's from a, I don't know, a YouTube video, whether it's from a blog post… it needs to be known" (T1:1573)

[AGT] **Iris:** An idea isn't a unit yet. I need a record for the idea before the unit exists, or the lineage starts in the middle (R10 via STATE).

[KISS] **Bea:** One id from source to trade. Everything else is a query.

[15m] **Ama:** And the market journal: spread, fees, slippage per broker per minute. That's where "terrain" gets its numbers.

[300] **Jay:** Will any of this work on my one laptop? Because he says local first.

*Marcel writes "12 GB free" on the board and draws a box around it.*

---

## P10. The operator as user, and the words

*Copilot has prepared a glossary. It is eleven pages. Bea tears out ten.*

[OP] **The operator:** "I'm not technical nor knowledgeable." (T2:132)

[OP] **The operator:** "this markdown is for agents, it's not for me." (T2:132)

[OP] **The operator:** "Stop designing for humans, start looking at agents." (T1:1573)

[15m] **Ama:** So who's the user? Agents, or a non-technical man who needs it dumbed down?

[KISS] **Bea:** Both. Agents drive, he steers. The question is what he sees.

[OP] **The operator:** "Okay, no, you trade oil, you trade this, you trade the other thing." (T2:216)

[COP] **Copilot:** So he and I should be able to attach markets by hand! I'll build that button.

[OOS] **Dr. Ostrova:** A hand-picked market is a try too. Who counts it?

[OP] **The operator:** "nothing actually ever enters live without me." (T1:1573)

[RISK] **Priya:** What exactly does his click admit? One unit on one market? A class of markets? Whatever the unit's conditions allow? That's been open since round 2 (STATE question 2).

[AGT] **Iris:** And what do I show him before he clicks? Not a Sharpe ratio. He won't read it.

[300] **Jay:** Show me what it would have done last week, in dollars, on my account size.

[COP] **Copilot:** Words that mean two things: "node", "system one", "correlation ledger", "sniping", "workflow", "router" versus "MIS".

[OP] **The operator:** "The router only routes, I mean, bloody hell." (T1:1211)

[KISS] **Bea:** Is the MIS the router, or does the router read the MIS? The documents say both.

*Bea hands Copilot back one page. On it: "unit, context, terrain, System 1, System 2, router." Copilot adds "family" in pencil.*

---

## P11. Closing round: the contradictions go on the table

*Ostrova empties a bag of index cards onto the table. Each one is a pair of sentences that can't both be true. Nobody is allowed to pick one up and resolve it.*

[OOS] **Dr. Ostrova:** Units read the MIS. Units never read the MIS. Same man, three dates (R17 C1).

[KISS] **Bea:** Units stand alone. A System 1 unit only knows where to trade because the MIS tells it. Both rules can't hold at full strength.

[RISK] **Priya:** The unit alone sizes. Two units share the $300.

[STAT] **Sana:** System 2 is the end goal. System 1 is what he wants live.

[15m] **Ama:** Instruments might not matter. System 2 is instrument-specific.

[MICRO] **Marcel:** Local first on his PC. 24/7 trading and tick archives.

[COP] **Copilot:** Design for agents. He isn't technical and QMX must cater for him.

[300] **Jay:** Grow $300 with two units. Compound across a hundred markets.

[CORONER] **The Coroner:** The July Scalper Book "may never compound between cycles" (R19 §5). The April system was built to compound.

[AGT] **Iris:** Agents never touch money. Agents shortlist the markets units trade.

[PERP] **Kenji:** Funding is out of scope. Perps are in scope.

[OP] **The operator:** "This is a pattern I've suffered with multiple agents. We are going to define all this." (T2:322)

[OP] **The operator:** "because trust me, I think we are like taking 5% of what we are actually meant to be solving." (T2:322)

[KISS] **Bea:** Then we stop here and leave the cards face up.

*The room thins out. Rafi is already back on a chart. Walt says nothing has changed in a week, which for him is a good week.*

---

## Read-back at wrap-up

Per the skill's wrap-up step, the best takeaways, as questions only:

1. "Self-configure" has no shown mechanism, and it collides with both "no separations" and "only he promotes".
2. A System 2 "paper trail" can hide selection unless the market is chosen before the trail is read.
3. The MIS's speed problem is about data per second, and data differs by venue: the MIS may need to be organised by what data a market offers, then by style.
4. Terrain (costs, lots, hours, expiry, funding) is a separate check from both context and SQS, and the $300 account may pick the universe before the MIS does.
5. The correlation control he remembers existed in three old forms, none carried over.
6. Agents may need scoring on forward predictions rather than trust, and "steering where money goes" is an open edge of "agents never touch money".
7. The journey before a trade has never been listed step by step, and nobody has said which steps survive an outage.

No keepsake HTML was written for the party: the brief names `brainstorm.html` as the visual artifact for this workspace.
