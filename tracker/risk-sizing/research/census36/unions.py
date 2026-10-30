"""Union counts for concept groups over included articles; plus a few single concepts."""
import json, csv
art = json.load(open("articles.json")); inc = {a: v for a, v in art.items() if v["include"]}
U = {
 "learned model as signal source": ["neural-network", "lstm / rnn / gru", "cnn / convolution", "transformer / attention", "reinforcement-learning", "tree ensembles (RF, boosting)", "svm / knn / naive-bayes", "clustering (k-means, SOM, DBSCAN)", "autoencoder / gan / vae", "llm / ai-agent", "onnx-model"],
 "statistical/econometric model or test as signal or context": ["adf / kpss / stationarity", "cointegration / pairs", "hurst / fractal-dimension", "garch / arch", "arima / autoregression", "kalman-filter", "hidden-markov / markov", "entropy / information", "regression", "pca / svd", "fourier / wavelet / spectral", "autocorrelation / variance-ratio", "bayesian", "ornstein-uhlenbeck / half-life", "copula", "z-score"],
 "evaluation / judge vocabulary": ["performance ratios (Sharpe, Sortino, Calmar, PF)", "hypothesis tests (t, KS, chi2, Wilcoxon)", "walk-forward / out-of-sample", "overfitting controls (CSCV, PBO, deflated Sharpe)", "cross-validation", "monte-carlo / bootstrap / permutation", "expectancy / win-rate", "mfe / mae", "distribution shape (skew, kurtosis, tails)"],
 "averaging / grid / martingale / hedging family": ["grid entry", "grid management", "martingale", "anti-martingale", "recovery (zone/loss recovery)", "hedging / locking", "grid basket TP on weighted average", "averaging / dca"],
 "account-level exits (basket, equity stop, daily loss)": ["basket / total-profit exit", "equity / drawdown close-all (kill switch)", "daily loss limit"],
 "non-time bars (Renko, Kagi, range, tick, Heikin-Ashi)": ["renko / kagi / range / tick bars", "heikin-ashi"],
 "MT5 built-ins absent from dictionary (CCI, WPR, DeMarker, SAR, AO, AC, Alligator, Bulls/Bears, Force, MFI, BW MFI, OBV, A/D, RVI, TRIX)": ["cci", "williams-%r", "demarker", "parabolic-sar", "awesome-oscillator", "accelerator-oscillator", "alligator / gator", "bulls/bears-power (Elder ray)", "force-index", "money-flow-index", "market-facilitation-index", "obv", "accumulation-distribution / chaikin", "rvi (relative vigor)", "trix"],
 "covered core indicators (MA, RSI, Stoch, MACD, ATR, BB)": ["moving-average", "rsi", "stochastic", "macd", "atr", "bollinger-bands"],
}
for k, cs in U.items():
    s = {a for a, v in inc.items() if any(c in v["hits"] for c in cs)}
    print(f"{len(s):5d} ({100*len(s)/len(inc):.0f}%)  {k}")
R = {r["concept"]: r for r in csv.DictReader(open("concept_counts.csv", encoding="utf-8"))}
for c in ["grid entry", "grid management", "martingale", "hedging / locking", "basket / total-profit exit", "heikin-ashi", "renko / kagi / range / tick bars", "supertrend", "elliott-wave", "doji", "megaphone / broadening", "kelly / optimal-f", "prop-firm rules", "drawdown-based size reduction", "consecutive-loss pause", "edge-decay / drift monitor", "equity-curve trading", "stops-level / freeze-level", "close-by (opposite position)", "model / confidence exit", "news straddle", "random entry (test baseline)", "risk of ruin", "confidence-scaled sizing", "correlation exposure limit", "holidays / month-end", "llm / ai-agent", "labeling (triple-barrier, trend-scanning, meta-label)", "market fingerprint / state vector", "volume-spread-analysis", "fixed ratio (Ryan Jones)", "anti-martingale", "recovery (zone/loss recovery)", "equity / drawdown close-all (kill switch)", "daily loss limit", "grid basket TP on weighted average"]:
    r = R[c]; print(f"   {r['articles']:>4} art {r['mentions']:>5} men | {c} | {r['top_ids']}")
