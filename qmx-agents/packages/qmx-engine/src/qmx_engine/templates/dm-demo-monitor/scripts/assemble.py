"""One tile per demo unit: its stats, band verdict, faults, cost level and any bench proposal, with
the candidate causes for a unit out of its band. Its inputs, the checked units and the causes when
some unit was out of band, are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
checked = next(v for v in given if "out_of_band" in v)
causes = next((v["causes"] for v in given if "causes" in v), [])
print(json.dumps({"at": checked["at"], "units": checked["units"], "causes": causes}))
