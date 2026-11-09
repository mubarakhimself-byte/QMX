# Strategy and process ideas raised in the numbers talk

For the methodology session and the Lab. None is tested. His words are in `seeds/operator-words-2026-11-09.md`.

1. **The funnel (M65, his framing, "the way I see it").** Breadth first: map the global markets. Then suitability: which ones suit scalping and which suit an ORB, this season. Then the edge, which belongs to the methodology session and the strategy agents.
2. **Overnight catch-up.** When a home exchange's main session is closed, its index futures and CFDs keep trading (Japan 225 follows the US at night). The home open then catches up. Test: how the open behaves after a large overnight move. Does the gap continue or fill?
3. **Relative moves between related indices.** Index pairs that normally move together (the Nasdaq and the S&P, Germany and Euro Stoxx) or move against each other. Look at how far apart they drift, and trade the spread or pick the stronger one.
4. **Carry a proven ORB across regions.** Start from the published US index-open ORB and test the same rule at the Europe, Tokyo and other opens. Pick candidates with the session map, not at random.
5. **Read futures, trade CFDs.** Use CME or other exchange order flow as the signal and place the trade on the matching CFD. First, measure the price gap between the future and the CFD.
6. **Strongest per cluster.** At each open, rank the related markets by move since the open divided by their normal move. Trade the top one.
7. **Weekly instrument report.** Rerun the measurement every week (or day) so he and the copilot can update the instrument list. Deterministic now; agents can take it over later (MIS finder content).
8. **Stocks in play.** Single large US stocks at the open with an ORB. Published work on opening-range trades with a "stocks in play" filter. A later breadth layer.
9. **FX ORB.** He thinks an ORB may fit FX cleanly; later, once there is capital.
10. **Broker choice.** He is tempted by IBKR (real futures, many exchanges, concern about brokers trading against clients). QMX has only cTrader today; IBKR would need a new venue adapter. Decide later, with costs measured per broker.
