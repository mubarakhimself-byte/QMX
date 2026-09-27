# Video reference: terminal-preview.mp4

Source: `C:\Users\Mubarak\Documents\brain\brain\terminal-preview.mp4`  
Reviewed: 2026-09-23  
Method: frames-only review. Initial efficient pass sampled four encoded keyframes at 512 px width; those same moments were then extracted at 1600 px width (00:00, 00:01, 00:05, 00:09) for legible UI labels. No transcript was available; speech and interactions between frames are not established.

## Timestamped observations

- **00:00** — The window title reads **“EUR/JPY 1h - LSE Terminal.”** The app header shows **London Strategic Edge** and top-level sections **Markets, Backtest, Economic, Workspace, Research**. In Markets, the selected subview is **Price & Charts**; adjacent choices include **Options, News, Screener**. The main area is a one-hour EUR/JPY candlestick chart with an indicator overlay and a sharp late-July/early-August drop followed by recovery. The left **Watchlist** shows instrument rows including EUR/JPY, BTC/USD, VIX/USD, DXY/USD, NVDA, AAPL, TSLA, AMAT, NFLX, NAS100/USD, US30/USD, IWM, AUD/JPY, CHF/JPY, EUR/AUD, ES, GC.F, DE30/EUR, XAU/USD, XAG/USD, XPT/USD, and WTI/USD, grouped beneath Forex, Stocks, Crypto, Indices, Commodities, ETFs, Futures, Currency Index, Volatility, and Interest Rates. A right trading ticket shows EUR/JPY with Buy/Sell prices and order fields; below it is an **LSE Assistant** panel. Visible suggested prompts include an account exposure/margin/open P&L risk check, a question about 2y/10y yields and the EUR/JPY curve, and a Z-score mean-reversion strategy/backtest request. A bottom positions area shows balance/equity and a BTC/USD position row.
- **00:01** — **Workspace** is selected, with sub-tabs **IDE, Data Visualisation, Notebook**. The IDE has file `curve_regime_overlay.py` open; the left side is divided into **Library**, **Workspace (15)**, **Data (11)** and **Notebooks (0)**. Library offers **Import LSE Data**. The workspace tree contains strategy scripts; Data lists sample files such as Apple, Bitcoin, Brent Crude, Euro/US Dollar, Gold, Nasdaq, S&P 500, Silver, US Dollar/Japanese Yen, US Large Caps, and US Treasury Curve, with file type/row count indicators. The central editor shows Python strategy code and a lower **Terminal** pane. The LSE Assistant remains docked at right with quick-action labels **list_datasets, preview_dataset, run_backtest, read_guide** (and a further clipped label). The code comments describe a yield-curve regime overlay and refer to US Treasury curve data.
- **00:05** — This higher-resolution extraction corrects the initial low-resolution impression that the workspace was blank: the IDE and `curve_regime_overlay.py` editor are still visible, with **LSE Assistant** expanded on the right. Its response area shows a user prompt: **“Long spx500 only when the 3m10y curve is not inverted and price is above its 200 period moving average. Backtest it.”** A collapsed assistant activity/status row is below. This is a visible backtest request, not evidence of a completed run or its result.
- **00:09** — The window title reads **“GOLD - Gold 1h - LSE Terminal.”** **Backtest** is selected; its sub-tabs are **Algo Development, Machine Learning, Manual**. The editor has multiple strategy tabs and `spx500_curve_ma200_trend.py` selected. The left Library/Workspace/Data panels remain, with the strategy scripts and sample datasets visible. A lower **Terminal** pane is open. The LSE Assistant displays generated strategy/code content and a message that begins **“Run it on SPX500 1h. Want me to check how it holds out-of-sample with a walk-forward, or add a cost pass to see what the spread eats?”** There are visible controls including **Copy** and **To strategy IDE**. This shows a machine-learning/backtest-related workflow surface and generated code, but no resulting metrics or completed backtest are visible.

## What this clip supports

The interface exposes Markets/price charts, a watchlist across multiple asset classes, trading ticket and positions, a Workspace with IDE/data visualisation/notebook tabs, a Library and sample dataset browser, a terminal, and a Backtest area with Algo Development/Machine Learning/Manual tabs. The docked LSE Assistant has dataset/backtest/guide quick actions and displays strategy prompts/code. At 00:05 the assistant responds to a concrete curve-and-moving-average backtest request; by 00:09 a generated strategy is open in Backtest > Algo Development with an option to send it to Strategy IDE.

The visible code and UI make a data/strategy workflow plausible, but this brief clip does not show dataset import completion, an actual model-training run, backtest execution, metrics, or a full click-by-click path. Although **Machine Learning** is a visible backtest sub-tab, no training behavior is demonstrated. “LSE” appears in the product/assistant names; the clip alone does not establish its expansion or any live exchange integration.

## Sampling limits

This is an 11.1-second reference, not a complete product tour. The initial efficient pass selected four encoded keyframes; the higher-resolution pass extracted the same four timestamps directly. Intermediate interactions, hover states, transitions, animation, and changes between sampled moments are missing. The higher-resolution frames make most primary labels and text readable, but fine details can remain soft. No audio transcript was produced.

## Preserved evidence

Original efficient samples:

- [00:00 frame](video-frames/frames/frame_0001.jpg)
- [00:01 frame](video-frames/frames/frame_0002.jpg)
- [00:05 frame](video-frames/frames/frame_0003.jpg)
- [00:09 frame](video-frames/frames/frame_0004.jpg)

Higher-resolution samples for label inspection:

- [00:00 frame, 1600 px](video-frames-highres/frames/cue_0000.jpg)
- [00:01 frame, 1600 px](video-frames-highres/frames/cue_0001.jpg)
- [00:05 frame, 1600 px](video-frames-highres/frames/cue_0002.jpg)
- [00:09 frame, 1600 px](video-frames-highres/frames/cue_0003.jpg)
