"""Deflated Sharpe over every trial in the family (Bailey and Lopez de Prado, 2014), the
`family-ledger` block's last step.

Its input is one value, or a list of values, of which one carries `family_trials` (the per-period
Sharpe ratio of every trial the family ever ran, passed or not, dead parents included) and
`candidate` (the chosen trial's per-period `sharpe`, its number of `observations`, and the `skew`
and `kurtosis` of its returns). The expected best Sharpe of that many trials by luck alone is the
bar; the candidate's probability of beating it, net of skew and fat tails, is the deflated Sharpe.
It passes at 0.95. Prints the family's trial count, the bar and the probability.
"""

import json
import math
import sys
from statistics import NormalDist, pvariance

EULER = 0.5772156649
PASS_AT = 0.95

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
found = next(v for v in given if isinstance(v, dict) and "family_trials" in v)
trials, candidate = found["family_trials"], found["candidate"]
normal = NormalDist()
n = len(trials)
if n < 2:
    bar = 0.0
else:
    spread = math.sqrt(pvariance(trials))
    bar = spread * (
        (1 - EULER) * normal.inv_cdf(1 - 1 / n) + EULER * normal.inv_cdf(1 - 1 / (n * math.e))
    )
sharpe, t = candidate["sharpe"], candidate["observations"]
tails = 1 - candidate["skew"] * sharpe + (candidate["kurtosis"] - 1) / 4 * sharpe**2
probability = normal.cdf((sharpe - bar) * math.sqrt(t - 1) / math.sqrt(tails)) if t > 1 else 0.0
print(
    json.dumps(
        {
            "deflated_sharpe": {
                "trials": n,
                "expected_best_by_luck": round(bar, 4),
                "candidate_sharpe": sharpe,
                "probability": round(probability, 4),
                "passes": probability >= PASS_AT,
            }
        }
    )
)
