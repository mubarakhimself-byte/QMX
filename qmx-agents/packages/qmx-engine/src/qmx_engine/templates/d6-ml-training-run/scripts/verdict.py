"""The verdict a model never sets (card D6 steps 6 to 9 and its gates).

"Likely overfitting" when the chosen configuration's train score beats its validation score by more
than 0.10. The sealed test "did not hold" when its score falls outside the validation band, and the
model is kept as a dead end. The model is published only when it held and the ablation shows a gain
in expectancy after costs. Every configuration tried counts as a trial.

A run with no ablation has no gain to read: the ablation needs the QMB door, so this step says the
model waits for it rather than reading a gain of nothing.
"""

import json
import sys

OVERFIT_GAP = 0.10

ran = json.load(sys.stdin)["in"]
chosen = next(c for c in ran["configs"] if c["id"] == ran["chosen"])
gap = round(chosen["train_score"] - chosen["validation_score"], 4)
low, high = ran["validation_band"]
sealed = ran["sealed_score"]
held = sealed is not None and low <= sealed <= high
ablation = ran.get("ablation")
gain = None if ablation is None else round(ablation["with_r"] - ablation["without_r"], 4)
if not held:
    verdict = "did not hold"
elif gain is None:
    verdict = "waits for the ablation"
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
            "sealed_score": sealed,
            "validation_band": ran["validation_band"],
            "held": held,
            "ablation": None if ablation is None else ablation | {"gain_r": gain},
            "trials": ran["trials"],
            "model_ref": ran["model_ref"],
        }
    )
)
