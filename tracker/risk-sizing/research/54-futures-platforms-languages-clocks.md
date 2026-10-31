# 54: Futures platforms and order-flow data, platform languages, futures and indices explained, clocks across regions

Grounding agent G3, 2026-10-31 midday program, half (b). Facts and options only. No design and no choice.

His words this answers (verbatim, `operator/transcript-2026-10-30-to-31.md`):
- 31 Oct 09:12: "CTrader might not handle futures." "I don't want to pay for a platform, I'm not gonna lie. Maybe find me a free one, especially the ones with order flow data, because I might need it. Let me see Sierra, how much Sierra costs." "I don't think they need order flow like charts. They need order flow data."
- 31 Oct 04:05: "we need to also know whether it's going to be Python, Golang, or I don't know which language, because each provider uses a different language." "Okay, you explain to me what futures, then indices." "when you look at the clock on a trading node located in Singapore, and then the clock on a trading node located in London, those are not so similar."
- 30 Oct 06:19: "Can I trade futures on CTrader? With order flow and stuff? Then of course, Hyperliquid".

## How to read this

- **CHECKED** = read today at the URL, or run today (command named), or read in an earlier research file that marked it CHECKED (file and section named). **INFERRED** = reasoned from checked facts. **SECONDARY** = read today on a third-party page, not the vendor's own.
- **Origin** column: **earlier** = harvested from the earlier work (file and section named); **new** = found today; **re-checked** = earlier fact read again today because it may be stale.
- Prices are the vendors' own on the date read. None is a QMX cap. Every number QMX would use is a named setting with a starting default, never a constant.
- Quotes from outside sources stay under 15 words.
- Companion files: research 38 (venues and connectivity, the main earlier source), 02 (instruments), 04 (platform study), 12 (feeds), 32 (instrument facts), 33 (data depth and terms), 31 (live path), `workroom/research/05-broker-connectivity.md` in the engine checkout (17 Aug). The code side is `architecture/grounding/G3-node-and-external.md`.

---

## 0. The short answer

1. **cTrader cannot trade exchange futures.** Spotware sells it as a "Premium FX/CFD trading platform" (re-checked https://www.spotware.com/ctrader/). IC Markets lists its futures-based CFDs on MT4/MT5 only (research 38 §0, CHECKED 30 Oct).
2. **No platform gives free real-time futures order-flow data to an outside algorithm.** The exchange (CME) charges every real-time user. The cheapest non-professional depth costs about USD 13.50 to 16 a month per exchange, and only with a funded futures account at a supported broker (Sierra Chart and NinjaTrader fee tables, CHECKED today). Free order-flow data exists only for crypto: Hyperliquid, Binance, Bybit (CHECKED, §1.4).
3. **Sierra Chart is cheap but locks its data inside its own desktop program.** USD 26 to 56 a month plus exchange fees (CHECKED). Sierra's own engineers say its Denali data "can only be used within the Sierra Chart desktop program", and external access over its DTC protocol is "no longer allowed due to exchange rules" (support board, Oct and Jul 2026, CHECKED). An algorithm would have to be written in C++ inside Sierra (ACSIL). It is not a data feed for QMX.
4. **For an algorithm, order-flow data comes from a data API or a broker API, not a charting platform.** The checked ways in: Databento (CME, data only, USD 199 a month, full order book), Rithmic or CQG through a futures broker (data plus orders, any language over WebSocket and protobuf), IBKR (cheap but 3 depth books and a manual weekly login). Ranked in §1.5.
5. **Languages:** charting platforms force their own language inside their app (cTrader C# or Python, NinjaTrader C#, MT5 MQL5, Sierra C++, Quantower C#, ATAS C#, MultiCharts PowerLanguage or C#, Bookmap Java or Python). Every broker or data API that QMX would use speaks a wire protocol any language can use (protobuf or JSON over TCP or WebSocket). So QML can stay Python and add adapters, not language ports (§2, INFERRED).
6. **Clocks:** standard practice is one time scale (UTC) for every stamp, local time only for display and session rules, a synchronised clock on every machine, and calendars from the exchange. Two DST traps sit near today: London moved back on 25 Oct 2026 and New York moves back on 1 Nov 2026, so London and New York are 4 hours apart this week instead of 5 (computed today with Python `zoneinfo`, §4).

---

## 1. Futures and order-flow data, free or cheap, for algorithms

"Order flow" here means data, not charts: every trade with its aggressor side (who crossed the spread), depth by price (MBP), and ideally the full order book order by order (MBO, "market by order").

### 1.1 Charting and trading platforms

| Platform | Cost (vendor's) | Order-flow data | Can an outside algorithm read the data? | Language for strategies | OS | Origin | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **cTrader** | Free platform; broker spreads | Quotes, broker depth with sizes, bars; no trades tape, no real volume, no open interest | Yes, Open API (Protobuf on port 5035 or JSON on 5036) | cAlgo: C# or native Python inside the app | Any OS for the Open API | earlier, re-checked | research 38 §3.1; https://www.spotware.com/ctrader/ (CHECKED) |
| **Sierra Chart** | Packages USD 26 (base), 36, 46, 56 a month (Package 12 adds MBO); 35% off for 12 months; no one-time licence | Denali feed: tick by tick with bid/ask trade volume, full depth, MBO on Package 12 (orders of size 3 and up only) | **No.** "only for use within the Sierra Chart" desktop program; DTC data access not allowed | ACSIL (C++) inside Sierra | Windows (Linux or Mac through Wine, INFERRED) | **new** | https://www.sierrachart.com/index.php?page=doc/Packages.php ; https://www.sierrachart.com/index.php?page=doc%2FDenaliExchangeDataFeed.php ; support threads 107669 (12 Oct 2026), 106706 (24 Jul 2026), 107797 (23 Oct 2026) (all CHECKED) |
| Sierra exchange fees (non-pro, funded account at IBKR, Rithmic, Teton or CQG required) | CME top of book USD 2; CME depth USD 13.50; full CME Group (4 exchanges) with depth USD 40.50; professional or no account USD 115.50 per exchange, 462 for all four | | | | | **new** | Denali page above (CHECKED). Prop evaluation accounts (Topstep and similar) do not qualify |
| **NinjaTrader** | Free plan USD 0 (commission 0.39 per micro side); Monthly USD 99; Lifetime USD 1,499. Data needs a funded account. Free plan: USD 35 fee if no live trade in 30 days | CME L1 USD 12 bundle or 4 per exchange; L2 USD 48 bundle or 16 per exchange (non-pro); professional USD 156 per exchange. Order Flow+ is a paid add-on (included with Lifetime) | Only inside NinjaTrader Desktop (NinjaScript). The Tradovate API gives orders, not market data, without a CME sub-vendor licence (research 38 §3.4) | NinjaScript (C#) | **Windows only**: "built for Windows-based systems" | **new** + earlier | https://ninjatrader.com/pricing/ ; https://ninjatrader.com/pricing/account-fees/ ; https://ninjatrader.com/pricing/pricing-faqs/ ; https://ninjatrader.com/uk/platform/desktop-trading/ (CHECKED) |
| **Quantower** | Free version (one connection, DOM, Time & Sales, free API, Strategy Runner); All-in-One about USD 70 a month; volume analysis (footprint) is paid | Whatever the connected feed gives (Rithmic, CQG, dxFeed, crypto exchanges) | Only inside Quantower | C# (Visual Studio extension) | **Windows only** | **new** | https://www.quantower.com/pricing ; https://www.quantower.com/faq ; https://help.quantower.com/quantower/quantower-algo/introduction ; https://help.quantower.com/quantower/getting-started/connect-your-broker (CHECKED). It also connects to cTrader and Hyperliquid |
| **ATAS** | Start plan free; Plus EUR 24.95, Pro EUR 69.95, Ultra EUR 89.95 a month (SECONDARY prices) | Footprint, cumulative delta, DOM on every plan; real-time crypto free; futures on Start and Plus are 15 minutes late; real-time futures need Pro or Ultra plus a paid feed | Only inside ATAS ("no REST or WebSocket API", SECONDARY) | C# inside ATAS | Windows; ATAS X for macOS in beta | **new** | https://atas.net/pricing/ (CHECKED features); prices SECONDARY https://cryptomarkets.tools/tools/atas , https://tradingloot.com/comparisons/atas-vs-bookmap/ |
| **Bookmap** | Digital free (crypto, one symbol at a time); Global USD 49, Global Plus USD 99 a month (SECONDARY); futures data extra (dxFeed about USD 37 per exchange, Rithmic USD 40 to 101, SECONDARY) | Heatmap of the full book, trades; crypto data free | Add-ons inside Bookmap; an L0 "Connect" API lets you write your own data adapter | Java (add-ons), Python API in early stage | Windows, Mac, Linux (SECONDARY) | **new** | https://bookmap.com/knowledgebase/docs/API ; https://bookmap.com/knowledgebase/docs/KB-IntroductionToBookmap-Connectivity (CHECKED); prices SECONDARY https://cryptomarkets.tools/tools/bookmap |
| **MultiCharts** | Free: simulator only, "Market data is not available"; paid plans from about USD 99 a month; lifetime USD 1,497 | Whatever the connected broker or feed gives | Only inside MultiCharts | PowerLanguage (EasyLanguage-like) or MultiCharts .NET (C#, VB.NET; Python in beta) | Windows 11, .NET 4.8 | **new** | https://www.multicharts.com/purchase/ ; https://www.multicharts.com/compare/ ; https://multicharts.com/net/tech-specs/ (CHECKED) |
| **MT5 at AMP Futures** | Free terminal | Real CME and Eurex futures through a CQG gateway; **top of book only** on MT5 | Python package against a running terminal | MQL5; Python as a data and order bridge | Windows (Wine on Linux) | earlier | research 38 §3.2 |
| **TopstepX / ProjectX** (prop firm) | USD 29 a month (14.50 with code) | Quotes, trades, depth over SignalR | Yes, but "VPS, VPN and remote servers are prohibited" for orders; live funded accounts cannot trade through the API | Any (REST, SignalR) | Any | earlier | research 38 §3.7 |

### 1.2 Data APIs and broker APIs (the ones an algorithm can call)

| Route | What you get | Cost and catch | Language and wire | OS | Origin | Source |
| --- | --- | --- | --- | --- | --- | --- |
| **Databento** (data only) | CME, CBOT, NYMEX, COMEX: 650,000+ symbols; live trades, top of book, MBP-10 depth, **MBO** full order book; nanosecond PTP timestamps; same API for live and replay | CME Standard plan **USD 199 a month** from 22 Jun 2026 (179 kept for existing subscribers); history included: bars and definitions 16+ years, L1 and trades last 12 months, L2 and L3 last month; deeper history pay per GB; **USD 125 free credits** for 6 months; personal use on **up to 2 devices**, CME licence fee included for personal use | Python, C++, Rust clients; raw TCP | Any | re-checked + **new** | https://databento.com/pricing ; https://databento.com/blog/updates-to-subscription-pricing (29 May 2026); https://databento.com/docs/portal/live-data (CHECKED) |
| Databento catch | An algorithm is "non-display use"; Databento says "some venues support personal non-display use". Whether CME personal licensing covers an algorithm placing orders was not confirmed | | | | **new** | same live-data page (CHECKED); coverage INFERRED open |
| **Rithmic** (through a futures broker, an FCM) | Data and orders: CME group and others; "Full depth, MBO, tick-by-tick" with microsecond stamps on R\|API+; server-side risk (auto-liquidation, position and loss limits) | At AMP: USD 25 a month connection, USD 0.10 per side routing, CME depth bundle USD 45 non-pro. Conformance test before production. Protocol API reported unavailable on paper accounts with live data (SECONDARY) | R\|API+: C++ and .NET. **R\|Protocol: WebSockets plus protobuf, any language, any OS.** Python community clients exist (async_rithmic, pyrithmic) | Any (Protocol) | earlier + **new** | https://www.rithmic.com/solutions/builders (CHECKED); https://tradefutures4less.com/rithmic-protocol/ (FCM reprint of Rithmic text); research 38 §3.3 |
| **CQG WebAPI** (through an FCM) | Streaming L1 and L2, orders, accounts | Price "Contact us"; formal conformance test before production; a fully simulated environment exists | Protobuf over secure WebSocket, any language | Any | **new** | https://help.cqg.com/apihelp/Documents/cqgwebapi.htm ; https://partners.cqg.com/marketing-resources/monthly-price-sheet (CHECKED) |
| **Interactive Brokers** | Futures, stocks, FX in one account; at 100 data lines: 3 depth books, 5 tick-by-tick streams | Data billed per username per full month. TWS API needs a running TWS or IB Gateway with a manual login; "headless" not supported; weekly re-login. The Web API for individual accounts also goes through a Java gateway with SSO login; programmatic OAuth is for advisors, brokers and institutions only | TWS API: Python, Java, C++, C# and VB.NET (C# and VB.NET Windows only), TCP socket with protobuf | Java gateway (runs on Linux) | earlier + **new** | research 38 §3.6; https://www.interactivebrokers.com/docs ; https://www.interactivebrokers.com/docs/web-api/authentication/introduction ; https://interactivebrokers.github.io/tws-api/initial_setup.html (CHECKED) |
| **Tradovate API** | Orders only | USD 25 a month; USD 1,000 live minimum; no market data without a CME sub-vendor licence; one connection per customer | REST and WebSocket | Any | earlier | research 38 §3.4 |
| **dxFeed** | CME group depth and Time & Sales, rolling (continuous) futures, history since 2010 | Sold to retail through platforms (ATAS, Quantower, Bookmap and others); a 2024 promotion listed CME depth at USD 29 (normally 39) a month | Java, FIX, C/C#, JavaScript/REST, Python/R (a business relationship, INFERRED) | Any | **new** | https://choose.dxfeed.com/individuals/ ; https://choose.dxfeed.com/futures-market-data/ (CHECKED); price https://dxfeed.com/dxfeed-launches-exclusive-black-friday-deals/ (Nov 2024, stale) |

### 1.3 CME's non-professional fees, side by side (per month)

All vendors pass the exchange fee through, with their own markup. Every one bills a full calendar month.

| Vendor | CME top of book | CME depth (one exchange) | All four CME exchanges with depth | Professional | Source |
| --- | --- | --- | --- | --- | --- |
| Sierra Chart (Denali) | USD 2 | USD 13.50 | USD 40.50 | USD 115.50 per exchange | Denali page (CHECKED today) |
| NinjaTrader | USD 4 | USD 16 | USD 48 | USD 156 per exchange | account-fees page (CHECKED today) |
| CQG via FCM | USD 2 | USD 13 | USD 41 bundle | about USD 145 per exchange | research 02 §7.2 (CHECKED 24 Oct) |
| AMP (Rithmic or CQG) | USD 15 L1 bundle | USD 17 | USD 45 bundle | not read | research 38 §3.3 (CHECKED 30 Oct) |
| Databento Standard | included | included | included (plus MBO) | commercial USD 973 per exchange | Databento pages (CHECKED today) |

"Non-professional" needs a funded futures account at a supported broker (Sierra: IBKR, Rithmic, Teton or CQG). Prop-firm evaluation accounts do not qualify (Sierra Denali page, CHECKED).

### 1.4 Crypto: free order-flow data

| Venue | Free live streams | Aggressor side? | Limits | Origin | Source |
| --- | --- | --- | --- | --- | --- |
| **Hyperliquid** (perps, plus HIP-3 perps on stocks, indices, gold, FX) | `trades`, `l2Book` (20 levels, about every 5.4 s; `fast` 5 levels about every 500 ms), `bbo`, `activeAssetCtx` (funding, open interest, mark), `candle`; no key needed | Yes: each `WsTrade` carries `side`, `px`, `sz`, `time`, `tid`, `users` [buyer, seller]. `side` is the taker's side ("B" bought, "A" sold) per a third party | Per IP: 10 websockets, 1,000 subscriptions, 2,000 messages a minute; candles only the last 5,000 | earlier + **new** | https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket/subscriptions (CHECKED fields); taker meaning SECONDARY https://docs.hydromancer.xyz/readme/websocket/trades ; limits research 38 §3.8 |
| **Binance** (spot and futures) | `aggTrade` every 100 ms, depth diff streams, bulk history files | Yes: `m` = "Is the buyer the market maker?" | 1,024 streams per connection, cut every 24 h; Binance Vision files under a non-commercial licence since 26 Aug 2026 | earlier + **new** | https://developers.binance.com/docs/derivatives/coin-margined-futures/websocket-market-streams/Aggregate-Trade-Streams (CHECKED); research 12 §4.1, research 33 §3.2 |
| **CCXT** (any of 100+ exchanges) | `watch_trades`, `watch_order_book`, `watch_ohlcv` and others; WebSocket support is inside the free MIT `ccxt` package, Hyperliquid included (`ccxt.pro.hyperliquid`) | as the exchange gives it | the exchange's own | **new** | context7 `/websites/ccxt` FAQ pages (CHECKED) |

INFERRED: Hyperliquid's HIP-3 books give real traded order flow on stock-index, gold and FX perps for free, on Hyperliquid's own book. It is not the CME tape, and its depth is 20 levels, not the full book.

### 1.5 Ranked shortlist for an algorithm (not a choice)

Judged on: cost, data depth (trades with aggressor side, depth, full book), language, licence limits, and whether it runs on his Windows PC and on a Linux server with no desktop app.

| Rank | Option | Markets | Depth | Cost a month | Windows PC | Linux server | Licence or catch |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **Hyperliquid public feeds** (direct or through CCXT) | Crypto perps; HIP-3 stocks, indices, gold, FX perps | Trades with taker side, 20-level book, funding, OI | 0 | Yes | Yes | Terms bar the US, Ontario and sanctioned places (research 38 §3.8); not the full book |
| 2 | **Binance or Bybit public feeds through CCXT** | Crypto spot and perps | Trades with aggressor flag, depth diffs | 0 | Yes | Yes | History files non-commercial (research 33 §3.2) |
| 3 | **Databento CME Standard** | CME, CBOT, NYMEX, COMEX futures | Trades, MBP-10, **MBO** live; 1 month of L2/L3 history included | 199 | Yes | Yes | Data only (orders elsewhere); personal use on 2 devices (his PC plus one server fits); algorithm use under personal licence not confirmed |
| 4 | **Rithmic through an FCM (for example AMP)** | CME group and other futures | Full depth, MBO on R\|API+; ticks and depth on R\|Protocol | about 25 + 45 depth + routing and commissions | Yes (Protocol API) | Yes | Funded account; conformance test; country eligibility; data and orders in one |
| 5 | **CQG WebAPI through an FCM** | Futures | L1 and L2 | on request + exchange fees | Yes | Yes | Conformance test; price unknown |
| 6 | **IBKR** | Futures, stocks, FX | 3 depth books, 5 tick streams at 100 lines | small data fees | Yes | Awkward (manual login) | Weekly manual login; daily restart |
| n/a | Not a data source for an outside algorithm | Sierra Chart, NinjaTrader Desktop, Quantower, ATAS, Bookmap, MultiCharts | | | | | Data and strategies live inside the desktop app; most are Windows-only |
| n/a | Rejected for a trading node | TopstepX | | | | | No orders from a server |

INFERRED, for the foundation: options 1 and 2 cover free order-flow units today. Options 3 to 5 are the only paths to real futures order flow; each is a paid, named setting the operator switches on, so nothing in the core should assume one of them. Index and gold CFD units on cTrader can read futures order flow as a proxy (research 38 §8 option B), with the price gap between the two measured (research 32).

---

## 2. Languages and APIs per platform

| Platform or API | Strategy language (inside the app) | External API and wire | Python today? | Origin | Source |
| --- | --- | --- | --- | --- | --- |
| cTrader | cAlgo: C# (`Robot` class) or native Python (via pythonnet; third-party packages only locally or on a VPS) | Open API: Protobuf or JSON over TCP or WebSocket, OAuth | Yes, any language over the Open API; QMX speaks Protobuf | earlier | research 04 §1.2; research 38 §3.1 |
| NinjaTrader | NinjaScript (C#), `OnStateChange` and `OnBarUpdate` | Tradovate REST and WebSocket (orders only) | Only through Tradovate | earlier + new | research 04 §1.3; research 38 §3.4 |
| MetaTrader 5 | MQL5 (C++-like); ONNX models inside | `MetaTrader5` Python package against a running terminal, Windows only, no push events | Yes, Windows only | earlier | research 04 §1.1; `workroom/research/05-broker-connectivity.md` §3 |
| Sierra Chart | ACSIL (C++) | DTC protocol, but external data access refused for Denali | No for data | **new** | §1.1 sources |
| MultiCharts | PowerLanguage or .NET (C#, VB.NET); Python in beta | broker connections inside the app | Beta only | **new** | §1.1 sources |
| Quantower | C# | none for outside programs | No | **new** | §1.1 sources |
| ATAS | C# | none for outside programs (SECONDARY) | No | **new** | §1.1 sources |
| Bookmap | Java add-ons; Python API early | L0 Connect API for custom adapters | Partly | **new** | §1.1 sources |
| Rithmic | n/a | R\|API+ (C++, .NET); R\|Protocol (WebSocket plus protobuf, any language) | Yes, through R\|Protocol (community clients) | earlier + new | §1.2 |
| CQG | n/a | WebAPI: protobuf over secure WebSocket | Yes, any language | **new** | §1.2 |
| IBKR | n/a | TWS API (Python, Java, C++, C#, VB.NET) over TCP; Web API (REST and WebSocket) | Yes | earlier + new | §1.2 |
| Databento | n/a | Python, C++, Rust clients; raw TCP; DBN binary, CSV, JSON | Yes | re-checked | §1.2 |
| Hyperliquid | n/a | JSON over REST and WebSocket; signed actions with nonces | Yes (official Python SDK exists, INFERRED; CCXT has it, CHECKED) | earlier | research 38 §3.8 |
| CCXT | n/a | One unified library in JavaScript, Python, PHP, C# and Go | Yes, pinned 4.5.85 in QMX | **new** | context7 `/ccxt/ccxt` description (CHECKED) |
| QuantConnect LEAN, Jesse, freqtrade, NautilusTrader | Python (LEAN also C#; Nautilus also Rust) | own engines | Yes | earlier | research 04 §2 table |

**What this means for QML and its adapters (INFERRED, options only):**
- Every venue QMX can reach from a server speaks a wire protocol: protobuf or JSON over TCP or WebSocket. None needs a language port; each needs an adapter that turns its messages into the CT-19 commands and CT-20 events QMX already has (G3 §3).
- Only in-app strategies force a language: C# (cTrader, NinjaTrader, Quantower, ATAS, MultiCharts .NET), MQL5, C++ (Sierra), Java (Bookmap). These matter only if a unit must run inside such an app, which none of the shortlisted data paths needs.
- His "Golang" question: no checked platform requires Go. CCXT offers Go; Databento offers Rust and C++. A compiled core only pays off when the network is no longer the floor (research 31 §4, measured about 160 ms to cTrader from his PC against about 2 µs per in-process delivery).
- Options for the record: (a) Python everywhere, wire adapters per venue; (b) the same, plus an optional export of a unit to a cTrader C# or Python cBot for an outside cross-check of QMB's numbers (research 04 §5 item 9); (c) a compiled feed and order core under Python, for a co-located server only.

---

## 3. Futures and indices, in plain words (for him)

### 3.1 Futures

- **A futures contract is a promise to buy or sell something at a set price on a set date.** It trades on an exchange (CME in Chicago for US index, gold and oil futures), not with a broker. Everyone sees the same prices and the same trades.
- **Each contract has a size.** The E-mini S&P 500 (ES) is worth 50 dollars for every point the index moves. The Micro E-mini (MES) is one tenth of that, 5 dollars a point (research 02 §7.1, CHECKED at CME).
- **Prices move in fixed steps, called ticks.** ES and MES move in steps of 0.25 points. One tick is worth 12.50 dollars on ES and 1.25 dollars on MES. Micro Nasdaq (MNQ) is 0.50 dollars a tick (research 02 §7.1).
- **Contracts expire.** US index futures expire four times a year: March, June, September, December. The old contract stops trading at 8:30 a.m. Chicago time on the third Friday and is settled in cash (research 02 §7.1, CHECKED at CME).
- **Rolling.** Before expiry, traders move to the next contract. CME's usual roll day is the Monday before the third Friday, for example 14 December 2026 for the 18 December 2026 expiry (research 02 §7.1). After the roll, almost all trading is in the new contract.
- **Continuous contracts.** For charts and backtests, the contracts are joined into one long series. There are two ways: keep the real prices and accept a jump at each roll (Databento does this; its symbols roll by calendar, volume or open interest, for example `ES.c.0` is the front contract by calendar), or shift old prices so the jump disappears (back-adjusting; NinjaTrader offers it). A unit trained on shifted prices sees different price levels from the contract it trades (research 32 §3.2; https://databento.com/docs/conventions/symbology, CHECKED).
- **Margin is a deposit, not a price.** You put up a small part of the contract's value. NinjaTrader asks 50 dollars a contract during the day for micro index futures and 500 for E-minis; holding overnight needs the exchange's much larger margin (https://ninjatrader.com/pricing/, CHECKED today).
- **Sessions.** CME index futures trade nearly 24 hours: Sunday to Friday, 5 p.m. to 4 p.m. Chicago time, with a one-hour daily break. The busiest part is the US cash session from 9:30 a.m. New York (research 02 §7.1 and §4.2).
- **Price limits.** If the index falls 7%, 13% or 20%, trading pauses or stops for the day (research 02 §7.1).
- **Why futures have order-flow data.** Because all trades happen on one exchange, the exchange publishes every trade and the whole order book. That is the "order flow" scalpers read. It is not free: the exchange charges a monthly fee (§1.3).

### 3.2 Indices

- **An index is a number, not something you can buy.** The S&P 500 is the weighted value of 500 US companies. You trade it through something that follows it.
- **Index future** (ES, MES, NQ): trades on CME, expires, has real volume and a public order book (above).
- **Index CFD** (IC's US500 on cTrader): a contract with the broker that follows the index. It never expires. You pay a daily financing charge, three times on Friday for indices. Dividends are paid to longs and charged to shorts. There is no real volume, only the count of price changes, and no public trades tape. Each index has its own daily breaks (research 02 §4.1, CHECKED at IC and cTrader).
- **Index futures CFD** (IC's MT5 futures-based CFDs): follows a future, expires two working days before it, and is never rolled. IC lists these on MT5 only (research 38 §5, research 32 §3.1 case E2).
- **On cTrader, a futures-style CFD carries no expiry field.** It only turns "close only" through a trading-mode change event (research 32 §3.1 case E4, CHECKED in the protocol file).
- **Hyperliquid HIP-3 perps** follow stock indices too. They never expire, trade 24/7, charge funding every hour, and have their own public order book (research 02 §8.2, research 38 §3.8).

### 3.3 What trading them needs from a unit

| Need | Why | Where the fact comes from |
| --- | --- | --- |
| Contract size, tick size and tick value per instrument | Money per point is what sizing uses | research 32 §1.3; venue specs |
| Which contract is live now, and the roll date | Liquidity moves on the roll | exchange calendar (research 32 §3.2: `roll_source` default exchange calendar) |
| The ending of every instrument (expiry, close-only date, settlement) | A unit holding through it must see the forced close, in backtest too | research 32 §3.2 |
| Sessions in the exchange's own time zone, plus halts and holidays | 9:30 New York matters more than the CFD's 23-hour schedule | research 02 §4.2; research 32 §1.5 |
| Intraday versus overnight margin | Margin jumps at the session close | broker page |
| A data entitlement check (does this machine have depth or the tape?) | Order-flow logic must not run on data that is not there | research 02 §7.4 |
| Price-limit state | Limit-down halts | research 02 §7.5 |
| Index CFD extras: financing, dividend cash events, per-index breaks, synthetic out-of-hours prices | They change P&L and fills | research 02 §4.4 |

### 3.4 What trading them needs from the data

- History that says how contracts were stitched (back-adjusted or not) and where each roll falls (research 12 §3 item 11).
- For order-flow units: trades with aggressor side, depth, and ideally the full order book, recorded with exchange time and receive time (§1).
- For a CFD unit reading futures as a proxy: both series on one clock, and the measured gap between them (research 38 §4, research 32).
- Exchange fees are per month and per exchange, never per unit (round 2 explainer, `explainers/round2/src/pages-b.mjs:125`).

---

## 4. Clocks across regions

### 4.1 Facts

| Fact | Detail | Origin | Source |
| --- | --- | --- | --- |
| DST dates, 2026 | London: summer time 29 Mar 01:00Z, back 25 Oct 01:00Z. New York: 8 Mar 07:00Z, back 1 Nov 06:00Z. Chicago: 8 Mar 08:00Z, back 1 Nov 07:00Z. Sydney: back 4 Apr, forward 3 Oct. Singapore, Tokyo, Nairobi: no change | **new** | computed today with Python `zoneinfo`, tzdata 2025.2 (CHECKED command) |
| DST dates, 2027 | London 28 Mar and 31 Oct; New York and Chicago 14 Mar and 7 Nov | **new** | same command |
| The mismatch weeks | Between the US and UK changes, London and New York are 4 hours apart instead of 5: 8 to 29 Mar 2026 and 25 Oct to 1 Nov 2026 (this week). A rule written as "London 13:00 = New York open" is wrong for those weeks | **new** | INFERRED from the dates above |
| Singapore against London | Singapore is UTC+8 all year; London is UTC+0 in winter, UTC+1 in summer. So Singapore is 8 hours ahead in winter and 7 in summer | **new** | INFERRED from the dates above |
| His machines | Windows zone "E. Africa Standard Time" (UTC+3, no DST); WSL zone Africa/Nairobi | **new** + earlier | `tzutil /g` (CHECKED today); research 38 §2 |
| His Windows clock sync | Windows Time service stopped, start type Manual; `SpecialPollInterval` 16384 s | **new** | `Get-Service w32time`; registry `W32Time\TimeProviders\NtpClient` (CHECKED today) |
| His WSL clock | "System clock synchronized: no" | earlier | research 31 §6.1 (CHECKED 30 Oct) |
| Windows accuracy | Windows 10 and later can deliver 1 s, 50 ms or 1 ms accuracy only under listed conditions (for 50 ms: under 5 ms network latency to the time source, stratum 5 or better) | **new** | https://learn.microsoft.com/en-us/windows-server/networking/windows-time-service/support-boundary (CHECKED) |
| chrony and timesyncd | chrony is preferred over `systemd-timesyncd`, which cannot poll several servers or spot a bad one; Ubuntu 24.04 ships timesyncd, so QMN's provisioning installs chrony | **new** + earlier | https://chrony-project.org/faq.html §1.2 (CHECKED); node spine TN-14 |
| chrony on Windows | The chrony FAQ has a section "Does chrony support Windows?" (answer read as no, INFERRED) | **new** | same FAQ §8.1 |
| Leap smear | Google and AWS spread a leap second over 24 hours, noon to noon UTC. Smeared and non-smeared time differ by up to about half a second during a smear, so sources must not be mixed | **new** | https://developers.google.com/time/smear (CHECKED); QMN rule "no smearing sources" (node spine TN-14) |
| Industry benchmark | EU RTS 25 (Regulation 2017/574): members' clocks within 1 ms of UTC for ordinary algorithmic trading, 100 µs for high-frequency trading. Repealed from 1 Mar 2026 by Regulation 2025/1155. It never bound him; it shows what firms aim for | **new** | https://eur-lex.europa.eu/eli/reg_del/2017/574/oj/eng (CHECKED) |
| cTrader time | Unix milliseconds in UTC; no server clock exists on the Open API, so receive time is recorded on every message | earlier | `packages/qmf-venue/src/qmf/venue/ctrader.py:14-17` (G3 §2.1) |
| Broker server time | IC's server runs at GMT+2 in winter and GMT+3 in summer (aligned to New York's 17:00 rollover, INFERRED) | earlier | research 32 §1.5, research 02 §1 |
| Exchange time | CME hours and expiries are stated in Chicago time; cash index opens in New York time | earlier | research 02 §7.1 |
| Calendars | cTrader gives each symbol a weekly schedule with its own time zone and a holiday list; open-source calendars exist (`pandas_market_calendars` has CME, ICE, EUREX, LSE and others) but can lag the exchange: its docs still show a CME equity break of "4:15 - 4:35 (NY)" | earlier + **new** | research 32 §1.5; context7 `/rsheftel/pandas_market_calendars` (CHECKED) |
| Signed actions with time windows | Hyperliquid rejects actions whose nonce falls outside the window around block time, so a drifting clock breaks trading there | earlier | research 38 §3.8 |
| The time zone database | QMX pins `tzdata` 2025.2; the latest on PyPI is 2026.6. Windows has no system tz database, so Python on Windows reads the `tzdata` package | **new** | `uv.lock:2002-2003`; https://pypi.org/project/tzdata/ (CHECKED); Windows reliance INFERRED |
| What QMN already does | Host clock is the only stamper, UTC stored, local time never stored as a stamp; chrony with 4+ sources; no trade before sync; four bands with evidence values 25 ms warn, 100 ms no new entry, 250 ms halt, an ok band at 10 ms or less; broker skew measured apart and never called latency | earlier | node spine TN-14; `qmn/src/qmn/time/discipline.py:1-7` |
| What the QMX host does | Cron triggers run in a named IANA zone with cron's own DST rules (a skipped time runs once after, a repeated time runs once); every instant leaves in UTC. No clock-sync check | earlier + **new** | `qmx-agents/packages/qmx-engine/src/qmx_engine/triggers/cron.py:1-7`; G3 §0 item 6 |
| One clock per job | The round 2 explainer proposed one clock per job (scalper ticks, session plans, slow labels on days or events) instead of one "5 trading days" plan clock | earlier | `explainers/round2/src/pages-b.mjs:86-92` |

### 4.2 Standard practice (INFERRED from the facts above, options not a design)

1. **One time scale for every stamp: UTC.** Every journal row, order, fill and log line carries UTC. Local time is computed for display and for session rules, from the instant plus a named zone and a tz database version. QMN already rules this (TN-14).
2. **Two times on every market event: the venue's time and the receive time.** cTrader gives only the receive time, so the machine's clock is the measurement. The gap between the two (skew) is watched, not corrected.
3. **Every machine disciplines its clock and reports its own offset.** Linux servers: chrony with several sources, no smeared sources. Windows: the Windows Time service running, or an NTP client, with its offset read and reported. A machine that cannot prove its offset marks its data as recorded while unsynchronised.
4. **Sessions live in the market's zone, not the node's.** "London open" is a London-zone rule, "CME close" is a Chicago-zone rule. A node in Singapore and a node in London compute the same session from the same instant. The node's own local time never enters a rule. His analogy of the node as a firm with its own office time fits the display, not the rules.
5. **The trading day is the venue's day boundary**, for example 17:00 New York for FX at many brokers, measured per broker (G3 §2.1).
6. **Calendars come from the exchange or the venue and are versioned**, with a maximum age before they count as suspect.
7. **Monitoring several nodes together:** every node sends UTC stamps, its clock band and its heartbeat; the screen shows each in the viewer's chosen zone. A node whose clock is off is shown as such, not silently merged.

### 4.3 Numbers to name (starting defaults, all editable)

| Number | Starting default | Why that start | Origin |
| --- | --- | --- | --- |
| `clock_drift_warn` | 25 ms | QMN registry evidence value, sized for about one-second decisions | earlier (TN-14) |
| `clock_drift_no_new_entry` | 100 ms | same | earlier |
| `clock_drift_halt` | 250 ms | same | earlier |
| `clock_unsynchronized_after` | not set in the files read | QMN names the row; value owed | earlier |
| `clock_skew_warn_ms` (receive clock against a time server) | 100 ms | research 33 §2 | earlier |
| `calendar_max_age_days` | 31 | one monthly futures cycle | earlier (research 32 §3.2) |
| `tzdata_max_age_days` before the pin is flagged | 180 | IANA ships several releases a year; 2025.2 to 2026.6 shows the drift (INFERRED) | **new** |
| `dst_mismatch_notice_days` (warn before a US/UK or other zone mismatch week starts) | 7 | the mismatch weeks are 1 to 3 weeks long (INFERRED) | **new** |
| `heartbeat_interval_s` per node | 60 | one-minute bars are the shortest decision step in scope (INFERRED); the QMN cadence value was not found in the files read | **new** |

---

## 5. Questions this raises (for the funnel; tagged)

| Id | Question | Tag |
| --- | --- | --- |
| F-01 | Real futures traded, or futures order flow read as a signal for CFD units, or both? (research 38 V-02) | operator, money (data fees) |
| F-02 | Does Databento's personal CME licence cover an algorithm that places orders (personal non-display use)? Ask Databento | research |
| F-03 | Which FCM accepts his country for Rithmic or CQG access? (research 38 V-01) | research once he names his country |
| F-04 | Can Rithmic's Protocol API run on a demo or paper account with live data, for the PC rehearsal? | research |
| F-05 | Which component owns a market's calendar (CME, ICE, Eurex, crypto 24/7, per-index CFD breaks), and how is it refreshed? | lead |
| F-06 | Does the QMX host on Windows check and report its own clock offset, as QMN does on Linux? | lead |
| F-07 | Hyperliquid's 20-level book and about 5 s snapshot: enough for the order-flow scalper types, or do they need trades only? | lead (research 02 §11) |

## 6. Not verified

- Databento's personal licence for algorithmic (non-display) use of CME data.
- Sierra Chart on Linux or Mac (Wine) was not read on Sierra's own pages.
- ATAS, Bookmap and dxFeed prices came from third-party pages or a 2024 promotion.
- Quantower's All-in-One price showed only as "70"; currency and period assumed USD a month.
- Rithmic's FAQ and its paper-account rule were read only through secondary pages.
- CQG WebAPI pricing for a retail user (listed as "Contact us").
- Hyperliquid's official definition of `side` (the docs give the field; the taker meaning is from a third party).
- The answer under chrony FAQ §8.1 was not read in full.
