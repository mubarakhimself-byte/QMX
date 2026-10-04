"""Validate complete mutmut 3.3.0 results, never a progress-spinner tally."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_RESULT = re.compile(r"(?P<name>[\w.]+__mutmut_\d+): (?P<status>.+)")


def main(argv: list[str] | None = None) -> int:
    """Gate the CLI's full listing and both command exit statuses."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--run-status", type=Path, required=True)
    parser.add_argument("--results-status", type=Path, required=True)
    parser.add_argument("--module", action="append", required=True)
    parser.add_argument("--min-kill-rate", type=int, choices=range(101), default=0)
    args = parser.parse_args(argv)
    try:
        if any(
            path.read_text(encoding="utf-8").strip() != "0"
            for path in (args.run_status, args.results_status)
        ):
            print("::error::mutation commands did not both complete successfully")
            return 2
        lines = args.results.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        print(f"::error::mutation evidence cannot be read: {error}")
        return 2

    names: set[str] = set()
    modules: set[str] = set()
    required: set[str] = set(args.module)
    killed = survived = 0
    for line in lines:
        if not line.strip():
            continue
        result = _RESULT.fullmatch(line.strip())
        if result is None or result["name"] in names:
            print("::error::mutation results contain an invalid or duplicate row")
            return 2
        name, status = result["name"], result["status"]
        module = name.rsplit(".", 1)[0]
        if module not in required or status not in {"killed", "survived"}:
            print(f"::error::mutation result is incomplete or outside the declared scope: {line}")
            return 2
        names.add(name)
        modules.add(module)
        killed += status == "killed"
        survived += status == "survived"

    if not names or modules != required:
        print("::error::mutation results do not cover every declared module")
        return 2
    total = killed + survived
    print(f"mutation gate: {killed} killed / {survived} survived; floor {args.min_kill_rate}%")
    if killed * 100 < args.min_kill_rate * total:
        print("::error::mutation kill-rate is below the preserved floor")
        return 1
    print("mutation gate: complete classified run; survivors still require evidence triage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
