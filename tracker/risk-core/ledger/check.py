"""Checker for the QMX risk-and-sizing variable ledger.

Run from anywhere:

    uv run --no-project --with pyyaml python check.py [extra files...] [--with-additions] [--strict] [--no-paths]

The ledger v0 (variables.yaml beside this script) is always loaded. Extra files
are added to it, so an additions file is checked against v0 and against each
other. --with-additions also loads every additions/*.yaml.

Errors (schema breaks, duplicate ids, couplings to ids that exist nowhere) make
the exit code 1. Warnings (a source path that cannot be found, a default with no
basis, an alias that matches another entry) are printed and do not fail unless
--strict is given. Info lines never fail.

The checker writes couplings.md beside this script: a Mermaid graph of every
coupling grouped by level, one smaller graph per level, and an edge table.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
TRACKER = HERE.parent  # tracker/risk-core, the root for relative source paths
BASE_FILE = HERE / "variables.yaml"
ADDITIONS = HERE / "additions"
SEEDS_FILE = TRACKER / "seeds" / "SEEDS.md"
OUT_FILE = HERE / "couplings.md"

LEVELS = ["trade", "position", "unit", "book", "methodology", "portfolio", "account", "node", "system"]
KINDS = [
    "size_input", "size_output", "limit", "brake_threshold", "brake_reset",
    "accelerator", "cost", "measure", "schedule", "evidence", "other",
]
MEASURES = ["R", "USD", "percent", "count", "bars", "minutes", "ratio", "pips_points_ticks"]
CLASSES = ["fx", "index", "metal", "energy", "crypto", "futures", "stock", "all"]
STYLES = ["scalper", "intraday", "swing", "all"]
DIRECTIONS = ["up", "down", "either"]
CHANGED_BY = ["operator", "agent_proposal", "automatic", "none"]
STATUSES = ["running", "built_not_running", "docs_only", "dropped", "proposal", "idea"]
BASES = ["formula", "reasoned", "stated", "open"]
GENERATIONS = [
    "april", "july", "sept_docs", "october", "unit_build",
    "operator_words", "grounding", "research", "expansion",
]

REQUIRED = [
    "id", "name", "level", "kind", "measure", "applies_to", "default", "derivation",
    "inputs", "affects", "configurable", "changed_by", "status", "sources",
]
OPTIONAL = ["basis", "seen_values", "aliases", "seed_ids", "notes", "open_questions"]
ALLOWED = set(REQUIRED) | set(OPTIONAL)

ID_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
SEED_RE = re.compile(r"^[A-E][0-9]+$")
REF_RE = re.compile(r"^(?P<path>.+?)(?::(?P<start>\d+)(?:-(?P<end>\d+))?)?$")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def err(self, where: str, msg: str) -> None:
        self.errors.append(f"{where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"{where}: {msg}")


@dataclass
class Entry:
    data: dict
    file: Path
    index: int

    @property
    def id(self) -> str:
        value = self.data.get("id")
        return value if isinstance(value, str) else f"<entry {self.index}>"

    @property
    def where(self) -> str:
        return f"{self.file.name}#{self.index} {self.id}"


def load(path: Path, report: Report) -> list[Entry]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        report.err(str(path), f"cannot read: {exc}")
        return []
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        report.err(str(path), f"not valid YAML: {exc}")
        return []
    if data is None:
        return []
    if not isinstance(data, list):
        report.err(str(path), "top level must be a YAML list, one item per variable")
        return []
    entries = []
    for i, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            report.err(f"{path.name}#{i}", "each item must be a mapping")
            continue
        entries.append(Entry(item, path, i))
    return entries


def is_open(text: str) -> bool:
    return text.strip().lower().startswith("open")


def check_measure(value, where: str, report: Report) -> None:
    if not isinstance(value, str):
        report.err(where, "measure must be a string")
        return
    if value in MEASURES:
        return
    if value.startswith("other:") and value[len("other:"):].strip():
        return
    report.err(where, f"measure '{value}' must be one of {MEASURES} or 'other: <what>'")


def check_applies_to(value, where: str, report: Report) -> None:
    if not isinstance(value, dict):
        report.err(where, "applies_to must be a mapping with classes, styles, timeframes")
        return
    extra = set(value) - {"classes", "styles", "timeframes"}
    if extra:
        report.err(where, f"applies_to has unknown keys {sorted(extra)}")
    for key, allowed in (("classes", CLASSES), ("styles", STYLES)):
        items = value.get(key)
        if not isinstance(items, list) or not items:
            report.err(where, f"applies_to.{key} must be a non-empty list")
            continue
        bad = [x for x in items if x not in allowed]
        if bad:
            report.err(where, f"applies_to.{key} has {bad}; allowed {allowed}")
        if "all" in items and len(items) > 1:
            report.err(where, f"applies_to.{key}: 'all' must stand alone")
    tf = value.get("timeframes")
    if tf == "all":
        return
    if not isinstance(tf, list) or not tf or not all(isinstance(x, str) and x.strip() for x in tf):
        report.err(where, "applies_to.timeframes must be 'all' or a non-empty list of strings")


class PathCache:
    def __init__(self) -> None:
        self.lines: dict[Path, int | None] = {}

    def line_count(self, path: Path) -> int | None:
        if path not in self.lines:
            try:
                with path.open("rb") as handle:
                    self.lines[path] = sum(1 for _ in handle)
            except OSError:
                self.lines[path] = None
        return self.lines[path]


def resolve(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else (TRACKER / path)


def check_ref(ref, where: str, report: Report, paths: PathCache | None) -> None:
    if not isinstance(ref, str) or not ref.strip():
        report.err(where, "source ref must be a non-empty string")
        return
    if ref.startswith(("http://", "https://")):
        return
    match = REF_RE.match(ref.strip())
    if not match:
        report.err(where, f"source ref '{ref}' must be 'path' or 'path:line' or 'path:line-line'")
        return
    if paths is None:
        return
    path = resolve(match["path"])
    if path.is_dir():
        return
    count = paths.line_count(path)
    if count is None:
        report.warn(where, f"source path not found: {match['path']}")
        return
    for key in ("start", "end"):
        if match[key] and int(match[key]) > count:
            report.warn(where, f"line {match[key]} is past the end of {path.name} ({count} lines)")


def seed_ids_known() -> set[str] | None:
    if not SEEDS_FILE.exists():
        return None
    text = SEEDS_FILE.read_text(encoding="utf-8")
    return set(re.findall(r"^#{3,4} ([A-E][0-9]+)\.", text, flags=re.MULTILINE))


def check_entry(entry: Entry, report: Report, paths: PathCache | None, seeds: set[str] | None) -> None:
    d, w = entry.data, entry.where
    for key in REQUIRED:
        if key not in d:
            report.err(w, f"missing field '{key}'")
    for key in d:
        if key not in ALLOWED:
            report.err(w, f"unknown field '{key}'")

    if "id" in d and (not isinstance(d["id"], str) or not ID_RE.match(d["id"])):
        report.err(w, "id must be snake_case (lower case letters, digits, single underscores)")
    for key in ("name", "derivation"):
        if key in d and (not isinstance(d[key], str) or not d[key].strip()):
            report.err(w, f"{key} must be a non-empty string")
    if "level" in d and d["level"] not in LEVELS:
        report.err(w, f"level '{d['level']}' must be one of {LEVELS}")
    if "kind" in d and d["kind"] not in KINDS:
        report.err(w, f"kind '{d['kind']}' must be one of {KINDS}")
    if "measure" in d:
        check_measure(d["measure"], w, report)
    if "applies_to" in d:
        check_applies_to(d["applies_to"], w, report)
    if "configurable" in d and not isinstance(d["configurable"], bool):
        report.err(w, "configurable must be true or false")
    if "status" in d and d["status"] not in STATUSES:
        report.err(w, f"status '{d['status']}' must be one of {STATUSES}")

    changed = d.get("changed_by")
    if "changed_by" in d:
        if not isinstance(changed, list) or not changed:
            report.err(w, "changed_by must be a non-empty list")
        else:
            bad = [x for x in changed if x not in CHANGED_BY]
            if bad:
                report.err(w, f"changed_by has {bad}; allowed {CHANGED_BY}")
            if "none" in changed and len(changed) > 1:
                report.err(w, "changed_by: 'none' must stand alone")

    # The rule: a default needs a derivation.
    default = d.get("default")
    derivation = d.get("derivation") if isinstance(d.get("derivation"), str) else ""
    basis = d.get("basis")
    if basis is not None and basis not in BASES:
        report.err(w, f"basis '{basis}' must be one of {BASES}")
    if default is not None:
        if not derivation.strip() or is_open(derivation):
            report.err(w, "a default needs a derivation: derivation is empty or 'open'")
        if basis == "open":
            report.err(w, "basis is 'open' but a default is set")
        if basis is None:
            report.warn(w, "default set with no basis (formula, reasoned or stated)")
    if basis == "open" and derivation and not is_open(derivation):
        report.warn(w, "basis is 'open' but the derivation does not start with 'open'")

    for key in ("inputs", "aliases", "seed_ids", "open_questions"):
        if key in d and d[key] is not None:
            if not isinstance(d[key], list) or not all(isinstance(x, str) and x.strip() for x in d[key]):
                report.err(w, f"{key} must be a list of non-empty strings")
    if isinstance(d.get("inputs"), list) and d.get("id") in d["inputs"]:
        report.err(w, "an entry cannot be its own input")

    affects = d.get("affects")
    if "affects" in d:
        if not isinstance(affects, list):
            report.err(w, "affects must be a list")
        else:
            for j, edge in enumerate(affects, start=1):
                ew = f"{w} affects[{j}]"
                if not isinstance(edge, dict):
                    report.err(ew, "must be a mapping {id, direction, how}")
                    continue
                if set(edge) - {"id", "direction", "how"}:
                    report.err(ew, f"unknown keys {sorted(set(edge) - {'id', 'direction', 'how'})}")
                if not isinstance(edge.get("id"), str):
                    report.err(ew, "id missing")
                elif edge["id"] == d.get("id"):
                    report.err(ew, "an entry cannot affect itself")
                if edge.get("direction") not in DIRECTIONS:
                    report.err(ew, f"direction must be one of {DIRECTIONS}")
                if not isinstance(edge.get("how"), str) or not edge["how"].strip():
                    report.err(ew, "how must be one line of plain words")

    sources = d.get("sources")
    if "sources" in d:
        if not isinstance(sources, list) or not sources:
            report.err(w, "sources must be a non-empty list")
        else:
            for j, src in enumerate(sources, start=1):
                sw = f"{w} sources[{j}]"
                if not isinstance(src, dict) or set(src) - {"gen", "ref", "note"}:
                    report.err(sw, "must be a mapping {gen, ref, note?}")
                    continue
                if src.get("gen") not in GENERATIONS:
                    report.err(sw, f"gen must be one of {GENERATIONS}")
                check_ref(src.get("ref"), sw, report, paths)

    seen = d.get("seen_values")
    if seen is not None:
        if not isinstance(seen, list):
            report.err(w, "seen_values must be a list")
        else:
            for j, item in enumerate(seen, start=1):
                vw = f"{w} seen_values[{j}]"
                if not isinstance(item, dict) or "value" not in item or set(item) - {"value", "gen", "ref", "note"}:
                    report.err(vw, "must be a mapping {value, gen, ref?, note?}")
                    continue
                if item.get("gen") not in GENERATIONS:
                    report.err(vw, f"gen must be one of {GENERATIONS}")
                if "ref" in item:
                    check_ref(item["ref"], vw, report, paths)

    if isinstance(d.get("seed_ids"), list):
        for sid in d["seed_ids"]:
            if not SEED_RE.match(sid):
                report.err(w, f"seed id '{sid}' must look like A1, C27, D50")
            elif seeds is not None and sid not in seeds:
                report.warn(w, f"seed id '{sid}' is not a heading in SEEDS.md")


def edges_of(entries: list[Entry]) -> list[tuple[str, str, str, str]]:
    """Return (source, target, direction, how). Inputs become 'feeds' edges."""
    out: dict[tuple[str, str], tuple[str, str, str, str]] = {}
    for e in entries:
        for edge in e.data.get("affects") or []:
            if isinstance(edge, dict) and isinstance(edge.get("id"), str):
                out[(e.id, edge["id"])] = (e.id, edge["id"], str(edge.get("direction")), str(edge.get("how", "")))
    for e in entries:
        for src in e.data.get("inputs") or []:
            if isinstance(src, str) and (src, e.id) not in out:
                out[(src, e.id)] = (src, e.id, "feeds", f"{e.id} is computed from it")
    return sorted(out.values())


def mermaid(nodes: dict[str, Entry], edges, levels_to_show: list[str], title: str) -> str:
    lines = ["```mermaid", "flowchart LR"]
    by_level: dict[str, list[str]] = defaultdict(list)
    for nid in sorted(nodes):
        by_level[nodes[nid].data.get("level", "unknown")].append(nid)
    for level in levels_to_show + sorted(set(by_level) - set(levels_to_show)):
        ids = by_level.get(level)
        if not ids:
            continue
        lines.append(f"  subgraph L_{level}[\"{level}\"]")
        for nid in ids:
            lines.append(f"    {nid}[\"{nid}\"]")
        lines.append("  end")
    arrow = {"up": "-->|up|", "down": "-->|down|", "either": "-->|either|", "feeds": "-.->|feeds|"}
    for src, dst, direction, _ in edges:
        if src in nodes and dst in nodes:
            lines.append(f"  {src} {arrow.get(direction, '-->')} {dst}")
    lines.append("```")
    return f"### {title}\n\n" + "\n".join(lines) + "\n"


def write_couplings(entries: list[Entry], edges, files: list[Path]) -> None:
    by_id = {e.id: e for e in entries}
    parts = [
        "# Variable couplings",
        "",
        "Generated by `check.py`. Do not edit by hand; edit the YAML and rerun the checker.",
        "",
        f"Files: {', '.join(p.name for p in files)}. Variables: {len(entries)}. Couplings: {len(edges)}.",
        "",
        "Arrows: `up` means a rise in the source pushes the target up, `down` pushes it down, `either` depends on the case.",
        "A dotted `feeds` arrow means the target lists the source in `inputs` and the source does not list the target in `affects`.",
        "The full graph is large; Mermaid viewers may refuse to draw more than about 500 edges, so each level also has its own graph.",
        "",
        "## All couplings, grouped by level",
        "",
        mermaid(by_id, edges, LEVELS, "Full graph"),
        "## One graph per level",
        "",
        "Each graph shows the level's variables and every variable one step away.",
        "",
    ]
    for level in LEVELS:
        core = {e.id for e in entries if e.data.get("level") == level}
        if not core:
            continue
        local = [x for x in edges if x[0] in core or x[1] in core]
        ids = core | {x[0] for x in local} | {x[1] for x in local}
        nodes = {i: by_id[i] for i in ids if i in by_id}
        parts.append(mermaid(nodes, local, LEVELS, f"Level: {level} ({len(core)} variables, {len(local)} couplings)"))
    parts += ["## Edge table", "", "| From | To | Direction | How |", "|---|---|---|---|"]
    for src, dst, direction, how in edges:
        parts.append(f"| `{src}` | `{dst}` | {direction} | {how.replace('|', '/')} |")
    parts += ["", "## Variables", "", "| Id | Level | Kind | Status | Name |", "|---|---|---|---|---|"]
    for e in sorted(entries, key=lambda x: (LEVELS.index(x.data["level"]) if x.data.get("level") in LEVELS else 99, x.id)):
        parts.append(f"| `{e.id}` | {e.data.get('level')} | {e.data.get('kind')} | {e.data.get('status')} | {str(e.data.get('name', '')).replace('|', '/')} |")
    OUT_FILE.write_text("\n".join(parts) + "\n", encoding="utf-8")


def table(title: str, counter: Counter, order: list[str]) -> str:
    keys = [k for k in order if k in counter] + sorted(set(counter) - set(order), key=str)
    width = max([len(str(k)) for k in keys] + [5])
    rows = [f"{title}:"] + [f"  {str(k):<{width}}  {counter[k]}" for k in keys]
    return "\n".join(rows)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", type=Path, help="extra ledger files, e.g. additions/sizing.yaml")
    parser.add_argument("--with-additions", action="store_true", help="also load every additions/*.yaml")
    parser.add_argument("--strict", action="store_true", help="fail on warnings too")
    parser.add_argument("--no-paths", action="store_true", help="skip the check that source paths and lines exist")
    parser.add_argument("--no-write", action="store_true", help="do not write couplings.md")
    args = parser.parse_args(argv)

    files = [BASE_FILE]
    for f in args.files:
        path = f.resolve()
        if path not in files:
            files.append(path)
    if args.with_additions and ADDITIONS.is_dir():
        for path in sorted(ADDITIONS.glob("*.yaml")):
            if path.resolve() not in files:
                files.append(path.resolve())

    report = Report()
    entries: list[Entry] = []
    for path in files:
        entries += load(path, report)

    paths = None if args.no_paths else PathCache()
    seeds = seed_ids_known()
    for entry in entries:
        check_entry(entry, report, paths, seeds)

    ids = Counter(e.id for e in entries)
    for dup, n in ids.items():
        if n > 1:
            homes = ", ".join(e.where for e in entries if e.id == dup)
            report.err(dup, f"id used {n} times ({homes})")
    known = set(ids)

    owner: dict[str, str] = {}
    for e in entries:
        owner.setdefault(e.id, e.id)
    for e in entries:
        for alias in e.data.get("aliases") or []:
            if not isinstance(alias, str):
                continue
            key = alias.strip().lower()
            if key in known and key != e.id:
                report.warn(e.where, f"alias '{alias}' is another entry's id; merge them or drop the alias")
            elif key in owner and owner[key] != e.id:
                report.warn(e.where, f"alias '{alias}' is also an alias of {owner[key]}; one idea may be split in two")
            else:
                owner[key] = e.id

    for e in entries:
        for ref in e.data.get("inputs") or []:
            if isinstance(ref, str) and ref not in known:
                report.err(e.where, f"input '{ref}' is not an id in any loaded file")
        for edge in e.data.get("affects") or []:
            if isinstance(edge, dict) and isinstance(edge.get("id"), str) and edge["id"] not in known:
                report.err(e.where, f"affects '{edge['id']}', which is not an id in any loaded file")

    edges = [x for x in edges_of(entries) if x[0] in known and x[1] in known]
    touched_out = defaultdict(int)
    touched_in = defaultdict(int)
    for src, dst, _, _ in edges:
        touched_out[src] += 1
        touched_in[dst] += 1
    orphans = sorted(i for i in known if not touched_out[i] and not touched_in[i])
    unaffected = sorted(i for i in known if not touched_in[i] and touched_out[i])
    one_sided = 0
    affects_pairs = {(e.id, x["id"]) for e in entries for x in (e.data.get("affects") or []) if isinstance(x, dict) and isinstance(x.get("id"), str)}
    for e in entries:
        for src in e.data.get("inputs") or []:
            if isinstance(src, str) and (src, e.id) not in affects_pairs:
                one_sided += 1

    print(f"Loaded {len(entries)} variables from {len(files)} file(s): {', '.join(p.name for p in files)}")
    print()
    print(table("By level", Counter(e.data.get("level") for e in entries), LEVELS))
    print(table("By kind", Counter(e.data.get("kind") for e in entries), KINDS))
    print(table("By status", Counter(e.data.get("status") for e in entries), STATUSES))
    print(table("By basis", Counter(e.data.get("basis", "(none)") for e in entries), BASES))
    with_default = [e for e in entries if e.data.get("default") is not None]
    derived = [e for e in with_default if isinstance(e.data.get("derivation"), str) and not is_open(e.data["derivation"])]
    print()
    print(f"Defaults set: {len(with_default)}; with a derivation: {len(derived)}; "
          f"of those reasoned or formula: {sum(1 for e in derived if e.data.get('basis') in ('reasoned', 'formula'))}, "
          f"stated without working: {sum(1 for e in derived if e.data.get('basis') == 'stated')}")
    print(f"Null defaults: {len(entries) - len(with_default)} "
          f"(open derivation: {sum(1 for e in entries if e.data.get('default') is None and is_open(str(e.data.get('derivation', ''))))})")
    print(f"Couplings: {len(edges)} ({sum(1 for x in edges if x[2] != 'feeds')} from affects, "
          f"{sum(1 for x in edges if x[2] == 'feeds')} from inputs only)")
    print(f"Orphans (no coupling either way): {len(orphans)}")
    for o in orphans:
        print(f"  {o}")
    print(f"Nothing affects these (roots that only push on others): {len(unaffected)}")
    if unaffected:
        print("  " + ", ".join(unaffected))
    print(f"Info: {one_sided} input links are not mirrored in the source's affects list (drawn as 'feeds').")

    if not args.no_write and not report.errors:
        write_couplings(entries, edges, files)
        print(f"Wrote {OUT_FILE}")
    elif report.errors:
        print("couplings.md not written because of errors.")

    if report.warnings:
        print()
        print(f"WARNINGS ({len(report.warnings)}):")
        for line in report.warnings:
            print(f"  {line}")
    if report.errors:
        print()
        print(f"ERRORS ({len(report.errors)}):")
        for line in report.errors:
            print(f"  {line}")
        return 1
    if args.strict and report.warnings:
        return 1
    print()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
