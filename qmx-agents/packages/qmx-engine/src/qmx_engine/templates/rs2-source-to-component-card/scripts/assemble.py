"""The finished component card: the card with its holes, what was changed to keep them, and the
calibration chip of each headline item."""

import json
import sys

given = json.load(sys.stdin)["in"]
kept = next(v for v in given if isinstance(v, dict) and "card" in v)
calibrated = next(v for v in given if isinstance(v, dict) and "calibration" in v)
card = kept["card"] | {
    "holes": kept["holes"],
    "changes": kept["changes"],
    "calibration": calibrated["calibration"],
}
print(json.dumps(card))
