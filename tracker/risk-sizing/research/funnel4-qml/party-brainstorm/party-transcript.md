# Party mode transcript: QML and the strategy dictionary

Run 2026-10-30 by the QML expansion agent. Skill: `bmad-party-mode`, **session mode** (one mind voices every persona, no subagents), run as an explicit non-interactive party on the brief's intent until a natural close. Activation scripts ran: `resolve_customization.py` (`party_mode = session`), `resolve_config.py` (user Mubarak, English), `resolve_party.py` (`installed_agents_resolved: false`, so the inline cast below is the roster). Per `references/party-memory.md`, an ad-hoc inline cast keeps no memlog, so this transcript is the party's only record. Speaker tags are text, not emoji (project rule).

**Voices with limits.**
- **The operator** speaks only in verbatim quotes, each tagged `(T1:n)` or `(T2:n)`: `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md`, line n holding the whole turn. Every quote was checked by script against those lines (`qmlfield/quotecheck.py` in the run's scratchpad; result in `qml-field.md` §7).
- **Sol**, the GPT model (gpt-5.6-sol) that built the dictionary design in August, speaks only from research 39's record of it. Its lines restate or quote R39's ledger, with the R39 row id in brackets (for example `[R39 C1, FG 831]`). It invents nothing new; when the room asks it something the record does not hold, it says so.
- **Viktor**, the MQL5 author, speaks from research 36's 36-article assembly sample and its article ids.

**Nothing here is a decision.** Clashes stay open. Ideas and questions surfaced here carry their round tag (P1 to P12) into `qml-field.md`.

Seed shorthand used by the personas: R20, R21, R34, R35, R36, R39, R40, R41 = `research/<n>-*.md`; PF = `research/funnel3/party-brainstorm/playing-field.md`; GL = `research/funnel3/cis/glossary-draft.md`; K1 to K20 = research 35 §6 "things any trader knows".

## The room

| Tag | Name | Who |
| --- | --- | --- |
| [SOL] | Sol | The GPT model that built the August dictionary design. Voiced only from R39. Formal, fond of lists, proud of the three layers. |
| [1M] | Rafi | 1-minute FX and gold scalper on cTrader. Counts in pips and seconds. Hates anything that lags. |
| [DOM] | Dee | Index-futures order-flow trader (ES, NQ). Footprint, delta, DOM. Scornful of lagging indicators. |
| [PERP] | Kenji | Crypto perps trader on Hyperliquid. Funding, open interest, liquidation maps. Never sleeps on a weekend. |
| [ORB] | Ama | Intraday opening-range and session trader. London and New York opens. Patient, precise about clocks. |
| [MQL] | Viktor | MQL5 strategy author. Writes EAs with fixed inputs and lets the tester pick them. Knows the Wizard. |
| [OOS] | Dr. Ostrova | Quant obsessed with overfitting. Counts every try. |
| [SQX] | Lena | StrategyQuant X power user. Genetic builder, building blocks, exit-type weights. Generates thousands of strategies a night. |
| [BLD] | Pip | A QMX building agent: a cheap model turning a YouTube transcript into a unit through QML. Literal, eager, easily confused. |
| [ANL] | Iris | A QMX analyst agent. Reads journals and markets. Wants every claim to be checkable. |
| [DEEP] | Hal | Deep-modules software designer. Small doors, big rooms. Counts what the caller must know. |
| [ONTO] | Noor | Vocabulary and ontology designer. Names, aliases, relations, versions. |
| [SKEP] | Morrow | The skeptic. Thinks the whole dictionary may be a museum. |
| [OP] | The operator | Only his own words. |

---

## P1. What is a bot, from first principles?

**[OP]:** "When you go back to first principles, what is a trading bot? It's just a set of rules. In programming, it's if-else statements. That's it." (T2:779)

**[OP]:** "So how do we make sure that those if-else statements can self-tune? Maybe that's the question at hand, in my opinion." (T2:779)

**[MQL]:** He's right, and I can show you the skeleton. New bar? Compute indicators. Position open? Skip. Condition true? Send order with SL and TP. Then trail on every tick. That's 15311, 16573, 23341. Four hundred and seventy-three articles say "new bar". It's if-else all the way down.

**[1M]:** And every one of those ifs has a number in it written in points. "Stop 40." Forty what? Forty on EURUSD at 3 a.m. is a different animal from forty on gold at the New York open.

**[MQL]:** Points in 84 articles, ATR in 9. Yes. We write a number and the optimiser fixes it.

**[DEEP]:** Then let's be precise about what an "if" is made of, because "self-tune" means nothing until we name the moving part. I count five things inside one if: what you read, what you compare it to, how much, when the comparison is allowed to count, and what you do.

**[ONTO]:** Reading, comparison, threshold, gate, action. Write them down. Those are the atoms.

**[OP]:** "The part that tunes itself actually is part two, under question number one. It's numbers." (T2:779)

**[OOS]:** Good. Numbers. So the threshold atom and the reading's settings. Not the comparison. Not the action. The moment the comparison or the action changes, I want a new version and a counted try.

**[SQX]:** Oh, come on. My builder changes the comparison every night. "ADX rising" becomes "ADX above 25". That's how you find strategies.

**[OOS]:** That's how you find noise, Lena. With a receipt.

**[SKEP]:** Before you two start: is "self-tune" even one thing? Research 20 found three meanings. Recompute size from a balance. Update a statistic from finished trades. Change the policy. Shipped platforms do the first two. Nobody does the third without a human.

**[ANL]:** And he wants to know which one he's getting: "If it can self-tune, I don't have to tune it myself, right? But it does beg the question, how does it do it and what is it actually tuning?" (T2:779)

**[BLD]:** Can I ask something stupid? If the number tunes itself, what number do I write when I build it?

**[1M]:** That's not stupid. That's the whole question.

*Surfaced:* the five atoms of a rule; numbers vs structure as the tuning line; three meanings of self-configuration; what the builder writes on day one.

---

## P2. Numbers that travel

**[1M]:** Here's what a scalper knows. A stop in pips doesn't travel. A stop in ATR multiples does. Chandelier, 22 periods, three ATR. That's not new.

**[OOS]:** It's K15 in research 35. Taken as given. Volatility-scaled distances are how one setting travels across instruments and regimes. Don't ask it as a question again.

**[DEEP]:** Then the question isn't whether. It's whether QML makes the travelling form the default form an agent writes. If the builder writes "40 pips", QML could say: that's one instrument's rule.

**[ORB]:** Careful. Some numbers are clocks, not distances. The London open is 08:00 London. The opening range is the first 15 minutes. That doesn't scale with volatility. It moves with daylight saving.

**[MQL]:** And with broker server time. Every session rule in MQL5 is written in server time. A hundred and fifteen articles fight GMT offsets.

**[ONTO]:** So numbers have kinds. Distance, count, clock, ratio, probability. Each kind has its own travelling form. Distance travels in ATR or percentiles. Clock travels in exchange time with a calendar. Count travels as... bars? Seconds?

**[DOM]:** Count travels badly on time bars. Use volume bars or tick bars and "10 bars" means ten chunks of real trading, not ten minutes of nothing at lunch.

**[1M]:** You'd make me trade Renko? No.

**[DOM]:** I'd make you say which bars you mean.

**[SQX]:** Percentile thresholds. "RSI below its own 10th percentile over the last 60 days." That tunes itself per instrument and per regime with no optimiser at all.

**[OOS]:** It also hides a lookback. Sixty days is a number. You just moved the try.

**[SQX]:** Everything is a number to you.

**[OOS]:** Everything is.

**[ANL]:** Then let me add a field. Every number says how it moves: fixed, scaled by a live statistic, refit on a window, chosen per measured state, learned. Research 36 saw all five in the corpus. The dictionary has no slot for any of them.

**[SOL]:** The record shows the August design labelled where a value came from: `source-stated`, `published-convention`, `STRATS-standardized`, `inferred`, `unresolved`. It did not label how a value moves. [R39 C12; SC]

**[DEEP]:** Origin and motion. Two labels on one number. Cheap to hold, and an agent can't misread them.

*Surfaced:* number kinds (distance, count, clock, ratio, probability) with travelling forms; percentile thresholds and their hidden lookback; motion label beside origin label; bar construction as part of the binding; broker server time.

---

## P3. The tuning ladder, and where structure starts

**[MQL]:** I'll give you the ladder from the corpus, bottom to top. Fixed inputs and the tester picks them: 2626, 1924. Re-optimise on a schedule live: 1467, 7718. Numbers relative to a live statistic: 16573, two ATR stop, three ATR target. Refit a model every bar: 19013. Branch by measured state: 17781, trending stop 100, ranging stop 50, volatile stop 150, with a smoothing period for transitions. Quality-gated switching: 18916. Own record drives size: 24147, Kelly. Learned policy: 21314, the RL agent with a promotion gate.

**[SKEP]:** Eight rungs. And the higher you climb, the less anyone can tell you why it made money.

**[OOS]:** Rung three is safe. Rung one is safe if you count tries. Rung five is where people lie to themselves. The detector lags, flips at the worst moment, and the backtest fitted it on all the data.

**[SOL]:** The August experiment design held a rule on this: "Regime labels must be available at evaluation time or fitted only on training data." [R39 I8, EXP §6]

**[ANL]:** No file had carried that rule until research 39 found it. It's a look-ahead rule for context. It belongs on every label.

**[SQX]:** And rung five is exactly his question. "If trending, do this, else do that." That is an if-else that self-tunes. The state picks the branch.

**[DEEP]:** Then a regime detector is just another reading feeding a gate. No new machinery. The branch is part of the logic, both branches get tested, and the state reading is a primitive with a version.

**[OOS]:** Both branches and the no-switch baseline. If the switch doesn't beat "always branch A", it's decoration.

**[SOL]:** The record also holds the opposite stance: "Pair, session and regime are challenge coordinates, not tunable strategy factors." [R39 I9, EXP §3]

**[ORB]:** That's a museum rule. My session profile is my strategy. I don't trade London the way I trade New York.

**[OOS]:** And the minute you tune per session you've got two strategies and half the trades each.

**[ORB]:** Then count them. Don't forbid them.

**[OP]:** "Then exits become a variant access. Yes, exits become variant, entry become variant." (T1:1177)

**[SKEP]:** Variant axis. So structure changes are variants. Fine. Where's the line between a number and a branch when the number is "which of three exits"?

**[SQX]:** In SQX it's a weighted probability. "How big probability is to use given exit method." The genetic search picks exits as structure.

**[OOS]:** And research 35 calls that the riskiest search there is.

*Left open:* whether a state-chosen branch is one unit or two; whether per-session sets are tuning or variants; whether "which exit" is a number or a structure. Exit maths itself stays with the risk-and-sizing session.

---

## P4. Why there is a dictionary at all

**[OP]:** "the idea was you get what multiple traders would use from languages. That's why it's called a dictionary, yeah? From languages, terminologies, stuff like that." (T2:779)

**[OP]:** "You combine everything so that if someone from a source mentions anything, we already know what it is, okay? Or if it's new, we can append it. In other words, the agents working in the workflows that are building the units are not confused." (T2:779)

**[BLD]:** That's me. I'm the one who gets confused. Yesterday a man on YouTube said "wait for the sweep, then the displacement, then enter on the pullback into the gap." I found `liquidity-sweep`. I found `fair-value-gap`. I did not find "displacement" as its own entry, so I wrote eleven lines of Python.

**[ONTO]:** And now you have a private word nobody else can find. That's the failure he named.

**[OP]:** "Because if you, again, have an issue whereby you don't have something in QML that caters for this, you'll have QML again having its appendix having new things, however, without it improving in any way, shape, or form." (T2:779)

**[SOL]:** The record's core move was this: "The biggest ontology improvement: primitives and roles must be separate." Bullish engulfing, RSI and order flow, each shown in four roles. [R39 C1, FG 831]

**[SOL]:** And three layers. "Primitive dictionary 'What things exist?' / Role bindings 'What job does this primitive perform here?' / Strategy logic graph 'How are the bound components combined?'" [R39 C2, FG 831]

**[OP]:** "the dictionary was GPT's idea, not mine. I never said it's unique." (T1:1211)

**[SKEP]:** There it is. The model at the table built it, and the man who owns it says it wasn't his idea. Why are we treating it like scripture?

**[SOL]:** The record does not say it is scripture. It records his reply on 26 Aug: "logic graph wasn't my idea. I agreed with it." [R39 GM 3262]

**[ONTO]:** Morrow, separate the shape from the job. The job is his: one vocabulary so cheap agents don't invent words. The shape is GPT's: three layers, role-neutral entries, twelve prose fields. The job is fixed. The shape is a seed.

**[SKEP]:** And the shape came with a rule nobody should keep: "Do not create Python." Two hundred and thirty-nine entries, zero lines of code.

**[SOL]:** That instruction is in the record. The workers' contract said: "Do not create Python, YAML schemas, CLIs, Pydantic, tests... or runtime machinery." [R39 §5, SC]

**[DEEP]:** Which made sense when QMX couldn't run anything. It doesn't now. An entry with no code is a promise. A builder can't run a promise.

**[OP]:** "Again, QML is a library so that we don't just write Python, okay?" (T2:779)

**[BLD]:** So I shouldn't write Python. But the entry has no code. So I have to write Python.

**[DEEP]:** *(Hal taps the table.)* That loop is the bug. The library must hold the code so the builder doesn't.

*Surfaced:* the dictionary's job vs its August shape; an entry needs runnable code; the builder's loop (no entry, so loose Python); appends that don't improve the library.

---

## P5. The small door

**[OP]:** "we want some sort of framework or library, actually, I think library is the right word, which agents can use to build units easily, monitor them, something that is simple on the eyes, so which means it can leverage JSON schemas, simple architecture or simple thoughts, simple mental models, instead of complicating it. In the back it can be complex." (T1:1211)

**[DEEP]:** So the door. What does a caller have to know? I'd say: a list of words, a way to bind a word to a job, a way to say how they combine, and a handful of verbs. `new`, `check`, `test`, `promote`, `watch`, `find`, from the 07 funnel. Everything else is behind the door.

**[OP]:** "For me, I'm imagining this like JSON. Most of it is JSON. Because in a way, it's actually very similar to a workflow. Because these are just conditionals." (T2:779)

**[DEEP]:** A unit as a JSON document that reads like a workflow. Nodes are bound primitives. Edges are the graph operators. The QMX workflow engine already runs JSON graphs. Why not let the same idea carry the rule graph?

**[MQL]:** Because my EA's loop runs every tick in microseconds and your workflow engine runs on a scheduler.

**[DEEP]:** Same shape, different runner. The JSON says what. The runner decides how fast.

**[ANL]:** And it gives me something. If a unit is a document, I can diff two units and say "they differ by one confirmation." I can count how many units bind `liquidity-sweep`. I can't do that with Python files.

**[SKEP]:** Until someone writes Python anyway. Plain Python is always allowed. That's ruled.

**[DEEP]:** So the escape hatch is a block. A Python block with a declared input and output, sitting in the graph like any primitive. Inside, anything. Outside, the same ports, the same journal, the same tries count.

**[OOS]:** As long as the tries count follows it out the door. Most escape hatches are where tries go to hide.

**[BLD]:** Who decides whether my eleven lines become a dictionary entry?

**[ONTO]:** An append rule. A new entry needs a family, a data class it reads, and either an implementation or a stated gap. If it can't name those, it isn't a word yet.

**[SQX]:** Gatekeeping. My builder makes ten thousand of those a night.

**[ONTO]:** Your builder makes ten thousand combinations of the same four hundred blocks, Lena. That's the point. The blocks are few.

*Surfaced:* the unit as a JSON graph like a workflow; same shape, different runner; the Python block with ports; append rule; diffs and counts across units.

---

## P6. Beyond FX: what each market adds

**[OP]:** "Order flow is good for scalpers, especially now that I'm adding indices. I've forgotten to add indices, but now I'm adding indices as an instrument." (T2:132)

**[DOM]:** Then add the words. Footprint, delta, cumulative delta, absorption, initial balance, value area, POC, RTH and ETH, overnight high and low, settlement, front month, roll week. And open interest.

**[SOL]:** The record kept order-flow entries with "non-transferability" notes, separating "centralized-exchange truth (exchange volume, VWAP, depth, footprint, delta)" from broker spot-FX tick volume. [R39 L7, GM 3938]

**[DOM]:** Good. Because CFD index price is a copy of somebody else's auction. You can trade the copy. You can't read the auction from it.

**[1M]:** I read tick volume on gold every day and it works.

**[DOM]:** It works as a proxy. Call it a proxy. Then nobody tests a footprint idea on it and calls it a footprint.

**[PERP]:** My turn. Funding rate. Mark price versus index price versus last price, because my stop triggers on mark. Basis. Open interest change. Liquidation levels and cascades. Hourly funding on Hyperliquid. Leverage tiers. And nothing closes. No session, no Friday.

**[ORB]:** No session? Volume still clusters by region. Asia, London, New York. You still have a clock.

**[PERP]:** A softer one.

**[ONTO]:** Research 35 says the asset class mostly changes terrain, not logic. Sessions, costs, carry, data truth.

**[DOM]:** Mostly. Except when the class gives you a signal nobody else has. Funding and open interest aren't terrain. They're readings. They go in the dictionary.

**[PERP]:** And liquidation cascades are a trigger. A big one.

**[MQL]:** And stocks? Nobody's said stocks. Earnings dates, ex-dividend, splits, halts, pre-market, short borrow. Research 02 says stock CFDs at his broker are MT5-only.

**[SKEP]:** Gold?

**[1M]:** Gold is FX hours with a London fix, a New York open that moves it, real yields, the dollar, and a swap on longs that eats you alive if you hold.

**[SOL]:** The record's view on gold was narrow: "a gold video may add a gold note and transferable concepts but no strategy." [R39 L8, GM 2724]

**[1M]:** That's a librarian's sentence.

**[OP]:** "mean reverting for which instrument? Because I don't think mean reverting is going to be the same across all markets, unless I'm wrong." (T2:132)

**[OOS]:** He isn't wrong. The concept travels. The test of it doesn't. A variance ratio on 1m gold and on 1m ES are two different animals.

**[ANL]:** So per class, three things: terrain facts on an instrument record, class-only readings in the dictionary, and a transfer status on every entry saying how far the word travels.

*Left open:* whether funding, OI and liquidations are context, trigger or terrain; whether proxies are their own entries; which class pack comes first.

---

## P7. Data classes

**[DEEP]:** Turn it sideways. Not "which market", but "which data". Bars, quotes, depth, trades, derivatives facts, calendar, events, fundamentals, sentiment, model outputs. Ten data classes.

**[MQL]:** Add bar construction. Renko, range, tick, volume bars, Heikin-Ashi. Ninety-eight articles.

**[DOM]:** That's not a data class, it's what you do to trades.

**[ONTO]:** Then it's a dependency of the binding. "This trigger on 100-tick bars." Not a primitive.

**[1M]:** And every primitive says which data it needs at minimum. Delta needs trades with aggressor side. You don't have that on spot FX, so you can't bind it there.

**[ANL]:** And the tester should refuse rather than quietly substitute. Research 35 says bar-only tests overstate tight exits. A primitive tested on weaker data than it needs is a lie with a chart.

**[OOS]:** Add statistics. Hurst, variance ratio, ADF, autocorrelation, efficiency ratio, half-life, entropy, z-score. Zero of forty in the dictionary. Thirty-one percent of MQL5 articles use them.

**[OP]:** "when you look at MIS, I mean, the one we are using is mostly using HMM, BOCPD, MS, GARC, and I believe we had market physics and so on and so forth, yeah?" (T1:1951)

**[ANL]:** Then the MIS's own models are readings too. One catalogue. Context is a role, not a separate dictionary. Research 16 said the same.

**[SKEP]:** And evaluation words? Sharpe. Walk-forward. PBO. Six of the top ten missing concepts.

**[OOS]:** Keep them out of the strategy dictionary. A builder that binds "Sharpe" as a trigger is a builder I don't want.

**[BLD]:** I would never.

**[OOS]:** You would by Tuesday.

*Surfaced:* ten data classes; bar construction as a binding dependency; minimum data class per primitive and refusal on weaker data; statistics and MIS models as readings in one catalogue; evaluation words kept apart.

---

## P8. Market context as the trader's sense

**[OP]:** "when you are looking at a chart, a market chart, you have to have market context. In other words, price action and technical analysis. If you don't use fundamentals, you get the idea." (T2:779)

**[ORB]:** Context is three clocks in one sentence. "Daily bullish, in the London killzone, after a sweep of Asian lows." Higher-timeframe bias, a session window, then the event.

**[SOL]:** The record bound a timeframe and session to every component: "H4 level, H1 bias, M5 trigger, M1 execution, London filter, pair spread limit." And "Timeframes and pairs are coordinates, not levels." [R39 D1, D2, FG 795, FG 831]

**[ORB]:** That one I'd keep.

**[1M]:** And context is mostly computable. Trend versus range: efficiency ratio, ADX, swing count. Volatility regime: ATR percentile. Session: a clock. Key levels: PDH, PDL, VWAP, POC.

**[ANL]:** Except three things traders read by eye: the swing lookback, how good a zone is, and the Wyckoff phase. Research 35 found those as the by-eye residue.

**[DOM]:** And absorption. I see it before any number says it.

**[OOS]:** Then you're the residue, Dee.

**[DOM]:** I'm the edge.

**[OP]:** "If we already have market context, doesn't this mean that market context is simply what the MIS is doing?" (T1:1951)

**[DEEP]:** One reading, two callers. The unit binds "volatility percentile above 80" as a veto. The MIS computes the same reading for a hundred instruments to rank them. Same entry, same code. If the MIS is down, the unit computes it itself.

**[SKEP]:** And when the MIS's version is newer than the unit's?

**[ANL]:** Then the label carries a version and the trade records which version it saw.

**[OP]:** "this was one of the one of the biggest reasons we actually built the dictionary, so that we have a standardized form." (T1:1951)

**[BLD]:** The YouTube man never says "mean-reverting". He says "it always comes back to the VWAP before London lunch."

**[ONTO]:** Then your job is the translation. His sentence becomes: context = intraday mean reversion, measured how; level = session VWAP; window = before London lunch. The dictionary is what makes that translation the same every time.

*Left open:* how by-eye judgements are represented; whether context states are coarse by default; who owns the version when unit and MIS disagree.

---

## P9. A cheap model builds a unit from a video

**[BLD]:** Let me walk it. I get a 40-minute transcript. I cut it into chapters. I pull the trading claims with timestamps. I match each word to an entry. I bind roles. I fill the graph. I mark every gap. I write the unit document. QMB checks it. I write the journal entry.

**[SOL]:** The August pipeline had ten stages: "discovery → immutable inventory → deterministic extraction (metadata, subtitles, transcript, frames, OCR) → visual analysis → temporal alignment (claim ↔ subtitle ↔ frame) → atomic claims → primitive and role mapping → graph → candidate or entry hypothesis → QMX." [R39 N1, FG 831]

**[DEEP]:** Each stage a verb, JSON in, JSON out. The cheap model only ever holds one stage.

**[ANL]:** And a match report. Every source sentence maps to an entry id or "unmatched". Unmatched sentences are either append proposals or the reason the build stops.

**[BLD]:** What if he never says the timeframe?

**[OOS]:** Then it's a parameter. K4: timeframe is a sweepable setting. Test a range, count the tries. Don't stop the build for it.

**[SOL]:** The record kept his line: "a bot that has ambiguity shouldn't be tested." [R39 K14, GM 3262]

**[ANL]:** And the paper trail kept the other half of his view: an unspecified timeframe is normal abstraction, an unknown order type is a real defect. Research 40, row 5.

**[ORB]:** Order type isn't a detail. Fades use limits, breakouts use stops. If the source doesn't say, the setup tells you.

**[OOS]:** K14. Given. Not a question.

**[BLD]:** What do I do when he gives no exit?

**[SKEP]:** You don't design one. That's the risk-and-sizing session.

**[SOL]:** The record's rule: no exit means an "entry hypothesis", and any added exit is labelled "added by our pipeline". [R39 J1, FG 795]

**[ANL]:** Then QML's room is a labelled exit slot: source-defined, builder-added from a named exit entry, or deliberately open, and the unit can't go to a test with "open". What fills it is not our session.

**[BLD]:** And I must not look at backtest results while I build?

**[OOS]:** Never. If you peek and adjust, your first test isn't a test. And if you're a model trained up to some date, your first honest test is after that date.

*Surfaced:* the source-to-unit chain as verbs; the match report; gap kinds (abstraction, defect, contradiction); labelled exit slot as the only room; blind building; post-cutoff first test.

---

## P10. Plain Python and ML beside QML

**[MQL]:** Thirty-nine percent of screened MQL5 articles use a learned model. Neural nets, trees, LSTM, ONNX files. Forecast direction. Class probability above 0.5.

**[DEEP]:** A model is a reading whose output is a probability. Its threshold is an ordinary threshold atom. It fits the same if-else frame.

**[ANL]:** With two extra fields. The training window, so tests inside it are refused. And a hash of the file.

**[SQX]:** And the meta-label. A second model that decides whether to take the first signal. That's a veto role, nothing more.

**[SOL]:** The record holds a seed nobody answered. He said: "I had an idea of using a mini scalper for an indicator." [R39 C5, FG 796]

**[ANL]:** A whole unit as a reading. Its signal port feeds another unit's context.

**[SKEP]:** And then the second unit can't trade when the first is off. Units stand alone. That's a standing order.

**[DEEP]:** Unless the mini scalper is library code the second unit runs inside itself. It's a reading with a lot of insides. Same as an HMM.

**[OOS]:** And its tries come with it. If the mini scalper was tuned on the same data, you've doubled the search.

**[PERP]:** What about an RL agent that's the whole unit?

**[DEEP]:** Then QML is only at the edges: ports, journal, risk socket, manifest. Inside, plain Python.

**[MQL]:** And 20185, where an LLM returns entry, stop and confidence at temperature 0.2?

**[ANL]:** Allowed as a block, stamped non-deterministic, and QMB replays the logged answer rather than calling the model again.

**[SKEP]:** You'd let an LLM trade?

**[ANL]:** I'd let it be tested honestly. Whether it trades is his click.

*Left open:* whether a unit may read another unit live; whether non-deterministic blocks are allowed live; what the minimal manifest of a plain-Python unit is.

---

## P11. The trader at the screen

**[OP]:** "how am I going to be using units, okay, to literally trade and make money, to be honest." (T2:849)

**[ANL]:** What he sees per unit: one trader's sentence, the pillar view, and which numbers moved this week and why. "ATR multiple 1.6, range 1.2 to 2.0, moved from 1.5 after 40 trades."

**[1M]:** And why it didn't trade. Spread too wide. Data stale. Context false. That's the question I ask my own bot every morning.

**[ORB]:** A trading plan. Setup, trigger, entry type, management, and a line that says "risk: from the risk socket". Tharp's shape. Every trader can read that.

**[SOL]:** The record proposed a five-layer trading plan (setup, bot plan, book plan, system plan, operator plan); he answered "the missing parts are the first two but the rest I think is already there". [R39 B3, FG 831, FG 902]

**[DEEP]:** He never edits code. He edits defaults and ranges. Configurable means UI-editable.

**[SKEP]:** And the "trader's lint"? QML nagging "fades usually use limits"?

**[ORB]:** As a warning, fine. As a rule, never. Some fades break the rule and pay.

**[OP]:** "add defaults, but keep it free, yeah? Same thing, I think, goes the dictionary, all right? Keep it free." (T1:1574)

*Surfaced:* the unit read as a trading plan; "why didn't it trade"; tuning shown as a dial inside a range; advisory-only trader's lint.

---

## P12. How it fails, and the last word

**[SKEP]:** My turn. Five ways this dies. One: self-tuning follows last month and calls it adaptation. Two: profiles multiply into ten thousand hidden variants nobody counted. Three: the dictionary grows faster than its code and builders bind words that can't run. Four: labels change version and old trades lie. Five: the same idea under two names gets counted as two bets.

**[OOS]:** Six: the MIS fits its regimes on all the data and every backtest that reads it is contaminated.

**[ANL]:** Seven: it all lives in one tool's folder and nobody else can read it. That happened in August. He called it "trash" in limbo.

**[ANL]:** And the review session on 26 Aug ended with him calling the 239 entries permanent library content, to be reviewed first if doubted. Research 41, from his own turn.

**[SKEP]:** And then he said the dictionary "needs a rebuild".

**[OP]:** "Auditing the dictionary, yeah, the dictionary needs a rebuild, an entire thing, like a whole bloody, because the ideas are there" (T2:216)

**[ONTO]:** Both are true. Review the ideas, rebuild the form.

**[SKEP]:** Or rebuild the ideas from the census and keep only the names.

**[SQX]:** Or let my builder generate ten thousand units and let the journals tell you which words matter.

**[OOS]:** Over my dead body.

**[OP]:** "Okay, you took it under the MIS, but when you look at QML, the questions even you are asking, so most of them, even me as a newbie trader, I already know what they mean." (T2:836)

**[1M]:** He's telling you to stop asking us what a stop is.

**[DEEP]:** Then the last rule of the room: before a question goes to him, check it against what every trader knows. If it's on that list, it's an input, not a question.

**[OP]:** "keep it stupid simple, but again, design for a very complex system, but not design a complex system." (T1:1177)

*The room breaks without agreement on:* review vs rebuild of the 239; whether state-chosen branches are one unit; whether funding and OI are readings or terrain; whether a unit may read another unit; whether a genetic builder belongs anywhere near QML.
