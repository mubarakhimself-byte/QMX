"""The drift card: the heatmap rows, the currency bars, the effective-bets tile and, when a rule
tripped, what drives it and a proposed tightening for his signature. Its inputs, the exposure and
the analyst's read when a rule tripped, are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
exposure = next(v for v in given if "trips" in v)
read = next((v for v in given if "drivers" in v), {"drivers": [], "proposal": None})
print(json.dumps(exposure | {"drivers": read["drivers"], "proposal": read["proposal"]}))
