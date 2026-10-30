# 20: What self-configuring trading systems read and change

Research date: 2026-10-30. Group A. Ticket: `wayfinder/tickets/research-self-configuring-systems.md`.

**CHECKED — method and scope.** Web access worked. The vendor pages below were checked during this run. The standing orders, STATE, both named tickets and the operator's own turns in both named verbatim transcripts were read. The research skill was read; its primary-source method was used. Poteto-mode was absent from the harness skill catalogue. This is a research comparison, with no selected formula, architecture, code change or trading action. Local references below use the path aliases in §7.

## 1. The answer

**INFERRED — three different meanings are being called self-configuration.** A system can (a) recalculate an order from a balance and a fixed rule, (b) update the rule's statistical inputs from completed observations, or (c) change the trading policy itself. Freqtrade's balance sizing and Jesse's risk-to-quantity helper demonstrate (a). The Kelly example demonstrates (b). None of those mechanisms, by itself, demonstrates a system discovering better sessions, stops and risk rules together. Sources: M1–M4, F1–F2, J1, K1 below.

**CHECKED — the QMX boundary remains open.** STATE puts risk and sizing inside the complete unit, reserves live promotion to the operator, and leaves grow-back and house money undecided. The handoff asks for the moving numbers, journal inputs, update rule, frequency and limits to be shown concretely. The operator later asks how the same capital can serve a changing number of units; that is a seed, not an agreed allocation formula. Sources: `P/STATE.md:21-25, 39-40, 75-78, 92-93`; `P/HANDOFF-RISK-SIZING.md:23-43`; `P/operator/transcript-2026-10-29-to-30.md:215-216`.

**CHECKED — the old July Kelly term was deliberately unfinished.** Its outer rule said to take the smaller of a book offer and a trust-bounded, cost-aware Kelly amount. It did not supply the implementation of that Kelly amount. Later QMX records explicitly retired both legacy sizing systems. Historical recovery therefore supplies options and missing questions, not a ready sizing module to reconnect. Sources: Q4, Q5, Q6 below.

## 2. Six examples: inputs, changes, limits and human control

**Reading the table.** CHECKED means the named document or code contains the behaviour; it does not mean the system was run here. INFERRED marks the interpretation of its human boundary. Vendor limits are reported as vendor behaviour, not proposed QMX caps.

| System and evidence status | What it reads | What it changes automatically | Limits and what it does not establish | Where a human acts |
|---|---|---|---|---|
| **MT5 Wizard money modules. CHECKED: shipped standard-library interfaces** [M1–M4]. | FixedRisk documents estimated entry, stop price and a configured `Percent`. SizeOptimized additionally uses previous deals; `DecreaseFactor` responds to consecutive losses. | Order volume. FixedLot, FixedMargin, FixedRisk and SizeOptimized are distinct choices under `CExpertMoney`. | A predefined percentage or margin rule is not an estimated edge. Money methods do not document learning sessions or selecting a stop. The reference alone does not settle the exact balance/equity basis of each concrete implementation. | **INFERRED:** author/operator selects the module and parameters before enabling the EA. These money interfaces show no per-resize approval step. That is not evidence of a QMX-style promotion gate. |
| **Freqtrade. CHECKED: documented balance allocation and callbacks** [F1–F2]. | Available balance, permitted trade slots; callback gets pair, time, price, proposed/min/max stake, leverage and tag. Custom logic can read analysed candles and wallet data. | Entry stake; separate callbacks can change stops or adjust an existing position. | Dynamic stake divides capital across remaining slots. Separate bots can receive `available_capital`; changes require configuration reload. Stake is capital committed, not cash loss at a stop. A callback exception falls back to proposed stake; out-of-range values are clamped; zero/None skips entry. | **INFERRED:** a person supplies the strategy, allocation and operating mode. The callback runs automatically, without a documented approval for every stake calculation. It does not decide QMX's live-admission policy. |
| **Jesse. CHECKED: documented sizing utilities, not an autonomous calibrator** [J1–J2]. | `risk_to_qty`: capital, risk percentage, entry, stop, precision and fee rate. Capital may come from current balance. A separate Kelly helper accepts win rate and payoff ratio. | Quantity returned to the strategy; the strategy supplies orders and stops. | Tight stops can produce unaffordable quantities; the docs warn about insufficient capital. The helper does not estimate its own risk percentage or Kelly inputs. Precision and fee assumptions matter. | **INFERRED:** author supplies the policy and launches trading. No per-calculation approval is shown in these helpers. Choosing a new policy is outside the helper. |
| **Adaptive/fractional Kelly, QuantConnect example. CHECKED: published code, not verified live** [K1]. | Hypothetical signal outcomes, window and scaling factor. | Portfolio weight after sufficient samples. | Unit-size outcomes; fees omitted; parameters historically tuned. Displayed snippet has a sign defect (§3). | **INFERRED:** author sets policy; code resizes without a documented recurring approval. |
| **Old enhanced Kelly plus house money. CHECKED: April/May QMX specification and recorded decisions; implementation gaps recorded** [Q1–Q3]. | Win rate, fee-adjusted wins/losses, equity, open risk, daily losses, slot P&L, session, market conditions and correlation; broker stop distance and value/lot facts for conversion. | Candidate risk, final cash risk and lots; context and loss-streak multipliers; house-money boost. | Half-Kelly, nine multipliers and a six-operand clamp are historical rules. The known-gaps file reports missing ceilings, unadjusted recomputation and duplicated multipliers. House-money ownership conflicts: April decision says bot; later spec says slot. | **CHECKED:** the lifecycle spec requires manual approval for paper-to-live, but also contains automatic probation and reinstatement transitions. Those older transitions cannot override today's operator-only promotion ruling. [Q7; `P/STATE.md:39`]. |
| **July trust-bounded, cost-aware Kelly. CHECKED: documentary outer rule; missing inner estimator** [Q4–Q5]. | Book equity and kill line, budget divisor, stop-out/shaping inputs, measured mean loss; cost/edge input to viability; an unspecified trust-bounded Kelly amount. | Offer and take per seat, and rollover-derived daily budget, if all inputs exist. | No checked implementation of the trust bound or Kelly estimator was found. Some old expressions were later replaced for dimensional reasons; do not reuse their dollar/R names as if validated. [Q6; Q8]. | **CHECKED historical boundary:** July core limits human authority to resurrection and committee review. **CHECKED current boundary:** STATE supersedes that with operator-only live promotion. A missing Kelly input is not evidence of permission to substitute one. |

## 3. What the examples actually prove

**CHECKED — MT5 offers a small money interface.** `CExpertMoney` supplies percentage and open-volume methods. FixedRisk is a fixed-risk implementation; FixedMargin is a different margin-based implementation. SizeOptimized reduces volume after consecutive losing deals. **INFERRED:** this is a useful precedent for keeping the external interface small, but it does not establish that its parameters are statistically self-calibrated. Sources: [M1](https://www.mql5.com/en/docs/standardlibrary/expertclasses/expertbaseclasses/cexpertmoney), [M2](https://www.mql5.com/en/docs/standardlibrary/expertclasses/samplemmclasses/cmoneyfixedrisk/cmoneyfixedriskcheckopenlong), [M3](https://www.mql5.com/en/docs/standardlibrary/expertclasses/samplemmclasses/cmoneysizeoptimized/cmoneysizeoptimizeddecreasefactor), [M4](https://www.mql5.com/en/docs/standardlibrary/expertclasses/samplemmclasses/cmoneyfixedmargin).

**INFERRED — balance compounding is not edge learning.** A larger balance can produce a larger stake while the risk percentage remains unchanged. Neither that result nor a loss-streak reduction proves the next trade is better or worse. This distinction follows from the inputs in F1, J1 and M3, not from a claim about their profitability.

**INFERRED — the displayed Kelly snippet has an arithmetic defect.** It divides mean wins by negative mean losses. Equal-magnitude outcomes at a 50% win rate therefore give a full-Kelly value of 1 rather than 0. This finding concerns the displayed snippet; the attached executable backtest was not retrieved or run. Source: [K1, Implementation](https://www.quantconnect.com/research/18312/kelly-criterion-applications-in-trading-systems/p1).

**CHECKED — academic alternatives make their assumptions explicit.** Busseti, Ryu and Boyd constrain the probability of wealth falling below a specified fraction of starting wealth, using a tractable bound. Sun and Boyd instead optimise against an uncertainty set of possible outcome distributions. Both provide code links. **INFERRED:** these supply distinct meanings for “bounded” or “trust”; neither is evidence that July QMX selected that meaning. No optimiser or trading simulation was run here. Sources: [Risk-Constrained Kelly Gambling](https://web.stanford.edu/~boyd/papers/kelly.html), [Distributional Robust Kelly Gambling](https://stanford.edu/~boyd/papers/robust_kelly.html).

## 4. Old QMX: recover the mechanism without endorsing it

**CHECKED — the April/May sequence was explicit.** Its request carried performance, account and context inputs. It computed a fee-adjusted payoff ratio, a half-Kelly base, a multiplier product, a minimum across risk ceilings, then a lot conversion using the original stop. It retained the candidate value and binding ceiling for audit. Sources: `V/02-Components/01-risk-and-sizing/01-canonical-formula.md:19-57, 63-121, 141-159`.

**CHECKED — “self-configuring” covered different scopes even then.** House money increased the slot's multiplier after a P&L threshold; reverse house money reduced sizing after losses in ORB-dominant windows; session modifiers came from a registry. None of those paragraphs defines an algorithm for learning the threshold or session modifier. Source: `V/02-Components/01-risk-and-sizing/02-multiplier-stack.md:56-88, 191-215`.

**CHECKED — two records conflict on ownership.** The April brainstorm's D1 uses realised paper statistics rather than planned reward/risk. Its D3 makes house money bot-scoped and resets it on swap. The later session specification makes house money slot-scoped and inherited by an incoming bot. These are different policies; this run does not pick one. Sources: `V/bmad-docs/brainstorming/brainstorming-session-2026-04-28-125147.md:103-114`; `V/02-Components/01-risk-and-sizing/05-session-architecture.md:90-112`; multiplier source above:73-86.

**INFERRED — two old assertions need mathematical review, not automatic inheritance.** A payoff ratio below the old 1.1 threshold does not alone prove negative expectancy: win probability matters too. Also, increasing exposure after profit does not alone guarantee preservation of starting equity. The old lot pseudocode clamps upward to broker minimum; when the affordable quantity is smaller, that can exceed the calculated risk. These observations follow from the old expressions, not a proposal for replacement maths. Sources: canonical formula:65-83, 143-156; multiplier stack:75-88. The threshold and multipliers are editable historical values, not universal facts.

**CHECKED — July changed the relationship, but left the hard part blank.** Its offer/take expression put a shared budget beside a unit-specific risk answer. The recovered formula explicitly leaves Kelly implementation to bot/book validation; the later recovery says not to fill it with generic Kelly. The current source file validates declared sizing units and value relationships and explicitly describes itself as defined but unwired, rather than an evaluator of live sizing. Sources: Q4, Q5, Q8.

**CHECKED — later retirement matters.** The August PRD reconciliation lists both the nine-multiplier half-Kelly system and trust-bounded cost-aware Kelly among retired formulas. Current STATE nevertheless asks to combine the best of the older and newer ideas in a separate risk session. **INFERRED:** researching those older ideas is authorised; declaring them current QMX policy is not. Sources: Q6; `P/STATE.md:92-93`; `P/HANDOFF-RISK-SIZING.md:23-36`.

## 5. Options and questions the comparison leaves open

**INFERRED — these are separable choices, not a proposed module boundary.** Each row names an option that changes the unit, its journal, the shared budget or the broker-data dependency. No row is selected.

| Question | Evidence-backed options | What it touches |
|---|---|---|
| What automatically changes? | Quantity under a fixed percentage (M2/J1); capital committed under a fixed allocation rule (F1); an estimated sizing input (K1); a policy such as session eligibility, which these examples do not establish how to learn. | Unit behaviour and its evidence record. |
| What does “capital available” mean? | Actual account balance; a separately assigned strategy capital amount (F1); or a shared-budget offer alongside the unit's own answer (Q4). Allocated capital, margin, notional and stop-loss risk are different quantities. | Account/pod bookkeeping and broker facts. |
| Which performance is read? | Realised paper statistics (Q3); realised live statistics; normalised hypothetical signal outcomes (K1); separately identified backtest/stress observations. Their costs and selection histories differ. | Unit journal and QMB/node provenance. |
| What is a trust bound? | A chosen fraction; uncertainty in estimated outcomes; a drawdown-probability condition; agreement with a frozen exam baseline. These are different questions, with different inputs. | Risk maths and baseline evidence. |
| Which session/stop changes are authorised? | Execute already declared rules; propose a changed policy for review; or a wider adaptation policy whose allowed changes still need discussion. | Unit identity, admission scope and journal. |
| What happens when data is missing? | Vendor fallback (F2), explicit skip, or a declared local fallback. A remote journal or market service cannot silently become essential to independent trading. | Local unit state and data availability; `P/STATE.md:64-73`; `P/STANDING-ORDERS.md:15-17`. |

**CHECKED — existing funnel numbers are proposals.** Research 07 suggests scheduled calibration of risk, loss points and session weights, plus fixed/only-shrink/grow-back alternatives. Research 08 proposes a nightly informational decay check, separate from fast loss rules. STATE leaves the relevant risk decisions open. **INFERRED:** neither the fortnight schedule nor a decay alarm is already authority to change session access, widen stops or return to live. Sources: `P/research/07-funnel.md:252-275, 384-395`; `P/research/08-old-qmx-testing-and-decay.md:283-317`; `P/STATE.md:39-40, 78, 92-93`.

### Editable starting values for a later walkthrough

**INFERRED — research fixtures only.** These values make alternatives comparable in a later prototype. They are editable starting defaults, not approved live risk settings, hard caps, required pass marks or chosen formulas.

| Named setting | Editable starting default | Why it is present |
|---|---|---|
| Example starting capital | USD 300 | The handoff requests a small-account explanation; not a claim that every instrument is affordable. |
| Fixed-risk comparison percentage | 0.5% | An illustrative input to the fixed-percentage option; cash risk starts at USD 1.50 before instrument/cost feasibility. |
| Fractional-Kelly comparison factor | 0.25 | A comparison case alongside 0.5 and 1; not an estimate of safe risk. The fraction does not repair bad edge estimates. |
| Rolling estimator comparison sample | 40 eligible completed outcomes | Reproduces K1's sample length only; editable. Keep the full record available; this is not a history or lookback cap. |
| Recalculation event | After an eligible outcome closes | Shows what new observation changes the calculation; scheduled/batched updating remains another option. |
| House-money comparison multiplier | 1.0, with a separate historical 1.5 case | Neutral starting comparison; 1.5 is the old slot booster, not a selected policy. |
| Missing July Kelly term | Explicitly unresolved; no guessed amount | Its estimator and trust definition were not recovered. A blank cannot demonstrate usable live sizing. |

**INFERRED — a concrete explanation can be short without choosing a formula.** Hold the percentage at 0.5% and change the illustrative balance from USD 300 to USD 330: the fixed-rule cash-risk calculation changes from USD 1.50 to USD 1.65. No improved edge has been learned. In a separate trial, hold balance fixed and change the completed-outcome sample: only an estimator-based option changes its edge input. Stop distance, fees and instrument value then determine whether either cash amount can produce a permissible order. This is arithmetic showing two different mechanisms, not a trading recommendation. Sources for the mechanisms: M2, J1, K1.

## 6. Limits of this research

**CHECKED — evidence boundary.** This run inspected documents and source code, not an installed MT5 library, a live vendor bot, a funded QMX account or the lost pre-crash implementation. No price data was downloaded, no Dukascopy request was made, and no money or credential operation was performed. QuantConnect's displayed snippet was checked, not its attached executable backtest. Vendor behaviour is not evidence of profitability.

**CHECKED — unavailable primary page.** Attempts to open the old GitBook formula and book-template URLs, with and without `.md`, failed. July conclusions use the local verbatim formula capture plus dated QMX recovery records, explicitly identified as such, rather than claiming a fresh live-page verification. No original trust-bound implementation was found in the checked material.

## 7. Sources and paths

Path aliases: `P = D:/QMX-worktrees/unit-plan/tracker/risk-sizing`; `R = D:/QMX-worktrees/unit-plan`; `V = C:/Users/Mubarak/Documents/Claude/QMX-discussion`. Local line references refer to files read on the research date. Earlier research reports were navigation aids; primary documents/code were followed where conclusions depend on them.

Vendor and academic sources, CHECKED on 2026-10-30:

- **M1:** [MetaQuotes: CExpertMoney](https://www.mql5.com/en/docs/standardlibrary/expertclasses/expertbaseclasses/cexpertmoney), base interface and descendants.
- **M2:** [MetaQuotes: FixedRisk open volume](https://www.mql5.com/en/docs/standardlibrary/expertclasses/samplemmclasses/cmoneyfixedrisk/cmoneyfixedriskcheckopenlong), parameters and risk definition.
- **M3:** [MetaQuotes: SizeOptimized](https://www.mql5.com/en/docs/standardlibrary/expertclasses/samplemmclasses/cmoneysizeoptimized) and [DecreaseFactor](https://www.mql5.com/en/docs/standardlibrary/expertclasses/samplemmclasses/cmoneysizeoptimized/cmoneysizeoptimizeddecreasefactor).
- **M4:** [MetaQuotes: FixedMargin](https://www.mql5.com/en/docs/standardlibrary/expertclasses/samplemmclasses/cmoneyfixedmargin).
- **F1:** [Freqtrade configuration](https://www.freqtrade.io/en/stable/configuration/#configuring-amount-per-trade), sections Tradable balance, Assign available Capital and Dynamic stake amount.
- **F2:** [Freqtrade callbacks](https://www.freqtrade.io/en/stable/strategy-callbacks/#stake-size-management), sections Stake size management, Custom stoploss and Adjust trade position.
- **J1:** [Jesse utilities](https://docs.jesse.trade/docs/utils#risk_to_qty), risk-to-quantity and Kelly utility definitions.
- **J2:** [Jesse strategy API](https://docs.jesse.trade/docs/strategies/api#fee_rate), fee-rate input.
- **K1:** [QuantConnect: Kelly Criterion Applications in Trading Systems](https://www.quantconnect.com/research/18312/kelly-criterion-applications-in-trading-systems/p1), Implementation and Results. Published example, not an independently verified live record.
- **K2:** [Busseti, Ryu and Boyd, 2016](https://web.stanford.edu/~boyd/papers/kelly.html), author-hosted paper and code links.
- **K3:** [Sun and Boyd, 2018](https://stanford.edu/~boyd/papers/robust_kelly.html), author-hosted paper and code links.

Local sources, CHECKED:

- **Q1:** `V/02-Components/01-risk-and-sizing/01-canonical-formula.md:19-57, 63-159`; `02-multiplier-stack.md:19-31, 56-88, 191-215` in the same folder.
- **Q2:** `V/02-Components/01-risk-and-sizing/07-known-gaps.md:21-120`. Records historical implementation gaps; this run did not reproduce the old audit.
- **Q3:** `V/bmad-docs/brainstorming/brainstorming-session-2026-04-28-125147.md:103-125, 159-161`.
- **Q4:** `R/_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-08-19/research-risk/extract-gitbook-capture.md:349-395`, verbatim formula registry capture; `R/archive/recovery/trading-node-delta/work/gitbook-baseline.md:112-142`, source URLs, historical values and units.
- **Q5:** `R/archive/recovery/trading-node-delta/trading-node-delta.md:79-90`, especially K-37; `V/.brain/entities/qmx-new-core.md:18-24, 28-67`, dated July authority, treasury and sizing description.
- **Q6:** `R/_bmad-output/planning-artifacts/prds/prd-QMX-2026-08-21/correlate.md:167-175`, superseded formulas and identifier warning.
- **Q7:** `V/02-Components/07-bot-registry-and-lifecycle.md:125-140`, historical transitions.
- **Q8:** `R/packages/qmf-risk/src/qmf/risk/sizing.py:1-34, 95-105, 140-175`, present unit checks, separate loss-count/budget variables and explicit absence of runtime sizing evaluation.

**CHECKED — bounded search record.** `rg --files` located sizing and formula sources. Targeted `rg -n -i 'trust.bounded|cost.aware.kelly|kelly.*trust|trust.*kelly'` over current docs, planning artifacts and workroom led to Q4–Q6 and Q8. These searches establish what was found in the checked tree, not the absence of an implementation on every old disk or branch. The old Hermes stores and credential files were not opened.
