# The playing field: questions around the unit

Written 2026-10-30 by the playing-field agent (planning run step 2, expansion). This file widens the field. It answers nothing and designs nothing. A later step converges.

## How to read this

**What fed it.** The operator's verbatim transcripts, `STATE.md`, `seeds.md` and grounding files 16 to 19, worked through two skills in this workspace:
- `party-transcript.md`: `bmad-party-mode` in session mode, non-interactive, 11 rounds (P1 to P11).
- `.memlog.md`: `bmad-brainstorming` headless, 18 techniques, 150 ideas (B001 to B150). Its artifacts are `brainstorm-intent.md` and `brainstorm.html`.

**Tags on each question.**
- `research`: facts, or academic or vendor evidence, would settle it.
- `operator`: his intent, his money, vocabulary he cares about, or scope that can't be undone.
- `lead`: a technical call the lead can settle.
- `fog`: in scope, but it can't be phrased sharply yet.

**Short source names.**

| Short | Means |
| --- | --- |
| T1:n | `operator/transcript-2026-10-20-to-28.md`, line n holds the whole turn (the R17 convention) |
| T2:n | `operator/transcript-2026-10-29-to-30.md`, same convention |
| ST | `STATE.md` (section named, or line) |
| SE | `seeds.md` (section named) |
| R16 to R19 | `research/16` to `research/19`, section given |
| R17 Xnn | a row id in research/17's ledger (U, M, Q, L, J, I, A, R, N, T, UI, P) |
| P1 to P11 | the party round where the question surfaced |
| B001 to B150 | the brainstorm entry where it surfaced |

Every question names the seed or file it came from. Where a question came out of the party or the brainstorm, the seed it grew from is still named.

---

## 1. The lenses

Twenty lenses. The first eleven come from the lens list in `2026-10-28-discussion-notes.md` as research 16 §5 restated it, plus research 16's three missing lenses. The rest came out of this run or out of the 29 and 30 Oct round in STATE.

| Lens | Name | Where it came from |
| --- | --- | --- |
| L01 | The unit: what it is | STATE 10-29/30 "code first"; R17 §1; party P1. New as its own lens |
| L02 | System 1, System 2 and expansion | STATE 10-28 round, Path A (ST:120); R16 §2, §4 |
| L03 | Market intelligence by style, timeframe and data | R16 §5 lens 5; ST:119 seed |
| L04 | Context, QML and the dictionary | STATE corrections 3; T2:216 "QML is next"; R16 §3. Split out in this run |
| L05 | Terrain: instruments, brokers, execution | R16 §5 lens 9 |
| L06 | The book: pod, guard, correlation, shared capital | R16 §5 lens 10 |
| L07 | Risk and sizing as a socket | R16 §5 lens 6, narrowed by "code first, numbers later" (ST:116) |
| L08 | QMB, testing and judging | R16 §5 lens 2; ST QMB sections |
| L09 | Journals, data collection and the Library | R16 §5 lens 4 |
| L10 | Sources, lineage and the family tree | R16 §5 lens 1 |
| L11 | QMX agents and workflows as analysts | R16 §5 lens 7; ST:118 |
| L12 | How agents prove their analysis | ST:118; T2:382. New as its own lens |
| L13 | The journey before a trade, and before live | T2:216 seed; R17 U49. New |
| L14 | The trading node, operations and failure | R16 §5 lens 11 |
| L15 | Time and cadence | T2:132 human rhythms; T2:322 "24/7"; party P7. New |
| L16 | Stack and speed | T2:52; T1:1177 router speed. New |
| L17 | The operator as user, the UI and explanations | R16 §5 lens 8 |
| L18 | What makes QMX unique: two theories of the edge | T2:6; T2:132. New |
| L19 | Words with two meanings | R17 C23; R18 §9; brainstorm B107 to B114. New |
| L20 | Old-system memory and principles | R19 whole file. New |

---

## 2. Questions by lens

### L01. The unit: what it is

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L01-01 | What exactly sits inside a unit when there are "no separations", and which parts are frozen and which calibrate themselves? | fog | ST:21; T1:1211; R17 U09, U13 | P1, B002 |
| L01-02 | What does "self-configure" read (own journal, account, pod, market journal), and what does it change? | research | T1:1573; T2:216; R17 U15 | P1, B004 |
| L01-03 | Is "malleable" one unit that changes style, or one template that makes separate scalper, intraday and swing units? | operator | T2:132; R17 U17 | P1, B003 |
| L01-04 | What are "multiple experiences that a unit can provide"? | operator | T2:6 | P1 |
| L01-05 | Is a unit's timeframe part of its logic or a coordinate outside it? (also C3) | lead | R17 C3; R16 §2 | B003 |
| L01-06 | Is a unit's session profile its own field, or something the MIS supplies? | fog | R17 U05; SE "Sniping" | B020 |
| L01-07 | Can one unit hold several logics ("hybrids, tribrids, quadbrids"), and what keeps it one unit? | lead | T1:264; R18 §9 row 4 | B005 |
| L01-08 | Does a plain-Python unit or an ML model get every right a QML unit gets (journal, placement, promotion)? | lead | ST:47; T1:1573 | B006 |
| L01-09 | What is the smallest declaration a unit must carry before QMX can test, place or watch it? | lead | R16 §6; ST:21 | B001 |
| L01-10 | Where does a unit's identity live: its code, its spec or its behaviour? | lead | T1:1121 (07a agent report); R16 §2 | B007 |
| L01-11 | What does a unit need from QMX that it cannot compute itself, given it must stand alone? | lead | ST:64; standing order 10 | B010 |
| L01-12 | Which states can a unit be in (draft, tested, paper, live, paused on one market, stopped by a risk rule, retired), and which changes happen without him? | operator | ST:39; R19 §5 old breaker | B009 |
| L01-13 | Does a unit carry its own stop rules (daily loss, max loss) or only obey central guards? | fog | T2:216; R18 §5; R17 C20 | P5, B036 |
| L01-14 | What travels with a unit from the PC to the node: state, journal, warmed indicators? | lead | SE "Trading node"; ST DEC-0261 conflict | B008 |
| L01-15 | Is "the unit itself is the end" about the product or about the design boundary? | fog | R17 U09 | P1 |
| L01-16 | Does a unit's trading style pick its risk system, as on 8 Oct ("one risk system per trading style")? | fog | R17 §1.1; T2:132 | P1 |

### L02. System 1, System 2 and expansion

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L02-01 | What must exist before a System 1 unit exists: a context claim, a tested universe, a pooled record? | fog | T1:1999 "the definition of system one is lacking"; R16 §2 | P2 |
| L02-02 | What is the paper trail that earns a System 2: on which account, how long, read by whom? | research | T2:216; ST:120; R17 U38 | P2, B011 to B014 |
| L02-03 | Is the market a System 2 is earned on chosen before or after its trail is read? | research | T2:216; R16 §1.3 | P2, B011 |
| L02-04 | How does a System 2 notice its market changed after it was earned, and what happens to it then? | research | T2:216; R17 U42 | P2, B016, B050 |
| L02-05 | Does a System 2 trade beside its System 1 parent on that market, replace it there, or only change size? | operator | T2:132; T1:1903 | P2 |
| L02-06 | If System 2 is "the end goal of QMX", what does QMX do on day one, when no System 2 exists? | operator | T2:132 | P2, B099 |
| L02-07 | Does the pre-live variant step (instrument × timeframe × window) survive the 28 Oct shift? | operator | T1:1999; R17 I06, I11 | P2 |
| L02-08 | What triggers bounded (development) expansion, and what triggers live expansion? | fog | R17 I10; ST:109 | P2 |
| L02-09 | Is a "wins broadly" test still needed if a System 2 comes only from its own trail? | research | R17 U34 to U36; T1:2051 | P2 |
| L02-10 | Does a source that says "I trade this on gold" enter as a System 2 seed, or as a System 1 after its logic is extracted? | lead | T1:2051; R17 I12 | P2 |
| L02-11 | Does every logic change make a new System 1, and what counts as a logic change? | lead | T1:2051; R16 §2 | B015, B017 |
| L02-12 | Can System 2s from different parents combine into a new System 1? | research | T1:2051; R17 U30 | - |
| L02-13 | Is a sniping window a System 2 specialisation, a session profile, or its own axis? | fog | T2:132; SE "Sniping" | B020 |
| L02-14 | How does "no rush to trade" become a rule a workflow can follow: wait for what? | lead | T2:216 | P2, B149 |
| L02-15 | What happens to System 2 children when their parent gets a new logic version? | lead | R17 U30 | B017 |
| L02-16 | Can two System 2s on correlated markets be earned from what is really one trail? | research | R16 §1.2 break 3 | B018 |
| L02-17 | Is System 2 more a sizing idea (size up where proven) than a placement idea? | fog | T2:132 "amplification is now more specific" | B123 |
| L02-18 | Does a System 2 get its own exam baseline, or inherit its parent's? | lead | R17 U06 | B019 |
| L02-19 | What happens to a System 2 when its venue delists the market? | lead | R17 T14; party P2 | B061 |

### L03. Market intelligence by style, timeframe and data

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L03-01 | What is the MIS's output: labels, scores, ranked lists, raw features, or "a pool"? | fog | T2:132 "The output is in a pool"; R17 M15 | P3, B021, B029 |
| L03-02 | Is the MIS organised by style, then timeframe, then the data a market offers, or in another order? | research | ST:119; T2:216 | P3, B021 |
| L03-03 | Which market states can be read fast enough at 1m to help a scalper's trades, and which only as a session or daily list? | research | R16 §1.2; R17 C9 | P3, B022 |
| L03-04 | Do order-flow and depth measures show mean reversion faster than price-only measures, on venues that have them? | research | T2:132; party P3 | P3, B023 |
| L03-05 | What stands in for volume and order flow on spot FX, which has no tape and no true volume? | research | T2:216; R17 T11 | P3, B027 |
| L03-06 | One shared state vocabulary with sensors per asset class, or a separate MIS per asset class? | research | T2:216; R17 M20, M21, C19 | P3 |
| L03-07 | Should a scalper's MIS hold only indicators, and slower styles hold models? | research | T2:216 | P3 |
| L03-08 | Who trains MIS models, how often, on whose data, and where do they run? | research | T1:1573; R17 M33 | B026 |
| L03-09 | When a unit uses the same indicator as the MIS, is that double counting, or does it make the unit "already specific"? | research | T2:216 | P3, B041 |
| L03-10 | When a new context term appears, who builds its sensor and who approves it? | operator | T1:1951; R17 M17 | B067 |
| L03-11 | Does the MIS add noise to an already noisy market, and how would anyone measure that? | research | T1:264 | P3, B141 |
| L03-12 | How does the MIS version its labels so a retrain never rewrites old trades? | lead | R16 §1.3 | B042, B060 |
| L03-13 | Does the MIS only describe markets and leave ranking to units, or rank markets for each unit? | fog | T1:1951; R17 M14, M26 | P3 |
| L03-14 | Can he or the copilot overrule MIS labels by hand ("you trade oil") and retrain from that? | operator | T2:216 | P10, B147 |
| L03-15 | Do fundamentals enter the MIS through an agent workflow with proof, and when? | research | SE "Fundamentals"; T1:376 | - |
| L03-16 | Can the MIS "grow its own limbs": new templates per market type made by workflows? | lead | T2:132 | - |
| L03-17 | Where does the MIS run: inside each unit, the feed keeper, the node, the PC, or one central place? (also C5) | lead | R17 C5; ST:69 | B021 |
| L03-18 | How fresh must MIS output be for each style, and who judges when it is stale? | lead | party P3; R16 §1.4 | P3 |
| L03-19 | Are market-physics measures (Hurst, variance ratio, efficiency ratio) MIS features or their own family? | research | T2:216; R17 M35 | P3 |
| L03-20 | Do markets behave alike in the same session enough for an almanac, and is that honest or look-ahead? | research | R17 T17, M28; T2:322 | B093 |
| L03-21 | Does publishing MIS labels change how his units trade enough to spoil the labels? | research | R17 M15 | B146 |
| L03-22 | Which MIS cells are impossible because the data does not exist on the chosen venues? | research | R17 T11; R18 §8 | B027 |
| L03-23 | What is the cheapest MIS that still answers "find mean reverting markets at that time"? | lead | T2:132 | B030 |
| L03-24 | How does the MIS treat 24/7 markets that have no clock sessions? | lead | T2:322 | B033 |
| L03-25 | Is perps funding a market state on a clock, a terrain fact, or an event? | research | R16 §2; party P3 | B025 |

### L04. Context, QML and the dictionary

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L04-01 | Is market context in the dictionary the same thing the MIS measures? | fog | T1:1951 | P3 |
| L04-02 | What does the dictionary rebuild cover: audit, wider scope, numbered states, code, tests? | lead | T2:216; R19 §6 | P8 |
| L04-03 | One catalogue where context is a role, or a separate MIS catalogue? | research | R16 §7 point 7; R19 §6 | B145 |
| L04-04 | Which strategy pillars hold now? He recalls event, trigger, risk and sizing; the ruled baseline is location, context, trigger, confirmation. | research | T1:2051; R17 L09 | - |
| L04-05 | What does QML need in order to build units rather than strategies? | lead | ST:22; T1:1211 | P8 |
| L04-06 | What does QML's small door look like, and what complexity hides behind it? | lead | T1:1211 "deep modules" | P8 |
| L04-07 | How does QML stop cheaper models making big mistakes: hooks, checks, refusals? | lead | T1:1573 | B144 |
| L04-08 | Are exits blocks in QML, and where do the 57 exit entries go? | lead | R17 L14; R19 §6 | - |
| L04-09 | Is "the logic" about 60% of a unit, and what is the other 40%? | fog | T1:2051 | P1 |
| L04-10 | Scalper types: a finite list (about 7) or defaults that never cage? | research | T2:132; ST:43 | - |
| L04-11 | How are hybrids written down so they stay testable? | lead | T2:132; T1:264 | B005 |
| L04-12 | Does a 0 to 100 signal strength feed sizing? | lead | R17 L18 | - |
| L04-13 | How does plain Python leave QML without losing journals, lineage and the tries count? | lead | ST:47 | B140 |
| L04-14 | Which instrument classes must the dictionary cover before perps and futures work: funding, open interest, roll, index sessions? | research | R19 §6 | P8 |
| L04-15 | Does each context dimension need numbered values so every agent means the same thing? | lead | R16 §1.4 | P8 |

### L05. Terrain: instruments, brokers, execution

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L05-01 | Which slow-changing facts per broker, account and instrument does a unit need checked? | research | R16 §2; T2:216 | P4 |
| L05-02 | When a market fits but its spread is too high, what decides: SQS at trade time, a check at admission, the unit, or the router? | lead | T2:216 | P4 |
| L05-03 | Is SQS enough for terrain, or is terrain a separate check that can disagree with SQS? (also C38) | lead | R18 §5; R16 §1.2 | P4 |
| L05-04 | Which instrument kinds come first: cTrader FX and CFDs, indices, Hyperliquid perps, futures? | operator | T2:322; T2:132 | P4 |
| L05-05 | How do early CFD expiries and rolls reach a unit holding through them? | research | ST:141; T2:216 | P4, B046 |
| L05-06 | When does funding come into scope for perps units? | operator | T2:216 | P4 |
| L05-07 | At $300, which instruments can a unit size at safe risk at the minimum lot? | research | R16 §7 point 3; T2:132 | P4, B037 |
| L05-08 | Which venues give order flow, which need paid data, and which never will? | research | ST round-2 Q7; R18 §8 | B032 |
| L05-09 | Which platform doors are in the first build: cTrader, MT5, CCXT, Hyperliquid? | operator | T2:322; R18 §8 | - |
| L05-10 | How do two machines share one cTrader grant without one going blind on a token refresh? | lead | R17 N09 | P4, B047 |
| L05-11 | Does the market journal (broker × account × instrument × minute) become terrain's measured half? | lead | ST:58; ST:151 | P9 |
| L05-12 | How does a unit learn it is on a venue that rations order actions? | research | R17 T14 | - |

### L06. The book: pod, guard, correlation, shared capital

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L06-01 | Does the correlation control he remembers exist, and in which form? (also C4) | research | T2:322; R18 §5; R19 §4 | P5 |
| L06-02 | What should a correlation control measure: currency legs, return correlation, shared regime, dated by method and horizon? | research | R19 §4; R18 §5 | P5 |
| L06-03 | Where does correlation sit: in the router, as a reader of MIS output, in the BMS? | fog | T2:216 | P5 |
| L06-04 | What is the "ideal BMS", as opposed to today's? | operator | T2:216 | P5 |
| L06-05 | Combine the account guard and the pod, or keep them apart? | operator | ST:76; ST round-2 Q1 | P5 |
| L06-06 | How do twenty units on twenty "mean-reverting" markets avoid being one bet? | research | R16 §1.2 break 3; T2:216 | P5, B045 |
| L06-07 | When two of his units want opposite trades on one symbol, who wins? | lead | R19 §2 | P7, B044 |
| L06-08 | When units compete for one budget: first setup wins, or a ranking? | fog | R19 §2; T2:216 | P5 |
| L06-09 | Is portfolio optimisation a template or a fixed part? | lead | T2:6 | - |
| L06-10 | How does one budget stretch from two units to many without his manual work? | operator | T2:216 | P5, B084 |
| L06-11 | Is the book per account, per broker, or across every account? | fog | ST:77 | P5 |

### L07. Risk and sizing as a socket (numbers deferred)

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L07-01 | What is the socket's shape: what does a unit plug in now, and what does the risk session wire later? | lead | T2:132 "male and female connector"; ST:116 | P1 |
| L07-02 | Which inputs must the socket expose: journal statistics, equity, budget share, lot sizes from terrain? | lead | T2:216; R16 §6 | B037 |
| L07-03 | What runs when the socket is empty: a fixed default, the minimum lot, or no trading? | lead | ST:116 | B099 |
| L07-04 | Which stops belong to the unit and which are central: kill line, daily loss, account floor? | operator | R18 §5; R17 C20 | P5 |
| L07-05 | How is the old "radioactive" sizing replayed when judging? | research | ST:89; R19 §5 | - |
| L07-06 | House money per unit, per slot or per account? | operator | R19 §5; ST round-1 Q5 | - |
| L07-07 | How do variables "configure themselves" as units are added, without him? | fog | T2:216 | P5 |
| L07-08 | Where does "tighten, never loosen" sit, and when is it explained to him? | operator | ST "Owed to the operator" | - |

### L08. QMB, testing and judging

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L08-01 | Reshape QMB or rebuild it? | lead | T2:132; R17 Q12, Q13 | P8 |
| L08-02 | What is missing for a backtest that actually trades through the agent door? | lead | R18 §2; ST QMB door | P8 |
| L08-03 | Do results come in R, with the market state stamped on each trade? | lead | R16 §1.3; R18 §2 | P8 |
| L08-04 | Where are tries counted: at the data door, in QMB, in workflows? | lead | SE "Domain expansion"; R18 §2 | B140 |
| L08-05 | In what sequence do historical and paper judging run? | research | ST:88 | B012 |
| L08-06 | How do quant desks iterate a strategy without overfitting, and which habits fit agents? | research | T2:132; R17 Q22 | P8 |
| L08-07 | How does QMB test units on crypto trade prints when its reader takes quotes only? | lead | R18 §2 | - |
| L08-08 | What is the shortest window of QMX's own recorded data worth backtesting on? | research | T2:216 | P9 |
| L08-09 | How do the What-If scenarios improve? | research | T2:132 | - |
| L08-10 | Do the old pass numbers in R (200 trades, +0.15R, PBO bands) return as editable defaults? | lead | R17 Q07 | - |
| L08-11 | What can the judging skill check that an agent cannot edit? | lead | ST:90 | B074 |
| L08-12 | How is "it runs and waits. It doesn't have to tinker with the results" enforced? | lead | T2:132 | P8 |
| L08-13 | Does model memory of past markets matter for backtests of agent-built units while live analysis stays safe? | research | R17 Q21; T2:382 | P6 |
| L08-14 | Until costs are calibrated, what counts as evidence at all? | lead | ST GAP-0048; R18 §2 | B051, B130 |
| L08-15 | What data depth exists per instrument class for "no lookback cap"? | research | ST:46; ST:151 | B137 |
| L08-16 | How does QMB replay a unit's own risk and sizing rather than a Book? | lead | R18 §2; ST:21 | - |

### L09. Journals, data collection and the Library

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L09-01 | Which fields go in the unit journal, the market journal and a router journal, with no duplication? | lead | ST:55-59 | P9, B139 |
| L09-02 | How are signals not taken and missed trades recorded without a flood of rows? | lead | ST:57 | B150 |
| L09-03 | Ticks or bars on a PC with about 12 GB free? | operator | ST:151, ST:152, ST:184 | P9, B128 |
| L09-04 | Which instruments does QMX record live from day one? | operator | T2:216 | P9 |
| L09-05 | One journal kind written by QMB, paper and live, or several? | lead | R18 §6 | P9 |
| L09-06 | How are labels stamped at entry and never recomputed? | lead | R16 §1.3 | B042 |
| L09-07 | How is data quality checked for each feed? | research | ST:84 | - |
| L09-08 | Which "landmark" windows do agents get for analysis? | lead | T2:382 | P6, B079 |
| L09-09 | Which tables would agents want "stacked" for them? | fog | T2:322 | P9 |
| L09-10 | Do Dukascopy's terms allow the history QMX keeps? (also C30) | research | ST "For his awareness" | P4, B052 |
| L09-11 | Does everything fit the Library (router logs, journals, caches), and which kind is missing? | lead | ST:70; R18 §6 | P9 |

### L10. Sources, lineage and the family tree

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L10-01 | Does an idea record come before a unit, so lineage starts at the source? | lead | ST:149; R17 L19 | P9 |
| L10-02 | How is each source class tagged: video, article, chat, copilot chat? | lead | T1:1573; R19 §7 | B068 |
| L10-03 | How is "where winners come from" counted per source? | lead | ST:52 | - |
| L10-04 | How is the "genetic" move of one part across families recorded? | lead | R17 L20 | - |
| L10-05 | How does agent memory keep failures and conditions across runs? | lead | SE "Strategy funnel"; R17 I19 | B081 |
| L10-06 | Does the fail branch ("most strategies can work") count every context it tries? | research | T1:513; R16 §1.4 | P8 |
| L10-07 | What does the family tree show in preview and in detail? | operator | ST:53 | - |

### L11. QMX agents and workflows as analysts

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L11-01 | What does a market-analysis workflow produce, and what does a unit-analysis workflow produce? | fog | T2:382; ST:118 | P6 |
| L11-02 | Daily review of the day's data and charts: numbers, images, or both? | research | T2:322; R17 A09 | P6, B077 |
| L11-03 | How does a workflow find "why did this unit trade this"? | lead | T2:322 | P6 |
| L11-04 | An "organogram" of specialist agents: a workflow, a mini app, or both? | lead | T2:322 | B063 |
| L11-05 | Do agents shortlist markets before a session, and does the shortlist bind units? | fog | T2:322; R17 M34 | P6, B048 |
| L11-06 | Do agents propose ranges from performance instead of research numbers? (also C27) | fog | T2:322 | P2 |
| L11-07 | With trading 24/7, when do reviews run? | lead | T2:322; R17 A08 | P7 |
| L11-08 | How does the copilot explain what a workflow did? | lead | T2:322 | B072 |
| L11-09 | Which of the 46 templates map to which analyses, and which wait on missing doors? | lead | R18 §1.5 | B071 |
| L11-10 | Which events fire unit analysis: a trade closes, a session ends, a result lands? | lead | R18 §1.2 | B070 |
| L11-11 | Should agents get a toolset that reads the MIS? | lead | R18 §4 | B132 |
| L11-12 | What may agents write into a unit's journal? | lead | ST:56 | B064 |
| L11-13 | Is tagging units with pairs a job for an agent, a workflow, or him? | operator | T2:322 "you can consider tagging" | - |
| L11-14 | Do the old Cartographer and Coroner personas come back as templates? | lead | R19 §8 | B065, B066 |
| L11-15 | Do market-analysis workflows feed the MIS, or only check it? | fog | T2:322 | B063 |

### L12. How agents prove their analysis

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L12-01 | In which ways can agents be wrong about markets and units? | research | T2:382 | P6 |
| L12-02 | Which tool can't be cheated: deterministic scripts, sealed data, timestamped predictions? | research | T2:382 | P6, B073 |
| L12-03 | Did he mean non-deterministic or deterministic proof? (also C15) | operator | T2:382 | P6 |
| L12-04 | Who compares an agent shortlist against the MIS alone and against nothing? | fog | T2:382 "Who's comparing?" | P6 |
| L12-05 | "After which costs" for an agent run on a monthly subscription? | operator | T2:382 | P6, B078 |
| L12-06 | Do agent claims become records with typed evidence and a superseded link? | lead | R19 §8 | B082 |
| L12-07 | Are agent predictions scored later, the way a forecaster is? | research | R19 §8; party P6 | B073 |
| L12-08 | Do several models serve as review lenses, never as a vote? | lead | R19 §8 | B076 |
| L12-09 | Is live forward data enough to rule out training-memory look-ahead? | research | T2:382 | P6 |
| L12-10 | Who checks a script an agent wrote? | lead | T2:382 "can't be cheated" | B074 |
| L12-11 | Must every agent analysis say what it did not see? | lead | T2:382 "landmark" | B079 |

### L13. The journey before a trade, and before live

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L13-01 | Which steps run between a signal and an order? | fog | T2:216 | P7 |
| L13-02 | Which steps are local to the unit, which central, and which may be skipped when something is down? | lead | ST:64-65 | P7 |
| L13-03 | How much time may each step take for a 1m scalper? | research | party P7 | - |
| L13-04 | In what order do checks run, and who vetoes first? | lead | party P7; R19 §2 | - |
| L13-05 | Is every refusal logged with its reason? | lead | ST:57 | P9 |
| L13-06 | What happens before a unit's first trade on a new market (indicator warm-up)? | lead | ST DEC-0261 conflict | - |
| L13-07 | What is each gate on the pre-live journey: source, idea, QML, QMB, stress, paper, his click, live? | fog | SE "Strategy funnel"; ST:39 | - |
| L13-08 | What does a unit do when its MIS input is late? | lead | party P7 | B053 |

### L14. The trading node, operations and failure

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L14-01 | What does the trading node need beyond the never-deployed QMN code? | research | T2:436; R18 §7 | P7 |
| L14-02 | Which kill-switch levels fire without the PC? | operator | SE "Trading node"; R17 N05 | P7 |
| L14-03 | What happens when the router, MIS, feed, PC or broker is down, and who is told? | lead | R16 §5 lens 11 | P7, B053 to B056 |
| L14-04 | One router or several when there are several nodes? | lead | ST:69 | B102 |
| L14-05 | How does one feed pool serve 200+ units across brokers? | research | ST:66; ST:151 | B054 |
| L14-06 | How do the PC and the node take turns on one broker connection? | lead | ST:151 | B047 |
| L14-07 | Which self-tests run when a node connects? | lead | SE "Trading node" | - |
| L14-08 | After a crash, which record of open positions wins? | lead | brainstorm | B056 |
| L14-09 | How are clocks, time zones and daylight saving kept the same across machines? | lead | brainstorm | B057, B062 |
| L14-10 | What does a full disk or a feed gap do to trading? | lead | ST:151 | B059 |

### L15. Time and cadence

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L15-01 | What rhythm does each style need for MIS updates, reviews and recalibration? | research | T2:132 | P3, B038 |
| L15-02 | What clock replaces "5 trading days"? | lead | T1:1573; ST:153 | P7 |
| L15-03 | How do 24/7 instruments and session instruments live in one book? | lead | T2:322 | B033 |
| L15-04 | What sets when a unit recalibrates: per trade, nightly, after a count? | lead | R17 U15 | B004 |
| L15-05 | How long is "no rush" for a System 2? | research | T2:216 | P2 |

### L16. Stack and speed

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L16-01 | Is Python right for the live path, or only for some parts? | research | T2:52 | P8, B133 |
| L16-02 | How is router speed solved by caching, as in feed and recommendation systems? | lead | T1:1177 | B121 |
| L16-03 | Can labelers run the same code in QMB and live? | lead | R16 §6 | P8 |
| L16-04 | How does feed fan-out scale across processes and machines? | research | ST:151 | B054 |

### L17. The operator as user, the UI and explanations

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L17-01 | What does he see each morning? | operator | T2:6; R18 §1.5 | B100 |
| L17-02 | What exactly does his click admit: one market, a class, or whatever the unit's conditions allow? | operator | T1:1573; ST round-2 Q2 | P10 |
| L17-03 | How does he attach markets by hand, and is that counted as a try? | lead | T2:216 | P10, B147 |
| L17-04 | What must always be explainable in plain words: why it traded, why it didn't? | lead | T2:132; T2:322 | P10 |
| L17-05 | How does he know QMX is not trading on luck? | fog | T2:216 | P2 |
| L17-06 | What does he control that agents never do? | operator | T1:1573; ST:20 | B104 |
| L17-07 | What does he stop doing by hand as units grow? | operator | T2:216 | B103 |
| L17-08 | What would a unit have done last week on his account size, in dollars? | lead | party P10 | - |
| L17-09 | Who is the main user: agents, or him? (also C33) | operator | T1:1573; T2:216 | P10 |

### L18. What makes QMX unique: two theories of the edge

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L18-01 | What makes QMX unique against MT5 and against copilots? | operator | T2:6 | P1 |
| L18-02 | Is judging the product, placing the product, or both? | fog | ST:29; T2:132 | - |
| L18-03 | Grow $300 with one or two units, or compound across breadth: which comes first? (also C36) | operator | T2:132; SE "Breadth compounding" | P4, B091 to B094 |
| L18-04 | Does the system amplify a weak edge, as he says, and how would that be shown? | research | T2:132 | P1 |

### L19. Words with two meanings

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L19-01 | Router, MIS, load balancer, matcher, scanner, sentinel: one thing or several? | operator | R17 M01 to M14; T1:1211 | P10, B107 |
| L19-02 | Does "correlation ledger" keep the docs meaning (order lineage) or his (market correlation)? | operator | R18 §9 row 7 | P5, B108 |
| L19-03 | Does "system one" need a new name, given its September meaning? (also C23) | operator | R17 C23 | P2, B109 |
| L19-04 | Does "node" stay as the name for both the workflow server and the trading server? | lead | R18 §1.3, §7 | P7, B110 |
| L19-05 | Does "terrain" stay as a word? | operator | R16 §2 | P4 |
| L19-06 | "Sniping": a time window or an order-flow trigger? | lead | R17 M43 | B113 |
| L19-07 | Two "workflow"s: a QMX workflow and the planning run. How are they told apart in files? | lead | R17 A13 | B112 |
| L19-08 | What is a "family" in the family tree? | fog | ST:53; R17 I02 | P10 |

### L20. Old-system memory and principles

| ID | Question | Tag | Source | Surfaced |
| --- | --- | --- | --- | --- |
| L20-01 | Do April's Sharia rules (no leverage, swap-free, no futures) still bind? (also C34) | operator | R19 §5; R17 T04 | P4 |
| L20-02 | Compound between cycles, or reset to seed as the July Scalper Book did? (also C32) | operator | R19 §5 | P11 |
| L20-03 | Which of the 20 old ideas that no current file mentions come back? | lead | R19 closing list | P5 |
| L20-04 | Is WF4 "ecological + feature mutation" the same thing as domain expansion? | research | R19 §1 | - |
| L20-05 | Does an automatic breaker (LIVE to PAPER to RECOVERY to RETIRED) fit "only he promotes"? | operator | R19 §5; ST:39 | B009 |
| L20-06 | Does weekly pair selection "backed by a lot of evidence" come back? | research | R19 §2 | - |

---

## 3. Contradictions, as open questions

C1 to C23 are research 17's (§4), restated as questions with its citations. C24 to C38 are new in this run. None is resolved here.

| ID | The question | One side | Other side | Tag |
| --- | --- | --- | --- | --- |
| C1 | Do units read the MIS? | "Bots never read the MIS inside their rules" (SE) | "the unit itself accesses both market and MIS" (T1:1573); "units… pick the output" (T1:1951) | operator |
| C2 | Is the same logic on a new instrument a new unit? | "a new instrument, time frame broker makes a sibling unit" (T1:1573) | Lead 28 Oct "stays the same unit" (T1:1935); "system two is just a variant of system one" (T1:1999) | operator |
| C3 | Is a timeframe change a new unit? | 13 Oct "becomes a brand new strategy" (R17 C3) | 20 Oct "two different bots with the same bloody logic" accepted (T1:484); 29 Oct still unanswered (R17 C3) | lead |
| C4 | Does a market-correlation control exist? | "we have a correlation ledger… it's actually already there" (T1:442); "the correlation ledger exists" (T2:322) | Docs name = order lineage; only a draft template computes correlation (R18 §5) | research |
| C5 | Where does the MIS run? | "The trading node keeps only the MIS and the kill switch" (SE) | "not splitting" then "splitting… best fit" (T1:1573); "centralized… also the MIS" (T2:216) | lead |
| C6 | Do more variants mean more compounding? | "it expands the domain. So it means more variants" (T1:484) | "increasing numbers of strategies… doesn't seem so useful… if we are live trading" (T1:1999) | operator |
| C7 | Can anything reach live without his click? | "nothing actually ever enters live without me" (T1:1573) | Option (c) children "born at minimum size inside" an admitted class (R16 §4) | operator |
| C8 | QML: rebuild from scratch or upgrade in place? | "rebuild QML from scratch" (13 Oct, R17 C8) | "QML deserves an upgrade" (T1:1211); "the dictionary needs a rebuild" (T2:216) | lead |
| C9 | How fast can the MIS work for a scalper? | ~8 h to see a trend at 1m (R16 §1.2) | "they need data quickly… multiple indicators inside a scalper's MIS" (T2:216) | research |
| C10 | Does a new System 2 start with no history? | "starts from the parent's numbers" (lead via R16, T2:147) | "you are assuming as if this system two variant came from thin air" (T2:216) | operator |
| C11 | Where do trade-count thresholds come from? | "roughly 270 to 550… trades" (lead, T2:184) | "Where are you getting that number from?" (T2:216); "I don't trust the math" (T2:322) | research |
| C12 | News trading: in or out? | "for now, man, I don't intend to try news" (13 Oct) | "which means I can trade news" (T1:2051); news units vs the global news kill switch (ST:154) | operator |
| C13 | Live first, or backtesting first? | "the back testing system… might have to take a seat for now" (13 Oct) | QMB belongs to the unit work (ST:188); "QMB is obviously going to be readjusted" (T2:132) | operator |
| C14 | Solutions now, or broaden first? | "discovering issues without proposing solutions" (T2:216) | "I don't think we need solutions yet… first broaden" (T2:322) | operator |
| C15 | Proof tools: deterministic or non-deterministic? | "a skill… has hooks and deterministic scripts" (T1:1573) | "we need something that is non-deterministic… can't be cheated" (T2:382) | operator |
| C16 | Wayfinder: premature, important, or narrow? | "these questions are stupid… premature" (13 Oct) | "Wayfinder is very important" (T1:651); "very narrow" (T2:436) | lead |
| C17 | Scalpers first, or malleable from the start? | "design for scalpers first, then the rest can inherit" (13 Oct) | "a unit… should be malleable" (T2:132) | operator |
| C18 | Do instruments matter? | "I don't think future is going to use the same analysis system… as a currency" (T1:1999) | "instruments might not matter so much" (T2:216) | research |
| C19 | One MIS, or one per scalper type? | "a mean-reversion scalper and a volatility scalper might require a specific version… of the MIS" (13 Oct) | Lead "don't build one MIS per scalper type" (T2:176), answered "that's your opinion" (T2:216) | research |
| C20 | Does the unit alone size, or do central parts size? | "The unit alone controls its trading, risk and sizing" (ST:24) | "there should be some sort of centralized parts… like the BMS"; two bots share the 300 (T2:216) | operator |
| C21 | Who owns the unit idea? | "The unit was my idea" (T1:376) | The word was coined by Claude on 8 Oct (R17 §1.1) | operator |
| C22 | The pain floor: open or answered? | Listed open in decisions.md (R17 C22) | Rejected on 6 Oct, "percentage of what" (R17 C22) | research |
| C23 | "System one" means two things. | Sept: small trainable MIS models (R19 via R17 C23) | 28 Oct: a context-defined unit (T1:1951) | operator |
| C24 | Can a unit stand alone if System 1 live needs the MIS to know where to trade? | Units stand alone (standing order 10; ST:64) | "it should take in information from, let's say now, an MIS cluster" (T2:132); System 1 trades where the MIS finds its context (T1:1903) | fog |
| C25 | Does steering where money goes count as touching money? | "Agents never touch money" (ST:20) | Agents shortlist markets units then trade (T2:322) | operator |
| C26 | Self-configuring budget, or only his click? | "nothing actually ever enters live without me" (T1:1573) | "certain variables should be able to configure themselves… So that I don't have to come and manually do it" (T2:216) | operator |
| C27 | Where do default numbers come from? | Numbers "ship as editable defaults or templates" (ST:116) | "I don't trust the math because I never requested for it" and agents propose ranges instead (T2:322) | fog |
| C28 | Is the build serving System 2 or System 1? | "system two is the end goal of QMX" (T2:132) | "during live trading, system one is the one I want" (T1:1903) | operator |
| C29 | Do instruments matter if System 2 is instrument-specific? | "instruments might not matter so much" (T2:216) | System 2 = "market context and conditions plus specific instruments" (T1:1951), the end goal (T2:132) | fog |
| C30 | Can QMX stack the data it collects? | "QMX… should be collecting… live market data" (T2:216); "data stacking… is very important" (T2:322) | Dukascopy's site terms forbid bots and databases (ST "For his awareness") | research |
| C31 | Local first, or 24/7 trading with tick archives? | Everything works on his PC alone (ST:72-73) | "We are literally trading 24/7" (T2:322); 150-200 GB of ticks, about 12 GB free (ST:151, ST:152, ST:184) | operator |
| C32 | Compound, or reset between cycles? | Compounding is the founding idea (T1:264, the Hummingbird story) | July Scalper Book "may never compound between cycles" (R19 §5) | operator |
| C33 | Who is the user? | "Stop designing for humans, start looking at agents" (T1:1573) | "I'm not that technical. It means QMX is meant to be built to cater for this" (T2:216) | operator |
| C34 | Do the April Sharia rules still bind? | "NO LEVERAGE… swap-free… no futures" (R19 §5) | CFDs, perps and futures in scope (R17 T01); indices added (T2:132) | operator |
| C35 | Is the MIS a constant, or retrained and upgraded? | Aug: "MIS is like centrally used… it's a constant", no versions side by side (R19 §2) | "we can retrain a version of the MIS" (T2:216); agents upgrade it with approval (T1:1951) | lead |
| C36 | One or two units on $300, or a breadth scanner? | "300 can be grown by only one or two units" (T2:132) | "across 100… we have 20 possible opportunities" (T1:1903); breadth compounding (SE) | operator |
| C37 | Funding out of scope, perps in scope? | Funding "is a bit out of scope for now" (T2:216) | "I might also start with Hyperliquid, with perpetual features" (T2:322) | operator |
| C38 | Does SQS cover terrain? | "the SQS is going to fire and we don't thread. Is that it?" (T2:216) | SQS compares live spread with its own baseline, not with the unit's target (R18 §5; R16 §1.2) | lead |

---

## 4. Permutation cross-map

How questions combine, depend on each other, or conflict. "Same" means one question in different clothes. Read each row left to right.

| From | Relation | To | Why (INFERRED) |
| --- | --- | --- | --- |
| L08-03 labels on trades, results in R | enables | L02-02, L02-09, L03-03, L06-06, L12-07, L18-04 | Each needs per-trade state and R to be measurable at all |
| L03-12 MIS versions | enables | L09-06 stamp at entry | A stamp is only honest if the labeler has a version |
| L03-09 same indicator in unit and MIS | same | L04-03 one catalogue with roles; B041 | Both ask what the unit and the MIS share and who owns it |
| C24 stand alone vs System 1 needs MIS | conflicts with | L03-01 output form; L03-17 place; L01-11 | The output's form and place decide whether a unit can live without it |
| L01-02 self-configure | same | C26; L06-10; L07-07 | Four phrasings of who changes size when units are added |
| L02-03 market chosen before the trail is read | same | L11-05 agent shortlist; L12-04 who compares | Selection bias moves from backtest to journal to agent; one guard question three times |
| L05-02 spread too high | depends on | L05-03 SQS vs terrain; C38; L13-04 order of checks | Who decides depends on which check exists and which runs first |
| L05-07 the $300 universe | conflicts with | L18-03 two theories; C36; L02-06 day one | A $300 account and a hundred-market scanner pull the first build apart |
| L06-01 does correlation exist | depends on | C4; L19-02 the name; L20-03 revived old ideas | What he remembers may be the Intent Aggregator or the exposure ledger |
| L14-03 outage behaviour | same | L13-02 local steps; C24; B053 to B056 | Independence is one rule seen from ops and from the trade path |
| L09-03 ticks or bars | depends on | C31; L09-04 what to record; L03-04 order flow; L05-08 paid data | Order-flow MIS needs ticks; ticks need disk or paid feeds |
| L09-10 Dukascopy terms | conflicts with | C30; L08-15 data depth | The deepest free FX history may not be keepable |
| L11-02 numbers or images | depends on | L12-01 ways agents are wrong | Misreading a chart image is one of the failure modes |
| L11-06 agents propose ranges | conflicts with | C27; C11; L07 numbers deferred | Three sources of numbers, none agreed |
| L04-02 dictionary rebuild | depends on | L04-14 class coverage; L03-06 vocabulary vs per-class; L03-25 funding | The rebuild's scope is the MIS's vocabulary |
| L16-01 Python live | depends on | L16-03 same labeler code; L13-03 latency per step | A second runtime doubles the labeler unless it is shared |
| L17-02 what his click admits | same | C7; C26; L02-05 | All ask where his authority ends and automation starts |
| L01-03 malleable | depends on | C17; L03-02 MIS by style; L15-01 rhythm per style | If style changes, the MIS reading and the clocks change with it |
| L02-07 pre-live step survives | depends on | C6; L10-06 fail branch tries; L08-04 where tries are counted | Variant counts and tries counts are one budget |
| L20-01 Sharia rules | conflicts with | C34; L05-04 instrument kinds; L05-06 funding | Leverage and futures are the instruments now in scope |
| L20-02 compound or reset | same | C32; L18-03 | Both ask what the money is for between cycles |
| L03-14 hand-attached markets | depends on | L17-03 counted as try; L12 proof | A hand pick is evidence or bias depending on how it is counted |
| L11-11 agents read the MIS | depends on | L03-01 output form | A toolset needs a defined output |
| L14-01 the node | depends on | L19-04 name; C5 MIS location | Two "nodes" and an undecided MIS home |
| L08-13 model memory in backtests | same | L12-09 live forward data; R17 Q21 | Same worry split by backtest vs live |
| L07-01 socket shape | depends on | L01-01 inside a unit; C20; L06-04 ideal BMS | The socket's sides are the unit and the central parts |
| L02-04 market changed after earning | depends on | L15-05 how long is no rush; L08-08 shortest window | Earning and expiring share one clock |
| L13-01 steps before a trade | combines with | L06-07 opposite intents; L05-03 SQS; L14-02 kill levels | The journey is where the book, terrain and guards meet in order |
| L18-01 uniqueness | combines with | L18-02 judging vs placing; L01-04 experiences | What he is justifying to himself is these three together |
| L19-01 router vs MIS | same | C1; C5; L03-13 rank or describe | Half the router debate is a word problem |
| L10-01 idea record | enables | L10-03 where winners come from; L02-10 gold source entry | Lineage needs a record before the unit exists |

---

## 5. Parked

In scope, deferred by a ruling or by his own words. Parked is not dropped.

| Item | Why parked | Source |
| --- | --- | --- |
| Risk and sizing numbers: house money, Kelly ceiling, size growing back, the floor ratchet's maths | Own session from a hand-off; "code first, numbers later" | ST:93; ST:116; T2:216 |
| Funding modelling for perps | "a bit out of scope for now" (kept as C37 and L05-06) | T2:216 |
| Prop-firm accounts | Parked 5-8 Oct | R17 T15 |
| Swing units beyond "barely" | Horizons seed | SE "Horizons" |
| The shift to a spot-only system | Later aim | SE "Horizons"; R17 T04 |
| The MQL5 DeepSeek idea-mining run | No credits; use articles inside QMX later | ST:28 |
| Paid data (Databento, Tardis) | Only when a unit needs it | ST round-2 Q7 |
| News trading | Open (C12) | T1:2051 |
| UI screens beyond what this map names | UI is its own session | R17 UI07 |
| Portfolio optimisation numbers | Ship as templates or defaults | T2:6 |
| Pass marks and thresholds | Editable defaults later | ST:116 |
| Fable use | Only if he asks | ST:122 |
| The planning method's own order (wayfinder before or after expansion) | Process, settled for this run in STATE | ST "The planning run" |

---

## 6. Counts

Questions per lens, by tag. Contradictions are counted separately.

| Lens | Questions | research | operator | lead | fog |
| --- | --- | --- | --- | --- | --- |
| L01 The unit: what it is | 16 | 1 | 3 | 7 | 5 |
| L02 System 1, System 2 and expansion | 19 | 6 | 3 | 6 | 4 |
| L03 Market intelligence by style, timeframe and data | 25 | 15 | 2 | 6 | 2 |
| L04 Context, QML and the dictionary | 15 | 4 | 0 | 9 | 2 |
| L05 Terrain: instruments, brokers, execution | 12 | 5 | 3 | 4 | 0 |
| L06 The book: pod, guard, correlation, shared capital | 11 | 3 | 3 | 2 | 3 |
| L07 Risk and sizing as a socket | 8 | 1 | 3 | 3 | 1 |
| L08 QMB, testing and judging | 16 | 6 | 0 | 10 | 0 |
| L09 Journals, data collection and the Library | 11 | 2 | 2 | 6 | 1 |
| L10 Sources, lineage and the family tree | 7 | 1 | 1 | 5 | 0 |
| L11 QMX agents and workflows as analysts | 15 | 1 | 1 | 9 | 4 |
| L12 How agents prove their analysis | 11 | 4 | 2 | 4 | 1 |
| L13 The journey before a trade, and before live | 8 | 1 | 0 | 5 | 2 |
| L14 The trading node, operations and failure | 10 | 2 | 1 | 7 | 0 |
| L15 Time and cadence | 5 | 2 | 0 | 3 | 0 |
| L16 Stack and speed | 4 | 2 | 0 | 2 | 0 |
| L17 The operator as user, the UI and explanations | 9 | 0 | 5 | 3 | 1 |
| L18 What makes QMX unique: two theories of the edge | 4 | 1 | 2 | 0 | 1 |
| L19 Words with two meanings | 8 | 0 | 4 | 3 | 1 |
| L20 Old-system memory and principles | 6 | 2 | 3 | 1 | 0 |
| **All lenses** | **220** | **59** | **38** | **95** | **28** |
| Contradictions C1 to C38 | 38 | 7 | 22 | 6 | 3 |

Totals beyond the lens tables: 38 contradictions (23 from research 17, 15 new), 31 cross-map rows, 13 parked items, 150 brainstorm entries (B001 to B150, many folded into the questions above), 11 party rounds with 63 verbatim operator quotes checked against the transcripts.

---

## 7. How this was run, and what was not done

- **Party mode** ran in session mode as a non-interactive party, with its activation scripts run (`resolve_customization.py`, `resolve_config.py`, `resolve_party.py`). An inline cast keeps no memlog under the skill's own rule, so the party has a transcript and no memlog. Speaker tags are text, not emoji. Every operator line was checked verbatim against `T1` and `T2` by script (63 quotes, 0 missing).
- **Brainstorming** ran headless per `references/headless.md`: technique list from `brain.py list --all`, 18 techniques, a domain shift about every 10 ideas, memlog kept with `memlog.py` (176 entries, status complete).
- **Deviation:** the headless reference says to delegate the HTML and intent artifacts to subagents. The brief forbids subagents, so I wrote them myself from the memlog.
- **Deviation:** the brainstorming `on_complete` hook recommends `bmad-prd` next. This run's next step is the wayfinder chart (ST "The planning run"), so the hook's advice is recorded and not followed.
- **Not verified:** no code was run; facts about code come from research 18. Questions tagged `research` are unanswered by design.
