# E4: logic linking, as ideas and as something the canvas can do

Round two, expansion. Written 7 Nov 2026 by the linking agent. Nothing here is ranked; the funnel ranks.

**What he asked.** "pick a methodology from maybe a given paper, link it to another one from another" (`seeds/operator-words-2026-11-03.md` M29). "These guys link logic" (M28). "Then of course, logic linking is the word" (M33). The cross-source pass the lead promised was never run (`harvest/H5-papers-articles-borrowed-logic.md` section 5).

**Short answer.**
1. The old linking joined pieces on paper and never tested the joint. A link is a claim that two things do more together than apart. That claim can be tested cheaply and nobody tested it.
2. The MT5 corpus holds the instruments for that test, in articles R5 did not read. Partial information decomposition, three-arm controls, block-shuffled nulls, propensity scores, logging design. Prior work has **zero** mentions of synergy, propensity, treatment effect, transfer entropy, tail index, roughness or strategy factorisation in `expansion/X*.md` (counted by search, section 9).
3. Linking on the canvas needs one small grammar (seven joints), one test recipe (link proof) and about a dozen fields and sockets. Most fields already exist in QML's block entry. The sockets mostly do not run yet (`unit-baseline/SWAP-CHART.md`).

**Contents.** 1 Sources and honesty. 2 The problem, diagnosed. 3 The seven joints. 4 Linked ideas. 5 Wild ideas. 6 Recipe list: the 15 workflows. 7 Recipe list: best combinations. 8 What the unit baseline and QML must carry. 9 Coverage, overlaps, seeds, gaps.

---

## 1. Sources and honesty

**Paths.** Relative to `D:\QMX-worktrees\risk-plan\tracker\risk-core\` unless stated. `md\24382:751` means line 751 of `C:\Users\Mubarak\Desktop\QMX\.worktrees\mql5-library\data\mql5-library\md\24382.md` (online at `mql5.com/en/articles/24382`). Code paths are under `D:\QMX-worktrees\bld-repair-24`.

**What I read for this.** H5; R4 workflows and combinations (`research/R4-alphaxiv/R4-alphaxiv-synthesis.md:816-903`); R5 Parts IV, V, VII; R6 synthesis; SWAP-CHART in full; M26 to M38; QML `catalogue/roles.py`, `datalevel.py`, the top of `entry.py`, two block entries, `compile/compiler.py:100-118`. A1 to A5 and X0 to X7 I **searched by term**, not read whole.

**MT5 articles.** Full-text search over all 3,128, then 55 unread articles. For those I read the opening and the closing prose, code skipped. So article claims below are the authors' own conclusions, not checked by me. Seven of the 55 were on R5's "worth a look" list (15541, 17546, 16979, 13162, 22047, 18303, 23137). Three turned out to hold nothing for this: 13647 is matrix multiplication for graphics, 18192 states strong results with no test design I could see, 22768 is platform history.

**Papers.** alphaXiv MCP, read-only, nothing changed in his library. Read through its page extracts: 2605.15108, 2604.01443, 2609.12536, 2610.01897. "Abstract only" marks the rest. One search result (2601.23172) came back with a corrupted affiliation field; I used only its abstract line. Results quoted from R4 stay the assistant's claims.

**Ids.** `row n` and `E1` to `E18` are rows of `unit-baseline/SWAP-CHART.md` section 1, and S3 or M1 its probes, unless I write "file E1-mis-sqs", the round-two file. `Xn-Hnn` are hybrids in `expansion/`, A-numbers components in `linking/components/`. `L`, `W`, `WF`, `C`, `N` are this file's own.

**Evidence words** are R5's: NONE, BT-IS (author backtest, in sample), BT-OOS, SIM, DEMO, MECH (maths or code checked). Plus PROOF (formal) and GUESS (my analogy, no source tests it).

**Skills, run headless.** `bmad-cis-problem-solving`: section 2. `bmad-brainstorming`: section 4, 5 and the seed list in 9. Its memlog and HTML were not written: the common brief allows one output file, and he said of `brainstorm.html` "I don't think I need one" (M31). Techniques used: Morphological Analysis, Forced Relationships, Concept Blending, Analogical Thinking, Cross-Pollination, Trait Transfer, Reverse Brainstorming, Failure Analysis, Predator and Prey, Entanglement Thinking, Swarm Logic, Worst Possible Idea, Kill the Crown Jewel.

**Out of scope, respected.** No dollar simulation. No argument over values: numbers quoted are the sources'. Pass rules go to methodology. Game theory stays parked (`round-2/RUN.md`); section 9 reports only what the two articles contain.

---

## 2. The problem, diagnosed

**Refined statement.** A user or copilot can put two blocks together today, and QML checks that the ports fit. Nothing checks whether the join means anything, whether it adds anything, or whether the two parts are one fact counted twice. So linking at scale produces slop that looks like work, which is the thing he built QML to stop.

**Is and is not.**

| | Is a linking problem | Is not |
|---|---|---|
| Where | The joint between blocks, papers and fields | The blocks themselves: QML's entries are strong, with goldens and class notes |
| When | Between idea and proof | Live safety: exits, kill switch, his promote click are held elsewhere |
| Who | A newcomer, a copilot, a discovery agent at speed | Him alone at a desk |
| What | "Do these fit, and did the join do the work?" | "Which idea is best?", which is the funnel's job |

**Five whys.**
1. Why did 510 hybrids need a judge to sort them? Their joints were assertions (`funnel/HYBRID-FATES.md`, as material only).
2. Why assertions? No test exists that credits a joint rather than its parts.
3. Why not? Each piece's evidence is about the piece. R4 lists its combinations as "proposed designs, not tested end to end" (`R4-alphaxiv-synthesis.md:859`).
4. Why does that bite? Adding a filter nearly always looks good, because trading less looks like safety (H5 idea 12; `md\22274` via R5). And filters overlap, so a second filter can be the first one again.
5. Root cause: **a link has no type and no null.** A block has a face. A link has nothing.

**Forces.** Pushing: his creativity ask (M50), agents' speed, a corpus full of parts. Resisting: false discovery grows with every link tried; 200 units; only 7 of 18 roles run (`compiler.py:107-117`); a compiler format bump forces new test records on every deployed unit (SWAP 2.3).

**The bottleneck.** Not ideas. It is that nothing can reach the risk places. `reads`, sizer inputs, exit inputs, halts all refuse by name (SWAP 2.4). "A copilot has no real risk choice to make from the shelf" (SWAP section 3). Fix that and linking follows.

**The contradiction (TRIZ).** More links means more chances to find something and more false finds. Resolve by separating in time and in object: search freely, and charge the proof to the joint. Run the same entries with the joint on, off, inverted and random. Every variant counts as a try, in the existing try counter (`qmx_judge/tries.py:112-150`).

**Recommended solution.** Seven named joints, a link proof recipe, a recipe kind on top of unit templates, and the seats in section 8. Rejected: a fixed library of approved combinations (it closes the canvas), and refusing bad links (a reckless setup must be expressible, so links warn and label, and only the fixed lines refuse).

**How we would know it fails.** A planted joint on synthetic data is not found. A shuffled joint is credited. Copilots stop reading warnings. Section 4 gives each idea its own kill.

---

## 3. The seven joints

Morphological analysis across every source gave these parameters: the job, the source field, the clock, the output's meaning and the joint. The joint is the part nobody named. Authors in the corpus use the same few joints again and again, so a canvas can offer them as verbs.

| Joint | Plain meaning | Example from the sources | What must match | Runs today? |
|---|---|---|---|---|
| **Pipe** | A's output is B's input | Kalman level into z-score; EVT estimate into size (`md\23278:559`) | Measure and clock | In logic slots, yes. Into sizer or exits: refused (`compiler.py:930-936`, `:482-487`) |
| **Gate** | A says whether B may act | Meta-label over a primary rule (`md\23310:255`) | A's false rate is known; beats a random gate | `filter` yes. `veto`, `arming`, `cooldown`: refused (E2) |
| **Scale** | A multiplies B's size | Volatility forecast as "the denominator" (`md\22539:572`) | A means something absolute, not just a rank (`md\21938:328`) | `sizing_modifier` refused (E2) |
| **Vote** | Several say; a rule combines | "Trading only when both agree" (`md\20238:42` via R5) | Voters are not one fact twice | `all`, `any`, `k_of_n` run (`compiler.py:104-106`) |
| **Switch** | A state picks which sub-logic runs | Trend or cycle playbook (`md\23444:53` via R5) | State is sticky and knowable in time | `regime_detector` refused; no `routes` (E2, E6) |
| **Overlay** | One thing acts across many units | Basket caps; netting; a cluster budget | Units publish intent and tags | Hook is a stub (row 6) |
| **Referee** | Never trades; judges the others | Random-control certificate; link proof | Referee cannot be tuned by what it judges | Judge exists; arms do not |

The category theory series (`md\12394`, `md\13200`) gives this a formal backbone: composition, spans (one source read two ways), natural transformations. Its trading evidence is thin. What transfers is one law, used in L13: **order of operations should not change the answer.**

**The check before any run: same boundary or different.** From 2604.01443 (PROOF, Lean, Bayesian agents with finite actions): two information sources substitute only when one moves the decision across a boundary. Sources resolving different boundaries complement. A source that cannot change the decision alone can still raise another's value. So a copilot's first question about a link is: do these two decide the same thing? Two volatility filters: same boundary, probably redundant. A volatility filter and a spread filter: different boundaries, worth trying. Its limit: miscalibrated updates break the identity, and it was not tested on markets.

---

## 4. Linked ideas

Each gives: pieces, fit, use for scalper and intraday, what it needs in QMX, evidence, null test that can kill it, and the common brief's test (**config**, **seat** meaning the core must leave room, **content**, or **other session**). Labels are hints: solid, plausible.

### A. Links that test links

**L01. Link scanner: do these two say more together?** [plausible]
- **Pieces:** partial information decomposition splits what two readings tell you about a target into unique, redundant and synergy (`md\24382:79-81`); block-shuffled null plus family-wise correction (`md\24382`, `md\24137:881`); the same-boundary check (section 3).
- **Fit:** pairwise screens cannot find "this move matters only if volume confirms it" (`md\24382:81`). Stacked filters can be the reverse, one fact twice.
- **Scalper:** every filter costs trades, so drop the redundant ones and keep pairs that add. **Intraday:** tests "opening range plus volume" as a pair, not two votes.
- **QMX:** a Lab job over blocks, reading unit trades as target. Output one row per pair. `family` and `eligible_roles` already exist.
- **Evidence:** MECH with outside cross-check, then an honest negative: no gold edge, 11 or 12 of 16 retrains found no significant synergy (`md\24382:761,769`).
- **Kill:** raw atoms do not read zero on independent columns (`md\24382`, section title at `:57`), so measure the floor first. Kill it if flagged pairs beat singles held-out no more often than pairs flagged on a shuffled control target (`md\24137:881` shows a control producing its own survivor).
- **Test:** **content** on the Lab; needs the arm seat in L02.

**L02. Link proof: the six arms.** [solid]
- **Pieces:** three-arm forecast test, reading, constant, inverted (`md\24382:751-763`, where "the inverted control is the best arm", which "a working forecast never produces"); ablation ladder restoring one input at a time (`md\24194:1160,1178`); random gate at the same rate (`md\23482` via R5); decompose bundled changes (`md\23137:180`).
- **Fit:** the old random control asks "does firing here beat firing anywhere?" The inverted arm also asks "is the direction real?". Together they credit the joint rather than the parts.
- **Arms:** A alone; B alone; A+B; A+constant; A+inverted B; A+random B at B's rate. Entries fixed where the joint is not an entry.
- **Scalper:** quick to fill, but count sessions rather than trades (H5 idea 46). **Intraday:** few trades per arm, as in 142 trades "cannot separate the arms" (`md\24382:761`), so the report must say "can't tell", not "no".
- **QMX:** arm id, parent and link id on each run; a judge view across arms. Every arm counts as a try. Pass rules: methodology.
- **Evidence:** real test design, small samples. X3-H13 holds the random arm; constant and inverted are new (search, section 9).
- **Kill:** plant an exclusive-or on synthetic data, and plant nothing. If it misses the first or credits the second, the instrument is broken.
- **Test:** **seat** for arm fields on the run record; the recipe is **content**.

**L03. A null is not one thing: name the shuffle.** [solid]
- **Pieces:** feature screening with three shuffle schemes: naive shuffling gave false-positive rates of 58 % under correlation and **100 %** under mutual information, against 3.5 to 9.3 % for dependence-respecting schemes (`md\24468:320`); block length is load-bearing (`md\24382:59`); trend scanning's t-value exceeded its nominal 5 % threshold on 99.94 % of bars of a trendless random walk (`md\23659:298`); p-value floors from too few draws (`md\24382:715`).
- **Fit:** H5 idea 12 says ship a null beside every statistic. This corrects it: a naive null can certify nothing. A published method can also be wrong by construction, and QML has cases like this already (CUSUM firing five times theory, `md\23103`).
- **Both styles:** scalper data overlaps heavily, so naive shuffles flatter it most (my inference).
- **QMX:** the null field names scheme, block length and draw count. The Lab warns on `naive`.
- **Evidence:** measured by the author on EURUSD H1 and synthetic; an unusually careful revision note.
- **Kill:** on your own instruments, if block and naive schemes agree, the extra field earns nothing.
- **Test:** **seat** (field); schemes are **content**.

**L04. Log the coin: every gate as a treatment.** [plausible, strong for 200 units]
- **Pieces:** propensity score and inverse probability weighting (`md\14360:42,398-400`); meta-learners on randomised assignment (`md\13957:451-472`); logging policy design: the data you collect decides what you can evaluate later, uniform is worst-case safe, soft-greedy gets close (2605.15108); would-have rows (SWAP row 29).
- **Fit:** would-have rows alone are biased. A gate refuses in particular conditions, so refused and taken trades differ. If a paper twin takes a logged small random share of refused entries, and writes the probability, any **future** gate can be scored offline without running it.
- **Scalper:** refusals are plentiful, so this fills fast at no money cost on the paper twin. **Intraday:** slower; pool by family.
- **QMX:** one field on decision rows, `propensity`, plus the would-have writer that does not exist (`journal_kinds/unit.py:181`). Agents get a real research asset: score a new brake on last month with no replay of the market.
- **Evidence:** PROOF and simulation for logging (recommender setting, no market test); BT for 14360. Its limit: IPW variance explodes at small probabilities, and fills differ on paper.
- **Kill:** A/A check. A gate that does nothing must score zero. A gate tested live must score near its offline score.
- **Test:** **seat**. Left out, past journals can never be used this way, so the core reworks later.

**L05. Judge a rule by replacing it, never by the trade it missed.** [solid]
- **Pieces:** inaction audit (2609.12536): oracle says "you should have traded"; in simulation 99.3 % of that missed advantage reversed when the original policy carried on, yet running the new rule at every step improved all 50 policies; no-trade filters (2606.00060, R6); turnover decomposition.
- **Fit:** an agent or copilot looking at a chart will always find missed trades. This says single-trade regret and rule replacement answer different questions.
- **Scalper:** the paper's BTC rule gained through cost, with gross down 3.71 bp a day and costs down 138.74 (`2609.12536` section 5.4). So expect "better" scalper changes to be turnover cuts, and label them so. **Intraday:** same logic for session filters.
- **QMX:** a report rule: a proposed change is judged by a full replay of the changed unit. The copilot skill refuses to present "missed trade" as evidence. Include the paper's known-perturbation check on the audit itself.
- **Evidence:** controlled simulation; one frozen replay, relative gains only.
- **Kill:** if rule replacement and isolated deviation agree on your units, drop the distinction.
- **Test:** **content** (agent skill, report) with **other session** for methodology.

**L06. Fit map: which edge does this reading belong to?** [plausible]
- **Pieces:** a regime signal that was "real, not noise" and still did not help a moving-average cross, because that strategy's money does not live in that regime (`md\23488:1068,1080`); heterogeneous treatment effect by cluster (`md\14548:539`); simple clustering often beat complex (`md\14548:537`).
- **Fit:** a reading can be true and useless to this unit. So report per reading and per unit family: where does it help, by state?
- **Scalper:** spread states against reversal entries. **Intraday:** volatility state against breakout, as the author proposes next.
- **QMX:** Lab job on unit trades plus reading values. Output feeds the copilot: "this reading has helped breakouts, not crosses." Needs reading values stored at entry.
- **Evidence:** BT, one honest test.
- **Kill:** per-state effects vanish under shuffled state labels at the same state frequency.
- **Test:** **content**; **seat** for reading values on decision rows.

### B. Size and exits

**L07. Position as a curve: the option without the option.** [plausible]
- **Pieces:** a call's delta is a sigmoid in price, so buying and selling the underlying along it emulates the option, including on spreads or other synthetics (`md\18131:42,264`); ten levels with an up table and a down table, to stop churn at level edges (`md\18131:546-557`); rebalancing loss "comparable to the premium" (`md\18363:79`); forced expiry by clock (`md\18363:613`); straddles and strangles as lists of curves (`md\18951:640`); the warning that hedging with impact changes the payoff (2609.36257, abstract only).
- **Fit:** today a unit is one entry, one stop, one target. This makes **position a function of price and time**. Risk is stated as a premium you accept, not a stop distance.
- **Intraday:** long-curve positions build along a trend day and bleed small on a range day, closed at session end. **Scalper:** probably not: the premium is paid in spread. Short-curve versions are mean-reversion ladders, reckless and expressible.
- **QMX:** a sizer that answers a target quantity per bar. Needs sizer per-bar update (row 1), partial close on the node (row 10), market entries through the path in steps, and the amend path. Large socket.
- **Evidence:** MECH plus two single demo days (`md\18363:613`). Nothing more.
- **Kill:** run the same curve with coin-flip direction: mean must be about minus cost. Then the realised "premium" must track the theoretical one for the same volatility. If it runs far above, emulation fails on that instrument.
- **Test:** **seat**: a target-position answer type. If left out, every scale-in design reworks exits and the handler. The curves are **content**.

**L08. Fit the worst move, with a refusal.** [plausible]
- **Pieces:** extreme value tail fit with shape xi, VaR, expected shortfall, says "insufficient data" out loud, and returns nothing when xi nears one (`md\23278:549,557-558`); cushion sizing needing a worst one-step move per class (2609.23272, R6); weekend crypto raising the worst move for Monday (2610.35702, R6).
- **Fit:** cushion sizing needs that number from somewhere. R6 says it must be per class and holding time. Nothing supplied it.
- **Scalper:** gap and slip allowance past stops. **Intraday:** overnight and open.
- **QMX:** a reading fed to sizer or brake. Needs `reads` (E1). Has an existing home in `reading.outputs.health`, with `min_sample`.
- **Evidence:** author's year-plus backtest: max drawdown down about 24 % on identical trades (`md\23278:559`). Trap: same trades smaller is just less exposure. Not separated by the author as far as I read.
- **Kill:** compare with a same-average-size flat cut. Must beat it on return per unit of drawdown. Then a held-out check: exceedances near the stated rate.
- **Test:** **content**; `reads` is the seat.

**L09. Calibration contract: a number that sizes must mean what it says.** [solid]
- **Pieces:** rank is not probability, and sizers use the absolute value (`md\21938:328`); isotonic through purged folds, three metrics, re-fit after shifts (`md\21938:332-336`); bet sizing and Kelly multiplier reading that probability (`md\22047:898`); conformal confidence sets as a separate way to drop junk signals (`md\18324:511,536`). Conflict kept: Conformal Kelly ranked last of 11 on Sharpe and Calmar (R6).
- **Fit:** Pipe joint with a type. Any block that outputs "probability" into a sizer brings a calibration record, or the link warns. Worst-bin error (MCE) catches a band of probabilities that gets sized badly while the average looks fine.
- **Both styles:** meta-label gates, scalper and intraday alike.
- **QMX:** output meaning on the face: `probability_calibrated` against `score`, `rank`, `percentile`. Calibrator as a block with a retest date.
- **Evidence:** BT with PBO improvement claim (`md\21938:324`); not a live test.
- **Kill:** sizing on calibrated probability against the same probabilities permuted within each trade's day, same mean size.
- **Test:** **seat** (output meaning); calibrators are **content**.

**L10. Aftershock clock.** [plausible; the science is strong, the trading test absent]
- **Pieces:** Hawkes self-exciting process, borrowed from earthquakes; core orders against reaction flow (2601.23172, abstract only); microstructure foundations of rough volatility (2608.07709, abstract only); roughness index, which failed alone as direction, 48 % held-out, PF 0.91, and whose author says use it as a filter on an independent signal (`md\24480:909,917`); duration gauge (`md\24742` via R5); the warning that common signals fake cross-excitation (2610.19428, abstract only).
- **Fit:** volatility clusters because activity triggers activity. The branching share says how much of now is reaction. After a shock, expected event rate decays by a known shape. No article I found builds this: a search for Hawkes, earthquake, aftershock or Omori hits 7 of 3,128 articles, and those I opened use it in passing, such as "market earthquakes" as a metaphor (`md\20485:178`).
- **Scalper:** high reaction share: widen or stand aside; decays: re-enter by the clock, not a fixed timer. **Intraday:** post-news re-entry timing.
- **QMX:** a block fed quote or trade arrivals, `data_level` 2 or 4. On a CFD quote feed it measures the broker's update process, so `class_meanings` must say so.
- **Evidence:** academic fit on real books; no retail or FX test read. UNKNOWN whether it survives quote feeds.
- **Kill:** shuffle arrivals within time-of-day buckets; gate at the same rate must lose to it after costs.
- **Test:** **content**. Tick-tier reading needs the data level, already in the vocabulary.

### C. Across instruments

**L11. Lead-lag with an expiry date.** [plausible]
- **Pieces:** transfer entropy with shuffle significance, lag by lag (`md\15393:950-976`); Levy area, a path signature term, as a lead-lag oscillator, stronger in a two-symbol single run, "best used as a feature", thresholds per market (`md\23548:863-879`); no correlation peak at non-zero lag means not tradeable (`md\21811:810`); cross-market links appear and vanish (2610.35702, R6); the +1 bar test (2605.04004, R6).
- **Fit:** a screen, a proof of direction, a live reading and a retest date. No prior hybrid joins them, and transfer entropy and Levy area have zero mentions in X and A files.
- **Scalper:** leader as veto, not as trigger; a trigger would need to beat the spread. **Intraday:** gold and miners, index and sector, crypto weekend into Monday.
- **QMX:** a second bound instrument, `context_needs` (refused, E6). Time alignment per `reading.time_base`. `retest_by` on the link.
- **Evidence:** MECH and synthetic for 15393; unoptimised single passes for 23548; no costs in 21811 (`:798`).
- **Kill:** random-lag series with the same pair count, family-wise. Then the +1 bar delay after costs.
- **Test:** **seat** for retest date and second-instrument input; content otherwise.

**L12. Arbitrage maths as a feed alarm.** [plausible, cheap, untried]
- **Pieces:** currency graph, cycles found with Floyd-Warshall and DFS over 25 currencies in under 100 ms (`md\19462:880`), detecting 5 to 10 potential cycles an hour in volatile periods (`:882`, demo); stale or dealer-skewed quotes (2601.13421, R6, model only); spread percentile (`md\23355`); SQS seat (E7).
- **Fit:** forced relationship. Don't trade the triangle. Read the gap between a quoted cross and the cross implied by its legs as a **measurement of the broker's feed**. A widening gap says quotes are stale or skewed right now, a question R6 says no paper answers for retail.
- **Scalper:** directly: gate entries when the feed looks stale. **Intraday:** mostly a broker monitor.
- **QMX:** FX only. Reading over `QUOTE_TICKS` across several symbols; SQS or MIS publishes it. Same graph doubles as the exposure view (`md\24392` legs, R5).
- **Evidence:** GUESS for this use. 19462 is demo, for arbitrage.
- **Kill:** gap fails to predict your own slippage and post-fill markout better than spread alone.
- **Test:** **content**, with the SQS work in file E1-mis-sqs.

**L13. The commuting check: a law for joints.** [plausible, cheap]
- **Pieces:** naturality square (`md\13200:91`): two routes through a diagram must agree; composition laws (`md\12394:64`); real bugs: gold micro futures charged Nasdaq point cost (2605.04004 via H5); USDJPY sizer error (SWAP 4.3); the make-versus-evidence trap (SWAP 2.1).
- **Fit:** convert then sum must equal sum then convert. Resample then compute should stay close to compute then resample, within a stated tolerance. A property test on links, run at check time, catches a whole class of unit and scale errors.
- **Both styles:** multi-instrument units benefit most.
- **QMX:** a new check layer beside A to F, using goldens already present. Warn, don't refuse.
- **Evidence:** maths. No source tests it in trading.
- **Kill:** seed known unit bugs. If it misses them, or fires on most good links, drop it.
- **Test:** **content** in the checker; a warning has no socket cost.

**L14. Porting by mapping: move a recipe to another class on purpose.** [plausible]
- **Pieces:** functors, structure-preserving maps (`md\13018`, `md\13033`); calendar classification by schema so EUR and USD events can be compared (`md\12950:105-121`); QML's `transfer` and `class_meanings` per class; Part II of R5.
- **Fit:** "It trades many instruments." A port says: this port maps to that; this relation survives; that one does not. So "spread percentile" on FX becomes what on an index future, and why.
- **Both styles:** a scalper recipe ported from an exchange book to a CFD loses order flow, and the map says so before a run.
- **QMX:** the copilot reads `transfer`; a port produces a new draft with a port note. Fields exist.
- **Evidence:** none in trading; the fields already encode the idea.
- **Kill:** ported recipes pass the target-class null no more often than unmapped copies.
- **Test:** **content** on existing fields.

### D. The fleet

**L15. Installed against active: who is actually firing?** [plausible]
- **Pieces:** with three model families in fixed equal numbers, wording moved one family's share of submitted orders from 17.5 % to 57.4 % (2610.01897); one-sided flow needs no coupling, only shared direction and participation (its Proposition 1); agreement reading (MASS, H5 idea 43); chorus breaker (X3-H21); basket caps (`md\24331`).
- **Fit:** diversity counted over the fleet overstates it. What counts is the mix among units with orders right now. The paper's own permutation test gives the null.
- **Scalper:** at a release many scalpers pass filters together. **Intraday:** opens.
- **QMX:** direction and family per intent at the hook (row 6). Overlay joint. An MIS-style book reading. Also fits his agents: which models produce proposals.
- **Evidence:** SIM with small language models, not units. My transfer is by analogy. The paper warns that concentration alone doesn't rank outcomes.
- **Kill:** within seed and round permutation of direction among active units. Then: does the reading predict joint-loss sessions beyond plain position count?
- **Test:** **seat**: intent with direction and family reaches a shared place.

**L16. Find the hidden families from the trades.** [plausible]
- **Pieces:** matrix factorisation over candidate strategies, white-box, "explicit guidance on which strategies to retain" (`md\20256:994`); mutual information to pick what a model can learn (`md\20317:892`, Sharpe 0.13 to 0.4, one test); residualising shared factors (A5-topup-004); try counting per family (`qmx_judge/tries.py`).
- **Fit:** block families are labels. Unit-by-session returns reveal who is really the same. That feeds cluster budgets, chorus readings and try counts.
- **Both styles:** tells a scalper fleet it holds three bets, not sixty.
- **QMX:** Lab or fleet job; a many-to-many family tag written back.
- **Evidence:** BT-IS. Selecting from the same data is a trap, so count it.
- **Kill:** factors from shuffled sessions per unit explain as much; or families don't predict co-loss next period.
- **Test:** **seat** for tags (H5 already asks); job is **content**.

**L17. Tail coupling instead of correlation.** [plausible]
- **Pieces:** copulas separate dependence shape from marginals (`md\18361`); Clayton and Gumbel read lower and upper tails (`md\19931`); mixtures fitted worse than the best single (`md\19930:1193`), so stay simple; hours-clause cluster ledger (X3-H20).
- **Fit:** two units with low correlation can still crash together. A lower-tail coefficient per pair is the number a cluster budget wants.
- **Intraday:** cross-class books. **Scalper:** weak, little overlap.
- **QMX:** book reading from aligned returns. Shrink hard; thin data.
- **Evidence:** MECH; tail estimates are data-hungry. A1 to A5 hold one mention.
- **Kill:** does not predict joint-loss days beyond plain correlation, block-shuffled pairing.
- **Test:** **content**.

**L18. Placement as a three-stage score.** [plausible]
- **Pieces:** stat-arb scoring: strategic choices first, then eliminators such as liquidity and cost, then ranking (`md\20026:524-526`); own cost cushion (`md\23299`); fit map (L06); tick tier (2607.01550); a discovered family (L16).
- **Fit:** partly answers his "where do we allocate the unit in which instrument?" (M51), a gap H5 names. Eliminators are binary and cheap; only survivors get ranked.
- **Both styles:** a scalper's eliminator is the cost cushion; intraday's is session and volatility fit.
- **QMX:** a mini app or pod setting; weights are config, not law.
- **Evidence:** BT; author admits odd results (`md\20026:504`).
- **Kill:** ranked placements beat shuffled placements no better after try counting.
- **Test:** **config** plus **content**. Game-plan numbers wait for the numbers talk.

### E. Honest negatives that link

**L19. The clock is a confound: stop assuming fancy bars help.** [solid as a warning]
- **Pieces:** on spot FX six of ten bar types collapse onto tick bars, dollar bars solve an equities problem; tick bars halve kurtosis and classic rules still sit near no-skill (`md\23310:259-261`); equalise sample sizes, purge, permutation-test.
- **Use:** a recipe preset: test a unit on tick and time bars at the same sample size, instead of a default. Saves agents a wrong turn. Held to FX, two years, classic rules.
- **QMX:** `reading.time_base` exists; `tick`-clock bars would be an input option.
- **Kill:** on exchange futures with real volume, it may reverse. Test before assuming either way.
- **Test:** **content**, shipped as a warning.

**L20. Failures as library cards.** [solid]
- **Pieces:** rough volatility failing on arrival (`md\24480:915`); PID on gold (`md\24382:769`); MIC, "all four strongest rules... covering zero" (`md\24137:881`); DMD "hopeless" past a few steps (`md\19188:1247`); deep learning lost on 2 of 3 in `md\15819:999-1001`; Wizard runs on 12 trades (`md\23144:451`); SAX "no edge" most of the time (`md\23484:772`).
- **Fit:** his idea of papers in the Library as mental models, retrieval favouring negative evidence (H5 idea 11, `conv-02`). These 2026 authors write negatives well, so a copilot can answer "someone tried that link: here is what happened and how they tested it".
- **QMX:** Library cards keyed by block and joint, surfaced in `blocks_find`.
- **Kill:** agents with the cards repeat dead links as often as agents without.
- **Test:** **content** / **other session** (QMA memory).

---

## 5. Wild ideas, labelled wild

None has a test. Each could be built by a user if the seats exist, which is the point.

| # | Idea | Pieces joined | What it would do | Kill |
|---|---|---|---|---|
| W1 | **Fleet aftershocks** | Hawkes branching (L10) + unit loss events + SIR's reproduction number, GUESS | One unit's loss raises others' loss rate. Reading above one: contagion, not coincidence. A brake with a physical meaning | Shuffle units' loss times inside sessions |
| W2 | **Call option on a unit** | Option on anything (`md\18131:42`) + unit's own equity + hysteresis tables | Size follows the unit's own curve smoothly, with a stated premium. Equity-curve trading with a price tag | Random-direction curve; a random gate at the same rate |
| W3 | **The incoherent model stands aside** | Naturality square (`md\13200`) + multi-horizon coordinates (`md\19383:976`) | Forecast one step twice and two steps once. When the routes disagree, the model does not understand now. Health reading with no labels | Random-walk model's disagreement rate |
| W4 | **Market words as agent memory keys** | SAX (`md\23484`) + Markov over words (`:772`) + hindsight memory (M35) | Agent recalls what happened the last times the session looked like `bddcbbba` | Words on permuted series recall equally "useful" lessons |
| W5 | **Straddle the release** | Emulated straddle (`md\18951`) + event windows (`chat-09`) + pre-event liquidity state (2607.09230) | Direction-free event unit, paying for a move | Same clock, non-event days; slippage will likely kill it first |
| W6 | **Evolve joints, not numbers** | Population optimisers (Dik's series, titles only) + seven joints + six arms as fitness | Search the graph shape. Every candidate counted | No-edge market: does it "find" joints? (`md\24664`) |
| W7 | **Critical slowing down** | Rising autocorrelation and variance before a shift, GUESS from physics + `return-autocorrelation`, `rolling-standard-deviation` blocks + `k_of_n` | Early warning from blocks already on the shelf | Fires as often before non-events |
| W8 | **Feed a video, get a graph** | His YouTube and TikTok ingest (M35) + seven joints + link proof | Copilot turns a guru's video into blocks and joints, then disproves it automatically | Share of ingested ideas surviving is no higher than random recipes |
| W9 | **Shape distance for model drift** | Persistence diagrams with bottleneck or Wasserstein distance (`md\23286:427`, `md\24449` via R5) | "Today is shaped unlike training", shape only | Fires equally on permuted days |
| W10 | **Biological neuron as fair value band** | Hodgkin-Huxley system whose forecasts over-amplify, read as "fair value" (`md\16979:345-347`) | A level, never a direction | Author has not run it live (`:365`); beat a moving average at the same width |
| W11 | **Agents' own fleet concentration** | L15 applied to providers + 2610.26438 fake news | Which LLM family is suddenly proposing most? A flag when one wording drives the desk | Same permutation null |
| W12 | **Arena mode** | Six arms + recipes as competitors + his "come up, tear down, enhance" (M35) | A weekly recipe tournament in paper, in the Lab | Winners do no better next period than losers (his "learning strategy" premise) |

---

## 6. Recipe list: the 15 workflows

From `R4-alphaxiv-synthesis.md:820-834`, none shown to him before. A **recipe** here means a graph of blocks and joints a user or copilot can drop on the canvas, with its proof plan. All are configuration or content. Numbers come from presets later.

**Key.** Blocks: plain name = in stdlib today; **NEW** = to write. Data uses QML's levels: CAL 0, BARS 1, QUOTE 2, DEPTH 3, TAPE 4, DERIV 5, OUTSIDE 6; HOST = position, account, record, own trades (`datalevel.py`). Fields: existing unless marked `+`, which means proposed in section 8. Socket tags: **read** (E1), **role** (E2), **sizer** (row 1), **exit** (rows 2-4, 9, 10), **halt** (row 5), **hook** (row 6), **motion** (rows 7-8), **rows** (row 29), **acct** (row 17), **ctx** (E6), **save** (2.2). "Beside" means it runs beside units, with no unit socket.

| # | Recipe | Joints | Blocks | Data | Fields relied on | Needs | Evidence warning |
|---|---|---|---|---|---|---|---|
| WF1 | Search ledger to promotion gate | Referee | **NEW** try ledger; **NEW** shrink, deflated Sharpe, PBO, e-process. `tries.py` exists | HOST, every try's net returns | `family`, `fingerprint`, `+lineage`, `+arm` | Beside; his click | Keep costs fixed before scoring |
| WF2 | Graded live demotion | Referee, Overlay | `cusum-change-point` for price side; **NEW** e-detector on own trades; `dc-decay-and-limit-report` | HOST, BARS | `min_sample`, `reading.outputs.state`, `reading.outputs.health` | halt; `risk_stop` has no producer (row 23) | Weak edges take long to detect (H5 idea 1) |
| WF3 | External breaker | Overlay | Five halts shipped; **NEW** order-boundary worst loss | HOST, QUOTE age, rejects | `reading.stale_after_s`, `component_type`, `+scope` | halt, hook, acct, kill table (row 18) | Only his hand lowers the kill switch |
| WF4 | Bucket stress isolation | Gate, Overlay | **NEW** turbulence, correlation surprise, absorption; `rolling-standard-deviation`, `z-score` | BARS across a bucket | `reading.valid_classes`, `transfer`, `min_sample`, `+scope` | read, hook, ctx | Calendar-aware baselines needed |
| WF5 | Read-only risk narrator | Referee | Agent, no block | Journals, reason codes | `sources`, `+assumes`, reason census (R15) | Beside; QMA session | No paper shows an LLM catching problems sooner (H5 idea 2) |
| WF6 | Bound approval packet | Referee | `promote.py` hash and stage | Run records | `fingerprint`, identity table (unwired, E16) | His click | |
| WF7 | Governed research pipeline | Referee chain | WF1 + WF6 + QML as typed language | Frozen data and cost versions | All of WF1, `+lineage`, `+knows_at` | save, Lab pods not on any surface | Honest evaluation "certified none" (H5 idea 8) |
| WF8 | Staged ramp ladder | Scale | `fixed-fraction-at-stop`; **NEW** step multiplier; **NEW** promotion step | HOST | `parameters`, `origin`, `+retest_by` | role, sizer, motion | "Zero" when one lot exceeds the step's budget (`convert.py:88`) |
| WF9 | Shared cost ledger | Pipe into Gate | **NEW** markout, slippage at risk, session cost estimate | QUOTE, DEPTH where real, fills | `data_level`, `class_meanings`, `+output_meaning` | rows; E13 `r_after_costs` holds R with no costs | Slippage on a CFD quote is not a book |
| WF10 | Meta-label exit and size gate | Gate, Scale | Any trigger; **NEW** triple-barrier labeler (`component_type: labeler` exists), **NEW** meta-model, **NEW** isotonic calibrator | BARS, HOST | `output`, `+output_meaning`, `+retest_by`, `confirmation_lag_bars` | role, sizer | Calibrate through purged folds (`md\21938:334`) |
| WF11 | Event calendar control | Gate, Switch | `eia-*`, `lbma-*`, `perp-funding` clocks; **NEW** per-release width | CAL, QUOTE for re-entry | `time_base`, `class_meanings`, `+knows_at` | role (`veto`, `re_entry`), E7 | Exits never blocked. "Thin for oil, gold" (H5 idea 30) |
| WF12 | Alert rationalisation | Overlay | Alert fields, no block | Alarms, reason codes | `+alert.action`, `+alert.deadline` | Beside; R16 | Numbers from other fields, none trading |
| WF13 | Interactive simulation bench | Referee | QMB + **Python** ABIDES, CrashGym | BARS to TAPE | Run stamp `+arm`, `+quote_source` | Beside; other session | Compare rules, don't forecast (H5 idea 44) |
| WF14 | Conservative parameter tuning | Pipe (motion) | `shrink_from_own_trades` motion rule exists; **NEW** bandit rule | HOST | `parameters.range`, `number kind`, `authority` | motion; rule gets only strength and R (E12) | Agents can't loosen protected fields |
| WF15 | Propose, constrain, one step | Overlay | **NEW** projection block | HOST, intents | `+scope`, `CrossUnitHook.before_order` | hook, exit, E4 | Robot simulation only; jumps break bounds |

---

## 7. Recipe list: best combinations

Chosen from about 60 in R4, 21 in R5 and 14 in R6 by how far they reach a scalper or intraday unit, and by mixing fields. The source lines are single assistant or author claims, "not tested end to end". Each ships with link proof (L02). This is a selection for a starter shelf, not a ranking; the rest stay available at the cited lines.

| # | Recipe | Joins | Style | Blocks | Data | Fields | Needs |
|---|---|---|---|---|---|---|---|
| C1 | **One cost number, two jobs** | 2605.04004 + 2606.00060 (R6) | Scalp, intraday | **NEW** gross-edge over friction; hurdle filter | BARS, cost record | `+output_meaning`, record costs | E13, role |
| C2 | Two-speed drift | `md\23103` + R2 + Basel zones (R5 V.4) | Any | `cusum-change-point`; **NEW** trade-side CUSUM | BARS, HOST | `min_sample`, per-instrument calibration `+` | read, role |
| C3 | Restore ladder | `md\23315` + `md\15085` + `md\22833` + recloser (R5 V.5) | Any | **NEW** half-open state | HOST | lifecycle states `+` | halt |
| C4 | Live cost monitor | `md\22998` + `md\23355` + `md\24251` + `md\23299` (R5 V.7) | Scalp | `percentile-of-own-history`; **NEW** cushion, anomaly | QUOTE, fills | `reading.tier` | rows, read |
| C5 | Backtest validity stamp | `md\24562` + `md\15330` + `md\15360` + `md\22772` (R5 V.8) | Scalp | None: run record | Tester metadata | `+real_tick_share`, `+quote_source` | Run stamp |
| C6 | Exposure ledger | `md\24392` + `md\23322` + `md\24243` + `md\24202` (R5 V.1) | Book | **NEW** legs, denoise; curvature only as an alarm | BARS | `+scope`, `transfer` | hook, acct |
| C7 | Risk-as-output accelerator | `md\24331` + `md\22187` + `md\22684` (R5 V.2) | Intraday | **NEW** implied-risk cap | HOST | `+scope` | sizer, E4 |
| C8 | Concurrency-aware scalpers | `md\21824` + `md\24331` + `md\23629` (R5 V.11) | Scalp | **NEW** active-bet divider | Intents | `+intent.direction`, `+family_tag` | hook |
| C9 | Trade-rate-scaled breakers | `md\21313` + R2 + `md\20449` (R5 V.14) | Scalp | `session-fill-limit-halt` | HOST | `min_sample`, `+rate_of_own` | halt |
| C10 | Immune brake | IV.6 + `md\24251` + `md\23983` + `md\22940` + `md\21235` (R5 V.19) | Any | `k_of_n` on weak signals; **NEW** accumulator | BARS, QUOTE, HOST | `reading.outputs.health` | role, halt. GUESS for risk |
| C11 | Session-open unit | `md\23226` + `md\17745` + `md\18821` + `md\16171` (R5 V.16) | Intraday | `initial-balance-*`, `session-running-*`, `vwap-session-anchored`; relative volume | BARS | `transfer`, `class_meanings`, session clock | E6 for `sessions` |
| C12 | Regime age | `md\24460` + `md\23482` + `md\21833` (R5 V.17) | Intraday | **NEW** duration reading | BARS | `+output_meaning` (age, probability) | role, read |
| C13 | Exit calibration pipeline | `md\22855` → `md\23245` → `md\24466` → `md\24106` → `md\22275` (R5 V.9) | Any | `offset-gated-trailing-stop`, `stepped-profit-stop`; **NEW** hazard | HOST (MFE, MAE) | `mirroring`, `state_bound` | exit, E15 |
| C14 | Order flow where it pays | OFI/MLOFI + session cost + hard budget (R4 E) | Scalp, exchange only | **NEW** OFI, MLOFI | DEPTH, TAPE | `data_level`, `transfer` not CFD | Other session per his note |
| C15 | Execution-risk score | 1011.6402 + 2508.06788 + 2607.09230 (R6) | Scalp, intraday | **NEW** three-word liquidity state | DEPTH | `reading.valid_classes` | read; SQS |
| C16 | Don't queue at the bell | 2502.18625 + 2607.09426 (R6) | Scalp | **NEW** entry offset | QUOTE, fills | `+entry_offset`, markout | E14 |
| C17 | Hard cap, soft worry | 2609.23272 + 2608.00127 (R6) | Book, unit | **NEW** cushion, worry line | HOST | Style tag `+` | sizer, acct |
| C18 | Monday worst move | 2609.23272 + 2610.35702 (R6) | Index, metals | **NEW** weekend gauge | BARS across class | `+retest_by` | read, ctx |
| C19 | Decay and bucket together | Conformal Kelly + CUSUM + bucket gate (R4 chat 08) | Any | as named | HOST, BARS | `min_sample` | role, hook |
| C20 | Regimes cut, never re-weight | 2402.05272 + 2610.27751 (R6) | Book | **NEW** jump model | BARS | `+output_meaning` | read, hook |
| C21 | Start diagonal, shrink on coupling | 2604.23833 + 2606.12612 + 2002.02008 (R6) | Book | **NEW** CRISP knob | BARS | Book kind (shell today) | Book |
| C22 | Fee-aware rare-event classifier | Label Unbalance + FinRL-X + 2610.05077 (R4 22d) | Scalp | **NEW** labeler | BARS | `+output_meaning` | role |
| C23 | Evidence record | MarketSenseAI + OpenPM + 2610.26438 (R4 22c) | Any | Agent record | OUTSIDE | `+knows_at`, source and feed ids | read |
| C24 | Tuner pair | TPE-AS + Conservative + Rotting Bandits (R4 chat 17) | Any | **NEW** motion rule | HOST | `parameters.range` | motion, E18 |
| C25 | Forward-looking stress | `md\23734` + `md\24742` + `md\22938` + `md\22940` (R5 V.12) | Scalp, intraday | **NEW** implied ratio, duration gauge | QUOTE, OUTSIDE | `reading.lag_bars` | read, role |
| C26 | Statistics apart from the trip | e-values + burn alerts + hard limits (R4 chat 07) | Any | **NEW** burn permit | HOST | `+alert.*` | halt |
| C27 | Crowding test before promotion | ABIDES + FARSIGHT + AllPath (R4 chat 21) | Fleet | External | TAPE | Run stamp | Beside |
| C28 | Fast loop, slow agent | 2610.12988 + 2609.19705 + 2610.26438 (R6) | Crypto, any | Halts plus states | HOST, OUTSIDE | Conflict A (H5): cut-only against add | halt, read |

**New recipes from this file.**

| # | Recipe | From | Style | Blocks | Data | Fields | Needs |
|---|---|---|---|---|---|---|---|
| N1 | **Link proof**, six arms | L02 | Any | Referee | Any | `+arm`, `+link_id` | Arm runs |
| N2 | **Pair scan** before stacking filters | L01 | Any | **NEW** PID scan | Any reading, own trades | `+null`, `eligible_roles` | Beside |
| N3 | **Coin-logged paper twin** | L04 | Scalp | None | Decision rows | `+propensity` | rows, paper lane |
| N4 | **Intraday long curve**, sigmoid with expiry | L07 | Intraday | **NEW** curve sizer | BARS, HOST | `+answer: target_quantity` | sizer, exit, row 10 |
| N5 | **Fitted tail for the cushion** | L08 | Book, unit | **NEW** EVT reading | BARS | `reading.outputs.health`, `min_sample` | read |
| N6 | **Calibrated meta-gate** | L09 + WF10 | Scalp, intraday | Calibrator | BARS, HOST | `+output_meaning`, `+retest_by` | role |
| N7 | **Aftershock cooldown** | L10 | Scalp | **NEW** branching reading | QUOTE or TAPE | `data_level`, `class_meanings` | role `cooldown` |
| N8 | **Leader as veto, with expiry** | L11 | Intraday | **NEW** transfer entropy screen, Levy reading | BARS on two symbols | `+retest_by`, `time_base` | ctx, read |
| N9 | **Feed-gap alarm** | L12 | FX scalp | **NEW** implied-cross gap | QUOTE on three symbols | `transfer: fx only` | read; SQS |
| N10 | **Active mix reading** | L15 | Fleet | **NEW** overlay | Intents | `+intent.direction`, `+family_tag` | hook |
| N11 | **Three-stage placement** | L18 | Any | Mini app | Costs, fit map | Weights are config | Mini app |

**What it looks like to a newcomer.** Pick "Leader as veto". The canvas shows two blocks and a Gate. The copilot says: "This needs bars on two symbols, your broker has them. Both read the same decision? No, different boundaries. The link needs a retest date. Proving it runs six arms; I'll count those as tries. Someone tried this on gold and miners with no costs in the test; card attached." The user can ignore all of it and still run it in paper. Only promotion stays his.

---

## 8. What the unit baseline and QML must carry

**Rule for this table.** Link safety means labelled and tested. Links warn and never refuse, except at the fixed lines: agents never touch money, only he promotes, exits never blocked, only his hand lowers the kill switch. A reckless link stays expressible.

### 8a. Already there: don't rebuild

From entries such as `qml/src/qml/blocks/stdlib/cusum-change-point/1/entry.json` and `catalogue/entry.py`: `sources`, `family`, `eligible_roles`, `transfer` per class (native to not_assessed), `class_meanings`, `inputs[].data_level`, `output.type`, `output.measure`, `min_sample`, `warm_up`, `confirmation_lag_bars`, `mirroring`, `state_bound`, `reading.{tier, concern, time_base, lag_bars, valid_classes, stale_after_s, outputs.health}`, `golden`, `fingerprint`. Combiners `all`, `any`, `k_of_n`. Motion with cadence and shrink. `unit_check`, `blocks_find`, `blocks_check`. `_templates()` lists a folder, so a new JSON is a new template (SWAP section 3). QML is further along for linking than H5's table implied.

### 8b. Fields to add to the block entry

| Field | What | Why linking needs it | If left out |
|---|---|---|---|
| `output_meaning` | `probability_calibrated`, `score`, `rank`, `percentile`, `multiplier`, `permission`, `state`, `level`, `age` | A Scale joint on a raw score sizes nonsense (`md\21938:328`). `measure: ratio` doesn't say this | Slots have no type check today: a trigger compiles in the sizer (S3) |
| `assumes` | Short list: iid, stationarity, real volume, central book | CUSUM's iid assumption, 5x firing (`md\23043:639`, `md\23103`) | Copilot can't warn before running |
| `null` | Scheme, block length, draws | L03 | Naive nulls pass; H5 idea 12 is hollow |
| `evidence` | Label, instruments tested, source of the label | `Status` stops at `implemented`; "nothing computes" the next rungs (`entry.py:16-17`) | Copilot can't tell a proof from a claim |
| `retest_by` | Date or trigger; on blocks and on links | Links vanish (2610.35702) | Old links run for ever |
| `knows_at` | Event time against available time, for readings and agent evidence | Leakage must be blocked by tools (H5 idea 1) | Look-ahead in agent-built links |
| `decides` | Which decision boundary it speaks to: direction, whether to trade, size, exit, data quality | Same-boundary check, section 3 | Stacking redundant filters |

Add these where they don't move compiled fingerprints if possible. A format bump forces new test records on every deployed unit (SWAP 2.3). Whether `block_fingerprint` covers the whole entry: UNKNOWN; check before choosing.

### 8c. Sockets and records: core rework if left out

| Seat | Now | Why | From |
|---|---|---|---|
| **Fed inputs to sizer, exits, halts** | Refused, `compiler.py:930-936`, `:482-487`, `:902-903`. Moved numbers refused M1 to M5 | No link reaches risk without it. Every recipe marked read, sizer, exit, halt waits on this | SWAP rows 1-5, 7 |
| **`reads`** | Refused, `:900-901` | Readings are half of all recipes | E1 |
| **Roles** | 7 of 18 run. `veto`, `sizing_modifier`, `regime_detector`, `cooldown`, `invalidation`, `re_entry`, `arming`, `timeout` refuse | Gate, Scale and Switch joints | E2 |
| **Target-position answer** | Unit asks for one close; one position per market | L07, ladders, partials, netting later | Rows 9, 10; E4 |
| **Link record** | None | A link is a graph edge with joint, `retest_by`, parent runs | L02 |
| **Arm fields on run record** | None | Link proof; every arm counted as a try (`tries.py`) | L02 |
| **`propensity` plus would-have writer** | Kind declared, no writer | Past journals become a research asset. Can't be back-filled | L04, row 29 |
| **Reading values on decision rows** | `numbers_in_force` exists; readings don't run | Fit map, replay | L06 |
| **Intent with direction and family at a shared place** | Node stub, QMB none | Overlay joint, active mix | L15, row 6 |
| **Second instrument input and aligned clocks** | `context_needs`, `routes` refused | Cross-market links | L11, E6 |
| **Many-to-many tags** | H5 asks; not read in code | Families that overlap; written back by a job | L16 |
| **Save a block** | "An agent can draft and check a block and cannot land it" | No canvas without it | SWAP 2.2 |
| **Identity wired** | No `classify(` found | Is this edit a new unit? Link swaps need an answer | E16 |
| **Recipe kind** | `template` kind is a shell | A recipe = template + joints + required fields + proof plan. Could extend the unit template JSON rather than a new kind | SWAP section 3 |
| **Protected fields** | Fixed lines live in code and his hand | An agent can't link around limits | H5 idea 38 |

### 8d. Copilot and agent rules, as a skill

These are **content** in `qmx-agents/plugin/skills/build-unit/SKILL.md` terms:
1. Name the joint before you wire it.
2. Check the data level and class. `transfer: not_assessed` means say so.
3. Check same boundary against different boundary.
4. Warn on: no `null`, expired `retest_by`, a score piped into a size, a proof resting on naive shuffling.
5. Run link proof before claiming the link did anything. Every arm is a try.
6. Never present a missed trade as evidence (L05).
7. Report "can't tell" when arms are thin. Never read lower drawdown from less trading as skill.
8. Cite the failure card if one exists.
9. Warnings go to the user. Do not refuse his or a user's reckless link.

### 8e. Against the brief's test

**Seats:** 8b fields, 8c rows. **Config:** weights, recipe choices, preset numbers, which proof arms to run. **Content:** the recipes in 6 and 7, nearly all ideas in 4 and 5. **Other sessions:** pass rules (methodology), memory and cards (QMA), SQS and MIS details (file E1-mis-sqs), fleet (file E5-fleet-selfconfig-dev), pods (file E2-pods-miniapps). **Hand-off for methodology:** L02, L03, L05 are inputs for "how a unit is proven valid per type".

---

## 9. Coverage, overlaps, seeds, gaps

### What was new against prior work

Search counts, hits in `expansion/X*.md` / `linking/components/*.yaml`:

| Term | X | A | | Term | X | A |
|---|---|---|---|---|---|---|
| propensity | 0 | 0 | | synergy (`synerg`) | 0 | 0 |
| treatment effect | 0 | 0 | | tail index, GPD, extreme value | 0 | 0 |
| transfer entropy | 0 | 0 | | rough volatility | 0 | 0 |
| Levy area, path signature | 0 | 0 | | Hawkes | 0 | 0 |
| matrix factorisation | 0 | 0 | | category theory | 0 | 0 |
| mutual information | 0 | 0 | | isotonic | 0 | 0 |
| copula | 0 | 1 | | lead-lag | 0 | 3 |
| conformal | 3 | 17 | | ablation | 15 | 12 |
| sigmoid | 2 | 5 | | no-trade band, hysteresis | 19 | 36 |

Term search misses synonyms, so "zero" means not by that word. Overlaps to keep in mind: random-control certificate X3-H13 (L02 extends it), chorus breaker X3-H21 (L15 sharpens it), cushion clip X3-H25 (L08 feeds it), ablation for agents A4-137 (L02 applies it to links), R5 V.13 controller with fair test.

### Coverage of the corpus

| Series | Parts | Read here | What it gave |
|---|---|---|---|
| MQL5 Wizard Techniques | about 100 | 2 + titles | Socket precedent: Signal, Trailing, Money classes joined per article (`md\18776:404`). Pairing method. Thin tests (`md\23144:451`) |
| Neural Networks Made Easy / in Trading | about 145 | 2, both cut before their test parts | Paper-to-code habit. **Largest unread link source** |
| Category Theory | 23 | 3 | Vocabulary only |
| Feature Engineering for ML | 14 | 3 | Screen, trend-scan flaw |
| ML Blueprint | 21 | 4 | Calibration, bet sizing, bagging lesson |
| Overcoming the Limitation of ML | 9 | 3 | Strategy selection, horizons |
| Beyond GARCH | 8 | 2 | Volatility as the denominator. Verdict section not reached in my extract; UNKNOWN |
| Causal inference (Dmitrievsky) | 4 | 3 | Propensity, clusters |
| Trading Options Without Options | 4 | 3 | L07 |
| Bivariate Copulae | 3 | 1 | L17 |
| Defining your Edge | 6 | 1 | Ablation stance |
| Population optimisation (Dik) | many | Titles | W6 |
| Quantum items | about 10 | Titles | Not read. UNKNOWN value |
| Price Action Toolkit, Replay, DoEasy, Automating Strategies | 200+ | Titles | Tools, not linked logic, from titles alone |

So: 55 articles sampled on top of R5's 150, and the whole corpus searched by term. Most of the corpus remains unread, which is honest for one agent. He said so too: "I don't think one agent can handle it" (M29).

### What his words predicted, and a finding

M28: authors say markets act "as a neural network" and borrow from other sectors. Confirmed in spirit. The 2026 articles add what the older ones lack: they borrow the **test** too. Compare the promotional framing in `md\18192:40,659` with `md\24382:763`, `md\23488:1078`, `md\24194:1178`, `md\24480:915`. Prefer the second kind as sources for block authors.

### Game theory, flagged only

`md\15541` weights strategies with what it calls Nash equilibrium and an HMM over regimes; recalibration every few months (`:1234`). `md\17546` is a Q-learner over seven pairs with Nash as selection. `md\15819`: deep learning helped one of three. Neither studies other players as a trader would mean it. M51's question stays open, parked.

### Raw seeds

Unvetted; for the funnel to mine, in the spirit of "some might come out as seeds" (M29). Pieces are named so a later agent can find them.

**Forced pairs: tests onto blocks already on the shelf**
1. `permutation-entropy` + `percentile-of-own-history`: disorder gate per instrument.
2. `kalman-local-level` + `cusum-change-point`: level shift alarm on a filtered series.
3. `hurst-exponent` + `variance-ratio` + `dickey-fuller-statistic`: three-way vote on trendiness; PID shows if they are one fact.
4. `half-life-of-mean-reversion` as `time-exit-bars` value: holding time from the market (needs motion on exits).
5. `efficiency-ratio` as Scale on `offset-gated-trailing-stop`.
6. `choppiness-index` Switch between two sub-logics.
7. `tpo-value-area-high` + `tpo-value-area-low` as stop location.
8. `momersion` + session clock: intraday mean-reversion window.
9. `garman-klass-volatility` against `close-to-close-volatility`: their gap as a reading of jumps.
10. `session-running-range` over `atr-wilder`: day-type word.
11. `perp-funding-settlement-clock` as a Gate on crypto scalpers.
12. `return-autocorrelation` sign as Switch for trend or fade.
13. `trend-floor-from-record` copied to size: own record sets a size floor.
14. `value-above` + `rolling-standard-deviation`: self-scaled thresholds everywhere.

**Medicine**
15. Stopping rules for benefit, not only harm: promote early on strong evidence (BOIN and Lan-DeMets, H5 idea 22).
16. Late-onset toxicity for open trades; count damage when closed.
17. Run-in period: each new unit gets a placebo phase with zero-size twin.
18. Number needed to treat: how many refusals to avoid one bad trade.
19. Dose-response for brakes: three strengths; a real brake shows a curve (extends L02).
20. Crossover design: same market periods, unit with and without a brake, swap order.

**Reliability, aviation, plants**
21. Pre-mortem card on each link, written by the copilot.
22. Checklist blocks that must be read at each session start (`md\22833` discipline).
23. Black-box recorder: last N decisions kept at full detail on any trip.
24. Shelving with an expiry for alerts, ISA-18.2 (H5 idea 17), applied to link warnings.
25. Weibull life for an edge: survival curve of units by family (`md\24106` applied to units).

**Ecology and epidemiology**
26. Carrying capacity per instrument: how many units before they eat each other's edge (2601.13421).
27. Niche overlap index among units, Pianka, GUESS.
28. Keystone unit: remove each unit in replay; who hurts the book most?
29. Succession: fresh units get small niches first.
30. Herd immunity: a share of the fleet with a hedge makes contagion die. GUESS.

**Information, signals**
31. MIC against distance correlation gap to sort non-linear pairs (`md\24137:879`).
32. Compression ratio as a day-type reading (`md\21372`).
33. Spectrum drift: dominant cycle moved, retest (`md\23444`).
34. Wavelet thresholding as a generic denoise Pipe (`md\23013`), with a shuffle.
35. Catch22 as MIS vocabulary (`md\23488`), for file E1-mis-sqs.
36. Dynamic mode decomposition for very short forecasts only (`md\19188:1247`).
37. Mann-Whitney between two periods before pooling trades (`md\23328:935`), and Hodges-Lehmann for size (`:945`).
38. Kruskal-Wallis across regimes (`:945`).
39. Sequential uniqueness: throttle sample count by uniqueness when training (`md\23137:178`).

**Finance theory**
40. Covered-call unit: short-curve overlay on a trend unit (`md\18951`). Reckless, expressible.
41. Collar: long curve plus short curve around a position (`md\19704`).
42. Unit as a seller of insurance: which units are short tail? Read from their trade shape.
43. Payoff-shape tag on each unit: concave or convex, measured. A book needs both.
44. CFTC positioning as a slow reading, weekly (`md\18303:571`).
45. Implied-minus-realised as a budget (`md\23734`), not timing.

**Agents and canvas**
46. Copilot proposes three links: one same-boundary, one different, one wild. User sees the difference.
47. "Explain this link like I'm new" button reading `assumes` and failure cards.
48. Recipe diff: what changed from the parent and which arm paid for it.
49. Link heatmap: blocks by families, cells coloured by tested synergy, across all users' Lab runs.
50. Recipe remix: user replaces one node; proof re-runs only arms it affects.
51. Bounty: agent gets credit only for links surviving a retest date.
52. Discovery agent forced to start from a failure card.
53. A devil's advocate agent writes the null for each link, blind to the story (H5 idea 40).
54. Wizard-style pattern bitmap: a block with many patterns exposes each as a separate port (`md\18776:166`).
55. "Repair only the patterns that failed" workflow (`md\18776:166`), trial-counted.
56. Agent reads a paper and outputs joints, never code (his M35 ingest).
57. Paper-to-block card: what we took, what we refused to take.
58. Library "shelf of nulls": reusable null runs per instrument, so most links get a fast first answer.
59. Shared floor table: noise level of each statistic per instrument, computed once (`md\24382:57`).

**Reverse brainstorm: how to guarantee slop, and the flip**
60. Link everything to everything, then pick the best curve → count tries.
61. Use the same data to pick and prove → locked hold-out.
62. Stack filters until drawdown looks small → the random arm.
63. Call a score a probability → `output_meaning`.
64. Port by copy → L14.
65. Trust a famous method's threshold → L03, `md\23659:298`.
66. Let the agent grade its own link → the Referee joint; Steward (H5 idea 4).
67. Never expire a link → `retest_by`.
68. Hide refusals from arms, compare with survivors only → write would-have rows.
69. Compare unequal samples across clocks → `md\23310:261`.
70. Change two things at once and credit the famous one → `md\23137:180`, `md\24194:1176`.
71. Trust the tester's "real ticks" → C5.
72. Average away the worst probability bin → `md\21938:336`.

**Scalper-specific**
73. Spread-state word plus time-of-day as the only context: smallest possible scalper recipe.
74. Rate-scaled cooldown from own trades (R5 V.14) + aftershock clock.
75. Netting-aware recipe: two opposing scalpers publish, one nets (H5 idea 31).
76. Reject and requote streak as a gate (H5 idea 32).
77. Markout-driven maker or taker switch (2502.18625).
78. Random jitter on entries as a block, with a test that jitter costs nothing (2607.09426).
79. Min-hold block, labelled as a turnover cut (2609.12536).
80. Fee-threshold labels for any scalper's training (Label Unbalance, R4).

**Intraday-specific**
81. First half hour into last half hour (Gao et al., R4 seeds) with a session clock, ported per class.
82. Day-type Switch: range day or trend day by initial balance extension.
83. Curve sizer closing by session end (L07).
84. Monday overlay (C18).
85. Overnight tail reading before holding past the close (L08).
86. Gap accept or reject (QuantaAlpha, H5 section H) as a Switch.
87. London flip with a delay (2605.04004, H5).
88. Larry Williams series patterns as a shelf of triggers, each with a null. 17 parts unread.
89. Regime age tapers adds (R5 V.17).
90. VWAP distance as a Scale on mean reversion.

**Book and fleet**
91. Hidden-family budget from L16 replaces labels.
92. Tail-coupled pairs share a cap (L17).
93. Active mix gate only at releases (L15).
94. Effective bets on families discovered, not labelled (A5-topup-001 + L16).
95. Exposure graph shows cycles among unit positions (`md\19462`, `md\24392`).
96. Each new unit must add a direction the book lacks, as a placement eliminator.
97. Fleet-level inaction audit: did stopped units' replacements do better?
98. Agent-run weekly link rescan, publishing only changes.
99. Retire links in order of expiry and failure, automatically to paper, with his click for any live change.
100. A fleet "boredom" alarm: nobody trades when they normally would. Often a data fault.

### Gaps left

- **Actual measurement.** No link here has been run through QMB; sockets are not there, and this agent may not run things. Every idea stays an idea.
- **Retail FX.** Still nothing proves scalping survives spreads (R6). L12 and N3 are ways for QMX's own logs to answer.
- **Energy.** Nothing new read.
- **alphaXiv assistant's chat linking.** Not used, by the lead's decision (`round-2/RUN.md`). A chat pass on "which of these join well" remains open if he wants it.
- **The rest of the corpus,** above all Neural Networks in Trading's paper translations and the Wizard pairings.
- **`block_fingerprint` coverage** and **whether a Library-held block runs end to end** (SWAP section 3): UNKNOWN.
