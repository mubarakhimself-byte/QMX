# The MIS: one place to come back to

Content for his MIS page, owed to him since his 31 Oct midday rulings (STATE ruling 55, for the lead). The lead turns it into a visual page. Words and data only.

Sources read for this file: the MIS research (`research/22-mis-sensor-speed.md` with its three simulation scripts in `research/22-study/`, `research/23-mis-organisation.md`, `research/37-mis-academic.md`, `research/funnel5-mis/party-brainstorm/`); his words in `operator/transcript-2026-10-29-to-30.md` and `operator/transcript-2026-10-30-to-31.md`, plus five quotes from two of his 28 Oct turns in `operator/transcript-2026-10-20-to-28.md` that the design already builds on; STATE midday rulings 44, 48, 50 and 55; the Level 0 spine (the MIS part and its main rule); `architecture/parts/C-node-mis-external/MIS.md`, its spine answers, `UI-NEEDS.md` and `BUILD-SLICES.md`; the merged build order in `architecture/review/FC1-fix-check.md`.

Every quote of his below names its date and the transcript line it sits on. All paths are under `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\`.

## 1. What the MIS is

The MIS (market information system) reads every market QMX trades and publishes what it sees, such as how volatile a market is against its own usual level, whether it is trending or ranging, how wide the spread is, and which session or event window is open, with the time of each reading. Units pick from these readings if they want them, and no unit needs the MIS to trade, so if the MIS stops, every unit keeps trading on its own conditions. It starts with plain indicators and simple statistics that need no training, and it takes the models he trains later in the Lab without any unit changing.

## 2. His visions, in his words

Grouped by idea. Each group ends with where the design keeps it, or what is still open.

On 31 Oct he named two of these ideas as key, more than the research: levels of specificity, and an MIS that works on one market alone. His exact words in that message are not in the transcripts read here, so they are not quoted. His earlier words on both ideas are in groups F and G.

### A. It reads and publishes. Units pick. Nobody depends on it.

- "What I wanted was the MIS just reads and outputs." (28 Oct, transcript-2026-10-20-to-28.md:1951)
- "It doesn't mean that if the MIS is not working, it doesn't mean that these bots won't trade. They will, okay?" (29 Oct, transcript-2026-10-29-to-30.md:135)
- Agreeing that the MIS reads and publishes and no unit needs it: "Number two, I agree with it. I've been saying this over and over again" (31 Oct, transcript-2026-10-30-to-31.md:1105)

**Kept.** Each unit lists the readings it uses and what to do without them. A build test stops the MIS and checks that a dummy unit still enters a trade.

### B. It amplifies a unit. It never switches one on or off.

- "So in other words, it can be amplified by the MIS." (29 Oct, transcript-2026-10-29-to-30.md:135)
- "it should take in information from, let's say now, an MIS cluster" (29 Oct, transcript-2026-10-29-to-30.md:135)

**Kept, measurement open.** The MIS publishes a board of which markets are in which condition now. It never turns a unit on or off. How much it lifts a given unit is not measured yet. That test runs in QMB once trades carry the reading they saw at entry.

### C. Context is what it senses. Find the mean-reverting markets.

- "I think context is what the MIS is meant to be sensing" (29 Oct, transcript-2026-10-29-to-30.md:135)
- "the whole point of the MIS, okay, should be to find mean reverting markets at that time" (29 Oct, transcript-2026-10-29-to-30.md:135)
- "Context is what the market, I believe, should be using, or that should be producing." (30 Oct, transcript-2026-10-29-to-30.md:789)

**Kept, with a limit the research found.** Every class gets a trend-against-range reading (his meaning of regime), built from the efficiency ratio, the variance ratio and Hurst. On 1-minute and 5-minute bars a trend or a mean reversion takes hours to show. So this reading works as a list for the session or the day, not as a per-trade signal.

### D. Style first, then timeframe, then the data a market offers.

- "we need a trading style, firstly" (29 Oct, transcript-2026-10-29-to-30.md:219)
- "we are going to consider variables that each market has" (29 Oct, transcript-2026-10-29-to-30.md:219)
- "a Forex one is different from a futures one, but the time frame or the time frames are the same" (29 Oct, transcript-2026-10-29-to-30.md:219)
- "So it means the MIS for a market that has all that data is different." (29 Oct, transcript-2026-10-29-to-30.md:219)

**Kept.** Every reading states its clock (tick, bar, session or day, which follows the style and timeframe) and the least data it needs (bars, quotes, depth, a trade tape, or funding fields). A market gets only the readings its data allows. A market with less data gets fewer readings, never wrong ones.

### E. A scalper's MIS holds fast indicators, chosen by research.

- "you are not going to put an HMM inside a scalper's MIS" (29 Oct, transcript-2026-10-29-to-30.md:219)
- "But you can put multiple indicators inside a scalper's MIS." (29 Oct, transcript-2026-10-29-to-30.md:219)
- "The MIS for a scalper should be from the research. We shouldn't assume that the HMM will work." (29 Oct, transcript-2026-10-29-to-30.md:219)
- "for us to find a market that is mean reverting, I don't think we are going to require a BOCPD" (29 Oct, transcript-2026-10-29-to-30.md:219)

**Kept, sharpened by the research.** The defaults ship no HMM. The fast readings are ratios against usual levels plus small change detectors, which the research found fast enough for a scalper. HMMs and other regime models belong on the day clock, later, through the Lab.

### F. Per class, and down to one market.

- "categorizing by instrument type" (28 Oct, transcript-2026-10-20-to-28.md:1999)
- "we can design an MIS that fits, should I say, a futures market, then an MIS that also fits a Forex market" (29 Oct, transcript-2026-10-29-to-30.md:135)
- "you can't simply say that the fix isn't a separate MIS per market. That's your opinion." (29 Oct, transcript-2026-10-29-to-30.md:219)
- "remember, we are literally working with almost every instrument now" (31 Oct, transcript-2026-10-30-to-31.md:1264)

**Kept.** Every instrument class gets its own default pack of readings. Each reading compares a market with that market's own history, at the same minute of its own session. An MIS for one market alone is the same MIS set to read one market. **Open.** Whether a market whose habits differ from its class should get its own pack version is a Lab question for later.

### G. Levels of specificity.

- "It means that specificity is simpler." (28 Oct, transcript-2026-10-20-to-28.md:1999)
- "is making rather that unit more specific. So it means the amplification is now more specific." (29 Oct, transcript-2026-10-29-to-30.md:135)
- "if it's using the same things as in those in the MIS, it means it is already specific" (29 Oct, transcript-2026-10-29-to-30.md:219)
- "Now I also think there are times whereby we can already attach a specific instrument or specific market to a unit." (29 Oct, transcript-2026-10-29-to-30.md:219)

**Kept.** Specificity is a setting, not a separate design. The same reading code reads everything, one class, or one market. A unit whose rules already state its context needs little from the MIS. For that unit the MIS shows where else that condition holds now. **Open.** Agents in the slow lane may propose a more specific variant from MIS history. Making it trade stays his click.

### H. What goes in decides what comes out.

- "the quality of what's processing information inside the MIS is directly proportional to the quality of output" (29 Oct, transcript-2026-10-29-to-30.md:219)
- "Remember, we also had market physics also that was there, because that alone also provides more information" (29 Oct, transcript-2026-10-29-to-30.md:219)
- "there is also a way you can calculate mean reverting using specific things like order flow" (29 Oct, transcript-2026-10-29-to-30.md:135)
- "Maybe the correlation ledger can take the output also" (29 Oct, transcript-2026-10-29-to-30.md:219)

**Kept.** Hurst, the variance ratio and the efficiency ratio ship with minimum-history rules. The mean-reversion readings use mid prices and a check for bid-ask bounce. Order-flow readings ship where a venue has the data. On cTrader they are broker-side estimates and say so on every record. Every record names the data it used and any fallback it took. The MIS publishes dispersion (how far related markets drift apart) and crowding counts (how many units sit on one market). The risk side decides what to do with them.

### I. Defaults now, his models later. It grows.

- "Let's make defaults for the MIS. I'll train the models when I can." (31 Oct, transcript-2026-10-30-to-31.md:1264)
- "So the MIS itself is incomplete." (31 Oct, transcript-2026-10-30-to-31.md:1264)
- "we can retrain a version of the MIS that can also see such" (29 Oct, transcript-2026-10-29-to-30.md:219)
- "the MIS can be upgraded as the agent see fit, obviously with my approval" (28 Oct, transcript-2026-10-20-to-28.md:1951)
- "grow its own limbs" (29 Oct, transcript-2026-10-29-to-30.md:135)
- "this part of training an HMM per market is not viable in any way, shape or form" (29 Oct, transcript-2026-10-29-to-30.md:219)

**Kept.** Every class gets defaults that need no training. Behind each reading sits a slot for a model. Models train in the Lab, run in shadow, and go live only on his yes. They are pooled by class or by underlying, never one per market. Settings from papers are starting points, refit on his own data.

### J. Agents work in the slow lane and read the MIS's logs.

- "They should be using the logs from the MIS. Those are two different things." (31 Oct, transcript-2026-10-30-to-31.md:903)
- "All they are trying to do is literally replicating the MIS's thing." (29 Oct, transcript-2026-10-29-to-30.md:325)
- "The MIS gives us low label per session or per day" (29 Oct, transcript-2026-10-29-to-30.md:325)
- "we've seen and confirmed that these markets are mostly mean reverting" (29 Oct, transcript-2026-10-29-to-30.md:219)

**Kept.** Agents read reading history through one read tool, never a live model. Before a session an agent writes its own dated reading in the MIS's words, and it is scored later against what happened. Where the agent and the MIS disagree, the examples go to him to improve the MIS. Agents never feed the fast lane. The slow readings give the per-session and per-day list he described. **Open.** Whether his and the copilot's weekly labels may train models (in shadow only) is his call later.

### K. Questions before answers. The MIS gets its own lens.

- "We should instead pose questions that are meant to be answered with the workflow." (29 Oct, transcript-2026-10-29-to-30.md:219)
- "we should have structure and intention, but it's not set in stone" (30 Oct, transcript-2026-10-29-to-30.md:789)
- "So don't combine the MIS work with the QML work and the unit work." (31 Oct, transcript-2026-10-30-to-31.md:903)
- "We haven't talked about the MIS. What models are we using?" (31 Oct, transcript-2026-10-30-to-31.md:904)
- "But the MIS, I still don't know what we are going to be using inside there." (31 Oct, transcript-2026-10-30-to-31.md:1264)

**Kept.** The MIS has its own design file, with plain answers to his questions on where it lives, its screen, its readings, training and data. The questions still open are in section 6. Every default is a starting value he can change.

### L. Market state as a source of strategies.

- "there is a huge possibility we can discover market inefficiencies with only that" (28 Oct, transcript-2026-10-20-to-28.md:1999)

**Open, with evidence.** The research found real patterns tied to market state, such as momentum into the close in 60+ futures and extreme perps funding. They fade once known (section 3). Each would become a unit through the Lab and QMB, with a reason it should last and a watch for decay.

### M. The node sets it up.

- "setting up the MIS, and what everything the unit needs to trade autonomously" (31 Oct, transcript-2026-10-30-to-31.md:1562)

**Kept.** A trading node installs its MIS with it, in the same one-click setup. His PC runs its own instance.

## 3. What the research found

All lag numbers come from simulations on made-up 1-minute bars, set to one false alarm per 10 trading days. Real markets have fat tails and daily rhythms, so real lags will be somewhat longer. No real price data has been replayed yet.

1. **Volatility shows in minutes. Direction takes hours.** A 50% jump in volatility shows in about 8 bars when read from bar ranges, and about 27 bars from closes. He had flagged 44 minutes ("this 44 minute thing is huge", 29 Oct, transcript-2026-10-29-to-30.md:325). Source: `research/22-mis-sensor-speed.md` §2.
2. **Trend or mean reversion on 1m and 5m is a session or day list.** A strong trend takes about 4 hours to show, and strong mean reversion about 4 to 5 hours. Weak versions take a day or more. Bar size changes the bar count, not the hours. Source: `research/22-mis-sensor-speed.md` §2 and §3.
3. **Only the label known at entry is honest.** With 2-hour states, gating trades by the at-entry label gave no gain in total. A label computed afterwards claimed a 76% better edge per trade. With 2-day states the honest label kept 81% of the perfect-knowledge edge. The rule of thumb is that a state must last at least 5 times the reading's window. Source: `research/22-mis-sensor-speed.md` §4.
4. **Bid-ask bounce fakes mean reversion.** With heavy bounce, price-only mean-reversion readings false-alarm 10 to 130 times more often than designed. Mid prices and a bounce check fix it. Source: `research/22-mis-sensor-speed.md` §2.
5. **Hurst needs a long history.** Below about 1,000 points it means little. That is 17 hours of 1-minute bars. Source: `research/37-mis-academic.md` §1 (sample-size studies).
6. **Order flow is fast and short-lived.** Book and trade-flow pressure predict the next seconds and are gone by 30 to 60 seconds. Spot forex has no tape. Its tick count tracks real traded volume at the hourly scale (correlation 0.96 to 0.99, one vendor study). Source: `research/37-mis-academic.md` §1 and §3.
7. **Shared words carry across markets. Trained models do not.** Book features rank the same across crypto assets of very different size. Fitted models did not transfer from one crypto asset to another, only between the spot and futures of one asset. Source: `research/23-mis-organisation.md` short answer 2.
8. **Gold's price forms at COMEX futures.** COMEX leads price discovery with about a tenth of London's volume. So the research backs reading the futures for a gold CFD. Source: `research/37-mis-academic.md` §1 and §3.
9. **Patterns tied to market state are real, and they fade.** Published stock predictors lose 58% of their returns after publication. Forex technical rules faded over about a decade. Source: `research/37-mis-academic.md` §7.
10. **HMMs flip falsely.** They detect changes as fast as penalised jump models but with many short false switches. They belong on the day clock. Source: `research/37-mis-academic.md` §1 and §6; `research/22-mis-sensor-speed.md` §6.

## 4. What the build ships first

The MIS on his PC lands in stage 5 of the 8-stage build, after QML and the dictionary. The MIS beside each trading node lands with the node in stage 7. Readings and their code ship first. Models come later.

### What every reading gives

Each reading publishes three things for a market: a value, where that value sits against the market's own usual for that minute of its session, and a word (for example quiet, normal, elevated, stressed). Each record also carries its health word: fresh, stale, degraded (a fallback was taken), thin (too little history), shadow, or retired. Records are never rewritten. A correction is a new record linked to the old one.

The word regime means trend against range. The old volatility labels in the shipped code are renamed volatility state. That rename is his to veto.

### Readings every class gets

- Volatility against usual, from bar ranges.
- Volatility state (quiet, normal, elevated, stressed).
- Spread against usual, and a spread quality score.
- Tick rate against usual (never called volume).
- Quote gaps, feed state and failing sensors.
- Liquidity stress.
- Small change detectors (CUSUM on returns, two-scale volatility, a Kalman level).
- Efficiency ratio.
- Variance ratio and Hurst (at least 1,000 points, mid prices, bounce check).
- Trend against range.
- Calendar states (session windows, holidays, dead zones).
- On his PC only: currency strength, dispersion, crowding counts, and dated readings between pairs.

### What each class adds

| Class | Adds on top of the shared readings |
| --- | --- |
| Forex | Depth against usual and depth imbalance from cTrader's broker book; order-flow pressure as a broker-side estimate; currency strength across pairs |
| Futures | Roll state, days to expiry, price-limit state, sessions in the exchange's time zone; open interest at end of day; depth and real order flow once he switches on an exchange data feed (a working placeholder ships now that reads files he drops in a folder); index futures get the cash-open readings; gold futures get the fix windows |
| Metals | London fix windows (10:30 and 15:00 London); broker depth; order-flow estimate |
| CFDs | Commodity CFDs and stock CFDs take the shared readings; stock CFDs add the cash-open readings; futures-style CFDs add the roll state |
| Indices | Cash open, opening drive, initial balance, overnight range; broker depth and order-flow estimate on index CFDs |
| Crypto perps | Real depth and trade flow (free from Hyperliquid, Binance and Bybit); funding state and its extremes; open interest change; mark against last; basis; activity sessions in place of clock sessions; index perps get the cash-open readings and gold perps the fix windows |

Crypto spot gets the shared readings plus real depth and trade flow, with activity sessions.

### Where it runs

- **On each trading node.** The node itself runs the readings that need every tick: spread, quote gaps, feed state, tick rate, depth and order flow. Only the node holds the live connection, and some of these are its own safety guards. A small MIS app beside the node runs the bar, session and day readings for that node's markets.
- **On his PC.** The MIS app runs the slow readings for markets no node trades, the readings that compare markets, the board, and any model in shadow. It works alone on Library history, with no server needed.
- **One writer per reading.** His PC never recomputes a reading a node already publishes for its own markets.
- **Everything comes home.** Readings from every node land in the Library, so QMB, the copilot and his screens see the same history.

### What its screen shows

- **On each node's page, a Readings section.** It shows that node's markets and their readings now and recently, each with its health word, and a badge when a unit had to use a fallback.
- **On his PC, the MIS tab.** It shows every market and every reading, with its version, its clock, its health word, and which units read it with which fallback. It has a history chart with each change of state. A default marker sits on readings a model may replace. A shadow model's record sits beside the default, with his yes to make it live.
- **Through the copilot.** He can ask what the MIS read for a market last week and get the stored answer.

### How units use it without depending on it

- A unit lists the readings it reads. For each one it names a fallback: compute the reading itself, treat it as absent, or take no new entries.
- Readings are shared code. A unit, QMB and the MIS run the same code, so a backtest and live trading see the same number. A replay of one recorded day checks this to the last digit.
- A reading older than its freshness limit counts as absent: 2 seconds for tick readings, one bar, one session or one day for the others.
- With no board, a unit trades every market he admitted, on its own conditions.
- A test stops the MIS and checks that a dummy unit still trades.

## 5. What comes later, through the Lab

- **Models.** Regime models such as HMMs, jump models and mixtures, on the day and session clocks. They are pooled by class or by underlying, because models fitted on one market did not carry to another. Settings from papers are starting points. His and the copilot's dated labels can become training targets, in shadow only, if he agrees.
- **Training.** The Lab's training slot on his PC is built but has never run. It has a GPU slot, a disk check, exact data partitions and fingerprints. A model trains on Library history and lands with its data fingerprint, code version and seed. Refits run monthly in shadow.
- **Data.** Library history, which he downloads, plus the live feeds that come home from each node. Real futures order flow arrives when he switches on an exchange feed. Outside data, such as fundamentals and news, has no default reading yet.
- **How a model replaces a default.** A model is a reading with its trained weights pinned by fingerprint. It runs on his PC beside the default and writes shadow records. He compares the two on the MIS tab and says yes. The next configuration names the model. The reading keeps its name and shape, and only its version moves, so no unit changes. Old records keep the version they were made with.
- **New readings from agents.** Agents may propose a new reading. It runs in shadow and goes live only on his yes.
- **Proof it helps.** In QMB a unit is replayed twice: once with readings stamped at entry, and once with the same readings computed afterwards. The gap shows how much a backtest would overstate the MIS's value for that unit.

## 6. Open questions worth his time later

1. **Futures data.** Should he pay for an exchange feed? It gives real futures order flow, and lets a gold CFD read the COMEX tape. The other choice is to stay on broker-side estimates. A placeholder ships either way.
2. **The word regime.** It now means trend against range, and the old volatility labels become volatility state. Keep it, or veto it.
3. **His own labels.** May the market labels he and the copilot write each week train models, in shadow only? His example: "these markets are mostly mean reverting" (29 Oct, transcript-2026-10-29-to-30.md:219).
4. **One market apart.** When a market behaves unlike its class, does it get its own pack version, or only its own usual levels (which every market already has)?
5. **The board on the server.** Should units on a node see which of their markets the board favours now? This build ships it last and as optional. Without it, units trade every admitted market on their own conditions.

## 7. Data table for the chart

Speeds are for 1-minute bars at one false alarm per 10 trading days. The fast case is a strong change (a 50% volatility jump, a strong trend, strong mean reversion) or the faster venue. The slow case is a weak change, the slower venue, or the 90th percentile where no weak change was run. On 5-minute bars, volatility readings need the same number of bars, so five times the minutes; direction readings take about the same hours. Blank cells have no number to chart. The basis column says where each number comes from: simulated (research 22's scripts), design (the MIS design file), or research (a cited study).

| Reading | Market classes | Clock | Reacts in (plain) | Minutes, fast case | Minutes, slow case | Basis | Fallback when data is missing |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Volatility against usual (bar ranges) | all | bar | about 8 bars | 8 | 16 | simulated, median and 90th percentile | closes over 30 bars, which react in about 27 bars |
| Volatility from closes (the fallback) | all | bar | about 27 bars | 27 | 69 | simulated, median and 90th percentile | reading absent; the unit takes its own fallback |
| Volatility state | all | bar, session | follows volatility against usual | 8 | 16 | design, from the reading above | same as volatility against usual |
| Change detectors (CUSUM and similar) | all | bar | about 29 bars for a volatility jump; hours for a drift | 29 | 61 | simulated, median and 90th percentile, volatility jump | reading absent; the unit takes its own fallback |
| Spread against usual | all | tick | seconds | 0.03 | | design, 2-second freshness limit | stale after 2 seconds, then absent |
| Tick rate against usual | all | tick | seconds to a few minutes | 0.03 | | design, 2-second freshness limit | stale after 2 seconds, then absent |
| Quote gaps and feed state | all | tick | at once | 0.03 | | design, 2-second freshness limit | a stale feed stops new entries on the node; exits and stops keep working |
| Liquidity stress | all | bar | one bar | 1 | | design | reading absent; the unit takes its own fallback |
| Efficiency ratio (sees trend only) | all | session | about 4.4 hours strong; about a day weak | 264 | 1530 | simulated, 240-bar window | marked thin until it has enough history |
| Variance ratio (sees mean reversion only) | all | day | about 5 hours strong; about 18 hours weak | 318 | 1072 | simulated, 240-bar window | uses mid prices; blocked when bounce is heavy; thin until enough history |
| Hurst | all | day | needs at least 1,000 points; flagged under 4,000 | 1000 | 4000 | research, sample-size studies | thin, with no value shown, under 1,000 points |
| Trend against range (his regime) | all | session, day | about 4 to 5 hours strong; a day or more weak | 264 | 1530 | inferred from its two parts | thin when either part is thin |
| Calendar states | all; crypto uses measured activity sessions | calendar | known in advance | 0 | | design | the instrument's own calendar |
| Depth against usual and imbalance | forex, metals, index CFDs (broker book); perps and crypto spot (real); futures with a feed | tick | seconds | 0.03 | | design, 2-second freshness limit | absent where no book exists |
| Order-flow pressure | all (broker estimate on cTrader; real on perps; futures with a feed) | tick | ticks; its signal lasts 30 to 60 seconds | 0.03 | | research, order-flow studies; design freshness limit | trade tape, then depth imbalance, then tick rule, then range pressure, each step recorded |
| Funding state and extremes | crypto perps | bar, session | at each settlement: hourly on Hyperliquid, every 8 hours on Binance | 60 | 480 | research, venue schedules | absent on markets without funding |
| Open interest change, mark against last, basis | crypto perps; open interest at end of day on futures | bar, session | one bar on perps; one day on futures | 1 | 1440 | design | absent where the field does not exist |
| Roll state, days to expiry, price limits | futures, futures-style CFDs | calendar, session | known in advance | 0 | | design | the exchange calendar |
| Cash open, opening drive, initial balance, overnight range | indices, stock CFDs, index futures, index perps | session | known once its window has passed; a measured move, not a guess | | | design; research on first and last half-hour returns | reading absent; the unit takes its own fallback |
| London fix windows | metals: gold CFD, gold futures, gold perps | calendar | known in advance | 0 | | design | the calendar |
| Currency strength, dispersion, crowding counts | all, on his PC only | session, day | not yet measured | | | none yet | computed on his PC from Library history; a market without history is left out |

A unit names one of three fallbacks for each reading it uses: compute the reading itself, treat it as absent, or take no new entries.
