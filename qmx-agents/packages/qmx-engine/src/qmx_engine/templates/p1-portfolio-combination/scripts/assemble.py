"""The book-picture explainer: the writer's headline and findings beside the study's numbers, which
come from the simulation and never from the model. Its inputs, the study and the writer's text,
are told apart by shape."""

import json
import sys

given = json.load(sys.stdin)["in"]
study = next(v for v in given if "candidates" in v)
text = next(v for v in given if "headline" in v)
print(json.dumps({"headline": text["headline"], "findings": text["findings"]} | study))
