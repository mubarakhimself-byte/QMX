"""`python -m qma.serve`: the QMA process entry point.

Order is the invariant: `qma.boot.scrub_process_env(os.environ)` first, then import
`qma.harness.routes` and call `serve(scrubbed=...)`. What must hold is "scrubbed before the
first `connect()`", because the SDK reads `os.environ` there, not at import. Importing late
costs nothing and keeps the rule obvious. The QMB host's spawn target is `qma.serve`.
"""

from __future__ import annotations

import os

from qma.boot import read_keep_names, scrub_process_env


def main() -> None:
    """Parse `--home` with `argparse`, scrub, then import the harness and serve:

        extra = read_keep_names(home / "settings.toml")     # the UI keep list, stdlib only
        removed = scrub_process_env(os.environ, extra)
        from qma.harness.routes import serve
        serve(scrubbed=removed)
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
