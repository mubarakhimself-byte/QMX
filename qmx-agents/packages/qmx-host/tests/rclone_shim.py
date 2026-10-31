"""A stand-in for rclone that records each call's command line, one JSON list per line, to
`QMX_SHIM_LOG`, then runs the real binary `QMX_SHIM_REAL` with the same arguments, stdin and
stdout, and exits with its code."""

import json
import os
import subprocess
import sys

with open(os.environ["QMX_SHIM_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(sys.argv[1:]) + "\n")
sys.exit(subprocess.run([os.environ["QMX_SHIM_REAL"], *sys.argv[1:]], check=False).returncode)
