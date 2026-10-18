"""The verdict a model never sets (card D6 steps 6 to 9 and its gates).

"Likely overfitting" when the chosen configuration's train score beats its validation score by more
than 0.10. The sealed test "did not hold" when its score falls outside the validation band, and the
model is kept as a dead end. The model is published only when it held and the ablation shows a gain
in expectancy after costs. Every configuration tried counts as a trial.
"""

import json
import sys

OVERFIT_GAP = 0.10

ran = json.load(sys.stdin)["in"]
chosen = next(c for c in ran["configs"] if c["id"] == ran["chosen"])
gap = round(chosen["train_score"] - chosen["validation_score"], 4)
low, high = ran["validation_band"]
held = low <= ran["sealed_score"] <= high
gain = round(ran["ablation"]["with_r"] - ran["ablation"]["without_r"], 4)
if not held:
    verdict = "did not hold"
elif gain <= 0:
    verdict = "no gain after costs"
else:
    verdict = "publish"
print(
    json.dumps(
        {
            "verdict": verdict,
            "likely_overfitting": gap > OVERFIT_GAP,
            "train_validation_gap": gap,
            "sealed_score": ran["sealed_score"],
            "validation_band": ran["validation_band"],
            "held": held,
            "ablation": ran["ablation"] | {"gain_r": gain},
            "trials": ran["trials"],
            "model_ref": ran["model_ref"],
        }
    )
)
