"""Run one command on the machine its node is placed on.

A placed CPU or GPU job is a one-node workflow (AD-57): this node's `runs_on` names the machine,
and the engine's remote worker ships the attempt there under the run sidecar. The script reads the
attempt's inputs on stdin, runs the argv, and answers with the exit code and the tails of the two
streams, so the run card carries the job's evidence and nothing has to be fetched from the box.
"""

import json
import subprocess
import sys

DEFAULT_TIMEOUT = 900
TAIL = 4_000


def main() -> int:
    inputs = json.load(sys.stdin)
    command = inputs.get("command")
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(part, str) for part in command)
    ):
        print("QMX_FAILURE inputs.command must be a non-empty argv list")
        return 0
    timeout = inputs.get("timeout_seconds", DEFAULT_TIMEOUT)
    try:
        done = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=float(timeout),
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"QMX_FAILURE the job ran past {timeout} s")
        return 0
    print(
        json.dumps(
            {
                "exit_code": done.returncode,
                "stdout": done.stdout[-TAIL:],
                "stderr": done.stderr[-TAIL:],
            }
        )
    )
    if done.returncode:
        print(f"QMX_FAILURE the job exited {done.returncode}: {done.stderr.strip()[-TAIL:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
