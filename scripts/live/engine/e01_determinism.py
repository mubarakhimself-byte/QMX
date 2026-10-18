"""EP5 lane 2 (E1): one recorded event log folded in two processes gives byte-equal commands.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e01_determinism.py`
The log is E2's run (node 3 fails, then the run resumes), saved as JSON lines. Two child processes
with different `PYTHONHASHSEED`s each fold every prefix of it and print the encoded command list
per prefix. Writes `evidence/ep5/<ENGINE_LOG_PREFIX>ep5-e01.log`.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Final

from common import Log, throwaway_home
from e02_replay import chain, e02_run
from ep2_lanes import clean_env, git
from qmx_engine.core.commands import encode
from qmx_engine.core.fold import fold
from qmx_engine.core.ready import next_commands
from qmx_engine.core.simulate import Entry

SCRIPT: Final = Path(__file__).resolve()
SEEDS: Final = ("1", "4242")


def child(path: Path) -> None:
    events = [Entry(**json.loads(line)) for line in path.read_text(encoding="utf-8").splitlines()]
    definition = chain()
    out = sys.stdout.buffer
    for k in range(len(events) + 1):
        out.write(encode(next_commands(fold(definition, events[:k]))) + b"\n")
    out.flush()


def main() -> int:
    if sys.argv[1:2] == ["_child"]:
        child(Path(sys.argv[2]))
        return 0
    log = Log("ep5", "ep5-e01")
    log(f"lane e01 at head {git('rev-parse', 'HEAD')}")
    sim, _, _ = e02_run()
    path = throwaway_home("ep5", "e01") / "events.jsonl"
    path.write_text(
        "".join(
            json.dumps(
                {"seq": e.seq, "run_id": e.run_id, "at": e.at, "kind": e.kind, "data": e.data}
            )
            + "\n"
            for e in sim.events
        ),
        encoding="utf-8",
    )
    log(f"recorded {len(sim.events)} events to {path}")
    outputs: list[bytes] = []
    for seed in SEEDS:
        done = subprocess.run(
            [sys.executable, str(SCRIPT), "_child", str(path)],
            env=clean_env(PYTHONHASHSEED=seed),
            capture_output=True,
            check=False,
        )
        log(
            f"process with PYTHONHASHSEED={seed}: exit {done.returncode}, "
            f"{len(done.stdout)} bytes, sha256 {hashlib.sha256(done.stdout).hexdigest()[:16]}"
        )
        if done.stderr:
            log(f"  stderr: {done.stderr.decode(errors='replace')[-400:]}")
        outputs.append(done.stdout)
    lines = outputs[0].splitlines()
    kinds = sorted({c["command"] for line in lines for c in json.loads(line)})
    log(f"prefixes folded: {len(lines)}; command kinds seen: {' '.join(kinds)}")
    log.check(
        "both processes folded every prefix",
        all(len(o.splitlines()) == len(sim.events) + 1 for o in outputs),
        len(lines),
    )
    log.check(
        "the command lists are byte-equal", outputs[0] == outputs[1] and outputs[0] != b"", ""
    )
    log.check(
        "the log exercises start, memo, park and finish",
        {"StartNode", "UseMemo", "Park", "Finish"} <= set(kinds),
        kinds,
    )
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
