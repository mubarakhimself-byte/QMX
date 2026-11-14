"""Rewrite tools/ci/durations.json, the seconds each test file takes, from a deep run's shards.

    python tools/ci/durations.py <run id>

Runs on a laptop with `gh` signed in. It downloads every whole-suite shard's artifact
(`ci-out-suite-<system>-<n>`), reads the shard's plan (which files it ran, keyed `<cwd>::<path>` as
the splitter keys them) and its JUnit reports, and adds up each file's test times. A file's weight
is the larger of its Linux and Windows times, plus `ci_units.SECONDS_PER_FILE` for collection and
start-up. The splitter (`ci_units.shard`) balances shards by these weights; a file the run did not
time keeps the splitter's own estimate from its count of tests.
"""

from __future__ import annotations

import json
import sys
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import cast

import ci_units
import pull_reds
import qci

TARGET = Path(__file__).resolve().parent / "durations.json"
SUITE_ARTIFACT = "ci-out-suite-"


def full_path(key: str) -> str:
    """`<cwd>::<path>` as a repo path."""
    cwd, _, path = key.partition("::")
    return path if cwd == ci_units.ROOT_WS else f"{cwd}/{path}"


def owner(path: str, units: Iterable[str]) -> str | None:
    """The deepest unit root holding `path`."""
    owners = [u for u in units if path.startswith(u.rstrip("/") + "/")]
    return max(owners, key=len, default=None)


def matching_file(classname: str, files: Iterable[str]) -> str | None:
    """The file key a JUnit classname (`dotted.module[.Class]`) came from. JUnit names the module
    from pytest's rootdir, so any tail of the file's dotted path may start the classname; the
    longest tail that matches wins."""
    best: tuple[int, str] | None = None
    for key in files:
        parts = full_path(key).removesuffix(".py").split("/")
        for i in range(len(parts)):
            dotted = ".".join(parts[i:])
            if classname == dotted or classname.startswith(dotted + "."):
                if best is None or len(parts) - i > best[0]:
                    best = (len(parts) - i, key)
                break
    return None if best is None else best[1]


def shard_seconds(folder: Path) -> dict[str, float]:
    """Each file's summed test seconds in one shard's artifact folder."""
    found: dict[str, float] = {}
    for plan_path in sorted(folder.glob("plan-*.json")):
        plan = cast("dict[str, object]", json.loads(plan_path.read_text("utf-8")))
        system, shard = str(plan["system"]), int(cast("int", plan["shard"]))
        units = [str(u) for u in cast("list[object]", plan.get("units") or [])]
        files = [str(f) for f in cast("list[object]", plan.get("files") or [])]
        by_unit: dict[str, list[str]] = {}
        for key in files:
            unit = owner(full_path(key), units)
            if unit is not None:
                by_unit.setdefault(unit, []).append(key)
        stems = {u.replace("/", "_"): u for u in units}
        prefix = f"{system}-{shard}-"
        for report in sorted((folder / "junit").glob(f"{prefix}*.xml")):
            stem = report.stem.removeprefix(prefix).removesuffix("-serial")
            unit = stems.get(stem)
            if unit is None:
                continue
            for case in qci.junit_cases(report):
                classname = case.get("classname") or ""
                key = matching_file(classname, by_unit.get(unit, [])) if classname else None
                if key is not None:
                    found[key] = found.get(key, 0.0) + float(case.get("time") or 0)
    return found


def durations(shards: Iterable[Mapping[str, float]]) -> dict[str, float]:
    """Per file, the slowest shard's time (the larger of the two systems), plus start-up."""
    slowest: dict[str, float] = {}
    for found in shards:
        for key, seconds in found.items():
            slowest[key] = max(slowest.get(key, 0.0), seconds)
    return {k: round(v + ci_units.SECONDS_PER_FILE, 1) for k, v in sorted(slowest.items())}


def main(argv: list[str]) -> int:
    run_id = argv[1]
    listing = json.loads(
        pull_reds.gh(
            "api", f"repos/{pull_reds.GITHUB_REPO}/actions/runs/{run_id}/artifacts?per_page=100"
        )
    )
    names = sorted(
        str(a["name"])
        for a in cast("list[dict[str, object]]", listing["artifacts"])
        if str(a["name"]).startswith(SUITE_ARTIFACT)
    )
    found: list[dict[str, float]] = []
    with tempfile.TemporaryDirectory(prefix="qmx-durations-") as tmp:
        for name in names:
            where = Path(tmp) / name
            repo = pull_reds.GITHUB_REPO
            pull_reds.gh("run", "download", run_id, "-R", repo, "-n", name, "-D", str(where))
            found.append(shard_seconds(where))
    result = durations(found)
    TARGET.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    total = sum(result.values())
    print(f"{len(result)} files, {total:.0f} s in all, from {len(names)} shards of run {run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
