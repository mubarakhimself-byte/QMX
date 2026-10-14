"""`python -m qma.serve`: the QMA process entry point.

Order is the invariant: `qma.boot.scrub_process_env(os.environ)` first, then import
`qma.harness.routes` and call `serve(scrubbed=...)`. What must hold is "scrubbed before the
first `connect()`", because the SDK reads `os.environ` there, not at import. Importing late
costs nothing and keeps the rule obvious. The QMB host's spawn target is `qma.serve`.
"""

from __future__ import annotations

import os

from qma.boot import scrub_process_env


def main() -> None:
    """Scrub, then import the harness and serve:

        removed = scrub_process_env(os.environ)
        from qma.harness.routes import serve
        serve(scrubbed=removed)
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
