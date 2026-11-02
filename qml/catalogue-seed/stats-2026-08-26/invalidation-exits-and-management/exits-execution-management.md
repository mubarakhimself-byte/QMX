# Candidate primitives — invalidation, exit, execution, and management

| Family | Entries |
|---|---:|
| Invalidation and reference distinctions | 8 |
| Exit events, orders, and management | 17 |
| Entry order and timing semantics | 12 |
| Pending-order lifecycle and re-entry | 10 |
| Source-native sizing/risk concepts | 5 |
| Market-structure and execution-transfer constraints | 5 |
| **Total** | **57** |

## level-invalidation — Level invalidation

- **Family:** Invalidation and reference distinctions
- **Aliases:** invalidated level; broken level; failed level
- **Definition:** An event or condition that makes a previously relevant price reference no longer eligible for the use assigned in a strategy.
- **Boundaries:** Not necessarily a trade exit, stop order, or proof that price will reverse; it concerns validity of a reference, not necessarily an open position.
- **Observable inputs:** Defined level or zone; bid/ask, last-trade, or bar prices; optional time and session data.
- **Recognition semantics:** Evaluate the source-specified breach, close, acceptance, or elapsed-time condition against the level's construction and price basis. Record whether the level is merely demoted, deleted, or replaced.
- **Parameters/profiles:** breach rule, price basis, bar timeframe, confirmation requirement, and lifecycle action — all `source-stated` or `unresolved`.
- **Eligible roles:** invalidation; filter; signal cancellation; management input.
- **Market/data constraints:** A spot-FX chart's displayed bid, mid, or broker feed can disagree with an executable side; the price basis is intrinsic.
- **Transfer notes:** Portable in concept. A futures last-trade breach and a crypto-exchange last-trade breach should not be treated as an OTC-FX executable-quote breach without an explicit transfer assumption.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Close beyond,” “wick through,” and “acceptance beyond” are distinct variants rather than interchangeable wording.

## setup-invalidation — Setup/thesis invalidation

- **Family:** Invalidation and reference distinctions
- **Aliases:** trade thesis invalidation; setup failure; premise failure
- **Definition:** A condition under which the complete pre-entry or post-entry setup no longer justifies the intended trade.
- **Boundaries:** Broader than level invalidation because it can depend on timing, regime, structure, or a missing prerequisite; distinct from an actual protective exit order.
- **Observable inputs:** All setup prerequisites, their timestamps, market state, and relevant price/derived signals.
- **Recognition semantics:** Maintain the setup's required propositions. Invalidate when a source-defined hard prerequisite fails, a mutually exclusive state occurs, or the setup's permissible time window ends.
- **Parameters/profiles:** prerequisite set, hard-versus-soft status, evaluation cadence, and invalidation action — all `source-stated` or `unresolved`.
- **Eligible roles:** invalidation; signal cancellation; pending-order cancellation; exit trigger.
- **Market/data constraints:** Requires a stateful record of which conditions were satisfied and when; a static chart pattern alone may be insufficient.
- **Transfer notes:** Portable, but a futures-source premise based on centralized order-book behavior needs separate evidence before use on spot FX or another crypto venue.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** A failed setup can be a cancellation before entry, an exit trigger after entry, or only an alert; the binding must say which.

## signal-cancellation — Armed signal cancellation

- **Family:** Invalidation and reference distinctions
- **Aliases:** disarm; signal revoke; cancel signal
- **Definition:** Withdrawal of an actionable but unfilled entry signal before an entry order fills.
- **Boundaries:** Not an exit because there is no position; not ordinary order cancellation unless an actual pending order exists.
- **Observable inputs:** Signal state, pending-order state if any, cancellation condition, and clock/session state.
- **Recognition semantics:** After a signal arms, test named cancellation conditions until fill, expiry, or manual/source-defined cancellation. If met, mark the signal unusable and cancel linked orders where supported.
- **Parameters/profiles:** cancellation conditions, linkage to order identifiers, and reset policy — all `source-stated` or `unresolved`.
- **Eligible roles:** signal cancellation; entry lifecycle; risk control.
- **Market/data constraints:** Needs an unambiguous distinction between signal issuance, order acknowledgement, fill, and position creation.
- **Transfer notes:** In OTC FX, an order may be held by a broker/dealer; in CLOB markets it may be resting at an exchange. Cancellation acknowledgement is venue-specific.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Cancel on opposite signal” may mean cancel only, reverse, or enter only after flat; retain the original wording.

## stop-reference — Protective-stop reference

- **Family:** Invalidation and reference distinctions
- **Aliases:** stop level; stop placement reference; protective threshold
- **Definition:** A calculated or identified price reference intended to bound a trade's adverse excursion or express its invalidation point.
- **Boundaries:** It is a reference, not proof that a stop order exists, is accepted, or will fill at that price. It may be managed manually or used only for source-native sizing.
- **Observable inputs:** Entry reference, structural/volatility/fixed rule inputs, executable price side, and current position direction.
- **Recognition semantics:** Produce a directional threshold according to a stated rule, then separately bind it to an order, alert, exit trigger, or sizing calculation if the source specifies one.
- **Parameters/profiles:** reference construction, price side, update policy, and relation to entry — all `source-stated` or `unresolved`.
- **Eligible roles:** invalidation; sizing input; management input; exit trigger reference.
- **Market/data constraints:** A long-position stop commonly depends on a sellable/bid-side condition, but dealer/platform trigger conventions must be recorded rather than assumed.
- **Transfer notes:** Portable conceptually; guaranteed-stop products, exchange-native stops, and simulated platform stops are materially different implementations.
- **Evidence/status:** SEC explanation distinguishes stop price (trigger) from execution price: https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15
- **Uncertainty/variants:** A stop reference can intentionally differ from setup invalidation, for example when a source tolerates a level breach but caps loss earlier.

## protective-stop-order — Protective stop order

- **Family:** Invalidation and reference distinctions
- **Aliases:** stop-loss order; protective order
- **Definition:** An executable order or broker-side instruction intended to reduce or close an existing exposure after its stop condition is triggered.
- **Boundaries:** Not synonymous with a protective-stop reference; triggering does not guarantee a particular fill price or even a fill for stop-limit implementations.
- **Observable inputs:** Position size/side, stop trigger, trigger price basis, order type after trigger, order status, and execution reports.
- **Recognition semantics:** Confirm that an order is accepted, linked to the appropriate position or quantity, and has a trigger-to-order transformation defined by the venue/broker.
- **Parameters/profiles:** trigger price, trigger basis, child order type, reduce-only flag, quantity, and time-in-force — all `source-stated` or `unresolved`.
- **Eligible roles:** exit order; protection; management.
- **Market/data constraints:** Native availability and trigger basis vary. SEC notes that brokers can use last-sale or quotation prices and that a triggered stop may execute away from the stop price.
- **Transfer notes:** A CLOB/exchange stop may be native or simulated; retail OTC-FX stops are dealer/platform instructions. Verify the broker's policy before porting a source rule.
- **Evidence/status:** https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15
- **Uncertainty/variants:** Stop-market, stop-limit, trailing, and guaranteed-stop products require separate primitives/bindings.

## target-reference — Target reference

- **Family:** Invalidation and reference distinctions
- **Aliases:** take-profit level; objective; profit target; TP level
- **Definition:** A price, zone, statistic, or structural reference at which a strategy may assess, reduce, or close a favorable position.
- **Boundaries:** A target is not necessarily an exit trigger or resting limit order, and touching a target does not itself establish a fill.
- **Observable inputs:** Position direction, reference construction inputs, current executable prices, and optional reward/risk inputs.
- **Recognition semantics:** Calculate or identify the named target independent of the decision that follows. Bind subsequent action explicitly: alert, partial exit, full exit, trail activation, or no action.
- **Parameters/profiles:** target construction, target sequence, price basis, and action on touch — all `source-stated` or `unresolved`.
- **Eligible roles:** target; exit trigger reference; management input; sizing input.
- **Market/data constraints:** A sell target for a long needs a bid-side executable consideration; chart last price can overstate attainable exit price.
- **Transfer notes:** A futures target may rest as a centralized limit order; OTC FX and crypto spot availability/queue position must not be inferred.
- **Evidence/status:** Coinbase documents take-profit/stop-loss as predefined exit price levels, while platform mechanics remain venue-specific: https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Uncertainty/variants:** “Liquidity target” can mean a visual objective, a mandatory exit, or a trade-management checkpoint.

## exit-trigger — Exit trigger

- **Family:** Invalidation and reference distinctions
- **Aliases:** close trigger; liquidation trigger; exit signal
- **Definition:** An event that directs a strategy to reduce or close an already-open position.
- **Boundaries:** Not the exit order itself and not necessarily a target or stop; it can be price-, time-, signal-, or session-based.
- **Observable inputs:** Position state, trigger condition, timestamps, relevant market data, and order status.
- **Recognition semantics:** Evaluate only while a position or specified remaining tranche exists. On transition to true, emit an exit instruction with a separately stated order type and quantity.
- **Parameters/profiles:** trigger condition, evaluation timing, action priority, and quantity scope — all `source-stated` or `unresolved`.
- **Eligible roles:** exit; management; emergency cancellation of opposing orders.
- **Market/data constraints:** Intrabar trigger observation does not establish the price or time at which a real order would be accepted or filled.
- **Transfer notes:** Portable. Venue-native contingent exits can automate trigger-to-order conversion; manual/bot-managed versions introduce latency and failure modes.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** A trigger can request an immediate market exit, create a limit order, or alter a stop; preserve that distinction.

## exit-order — Exit order

- **Family:** Invalidation and reference distinctions
- **Aliases:** closing order; reducing order; liquidation order
- **Definition:** A submitted executable instruction intended to reduce or close an existing position or spot inventory.
- **Boundaries:** Distinct from an exit trigger, target, and stop reference. An order submission is not a fill.
- **Observable inputs:** Position/inventory, side, quantity, order type, venue acknowledgement, fills, cancellation/rejection status.
- **Recognition semantics:** Submit an order whose quantity and side are consistent with the intended reduction; reconcile partial fills and remaining exposure before declaring the position closed.
- **Parameters/profiles:** order type, quantity, reduce-only behavior where available, price/trigger, and time-in-force — all `source-stated` or `unresolved`.
- **Eligible roles:** exit execution; management.
- **Market/data constraints:** Spot holdings cannot normally be reduced below available inventory without borrowing/margin facilities; derivatives positions may support reduce-only flags.
- **Transfer notes:** Crypto spot exits generally sell held base asset; OTC-FX and futures can close long or short positions under their respective account agreements.
- **Evidence/status:** Coinbase explains bracket/TP-SL exits and warns that execution protection is not guaranteed in high volatility: https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Uncertainty/variants:** “Close position” can mean cancel linked orders first, submit an offsetting order, or use a venue close-position function.

## bracket-oco-exit — Linked target-and-stop exit

- **Family:** Exit events, orders, and management
- **Aliases:** bracket order; OCO exit; TP/SL; one-cancels-the-other
- **Definition:** A linked pair of alternative exit instructions in which activation/fill of one side cancels or disables the other according to venue rules.
- **Boundaries:** Not merely naming both a target and stop in prose; linkage and cancellation semantics must exist or be managed explicitly.
- **Observable inputs:** Position/filled parent quantity, target and stop definitions, child-order states, cancellation acknowledgements, and fills.
- **Recognition semantics:** Activate child exits according to the parent-fill policy; when one eligible child fills or triggers, reconcile the remaining child and exposure before treating the pair as resolved.
- **Parameters/profiles:** parent activation threshold, target order form, stop order form, quantities, linkage event, and partial-fill handling — all `source-stated` or `unresolved`.
- **Eligible roles:** exit execution; management; protection.
- **Market/data constraints:** Native OCO/bracket behavior varies and partial fills can create residual-exposure cases.
- **Transfer notes:** Coinbase describes TP/SL/bracket mechanics for its markets; do not assume equivalent atomic linkage at an FX broker or another crypto exchange.
- **Evidence/status:** https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Uncertainty/variants:** Triggering versus filling is a critical cancellation point; some venues cancel on trigger, others on fill.

## fixed-price-stop — Fixed-distance protective threshold

- **Family:** Exit events, orders, and management
- **Aliases:** fixed stop; hard stop; static stop
- **Definition:** A protective-stop reference placed at a fixed price distance or fixed percentage distance from an entry or other anchor.
- **Boundaries:** Not a structural or volatility-adaptive stop; not necessarily an actual stop order.
- **Observable inputs:** Entry/anchor price, direction, defined distance, and executable price basis.
- **Recognition semantics:** Offset the anchor in the adverse direction by the source-defined distance; do not move it unless a separate management rule permits movement.
- **Parameters/profiles:** distance unit, anchor, adverse-side rule, and update prohibition/permission — all `source-stated` or `unresolved`.
- **Eligible roles:** stop reference; sizing input; exit trigger.
- **Market/data constraints:** Tick/pip precision and quote conventions determine representability.
- **Transfer notes:** Futures sources may express distance in ticks; spot FX in pips/points; crypto spot in quote currency or percentage. Convert only with explicit unit semantics.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Fixed” can mean fixed at entry or fixed from a moving anchor; the latter is a trailing rule.

## structural-stop — Structure-derived protective threshold

- **Family:** Exit events, orders, and management
- **Aliases:** swing stop; beyond-structure stop; technical stop
- **Definition:** A protective-stop reference placed relative to an identified market structure such as a swing, range boundary, pattern extremum, or level.
- **Boundaries:** Not identical to structure invalidation: a source can place a stop beyond a structure while retaining or abandoning the thesis under a different rule.
- **Observable inputs:** Structural object definition, direction, extremum/zone geometry, optional buffer, and price basis.
- **Recognition semantics:** Identify the specified structural object without hindsight, select the applicable boundary, and place the threshold on the adverse side plus any stated buffer.
- **Parameters/profiles:** structure type, lookback/confirmation definition, buffer unit, and price basis — all `source-stated` or `unresolved`.
- **Eligible roles:** stop reference; setup invalidation; sizing input.
- **Market/data constraints:** Swing detection is often retrospective; recognition must state whether confirmation delays use.
- **Transfer notes:** Portable price-structure concept. Futures order-flow structures or venue-specific liquidity maps are not automatically observable in spot FX.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** The relevant boundary may be the wick, close, zone edge, or a volatility-adjusted extension.

## volatility-stop — Volatility-derived protective threshold

- **Family:** Exit events, orders, and management
- **Aliases:** ATR stop; volatility-adjusted stop; dynamic stop distance
- **Definition:** A protective-stop reference whose distance is derived from a volatility measure rather than a fixed absolute distance.
- **Boundaries:** Not a trailing stop unless the reference is recomputed and only ratchets favorably; not a claim that volatility predicts direction.
- **Observable inputs:** OHLC/quote series, stated volatility estimator, anchor, direction, and update schedule.
- **Recognition semantics:** Compute the stated estimator on the stated data/timeframe, apply the stated multiplier or transformation, and state whether it is frozen at entry or recalculated.
- **Parameters/profiles:** estimator, lookback, multiplier, timeframe, anchor, and recalculation policy — every numerical value `source-stated`, `published-convention`, or `unresolved`.
- **Eligible roles:** stop reference; sizing input; management.
- **Market/data constraints:** Different feeds and bar construction alter ATR/range estimates; crypto's continuous trading has no universal daily close.
- **Transfer notes:** Transferable only after matching bar/session construction. Futures volatility based on regular trading hours differs from 24-hour FX/crypto series.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** ATR, realized volatility, implied volatility, and range percentiles are distinct inputs.

## time-stop — Time-based exit

- **Family:** Exit events, orders, and management
- **Aliases:** time stop; maximum holding time; timeout exit
- **Definition:** An exit trigger based on elapsed time, bar count, or a scheduled clock point rather than a price threshold.
- **Boundaries:** Not pending-order expiry, which applies before fill; not session exit unless tied to a named session boundary.
- **Observable inputs:** Fill time, bar timestamps/count, exchange/broker clock, and position state.
- **Recognition semantics:** Start the timer at the stated state transition, then emit an exit instruction when the allowed duration or endpoint is reached, regardless of unrealized P&L unless stated otherwise.
- **Parameters/profiles:** start event, duration/bar count, clock timezone, and exit order type — all values `source-stated` or `unresolved`.
- **Eligible roles:** exit trigger; management; risk control.
- **Market/data constraints:** Time zones, daylight-saving transitions, and bar-close conventions are material.
- **Transfer notes:** Futures session clocks and FX broker server clocks must not be silently substituted for crypto exchange time.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Exit after N bars” requires a definition of bar timeframe and treatment of missing/no-trade bars.

## signal-exit — Opposing or deterioration signal exit

- **Family:** Exit events, orders, and management
- **Aliases:** indicator exit; reversal-signal exit; signal-based close
- **Definition:** An exit trigger generated by a defined market signal, including a reversal, momentum deterioration, or loss of a condition.
- **Boundaries:** Not necessarily setup invalidation, and not automatically a reversal entry. It is an event acting on an open position.
- **Observable inputs:** Position state; specified indicator/pattern/structure data; evaluation timing; signal timestamps.
- **Recognition semantics:** Evaluate the named signal according to its own primitive semantics only after the position is open; when it meets the exit condition, create the stated reducing or closing instruction.
- **Parameters/profiles:** signal primitive, threshold/pattern condition, close-versus-intrabar timing, and exit quantity — all `source-stated` or `unresolved`.
- **Eligible roles:** exit trigger; management; signal cancellation for opposite pending orders.
- **Market/data constraints:** Post-entry signal delay and revision/repainting behavior must be visible.
- **Transfer notes:** Portable where inputs are price-derived; venue-specific order-flow signals need explicit transfer assumptions.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** An “opposite signal” may trigger full exit, partial exit, stop tightening, or reversal; do not normalize them together.

## session-exit — Session-boundary exit

- **Family:** Exit events, orders, and management
- **Aliases:** end-of-session exit; flatten-before-close; session close
- **Definition:** An exit trigger tied to the end, start, or transition of a named trading session or trading day.
- **Boundaries:** Not generic time stop; its semantics depend on a session calendar and a chosen definition of the boundary.
- **Observable inputs:** Position state, session calendar/timezone, broker/exchange schedule, holidays, and clocks.
- **Recognition semantics:** Map timestamps to the named session and issue the stated exit instruction at the specified boundary or lead time.
- **Parameters/profiles:** session identity, timezone/calendar, boundary/lead time, and exit order type — all values `source-stated` or `unresolved`.
- **Eligible roles:** exit trigger; management; order expiry/cancellation input.
- **Market/data constraints:** Spot FX has broker-specific daily roll/cutover; crypto spot trades continuously; futures have product exchange sessions and maintenance periods.
- **Transfer notes:** A futures “close” rule is not directly portable to continuous crypto spot or OTC FX without defining the corresponding operational session.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Do not hold overnight” can mean flatten at a clock time, before rollover, or before a market closure.

## trailing-protective-threshold — Trailing protective threshold

- **Family:** Exit events, orders, and management
- **Aliases:** trailing stop; ratcheting stop; chandelier-style trail
- **Definition:** A protective-stop reference that follows favorable price movement by a stated distance or rule while normally not loosening when price moves adversely.
- **Boundaries:** Not any dynamically recalculated stop; the directional ratchet/non-loosening property is the key distinction.
- **Observable inputs:** Current/high-water/low-water price or structural anchor, direction, distance rule, and prior threshold.
- **Recognition semantics:** Update the reference only when the candidate threshold improves protection in the favorable direction; retain the previous threshold otherwise. Bind separately to a native trailing order or managed exit instruction.
- **Parameters/profiles:** anchor, distance/estimator, update frequency, ratchet rule, trigger basis, and implementation form — all values `source-stated` or `unresolved`.
- **Eligible roles:** stop reference; management; exit trigger.
- **Market/data constraints:** Native trail features and trigger price bases differ by venue; a managed trail requires timely data and order amendments.
- **Transfer notes:** SEC describes a trailing stop as a stop/stop-limit whose threshold trails favorable price by a defined amount or percentage; broker/exchange availability remains specific. https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15
- **Evidence/status:** cited educational definition; source-specific parameters still needed.
- **Uncertainty/variants:** Price trail, ATR trail, moving-average trail, and structure trail share management intent but differ operationally.

## break-even-adjustment — Break-even protective adjustment

- **Family:** Exit events, orders, and management
- **Aliases:** move stop to BE; scratch protection; risk-free move
- **Definition:** A management operation that moves a protective threshold toward an entry-derived reference after a stated condition.
- **Boundaries:** “Break-even” is not necessarily zero realized economic loss because spread, commission, financing, fees, and fill slippage can remain. It is not a target exit.
- **Observable inputs:** Actual average fill price, current position quantity, costs if included, trigger condition, and current stop reference/order.
- **Recognition semantics:** On a stated qualifying event, amend or replace the protection threshold with the stated entry-derived reference; state whether it may later trail.
- **Parameters/profiles:** activation condition, reference basis (entry versus cost-adjusted), offset, and amendment form — all values `source-stated` or `unresolved`.
- **Eligible roles:** management; stop reference; exit trigger.
- **Market/data constraints:** Actual fill price rather than intended entry is needed for a meaningful break-even calculation.
- **Transfer notes:** Futures/crypto exchange fees and spot-FX spread/financing can make price-only break-even materially different from economic break-even.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** A “free trade” claim must identify whether it includes costs and whether residual partial position changes the reference.

## partial-exit — Partial position exit

- **Family:** Exit events, orders, and management
- **Aliases:** scale-out; trim; partial take profit
- **Definition:** An operation that reduces, but does not intend to eliminate, current exposure.
- **Boundaries:** Not partial fill, which is an execution outcome rather than an intended management operation; not a complete exit.
- **Observable inputs:** Current position quantity, desired reduction quantity/fraction, trigger, execution reports, and residual position.
- **Recognition semantics:** Submit or record a reducing instruction for the stated portion; reconcile actual fill and make subsequent stops/targets explicitly refer to remaining quantity.
- **Parameters/profiles:** reduction quantity/fraction, trigger, order type, and residual-management rule — all values `source-stated` or `unresolved`.
- **Eligible roles:** exit; management; risk reduction.
- **Market/data constraints:** Minimum order sizes, lot increments, and fees may make a stated fraction infeasible or economically different.
- **Transfer notes:** Crypto spot requires available base inventory to sell; futures supports contract increments; spot FX supports broker lot increments.
- **Evidence/status:** Coinbase describes multiple derivative TP/SL orders totaling no more than position size, illustrating venue-defined multi-level reduction mechanics: https://help.coinbase.com/en/coinbase/derivatives/bracket-orders
- **Uncertainty/variants:** Partial reduction can be percentage-of-original, percentage-of-current, or a fixed quantity; those are not interchangeable.

## exit-ladder — Multi-stage exit ladder

- **Family:** Exit events, orders, and management
- **Aliases:** scale-out ladder; multiple targets; TP1/TP2/TP3
- **Definition:** An ordered set of intended partial and/or final exits, each with a trigger/reference and allocated quantity.
- **Boundaries:** Not a single partial exit; not automatically a native linked order group.
- **Observable inputs:** Position quantity, ordered exit definitions, fills, canceled quantities, and remaining exposure.
- **Recognition semantics:** Define each rung's activation rule and quantity basis in advance; after each fill, reconcile remaining exposure and cancel/amend any quantity that now exceeds it.
- **Parameters/profiles:** rung order, trigger/reference, quantity allocation, child order type, and post-rung management — all values `source-stated` or `unresolved`.
- **Eligible roles:** exit; target; management.
- **Market/data constraints:** Native support for several linked exits differs; disconnected orders can over-close or reverse exposure if not reconciled.
- **Transfer notes:** Exchange reduce-only facilities can mitigate over-close on derivatives, but crypto spot/OTC-FX implementations require venue-specific quantity handling.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Targets may be sequential mandatory exits or independent optional liquidity points.

## target-touch-event — Target-touch event

- **Family:** Exit events, orders, and management
- **Aliases:** TP hit; objective reached; target interaction
- **Definition:** Market interaction with a defined target reference, without presuming any particular trade-management response.
- **Boundaries:** Not equivalent to a target fill, exit, or target invalidation; a chart touch can occur without executable liquidity at the desired price.
- **Observable inputs:** Target reference, specified price basis, timestamped market prices/quotes, and optional order fills.
- **Recognition semantics:** Detect the stated touch/cross/reach condition using the declared price basis, then emit the target's separately bound action if any.
- **Parameters/profiles:** touch relation, price basis, confirmation timing, and action — all `source-stated` or `unresolved`.
- **Eligible roles:** exit trigger; management input; alert.
- **Market/data constraints:** Bid/ask and last-trade differences matter, especially for spread-sensitive spot FX and thin crypto books.
- **Transfer notes:** Portable only at the semantic event level; no transfer should imply an order fill.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Tag,” “sweep,” “close through,” and “hold above/below” have different recognition rules.

## close-confirmed-exit — Close-confirmed exit

- **Family:** Exit events, orders, and management
- **Aliases:** bar-close exit; close-based liquidation
- **Definition:** An exit trigger evaluated only after a designated bar or session interval is finalized.
- **Boundaries:** Not an intrabar stop; not merely using a closing price as a reference. The order can only be submitted after confirmation unless pre-staged by other logic.
- **Observable inputs:** Final OHLC for stated timeframe, bar timestamp, position state, and subsequent order/fill data.
- **Recognition semantics:** Wait for the bar to complete, test the close-based condition, then initiate the stated exit order at the next permitted evaluation/execution moment.
- **Parameters/profiles:** timeframe, close condition, bar source/timezone, and exit order type — all `source-stated` or `unresolved`.
- **Eligible roles:** exit trigger; management.
- **Market/data constraints:** A backtest cannot honestly fill at the same bar close unless its ordering/price assumptions explicitly allow it.
- **Transfer notes:** Bar construction varies across OTC FX brokers, futures sessions, and crypto exchanges; porting requires a declared bar source.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Close confirmed” may mean candle close, daily settlement, or end-of-session mark; preserve source wording.

## intrabar-protective-exit — Intrabar protective exit

- **Family:** Exit events, orders, and management
- **Aliases:** tick exit; real-time stop; within-bar exit
- **Definition:** An exit trigger or protective mechanism evaluated during formation of a bar, rather than only after its close.
- **Boundaries:** Not synonymous with any stop order: an intrabar strategy can still submit a limit order or alert; historical OHLC alone may not identify path/order.
- **Observable inputs:** Tick, quote, or lower-timeframe sequence; trigger basis; position/order state; latency data where relevant.
- **Recognition semantics:** Observe real-time eligible events throughout the interval and execute or submit the stated exit instruction immediately upon the first qualifying state transition.
- **Parameters/profiles:** data resolution, trigger basis, latency assumption, and post-trigger order type — all `source-stated` or `unresolved`.
- **Eligible roles:** exit trigger; management; protection.
- **Market/data constraints:** OHLC bars cannot resolve whether both target and stop were reached first; tick/quote provenance is required.
- **Transfer notes:** OTC FX quote streams and exchange trade streams are different event sources; do not use a futures last-trade sequence as if it were an FX bid/ask sequence.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Intrabar” may be tick-based, quote-update-based, or lower-timeframe proxy-based.

## adverse-gap-slippage — Trigger-to-fill displacement

- **Family:** Exit events, orders, and management
- **Aliases:** stop slippage; gap-through; execution gap
- **Definition:** The difference between an intended/trigger price and the actual execution price when market movement or available liquidity prevents a fill at the reference.
- **Boundaries:** Not a stop reference, and not limited to visible opening gaps; it can occur during continuous rapid repricing.
- **Observable inputs:** Trigger/reference price, order timestamps/status, actual fill prices/quantities, bid/ask or order-book data where available.
- **Recognition semantics:** Compare the specified benchmark with volume-weighted actual fill(s), preserving the direction, price side, and whether the cause is a gap, spread change, latency, or limited liquidity.
- **Parameters/profiles:** benchmark, fill aggregation, data source, and cost attribution — all `source-stated` or `unresolved`.
- **Eligible roles:** execution constraint; management risk input; evidence annotation.
- **Market/data constraints:** A stop price is a trigger, not a guaranteed execution price; SEC specifically cautions that a stop-market fill may deviate substantially in fast markets.
- **Transfer notes:** Crypto CLOB depth, futures protection mechanisms, and OTC-FX dealer quotes produce different slippage processes.
- **Evidence/status:** https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15
- **Uncertainty/variants:** Distinguish a modeled adverse fill from observed execution data.

## market-entry-order — Market entry order

- **Family:** Entry order and timing semantics
- **Aliases:** market buy; market sell; aggressive entry
- **Definition:** An entry instruction seeking immediate execution against currently available liquidity, without a specified favorable limit price.
- **Boundaries:** Not guaranteed execution at the displayed chart price; not simply “enter now” unless its order form and price source are known.
- **Observable inputs:** Intended side/quantity, executable bid/ask or book depth, submission/acknowledgement/fill timestamps, and fills.
- **Recognition semantics:** Submit the marketable instruction after the entry trigger; record average actual fill and any unfilled remainder rather than substituting the signal price.
- **Parameters/profiles:** side, quantity, execution venue, price-protection behavior, and residual handling — all `source-stated` or `unresolved`.
- **Eligible roles:** entry execution; re-entry execution; exit execution.
- **Market/data constraints:** Market orders consume available liquidity and can fill across prices; some venues apply protection limits or partial fills.
- **Transfer notes:** Coinbase states market orders execute immediately at the best available price and can partially fill across prices; the mechanics do not establish those of another venue. https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Evidence/status:** cited venue documentation; source strategy semantics still needed.
- **Uncertainty/variants:** “Market” can be broker-dealer immediate execution, exchange market order, or marketable limit.

## limit-entry-order — Limit entry order

- **Family:** Entry order and timing semantics
- **Aliases:** passive entry; resting limit; buy limit; sell limit
- **Definition:** An entry instruction that may execute only at its stated limit price or a more favorable price.
- **Boundaries:** Not a guarantee of fill; not necessarily passive because a marketable limit can execute immediately.
- **Observable inputs:** Side, limit price, quantity, order-book/quote state, order acknowledgement, fills, and expiry/cancel status.
- **Recognition semantics:** Submit at the stated limit once its prerequisite is met; treat fill as conditional on available executable liquidity and reconcile any remaining order quantity.
- **Parameters/profiles:** price anchor/offset, quantity, time-in-force, post-only/maker constraint, and cancellation rule — all values `source-stated` or `unresolved`.
- **Eligible roles:** entry execution; retracement entry; target exit order.
- **Market/data constraints:** Queue priority and displayed depth are meaningful on a CLOB but not a complete representation of OTC FX liquidity.
- **Transfer notes:** CME defines a limit as a maximum buy/minimum sell constraint and notes it may rest until executed, canceled, or expired; broker implementations vary. https://www.cmegroup.com/education/courses/things-to-know-before-trading-cme-futures/futures-order-types
- **Evidence/status:** cited futures-market definition; transfer requires venue declaration.
- **Uncertainty/variants:** “Limit at level” must specify whether price is the zone edge, midpoint, or a calculated offset.

## stop-entry-order — Stop entry order

- **Family:** Entry order and timing semantics
- **Aliases:** breakout stop; buy stop; sell stop
- **Definition:** A contingent entry instruction activated when market price reaches a stop trigger and then transformed into the venue's specified executable order form.
- **Boundaries:** Not a protective stop simply because it uses a stop trigger; its intended purpose is to open/increase exposure.
- **Observable inputs:** Trigger price/basis, side, quantity, activation and fill reports, and resulting order type.
- **Recognition semantics:** Keep the instruction inactive until the declared trigger criterion occurs; then create/activate the specified entry order and separately verify fill.
- **Parameters/profiles:** trigger price/basis, post-trigger order type, quantity, time-in-force, and cancellation/expiry rule — all `source-stated` or `unresolved`.
- **Eligible roles:** entry execution; breakout execution.
- **Market/data constraints:** Stop-trigger conventions differ between last trade and quotations; native support may be broker/platform simulated.
- **Transfer notes:** CME describes a stop as inactive until triggered by a market trade, then distinguishes stop-limit and stop-with-protection behavior; OTC FX and crypto may use different bases/mechanics. https://www.cmegroup.com/education/courses/things-to-know-before-trading-cme-futures/futures-order-types
- **Evidence/status:** cited futures mechanics; no universal implementation assumed.
- **Uncertainty/variants:** A stop entry may be used for breakout continuation or stop-and-reverse only if that strategy binding says so.

## stop-limit-entry-order — Stop-limit entry order

- **Family:** Entry order and timing semantics
- **Aliases:** stop-limit breakout; triggered limit entry
- **Definition:** A contingent entry order that becomes a limit order after its stop trigger is reached.
- **Boundaries:** Not a stop-market entry and not guaranteed to fill after triggering; it explicitly trades execution certainty for a price bound.
- **Observable inputs:** Stop trigger/basis, limit price, side, quantity, activation state, and fill/cancel/expiry status.
- **Recognition semantics:** On trigger, submit/activate a limit order with the declared limit; retain it only under its time-in-force and cancellation rules if price moves away.
- **Parameters/profiles:** stop price, limit price, permissible trigger-to-limit relation, quantity, time-in-force, and cancellation rule — all values `source-stated` or `unresolved`.
- **Eligible roles:** entry execution; exit execution; protection.
- **Market/data constraints:** The stop and limit prices are distinct order fields and trigger-without-fill is a normal state.
- **Transfer notes:** SEC describes the general transformation into a limit order and its non-execution risk; CME gives futures-specific trigger/limit behavior. https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15 ; https://www.cmegroup.com/education/courses/things-to-know-before-trading-cme-futures/futures-order-types
- **Evidence/status:** cited educational/venue sources.
- **Uncertainty/variants:** A source's “stop limit” may omit the limit offset; retain it as `unresolved` rather than assume equality.

## close-confirmed-entry — Close-confirmed entry

- **Family:** Entry order and timing semantics
- **Aliases:** candle-close entry; confirmation-close entry
- **Definition:** An entry rule that permits an order only after a designated bar has finalized with the stated condition.
- **Boundaries:** Not an order type. It describes signal timing and may lead to market, limit, or stop execution.
- **Observable inputs:** Final OHLC or other finalized-bar data, timeframe/bar source, signal state, and subsequent order/fill data.
- **Recognition semantics:** Wait for bar finalization, evaluate the condition from immutable final values, then issue the separately specified entry order no earlier than the next permitted moment.
- **Parameters/profiles:** timeframe, confirmation rule, bar source/timezone, and resulting order type — all `source-stated` or `unresolved`.
- **Eligible roles:** entry trigger; confirmation; entry timing.
- **Market/data constraints:** Backtests must state whether an order at close is assumed possible and what fill occurs after the signal.
- **Transfer notes:** Broker/exchange daily and intraday bar boundaries are not universal across FX, futures, and crypto.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** A “confirmed close” can mean close beyond a level, close within a zone, or pattern completion.

## intrabar-entry — Intrabar entry

- **Family:** Entry order and timing semantics
- **Aliases:** real-time entry; tick entry; enter on touch
- **Definition:** Entry execution permitted while a bar is still forming when a live condition occurs.
- **Boundaries:** Not simply using a lower timeframe, and not identifiable from final OHLC without a path assumption.
- **Observable inputs:** Tick/quote or lower-resolution events, live state, order timestamps, and fills.
- **Recognition semantics:** Detect the first qualifying live event, then submit the specified order without waiting for the containing bar close; retain event ordering.
- **Parameters/profiles:** data event type, trigger basis, evaluation latency, order type, and one-shot/retry rule — all `source-stated` or `unresolved`.
- **Eligible roles:** entry trigger; entry timing; execution.
- **Market/data constraints:** Requires data resolution sufficient to distinguish a touch, a crossing, and the ordering of several intrabar events.
- **Transfer notes:** Exchange trades/order-book updates are not equivalent to OTC-FX broker quotes. A source must name the data event before transfer.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Touch-based and break-through-based entries are separate conditions.

## retracement-entry — Retracement entry

- **Family:** Entry order and timing semantics
- **Aliases:** pullback entry; fade-back entry; return-to-level entry
- **Definition:** An entry operation that waits for price to return toward a designated reference after an initiating move or signal.
- **Boundaries:** Not any limit order: it supplies the sequencing relationship between impulse/confirmation and later entry opportunity.
- **Observable inputs:** Initiating event, reference/zone, time order, current price/quotes, and order/fill status.
- **Recognition semantics:** Arm after the stated initiating move; accept entry only when price revisits the stated reference under any specified cancellation or confirmation conditions.
- **Parameters/profiles:** initiating event, retracement reference/zone, max wait, order type, and cancellation condition — all values `source-stated` or `unresolved`.
- **Eligible roles:** entry trigger; entry execution; management re-entry.
- **Market/data constraints:** Requires a formal definition of the initiating move and of whether a wick, close, or quote touch counts as a retracement.
- **Transfer notes:** Portable price behavior; any volume/order-flow confirmation imported from futures requires explicit target-market evidence.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Pullback continuation and mean-reversion retracement are different strategic bindings of the same execution concept.

## break-retest-entry — Break-and-retest entry

- **Family:** Entry order and timing semantics
- **Aliases:** breakout-retest; break-reclaim entry; retest confirmation
- **Definition:** A sequenced entry condition requiring a reference break followed by a return interaction that meets a stated retest criterion.
- **Boundaries:** Not synonymous with first-break stop entry or generic retracement; it requires both a break state and a retest state.
- **Observable inputs:** Level/zone, break event, retest prices, optional close/structure confirmation, timestamps, and execution data.
- **Recognition semantics:** Record the first valid break, arm the retest phase, and permit entry only if price subsequently interacts with the defined reference in the allowed way before expiry or invalidation.
- **Parameters/profiles:** level definition, break criterion, retest criterion, maximum interval, order type, and invalidation — all `source-stated` or `unresolved`.
- **Eligible roles:** trigger; confirmation; entry execution.
- **Market/data constraints:** Bar-only data can obscure whether break/retest occurred in the required order.
- **Transfer notes:** Portable where price-derived, but central-book “acceptance” language needs a source-specific observable on OTC FX/crypto spot.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Retest can be a touch, rejection, close back through, or hold; no universal algorithm is implied.

## marketable-limit-entry — Marketable limit entry

- **Family:** Entry order and timing semantics
- **Aliases:** aggressive limit; protected market entry
- **Definition:** A limit order priced so it is eligible to execute immediately against current liquidity while retaining a worst acceptable price.
- **Boundaries:** Not a market order because it has a price bound; not passive limit entry because it deliberately crosses available liquidity.
- **Observable inputs:** Current executable bid/ask/book, side, limit bound, quantity, and fills.
- **Recognition semantics:** At signal time set a limit price that crosses the current opposite-side quote/book within the source-defined tolerance; accept partial fill/remainder behavior explicitly.
- **Parameters/profiles:** limit-protection offset, quantity, price source, time-in-force, and residual action — all values `source-stated` or `unresolved`.
- **Eligible roles:** entry execution; exit execution; retry execution.
- **Market/data constraints:** Current quote/book can move before acceptance; a price-protected instruction can leave residual quantity.
- **Transfer notes:** CME documents market-limit behavior in which an unfilled remainder can become resting limit liquidity; broker/crypto implementations differ. https://www.cmegroup.com/education/courses/things-to-know-before-trading-cme-futures/futures-order-types
- **Evidence/status:** cited futures example; direct transfer is `unresolved`.
- **Uncertainty/variants:** Some platforms label distinct products “marketable limit,” “market limit,” or “price protection.”

## post-only-entry — Post-only limit entry

- **Family:** Entry order and timing semantics
- **Aliases:** maker-only; add-liquidity-only
- **Definition:** A limit entry instruction rejected or canceled if it would immediately execute as a taker, thereby requiring it to rest as displayed/eligible passive liquidity where supported.
- **Boundaries:** Not any ordinary limit order; it imposes a venue-specific execution constraint and does not assure a fill.
- **Observable inputs:** Limit price, current book, venue order acknowledgement/rejection, resting status, and fills.
- **Recognition semantics:** Submit a venue-supported post-only limit; if it would cross current liquidity, treat rejection/cancellation as an execution outcome subject to the source's retry policy.
- **Parameters/profiles:** price reference/offset, quantity, time-in-force, and retry/reprice policy — all values `source-stated` or `unresolved`.
- **Eligible roles:** entry execution; cost-sensitive execution.
- **Market/data constraints:** Requires an exchange/CLOB feature; displayed order-book participation and maker/taker classification are venue rules.
- **Transfer notes:** Coinbase documents “post only” as ensuring a limit order rests on its book or is rejected when it would execute immediately. It is not assumed available in OTC spot FX. https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Evidence/status:** cited exchange documentation.
- **Uncertainty/variants:** Post-only does not define queue rank, fill probability, or an economic edge.

## trigger-price-basis — Trigger price basis

- **Family:** Entry order and timing semantics
- **Aliases:** stop trigger source; mark/last/bid/ask trigger; quote-side rule
- **Definition:** The named market-price stream used to decide whether a contingent entry, exit, level breach, or target touch has occurred.
- **Boundaries:** Not the order price and not a generic chart price; the same numerical level may trigger at different times under bid, ask, mid, mark, or last trade.
- **Observable inputs:** Timestamped bid/ask quotes, last trades, marks/indexes if relevant, and broker/exchange trigger policy.
- **Recognition semantics:** Attach each threshold condition to one declared price basis and preserve it through recognition, simulation, and evidence capture.
- **Parameters/profiles:** price source, sampling/event rule, and fallback for missing data — all `source-stated` or `unresolved`.
- **Eligible roles:** execution semantics; invalidation; trigger; exit trigger.
- **Market/data constraints:** In OTC FX, executable bid/ask from a specific dealer/broker is central. In CLOB markets, last trade and best quote are separately observable.
- **Transfer notes:** SEC notes different firms may use last-sale or quotation prices for stop triggers; this supports treating trigger basis as first-class rather than universal. https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-15
- **Evidence/status:** cited general evidence; specific broker/exchange policy required.
- **Uncertainty/variants:** Mark and index prices are especially derivative-venue concepts and should not be silently created for spot strategies.

## partial-fill-handling — Partial-fill handling

- **Family:** Entry order and timing semantics
- **Aliases:** fill reconciliation; residual-order handling
- **Definition:** The operation that reconciles an order that fills for less than its requested quantity and determines the treatment of residual order and actual exposure.
- **Boundaries:** Not a planned partial exit; it responds to execution outcome and applies to entries and exits.
- **Observable inputs:** Requested quantity, individual fills, order status, remaining order quantity, current exposure/inventory, linked orders.
- **Recognition semantics:** On every fill report, update actual average fill and exposure; apply the stated policy to remaining order quantity and resize/cancel linked protection/target orders as needed.
- **Parameters/profiles:** minimum acceptable fill, residual action, linked-order resize rule, and timeout — all values `source-stated` or `unresolved`.
- **Eligible roles:** execution management; entry; exit.
- **Market/data constraints:** Partial execution is normal on CLOBs and can occur on market orders. Coinbase explicitly notes market orders can execute partially at multiple prices.
- **Transfer notes:** OTC FX execution reports and dealer fill conventions differ from exchange matching-engine events; do not assume order-book residual semantics.
- **Evidence/status:** https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Uncertainty/variants:** A source may permit partial entry, require all-or-none, or cancel/hedge residual exposure; each is distinct.

## entry-retry — Entry retry/requote operation

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** retry entry; requote; chase retry
- **Definition:** A source-defined attempt to submit a replacement entry order after rejection, cancellation, expiry, or insufficient fill of an earlier attempt.
- **Boundaries:** Not re-entry after a completed trade, and not automatic permission to chase price indefinitely.
- **Observable inputs:** Prior order outcome, current signal/setup state, current market data, retry count, and clock.
- **Recognition semantics:** Permit a new order only when the prior outcome matches the named retry condition and all original/prioritized setup validity checks remain true.
- **Parameters/profiles:** eligible outcomes, maximum attempts, delay/reprice rule, and cancellation condition — every numerical value `source-stated` or `unresolved`.
- **Eligible roles:** execution management; entry lifecycle.
- **Market/data constraints:** Rejection codes and requote behavior are broker/venue-specific; rapid retry requires latency-aware timestamps.
- **Transfer notes:** A decentralized OTC dealer quote/requote process is not equivalent to a rejected CLOB post-only order.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Retrying the same price, repricing to current market, and abandoning after a missed trade are separate policies.

## pending-order-cancellation — Pending entry-order cancellation

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** cancel unfilled order; withdraw entry order
- **Definition:** An operation that requests withdrawal of a still-active, unfilled or partially unfilled entry order.
- **Boundaries:** Not signal cancellation without an actual order, and not expiry; cancellation has acknowledgement/race semantics.
- **Observable inputs:** Order identifier/status, fills, cancellation request/acknowledgement, linked signal state, and current exposure.
- **Recognition semantics:** Submit cancel when the named condition occurs; continue reconciling fills until the venue confirms final order state, because fills can race with cancellation.
- **Parameters/profiles:** cancellation condition, affected order scope, residual-fill policy, and linked-order action — all `source-stated` or `unresolved`.
- **Eligible roles:** execution management; signal cancellation; risk control.
- **Market/data constraints:** An accepted cancellation request does not retroactively prevent a fill that matched first.
- **Transfer notes:** Futures/CLOB status progression is exchange-specific; OTC-FX pending instructions are broker/dealer-specific.
- **Evidence/status:** CME notes that a resting limit remains until executed, canceled, or expires: https://www.cmegroup.com/education/courses/things-to-know-before-trading-cme-futures/futures-order-types
- **Uncertainty/variants:** Cancel-on-invalidation, cancel-on-session-end, and cancel-on-opposite-signal are separate triggers.

## pending-order-expiry — Pending-order expiry

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** entry timeout; order timeout; signal expiry
- **Definition:** Automatic loss of eligibility of an unfilled order or armed entry opportunity at a designated time/event.
- **Boundaries:** Not position time stop; not discretionary cancellation. It occurs before full entry.
- **Observable inputs:** Order/signal activation time, expiry rule, venue time-in-force, calendar/session state, and order status.
- **Recognition semantics:** At the specified deadline or state boundary, mark the signal/order expired and request/corroborate cancellation if the venue has not already expired it.
- **Parameters/profiles:** expiry timestamp/duration/bar count/session endpoint, timezone, and action after expiry — all values `source-stated` or `unresolved`.
- **Eligible roles:** entry lifecycle; signal cancellation; timing constraint.
- **Market/data constraints:** Native time-in-force and strategy-level signal expiry can disagree; represent both when relevant.
- **Transfer notes:** Coinbase documents GTC, GTT, and IOC options for its limit orders. These labels and availability must not be presumed for an FX broker. https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Evidence/status:** cited venue documentation.
- **Uncertainty/variants:** “Valid for one candle” needs a declared start/end and bar source.

## time-in-force — Order time-in-force instruction

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** TIF; GTC; GTT; IOC; FOK
- **Definition:** A venue/order instruction defining how long an order may remain active and, for some forms, whether immediate full or partial execution is acceptable.
- **Boundaries:** Not the strategy's setup expiry, although it can implement part of one; availability and exact semantics are venue-specific.
- **Observable inputs:** Order instruction, acknowledgement, fill quantity, cancellation/expiry status, and venue rulebook.
- **Recognition semantics:** Preserve the explicit time-in-force submitted with each order and evaluate results according to that venue's defined behavior rather than generic label assumptions.
- **Parameters/profiles:** instruction label and deadline where applicable — `source-stated`; unsupported label — `unresolved`.
- **Eligible roles:** execution constraint; pending-order lifecycle.
- **Market/data constraints:** GTC may be subject to venue cancellation rules, maintenance, or product lifecycle; IOC permits partial execution by definition on many venues.
- **Transfer notes:** Coinbase defines GTC, GTT, and IOC for its Advanced orders; CME/order-routing firms may expose a broader/different set. https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Evidence/status:** cited venue documentation.
- **Uncertainty/variants:** Fill-or-kill must not be inferred from IOC; it requires its own venue-supported semantics.

## one-shot-signal — One-shot entry permission

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** single-use signal; consume-on-attempt; no-repeat entry
- **Definition:** A state rule limiting a recognized setup to one defined entry attempt, fill, or completed trade before reset.
- **Boundaries:** Not an order type and not a cooldown; it specifies consumption and reset semantics.
- **Observable inputs:** Setup instance identity, order attempts/fills, trade lifecycle, and reset condition.
- **Recognition semantics:** Create a durable instance when setup arms; after the specified consuming event, suppress further entries from that instance until a separately defined reset/rearm occurs.
- **Parameters/profiles:** consuming event, scope identity, reset event, and treatment of rejected/partial orders — all `source-stated` or `unresolved`.
- **Eligible roles:** entry lifecycle; risk control; sequencing.
- **Market/data constraints:** Requires state continuity across bar/session transitions and reconciliation of rejected/canceled orders.
- **Transfer notes:** Portable across markets; venue is relevant only to what counts as a submitted/accepted/filled attempt.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** One-shot may mean one order attempt, one fill, or one position per level; do not collapse them.

## entry-cooldown — Entry cooldown

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** lockout; refractory period; wait-after-trade
- **Definition:** A rule prohibiting new entry attempts for a defined interval or state period after a specified event.
- **Boundaries:** Not expiry of the prior signal and not time stop on an open trade; it gates subsequent entries.
- **Observable inputs:** Triggering event time/state, clock/bar count/session state, candidate signal state, and position state.
- **Recognition semantics:** On the named event, start a lockout timer/state; reject otherwise-valid new entries until the duration ends or reset condition occurs.
- **Parameters/profiles:** triggering event, duration/bar/session rule, scope (instrument/direction/strategy), and override conditions — all values `source-stated` or `unresolved`.
- **Eligible roles:** entry filter; re-entry control; management.
- **Market/data constraints:** Requires a timezone/bar construction and a stable instrument identity.
- **Transfer notes:** Portable. Continuous crypto trading makes clock/session selection explicit; futures halts and FX rollovers may interrupt the chosen time basis.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** A cooldown after loss, after exit, and after any attempt are distinct rules.

## re-entry — Re-entry after exit or stop-out

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** reengagement; second entry; re-open
- **Definition:** A new entry into the same directional or setup idea after a prior position was reduced or closed.
- **Boundaries:** Not retry of an unfilled order and not automatic reversal. It begins after a position/trade lifecycle event.
- **Observable inputs:** Prior trade state/outcome, new/continuing setup state, cooldown/one-shot state, current market data, and new order status.
- **Recognition semantics:** Permit a fresh entry only if the re-entry condition, reset/rearm condition, and any maximum-attempt rule are explicitly satisfied; create a new trade instance.
- **Parameters/profiles:** eligible prior exit types, rearm trigger, delay/cooldown, maximum re-entries, order type, and sizing rule — all values `source-stated` or `unresolved`.
- **Eligible roles:** entry; execution management; sequencing.
- **Market/data constraints:** Position accounting must distinguish a re-entry from a partial fill or an order amendment.
- **Transfer notes:** Crypto spot re-entry must have quote-currency inventory/balance; futures/OTC margin mechanics may differ materially.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Re-enter at same level, after new confirmation, or on reclaim are separate variants.

## contingent-order-linkage — Entry-linked contingent order activation

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** parent-child order; attached TP/SL; conditional child order
- **Definition:** A rule that activates, sizes, modifies, or cancels a child protective/target order in response to a parent entry order's acknowledgement or fill state.
- **Boundaries:** Not merely listing entry and exit rules together; it requires a defined parent-child state relation.
- **Observable inputs:** Parent order/fills, position quantity, child order statuses, linkage policy, and cancellations.
- **Recognition semantics:** On each parent fill event, apply the stated activation threshold and child quantity rule; reconcile child orders as parent fills, is canceled, or is partially filled.
- **Parameters/profiles:** activation event, quantity basis, linkage/OCO policy, partial-fill rule, and cancellation rule — all `source-stated` or `unresolved`.
- **Eligible roles:** execution management; protection; exits.
- **Market/data constraints:** Atomicity is venue-specific; non-native implementations have race risk between parent fill and child protection placement.
- **Transfer notes:** Coinbase says its TP/SL activates when the parent order starts filling and sizes the exit to filled quantity; this is a platform-specific implementation, not a portable guarantee. https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Evidence/status:** cited venue documentation.
- **Uncertainty/variants:** Child activation on partial fill versus full fill changes protection timing materially.

## fixed-fractional-risk-sizing — Fixed-fractional risk sizing

- **Family:** Source-native sizing/risk concepts
- **Aliases:** percent-risk sizing; fractional-risk model
- **Definition:** A source-native sizing concept that chooses position quantity so a stated loss-at-stop estimate corresponds to a stated fraction of an account/equity reference.
- **Boundaries:** Not platform governance, a recommendation, or a guarantee of maximum realized loss; gaps, slippage, costs, and stop non-fill can exceed an estimate.
- **Observable inputs:** Account/equity reference, entry estimate/actual fill, stop reference, contract/lot/instrument value, costs if source includes them.
- **Recognition semantics:** Preserve the source's calculation inputs and sizing instruction; distinguish intended risk at reference prices from realized outcome.
- **Parameters/profiles:** equity basis, risk fraction, stop basis, instrument value conversion, and cost/slippage treatment — every value `source-stated` or `unresolved`.
- **Eligible roles:** sizing input; management; source-native risk claim.
- **Market/data constraints:** FX pip value depends on pair/account currency and lot; futures have contract multipliers; crypto spot size is base/quote inventory constrained.
- **Transfer notes:** The concept transfers only after instrument-value and account-currency conversion are made explicit; no default fraction is standardized here.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Risk may be computed from planned entry versus actual fill, producing different quantities.

## fixed-cash-risk-sizing — Fixed-currency risk sizing

- **Family:** Source-native sizing/risk concepts
- **Aliases:** fixed-dollar risk; fixed monetary risk
- **Definition:** A source-native sizing concept that targets a stated nominal currency loss estimate at a defined protective-stop reference.
- **Boundaries:** Not fixed position notional and not a claim of realized-loss certainty.
- **Observable inputs:** Cash-risk amount, entry/stop estimates, instrument-value conversion, account currency, and costs if included.
- **Recognition semantics:** Determine quantity from the source-stated loss estimate per unit between entry and stop, preserving conversion timing and rounding rules.
- **Parameters/profiles:** cash amount, account currency, entry/stop basis, conversion rate, rounding, and cost treatment — all values `source-stated` or `unresolved`.
- **Eligible roles:** sizing input; source-native risk claim.
- **Market/data constraints:** Cross-currency FX conversion can change risk; futures multiplier and crypto quote denomination must be known.
- **Transfer notes:** Do not treat a futures contract dollar-per-tick relationship as a spot-FX pip value or a crypto unit value.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** The nominal amount may be fixed per trade, per day, or per setup; scope is essential.

## fixed-notional-sizing — Fixed notional/quantity sizing

- **Family:** Source-native sizing/risk concepts
- **Aliases:** fixed size; fixed lot; fixed units
- **Definition:** A source-native sizing instruction using the same stated quantity, lot amount, or quote-currency notional for each qualifying trade.
- **Boundaries:** Not risk-normalized sizing: the estimated loss at a stop changes when stop distance or instrument price changes.
- **Observable inputs:** Instrument quantity/lot/notional definition, account balance/inventory if relevant, entry price, and lot/minimum increments.
- **Recognition semantics:** Submit the stated quantity after applying venue increment/minimum rules; record any rounding or insufficient-balance outcome.
- **Parameters/profiles:** quantity unit, fixed amount, rounding rule, and insufficient-balance action — all values `source-stated` or `unresolved`.
- **Eligible roles:** sizing input; source-native risk claim.
- **Market/data constraints:** “Lot” is broker/instrument-specific; crypto base amount and quote notional are different sizing units.
- **Transfer notes:** Futures contract count, OTC-FX lot, and crypto base quantity must not be silently converted into each other.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** A fixed quantity can be fixed per instrument or normalized by a source-defined basket; retain scope.

## stop-distance-position-sizing — Stop-distance-derived position sizing

- **Family:** Source-native sizing/risk concepts
- **Aliases:** size-from-stop; inverse-stop-distance sizing
- **Definition:** A sizing relationship in which planned position quantity changes with the distance between an entry reference and a protective-stop reference.
- **Boundaries:** Not necessarily fixed-fractional sizing: the target may be a cash amount, a volatility budget, or another source-defined quantity.
- **Observable inputs:** Entry reference, stop reference, direction, instrument-value conversion, target risk measure, and rounding/minimums.
- **Recognition semantics:** Calculate adverse movement per unit between entry and stop and use the stated target risk measure to derive a permissible quantity; preserve treatment of changed stops after entry.
- **Parameters/profiles:** entry/stop basis, target risk measure, conversion, rounding, and pre/post-fill recalculation policy — all values `source-stated` or `unresolved`.
- **Eligible roles:** sizing input; management; source-native risk claim.
- **Market/data constraints:** Need a valid unit-value model, including FX quote/account conversion or futures multiplier.
- **Transfer notes:** No sizing formula is presumed universal between OTC FX, centralized futures, and crypto spot.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Some sources size at planned stop; others resize after actual fill or do not resize at all.

## scale-in — Staged entry/position addition

- **Family:** Source-native sizing/risk concepts
- **Aliases:** add-on entry; pyramid; averaging in; tranche entry
- **Definition:** A source-defined operation that adds exposure in one or more later tranches after an initial entry.
- **Boundaries:** Not partial fill and not re-entry after flat; the original exposure remains open while quantity increases.
- **Observable inputs:** Existing position, add trigger, permitted direction, add quantity, average fill, new protective/target instructions, and account/inventory availability.
- **Recognition semantics:** When an add trigger occurs, submit the stated additional quantity; update aggregate average entry, total exposure, and all linked protection/target quantities according to the source rule.
- **Parameters/profiles:** add trigger, tranche quantity, maximum tranches, averaging/pyramiding condition, and revised-stop rule — all values `source-stated` or `unresolved`.
- **Eligible roles:** management; entry; source-native sizing/risk claim.
- **Market/data constraints:** Requires clear aggregate versus per-tranche accounting; spot inventory and margin/contract rules constrain feasibility.
- **Transfer notes:** “Averaging down” and trend pyramiding have materially different risks but are both staged-entry operations; neither is endorsed by this entry.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Adds can be at better price, worse price, time intervals, or confirmation events.

## otc-fx-execution-context — OTC spot-FX execution context

- **Family:** Market-structure and execution-transfer constraints
- **Aliases:** dealer FX; broker FX; OTC FX market structure
- **Definition:** The execution context in which spot-FX prices, liquidity, and order handling are supplied through specific dealer, broker, or liquidity-provider relationships rather than one universal public central limit order book.
- **Boundaries:** Not a claim that all retail FX brokers operate identically, and not equivalent to a centralized futures exchange or one crypto exchange book.
- **Observable inputs:** Broker/dealer quote stream, bid/ask, order confirmations, broker order policy, roll/session schedule, and fill reports.
- **Recognition semantics:** Attach each execution rule to the named broker/dealer feed and its stated trigger, pending-order, and fill conventions; mark absent venue details `unresolved`.
- **Parameters/profiles:** broker/dealer, quote source, order-policy version, server timezone, and account execution model — all `source-stated` or `unresolved`.
- **Eligible roles:** market/data constraint; execution provenance; transfer constraint.
- **Market/data constraints:** BIS characterizes FX and OTC derivatives as OTC markets and reports on their size/structure; the relevant retail feed remains only a partial venue-specific observation.
- **Transfer notes:** Centralized futures volume/depth and a crypto exchange order book are not complete observations of OTC FX liquidity.
- **Evidence/status:** BIS Triennial Survey overview: https://www.bis.org/statistics/rpfx22.htm ; BIS discussion of less-visible and bilateral FX trading: https://www.bis.org/publ/qtrpdf/r_qt2212d.pdf
- **Uncertainty/variants:** ECN, single-dealer, multi-dealer, and retail broker models require source/broker evidence.

## centralized-futures-execution-context — Centralized futures execution context

- **Family:** Market-structure and execution-transfer constraints
- **Aliases:** exchange-traded futures context; CLOB futures context
- **Definition:** The execution context of a listed futures contract traded under a specific exchange rulebook, contract specification, tick size, matching engine, and session calendar.
- **Boundaries:** Not the intended STRATS venue and not interchangeable with spot price trading merely because both show candles.
- **Observable inputs:** Contract symbol/specification, exchange trade/book data, tick size, session state, order acknowledgements/fills, and rulebook/order-type documentation.
- **Recognition semantics:** Retain source contract and exchange identity with any primitive relying on volume, depth, stops, protections, or sessions; state transfer assumptions separately.
- **Parameters/profiles:** contract, exchange, tick value/size, session, order type, and protection mechanism — all `source-stated`, `published-convention`, or `unresolved`.
- **Eligible roles:** market/data constraint; source provenance; transfer constraint.
- **Market/data constraints:** CME specifies futures order types, including exchange-specific stop and protection behavior; these mechanisms arise from that venue's rules.
- **Transfer notes:** Futures-derived price action can be researched as source material, but centralized volume/order-book/last-trade claims are not silently transformed into Forex or crypto-spot facts.
- **Evidence/status:** CME futures order types: https://www.cmegroup.com/education/courses/things-to-know-before-trading-cme-futures/futures-order-types
- **Uncertainty/variants:** A futures source may use continuous contracts, front months, or regular-trading-hours data; each affects recognition.

## crypto-spot-execution-context — Centralized crypto-spot execution context

- **Family:** Market-structure and execution-transfer constraints
- **Aliases:** CEX spot context; crypto exchange spot book
- **Definition:** The execution context of buying or selling actual spot crypto assets on a named exchange market with its own order book, balances, fees, trading rules, and available contingent features.
- **Boundaries:** Not crypto derivatives, not a market-wide crypto order book, and not a guarantee that an order feature is available in all regions/pairs.
- **Observable inputs:** Named exchange/pair, order book/trades, balances, tick/size increments, fees, order status, and exchange rules.
- **Recognition semantics:** Bind execution behavior to exchange and pair, reconcile base/quote balances after every fill, and distinguish a spot sale of held asset from derivative position reduction.
- **Parameters/profiles:** exchange, pair, base/quote units, order feature, size/price increments, and balance policy — all `source-stated` or `unresolved`.
- **Eligible roles:** market/data constraint; execution provenance; entry/exit constraint.
- **Market/data constraints:** Order-book/depth data are exchange-local. Spot short exposure commonly requires borrowing/margin facilities outside simple held-inventory selling.
- **Transfer notes:** Coinbase's order types and bracket behavior provide one exchange example, not a universal crypto-spot contract. https://help.coinbase.com/coinbase/trading-and-funding/advanced-trade/order-types
- **Evidence/status:** cited exchange documentation.
- **Uncertainty/variants:** Centralized-exchange spot and DEX spot have different matching, custody, latency, and order semantics.

## order-book-data-scope — Order-book and volume data scope

- **Family:** Market-structure and execution-transfer constraints
- **Aliases:** venue-local depth; volume provenance; order-flow scope
- **Definition:** The constraint that observed trades, displayed depth, volume, and order-flow features describe only their named venue/feed and may not represent the broader market.
- **Boundaries:** Not a trading signal itself and not a claim that data are useless; it prevents scope inflation.
- **Observable inputs:** Data vendor/feed, venue, instrument, timestamp, depth/trade fields, and coverage statement.
- **Recognition semantics:** Label every volume/order-book-derived primitive with the exact market/feed it measures and reject transfer claims lacking a stated link to the target market.
- **Parameters/profiles:** venue/feed identity, instrument mapping, depth level, aggregation window, and coverage caveat — all `source-stated` or `unresolved`.
- **Eligible roles:** market/data constraint; evidence qualifier; transfer constraint.
- **Market/data constraints:** Futures and centralized crypto exchange data can be coherent venue data; spot-FX retail volume/depth is commonly broker/feed-specific.
- **Transfer notes:** Do not call broker DOM the complete FX order book; do not call one exchange's BTC spot book the complete crypto market.
- **Evidence/status:** Consistent with BIS discussion of less-visible and bilateral FX venues: https://www.bis.org/publ/qtrpdf/r_qt2212d.pdf ; ontology-seed for operational labeling.
- **Uncertainty/variants:** Aggregated multi-venue data require a disclosed aggregation method and timing alignment.

## execution-state-reconciliation — Order/position state reconciliation

- **Family:** Market-structure and execution-transfer constraints
- **Aliases:** execution reconciliation; fill-state audit; order state machine
- **Definition:** The operation of reconciling intended signals/orders with authoritative acknowledgements, fills, cancellations, and current actual exposure.
- **Boundaries:** Not strategy logic by itself and not platform governance; it is necessary to tell whether an intended entry/exit/management action actually occurred.
- **Observable inputs:** Order identifiers, timestamps, acknowledgements, rejects, fills, cancellations, positions/inventory, and linked-order states.
- **Recognition semantics:** Treat broker/exchange execution reports and actual exposure as authoritative for state; update strategy instance state only after defined events and retain unknown/inconsistent states visibly.
- **Parameters/profiles:** authoritative source, reconciliation cadence, linkage identifiers, and unresolved-state handling — all `source-stated` or `unresolved`.
- **Eligible roles:** execution management; evidence/provenance; risk control.
- **Market/data constraints:** Order state names and atomicity vary by broker/exchange; a UI/chart marker is not necessarily authoritative execution evidence.
- **Transfer notes:** Essential in all target markets, but the concrete reports differ: OTC-FX dealer confirmations, futures exchange reports, and crypto exchange REST/WebSocket order states.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Whether a strategy reacts on acknowledgement, partial fill, full fill, or settled inventory must be explicit.

## reversal-entry-after-exit — Exit-to-reversal sequence

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** stop-and-reverse; flip; reverse on signal
- **Definition:** A sequenced operation that closes or reduces an existing exposure and then opens exposure in the opposite direction under explicitly linked conditions.
- **Boundaries:** Not an opposing-signal exit alone, and not necessarily an atomic exchange order. It has both an exit and a new-entry leg.
- **Observable inputs:** Existing position, reversal trigger, exit order/fills, new-entry prerequisites, new-order/fills, and residual exposure.
- **Recognition semantics:** Define whether the new leg may submit before the exit fills, only after flat confirmation, or only after an additional confirmation; reconcile partial fills to prevent unintended double exposure.
- **Parameters/profiles:** trigger, exit form, flat-confirmation requirement, new-entry form/size, and failure policy — all `source-stated` or `unresolved`.
- **Eligible roles:** exit; entry; management; sequencing.
- **Market/data constraints:** Atomic reversal functions, reduce-only controls, netting/hedging modes, and shortability differ by venue/account.
- **Transfer notes:** Simple crypto spot inventory cannot always create opposite short exposure; futures and margin-enabled OTC FX may support it under different rules.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Reverse” can mean close then wait, close-and-open immediately, or hedge; do not normalize.

## no-new-entry-after-exit — Exit-conditioned entry lock

- **Family:** Pending-order lifecycle and re-entry
- **Aliases:** stop-out lock; exit lockout; no-chase rule
- **Definition:** A rule that restricts new entries after a specified exit event until a named requalification, time interval, or market-state reset occurs.
- **Boundaries:** More specific than generic cooldown because the lock attaches to an exit category and a requalification policy; not an exit operation itself.
- **Observable inputs:** Exit classification, timestamp, signal/setup instances, reset condition, and position state.
- **Recognition semantics:** On a named exit (for example stop-triggered or target-filled), set the scope-specific lock; allow later entry only when the stated reset/rearm condition is met.
- **Parameters/profiles:** covered exit types, lock scope, reset/requalification condition, and duration if any — all values `source-stated` or `unresolved`.
- **Eligible roles:** re-entry control; entry filter; management sequencing.
- **Market/data constraints:** Depends on trustworthy exit classification and actual fill state, not merely a target/stop touch.
- **Transfer notes:** Portable; exact handling of partially exited versus fully flat position must be stated.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** Some sources forbid only same-direction re-entry, while others prohibit all new trades in an instrument/session.

## target-to-trail-transition — Target-triggered trailing transition

- **Family:** Exit events, orders, and management
- **Aliases:** trail after TP; runner management; protect after objective
- **Definition:** A management state transition in which interaction with a target changes the protective-threshold rule for remaining exposure, rather than necessarily closing all exposure.
- **Boundaries:** Not a target reference alone, partial exit alone, or ordinary trailing stop; it explicitly defines a target-event-to-management transition.
- **Observable inputs:** Target-touch/fill event, remaining quantity, existing stop/reference, new trailing-rule inputs, and child-order state.
- **Recognition semantics:** When the stated target event occurs, apply the stated partial-exit/remainder rule and initialize or alter the trailing threshold only for the remaining exposure.
- **Parameters/profiles:** qualifying target event, retained quantity, new trail type/distance, and order-amendment policy — all values `source-stated` or `unresolved`.
- **Eligible roles:** management; exit; trailing protection.
- **Market/data constraints:** Fill versus touch must be distinguished; order amendments can race with partial fills.
- **Transfer notes:** Native linked conditional management is venue-specific; managed implementations require explicit reconciliation.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** A source may move to break-even, fixed trail, structure trail, or full close at first target.

## spread-cost-aware-exit-reference — Spread/cost-aware exit reference

- **Family:** Exit events, orders, and management
- **Aliases:** net target; cost-adjusted break-even; executable target
- **Definition:** A target or break-even reference adjusted by stated transaction costs, spread, financing, or expected execution effects to express a net rather than chart-price objective.
- **Boundaries:** Not a universal cost model and not a promise of realized net result; it is a source-native reference construction.
- **Observable inputs:** Entry fills, bid/ask spread, commission/fees, financing if included, target/stop rule, and account currency conversion.
- **Recognition semantics:** Apply only the stated cost components and price-side convention when calculating the reference; record unknown costs rather than silently setting them to zero.
- **Parameters/profiles:** cost components, estimate source, price basis, account conversion, and update policy — all values `source-stated` or `unresolved`.
- **Eligible roles:** target reference; break-even adjustment; sizing input; management.
- **Market/data constraints:** OTC-FX spread and financing, futures commissions/tick values, and crypto maker/taker fees differ by account and venue.
- **Transfer notes:** A source's fixed futures commission/tick calculation cannot be ported directly to spot FX or crypto spot.
- **Evidence/status:** ontology-seed — needs source evidence.
- **Uncertainty/variants:** “Break-even plus costs” needs the actual cost set and whether slippage is included.

## Deduplication notes

- `level-invalidation`, `setup-invalidation`, and `signal-cancellation` are distinct state changes: reference validity, complete setup validity, and an armed unfilled signal respectively.
- `stop-reference`, `protective-stop-order`, `target-reference`, `exit-trigger`, and `exit-order` deliberately remain separate. A strategy binding may connect them, but none implies the next.
- `partial-exit` is intentional management; `partial-fill-handling` is an execution outcome. `entry-retry` occurs after an unfilled/failed attempt; `re-entry` occurs after a position/trade lifecycle event.
- `time-stop`, `pending-order-expiry`, `time-in-force`, and `entry-cooldown` apply to different objects: open position, pending opportunity/order, order instruction, and future-entry permission.
- The four exit-status concepts are metadata/status primitives, not trading exits. They preserve source fidelity without designing any external policy.

## Unresolved taxonomy questions

1. Should source-native sizing concepts remain dictionary primitives or be represented as documented source claims with optional primitive links?
2. Should `deliberately-open`, `external-policy`, `unresolved`, and `source-defined` be dictionary entries, controlled status vocabulary, or both?
3. Is a stop reference that is explicitly used for sizing but never acted on better called a risk reference than a protective stop reference?
4. Which venue-neutral vocabulary should distinguish order acceptance, activation, trigger, matching, partial fill, full fill, cancellation acknowledgement, and settlement/inventory update?
5. How should strategy bindings state a target/stop collision within one OHLC bar when source evidence supplies only bar data?
6. What minimum evidence is required to classify a creator's discretionary “manage the trade” language as `deliberately_open` rather than `unresolved`?
