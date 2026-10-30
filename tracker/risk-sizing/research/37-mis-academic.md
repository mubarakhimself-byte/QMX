---
ticket: research-mis-academic
title: What academic and serious practitioner work says about reading market state, by style, timeframe, data and asset class
date: 2026-10-30
author: research agent 1 (MIS), Opus poteto-agent; this file, 22 and 23 are its only writes
method: Exa search and fetch of primary pages (journal pages, arXiv, SSRN, authors' PDFs, central-bank and exchange-adjacent research), read 2026-10-30, in many framings (regime detection, change points, Hurst and variance ratio, HMM and Markov switching, jump models, volatility models, order-flow imbalance, microstructure, info-driven bars, per asset class). Two small simulations of my own (scripts in the scratchpad, named in §7). No Firecrawl, no browser, no paid agent runs.
labels: CHECKED (URL, path:line or command) = read or run this session. PRACTITIONER = vendor, blog, thesis or unreviewed repo. INFERRED = my reasoning. Each paper's result is that paper's claim.
---

# 37: Market-state reading in the literature, per style, timeframe, data and asset class

## How to read this

- This is evidence and options, not a design. Nothing here is chosen.
- His seed sets the order of the matrix: trading style, then timeframe or bar type, then the data a market offers, then asset class (STATE 29/30 Oct, CHECKED `STATE.md:119`). His words: "We can research firstly the trading style, then trading style with the timeframes" (`T2:219`, CHECKED). `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md`, `n` = the line holding his whole turn.
- Research 05 already covers the detection bound, intraday seasonality, OFI, BOCPD, jump models and HAR; this file cites it instead of repeating it (`research/05-academic.md` §1, CHECKED).
- Section 1 is the evidence catalogue (one row per source: sample, period, costs, out-of-sample result, lag, look-ahead risk). Sections 2 and 3 are the two matrices the ticket asks for. Section 4 lists empty cells. Section 5 sorts method families into shared and single-cell. Section 6 lists disagreements. Section 7 answers his inefficiency point. Section 8 names the numbers.
- Research 22 (speed) and 23 (organisation) lean on this file and cite its row ids (E01 and so on).

## Short answer

1. **The information limit decides speed, not the method.** No detector beats the bound in research 05 (CHECKED `research/05-academic.md:21`). My own simulation agrees: at one false alarm a day on 1-minute bars, a volatility rise of 50% shows in about 16 to 19 bars, a very strong trend in about 150 to 200 bars, strong bar-level mean reversion in about 120 to 220 bars, and weak versions take a day or more (CHECKED command, §7 S1). Indicators, statistical tests and models all live under the same limit.
2. **His question "how are these models different from technical analysis using indicators" (`T1:1951`, CHECKED) has a measured answer.** The difference that matters is not indicator versus model. It is (a) what data feeds it (ticks, depth, tape, funding carry more information per minute than closes), (b) how long the state it detects lasts compared with its window, and (c) whether it flips falsely. HMMs detect as quickly as penalised jump models but with many spurious short switches (E19). Model-based regime work with honest out-of-sample trading after costs exists mostly at daily and slower horizons (E19, E23, E41, E44).
3. **The literature is horizon-split, and it matches his style order.** Seconds: order flow and book imbalance predict, and the signal is gone within 30 to 60 seconds (E06, E46). Minutes to an hour: reversal from bid-ask bounce and liquidity pressure (E13, E14). Half-hour to day: continuation into the close, "everywhere" across 60 futures (E10, E11). Days to months: persistence and slow regimes (E14, E17, E23). A scalper, an intraday trader and a swing trader are reading different physics.
4. **Price-only mean-reversion sensors on short bars are polluted by bid-ask bounce.** With bounce noise at half a bar's sigma, variance-ratio and autocorrelation sensors false-alarm 10 to 130 times more often than designed; trend sensors do not (CHECKED command, §7 S1). Intraday "anti-persistence" findings on traded prices (E14) carry this risk.
5. **A label known at entry is worth much less than the same label computed with hindsight when states are short.** With 2-hour states, a 240-bar sensor gives no gain in total result over no gate, while a centred (look-ahead) label claims a 76% better edge per trade. With 2-day states the honest gate keeps most of the oracle's edge (CHECKED command, §7 S2).
6. **Per class, the evidence is uneven.** Rich: index and commodity futures (intraday momentum, tape), crypto spot and perps (periodicity, book imbalance, funding), US stocks (stocks in play, intraday periodicity, OFI). Thin: spot FX at retail venues (no tape; tick volume tracks real volume hourly per one vendor study, E30), gold CFDs (COMEX futures lead price discovery, E32), index CFDs (nothing found on the CFD itself). Empty cells are listed in §4.
7. **Yes, reading market state reveals tradeable patterns, and they decay.** Intraday momentum, stocks in play, funding extremes, fixing windows and same-time-of-day continuation are each a state-conditioned pattern a unit could trade (§7). Published patterns lose about half their returns after publication (E42), and FX technical rules faded over a decade (E17). So "strategies born from the MIS" are a real source of units, each needing a mechanism line and a decay watch.

---

## 1. Evidence catalogue

Each row: what it tested, sample and period, costs, out-of-sample (OOS), lag, look-ahead risk. Rows E01 to E04 come through research 05 and were not re-read.

| Id | Source | Asset, data, bars | Sample and period | Costs | OOS result | Lag or horizon | Look-ahead and other risks |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E01 | Lorden bound, CUSUM optimality (via research 05 §1.3) | theory | none | none | bound | delay ≈ ln(false-alarm spacing) ÷ information per bar | assumes known change; real delays longer |
| E02 | Andersen & Bollerslev 1997, intraday periodicity (via 05) | FX, equities, 5m | per paper | none | n/a | seasonality dominates HF volatility | must deseasonalise before any change test |
| E03 | Cont, Kukanov & Stoikov 2014, OFI (via 05) | US stocks, book | per paper | none | contemporaneous fit | same interval | explains, does not forecast far |
| E04 | Gould & Bonart 2016, queue imbalance (via 05) | stocks, book | per paper | none | OOS next-mid accuracy gain | one tick | large-tick vs small-tick differ |
| E05 | Cont, Cucuringu & Zhang 2023, cross-impact of OFI. CHECKED https://arxiv.org/html/2112.13213 | US stocks, multi-level book | sample per paper, not read | not read | lagged cross-asset OFI raises OOS R² for 1-minute returns; profit shown | decays within minutes | integrated multi-level OFI explains contemporaneous impact; cross terms help forecasting only briefly |
| E06 | Garaj 2025 thesis, Charles Univ. PRACTITIONER (thesis). CHECKED https://dspace.cuni.cz/handle/20.500.11956/213492 | BTCUSDT perp, 20-level book, 100 ms | most of 2025 | none stated | OFI + trade-flow imbalance explain about 7.5% of OOS return variation at 100 ms, with purging and embargo | no economic edge beyond 30 s | single asset, single year |
| E07 | Pindza 2026, Frontiers in Blockchain. CHECKED https://www.frontiersin.org/journals/blockchain/articles/10.3389/fbloc.2026.1811716/full | 6 cryptos, Binance spot and perps, 1m | 3.4 M bars, Aug 2025 to Feb 2026 | retail fees (20 bps round trip spot) | features carry weak, leakage-free information; gradient boosting overfits; no strategy survives fees at a 5-minute hold; models transfer spot↔futures of one asset, not across assets | 5-minute target | 6.5 months only |
| E08 | Bieganowski & Ślepaczuk 2026. CHECKED https://arxiv.org/abs/2602.00776 | 5 Binance perps, book and trades, 1s | Jan 2022 to Oct 2025 | taker and maker backtests | feature rankings and effect shapes stable across assets of very different size | seconds | abstract read only |
| E09 | Albers, Cucuringu, Howison & Shestopaloff 2024. CHECKED https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5074873 | Binance BTC perp, live experiment | per paper | real fills | maker fill likelihood is negatively tied to post-fill return; viable maker logic trades against book imbalance | touch to short horizon | live data, one venue |
| E10 | Gao, Han, Li & Zhou 2018, JFE. CHECKED https://www.sciencedirect.com/science/article/abs/pii/S0304405X18301351 | SPY and 10 ETFs, half-hour returns | 1993 to 2013 | yes, survives | first half-hour predicts last half-hour; OOS R² 1.4% (2.0% with the 12th half-hour); stronger on high-volatility, high-volume and news days | known by 10:00 New York, traded at 15:30 | ETFs only; costs assumed |
| E11 | Baltussen, Da, Lammers & Martens 2021, JFE. CHECKED https://academicweb.nd.edu/~zda/intramom.pdf | 17 equity index, 16 bond, 21 commodity, 8 currency futures | Dec 1974 to May 2020 | not read | rest-of-day return predicts the last 30 minutes "everywhere"; asset-class Sharpe 0.87 to 1.73; reverts over next days; tied to gamma hedging | known before the last half-hour | the second-to-last half-hour predictor does not carry to commodities and currencies |
| E12 | Elaut, Frömmel & Lampaert 2018, JFM. CHECKED https://biblio.ugent.be/publication/8060014 | RUB/USD on MICEX, transactions | 2005 to 2014 | not read | intraday momentum present, driven by liquidity providers avoiding overnight risk | half-hour | an FX market with explicit hours, unlike 24h spot FX |
| E13 | Heston, Korajczyk & Sadka 2010, JF. CHECKED https://arxiv.org/abs/1005.3535 | 1,715 NYSE stocks, half-hour | 2001 to 2005 | execution-timing gain about one effective spread | short-term reversal from bid-ask bounce and liquidity imbalance lasting under an hour; same-time-of-day continuation for 40+ days | under 1 hour (reversal); daily multiples (continuation) | in-sample panel |
| E14 | "Persistence in High Frequency Financial Data", Brunel working paper 2215. CHECKED https://www.brunel.ac.uk/economics-finance-and-accounting/research/pdf/2215-Oct-GMC-High-Frequency-persistence.pdf | EuroStoxx 50 futures, trades | 2002 to 2018, 720 M trades | none | Hurst by R/S: intraday 0.37, daily 0.54, monthly 0.72; persistence varies over time | sliding windows of months | traded prices carry bid-ask bounce, which pushes intraday Hurst down (INFERRED, see §7 S1) |
| E15 | Jones & Batten, AUD/USD local Hurst. CHECKED https://export.arxiv.org/pdf/math/0412344v1.pdf | AUD/USD spot quotes | per paper | none | dependence and volatility vary across the 24-hour day, aligned with market opens and closes | intraday | descriptive only |
| E16 | Wiśniewska 2015. CHECKED https://doi.org/10.15678/aoc.2015.1302 | EUR/USD 1m bid and ask | per paper | spread via bid/ask | a high-volatility mean-reversion intraday rule earned well | 1m | no OOS design stated in the abstract; weak venue |
| E17 | Neely, Weller & Ulrich 2009, JFQA. CHECKED https://files.stlouisfed.org/files/htdocs/wp/2006/2006-046.pdf | FX majors, daily | rules from 1970s-90s studies, tested to 2005 | yes | true OOS: 1970s-80s profits were genuine, gone by early 1990s for filter and moving-average rules; complex rules decayed more slowly | daily | publication and adaptation |
| E18 | Christensen, Godsill & Turner 2020. CHECKED https://arxiv.org/abs/2006.08307 | intraday futures/securities | per paper | not read | HMM for intraday momentum with 2 or 3 states; side information (realised-vol ratio, intraday seasonality) enters the transition matrix | claims no filter lag | abstract read only |
| E19 | Nystrup, Lindström & Madsen, jump-penalised HMM; greedy online classifier. CHECKED https://backend.orbit.dtu.dk/ws/files/255194701/Learning_hidden_Markov_models_with_persistent_states_by_penalizing_jumps_ACCEPTED_ESWA.pdf and https://backend.orbit.dtu.dk/ws/portalfiles/portal/242396317/Greedy_online_classification_of_persistent_market_states_using_realized_intraday_volatility_features.pdf | S&P 500, daily with intraday-volatility features; simulations | per paper | turnover cost shown | penalising jumps gives persistent states, lower turnover, robustness to misspecification; an HMM detects changes as fast but with many spurious short-lived switches | online, no smoothing | research 05 adds a 25-day median crash latency for jump models on daily data |
| E20 | Koukorinis, Peters & Germano 2025. CHECKED https://discovery.ucl.ac.uk/id/eprint/10209714/1/MethodolComputApplProbab_27_36_2025.pdf | 40 FTSE 100 stocks, trade-clock microstructure | per paper | none | HMM fitted per day on the previous day, features into SVM/MKL; OOS day-ahead classification beats logistic and feed-forward nets | intraday regimes | classification accuracy, not trading |
| E21 | Hendricks, Gebbie & Wilcox 2015. CHECKED https://arxiv.org/abs/1508.04900 | intraday microstructure features | per paper | none | online state detection by clustering correlation matrices; time-scale hierarchy of states | streaming | no trading result |
| E22 | Tenyakov, Mamon & Davison 2016. CHECKED https://dlnext.acm.org/doi/10.1016/j.knosys.2016.03.014 | GBP/JPY, USD/JPY high-frequency | per paper | none | zero-delay HMM fits and forecasts better than GARCH and random walk on likelihood and error | high frequency | statistical fit, no trading |
| E23 | Ardia, Bluteau, Boudt & Catania 2018, IJF. CHECKED https://lirias.kuleuven.be/retrieve/7cf220ed-9a49-4cee-a4eb-b586e7f2c934 | many stocks, indices, FX, daily | large-scale | n/a | MS-GARCH gives better VaR, ES and left-tail forecasts than single-regime GARCH at 1, 5 and 10 days, mostly for stocks | daily | risk forecasts, not entries |
| E24 | Corsi 2009, HAR-RV (via 05) | realised vol | per paper | n/a | strong vol forecasts | daily | none |
| E25 | Easley, López de Prado & O'Hara 2012, volume clock. CHECKED https://c.mql5.com/forextsd/forum/173/the_volume_clock_-_insights_into_the_high_frequency_paradigm.pdf ; Ané & Geman 2000. CHECKED https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00286 | E-mini S&P futures; stocks | Jan 2008 to Oct 2010 (E-mini) | none | volume-time sampling removes most intra-session seasonality and partly restores normality; trade count is an even better clock (Ané & Geman) | bar-dependent | no trading claim |
| E26 | Daru Finance replication of info-driven bars. PRACTITIONER. CHECKED https://daru.finance/research-review/lopez-de-prado/information-driven-bars | 27 Binance perps, 9 ETFs, 8 FX majors, 1m base | per page | none | tick, volume and dollar bars cut excess kurtosis (crypto 5.29 to about 1.5; equities 9.95 to 3.4; FX tick bars 2.98 to 1.06); bars must not span the overnight gap | n/a | no edge claim; FX has no volume or dollar bars |
| E27 | Parkinson 1980, range estimator (via 05) | any OHLC | n/a | n/a | about 5× fewer observations than close-to-close | n/a | none |
| E28 | Zhang, Mykland & Aït-Sahalia 2005, JASA. CHECKED https://www.nber.org/system/files/working_papers/w10111/w10111.pdf | theory and data | n/a | n/a | at the highest frequencies realised variance mostly measures noise; FX practice samples 5 to 30 minutes; a two-scale estimator fixes it | tick | bears on every tick-level sensor |
| E29 | Corwin & Schultz 2012, JF; Abdi & Ranaldo 2017, RFS. CHECKED https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2012.01729.x , https://academic.oup.com/rfs/article/30/12/4437/4047344 | US stocks, daily OHLC | up to 1926 onwards | n/a | spread estimates from high, low and close track TAQ spreads; Abdi-Ranaldo best overall | daily | stock data; intraday use on crypto in E33 (Brauneis) |
| E30 | Marney, tick vs traded volume in FX. PRACTITIONER (vendor). CHECKED https://varianse.com/wp-content/uploads/2022/07/fxvolume-tick-volume-vs-real-volume-study-1.pdf ; FMG discussion paper 265. CHECKED https://www.fmg.ac.uk/sites/default/files/2020-10/dp265.pdf | EURUSD, USDJPY, GBPUSD, EURCHF; HotSpot and EBS volume vs eSignal ticks | per study | n/a | hourly Pearson 0.96 to 0.99 | hourly only; finer untested | vendor sells volume indicators; FMG finds monthly tick-volume ties unstable over time |
| E31 | Evans & Lyons 2002, JPE. CHECKED https://www.bis.org/publ/bppdf/bispap02j.pdf | DM/$, ¥/$ interdealer order flow | May to Aug 1996 | n/a | order flow explains about 60% of daily DM/$ changes; beats random walk 1 day to 2 weeks | daily | "forecasts" use realised order flow, so not true OOS; interdealer flow is not visible to retail |
| E32 | Hauptfleisch, Putniņš & Lucey 2016, JFM. CHECKED https://doi.org/10.1002/fut.21775 ; Caminschi & Heaney 2013. CHECKED https://doi.org/10.1002/fut.21636 ; Cai, Cheung & Wong 2001. CHECKED https://onlinelibrary.wiley.com/doi/10.1002/1096-9934(200103)21:3%3C257::AID-FUT4%3E3.0.CO;2-W | gold: London OTC spot vs COMEX futures, 1s; GC and GLD around the PM fix; GC intraday | 1997 to 2014 (price discovery) | n/a | COMEX futures lead price discovery with about a tenth of London's volume; after GLOBEX, no daylight pattern; PM fix lifts GC volume over 50% and volatility over 40%; employment, GDP, CPI and personal income are the biggest announcements | 1s to intraday | supports reading the GC tape for a gold CFD |
| E33 | Crypto periodicity: Hansen, Kim & Kimbrough 2021. CHECKED https://arxiv.org/html/2109.12142v2 ; Brauneis, Mestel & Theissen 2024. CHECKED https://link.springer.com/article/10.1007/s11156-024-01304-1 ; Baur et al. 2019. CHECKED https://ideas.repec.org/a/eee/finlet/v31y2019icp78-92.html | BTC, ETH on Coinbase, Binance, Uniswap; 1,940 pairs on 38 exchanges; 7 exchanges | 15 M+ observations (Baur) | n/a | strong day-of-week, hour-of-day and minute-of-hour patterns in volatility and volume; spikes at funding times 0h, 8h, 16h UTC; activity peaks 16:00-17:00 UTC across venues; return anomalies not persistent, activity patterns persistent | zero (calendar) | descriptive |
| E34 | Funding as a signal: "funding-rate-alpha" repo. PRACTITIONER (unreviewed). CHECKED https://github.com/OctopusTakopi/funding-rate-alpha ; AIJMR 2026. CHECKED https://www.aijmr.com/papers/2026/4/1493.pdf | 791 USDT perps, 2.43 M settlements; Binance BTCUSDT | 2020 to 2026; Sep 2019 to Aug 2026 | 4 bps one-way schedule (repo) | repo: funding level predicts returns only at 8 h and shorter, too little to trade; sign flips between a 2020-21 and a 2023-26 regime; open-interest conditioning collapses under a same-day control; carry nets 8.9 bps a day, mostly in 2020-21. AIJMR: extreme negative funding (bottom decile of trailing 180 days) is followed by about +0.5% over 24 h; the positive tail is not | settlement to 24 h | unreviewed sources; regime-dependent |
| E35 | Zarattini, Barbon & Aziz 2024, SSRN 4729284. CHECKED https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284 | 7,000+ US stocks, 5m opening range | 2016 to 2023 | yes | restricting ORB to "stocks in play" (unusual relative volume) lifts results; top-20 portfolio net Sharpe 2.81 | known at minute 5 | practitioner authors; one period |
| E36 | Pepelyshev & Polunchenko 2015. CHECKED https://arxiv.org/html/1509.01570 | one stock, daily | 2001 to 2003 case | n/a | Shiryaev-Roberts and CUSUM both detect a drift change about a day late at a false-alarm spacing of about 77 samples | 1 bar | single case |
| E37 | Hurst sample-size studies. CHECKED https://www.sciencedirect.com/science/article/abs/pii/S0098300403001055 (short series), https://doi.org/10.36334/modsim.2011.d3.rea (Rea et al.), https://pmc.ncbi.nlm.nih.gov/articles/PMC3204962/ (Cannon et al.), https://mpra.ub.uni-muenchen.de/16446/1/MPRA_paper_16446.pdf (Krištoufek) | simulated series | n/a | n/a | under 500 points Hurst is too uncertain to use; R/S is biased; acceptable estimators need 700 to 4,000+ points; telling two H values 0.1 apart needs about 32,768 points | n/a | non-finance series in some studies |
| E38 | Kaufman's efficiency ratio. PRACTITIONER. CHECKED https://www.tradingview.com/support/solutions/43000773012-kaufman-s-adaptive-moving-average-kama/ , http://www.adaptrade.com/Newsletter/NL-AdaptIndicators.htm | definition | n/a | n/a | net move ÷ sum of bar moves over N bars; near 1 trending, near 0 choppy | N bars | no peer-reviewed OOS test found |
| E39 | Entropy as a state: arXiv 2512.15720. CHECKED https://arxiv.org/html/2512.15720v1 ; Shternshis & Mazzarisi 2024. CHECKED https://link.springer.com/article/10.1007/s10203-023-00427-9 | SPY trades at 1s; meme and IT stocks | 36 trading days (SPY) | fixed costs assumed | low order-flow entropy predicts larger 5-minute moves (2.9× at the 5th percentile) with no directional skill; walk-forward over 5 folds | 120 s window | one instrument, 36 days, one day gave 38% of profit; entropy needs seasonality and noise filtered first |
| E40 | 3D Ising market model. CHECKED (abstract only) https://www.sciencedirect.com/science/article/abs/pii/S0378437116303338 | model | n/a | n/a | links interaction intensity to volatility | n/a | no trading test found |
| E41 | Practitioner regime models: Two Sigma GMM. CHECKED https://www.twosigma.com/articles/a-machine-learning-approach-to-regime-modeling/ ; State Street t-mixture-GARCH. CHECKED https://www.ssga.com/library-content/assets/pdf/global/pc/2025/decoding-market-regimes-with-machine-learning.pdf | 17 factors, monthly, since the 1970s; 23 features | decades | n/a | four regimes (crisis, steady state, inflation, "walking on ice") used for risk and allocation | monthly | allocation lens, not trading timing |
| E42 | McLean & Pontiff 2016, JF. CHECKED https://gwern.net/doc/economics/2016-mclean.pdf | 97 stock predictors | per paper | n/a | returns 26% lower out of sample, 58% lower after publication; price-and-volume-only predictors decay more | months | the base rate for "published patterns fade" |
| E43 | Market-state classifier ensembles, BTC. CHECKED https://ar5iv.labs.arxiv.org/html/2012.03078 | BTC/USDT Binance, 1m | train 2018-19, past Jan-May 2020, OOS May-Sep 2020 | 0.05% per trade, next-open fills | ensembles outperform OOS; labels are built from future data and used only as training targets, with gaps between sets | 1m | short OOS; strategy selection on a custom metric |
| E44 | Crypto HMMs at daily scale: Koki, Leonardos & Piliouras 2020. CHECKED https://arxiv.org/abs/2011.03741 ; Giudici & Abu Hashish 2020. CHECKED https://onlinelibrary.wiley.com/doi/10.1002/qre.2673 | BTC, ETH, XRP daily | per paper | n/a | four-state non-homogeneous HMM gives best one-step density forecasts | daily | density fit, not trading |
| E45 | Directional change + HMM on FX ticks. CHECKED https://arxiv.org/html/2309.15383v1 | several FX pairs, tick data | per paper | not read | improved thresholds plus HMM regime-change flag raise profit and cut risk | event time | abstract only; costs not checked |
| E47 | Yao, Cao, Zhai, Liu, Xiang & Wang 2020, ESWA. CHECKED https://doi.org/10.1016/j.eswa.2020.113722 | 4 FX rates hourly; CSI 300 5m order book; US industry daily | FX Jan 2009 to Aug 2015 | not read | penalised VAR semi-Markov HMM recognises anomalous events better and gives a better pseudo-trading Sharpe at minute, hour and day frequencies | hourly (FX) | pseudo-trading; abstract read only |
| E48 | Iwatsubo, Watkins & Xu, RIETI DP 17-E-120. CHECKED https://www.rieti.go.jp/jp/publications/dp/17e120.pdf | gold and platinum futures, Tokyo and New York | per paper | n/a | volatility peaks at the Tokyo, London and New York day-session opens; Tokyo and New York opens most volatile | intraday | descriptive |
| E49 | Helminen 2022, Aalto bachelor's thesis. PRACTITIONER (thesis). CHECKED https://aaltodoc.aalto.fi/items/7a663327-a08a-4f52-b274-33e881be7c7f/full | ETH perps, Binance and FTX | Dec 2019 to Sep 2022 | not read | funding Granger-causes price; a forecast-based backtest showed an edge | per paper | student work |
| E46 | "Machine Learning in the Order Book", Microstructure Lab. PRACTITIONER. CHECKED https://themicrostructurelab.substack.com/p/machine-learning-in-the-order-book | Binance BTC, ETH perps, 1s | Oct 2025 to May 2026 | none | boosting beats ridge at 1 s on every test day; at 60 s nothing beats anything | 1 to 60 s | blog |

---

## 2. Matrix A: style × bar type against the data a market offers

Rows follow his order: style, then the bar or clock. Columns are data levels (the rungs of `mis-field.md` B004, CHECKED). A cell lists what is tested there, with the evidence row ids. "none found" means this run found no serious study; it is not proof that none exists.

| Style × bar | Price only (OHLC, quote ticks) | Price + real volume | Order book (depth) | Trade tape (signed trades) | Open interest, funding, basis |
| --- | --- | --- | --- | --- | --- |
| Scalper, sub-second to seconds, tick or event bars | microstructure noise dominates (E28); quote-tick counts as activity (E30) | trade-count clock best for normality (E25) | queue and depth imbalance predict next mid moves (E04, E08, E46); OFI explains same-interval moves (E03); maker logic must fade imbalance (E09) | OFI + trade-flow imbalance, about 7.5% OOS at 100 ms, gone by 30 s (E06) | funding-time spikes in activity (E33) |
| Scalper, 1m to 5m time bars | seasonal "now versus usual" ratios (E02, research 05 T1); range estimator (E27); spread from OHLC (E29); ER, VR, AC1 need hours (§7 S1); short-term reversal partly bounce (E13, E14); one FX 1m mean-reversion study, no OOS (E16) | 5m stocks-in-play filter (E35); minute features too weak after retail fees (E07) | lagged cross-asset OFI helps 1-minute forecasts briefly (E05) | none found at 1m-5m beyond E07 | funding level predicts ≤ 8 h but too little to trade (E34) |
| Scalper, tick or volume bars | tick bars Gaussianise FX returns (E26) | volume bars remove intra-session seasonality (E25, E26) | none found | none found | none found |
| Intraday, 15m to 1h | intraday momentum into the close from the rest-of-day return (E10, E11, E12); local Hurst follows session opens (E15); HMM intraday momentum (E18) | momentum stronger on high-volume days (E10) | none found | none found | gamma-hedging link via options data (E11) |
| Intraday to swing, 1h to 4h | enhanced semi-Markov HMM on hourly FX, better pseudo-trading Sharpe (E47); zero-delay HMM fit (E22); jump-penalised online states with intraday-volatility features (E19) | none found | none found | none found | extreme funding tails over 24 h (E34) |
| Swing and position, daily and slower | MS-GARCH for risk (E23); HAR (E24); HMMs and HSMMs on crypto and indices (E44); FX technical rules decay (E17); monthly persistence H 0.72 (E14); regime factor models (E41) | none needed here | n/a | interdealer FX order flow explains daily moves (E31) | carry harvesting (E34) |
| News and event clock | macro releases dominate gold volatility (E32); intraday momentum stronger on news days (E10) | volume spikes at the gold PM fix (E32) | none found | none found | funding settlements as scheduled events (E33) |

**Reading the matrix (INFERRED).** The top two rows are microstructure; the evidence there is about pressure and liquidity, not "trending or ranging". The middle rows hold the best documented timing patterns (intraday momentum), which are known states (a measured return), not inferred regimes. Regime models with trading evidence sit in the bottom rows.

## 3. Matrix B: asset class against data class, with evidence per cell

Rows are the classes now in scope. "Venue fact" cells cite research 02 through STATE (CHECKED `STATE.md:179`) or the cited paper.

| Class | Price only | Real volume | Order book | Trade tape | OI, funding, basis | Calendar and events |
| --- | --- | --- | --- | --- | --- | --- |
| Spot FX (cTrader) | seasonality (E02); local Hurst by session (E15); 1m MR study (E16); daily rules decayed (E17) | none: tick volume only; tracks traded volume hourly (E30) | broker L2 exists, no study of its predictive power (empty) | none exists; interdealer flow matters daily but is not visible (E31) | swap only | 5 p.m. New York roll; sessions (research 02) |
| Gold and metals (CFD) | intraday volatility peaks at Tokyo, London, New York opens (E48) | none on the CFD | broker-dependent | none on the CFD; COMEX GC tape leads (E32) | GC open interest | London fixes, COMEX open, US macro releases (E32) |
| Index CFDs | none found on CFDs themselves | none | broker-dependent | none; futures carry the tape | none | cash open and close, intraday momentum into the close (E10, E11) |
| Real futures (index, commodity, FX, bond) | intraday momentum everywhere (E11); intraday anti-persistence (E14) | volume clock (E25) | OFI literature mostly on stocks; transfer INFERRED | full tape; delta and VPIN (VPIN discredited, research 05 §1.2) | open interest, COT | roll, settlement, RTH vs ETH |
| US stocks (MT5 CFDs at IC; exchange via other brokers) | half-hour periodicity (E13); OHLC spread estimators (E29) | stocks in play by relative volume (E35) | OFI and cross-impact (E03, E05) | trade signs via TAQ in studies | none | earnings, opening auction, corporate actions |
| Crypto spot | periodicity, 16-17 UTC peak (E33); minute features weak after fees (E07) | real but fragmented per venue (E33) | book features stable across assets (E08) | trades public per venue | none | 24/7, weekends quieter (E33) |
| Crypto perps (Binance, Hyperliquid) | HMM daily (E44); 1m classifier ensembles (E43) | real | imbalance predicts seconds ahead (E06, E46); maker contrarian (E09) | public trades | funding level, extremes, OI (E34) | funding hours 0/8/16 UTC on Binance; hourly on Hyperliquid (research 02) |

---

## 4. Empty cells (no serious evidence found this run)

1. **Spot FX broker depth (cTrader L2) as a predictor.** Studies of OFI use exchange books (E03 to E06). Whether an aggregated retail-broker book carries the same information is untested. A QMX study would be the first evidence.
2. **Tick-volume information below one hour in FX.** The only correlation study is hourly and vendor-written (E30).
3. **Index CFDs and gold CFDs as their own data.** Everything found is about the futures or the London spot market (E11, E32). Borrowing the futures reading is supported for gold by price discovery (E32), and INFERRED for indices.
4. **HMM, MS-GARCH or jump models at 1m to 5m with trading results after costs.** Found only statistical fit (E22), classification (E20), one tick-data FX study with unchecked costs (E45) and one crypto ensemble with a four-month OOS (E43).
5. **Lag and false-alarm rates of ER, variance ratio or Hurst as live filters at 1m or 5m on real data.** No peer-reviewed study. My simulation (§7 S1) is the only number here, and it is on simulated bars.
6. **Detector lag on tick or volume bars versus time bars.** Bar-type studies stop at distribution shape (E25, E26).
7. **Hyperliquid HIP-3 perps on stocks, gold and FX.** New markets; no studies.
8. **Perps funding or open interest at 1m to 5m.** Evidence is at settlement to 24-hour horizons (E34).
9. **Cross-sectional FX readings (currency strength, dispersion) as intraday filters.** None found; only stock cross-impact (E05).
10. **Market-physics measures with trading tests.** Ising: none (E40). Entropy: one 36-day single-instrument study (E39).
11. **Ensembles of market-state sensors (the old HMM + BOCPD + MS-GARCH ensembler, research 19 §2).** No study found that tests such an ensemble at intraday horizons.

## 5. Method families: shared across cells, or one cell only

**Families that recur across many cells (candidates for one shared reading library):**

| Family | Cells it serves | Evidence |
| --- | --- | --- |
| Seasonal baseline, "now versus usual for this minute of the week" (volatility, spread, tick rate, depth, volume) | every class and every style; the calendar differs per class | E02, E15, E25, E33, research 05 T1 |
| Volatility estimators (range, realised, two-scale) and volatility models (EWMA, HAR, GARCH family) | every class; models at day scale | E24, E27, E28, E23 |
| Liquidity and cost readings (quoted spread where quotes exist; OHLC spread estimators where not) | every class | E29, research 05 |
| Calendar and event readings (sessions, fixes, releases, roll, funding times) | every class, zero lag | E10, E32, E33 |
| Persistence family: ER, variance ratio, autocorrelation, Hurst, entropy | every class with prices; slow; needs noise and seasonality removed | E14, E37, E38, E39, §7 S1 |
| Change-point detectors (CUSUM, Shiryaev-Roberts, robust BOCPD) | every class; fast for volatility, slow for direction | E01, E36, research 05 T2 |
| Regime models (HMM, jump models, mixtures) | session, day and slower tiers in every class | E19, E41, E44 |
| Known-state returns (rest-of-day return, first half-hour return, overnight return) | every market with a daily close: futures, indices, stocks, FX futures | E10, E11, E12 |
| Cross-sectional readings (lead-lag, dispersion, cross-impact) | classes with many related markets | E05, E32 (lead), mis-field B044 |

**Families that make sense in one cell only:**

| Family | Only where | Evidence |
| --- | --- | --- |
| Book imbalance, OFI, queue imbalance | venues with depth; strongest at seconds | E03 to E06, E08, E46 |
| Trade-flow imbalance, delta, footprint | venues with a tape (futures, crypto, stocks) | E06; research 02 |
| Funding level and extremes, open-interest change, liquidations, basis | perps (OI also futures) | E34, E33 |
| Relative volume "in play" | single stocks with news | E35 |
| Fixing windows | gold (London), FX (4 p.m. London fix) | E32 |
| Gamma-hedging pressure | indices with listed options, leveraged ETFs | E11 |
| Tick volume as volume | FX and CFDs | E30 |
| Roll and settlement calendar | futures | research 02 |

## 6. Where the papers disagree, and why (mostly horizon)

| Disagreement | Side A | Side B | Reconciliation |
| --- | --- | --- | --- |
| Do intraday returns persist or revert? | anti-persistent intraday, H 0.37 (E14); reversal under one hour (E13) | momentum into the close (E10, E11) | different horizons: minutes revert (bounce, liquidity), half-hours to the close continue (hedging, rebalancing). INFERRED |
| Are HMMs usable? | HMMs fit and forecast high-frequency FX (E22); daily crypto densities (E44) | HMMs switch spuriously; penalised jump models are needed in production (E19) | fit is not tradability; turnover from false switches is the cost |
| Is OFI the strongest book signal? | OFI explains price moves best (E03) | static imbalance beat OFI as a predictor in one blog test (substack noted in search results; not in the catalogue) | contemporaneous explanation versus forward prediction differ |
| Does machine learning help on microstructure? | boosting wins at 1 s (E46) | boosting overfits at 1-5 min (E07) | horizon again: the signal decays within seconds |
| Is funding a price signal? | Granger-causal and tradable in a student thesis (E49) | too small to trade, sign flips by regime (E34) | treat funding as carry and a tail state, not a linear predictor |
| Do information-driven bars help? | yes for distribution shape (E25, E26) | no edge claim anywhere | shape helps estimators, not necessarily profits |
| Where does gold's price form? | London has ten times the volume | COMEX leads price discovery (E32) | market structure beats volume |
| Do technical rules work in FX? | 1970s-80s genuine (E17) | gone by the 1990s (E17) | adaptive markets: real and decaying |

## 7. His 28 Oct point: does market-state reading reveal inefficiencies, and is that a source of units?

His words: "there is a huge possibility we can discover market inefficiencies with only that, which means those alone can give us strategies" (`T1:1999`, CHECKED).

**Yes, with evidence, and with a decay warning.**

| State-conditioned pattern | Class | Evidence | Mechanism the paper gives |
| --- | --- | --- | --- |
| The rest-of-day return predicts the last half-hour | 60+ futures, all classes | E11 | gamma hedging by option dealers and leveraged ETFs |
| First half-hour predicts last half-hour, stronger on volatile, high-volume, news days | US index ETFs | E10 | infrequent rebalancing, late-informed traders |
| Same half-hour tomorrow continues today's move, for 40 days | US stocks | E13 | institutional flow patterns |
| Opening range breakout works on "stocks in play" | US stocks | E35 | news-driven attention |
| Extreme negative funding precedes a 24-hour rebound | BTC perps | E34 | crowded shorts paying carry |
| PM fix lifts volume and volatility in GC | gold | E32 | the benchmark auction |
| Funding-time and minute-of-hour activity bursts | crypto | E33 | algorithmic schedules, funding |
| Low entropy precedes larger moves (size, not direction) | SPY | E39 | informed trading |

**What every such source needs, as a unit (INFERRED):** a mechanism line (why it should persist), a decay watch (published predictors lose 58% after publication, E42; FX rules faded over about a decade, E17), and a test on stamped readings only (E43 shows how labels built with future data must stay training targets, never inputs). The mis-field idea "strategies born from the MIS" (`mis-field.md` B098, CHECKED) and the per-class inefficiency hunts (B021) are where these land.

**Two of my own measurements behind the short answer.** Both are simulations on Gaussian bars, rerunnable, not real data.

- **S1, sensor lag and false alarms.** `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\mis_sensor_lag.py`, run with targets 1440 and 14400 bars between alarm episodes (CHECKED command). Detail and tables in research 22 §2.
- **S2, label at entry versus label in hindsight.** `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\mis_label_timing.py`, run with state spells of 120, 720 and 2,880 bars (CHECKED command). Detail in research 22 §4.

## 8. Numbers this file touches (names and starting defaults, none settled)

| Number | Starting default | Why that default |
| --- | --- | --- |
| False-alarm spacing per reading per market | one alarm episode per 10 trading days of bars | research 05 §1.3 used the same spacing (CHECKED) |
| Minimum points before a Hurst value is shown | 1,000 bars; flag below 4,000 | E37 (700-1,000 minimum for the best estimators; 4,000 for most) |
| Bounce ratio that disqualifies price-only mean-reversion sensors on traded or one-sided prices | flag above 0.1, disqualify above 0.25 (noise sigma ÷ one-bar sigma) | §7 S1: at 0.1 false alarms barely move; at 0.25 they rise 2 to 5 times; at 0.5 they rise 10 to 130 times (research 22 §2) |
| State spell ÷ sensor window, below which a direction label may not gate trades | 5 | §7 S2: ratio 0.5 gave no total gain, 3 kept most, 12 kept nearly all (research 22 §4) |
| Funding extreme tail | bottom and top 10% of the trailing 180 days | E34 (AIJMR) used deciles over 180 days |
| Relative-volume "in play" cut | top 20 by relative volume per day | E35 |

## 9. Not verified

- Many rows were read at abstract or summary level (marked). Costs and OOS design were not checked for E05, E11, E18, E45.
- E06, E26, E30, E34, E46 are theses, vendor pages, blogs or an unreviewed repo; their numbers are their authors' claims.
- One source in the search results (static imbalance beating OFI) was a blog and is not catalogued.
- The simulations assume Gaussian bars, fixed sigma and iid bounce noise. Fat tails, volatility clustering and real seasonality make real lags longer and false alarms more frequent.
- No real price data was used: no Library partition path was found on this machine in the time spent, and downloads (Binance Vision) were not attempted, since a download needs his go.
