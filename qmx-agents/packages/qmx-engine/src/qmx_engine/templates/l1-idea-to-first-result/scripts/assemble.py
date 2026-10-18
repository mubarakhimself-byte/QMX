"""The two board artifacts (card L1 output): the spec card with its questions and the recommended
answers written in, and the first-result scorecard, one column per reading, with the iteration
counter. A card that failed its check ends at the card, naming the missing fields. Its inputs are
told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
given = given if isinstance(given, list) else [given]
facts = next(v for v in given if "toolbox" in v)
checked = next(v for v in given if "readings" in v and "missing" in v)
gates = next((v for v in given if "results" in v), {"results": []})
prose = next((v for v in given if "summary" in v), {"summary": ""})
print(
    json.dumps(
        {
            "card": checked["card"],
            "questions": checked["questions"],
            "dead_end_warning": checked["dead_end_warning"],
            "missing": checked["missing"],
            "facts": {
                "dead_ends": facts["dead_ends"],
                "toolbox": facts["toolbox"],
                "data": facts["data"],
            },
            "results": gates["results"],
            "iteration": "1 of 2" if checked["ok"] else "card only",
            "summary": prose["summary"],
        }
    )
)
