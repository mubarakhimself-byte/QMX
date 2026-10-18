"""The incident's impact (card R8 step 2): the loss in dollars and in R (over the largest active r),
and the cushion above the kill line before and after, also as a share of the cushion before."""

import json
import sys

incident = json.load(sys.stdin)["in"]
before, after = incident["account_before"], incident["account_after"]
loss = before["equity"] - after["equity"]
cushion_before = before["equity"] - before["kill_line"]
cushion_after = after["equity"] - after["kill_line"]
print(
    json.dumps(
        {
            "incident": incident["incident"]["id"],
            "loss_usd": round(loss, 2),
            "loss_r": round(loss / before["largest_r"], 2) if before["largest_r"] else None,
            "cushion_before_usd": round(cushion_before, 2),
            "cushion_after_usd": round(cushion_after, 2),
            "cushion_used_pct": round(100 * loss / cushion_before, 1) if cushion_before else None,
        }
    )
)
