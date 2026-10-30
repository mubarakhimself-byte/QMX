"""Title screen re-implemented from 06-mql5-pilot.md section 3.2. Writes screen.json {id: {title, section, year, decision, rule}}."""
import json, re, sqlite3, sys
LIB = sys.argv[1] if len(sys.argv) > 1 else "C:/Users/Mubarak/Desktop/QMX/.worktrees/mql5-library/data/mql5-library"
X = {
 "X1": r"graphical interface|\bgui\b|\bpanel|dashboard|canvas|doeasy|graphics|chart objects?|graphical objects?|\bbuttons?\b|\bcontrols?\b|animation|colou?r|theme|scrollbar|gauge|\bdisplay|mql5 trading tools \(part|trading toolkit \(part|ex5 librar|notification|visuali[sz]|\bwindow|table view|tooltip|\bui\b|interface",
 "X2": r"\bcsv\b|\bjson\b|\bxml\b|database|sqlite|\bsql\b|socket|\bhttp|webrequest|\bapi\b|mqtt|zeromq|telegram|discord|twitter|e-?mail|\bdll\b|\.net|\bc#|opencl|\bfiles?\b|export|import|excel|google sheets|cloud|\bvps\b|algo forge|python-metatrader 5 strategy tester|\bweb\b|\brest\b",
 "X3": r"from basic to intermediate|introduction to mql5|beginner|newbie|design patterns|\boop\b|classes|debugging|logging|unit tests?|structs?|arrays?|strings?|timers?|\bevents?\b|caching|throttl|state persistence|standard library explorer|self-healing|\bmql4\b.*(novice|newbie)|learning mql5|programming basics|syntax|preprocessor|templates in mql|memory|compiler",
 "X4": r"\bmarket\b.*(sell|product)|freelance|signals service|championship|interview|seller|\bcontest",
 "X5": r"developing a replay system|market simulation|developing a trading expert advisor from scratch",
 "X6": r"population optimi[sz]ation algorithms|\b(bat|ant colony|aco|woa|whale|bee|cuckoo|firefly|grey wolf|harmony|bacterial|swarm|artificial)\b.*algorithm|optimization algorithms?\b.*\(part",
}
RESCUE = r"risk|money management|position siz|lot siz|stop ?loss|trailing|breakeven|break-even|regime|volatility|correlation|portfolio|walk-forward|monte carlo|overfit|statistic|forecast|scalp|arbitrage|cointegrat|microstructure|order flow|kelly|drawdown|expectancy|mfe|mae\b|liquidity|spread|session|mean reversion|\bedge\b"
INCLUDE = r"strateg|indicator|signal|pattern|neural|network|machine learning|\bml\b|\bai\b|forecast|predict|statistic|tester|optimi[sz]|expert advisor|\bea\b|trading|trader|trade|eurusd|gold|xauusd|bitcoin|crypto|forex|stock|index|trend|oscillator|candle|price|market|volume|order|position|lot|profit|regress|model|learning|grid|martingale|hedg|breakout|pivot|fibonacci|wave|cycle|filter|entropy|hurst|kalman|garch|arima|markov|bayes|cluster|transformer|lstm|reinforcement|genetic|rsi|macd|moving average|bollinger|ichimoku|zigzag|fractal|smart money|ict\b|supply|demand|support|resistance|channel|arbitrage|portfolio|exit|entry|stop|sizing|risk|volatility|correlation"
def screen(title):
    t = title.lower()
    for k, rx in X.items():
        if re.search(rx, t):
            if k in ("X1", "X2", "X3") and re.search(RESCUE, t):
                return "include", k + "-rescued"
            return "exclude", k
    if re.search(RESCUE, t) or re.search(INCLUDE, t):
        return "include", "include"
    return "unmatched", "none"
c = sqlite3.connect(f"file:{LIB}/index.sqlite?mode=ro", uri=True)
out = {}
for i, title, section, pub, series, part in c.execute("select id,title,section,published,series_title,series_part from articles where fetch_status='ok'"):
    d, r = screen(title or "")
    out[i] = {"title": title, "section": section, "year": (pub or "")[:4], "series": series, "part": part, "decision": d, "rule": r}
json.dump(out, open("screen.json", "w"), indent=0)
from collections import Counter
print(Counter(v["decision"] for v in out.values())); print(Counter(v["rule"] for v in out.values()))
