"""Keep the machine from sleeping while a flag file exists. Started by preflight, ended by teardown
removing the flag. Standalone on purpose: no package imports, so it survives any later change.

Windows: SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED) for as long as this process
lives. Linux: preflight starts it under `systemd-inhibit` when that exists. A closed lid can still
sleep a laptop whose lid action is "sleep"; preflight prints that as a manual step.
"""

import sys
import time
from pathlib import Path

ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001


def main(flag: Path, poll_s: float) -> int:
    windows = sys.platform == "win32"
    if windows:
        import ctypes

        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)
    try:
        while flag.exists():
            time.sleep(poll_s)
    finally:
        if windows:
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), float(sys.argv[2])))
