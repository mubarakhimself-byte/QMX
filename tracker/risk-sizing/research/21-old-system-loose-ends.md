# 21: Old-system loose ends — WF4, the pillars and tick data

Research date: 2026-10-30. Group A. Ticket: `wayfinder/tickets/research-old-system-loose-ends.md`.

**CHECKED — method.** Web access worked. Standing orders, STATE, the ticket, the research skill and the operator's own turns in the two named verbatim transcripts were read. Earlier research 10 and 19 supplied pointers; conclusions below follow those pointers to the old documents, the Stats lock, selected credential-filtered passages of the old GPT conversation, current code and current vendor documentation. This file records findings and options only. No design is selected.

Path aliases: `P = D:/QMX-worktrees/unit-plan/tracker/risk-sizing`; `R = D:/QMX-worktrees/unit-plan`; `V = C:/Users/Mubarak/Documents/Claude/QMX-discussion`; `S = C:/Users/Mubarak/Desktop/Stats`; `G = V/07-Source-Material/gpt-trading-algorithm-research.md`. CHECKED local references are to files read during this run.

## 1. Was WF4 the same thing as today's domain expansion?

**INFERRED — it was an ancestor of part of the idea, not an exact synonym.** Old ecological mutation changed a bot's setting or habitat and could assign a new symbol or timeframe. Feature mutation changed its signal ingredients. Today's discussion includes both making changed variants before live and letting a live unit find suitable markets without necessarily changing its logic. Only the first has a close match to the old mutation workflow. Sources: the two original old documents below; `P/operator/transcript-2026-10-20-to-28.md:483-484, 512-513, 1902-1903, 1950-1951`.

**CHECKED — WF4 was named in a surviving old document.** The backend deployment diagram lists WF1 as AlphaForge, WF2 as the paper-trading gate, WF3 as the bot improvement loop and WF4 as ecological plus feature mutation. That establishes an old documented role, not proof that a deployed WF4 ran. Source: `V/05-Deployment/02-backend-node.md:67-72`.

**CHECKED — a later specification explicitly removed that workflow name.** Its mutation table distinguishes:

- **FEATURE:** add, remove or swap features while retaining archetype and session/symbol profile.
- **ECOLOGICAL:** change archetype, often specialise for another session; a new symbol or timeframe may be assigned.

Both produce a child specification with a parent link. The 2026-05-01 note calls WF4 a phantom and assigns mutation to WF2 or WF3's rehabilitation sub-workflow. Source: `V/02-Components/07-bot-registry-and-lifecycle.md:149-162`.

**CHECKED — the surviving recollection qualifies the word “phantom.”** A July source note records that WF4 existed only in the crashed-laptop version. That is a recorded recollection, not recovered executable code. **INFERRED:** “removed from the later workflow set” and “remembered in lost code” can both be true; neither licenses saying it never existed anywhere. Source: `V/.brain/sources/agentic-braindump-2-2026-07-17.md:39-42`.

| Comparison | Evidence and conclusion |
|---|---|
| Change logic or inputs and create a variant | **CHECKED historical mechanism:** FEATURE/ECOLOGICAL mutations plus parent linkage. **INFERRED match:** close to pre-live expansion and rehabilitation, with current identity rules still unresolved. |
| Try another instrument, timeframe or session | **CHECKED historical possibility:** ecological mutation could do this. **INFERRED difference:** it treated the result as a new child; today's same-unit versus new-child question remains open. |
| An unchanged live unit selects among suitable markets | **CHECKED present seed:** the operator's System 1 discussion. **INFERRED:** not identical to the old mutation mechanism, which makes a new specification. |
| Return a changed variant to live automatically | **CHECKED current prohibition:** operator-only live promotion supersedes the old lifecycle's automatic transitions. Source: `P/STATE.md:39`; old lifecycle:125-140. |

**INFERRED — options remain open.** The later discussion can reuse the old name for research, keep pre-live mutation and live market selection distinct, or adopt another vocabulary. The evidence does not choose a workflow, identity rule or architecture. It touches unit lineage, research workflows and live placement.

## 2. Which strategy pillars hold now?

**CHECKED — the Stats lock is unambiguous.** Its four human review lenses are **location/level; market context/filter; trigger; confirmation/confluence**. A trigger is the event that fires. These are review lenses, not folders or a second ontology. Source: `S/schema/strategy-dna.md:126-140`.

**CHECKED — the operator's later recollection was expressly uncertain.** In the verbatim October discussion he recalls event, trigger, risk and position sizing, then says he has forgotten a pillar. That passage does not amend the Stats lock. STATE also says his statements are seeds unless recorded as rulings. Sources: `P/operator/transcript-2026-10-20-to-28.md:2050-2051`; `P/STATE.md:115`.

**CHECKED — four lenses do not exhaust the record.** The locked candidate package has A–I fields for identity, evidence, primitive references, role bindings, logic graph, exit completeness, dependencies, unknowns and lineage. It separately distinguishes entry semantics, invalidation versus stop, exits/management and timing. The dictionary is role-neutral; components acquire jobs through bindings and combine in a logic graph. Sources: `S/schema/strategy-dna.md:5-21, 29-43, 65-87, 89-122, 126-140`.

| Word in the discussion | What the checked baseline actually says |
|---|---|
| Location or level | **CHECKED:** where price is relevant; one of the four lenses. Stats lock:130. |
| Context or filter | **CHECKED:** regime, session, higher timeframe and vetoes; another lens. Stats lock:131. |
| Event and trigger | **CHECKED:** the trigger is the firing event. The lock does not name event as a separate fifth pillar. Stats lock:132. |
| Confirmation and confluence | **CHECKED:** supporting evidence; confluence is graph composition, not a primitive class. Stats lock:133. |
| Risk and sizing | **CHECKED:** absent from this four-lens list; the present QMX ruling nevertheless places both inside the complete trading unit. `P/STATE.md:21`. **INFERRED:** candidate-knowledge organisation and complete-unit responsibilities are different scopes. |

**INFERRED — answer for the dictionary ticket.** The checked historical baseline is the four lenses above, backed by bindings, a graph and A–I, not “event/trigger/risk/sizing.” Whether QML should retain or extend that view for complete units is still a planning question. Calling the old lock the latest approved *unit* schema would also overstate the evidence: it describes source-faithful candidate knowledge, explicitly not a running executor. Sources: Stats lock:5, 19-21, 31, 87; `P/STATE.md:21, 43`.

## 3. Was the tick-data API problem solved?

**INFERRED — three different problems were being mixed.** Quotes and depth were found in the API; a proxy approach was discussed; a public market-wide executed-trade tape was not recovered. The surviving record supports a documentation-level resolution, not an end-to-end, verified tape implementation.

### What the older conversation actually resolved

**CHECKED — the operator already separated decision data from execution.** He asked whether another source could supply order flow while execution stayed at his broker, then proposed recording streaming data for later use. Sources: `G:649, 5688`. These are his words, not an earlier agent's summary.

**CHECKED — the answer was a different data capability, not a hidden API switch.** The conversation describes quotes/depth from cTrader, an external source if executed trade flow is needed, and a depth-derived microstructure proxy with honest labels. Source: `G:5700-5737, 6298-6321`.

**CHECKED — its “blocker closed” statement was specifically research-level.** It says the documented API surfaces were sufficient to close a design/research blocker and separately asks whether the real adapter should now be implemented. An earlier code-audit passage still calls the market adapter a stub. Neither is a recorded broker-stream acceptance test. Sources: `G:10574-10580, 13421-13455`.

### What current primary documentation supports

| Data | CHECKED capability | INFERRED limit on the claim |
|---|---|---|
| Live quote ticks | `ProtoOASpotEvent` provides bid/ask; fields can be absent. [Message reference](https://help.ctrader.com/open-api/messages/#protooaspotevent). | Useful for quote/spread behaviour; this is not a market trade print. |
| Historical quote ticks | Request selects BID or ASK; results are newest-first, with `hasMore`. [Message reference](https://help.ctrader.com/open-api/messages/#protooagettickdatares). | Separate-side history does not create executed trade volume. |
| Live displayed depth | Updates carry changed quote IDs and deletions. Quote records include price and required size. [Depth event](https://help.ctrader.com/open-api/messages/#protooadepthevent), [Depth quote model](https://help.ctrader.com/open-api/model-messages/#protooadepthquote). | Can support displayed-liquidity studies; a disappearing quote does not identify a trade rather than cancellation. |
| Market-wide executed-trade tape | No such public subscription was found in the checked message catalogue. The deal-history request is explicitly for the trader's own deals. [Spotware protocol definitions](https://github.com/spotware/openapi-proto-messages/blob/main/OpenApiMessages.proto), `ProtoOADealListReq`. | Account fills are not a market tape. True buy/sell executed-volume analytics cannot be claimed from quote/depth alone. |

**CHECKED — one old assertion needs correction.** The older architecture text says depth has no per-level volume, yet the vendor's depth-quote model includes a required size, and the tutorial explains its conversion to units. **INFERRED:** the old blanket absence claim is wrong; the defensible distinction is displayed quote size versus executed trade size. Sources: `G:7286-7289, 7907`; [Depth quote model](https://help.ctrader.com/open-api/model-messages/#protooadepthquote); [Depth tutorial](https://help.ctrader.com/open-api/symbol-data/#depth-quotes).

**CHECKED — the historical limit is per request.** A tick request spans at most 604,800,000 milliseconds, or one week. Response chunk size depends on backend configuration; `hasMore` reports additional records. Historical request rate is five per second per connection; non-historical is fifty. Sources: [Historical ticks tutorial](https://help.ctrader.com/open-api/symbol-data/#attain-historical-tick-data), [Published rate limits](https://help.ctrader.com/open-api/).

**INFERRED — this does not establish total retention.** Paging can address a request-size limit; it cannot recover data the backend does not retain, manufacture historical depth, add trade prints, or guarantee every live quote update is delivered. Actual retention, gaps and delivery completeness remain broker/feed measurements. The checked API catalogue documents live depth but no historical-depth retrieval endpoint. No broker account was queried in this run. Sources: the tutorial above; [Spotware protocol definitions](https://github.com/spotware/openapi-proto-messages/blob/main/OpenApiMessages.proto); `R/docs/components/ctrader.md:63-65, 79-90, 106-111`.

### What current QMX code establishes, and what it does not

**CHECKED — some mechanics already exist as code.** `tick_span_within_cap` checks a single request and explicitly tells its caller to page into weekly spans. `TickQuote` preserves separate bid and ask facts with exact scaled values. Sources: `R/packages/qmf-venue/src/qmf/venue/ctrader.py:591-618`; `R/packages/qmf-data/src/qmf/data/ticks.py:1-5, 141-194`.

**CHECKED — an inspected continuity helper is narrower than the API permits.** `VenueContinuityBridge.plan` rejects the whole archive-to-live gap if it exceeds its span cap, then generates hourly page descriptions. It does not send requests, consume returned `hasMore`, or decode returned ticks. **INFERRED:** that whole-gap refusal is a local implementation restriction, not evidence of a vendor-wide one-week retention limit or a complete historical downloader. Source: `R/qmn/src/qmn/data/bootstrap.py:158-217`.

**CHECKED — the inspected short-session broker transport is also narrower.** Its allowlist includes trendbar requests and spot subscriptions, but not historical-tick or depth requests. Its spot method assembles bid/ask/timestamp into a short read. **INFERRED:** this transport cannot establish that a full tick-history/depth pipeline was shipped elsewhere. Source: `R/qmx-agents/packages/qmx-broker/src/qmx_broker/ctrader_transport.py:14-25, 79-122`.

**INFERRED — answer for order-flow sensors.** Quote-based sensors, displayed-depth sensors and executed-volume sensors require different evidence. The first two have documented cTrader inputs; the last would need an actual executed-trade source. An external venue can be studied while retaining cTrader execution, but transfer between venues remains a hypothesis, not identical market evidence. These options touch market-data acquisition, sensor labels and replay fidelity. No provider, broker switch or design is selected.

## 4. Search record, numbers and remaining uncertainty

**CHECKED — searches performed.** The following read-only searches and reads were used; the negative findings are bounded to this material:

- Read `V/05-Deployment/02-backend-node.md:50-80` and `V/02-Components/07-bot-registry-and-lifecycle.md:120-172`; checked the July recollection at `.brain/sources/agentic-braindump-2-2026-07-17.md:39-42`.
- Read `S/schema/strategy-dna.md` in full. Followed research 10/19's pillar pointers back to this lock.
- In G, searched case-insensitively for tick near API/data/problem/fix/history/solved, and `GetTickData`, `SpotEvent`, `coalesc`, `conflat`, `throttl`, `order.flow.proxy`. There were 95 matching lines in this bounded search; relevant passages cited above were read with credential-related lines suppressed before display. Old Hermes logs and credential files were not opened or copied.
- Searched current `packages`, `qmn/src/qmn` and the broker transport for `ProtoOAGetTickData`, `ProtoOASubscribeSpots`, `ProtoOADepth`, `ProtoOASpot`, `tickData`, `hasMore` and depth handling; read the cited implementations. Compiled protocol definitions were not treated as proof of a working connection.
- Browsed the current official cTrader tutorial, message catalogue, model catalogue and rate-limit page. No market data was downloaded; no Dukascopy request or broker connection was made.

**CHECKED — “not found” boundary.** A recovered, end-to-end test proving that the old executed-trade/tick problem was solved was not found in these searches. The crashed implementation itself was not recovered. A complete market-wide tape endpoint was not found in the current public API catalogue. These findings do not assert that every historic branch, private broker service or disk has been exhausted.

**INFERRED — editable defaults.** This ticket needs no new strategy threshold, lookback cap or risk number. If a later historical-data demonstration needs a chunk setting, an editable starting default is one day per request, with adaptive subdivision where a backend truncates; it is a request batch size, never a retained-history limit. The vendor's one-week request ceiling and published rates are external limits, not editable QMX policy. No fixed returned-tick count is assumed. Historical workflow numbers and the four pillar count describe the sources, not tunable trading rules.

**INFERRED — three findings to carry forward.** Old WF4 is evidence for mutation and lineage, not a settled live-expansion design. The Stats baseline has four review lenses with risk/sizing belonging to a broader complete-unit question. The tick issue was partly resolved as API capability and proxy planning; that did not supply a public trade tape or prove an operational pipeline.
