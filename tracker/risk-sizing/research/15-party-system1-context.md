# 15: Party and brainstorm on System 1 → System 2, logic and market context

Ideas only. Nothing here is decided, and nothing is folded into architecture. 2026-10-28, one agent, every voice played in one context, no subagents.

**Method.** `bmad-party-mode` (13 voices, nine rounds) and then `bmad-brainstorming` (six techniques, run headless because no operator was present). This run was read-only and wrote only this one file, so the brainstorm memlog was not kept. The ideas live here.

**Seed read, in order:** `operator/2026-10-28-discussion-notes.md`, `operator/2026-10-28-router-system1-system2.md`, `STATE.md`, `research/10-hermes-stats-goldmine.md`, `C:\Users\Mubarak\Desktop\Stats\schema\strategy-dna.md`, `C:\Users\Mubarak\Desktop\Stats\dictionary\` (the context file in full, the rest by grep), and parts of `research/02`, `05`, `06`, `07`, `13`.

**Labels.** **CHECKED (path)** means I read it there. **INFERRED** means it is my reasoning or a panel voice's. Numbers marked *(cfg)* are starting points and are configurable, never caps.

---

## 0. The short version

1. **"Most of this already exists" is half true.** CHECKED: the four pillars (location, context, trigger, confirmation) sit at `Stats\schema\strategy-dna.md` lines 126-140, and the context file `Stats\dictionary\context-regime-and-intermarket\context-filters-confirmations.md` holds **66 entries, not ~69**. The 69 `##` headings include three that are not entries: Coverage, Deduplication and Unresolved. What exists is the **requirement vocabulary**: names and definitions of conditions. What is missing is the **measurement side**:
   - The dictionary has zero hits for Hurst, variance ratio, efficiency ratio, HMM, BOCPD, GARCH, open interest or real rates (CHECKED, grep over `Stats\dictionary\`).
   - Six of ten dictionary folders are empty, including `time-sessions-and-events` and `indicators-and-transformations` (CHECKED, `ls`).
   - The 13 mini-KB folders hold only READMEs, 1,839 bytes in total (CHECKED, `Stats\knowledge\*\README.md`).
   - The library was scoped to forex and crypto spot (CHECKED, `strategy-dna.md` "Markets").
2. **The dictionary itself asks for tonight's answer.** Its unresolved question 3 reads: `market-regime` "has no standardized state taxonomy … would need a decision" (CHECKED, context file, "Unresolved taxonomy questions"). The shared context dimensions are that decision.
3. **The strongest single idea: "broadly wins" should mean context lift, not instrument count.** The unit wins when its context is present and does not when it is absent, and that holds on most independent instruments. That tests the unit's actual claim. A breadth count alone rewards 7 USD pairs that are really one bet.
4. **The parent always exists, as an abstract record.** A System 1 parent that fails broadly is like an abstract class or a genus: it groups its children, carries the try count and the context claim, and receives "upstreamed" improvements. It never trades on its own.
5. **Logic vs calibration has a clean line, taken from August's edit operations** (CHECKED 10 §5.1). Changes to the graph, roles, timing, entry, exits or context pillar make a new System 1 variant. A number moved inside its declared range is calibration, which makes a System 2 specialisation or a try. **New line proposed:** *terrain gates* (gold fix windows, rollover, roll week) come from the instrument spec, not the logic, so a child may carry them without becoming new logic.
6. **The skeptic's hard fact:** at 1m, a trend or mean-reversion state takes about 480 bars (~8 hours) to detect (CHECKED `research/05` short answer 2), and 07 rejected "regime labels as scalper entry gates" (CHECKED `07-funnel.md:712`). So the System 1 scan ("20% of 100 markets are mean-reverting") works for **placement over a session or a day**. It does not time entries. Fast context means volatility, spread, liquidity and cost measured against the normal level for that hour.
7. **One sensor kind, three engines.** Indicators, statistical tests and models are all "sensors" with the same output shape: value, label, confidence, lag tier and version. They are the same library code in the Lab, QMB and live. A sensor earns a place only if it *predicts a unit's edge*. The medical analogy is a companion diagnostic, which qualifies by predicting a patient's response to a drug.
8. **Seven questions for the operator** are in §5: the meaning of "broadly", a middle (class) level, the terrain-gate line, live expansion, news units against the global news kill switch, the first asset classes to research, and how far sensor approval reaches.

---

## 1. The panel

| Voice | Who | Pet topic |
| --- | --- | --- |
| **Kofi** | FX scalper, London desk, 12 years | Spread, session handovers, "seven USD pairs are one trade" |
| **Delphine** | Gold trader | Fix windows, NY open, the dollar and real rates |
| **Marcus** | Futures day trader (ES, NQ, CL) | Real volume, VWAP, open auction, roll week |
| **Yuki** | Crypto perps trader (Hyperliquid, CEXs) | Funding, open interest, liquidation cascades, 24/7 |
| **Rania** | News trader | Calendars, surprise vs consensus, slippage on the spike |
| **Ines** | Quant researcher on a desk that studies market inefficiencies per asset class | "Context-first" research, the inefficiency atlas |
| **Priya** | Statistician who fears overfitting | Tries, pre-registration, shrinkage |
| **Tomasz** | Market-microstructure expert | Deseasonalising, information per bar, order types |
| **Leo** | ML and genetic-search engineer | Genomes, crossover, XGBoost, quality-diversity |
| **Hana** | QML library designer | Deep modules, JSON schemas, one name per thing |
| **Otto** | AI-agent designer | Workflows, skills, what an agent can decide on its own |
| **Vera** | The skeptic | "Show me it beats doing nothing" |
| **The Operator** | His own voice, from the 28 Oct dictation | Breadth, compounding, System 1 live |

Running bits that build across rounds: Kofi and Yuki agree that "breadth is mostly one bet". Priya and Leo fight over generation versus tries. Vera keeps a tally of "things that describe the past".

---

## 2. The rounds

### Round 1. System 1 → System 2: the default parent, what "broadly wins" means, and the failed parent

**The Operator:** System two makes sense before live. System one is the one I want live. And every System 2 should have a System 1 parent by default, even when the parent doesn't win broadly.

**Hana (QML):** Then the parent is an abstract class. It has the logic and the context claim but no home instrument. A System 2 is the parent plus one instrument binding plus a calibration table. In the spec, the parent's instrument field reads "any". The child names one, for example `XAUUSD`, and links back with a `specialises` edge.

**Vera (skeptic):** An abstract parent that never trades is a folder with a name. Why keep it?

**Hana:** For four reasons. It carries the family's try count. It holds the context claim the children inherit. It receives fixes the children discover. And it is where a new instrument's first settings come from.

**Priya (stats):** And it is the prior. Cells too thin to judge alone borrow strength from their parent (CHECKED `research/05` short answer 11: about 270 trades for a 0.1R edge at 95%, ~550 for a skewed 70%-win scalper). The parent is the pooled estimate and each child shrinks toward it. A parent is not "a unit that failed". It is the average of its children.

**Ines (quant desk):** Right. Turn it around: the parent's broad record *is* the pooled posterior of its children. If it fails broadly, the children still exist; the parent just says "this logic is narrow".

**Kofi (FX):** Before you define "broadly", know this: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF and USDJPY are seven tickers and maybe two bets. A mean-reversion scalper that "wins on 7 of 7" may have won on the dollar once.

**Yuki (perps):** Same in crypto. A hundred and fifty perps, one BTC beta. "Wins on 40 coins" can be one bet.

**Priya:** So breadth counts **independent** instruments. Use effective N, the number of uncorrelated bets you would need to get the same spread. That is the same idea as the fundamental law of active management: skill × √(independent bets) (INFERRED, standard quant result). The operator's "compounding through breadth" is exactly that law, and it punishes correlated breadth.

**Vera:** Second problem: costs. A scalper with a 2-pip target dies on GBPJPY's spread. "Fails broadly" may only mean "fails where costs eat it".

**Tomasz (micro):** Then judge breadth in R after each instrument's own measured costs, and drop instruments where cost ÷ target is above the unit's limit *before* the test. That is a terrain filter, not a result. The cost ratio is the master state for scalpers (CHECKED `research/05` line 409).

**Ines:** Here are three definitions of "broadly wins". I'd pick the third.

- **B1, count.** It passes the unit's own bar on at least 60% *(cfg)* of a pre-registered universe of at least 12 instruments *(cfg)* across at least 3 classes *(cfg)*, with effective N of at least 6 *(cfg)*.
- **B2, pooled with no carrier.** Pooled expectancy is at least +0.10R after costs and after the tries correction *(cfg)*. The median instrument is above 0R. No single instrument contributes more than 25% of total R *(cfg)*.
- **B3, context lift.** The unit claims "I win in context X". So test that edge in X minus edge outside X is at least +0.05R *(cfg)*, positive on at least 60% of independent instruments *(cfg)*, with pooled in-context expectancy above 0 after costs. This tests the claim itself, not the instrument list.

**Priya:** B3 is the only one that makes the MIS matter. If the edge does not depend on context, the MIS is decoration and you have an always-on unit. That is fine too, but say so.

**Vera:** B3 needs the MIS labels on backtest trades. QMB attaches none today and stores results in money, not R (CHECKED `research/05` short answer 12, `research/01` §7.9). So B3 is blocked on two missing fields.

**Hana:** Then those two fields are foundations, not features. Noted.

**Delphine (gold):** You're all talking as if the parent comes first. In my world the child comes first. Someone says "I trade the NY-open sweep on gold". That is a System 2 seed. The parent is something you *derive* by asking what the logic is without gold.

**Hana:** Agreed. The parent is created by default, but often *after* its first child. Birth order is not rank.

**Leo (ML):** The old vault already had this order: young units were broad, mature ones were session specialists (CHECKED `research/07a-funnel-party.md:568`, "young → mature session specialists"). Tonight's version flips who is born first, but the shape is the same.

**The Operator:** So a parent that fails broadly still lives?

**Priya:** As a record with a status. I'd use five (INFERRED):
- `unproven`: not yet tested broadly;
- `broad`: passes B3 (or the chosen test) across classes;
- `class-broad`: passes inside one class only;
- `narrow`: wins on 1-3 instruments, which are its children;
- `refuted`: no winner anywhere, kept in the failure ledger.

The operator asked for failures to be kept: "a ledger … when it failed, how it failed" (CHECKED `research/10` §2.9).

**Vera:** And a `refuted` parent with live children? Contradiction.

**Priya:** No. It means "the logic as stated is not general". The children's edge is local and should be judged locally, with stricter shrinkage, because they lack a broad parent to borrow from.

**Leo:** The refuted parents are my best training data: negative examples for the generator.

*Agreements:* the parent always exists as a record; it is the pooled prior for its children; breadth counts independent instruments after each one's costs; statuses replace a pass/fail switch.
*Live disagreements:* B1/B2 (simple, reportable) against B3 (tests the claim, blocked on QMB fields); whether the parent ever trades by itself or only through children; whether a class level belongs between parent and child (Kofi: yes, "FX-majors MR scalper" is a real thing; Hana: tags, not a level).

---

### Round 2. What "logic" is, and logic change vs calibration

**Hana:** The DNA already answers most of it. Logic is parts C, D, E and F of the A-I record (CHECKED `strategy-dna.md` lines 33-43):
- **C:** which dictionary primitives are used.
- **D:** the role and timing each primitive gets.
- **E:** the graph that combines them.
- **F:** which exit slots exist.

What is *not* logic: the **coordinates**, meaning instrument, timeframe and session placement, and the **numbers** inside declared ranges. August said it plainly: "Pair, session, and regime are normally challenge coordinates, not tunable strategy factors" (CHECKED `research/10` §2.10, quoting `EXP`).

**Ines:** So the four pillars plus entry semantics plus exits are the logic. The context pillar is part of it. The context claim is logic.

**Hana:** Yes. Proposal: a **logic fingerprint**, a hash of primitives, roles, timing, graph operators and exit-slot kinds, excluding numbers and coordinates. If the fingerprint changes, it is a new System 1 variant. If only numbers move inside their ranges, it is calibration.

**Priya:** Careful. A 5-bar MA and a 200-bar MA are the same fingerprint, but one is a noise filter and the other a trend filter. Numbers can change the nature of a part.

**Hana:** That is why the *range* is part of the logic. August's mapping already says so: `replace_parameter` inside the range is a try; outside it, it is a new version (CHECKED `research/10` §5.1 table). A child may calibrate only inside the parent's range.

**Delphine:** My gold child avoids 10:30 and 15:00 London because of the LBMA auctions (CHECKED `research/02` §3.2). That is a filter. By your rule, it is a new logic.

**Kofi:** And my EURUSD child skips the rollover minutes. Same problem.

**Tomasz:** Those are not *state* filters. They come from the instrument's calendar. Split context into two kinds:
- **state**, which the market does: trending, volatile, liquid;
- **terrain**, which the instrument is: its hours, fixes, rollover, roll week, contract size.

Terrain gates come from the typed instrument spec (CHECKED `research/04`, via STATE: "Any instrument = typed instrument specs"). A child inherits them for free, and they never change the fingerprint.

**Vera:** Nice line. Who polices it? An agent will call everything "terrain" to avoid a new variant.

**Otto (agents):** The check does. A terrain gate may only reference instrument-spec fields: calendar, fixes, roll dates, session hours. A gate that reads price or a sensor is state, so it is logic. `qml.check` refuses a "terrain" gate that reads price.

**Marcus (futures):** What about order type? A passive limit entry and a market entry are different edges for a scalper.

**Tomasz:** Entry semantics is logic. Trigger ≠ order (CHECKED `strategy-dna.md` line 137). Maker vs taker changes the cost side completely.

**Yuki:** But post-only exists on Hyperliquid and not everywhere. Isn't that terrain?

**Tomasz:** The *availability* is terrain. The *choice* is logic. If the venue cannot do it, the unit cannot go there. That's a terrain refusal, not a calibration.

**The Operator:** And a logic change can come from combining several System 2s?

**Hana:** Yes, in two ways. First, **upstreaming**: two children each discover the same tweak, say "skip the first 5 minutes after the open", and the tweak is lifted into the parent as a new System 1 variant with `derived-from` the parent and `informed-by` both children. That is like a patch going upstream from two forks. Second, **composites**: parts of two families joined through named ports (`setup_signal`, `entry_signal`, `invalidation_signal`, `exit_signal`, `regime_filter`). CHECKED `research/10` §2.3: designed in August's `PKG`, not carried into the 1 Sep build.

**Priya:** Upstreamed tweaks are found *in-sample on the children*. The new parent must be judged on instruments that neither child traded. Otherwise you have tested your own discovery.

**Leo:** And sizing? The unit sizes itself (correction 2).

**Hana:** The sizing *method* is logic, because it is a module in the unit. The sizing *numbers* are calibration and self-calibrate from the journal. Changing fixed-fractional to volatility-scaled makes a new variant; the risk percentage moving is calibration.

**Vera:** Tally: that is now three kinds of "not logic": coordinates, numbers in range, and terrain gates. I'll allow it. It's still simpler than one undefined word.

*Agreements:* logic = pillars + roles + timing + graph + entry semantics + exit slots + sizing method; the declared ranges belong to the logic; coordinates and in-range numbers are calibration; edit operations decide automatically (CHECKED `research/10` §5.1).
*Live disagreements:* terrain gates in children (Tomasz and Delphine: yes; Vera: a loophole unless enforced); whether a timeframe change is a coordinate (Hana) or new logic (Kofi: "1m and 1h versions behave like different animals, because costs dominate one and not the other").

---

### Round 3. Market context: a firm definition, the dictionary map, registering new sensors

**Ines:** Draft definition: **market context is the measured state of one instrument at one timeframe at one moment, in a shared vocabulary of dimensions. Each asset class measures it with its own sensors.** Context is the state, which changes minute to minute. Terrain is the instrument, which changes rarely.

**Tomasz:** The five shared dimensions from the notes, each with a horizon tag:

| # | Dimension | Measures | Fastest honest horizon |
| --- | --- | --- | --- |
| D1 | Direction and efficiency | trend vs mean reversion vs noise | hours to days (CHECKED `research/05` short answer 2: ~480 bars at 1m for a drift) |
| D2 | Volatility | now vs the usual for this hour | minutes (CHECKED `research/05` §1.1 T1/T2) |
| D3 | Participation and liquidity | spread, depth, tick rate, volume vs the usual | seconds to minutes |
| D4 | Time and session | which session, is it live today | zero lag (calendar) plus a measured "is it active" |
| D5 | Events | scheduled news, roll, funding, expiry, fixes | zero lag (calendar) |

**Kofi:** Add **D6 cost**: live round-trip cost ÷ the unit's target. For a scalper it decides everything.

**Vera:** Cost is terrain times state. If you put it in context, the MIS ends up computing per-unit numbers.

**Tomasz:** Then measure the cost *state* per instrument (spread and slippage vs normal) in D3, and let the unit divide by its own target. The MIS publishes market facts; the unit does its own maths.

**Yuki:** **D7 crowding** is missing: funding, open interest, liquidations. In perps it's the biggest context there is.

**Marcus:** For futures, crowding is open interest change and the commitments-of-traders data. Yes to D7, but it's class-specific.

**Delphine:** And **D8 intermarket**: the dollar, real rates, risk-on and risk-off. Gold without the dollar is half a market. The dictionary already has five intermarket entries (CHECKED context file coverage table: currency-pair-correlation, dollar-index, currency-strength, intermarket-risk-regime, safe-haven-demand).

**Hana:** So five core dimensions every class must fill, and optional ones a class may add. Here is how the 66 existing entries map (CHECKED names from the coverage table; mapping INFERRED):

| Dimension | Existing dictionary entries |
| --- | --- |
| D1 direction | trend-direction, trend-strength, higher-timeframe-trend-bias, market-regime, moving-average-trend, range-bound-state, momentum, rate-of-change, timeframe-alignment |
| D2 volatility | average-true-range, bollinger-bands, realized-volatility, implied-volatility, donchian-channel, keltner-channel, average-daily-range |
| D3 participation | bid-ask-spread, spread-widening-condition, market-depth, slippage, trading-cost, exchange-volume, spot-fx-tick-volume, order-book-depth, footprint-order-flow, cumulative-delta, absorption, data-health-feed |
| D4 time | trading-session, session-overlap, time-of-day-window, day-of-week-window |
| D5 events | economic-calendar-event, news-event-window, news-event-class, rollover-swap-cost (partly) |
| D8 intermarket | the five entries above |
| **Not context** (location or trigger roles) | fair-value-gap, order-block, supply-demand-zone, liquidity-sweep, support-resistance, distance-to-level, session-open-price, higher-timeframe-reference, vwap, volume-profile, plus triggers: moving-average-crossover, market-structure-break, macd, rsi, stochastic, divergences, crossover |
| **Operations or families** | moving-average, oscillator, band-envelope, ichimoku-cloud, confluence-count, pattern-quality-grade, reward-risk-distance |

**Hana:** Two lessons. First, the file mixes roles. It calls itself "Context, Filter, Confirmation & Indicator Primitives" and says no role is intrinsic (CHECKED, first lines). That is correct: primitives are role-neutral (CHECKED `research/10` §2.1). So "context" is a *role and a dimension*, not a folder. Second, the measurement side is missing. Not one entry names Hurst, variance ratio, efficiency ratio, HMM or BOCPD (CHECKED grep). D7 crowding has no entry at all: no open interest, and funding appears only as a cost note (CHECKED context file lines 594-631).

**Ines:** So the dictionary entry is the *term*, and the MIS needs *sensors* per term per class. The field that joins them already exists: every entry has "Recognition semantics" (CHECKED, e.g. `market-regime`: "explicitly multi-indicator and heuristic; there is no single authoritative algorithm"). Each sensor is one concrete way to meet that field.

**Priya:** And requirement against measurement is a band per dimension. Example context claim: `D1 = mean-reverting at 15m over the last session; D2 = 0.7-1.4× the hourly norm; D3 = spread ≤ 1.2× norm; D5 = no high-impact event within 30 min`. The MIS publishes readings; matching is band inclusion.

**Tomasz:** Deseasonalise everything first. "Volatile" means "volatile for 14:30 on a Tuesday". Otherwise every model rediscovers the London open (CHECKED `research/05` §1.2).

**Vera:** Tally item one: D1 at scalper speed describes the past. The operator's scan of "20 of 100 mean-reverting" is fine for *which markets this session*, but useless for *this minute*.

**The Operator:** That's fine. I said expand the domain. Pick the markets, then the unit does its job.

**Otto:** Registering a new sensor. A workflow meets a term it cannot measure, say "funding stretched". The agent drafts four things:
1. a dictionary entry with the 12 fields (CHECKED `research/10` §2.5);
2. a sensor in plain Python against the sensor schema;
3. a backfill over history so QMB can replay it;
4. a lift report: does the reading change any family's R?

The user approves. The sensor is stamped `name@version` (CHECKED `research/13` I77) and starts recording.

**Priya:** Every sensor tried in a lift study is a try for every family it was tested on. Count them.

**Vera:** And sensor sprawl? Fifty sensors measuring "volatility" ten ways.

**Hana:** Sensor hygiene, like the dictionary-collision list (CHECKED `Stats\catalog\dictionary-collisions.md` via `research/10` §2.5): two sensors whose readings agree above 0.9 *(cfg)* are flagged as duplicates.

*Agreements:* five core dimensions plus class extras; dictionary = terms, MIS = sensors; deseasonalise; horizon tag on every dimension; agent proposes and the user approves; label versions are stamped.
*Live disagreements:* cost as a dimension or the unit's own maths; whether D7 and D8 are core or class extras; bins (three levels per dimension, Priya, to limit tries) or continuous readings (Tomasz).

---

### Round 4. Indicators vs statistical tests vs models, and the Lab

**Leo:** They are the same family with different engines:

| Engine | What it is | Examples | Cost and lag | Needs |
| --- | --- | --- | --- | --- |
| Indicator | deterministic transform | ATR, ADX, RSI, Kaufman efficiency ratio, spread ÷ norm | cheap, lag = window | nothing |
| Statistical test | statistic plus confidence over a window | variance ratio, Hurst estimate, ADF, runs test, autocorrelation | medium; needs enough bars | a window and a null |
| Model | fitted, versioned, can drift | HMM, jump model, BOCPD, MS-GARCH, XGBoost | training plus inference | training data, retraining, a registry |

**Ines:** Small correction to the notes: Kaufman's efficiency ratio is an indicator, not a test. It has no null and no p-value. Hurst sits in between, as an estimator often used like a test (INFERRED).

**Hana:** One schema for all three: a **sensor** declares inputs, window, the class it applies to, output (value, label, confidence), lag tier T0-T3 (CHECKED `research/05` §1.1) and version. Every engine returns the same reading shape, so a unit's context claim never cares which engine is behind it.

**Tomasz:** The lag tier matters most. Rule: a sensor whose lag exceeds the unit's typical holding time × 3 *(cfg)* may be used for placement, not for entries. That turns Vera's tally into a check.

**Vera:** The code today: the MIS has six rule labelers, one fitted (`liquidity_stress_v1`) and one untrained regime classifier. HMM, BOCPD and MS-GARCH are "candidates without authority" (DEC-0262) (CHECKED `research/01` lines 227-228). The UI shows labelers that do not exist (CHECKED `research/01` finding 10). Don't sell the Lab on things that aren't there.

**The Operator:** I want this layer in the Lab.

**Otto:** The Lab gets a **sensor bench**:
- pick instruments, a period and sensors;
- see labels painted on the chart;
- see where sensors agree and disagree;
- see how long a label persists (half-life);
- run a lift test of any sensor against any unit's journal.

The same library code runs in the Lab, QMB and live. Market labels are library code, so a unit can compute them itself when the router's copy is missing (CHECKED `research/14` via STATE row 14).

**Priya:** Persistence is the forgotten number. If a "mean-reverting" label lasts 40 minutes on average, placing a unit for a whole session on it is wrong. The bench should report the median label run length per class.

**Leo:** Models need per-instrument training (CHECKED STATE.md:69) with pooled strength across a class (CHECKED `research/13` I69). Train per class, fine-tune per instrument.

**Ines:** And the bench becomes the research tool for Round 5: a sensor leaderboard per class, asking which sensor best predicts which family's edge on which class.

**Vera:** "Best predicts" across many sensors, families and classes is a multiple-testing machine.

**Priya:** Yes. Pre-register the leaderboard's families and classes. Use a holdout year *(cfg)* for the final ranking. Report the false-discovery rate, not the top line.

*Agreements:* one sensor kind with three engines; a lag tier on every sensor; the sensor bench in the Lab; the same code everywhere.
*Live disagreements:* models in the live path (Leo: yes if fast; Vera, citing `research/09` "No regime model, HMM, BOCPD or ML model in the gate", CHECKED: placement only); whether XGBoost counts as a sensor or as a unit part (Round 7).

---

### Round 5. The MIS organised by asset class: inefficiency research, context-first strategies, and news through the events dimension

**Ines:** This is my desk's job. Each class has recurring, studied effects. Make one **inefficiency atlas** per class. Starter rows (sources as given):
- **FX.** Asian-range mean reversion in quiet hours (CHECKED `research/02` §11 row 2); session handover; rollover-minute spread spikes (CHECKED `research/02` §1 table: break 23:59-00:01 server); the 4pm London benchmark fix and month-end flows (INFERRED, not yet sourced).
- **Gold.** LBMA auctions at 10:30 and 15:00 London (CHECKED `research/02` §3.2); NY-open and London-open sweeps that revert to mid-range within 30-90 minutes in live sessions (PRACTITIONER, as cited in `research/02` §3.3); the dollar and real rates (INFERRED).
- **Futures.** The opening range in stocks "in play" by relative volume (CHECKED `research/02` §11 row 5); VWAP reversion with real volume (CHECKED §11 row 6); roll week and settlement; the overnight session vs regular hours.
- **Crypto perps.** Funding times and extremes as crowding (CHECKED `research/02` §11 row 8); avoiding the 16-17 UTC peak for mean reversion (CHECKED §11 row 2); liquidation cascades and weekend thinness (INFERRED).
- **Index CFDs.** Open gap, close auction, dividend adjustments (CHECKED `research/02` §1 table).

**Delphine:** And gold trends at the NY open, per the notes. That's a *habit*: a seasonal profile of D1 by hour. Store it as a habit table per instrument (direction and volatility by hour of week) beside the terrain.

**Ines:** Yes. A habit table is context averaged into a prior. Live state still overrides it.

**Ines:** Now the new source. A **context-first strategy** starts from a measured inefficiency, then looks for the trigger that harvests it. Example: "funding above its 95th percentile with rising open interest" is the context. The trigger is a failed breakout. The context *is* the edge.

**Hana:** In DNA terms the seed is the context pillar alone: class `fragment` or `entry_hypothesis`, origin "context study" (CHECKED class list, `strategy-dna.md` lines 45-56). Primitives have no fixed role (CHECKED `research/10` §2.1), so a sensor can be promoted from the context role to the trigger role.

**Priya:** Context-first research is data-mining by design. You scan 40 sensors × 5 classes for anything odd. Every scan is a try. Use a holdout and the false-discovery rate. And demand a *mechanism*, a reason someone loses money to you, before building a unit.

**Kofi:** Use class-correct data. Tick volume is not volume; the dictionary keeps them split and says never merge them (CHECKED context file, Deduplication notes). An FX "volume" sensor is a tick-rate sensor. Label it.

**Rania (news):** Events. The dictionary already has calendar, window and event class, and admits there is no cross-market event taxonomy: FX macro and crypto events "likely need separate vocabularies" (CHECKED context file, unresolved question 4). So D5 is per class:
- FX and gold: macro releases;
- futures: roll, expiry, inventory reports;
- perps: funding times, unlocks, listings, liquidations.

**Rania:** On retail CFDs, trading the spike is a donation. Spreads blow out and fills slip. The edge is in the **aftermath**: drift or fade 5-30 minutes later *(cfg)*, measured by surprise against consensus.

**Vera:** Two problems. One: `research/02` §11 says "The operator has news trading off" (CHECKED). Two: the news kill switch exists and is global (CHECKED `seeds.md:101`). A news unit fights the guard.

**Rania:** So the guard needs a per-unit exemption that names the event class. But guards must not depend on unit claims…

**Otto:** The exemption lives in the operator's admission card, not in the unit, so the guard reads his click, not the unit. Still a real conflict for him to rule on (§5 Q5).

**Marcus:** And news data: his rulings say free news only (CHECKED, operator memory index `MEMORY.md` line 6). Surprise needs consensus numbers. Free calendars carry forecast fields (CHECKED context file `economic-calendar-event`: "forecast/previous fields"), so it's workable at first.

**The Operator:** And fundamentals were always meant to feed MIS variables.

**Ines:** CHECKED: `seeds.md:99-100`, "An agentic QMX workflow does fundamental analysis with proof … and feeds MIS variables". That is D8 intermarket plus D5 events, done by a workflow at a slow cadence.

*Agreements:* one atlas per class; habit tables as priors; context-first is a new idea source; events are per class; trade the aftermath, not the spike.
*Live disagreements:* news units vs the global kill switch; context-first as data-mining (Priya) vs the desk's bread and butter (Ines); whether the atlas is durable research (a mini-KB) or live intelligence (the market journal). August split it: "knowledge = slower durable understanding; intelligence = dated changing observations" (CHECKED `research/10` §2.11).

---

### Round 6. Sources and intake: context claim, instrument claim, both or neither

**Hana:** Every source gets two fields on its idea record: `context_claim` and `instrument_claim`, each `stated`, `inferred` or `absent`. That gives four cells:

| | Instrument stated | Instrument absent |
| --- | --- | --- |
| **Context stated** | "I scalp gold mean reversion in the quiet Asian hours": a System 2 seed plus a context claim. Test the parent across the universe. | "Works in ranging markets": a System 1 seed. Research finds the instruments. |
| **Context absent** | "I trade this on gold": a System 2 seed. Research must *discover* the context. | "Here's an EMA cross": research fills both blanks. |

**Delphine:** "What exactly do you trade on gold?" is a four-part interview, not one question:
1. **Logic:** what are the location, trigger, confirmation and exit?
2. **Context:** when does it work, and when do you stop?
3. **Habits:** what is gold-specific (fixes, NY open, dollar days)?
4. **Numbers:** which values did you settle on?

Part 1 is the parent. Part 3 is terrain or habit. Part 4 is the child's calibration. Part 2 is the context claim.

**Ines:** Often part 1 names an instrument-specific primitive. "Fade the 15:00 fix" only exists on gold. You can still get a parent by *lifting the primitive to its analogue class*: gold fix → FX 4pm fix → futures settlement → index close auction. The parent becomes "fade benchmark-fix dislocations". That's how a gold seed becomes a System 1.

**Kofi:** Nice, but an analogue map is a hypothesis. The FX fix is a different crowd.

**Ines:** That's why it's tested broadly, not assumed.

**Priya:** Filling blanks. Run the logic on the universe in QMB, tag each trade with MIS readings at entry, then split. Rules:
1. Only the five core dimensions, three bins each *(cfg)*. Marginal splits first (15 cells), pairs only for the top 2 *(cfg)*.
2. Every split is a try.
3. A discovered claim gets evidence class `inferred`, never `source-stated` (CHECKED class names, `strategy-dna.md` B).
4. Confirm on a holdout period before it drives live matching.

**Leo:** Order the queue by information gain: test where the uncertainty is biggest. The "neither" cell may teach the most.

**Vera:** Or teach you noise the fastest. Do the "both stated" cell first: the cheapest falsification.

**Otto:** The first cheap breadth step is August's three-pair challenge: home, close analogue, adversarial, chosen before results (CHECKED `research/10` §2.10). Run it before the full universe. Kill early, save compute.

**Hana:** And the intake queue exists: 359 NotebookLM sources, 46 priority-forex, never processed (CHECKED `research/10` §2.8, §6.8).

**The Operator:** And where winners come from?

**Hana:** Add claim type to the analyst lens. If "context stated" sources produce more survivors, that's a finding about sources.

*Agreements:* two claim fields with three states; a four-part interview; lift instrument-specific primitives to analogue classes; inferred claims labelled as inferred; the three-pair challenge first.
*Live disagreements:* queue order (information gain vs cheapest falsification); whether an `inferred` context claim may ever drive live matching without his look (Priya: holdout is enough; Vera: he should see it).

---

### Round 7. Generation, now that it targets logic, not instruments

**Leo:** The genome is the graph with named ports. Mutation = an edit operation (CHECKED list, `research/10` §2.6). Crossover = swap a port between families. Fitness = B3 context lift across independent instruments after costs, deflated by tries. The search moves over logic, and instruments become the *test bed*, not the search space.

**Priya:** 07 rejected genetic crossover with evidence (CHECKED `07-funnel.md:712`). And 11 found overfitting grows with refinement depth, with gains decaying after about 15 rounds (CHECKED STATE row 11).

**Leo:** 07 rejected *blind* crossover of parameters. The operator's idea is different: move one proven part across families, "test it across families" (CHECKED `research/10` §2.9, `RES #0`). Use the August search order:
1. fix location and context;
2. compare trigger families;
3. keep a few robust ones;
4. add one confirmation at a time and measure the gain;
5. test interactions last.

That is staged, not brute force (CHECKED `research/10` §2.2, `DB 4065`).

**Priya:** Then count every candidate as a try in its receiving family, stop at a depth limit, and use an untouched holdout.

**Vera:** "Nothing capped" is a binding rule. A depth limit is a cap.

**Priya:** It's a *stopping rule*, not a cap. Tries are counted, not capped; the correction grows with the count. An agent may run on, but its results get discounted harder.

**Leo:** Quality-diversity search: keep the best candidate *per niche* (context × class), not one global best. That's MAP-Elites (INFERRED). It matches August's "no magical best variant" (CHECKED `research/10` §2.7). The archive *is* the family tree arranged by niche.

**Leo:** XGBoost has three jobs:
1. **Context learner:** on a unit's trades, which sensor readings at entry predict R? Its splits propose a context claim. Feature importance never *is* the claim.
2. **Meta-label part:** a model in the confirmation role, deciding take or skip (CHECKED `research/05` short answer 4). That is a logic change, so it becomes a new System 1 variant.
3. **Surrogate fitness:** predicts which candidates are worth a full backtest.

**Priya:** The surrogate only orders the queue. Everything it skips still counts as tried; otherwise you hide the tries.

**Otto:** Workflows, one job each:
- **W-generate:** N candidates per niche, staged order;
- **W-breadth:** the broad test, B-rule;
- **W-context:** discover a context claim;
- **W-upstream:** merge tweaks that several children share into a parent variant;
- **W-sensor:** propose a sensor.

An agent decides nothing about money or promotion. It proposes, and the proposals render in the UI.

**Hana:** LLM-built logic needs a test window after the model's training cutoff, because of memory look-ahead (CHECKED STATE row 11).

**Ines:** One more generator: **context-first generation**. Take a niche that is empty in the MAP-Elites archive, say "high-vol, illiquid, perps", and ask agents for logic aimed at it. That's directed search into the gaps.

**The Operator:** And many System 2s can make a new System 1?

**Leo:** Yes: upstreaming (Round 2), or a **consensus parent**. Take the parts most children kept after their own calibration and call that the new parent. Biology calls it a consensus sequence.

*Agreements:* search over logic with instruments as the test bed; staged order; ports; per-niche archive; every candidate counted; XGBoost proposes but never decides.
*Live disagreements:* crossover at all (Priya: only staged and with a depth stop; Leo: freer); surrogate pruning (Leo) vs hidden tries (Priya); whether the consensus parent is a new logic or the old parent recalibrated.

---

### Round 8. Live expansion of a System 1 unit to an instrument it never traded

**The Operator:** The options from the notes: (a) only already-tested instruments; (b) any instrument whose terrain passes, starting small and logged; (c) the context claim proven broadly first, then entry small.

**Vera:** Ruling Q3: "Nothing enters live without him … the minimum-lot auto-promotion is rejected" (CHECKED STATE.md:39). Option (b) as written breaks it.

**Otto:** Not if his click admits an **envelope by class**: "this unit may trade FX majors whose terrain passes". Then (b) runs inside what he ticked. Round 2's admission envelope already went this way (CHECKED STATE row 13).

**Priya:** Each new instrument is one more test in a stream. Alpha-investing spends error budget per test and earns it back on discoveries (CHECKED `research/05` short answer 10). That's the maths for (b) and (c).

**Marcus:** The terrain check must include the contract value factor. QMX already refuses when it's missing (CHECKED `research/02` §3.4).

**Yuki:** And the venue's request budget. Hyperliquid rations order actions by traded volume (CHECKED `research/02` short answer 4).

**Kofi:** (c) only works if "proven broadly" is B3. A unit proven on EURUSD and GBPUSD isn't proven for USDJPY at the Tokyo open.

New options from the room:
- **(d) Shadow first.** On untested instruments the unit trades on paper automatically, in a shadow lane, until N trades *(cfg, e.g. 100)*. Then a proposal card goes to him. Nothing live without his click. **Vera:** "This one I like."
- **(e) Class envelope plus borrowed prior.** He admits a class. The unit trades a new member at a size set by the parent's shrunk estimate for that class, which starts small because the prior is wide.
- **(f) Matching-only expansion.** The unit may go only where the MIS shows its context claim *and* the instrument shares a class with an instrument where the claim was proven.

**The Operator:** I want compounding through breadth. (a) is too slow.

**Priya:** Then (d) feeding his click is the fastest option that keeps ruling Q3. If he wants faster, (e) is the honest version of (b).

*Agreements:* (b) as written conflicts with ruling Q3; every new instrument is a counted test; terrain refusals happen before anything else.
*Live disagreements:* (d) shadow plus click (Vera, Priya) vs (e) class envelope (Otto, the Operator's lean toward speed) vs (c) (Kofi, only with B3).

---

### Round 9. The lens list: challenged, and the missing lenses

Draft (from the notes): 1 sources and intake · 2 research before live · 3 live trading · 4 journal analysis · 5 market intelligence per class · 6 the numbers · 7 agents and workflows · 8 the operator and the UI.

**Hana:** It mixes two axes. Lenses 1-4 are *stages* of a unit's life. Lenses 5-8 are *concerns* that cut across every stage. Make it a grid: stages down the side, concerns across the top. Then "MIS in research" and "MIS live" are two cells, not one blur.

**Priya:** **Judging and tries** is missing as its own lens. "Judging is the product" (correction 10). It hides inside "research before live" today.

**Marcus:** **Terrain**: instruments, venues and brokers, costs, contracts, calendars. Every round tonight hit it.

**Kofi:** **Data and feeds**: depth of history, recording our own (Hyperliquid keeps ~3.5 days of 1m, CHECKED STATE row 02), quality, Dukascopy's bot wall (CHECKED STATE row 12).

**Hana:** **Identity and lineage**: what a unit *is*, logic vs calibration, the parent and child tree. Tonight is mostly this lens.

**Vera:** **Safety and independence**: guards, kill switches, the router as a point of failure (CHECKED STATE.md:64-65).

**Ines:** **Durable knowledge**: the atlas, habit tables, mini-KBs. Not live intelligence, not journals.

**Otto:** **Evolution over time**: decay, retirement, succession, upstreaming. Journal analysis looks back; evolution decides what changes.

**Rania:** **Explaining a trade**: why this trade, on this market, now. Round 2 had one id from source to trade (CHECKED STATE row 13).

**The Operator:** And usage. Agents cost my plan's limits.

**Otto:** **Compute and usage**: where jobs run (local first, CHECKED STATE.md:72-73) and what the agents spend. Usage is not a cap, but it shapes order.

Resulting grid (INFERRED):
- **Stages:** intake → research → judging → paper → live → review and evolution.
- **Concerns:** identity and lineage · market intelligence per class · terrain · data and feeds · the numbers · safety and independence · agents and workflows · operator and UI · durable knowledge · compute and usage.

*Agreements:* stages × concerns beats a flat list; judging, terrain, data, identity and safety are missing.
*Live disagreements:* whether "explaining a trade" is a lens or a feature of journals; whether usage belongs in design at all (Vera: "design for the work, then budget it").

---

### 2.10 Brainstorming passes (headless, six techniques)

#### A. Morphological analysis

Axes and sample values:

| Axis | Kind | Values (sample) |
| --- | --- | --- |
| Logic | logic | MR scalper, momentum breakout, liquidity-sweep reversal, ORB, VWAP reversion, passive maker, fix-fade, funding-fade, news aftermath |
| Context | state | D1 (trend / MR / noise) × D2 (low / normal / high) × D3 (thin / normal / deep) × D5 (none / pre / post event) |
| Asset class | terrain | FX, gold, index CFD, futures, perps, spot crypto |
| Instrument | coordinate | EURUSD, XAUUSD, MES, BTC-PERP… |
| Timeframe | coordinate (contested) | 1m, 5m, 15m, 1h |
| Session | coordinate | Asia, London, NY, overlap, 24/7 hour bands |

Finds:
- Only one axis is logic. Context is *state*, class and instrument are *terrain or coordinate*, and session is a coordinate. Search over the first axis; test over the rest. (INFERRED)
- The combinatorics: 9 logics × 36 contexts × 6 classes × 4 timeframes ≈ 7,800 niches before instruments. Hence niches with borrowed strength, not cells judged alone.
- Interesting cells: *passive maker × D3 deep × perps × 24/7 quiet hours*; *fix-fade × D5 = fix window × gold/FX*; *news aftermath × D5 post × gold × NY*; *MR scalper × D2 low × D1 noise × FX Asia*; *VWAP reversion × futures × RTH × D3 normal*. Each is a starting row for the atlas, not a claim.
- Impossible cells say something too. Footprint-based logic × FX is empty because there is no tape on cTrader (CHECKED `research/02` short answer 5). The morphology box doubles as a terrain-refusal table.

#### B. First principles

- A unit makes money from (edge per trade − cost) × trades per period × independent bets.
- The MIS can only help in three ways: pick contexts with a higher edge, find more places to trade, and pick less correlated places.
- So the **MIS value test** is: run the same unit in QMB with the MIS on and off, then compare in R. Look at R per trade, trades per week and effective N. Round 2 already asked for "declared MIS-missing behaviour, tested both ways" (CHECKED `research/13` I59).
- If the MIS adds nothing to a unit, that unit is always-on, and that's an honest result.

#### C. Reverse brainstorming: how do System 1, System 2 and the MIS lose money?

1. Every "broad" unit is the same dollar bet.
2. The MIS labels mean-reversion after it ended (lag).
3. Sensor sprawl turns into a tries explosion, which turns into false context claims.
4. "Mean-reverting" markets are mean-reverting because market makers fade there, and you are the one being faded (adverse selection, measurable by order-flow imbalance, CHECKED `research/05` §1.1 T1 micro).
5. A child sneaks a state filter in as a "terrain gate".
6. A label version changes silently, and QMB replays differently from live.
7. The parent's prior is wrong for a new class, and a borrowed size blows up.
8. A news unit trips the global news kill switch, or worse, gets an exemption that becomes a habit.
9. An upstreamed tweak was found on the same data it is judged on.
10. LLM-built logic remembers 2024.
11. A habit table (gold trends at the NY open) stops being true, and nobody re-measures it.
12. Abstract parents pile up as zombie records nobody reads.

Each one turns into a guard idea in §4.

#### D. Analogies

- **Biology.** Genus → species → subspecies (or ecotype). Logic = genotype. Calibration = phenotypic plasticity. A logic change = speciation. A transplant = horizontal gene transfer. A refuted parent = the fossil record. Context = the niche. Instrument = habitat. Quality-diversity search = one survivor per niche. A consensus parent = a consensus sequence.
- **Recommender systems.** Units are users, market-and-context cells are items, and R is the rating.
  - The declared context claim is *content-based* filtering.
  - Learning from journals is *collaborative* filtering: units with similar logic like similar markets.
  - A new System 1 variant has a *cold start*, so seed it from its parent's and siblings' tastes.
  - Exploration happens through a bandit *inside the unit*, never a router switch.
  - The MIS matchmaker is a hybrid recommender.
- **Medicine.** Drug = logic, patient = market. A sensor is a **companion diagnostic** that qualifies only if it predicts response. Drug repurposing = testing logic in a new context. Trial phases = research → paper → live.
- **Git.** A child is a fork. A shared tweak is upstreamed. A transplant is a cherry-pick. A refuted parent is an archived branch kept for history.
- **Object-oriented code.** The parent is an abstract class, the child a subclass that overrides numbers, not methods, and a transplant is a mixin.
- **Weather.** Sensors per class are stations. Nowcast (T1) vs forecast (T3). An ensemble of sensors, with disagreement shown, not averaged away.

#### E. Assumption reversal

- *What if the instrument, not the unit, is the main object?* Each market keeps a roster of units whose claims it currently matches. The operator's view becomes a market × unit grid. (INFERRED; it fits his "qualitative tracking".)
- *What if context is learned, not declared?* The unit's journal plus XGBoost writes its claim, and the declared claim becomes the prior.
- *What if System 2 is primary and System 1 is only a summary?* The parent becomes the pooled estimate over its children. This reconciles "a parent by default, even if it fails".
- *What if the MIS outputs clusters, not a list?* "20 mean-reverting markets in 4 correlated clusters" tells the unit and the pod the true breadth at once.

#### F. SCAMPER on the MIS (short)

- **Substitute:** labels → bands with confidence.
- **Combine:** MIS readings plus market-journal costs in one stream.
- **Adapt:** SQS's hourly norm to every D2/D3 sensor (CHECKED `research/05` short answer 3).
- **Modify:** horizon tags on every reading.
- **Put to other use:** MIS history as the atlas research set.
- **Eliminate:** regime models from the live entry path.
- **Reverse:** the market chooses units (the roster).

---

## 3. Permutation map: how the ideas combine or conflict

### 3.1 Clusters

| Code | Cluster | Ideas (§4) |
| --- | --- | --- |
| A | Identity: abstract parent, statuses, logic fingerprint, terrain line, upstreaming | 1-16 |
| B | Breadth: B1/B2/B3, effective N, cost-normalised R | 17-28 |
| C | Context vocabulary: dimensions, bands, horizon tags, dictionary map | 29-42 |
| D | Sensors: one kind with three engines, lag tier, bench, registration | 43-58 |
| E | Class research: atlas, habits, context-first, events and news | 59-74 |
| F | Intake: claim matrix, interview, analogue lifting, discovery | 75-84 |
| G | Generation: ports, staged search, niche archive, XGBoost roles | 85-100 |
| H | Live expansion: (a)-(f), bandit, MIS value, drift | 101-112 |
| I | Lenses, views and operations | 113-127 |

### 3.2 Cross-map

`+` reinforces · `x` conflicts · `→` row needs column first · `.` little contact

| | A | B | C | D | E | F | G | H |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A** | | → (statuses need a breadth rule) | + (context claim is logic) | . | + (habits as terrain) | + (child-first birth) | + (edit ops decide variants) | + (parent = prior for new markets) |
| **B** | | | → (B3 needs labels) | → (B3 needs sensors on backtest trades) | . | x (discovery and test on one dataset) | + (fitness = B3) | → (options c, e, f need B3 or class-broad) |
| **C** | | | | → (dimensions filled by sensors) | + (class extras D7, D8) | + (claim fields use the vocabulary) | + (niches = context cells) | + (matching = bands) |
| **D** | | | | | + (bench is the atlas tool) | + (discovery splits by sensors) | x (sensor sprawl = more tries) | x (models in the live path vs `research/09` gate) |
| **E** | | | | | | + (context-first seeds) | + (empty niches steer generation) | x (news units vs the global kill switch) |
| **F** | | | | | | | + (inferred claims as generator targets) | . |
| **G** | | | | | | | | x ("nothing capped" vs a depth stop, resolved as discount, not cap) |

### 3.3 Strongest combinations

1. **B3 + lag tier + MIS on/off test (19, 44, 110).** The unit's context claim is proven, used only at a speed the sensor supports, and the MIS's own value is measured per unit. This is the heart of "System 1 live".
2. **Abstract parent + borrowed strength + class envelope (1, 3, 105).** Breadth with honest starting sizes, inside what his click admitted.
3. **Claim matrix + four-part interview + analogue lifting (75, 77, 10).** Every source becomes a parent plus a child, even a gold-only one.
4. **Niche archive + atlas + empty-niche generation (89, 59, 90).** Search is steered into contexts and classes nobody covers yet.
5. **Terrain/state split + `qml.check` rule + instrument spec (7, 13, 108).** Children carry instrument habits without the logic drifting.
6. **Sensor bench + leaderboard + companion-diagnostic rule (46, 52, 45).** The class research the operator asked for, with a built-in guard against fishing.
7. **Clusters output + effective N + fundamental-law readout (42, 20, 28).** He sees true breadth at a glance, which is exactly his compounding argument.

### 3.4 Conflicts to settle

| # | Conflict | Sides | Where it goes |
| --- | --- | --- | --- |
| X1 | Live option (b) vs ruling Q3 "nothing enters live without him" (CHECKED STATE.md:39) | speed vs his click | §5 Q4 |
| X2 | News units vs the global news kill switch (CHECKED `seeds.md:101`) and "news trading off" (CHECKED `research/02` §11) | Rania vs Vera | §5 Q5 |
| X3 | Units reading MIS output (System 1 needs it) vs DEC-0204 "never bots" (CHECKED `research/01` line 226); still open as Round 2's Q4 (CHECKED STATE.md:149) | System 1 vs old docs | Already queued to him as Q4 in STATE. Not re-asked here. |
| X4 | Genetic crossover rejected in 07 (CHECKED `07-funnel.md:712`) vs his transplant idea (CHECKED `research/10` §2.9) | Priya vs Leo | Settle in design: staged transplants with counted tries (ideas 86-88, 94) |
| X5 | Regime models in the live path vs `research/09`'s "no regime model … in the gate" (CHECKED) | Leo vs Vera | Settle in design: lag tier rule (idea 44) |
| X6 | Discovered context claims judged on the data that found them | F vs B | Settle in design: holdout before live matching (idea 79) |
| X7 | Depth stop vs "nothing capped" | Priya vs the rule | Settle in design: count and discount, never stop (idea 94) |
| X8 | Timeframe as a coordinate vs new logic | Hana vs Kofi | Open; low stakes. Default: coordinate, with costs re-checked |
| X9 | Atlas as durable knowledge vs live intelligence | Ines vs August's split | Both: rows are durable, measurements live in the almanac (ideas 59, 74) |

### 3.5 What must exist first

1. **Results in R** and **MIS readings on every backtest trade, point in time** (CHECKED missing, `research/05` short answer 12). B3, discovery, the bench's lift test and the MIS on/off test all wait on these two.
2. **The typed instrument spec** (terrain: calendars, fixes, roll, value factor). Terrain gates and refusals wait on it.
3. **The sensor schema plus `name@version` stamping.** Everything in D waits on it.
4. **The tries ledger at the QMB door** (CHECKED planned, `research/07` foundations). Generation, discovery and the leaderboard need it.
5. **The market journal** (costs per broker, instrument and minute, CHECKED STATE row 12). Cost-normalised breadth needs it.

---

## 4. Idea list (numbered, unranked)

Format: **Idea.** What it is. · *Lens* · *QMX surface* · *What it touches*

Lenses use the grid from Round 9: intake, research, judging, live, review/evolution (stages); identity, MI-class, terrain, data, numbers, safety, agents, UI, knowledge, compute (concerns).

### A. Identity and lineage

1. **Abstract parent by default.** Every System 2 links to a System 1 parent record, created even when the child came first. · identity · QML unit spec, Library · new `specialises` edge
2. **Parent statuses.** `unproven`, `broad`, `class-broad`, `narrow`, `refuted`, instead of pass/fail. · identity, judging · Library, journal · status field, UI badge
3. **Parent = pooled estimate of its children.** Children shrink toward it, and it is the prior for any new instrument. · judging, numbers · QMB judge · needs results in R
4. **Logic fingerprint.** A hash of primitives, roles, timing, graph operators, exit-slot kinds, entry semantics and sizing method. Numbers and coordinates are excluded. A changed hash means a new System 1 variant. · identity · `qml.check` · unit spec schema
5. **Declared ranges belong to the logic.** Children calibrate only inside the parent's ranges. · identity · QML spec · parameter schema
6. **The edit operation decides "new or same" automatically,** using August's mapping (CHECKED `research/10` §5.1). · identity, agents · `qml.check` · lineage edges
7. **Terrain gates vs state filters.** A terrain gate may read only instrument-spec fields (calendar, fixes, roll, hours). A gate that reads price or a sensor is logic. `check` refuses a mislabelled one. · identity, terrain · `qml.check`, instrument spec
8. **Upstreaming.** A tweak found in two or more children *(cfg)* is lifted into a new parent variant with `informed-by` edges, and is judged only on instruments neither child traded. · review/evolution · QML lineage, W-upstream
9. **Consensus parent.** The parts most children kept after calibration become a candidate parent. · review/evolution · workflow
10. **Analogue lifting.** An instrument-only primitive is lifted to its class of analogues (gold fix → FX 4pm fix → futures settlement → index close auction) to derive a parent from a single-market seed. · intake, identity · dictionary relation `analogue-of`
11. **Three new link types:** `specialises`, `informed-by` and `analogue-of`, beside August's `composed-from` and `corrected-from` (CHECKED `research/10` §4). · identity · Library lineage
12. **Sizing method = logic; sizing numbers = calibration** (self-calibrated from the journal). · identity, numbers · unit spec
13. **Entry semantics is logic; venue support is terrain.** Maker vs taker is a choice inside the logic. A venue without post-only refuses the unit. · identity, terrain · unit spec, instrument spec
14. **Failure ledger for refuted parents,** with the breadth map that shows *how* they failed. · review · Library
15. **Quiet-parent folding.** Parents with no child activity for 6 months *(cfg)* fold into a compact view. Never deleted. · UI, knowledge · Library UI
16. **Record birth order** (child-first or parent-first) for the analyst lens. · intake, review · idea record

### B. Breadth ("broadly wins")

17. **B1 count.** Passes on ≥60% *(cfg)* of a pre-registered universe of ≥12 instruments *(cfg)* across ≥3 classes *(cfg)*, with effective N ≥6 *(cfg)*. · judging · QMB
18. **B2 pooled, no carrier.** Pooled ≥ +0.10R after costs and the tries correction *(cfg)*, median instrument > 0R, no instrument > 25% of total R *(cfg)*. · judging · QMB
19. **B3 context lift.** In-context minus out-of-context edge ≥ +0.05R *(cfg)*, positive on ≥60% of independent instruments *(cfg)*, and pooled in-context > 0 after costs. Tests the unit's real claim. · judging, MI-class · QMB · needs MIS readings on trades
20. **Effective N.** Count independent bets from the correlation structure, not tickers. · judging · QMB, correlation ledger
21. **Cost-normalised breadth.** R after each instrument's own measured costs. Instruments failing the unit's cost ratio are dropped *before* the test as a terrain refusal, not counted as failures. · terrain, judging · QMB, market journal
22. **Pre-registered universe** per family, chosen before results. · judging · tries ledger
23. **Class-broad tier.** The same test inside one class with ≥5 instruments and effective N ≥3 *(cfg)*. · judging · QMB
24. **Three-pair challenge as breadth stage 0:** home, close analogue, adversarial (CHECKED `research/10` §2.10). · research · W-breadth
25. **Breadth map view.** Per instrument: in-context and out-of-context R, grouped by correlated clusters. · UI · unit detail view
26. **Leave-one-instrument-out transfer test.** Calibrate on N−1, test on the held-out instrument. · judging · QMB
27. **Breadth re-test** every quarter *(cfg)*, because breadth decays too. · review · workflow
28. **Fundamental-law readout.** Skill × √(effective N), shown so the payoff of real versus correlated breadth is visible. · UI, numbers · unit and pod views

### C. Context vocabulary

29. **Firm definition.** "The measured state of one instrument at one timeframe at one moment, in a shared vocabulary of dimensions, measured by class-specific sensors." Terrain is separate. · MI-class · MIS, QML dictionary
30. **Five core dimensions plus class extras.** D1 direction, D2 volatility, D3 participation and liquidity (including cost state), D4 time, D5 events. Extras: D7 crowding (perps, futures) and D8 intermarket (gold, FX). · MI-class · MIS schema
31. **Horizon tag** on every dimension and every reading. · MI-class · MIS schema
32. **Bands with confidence, not bare labels.** · MI-class · MIS output schema
33. **Deseasonalise everything:** "now vs normal for this hour of the week", generalising SQS (CHECKED `research/05` short answer 3). · MI-class · MIS sensors
34. **Time is a coordinate; "this session is active today" is context,** measured from participation. · MI-class · MIS
35. **Context claim schema on the unit.** Per dimension, a band; hard (must) or soft (prefer); K-of-N matching. · identity, MI-class · unit spec
36. **Stand-aside contexts as first-class claims.** Example: quiet trends are the worst state for mean-reverters and grids (CHECKED `research/06` §1, article 21833). · MI-class · unit spec
37. **Map the 66 context entries to dimensions,** and mark location and trigger entries as non-context roles (Round 3 table). · knowledge · Stats dictionary into QML
38. **Fill the empty `time-sessions-and-events` and `indicators-and-transformations` folders** from the dimension list (CHECKED empty). · knowledge · dictionary
39. **Standard regime vocabulary:** D1 has three states (trend, mean-reverting, noise) × horizon. This answers the dictionary's unresolved question 3. · knowledge · dictionary
40. **Per-class event vocabularies.** Answers the dictionary's unresolved question 4. · MI-class · dictionary, MIS
41. **Habit tables per instrument.** D1 and D2 by hour of the week, stored as priors beside the terrain; live readings override them. · MI-class, knowledge · market journal, instrument spec
42. **The MIS outputs clusters,** not just a list: "20 matches in 4 correlated groups". · MI-class, numbers · MIS output

### D. Sensors (indicators, tests, models)

43. **One sensor schema, three engines** (indicator, test, model). · MI-class · QML `sensor` kind
44. **Lag tier rule.** A sensor whose lag exceeds the unit's holding time × 3 *(cfg)* is placement-only. · MI-class, safety · `qml.check`
45. **Companion-diagnostic rule.** A sensor qualifies only by measured lift on some family's R. · judging · QMB lift test
46. **Sensor bench in the Lab:** paint labels on the chart, show agreement, persistence and lift against any journal. · UI, research · Lab
47. **Label persistence** (median run length) reported per class. · MI-class · bench
48. **Sensor registration:** entry + plain-Python sensor + backfill + lift report → he approves → `name@version`. · agents · W-sensor, Library
49. **Backfill on registration** so QMB can replay the sensor; runs locally first. · data, compute · QMB, Library
50. **Sensor hygiene.** Readings that agree above 0.9 *(cfg)* are flagged as duplicates. · knowledge · Library
51. **Models trained per class, fine-tuned per instrument** (CHECKED `research/13` I69, STATE.md:69). · MI-class · model registry
52. **Sensor leaderboard per class:** pre-registered, holdout year, false-discovery rate reported. · research, judging · Lab
53. **Disagreement as a reading.** When sensors disagree, confidence drops, and units with hard claims stand aside. · MI-class · MIS output
54. **Plain-Python sensors always allowed;** the schema exists for agents (binding rule). · agents · QML
55. **17-number market fingerprint** with a "mutation" alarm (CHECKED `research/06` §1, article 19460) as a cross-class similarity sensor. · MI-class · MIS
56. **Volatility/drift ratio** (CHECKED `research/06` §1, article 21833) as a D1 sensor. · MI-class · MIS
57. **Random-walk null screen** (CHECKED `research/06` §1, article 5373) before building any entry-plus-stop idea. · research · QMB
58. **Show only sensors that exist, with versions.** The UI shows phantom labelers today (CHECKED `research/01` finding 10). · UI · Portfolio MIS tab

### E. Class research, context-first strategies, news

59. **An inefficiency atlas per class:** durable rows with mechanism and evidence grade; the mini-KB home (CHECKED empty `Stats\knowledge\`). · knowledge, MI-class · Library notes
60. **Every atlas row needs a mechanism:** who loses money to you, and why. · judging · atlas schema
61. **Context-first strategy seeds** from atlas rows (class `fragment` or `entry_hypothesis`, origin "context study"). · intake, research · idea record
62. **Sensor-to-trigger promotion.** A context sensor rebound into the trigger role (roles are not fixed, CHECKED `research/10` §2.1). · identity · QML bindings
63. **FX atlas starters:** Asian-range mean reversion, rollover spikes, session handover, 4pm fix and month-end (the last two to be sourced). · MI-class · atlas
64. **Gold atlas starters:** LBMA 10:30 and 15:00 windows as terrain gates and as fade candidates, NY/London-open sweeps, dollar and real-rate context. · MI-class, terrain · atlas, instrument spec
65. **Futures starters:** in-play relative volume for opening ranges, VWAP reversion on real volume, roll week, overnight vs regular hours. · MI-class · atlas
66. **Perps starters:** funding extremes as crowding, open-interest change, liquidation cascades, weekend thinness, avoiding 16-17 UTC for mean reversion. · MI-class · atlas
67. **Index CFD starters:** open gap, close auction, dividend adjustments. · MI-class · atlas
68. **Per-class event calendars for D5:** FX macro; futures roll, expiry and inventory reports; perps funding times, unlocks and listings. · MI-class, data · MIS
69. **News-aftermath units:** enter 5-30 minutes after the release *(cfg)*, keyed to surprise; never the spike. · live, MI-class · unit family
70. **Surprise sensor** from the free calendar's forecast and previous fields. · data · MIS
71. **News exemption on his admission card,** not in the unit, so the guard reads his click. · safety · guard, admission
72. **Fundamentals workflow** feeds D5 and D8 slowly (CHECKED `seeds.md:99-100`). · agents · workflow → MIS
73. **Class-correct data labels:** tick rate is not volume; VWAP on CFDs is a proxy (CHECKED `research/02` §11 row 6). · data · sensor schema
74. **Market almanac** (CHECKED `research/13` I45) as the atlas's measured history. · knowledge · market journal

### F. Sources and intake

75. **Two claim fields on every idea record:** `context_claim` and `instrument_claim`, each stated, inferred or absent. · intake · idea record (DNA A/B)
76. **Four-cell routing** (Round 6 table). · intake, agents · intake workflow
77. **"What exactly do you trade on gold?" as a Copilot skill:** a four-part interview covering logic, context, habits and numbers. · intake, agents · Copilot
78. **Discovery splits:** five core dimensions × three bins, marginal first, pairs for the top 2 only *(cfg)*. · research, judging · W-context
79. **Inferred claims are labelled `inferred`** and must pass a holdout before driving live matching. · judging · idea record, matching
80. **Queue-order policy as a setting:** cheapest falsification first, or largest information gain. · agents · intake queue
81. **The 359 NotebookLM sources as the first feed** (CHECKED `research/10` §2.8). · intake · intake queue
82. **Analyst lens by claim type:** which claim cells produce survivors. · review · journals × idea records
83. **Promotional claims kept and labelled, never used as evidence** (CHECKED `research/10` §2.8). · intake · idea record
84. **Operator dictations as a source kind** (`operator-dictation`) that can carry context claims. · intake · source manifest

### G. Generation

85. **Genome = the graph with named ports** (setup, entry, invalidation, exit, regime). · research, agents · QML graph
86. **Mutation = edit operation; crossover = port swap.** · research · QML edit ops
87. **Fitness = B3 lift after costs, deflated by tries.** · judging · QMB
88. **August's staged search order** (CHECKED `research/10` §2.2). · research · W-generate
89. **Niche archive (MAP-Elites):** the best per context × class cell, never one global best. · research · Library family tree
90. **Empty-niche generation:** aim agents at uncovered cells. · agents · W-generate
91. **XGBoost context learner** proposes a context claim from entry readings. · research · W-context
92. **XGBoost meta-label as a confirmation part.** That is a logic change, so a new variant. · identity · QML part
93. **The surrogate only orders the queue;** skipped candidates still count as tries. · judging · tries ledger
94. **Count and discount, never cap.** The deeper the refinement, the harder the correction. · judging · tries ledger
95. **LLM-memory window:** test LLM-built logic after the model's cutoff (CHECKED STATE row 11). · judging · QMB
96. **Refuted parents as negative examples** for the generator. · research · failure ledger
97. **Transplant ledger:** each part's record of how many families it improved. · review · Library
98. **Proven-parts shelf:** runnable blocks with a lift history, ahead of plain definitions. · knowledge · QML dictionary
99. **Five single-job workflows:** W-generate, W-breadth, W-context, W-upstream, W-sensor. · agents · QMA workflows
100. **Cold start by collaborative filtering:** a new variant inherits its parent's and siblings' market preferences as a prior. · research, MI-class · matching

### H. Live expansion and matching

101. **(a) Only tested instruments.** Safest and slowest. · live · admission
102. **(b) Any instrument whose terrain passes,** but only inside a class envelope he ticked. · live · admission
103. **(c) Context claim proven broadly first (B3), then small entry.** · live · admission
104. **(d) Shadow first:** automatic paper on new instruments until 100 trades *(cfg)*, then a proposal card. · live, UI · node paper lane, cards
105. **(e) Class envelope with a borrowed prior:** he admits a class, and the size starts from the parent's shrunk estimate. · live, numbers · admission, sizing
106. **(f) Matching-only within proven classes.** · live · MIS matching
107. **Alpha-investing ledger** for live expansion (CHECKED `research/05` short answer 10). · judging · tries ledger
108. **Terrain refusals before any expansion:** value factor, request budget, data entitlement (CHECKED `research/02` §3.4, short answer 4). · terrain, safety · instrument spec
109. **A per-unit bandit picks among matching markets,** using its own record plus the parent prior. This is his "best record" rule with room to explore. · live · inside the unit
110. **The MIS on/off test is the standing proof** of the MIS's value per unit (CHECKED `research/13` I59). · judging · QMB
111. **System 2 still uses the MIS for "when"** on its own instrument, so the MIS is not useless for System 2. · MI-class · unit spec
112. **Context-drift alarm:** CUSUM on in-context minus out-of-context R in the journal (CUSUM per `research/08`). · review, safety · nightly decay check

### I. Lenses, views and operations

113. **A stages × concerns grid replaces the flat lens list.** · operator · plan docs
114. **Add the judging and tries lens.** · judging
115. **Add the terrain lens.** · terrain
116. **Add the data and feeds lens.** · data
117. **Add the identity and lineage lens.** · identity
118. **Add the safety and independence lens.** · safety
119. **Add the durable knowledge lens.** · knowledge
120. **Add the evolution lens:** decay, retirement, upstreaming. · review
121. **Add the compute and usage lens.** · compute
122. **Market × unit match grid (roster view).** Each market shows which units' claims it matches now. · UI · MIS view
123. **Unit × hour-of-week heatmap** for his qualitative tracking. · UI · journal view
124. **Context claim card** in the same vocabulary as MIS readings, side by side. · UI · unit detail view
125. **Fortnightly qualitative review workflow** writes "where and when this unit wins" notes into its journal (his ORB-at-NY-open example). · agents, review · journal
126. **Label version stamped on every trade,** plus a replay-mismatch alarm. · safety, data · journal, QMB
127. **MIS readings stored once** per instrument × timeframe × minute in the market journal; unit journals link to them and never copy. · data · market journal

---

## 5. Questions only the operator can answer (7)

Each one is explained plainly. The panel's lean is given, never assumed. Already-queued questions (units reading MIS output, paying for data in general) are not repeated.

**Q1. What should "wins broadly" mean?**
A System 1 unit is supposed to win on many markets. There are three ways to count that.
- (a) **It wins on most markets we tried.** Seven US-dollar pairs count as about two markets, because they move together.
- (b) **It wins when all markets are added up,** and no single market carries the result.
- (c) **It wins when its market condition is present and not when it is absent, on most markets.** For example, a mean-reversion unit makes money in mean-reverting hours and not in trending ones. This tests what the unit claims about itself.

Panel lean: (c), with (b) as a safety check. All numbers stay editable. (c) needs two backtest fixes first: results in R, and market labels on every backtest trade.

**Q2. Should there be a middle level between "logic" and "one instrument"?**
Example: "mean-reversion scalper" → "FX-majors mean-reversion scalper" → "EURUSD mean-reversion scalper".
- (a) Two levels only: logic, then instrument.
- (b) Three levels: logic, then asset class, then instrument.
- (c) The class is a status ("wins across FX") and a tag, not a level of its own.

Panel lean: (c). It keeps the tree simple and still shows class-wide winners.

**Q3. When a gold child avoids the gold fix times, is it still the same logic?**
Some filters come from the instrument's own calendar: fix auctions, rollover minutes, futures roll week, trading hours. Others read the market: "only when volatility is low".
- (a) Strict: any added filter makes a new logic, a new System 1 variant.
- (b) Calendar filters from the instrument's own facts stay inside the child. Filters that read price make new logic.
- (c) Children may add any filter, and it is logged.

Panel lean: (b). The library check would enforce it, so agents cannot hide a real logic change as a "calendar" filter.

**Q4. How may a live System 1 unit reach a market it has never traded?**
Your rule is that nothing goes live without your click. Option (b) from the notes breaks that rule as written.
- (a) Only markets it was already tested on.
- (b) Any market whose costs and hours pass, starting small. This conflicts with your rule unless your click covers it.
- (c) Only after its market-condition claim is proven broadly (Q1 answer), then small.
- (d) **Shadow first:** it paper-trades the new market automatically for about 100 trades, then you get a card to admit it.
- (e) **You admit a whole class** ("FX majors"). It may then trade any member, starting at a size set from its parent's record.

Panel lean: (d) now, (e) once the class-wide tests exist.

**Q5. News: the events dimension makes news trading possible. Should it?**
Our earlier instruments study recorded "news trading off", and the news kill switch stops everything around news.
- (a) Keep it off. Events are used only to stand aside.
- (b) Allow "after-the-news" units that trade 5-30 minutes after a release, never the spike. The kill switch exempts only units you admitted for that kind of event.
- (c) Research and paper only for now; decide on live later.

Panel lean: (c). It costs nothing to study, and the guard question can wait for evidence.

**Q6. Which asset classes get the market-intelligence research first?**
- (a) **FX and gold.** Free history exists, and live trading runs through cTrader.
- (b) **Add crypto perps.** The data is free, but the exchange keeps only a few days of 1-minute history, so QMX must start recording its own now (CHECKED STATE row 02).
- (c) **Add CME futures.** Real volume and order flow, but paid data (about $199 a month, CHECKED STATE.md:152).

Panel lean: (a) plus (b), with perps recording started early because lost days cannot be bought back.

**Q7. How far should "the agent proposes a new market sensor, you approve" reach?**
- (a) You approve every sensor, including Lab experiments.
- (b) Agents may add sensors freely in the Lab. Your approval is needed only when a live unit would read one.
- (c) You approve in a weekly batch.

Panel lean: (b). It keeps your attention for things that touch money.
