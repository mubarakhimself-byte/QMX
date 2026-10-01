"""Start the installed QMA host through its documented QMB lifecycle door.

Requires the product wheels installed in this interpreter. This launcher does
not imply browser journey acceptance or any provider connectivity.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Invoke the sole QMB operator CLI; preserve diagnostic output and status."""
    scripts = Path(sys.executable).parent
    qmb = scripts / ("qmb.exe" if os.name == "nt" else "qmb")
    if not qmb.is_file():
        print("QMX: install the bundled product wheels in this environment first", file=sys.stderr)
        return 2
    return subprocess.run([str(qmb), "host", "start"], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
