# 33: Data depth per class, quality checks, terms, and disk for QMX's own recording

Ticket: `wayfinder/tickets/research-data-depth-and-terms.md` (covers L08-15, L09-07, L09-10). Written 2026-10-30 by research agent 3. Facts and options; his decision on recording data and disk (research 43, decision 5) stays his.

## How to read this

- **CHECKED** = read or run today at the URL, file or command named. **INFERRED** = reasoned from checked facts. **SECONDARY** = third-party page read today.
- Research 12 (27 Oct) already holds a depth table and a 17-item quality checklist. This file re-checks the parts that move, adds what changed since, and adds the terms and disk answers. Where 12 still holds, this file points to it instead of repeating it.
- Who gives which data live is research 38. Instrument facts are research 32. The recorder on the node is research 31.
- His seed (STATE round 2026-10-27): no lookback cap, "If a test wants 1990, allow it." His seed (30 Oct, verbatim `transcript-2026-10-29-to-30.md` 17:53): "for raw data, we are going to first see, because this 44 minute thing is huge."
- No Dukascopy download was made (his go is needed). Its terms page was read.

## 0. The short answer

1. **"No lookback cap" is real in code once QMB's reader is windowed; the real limit is how far each source goes back.** Intraday history starts in 2003 for FX and gold (Dukascopy), 2010 for CME futures (Databento), 2017 for stocks and crypto, late 2024 for Hyperliquid (Tardis). Before that, daily bars only (research 12 §2, CHECKED 27 Oct; Databento and Tardis re-checked today).
2. **Dukascopy's terms allow download for personal, non-commercial use, but forbid building a database from it and forbid bots without written consent.** The clause: the site "may not be used to construct a database of any kind" (CHECKED https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/). Keeping its history in QMX's store is storing it "in databases for access by you", which the same paragraph also forbids. Plainly: QMX keeping Dukascopy history is against the letter of the terms. Asking Dukascopy for written consent is the only clean fix.
3. **Dukascopy is also actively blocking automated downloads.** dukascopy-node shipped two fixes on 21 and 28 Oct; an open issue (27 Oct) reports HTTP 403 after the bot-wall challenge (CHECKED GitHub API, issues #261, #264, #265, #266).
4. **New since research 12: Binance Vision now has dataset terms (26 Aug 2026).** The files are licensed CC BY-NC-SA 4.0. Personal, non-production backtesting is allowed. Use "for live proprietary trading execution" is not (CHECKED https://github.com/binance/binance-public-data , `TERMS_AND_CONDITIONS.md` §3-4). So Binance Vision suits research and backtests, and is a question mark for data a live unit trades on.
5. **QMX's own recording is the escape route from both:** data a QMX feed keeper records from his own broker or venue connection is his. Its terms are the venue's live-data terms, not a download site's (INFERRED; venue terms for recording not read in full).
6. **Disk.** D: has 58.1 GB free and C: 16.0 GB (CHECKED PowerShell `Get-PSDrive`, 30 Oct). Quote ticks cost about 30 MB per FX pair per month; 1-minute bars under 1 MB; depth is the unknown, 0.1 to 1+ GB per symbol per month (estimates in §4, partly measured on synthetic data). 60 instruments of ticks fit on D: for about two to three years; depth on 60 symbols does not fit for long.
7. **His PC's Linux clock is not synchronised** (CHECKED `timedatectl` in WSL: "System clock synchronized: no"). A recorder stamps receive time; an unsynchronised clock corrupts every latency and staleness number, and Hyperliquid rejects actions whose time stamps fall outside its window (research 38 §3.8). This is a quality check, not a footnote.

---

## 1. Depth per class and source

"Depth" = how far back each kind of data goes. Prices are the vendors'.

| Class | Free, deep | Free, own broker | Paid | Order flow, OI, funding history |
| --- | --- | --- | --- | --- |
| **FX** | Dukascopy ticks and 1m from 2003, daily from 1973 (research 12 §2.1, CHECKED 27 Oct). HistData FX ticks and 1m (files before June 2009 have bid and ask swapped; research 12). | cTrader trendbars and one-side ticks, one week per request; total retention not documented (research 38 §3.1). MT5 terminal history. | FirstRate FX 1m from 2009/2010 (research 12). | None exists for spot FX (OTC). CME FX futures as a proxy via Databento. |
| **Metals** | Dukascopy gold from 2003, daily from 1999. | Same as FX. | Databento COMEX (GC, MGC) 16+ years. | COMEX tape and depth via Databento. |
| **Index CFDs** | Dukascopy indices 1m from 2011-2012, daily from 1980 (US 500). | cTrader, MT5. | Databento CME ES/MES/NQ 16+ years; FirstRate from 2008. | CME tape via Databento as proxy. |
| **Real futures** | None deep and free. | IBKR: no expired futures older than 2 years, no bars of 30 s or less older than 6 months, no time and sales beyond 3 years (CHECKED https://www.interactivebrokers.com/docs/tws-api/doc/md/introduction.md). Rithmic history plant (depth not read). | **Databento** (CHECKED https://databento.com/pricing): bars 1s/1m/1h/1d, definitions, statistics, status for 16+ years on every plan; on Standard: L1 and trades for the last 12 months, L2 (MBP-10) and L3 (MBO) for the last month; Plus: 16+ years of L1; Unlimited: 16+ years of everything. Pay-per-GB history on any schema. | Trades and depth: Databento. Open interest: Databento statistics schema (INFERRED from "Statistics" row; not opened). |
| **Stock CFDs** | Dukascopy 546 US stocks from 2017. | MT5 at IC. | FirstRate 1m from 2000, adjusted, delisted names (research 12). | Stock tape: not checked. |
| **Crypto spot** | Binance Vision daily and monthly files: klines from 1s, trades, aggTrades; SHA-256 checksum per zip; spot stamps in microseconds from 1 Jan 2025 (CHECKED binance-public-data README). | The exchange is the broker; CCXT top-ups. | Tardis spot. | Trades in the files. |
| **Crypto perps (CEX)** | Binance Vision USD-M and COIN-M klines, trades, aggTrades (CHECKED README). Terms: §3. | The exchange. | Tardis Perpetuals plan: 30 venues, trades, book updates, snapshots, funding, OI, liquidations; history reach by billing: monthly 4 months, quarterly 12, yearly 4 years; Business yearly back to 2019-03-30 (CHECKED https://docs.tardis.dev/faq/billing-and-subscriptions). | Funding: Binance funding history endpoint (research 12; not opened today). OI: Tardis. |
| **Hyperliquid perps and HIP-3** | Candles: last 5,000 only (research 02 §8.3). S3 archive of hourly L2 snapshots and asset contexts, uploaded about monthly, requester pays (research 02). | The venue. | Tardis: Hyperliquid since 2024-10-29, HIP-3 since 2025-12-02; channels trades, `l2Book` (about 5.4 s), `fastBook` (about 500 ms, since 2026-06-17), `bbo` (since 2025-06-26), `activeAssetCtx`; first day of each month free (CHECKED https://docs.tardis.dev/historical-data-details/hyperliquid). | Funding and OI: `activeAssetCtx` in Tardis; `fundingHistory` on Hyperliquid's info endpoint (rate-limited by items returned, CHECKED rate-limits page). |

**The "1990" answer, re-checked (INFERRED from the table):** a 1990 test runs on daily bars (FX from 1973, US 500 from 1980). Minute data before 2003 (FX), 2008-2010 (futures and indices) or 2017 (stocks, crypto) does not exist in any source found. The honest behaviour is research 12's: accept any start, use the deepest data that exists, say plainly where it starts.

**What changed since research 12 (CHECKED today):**
- dukascopy-node v1.51.0 (21 Oct) and v1.51.1 (28 Oct) rewrote the fetcher and its 403 handling; issue #264 (open, 27 Oct): requests fail with HTTP 403 after the bot-wall challenge.
- Binance Vision gained dataset terms (§3.2).
- Tardis: Hyperliquid `fastBook` from 2026-06-17 changes the book snapshot cadence inside the archive (a source seam, §2).
- Databento: the Standard price did not render today; research 12 read USD 199 a month on 27 Oct.

---

## 2. Quality checks per feed

Research 12 §3 lists 17 checks for every dataset (completeness by the session clock, silent empties, gaps, spikes, crossed spreads, spread outliers, duplicates, ordering, time zone and daylight saving, corporate actions, futures rolls, weekend bars, bar versus tick agreement, side pairing, cross-source check, source seams, replaced files). They still hold. This table adds what each feed needs on top, from today's sources.

| Feed | Specific failure | Check | Source |
| --- | --- | --- | --- |
| Dukascopy via dukascopy-node | An hour comes back empty with no error after a bot-wall challenge; 403 after the challenge | Treat every empty trading hour as a fetch failure until a retry and a second source agree; record the library version on the dataset card | CHECKED issues #261, #264 |
| Dukascopy | Its prices are Dukascopy's own, not his broker's | Cross-source check against his broker's bars (research 12 check 15) | research 12 §2.1 |
| Binance Vision | Archived files may be replaced later | Keep the old checksum; a new checksum is a new card version | CHECKED README "Updates" section |
| Binance Vision | Spot stamps switched from milliseconds to microseconds on 1 Jan 2025 | Unit check on every file's stamps | CHECKED README |
| Hyperliquid via Tardis | Book snapshot cadence changed (`l2Book` about 5.4 s, then `fastBook` about 500 ms from 2026-06-17); normalised 5- and 25-level snapshots switch source at that date | Record the seam on the card; never compare book statistics across it without saying so | CHECKED Tardis Hyperliquid page |
| Hyperliquid via Tardis | Trades from 2024-12-01 carry buyer and seller addresses; earlier ones do not | Column-presence check per month | CHECKED same page |
| Databento CME | Before 2017-05-21 the finest level is MBP-10 and timestamps carry a bad-receive-time flag | Seam on the card | research 12 §2.2 (CHECKED 27 Oct) |
| IBKR history | Historical volume is filtered (fewer trades than the live feed) | Never mix IBKR historical volume with live volume in one series | CHECKED IBKR market data page |
| cTrader live | Bid and ask each optional in a spot event; depth is differential with no snapshot message | Keep the last value per side; rebuild the book after a reconnect | research 12 §4.1, research 21 §3 |
| cTrader history | Ticks one side per request; retention per broker unknown | Pair bid and ask downloads (QMX already refuses half pairs); measure retention once on demo | research 21 §3; research 12 §2.1 |
| **QMX's own recorder** | The receive clock drifts or is unsynchronised | Stamp venue time and receive time; check clock sync before recording; mark rows recorded while unsynchronised | CHECKED `timedatectl` on his WSL: not synchronised |
| QMX's own recorder | Gaps during reconnects; backfilled rows mixed with live rows | Mark backfilled rows (research 12 §4.3) | research 12 |

Numbers (starting defaults, editable):

| Number | Starting default | Why |
| --- | --- | --- |
| `clock_skew_warn_ms`: receive clock versus a time server | 100 ms | A 1-minute scalper's step budget is seconds (research 31); 100 ms keeps skew under a tenth of the smallest step budget there (INFERRED) |
| `empty_hour_retries` before a Dukascopy hour is marked missing | 3 | dukascopy-node's own default was 0, which caused #261 (CHECKED) |
| `source_seam_test_window_days` either side of a seam | 30 | One month of statistics each side (INFERRED) |

---

## 3. The terms, plainly

### 3.1 Dukascopy

- **What it allows:** "you may download material from the WEBSITE ... for your own personal, non-commercial use" (paraphrase; the permission sits in the copying paragraph). CHECKED https://www.dukascopy.com/swiss/english/legal-pages/terms-of-use/
- **What it forbids:** constructing "a database of any kind"; storing the website's content in databases "for access by you or any third party"; any "scraper", "robot" or "bot" used to acquire data without prior written consent. CHECKED same page (quotes are fragments under 15 words).
- **What that means for QMX (INFERRED):** downloading a little by hand for personal study fits the terms. A downloader that runs on a schedule is a bot. Storing the result in QMX's Parquet store, read by QMB, is a database for his own access. Both are against the letter, regardless of being personal. QMX's existing `internal-only` licence stamp (DEC-0170, research 12) keeps the data private but does not make the storage allowed.
- **His options (not a choice):**
  1. Ask Dukascopy for written consent for personal, non-commercial storage and backtesting. Clean if granted.
  2. Keep the stance research 12 called the posture of every dukascopy-node user, knowing it is against the letter and that Dukascopy is now blocking bots (§0 item 3).
  3. Use Dukascopy only for the 10 GB of old ticks already on disk and replace new history with QMX's own recording plus other sources.
  4. Drop Dukascopy as a source.
- Training models on it: the terms say nothing about model training (SECONDARY https://openbrokerapi.com/data-sources/dukascopy-historical-data , which read the terms on 9 Oct).

### 3.2 Binance Vision (new terms, 26 Aug 2026)

- **Licence:** CC BY-NC-SA 4.0 (§3.1). Commercial use needs a separate written licence (§3.4). CHECKED `TERMS_AND_CONDITIONS.md` in https://github.com/binance/binance-public-data
- **Allowed:** "algorithmic historical backtesting for purely personal non-production research" (§4.1, fragment).
- **Not allowed:** use "for live proprietary trading execution" or automated commercial order generation (§4.2); hosting or reselling the data (§4.3); integration into commercial trading bot platforms (§4.4).
- **Access:** obey rate limits; no scraping routines that get around them (§7).
- **Amendments:** apply only to data made available after the change; already-downloaded data keeps the terms of the time (§1.4).
- **What that means for QMX (INFERRED):** backtests and research on Binance Vision files fit §4.1. A unit that trades live and was tuned on these files is the grey zone: §4.2 forbids using the Datasets for live execution, and §2.4 says data "derived from" them is governed too. Whether "a unit judged on Binance Vision history, trading on Binance's own live feed" is "use for live execution" is not answered by the text. This is a question for him (and, if it matters, for Binance), not for an agent to settle. The standing order "use the Library's partitions or Binance Vision" for price data stays valid for research.

### 3.3 Others

| Source | Terms read today | What they say |
| --- | --- | --- |
| Databento Standard | Pricing page | Personal use on up to 2 devices, licence fees included; commercial use and redistribution need Plus or higher (CHECKED https://databento.com/pricing) |
| Tardis | Billing FAQ only | Subscription types and history reach; licence text not read |
| CME data through an FCM | AMP fee page | Non-professional prices; full month billed; per user id, not shareable between usernames (CHECKED https://www.ampfutures.com/trading-info/exchange-data-fees) |
| IBKR | Market data page | Subscriptions per live username; paper users can share (CHECKED) |
| Hyperliquid | Terms §1.6 (who may use the interface) | Recording rules not stated in what was read |
| His broker's live feed (cTrader) | Not read | Whether recording and keeping IC's quotes is allowed is not checked (question D-01 below) |

---

## 4. Disk for QMX's own recording

### 4.1 What was measured

- **Free disk, 30 Oct (CHECKED PowerShell `Get-PSDrive`):** C: 16.0 GB free, D: 58.1 GB free. (Research 12's figures, 12 GB and 8.3 GB, were older; the 30 Oct STATE figure of about 57.7 GB for D: matches.)
- **WSL's virtual disk** reports 1007 GB size, 954 GB available (CHECKED `df -h /` in WSL). That is a sparse virtual disk stored on C: (CHECKED registry `HKCU:\...\Lxss`: Ubuntu-24.04 lives under `C:\Users\Mubarak\AppData\Local\wsl\`; docker-desktop under `C:\Users\Mubarak\AppData\Local\Docker\wsl\main`). It cannot hold more than C: actually has free. Data recorded inside WSL lands on C:, which has 16 GB free, unless the recorder writes to D: through `/mnt/d` or the distribution is moved (INFERRED; a hard case for "run the node on the PC").
- **Bytes per row on Parquet with zstd, synthetic data (CHECKED, script `pqsize.py` in the scratchpad, run with QMX's own pyarrow 25.0.1, in memory):**
  - FX quote ticks (venue time, receive time, bid, ask as integers), 70,000 rows a day: **19.9 bytes per row, 1.39 MB a day.**
  - Depth updates, assumed 10 per quote tick: 6.9 bytes per row, 4.8 MB a day.
  - 1-minute bars: 14.1 bytes per row, 20 KB a day.
- **What limits these numbers (explained):** synthetic random walks with random timestamp gaps. Two random 64-bit time columns dominate the tick row; real data with regular stamps may compress better. The depth row is small because its synthetic prices cluster; **the real unknown for depth is the update rate, not the bytes per row.** cTrader's depth update rate per symbol was not measured (no sign-in). So the tick figure is within a factor of about 2 (research 12's figure from real Dukascopy data, 150-300 MB per instrument-year, is 12-25 MB a month, which matches), and the depth figure is a guess until a day of demo depth is recorded.

### 4.2 Per class, per month (INFERRED from §4.1 and research 12 §5.2)

| What is recorded | Per symbol per month | 60 symbols per month | Notes |
| --- | --- | --- | --- |
| 1-minute bars, bid and ask | about 1 MB | about 60 MB | Negligible |
| FX or CFD quote ticks (cTrader) | about 20-40 MB | about 1.2-2.4 GB | 22 trading days |
| Crypto trades, a top perp | not measured; research 12: "GBs a month per top symbol" | measure first | 24/7, 30 days |
| Hyperliquid `fastBook` (5 levels, about 2 snapshots a second) | about 170,000 snapshots a day × 10 levels ≈ 52M level rows a month; at 5-10 bytes a row about 0.25-0.5 GB | 15-30 GB | Arithmetic from the Tardis cadence (CHECKED cadence) |
| cTrader depth | 0.1 GB (at 10 updates per tick) to 1 GB or more (at 100) | 6-60 GB | **Unknown rate; measure one day on demo** |
| CME full order book (MBO) | very large; not measured | not for the PC | Buy from Databento per GB when needed instead of recording |
| Market journal, 1-minute buckets | research 12: about 1-2 GB a year for 60 instruments × 2 brokers | about 0.1-0.2 GB | |
| Unit journals | research 12: a few hundred MB a year for 200 units | small | |

### 4.3 What fits on his PC (INFERRED)

- **Bars and quote ticks for 60 instruments fit on D:** at about 1.3-2.5 GB a month, 58 GB lasts about 2 to 4 years.
- **Depth for every symbol does not fit:** 6-60 GB a month fills D: in 1 to 10 months.
- **The 10 GB of old Dukascopy ticks** (research 12) take a sixth of D:'s free space.
- **Research 12's stance still holds:** the full tick and depth archive lives on the server and in the storage bucket; the PC keeps a cache sized to its free space. A bigger local disk is his call.

### 4.4 Options for what to record (not a choice)

| Option | Records | Disk on the PC | Hard cases | Explain |
| --- | --- | --- | --- | --- |
| D1 | Everything every connection gives | Fills D: in months | Strong: no data is ever lost | "Keep everything" |
| D2 | What some admitted unit declares it needs, plus quote ticks for all subscribed symbols | Bars and ticks fit; depth only where declared | A new unit cannot backtest depth that was never recorded | "Record what units use, plus the basics" |
| D3 | D2 on the PC; D1 on the server, copied to the bucket | PC holds a cache | Server cost; PC first rule: the PC can still record everything for a day to rehearse | "The server keeps the full archive; your PC keeps what it needs" |
| D4 | Record nothing; buy history when needed (Databento, Tardis) | Minimal | Costs money each time; no history of his own broker's spreads | "Buy it when you need it" |

Numbers (starting defaults, editable):

| Number | Starting default | Why |
| --- | --- | --- |
| `pc_cache_max_fraction`: share of a drive's free space the price cache may use | 0.5 | Leaves room for the Library, backups and Windows (INFERRED) |
| `record_ticks_for`: which symbols record quote ticks from day one | every subscribed symbol | Ticks are cheap (§4.2) and live data becomes history (`live-field.md` B040) |
| `record_depth_for`: which symbols record depth | symbols a unit declares depth for | Depth is the expensive unknown |
| `depth_rate_probe_hours`: hours of demo depth recorded to measure the real rate | 24 | One full FX day covers every session (INFERRED) |

---

## 5. Questions

| Id | Question | Tag |
| --- | --- | --- |
| D-01 | Does IC Markets (or Spotware) allow a client to record and keep the cTrader quotes and depth his account receives, for personal use? | research (read IC's client agreement) |
| D-02 | Will he ask Dukascopy for written consent, keep the current stance, keep only the old ticks, or drop Dukascopy? (§3.1) | operator |
| D-03 | Is a unit tuned on Binance Vision history and trading live on Binance "use for live execution" under §4.2? | operator (possibly ask Binance) |
| D-04 | Record depth from day one for which symbols, given 6-60 GB a month for 60 symbols? | operator |
| D-05 | A bigger local disk, or the server and bucket as the archive? (already STATE "For his awareness") | operator |
| D-06 | Should the node, when run on the PC, write recordings to D: rather than the WSL disk on C:? | lead |
| D-07 | How deep does IC's cTrader history go per symbol? (one demo read per symbol) | research |
| D-08 | Turn on clock sync in his WSL before any recording? | lead (settled by a check, not a question for him) |

## 6. Not verified

Tardis licence text; Databento Standard price today; Binance funding-history files; Hyperliquid S3 archive terms; cTrader history retention; real cTrader depth update rates; CME open interest in Databento's statistics schema.
