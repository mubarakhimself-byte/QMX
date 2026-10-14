"""`python -m qma.serve`: the QMA process entry point.

Not `python -m qma.harness`. That form imports `qma.harness.__init__` (and through it the
SDK) before any code of ours runs, so the scrub could not come first. The QMB host's spawn
target is `qma.serve`.

Order is the invariant:
1. `qma.boot.scrub_process_env(os.environ)`, stdlib only;
2. only then import `qma.harness.routes` and call `serve(scrubbed=...)`.
"""

from __future__ import annotations

import os

from qma.boot import scrub_process_env


def main() -> None:
    """Scrub, then import the harness and serve:

        removed = scrub_process_env(os.environ)
        from qma.harness.routes import serve      # deliberately after the scrub
        serve(scrubbed=removed)
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
