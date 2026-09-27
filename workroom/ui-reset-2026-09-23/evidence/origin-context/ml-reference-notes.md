# London Strategic Edge reference notes for QMX ML Studio

Checked 2026-09-23. Evidence is separated into observed video/UI, current vendor marketing, and proposed QMX adaptations. These notes describe product surfaces, not validated trading behavior or model quality.

## Evidence and useful capabilities

1. **Market and portfolio context — observed in supplied video.** The Markets screen pairs a one-hour EUR/JPY chart and indicator with a cross-asset watchlist, Buy/Sell ticket, and positions/account strip. This suggests ML work should reconnect to the instrument and portfolio it affects. The frames do not establish live balances or trade execution.

2. **Research workspace — observed in supplied video.** Workspace exposes IDE, Data Visualisation, and Notebook tabs; the IDE has Library, Workspace, Data, and Notebooks areas, a code editor, and lower Terminal. Sample datasets have row/type labels. This supports co-locating data and code, not claims about import completion, execution, or persistence.

3. **Prompt-to-code handoff — observed in supplied video.** A docked assistant shows dataset/backtest/guide quick actions, responds to a curve-and-moving-average backtest request, and later displays generated strategy code with Copy and “To strategy IDE” controls. It offers walk-forward and cost-pass follow-ups. The frames show a request and code, not completed results. For QMX, generated work should remain inspectable and editable.

4. **Model catalogue and guided training form — observed in public ML Studio UI.** The left rail groups models into Forecasting, Classification, Risk Analysis, Deep Learning, Time Series, and Sentiment. Selecting XGBoost Price Predictor opens a Train form with dataset, timeframe, date range, prediction horizon, test split, and model parameters. A right Model Guide explains the model and lists parameter references. Feature engineering selectors include Price Data, Volume, and Momentum. Visible controls do not prove runs complete.

5. **Dataset selection scopes the form — observed in public UI.** Searching “EUR” in the dataset picker and selecting EUR/USD visibly changes the form from BTC/USD to EUR/USD. This is a clear app-specific picker pattern; the page did not establish data provenance, freshness, or custom-data import.

6. **Optimisation is a separate prerequisite-aware stage — observed in public UI.** Train and Optimise are separate tabs. Optimise replaces the model rail with Grid Search, Walk Forward, Monte Carlo, Fixed R:R, Adaptive, and Volatility-Scaled. Before a trained model exists, the center says none is available and requires training; the run control is disabled. The guide changes with the selected method. Walk Forward exposes fold count and describes testing on unseen data; no run was launched.

7. **Risk controls within optimisation — observed in public UI.** Walk Forward exposes ATR/Pips/% distance modes; stop-loss and take-profit ranges; max hold; starting capital; position sizing; lot size; and risk per trade. Its guide describes an out-of-sample result and warns a grid-search winner may be noise. This is the strongest reference for QMX’s risk and position-sizing emphasis, but remains UI copy, not verified methodology.

8. **Algorithm and infrastructure breadth — marketing only.** The current official [ML Studio page](https://www.londonstrategicedge.com/machine-learning-studio/) advertises LSTM, XGBoost, CatBoost, LightGBM, Random Forest, Transformer, ARIMA, Prophet, GARCH, CNN, and GAN models, GPU infrastructure, customizable hyperparameters, and performance reporting. These claims do not prove every option is available or establish the quality and contents of outputs. The page says JavaScript is required for the full platform. The [Terminal landing page](https://www.londonstrategicedge.com/terminal/) was inaccessible through the web research tool; use the local video for its UI evidence.

## QMX adaptations (proposed, not vendor facts)

Keep training and validation as distinct workflow stages with inputs and outputs visible together. Make risk budget, exposure, sizing rule, costs, and capital path first-class alongside predictive scores; show compounding and drawdown before promotion into a strategy. Keep prerequisites and validation windows visible before enabling downstream actions. Let an assistant propose code, then show a reviewable diff and handoff into the strategy workspace. Connect results to charts and observability so users can inspect what ran, on which data, and why risk changed. These fit QMX’s self-extensible platform direction; references do not decide its UI contract or execution authority.

## Source trail and limits

The existing [video reference](../../video-reference.md) records the four sampled moments and limitations. [Live research](../../live-research/quantx-lse-minara.md) records public UI interactions and links saved captures: [ML Studio](../../live-research/screenshots/lse-ml-studio.png), [dataset selection](../../live-research/screenshots/lse-dataset-selected.png), and [Walk Forward](../../live-research/screenshots/lse-walk-forward.png). No sign-in, training, optimisation, trade, download, or installation was performed.

