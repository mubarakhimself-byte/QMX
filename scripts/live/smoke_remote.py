"""Operator-only remote smoke; requires configured targets and scoped credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qmx_control.service import ControlService

from qmx_remote.models import RunBundle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--definition-path")
    parser.add_argument("--target", default="vps")
    parser.add_argument("--run-id")
    parser.add_argument(
        "--action", choices=["start", "status", "logs", "fetch", "resume", "stop"], default="start"
    )
    args = parser.parse_args()
    service = ControlService(args.home)
    try:
        if args.action == "start":
            if args.bundle is None:
                parser.error("--bundle is required for start")
            bundle = RunBundle.model_validate_json(args.bundle.read_bytes())
            result = service.runs_start_remote(bundle, args.target, args.definition_path)
        else:
            if args.run_id is None:
                parser.error("--run-id is required")
            if args.action == "resume":
                result = service.runs_resume(args.run_id, args.target)
            else:
                result = getattr(service, "runs_" + args.action)(args.run_id)
        print(json.dumps(result, indent=2))
    finally:
        service.close()


if __name__ == "__main__":
    main()
