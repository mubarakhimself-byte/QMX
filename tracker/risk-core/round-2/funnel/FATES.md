# Fates, round two: one row per idea

Fable funnel judge, 7 Nov 2026. Companion to `FUNNEL.md`. One row per idea across the harvests (H1 to H5), the round-two expansions (E1 to E5) and the 510 hybrids (X0 to X7). Nothing here was cut by dollars and nothing kept out of politeness. Each row: id, one line, fate, evidence.

**Fate words.**
- **core**: a socket, input, record, hook or invariant the first increment must carry; the `FUNNEL.md` section 3 row is named (S, I, R, K, V).
- **default block**: a block switched on in the first baseline (`FUNNEL.md` 4.1).
- **template**: switched on or present in a shipped template (`FUNNEL.md` 4.2: A = `scalper-mr`, B = `intraday-trend`, orb variant, canary).
- **content**: a block, preset, pod, workflow or document someone adds later on a seat that exists; no core change.
- **other: <session>**: methodology, agentic (the agentic upgrade), UI, repair, release, numbers (the numbers talk).
- **parked: numbers**: a value or an argument about values.
- **dropped: <reason>**: with the reason; dropped ideas keep their history in the ledger's `seen_values`.

**Evidence words.** BUILT, REAL (field named), MODEL (our simulation), PROPOSAL, GUESS, RULING (his words), UNKNOWN. Several labels may apply; the first is the strongest honest one.

**Counting.** Rows are placed, not kept or dropped. `FUNNEL.md` Appendix B answers "you kept everything again".

---

## H1: the market side (`harvest/H1-market-side.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| H1-1 | MIS as router with a door to widen a unit's markets | core I5 (allowed, home, active); the finder is content (E1 MIS-3) | RULING (M5); PROPOSAL; MODEL on lag |
| H1-2 | Units read MIS readings, each with a stated fallback | core S8 | designed, REFUSED today |
| H1-3 | Contexts, not sessions; settings keyed to a word | content on S8; context key reserved in the override chain | PROPOSAL; RULING (M10 accepted it) |
| H1-4 | A named reading allowed to change size, with range and reason | core S2 | PROPOSAL |
| H1-5 | Mini apps and agents as publishers of readings | core S8 (open `source`, publisher on reads) | RULING (M50); PROPOSAL |
| H1-6 | Agents write a dated reading, scored like a sensor | other: agentic; needs R13 | PROPOSAL |
| H1-7 | Reading organisation: clock tier and data level on each reading, class as a pack | content (MIS app, card shape) | PROPOSAL with hard-case tests |
| H1-8 | Stamped history and an as-of question | core R13 | MODEL (76 % flattery in simulation); logic |
| H1-9 | Proving the MIS helps at all (with and without, shuffled readings, noise meter) | other: methodology; content job | PROPOSAL |
| H1-10a | Finder job: where else is this true now | content (E1 MIS-3) | PROPOSAL |
| H1-10b | Stand-aside readings | content | PROPOSAL |
| H1-10c | Inverse MIS: states where every unit loses | content | PROPOSAL |
| H1-10d | Unit as sensor; MIS reads which units win where | content (E1 P13) | PROPOSAL |
| H1-10e | Market twins: test a proven unit on a look-alike market first | content | PROPOSAL |
| H1-10f | Session measured, not assumed | content | PROPOSAL |
| H1-10g | State age and transition chance | content | PROPOSAL |
| H1-10h | Lag-to-hold admission rule for readings | content (card field) | PROPOSAL |
| H1-10i | Sensor scout agent turns articles into reading cards | other: agentic | PROPOSAL |
| H1-10j | Teach the MIS: a dated human note becomes a shadow reading | content on S8 | PROPOSAL |
| H1-10k | Market card, weather report, opens page, chart overlay | other: UI | PROPOSAL |
| H1-10l | Almanac and per-class inefficiency hunts | content (Lab) | PROPOSAL |
| H1-10m | Crowding counts, dispersion, joint-state correlation, lead-lag | content (PC-side readings) | PROPOSAL |
| H1-11 | Two hourly tables per instrument: volatility and cost; refuse when missing (refusal is a block) | core I2, I4 | REAL on cost shape (NBER); cells synthetic until fills |
| H1-12 | Cost windows found by data; sniping as a counted slice | core R16 window card, S9, R6; finding is content | REAL on cost and activity; no window-sizing study |
| H1-13 | SQS as sensor, not only gate | core S6 and the node sensor | BUILT rule text, never run on a venue |
| H1-14 | SQS K-of-N class caution | content (isolation evidence) | REAL mechanism (liquidity commonality); PROPOSAL rule |
| H1-15 | Spread gate against the instrument's own percentiles, two windows | content block (SQS-1 variant) | author backtest |
| H1-16 | Five execution gates: can the market fill an order now | content, shadow (SQS-3) | author backtest; filters screen winners |
| H1-17 | Cost nomogram: size shrinks before the SQS blocks | content, off (SQS-4 on S2) | author backtest |
| H1-18 | One execution-risk score or three-word liquidity state | content reading | author backtest (crypto) |
| H1-19 | The fast MIS tier is SQS generalised: now versus usual | core I6 (one curve artifact) | PROPOSAL |
| H1-20 | Venue rule: never call a quote a book | core I4 (book-or-quote flag) | REAL for exchange books |
| H1-21 | Broker and venue quality record; probing capacity | core R7; probe content | demo measurements; idea |
| H1-22 | Scope keys: class, region, currency, underlying, session | core S11 | design |
| H1-23 | His isolation protocol: two tells, graded, lifecycle, accuracy record | content pod block; core R14 | daily-data author backtests; no live precedent |
| H1-24 | Unknown is not calm | core S10 | design logic |
| H1-25 | How does the MIS adjust: it doesn't; stickers refuse, the finder skips | decided (D24); UI must draw it | RULING; decision text |
| H1-26 | Risk-off tells, fast and slow, no master score | content | author backtests |
| H1-27 | Agent isolation over days by card | other: agentic; door K2 core | PROPOSAL |
| H1-28 | Budget follows what's open; weekend crypto raises Monday caution | content pod rule | author backtest, short sample |
| H1-29a | Region shift without budget rotation | content | old rule, killed in July |
| H1-29b | Peer ejection | content | REAL (Envoy) |
| H1-29c | Immune brake | content | GUESS |
| H1-29d | Chorus | content | old rule, never ran |
| H1-29e | Stack breaker | content | PROPOSAL |
| H1-29f | Curvature and spectral detectors | content, null beside | author |
| H1-29g | Bulkhead compartments of open risk | content | REAL elsewhere |
| H1-30 | News as measured impact with driver tags beyond currency | core I4 tags, S10; measurements content | REAL old price-discovery; author backtests |
| H1-31 | News windows in the customisable layer; kill switch keeps the hard kill | core S10 tolerations | RULING (M49, C28) |
| H1-32 | Event policy details: flat through, cool down, re-enter on spreads, never widen a stop in news | content; V1 holds | E-mini author study |
| H1-33 | News as something to trade; event clock | content; core I7 event clock | author backtest (daily stocks) |
| H1-34 | News agents with limits (typed, expiring, provenance, one-item cap) | other: agentic; door core | controlled test; simulation |
| H1-35 | Testable news rules: versioned event file, collision rate | content | author |
| H1-36 | Session, open and fix minutes as caution windows with measured widths | core S9; widths content | fix behaviour REAL; no width derived |
| H1-37 | Day boundary, rollover, weekend, holidays, DST as contracts | core I4, R5 | design; market facts |
| H1-38 | ORB as a family across opens | template (orb variant); core I9 family tag | REAL (stocks in play, one period) |
| H1-39 | In-play gate: RVOL, tick rate on FX | content; needs I7 (Q2) | one vendor study |
| H1-40 | Activity sessions for 24/7 markets | content calendar | author backtests |
| H1-41 | Persistence readings at the router's timeframe, mid prices, bounce check | content (MIS pack) | BUILT blocks; MODEL lags |
| H1-42 | Old physics as a quarry: Chaos, Ising, entropy, compression | content with null floors (E1 P6, P14) | no trading evidence |
| H1-43 | Regimes cut, they don't choose | content class cap | author backtest (indices) |
| H1-44 | Macro as a slow governor | content (macro desk) | idea |
| H1-45 | Change detectors, each with one job; regime-age taper | content | author backtests; controlled random-brake test |
| H1-46 | Order-flow and intraday seeds (U-A3-01 to 30) | content; see UB rows | as source reports |
| H1-47 | Crypto as the 24/7 spine | content (crypto pod) | author backtests |
| H1-48 | Energy and stocks as data overlays | content rows | exchange facts |
| H1-49 | Limits by tick-size tier and holding horizon | content I4 field | author backtest (100 futures) |
| H1-50 | Factor buckets, grouping by underlying | core I4 (underlying, bucket), bet key I9 | SIMM practice |
| H1-51 | Which classes can be traded at this budget | core D5 verdict shown; refusal a block | arithmetic |
| H1-52 | Style as a dial (holding horizon) | content optional derivation; measured field on rows | wild |
| H1-53 | Style by class matrix | content starter sheet for templates | varies |
| H1-54 | Scenario harness and scenarios as data | core S15 replay path; scenario kind content | design |
| H1-55 | Market scenario families worth reading | content (X4 rows) | design |
| H1-56 | Stress generators | content (Lab) | author backtests |

## H2: sizing, brakes, exits, drift, costs, ledger (`harvest/H2-sizing-brakes-exits.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| H2-I1 | Re-size a recorded trade list under another sizing rule | core R2 fields; tool content | REAL product (QuantAnalyzer) |
| H2-I2 | Sizing base is a derivation; dollars first, lots last | core S1 | PROPOSAL over BUILT converter |
| H2-I3 | The rule that splits risk across units is a swappable row | core I10 | REAL (bank limit hierarchy); MODEL for sqrt |
| H2-I4 | House money and reverse house money are one rule; the anchor decides | core R5; shape content; template A on | REAL theory; MODEL no gain on independent trades |
| H2-I5 | One row for every brake or accelerator | core S5 | PROPOSAL |
| H2-I6 | Two ledgers: money for brakes, events for decay | core R2 (mechanism on every close), R5 | MODEL; REAL document practice |
| H2-I7 | Exit stack fed with the position, three verbs | core S3 | BUILT blocks; PROPOSAL stack |
| H2-I8 | Costs are observed facts; rules read them | core I2 | REAL hourly spread research |
| H2-I9 | Speed by kind of signal: money fast, estimates slow, growth slower | core S5 attack and release fields; values content | REAL elsewhere |
| H2-I10 | A money brake at the unit's own percentile | template A and B on; core: window in trades on S4 | MODEL; REAL firms use money |
| H2-I11 | What a brake does is configurable per pod | core S5 `on_fire` | RULING (M49) |
| H2-I12 | Every number carries how it derives | core S13 | REAL in software; never on a trading unit |
| H2-I13 | A rule may read unit, pod and account statistics | core I1 | PROPOSAL |
| H2-I14 | Risk only the cushion above a fixed dollar floor | default block option (base = cushion above a user floor, template A) | REAL theory; dollar sim dropped as verdict |
| H2-I15 | Ring-fence the stake; sweep; ratchet | content on R5; banker acts core (R5 anchors) | REAL fund practice; MODEL |
| H2-I16 | Make each loss smaller, so each bet can be bigger (FI) | template A on with warning; C1 open | MODEL; REVIEW M4 caveat |
| H2-I17 | Concentrate: few units, best basket | content allocation mode | PROPOSAL; lore |
| H2-I18 | Press with winnings only | content on R5 | REAL prop rule; MODEL |
| H2-I19 | AIMD: cut hard after a bad day, add a little after green | content | REAL networking; MODEL |
| H2-I20 | The largest size that keeps a stated floor chance | content bases (horizon, Kelly) | REAL papers; MODEL |
| H2-I21 | Reserve for the one move that really ruins | core I15 hook; worst-step table content | REAL in their fields |
| H2-I22 | Step ladder earned by profit, stepped down the same day | content | REAL rules (Topstep) |
| H2-I23 | Press only when own results persist | content | REAL monthly factors; no intraday |
| H2-I24 | Size where the edge is, in time: measured windows | content on R16, S2 | MODEL; author |
| H2-I25 | Taper as you near a goal | content | article simulation |
| H2-I26 | Restart after a near-breach with less size | content; V5 holds | REAL paper, one period |
| H2-I27 | Stack methods by capital stage | core I10 (pod changes rows at an anchor, no new identity); stack content | GUESS as stack |
| H2-I28 | Audits that catch hidden ruin; firewall as a warning | content (S19 layer) | author tools |
| H2-I29 | Negative-skew units get a tail budget | content base; template A candidate | simulation |
| H2-I30 | Margin as a bound of its own | core I3, I15 | BUILT in part |
| H2-I31 | Slow start with a first-warning switch | content | REAL medicine |
| H2-I32 | Falling-risk pyramiding | content; core S17 | author backtests |
| H2-I33 | Calm-volatility scaling with a guard | content | REAL backtests; failed generalisation |
| H2-I34 | Probe for capacity | content | REAL betting limits |
| H2-I35 | Overdose control on size steps | content | simulation |
| H2-I36 | Bounded-cost exploration of a bigger size | content | bandit simulations |
| H2-I37 | Agents breed sizing profiles in the Lab | content; other: agentic | GUESS |
| H2-I38 | Above capacity, growth buys breadth | content pod rule | analogue |
| H2-I39 | Risk classes with lending | content pod | REAL in software |
| H2-I40 | A book thermostat | content | GUESS |
| H2-I41 | Size by setup quality or calibrated probability | core I12 binding; rule content | in-sample |
| H2-I42 | Lot dither | content option, off | analogue |
| H2-I43 | Meta-allocators in the Lab | content | author backtests |
| H2-I44 | Graded ladder: reduce before bench | content; two_live_readers becomes a warning | REAL grid; MODEL |
| H2-I45 | Loss points | content | never ran |
| H2-I46 | His losing-run brake, made fair | template A present, off | MODEL |
| H2-I47 | Streak brake only where results persist | content | MODEL |
| H2-I48 | Two-speed circuit breaker | content; name kept; slow half display | REAL Basel; MODEL |
| H2-I49 | Expected fire band on the card | core card field (I14); producer other: methodology | PROPOSAL |
| H2-I50 | Portfolio day stop reading its own swing | default block (group row) | MODEL |
| H2-I51 | Portfolio breaker on stacked evidence | content pod | REAL exchange breakers |
| H2-I52 | Losing together counts once | core I9 driver tags; rule content | REAL insurance |
| H2-I53 | Chorus breaker | content pod | spec, never ran |
| H2-I54 | Burn-rate permit | content | REAL SRE |
| H2-I55 | Class, region, market isolation | core S10, S11; protocol content | daily-data author backtests |
| H2-I56 | Pod-style step ladder on capital | content pod | REAL press-reported |
| H2-I57 | Peer ejection | content | REAL software |
| H2-I58 | Five states, one rank table | core S4 | REAL (Nautilus); MODEL |
| H2-I59 | Restore family | core S4 RESTORE state, K6 settle hook; methods content; retry-then-lockout default | REAL elsewhere |
| H2-I60 | Random-control certificate and brake scorecard | content report; core R3 | REAL single test |
| H2-I61a | Day-boundary contract | core R5 | demo tests |
| H2-I61b | Get-even flag | content | REAL (Nasdaq traders) |
| H2-I61c | Changepoint cooldown per instrument | content | REAL fair test, one |
| H2-I61d | Execution-anomaly pause | content | PROPOSAL |
| H2-I61e | Danger accumulator | content | GUESS |
| H2-I61f | Brakes stake wealth and retire themselves | content | GUESS |
| H2-I61g | Regime-age taper on adds | content | one gold test |
| H2-I61h | Staged shedding by priority | content | REAL Google |
| H2-I61i | Region blocked, budget kept as reserve | content | old rule |
| H2-I61j | Weekend and single-class budget cap | content | author |
| H2-I61k | Drawdown cuts agent autonomy to his click | other: agentic | one live case |
| H2-I61l | Re-entry cooling after a fill through the stop | content | PROPOSAL |
| H2-I61m | Order-rate limit and size sanity band | core I15 | design |
| H2-I62 | Cost triple: denominator, ceiling, gate | core I2 denominator in default sizer; ceiling and gate content | author backtest |
| H2-I63 | A missing cost starts on a stressed guess that decays | core I2 label and fallback | PROPOSAL |
| H2-I64 | News as an observed fact | core S10 tier per unit; widths content | E-mini author |
| H2-I65 | The record must split by session and hour | core R6 | code fact (G7) |
| H2-I66 | Input-first drift: costs, fills, rate move before profit | core K4 twin rows; bands content | practitioner |
| H2-I67 | Graded cost shrink before the SQS block | content (SQS-4) | NQ study |
| H2-I68a | Carry and funding inside the hold decision | content | REAL rules; MQL5 sims |
| H2-I68b | Minimum worthwhile risk (commission floor) | content; speaks to "less than $1" | EOQ analogue |
| H2-I68c | Combined-flow netting | core S18 intent apart from placement; netting content | author |
| H2-I68d | Hour map instead of session flags | content | one model study |
| H2-I68e | Broker reality check before deploying | content | author |
| H2-I68f | Cost cushion and retention score | content | author |
| H2-I68g | Stop fills at the stressed spread in backtests | other: methodology (QMB convention) | secondary |
| H2-I69 | Exit families per style as starting templates | template A and B; content families | one study or theory per cell |
| H2-I70 | Fast invalidation from the unit's own winners | template A on | MODEL; no cost test |
| H2-I71 | Thesis-first invalidation | template B on; core reason code | REAL paper account |
| H2-I72 | No stop, or a stop not used to size | core I13 (R as declared basis) | PROPOSAL |
| H2-I73 | Stops only where they earn: stopping premium | content Lab test | REAL daily scale |
| H2-I74 | The dynamic stop and target, rebuilt | template B after step 3; content | April spec, never validated |
| H2-I75a | Survival-analysis hold-or-close | content | one test, mixed |
| H2-I75b | Hold-or-exit classifier, model-confidence exit | content | author |
| H2-I75c | Half-life time exit | content | simulation |
| H2-I75d | Edge-ratio time stop | content | MNQ survivors |
| H2-I75e | Scale-out rungs from MFE percentiles | content (step 3) | author |
| H2-I75f | Trail chosen by why the position opened | content | author |
| H2-I75g | Per-instrument asymmetric stops | content | two months |
| H2-I75h | Target and stop from a fitted reversion process | content | author |
| H2-I75i | Exit by trend or reversion state at horizons | content | author |
| H2-I75j | Staged against immediate exit by cost of waiting | content | author |
| H2-I75k | Basket loss cut and basket time stop | content; account-scope form is a pod | author |
| H2-I75l | Triple barrier bundle | content | live open-source |
| H2-I75m | Flat before the close with a buffer | template B on | design |
| H2-I75n | Two knobs: stop from volatility and horizon, size from budget | content | author |
| H2-I75o | Exit used as a trigger in another strategy | content; same primitive both roles | RULING (T2) |
| H2-I75p | Suspending stops during news | dropped as a default: leaves positions naked; kept as a labelled trap | author |
| H2-I76 | Every exit change is a counted trial on fixed entries | core R8 arms, R2 bar path; test other: methodology | controlled test |
| H2-I77 | A level slot; no ladder in the baseline | core I11 | BOIN elsewhere |
| H2-I78 | The edge as a gate or dial, chosen per preset | content; `edge_range` on R12 core | shrinkage simulations |
| H2-I79 | Asymmetric equity basis | core I3 basis per row | REAL prop practice |
| H2-I80 | Per-scope anchor clocks | core R5 | demo tests; Topstep |
| H2-I81 | Feasibility first, and the lot-shed rule | core D5 verdict; shed rule content | MODEL |
| H2-I82 | The deployment carries share, costs and level | core I3 budget share, I9 | REAL build design |
| H2-I83 | Three numbers per instrument on one money scale | core I4 | REAL banks (SIMM) |
| H2-I84 | Same bet counted once; heat cap | core I9 bet key, S7; heat cap content | textbook |
| H2-I85 | Smallest-wins, naming the binding cap | core R1 receipt | REAL dash.js; April audit |
| H2-I86 | Meters of what safety costs; choke budget | content report; core R3; no CI block | MODEL |
| H2-I87 | Three speeds, with cause | core S4 states and cause codes; rule content | MODEL |
| H2-I88 | Trade CUSUM on R | content default-off block | MODEL |
| H2-I89 | A family fading everywhere (pooled) | core I9 family tag; detector content | MODEL |
| H2-I90 | False-demotion budget across many units | content (K6 group place) | simulation |
| H2-I91 | Bad luck, bad market, bad execution, or decay | core fire tags on R4; classifier content (agentic) | PROPOSAL |
| H2-I92 | Random-entry twin: was the edge ever real | core K4 | controlled design |
| H2-I93 | Drawdown as a decay detector, not a skill measure | content | REAL (Man Group) |
| H2-I94a | Expectation per regime | content | author |
| H2-I94b | Planned looks with three zones | content | REAL regulatory |
| H2-I94c | Upside alarm | content | prop practice |
| H2-I94d | Re-promotion on evidence plus his click | content; V4 | design |
| H2-I94e | E-process against a minimum viable edge | content | proofs |
| H2-I94f | Nightly 20-trade decay check | replaced (E5 fold) | MODEL (91 cards) |
| H2-I94g | Wasserstein drift, rolling Sharpe bands | content | author |
| H2-I94h | Change-point and regime-age readings | content (MIS) | author |
| H2-I94i | Agent drift explainer, coroner, advocate | other: agentic | PROPOSAL |
| H2-I94j | Rehab with the parent's record as prior | other: methodology | PROPOSAL |
| H2-I95 | Agents read, propose and carry the watching | core K2; jobs other: agentic; C16 open | REAL (Steward) |
| H2-I96 | A proposer that always wants more gets the slowest line | other: agentic | snippet |
| H2-I97 | A ledger of 835 variables with typed couplings | content map; re-tier; S19 check layer core | catalogue |
| H2-I98 | Dead and parked values keep their history | content (`seen_values`) | design |

## H3: template, structure, architecture versions (`harvest/H3-unit-template-architectures.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| H3-T1 | Unit as one document; spec and status with separate writers | core R9 state, I9 generation stamp | REAL (Kubernetes) |
| H3-T2 | Every number carries its derivation; the derivation is a swappable block | core S13 | PROPOSAL; BUILT cousin |
| H3-T3 | The Lab's pod is the customization layer | core S14, S15; fork F1 | designed, unbuilt |
| H3-T4 | Dollars decide; lots spell the order | core S1; word Q3 | PROPOSAL over BUILT |
| H3-T5 | How units share capital is a declared rule | core I10 | REAL (LEAN, RiskMetrics) |
| H3-T6 | A rule row is movable between unit and guard | core S5 placement; fork F1 | MODEL (property test) |
| H3-T7 | Four kinds of unit, one door; nothing needs a QMB card | core V7 | RULING (M49) |
| H3-T8 | Typed schema beside code; unknown fields refused | core (D50 census); generators content | checked on many platforms |
| H3-T9 | Save only what differs from the preset, pin the version | core D36 pins and diffs | REAL (n8n) |
| H3-T10 | Presets are charts: one schema, many presets | core S16 template kind; presets content | REAL (Helm) |
| H3-T11 | Templates for a whole sizing structure: old-style, Book-style, hybrids; packs with a combiner | core S14 composition rules; packs content | checked (LEAN chaining) |
| H3-T12 | QML new roles | core S12 | PROPOSAL over BUILT protocols |
| H3-T13 | Dictionary holds closing mechanisms; a closing rule is a block | core S3 | BUILT |
| H3-T14 | Facts, responses, limits are three things | core I4, V8 | author |
| H3-T15 | One instrument record per unit, instrument, broker; fields not branches | core I4 | PROPOSAL |
| H3-T16 | Override chain of eleven keys | core (keys reserved); evidence-earned overrides content | SIMM read |
| H3-T17 | Cascade with "important" outer rule; inspector | core (group rank); `risk_explain` content | checked elsewhere |
| H3-T18 | The needs list | core S15 (replaces `unsupported_blocks`) | REAL (Bevy) |
| H3-T19 | New type or brake needs one folder, zero core edits; stress battery | content CI test (D39) | PROPOSAL |
| H3-T20 | Outside code: Library block, trust ladder, hatch | core K6 save path; ladder and hatch content | BUILT loader; PROPOSAL |
| H3-T21 | Small expression form compiled to a block | content | REAL (n8n) |
| H3-T22 | Two adapters per seam; contract tests per class | core D50 tests | BUILT weaknesses |
| H3-T23 | Three faces per block | content, early | BUILT shape |
| H3-T24 | Learner and applier (VPA) | content; fork F2 | REAL (VPA); MODEL little gain |
| H3-T25 | Facts move live, numbers at anchors | default mode, not law | PROPOSAL |
| H3-T26 | A tuned number is a guess with a guard and freeze | core S13 fields; conditions content | elsewhere |
| H3-T27 | Direction-split motion, grow only on evidence | core S13 room for behaviour; rule content | elsewhere |
| H3-T28 | A reason on every resolved value | core R1 | spec checked |
| H3-T29 | Never-self-tune list, per template | core S13 marker; list config | elsewhere |
| H3-T30 | Pooled priors for a new unit | content rung | standard method |
| H3-T31 | Herding guard | core K6 group place; rule content | GUESS |
| H3-T32 | Bandit arms, learned profiles, genomes | content (Lab) | papers |
| H3-T33 | A pod as a shippable bundle | core S16 | BUILT (MIS proves apps run blocks) |
| H3-T34 | The Risk Lab mini app | content | PROPOSAL |
| H3-T35 | Resize a recorded trade list | core R2 fields; tool content | REAL product |
| H3-T36 | Clusters as tags; Book and BMS as three documents | core I10 `tag:` and `parent`; structure his later | no generation ran it |
| H3-T37 | Pods configure pod-life answers | core S5 `on_fire`, verbs | RULING |
| H3-T38 | One simulator or one guard: same evaluator | core S15 | reading of two documents |
| H3-T39 | One catalogue for pod-block and component | core S16 | reading |
| H3-T40 | A model as a block under a rule ceiling | content | PROPOSAL |
| H3-T41 | Family ledger counts every trial; identity table is data | core I9 vocabulary; methodology owns rules | designed |
| H3-T42 | Paper as daily finite runs; promotion two clicks | other: methodology; core "unit parts as a list" | designed |
| H3-T43 | Mini apps feed each other; one narrow road to a unit | core K3 | BUILT narrow |
| H3-T44 | Budget share travels with the deployment | core I3 | elsewhere |
| H3-T45 | Shed by class; burn tiers; spent budget freezes versions | content | REAL SRE |
| H3-T46 | Isolation by peer comparison with growing timeouts | content | REAL (Envoy) |
| H3-T47 | Same compiled unit on PC and node | core (placement); agents' VMs later | BUILT one path |
| H3-T48 | Two records: logic in R, money per version | core D40 | BUILT judge |
| H3-T49 | Pinned versions plus a forwarding map | core D40 | REAL (Simulink) |
| H3-T50 | Plan before change; click bound to the effect | core D40, V4 | REAL (Terraform) |
| H3-T51 | Shadow, canary, full | core rollout field; analysis other: methodology | production elsewhere |
| H3-T52 | Upgrade offers never silent | core lineage; offers content | checked |
| H3-T53 | Self-test card per version | core D40; pass rules other: methodology | BUILT analogue |
| H3-T54 | Deployment controls as important as logic; rip-out check | core D40 | REAL (Knight) |
| H3-T55 | Migration of stored shapes; config-effective timing | core D40, V12 | BUILT |
| H3-T56 | Read door and proposal door | core K2 | REAL paper runs |
| H3-T57 | New-block door for agents | core K6 | gap verified |
| H3-T58 | Ledger as source of truth, layer H check | core S19; runtime edges dropped | BUILT script |
| H3-T59 | One fold, many readers: RiskState | core R9 | Gen 3 docs |
| H3-T60 | Six words made exact, plus UNKNOWN | core R9 predicates; surfaces other: UI | control-room practice |
| H3-T61 | Decision trail, trace id, three weights | core R1, R15 | production practice |
| H3-T62 | Trade row v2 | core R2 | BUILT kind fields |
| H3-T63 | Closed reason codes at source | core R4 | bug verified |
| H3-T64 | Requested, enforced, observed | core R15 | Gen 3 |
| H3-T65 | Cost cell: assumed against realised | core I2 | author |
| H3-T66 | Alert tiers, wake contract, incident funnel | other: UI; core R10 fields | SRE practice |
| H3-T67 | Family alarm budget | content (K6 place) | proofs |
| H3-T68 | Brake scorecard, trip tax, sitting-duck meter | content; core R3 | counterfactual |
| H3-T69 | Observability observes itself; stack choice | content; V11; stack his later | REAL (Knight) |
| H3-T70 | Exit capacity, locked heat, stress gauge | content (R9 reserved field) | SPAN practice |
| H3-T71 | Maintainability pieces | core D50 | BUILT partly |
| H3-drop1 | Central risk oracle (X1-H69) | dropped: breaks units-stand-alone; same pipeline in the guard | ruling |
| H3-drop2 | Runtime `affects` edges (X1-H71) | dropped: too much machine; compile-time check keeps most | ruling |
| H3-drop3 | Permission controller (X1-H75) | content if wanted | PROPOSAL |
| H3-drop4 | Netted virtual positions (X1-H74) | content on S18 | author |
| H3-drop5 | Sound map, observability budget, attention telemetry, vital signs (X6-47, 46, 26, 44) | other: UI or dropped: low value | GUESS |
| H3-drop6 | Marketplace (X1-H78) | content, after S16 | PROPOSAL |

## H4: agents, judging, fleet, workflows per type, unit idea bank (`harvest/H4-agents-methodology-unit-ideas.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| H4-I-01 | The early fake-edge kit | other: methodology; core swappable entries (S3), costs in R (R2) | REAL per check; kit PROPOSAL |
| H4-I-02 | Machine check in days against a paper twin | core K4 | production practice; arithmetic |
| H4-I-03 | Costs as the data-analyst lens | core I2 | author backtest; live MM result |
| H4-I-04 | Count every try | other: methodology, agentic; core R12 | REAL finding |
| H4-I-05 | Leakage blocked in the tools | core I7 `knows_at`; rest other: methodology | REAL (planted cheat passed stats) |
| H4-I-06 | The edge as a band with a reasoned low end | other: methodology; band on R12 | simulation |
| H4-I-07 | "Too thin to prove" verdict; plan priced in trades | other: methodology | arithmetic |
| H4-I-08 | Independent challenger, blind checker | other: methodology | controlled test (blind check) |
| H4-I-09 | Pipeline tested on nulls and planted edges | other: methodology | strong method |
| H4-I-10 | Family false-discovery rate on a synthetic market | content later | wild |
| H4-I-11 | Tool table priced in trades | content (Library page) | arithmetic |
| H4-I-12 | The proof battery | content judge presets; other: methodology | solid |
| H4-I-13 | Three speeds, three jobs | core S4 states; rules content | maths |
| H4-I-14 | Anytime-valid promotion ledger | content block | simulation (daily) |
| H4-I-15 | Planned looks, trial-style stopping | content | regulatory practice |
| H4-I-16 | Three zones | core state word; rule content | regulatory |
| H4-I-17 | Dose-style size levels | content (I11 slot) | never on a trading unit |
| H4-I-18 | Cone in the current regime; worry lines by style | content | simulation |
| H4-I-19 | Old circuit breaker made honest | core R4 fire rows; test content | old spec |
| H4-I-20 | "Too good" checks | content | prop practice |
| H4-I-21 | Exits are tries too | core R2, S3 | controlled test |
| H4-I-22 | New version against old, same minute | core K4 | simulation; Argo |
| H4-I-23 | Canary across markets | core rollout field | production practice |
| H4-I-24 | Sniping window as a measured slice | core S9; search content | idea plus placebo |
| H4-I-25 | Two vetoes, logged apart | content pod | author |
| H4-I-26 | Funded error budget per family; burn permit | content | SRE analogue |
| H4-I-27 | Pooled proof across opens | core I9 family id; rule content | plausible |
| H4-I-28 | World-switch reset | core I9 world and stage tags | BUILT one path |
| H4-I-29 | Restarted detectors; variance cap | content | proofs |
| H4-I-30 | Thresholds calibrated on the unit's own record | content | plausible |
| H4-I-31 | Exploration budget | parked: numbers; content pod | idea |
| H4-I-32 | Edge as gate, not amount | content; baseline allows both | numbers |
| H4-I-33 | Fleet watch: scripts decide, agents explain | content workflows; core rows (E5) | pieces BUILT |
| H4-I-34 | One alarm budget across all units | content (K6 place); E5 corrected the scale claim | theory; simulation |
| H4-I-35 | One logic fading everywhere | core I9 family id; detector content | plausible |
| H4-I-36 | His attention budget | other: agentic, UI | plausible |
| H4-I-37 | One incident, one card | core R10 key | SRE |
| H4-I-38 | Dark cockpit: six words, four tiers | other: UI | aviation |
| H4-I-39 | Agent report card and matched random check | other: agentic | strong design |
| H4-I-40 | Morning brief, drift explainer, coroner | content workflows (agentic) | solid to plausible |
| H4-I-41 | Explain any size in ten words | core R1 `explain_size` | old rule |
| H4-I-42 | Verification template per type as data | content preset; core free type tag | RULING (A5) |
| H4-I-43 | Harness differs per asset class | other: methodology | assistant synthesis |
| H4-I-44 | Five-gate falsification protocol | other: methodology | author OOS |
| H4-I-45 | Eligibility by holding time | core style scope on I8 | one study |
| H4-I-46 | Classes change what the papers say | content (Library) | varies |
| H4-I-47 | Research harness in eight steps | other: methodology | REAL (frozen referees) |
| H4-I-48 | Parallel search beats sequential | other: methodology | one paper |
| H4-I-49 | Champion and diverse archive | other: methodology | pattern |
| H4-I-50 | Three surfaces: read, propose, run | core K2 | BUILT door |
| H4-I-51 | Risk state handed to the proposer first | core RiskState read (R9) | author backtest |
| H4-I-52 | Evidence as a fact the unit's own rule reads | core I8; C16 open | no end-to-end test |
| H4-I-53 | Evidence contracts per kind | other: agentic; content | simulation |
| H4-I-54 | Fast loop with no LLM | core V3; RULING | author backtest |
| H4-I-55 | Direction on every operation | other: agentic | controlled test |
| H4-I-56 | Effect-bound card and bound click | core V4, D40 | controlled tests |
| H4-I-57 | Spec, status, suggestions: three owners | core I9 | production practice |
| H4-I-58 | Risk mini app with an MCP server | other: agentic | shape solid |
| H4-I-59 | Lab as tenant of the run surface | other: UI, agentic; core S15 | designed |
| H4-I-60 | Risk preflight plus challenger | core S19 | BUILT A to G |
| H4-I-61 | Autonomy ladder and job registry | other: agentic | one live case |
| H4-I-62 | Governed self-improvement | other: agentic | two cycles |
| H4-I-63 | Never let an agent grade itself | other: agentic, methodology | one study |
| H4-I-64 | Promotion gates for memory, skills, tools | other: agentic | PROPOSAL |
| H4-I-65 | Agent profile contract | other: agentic | PROPOSAL |
| H4-I-66 | Red-teaming the information path | other: agentic | attack papers |
| H4-I-67a | Slow isolation by card | content pod; core S11 | RULING (C27) |
| H4-I-67b | Adversarial scenario author plus sealed set | content | simulation |
| H4-I-67c | Tuning proposer under an applier | content (Lab) | RULING (M49 hill climb) |
| H4-I-67d | Template version drafter | other: agentic | solid |
| H4-I-67e | Sitting-duck advocate | content | fits M50 |
| H4-I-67f | Accelerator scout | content | PROPOSAL |
| H4-I-67g | Breadth and placement proposer | content | PROPOSAL |
| H4-I-67h | Slot rebalancer | content pod | PROPOSAL |
| H4-I-67i | Get-even guard | content | REAL (prop traders) |
| H4-I-67j | Per-class roster and event mapper | content | PROPOSAL |
| H4-I-67k | Structure labeller with capacity veto | content | PROPOSAL |
| H4-I-67l | One-tap kill escalation card | other: UI, node; core `on_fire` card | design |
| H4-I-67m | Prediction market, ghost tracks, self-proposing ledger, staking | content if ever | wild |
| H4-I-68 | Ingestion from video, channel, paper | other: methodology, agentic | BUILT templates |
| H4-I-69 | Blacksmith: reforge failed strategies | other: methodology | pattern BUILT; value unproven |
| H4-I-70 | Shepherd | other: agentic | early alpha |
| H4-I-71 | Strong model structures, cheap model runs | other: agentic | no test |
| H4-I-72 | Mini apps as departments | other: agentic; roads core (D37) | BUILT runtime |
| H4-I-73 | A week on one market | other: methodology | PROPOSAL |
| H4-I-74 | Agents' own computers, charts | other: agentic | studied |
| H4-I-75 | Library and memory ship with knowledge | other: methodology | PROPOSAL |
| H4-I-76 | Methodologies from papers as skills | other: methodology | eval battery BUILT |
| H4-I-77 | Borrowed logic from other fields | content (mental models) | author |
| H4-I-78 | Trading platforms as agent tools | other: agentic | RULING (demo MCP) |
| H4-I-79 | The unit is the final step; QML first | core V7, D45 | RULING |
| UB-01 | Order-flow imbalance | content (needs tick; Q2) | explains, not forecasts |
| UB-02 | Book events predict ~10 seconds | content (tick) | author |
| UB-03 | Auction-market features | content (tick, vol) | author; deep drawdowns |
| UB-04 | Session labelling: follow or fade | content (vol, sess, read) | in-sample |
| UB-05 | Regime breaks in order flow | content (tick, read) | internship report |
| UB-06 | Will the next minute clear the fee band | content (tick, py) | no returns |
| UB-07 | Post passive only when imbalance signal likely wrong | dropped for now: co-location required | live small |
| UB-08 | Crypto 15-minute reversal | content (tick, vol); fees bind | frozen holdout |
| UB-09 | Quarter-hour bursts | content (timing offset S18) | useful for timing |
| UB-10 | Crypto one-minute model, triple barrier | content (py, model) | bull period |
| UB-11 | Open-interest unwinds | content (vol, read) | weak |
| UB-12 | First half hour predicts last | content (sess) | survives cost in ETF study |
| UB-13 | MNQ regime-transition entry, London signal | content (sess); delay warning | 53+ combos |
| UB-14 | Asia expansion bars, post-news drift, ORB pullback | dropped: negative result; kept as warning | negative |
| UB-15 | ORB only on markets unusually active | template orb variant (needs vol; Q2) | net Sharpe 2.81 one period |
| UB-16 | 30-minute US stock long-short | content (route, model) | retail cost erases |
| UB-17 | Earnings gap continue or skip | content (route, cal) | idea |
| UB-18 | Dollar rises before FX fixes | content (sess); real sniping window | negative at full spread |
| UB-19 | Month-end hedge flow into London fix | content | academic |
| UB-20 | Rule and model agree | content (model) | in-sample |
| UB-21 | Per-symbol agents share signals | content (read); touches desks | no numbers |
| UB-22 | LLM fine-tuned on pair statistics | dropped as a strategy; lesson kept | in-sample |
| UB-23 | Regime age close or skip | content (read) | in-sample |
| UB-24 | Dominant cycle switches logic | content | in-sample |
| UB-25 | Calibrated firm news score | content (route, model) | post-cutoff |
| UB-26 | Filing downgrade plus weak momentum | content | pipeline backtest |
| UB-27 | Analyst synthesis with "this proves me wrong" | core reason code (thesis exit, S3); unit content | paper account |
| UB-28 | News-attributed jumps | content (cal, model) | author |
| UB-29 | Macro surprise against consensus | content (cal, read) | forecast score |
| UB-30 | EIA, OPEC event studies | content (cal, roll) | abstracts |
| UB-31 | Trade ahead of index rolls | content (roll, cal) | abstract only |
| UB-32 | Expiry and roll dislocation | content (roll) | idea |
| UB-33 | Calendar effects by peeking | dropped: 0 of 24 passed; warning kept | negative |
| UB-34 | Staged re-entry after a shock | content (read) | idea |
| UB-35 | Trend across all futures | content (roll, route) | long record |
| UB-36 | Fast and slow trend by tick tier | content (roll) | Sharpe fell after 2008 |
| UB-37 | Leaders lead laggards | content (read, legs) | related sleeve |
| UB-38 | Gold futures trend vol target | content (roll) | low CAGR |
| UB-39 | ETF momentum rotation | content (route, legs) | weak |
| UB-40 | Weekly rotation with regime gate | content | one run |
| UB-41 | Sit out declines filter | content (read) | under market |
| UB-42 | Evolved allocation score | content (legs) | one run |
| UB-43 | Multi-horizon vol-scaled momentum | content | causal untested |
| UB-44 | Multi-scale momentum, gap acceptance | content (vol, sess) | corrected rerun negative |
| UB-45 | Moving-average crossovers as controls | content (control units) | examples |
| UB-46 | Supertrend | content default block as control; tuned values dropped | default lost |
| UB-47 | Ranker runs while errors healthy | content (route, read) | gate AUROC |
| UB-48 | Daily agent stack BTC, ETH | content (read) | no trial count |
| UB-49 | Crypto trend and relative value | content (legs, read) | idea |
| UB-50 | Spread trade from its fit | content (legs) | analytical |
| UB-51 | Vol-managed momentum, FX carry | content (read) | disputed real-time |
| UB-52 | FX carry with swap in the hold | content (read) | simulated swap |
| UB-53 | Perp funding carry, basis | content (legs, read) | idea |
| UB-54 | Agent-mined factors, tree model | content (route, model) | survivorship |
| UB-55 | Simulated investors agreement minus disagreement | content reading over own units | weak |
| UB-56 | Classic factors, LLM vol breakout | dropped: 0 of 5 survived deflation | negative |
| UB-57 | Evolved factor trees | content | short windows |
| UB-58 | LLM picks factors | content (model) | one year |
| UB-59 | Stricter constraints per regime for an LLM trader | other: agentic | one test |
| UB-60 | Short-dated SPX put writing | dropped for now: no route, no crisis in test | 2024 only |
| UB-61 | Short straddles with learned exit | dropped for now: same | no crisis |
| UB-62 | Mean-reversion half-life per market and session | content (read); gold 5m MR warning | model |
| UB-63 | Probability the regime just broke | content (read) | few trades |
| UB-64 | Regime age reading | content (read) | short sample |
| UB-65 | Volatility-break alarm calibrated per instrument | content; calibration record core (I4) | cross-asset |
| UB-66 | Trend or reversal per timeframe at scalper scale | content | tiny R² |
| UB-67 | Session volatility beats session flags | content | one model |
| UB-68 | Forecast only when agents agree | content (model) | simulation |
| UB-69 | Sniping windows as stored artifacts | core R16 window card | idea |
| UB-70 | Dollar and carry factors | content (read) | published |
| UB-71 | Early warnings: ETF gap, correlated drops, toxicity | content (read) | idea |
| UB-72 | Wait between quotes as activity gauge | content (tick) | small OOS |
| UB-73 | Implied over realised for placement | content (read) | mechanism |
| UB-74 | Crypto weekend predicts Monday gaps | content (read) | backtest |
| UB-75 | Prediction-market moves forecast crypto vol | content (read) | short |
| UB-76 | Liquidation-risk throttle | content (read, vol) | seven cascades |
| UB-77 | RL and LLM paper list | other: methodology (reading list) | titles |
| UB-78 | Agent reads charts like a trader | other: agentic (Lab) | idea |

## H5: papers, MT5 articles, borrowed logic (`harvest/H5-papers-articles-borrowed-logic.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| H5-1 | The "never real" kit agents can be handed | core R12 lineage and trial count; checks content; rules other: methodology | REAL per paper; kit PROPOSAL |
| H5-2 | Monitoring department: code detects, agents explain | content (E5 design) | PROPOSAL; no paper shows LLM monitors sooner |
| H5-3 | Making it affordable: write once check many, rank false alarms, LLM after a rule fires | other: agentic | author tests outside trading |
| H5-4 | Every unit states what would prove it wrong, watched by code | core S12 (`invalidation` after entry), S3 reason code; template B | REAL paper account |
| H5-5 | Risk state reaches the proposer first | core R9 read | backtest, two coins |
| H5-6 | One evidence record for every agent, with expiry | core I8 | PROPOSAL |
| H5-7 | Departments as bounded mini-harnesses with "must not see" | other: methodology, agentic; seat in pod manifest | PROPOSAL |
| H5-8 | Alpha discovery as a workflow inside QMX | content on QML; other: methodology | mixed, sobering |
| H5-9 | Agents find timing, not stock-picking: a home for overlay units | content (QML role) | one paper |
| H5-10 | Linking as a capability: block manifest with source, evidence, classes, data, null | core R16 fields | assistant lines untested |
| H5-11 | Papers in the Library as mental models, negatives first | content; other: agentic (memory) | PROPOSAL |
| H5-12 | Ship a null beside every statistic | core R16 `null` field; E4 L03 corrects it | REAL test design |
| H5-13 | A market with no edge as a test instrument | other: methodology | simulation by design |
| H5-14 | A dumb control beside every agent result | content report rule | one paper |
| H5-15 | Immunology: a brake that gathers danger | content | GUESS |
| H5-16 | Power grids: nearest breaker trips first | core S11 scope order; settings content | engineering practice |
| H5-17 | Plants and ICUs: an alert names an action and a deadline | core R10 alert fields | REAL in source fields |
| H5-18 | Reinsurance: count exposure to the same event; many-to-many tags | core I9, S11 | analogy |
| H5-19 | Robotics: propose, constrain, one step, look again | content; K1 fits | robot simulation |
| H5-20 | Self-healing: half-open probe, transient vs permanent errors, Safe Mode | core S4 state names; methods content | demo and code checks |
| H5-21 | Control theory: the strategy is a plant | content | author |
| H5-22 | Clinical trials: dose steps, spend a false-alarm budget | content | simulation |
| H5-23a | Random matrices clean the correlation matrix | content | author |
| H5-23b | Curvature: have clusters merged | content, lesson first | author |
| H5-23c | Optimal transport for drift | content | author |
| H5-23d | Autoencoder co-movement | content | mixed |
| H5-23e | Compression | content | negative vs null |
| H5-23f | CUSUM fires 5x theory; fit per instrument | core I4 calibration record | measured |
| H5-23g | Chaos measures | dropped for now: "not the Holy Grail"; a user may add | author |
| H5-24 | Regimes have an age; sticky models | content; MIS seat outputs probabilities and age | backtests |
| H5-25 | Macro as slow budget, market state as what's usable | content; S10 `unknown` core | policy to test |
| H5-26 | Separate the two residuals: signal faded or execution worse | core I2 | PROPOSAL |
| H5-27 | Three-word liquidity state | content (SQS-3) | REAL OOS, two coins |
| H5-28 | Impact law as a live gauge; venue-type field | core I4 flag; order flow other | explains |
| H5-29 | Links between markets appear and vanish; retest date | core R16 `retest_by`; rule content | REAL, recent, short |
| H5-30 | Learn which events matter per instrument | core S10 per-release widths seat; map content | REAL FX and futures |
| H5-31 | Many units, one netted order | core S18 | author; inference |
| H5-32 | Repeat same-side trades get worse quotes; log rejections | core R7 | theory |
| H5-33 | Fills are selected; post-fill markout | core R7 markout | REAL live orders, one week |
| H5-34 | Bar closes are the crowded moment; jitter | core S18 entry-timing offset | crypto backtest |
| H5-35 | Group instruments by what they wrap; tick tier | core I4 | REAL measurements |
| H5-36 | One record per unit, instrument and broker | core I4 | code checks |
| H5-37 | Stamp every test with its conditions | core R8 run stamp | measured |
| H5-38 | Self-improvement that can't loosen anything | other: agentic; core protected field list | short windows |
| H5-39 | Promotion gates for memory, skills, tools | other: agentic | PROPOSAL |
| H5-40 | Blind the reviewer to the story | content; decision-chain record core R15 | synthetic |
| H5-41 | A news item can only move so much | core I8 source and feed ids; cap content | sandbox tests |
| H5-42 | Agents that can say "I don't know" | content | simulated |
| H5-43 | Do your units agree on this instrument | content reading; units publish direction (I9) | stock-picking paper |
| H5-44 | Let the agent try its fix in a lab first | content | one synthetic asset |
| H5-45 | Authority that expires; evidence apart from money | core status expiry; policy other: methodology | simulation |
| H5-46 | Can this edge live long enough to be proven | other: methodology; core counters (sessions, regimes) | model |
| H5-S1 | Post-deleveraging crypto | content seed | author |
| H5-S2 | Trailing multi-horizon vol-normalised momentum | content seed | author |
| H5-S3 | Gap acceptance, trend quality | content seed | daily equities |
| H5-S4 | Trend filtered by tick-size tier | content seed | futures |
| H5-S5 | Commodity expiry and roll dislocation | content seed | spreads |
| H5-S6 | Post-shock staged re-entry | content seed | unproven |
| H5-S7 | Fast numbers, slow language around earnings | content seed | stocks |
| H5-S8 | Calibrated news sentiment firm-day | content seed | licensed news |
| H5-S9 | Prediction-market repricing to crypto vol | content seed | MIS input |
| H5-S10 | News-attributed jump risk | content seed | futures |
| H5-S11 | Crypto 15-minute reversal, maker only | content seed | fees bind |
| H5-S12 | MNQ survivors, London flips with delay | content seed | 53+ tries |
| H5-S13 | Network momentum lead-lag | content seed | futures |
| H5-S14 | Perp premium from positional traders | content seed | model |
| H5-S15 | Implied against realised as forward input | content seed; not timing | gold, indices |
| H5-S16 | Session volatility beat session flags | content seed | intraday |
| H5-S17 | Quote-duration activity gauge | content seed | per broker |
| H5-S18 | Relative volume in-play gate at the open | content seed (Q2) | stocks |
| H5-T1 | Suspending stops during news | dropped as default; trap warning | author |
| H5-T2 | Degraded mode trading without its controller | dropped as default; trap | author |
| H5-T3 | Daily capital rotation to recent winners | dropped as default; trap | author |
| H5-T4 | Agents executing chat-channel signals | dropped as default; trap | author |
| H5-T5 | Confidence sizing that grew average loss | dropped as default; trap; E3-11 agrees | author |

## E1: designs for the SQS and the MIS (`round-2/expand/E1-mis-sqs.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| E1-1a | The card's clock sets the MIS bar (one bar size per MIS today) | content (MIS app) | BUILT limit |
| E1-1b | Full bar port (blocks fed closes only) | content | BUILT limit |
| E1-1c | Keep reading state between rounds | content | BUILT cost UNKNOWN |
| E1-1d | Pack parameters reach blocks | content (config) | BUILT limit |
| E1-1e | Three output forms: value, against usual, word | core I6 curves; form content | PROPOSAL |
| E1-1f | Pack contents per class; 17 cards exist, 4 in use | content | BUILT |
| E1-1g | Retire `spread_state` fixed cuts when curves arrive | content | BUILT |
| E1-1h | Tick-tier readings move to the node | core S6 node sensor | BUILT stand-in |
| E1-1i | Record `source` open beyond node and mis | core S8 | BUILT enum of two |
| E1-1j | An app declares it reads other apps' readings | core S8 capability (D37) | UNKNOWN in supervisor |
| E1-1k | Clock facts reach the app (C-01) | other: repair | BUILT `clock_ok=False` |
| E1-1l | `Placement` narrows only; stale board trades all listed | core I5 fix | BUILT hazard |
| E1-SQS-1 | The same gate, moved and made swappable | default block (floor) | BUILT rule text, never run live |
| E1-SQS-2 | The cost hurdle | default block (gate) | PROPOSAL over REAL cost shape |
| E1-SQS-3 | The fillability bank | content, shadow | author backtests |
| E1-SQS-4 | The cost dial | content, off, on S2 | author backtest NQ |
| E1-SQS-rec | One sensor, one open slot; SQS-2 gate, SQS-1 floor | core S6; defaults 4.1 | PROPOSAL |
| E1-SQS-wait | A "wait" verb: hold the intent briefly | content block | PROPOSAL |
| E1-MIS-1 | The deeper board | content (pack list) | designed |
| E1-MIS-2 | The open bus | core S8 | PROPOSAL; record BUILT |
| E1-MIS-3 | The finder | content, first app | RULING (M5); MODEL on lag |
| E1-MIS-4 | Two products: curve factory and node stream | core I6, S6 | PROPOSAL |
| E1-MIS-poleA | Slow-only MIS (B106) | content pole for architects | PROPOSAL |
| E1-MIS-poleB | No central MIS, shared sensor code (B105) | fork F3 shape C field | PROPOSAL |
| E1-MIS-poleC | Cross-sectional only (B107) | content | PROPOSAL |
| E1-MIS-poleD | Per-reading placement rule (B126) | content card field | PROPOSAL |
| E1-MIS-poleE | Several products under one vocabulary (QF01) | folded into MIS-4 | PROPOSAL |
| E1-MIS-rec | MIS-2 and MIS-4 as shape; MIS-3 first app; MIS-1 content | core S8, I6; D22 | PROPOSAL |
| E1-sticker | Sticker record: scope, kind, strength, expiry, why, who | core S10 | PROPOSAL (Kubernetes taints analogy) |
| E1-toleration | Tolerations per unit, pod-overridable | core S10 | RULING (M49 pod question) |
| E1-sticker-fail | Unreadable sticker table reads `unknown` per scope | core S10 | design |
| E1-iso-who | Who may place: two-tell rule, agent card, person | config; rule content | author backtests |
| E1-iso-evidence | SQS blocks across a class; volatility against usual; commonality | content | REAL commonality |
| E1-iso-record | Each isolation writes whether a loss followed | core R14 | PROPOSAL |
| E1-news-tags | Calendar to sticker with driver tags | core I4, S10 | REAL old |
| E1-news-strength | Measured impact replaces colours | content | author |
| E1-news-who | Who decides: pod setting; kill keeps hard kill | config; V2 | RULING |
| E1-news-trade | News units tolerate the sticker; event clock | core I7; units content | author |
| E1-news-pre | Pre-event liquidity state predicts post | content | abstract |
| E1-news-missed | Velocity tell backstops the calendar | content | PROPOSAL |
| E1-news-agents | News agents typed, expiring, de-risk only | other: agentic; door core | controlled test |
| E1-snipe-answer | ORB is a logic; an open is a window; a sniping window is a record | decided (D30) | reasoning |
| E1-window-card | Window card: slice, family, how found, tries, expiry, status | core R16 | PROPOSAL |
| E1-window-det | Deterministic windows from curves | content | author |
| E1-window-agent | Agent-nominated windows, counted | content; other: agentic | RULING (M50 week) |
| E1-window-hand | Hand-written window trades unproven, labelled | content; V9 | canvas |
| E1-window-effect | Lift through S2 or restriction through `sessions` | core S2, S9 | design |
| E1-caution-width | Caution widths measured from curves | content; parked: numbers | no width derived |
| E1-router-shape | Active list is a reading; no router service | core I5, S8 | PROPOSAL |
| E1-router-hazard | Fallback must be home markets | core I5 | BUILT hazard |
| E1-router-lock | List read at session open, held | config | MODEL lag |
| E1-rung0 | Fixed list | template default | design |
| E1-rung1 | Board narrows | content (BUILT, unwired) | BUILT |
| E1-rung2 | Active list with home fallback | content | PROPOSAL |
| E1-rung3 | Card adds to allowed, counted try | content; other: methodology | PROPOSAL |
| E1-rung4 | Free: allowed is a class | content (reckless) | canvas |
| E1-router-needs1 | Records per unit, market, session | core R6 | code fact |
| E1-router-needs2 | Newly active mark on the trade row | core R2 | PROPOSAL |
| E1-router-needs3 | Same-bet key and cluster cap by unit rule | core I9; rule content | PROPOSAL |
| E1-router-needs4 | Lists kept and scored side by side | content | PROPOSAL |
| E1-router-needs5 | Spread and cost in the finder | content; parked: numbers | arithmetic |
| E1-router-needs6 | Honest as-of labels only | core R13 | MODEL |
| E1-router-methods | Twin search, good-days match, scouts, pheromone, brief, typed list | content publishers | PROPOSAL |
| E1-sessions | Handover re-runs the finder; words keyed per market | content; answers "how do we change sessions" | PROPOSAL |
| E1-pub1 | `source` as publisher identity | core S8 | BUILT enum |
| E1-pub2 | Capabilities to read and publish readings | core S8 | UNKNOWN |
| E1-pub3 | Inputs named on each record | core S8 | PROPOSAL |
| E1-pub4 | `valid_until` beside `stale_after_s` | core S8 | PROPOSAL |
| E1-pub5 | Reading card published with it | config | BUILT shape |
| E1-rule1 | Reading isn't controlling | core V3, V7 | design |
| E1-rule2 | Shadow first by default | config | design |
| E1-rule3 | Tier follows speed; no LLM on fast tiers | config; RULING | REAL latency |
| E1-rule4 | Agent readings reduce risk only | core V3; Q4 | RULING |
| E1-rule5 | No look-ahead by tool | core I7 `knows_at` | design |
| E1-rule6 | Scored like sensors | content | PROPOSAL |
| E1-rule7 | Same word, same meaning test | content | PROPOSAL |
| E1-rule8 | Retire what nobody reads | content | PROPOSAL |
| E1-walk | His departments walk: macro, FX, futures, finder, unit | content; other: agentic | PROPOSAL |
| E1-floors | Three floors for every reading: null, bounce, use | core R16 `null`; floors content | MODEL bounce |
| E1-P1 | Activity-price split (market temperature) | content | GUESS |
| E1-P2 | Quote self-excitement (Hawkes) | content, expect failure | snippets warn |
| E1-P3 | Liquidity commonality | content, first | REAL (Mancini) |
| E1-P4 | Aftershock clock | content | memory (Omori) |
| E1-P5 | Directional-change clock | content; null may absorb | memory |
| E1-P6 | Class alignment (Ising, retested) | content | no trading evidence |
| E1-P7 | Time irreversibility | content | snippet |
| E1-P8 | Critical slowing | content; disk warns | REAL (events differ) |
| E1-P9 | Information flow between related markets | content | snippets |
| E1-P10 | Mini and micro residue | content; needs futures route (Q2) | GUESS |
| E1-P11 | Level gravity | content | memory |
| E1-P12 | Scalpability and tick constraint | content, first | arithmetic |
| E1-P13 | Species survey of scout logics | content | PROPOSAL |
| E1-P14 | Disorder and compression with null | content | negative vs null |
| E1-P15 | Trend age hazard | content | snippet |
| E1-quarry | Old Chaos and Ising readings get cards and floors | content | UNKNOWN code runs |
| E1-C1 to E1-C26 | The 26 must-carry rows of E1 section 8 | core: S8 (1-3), I5 (4-5), S6 (6-7), I2 (8), S2 (9), S6 node sensor (10), I6 (11), S10 (12-13), S11 (14), V1 (15), S9 (16), I4 (17), R2 (18), R3 (19), R6 (20), I9 (21), R13 (22), I7 (23), I1 (24), K2 (25), S15 (26) | design |
| E1-preset-scalper | Scalper: cost hurdle, floor, tolerates none, fast readings, rung 0-1 | template A | design |
| E1-preset-orb | ORB: hurdle, floor per open, tolerates open, open shortlist | template orb variant | design |
| E1-preset-intraday | Intraday: hurdle, floor, per pod, session words | template B | design |
| E1-preset-news | News unit: tolerates news, event clock | content template | design |
| E1-preset-reckless | Reckless: gates off, tolerates all but kill, rung 4 | content template; V9 | canvas |
| E1-A1-20 | Assumption reversal: flip to cost check (1), no baseline (2), one sensor one verb (3), verb list (4), bank (5), markout (6), one curve (7), borrowed curve (8), wait verb (9), resting order on wide spread (10), spread recovery seed (11), forward cost (12), dealer skew (13), two venues (14), block counts as reading (15), would-have per refusal (16), refused-share reading (17), control gate (18), gate can't size (19), curves where data allows (20) | 1,2 default block; 3,4,7 core S6/I6; 16 core R3; 19 core (S2 only sizes); 8,20 core I6 options; rest content | PROPOSAL |
| E1-A21-40 | Reverse brainstorm: meaning-flip replay (21), isolation a stand-down row (22), dark runs (23), keep state (24), card clock (25), full bar (26), packs differ (27), words from own percentile (28), as-of only (29), herding count (30), retire card (31), news expire de-risk (32), allowed and active (33), list locked (34), cluster cap (35), three lists scored (36), home fallback (37), tick readings where feed lands (38), clock fact (39), yesterday's curves (40) | 22 core S10; 29 core R13; 33, 37 core I5; 32 core I8; 40 core I6; rest content | PROPOSAL |
| E1-A41-60 | Cross-pollination: forecast and nowcast (41), NOTAM sticker (42), taints and tolerations (43), strengths (44), node affinity (45), triage vitals (46), explore slots on paper (47), aftershock clock (48), yield management (49), readings as pinned packages (50), word plus outlook (51), bee scouts (52), pheromone (53), good-days match (54), outlier ejection (55), feature flags per pod (56), correction record (57), almanac (58), niches (59), no router local rule (60) | 42-44 core S10; 50 core S8 pins; 56 content on S14; rest content | PROPOSAL, GUESS |
| E1-A61-82 | Trader lens: ORB shortlist (61), same window two meanings (62), opening-range quality (63), ORB family cells (64), scalpability (65), tape speed (66), level map (67), context sentence (68), gold reads COMEX (69), mini-micro residue (70), cost per risk across sizes (71), instrument dossier app (72), window card (73), sniping lift (74), news sticker tags (75), pre-event state (76), re-entry on spreads (77), news units tolerate (78), velocity backstop (79), London active today (80), handover re-run (81), spread-to-stop check (82) | 62 core S10; 73 core R16; 74 core S2; 75 core I4; 82 default block (hurdle); rest content | PROPOSAL |
| E1-A83-94 | Systems lens: same-meaning test (83), replay parity check (84), admission from card lag (85), reading price tag (86), publisher pin (87), three forms (88), last-good fallback (89), active markets a reading (90), router as workflow (91), curves as artifact (92), node starts from curve (93), scope keys (94) | 87 core S8; 90 core I5; 92-93 core I6; 94 core S11; 84 content test; rest content | PROPOSAL |
| E1-A95-109 | New physics list (duplicates P1 to P15, plus complexity-entropy plane 107, network markers 108) | content | as P rows |
| E1-B | Party clashes: hurdle plus floor, one curve with age word, morning list, home markets, stickers with accuracy record, physics with nulls | folded into D26, D22, D23, D27 | one mind |

## E2: pods, mini apps, unit and pod (`round-2/expand/E2-pods-miniapps.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| E2-sense1 | Pod as the stack (seven slots) | core S14; word Q3 | RULING (M7, M49) |
| E2-sense2 | Pod as the department (desk) | other: agentic; word Q3 | RULING ("I think", M51) |
| E2-sense3 | Pod as who shares money (pod deployment) | core S14 deployment key | BUILT screen (Portfolio card) |
| E2-sense4 | Pod as how it arrives (package) | core S16 | RULING (M10) |
| E2-words | Pod, pod deployment, desk, mini app; Book and BMS retire as screen words | default vocabulary; Q3 | my read |
| E2-Way1 | Pod compiled into the unit's own blocks | fork F1 shape A | BUILT fingerprint constraint |
| E2-Way2 | Pod as a group document above units | fork F1 shape C | candidates 1, 2 |
| E2-Way3a | Mini app as package | core S16 (orthogonal to the relation) | BUILT runtime |
| E2-Way3b | Mini app as controller publishing rulings | content for slow rulings (allocator); not a brake path | BUILT relay, no importer |
| E2-Way4 | No pod at all; tags and one config | survives inside Way 5 as the empty pod | PROPOSAL |
| E2-Way5 | One pod document split by scope; empty slot = unit's own | fork F1 shape B; its seats core (S14, S7, I9) | MODEL (property test, cuts only) |
| E2-clocks | Slots don't share a clock; allocator is off the order path | decided (D33 area); core S14 placement | reasoning |
| E2-slots-table | Where each of seven slots runs per way | fork F1 material | reasoning |
| E2-exit-gap | Seven slots have no exit; exits stay on the unit; template carries exits, pod ref, presets | core S3, D6; open edge in F5 | round table |
| E2-Pod1 | Relentless (April's vault system) | content pod | old system |
| E2-Pod2 | Session relay | content pod; needs S9, R6 | old system |
| E2-Pod3 | Classic Book | content pod template | Book docs |
| E2-Pod4 | Cushion pair | template A (on, day anchor); content pod | REAL theory; MODEL |
| E2-Pod5 | The old pair as it really was | content pod | R9 |
| E2-Pod6 | Scalper first | template A's pod form | design |
| E2-Pod7 | Human mimic | content pod; needs I12, order flow (Q2) | in-sample |
| E2-Pod8 | Best basket | content pod (allocation mode) | lore |
| E2-Pod9 | Stage switcher | content pod; core I10 seat | RULING (M51) |
| E2-Pod10 | Prop rider | content pod (other users) | REAL rules |
| E2-Pod11 | Earned tiers | content pod | REAL (Topstep) |
| E2-Pod12 | Multi-manager | content pod | REAL press-reported |
| E2-Pod13 | Own size, capped total | default block (group row allocation mode) | REAL bank practice |
| E2-Pod14 | Run together (pod of pods) | content; core `parent` | designed (OPEN-4) |
| E2-Pod15 | Futures desk pod | content pod; needs futures route (Q2) | RULING (M50) |
| E2-Pod16 | Model-sized hybrid | content pod; needs list | PROPOSAL |
| E2-Pod17 | Watched by agents | content pod; C16 open (Q4) | PROPOSAL |
| E2-Pod18 | Volatility core | content pod | REAL backtests |
| E2-Pod19 | Canary | template (third, for a stranger) | trivial |
| E2-Pod20 | Full press (reckless) | content pod; V9; graded F | REAL as ruin |
| E2-field-Q5 | Portfolio stop raising kill: `on_fire` field | core S5 | RULING |
| E2-field-Q1 | A rule closing a position: guard verb plus dictionary exits | core S4 verbs, S3 | RULING |
| E2-field-Q4 | Press after a record passes a rule: press-gate block | content on R5 | design |
| E2-field-restore | Stand down and come back: attack, release, restore on the row | core S5 | design |
| E2-ship1 | A pod document, copied; `.qmxpod` file | core S16 kinds; extension content | PROPOSAL |
| E2-ship2 | Pod plus new blocks through a save door | core K6 | gap verified |
| E2-ship3 | A mini app carrying pods, installed disabled until approved | core S16 lander; install card other: UI | BUILT runtime partly |
| E2-ship4 | A desk: level 3 plus agents, workflows, screens | other: agentic, methodology | PROPOSAL |
| E2-n8n | Store only diffs plus pinned block versions | core D36 | REAL (n8n) |
| E2-roadA | Artifact feed between apps | content (BUILT) | BUILT |
| E2-roadB | Library landing as event | content (BUILT, only qmb-run lands) | BUILT |
| E2-roadC | Proposal to a pod | core K2 door | partly |
| E2-roadD | Reading to a unit | core K3 | not built |
| E2-week | His futures week, walked | content; other: agentic | PROPOSAL |
| E2-gap1 | One lander per app, only `qmb-run` | core S16 | BUILT |
| E2-gap2 | Landers are run-shaped | core S16 | BUILT |
| E2-gap3 | Pack holds plugin.json and skills only | core S16 | BUILT |
| E2-gap4 | pod, pod-block shells; template retired | core S16 | BUILT |
| E2-gap5 | No row saves a block | core K6 | BUILT |
| E2-gap6 | Two block worlds | core S16 | reading |
| E2-gap7 | `reads` refused; relay unwired | core S8, K3 | BUILT |
| E2-gap8 | No app-level `requires` | content | BUILT |
| E2-gap9 | No subscription | content | BUILT |
| E2-gap10 | No pin or upgrade across units | core D40 | BUILT |
| E2-gap11 | Agent code installs only at T2 or after review | other: agentic | BUILT |
| E2-gap12 | `build-mini-app` placeholder; no `build-pod` skill | other: agentic; content | BUILT |
| E2-gap13 | Library block reaching a node | core check first (D46) | UNKNOWN |
| E2-gap14 | A stdlib block bumps the money app; blocks live outside it | design note (F4 core home) | BUILT |
| E2-eval1 | One core in a library both import | core S15 | PROPOSAL |
| E2-eval2 | State in and out: pure and stateful both true | core S15 | reasoning |
| E2-eval3 | Four drivers, one core | core S15 | PROPOSAL |
| E2-eval4 | Size trail equals the decision row | core R1 | PROPOSAL |
| E2-eval5 | Merge order declared | core S15; UNKNOWN node order | reasoning |
| E2-eval6 | `unsupported_blocks` becomes the needs list | core S15 | PROPOSAL |
| E2-eval7 | Conformance tape in CI | core S15, V10 | candidates 2, 3 |
| E2-forced1 | Workflows at trade time: a graph block compiles or publishes a fact | core S16 one catalogue | design |
| E2-forced2 | Replay explores, rerun proves | other: methodology | design |
| E2-forced3 | Compile target = pod document plus unit | core S15 | design |
| E2-g1 to E2-g20 | The 20 must-carry rows of E2 (g) | core: S14 (1-2, 5-6), I9 (3), R3 (4), S1 (7), S2 (8), S4 (9), S7 (10), S11 (11), R5 (12), S5 (13), V9 (14), S3 (15), V7 (16), K3 (17), S16 (18), D40 (19), K2 (20) | design |
| E2-rt1 | Guards change the record, so would-have rows are baseline | core R3 | round table |
| E2-rt2 | Allocator isn't a trade-time slot | decided | round table |
| E2-rt3 | Empty slot means unit's own block | core S14 | round table |
| E2-rt4 | A pod lives on one place; spanning is a mix | design rule | round table |
| E2-rt5 | Team and pod are separable | decided (D32) | round table |
| E2-open1 | Pod swapping exit rows at an anchor | fork F5 shape C, open | dissent |
| E2-open2 | Kill line as warning or wall | decided warning; dissent recorded | dissent |
| E2-open3 | Automatic cut against agents never touch money | Q4 | open |
| E2-open4 | Way 5 contract against a thin group document | fork F1 | open |
| E2-UNK | Ten unknowns (UI not run, group-stage latency, node order, Library block to node, graph compile, Decimal speed, os.replace in relay, raises in two stages, pods in X files, nothing run) | carried as UNKNOWN | UNKNOWN |

## E3: the 302 papers, read for ideas (`round-2/expand/E3-papers.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| E3-1 | Say, do, real: check words against code and record; claim scoreable by code | core R12 claim field; scoring content | REAL small (40 strategies) |
| E3-2 | Run the whole research process on a market with nothing in it | other: methodology | REAL as design |
| E3-3 | Mine and shrink may do as well as strict gates | other: methodology (beside H5 conflict B) | REAL (US stocks monthly) |
| E3-4 | A time-series test can't have everything; print the fold choice | other: methodology; core R8 stamp | theorem |
| E3-5 | Same strategy, different engine, different answer; known-answer cost check | content (cheap test); other: methodology | REAL (five engines) |
| E3-6 | Retune cadence from a budget on harmful updates | core R11 per-change record; scheduler content | MODEL plus clinical |
| E3-7 | Window lengths compete, costs inside the score | content | REAL thin |
| E3-8 | Evidence authorises forgetting | content | MODEL |
| E3-9 | A test for pool or fit per instrument | content | MODEL |
| E3-10 | After a detector fires, when did the change begin | content | MODEL |
| E3-11 | Uncertainty is a gate, not a size divisor | content warning; agrees with trap H5-T5 | REAL one ranker |
| E3-12 | A Kelly fraction with a derivation | content derivation block; parked: numbers | MODEL |
| E3-13 | Three more allocators: factor budgets, agnostic parity, damping knob | content on I10 | REAL and MODEL |
| E3-14 | Size ramps: backfill, pending trades, learned margin certificate | content | medical simulation; GUESS transfer |
| E3-15 | Warning signs depend on the kind of crash | content; rule of thumb on readings | REAL seven events |
| E3-16 | Herding and arbitrage look identical on usual gauges; sign agreement separates | content reading | MODEL (AMM) |
| E3-17 | Stacked checks aren't independent; two thresholds route to review | content scorecard row; alert preset | REAL agent safeguards |
| E3-18 | Statistics papers: simple calibrated threshold first; anytime-valid as a swappable block; no stats engine in core | content; design rule | outside finance |
| E3-19 | Trends behave by timescale; scalper and intraday read it oppositely | content; other: methodology | REAL broad futures |
| E3-20 | Exchange halts bend measured news impact | content flag on measurement | MODEL plus regression |
| E3-21 | A macro agent that earns its weight; Kelly-bettor scoring | content; other: agentic | REAL short; MODEL |
| E3-22 | Forward slippage from the book; depth fragility | content (real books only) | REAL perps, one event lead |
| E3-23 | A third decay: from your own use (crowding ourselves out) | content test on timestamps | MODEL; GUESS |
| E3-24 | The dealer remembers you; two stable moods | content; core R7 per-account series | MODEL institutional |
| E3-25 | Watching 200 units: compile repeated steps into tools | other: agentic | REAL warehouse ops |
| E3-26 | Agents go around a human click | core K5 | REAL tests on real products |
| E3-27 | Every agent loop needs a written stopping rule | other: agentic, methodology | REAL scan |
| E3-28 | Don't show agents each other's tallies | other: agentic | experiment |
| E3-29 | Score agents on audit gaps and discipline apart from returns | other: agentic | REAL recent; one vendor |
| E3-30 | A harness that improves itself; SHEPHERD forking is cheap | other: agentic | coding benchmarks |
| E3-S1 | Mean-reverting energy spread with stop, band, leverage solved together | content seed | one pair one year |
| E3-S2 | Crypto 6-hour trend with trailing stop | content seed; distrust headline | author |
| E3-S3 | Auction features as QML vocabulary | content seed (order flow, Q2) | author |
| E3-S4 | Multi-level imbalance | content seed (real books) | explains |
| E3-S5 | Gold futures trend, Sharpe 2.88 claimed | content seed as a never-real-kit test case | implausible |
| E3-S6 | Short from long trend in CTA returns | content seed | adviser's own |
| E3-S7 | Market making with funding as state | content seed (reckless) | author |
| E3-S8 | Short-dated far OTM put selling | content seed; options not in instruments | in-sample |
| E3-S9 | Deep RL overlay on crypto pairs | content seed | p about 0.06 |
| E3-carry1 | Claim in lineage as metric, benchmark, window | core R12 | REAL |
| E3-carry2 | Per-change record on every self-configured update | core R11 | MODEL |
| E3-carry3 | Promotion and money doors outside agent reach | core K5 | REAL |
| E3-gaps | Retail FX scalping unmeasured; energy one pair; game theory parked; allocation across instruments; Monte Carlo reader missing; text failures | carried; parked: numbers (game theory) | honest |
| E3-table | 302 papers, one line and a triage each (section 6) | material; no row changes a seat | as triaged |

## E4: logic linking (`round-2/expand/E4-linking.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| E4-root | A link has no type and no null; nothing reaches the risk places | diagnosis; core S1-S4, S8, S12 | reasoning |
| E4-J1 | Pipe joint | core S12 roles, S1 inputs | BUILT in logic slots only |
| E4-J2 | Gate joint | core S12 (`veto`, `arming`, `cooldown`) | `filter` BUILT |
| E4-J3 | Scale joint | core S2 | REFUSED |
| E4-J4 | Vote joint | BUILT combiners | BUILT |
| E4-J5 | Switch joint | core S12 `regime_detector`; routes content | REFUSED |
| E4-J6 | Overlay joint | core S7 | STUB |
| E4-J7 | Referee joint | core R8 arms; judge BUILT | BUILT judge |
| E4-boundary | Same boundary or different: the first question about a link | core R16 `decides`; skill content | PROOF (Lean), untested on markets |
| E4-L01 | Link scanner: do these two say more together | content (Lab) | MECH; honest negative |
| E4-L02 | Link proof: the six arms | core R8 arm fields; recipe content | REAL design, small samples |
| E4-L03 | A null is not one thing: name the shuffle | core R16 `null` scheme | REAL (58-100 % false positives naive) |
| E4-L04 | Log the coin: every gate as a treatment; propensity | core R3 `propensity`, would-have writer | PROOF and simulation |
| E4-L05 | Judge a rule by replacing it, never by the missed trade | content skill rule; other: methodology | controlled simulation |
| E4-L06 | Fit map: which edge does this reading belong to | content; core readings on R1 | one honest test |
| E4-L07 | Position as a curve: target-quantity answer type | core S18/S3 answer type; curves content | MECH; two demo days |
| E4-L08 | Fit the worst move, with a refusal | content; needs S8 | author backtest |
| E4-L09 | Calibration contract: a sizing number must mean what it says | core R16 `output_meaning` | backtest |
| E4-L10 | Aftershock clock (Hawkes) | content | academic; untested retail |
| E4-L11 | Lead-lag with an expiry date | core R16 `retest_by`, second instrument input (`context_needs`) | MECH; single passes |
| E4-L12 | Arbitrage maths as a feed alarm | content (SQS) | GUESS |
| E4-L13 | The commuting check: a law for joints | content check layer (S19) | maths |
| E4-L14 | Porting by mapping | content on existing fields | none in trading |
| E4-L15 | Installed against active: who is firing | core I9 direction and family on intents (S7) | SIM small models |
| E4-L16 | Find hidden families from the trades | core I9 many-to-many tags; job content | BT-IS |
| E4-L17 | Tail coupling instead of correlation | content | MECH |
| E4-L18 | Placement as a three-stage score | config plus content; parked: numbers | BT |
| E4-L19 | The clock is a confound: fancy bars don't help on FX | content warning | REAL FX two years |
| E4-L20 | Failures as library cards | content; other: agentic (memory) | authors' negatives |
| E4-W1 | Fleet aftershocks (Hawkes on unit losses) | content, wild | GUESS |
| E4-W2 | Call option on a unit | content, wild | GUESS |
| E4-W3 | The incoherent model stands aside | content, wild | GUESS |
| E4-W4 | Market words as agent memory keys | content, wild | GUESS |
| E4-W5 | Straddle the release | content, wild | GUESS |
| E4-W6 | Evolve joints, not numbers | content, wild | GUESS |
| E4-W7 | Critical slowing from shelf blocks | content, wild | GUESS |
| E4-W8 | Feed a video, get a graph | content, wild; other: agentic | GUESS |
| E4-W9 | Shape distance for model drift | content, wild | author |
| E4-W10 | Biological neuron as fair value band | content, wild | author not live |
| E4-W11 | Agents' own fleet concentration | content, wild | GUESS |
| E4-W12 | Arena mode: weekly recipe tournament | content, wild (Lab) | GUESS |
| E4-WF1 | Search ledger to promotion gate | content recipe; other: methodology | REAL finding |
| E4-WF2 | Graded live demotion | content recipe; needs S4 | MODEL |
| E4-WF3 | External breaker | content recipe; needs S4, I3 | design |
| E4-WF4 | Bucket stress isolation | content recipe; needs S8, S7 | author |
| E4-WF5 | Read-only risk narrator | other: agentic | PROPOSAL |
| E4-WF6 | Bound approval packet | core D40 | BUILT hash |
| E4-WF7 | Governed research pipeline | other: methodology | sobering |
| E4-WF8 | Staged ramp ladder | content (I11 slot) | design |
| E4-WF9 | Shared cost ledger | core I2, R7 | design |
| E4-WF10 | Meta-label exit and size gate | content recipe | BT |
| E4-WF11 | Event calendar control | content recipe; core S10 | author |
| E4-WF12 | Alert rationalisation | other: UI; core R10 | SRE |
| E4-WF13 | Interactive simulation bench | other: methodology | simulation |
| E4-WF14 | Conservative parameter tuning | content motion rule | design |
| E4-WF15 | Propose, constrain, one step | content; K1 fits | robot simulation |
| E4-C1 | One cost number, two jobs | default block (hurdle) plus content gate | REAL |
| E4-C2 | Two-speed drift | content | MODEL |
| E4-C3 | Restore ladder | core S4 RESTORE; methods content | REAL elsewhere |
| E4-C4 | Live cost monitor | content; core R7 | author |
| E4-C5 | Backtest validity stamp | core R8 | measured |
| E4-C6 | Exposure ledger | content; core S7, I9 | author |
| E4-C7 | Risk-as-output accelerator | content | author |
| E4-C8 | Concurrency-aware scalpers | content; core I9 direction | author |
| E4-C9 | Trade-rate-scaled breakers | content (BUILT halt) | design |
| E4-C10 | Immune brake | content | GUESS |
| E4-C11 | Session-open unit | template orb material | author |
| E4-C12 | Regime age | content | author |
| E4-C13 | Exit calibration pipeline | content (step 3) | author |
| E4-C14 | Order flow where it pays | content; Q2 | author |
| E4-C15 | Execution-risk score | content | REAL two coins |
| E4-C16 | Don't queue at the bell | core S18 offset; block content | REAL |
| E4-C17 | Hard cap, soft worry | content | REAL daily |
| E4-C18 | Monday worst move | content | REAL short |
| E4-C19 | Decay and bucket together | content | author |
| E4-C20 | Regimes cut, never re-weight | content | REAL indices |
| E4-C21 | Start diagonal, shrink on coupling | content (Book kind) | author |
| E4-C22 | Fee-aware rare-event classifier | content | author |
| E4-C23 | Evidence record | core I8 | PROPOSAL |
| E4-C24 | Tuner pair | content motion rule | papers |
| E4-C25 | Forward-looking stress | content | author |
| E4-C26 | Statistics apart from the trip | content | author |
| E4-C27 | Crowding test before promotion | other: methodology | simulation |
| E4-C28 | Fast loop, slow agent | core V3; content | author |
| E4-N1 | Link proof, six arms | core R8 fields; recipe content | design |
| E4-N2 | Pair scan before stacking filters | content | MECH |
| E4-N3 | Coin-logged paper twin | core R3 `propensity`, K4 | PROOF |
| E4-N4 | Intraday long curve | content; core answer type | MECH |
| E4-N5 | Fitted tail for the cushion | content | author |
| E4-N6 | Calibrated meta-gate | content | BT |
| E4-N7 | Aftershock cooldown | content (S12 `cooldown`) | academic |
| E4-N8 | Leader as veto with expiry | content; core `retest_by` | MECH |
| E4-N9 | Feed-gap alarm | content (FX) | GUESS |
| E4-N10 | Active mix reading | content; core I9 | SIM |
| E4-N11 | Three-stage placement | content mini app; parked: numbers | BT |
| E4-8a | Already in QML's entry: sources, family, roles, transfer, class meanings, data level, min_sample, reading fields, combiners, motion | keep; don't rebuild | BUILT |
| E4-8b-1 | `output_meaning` | core R16 | S3 proof (trigger compiles in sizer) |
| E4-8b-2 | `assumes` | core R16 | CUSUM 5x case |
| E4-8b-3 | `null` scheme, block length, draws | core R16 | REAL |
| E4-8b-4 | `evidence` label, instruments, source | core R16 | design |
| E4-8b-5 | `retest_by` | core R16 | REAL (links vanish) |
| E4-8b-6 | `knows_at` | core I7 | design |
| E4-8b-7 | `decides` boundary | core R16 | PROOF |
| E4-8c-1 to 15 | Seats: fed inputs to sizer, exits, halts; `reads`; roles; target-position answer; link record; arm fields; propensity and would-have; readings on decision rows; intent with direction and family; second instrument input; many-to-many tags; save a block; identity wired; recipe kind; protected fields | core: I1 and S3 and S4; S8; S12; S18; R8; R8; R3; R1; S7 and I9; S8; I9; K6; D40; R16; K5 protected list | BUILT refusals |
| E4-8d | Copilot and agent rules as a skill (name the joint, check boundary, warn on no null, run link proof, never present a missed trade, warnings never refuse) | content, early (skill) | design |
| E4-seeds-1-14 | Forced pairs onto shelf blocks (entropy gate, Kalman plus CUSUM, trendiness vote, half-life as time exit, efficiency on trailing, choppiness switch, TPO stop, momersion window, GK vs close vol gap, range over ATR day type, funding gate, autocorrelation switch, record sets size floor, self-scaled thresholds) | content seeds; 4 and 13 need S13 motion on exits and sizer | GUESS |
| E4-seeds-15-20 | Medicine: benefit stopping, late-onset harm, run-in placebo twin, number needed to treat, dose-response for brakes, crossover design | content seeds; 17 fits K4 | GUESS |
| E4-seeds-21-25 | Reliability: pre-mortem card, checklist blocks, black-box recorder, shelving with expiry, Weibull life | content seeds; 23 fits R1 | GUESS |
| E4-seeds-26-30 | Ecology: carrying capacity, niche overlap, keystone unit, succession, herd immunity | content seeds | GUESS |
| E4-seeds-31-39 | Information: MIC vs distance correlation, compression day type, spectrum drift, wavelet denoise, Catch22 vocabulary, DMD short, Mann-Whitney before pooling, Kruskal-Wallis, uniqueness throttle | content seeds | author |
| E4-seeds-40-45 | Finance theory: covered call, collar, insurance seller, payoff-shape tag, CFTC positioning, implied minus realised budget | content seeds; 40 reckless expressible | author |
| E4-seeds-46-59 | Agents and canvas: three links proposal, explain this link, recipe diff, link heatmap, remix, bounty, start from failure card, devil's advocate null, pattern bitmap ports, repair failed patterns, paper to joints never code, paper-to-block card, shelf of nulls, shared floor table | content seeds; 56 other: agentic | GUESS |
| E4-seeds-60-72 | Reverse brainstorm flips: count tries, locked hold-out, random arm, output_meaning, port by map, name the shuffle, referee grades, retest_by, would-have rows, equal samples, one change at a time, real-tick stamp, worst bin | each maps to a core field or rule above | design |
| E4-seeds-73-80 | Scalper-specific: smallest scalper recipe, rate-scaled cooldown plus aftershock, netting-aware pair, reject streak gate, markout maker-taker switch, jitter block, min-hold as turnover cut, fee-threshold labels | content seeds | author |
| E4-seeds-81-90 | Intraday-specific: first half hour into last, day-type switch, curve sizer to close, Monday overlay, overnight tail reading, gap accept or reject, London flip with delay, Larry Williams shelf, regime age tapers adds, VWAP distance scale | content seeds | author |
| E4-seeds-91-100 | Book and fleet: hidden-family budget, tail-coupled caps, active mix at releases, effective bets on discovered families, exposure graph cycles, direction eliminator, fleet inaction audit, weekly link rescan, retire links to paper, boredom alarm | content seeds | GUESS |
| E4-game | Game theory in md 15541, 17546 | parked: numbers | not what a trader means |
| E4-gaps | No link run; retail FX unmeasured; energy none; alphaXiv chat pass not run; corpus mostly unread | carried | honest |

## E5: fleet watch, self-configuration, newcomer, developer (`round-2/expand/E5-fleet-selfconfig-dev.md`)

| Id | One line | Fate | Evidence |
|---|---|---|---|
| E5-census | Shipped decay job: ~91 cards a night for 200 healthy units | finding; replaces the rule | MODEL |
| E5-L0 | Inside the unit: brakes act, no agent | core S4, V3 | RULING |
| E5-L1 | Health script every 5 minutes, fires on hash change | content (BUILT monitor node) | BUILT |
| E5-L2 | Nightly fold: one row per unit | content; core R9 | pieces BUILT |
| E5-L3 | Grouping by root-cause key | content; core R10 | design |
| E5-L4 | Triage agent reads top K plus incidents, names a cause from a fixed list | other: agentic | design |
| E5-L5 | Slow jobs: coroner, reruns, replay tuning | other: agentic | templates BUILT |
| E5-L6 | To him: digest, cards, pages | other: UI | BUILT pieces |
| E5-jobs | Fixed agent jobs: triage, morning words, coroner, sitting-duck advocate | other: agentic; content | design |
| E5-tiers | Silent, digest, card, page | other: UI; core R10 | SRE |
| E5-away | A card carries what silence means; units run under pod rules | config | BUILT template |
| E5-list1 | Who gets looked at: ranked top K, no threshold | config | MODEL |
| E5-list2 | Who gets acted on: strict bar under a fleet budget | config; core K6 place | MODEL (e-detector) |
| E5-correction | 10x units slows catch by 30-135 %, not tenfold | finding | MODEL |
| E5-pooling | Family pooling: 179 days alone, 51 pooled | core I9 family id | MODEL |
| E5-incident | One incident, one card; key written where seen | core R10 | design |
| E5-20v200 | Rows read nightly 24k vs 236k without a fold | finding | arithmetic |
| E5-app1 | App ships a workflow: no installer found | other: agentic | BUILT gap |
| E5-app2 | App reads journals: `data_reads` market only | other: agentic | BUILT gap |
| E5-app3 | App lands a card: path UNKNOWN | other: agentic | UNKNOWN |
| E5-app4 | Guide for building a mini app: placeholder | other: agentic | BUILT gap |
| E5-app5 | Risk label `shows` fits | note | BUILT |
| E5-reuse | Reuse map for eight templates (dc, t7, dm, gw, rk8, s2, morning-digest, pp) | content | BUILT |
| E5-pub1 to 12 | What the unit must publish: identity with type tag and family; state word; decision rows; trade row; receipt; would-have; risk_event; calibration; root-cause key; expectation at birth; fleet read | core I9, R9, R1, R2, R3, R4, R10, I14 | design |
| E5-find1 | Engine memory never ends (`SlowState.read`) | core S13 bounded window; other: repair flag | BUILT finding |
| E5-find2 | The built engine already is an applier | decided (D16) | BUILT finding |
| E5-find3 | It sees only taken trades; drifts down as cheap exploration | finding | BUILT |
| E5-census1 | Of 172 classifiable ledger rows, 119 read facts only | finding against the learner premise | rough match |
| E5-census2 | Telling 0.05R apart takes ~1,600 trades | finding | arithmetic |
| E5-M1 | Built motion engine | default block (correct), per-type preset | BUILT; MODEL |
| E5-M2 | Facts alone (track) | default block; cannot fix a wrong start | MODEL |
| E5-M3 | Learner with bounds plus applier | content; fork F2 shape A | MODEL little gain |
| E5-M4a | Small steps, honest guard (live climb) | dropped as live rule: stalls | MODEL |
| E5-M4b | Small steps, no guard | dropped as live rule: wanders | MODEL |
| E5-M4c | Whole range, recent window | dropped as live rule: too little history | MODEL |
| E5-S | One replay over long history finds the number | default block (find) | MODEL; fooled by flattering replay |
| E5-S+M1 | Find, then correct | default (D16) | MODEL held across worlds |
| E5-controls | C-right, C-wrong, C-walk, C2 shuffled | content controls; core report with and without motion | MODEL |
| E5-size-test | Own-record press: large gain with runs for a scalper, loss for swing; volatility fact helps all | template A press on (day anchor), B off; vol fact available | MODEL |
| E5-job-find | Find at birth or on demand, counted | default; other: methodology for "better" | BUILT pieces |
| E5-job-track | Track facts live, pure arithmetic | core S13 `scaled`, S8 | BUILT for logic |
| E5-job-correct | Correct every N trades when flat, bounded, switchable | core S13 | BUILT |
| E5-auth-lots | Lots by track from money, stop, value per point | core S1 | arithmetic |
| E5-auth-money | Money at risk per trade: find sets, track scales | config; parked: numbers | design |
| E5-auth-stops | Stop and target multiples: find, track via ATR; correct per pod | config; row records R change | design |
| E5-auth-filters | Filters and thresholds: find, track, correct | default | BUILT path |
| E5-auth-press | Press and accelerators: correct per pod, off where trades are few | config | MODEL |
| E5-auth-cost | Cost gate, news window: track | default | RULING (M51) |
| E5-auth-brakes | Brake levels: find from own replay | config | design |
| E5-auth-markets | Markets, sessions: find then u1, u2, s2 | content | BUILT templates |
| E5-auth-never | Never-self-tune list per template; kill switch fixed | core S13 marker; V2 | RULING |
| E5-rules | Inside range moves by own rule; outside is a new version and his click; agents never on a running unit | core D17 | BUILT identity table |
| E5-not1-7 | Not in baseline: separate applier, dead band, retune share cap, target-with-bounds object, bandit over presets, pooled priors, Simplex | content | MODEL did not earn |
| E5-seat1 | `authority` real `off` and `motion_inside_range`; non-flat anchors; calendar cadence | core S13 | BUILT gap |
| E5-seat2 | Calibrated without a logic stamp | core S13 | BUILT gap |
| E5-seat3 | Bounded window on engine memory | core S13 | BUILT gap |
| E5-seat4 | `scaled` motion block | core S13 | design |
| E5-seat5 | Reason on every resolved value; Origin "found by replay" | core R1, S13 | design |
| E5-seat6 | Report with and without motion, always | core (MotionSwitch exists) | BUILT |
| E5-climb | Live hill climb is the wrong place; Lab on long history, counted | decided (D16); content job | MODEL |
| E5-style | Help or harm by style: correct off for swing press; cadence per type | template presets | MODEL |
| E5-herd | Herding: daily cap only delayed; room for a group rule, not the rule | core K6 group place | MODEL (filters only) |
| E5-G1 | No installer a stranger can run | other: release | BUILT gap |
| E5-G2 | Install and launcher describe the older host | other: release | BUILT gap |
| E5-G3 | First start hands over to a desktop app nobody could find | other: UI | UNKNOWN |
| E5-G4 | A step ticks when opened, not done | other: UI | BUILT gap |
| E5-G5 | With demo off nothing has content | other: UI | BUILT gap |
| E5-G6 | Spotware approval takes about a day | outside; Q1 | BUILT note |
| E5-G7 | Never run against a real broker | other: repair; Q1 | BUILT |
| E5-G8 | Can a newcomer backtest before a broker exists | core if no (D49) | UNKNOWN |
| E5-G9 | One template | core 4.2 | BUILT |
| E5-G10 | Copilot has no real risk choice from the shelf | core S1-S4 | BUILT |
| E5-G11 | A working default size and brakes | core 4.1 | this session |
| E5-G12 | Skill says never test; tools do | other: agentic | BUILT |
| E5-G13 | Dictionary's risk blocks cannot be tried | core S3, S4 | BUILT |
| E5-G14 | Persona speaks of one person | other: agentic | BUILT |
| E5-G15 | No one-click "watch my units" | content | BUILT |
| E5-G16 | Cost and fact feeds absent at live | core I2, I3 | BUILT |
| E5-G17 | Customize: kinds are shells; Lab has no pods | core S14, S16 | BUILT |
| E5-new1 | Working template per type, compiling and passing G | core 4.2 | design |
| E5-new2 | Default size and brakes run with nothing set | core 4.1 | design |
| E5-new3 | The walk as a rehearsal test | core K7 | BUILT start |
| E5-map | Module map | core D50 | reading |
| E5-trap | Two risk worlds; one statement per module; subtract what retires | core D50 | reading |
| E5-add1 | Adding a logic block: save row, scaffold, traced Library path | core K6; path UNKNOWN | BUILT gap |
| E5-add2 | Adding a sizer: face check, money then converter, reference block reads evidence | core S1 | BUILT trap |
| E5-add3 | Adding a brake: a host that runs them, required statistics, would-have | core S4, R3 | BUILT gap |
| E5-add4 | Adding an instrument class: rows not branches; test fails on branching | core I4, D50 test | BUILT (two readers only) |
| E5-add5 | A number that moves | core S13 | BUILT |
| E5-add6 | A check layer | core S19 | BUILT stops at F |
| E5-add7 | A tool for agents: direction | other: agentic | BUILT gap |
| E5-tests-exist | Socket contracts, census, goldens, upgrader rule, layer F and G, placeholders tool, apps in CI, failure register | keep | BUILT |
| E5-tests-missing | Same decision both hosts; exits never blocked; refused fields labelled incl. authority and reads; number has reason and range; motion bounds plus shuffled control; every template reaches paper; no agent path to money; RiskState one fold | core D50 | design |
| E5-debug | One decision row that replays; `explain_size`; replay test | core R1 | BUILT literal today |
| E5-logs | Logs apart from journals kept; add trace id, motion counters, stack choice his | core R15; stack other | BUILT |
| E5-ver1 | Widen all sockets in one bump | core V12 | BUILT constraint |
| E5-ver2 | Re-test workflow per bump | content | design |
| E5-ver3 | Pins with diffs, lineage, forwarding map | core D40 | design |
| E5-ver4 | Keep upgrader chain; cold restore rebuild UNKNOWN | core D40; UNKNOWN | BUILT |
| E5-ver5 | A file extension | content (config) | RULING ("I don't care") |
| E5-guide | Generated `EXTENDING.md` with staleness test | core D50 | design |
| E5-grill | Self-grilling: facts alone equal C-wrong; S lost to flattering replay; applier worded down; herding limited | recorded corrections | honest |
| E5-F1 to F19 | Flaws for the agentic upgrade (build-mini-app placeholder; workflows entrypoint; data_reads; inbox path; scripts can't read Library; cron clocks; no fleet read; no attention budget; closed card asks; tighten says nothing; no save row; one template; skill vs tools; judge as operator; no direction; no triage job; no replay of runs; one-person persona; copilot not told about Lab) | other: agentic (section 8 of FUNNEL) | BUILT gaps |
| E5-hand | Hand-offs to methodology, numbers, UI, repair, release | FUNNEL section 8 | design |
| E5-must1 to 26 | The 26 must-carry rows of E5 section 8 | core: S13 (1-5, 8), S1 (6), report both (7), I14 (9), I9 (10), R9 (11), R2 (12), R3 and R4 (13), R10 (14), R9 fleet read (15), 4.2 (16), 4.1 (17), D49 (18), K7 (19), V12 (20), R1 (21), D50 (22-24), K6 and D40 (25), D50 guide (26) | design |

## X0 to X7: the 510 hybrids (`expansion/X*.md`, through `funnel/HYBRID-FATES.md`)

The old tier (core, shadow, later, dropped) is material only. The new fate is by the round's test. Where the old tier came from the dollar sim or the go-live lens, the row says what it is now.

| Id | One line | Fate | Evidence |
|---|---|---|---|
| X0-01 | One loss currency; routine risk and feasible size per instrument | core I4 | design |
| X0-02 | Effective-bets split as the B factor | content allocation mode (sqrt); was law by dollar sim | MODEL |
| X0-03 | Sleeves as risk shares; re-slotting | content pod | PROPOSAL |
| X0-04 | The edge is a gate; breadth is the amount | content gate block; other: methodology | PROPOSAL |
| X0-05 | Cushion pair at a declared anchor | core R5; template A on | REAL theory; MODEL |
| X0-06 | Macro governor, cut-only | content | idea |
| X0-07 | Isolation by underlying process | content | author |
| X0-08 | Three signals apart with their own speeds | core S5 attack and release; S4 | design |
| X0-09 | Six-tier ramp | content on I11 | PROPOSAL |
| X0-10 | Hours clause on counts | content; core I9 driver tags | REAL insurance |
| X0-11 | RiskState rows: exposure per bet key, open risk, drawdown | core R9 | design |
| X0-12 | Venue capacity probe | content | idea |
| X0-13 | R gross at the disaster stop, net_r beside, cut inside the loss distribution | core I13, R2 | design |
| X0-14 | Admission: low end positive after costs; k | content gate; parked: numbers (k) | PROPOSAL |
| X0-15 | FI cut as the working exit, disaster clamp, safest exit wins | template A; core S3 | MODEL |
| X0-16 | Money at the unit's own percentile over a window in trades | template A, B on | MODEL |
| X0-17 | Size bound with costs in the denominator; round down; skip; lot-shed | default block (denominator); shed content | design |
| X0-18 | Execution-fit gates as shadow labels | content (SQS-3) | author |
| X0-19 | Scalper accelerators on the receipt | content on S2 | MODEL |
| X0-20 | Tail-loss sizing for negative skew | content base | simulation |
| X0-21 | Tick rate as the activity gauge | content; I7 (Q2) | vendor |
| X0-22 | Sub-minute maker scalper | content, wild | author |
| X0-23 | Intraday risk unit with the hold's volatility forecast | content base | PROPOSAL |
| X0-24 | Dynamic SL and TP rebuilt; breakeven after test | template B (after step 3) | April spec |
| X0-25 | ORB as a family across opens | template orb; core I9 | REAL stocks in play |
| X0-26 | Placement by persistence readings | content (finder) | MODEL lag |
| X0-27 | Day boundary as a contract; counters persist | core R5 | design |
| X0-28 | Daily ladders as burn-rate tiers | content | SRE |
| X0-29 | Tier ladder and persistence press | content | REAL rules |
| X0-30 | Session-open and fix caution windows | core S9; widths content | fix REAL |
| X0-31 | Swing risk unit | content | PROPOSAL |
| X0-32 | Thesis reversal exit for trend units | template B (thesis exit) | REAL paper account |
| X0-33 | Carry, swap, funding, roll in the cost record | content on I4, I2 | REAL rules |
| X0-34 | Swing brakes | content | PROPOSAL |
| X0-35 | Pyramiding, calm scaling | content | author |
| X0-36 | Swing breadth by HRP | content | author |
| X0-37 | Two per-instrument-hour tables | core I2, I4 | REAL cost shape |
| X0-38 | Venue rule as a flag on the record | core I4 | REAL books |
| X0-39 | News window first slice: entries only, both legs | core S10; default | author E-mini |
| X0-40 | Day budget scaled by open breadth | content pod rule | author |
| X0-41 | Factor buckets | core I4 bucket; rule content | SIMM |
| X0-42 | Regimes cut gross | content | author |
| X0-43 | Risk-off tell stack | content | author |
| X0-44 | Presets over cells; override chain | core keys reserved; templates | software checked |
| X0-45 | Per-class feasibility verdict, re-run at anchors | core D5 | arithmetic |
| X0-46 | Placement score | content (finder) | PROPOSAL |
| X0-47 | Sniping windows as counted slices | core R16; content finding | author |
| X0-48 | Contexts not sessions | content on S8 | PROPOSAL |
| X0-49 | Style as a dial | content optional derivation (was dropped) | wild |
| X0-50 | Dry chassis as the null | core K4 | design |
| X0-51 | Multi-position units | core S17 | RULING (A8) |
| X0-52 | Cost-of-conservatism meter | content; core R3 | MODEL |
| X0-53 | World switch resets; costs per world | core I9, I2 | design |
| X0-54 | Crypto parts | content pod | author |
| X0-55 | Energy and stocks as data overlays | content rows | exchange facts |
| X1-H01 | Spec and status with separate write rights | core I9, R9 | REAL (Kubernetes) |
| X1-H02 | Learner publishes a target with bounds | content; fork F2 | REAL (VPA); MODEL little gain |
| X1-H03 | Applier with authority modes | content object; `authority` field core S13 | REAL (VPA) |
| X1-H04 | Guard per tuned number, freeze after trips | core S13 | elsewhere |
| X1-H05 | Asymmetric motion; cautious direction | core S13 room; rule content | elsewhere |
| X1-H06 | Never-self-tune list | core S13 marker; list config | elsewhere |
| X1-H07 | Reason code on every resolved value | core R1 | spec |
| X1-H08 | Derivation block, receipt, fallback ladder | core S13 | PROPOSAL |
| X1-H09 | Expressions compiled to blocks | content | REAL (n8n) |
| X1-H10 | Trading-state spine; kill levels stay facts | core S4 | REAL (Nautilus) |
| X1-H11 | Restore: retry-then-lockout; probes later | default; core S4 | REAL elsewhere |
| X1-H12 | Shadow switch on every row | core S5 | design |
| X1-H13 | One arbiter per scope; any brake blocks every raise | default group row (raise gate), not law | design |
| X1-H14 | One registry row per control | core S5 | PROPOSAL |
| X1-H15 | Risk profile as its own document; unknown fields refused | core S14 (the pod document is that profile); census core | REAL (Nautilus) |
| X1-H16 | One schema, many presets | core S16 template kind | REAL (Helm) |
| X1-H17 | Packs that stack with combiners | core S14 composition rules; packs content | checked (LEAN) |
| X1-H18 | Instrument risk record as the facts object | core I4 | PROPOSAL |
| X1-H19 | Needs list the host must meet | core S15 | REAL (Bevy) |
| X1-H20 | Template behind three verbs | core S15 | design |
| X1-H21 | Self-test card; stress battery | core D40; battery content | design |
| X1-H22 | Trust ladder; signed blocks | content; signature check core K6 | REAL (n8n) |
| X1-H23 | Three faces | content | BUILT shape |
| X1-H24 | Raw-code hatch, quarantined | content | design |
| X1-H25 | Two adapters per slot | core D50 | design |
| X1-H26 | Guard node-local, two adapters | fork F1; seam K1 core | design |
| X1-H27 | `before_order` pass, shrink, refuse | core S7, K1 | design |
| X1-H28 | Fast lane feeds facts; a brake raises a stand-down, never lowers kill | core V2 | RULING |
| X1-H29 | Risk Lab mini app | content | PROPOSAL |
| X1-H30 | Pod as a shippable bundle | core S16 | BUILT (MIS runs blocks by id) |
| X1-H31 | Same compiled unit and guard on PC and node | core placement (S5, S14) | BUILT one path |
| X1-H32 | Budget share travels with the deployment | core I3 | elsewhere |
| X1-H33 | Lab as a producer; compile target | core S15 | designed |
| X1-H34 | Tag scopes | core S11 `tag:`; drop-ins content | elsewhere |
| X1-H35 | Down as caps and states, up as events | content ledger map; S19 | design |
| X1-H36 | Cascade over keys | core group rank | elsewhere |
| X1-H37 | Full override chain | core keys reserved | SIMM |
| X1-H38 | Same bet once; parent limit below the sum | core I9; default block (parent limit) | REAL banks |
| X1-H39 | One hard floor, the buffer, two anchors | core V5, R5; values parked | design |
| X1-H40 | Profile, cluster tags, portfolio config | core I10 `tag:` and `parent`; structure his later | no generation ran it |
| X1-H41 | Shedding by class; burn tiers | content | SRE |
| X1-H42 | Methodology and cluster drop-ins | content | design |
| X1-H43 | Pinned versions, migration map, identity labels | core D40 | REAL (Simulink) |
| X1-H44 | Two records | core D40 | BUILT judge |
| X1-H45 | A new version shadows; canary later | core rollout field | production elsewhere |
| X1-H46 | Effect-bound click | core V4 | REAL (Terraform) |
| X1-H47 | Upgrade offers | content | checked |
| X1-H48 | Conservative bandit | content | papers |
| X1-H49 | Read door | core K2 | design |
| X1-H50 | Proposal door: cut-only applies; loosening is a card | core K2; Q4 | design |
| X1-H51 | `rp-` nightly workflows | content | design |
| X1-H52 | Steward boundary | core V3 | REAL paper |
| X1-H53 | Tool rows read and propose; run | core K2 | BUILT rows |
| X1-H54 | Read-only explainer | content on core R1 `explain_size` | design |
| X1-H55 | Agent department plugs in through the two doors | other: agentic | design |
| X1-H56 | Compiler format bump | core V12 | BUILT constraint |
| X1-H57 | Guard package | fork F1; K1 core | design |
| X1-H58 | Sizer inputs widened; receipt made real | core I1, R1 | BUILT gap |
| X1-H59 | Trade rows carry mechanism, costs, excursions, stage | core R2 | BUILT kind fields |
| X1-H60 | Exits after entry run; stops tighten | core S3, V6 | design |
| X1-H61 | Closed reason codes; constants as rows; scope keys | core R4, S11 | bug verified |
| X1-H62 | Library kinds beyond risk-profile | core S16 | shells today |
| X1-H63 | Balance refresh, commission key, cost profile writer, slippage script | core I3, I2 | BUILT gaps |
| X1-H64 | Agent rows and the socket contract on Library blocks | core K6, S16 | design |
| X1-H65 | Risk-couplings check | core S19 | BUILT script |
| X1-H66 | Catalogue to dictionary entries | content | design |
| X1-H67 | New block roles | core S12 | PROPOSAL |
| X1-H68 | Class coverage on entries | core R16 `evidence` | design |
| X1-H69 | Central oracle | dropped: breaks units-stand-alone | ruling |
| X1-H70 | Genome variants | content, wild | papers |
| X1-H71 | Runtime `affects` edges | dropped: too much machine | ruling |
| X1-H72 | Overrides by a context word | content | PROPOSAL |
| X1-H73 | Dry chassis offline; live twin | core K4 | design |
| X1-H74 | Netted virtual positions | content on S18 | author |
| X1-H75 | Feedback controller permission | content if wanted | PROPOSAL |
| X1-H76 | Three weights on every decision | core R1, R15 | practice |
| X1-H77 | Slot self-optimisation by proposal | content | PROPOSAL |
| X1-H78 | Marketplace | content after S16 | PROPOSAL |
| X2-H01 | Horizon floor-odds sizer | content block, off, labelled MODEL (was law) | MODEL |
| X2-H02 | Day-sigma budget | content (one formula with H01) | MODEL |
| X2-H03 | Edge dial field | content; `edge_range` on R12 core | shrinkage sims |
| X2-H04 | Cost-and-gap Kelly ceiling on the receipt | content | author |
| X2-H05 | Risk-constrained Kelly | content base | REAL theory |
| X2-H06 | Smallest-wins, binding clamp named and counted | core R1 | REAL (dash.js) |
| X2-H07 | Cushion clip with the reserve | core I15 hook; values parked | proofs |
| X2-H08 | Tail-budget sizing | content base | simulation |
| X2-H09 | Swing holding-period risk | content base | PROPOSAL |
| X2-H10 | One-ledger pair | core R5; template A on | REAL theory; MODEL |
| X2-H11 | Portfolio ledger with an event window | core R5 scope; window content | PROPOSAL |
| X2-H12 | Per-scope anchor clocks | core R5 | demo tests |
| X2-H13 | Levels as fractions of the baseline; start from holdout | core I11; start rule content (was law) | design |
| X2-H14 | Slow start one level per clean cohort | content | medicine |
| X2-H15 | Restore engine beyond retry-then-lockout | content | REAL elsewhere |
| X2-H16 | EWOC steps | content | simulation |
| X2-H17 | Conservative-UCB probe | content | bandit sims |
| X2-H18 | Tier ladder | content | REAL rules |
| X2-H19 | Persistence press | content | REAL monthly |
| X2-H20 | The pair's proof card as switch-on; resize replay | content press gate; core R2 fields | REAL product |
| X2-H21 | Pyramiding for trend | content; core S17 | author |
| X2-H22 | Calm-volatility scaling | content | REAL; failed generalisation |
| X2-H23 | Capacity finder | content | REAL betting |
| X2-H24 | Raise permission gate | default group row | design |
| X2-H25 | Generic graded step nomogram | content | author |
| X2-H26 | AIMD red-zone mode | content | REAL networking |
| X2-H27 | Size = base x level x taper | core S2 chain structure | design |
| X2-H28 | Breadth-to-budget on residual stressed correlation | content allocation mode | MODEL |
| X2-H29 | Overbooking as cushion lending; own full size under a parent | default block (parent limit); lending content | REAL banks |
| X2-H30 | QoS classes and lending | content | REAL (Kubernetes) |
| X2-H31 | AIMD shares | content | analogue |
| X2-H32 | Hierarchy and inverse volatility for swing | content | author |
| X2-H33 | Marginal stress budget | content | author |
| X2-H34 | Bet key and basket cap; heat cap | core I9; heat cap content | textbook |
| X2-H35 | ORB family budget | content; core I9 | PROPOSAL |
| X2-H36 | Open-breadth scaling | content | author |
| X2-H37 | Poker-band pots | content | lore |
| X2-H38 | Swarm split | content, wild | analogue |
| X2-H39 | Cost triple | core I2 denominator; ceiling and gate content | author |
| X2-H40 | Session multipliers and premium lifts deleted | dropped as law; a window lift is a block on S2 | design |
| X2-H41 | Carry and funding in the hold | content | REAL rules |
| X2-H42 | Cost nomogram before the SQS block | content (SQS-4), off | author NQ |
| X2-H43 | Combined-flow netting | content on S18 | author |
| X2-H44 | Asymmetric equity basis | core I3 | REAL prop |
| X2-H45 | Feasibility-first admission, re-run at anchors | core D5 | MODEL |
| X2-H46 | Lot dither | content option (was dropped) | analogue |
| X2-H47 | Three-number record | core I4 | REAL SIMM |
| X2-H48 | Tick-size tiers | content I4 field | author |
| X2-H49 | Whole-contract ladders | content | design |
| X2-H50 | Deployment carries share, costs, level | core I3, I9 | REAL design |
| X2-H51 | The loop for sizing inputs | core S13 (motion reaches risk numbers) | design |
| X2-H52 | Simplex safe-region fallback sizer | content | REAL robotics |
| X2-H53 | Bandit | content, wild | papers |
| X2-H54 | Genomes | content, wild | papers |
| X2-H55 | Thermostat | content, wild | GUESS |
| X2-H56 | Gain-lock ratchet | content on R5; floor V5 | REAL funds; MODEL |
| X2-H57 | Priced reinstatement | content, wild | insurance snippet |
| X2-H58 | Cut-only agent evidence | core I8 | design |
| X2-H59 | Lab as run-surface tenant | other: UI, agentic; S15 | designed |
| X2-H60 | Martingale firewall | content warning on S19, never a refusal | REAL ruin |
| X2-H61 | Meta-label sizing | content | in-sample |
| X2-H62 | Macro-state multiplier | content | idea |
| X3-H01 | Own-percentile money bench | template A, B on | MODEL |
| X3-H02 | REDUCING at own p10 | content | MODEL |
| X3-H03 | Loss points | content | never ran |
| X3-H04 | Money ledger; event-ledger rates | core R2, R5 | MODEL |
| X3-H05 | His "about three" at the unit's own run length | template A present, off | MODEL |
| X3-H06 | Persistence test that would switch H05 on | content | MODEL |
| X3-H07 | AIMD red-zone | content | MODEL |
| X3-H08 | Fire-density sentinel | content | MODEL |
| X3-H09 | Expected fire band on the card | core I14 card field | PROPOSAL |
| X3-H10 | Context-tagged density | content; fire tags core R4 | PROPOSAL |
| X3-H11 | Trade CUSUM key | content block, off by default | MODEL |
| X3-H12 | Scorecard over time | content | counterfactual |
| X3-H13 | Random-control certificate as a report | content report; core R3 | REAL one test |
| X3-H14 | Shadow-first switch | core S5 | design |
| X3-H15 | Retry-then-lockout | default restore | REAL elsewhere |
| X3-H16 | Probe on the twin | content | REAL elsewhere |
| X3-H17 | Memory ceiling | content | REAL elsewhere |
| X3-H18 | Earned restore after a slow demotion | content | PROPOSAL |
| X3-H20 | Hours-clause ledger | content; core I9 tags | REAL insurance |
| X3-H21 | Chorus | content | spec |
| X3-H22 | Burn-rate permit | content | SRE |
| X3-H23 | Methodology pooled CUSUM | content; core I9 family | MODEL |
| X3-H24 | Portfolio day stop | default group row | MODEL |
| X3-H25 | Cushion clip | core I15 | proofs |
| X3-H26 | Pod-style ladder on capital share | content | REAL press |
| X3-H27 | Priority shedding | content | REAL Google |
| X3-H28 | Two-tell isolation | content | author |
| X3-H29 | SQS K-of-N class caution | content | REAL mechanism |
| X3-H30 | Peer ejection | content | REAL Envoy |
| X3-H31 | News window, entries only | core S10; default | author |
| X3-H32 | Region shift | content | old rule |
| X3-H33 | Isolation lifecycle (TTL, staged resume) | core S10 expiry and resume fields; rule content | design |
| X3-H34 | Slow isolation by card | other: agentic; K2 | PROPOSAL |
| X3-H35 | Scope keys in the stand-down table | core S11 | design |
| X3-H36 | Unknown is not calm | core S10 | design |
| X3-H37 | Weekend scaler | content | author |
| X3-H38 | Stopping-premium gate per unit | content Lab test | REAL daily |
| X3-H39 | Cut from the winners' MAE | template A on | MODEL |
| X3-H40 | Thesis-first FI with a price backstop | template B on | REAL paper account |
| X3-H41 | Breakeven after the two-arm test | content | no test |
| X3-H42 | Survival hazards | content | one mixed test |
| X3-H43 | Exit families as defaults | templates A, B; content | theory per cell |
| X3-H44 | Exits feed the sizer | content base | MODEL |
| X3-H45 | Mechanism and outcome on every trade row | core R2 | BUILT fields |
| X3-H46 | Exits never blocked | core V1 | RULING |
| X3-H47 | Stressed-spread fills in replay | other: methodology | secondary |
| X3-H48 | Zones as the display | content | REAL regulatory |
| X3-H49 | Money fast, warning reversible, second warning to paper | core S4 states; rule content | MODEL |
| X3-H50 | Bad-day classifier | content (agentic) | PROPOSAL |
| X3-H51 | Input-first: cost, rate, replay match | core K4 | practitioner |
| X3-H52 | Lifetime false-demotion budget | content | simulation |
| X3-H53 | Re-promotion by his click | core V4 | RULING |
| X3-H54 | Regime-conditional expectation | content | author |
| X3-H55 | Upside alarm | content | prop |
| X3-H56 | Worry lines | content | REAL daily |
| X3-H58 | Registry row | core S5 | PROPOSAL |
| X3-H59 | Five-state spine | core S4 | REAL (Nautilus) |
| X3-H60 | Deterministic fast loop | core V3 | RULING |
| X3-H61 | Self-configuring brake thresholds through the loop | core S13 | design |
| X3-H62 | Kill switch fit | core V2, S5 `on_fire` | RULING |
| X3-H63 | SQS as sensor and gate | core S6; default floor | BUILT rule |
| X3-H64 | Sitting-duck meter | content | MODEL |
| X3-H65 | Choke budget as the harness total | content report; no CI block | MODEL |
| X3-H66 | Danger accumulator | content | GUESS |
| X3-H67 | Brakes staking wealth | content | GUESS |
| X3-H69 | Get-even flag | content | REAL traders |
| X3-H70 | Drawdown freezes agent grants | other: agentic | one live case |
| X3-H71 | Execution-anomaly brake | content | PROPOSAL |
| X3-H72 | Changepoint cooldown | content | REAL one fair test |
| X3-H73 | Regime-age taper | content | one gold test |
| X3-H74 | Day-boundary contract | core R5 | demo tests |
| X3-H75 | Order-boundary veto | core I15 | design |
| X4-01 | Losing together: day stop and bet keys | content scenario; exercises I9, group row | design |
| X4-02 | Correlation spike | content scenario | design |
| X4-03 | Same signal, many units | content scenario; exercises I9 | design |
| X4-04 | The logic fades everywhere | content scenario | design |
| X4-05 | Winning together | content scenario | design |
| X4-06 | Three books, one account | content scenario; exercises I3 | design |
| X4-07 | The slow bleed | content scenario | design |
| X4-08 | One class turns toxic | content scenario | design |
| X4-09 | The false isolation | content scenario; exercises R14 | design |
| X4-10 | One region goes bad | content scenario | design |
| X4-11 | Isolation with positions open | content scenario; V1 | design |
| X4-12 | Resume after isolation | content scenario | design |
| X4-13 | Isolation by agent evidence | content scenario; K2 | design |
| X4-14 | Everything bad everywhere | content scenario; exercises group row | design |
| X4-15 | A scheduled release | content scenario; S10 | design |
| X4-16 | The release the calendar missed | content scenario; SQS floor | design |
| X4-17 | News beyond the currency map | content scenario; I4 tags | design |
| X4-18 | The window swallows the day | content scenario | design |
| X4-19 | Post-event cost tail | content scenario | design |
| X4-20 | Exits never blocked | core V1 property test | design |
| X4-21 | Window on a correlated group | content scenario | design |
| X4-22 | The hand-over hour | content scenario; R5, I2 | design |
| X4-23 | Netting refusal | content scenario; S18 setting | BUILT R22 |
| X4-24 | Crypto weekend | content scenario | design |
| X4-25 | Weekend gap through the stop | content scenario; fork F5 test | design |
| X4-26 | Rollover minute | content scenario | design |
| X4-27 | Holidays | content scenario | design |
| X4-28 | DST | content scenario; I4 clock | design |
| X4-29 | Day-boundary exploit | content scenario; R5 | design |
| X4-30 | World switch resets | content scenario; I9 | design |
| X4-31 | Flash crash | content scenario; fork F5 test | design |
| X4-32 | Spreads widen everywhere | content scenario; fork F3 test | design |
| X4-33 | Halts | content scenario (stock route) | design |
| X4-34 | Limit moves | content scenario (futures route) | design |
| X4-35 | Black swan | content scenario; kill BLACK | design |
| X4-36 | Liquidity hole | content scenario; protection escalation | design |
| X4-37 | Aftershock | content scenario | design |
| X4-38 | Live slippage twice demo | content scenario; I2, K4 | design |
| X4-39 | Broker changes costs | content scenario; fork F2 test | design |
| X4-40 | Behaviour gap | content scenario; K4 | design |
| X4-41 | Minimum lot | content scenario; D5 | design |
| X4-42 | Wrong conversion | content scenario; I3 USD seam | design |
| X4-43 | Partial fills, duplicates | content scenario; R7 | design |
| X4-44 | Carry shocks | content scenario | design |
| X4-45 | Link down | content scenario | design |
| X4-46 | Stale feed | content scenario; S10 unknown | design |
| X4-47 | Wrong clock | content scenario | design |
| X4-48 | Restart and crash loop | content scenario; fork F4 test | design |
| X4-49 | Split brain | content scenario; node lease flag | design |
| X4-50 | Disk full | content scenario; V11 | design |
| X4-51 | Spec change | content scenario; I3 producer | design |
| X4-52 | Hyperliquid | content scenario (crypto rows) | design |
| X4-53 | Unit bug | content scenario; I15 clamps | design |
| X4-54 | Runaway unit | content scenario; I15 order rate | design |
| X4-55 | Upgrade mid-day | content scenario; fork F4 test | design |
| X4-56 | Blank number refused | content scenario; S13 | design |
| X4-57 | Agent proposes wrong | content scenario; K2 | design |
| X4-58 | Fake news | content scenario; I8 | design |
| X4-59 | Two controls disagree | content scenario; S5 rank | design |
| X4-60 | Slow decay | content scenario; fork F2 test | design |
| X4-61 | Regime against placement | content scenario | design |
| X4-62 | A losing streak with a real edge | content scenario | design |
| X4-63 | A winning streak | content scenario; raise gate | design |
| X4-64 | ORB family crowding | content scenario; I9 | design |
| X4-65 | The 2007 unwind | content scenario | design |
| X4-66 | Overfit card | content scenario | design |
| X4-67 | Leverage cut | content scenario; I3 | design |
| X4-68 | Margin close-out | content scenario; I15 | design |
| X4-69 | Seed near the floor | content scenario | design |
| X4-70 | Cushion after a big win | content scenario; R5 | design |
| X4-71 | Restart after a budget hit | content scenario; restore | design |
| X4-72 | Sweep re-derives anchors | content scenario; R5 | design |
| X4-73 | Deposit keeps verdicts | content scenario | design |
| X4-74 | Operator away | content scenario; absence policy config | design |
| X4-75 | Operator error | content scenario; V4 effect card | design |
| X4-76 | Panic and early resume | content scenario | design |
| X4-77 | Unreachable with a page | content scenario; UI | design |
| X4-78 | Rolls | content scenario (futures rows) | design |
| X4-79 | EIA | content scenario (energy calendar) | design |
| X4-80 | Liquidation cascade | content scenario (crypto rows) | design |
| X4-81 | Single stocks | content scenario (stock route) | design |
| X4-82 | Release while the feed is stale | content scenario | design |
| X4-83 | Crash while down | content scenario; reconcile | design |
| X4-84 | Decay and cost drift apart | content scenario; I2 two residuals | design |
| X4-85 | Isolation while away | content scenario | design |
| X4-86 | Bug with accelerators | content scenario | design |
| X4-87 | Correlation spike plus leverage cut | content scenario; de-gross verb | design |
| X4-88 | Seed near the floor in a normal run | content scenario | design |
| X4-89 | The energy triple | content scenario | design |
| X4-90 | The harness (light form) | core S15 replay path; harness jobs content | design |
| X4-91 | The event window | content on R5 | PROPOSAL |
| X4-92 | Per-driver caps sized to a tail gap | content; core I9 driver tags | design |
| X4-93 | Effective units on screen | other: UI | design |
| X4-94 | Isolation lifecycle | core S10 fields | design |
| X4-95 | Driver tags | core I4 | REAL |
| X4-96 | Scenario as data | content kind (on S15) | design |
| X4-97 | Scorecard with survival gates | content report; no gate | design |
| X4-98 | Reverse stress | content | author |
| X4-99 | Agent-based bench | other: methodology | simulation |
| X5-H01 | Novelty check and search ledger | other: methodology; core R12 | REAL finding |
| X5-H02 | Look-ahead block in tools | core I7 `knows_at`; other: methodology | REAL |
| X5-H03 | Gate: low end positive after costs | content; other: methodology | solid |
| X5-H04 | Band from four shrinkages | other: methodology; band on R12 | simulation |
| X5-H05 | Honest counts | other: methodology | design |
| X5-H06 | Plan priced in trades; too-thin verdict | other: methodology | arithmetic |
| X5-H07 | Challenger | other: methodology | controlled (blind check) |
| X5-H08 | Event replays and the dry chassis | core K4 | design |
| X5-H09 | Machine check against the twin in a week | core K4 | practice |
| X5-H10 | Bound click | core V4 | REAL (Terraform) |
| X5-H11 | Two vetoes | content pod | author |
| X5-H12 | Funded e-meter for raises | content block | simulation |
| X5-H13 | Evidence bar under the baseline | dropped: makes a weak unit a sitting duck (REVIEW M2 kept) | MODEL |
| X5-H14 | Cohorts set the speed | content | medicine |
| X5-H15 | Three speeds | core S4 states; rules content | maths |
| X5-H16 | One alarm budget | content; K6 place | theory |
| X5-H17 | Paid restarts, variance cap | content | proofs |
| X5-H18 | Cone in the current regime | content | simulation |
| X5-H19 | Fire density as display | content | MODEL |
| X5-H20 | Test of the tests | other: methodology | strong method |
| X5-H21 | Paper twin and shadow lane | core K4 | design |
| X5-H22 | Too good checks | content | prop |
| X5-H23 | Family-level decay | content; core I9 | plausible |
| X5-H24 | Three zones display | content | regulatory |
| X5-H25 | Error-budget burn | content | SRE |
| X5-H26 | Demotion with a cause code; re-promotion by click | core R4 cause codes; V4 | design |
| X5-H27 | Rehab and lineage | other: methodology; core R12 | PROPOSAL |
| X5-H28 | World switch resets; contract-level replay | core I9 | design |
| X5-H29 | Exit change as a counted trial | core R8 | controlled test |
| X5-H30 | Narrators | other: agentic | PROPOSAL |
| X5-H31 | Cut-only proposals | core I8 | design |
| X5-H32 | Protected core | core K5 protected list | design |
| X5-H33 | Audit and red team | other: agentic | attack papers |
| X5-H34 | Staking | content, wild | GUESS |
| X5-H35 | Governed pipeline | other: methodology | sobering |
| X5-H36 | Contrast test, new against old | core K4 | simulation |
| X5-H37 | Evidence ledger with stage tags | core R2 stage | design |
| X5-H38 | One cost ledger from node rows | core I2 | design |
| X5-H39 | Passport strip | other: UI; R9 | design |
| X5-H40 | Verification template per type is the preset | content preset; core type tag | RULING (A5) |
| X5-H41 | Node emits verification state; guard reads it | core R9 state input | design |
| X5-H42 | Thresholds by simulation on own record | content | plausible |
| X5-H43 | Calendar looks for rare traders | content | regulatory |
| X5-H44 | Edge decides gate and level, never amount | content; parked: numbers | PROPOSAL |
| X5-H45 | Certified capacity | other: methodology | model |
| X5-H46 | Canary across markets | core rollout field | practice |
| X5-H47 | Windows as counted slices | core R16 | idea |
| X5-H48 | Exploration budget | parked: numbers; content pod | idea |
| X6-01 | One fold, many readers | core R9 | Gen 3 |
| X6-02 | Equity triple and drawdown by kind | core R9 | design |
| X6-03 | Decision trail | core R1 | practice |
| X6-04 | Trade row v2 | core R2 | BUILT fields |
| X6-05 | Two ledgers | core R2, R5 | MODEL |
| X6-06 | Closed reason codes at source | core R4 | bug verified |
| X6-07 | Meters for the core brakes | content | design |
| X6-08 | Motion receipts | core R11 | design |
| X6-09 | Requested, enforced, observed | core R15 | Gen 3 |
| X6-10 | Context tags on every fire | core R4 fire tags | design |
| X6-11 | Six words and UNKNOWN | core R9 predicates; other: UI | practice |
| X6-12 | Decision pulse | content | design |
| X6-13 | Safety display | other: UI | design |
| X6-14 | Four tiers | other: UI; core R10 | SRE |
| X6-15 | Burn tiers | content | SRE |
| X6-16 | One incident, one page | core R10 | SRE |
| X6-17 | Wake contract | other: UI | SRE |
| X6-18 | Distance bars | other: UI | design |
| X6-19 | Watch windows | other: UI | design |
| X6-20 | Exit capacity | content (R9 reserved field) | SPAN |
| X6-21 | Brake scorecard | content | counterfactual |
| X6-22 | Trip tax, sitting-duck meter | content | MODEL |
| X6-23 | Accelerator earned-keep | content | MODEL |
| X6-24 | Growth waterfall | other: UI | design |
| X6-25 | Family alarm budget | content; K6 place | proofs |
| X6-26 | Attention telemetry | dropped: low value; UI if wanted | GUESS |
| X6-27 | Passport strip | other: UI | design |
| X6-28 | Drift decomposition | other: UI | design |
| X6-29 | Bad-day sentence | content (agentic words) | PROPOSAL |
| X6-30 | Cost cells | core I2 | author |
| X6-31 | Markout | core R7 | REAL live orders |
| X6-32 | Shadow first | core S5 | design |
| X6-33 | Exposure board | core R9 | design |
| X6-34 | Chorus detector | content | spec |
| X6-35 | Stress gauge | other: UI | SPAN |
| X6-36 | Incident bundle | core R10; narrator other: agentic | design |
| X6-37 | Fact flow and authority | core R15 | design |
| X6-38 | Read tools for agents | core K2 | design |
| X6-39 | Lab parity | core S15 | design |
| X6-40 | Observability observes itself | content; V11 | REAL (Knight) |
| X6-41 | Ledger generates alerts | content | design |
| X6-42 | Get-even flag | content | REAL traders |
| X6-43 | Morning card | content; other: UI | design |
| X6-44 | Vital-signs strip | dropped: low value | GUESS |
| X6-45 | Status page | other: UI | design |
| X6-46 | Observability budget | dropped: low value | GUESS |
| X6-47 | Sound map | dropped: low value | GUESS |
| X7-H01 | Three-surface door | core K2 | BUILT door |
| X7-H02 | Direction on every operation | other: agentic | controlled test |
| X7-H03 | Evidence as a fact the unit's rule reads | core I8 | design |
| X7-H04 | Effect-bound card | core V4 | controlled tests |
| X7-H05 | Two-speed authority; pre-authorised restore ladder | core S5 restore; default | design |
| X7-H06 | Spec, status, suggestions | core I9 | practice |
| X7-H07 | Feasible-by-construction proposals | core R9 read | author backtest |
| X7-H08 | LLM-free fast loop | core V3 | RULING |
| X7-H09 | One search ledger | other: methodology | REAL finding |
| X7-H10 | Testing wealth | content, wild | GUESS |
| X7-H11 | Random de-risker per agent | other: agentic | strong design |
| X7-H12 | Sealed scenarios | content | simulation |
| X7-H13 | Rationale-blind admission | other: methodology | controlled |
| X7-H14 | Point-in-time inputs | core I7 | design |
| X7-H15 | Attention budget | other: agentic, UI | plausible |
| X7-H16 | Graduation | other: agentic | design |
| X7-H17 | One incident, one card | core R10 | SRE |
| X7-H18 | Autonomy ladder | other: agentic | one live case |
| X7-H19 | Get-even guard | content | REAL traders |
| X7-H20 | Money both ways cards | other: agentic | design |
| X7-H21 | Slow isolation by card | content; K2 | RULING (C27) |
| X7-H22 | Drift explainer | other: agentic | PROPOSAL |
| X7-H23 | Adversarial scenario author | content | simulation |
| X7-H24 | Tuning proposer under the applier | content (Lab job) | RULING (M49) |
| X7-H25 | Cost-window prospector | content | author |
| X7-H26 | Structure labeller | content | PROPOSAL |
| X7-H27 | Journal coroner | other: agentic | PROPOSAL |
| X7-H28 | Template version drafter | other: agentic | solid |
| X7-H29 | Promotion pack with bound capability | core V4 | design |
| X7-H30 | Preflight | core S19 | BUILT A to G |
| X7-H31 | Decay watch: the script decides | content (E5 fold replaces the rule) | MODEL |
| X7-H32 | Sitting-duck advocate | content | fits M50 |
| X7-H33 | Accelerator scout | content | PROPOSAL |
| X7-H34 | Breadth proposer | content | PROPOSAL |
| X7-H35 | Slot rebalancer | content pod | PROPOSAL |
| X7-H36 | Risk mini app | content; doors other: agentic | shape solid |
| X7-H37 | Lab as a tenant | other: UI; S15 | designed |
| X7-H38 | Shepherd-ready call contract | other: agentic | early alpha |
| X7-H39 | Evidence contracts per kind | other: agentic | simulation |
| X7-H40 | Prediction market | content, wild | GUESS |
| X7-H41 | Ghost tracks | content, wild | GUESS |
| X7-H42 | Self-proposing ledger | content, wild | GUESS |
| X7-H43 | One-tap kill escalation card | core `on_fire` card; other: UI | design |
| X7-H44 | Self-evolution | other: agentic | two cycles |
| X7-H45 | Per-class agents | content | PROPOSAL |
| X7-H46 | Agent-written glance | other: agentic | design |
| X7-H47 | Provenance walker | content on R1 | old rule |
| X7-H48 | Non-FX event mapping | content | PROPOSAL |
| X7-H49 | Agent-trader units | reserved type name; other: agentic | RULING (D44) |

## Counts

| Source | Rows (measured by script) | Of which core (names a section 3 row) | Default block or template | Content | Other session | Parked | Dropped |
|---|---|---|---|---|---|---|---|
| H1 | 74 | 24 | 2 | 40 | 7 | 0 | 1 (as default) |
| H2 | 140 | 48 | 10 | 67 | 11 | 0 | 4 (as defaults) |
| H3 | 77 | 52 | 1 | 17 | 4 | 0 | 3 |
| H4 | 169 | 25 | 1 | 92 | 43 | 1 | 7 |
| H5 | 75 | 29 | 2 | 31 | 8 | 0 | 5 (as defaults) |
| E1 | 107 (Appendix A grouped in 6 rows) | 42 | 4 | 50 | 5 | 1 | 0 |
| E2 | 82 (must-carry grouped in 1 row) | 40 | 5 | 27 | 10 | 0 | 0 |
| E3 | 44 | 7 | 0 | 22 | 13 | 2 | 0 |
| E4 | 117 (seeds grouped in 10 rows) | 38 | 1 | 60 | 12 | 2 | 0 |
| E5 | 101 (must-carry grouped in 1 row) | 50 | 8 | 20 | 20 | 1 | 3 (as live rules) |
| X0 to X7 | 510 | 205 | 24 | 220 | 44 | 4 | 8 |

The Rows column is counted by script over the tables above (1,496 rows in all). The fate columns are counted by hand and approximate to a few rows; a row that names a core seat and also ships a default is counted once, under core. "Dropped" means dropped as a default or a law, with the idea kept as a labelled trap or an optional block; outright drops are X1-H69, X1-H71, X5-H13, X6-26, X6-44, X6-46, X6-47, UB-07, UB-14, UB-22, UB-33, UB-56, UB-60, UB-61, H5-23g, X2-H40 (as law) and E5's three live-climb rules.
