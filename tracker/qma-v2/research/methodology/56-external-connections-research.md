# 56 — External connections: brokers, platforms, exchanges and data providers

Date: 2026-10-22. Research only. Nothing here is decided, built, merged or committed.

**How this was read.** Official docs, SDK repos and package indexes were fetched today with WebFetch, WebSearch and `curl`. QMX's own code was read read-only at `origin/engine/base` (`8af1a1cd`) with `git show`. Tags: **[retrieved]** = read in that source today; **[local]** = checked in this repo today; **[inferred]** = my reasoning from retrieved facts; **[remembered]** = known from before and not re-read today. Every section ends with its sources.

**Inputs.** The operator's seeds (`51-data-round-seeds.md` §8-9), the data stack study (`53-data-stack-research.md`), the risk-lab seed "Trading node = a trading server" (`workroom/risk-lab-2026-10-05/seeds.md`), and the code in `qmx-agents/packages/qmx-broker` and `packages/qmf-venue`. Rules carried over: agents never touch money; the operator controls brokers inside QMX, not in an outside browser; no invented limits; design for complexity, not a complex system.

---

## 0. Plain words first

**The short answer.** Every outside service QMX talks to fits one shape: a **connection type** (how to talk to cTrader, MT5, Hyperliquid, a CCXT exchange, Databento …), a **connection** (one login, token or key, demo or live, living on one machine) and the **accounts** found under it. Each type declares up front what it can read, what it can do, how it signs in, what limits its maker publishes, where it can run and how to test it. New types are added as plug-in adapters that QMX discovers, not by changing QMX's core.

1. **cTrader** is a network API. It does **not** need Windows. One sign-in (OAuth) covers every account he ticks, demo and live go through two separate connections, and the limits are 50 requests a second (5 for history). The catch: refreshing the token **kills the old token everywhere**, so only one machine may own the refresh. A new Spotware tool, cTrader CLI (August 2026), runs cBots and trades from Linux or Docker, but it signs in with his cTrader ID **password**, a much bigger key than a token.
2. **MetaTrader 5 needs a running terminal**, and the Python package installs only on Windows. On Linux it runs only under Wine. Each account at the same time needs its own terminal. This is the one connection that pins a node to Windows (or to Wine).
3. **Hyperliquid** has no API keys. Writes are signed by a wallet. The master wallet approves an "agent" key that signs trades; withdrawals and transfers use a different signature that, by my reading of the docs, the agent key cannot make. That suits "agents never touch money" well: the node holds only the agent key. Two surprises: errors come back as HTTP 200 with the error inside the body, and a new account gets only **one write per 1 USDC ever traded**, after a starting allowance of 10,000.
4. **CCXT** covers about 100 crypto exchanges with one interface, and its websocket part is now free. Adding a new exchange is a settings row, not code. But each exchange still has its own limits, sign-in extras and missing features, and you must check what each one supports when it runs. Binance bans an IP for 2 minutes up to 3 days if you ignore its "slow down" replies.
5. **Order flow** means the exchange's own trade tape with the aggressor side, plus the order book (by price, or order by order). It exists for **futures and crypto exchanges, not for spot FX or broker CFDs**. Databento sells it for CME: history by the gigabyte ($125 free credit), live from $199 a month, and deep order-by-order history in a plan only at $4,500 a month. Rithmic and CQG are the futures broker pipes; both need a **conformance test** before you can trade. Interactive Brokers needs a **login window and a weekly manual login**, by its own rules.
6. **Data-only sources** (Dukascopy, Massive, the new name for Polygon, Tiingo, Alpaca, Twelve Data) all fit the same shape with the kind "data" and nothing to trade.
7. **Credentials** are in the Windows vault today. A Linux node has no Windows vault. It needs its own secret store, and it should hold only the narrowest key: trade-only, never withdraw.

The comparison is in §1, one section per connection in §2-§7, and the design-neutral findings in §8-§11.

---

## 1. Comparison

| | cTrader Open API | MetaTrader 5 | Hyperliquid | CCXT (e.g. Binance) | Databento | Rithmic / CQG | Interactive Brokers |
|---|---|---|---|---|---|---|---|
| Kind | platform (many brokers) | platform (many brokers) | exchange | exchange library | data | broker pipe (via futures broker) | broker |
| Markets | CFDs, FX, metals, indices | CFDs, FX, some exchange instruments | perpetual futures, spot | spot, perps, futures, options | CME futures and options, equities | CME, Eurex and others, futures | stocks, futures, options, FX, CFDs |
| Sign-in | OAuth app (Spotware approval), token per cTrader ID | terminal login (account, password, server) | wallet signature; agent key per sub-account | API key + secret (+ passphrase) | API key | broker login; app must pass conformance | username + password in a login window |
| Accounts per login | all accounts granted, unlimited per connection | one per terminal | master + sub-accounts and vaults | usually one key per (sub)account | — | per broker login | one session per username |
| Demo / live | separate hosts, separate connections | per broker server | testnet URL | `set_sandbox_mode` where offered | — | Rithmic Test / paper; CQG demo | paper account (needs a funded live account) |
| Reads | accounts, positions, orders, deals, bars, ticks (1 week per call), **L2 depth**, no trade tape | accounts, positions, history, bars, ticks, depth (if broker sends) | fills (last 10,000), orders, **L2 20 levels**, candles (last 5,000), trades | per exchange: balances, positions, OHLCV, trades, order book | L0-L3, trade tape with aggressor side | L1, L2, history (Rithmic ticks since 2011) | L1, L2, history; no data for stock/FX CFDs |
| Orders | market, limit, stop, stop-limit, market-range, SL/TP | `order_send` | limit (Gtc/Ioc/Alo), trigger TP/SL, TWAP, dead man's switch | unified `create_order` + exchange params | none | server-side brackets, OCO, trailing | full |
| Published limits | 50/s, 5/s history, per connection | none published | 1,200 weight/min per IP; 1 action per USDC traded per address | per exchange (Binance: per IP, 429 then 418 ban) | per plan | Rithmic history 40 GB/week | 50 requests/s at 100 lines |
| Wire | protobuf or JSON over TLS TCP or websocket | local process link to terminal | HTTPS + websocket | HTTPS + websocket | HTTPS + TCP | Rithmic: protobuf over websocket; CQG: protobuf over WSS | TCP socket to a local Java app |
| Runs on | anywhere | **Windows** (Wine on Linux) | anywhere | anywhere | anywhere | anywhere (Protocol API / Web API) | Windows, macOS, Linux, **needs a desktop session** |
| Cost | none found | free terminal | trading fees | trading fees | $/GB; $199-$4,500/month | via broker; conformance | data subscriptions |

---

## 2. cTrader Open API (Spotware) — CFDs, his main broker platform

**What it is.** A network API to the cTrader backend for anyone with a cTrader ID at a cTrader broker. It gives live prices, trading and the history of deals, orders and positions **[retrieved, help.ctrader.com/open-api]**.

**Authentication.**
- You register an **application** on the Open API portal and Spotware must **approve** it before you build ("Spotware carefully evaluates new Open API services"). The page gives no timeline or cost **[retrieved, creating-new-app]**.
- The user grants the app access through **OAuth 2.0** at `id.ctrader.com`. Two scopes: `accounts` (view only) and `trading` (data plus trading) **[retrieved, account-authentication]**.
- The authorisation code lives **one minute**. The access token lives **2,628,000 s (about 30 days)**. The refresh token **never expires**. A refresh returns a new access **and** refresh token and kills the old pair **[retrieved]**.
- On the wire: `ProtoOAApplicationAuthReq` (client id and secret), then `ProtoOAGetAccountListByAccessTokenReq`, then `ProtoOAAccountAuthReq` per account **[retrieved; local: `qmx_broker/adapters.py` does exactly this]**.
- **One token covers every account the user ticked** at grant time. Accounts opened later need the user to grant again **[retrieved]**.

**Connection model.**
- Protobuf on port **5035**, JSON on port **5036**, each over TLS TCP **or** websocket, at `live.ctraderapi.com` and `demo.ctraderapi.com`. AWS Global Accelerator routes to the nearest proxy **[retrieved, proxies-endpoints]**.
- **Demo and live are fully separate.** At most **two connections per app**: one demo, one live. **Each connection can carry an unlimited number of accounts** of its type **[retrieved, connection]**.
- Heartbeat (`ProtoHeartbeatEvent`) at least every **10 s**, or the server drops you **[retrieved, connection + FAQ]**.
- The official Python SDK is TCP only and Twisted-based; QMX does not use it. QMF has its own asyncio TLS transport on 5035 **[retrieved; local: `qmf/venue/connection.py`]**.

**What you can read.** Accounts, balance and equity, positions and pending orders (`ProtoOAReconcileReq`), deal and order history, unrealised P&L, symbols and their specs, live spots, live trendbars, **depth quotes ("Level II")**, historical trendbars and ticks **[retrieved, messages, symbol-data]**.
- Ticks: **at most one week per request**, paged with `hasMore` **[retrieved, symbol-data]**.
- Trendbars: the allowed span per request depends on the period; the per-period table is not published **[retrieved]**.
- Bar "volume" is a tick count. There is **no market trade tape**: the only executions you see are your own **[local, earlier study `ctrader-depth-and-connectivity-research.md`, from the proto files]**.

**What you can do.** Market, limit, stop, market-range and stop-limit orders; amend stop loss and take profit; close; cancel. Needs the `trading` scope **[retrieved, messages]**.

**Rate limits and how they show.**
- **50 requests/s per connection** for ordinary requests, **5/s for historical** requests **[retrieved, open-api home]**.
- Over the limit: error `REQUEST_FREQUENCY_EXCEEDED` (108). Too many connections: `CONNECTIONS_LIMIT_EXCEEDED` (67). Expired token: `OA_AUTH_TOKEN_EXPIRED` (1) **[retrieved, model-messages]**.

**Failure events.**
- `ProtoOAClientDisconnectEvent`: the server dropped the whole app (for example, blocked by an admin); every account session ends.
- `ProtoOAAccountDisconnectEvent`: one account's session dropped; authorise it again.
- `ProtoOAAccountsTokenInvalidatedEvent`: some accounts lost their token (account deleted, cTID deleted, **token refreshed**, or revoked); the others stay connected **[retrieved, messages]**.
- Maintenance "sometimes" happens at weekends, with the API down; no schedule is published **[retrieved, FAQ]**.

**Where it runs.** Anywhere with Python and TLS. **The Open API needs no Windows machine** **[inferred from the network-only model above]**.

**The second door: cTrader CLI (new, August 2026).**
- A Spotware command-line tool that reads accounts, prices and history; places, modifies and cancels orders; and runs, backtests and optimises cBots, "without opening the cTrader desktop application" **[retrieved, help.ctrader.com/ctrader-cli]**.
- Runs on **Windows, macOS and Linux**; also a Linux Docker image `ghcr.io/spotware/ctrader-console`. cBots must be .NET 8 builds **[retrieved, ctrader-cli/setup]**.
- It signs in with the **cTrader ID and its password** read from a file (`--pwd-file`), plus an account number **[retrieved]**. That is a stronger secret than an OAuth token: it opens every account on the cTID.
- `run` is long-running and needs a supervisor such as systemd or Docker. Spotware's own page says agents should not start `run` on their own **[retrieved]**.
- Spotware also ships cTrader MCP servers, which need a cTrader host open in the background **[retrieved]**.

**Costs.** None found for the API itself **[retrieved: no cost stated on any page read]**.

**What QMX already has [local].**
- `qmx-broker`: read-only cTrader and CCXT adapters behind one `ReadAdapter` protocol (`account_state`, `positions`, `quotes`, `bars`, `symbol_info`), settings shaped `broker → connection (demo|live, credential_ref) → accounts`, proposals only (no submit).
- `qmf-venue`: the long-running asyncio TLS transport, a 10 s heartbeat, the 50/5 pacer, the one-week tick cap, token lifecycle classes, and a **two-part capability model**: a static declaration (no credentials needed) plus a profile measured at first connection, with a versioned error map that treats any unmapped code as "outcome unknown".
- Credentials: Windows Credential Manager entries `qmx/<connection>` holding `clientId`, `clientSecret`, `accessToken` (the `keyring` library).

Sources: https://help.ctrader.com/open-api/ · https://github.com/spotware/openapi-proto-messages (execution types, `ProtoOAVersionReq`, `ProtoOAReconcileReq`) · https://help.ctrader.com/open-api/connection/ · https://help.ctrader.com/open-api/proxies-endpoints/ · https://help.ctrader.com/open-api/account-authentication/ · https://help.ctrader.com/open-api/creating-new-app/ · https://help.ctrader.com/open-api/messages/ · https://help.ctrader.com/open-api/model-messages/ · https://help.ctrader.com/open-api/symbol-data/ · https://help.ctrader.com/open-api/faq/ · https://help.ctrader.com/ctrader-cli/ · https://help.ctrader.com/ctrader-cli/setup/

---

## 3. MetaTrader 5 — the other retail CFD platform

**What it is.** A desktop terminal per broker account. There is **no public network API for traders**; programs talk to a running terminal **[inferred; the Python package docs describe only terminal IPC]**.

**The Python package (`MetaTrader5`).**
- "Obtaining of exchange data via interprocessor communication directly from the MetaTrader 5 terminal" **[retrieved, mql5.com/en/docs/python_metatrader5]**.
- `initialize(path, login, password, server, timeout=60000, portable=False)` starts the terminal if needed. Without a login it uses the last account and the password saved in the terminal **[retrieved]**.
- **Windows only in practice:** PyPI version 5.0.6231 ships only `win_amd64` wheels, Python 3.6-3.14, MIT licence **[retrieved, pypi.org JSON]**.
- One `path` = one terminal. Several accounts at once means several terminal installs (portable mode) and one Python process per terminal **[inferred from `path`; the docs do not cover several terminals]**.

**What you can read.** Account and terminal info, symbols, the latest tick, bars (`copy_rates_*`), ticks (`copy_ticks_*`, flags for all, bid/ask or trades), **market depth** (`market_book_add/get`) where the broker sends it, open orders and positions, order and deal history **[retrieved]**. Times are stored in UTC **[retrieved, copy_ticks_range]**. Bar depth is capped by the terminal's "Max. bars in chart" setting **[retrieved in study 53]**.

**What you can do.** `order_check`, `order_calc_margin`, `order_calc_profit`, `order_send` **[retrieved]**.

**Rate limits.** None published for the package; the limit is the terminal and the broker's trade server **[retrieved: none stated]**.

**Linux.**
- MetaQuotes' own `mt5linux.sh` installs the terminal under **Wine** on Ubuntu, Debian, Mint and Fedora **[retrieved, metatrader5.com install_linux]**.
- The Python package still needs a **Windows Python running inside the same Wine prefix**. Community bridges (for example `mt5linux`, which uses RPyC) expose it to Linux Python **[remembered; not an official MetaQuotes product]**.

**EA bridges.** An Expert Advisor inside the terminal can open TCP or TLS sockets (`SocketCreate`, up to 128 per program, Expert Advisors and scripts only, target hosts must be on the terminal's allowed list) and talk to QMX **[retrieved, mql5.com SocketCreate]**. This keeps the terminal as the only thing that holds the broker login; QMX talks to the EA. ZeroMQ bridges are community code **[remembered]**.

**Costs.** The terminal and package are free; the broker sets account terms **[remembered]**.

Sources: https://www.mql5.com/en/docs/python_metatrader5 · https://www.mql5.com/en/docs/python_metatrader5/mt5initialize_py · https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py · https://www.mql5.com/en/docs/network/socketcreate · https://www.metatrader5.com/en/terminal/help/start_advanced/install_linux · https://pypi.org/project/MetaTrader5/

---

## 4. Hyperliquid — on-chain perpetual futures

**What it is.** A blockchain exchange for perpetual futures (and spot) with an HTTP and websocket API. Mainnet `https://api.hyperliquid.xyz`, testnet `https://api.hyperliquid-testnet.xyz`; the same calls work on both **[retrieved, docs api; SDK constants]**.

**Authentication: wallet signing, no API keys.**
- Every write (`POST /exchange`) carries an EIP-712 signature. There are **two signing schemes**: "L1 actions" (orders, cancels, leverage) and "user-signed actions" (transfers, withdrawals, agent approval). The docs advise using an SDK because field order matters for msgpack **[retrieved, signing]**.
- The master wallet approves **API wallets** ("agent wallets") with `ApproveAgent`. They are "only used to sign"; reads must use the master or sub-account address **[retrieved, nonces-and-api-wallets]**.
- Money moves (`usdSend`, `withdraw3`) are user-signed actions. The docs single out "Agent Send Asset" as the one transfer an agent may sign, so the others need the master key **[retrieved, exchange-endpoint; inferred]**. This is a natural fit for "agents never touch money": the node holds only an agent key.
- Sub-accounts and vaults have no keys; the master (or its agent) signs with `vaultAddress` set **[retrieved]**.
- Agent wallets can be **pruned** when deregistered, expired, or the account empties; never reuse an agent address, because pruned nonces allow replay **[retrieved]**.

**Nonces and clocks.** Nonces are per signer; the chain keeps the 100 highest; a new nonce must exceed the smallest of them and fall **between T − 2 days and T + 1 day** of the block time (ms). Use a separate agent wallet per sub-account to avoid nonce collisions **[retrieved]**. A bad clock therefore breaks writes **[inferred]**.

**What you can read (`POST /info`).** Mids, open orders, fills (`userFills` at most 2,000 recent; `userFillsByTime` 2,000 per page and only the **10,000 most recent** fills), historical orders (2,000), order status, **L2 book (at most 20 levels per side)**, candles (**only the most recent 5,000 per interval**), sub-accounts, fees, portfolio, rate-limit status **[retrieved, info-endpoint]**. Websocket at `wss://api.hyperliquid.xyz/ws` (testnet `wss://api.hyperliquid-testnet.xyz/ws`) streams trades, book, candles and user events. The server may drop clients "without notice"; on reconnect, "missed data during the reconnect will be present in the snapshot ack" **[retrieved, websocket]**.

**What you can do.** Limit orders (`Gtc`, `Ioc`, `Alo` post-only), trigger take-profit and stop-loss, modify, cancel by id or client id, TWAP, leverage and isolated margin, `expiresAfter`, and **`scheduleCancel`, a dead man's switch**: cancel-all at a time at least 5 s ahead, at most 10 triggers a day **[retrieved, exchange-endpoint]**.

**Rate limits.**
- Per IP: **1,200 weight per minute** across REST. Exchange actions weigh `1 + floor(batch/40)`; `l2Book`, `allMids`, `clearinghouseState`, `orderStatus` weigh 2; most other info calls 20, plus extra per 20 items returned **[retrieved, rate-limits]**.
- Websocket per IP: 10 connections, 30 new per minute, 1,000 subscriptions, 10 distinct users, 2,000 messages a minute **[retrieved]**.
- **Per address: 1 action per 1 USDC traded since the account opened, plus a 10,000 starting buffer.** When limited, one action per 10 s; cancels get a higher ceiling **[retrieved]**. A new low-volume account runs out of writes before it runs out of IP weight **[inferred]**.
- Open orders: 1,000 by default, up to 5,000 with volume **[retrieved]**.
- **Errors come back as HTTP 200** with per-order `{"error": …}` inside `statuses` **[retrieved, exchange-endpoint]**. A client must read the body, not the status code.

**History.** An S3 archive (`hyperliquid-archive`) holds L2 snapshots and asset contexts, uploaded about monthly, "no guarantee of timely updates and data may be missing", **requester pays** transfer costs. No candles in the archive; record them yourself **[retrieved, historical-data]**.

**Where it runs.** Anywhere (HTTP and websocket). Official Python SDK; CCXT also supports Hyperliquid **[retrieved]**.

**Costs.** No API fee found; trading fees apply **[retrieved: none stated for the API]**.

Sources: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api · https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/rate-limits-and-user-limits · https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets · https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint · https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint · https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/signing · https://hyperliquid.gitbook.io/hyperliquid-docs/historical-data · https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/websocket · https://github.com/hyperliquid-dex/hyperliquid-python-sdk

---

## 5. CCXT and CCXT Pro — one library for many crypto exchanges

**What it is.** An MIT library that wraps "104 cryptocurrency exchange markets and trading APIs" (Binance, Bybit, OKX, Kraken, Coinbase, Hyperliquid and others) in Python, JavaScript, PHP, C#, Go, Java and Rust **[retrieved, CCXT Manual]**. **CCXT Pro (websockets) is now "a free part of CCXT"** **[retrieved, ccxt.pro.manual]**.

**Unified versus exchange-specific.**
- The unified API (`load_markets`, `fetch_ticker`, `fetch_ohlcv`, `fetch_order_book`, `fetch_balance`, `create_order`, `fetch_positions`, funding rates, margin mode …) returns the same shapes everywhere **[retrieved]**.
- Each exchange also exposes its raw endpoints as "implicit methods" **[retrieved]**. Anything the unified API lacks (sub-account switches, special order flags) goes through `params` or these raw calls **[retrieved; local: `qmx-broker` README notes "CCXT has no universal subaccount selector"]**.
- What an exchange supports is reported per exchange (`has`, and the newer `features` map, which "might be incomplete") **[retrieved]**. A connection must read these at runtime, not assume them **[inferred]**.

**Authentication.** API key plus secret, signed with HMAC (or RSA or Ed25519 where the exchange offers it); some exchanges also need a `password` (passphrase) or `uid`. `requiredCredentials` tells you which. Wallet-based exchanges such as Hyperliquid use a wallet address and private key instead **[retrieved, Manual "API Keys Setup"; remembered for the wallet fields]**.
- "Do not reuse API keys with different software": a second program pushes the nonce up and causes `InvalidNonce` **[retrieved]**. One key pair per QMX connection, used by one process **[inferred]**.
- Exchanges let you create keys **without withdrawal permission**, usually with an IP allow-list **[remembered]**. QMX should refuse a key that can withdraw **[inferred from "agents never touch money"]**.

**Rate limits.**
- The built-in limiter is **on by default**, a leaky bucket where `pause = rateLimit (ms) × cost of the call`. "Each exchange instance has its own rate limiter": reuse one instance per key **[retrieved]**. `qmx-broker` already reuses instances **[local]**.
- The exchange's own limits sit on top. Example, Binance spot: limits are **per IP**, published live in `/api/v3/exchangeInfo`; every reply carries `X-MBX-USED-WEIGHT-*`; over the limit gives **HTTP 429** with `Retry-After`; ignoring 429s gives **HTTP 418, an IP ban from 2 minutes to 3 days** **[retrieved, developers.binance.com limits]**.
- CCXT maps these to `RateLimitExceeded` / `DDoSProtection` **[retrieved]**.

**Errors CCXT gives you** **[retrieved, Manual "Exception Hierarchy"]**:
- recoverable `NetworkError`: `RequestTimeout`, `ExchangeNotAvailable` (sub-type `OnMaintenance`), `RateLimitExceeded`, `DDoSProtection`, `InvalidNonce`;
- not recoverable `ExchangeError`: `AuthenticationError`, `PermissionDenied`, `AccountSuspended`, `InsufficientFunds`, `InvalidOrder`, `OrderNotFound`, `DuplicateOrderId`, `NotSupported` …
- **A `RequestTimeout` on `create_order` means the outcome is unknown**: the order may or may not exist, so check before retrying **[retrieved]**. This matches QMF's "UNKNOWN is a state" rule **[local]**.

**Clocks.** Signed calls carry a timestamp. Binance rejects a request more than **1 s ahead** of server time or older than `recvWindow` (default 5,000 ms, max 60,000) **[retrieved, Binance endpoint-security-type]**. CCXT's `adjustForTimeDifference` option measures and corrects the offset **[retrieved]**.

**Websockets (CCXT Pro).** `watch_order_book`, `watch_trades`, `watch_ohlcv`, `watch_balance`, `watch_orders`, `watch_positions` … The library keeps the link alive (`keepAlive` 30 s ping, drop after 2 missed pongs) and **reconnects with exponential backoff on the next `watch` call** **[retrieved, ccxt.pro.manual]**. A reconnect can miss updates in between, so order books must resync from a snapshot and orders from a REST fetch **[inferred]**.

**Demo and live.** `set_sandbox_mode(True)` "immediately after creating the exchange before any other call", only where the exchange has a testnet **[retrieved]**. `qmx-broker` does this for `environment: demo` **[local]**.

**History depth.** Exchanges cap how far back candles go; CCXT pages with `paginate` **[retrieved in study 53]**. Deep crypto history comes from Binance's free bulk archive, not the API **[study 53]**.

**Where it runs.** Anywhere Python runs; no platform piece **[inferred]**.

**Costs.** Free library; exchange trading fees apply **[retrieved: MIT, no fee]**.

Sources: https://github.com/ccxt/ccxt/blob/master/wiki/Manual.md (sections Testnets, Rate Limit, Authentication, Exception Hierarchy, OHLCV) · https://github.com/ccxt/ccxt/blob/master/wiki/ccxt.pro.manual.md · https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits · https://developers.binance.com/docs/binance-spot-api-docs/rest-api/endpoint-security-type

---

## 6. Futures and order flow

### 6.1 What "order flow" data really is

Order flow is built from three exchange feeds **[retrieved, Databento schemas]**:

| Level | What it holds | Databento schema |
|---|---|---|
| **L3, market by order (MBO)** | every single order: add, modify, cancel, trade, fill; queue position can be rebuilt | `mbo` |
| **L2, market by price (MBP)** | total size at each price, top 10 levels, every update | `mbp-10` |
| **L1** | best bid and offer, and **every trade with its aggressor side** ("Ask for a sell aggressor … Bid for a buy aggressor") | `mbp-1`, `tbbo`, `trades` |
| L0 | bars, daily stats (open interest, settlement), contract definitions, halts | `ohlcv-*`, `statistics`, `definition`, `status` |

- The usual order-flow tools follow from these **[inferred]**: delta and footprint charts need **trades with aggressor side** (L1); depth heatmaps and liquidity pulls need **L2**; queue position, iceberg spotting and spoof detection need **L3**.
- **This exists for exchange-traded futures and crypto exchanges, not for spot FX or broker CFDs.** cTrader gives depth from the broker's own liquidity providers but **no market trade tape** (§2), and its bar "volume" is a tick count **[local, earlier cTrader study]**. Hyperliquid gives an L2 book of 20 levels and public trades (§4).
- CME's feed (MDP 3.0) carries full order-by-order detail since **May 2017**; Databento covers all CME futures and options from **June 2010**. Implied trades may have no aggressor side **[retrieved, Databento GLBX.MDP3]**.

### 6.2 Databento — data only

- **What:** CME, CBOT, NYMEX, COMEX and more, all the schemas above, nanosecond timestamps, historical and live **[retrieved]**.
- **Plans [retrieved, databento.com/pricing]:**
  - **Usage-based:** pay per GB of uncompressed data, historical only, 16+ years. **$125 free credit** for new users, expiring after 6 months. Re-download within 30 days is free.
  - **Standard $199/month:** live data with "no license fees"; history L0 16+ years, L1 1 year, **L2 and L3 only 1 month**.
  - **Plus $1,750/month** and **Unlimited $4,500/month** (annual contracts); only Unlimited gives 16+ years of MBO and MBP-10 inside the plan.
- So **deep MBO history is bought by the gigabyte**, and live order flow needs at least Standard **[inferred from the plan table]**.
- **Auth and model:** an API key; HTTP for historical, a TCP gateway for live **[remembered]**. Runs anywhere.

### 6.3 Rithmic — futures broker connectivity (through a futures broker, an FCM)

- Three APIs to the same platform **[retrieved, rithmic.com API suite]**:
  - **R|API+**: C++ (Windows, macOS, Linux) and .NET (Windows only).
  - **R|Protocol API**: "a wire-line spec using WebSockets and Google Protocol Buffers, works in any language", any OS. **The one QMX would use** **[inferred]**.
  - R|Diamond API: Linux C/C++, co-location only.
- Server-side brackets, OCOs and trailing stops "fire even when the client connection drops" **[retrieved]**.
- Historical ticks back to December 2011, **40 GB per user per week** **[retrieved]**.
- **Access:** develop against Rithmic Test freely; **conformance testing is required** before production or paper trading; live logins come from your FCM or broker, who also sets fees. A Protocol-only dev kit can be signed up for online **[retrieved]**.

### 6.4 CQG — futures broker connectivity

- **CQG Web API**: protobuf over secure websockets, streaming L1 and L2 "without any filtering, compression, or consolidation", historical ticks and bars, order routing and account data **[retrieved, partners.cqg.com]**.
- WSS only; users log on with their CQG gateway login, enabled for Web API; a demo server exists; **a formal conformance test** comes before production **[retrieved via a search summary of help.cqg.com; pages not opened one by one]**.
- Costs are by request form **[retrieved: none published]**.

### 6.5 Interactive Brokers — a multi-asset broker

- **TWS API** is a TCP socket API into a running **Trader Workstation or IB Gateway** (Java desktop apps). It recently moved to Protobuf **[retrieved, IBKR docs]**.
- "The user must manually enter their username and password into a login window. For security reasons, **a headless session of TWS or IBGW without a GUI is not supported**." Both "were designed to be restarted daily". With auto-restart they can run Sunday to Sunday, but after the Saturday night reset **you must log in again** **[retrieved, the-ib-gateway]**. Community tools (IBC) automate the login window **[remembered; not an IBKR product]**.
- **One username, one live session.** Make extra usernames per app; market data subscriptions are per username **[retrieved, logging-into-multiple-applications]**.
- **Pacing:** requests per second = market data lines ÷ 2; **default 100 lines, so 50 requests/s**. Over the limit gives error 100, and **three breaches end the session**; or a TWS setting makes TWS pace for you. FIX through IB Gateway allows 250 messages/s **[retrieved, pacing pages]**.
- **Depth:** `reqMktDepth` gives L2 without sampling (odd lots excluded). You must handle error 317 "Market depth data has been RESET" or the book corrupts. **IB gives no market data for stock and forex CFDs**; depth requests reroute to the underlying **[retrieved, market-depth]**.
- **Paper accounts** need an approved, funded live account; execution "may vary" from live **[retrieved]**.
- Runs on Windows, macOS and Linux (Java) **[remembered]**, but needs a desktop session for the login window **[retrieved, above]**.

Sources: https://databento.com/docs/schemas-and-data-formats · https://databento.com/docs/schemas/trades · https://databento.com/docs/datasets/glbx-mdp3 · https://databento.com/pricing · https://www.rithmic.com/products/api-suite · https://partners.cqg.com/api-resources/web-api · https://help.cqg.com/apihelp/Documents/cqgwebapi.htm · https://www.interactivebrokers.com/docs/tws-api/doc/pacing-limitations/introduction · https://www.interactivebrokers.com/docs/tws-api/doc/pacing-limitations/pacing-behavior · https://www.interactivebrokers.com/docs/tws-api/doc/md/market-depth · https://www.interactivebrokers.com/docs/tws-api/doc/architecture/the-trader-workstation/the-ib-gateway · https://www.interactivebrokers.com/docs/tws-api/doc/connectivity/logging-into-multiple-applications · https://www.interactivebrokers.com/docs/tws-api/doc/notes-limitations/tws-api-limitations

---

## 7. Market-data-only providers worth adding

| Provider | What | Free tier | Paid | Notes |
|---|---|---|---|---|
| **Dukascopy** via `dukascopy-node` | forex, metals, indices, CFDs, stocks; ticks to monthly | free | — | Timeframes `tick`, `s1`, `m1` … `mn1`; **bid or ask, one side per run**; volumes off by default; batches of 10 with a 1 s pause; **retries off by default, and empty responses are not retried unless `--retry-on-empty`** **[retrieved, config/cli and errors-and-empty-data]**. These are Dukascopy's own prices and volumes, not his broker's and not market-wide **[inferred]**. |
| **Massive** (formerly Polygon.io; `polygon.io` now redirects to `massive.com`) | US stocks, options, indices, currencies, futures | 5 calls/min, 2 years, end of day | Starter $29 (5 years, 15-min delayed, websockets) … Advanced $199 (20+ years, real time) | **[retrieved, pricing; redirect checked with curl]** |
| **Tiingo** | stocks (30+ years), fundamentals, crypto, IEX feed | 50 requests/hour, 1,000/day, 500 symbols/month | Power $30/month (individual) | "internal use … only for your own personal use" **[retrieved]** |
| **Alpaca** | US stocks, options, crypto; also a broker with paper accounts | Basic: IEX only, 30 websocket symbols, 200 calls/min, history since 2016 but not the latest 15 min | Algo Trader Plus $99/month: all US exchanges, 10,000 calls/min | crypto history needs no login **[retrieved]** |
| **Twelve Data** | stocks, forex, crypto | 8 credits/min, 800/day | Grow $79 … Ultra $999 per month | the page's own structured data disagrees with its cards; confirm before relying **[retrieved]** |
| Binance bulk archive; Databento | crypto history; real futures | free; pay per GB | — | study 53 §3.2 and §6.2 here |

Sources: https://www.dukascopy-node.app/config/cli · https://www.dukascopy-node.app/errors-and-empty-data · https://massive.com/pricing · https://www.tiingo.com/about/pricing · https://docs.alpaca.markets/docs/about-market-data-api · https://twelvedata.com/pricing

---

## 8. One generic connection model (design-neutral)

Everything below is **[inferred]** from §2-§7 and the existing code, unless tagged otherwise.

### 8.1 Three layers that every source above fits

| Layer | What it is | Example |
|---|---|---|
| **Connection type** (the adapter) | code that knows how to talk to one platform, exchange or provider; ships a static declaration | `ctrader`, `mt5`, `hyperliquid`, `ccxt`, `databento`, `dukascopy` |
| **Connection** | one sign-in: one token, key pair, wallet agent, terminal or login; one environment; one home machine | "IC Markets live", "Binance demo", "Hyperliquid main" |
| **Account** | something with a balance under that sign-in, found by asking, not typed in | cTrader `ctidTraderAccountId`, Hyperliquid sub-account, an exchange sub-account |

This is today's `qmx-broker` settings shape (`broker → connection → accounts`) **[local]** with one change: the adapter field stops being a closed list (`Literal["ctrader", "ccxt"]`) and becomes an open registry.

The mapping is not one-to-one everywhere, and the model must allow for that:
- cTrader: one token, many accounts, but **demo and live must be two connections** (separate hosts).
- CCXT: usually **one key per sub-account**, since CCXT has no universal sub-account switch **[local README]**.
- Hyperliquid: one master address with sub-accounts and vaults; **one agent key per sub-account** to avoid nonce clashes **[retrieved]**.
- MT5: **one terminal per account** at a time.
- IBKR: **one live session per username**.
- Data providers: a connection with no accounts at all.

### 8.2 What a connection type declares (static, readable without credentials)

QMF already has the pattern: a static capability declaration plus a profile measured at first connection, and an error map where any unknown code means "outcome unknown" **[local, `qmf/venue/capabilities.py`]**. Generalised:

| Field | Values (examples) |
|---|---|
| `kind` | `data`, `broker`, `exchange`, `platform` (a platform hosts many brokers: cTrader, MT5) |
| `auth` | `oauth2` (cTrader), `api_key` (CCXT, Databento, data vendors), `wallet_agent` (Hyperliquid), `terminal_session` (MT5), `login_session` (IBKR, Rithmic, CQG), `none` (Dukascopy) |
| `credential_fields` | names and which are secret, e.g. cTrader `clientId`, `clientSecret`, `accessToken`, `refreshToken`; CCXT `apiKey`, `secret`, `password` (from CCXT's own `requiredCredentials`). The "add connection" form is generated from this. |
| `environments` | `demo`/`live`, `testnet`/`mainnet`, `paper`/`live`, or `live` only |
| `reads` | `accounts`, `balances`, `positions`, `orders`, `fills`, `history`, `quotes`, `bars`, `ticks`, `depth_l2`, `depth_l3`, `trade_tape`, `funding`, `instrument_specs` |
| `writes` | order types, protections (SL/TP, server-side brackets), cancel, amend, dead man's switch; empty for `data` |
| `money_moves` | always `none` for anything QMX holds: no withdraw, no transfer (enforced by the key chosen, see §9.3) |
| `published_limits` | each limit as the maker states it, with the source link and the date read; never a QMX number |
| `limit_signals` | how a breach shows: error code 108 (cTrader), HTTP 429/418 + `Retry-After` (Binance), body error with HTTP 200 (Hyperliquid), error 100 then disconnect (IBKR) |
| `runs_on` | `any`, `windows`, `windows_or_wine`, `desktop_session` |
| `health_check` | the cheapest call that proves sign-in and reach (§8.4) |
| `error_map` | venue code → retry or not, and whether an order's outcome is known |

The **measured profile** then records what a live connection actually showed: accounts found, symbols, real limits from headers (`X-MBX-USED-WEIGHT-*`, Hyperliquid `userRateLimit`), server clock offset, depth levels actually sent.

### 8.3 Adding a new connection type without touching QMX's core

- **Contract.** A Python package implements one interface: `describe()` (the declaration), `open(secret)`, `health()`, `discover_accounts()`, read methods for each declared read, optional streams, and, **node-side only**, `submit`, `cancel`, `amend` behind the operator's signature. `qmx-broker`'s `ReadAdapter` protocol is the read half of this already **[local]**.
- **Discovery.** Python entry points (a group such as `qmx.connections`) let QMX find installed adapters by name, so a new type is "install the package, it appears in the list". QMX's plugin packs (`qma-core/plugins`) already keep secrets out of plugin payloads and pass only `credential_ref` strings **[local]**; an adapter can be one more thing a pack contributes.
- **Three cheaper paths before writing code:**
  1. A new **crypto exchange** is a CCXT connection with a different `exchange` id: a settings row.
  2. A new **cTrader or MT5 broker** is a new connection under the existing type: a settings row.
  3. A simple **HTTP data provider** (API key, JSON bars) could be a declarative adapter: base URL, auth header, a mapping from response to bars. An option, not checked against any provider here.
- **Conformance check for a new adapter.** Before the UI lists it: the declaration validates; `health()` passes on demo; one read per declared capability returns the right shape; every declared write is refused without the operator's signature. This mirrors QMF's first-connection verification suite **[local]**.

### 8.4 Health check per connection

| Type | Proves sign-in and reach | Watches while running |
|---|---|---|
| cTrader | app auth, account list, account auth, `ProtoOAVersionReq` **[retrieved, proto]** | heartbeat every 10 s; the three disconnect events (§2) |
| MT5 | `initialize`, `terminal_info`, `account_info` **[retrieved]** | terminal still running and connected |
| Hyperliquid | `clearinghouseState` (weight 2) and `userRateLimit` **[retrieved]** | websocket reconnects; agent key still approved |
| CCXT | `fetch_time` or `fetch_status`, then `fetch_balance` **[remembered method names]** | used weight from headers; `OnMaintenance` |
| Databento | a metadata or cost call **[remembered]** | credit or plan left |
| IBKR | the socket accepts and returns server time **[remembered]** | daily restart; weekly login |
| Data-only | one small bar request | empty responses (Dukascopy returns empty rather than failing) |

States worth showing: **ok**, **slowed** (rate-limited or paced), **maintenance**, **needs you** (token revoked, weekly login, agent key pruned, conformance), **down**.

---

## 9. Where each connection runs, and what a trading node needs

### 9.1 Placement

| Connection | PC (Windows) | Linux server / node | Windows machine needed? |
|---|---|---|---|
| cTrader Open API | yes | **yes** | **no** |
| cTrader CLI and cBots | yes | yes (Docker image) | no |
| MT5 | yes | only under Wine; the Python package is Windows-only | **yes, or Wine** |
| Hyperliquid | yes | yes | no |
| CCXT exchanges | yes | yes | no |
| Databento, Dukascopy, other data | yes | yes (server workflows, study 53) | no |
| Rithmic Protocol API, CQG Web API | yes | yes | no |
| Interactive Brokers | yes | yes, with a virtual display and a weekly login | no, but needs a desktop session |

The risk-lab seed says "cTrader on a server needs a Windows machine". **The documents say otherwise**: the Open API is a plain network API, and Spotware's own CLI ships a Linux Docker image **[retrieved]**. Only MT5 needs Windows or Wine **[retrieved]**.

### 9.2 What a trading node needs from a connection

- **A long-running connection, not short reads.** `qmx-broker` opens a short TLS session per read; QMF's connection manager is the long-running one, with heartbeat, reconnect and gap replay declared **[local]**.
- **Its own copy of the credential, scoped to the node.** cTrader token; Hyperliquid agent key; a trade-only exchange key with the IP allow-list set to the node's address.
- **Self-tests on connect** (the risk-lab seed): health check, a demo test order and cancel, the kill-switch path, and a clock check.
- **A home for the refresh.** cTrader refresh returns a new pair and invalidates the old one; `ProtoOAAccountsTokenInvalidatedEvent` lists "token refreshed" as a reason **[retrieved]**. If the PC and the node both refresh the same grant, each knocks the other off. One machine must own the refresh, or each machine gets its own grant. Whether two grants for the same app and user can live side by side is not stated in the docs; test it on demo.
- **Server-side protections where they exist**, because they act when the node is cut off: cTrader stop loss and take profit live on the broker; Rithmic brackets "fire even when the client connection drops"; Hyperliquid `scheduleCancel` cancels all orders at a set time unless renewed (at most 10 triggers a day) **[retrieved]**.

### 9.3 Credentials on a Linux node

- Today: Windows Credential Manager entries `qmx/<connection>`, read with Python `keyring` **[local]**.
- On Linux, `keyring` uses the Secret Service over D-Bus. Headless use needs a GNOME Keyring daemon unlocked from a password on stdin inside a D-Bus session **[retrieved, keyring README]**. That is workable but fragile on a server; a node-side secret store is a design decision for 55 (options include systemd credentials or an encrypted file unlocked at start) **[inferred]**.
- **Least power per key.** Exchange keys without withdrawal rights, IP-bound to the node; Hyperliquid agent keys (cannot sign user transfers); cTrader OAuth tokens (not the cTrader ID password, which the CLI wants). The master wallet and account passwords stay with the operator **[inferred from §2, §4, §5]**.

---

## 10. Failure behaviour per connection

| | Rate limit | Disconnect and reconnect | Token or session | Clock | Partial fills and unknown outcomes | Maintenance |
|---|---|---|---|---|---|---|
| **cTrader** | error 108 `REQUEST_FREQUENCY_EXCEEDED`; FAQ mentions HTTP 429; QMF paces 50/5 | heartbeat every 10 s; whole-app, per-account and per-token disconnect events; re-auth the account | access token ~30 days; refresh rotates both tokens; new accounts need a new grant | server stamps times; QMF tracks server-clock availability | `ORDER_PARTIAL_FILL` execution events; reconcile with `ProtoOAReconcileReq`; `clientOrderId` up to 50 chars **[retrieved, proto + messages]** | "sometimes" at weekends, API down, no schedule |
| **MT5** | none published | terminal loses its server; Python sees `last_error()` | password saved in terminal | terminal stores UTC | deals per order in history; check `order_send` result | broker-defined |
| **Hyperliquid** | IP weight 1,200/min; per-address actions tied to volume; when limited, 1 action per 10 s; **errors in an HTTP 200 body** | server may drop sockets without notice; missed data arrives in the snapshot on resubscribe | agent key can be pruned (deregistered, expired, empty account) | nonce must fall in T − 2 days … T + 1 day; unique per signer, so two processes must not share an agent key | per-order statuses in one response; fills via `userFills`; `cloid` 128-bit | not covered in pages read |
| **CCXT / Binance** | built-in limiter; Binance 429 + `Retry-After`, then 418 ban 2 min-3 days; limits per IP | CCXT Pro reconnects with backoff on the next `watch`; resync book and orders after | key revoked → `AuthenticationError` | Binance rejects > 1 s ahead or older than `recvWindow` (5 s default, 60 s max); `adjustForTimeDifference` | `RequestTimeout` on `create_order` = **outcome unknown**, check before retry; orders report `filled` and `remaining` | `OnMaintenance` error |
| **Databento** | per plan | live gateway reconnect | API key | nanosecond exchange timestamps | — | — |
| **Rithmic / CQG** | Rithmic history 40 GB/week | server-side brackets survive a drop | broker login; conformance per app | — | via execution reports | exchange hours |
| **IBKR** | error 100; 3 breaches end the session, or let TWS pace | error 317 "depth RESET" means rebuild the book | daily restart; **weekly manual login** after Saturday reset; one session per username | — | `orderStatus` filled and remaining | nightly reset |
| **Dukascopy** | none published; downloader pauses 1 s per batch of 10 | — | — | UTC by default | — | empty responses happen; retry-on-empty is opt-in |

**Patterns that hold across all of them [inferred]:**
1. **"Unknown" is a normal state for an order.** A timeout, a dropped socket or an unmapped error leaves you not knowing. Recover by client order id and a reconcile call, never by blind retry. QMF already encodes this **[local]**.
2. **Rate limits are signalled in at least four different ways** (error code, HTTP status, body text, disconnect). Each adapter must turn its own signal into one "slowed" state with a wait time.
3. **Reconnect means resync.** After any drop: re-authorise, re-subscribe, fetch a fresh book snapshot, reconcile orders and positions, and fill the bar or tick gap from history.
4. **Clock matters most for signed exchanges** (Binance's 1 s ahead rule). A node should keep NTP and record its offset to each venue in the measured profile.
5. **"Needs you" states are real and recurring**: IBKR's weekly login, cTrader grants for new accounts, Hyperliquid agent pruning, exchange key expiry. The UI must show them as tasks for the operator, not errors.

---

## 11. What QMX already has, and the gaps

**Has [local, `origin/engine/base` 8af1a1cd]:**
- `qmx-broker`: read adapters for cTrader and CCXT spot, settings `broker → connection (demo|live) → accounts`, credentials by `qmx/*` reference only, proposals stored and never submitted.
- `qmf-venue`: long-running cTrader transport, pacing, the one-week tick cap, token lifecycle, two-part capability model, error map with "unknown" as a state.
- `qma-core` plugins: `credential_ref`-only payloads and a schema check that keeps secrets out of plugin and hook data.

**Gaps against what the operator asked for [inferred]:**
- The adapter list is closed (`Literal["ctrader", "ccxt"]`); there is no registry or entry-point discovery for new types.
- No MT5, Hyperliquid, Databento or data-only adapters; CCXT is spot-only ("only active non-contract spot markets are accepted").
- `kind`, `auth`, `runs_on`, `published_limits` and `health_check` are not declared per type; a connection has no home machine field.
- OAuth sign-up and refresh are "operator/node duties" outside QMX **[local README]**; the operator wants to add and control connections inside QMX.
- The vault is Windows-only; the node has no secret store yet.

---

## 12. Open questions the docs did not answer

1. Can one cTrader app hold two independent grants for the same cTrader ID (one for the PC, one for the node), or does a new grant revoke the old? Test on demo.
2. cTrader's per-period trendbar span limits are not published; only runtime errors show them.
3. Hyperliquid testnet funding rules were not on the pages read.
4. CQG conformance and pricing need the request form.
5. Databento's live gateway details were not re-read today (marked **[remembered]**).
6. IBKR's platform list and IBC behaviour were not re-read today (marked **[remembered]**).
