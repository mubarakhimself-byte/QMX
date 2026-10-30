# Party mode transcript: the MIS field

Run 2026-10-30 by the MIS expansion agent. Skill: `bmad-party-mode`, **session mode** (one mind voices every persona, no subagents), run as an explicit `--non-interactive` party on the brief's intent until a natural close. Activation scripts ran: `resolve_customization.py` returned `party_mode = session`, `party_memory = true`; `resolve_party.py` returned `installed_agents_resolved: false` with no members, so the brief's inline cast is the roster. The skill's memory folder sits outside this run's write scope, so the room memory is kept at `party-memory/.memlog.md` in this workspace instead (written with `memlog.py`).

**Nothing here is a decision.** Clashes stay open on purpose. Every idea and question raised carries a round tag (P1 to P11) and is carried into `mis-field.md`.

## Voices with limits

- **The operator** speaks only in verbatim quotes, each tagged `(T1:n)` or `(T2:n)`. `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md`, and `n` is the line holding the whole turn. Every quote was checked by script against that line (`quotecheck.py`, run at the end; result in `mis-field.md` §0).
- **The Sentinel's designer** speaks only from research 19 §2 to §4 (the old system). Each line carries the R19 source it restates. When the room asks it something R19 does not hold, it says so.
- **Everyone else** is a persona. Their trading claims are INFERRED (general practice) unless they cite a research file and section, which this agent read this session (CHECKED by citation).

Shorthand: R05, R09, R15, R16, R18, R19, R35, R36, R39 = `research/<n>-*.md`; PF = `research/funnel3/party-brainstorm/playing-field.md`; QF = `research/funnel4-qml/party-brainstorm/qml-field.md`; K1 to K20 = research 35 §6 "things any trader knows".

## The room

| Tag | Name | Who |
| --- | --- | --- |
| [1M] | Tomas | 1-minute FX scalper on cTrader. EURUSD, GBPUSD, USDJPY. Counts in ticks and spread. Hates lag more than losses. |
| [GOLD] | Ines | Gold session trader. London open, New York open, the fixes. Thinks every instrument has a personality. |
| [DOM] | Marcus | Index-futures order-flow trader (ES, NQ). Footprint, delta, DOM, absorption. Calls indicators "rear-view mirrors". |
| [PERP] | Kai | Crypto perps trader. Funding, open interest, liquidation maps, weekend thinness. Awake at 03:00 UTC. |
| [ID] | Priya | Intraday 15-minute to 1-hour trader. VWAP, opening range, higher-timeframe bias. Patient. Writes everything down. |
| [MICRO] | Prof. Okafor | Market-microstructure researcher. Order-flow imbalance, queue imbalance, information per bar. Quotes papers. |
| [STAT] | Dr. Lindqvist | Regime-modelling statistician. HMMs, jump models, change points. Obsessed with label versions and look-ahead. |
| [PHYS] | Zed | "Market physics" enthusiast. Hurst, entropy, Ising spins, chaos. Loud, generous, sometimes right. |
| [SENT] | The Sentinel's designer | Designed the old QMX sentinel. Voiced only from R19. Speaks in the old system's names. |
| [ANL] | Mira | A QMX analyst agent. Reads charts, journals and MIS logs. Wants every claim to come with a tool that can check it. |
| [SOLO] | Bo | Systems designer. Units must stand alone. Draws boxes and then crosses out the arrows. |
| [SKEP] | Grace | The skeptic. Thinks the MIS mostly adds noise and a second place to be wrong. |
| [OP] | The operator | Only his own words. |

---

## P1. What is the MIS for?

**[OP]:** "What I want the MIS to do is understand what the market is going in." (T1:1903)

**[OP]:** "What I wanted was the MIS just reads and outputs. Then the units, or previously the bots, pick the output and they propose whether to use it or not. That's the simplest design I had." (T1:1951)

**[SKEP] Grace:** Reads and outputs. Fine. Then my first question is his, not mine.

**[OP]:** "So how is the MIS not adding more noise to an already noisy market?" (T1:264)

**[SKEP] Grace:** Nobody has answered that in ten days of files. Every unit already reads price. The MIS reads the same price and hands back a label. A label is a compressed copy of price with an extra failure mode.

**[MICRO] Prof. Okafor:** It is only a copy if it reads the same information. It does not have to. A unit on EURUSD 1m sees one chart. The MIS can see a hundred charts, the book depth where it exists, the calendar, and the history of every hour of the week. That is information the unit does not have. R05 §1.3 says it plainly: speed comes from more information per bar, not a cleverer model.

**[SOLO] Bo:** Which is also the trap. If the MIS sees what the unit cannot, the unit starts to need it. Then "reads and outputs" becomes "the unit can't trade without it".

**[OP]:** "It doesn't mean that if the MIS is not working, it doesn't mean that these bots won't trade. They will, okay?" (T2:135)

**[SOLO] Bo:** Good. So write it down as a test, not a hope. Every unit runs once with MIS input and once with the MIS dark. Both runs are in its record.

**[ANL] Mira:** And the difference between the two runs is the only honest answer to Grace. Call it the MIS lift, per unit, per market, per hour. If it is zero, the MIS is noise for that unit. Fine. Say so in the journal.

**[GOLD] Ines:** You are all talking like the MIS is one thing. When I trade, "what the market is doing" is three questions. Is it moving? Is it moving my way? Is it the time when it usually moves? Those are three readings with three clocks.

**[OP]:** "So the MIS is playing the role of just expanding the domain." (T1:1903)

**[PHYS] Zed:** Expanding the domain! Yes. It is a telescope, not a steering wheel.

**[SKEP] Grace:** A telescope that is eight hours late on trends, per R05 §1.3. Some telescope.

**[STAT] Dr. Lindqvist:** Eight hours for a strong new drift on 1m closes. About twelve minutes for a doubling of volatility. Those are different instruments in the same box. The box should say which reading is which speed.

**Round tags (P1):** MIS lift per unit as a standing pair of runs; "telescope not steering wheel" as the plain-words frame; three readings with three clocks (moving, moving my way, usual time); the noise question as a measurable, per-unit quantity. Clash left open: Grace (a label is a compressed copy of price) against Okafor (the MIS sees information the unit cannot).

---

## P2. Style first: what goes inside a scalper's MIS?

**[OP]:** "Because you are not going to put an HMM inside a scalper's MIS. That makes no sense. But you can put multiple indicators inside a scalper's MIS." (T2:219)

**[1M] Tomas:** Thank you. Finally someone said it. I hold for two minutes. Tell me the spread is normal, the tick rate is up, London just opened and there is no red news in the next ten minutes. That is my MIS. I do not want a hidden Markov anything.

**[STAT] Dr. Lindqvist:** You just listed four readings. Three are "now versus usual for this hour". That is a seasonal ratio, R05 §1.1 tier T1. You do not need an HMM for it. But do not tell me the HMM has no place. On a daily clock it can say "this week EURUSD has been in a quiet regime". You use that to pick which pairs to watch this morning.

**[1M] Tomas:** Then it is not in my MIS. It is in my morning coffee.

**[ID] Priya:** That is the point though. My MIS is the morning coffee. I trade 15 minutes to an hour. I care whether today is a trend day or a range day, and by 10:30 New York I want to know. A 15-minute regime label that is 2 hours late is useless to Tomas and about right for me.

**[OP]:** "A human trader who's a scalper will not wake up at the same time to look at charts as a person who day trades" (T2:135)

**[PHYS] Zed:** So build the MIS like a human trader's day. The scalper's MIS wakes every tick. The intraday MIS wakes every bar. The swing MIS wakes once a day. Same vocabulary, different alarm clocks.

**[MICRO] Prof. Okafor:** And different evidence. The scalper's fast readings should be things you observe directly, not infer: spread, tick rate, top-of-book depth, order-flow imbalance where the book exists. R05 §1.1 cites OFI explaining about 65% of short-interval mid moves. That is a "now" reading, not a forecast.

**[DOM] Marcus:** For my ES scalps, the MIS is the tape. Is delta confirming? Is someone absorbing at the high? That is order flow. You can't do it on a 1-minute OHLC bar. So "a scalper's MIS" means nothing until you say what data the market gives.

**[SKEP] Grace:** Which is the operator's third step. Style, then timeframe, then data. So far we have only got to step one and already there are four MISs at this table.

**[OP]:** "We can research firstly the trading style, then trading style with the timeframes." (T2:219)

**[SENT] The Sentinel's designer:** For the record, the old live path built "the authoritative RegimeReport from Chaos + Ising Regime + News, with optional HMM shadow/hybrid overlays" (R19 §2, `GPTR:14244-14246`). The weighted ensemble was "NOT wired into the live Sentinel tick path" (R19 §2, `GPTR:6560`). It was one sentinel for every style.

**[PHYS] Zed:** Chaos and Ising on a tick path! I love it and I am embarrassed by it.

**[OP]:** "I think for it, what it was using, why it was made like that is that because it was considered for bots that trade anywhere, so not just scalpers." (T1:444)

**[SKEP] Grace:** So the old one failed because it was one size for everyone. And the new idea is many sizes. That is more things to be wrong.

**[ANL] Mira:** Or fewer, if each style only carries the readings that pass its own speed test. A reading whose lag is longer than the style's holding time is not allowed in that style's fast tier. That is a rule an agent can check by script.

**Round tags (P2):** style decides the alarm clock (tick, bar, day); the fast tier holds only directly observed readings; a reading may sit in a style's fast tier only if its lag beats the holding time (extends R15 idea 44); the "morning coffee" tier for slow labels that pick what to watch; one vocabulary, several clocks. Clash left open: Lindqvist (HMMs belong on a daily clock) against Tomas (then they are not part of a scalper's MIS at all).

---

## P3. Timeframe second: 1m, 5m, seconds, and the HMM-per-timeframe worry

**[OP]:** "doesn't it mean that we are going to be training an HMM model at a 1 minute time frame and at a 5 minute time frame" (T2:135)

**[STAT] Dr. Lindqvist:** If you train models per timeframe per instrument you get a zoo. A hundred instruments, four timeframes, two retrains a month. Nobody can version that honestly.

**[OP]:** "If they are, if it's the same strategy, or rather the same unit trading the same pair on different time frames, that's just correlation." (T2:1001)

**[1M] Tomas:** Right, and K4 in research 35 says any trader knows that. 1m and 5m on the same pair is one idea. So why would the MIS need two different brains for it?

**[MICRO] Prof. Okafor:** It does not. It needs one reading at the finest data you have, then aggregated up. Realised variance from ticks rolls up into 1m, 5m and 1h. The 5m reading is not a new model. It is the same measurement, summed.

**[STAT] Dr. Lindqvist:** True for volatility. Not for direction. A trend on 5m and a trend on 1m are different questions with different lags. But you can still define them once with a horizon parameter. One reading, a horizon tag, many horizons. R15 idea 31 already proposed the tag.

**[ID] Priya:** I want the horizon tag to be in clock time, not bars. "Volatility over the last 15 minutes" means the same thing to me on 1m bars and on 5m bars. "Volatility over 14 bars" does not.

**[PHYS] Zed:** Clock time is fine for FX. For crypto, clock time is fine. For ES at 09:30 New York, the first fifteen minutes carry more trading than the next hour. Volume time. Tick time. Pick one.

**[DOM] Marcus:** Volume time for me. A 1,000-contract bar is a bar.

**[1M] Tomas:** I don't have real volume. I have ticks.

**[OP]:** "Yeah, FX has no real volume." (T2:219)

**[SKEP] Grace:** So now the clock itself depends on the data. You wanted timeframe second and data third. They are tangled.

**[ANL] Mira:** Tangled, but countable. A reading's horizon can be declared in one of three clocks: clock time, tick count, volume. A market that lacks real volume cannot offer a volume clock. That falls out of the data table, not a debate.

**Round tags (P3):** one reading at the finest data, aggregated up, instead of a model per timeframe; a horizon tag in a declared clock (clock time, tick count, volume); timeframe and data are entangled through the clock choice; the "model zoo" warning (instrument × timeframe × retrain). Clash left open: Okafor (aggregate up, one measurement) against Lindqvist (direction is a different question at each horizon).

---

## P4. Data third: what the market offers

**[OP]:** "So it means the MIS for a market that has all that data is different." (T2:219)

**[OP]:** "So in other words, a Forex one is different from a futures one, but the time frame or the time frames are the same." (T2:219)

**[MICRO] Prof. Okafor:** Let me give the room a ladder. Rung zero: the calendar only. Hours, sessions, news times, funding times, roll dates. Rung one: OHLC bars. Rung two: quote ticks and tick counts. Rung three: depth, the order book. Rung four: the trade tape, real volume, aggressor side. Rung five: derivatives fields, open interest, funding, liquidations, basis. Rung six: outside data, fundamentals, news text, other markets.

**[DOM] Marcus:** ES futures: rungs zero to five, all of it. Real tape.

**[1M] Tomas:** cTrader FX: zero to three. Depth yes, tape no. STATE.md records that from research 21.

**[PERP] Kai:** Perps on a good exchange: zero to five, and rung five is where my edge lives. Funding is hot, open interest is climbing with price, liquidations stacked below. No FX trader has that reading.

**[GOLD] Ines:** XAUUSD as a CFD is FX-like, zero to three. GC futures is ES-like. Same metal, two ladders.

**[ID] Priya:** And index CFDs inherit price from the future but not its volume. R35 §2.2 says so.

**[SKEP] Grace:** So the honest name for "a forex MIS" is "a rung-three MIS". The asset class is a guess at the rung.

**[OP]:** "I don't think future is going to use the same analysis system, market analysis or market intelligence as a currency." (T1:1999)

**[ANL] Mira:** He said that before the ladder existed, and the ladder explains why. The rungs differ. So the MIS might be organised by rung, and asset class becomes a lookup: "this instrument, at this venue, offers rungs zero to three".

**[SOLO] Bo:** Per venue, not per instrument. The same instrument at two brokers can sit on different rungs.

**[PHYS] Zed:** And a rung can be borrowed! Read ES tape to inform the US500 CFD. Read the BTC perp's funding to inform BTC spot. Proxies across venues.

**[MICRO] Prof. Okafor:** Borrowed rungs are a research question, not a free lunch. R35 §7 item 8 lists exactly that: how well futures order flow proxies CFD flow is not settled by practice.

**[SKEP] Grace:** And the minute you borrow, you depend on a second feed. Bo, your units just grew a dependency.

**[SOLO] Bo:** Only the MIS grows it. The unit never knows the reading came from ES. If the ES feed dies, the reading goes stale and the unit trades without it.

**Round tags (P4):** a data ladder (rungs 0 to 6) as the way "data a market offers" is stated; rungs belong to instrument-at-venue, not instrument; asset class as a lookup into rungs; borrowed rungs (cross-venue proxies) as an option and a research question; the same metal on two ladders. Clash left open: Grace (borrowing adds a dependency) against Bo (only the MIS carries it).

---

## P5. Asset classes as data, and inefficiencies found by looking

**[OP]:** "I think the MIS should be able to categorize by, of course, organization is important." (T1:1999)

**[OP]:** "there is a huge possibility we can discover market inefficiencies with only that" (T1:1999)

**[PERP] Kai:** He is right about that. Funding settles every eight hours by default (R35 §2.2). The hour before funding behaves differently. You don't need a strategy to see it. You need the MIS's logs, sorted by the hour.

**[GOLD] Ines:** Same with gold. The fixes, the New York open sweep. If the MIS stamps every reading with the hour and keeps it forever, the habits fall out of the history.

**[STAT] Dr. Lindqvist:** Falls out, then gets tested on months the search never saw. A habit found by sorting a thousand hours is a habit of the thousand hours until proven otherwise.

**[ID] Priya:** Fine. But I want the habits written somewhere I can read. A page per market: "what this market usually does at each hour of the week".

**[ANL] Mira:** That is the market almanac from research 13, fed by MIS logs. An agent can write it weekly. The operator reads it.

**[OP]:** "We are changing it to look at the MIS suitability in a way, shape or form." (T1:2051)

**[SKEP] Grace:** Note he said suitability. Not a strategy factory. Research on each class is to decide which sensors suit which class.

**[SENT] The Sentinel's designer:** The old system had a related habit store: `SessionPerformanceProfile` and young versus mature session specialists (R19 §3, covered elsewhere as G09 A.3). And in August, "Do not fork per market. Forex, crypto spot, and prop-firm constraints are tags on strategies" (R19 §3, `ST\dictionary\README.md:19-21`).

**[DOM] Marcus:** Tags on strategies, yes. But not tags on the MIS. My ES MIS and Tomas's FX MIS really are different machines.

**[MICRO] Prof. Okafor:** Different sensors. Maybe the same output words. That is the open choice: one vocabulary with per-class sensors (R16 §2), or separate MISs per class, which is how he put it.

**[OP]:** "we can design an MIS that fits, should I say, a futures market, then an MIS that also fits a Forex market." (T2:135)

**[PHYS] Zed:** Both! Separate engines, one dashboard. Like cars. Different engines, the same speedometer.

**[SKEP] Grace:** Until the speedometer says 100 on both and one of them means kilometres.

**Round tags (P5):** habits fall out of stamped, kept MIS logs (sorting by hour of week); the almanac written weekly by an agent from MIS logs; research per class decides sensor suitability, not strategies; "separate engines, one speedometer" as a framing of the vocabulary-versus-separate-MIS choice; Grace's unit warning (the same word must mean the same thing across classes). Clash left open: one vocabulary with per-class sensors against a separate MIS per class.

---

## P6. What a unit reads, and what the MIS publishes

**[OP]:** "what if a strategy is using an indicator that also the MIS is using? Is that repetition?" (T2:219)

**[OP]:** "if it's using the same things as in those in the MIS, it means it is already specific." (T2:219)

**[ANL] Mira:** K3 says one primitive, many roles. So the reading is not repeated. But his second point is new. If the unit's own rules already contain "ADX below 20", the unit has already declared its context. The MIS reading of the same thing adds nothing to that unit, except breadth: the MIS can say where else ADX is below 20.

**[1M] Tomas:** So for me the MIS isn't a filter. It is a finder. It tells me which pairs to look at. I filter myself.

**[SOLO] Bo:** Then units read two things. Their own feed, always. And a finder list, sometimes. The finder list can be late, empty or gone.

**[OP]:** "the bot itself also didn't like taking only information from the MIS. No, it took in also live market data." (T1:444)

**[SENT] The Sentinel's designer:** That is how the vault built it. A `BotInputAssemblerFactory` gave each bot `raw_broker_view`, `qml_feature_view` and `mis_context_view`, "so bots are not forced to rely on a single possibly-biased derived stream" (R19 §2, vault file lines 557-570). And the single-computation rule: no bot computed regime state locally; all read one snapshot (same file, 13-15).

**[STAT] Dr. Lindqvist:** Those two rules fight. Three views is independence. Single computation is dependence.

**[SOLO] Bo:** They fight only if the unit has no fallback. A unit could carry a cheap copy of the reading it needs, computed from its own feed, and prefer the MIS version when it is fresh.

**[SKEP] Grace:** Two versions of one reading. When they disagree, which one did the trade use? QF Q78 already asked that and nobody answered.

**[OP]:** "it should take in information from, let's say now, an MIS cluster." (T2:135)

**[PERP] Kai:** Cluster. I like that word more than list. Don't tell me "20 markets are ranging". Tell me "20 markets are ranging and they are 3 bets". R15 idea 42 had that.

**[ID] Priya:** What does the MIS publish then? Labels? Numbers? Lists?

**[MICRO] Prof. Okafor:** Publish the number and its usual range. Let the unit cut its own bands. A label is the MIS's opinion of a threshold. Different units want different thresholds.

**[GOLD] Ines:** I can't read numbers in the heat of the open. I want words.

**[ANL] Mira:** Both, then. Number, percentile against the usual for this hour, and a word. Units read the number. People read the word.

**Round tags (P6):** the MIS as a finder (where else is my context true now), not a filter, for units whose rules already declare their context; a unit's own cheap copy of the reading it needs, preferring the MIS when fresh; publish number + seasonal percentile + word (units read numbers, people read words); MIS output as clusters ("20 markets, 3 bets"); the three-view vault pattern versus the single-computation rule. Clash left open: Okafor (publish numbers, units cut bands) against Ines (people need words), and Grace's disagreement question (which version did the trade use).

---

## P7. New context, new sensors, and an MIS that grows

**[OP]:** "it means that the MIS can be upgraded as the agent see fit, obviously with my approval, yeah, or with the user's approval, not mine alone, the user of QMX's approval." (T1:1951)

**[OP]:** "some of the capabilities that KMX is meant to have is to grow its own limbs" (T2:135)

**[SENT] The Sentinel's designer:** In August he said the opposite thing about versions. "MIS is like centrally used and you kind of have no control over it. I just wanted you to know that it exists. Yeah, just exists, it's a constant." And he did not want MIS versions left running side by side (R19 §2, `GEN:1431`).

**[SKEP] Grace:** A constant that grows limbs. Pick one.

**[ANL] Mira:** Not a contradiction if the trunk is constant and limbs are added. Each sensor has a version. Old trades keep the version they were stamped with. The live MIS runs one version of each sensor at a time.

**[STAT] Dr. Lindqvist:** And a new version runs in shadow first. That exists today: `qmn/mis/shadow.py` (R18 §4). A candidate labeler without authority.

**[OP]:** "the quality of what's processing information inside the MIS is directly proportional to the quality of output" (T2:219)

**[PHYS] Zed:** Garbage in, garbage out! So who checks the limbs?

**[ANL] Mira:** An agent proposes a sensor: what it reads, what it calls its output, what lag it has at each clock, its false alarm rate, its lift on the units that would read it. The user approves. That is the operator's rule, and R15 idea 48 drafted the steps.

**[OP]:** "The MIS for a scalper should be from the research. We shouldn't assume that the HMM will work." (T2:219)

**[OP]:** "An HMM can work best in crypto, but you discover that, according to academic research, that an HMM with a specific configuration can work best in BT." (T2:219)

**[PERP] Kai:** That is a configuration on a sensor, per instrument. An HMM with three states on BTC, two on ETH. A limb with a setting.

**[STAT] Dr. Lindqvist:** And the configuration comes from a paper, which was fitted on someone else's sample. Paper configurations are priors, not facts.

**[SKEP] Grace:** Here is my worst case. Agents keep adding limbs. Nobody removes any. In a year the MIS has 300 sensors and 40 of them are near-duplicates.

**[SOLO] Bo:** Then removal must be as easy as adding. A sensor nobody reads for N weeks gets a retire card.

**[1M] Tomas:** And a sensor I read but that never helped me gets a card too. Per unit.

**Round tags (P7):** "constant trunk, added limbs" as the reconciliation frame for constant vs upgradable; shadow first for every new sensor version (exists today in `shadow.py`); the proposal card (reads, output words, lag per clock, false alarm rate, lift); paper configurations as priors; retire cards for unread or unhelpful sensors; per-instrument sensor settings. Clash left open: Grace (sensor sprawl is the likely end state) against Mira (cards make sprawl visible).

---

## P8. Agents as analysts: replicating the MIS by reading charts

**[OP]:** "Agents can look at price action for the day, market, whatever, price action for the day. They can use the TA, they can use the MIS logs and the MIS itself." (T2:325)

**[OP]:** "All they are trying to do is literally replicating the MIS's thing." (T2:325)

**[ANL] Mira:** That is my job description. I read the daily chart, the MIS log, the calendar. I write "EURUSD has ranged for three days; the MIS agrees; the Asian range is narrow". Then what?

**[SKEP] Grace:** Then nobody can tell if you were right. An agent that replicates the MIS is a second MIS with no version and a chatty style.

**[ANL] Mira:** Unless I write my reading in the MIS's own words, with a timestamp, before the session. Then my reading can be scored against what happened, the same as a sensor.

**[STAT] Dr. Lindqvist:** That makes the agent a sensor. With a lag of one day and a cost in usage. Fine. Put it in the slow tier.

**[OP]:** "The MIS gives us low label per session or per day" (T2:325)

**[ID] Priya:** Two speeds. The agent writes the morning shortlist. The fast sensors handle the minutes.

**[OP]:** "based off the information me and the copilot have been looking at this entire week, we do see that these markets, not just historically, we've seen and confirmed that these markets are mostly mean reverting." (T2:219)

**[OP]:** "we can retrain a version of the MIS that can also see such." (T2:219)

**[STAT] Dr. Lindqvist:** That is human labels as training data. Useful. Dangerous. Human labels made after the week know how the week ended.

**[ANL] Mira:** So the weekly label is stored with the date it was written and what it could see. It is a label about the past week, not about the next one.

**[SKEP] Grace:** And who decides whether the agent's shortlist beat the MIS alone, and both beat doing nothing? PF L12-04 asked that already.

**[SOLO] Bo:** Three shortlists logged every day. Agent, MIS, all-admitted. Score them after.

**[GOLD] Ines:** I'd read that page every Friday.

**Round tags (P8):** the analyst agent as a slow-tier sensor that writes in the MIS's vocabulary with a timestamp before the session; the operator-and-copilot weekly view as dated human labels; three logged shortlists (agent, MIS, all-admitted) scored after the fact; the analyst's output as an almanac page; human labels as training data with a hindsight warning. Clash left open: Grace (an agent that replicates the MIS is an unversioned second MIS) against Mira (stamped readings make it a sensor like any other).

---

## P9. Correlation and herding

**[OP]:** "Maybe the correlation ledger can take the output also, all right?" (T2:219)

**[PERP] Kai:** The day the MIS says twenty markets are ranging is the day they all range for the same reason. Dollar asleep, Asia holiday, whatever. R16 §7 point 2 says breadth is not independence.

**[MICRO] Prof. Okafor:** The MIS sees that before anyone else. It holds the readings for all markets at the same moment. Co-movement of readings is itself a reading: "dispersion is low today".

**[SOLO] Bo:** So the MIS publishes the readings, and the correlation side reads them. The MIS does not police correlation. It describes it.

**[OP]:** "If they are, if it's the same strategy, or rather the same unit trading the same pair on different time frames, that's just correlation." (T2:1001)

**[1M] Tomas:** Herding worries me more. Forty units all read "EURUSD quiet, spread normal" at 08:00 London. All forty fire in the same minute. On a $300 account that is one trade wearing forty hats.

**[SENT] The Sentinel's designer:** The old system had a per-tick answer, the Intent Aggregator. It gathered every intent on one symbol in a window of at most 50 ms, kept the higher `confluence_score` on opposite directions, dropped the lowest-priority intents over a per-symbol cap, and dropped marginal intents that pushed portfolio correlation too far (R19 §2, `QMLD\02-QML-bridges.md:74-100`).

**[SKEP] Grace:** STATE says book and correlation control belong to the risk-and-sizing session. So the MIS can't do any of that.

**[ANL] Mira:** It can still publish what the risk side needs. A herding count: how many units read this market as a match right now. That is a description, not a control.

**[STAT] Dr. Lindqvist:** And there is a feedback loop. If his units trade enough on a thin market, they change the market the MIS reads. PF L03-21 asked that. For a $300 account, not today. For a scaled account, one day.

**[PHYS] Zed:** Reflexivity! Soros! The observer moves the observed!

**[GOLD] Ines:** Zed, it's gold. Nobody's moving gold with 0.01 lots.

**Round tags (P9):** dispersion (co-movement of readings across markets) as an MIS reading; the MIS describes correlation, the risk side controls it; a herding count (how many units read a market as a match now) published, not acted on; the old Intent Aggregator as a reference for what the risk side might want from the MIS; reflexivity as a scaled-account question. Clash left open: where the line between describing and controlling sits once the MIS publishes counts.

---

## P10. Failure and independence

**[OP]:** "Neither does it switch on, nor does it switch off." (T1:1574)

**[SOLO] Bo:** Good. So the MIS failing can never switch a unit off either. A late reading is a missing reading.

**[1M] Tomas:** K10 says stale data means no new entries. That is my own feed. A stale MIS reading is different. My feed is fine. I keep trading on my own rules.

**[SKEP] Grace:** Unless the unit's whole life is "trade where the MIS finds my context". The pure System 1 unit has nothing of its own to fall back to.

**[OP]:** "system one and system two were never any definition under QMX." (T2:789)

**[SOLO] Bo:** Then don't argue about the word. Argue about the case. A unit that only knows how to pick markets from a finder list. With the finder dark, what does it trade? Its last list? Its home market? Nothing?

**[ANL] Mira:** Its last list, with an age on it. A list older than its style's freshness setting falls back to its home markets.

**[STAT] Dr. Lindqvist:** And a wrong MIS is worse than a dark one. A sensor whose output silently flips meaning after an update moves every unit at once. R16 §7 point 10: a change flag that false-alarms on every spike will move 200 units at once.

**[MICRO] Prof. Okafor:** Every published reading carries a health field: fresh, stale, degraded, shadow. `degraded-sensors` already exists as a labeler (R18 §4).

**[PERP] Kai:** Weekends. My markets never close but the feeds blink. A crypto MIS must survive a venue going down while the others keep trading.

**[GOLD] Ines:** And DST. Twice a year every "usual for this hour" baseline is one hour wrong for three weeks. R05 §1.5 names it.

**Round tags (P10):** a late reading is a missing reading, never a switch; a finder list carries an age and falls back to home markets after the style's freshness setting; a health field on every reading (fresh, stale, degraded, shadow), extending today's `degraded-sensors`; "a wrong MIS is worse than a dark one" (silent meaning flips after updates); venue-level failure in 24/7 markets; DST and holiday baseline breaks. Clash left open: Grace (a pure finder-list unit has nothing of its own) against Bo (then it has a home market by rule).

---

## P11. His view: what the MIS gives him

**[OP]:** "its edge can be amplified by these other things. So in other words, it can be amplified by the MIS." (T2:135)

**[OP]:** "Sniping is something I want to really focus on" (T1:442)

**[GOLD] Ines:** Sniping is my whole life. The open, the first sweep, the clean move. The MIS can tell him which market has the clean open today.

**[ID] Priya:** And which day. Not every New York open is the same. Some days the first 30 minutes are dead.

**[ANL] Mira:** "Today's opens, ranked by how they usually behave on a day like this." That is a page he would read before London.

**[SKEP] Grace:** "Amplified" is a strong word for a filter that may skip good trades. Show him the trades the MIS made him skip, and how they ended.

**[SOLO] Bo:** That is the same MIS lift from round one, shown as a story. "Last week the MIS kept you out of 12 trades. 8 would have lost."

**[OP]:** "Actually, most of this is just data organization, to be honest." (T1:442)

**[PHYS] Zed:** He is right! It's tables! Big beautiful tables!

**[OP]:** "We should instead pose questions that are meant to be answered with the workflow." (T2:219)

**[SKEP] Grace:** Then let's stop answering and leave the questions for him and the research runs. I still think it is mostly noise.

**[MICRO] Prof. Okafor:** And I still think noise is measurable.

**Round tags (P11):** "today's opens ranked by how they usually behave on a day like this" as a sniping page; the skipped-trades story ("the MIS kept you out of 12 trades, 8 would have lost") as how lift is shown to him; "most of this is data organization" as a reason to start from tables; amplification needs its downside shown. Clash left open, and the room closes on it: Grace (mostly noise) against Okafor (noise is measurable).

---

## Close

The party ran on the brief's intent to a natural close, as an explicit non-interactive run. No summary of agreement is given, because there was none. The clashes listed at the end of each round go into `mis-field.md` §5 as open questions. No keepsake HTML was made for the party; the brainstorm's `brainstorm.html` covers the run. No new faces need saving: the cast was inline for this run only.
