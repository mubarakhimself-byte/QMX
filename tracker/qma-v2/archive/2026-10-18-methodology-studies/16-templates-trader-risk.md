> STATUS 2026-10-16 (rubric walk): PARTLY-STALE. See 27-rubric-walk.md. Rulings in 26 win.

# 16 — Template catalogue: quant trader and risk quant

Written 2026-10-16 by an ideation agent. This is a draft for the operator to react to. Nothing in it is ratified.

Inputs:
- Files 01-14 in this folder. The ones read closely were 03, 06, 09, 11, 12 and 13.
- The clippings: Skydive research desk, BuildAlpha loop, BuildAlpha portfolio, the Hermes "scripts first" post, probabilistic thinking, and the two GPT-6 Astra posts. Only the role lists were taken from the Astra posts.

How the templates fit together:
- The engine has eight step kinds: `script`, `rule`, `model`, `agent`, `rlm`, `human`, `subflow` and `grader`. Their meaning is in 03 §9 and 12 (c).
- A template is a workflow folder with a parameter file. The trader or the copilot clones it into a variant (section 3).

Every template in this file obeys four hard lines:
1. **Agents read money. They never move it.** This is enforced by a hook, not by prompt text. No step in any template places, changes or closes an order, and no step uploads a unit to a live node.
2. **The account guard is read-only for every template.** The guard holds the kill line, the loss budget, correlation limits, the kill switch and the news filter. A template may read the guard and propose a change to it. Only the trader signs a change.
3. **Tighten-only.** A unit tunes itself through its own code recipe. Any workflow action on a unit can only tighten it: shrink, bench, or send it back to demo. Loosening is always a card the trader signs.
4. **No model, no problem.** Every trader and risk template has a script-only fallback that still delivers its numbers when the usage cap is closed or a model fails. The watchdogs never need a model.

The internals of a unit are still open (09). Templates therefore read a unit only through the **unit adapter** (section 4.1), which asks for named facts. They never read fixed fields.

---

## 1. Summary table

Mode legend (from 12 (a)):

| Mode | Meaning |
|---|---|
| **W** | A workflow runs alone. The copilot only shows the result. |
| **C** | The copilot alone. |
| **C+S** | The copilot plus sub-agents. |
| **C+W** | The copilot starts or edits a workflow. |

**Script-only** means a workflow with no model step at all.

Budget classes are defined in section 4.9: B0 = zero tokens, B4 = heavy.

| ID | Template | Lens | Mode | Trigger | Model use | Budget | Human point | Output, then what it feeds |
|---|---|---|---|---|---|---|---|---|
| T1 | Morning brief | Trader | W | Cron, weekdays, before his first session | 1 writer call. None on a quiet day. | B1 | Decisions with defaults | Dashboard card. Feeds T2 and his day plan. |
| T2 | Pre-session market read | Trader | W | Cron, 30 min before each session open | 1 cheap call, only when conditions changed | B1 | None | Session board (units × conditions). Feeds T1, T10 and the copilot. |
| T3 | News and macro calendar watch | Trader | W, script-first | Daily cron, plus event triggers before and after each release | Cheap note on a surprise only | B0-B1 | None | Calendar strip and alert lines. Feeds T1, T2, T7, R1, R5 and R8. |
| T4 | Research desk overnight | Trader | W | Cron, Sun-Thu 03:00 | Coordinator plus 6 analyst beats | B3 | Reads the brief | Ranked brief with "What I cut". Feeds T1, T2 and Lab hint cards. |
| T5 | Demo monitor | Trader | W | Monitor trigger: a closed deal, plus a heartbeat | Explainer only when out of band | B0-B1 | None (bench on demo is automatic) | Unit status tile and an evidence-ready event. Feeds T6 and R3. |
| T6 | Promotion evidence pack | Trader, risk | C+W | Event from T5, or manual | Writer, plus R7 as a subflow | B3 | **Signs promotion** | Scorecard and decision card. Feeds his click on the node. |
| T7 | Trade journal review in R | Trader | W weekly, C to discuss | Cron, Saturday | Analyst writes at most 3 lessons | B2 | Accepts or rejects each lesson | Explainer. Feeds lessons, Lab hints and R3. |
| T8 | Video to demo trial | Trader (Lab) | C+W | Manual drop in the copilot | Triage, extract, build, verdict | B4 | Fills spec holes; **signs the demo start** | Funnel scorecard. Feeds T5. |
| T9 | Execution quality check | Trader | W, script-only | Each closed deal, hourly, daily | None | B0 | None | Cost tiles and table. Feeds R3, R4 (cost model), T6 and R8. |
| T10 | End-of-day wrap | Trader | W | Cron, 17:05 New York (FX day roll) | 1 writer call. None on a quiet day. | B1 | None | Day card and digest. Feeds T1, T7 and R3. |
| R1 | Kill-line distance watchdog | Risk | W, script-only | Monitor: every 30 s with open risk, else every 5 min | None | B0 | None (push on red) | Cushion gauge and alerts. Feeds T1, T10 and R8. |
| R2 | Correlation and exposure drift | Risk | W | Position change, hourly, daily | Explainer only when a rule trips | B0-B1 | Signs any guard proposal | Heatmap and currency bars. Feeds R5, T6 and guard cards. |
| R3 | Strategy decay detection | Risk | W | Daily after T10, and every 10 trades | Explainer on amber or red | B1 | Bench or demote card | Red/amber/green list. Feeds the Lab rehab loop, R8 and T1. |
| R4 | Overfit audit of a candidate | Risk | W (subflow) | Event: the candidate reaches validate | Explainer only | B0-B1 (compute heavy) | None. **The gate is hard.** | Pass/fail scorecard. Feeds R7, T6 and negative results. |
| R5 | Stress tests | Risk | W | Weekly; also on a unit added, a promotion or a guard change | Explainer for the worst 3. Optional `rlm`. | B1-B3 | Signs proposals | Scenario heatmap. Feeds T6 and guard cards. |
| R6 | Tighten-only self-tuning check | Risk | W, script-only | Event: every profile version change; plus a daily sweep | None | B0 | Signs loosen proposals | Pass, or a black alert. Feeds R8 and the loosen cards. |
| R7 | Model-validation review | Risk | W, or C+S when he starts it | Event after R4 passes, or a subflow of T6 | Validator from another family, plus a judge | B4 | Reads the verdict; may override with a reason | Validation report and conditions. Feeds T6, R6 and T5. |
| R8 | Incident post-mortem | Risk | W, then C | Incident closed at red or above | Analyst plus validator | B2-B3 | Accepts actions | Timeline explainer and lessons. Feeds checks, the Lab and lessons. |

---

## 2. Template cards

Each card has the same fields.

- **Role** is the model role from Settings (section 4.8). `none` means a script or rule.
- **Kind** is the engine step kind.
- All numbers are **editable defaults**. They change in the UI, and every change is versioned.

### T1 — Morning brief

**Purpose.** One screen before his first session. It answers four questions: what the account looks like, what happened overnight, what is on today, and what needs him.

| Field | Value |
|---|---|
| Mode | W. The copilot answers "why" questions afterwards from the run log. |
| Trigger | Cron in his timezone. Default 06:00 Europe/London on weekdays, DST-aware, 60 min before London open. |
| Pre-check | Script. Compare today's inputs with yesterday's (`continuity`). If nothing is new (no deals, no alerts, no events above low impact, no research items, no pending decisions), the script renders a "quiet day" card from the template with **zero tokens**. |
| Gates / kill rules | Read-only. Grader: every number traces to a script output. Prose of at most 150 words. At most 3 decisions. |
| Human points | Up to 3 decision cards. Each has a recommendation, a default and "what happens if you do not answer". |
| Memory | `workflow` scope: yesterday's brief, used for "what changed". `operator` scope: sections he never opens get demoted. That is a lesson row, not silent. |
| Failure policy | If the writer fails, deliver the script-only card. Escalate only if the account read fails, because that is urgent: the brief without account state is wrong. |
| Budget guard | B1. One writer call of 8k tokens or less. If the cap is closed, the script-only card is delivered. |
| Output | `dashboard_card` JSON with these tiles: equity and cushion in R; overnight P&L in R; open positions; today's red events; unit states; research top 3; decisions. |
| Feeds | T2 (today's session list) and the inbox. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Read account and guard state: equity, kill-line cushion, open risk | script | none |
| 2 | Pull the latest outputs of T3, T4, T5, T10 (last night), R1, R2 and R3 (`context_from`) | script | none |
| 3 | Rank items. Red and black first, then decisions, then events in his sessions. | rule | none |
| 4 | Write the brief JSON | model | writer |
| 5 | Check numbers and links | grader | none |
| 6 | Render, deliver to the inbox, add to the digest | script | none |

### T2 — Pre-session market read (MIS conditions per scalper type)

**Purpose.** Before each session, show which units have their market conditions met, which are partly met, and which should stand aside, with reasons.

The node's MIS remains the authority for trading. This read is for his awareness, and it doubles as a check that the MIS is sane.

| Field | Value |
|---|---|
| Mode | W. Each session clone is a variant (section 3). |
| Trigger | Cron 30 min before each session open in the market's own timezone: Tokyo, London 08:00, New York 08:00 ET. Each is DST-aware. |
| Pre-check | Script. Are any demo or live units scheduled for this session? Is the data fresh (last tick less than 60 s old)? If not, stay silent or raise a data-staleness alert. |
| Gates / kill rules | Read-only. **Agents never edit MIS settings.** If the node's MIS answer differs from the script mirror for the same unit, that opens an incident (R8 candidate). |
| Human points | None. |
| Memory | `workflow`: the last read per session, so the model wakes only on change. Shared table `scalper-types` (his edits, versioned). |
| Failure policy | Continue per unit: one failing unit does not block the others. Its cell shows "could not check". |
| Budget guard | B1. One cheap call per session, only if some unit changed state since the last read. |
| Output | `session_board` JSON: a grid of units × conditions with go / caution / stand-aside, each cell carrying its number and threshold. |
| Feeds | T1, T10 and the copilot. Its condition hit rate feeds R3. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Features per instrument: spread percentile against the same hour over 20 days; ATR(M5) percentile; Asian range as a fraction of ADR; share of ADR used; distance to prior-day high and low and to the weekly open; slope of the higher timeframe; DXY move overnight; minutes to the next red event (from T3) | script | none |
| 2 | Read each unit's condition needs and its MIS answer through the unit adapter | script | none |
| 3 | Evaluate the needs against the `scalper-types` table (below). Mirror check against the MIS. | rule | none |
| 4 | One line per changed unit, saying why | model | scanner |
| 5 | Check numbers | grader | none |

Starter `scalper-types` table (his values to edit):

| Scalper type | Wants | Stands aside when |
|---|---|---|
| Session-open breakout (London or NY) | Asian range ≤ 0.6 × ADR; ATR percentile rising; spread percentile ≤ 60 | A red event within 30 min; ADR already more than 70% used |
| Momentum continuation | Higher timeframe slope agrees; ATR percentile ≥ 50 | Price within 0.2 ATR of a daily level; spread percentile ≥ 80 |
| Range mean-reversion | ATR percentile 20-60; flat higher timeframe | A red event within 60 min; breakout from the Asian range |
| News or event scalper | A scheduled event inside the window | Spread not back to normal within 2 min after release |
| Liquidity-sweep reversal | A clear prior high or low within 1 ATR | A trend day (more than 60% of ADR used by the open) |

### T3 — News and macro calendar watch (script-first)

**Purpose.** Know every scheduled release and every unscheduled central-bank headline that touches an active unit. Keep it **zero-token unless something surprises**.

| Field | Value |
|---|---|
| Mode | W, script-first. |
| Trigger | Cron 00:05 UTC fetches the day's calendar. For each event affecting a unit's currency, the engine creates event fires at T−30, T−5 and T+1 min (the trigger rows are made by the engine from his approved template, not by a run). Headline RSS is polled every 2 min during his sessions. |
| Pre-check | Script. Does the event or headline map to a currency of an active unit? For RSS: are there new item IDs that match the watch terms? Otherwise stay silent. |
| Gates / kill rules | Read-only. **Cross-check**: the guard's news list must contain every red event the script found. A missing event raises a black alert, because the guard would trade through it. |
| Human points | None. Urgent push for unscheduled central-bank or intervention-like moves, for example a JPY move of 2 ATR or more in 5 min with no scheduled event. |
| Memory | `workflow`: a history of surprises per series (actual − forecast) to compute z-scores. Lesson rows such as "this source posts actuals late". |
| Failure policy | Fetch failures retry on a 5/15/30 min ladder (spend-neutral). If the calendar is missing by 06:00, send an urgent alert, because T2 and the guard both lean on it. |
| Budget guard | B0 normally. B1 for one cheap note per surprise with \|z\| ≥ 1.5, and a cap of 10 notes a day. |
| Output | `calendar_strip` JSON plus one-line `alert`s, each with a source link. |
| Feeds | T1, T2, T7 (trades tagged near news), R1 (gap allowance), R5 (event scenarios) and R8 (timeline). |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Fetch the calendar from free sources; normalise to UTC; map currency → instrument → unit | script | none |
| 2 | Blackout windows per unit, from the unit's conditions and the account's prop-firm news rule | rule | none |
| 3 | At T+1: fetch the actual; compute the surprise z-score, the spread spike and the move in ATR | script | none |
| 4 | If a threshold trips: a two-line note on what moved and what it means for open units | model | scanner |
| 5 | Check links and numbers | grader | none |

### T4 — Research desk overnight run on a watchlist

**Purpose.** The Skydive desk, rebuilt for FX scalping. Several analysts each work one beat, a coordinator synthesises, and the cut rules are **code, not the coordinator's discretion**.

| Field | Value |
|---|---|
| Mode | W. A coordinator agent with fan-out analyst steps. |
| Trigger | Cron Sun-Thu 03:00 in his timezone, landing before T1. |
| Pre-check | Script. Is there anything new since the last run: new RSS IDs, a COT release day, a calendar change, any watchlist instrument moving more than 1 ADR? If none, stay silent and T1 says "desk: nothing new". |
| Gates / kill rules | **No source, no claim**: the `cut-rules` grader drops any claim without a link and records which analyst made it. **A single-analyst flag is cut** unless it is a scheduled tier-1 event, which is a fact rather than an opinion. Two analysts on the same instrument make it HIGH. A sentiment flag alone counts only above 5 sd from its own 30-day normal. |
| Human points | He reads the brief. No gate. |
| Memory | `workflow`: the last brief (repeats are skipped). Lessons: caught false positives, for example "COT is Tuesday data published Friday; not fresh on Monday". Stored per beat and read before the next run. |
| Failure policy | An analyst failure is retried once by the doctor on the next model tier. If it still fails, the coordinator may do that beat directly within budget. Otherwise the section reads "could not check: <beat>, <cause>". **Never a plausible filler.** |
| Budget guard | B3. 6 analysts with at most 10 tool calls each, and a hard stop at 20. A model-tier floor in Settings, because the clipping showed the cheapest tier failing. Reserve-then-refund per run. |
| Output | `ranked_brief` JSON with the sections HIGH, MEDIUM, CALENDAR, POSITIONING, CROSS-ASSET and WHAT I CUT AND WHY. Every claim carries a link and a label: retrieved, remembered or inferred. |
| Feeds | T1, T2 (bias notes), Lab hint cards (via a rule: HIGH items with a mechanism become hint cards), and lessons. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Load the watchlist, last brief and beat lessons | script | none |
| 2 | Beats in fan-out: (a) rates and central-bank speakers; (b) calendar and surprises (from T3); (c) positioning (CFTC COT, broker retail sentiment); (d) technical structure (levels, ranges, regime; mostly a script feeding the analyst); (e) cross-asset (DXY, yields, oil, equity risk-on/off); (f) headline volume against baseline | model ×6 (fan-out, `all` join, finished items kept) | analyst |
| 3 | Apply the cut rules | rule + grader | none |
| 4 | Synthesise the surviving claims, rank them, state ranges with 90% coverage where a number is forecast | agent | coordinator |
| 5 | Check citations and numbers | grader | none |
| 6 | Turn HIGH items with a mechanism into hint-card proposals (parked, not written to the Library) | rule | none |

Role list borrowed from the Astra posts, used as roles and not as standing bots: scanner → beats (a)-(f); "chief of staff" → the coordinator; "risk bot with zero negotiation authority" → the guard and R1, which have no model at all.

### T5 — Paper/demo trading monitor

**Purpose.** Watch each demo unit against what its backtest promised, catch behaviour faults early, and say when the evidence is ready for promotion.

| Field | Value |
|---|---|
| Mode | W. |
| Trigger | Monitor trigger on every closed deal from the node, plus a heartbeat every 15 min during the unit's sessions. |
| Pre-check | Script. Any new deals since the last tick? Otherwise check the heartbeat only: is the unit alive and connected? |
| Gates / kill rules | Behaviour faults raise an incident: a trade outside its sessions or in a blackout; size different from the expected r by more than 10%; a missing stop; duplicate orders; a spread at entry above its own condition. Kill rule on demo: drawdown of 8R or more, or 2 behaviour faults in a day, leads to an **automatic bench (tighten-only, demo only)** and a card. |
| Human points | None on demo. He sees the evidence-ready card via T6. |
| Memory | `run` and `workflow`: running stats per unit. Faults become lesson rows tagged to the unit's lineage. |
| Failure policy | If the node read fails 3 times, send an urgent alert: "demo unit unobserved". Never assume quiet means fine. |
| Budget guard | B0 per tick. B1 only for an out-of-band explanation (at most 2 a day per unit). |
| Output | `unit_tile` JSON: n trades, expectancy in R with CI, win rate, average win and loss in R, drawdown in R, trades per day, and cumulative R against the backtest's Monte Carlo 5-95% band. |
| Feeds | R3 (same stats), the T6 event `evidence_ready` once the minimum is met (default: at least 2 weeks and at least 100 trades for scalpers, see Q5), and T10. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Read new deals and the R journal through the unit adapter | script | none |
| 2 | Update stats; place them against the Monte Carlo band | script | none |
| 3 | Behaviour checks and the band verdict (in, edge, out) | rule | none |
| 4 | Bench on the kill rule (demo only), through the tighten interface | script | none |
| 5 | On out-of-band: candidate causes, each with what would make it true | model | analyst |

### T6 — Promotion evidence pack

**Purpose.** One pack that lets him sign or refuse a promotion (demo → live, or a bigger stage) in under five minutes, with every claim checkable.

| Field | Value |
|---|---|
| Mode | C+W. T5 fires it, or he asks the copilot "is unit X ready?". |
| Trigger | Event `evidence_ready` from T5, or manual. |
| Pre-check | Script. The minimum evidence is met, and no open red incident exists on the unit. |
| Gates / kill rules | Checklist rule, all green required. Demo minimum met. Demo results inside the Monte Carlo band. Live-calibrated cost at most 1.25 × the assumed cost (from T9). R4 pass on the current content hash. R5 shows no scenario breaching the kill line without the guard stopping it. R7 verdict is approve, or approve with conditions. R6 history clean. The account's prop-firm rules are compatible (minimum hold time, news ban, weekend holding). |
| Human points | **He signs the promotion card.** The default if he does not answer is "extend demo 1 week". The upload to a live node is his own click in the node UI; no step does it. |
| Memory | The pack is stored with the unit's lineage. A refusal reason becomes a lesson row. |
| Failure policy | If a subflow fails, its row reads "missing", and the checklist cannot be all green. Escalate to the inbox. |
| Budget guard | B3, mostly in the R7 subflow. The rest is scripts plus one writer call. |
| Output | `scorecard` (funnel: Lab → backtest → audit → stress → validation → demo → **you**) plus a `decision_card`. The marginal effect on the book is shown: effective number of bets before and after, and the account worst case before and after (from R2 and R5). |
| Feeds | His signature, T5 (monitoring plan from the R7 conditions) and R6 (the signed ranges become the baseline). |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Gather the term sheet, lineage, backtest, demo journal, T9 costs and R6 history | script | none |
| 2 | Re-run R4 if its hash is stale | subflow | — |
| 3 | R5 with the unit added to the current book | subflow | — |
| 4 | R2 marginal correlation and effective number of bets | script | none |
| 5 | Independent validation | subflow (R7) | validator |
| 6 | Checklist verdict | rule | none |
| 7 | Decision card: recommendation, default, consequence of silence | model | writer |
| 8 | Check numbers and links | grader | none |
| 9 | Promotion gate | human | — |

### T7 — Trade journal review in R, with lessons

**Purpose.** Find what is really different in his results, by session, setup or condition, without telling stories about noise. Then turn the real findings into lessons.

| Field | Value |
|---|---|
| Mode | W weekly. C to discuss: "why did London lose this week?" reads the same output. |
| Trigger | Cron, Saturday 09:00. A light daily slice is folded into T10. |
| Pre-check | Script. At least 20 new trades across units since the last review, or else a "too few trades" card with zero tokens. |
| Gates / kill rules | **Significance filter**: a slice is reported only if n ≥ 20 and its 90% CI on expectancy in R excludes the overall mean. The grader rejects any lesson without slice stats (n, CI). At most 3 lessons per week. |
| Human points | He accepts or rejects each lesson card. An accepted lesson becomes a row. A lesson accepted 3 times turns into a proposal to encode it: a unit condition (a Lab variant) or a checklist line. |
| Memory | `operator` lessons table: lesson, evidence pointer, times seen, status. Rejected lessons are kept so they are not proposed again. |
| Failure policy | If the model fails, deliver the stats explainer without lessons. |
| Budget guard | B2. One analyst call plus one judge call. |
| Output | `explainer`: R-multiple histogram; slice heatmap (session × setup × MIS state); MAE/MFE scatter in R with exit-efficiency lines; streaks; rule breaks; manual trades in their own lane. |
| Feeds | Lessons, Lab hint cards (for example a session filter idea), R3 (cross-check) and T2 (conditions table proposals). |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Load the R journal with tags: session, hour, setup, MIS state at entry, minutes to news, spread at entry, slippage, MAE and MFE | script | none |
| 2 | Stats by slice with bootstrap CIs; exit efficiency (captured R ÷ MFE); stop-hunt pattern (MAE just past the stop, then a reversal) | script | none |
| 3 | Significance filter | rule | none |
| 4 | Draft up to 3 lessons as hypotheses with candidate causes | model | analyst |
| 5 | Check each lesson against its slice stats; dedupe against the lessons table | grader | judge |
| 6 | Lesson cards | human | — |

### T8 — "Video to demo trial" in the Lab

**Purpose.** He drops a video. The Lab extracts the strategy faithfully, builds the vanilla version, audits it, and, if it survives, offers a small demo trial. This is template B of 12 (d), cut down for one source.

| Field | Value |
|---|---|
| Mode | C+W. He drops the URL in the copilot. The copilot starts the run and holds the conversation for the spec holes. |
| Trigger | Manual. |
| Pre-check | Script. Already in the source ledger (same video hash)? Then show the old result instead of reprocessing. |
| Gates / kill rules | **Exits are never invented**: a missing exit gets a house exit policy labelled `external_policy`. Compile and composition checks. **R4 must pass. The kill criteria are hard and no model can override them.** The demo trial starts with a **demo-only minimal risk profile**: fixed small r, tighten-only. |
| Human points | (1) Fill spec holes: one numbered grilling round, each question with a recommended answer, where "yes" accepts. (2) **Sign "start demo trial"**. The upload follows Q1. |
| Memory | The source ledger (never reprocess). Negative results with the reason and trial count. The trial ledger feeds the deflated Sharpe. |
| Failure policy | Escalate: the run pauses in the inbox at the failing stage with retry and skip buttons. Paid steps are never rerun (checkpoint). |
| Budget guard | B4, with his per-run cap. Transcript-only triage. Frames only for flagged windows, with a frame cap. Whisper only for videos without captions. |
| Output | `funnel_scorecard`: the stage reached, equity curve, in-sample vs out-of-sample, the R4 tick table, and the card's holes. |
| Feeds | T5 once the demo starts; otherwise the Library as a hint or negative result. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Capture: captions first, ASR fallback, metadata | script | none |
| 2 | Pre-filter (keywords, duration), then a "strategy present?" verdict | script, then model | none, then scanner |
| 3 | Section map, claims with timestamps, visual passes on flagged windows | agent | researcher |
| 4 | Strategy spec card with its holes kept | agent | builder |
| 5 | Spec completeness check | grader | none |
| 6 | Grilling round on the holes | human | — |
| 7 | Build vanilla in the Lab; compile; composition check | agent, then script | builder, then none |
| 8 | Backtest with costs (tick or M1 with a spread model per hour) | script | none |
| 9 | Overfit audit | subflow (R4) | — |
| 10 | Verdict JSON | model | writer |
| 11 | "Start demo trial?" | human | — |

### T9 — Execution quality check (script-only)

**Purpose.** Measure what fills really cost against what the backtest assumed. Costs kill scalpers before bad signals do.

| Field | Value |
|---|---|
| Mode | W, script-only. The copilot explains on request by reading the output. |
| Trigger | Every closed deal (event), an hourly roll-up, and a daily report after T10. |
| Pre-check | None needed. It runs on events only. |
| Gates / kill rules | Amber: cost ratio (real cost per trade in R ÷ assumed cost in R) above 1.25 over the last 50 trades. Red: above 1.5, or any single slippage worse than 0.5R, or a spread at entry above the unit's own maximum (a behaviour fault, sent to T5 and R8). |
| Human points | None. |
| Memory | `workflow`: the **live cost model** per instrument, hour and order type. It is versioned, and R4 and backtests use it. |
| Failure policy | If the deal feed has gaps, send an alert "cost data incomplete" and do not average over the gap. |
| Budget guard | B0. |
| Output | `tile_row` plus table. Spread at entry (pips, and in R as a share of the stop). Signed slippage in pips and R, by order type (market, stop, limit), by hour and by session. Fill latency (send → fill, ms). Rejects and requotes. Commission per round trip. Cost ratio. |
| Feeds | R3 (cost drift), the R4 cost stress (real cost model), T6, R8, and a broker comparison when there is more than one broker. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Read deals; join each one to the unit's intended price and the quote at signal time | script | none |
| 2 | Compute the metrics and update the cost model | script | none |
| 3 | Amber and red rules | rule | none |

### T10 — End-of-day wrap

**Purpose.** Close the trading day in one card: what happened in R, what is still open overnight, and what is on tomorrow.

| Field | Value |
|---|---|
| Mode | W. |
| Trigger | Cron 17:05 America/New_York (the FX day roll), or after his last session if earlier. |
| Pre-check | Script. Were there trades, alerts or incidents today? If not, a quiet card with zero tokens. |
| Gates / kill rules | Read-only. Friday adds overnight and weekend risk: open positions with gap allowance, and swap and rollover cost. |
| Human points | None. Pending decisions are listed with their defaults and expiry. |
| Memory | Daily row in the day log (`workflow`). T1 reads it the next morning. |
| Failure policy | Deliver the script-only card if the writer fails. |
| Budget guard | B1. |
| Output | `dashboard_card`: day P&L in R and $ per unit; cushion change; closest approach to the kill line today (from R1); day cost ratio (from T9); unit states; tomorrow's red events (from T3). |
| Feeds | T1 (`context_from`), T7, and R3 (runs after it). |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Gather the day: journal, R1 minimum, T9, T5, incidents, decisions | script | none |
| 2 | Tomorrow's events; Friday weekend checks | rule | none |
| 3 | Wrap JSON of at most 120 words | model | writer |
| 4 | Check numbers | grader | none |

### R1 — Kill-line distance watchdog (script-only)

**Purpose.** Always know how far the account is from its kill line and its daily loss budget, **including what open positions could still cost**. Also check that the guard itself is alive and configured as signed.

| Field | Value |
|---|---|
| Mode | W, script-only. |
| Trigger | Monitor every 30 s while any risk is open, every 5 min otherwise, plus an event on each equity update from the node. |
| Pre-check | None. The script is the job. |
| Gates / kill rules | Cushion D = equity − kill line. Worst-case cushion D_wc = D − Σ open risk to stops − a slippage allowance (k × typical slippage from T9 × open lots) − a gap allowance (near red events from T3, or over the weekend). The same is computed against the daily loss budget and the trailing drawdown from the account's prop-firm rule table. Distance in R = D_wc ÷ the largest active r. **Amber**: D_wc below 30% of the daily budget, or below 3R. **Red**: below 10%, or below 1R. **Black**: guard heartbeat missing for more than 60 s, **or the guard config hash differs from the signed config**. |
| Human points | None. Push on red and black. **The guard acts. R1 only watches and tells.** |
| Memory | `workflow`: the day's minimum cushion (for T10) and alert dedupe by signature. |
| Failure policy | R1 failing is itself **urgent**. The engine watchdog checks R1's last tick; if it is more than 2 min old with open risk, it sends a push "kill-line watchdog down". |
| Budget guard | B0, never paused at the cap. |
| Output | `gauge` JSON (cushion in $, in R and in % of budget) plus `alert` lines. |
| Feeds | T1, T10, R8 (red or black opens an incident), and the copilot. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Read equity, positions, stops and guard state (read-only) | script | none |
| 2 | Compute D, D_wc, the budget distances and distance in R; hash the guard config | script | none |
| 3 | Thresholds and alert dedupe | rule | none |

### R2 — Correlation and exposure drift

**Purpose.** Catch the book quietly becoming one bet, for example three USD-short units all leaning risk-on.

| Field | Value |
|---|---|
| Mode | W. |
| Trigger | Event on each position change; hourly during sessions; a full run daily after T10. |
| Pre-check | Script. Did exposure change since the last run? Intraday, only open-risk changes count. |
| Gates / kill rules | Script measures: currency-leg exposure (EURUSD long = +EUR −USD) in R of open risk; rolling 60-day correlation of unit daily R; overlap correlation (how often units are in trades at the same time); effective number of bets from the correlation eigenvalues. **Drift rule**: any pair \|Δρ\| > 0.3 against the promotion-time baseline; effective bets down more than 25%; or open risk in one currency above X R (from the guard's table, read-only). |
| Human points | Any guard change, even a tightening one, is a card he signs. Agents cannot touch the guard. |
| Memory | Baseline matrix per promotion (stored with T6). |
| Failure policy | Continue. Missing units show as "unknown", and an unknown counts as correlated (the conservative choice). |
| Budget guard | B0. B1 for one explainer call when a rule trips. |
| Output | `heatmap` (unit × unit ρ now vs baseline), `currency_bars` (open risk in R per currency), and the effective-bets tile. |
| Feeds | R5 (current matrix for the correlation stress), T6 (marginal effect), guard proposal cards, and T1. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Positions to currency legs; open risk in R | script | none |
| 2 | Correlations, overlap and effective bets | script | none |
| 3 | Drift rules | rule | none |
| 4 | On a trip: what is driving it, plus a proposed tightening | model | analyst |
| 5 | Check numbers | grader | none |

### R3 — Strategy decay detection

**Purpose.** Tell real decay from bad luck, per unit, early. The definition of decay is **pluggable** (09 §3.12), because it is still open with the risk session.

| Field | Value |
|---|---|
| Mode | W. |
| Trigger | Daily after T10, plus an event every 10 closed trades on a unit. |
| Pre-check | Script. The unit has new trades since the last run. |
| Gates / kill rules | Tests per unit: CUSUM of (R − expected EV), with k and h set from the backtest σ; rolling 50-trade expectancy with a bootstrap CI; cumulative R against the Monte Carlo 5-95% band; a binomial test on win rate; payoff-ratio drift; trade-frequency drift (Poisson); cost drift (T9); MIS hit-rate drift (T2). **Red needs a CUSUM breach, or at least 2 independent tests**, which avoids small-sample false alarms. |
| Human points | Red gives a card: bench / back to demo / keep watching, with a default (Q2). Amber is informational; the unit's own recipe may tighten itself as designed. |
| Memory | The decay history per unit. Decay causes become lessons on the strategy's lineage, for the Lab rehab loop (the old WF3). |
| Failure policy | Continue per unit. |
| Budget guard | B0 for the tests. B1 for at most 1 explainer call per amber or red unit per day. |
| Output | `rag_list` (red, amber, green per unit) and per-unit sparklines with band and CUSUM. The explainer gives candidate causes (regime, costs, implementation, chance), each with what would make it true and a 90% range for expectancy. |
| Feeds | The Lab rehab loop (tightened units become rework candidates), R8 (red on live), T1 and T6. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Load the journal in R and the backtest baseline through the unit adapter | script | none |
| 2 | Run the decay tests | script | none |
| 3 | Red/amber/green rule (pluggable definition) | rule | none |
| 4 | Candidate causes for amber and red | model | analyst |
| 5 | Check numbers | grader | none |
| 6 | Bench or demote card for red | human | — |

### R4 — Overfit audit of a candidate

**Purpose.** "The model proposes, the pipeline decides" (BuildAlpha). A hard, scripted gate that every candidate passes before validation and demo. **It is bound to the candidate's content hash.**

| Field | Value |
|---|---|
| Mode | W, used mostly as a subflow of T8, T6 and the Lab funnel. |
| Trigger | Event: the candidate reaches stage `validate`. Also manual. |
| Pre-check | Script. Hash code + config + data snapshot + cost-model version. If a pass for the same hash exists, reuse it. |
| Gates / kill rules | All scripts. Default thresholds (his to edit globally; a variant can only make them stricter): **(1) Walk-forward**: rolling, at least 6 folds; walk-forward efficiency (OOS ÷ IS) ≥ 0.5. **(2) Deflated Sharpe**: N = every variant in the lineage family, dead ones included, from the trial ledger; probability form ≥ 0.95 (12 says "above 0"; see Q9). **(3) PBO** (combinatorial cross-validation, 16 blocks) ≤ 0.25. **(4) Noise test**: 200 runs on prices perturbed by a fraction of ATR; at least 70% still profitable and median expectancy at least 50% of the original. **(5) Monte Carlo permutation**: 1,000 permutations of the signal timing; p ≤ 0.05. **(6) Random benchmark**: 1,000 random-entry runs with the same frequency, side mix, exits and holding time; the candidate beats the 95th percentile. **(7) Parameter neighbourhood**: at least 60% of ±1-step neighbours profitable, and no cliff. **(8) Cost stress**: profitable at 1.5 × the **live** cost model; 2 × is reported. **(9) Holdout**: sealed and opened once; the ledger records the opening. **(10) Sanity flags**: Sharpe above 3 on minute data means lookahead is suspected; same-bar TP and SL ambiguities are counted; scalper IS trades ≥ 200 and OOS ≥ 100. |
| Human points | None. **No override inside the run.** He may change a threshold only in Settings, as a versioned, logged act that applies to all candidates. |
| Memory | Negative results: the failing test, values, trial count and hash. The trial ledger is appended. |
| Failure policy | `fail_fast` on a data or engine error, and the doctor retries spend-neutral. A test failure is a result, not an error. |
| Budget guard | Tokens B0-B1 (one explainer call). Compute heavy: `runs_on` the server when he has one. A compute-minutes cap per candidate. |
| Output | `scorecard`: a tick or cross per test, the walk-forward equity, a permutation histogram with the real value marked, the random-benchmark distribution, the noise fan, and "what could fake this number". |
| Feeds | R7 (pass only), T6, T8, and the Library's negative results. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Freeze and hash; read the trial count | script | none |
| 2 | Tests (1)-(8) in fan-out; each test keeps its result | script ×8 | none |
| 3 | Holdout one-shot, only if (1)-(8) pass | script | none |
| 4 | Thresholds; verdict bound to the hash | grader | none |
| 5 | "What could fake this" explainer | model | writer |

### R5 — Stress tests

**Purpose.** Ask what the whole book does on the worst days FX has had, and whether the guard stops it in time.

| Field | Value |
|---|---|
| Mode | W. |
| Trigger | Weekly, Sunday 18:00. Also on events: a unit added or promoted, a guard config change, and as a subflow of T6. |
| Pre-check | Script. Did the book, guard config or cost model change since the last run? If not, reuse last week's results with a fresh stamp. |
| Gates / kill rules | **Historical scenarios** (replayed where tick data exists, otherwise applied as shocks): SNB unpeg (15 Jan 2015, EURCHF); Brexit vote night (24 Jun 2016); GBP flash crash (7 Oct 2016); JPY flash crash (3 Jan 2019); COVID week (9-20 Mar 2020); the five biggest NFP and CPI surprises in his instruments; rollover spread blowouts at 17:00 NY; Monday gaps. **Synthetic scenarios**: spread × 3 for 10 min; 2-pip slippage on every stop; a gap of 3 ATR through stops; all USD pairs at ρ = 1; broker disconnect for 5 min with positions open; a loss streak at the Monte Carlo 99th percentile; every unit stopped at once at 2 × slippage. **Pass**: after each scenario the equity stays above the kill line by at least a buffer, or the guard stops it with an overshoot below Y $. The prop daily limit is not breached. |
| Human points | Proposals only, all tighten-only: a smaller r, a session block, a guard change. He signs. |
| Memory | Scenario library (`workflow`). New windows found by the optional RLM step are added after his OK. |
| Failure policy | Continue per scenario. A missing-data scenario shows "not run", never "pass". |
| Budget guard | B1 normally. B3 when the optional `rlm` step runs (max children, a wall-clock limit, a sandbox only). |
| Output | `heatmap` (units × scenarios, cushion left in R), a worst-case waterfall, and guard reaction time per scenario. |
| Feeds | T6, guard proposal cards, R8 (a failing scenario on the live book opens a risk incident), and T1 (weekly line). |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Load the book, guard config (read-only), cost model and scenario library | script | none |
| 2 | Optional: scan the tick archive for new extreme windows (spread above 5 × normal, moves above 5 ATR in 1 min) | rlm | researcher |
| 3 | Run the scenarios through the unit logic and a guard simulation | script | none |
| 4 | Pass rules | rule | none |
| 5 | Explain the worst 3 and propose tightenings | model | analyst |
| 6 | Check numbers | grader | none |

### R6 — Tighten-only self-tuning check (script-only)

**Purpose.** A second line of defence. The node should already refuse loosening at write time. R6 independently proves that every self-tune stayed tighter, or inside what he signed.

| Field | Value |
|---|---|
| Mode | W, script-only. |
| Trigger | Event on every risk-profile version change a unit writes; a daily sweep; and before any upload. |
| Pre-check | None. |
| Gates / kill rules | Inputs: profile N, profile N−1, **the signed profile** (ranges and ramp schedule), and the **direction table** (per parameter, which way is tighter, for example r ↓, max trades a day ↓, max spread ↓). Rules: every changed parameter moves tighter, **or** moves within the signed ramp schedule (Q3); every value stays inside its signed range; the ranges themselves are unchanged; any loosening carries a signature id; the guard config hash is unchanged. A violation is **black**. |
| Human points | Loosen requests from a unit's recipe (for example "restore size after recovery" beyond the signed schedule) become **loosen cards** with evidence: R stats since the tighten, and the decay status. **He signs.** The card is rendered from a template, with zero tokens. |
| Memory | The profile version chain per unit, with the signature ids. |
| Failure policy | If R6 cannot read a profile version, it raises a black alert. A silent gap in this check is not allowed. |
| Budget guard | B0. |
| Output | `check_row` (pass) or `alert` (black) plus an incident. The suggested action is "revert to last signed profile" (Q2 decides whether that applies automatically). |
| Feeds | R8, loosen cards, and T6 (a clean history is a promotion requirement). |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Read versions N, N−1 and the signed profile through the unit adapter | script | none |
| 2 | Compare against the direction table and ranges; check the guard hash | rule | none |
| 3 | Render a loosen card or a violation alert | script | none |

### R7 — Model-validation review by a reviewer from a different model family

**Purpose.** The builder never grades its own work. A reviewer from a different model family gets the evidence, not the builder's story, and tries to disprove the unit. The checklist follows model-risk practice (SR 11-7 style, `[remembered]`): soundness, data, implementation, outcomes, use limits, and monitoring.

| Field | Value |
|---|---|
| Mode | W as a subflow. C+S when he says "have someone else check unit X". |
| Trigger | Event after R4 passes, or a subflow of T6. Also manual. |
| Pre-check | Rule. The reviewer's model family ≠ the builder's model family (from Settings and the run log). If no other family is configured, the run continues as a **same-family review**: a fresh context with a hostile brief, labelled as such (Q8). |
| Gates / kill rules | **Blind pack**: a script strips the builder's conclusions and keeps the term sheet, spec, code hash, data snapshot, R4 and R5 results and the demo journal. Checklist: (a) the mechanism makes sense; why would this edge exist? (b) data: point-in-time; broker server timezone; DST in session logic; gaps; (c) implementation: code matches spec; intrabar fills; spread per hour; (d) outcomes: OOS and Monte Carlo; does the demo match? (e) use limits: capacity, broker minimum stop distance, prop rules; (f) monitoring plan: which decay tests and thresholds. The validator may re-run read-only Lab scripts to test a doubt. Every finding needs an evidence pointer and a severity. **Any critical finding means reject. A major finding means approve with conditions.** |
| Human points | He reads the verdict. He may override a reject only with a written reason; the unit then carries an "override" badge (Q4). He may ask for a second validator from a third family. |
| Memory | Findings become a "common defects" checklist that builders read before they build. That is lessons into structure. |
| Failure policy | If the validator fails, the doctor retries on the next model, then escalates. **No verdict means no promotion.** |
| Budget guard | B4. At most 40 tool calls for the validator and a per-run cap. One judge call. |
| Output | `validation_report` (explainer): verdict, findings table, and the conditions list. Conditions are tighten-only constraints. |
| Feeds | T6, R6 (conditions become signed ranges) and T5 (monitoring plan). |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Build the blind evidence pack | script | none |
| 2 | Family check; label the review type | rule | none |
| 3 | Disprove attempt along the checklist | agent | validator |
| 4 | Every finding cites evidence | grader | none |
| 5 | Score the review against a rubric (judge ≠ validator) | grader | judge |
| 6 | Verdict mapping | rule | none |

### R8 — Incident post-mortem

**Purpose.** A blameless account of what happened, what it cost in R, why, and which check would have caught it. Repeat incidents turn into structure, not just notes.

| Field | Value |
|---|---|
| Mode | W, then C: he talks it through with the copilot, which reads the same timeline. |
| Trigger | An incident closed at red or above. That covers the kill switch firing, a guard trip, an R6 violation, slippage beyond the stop greater than 0.5R, a broker disconnect with open risk, R1 down for more than 2 min with open risk, a T2 mirror mismatch, and a failure of a money-adjacent template. |
| Pre-check | Script. Dedupe by error signature. Is there already a post-mortem for this signature in the last 7 days? Then append to that one. |
| Gates / kill rules | Grader: every timeline line has a source event. Cause categories are fixed: market, execution or broker, unit logic, risk config, infra or data, human or process. Each candidate cause states what would make it true. |
| Human points | He accepts actions. Action types: (a) a tighten-only proposal; (b) a new check, meaning a script or rule node; (c) Lab rework; (d) an accepted risk, with his reason. |
| Memory | Lessons table, keyed by signature. A **signature seen 3 times** auto-proposes a check (encode the lesson in structure). |
| Failure policy | If the agent fails, deliver the script timeline and impact. They are useful on their own. |
| Budget guard | B2-B3. |
| Output | `explainer` with a scroll-story timeline: before, trigger, guard reaction, aftermath. Impact in R and $ against the cushion. Causes. Actions. |
| Feeds | New checks into templates (via the builder, parked for his OK), the Lab, the lessons table and T1. |

| # | Step | Kind | Role |
|---|---|---|---|
| 1 | Timeline over ±2 h from guard, node, broker deals, MIS state, calendar, spreads and run logs | script | none |
| 2 | Impact in R and $; cushion before and after | script | none |
| 3 | Draft: what happened, contributing factors, candidate causes | agent | analyst |
| 4 | Challenge the draft | model | validator |
| 5 | Citations | grader | none |
| 6 | Action cards | human | — |

---

## 3. Cloning a template into a variant

Example request: **"London-session EURUSD scalper morning read."**

### 3.1 What a clone is

- A template is a versioned folder: `templates/pre-session-read@1.2.0/` with `workflow.yaml`, `params.schema.json`, `scripts/`, `prechecks/`, `fixtures/` and `README.md`.
- A variant is a small folder that **extends** a pinned template version and overrides only parameters.
- Nodes marked `locked` cannot be removed or edited by a variant. These are graders, cut rules, gates, kill rules, the tighten-only interface and every guard read.
- Risk thresholds in R1, R4 and R6 can be made **stricter** in a variant, never looser. Trader-read thresholds (T1-T4, T7, T10) are free.

```yaml
# workflows/morning-read.london-eurusd-scalper/variant.yaml
id: wf.morning-read.london-eurusd-scalper
extends: tpl.pre-session-read@1.2.0     # pinned; a template update proposes a rebase card
params:
  session: london                        # Europe/London, DST-aware
  open_local: "08:00"
  lead_minutes: 30
  instruments: [EURUSD]
  units:
    filter: {instrument: EURUSD, scalper_type: [session_open_breakout, range_mean_reversion], stage: [demo, live]}
  conditions_table: scalper-types@v3    # shared table; his edits
  quiet_policy: silent_if_unchanged
  deliver: {normal: inbox, red: push}
  context_from: [wf.news-watch, wf.research-desk]
roles:
  scanner: default                       # or a model for this variant only
thresholds:
  spread_pct_max: 60                     # free for read templates
```

### 3.2 How the trader and the copilot make it

1. **He says it** in the hub, in any home: "make me a London-session EURUSD scalper morning read".
2. **The copilot looks things up and does not ask about them.** It finds the closest template (`tpl.pre-session-read`), his EURUSD units and their scalper types (through the unit adapter), the London open in Europe/London, and the existing news and desk workflows to pull from.
3. **One grilling round** of at most 4 numbered questions, each with a recommended answer, where "yes" accepts all. For example:
   - (1) Include demo units as well as live? Yes.
   - (2) Stay silent if nothing changed since yesterday? Yes.
   - (3) Push only on stand-aside for a live unit? Yes.
   - (4) Also add GBPUSD? No.
4. **The copilot writes the variant into `pending/`.** It never enables it itself.
5. **Dry run.** The variant replays the last 5 London opens from `fixtures/` with the fake model plus one real cheap call. The copilot shows the preview board inline as a widget.
6. **He says yes.** The variant is enabled, and the engine creates the trigger row from his approval. A run can never create a trigger. Under the Lab standing rule in 12 (l), a Lab-scoped variant may not need the ask.
7. **Lineage.** `variant → template@1.2.0`. When the template moves to 1.3.0, a rebase card shows the diff, and he accepts or keeps the old version.
8. **Upkeep.** After 10 runs, the weekly harness review checks whether he opened the read. If he never did, it proposes disabling it as a lesson. It never deletes; the variant is archived.

### 3.3 Other clone examples

| Variant | Base | What changes |
|---|---|---|
| NY-open gold scalper read | T2 | `session: new_york`, `instruments: [XAUUSD]`, the event table includes US data at 08:30 ET |
| USD-only desk for Sunday night | T4 | Watchlist = USD pairs; beats (a), (b) and (e) only; trigger Sunday 21:00 |
| Prop account kill-line watchdog | R1 | Prop rule table (daily limit from start-of-day equity at server midnight, trailing drawdown); amber at 40% (stricter only) |
| Breakout-units decay watch | R3 | Unit filter by scalper type; tighter CUSUM h (stricter only) |
| "Run it once now" | Any | No folder. The copilot runs the template ad hoc with parameters in mode C and saves nothing unless he says "keep this". |

---

## 4. Shared building blocks

### 4.1 Unit adapter (keeps the templates loose)

- Templates ask for **named facts**, never fields: `unit.id`, `unit.stage`, `unit.instruments`, `unit.sessions`, `unit.scalper_type`, `unit.condition_needs[]`, `unit.mis_answer(session)`, `unit.journal_R()`, `unit.backtest_baseline()`, `unit.current_r`, `unit.signed_profile`, `unit.profile_versions()`, `unit.lineage`, `unit.content_hash`.
- The adapter maps these onto whatever structure the risk session settles. A fact the unit does not have yet returns `unknown`, and templates render "could not check". They never guess.
- The adapter is read-only. The only write is `unit.tighten(action)`, which goes through 4.6.

### 4.2 Read-only account and guard reader

- One script library, used by T1, T10, R1, R2, R5 and R6. It reads equity, positions, stops, the guard state, the guard config hash and the prop-firm rule table.
- It has no write path. The money hook blocks anything else.

### 4.3 R-journal statistics library

- Expectancy with a bootstrap CI.
- The Monte Carlo band from the backtest.
- CUSUM, binomial and Poisson tests.
- MAE/MFE and exit efficiency.
- Slice stats with the significance filter.
- Effective number of bets.

T5, T7, R2, R3 and R6 all share it, so one number means the same thing everywhere.

### 4.4 Cost model and trial ledger

- **The cost model is written by T9 and versioned.** R4, backtests and R5 read it, so backtests use live costs rather than guesses.
- **The trial ledger counts every variant in a lineage family**, dead ones included. It feeds the deflated Sharpe and PBO in R4.

### 4.5 Graders and rules shared across templates

| Block | Rule |
|---|---|
| `number-trace` | Every number in the output JSON resolves to a script output row. |
| `cut-rules` | No source means no claim, and the analyst is named. A single-analyst flag is cut unless it is in the exception list. The same rules apply to any multi-analyst template. |
| `label-check` | Every factual claim is labelled retrieved, remembered or inferred. A forecast number carries a range meant to hold 9 times in 10, plus "what would push it outside". |
| `refusal-ok` | "Could not check: <what>, <why>" is a valid output. A filler section is a grader failure. |
| `significance` | No slice is reported with n < 20, or with a CI that overlaps the overall mean. |
| `hash-bind` | Gate verdicts are stored against the unit's content hash. A changed hash makes the verdict stale. |

### 4.6 Tighten-only interface and direction table

- `tighten(action)` accepts only these actions: `shrink_r(to ≤ current)`, `bench`, `back_to_demo`, `block_session`, `lower_max_trades`, `lower_max_spread`.
- The **direction table** says, per parameter, which way is tighter. It is shared by the node (prevention at write time) and R6 (detection afterwards).
- Who may call `tighten` automatically, and on which stage, is set in the autonomy table (Q2).

### 4.7 Decision card and notification router

- **Decision card**: recommendation, default, consequence of silence, expiry, evidence links, and a "door type" (one-way or two-way).
- **Router by severity**:

| Severity | Where it goes |
|---|---|
| Info | Digest only. |
| Normal | Inbox. |
| Red | Inbox plus phone push. |
| Black | Push, repeated every 10 min until acknowledged. Used for guard missing, a config hash mismatch, an R6 violation, or a watchdog down. |

- One message per incident, not one per retry. Quiet success is `[SILENT]`, kept for audit.

### 4.8 Model roles (set in Settings, never in the template)

| Role | Used for | Default floor |
|---|---|---|
| `scanner` | One-line notes, triage | Cheap, but at or above the floor tier he sets. The clipping showed the cheapest tier failing. |
| `writer` | Briefs, verdicts, cards as JSON | Cheap to mid. |
| `analyst` | Beats, explanations, lessons | Mid. |
| `coordinator` | Desk synthesis | Strong. |
| `researcher` | Video and paper understanding, `rlm` | Mid to strong. |
| `builder` | Lab code | Strong. |
| `validator` | R7, R8 challenge | Strong, **different family from the builder**. |
| `judge` | Rubric scoring | Cheap, different from the author. |
| `doctor` | Run triage | Cheap first. |

A variant may override a role for itself. The family rule for `validator` is checked by a rule node, not trusted.

### 4.9 Budget classes

| Class | Meaning | When the cap is closed |
|---|---|---|
| B0 | Scripts and rules only | Never paused. |
| B1 | At most 1 cheap call, about 8k tokens | The script-only fallback is delivered. |
| B2 | At most 3 calls, about 40k tokens | Drain, park, resume after the reset. |
| B3 | Agent fan-out, at most 6 children, 10 calls each, about 300k tokens | Same as B2. Partial results are kept. |
| B4 | Heavy agent or Lab work, with his per-run cap | Same as B2. A pre-flight estimate is shown first. |

- All classes use admission control before each model step, and reserve-then-refund per run (11 §2).
- A 429 marks the step "waiting", not failed.

### 4.10 Failure policies and the run doctor

Policies:
- `fail_fast` for data or engine errors in gates.
- `continue` for per-unit and per-scenario fan-outs.
- `escalate` (the default) parks the run in the inbox.

The ladder (13 §4):
1. Retry transient errors.
2. The doctor repairs locally (bigger model, more turns, cleaned input) and replays only the remaining steps.
3. Escalate.

Further rules:
- Finished paid steps never rerun.
- A watchdog failure is itself an incident.
- The engine watchdog checks the last tick of R1, R6 and T5 (watching the watchers).

### 4.11 Memory scopes used here

| Scope | Holds |
|---|---|
| `run` | Working state. |
| `workflow` | Last output (`continuity`), cost model, scenario library, surprise history. |
| `home` | Lab negative results and the trial ledger. |
| `operator` | Lessons table, rejected lessons, sections he ignores. |

Rules: one writer per scope, size caps that raise an error rather than truncate, and lessons as tagged rows.

### 4.12 Output kinds (JSON, rendered by QMX templates)

`dashboard_card`, `session_board`, `calendar_strip`, `ranked_brief`, `unit_tile`, `scorecard` / `funnel_scorecard`, `explainer`, `heatmap`, `gauge`, `rag_list`, `validation_report`, `decision_card`, `alert`, `check_row`.

Every kind carries run chrome: template, version, trigger, models per step, cost, grader results, and a freshness stamp. Click any number to see its source.

### 4.13 Time

- Everything is stored in UTC.
- Sessions are defined in the market's own timezone (Tokyo, Europe/London, America/New_York), DST-aware.
- The broker server timezone is recorded per account, because daily loss limits often reset at server midnight.

---

## 5. Open questions (each with a recommended answer)

| # | Question | Recommended answer |
|---|---|---|
| Q1 | After he signs "start demo trial", may a **script** (not an agent) upload the unit to a **demo** node? | **Yes for demo only.** A script executes his signed card with an idempotency key. Live is always his own click in the node UI. |
| Q2 | May workflows apply tightening actions (bench, shrink, back to demo) without asking? | **Demo: yes, automatically. Live: a decision card whose default is "apply at next session open"**, unless he sets a standing allow rule. The unit's own recipe tightening is unaffected. An R6 violation on live reverts to the last signed profile **automatically**, because that only restores what he signed. |
| Q3 | Is stepping up a size ramp that he already signed a "loosening"? | **No, if it stays within the signed schedule and ranges.** Changing a range, skipping a ramp step, or ramping while R3 is amber or red counts as loosening and needs his signature. |
| Q4 | Can he override an R7 reject? | **Yes, with a written reason.** The unit carries an "override" badge, gets stricter R3 thresholds, and needs a second-family review before any size increase. |
| Q5 | How much demo evidence is enough for a scalper? | **At least 2 weeks and at least 100 trades** for scalpers (08's 30 trades suits swing units), plus results inside the Monte Carlo band. A borderline result gets one re-demo. |
| Q6 | Which free calendar and news sources? (His ruling: free news only.) | **Official central-bank and statistics-agency feeds plus one free aggregator calendar, cross-checked against each other.** Respect each site's terms. A source-disagreement row in T3 opens an incident. |
| Q7 | For T2, is the node's MIS or the script mirror the truth? | **The node's MIS is the authority.** The mirror exists for Lab and demo units not yet on a node, and as a check; a mismatch opens an incident. |
| Q8 | If only Claude is configured, can R7 still pass a unit? | **A same-family review may pass demo promotion but not live.** Live needs a reviewer from another family (a key provider in Settings), or his explicit override (Q4). |
| Q9 | Deflated Sharpe threshold: "above 0" (12, 08) or a probability? | **Use the probability form, at least 0.95**, and show the haircut Sharpe next to it. "Above 0" reads too loose for a multiple-testing gate. |
| Q10 | Show R or $ first? | **R first, $ second, everywhere.** The journal is in R, and R compares units of different sizes. |
| Q11 | Where do prop-firm rules live? | **One rule table per account inside the guard config.** R1, R5, T3 and T6 read it, and agents never write it. He edits it in Settings. |
| Q12 | What makes an incident big enough for R8? | **Any black alert, a kill-switch or guard trip, an R6 violation, slippage beyond the stop greater than 0.5R, or a watchdog outage longer than 2 min with open risk.** Smaller items go to the digest. |
| Q13 | Should the RLM kernel be used here? | **Off by default.** The first use is R5 stress-window discovery over the tick archive, in the research sandbox only, never near live paths. |
| Q14 | Default thresholds for R1, R3 and T9 as given? | **Ship them as editable defaults.** Revisit after 4 weeks of demo data. Every change is versioned and shown in run chrome. |
| Q15 | Should T4's watchlist include crypto perps and indices, or FX only? | **Start with FX majors plus XAUUSD.** Add others by cloning a variant, since the venue list is still open (09 §3.11). |
| Q16 | Who keeps the `scalper-types` conditions table: Settings or the Lab? | **The Lab owns it as a versioned table.** T2 reads it, he edits it in the UI, and later units may carry their own copy (09 §3.8). |
