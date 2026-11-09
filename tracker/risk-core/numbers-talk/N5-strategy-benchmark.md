# N5: what a strategy must show (the benchmark for the strategy search)

2026-11-09. Model results, not rules. Every value becomes a preset only when he agrees to it.

## The same edge can feel very different

All rows below have the same net edge of 0.2 of the risk per trade, are sized at 5% of the current balance (compounding on every trade), and use 3,000 simulated paths each. No brakes are in the model, and losses are assumed to stop at the full risk.

| Strategy shape | Median trades to 10x | About this many trading days at 8 a day | P(30% drop from a peak) | P(halving) |
|---|---|---|---|---|
| 80% win, each win 0.5 of the risk | 238 | 30 | 7% | 0% |
| 70% win, win 0.71 | 243 | 30 | 30% | 1% |
| 60% win, win 1.0 | 255 | 32 | 66% | 8% |
| 50% win, win 1.4 | 261 | 33 | 86% | 29% |
| 40% win, win 2.0 | 280 | 35 | 95% | 57% |
| 30% win, win 3.0 | 325 | 41 | 98% | 78% |

Reading: speed depends mostly on the edge. Pain depends on the shape. A high-win-rate scalper with the same edge is far smoother than a low-win-rate breakout strategy, so it can carry more risk per trade for the same pain.

## The trap

High win rates often hide rare large losses: gaps, slippage, a stop that does not fill. The model assumes every loss stops at the full risk. An 80% scalper whose worst losses are 3 times the risk is a different animal. So the benchmark has to include the worst loss.

## The benchmark (proposed)

1. **Net edge per trade after costs: at least 0.2 of the risk** (0.1 still works, but takes about twice as many trades).
2. **Smoothness: edge divided by the spread of trade results (the per-trade Sharpe), at least 0.2.** About 0.33 for the 80% shape, 0.20 for 60/1:1, 0.14 for 40/2:1.
3. **Worst losses stay close to the planned risk.** Among the largest losses, none beyond about 1.5 times the risk, after slippage.
4. **Enough trades per day** across the session map (separate bets, not tickers).
5. **Enough out-of-sample trades to believe it.** A count for the methodology session to set.

## Trades per day: an estimate, not a measurement

Separate bets from N4: Asia 3, Europe 3, London-New York overlap 3, US open 10 (6 without single stocks), US afternoon 2, US close 3. A bet is a market that may fire, not a trade. An ORB fires at most once per market per open, and only on qualifying days. A rough ORB count is 3 to 5 trades a day across Tokyo, Europe and the US opens; a scalper adds more. "8 a day" is an assumption until the rules are backtested on the map.
