# N1: the growth equation, derived and checked

A model, not a rule. Every value here is an example.

## Derivation

One trade risks a fraction f of the account. A win pays w times what was risked, a loss costs 1 times what was risked (stop hit). The win rate is p.

- After a win the account is multiplied by (1 + f·w). After a loss by (1 − f).
- After N trades with W wins and L losses: Account = 500 × (1 + f·w)^W × (1 − f)^L.
- On the typical path W = p·N and L = (1 − p)·N. Take logs:
  ln(Account / 500) = N × [ p·ln(1 + f·w) + (1 − p)·ln(1 − f) ] = N × g
- 10x means ln(10) = 2.303. So **N = 2.303 / g**.

Net edge per trade (in R, after costs) is μ = p·w − (1 − p). Kelly's risk is f* = μ / w. Half Kelly is f*/2.

## Results (`growth_check.py`, 4,000 simulated paths each)

| Unit | Risk | Formula trades | Simulated median trades | P(a 30% drop from a peak on the way) | P(a 50% drop from a peak) |
|---|---|---|---|---|---|
| 60% win, 1:1, edge 0.2 | 20% (full) | 114 | 84 | 97% | 82% |
| 60% win, 1:1, edge 0.2 | 10% (half) | 153 | 136 | 90% | 51% |
| 55% win, 1:1, edge 0.1 | 10% (full) | 460 | 340 | 99% | 86% |
| 55% win, 1:1, edge 0.1 | 5% (half) | 614 | 538 | 95% | 56% |
| 70% win, win 0.6R, edge 0.12 | 20% (full) | 186 | 137 | 97% | 80% |
| 70% win, win 0.6R, edge 0.12 | 10% (half) | 251 | 225 | 94% | 53% |

## Correction on the record

My first table quoted "half Kelly: 12% chance of halving". That figure is the chance of falling to half of the **starting** balance. The drop that matters is from the **running peak**, and the simulation puts it near 50% at half Kelly on the way to 10x. Assumptions: independent trades, fixed win and loss sizes, no gaps, no brakes.
