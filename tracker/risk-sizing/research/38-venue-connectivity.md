# 38: Venue connectivity: who gives which markets and data, and how QMX connects

Ticket: `wayfinder/tickets/research-venue-connectivity.md`. Written 2026-10-30 by research agent 3. Facts and options only, no design and no choice.

## How to read this

- **CHECKED** means read today at the URL, file or command named. **INFERRED** means reasoned from checked facts. **SECONDARY** means read today, but on a third-party page, not the vendor's own.
- Prices and limits are the vendors' own. None is a QMX cap.
- This file answers *who sells or gives which data* and *who places the order*. Contract facts per instrument (minimum lot, money per point, margin, expiry) are in research 32. History depth, data terms and disk are in research 33. The node and the path from signal to order are in research 31.
- His words this answers (verbatim, `operator/transcript-2026-10-29-to-30.md`, 30 Oct 06:19 and 06:42): "How am I trading futures? Can I trade futures on CTrader? With order flow and stuff? Then of course, Hyperliquid"; "who can provide that"; CCXT is "mostly for brokers. In other words, trade execution."

## 0. The short answer

1. **cTrader does not trade real exchange futures at IC Markets, and no cTrader broker offering them through the Open API was found.** cTrader is a CFD platform. IC Markets offers its futures-based CFDs only on MetaTrader 4 and 5, not on cTrader (CHECKED https://www.icmarkets.com/global/en/trading-markets/futures). A 2016 Spotware forum reply says futures are possible if a broker adds them; none was found in 2026 (CHECKED https://prod.ctrader.com/forum/ctrader-support/8295/).
2. **cTrader gives quotes, displayed depth with sizes, bars and his own fills. It gives no market-wide trades tape, no real volume, no open interest.** So footprint, delta and absorption cannot be computed from cTrader data (research 21 §3, CHECKED; re-read today in the protocol files, §3.1).
3. **Real futures with order flow at retail size come through a futures broker (an FCM) plus a data route.** The cheapest checked path: an FCM such as AMP Futures with Rithmic (USD 25 a month connection, USD 0.10 per side routing, CME depth bundle USD 45 a month non-pro) or NinjaTrader/Tradovate (API USD 25 a month, USD 1,000 live minimum). Each has a hard catch, listed in §3.
4. **Tradovate's API places orders but does not give market data.** Streaming CME data through it needs a CME sub-vendor licence (CHECKED https://support.ninjatrader.com/s/article/Tradovate-API-Access). So with Tradovate, data must come from elsewhere (Databento, or the Rithmic or CQG feed of another account).
5. **TopstepX (a prop firm) forbids running order code on a remote server or VPS.** That rules out its use from a trading node (CHECKED https://help.topstep.com/en/articles/11187768-topstepx-api-access).
6. **Interactive Brokers works, but its API needs a running desktop program with a manual login**, restarts daily, re-asks the login weekly, and allows only 3 depth books and 5 tick-by-tick streams at the default 100 data lines (CHECKED §3.6).
7. **Hyperliquid gives the most data for free:** trades, 20-level book, funding, open interest, mark and oracle prices, with no key. Its trading key (an "API wallet") can trade but cannot withdraw, expires after at most 180 days, and the venue has a dead man's switch. Its terms bar people located in the United States, Ontario or sanctioned places (all CHECKED §3.8).
8. **cTrader already offers a view-only live grant** (scope `accounts`), and QMX's stacked code already accepts it on the PC while refusing a grant that can trade live (CHECKED, §6). So "shadow runs on live prices on the PC" is possible at cTrader today in code, which answers an open point in research 43 §3.6.
9. **MT5 adds stock CFDs and futures CFDs at IC Markets, and real CME futures at AMP Futures (top of book only on MT5).** Its Python link runs only on Windows, against a running terminal (CHECKED §3.2).
10. **His country and account sizes are not in the files I read.** His PC's Linux clock is set to Africa/Nairobi (CHECKED `timedatectl` in his WSL, §2). Eligibility for every venue in this file depends on where he lives: an open question for him, not a guess for me.

---

## 1. Two questions, kept apart

His 30 Oct point (STATE "Data versus execution"): who provides order flow and other data is separate from who executes. A unit can read data from one place and trade through another. The table in §5 keeps the two columns apart.

| Role | What it is | Examples in this file |
| --- | --- | --- |
| **Data provider** | Sells or gives live and historical market data: quotes, depth, trades tape, volume, open interest, funding | The exchange (through a broker's feed), Databento, Tardis, Binance Vision, Hyperliquid's public feed, Dukascopy, the broker platform's own feed |
| **Execution route** | Holds the account and places the order | cTrader at IC Markets, MT5 at IC Markets or AMP, a futures broker through Rithmic, CQG, Tradovate or IBKR, Hyperliquid, a crypto exchange through CCXT |

Some routes are both (Hyperliquid, Binance, Rithmic, IBKR). Some are execution only for QMX's purposes (Tradovate's API, §3.4). Some are data only (Databento, Tardis, Dukascopy, Binance Vision).

---

## 2. His country, account and machine (what is known)

| Fact | Status |
| --- | --- |
| His country | **Not in the files I read.** His WSL Ubuntu reports time zone Africa/Nairobi, UTC+3 (CHECKED `wsl -d Ubuntu-24.04 -- timedatectl`, 30 Oct). That is a hint of region, not proof of residence. |
| His broker today | IC Markets on cTrader, Spotware Open API app registered 28 Aug, two demo accounts (memory note `qmx-broker-credentials-location.md`, CHECKED; no values read). |
| His machine | Dell Precision 5550 (his words, 30 Oct 07:31), Intel i7-10750H, 16 GB RAM, WSL2 Ubuntu 24.04 and Docker Desktop installed (CHECKED PowerShell `wsl -l -v`, `Get-CimInstance`). |
| Account sizes | Out of scope here (the risk session owns them). |

Why the country matters (INFERRED from the checked terms below):
- Hyperliquid bars persons located in the US, Ontario or sanctioned places (§3.8).
- NinjaTrader Clearing and Tradovate are US FCMs (CHECKED NFA ID on https://ninjatrader.com/pricing/). Whether they open accounts for his country was not checked.
- IC Markets Global, AMP and IBKR accept many countries; his was not checked.
- **Question for him (operator):** which country he lives in, so each route can be checked for eligibility.

---

## 3. The routes, one by one

### 3.1 cTrader Open API (IC Markets)

| Item | Fact | Source |
| --- | --- | --- |
| What it trades | FX, metals, index, commodity and crypto CFDs at IC (no stock CFDs, no futures CFDs on cTrader at IC) | CHECKED https://www.icmarkets.com/global/en/trading-markets/stocks (stocks "exclusively" MT5); futures page above |
| Real futures | None found on any cTrader broker through the Open API; review sites say cTrader has no exchange futures | CHECKED (SECONDARY) https://www.newtrading.io/ctrader-review/ ; https://bulltraders.com/platforms/ctrader/ |
| Live data | Spot quotes (bid and ask, each optional per event), live trendbars inside spot events, depth as differential quote updates with sizes | CHECKED `ProtoOASubscribeSpotsReq`, `ProtoOASubscribeDepthQuotesReq` in https://raw.githubusercontent.com/spotware/openapi-proto-messages/main/OpenApiMessages.proto ; research 21 §3 |
| Not given | Market trades tape, real volume, open interest, funding | CHECKED: no such subscription in the protocol file; `ProtoOADealListReq` is the trader's own deals |
| History given | Trendbars by period with `count` and `hasMore`; ticks one side (bid or ask) per request, one week per request | CHECKED `ProtoOAGetTrendbarsReq`, `ProtoOAGetTickDataReq` in the protocol file; research 21 §3. Total retention per broker: unknown, must be measured (research 33) |
| Rate limits | 50 requests a second per connection, 5 a second for history | CHECKED https://help.ctrader.com/open-api/ |
| Endpoints | `live.ctraderapi.com` and `demo.ctraderapi.com`, port 5035 (Protobuf) or 5036 (JSON), TCP or WebSocket, behind AWS Global Accelerator. Demo and live are fully separate; using both needs two connections | CHECKED https://help.ctrader.com/open-api/proxies-endpoints/ |
| Sign-in | OAuth. Access token about 30 days (2,628,000 s); refresh token never expires | CHECKED https://help.ctrader.com/open-api/account-authentication/ |
| Grant scopes | `accounts` = view only, no trading possible; `trading` = full | CHECKED same page |
| Token danger | A refresh invalidates the old token's sessions (`ProtoOAAccountsTokenInvalidatedEvent`) | CHECKED research 14 §9.1 (help.ctrader.com messages page) |
| App approval | Spotware reviews each new app; "usually around 24 hours" (forum, 2023); 24 to 48 hours (a vendor guide) | CHECKED https://help.ctrader.com/open-api/api-application/ ; SECONDARY https://communityuat.ctrader.com/forum/connect-api-support/41605 , https://clickalgo.com/open-api-configuration |
| Broker can switch it off | Brokers may disable Open API for their clients | CHECKED (Spotware, 2019) https://community.ctrader.com/forum/announcements/14832/ |
| Dead man's switch | None in the protocol (no cancel-on-disconnect message) | CHECKED: protocol file has order cancel only; `ProtoOAClientDisconnectEvent` is the server cutting the app |
| Withdrawals | No withdrawal request exists in the protocol | CHECKED (absence) in the protocol file. INFERRED: a trading token can lose money by trading but cannot move it out |
| Machine | Any OS; plain TCP or WebSocket with Protobuf or JSON. QMX's own client speaks Protobuf over asyncio TLS | CHECKED `packages/qmf-venue/src/qmf/venue/connection.py:1-17` at `origin/engine/base` |
| Measured from his PC | TCP connect to `live.ctraderapi.com:5035`: median 167 ms (156-203, n=8); demo median 156 ms (n=8) | CHECKED, script in scratchpad, 30 Oct. Limiter INFERRED: the network path from East Africa to the nearest Spotware proxy; a TCP handshake is one round trip, so an order's round trip is at least this |

### 3.2 MetaTrader 5 (IC Markets, AMP Futures)

| Item | Fact | Source |
| --- | --- | --- |
| What it adds at IC | 2,100+ stock CFDs (ASX, NYSE, NASDAQ) and the futures-based CFDs (VIX, DXY, Brent, WTI and commodities), MT4/MT5 only | CHECKED IC stocks and futures pages |
| Real futures | AMP Futures runs MT5 for CME and Eurex futures through a CQG gateway; on MT5 only the CME top-of-book bundle is available (no depth) | CHECKED https://faq.ampfutures.com/hc/en-us/articles/17160615763607 ; https://faq.ampfutures.com/hc/en-us/articles/360000579848 |
| Live data | Ticks, bars, depth where the broker sends it (`market_book_add`), real volume and session open interest fields where the broker fills them | CHECKED https://www.mql5.com/en/docs/python_metatrader5 ; symbol fields on https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfo_py |
| API shape | The Python package talks to a running MT5 terminal over local inter-process calls; no push callbacks (poll or an EA pushing over a socket) | CHECKED (functions list above); push detail from research 12 §4.1 |
| Machine | Windows (MetaQuotes points to the Windows Python installer); Linux only through Wine | CHECKED the install step on the Python page; Wine INFERRED |
| What it blocks | One terminal per account; a Windows machine for every MT5 unit (node question N-11 in `live-field.md`) | INFERRED |

### 3.3 Rithmic (through a futures broker such as AMP)

| Item | Fact | Source |
| --- | --- | --- |
| What it is | Data feed and order routing to CME, CBOT, NYMEX, COMEX and other venues; used by NinjaTrader and many prop firms | CHECKED https://www.rithmic.com/solutions/builders ; SECONDARY https://proptradingsoftware.net/blog/best-futures-prop-firm-platforms-compared/ |
| APIs | R\|API+ (C++/.NET libraries), R\|Protocol API (WebSockets plus Protocol Buffers, any language, any OS), R\|Diamond (co-location) | CHECKED https://tradefutures4less.com/rithmic-protocol/ (FCM reprint of Rithmic text); SECONDARY https://pickmytrade.io/help/rithmic/rithmic-api-overview/ |
| Access | Ask Rithmic; test credentials; a conformance check before production; personal use is a stated option. Reported 1-2 days for test access, 3-5 days for conformance | SECONDARY https://github.com/rundef/async_rithmic/issues/42 (user report, 2026) |
| Test environment | "Rithmic Test" before approval; Rithmic markets an exchange simulator | CHECKED rithmic.com builders page; SECONDARY the issue above |
| Catch | Protocol API is reported unavailable for paper accounts that carry live market data | SECONDARY pickmytrade.io (cites the Rithmic FAQ; FAQ not read) |
| Data | Live ticks, depth, trades; history plant for historical ticks | SECONDARY https://github.com/jacksonwoody/pyrithmic (plant names) |
| Server-side risk | Rithmic markets auto-liquidation, position limits and loss thresholds enforced on its side | CHECKED rithmic.com builders page |
| Costs at AMP | Rithmic connection USD 25 a month per user id; routing USD 0.10 per side per contract; CME depth bundle USD 45, top of book bundle USD 15, single exchange depth USD 17 (non-pro, not prorated; data switched off below USD 100 equity at month end) | CHECKED https://www.ampfutures.com/trading-info/exchange-data-fees (prices from 1 June 2026) |
| Python | Community clients exist (async_rithmic, pyrithmic, a Rust crate) | CHECKED repo pages above |

### 3.4 NinjaTrader and Tradovate

| Item | Fact | Source |
| --- | --- | --- |
| Who | NinjaTrader LLC (software) and NinjaTrader Clearing (a US FCM, NFA 0309379) | CHECKED https://ninjatrader.com/pricing/ |
| Plans | Free (USD 0.39 micro per side), Monthly USD 99, Lifetime USD 1,499; top-of-book data included once funded; Order Flow+ in the platform | CHECKED same page |
| Margins | USD 50 intraday for micro index futures, USD 500 for E-minis | CHECKED same page |
| Tradovate API | Add-on USD 25 a month; needs a live funded account with at least USD 1,000; prop and evaluation accounts excluded | CHECKED https://support.ninjatrader.com/s/article/Tradovate-API-Access ; https://api.tradovate.com/ |
| Data through the API | **Not included.** Streaming market data through the API needs a CME Information License Agreement as a sub-vendor | CHECKED same support article |
| Shape | REST plus WebSocket; separate hosts for live, demo (simulation) and market data | CHECKED https://api.tradovate.com/ |
| Connections | One simultaneous client connection per customer; more by subscription; the oldest is disconnected at the limit | CHECKED same page |
| Heartbeat | Client sends one every 2.5 s | CHECKED same page |
| Desktop platform | NinjaTrader Desktop runs NinjaScript (C#) strategies | INFERRED, not read today (Windows only, from general knowledge) |

### 3.5 CQG

Reached through FCMs (AMP lists CQG data prices beside Rithmic, §3.3). CQG's own API pages were not read today. Not verified.

### 3.6 Interactive Brokers

| Item | Fact | Source |
| --- | --- | --- |
| API shape | TWS API connects to a running TWS or IB Gateway; headless running is not supported; the user types the login | CHECKED https://interactivebrokers.github.io/tws-api/initial_setup.html |
| Restarts | Both restart daily; auto-restart can run Sunday to Sunday; login again after the Saturday night reset | CHECKED same page |
| Data lines | 100 by default; at 100 lines: 5 tick-by-tick streams, 3 depth books | CHECKED https://www.interactivebrokers.com/docs/general/market-data-subscriptions/market-data-lines/specialized-market-data-lines |
| Data needs | Trading permission, a funded account, a paid subscription per username; billed for the full month | CHECKED https://interactivebrokers.github.io/tws-api/market_data.html |
| History limits | No bars of 30 s or less older than six months; no expired futures older than two years; no time and sales beyond three years; pacing limits (60 requests per 10 minutes for small bars) | CHECKED https://www.interactivebrokers.com/docs/tws-api/doc/md/introduction.md |
| Markets | Futures, stocks, FX and more in one account | CHECKED setup page |
| Machine | TWS and Gateway are Java (they run on Linux); the manual login makes a server node awkward | CHECKED "Java-based" on the setup page; awkwardness INFERRED |

### 3.7 TopstepX / ProjectX (prop firm)

| Item | Fact | Source |
| --- | --- | --- |
| Cost | USD 29 a month (USD 14.50 with the Topstep code) | CHECKED https://help.topstep.com/en/articles/11187768-topstepx-api-access |
| Data | Quotes, trades and depth through a SignalR market hub | CHECKED https://gateway.docs.projectx.com/docs/realtime/ |
| **Block** | VPS, VPN and remote servers are prohibited for order flow: "your server can watch and record, but it cannot trade" | CHECKED Topstep article |
| Block | Live funded accounts cannot trade through the API; it serves the simulated environment | CHECKED Topstep article |
| Money | Evaluation money, not his brokerage account | CHECKED Topstep article |

INFERRED: TopstepX can be a data source on a server, and a PC-only execution route, never a trading-node route.

### 3.8 Hyperliquid (perps, HIP-3 perps on stocks, indices, gold and FX, spot)

| Item | Fact | Source |
| --- | --- | --- |
| Contract | Linear perps, 1 unit of the underlying, USDC collateral, USDT oracle for most (quanto); funding every hour; no expiry | CHECKED https://hyperliquid.gitbook.io/hyperliquid-docs/trading/contract-specifications |
| Live data, free, no key | Trades, `l2Book` (20 levels, about every 5.4 s), `fastBook` (5 levels, about every 500 ms, since 17 Jun 2026), `bbo`, `activeAssetCtx` (funding, open interest, mark) | CHECKED https://docs.tardis.dev/historical-data-details/hyperliquid (channel list); research 02 §8.3 |
| Per-IP limits | REST 1,200 weight a minute (`l2Book` 2, most info 20); 10 websockets; 30 new a minute; 1,000 subscriptions; 10 users across user streams; 2,000 messages sent a minute; 100 in-flight posts | CHECKED https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits |
| Per-address limits | 1 action per USDC traded since the address opened, plus 10,000 at start; when limited, 1 per 10 s; cancels get extra room; batched orders count as one for the IP and n for the address | CHECKED same page |
| Open orders | 1,000 default, +1 per USD 5M volume, at most 5,000; above 1,000 open, new reduce-only and trigger orders are rejected | CHECKED same page |
| Congestion | Addresses limited to 2x their previous day's maker share of block space | CHECKED same page |
| Trading key | API ("agent") wallets sign trades for the master; they cannot withdraw, transfer or approve agents; 1 unnamed plus up to 3 named per account; expiry at most 180 days | CHECKED approve-agent rules https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint ; cannot withdraw: SECONDARY https://docs.chainstack.com/reference/hyperliquid-exchange-approve-agent , https://www.openfort.io/docs/recipes/hyperliquid/agent-wallets |
| Nonces | 100 highest kept per signer; must lie within (block time minus 2 days, plus 1 day); one agent per trading process recommended | CHECKED https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets |
| Dead man's switch | `scheduleCancel`: cancels **all open orders** at a set time, at least 5 s ahead, at most 10 triggers a day (reset 00:00 UTC) | CHECKED exchange endpoint page |
| Testnet | Exists (testnet margin tiers and a "Testnet" chain value) | CHECKED https://hyperliquid.gitbook.io/hyperliquid-docs/trading/margin-tiers ; exchange endpoint page |
| History | Candles: last 5,000 only; S3 archive (research 33) | research 02 §8.3, CHECKED 27 Oct |
| Terms | Interface not available to persons located in the US, Ontario, sanctioned places, or citizens of sanctioned places; no licence anywhere | CHECKED https://app.hyperliquid.xyz/terms (updated 15 Jun 2026) §1.3, §1.6 |
| Measured from his PC | TCP connect to `api.hyperliquid.xyz:443`: median 31 ms (n=8); a full new HTTPS `allMids` request 306-801 ms (n=6) | CHECKED script, 30 Oct. Explained: the 31 ms is the handshake with a nearby edge; the full request includes a fresh TLS handshake and the trip to the API origin, so a kept-open websocket sits between the two (INFERRED) |
| In QMX code | None | CHECKED research 18 §8 (`git grep -i hyperliquid` = 0) |

### 3.9 Centralised crypto exchanges through CCXT (Binance, Bybit and others)

| Item | Fact | Source |
| --- | --- | --- |
| Data | Trades, books, funding, open interest per exchange; bulk history files (research 33) | research 12 §4.1 (CHECKED 27 Oct) |
| Binance futures dead man's switch | `countdownCancelAll` per symbol (USD-M); a heartbeat call resets the timer | CHECKED (SECONDARY spec mirror) https://rd0pguxv2g.apifox.cn/348629263e0 ; Binance options version https://developers.binance.com/docs/derivatives/options-trading/market-maker-endpoints/Set-Auto-Cancel-All-Open-Orders-Config |
| Bybit dead man's switch | Disconnect-cancel-all (window 3-300 s, default 10 s), **institutional clients only** | CHECKED https://bybit-exchange.github.io/docs/v5/order/dcp |
| Bybit cancel-all | Futures cancel-all takes up to 500 orders, picked at random above that | CHECKED https://bybit-exchange.github.io/docs/v5/order/cancel-all |
| Binance connection rules | Every websocket cut at 24 hours; 1,024 streams per connection | research 12 §4.1, CHECKED 27 Oct |
| Measured from his PC | TCP connect to `fapi.binance.com:443` median 37 ms; `api.bybit.com:443` median 32 ms (n=8 each; edges) | CHECKED script, 30 Oct |
| In QMX code | CCXT spot reads only; contract markets refused | research 02 short answer 6, research 18 §8 (CHECKED) |
| Country | Not checked for his country | open |

### 3.10 Data-only providers

| Provider | What | Price and terms (vendor's) | Source |
| --- | --- | --- | --- |
| **Databento** | CME, CBOT, NYMEX, COMEX: 650,000+ symbols; live and history; trades, top of book, depth (MBP-10), full order book (MBO) | Pay per GB for history; Standard plan: 16+ years of bars, last 12 months of L1 and trades, last month of L2 and L3, personal use on up to 2 devices; Plus USD 1,750, Unlimited USD 4,500 a month; USD 125 free credits. The Standard price did not render in today's fetch; research 12 read USD 199 a month on 27 Oct | CHECKED https://databento.com/pricing |
| **Tardis.dev** | Tick trades, book updates, snapshots, funding, open interest, liquidations for 30+ perp venues incl. Hyperliquid (since 29 Oct 2024; HIP-3 since 2 Dec 2025) | Solo (CSV files only) and higher; history reach set by billing: monthly 4 months, quarterly 12 months, yearly 4 years; first day of each month free. Perpetuals Solo quoted at USD 700 a month (SECONDARY) | CHECKED https://docs.tardis.dev/faq/billing-and-subscriptions , https://docs.tardis.dev/historical-data-details/hyperliquid ; SECONDARY https://cryptomarkets.tools/compare/tardis-dev-vs-0xarchive |
| **Binance Vision** | Binance spot and futures bulk files | Free, but new dataset terms (26 Aug 2026), research 33 §3 | CHECKED https://github.com/binance/binance-public-data |
| **Dukascopy** | FX, metals, indices, stocks, crypto history | Site terms, research 33 §3 | CHECKED (33) |
| **The FCM's feed** | CME data through Rithmic, CQG or TT at the FCM's prices (§3.3) | Per user id, not prorated | CHECKED AMP page |

---

## 4. Which data exists where (data levels per class)

The data levels follow research 43 F6 (0 calendar, 1 bars, 2 quote ticks, 3 depth, 4 trades tape, 5 derivatives fields such as funding and open interest, 6 outside data).

| Class | Level 2 quotes | Level 3 depth | Level 4 tape and real volume | Level 5 OI, funding | Where level 4-5 come from |
| --- | --- | --- | --- | --- | --- |
| FX CFDs | cTrader, MT5 | cTrader (displayed broker depth) | **No** (OTC; tick volume only) | No | Nowhere for spot FX. CME FX futures (6E, M6E) are a proxy (research 32) |
| Metals CFDs | cTrader, MT5 | cTrader | No | No | COMEX gold futures (GC, MGC) as a proxy |
| Index CFDs | cTrader, MT5 | cTrader | No | No | CME index futures (ES, MES, NQ) as a proxy |
| Real futures | FCM feed, Databento, IBKR | FCM feed (paid), Databento | **Yes** | OI daily from the exchange (INFERRED); MT5 field where filled | The exchange, through the FCM or Databento |
| Stock CFDs (IC MT5) | MT5 | Broker-specific | No (CFD) | No | The stock exchange tape (not checked; would need a stock data vendor) |
| Crypto spot | Exchange | Exchange | Yes | No | The exchange; Binance Vision; Tardis |
| Crypto perps | Exchange, Hyperliquid | Exchange, Hyperliquid | Yes | **Yes** | The venue itself; Tardis for deep history |
| HIP-3 perps (stocks, gold, FX, indices) | Hyperliquid | Hyperliquid | Yes (on Hyperliquid's own book) | Yes | Hyperliquid; Tardis |

INFERRED: order flow at the "true volume" level exists only for real futures, crypto and Hyperliquid's HIP-3 books. For FX, metals and index CFDs it exists only as a proxy from another market, which is the "proxy-data unit" idea B053 in `live-field.md`. The gap between proxy and traded market (basis) is a research 32 question.

---

## 5. The table: market type × route

"Cost" is the vendor's own monthly cost for the route, excluding commissions. "Machine" is what the route needs to run.

| Market | Route | Trades | Live data given | History given | Cost and minimum | API and limits | Machine | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FX, metals, index CFDs | cTrader at IC | Yes | Quotes, depth with sizes, bars | Bars, one-side ticks by week | Platform free; no API fee | 50/s, 5/s history; one live and one demo connection advised | Any OS | §3.1 |
| FX, metals, index CFDs | MT5 at IC | Yes | Ticks, bars, depth if sent | Terminal history | Free | Local terminal calls | Windows | §3.2 |
| Stock CFDs | MT5 at IC | Yes | Ticks, bars | Terminal history | Free | Same | Windows | §3.2 |
| Futures CFDs (VIX, DXY, oil, softs) | MT5 at IC | Yes, expire 2 working days early, never rolled | Ticks | Terminal | Free | Same | Windows | research 32 |
| Real CME/Eurex futures | MT5 at AMP (CQG gateway) | Yes | Top of book only on MT5 | Terminal | CME L1 bundle USD 15 | Same | Windows | §3.2, §3.3 |
| Real futures | Rithmic via an FCM (AMP and others) | Yes | Ticks, depth, trades | History plant | USD 25 connection + USD 0.10/side + data (USD 45 CME depth bundle) | Protocol API, conformance first | Any OS | §3.3 |
| Real futures | Tradovate API | Yes | **None through the API** without a CME licence | None | USD 25 API + USD 1,000 live minimum | REST/WebSocket; 1 connection | Any OS | §3.4 |
| Real futures | IBKR | Yes | Quotes; 3 depth, 5 tick streams at 100 lines | Limited (§3.6) | Data per username, full month | Socket to TWS/Gateway | Java, GUI login | §3.6 |
| Real futures | TopstepX (prop) | Sim/eval only, PC only | Quotes, trades, depth | Some | USD 29 (14.50) | SignalR | **Not from a server** | §3.7 |
| Crypto perps, HIP-3 | Hyperliquid | Yes | Trades, book, funding, OI, mark | 5,000 candles; S3 archive | Free; fees per trade | Per-IP and per-address limits | Any OS | §3.8 |
| Crypto spot and perps | Binance, Bybit via CCXT | Yes (QMX: spot only today) | Trades, book, funding, OI | Bulk files (33) | Free | Per exchange | Any OS | §3.9 |
| CME data only | Databento | No | Trades, L1, L2, L3 | 16+ years bars; more by plan | Standard plan (USD 199 per research 12) or per GB | Live TCP | Any OS | §3.10 |
| Perps data only | Tardis | No | Replay of live | 4 months to all years by plan | From about USD 700 (SECONDARY) | CSV, API from Professional | Any OS | §3.10 |

---

## 6. How live data reaches QMX, per route, and what the node must hold

| Route | Connections | Sharing between PC and node | Token and key rules | What a trading node holds | Source |
| --- | --- | --- | --- | --- | --- |
| cTrader | One per app per environment (live and demo are separate hosts). No symbol cap; one connection carries every symbol | A second machine on the **same grant** risks logging the first out on refresh. Options from research 14 §4.5: a lease, two apps, or split by environment | Access token about 30 days; refresh token never expires; refresh invalidates the old one | The live connection, the access token, and the refresh duty (one refresher per grant) | §3.1; research 14 §9.1 |
| cTrader, view-only live | A separate grant with scope `accounts` | The PC can hold it for live prices with no trading power | QMX's read app asks only `accounts` (`oauth.py:31-32` at `origin/build/sy5`; `:29-30` at `origin/engine/base`); stacked code refuses any grant that is not `SCOPE_VIEW` and lists a live account (`adapters.py:103-173`, `can_trade_live` at `:137-146`, `origin/build/sy5`) | Nothing; this is the PC's grant | CHECKED code; scope meaning CHECKED Spotware page |
| MT5 | A terminal per account | Two terminals on one account log in twice (INFERRED; not checked) | Password login in the terminal | A Windows process per account | §3.2 |
| Rithmic | Several WebSocket "plants" (ticker, history, order) per login | Not checked how many concurrent logins one user id allows | Username and password plus approved app name | The plant connections and the login | §3.3 |
| Tradovate | One client connection per customer by default | A second machine disconnects the oldest | API key plus access token | Execution only; data from elsewhere | §3.4 |
| IBKR | A socket to the local TWS/Gateway; data lines are per username across TWS and API | Lines are shared across every session of the username | Manual login, weekly | The Gateway process and its login | §3.6 |
| Hyperliquid | Per IP: up to 10 websockets, 1,000 subscriptions | Each machine has its own IP limits; both can read freely | One API wallet per trading process (own nonce set); the master key never needed on the node | An API wallet key (trade only, expiring) | §3.8 |
| CCXT exchanges | Per exchange; Binance cut at 24 h | Per IP, so both can read | Exchange key; trade-only and IP restriction (INFERRED, not read today) | The exchange key | §3.9 |
| Databento | Live session per key (limits not read) | Personal use on up to 2 devices (Standard) | API key | Optional: a data key | §3.10 |

**What the node therefore holds (INFERRED from the rows):** one feed keeper per (venue, account environment); the execution credential for each live route; the refresh duty for cTrader; a Windows host only if an MT5 unit is live; no master Hyperliquid key; data keys only for paid feeds a live unit declares. The keeper itself is research 31.

---

## 7. Safety features per venue (facts that move the ruling-135 options)

Facts only. The choice about ruling 135 is his.

| Venue | Read-only key for live prices | Trade-only key (no withdrawal) | Key expiry | Dead man's switch | Server-side risk limits | Test environment |
| --- | --- | --- | --- | --- | --- | --- |
| cTrader | **Yes** (`accounts` scope) | Every grant: no withdrawal message exists | Access 30 days; refresh never | **No** | Broker `maxExposure` per symbol field exists (research 32); account limits not found | Demo host |
| MT5 | Investor (read-only) password exists (INFERRED, not read) | Not checked | Not checked | No (INFERRED) | Broker-side | Demo servers |
| Rithmic | Not checked | Not checked | Not checked | Not checked | **Yes**, marketed (loss thresholds, position limits) | Rithmic Test |
| Tradovate | Permission choice at key creation (CHECKED wording only) | Not checked | Not checked | Not checked | Not checked | Demo host |
| IBKR | Not checked | Not checked | Weekly login | Not checked | Not checked | Paper account |
| Hyperliquid | Public data needs no key | **Yes**, API wallets | **Yes**, up to 180 days | **Yes**, `scheduleCancel` (cancels all open orders) | No | Testnet |
| Binance | Not checked today | Not checked today | Not checked | **Yes**, countdown per symbol | Not checked | Testnet (spec mirror lists one) |
| Bybit | Not checked | Not checked | Not checked | Institutional only | Not checked | Testnet (`api-testnet` in docs) |

Hard cases these features raise (INFERRED):
- **A dead man's switch that cancels all open orders also removes protective stop and take-profit orders** where they are resting orders (Hyperliquid's trigger orders are orders). Research 43 §3.6 already says "used only if it spares protective orders, or protection is re-placed after it fires". On Hyperliquid it does not spare them, so re-placing is the only way.
- **cTrader has no dead man's switch**, so protection must already sit on the position (stop and target attached at the broker) before the node can fail.
- **Hyperliquid's address budget** (1 action per USDC traded) is a live constraint for any unit that quotes and cancels. It is the venue's limit, and a unit must read it (research 32 field list).

---

## 8. Options: routes that cover the most for the least setup (not a choice)

Each is judged on standing order 6: hard cases, maintenance, explaining it.

| Option | Covers | Setup | Hard cases | Maintain | Explain |
| --- | --- | --- | --- | --- | --- |
| **A. cTrader + Hyperliquid** | FX, metals, index CFDs at IC; crypto perps and HIP-3 stocks, indices, gold and FX on Hyperliquid, with tape, funding and OI | Two routes; both run on Linux; Hyperliquid data needs no account | Order flow only on Hyperliquid; cTrader has no dead man's switch; Hyperliquid's terms depend on his location | Two adapters, both any-OS | "cTrader for CFDs, Hyperliquid for perps and their order flow" |
| **B. A + Databento as a data-only route** | Adds CME tape and depth as a signal for index and gold CFD units (proxy) | One paid key | Proxy basis must be measured (research 32); licence is personal use, 2 devices | One data adapter | "Read the futures market, trade the CFD" |
| **C. A + one futures FCM via Rithmic** | Adds real futures with depth and tape, traded | Account at an FCM, Rithmic conformance, USD 25 + data a month | Conformance wait; country eligibility; Protocol API on paper accounts reportedly limited | Third adapter, any-OS | "A real futures account, like the pros use" |
| **D. A + MT5 at IC** | Adds stock CFDs and IC's futures CFDs | Windows host for live MT5 units | MT5 forces Windows on the trading side; no push callbacks | A Windows-only adapter | "MT5 for stocks" |
| **E. A + IBKR** | Adds futures, stocks, many exchanges in one account | Desktop program with a manual weekly login | 3 depth books at 100 lines; daily restarts; awkward on a server | Gateway babysitting | "One big broker for everything, with a fussy login" |
| **F. A + Tradovate (execution) + Databento (data)** | Real futures traded, CME data from Databento | Two subscriptions; USD 1,000 minimum | One connection per customer; US FCM eligibility | Two adapters for one market | "Orders through one company, data from another" |

Rejected for a trading node (fails a hard case): TopstepX (no orders from a server).

---

## 9. Questions this raises

| Id | Question | Tag |
| --- | --- | --- |
| V-01 | Which country does he live in, so each route's eligibility can be checked? | operator |
| V-02 | Does he want real futures traded, or futures data used as a signal for CFDs, or both? | operator |
| V-03 | Is MT5 in scope for live units (it forces a Windows trading host), or for research only? | operator |
| V-04 | Rithmic: how many simultaneous logins per user id, and does the Protocol API work on a funded live account for personal use? (ask Rithmic) | research |
| V-05 | Does an IC Markets cTrader account carry any account-level loss limit the broker enforces? | research |
| V-06 | How deep does IC Markets' cTrader trendbar and tick history go per symbol? (measure on demo) | research (33) |
| V-07 | Can the existing Spotware app's approval cover a second app for the trading server, or must it be re-reviewed? (Spotware) | research |
| V-08 | Does Hyperliquid treat a trading server's location (a US data centre) as "located in" for its terms? | research |
| V-09 | Which paid feed, if any, first: Databento, Tardis, an FCM bundle? (already STATE round-2 Q7) | operator |
| V-10 | When a dead man's switch cancels protective orders, who re-places them, and from which machine? | lead |
| V-11 | MT5: does an investor password give live prices with no trading power, as cTrader's view-only grant does? | research |

---

## 10. What QMX's code has today for these routes (CHECKED at `origin/engine/base` d82be318 unless marked)

| Route | Code | Evidence |
| --- | --- | --- |
| cTrader read | Read adapter, view-only OAuth (`SCOPE = "accounts"`) | `qmx-agents/packages/qmx-broker/src/qmx_broker/oauth.py:29-30`; `adapters.py:20-36` declares "one demo and one live connection per registered app" |
| cTrader trading | QMN's live client encodes and submits commands through qmf-venue | `qmn/src/qmn/venue/live.py:1-30`; `packages/qmf-venue/src/qmf/venue/encode.py` (only file outside tests holding `ProtoOANewOrderReq`) |
| cTrader long-running connection | qmf-venue `ConnectionManager` (asyncio TLS, port 5035, 10 s heartbeat, token lifecycle) | `connection.py:454`; `ctrader.py:134-161` |
| Live grant refusal | Refuses a grant that can trade live; allows view-only live | `origin/build/sy5`: `adapters.py:103-173` |
| MT5 | Declaration only | research 18 §8 |
| CCXT | Spot reads only | research 18 §8 |
| Hyperliquid, Rithmic, Tradovate, IBKR | None | research 18 §8 (Hyperliquid); others: `git grep -i -E "rithmic|tradovate|ibapi"` not run beyond research 18's search, so INFERRED none |
| Databento | Key proof only | research 18 §8 |

---

## 11. Not verified

- CQG's own API pages; NinjaTrader Desktop OS needs; MT5 investor-password behaviour; Binance and Bybit key-permission pages; IC Markets' acceptance of his country; Rithmic's FAQ (read only through a secondary page).
- The Databento Standard price today (research 12 read USD 199 on 27 Oct).
- Tardis prices from Tardis itself (its pricing page did not load).
- Whether any other cTrader broker lists exchange futures through the Open API. None found; absence is not proof.
