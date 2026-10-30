import re, pathlib
p = pathlib.Path("concepts.py"); s = p.read_text(encoding="utf-8")
NEW = {
 "liquidity-sweep / stop-hunt": r"liquidity (sweep|grab|hunt|raid)s?|stop.?hunt|sweep of (the )?(high|low|liquidity)|swept (the )?(high|low|liquidity)",
 "signal strength / score": r"signal (strength|quality|score)|setup (quality|score|grade)|confidence score|pattern (score|quality)",
 "sentiment / positioning (COT, retail)": r"(market|investor|trader|news|retail) sentiment|sentiment (analysis|indicator|index|score)|commitment of traders|\bcot\b report|open interest|positioning data",
 "fractals-indicator": r"fractals? (indicator|up|down|high|low|level|breakout|point)|\bifractals\b|(up|down|upper|lower) fractals?|williams.{0,10}fractal",
 "range / consolidation": r"consolidation|range.bound|\branging\b|sideways (market|movement|trend|price|phase)|flat (market|period|phase)",
 "portfolio allocation / risk parity": r"portfolio (weights?|allocation|optimi[sz]ation|of (strategies|eas|symbols|assets|experts)|trading|construction|risk|rebalanc)|risk parity|capital allocation|markowitz|mean.variance|efficient frontier",
 "triangle / wedge": r"triangle (pattern|breakout|formation)|(symmetrical|ascending|descending|contracting|expanding) triangles?|\bwedges?\b|chuvashov",
 "price-gap": r"(price|opening|weekend|overnight|session|breakaway|runaway|exhaustion|common|bullish|bearish) gaps?\b|\bgap (up|down|fill|trading|strategy|open)|gaps? (up|down)\b|gap.?fill|fill(ed|s)? the gap",
 "grid entry": r"grid (trading|system|strategy|strategies|orders?|of orders|levels?|ea|expert|hedge|martingale|bot)|grid.based (trading|strategy|ea)",
 "hedging / locking": r"hedg(e|ing) (strategy|strategies|position|trade|ea|expert|technique|grid|order)s?|grid.hedge|lock(ing)? (the )?(position|trade|loss)|locking (strategy|technique)|hedge (the|a|an|each|open) (position|trade|loss)",
 "basket / total-profit exit": r"(basket|total|overall|combined|aggregate|floating) (profit|p/?l|loss) (target|reaches|exceeds|threshold|limit)|close all (positions|trades|orders)? ?(when|at|if|once) .{0,30}(profit|loss|equity)|equity target|basket (take.?profit|tp|close|exit|target)",
 "margin / leverage": r"free margin|margin level|margin call|stop.?out level|leverage (of|1:|is|ratio)|margin requirement",
 "trailing stop": r"trailing ?(stop|sl|profit|take|level|distance|step|start|method|mechanism|logic|class|function|module)|trail(ing|s|ed)? (the )?(stop|sl)",
 "divergence": r"(bullish|bearish|hidden|regular|rsi|macd|momentum|price|oscillator|indicator|classic) divergen|divergence (signal|pattern|setup|between (the )?price)",
 "rollover / swap": r"swap (rate|fee|cost|points|long|short|charge|free)s?|triple swap|rollover|overnight (fee|financing|swap)|swap.free|carry trade",
 "crossover entry": r"cross(es|ed|ing)? (above|below|over|under)|(ma|moving average|line|signal|indicator|macd|stochastic|ema|sma|averages) crossovers?|crossover (signal|strategy|entry|system)",
 "mfe / mae": r"\bmfe\b|maximum favou?rable excursion|maximum adverse excursion|mfe/mae",
 "rate-of-change": r"rate of change|\broc indicator|\broc\s?\(\d",
 "dom / order-book": r"depth of market|order book|market depth|level ?2 (data|quotes|book)|\bdom\b(?! (tree|element|elements|parser|node))",
 "equity-curve trading": r"equity curve.{0,60}(filter|moving average|stop trading|pause|switch off|turn off)|trade (the|its own) equity curve",
}
for cid, rx in NEW.items():
    pat = re.compile(r'(c\("' + re.escape(cid) + r'", \w+, r")([^"]*)(")')
    s, n = pat.subn(lambda m: m.group(1) + rx + m.group(3), s)
    assert n == 1, cid
p.write_text(s, encoding="utf-8"); print("patched", len(NEW))
