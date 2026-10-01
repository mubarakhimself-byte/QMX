"""Fail closed unless every named mandatory job completed successfully."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping, Sequence
from typing import cast


def evaluate(raw: str, required: Sequence[str]) -> list[str]:
    """Validate GitHub's needs JSON without accepting skipped or absent jobs."""
    if not required or len(set(required)) != len(required):
        return ["mandatory job names must be nonempty and unique"]
    try:
        parsed: object = json.loads(raw)
    except (ValueError, TypeError):
        return ["needs is not valid JSON"]
    if not isinstance(parsed, dict):
        return ["needs must be an object"]
    needs = cast("Mapping[str, object]", parsed)
    errors: list[str] = []
    if set(needs) != set(required):
        errors.append("needs must contain exactly the declared mandatory jobs")
    for job in required:
        entry = needs.get(job)
        if (
            not isinstance(entry, dict)
            or cast("Mapping[str, object]", entry).get("result") != "success"
        ):
            errors.append(f"{job}: mandatory job did not succeed")
    return errors


def main(required: Sequence[str] | None = None) -> int:
    """Read needs from the environment; never interpolate event data into shell."""
    errors = evaluate(
        os.environ.get("NEEDS_JSON", ""), sys.argv[1:] if required is None else required
    )
    for error in errors:
        print(f"::error::{error}")
    if not errors:
        print("All mandatory jobs completed successfully")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
