"""The one ask both QMB runs share: the unit's Library pin and the in-sample window. Zero tokens.

Its input is `Ready to test?`'s answer. The `app_op` nodes merge nothing over it, so QMB's lander
reads exactly these fields; the holdout is never in the window.
"""

import json
import sys

ready = json.load(sys.stdin)["in"]
print(json.dumps({"unit": ready["unit"]["pin"], "window": ready["window"]}))
