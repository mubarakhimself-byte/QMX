"""Backlog rows from CI: every finding CI knows about and lets through, one row each.

    python tools/ci/backlog.py --run <deep run id> [--walk <walk run id>] --out rows.tsv
    python tools/ci/backlog.py --summary summary.json [--summary walk.json] --out rows.tsv

Rows come from three places:

- every line of the baselines in this checkout's `ci/baselines/` (`vulture.txt`, `skylos.txt`,
  `mutmut.txt`, `pyright.txt`, `known-reds.txt`, `flaky.txt`);
- the run's `summary.json` (its artifact `summary`): known reds, flaky tests, and every quality
  finding that did not block (a note);
- the walk run's `summary.json`: its surviving mutants, which the walk records as notes.

A red or a finding that blocks is not a backlog row: it is the change's to fix. The columns are
those of `BACKLOG.tsv` (factory design 11.5) without `id`, `status` and `hops`, plus `key` first:
the tool and the ratchet key, stable across runs, so `ship backlog sync` can match a row to the
same finding next time. A key a baseline holds twice gets `#2` on its second row. `door` is
`mechanical` only when the rule is certain (an unused import, a flaky test) and the row touches no
fixed line, else `triage`. `touches` names the fixed-line module the row is in (one listed in
`ci/baselines/mutmut-modules.txt`), or `none`.

`--run` and `--walk` download the `summary` artifact with `gh` (signed in), from the repository
`QMX_GITHUB_REPO` names (default: the QMX home on GitHub).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import os
import shutil
import subprocess
import tempfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import cast

import ci_mutate
import ratchet

REPO = Path(__file__).resolve().parents[2]
BASELINES = REPO / "ci" / "baselines"
GITHUB_REPO = os.environ.get("QMX_GITHUB_REPO", "mubarakhimself-byte/QMX")
GH_TIMEOUT_S = 600
COLUMNS = ("key", "source", "what", "where", "first_seen", "program", "touches", "door")
# Baseline file -> (key prefix, backlog source).
BASELINE_SOURCES: dict[str, tuple[str, str]] = {
    "vulture.txt": ("vulture", "ci-vulture"),
    "skylos.txt": ("skylos", "ci-skylos"),
    "mutmut.txt": ("mutmut", "ci-mutmut"),
    "pyright.txt": ("pyright", "ci-types"),
    "known-reds.txt": ("known-red", "known-red"),
    "flaky.txt": ("flaky", "flaky"),
}
QUALITY_SOURCES = {"vulture": "ci-vulture", "skylos": "ci-skylos", "mutmut": "ci-mutmut"}
QUALITY_SOURCES["pyright"] = "ci-types"
FIXED_MODULES = "mutmut-modules.txt"


@dataclasses.dataclass(frozen=True)
class Row:
    key: str
    source: str
    what: str
    where: str
    first_seen: str
    program: str
    touches: str
    door: str

    def line(self) -> str:
        cells = (getattr(self, c) for c in COLUMNS)
        return "\t".join(" ".join(str(c).split()) for c in cells)


def module_of(path: str) -> str | None:
    """The dotted module a source file under `<package>/src/` holds."""
    found = ci_mutate.source_package(path)
    return ci_mutate.module_name(found[1]) if found else None


def touches(tool: str, key: str, fixed: Sequence[str]) -> str:
    """The fixed-line module a finding sits in, or `none`. A mutant names its function
    (`package|mutmut|module.function status`); any other quality finding names its file."""
    if tool == "mutmut":
        name = key.split("|", 2)[2].split(" ", 1)[0]
    elif tool in ("vulture", "skylos", "pyright"):
        name = module_of(key.split("|", 1)[0]) or ""
    else:
        return "none"
    for module in fixed:
        if name == module or name.startswith(module + "."):
            return module
    return "none"


def door(tool: str, key: str, touched: str) -> str:
    """`mechanical` where the rule is certain and no fixed line is touched, else `triage`."""
    if touched != "none":
        return "triage"
    parts = key.split("|")
    if tool == "flaky":
        return "mechanical"
    if tool == "vulture" and parts[2].startswith("unused import "):
        return "mechanical"
    if tool == "skylos" and parts[1].startswith("unused_imports:"):
        return "mechanical"
    return "triage"


def describe(tool: str, key: str) -> tuple[str, str]:
    """(what, where) in plain words for one finding."""
    parts = key.split("|")
    match tool:
        case "vulture":
            return f"Vulture: {parts[2]}", parts[0]
        case "skylos":
            return f"Skylos {parts[1]}: {parts[2]}", parts[0]
        case "pyright":
            return f"pyright {parts[1]}: {parts[2]}", parts[0]
        case "mutmut":
            function, _, status = parts[2].partition(" ")
            return f"mutant {status or 'survived'} in {function}", parts[0]
        case "known-red":
            return f"red test on {parts[0]}: {parts[2]}", parts[1]
        case _:
            return f"flaky test on {parts[0]}: {parts[2]}", parts[1]


def make_row(tool: str, key: str, source: str, seen: str, fixed: Sequence[str]) -> Row:
    what, where = describe(tool, key)
    touched = touches(tool, key, fixed)
    return Row(f"{tool}|{key}", source, what, where, seen, "", touched, door(tool, key, touched))


def baseline_rows(baselines: Path, seen: str) -> list[Row]:
    fixed = ratchet.read_baseline(baselines / FIXED_MODULES)
    rows: list[Row] = []
    for name, (tool, source) in BASELINE_SOURCES.items():
        for key in ratchet.read_baseline(baselines / name):
            rows.append(make_row(tool, key, source, seen, fixed))
    return rows


def summary_rows(summary: Mapping[str, object], seen: str, fixed: Sequence[str]) -> list[Row]:
    """Known reds, flaky tests and non-blocking quality notes from one run's summary.json."""
    rows: list[Row] = []
    for red in cast("list[dict[str, object]]", summary.get("reds") or []):
        kind = red.get("kind")
        if kind not in ("known", "flaky"):
            continue
        tool = "known-red" if kind == "known" else "flaky"
        key = f"{red['system']}|{red['id']}"
        rows.append(make_row(tool, key, tool, seen, fixed))
    for item in cast("list[dict[str, object]]", summary.get("quality") or []):
        tool = str(item.get("tool"))
        if item.get("kind") != "new" or item.get("blocks", True) or tool not in QUALITY_SOURCES:
            continue
        rows.append(make_row(tool, str(item["key"]), QUALITY_SOURCES[tool], seen, fixed))
    return rows


def merge(groups: Iterable[Sequence[Row]]) -> list[Row]:
    """One row per occurrence. Within one source (a baseline file, one run's summary) a key seen
    twice is two findings, as the ratchet counts them, and the second copy's key gets `#2`. The
    same finding from two sources (a known red in known-reds.txt and in the run's summary) is
    one row: a key gets as many rows as the one source that holds it most often."""
    ordered: list[Row] = []
    most: Counter[str] = Counter()
    for group in groups:
        counts = Counter(r.key for r in group)
        for key, n in counts.items():
            most[key] = max(most[key], n)
        ordered += group
    out: list[Row] = []
    emitted: Counter[str] = Counter()
    for row in ordered:
        if emitted[row.key] >= most[row.key]:
            continue
        emitted[row.key] += 1
        n = emitted[row.key]
        out.append(row if n == 1 else dataclasses.replace(row, key=f"{row.key}#{n}"))
    return out


def write_rows(path: Path, rows: Sequence[Row]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\t".join(COLUMNS) + "\n" + "".join(r.line() + "\n" for r in rows)
    path.write_text(body, "utf-8", newline="\n")


def gh(*args: str) -> str:
    exe = shutil.which("gh") or "gh"
    done = subprocess.run(
        [exe, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=GH_TIMEOUT_S,
        check=True,
    )
    return done.stdout


def fetch_summary(run_id: str, into: Path) -> tuple[dict[str, object], str]:
    """A run's summary.json and the date it started on (UTC), through `gh`."""
    gh("run", "download", run_id, "-R", GITHUB_REPO, "-n", "summary", "-D", str(into))
    summary = cast("dict[str, object]", json.loads((into / "summary.json").read_text("utf-8")))
    run = json.loads(gh("api", f"repos/{GITHUB_REPO}/actions/runs/{run_id}"))
    return summary, str(run.get("run_started_at") or run.get("created_at") or "")[:10]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Backlog rows from CI.")
    parser.add_argument("--run", help="a deep run's id: its summary artifact")
    parser.add_argument("--walk", help="a walk run's id: its summary artifact")
    parser.add_argument("--summary", type=Path, action="append", default=[], help="summary.json")
    parser.add_argument("--baselines", type=Path, default=BASELINES)
    parser.add_argument("--date", help="first_seen for every row (default: the run's date)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summaries: list[dict[str, object]] = [
        cast("dict[str, object]", json.loads(p.read_text("utf-8"))) for p in args.summary
    ]
    dates: list[str] = []
    with tempfile.TemporaryDirectory(prefix="qmx-backlog-") as tmp:
        for n, run_id in enumerate(r for r in (args.run, args.walk) if r):
            summary, started = fetch_summary(run_id, Path(tmp) / str(n))
            summaries.append(summary)
            dates.append(started)
    today = datetime.date.today().isoformat()  # ambient-scan: allow - a CLI's default date
    seen = args.date or (dates[0] if dates and dates[0] else today)
    fixed = ratchet.read_baseline(args.baselines / FIXED_MODULES)
    groups = [baseline_rows(args.baselines, seen)]
    groups += [summary_rows(summary, seen, fixed) for summary in summaries]
    found = merge(groups)
    write_rows(args.out, found)
    by_door = Counter(r.door for r in found)
    print(
        f"{len(found)} rows to {args.out} ({by_door['mechanical']} mechanical, "
        f"{by_door['triage']} triage)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
