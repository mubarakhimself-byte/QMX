"""Assembly fingerprint from concept hits. Part A: the 66 sampled articles (flags to check my reading).
Part B: corpus-wide shares among 'strategy-bearing' articles (an entry concept AND a stop or target mention).
Part C: tuning vocabulary counts over all included articles (prose) and tuning hooks in code."""
import json, re, pathlib, sys
from collections import Counter
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from census import split, LIB
art = json.load(open("articles.json")); sample = json.load(open("sample.json"))
G = {
 "entry": ["crossover entry", "threshold / overbought-oversold", "breakout", "pullback / retracement", "retest", "ma-crossover", "grid entry", "forecast-direction entry", "confidence / probability threshold entry", "engulfing", "pin-bar / hammer / shooting-star", "candlestick patterns (generic)", "divergence", "false-breakout", "order-block", "fair-value-gap", "liquidity-sweep / stop-hunt", "arbitrage"],
 "stop": ["stop-loss (generic)", "atr stop", "structural / swing stop", "fixed points SL/TP"],
 "target": ["take-profit (generic)", "rr-multiple target"],
 "trail/BE": ["trailing stop", "breakeven", "indicator trailing (SAR, MA, chandelier)", "step / profit-lock trailing"],
 "partial": ["partial close"],
 "time/session exit": ["time exit / max holding", "session / end-of-day exit", "weekend gap / friday close"],
 "signal exit": ["opposite-signal exit", "model / confidence exit", "stop-and-reverse"],
 "aggregate exit": ["basket / total-profit exit", "equity / drawdown close-all (kill switch)", "daily loss limit", "grid basket TP on weighted average"],
 "trend/regime context": ["trend-direction", "trend-strength", "market-regime", "volatility-regime", "higher / multi timeframe", "trend filter", "adx filter"],
 "session/time filter": ["trading-session", "time-of-day filter", "day-of-week", "asian / session range", "economic calendar / news", "news filter"],
 "cost filter": ["spread filter", "max spread / slippage guard"],
 "sizing beyond fixed": ["percent-risk sizing", "fixed cash risk", "stop-distance sizing", "volatility-scaled sizing", "kelly / optimal-f", "confidence-scaled sizing", "drawdown-based size reduction", "fixed ratio (Ryan Jones)"],
 "averaging/grid/martingale": ["martingale", "grid management", "averaging / dca", "pyramiding", "recovery (zone/loss recovery)", "hedging / locking"],
}
def flags(h): return {g: any(c in h for c in cs) for g, cs in G.items()}
print("PART A sample flags (1 = concept mentioned in prose)")
print("id | " + " | ".join(G))
for a in sample:
    f = flags(art[a]["hits"]); print(a, "|", " | ".join("1" if f[g] else "." for g in G))
strat = [a for a, v in art.items() if v["include"] and flags(v["hits"])["entry"] and (flags(v["hits"])["stop"] or flags(v["hits"])["target"])]
print("\nPART B strategy-bearing included articles:", len(strat))
cnt = Counter()
for a in strat:
    for g, v in flags(art[a]["hits"]).items(): cnt[g] += v
for g in G: print(f"  {g}: {cnt[g]} ({100*cnt[g]/len(strat):.0f}%)")
TUNE = {
 "tester optimisation (generic)": r"optimi[sz](e|ed|ing|ation) (the )?(parameters|inputs|settings)|strategy tester optimi|optimi[sz]ation (mode|results|passes|criteri)",
 "genetic optimiser": r"genetic (algorithm|optimi)|fast genetic",
 "custom optimisation criterion (OnTester)": r"ontester|custom (optimi[sz]ation )?criteri|optimi[sz]ation criteri",
 "walk-forward / periodic re-optimisation": r"walk.forward|re.?optimi[sz]|periodic(ally)? optimi|auto.?optimi[sz]",
 "self-optimising EA": r"self.optimi[sz]|optimi[sz]es? itself|self.adapt|self.tun|self.calibrat",
 "online learning / retraining": r"retrain|online (learning|training)|incremental (learning|training)|train(ed|ing)? on (each|every) (new )?bar",
 "rolling-window recalibration": r"rolling window|sliding window|moving window|recalculat(e|ed|es) (every|each|on each)",
 "adaptive indicator / period": r"adaptive (period|indicator|moving|threshold|parameter|filter|lookback|window)|dynamic (period|threshold|lookback|parameter)",
 "volatility-normalised levels (ATR multiples)": r"atr (multiplier|multiple)|multiple of (the )?atr|times (the )?atr|\d(\.\d)? ?(x|\*|×) ?atr",
 "quantile / percentile thresholds": r"(percentile|quantile).{0,30}(threshold|level|cut)|threshold.{0,30}(percentile|quantile)",
 "regime-switched parameter sets": r"(different|separate|own) (parameters|settings|parameter sets?|rules) (for|in|per) (each )?(regime|market (state|condition|phase))|switch(es|ing)? (between )?(strateg|mode|parameter).{0,30}regime",
 "bandit / strategy selection": r"multi.armed bandit|thompson sampling|\bucb\b|strategy selection|select(s|ing)? (the )?best (strategy|model|parameters)",
 "reinforcement learning policy": r"reinforcement learning|actor.critic|q.learning|policy gradient",
}
print("\nPART C tuning vocabulary over included articles (prose)")
inc = [a for a, v in art.items() if v["include"]]
tc = Counter(); tex = {}
code_hooks = Counter()
HOOKS = {"OnTester()": r"\bOnTester\s*\(", "ParameterSetRange": r"ParameterSetRange", "FrameAdd (optimisation frames)": r"FrameAdd", "TesterStatistics": r"TesterStatistics", "MQL5 Wizard CExpertSignal": r"CExpertSignal|CExpertTrailing|CExpertMoney"}
for a in inc:
    prose, code = split((LIB / "md" / f"{a}.md").read_text(encoding="utf-8", errors="replace"))
    for k, rx in TUNE.items():
        if re.search(rx, prose):
            tc[k] += 1; tex.setdefault(k, []).append(a)
    for k, rx in HOOKS.items():
        if re.search(rx, code): code_hooks[k] += 1
for k in TUNE: print(f"  {k}: {tc[k]} articles, e.g. {' '.join(tex.get(k, [])[-3:])}")
print("code hooks (articles):", dict(code_hooks))
