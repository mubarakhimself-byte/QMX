"""Build ledger v1 from ledger v0, the additions and the funnel's merge plan.

    uv run --no-project --with pyyaml python ledger/build_v1.py
    uv run --no-project --with pyyaml python ledger/check.py --v1

Reads variables.yaml, additions/*.yaml, funnel/ledger-merge.yaml and section 5.1 of
funnel/FUNNEL.md. Writes v1/variables.yaml, v1/dead.yaml, v1/core.md and v1/NOTES.md;
check.py --v1 writes v1/couplings.md. Every output is generated, so a fix belongs in the
plan or in this script, never in v1/. Rerunning gives the same bytes.

The plan is data. Its sections drive the build; the few plan notes that change a field
are read by the patterns in apply_plan_note. Where the plan is silent, the rule used and
every row it touched are listed in v1/NOTES.md.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

sys.dont_write_bytecode = True  # importing check.py must not leave a __pycache__ in the ledger folder
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import EDGE_TYPES, LEVELS, LIVE_TIERS, is_open  # noqa: E402

HERE = Path(__file__).resolve().parent
TRACKER = HERE.parent
V1 = HERE / "v1"
PLAN_FILE = TRACKER / "funnel" / "ledger-merge.yaml"
FUNNEL_FILE = TRACKER / "funnel" / "FUNNEL.md"

FIELD_ORDER = [
    "id", "name", "tier", "level", "kind", "measure", "applies_to", "default", "basis", "derivation",
    "seen_values", "inputs", "affects", "configurable", "changed_by", "status", "sources", "seed_ids",
    "aliases", "notes", "open_questions",
]
DEAD_FIRST = ["id", "name", "tier", "dead_reason", "dead_with", "status", "status_before", "removed_references"]
STATUS_WORDS = "running|built_not_running|docs_only|dropped|proposal|idea"
RANK = {level: i for i, level in enumerate(LEVELS)}
PLAN_STATE_IDS = {"brake_state", "x1_trading_state"}  # plus kill_switch_*, as the plan's rule says
# The plan's deaths leave these rows with no coupling at all. The plan does not mention them, so the
# replacement edge is this script's call: the dead edge's meaning, moved to the row the plan says survives.
# NOTES.md lists them.
REPAIRED_ORPHANS = [
    ("ev_core_deny_list", "ev_bet_grid", "either", "on the list; the row's default names the bet grid"),
    ("ev_pipeline_null_rate", "ev_evidence_e", "either", "a high null rate tightens the evidence bar for raises above baseline"),
]


class NoAnchors(yaml.SafeDumper):
    def ignore_aliases(self, data):  # noqa: ANN001, ANN201
        return True


@dataclass
class Log:
    """What the build decided where the plan was silent. NOTES.md prints all of it."""

    level_measure: list[str] = field(default_factory=list)
    adopted_default: list[str] = field(default_factory=list)
    default_not_adopted: list[str] = field(default_factory=list)
    adopted_derivation: list[str] = field(default_factory=list)
    running_absorbed: list[str] = field(default_factory=list)
    status_kept_running: list[str] = field(default_factory=list)
    revived_from_dropped: list[str] = field(default_factory=list)
    implied_merges: list[str] = field(default_factory=list)
    extended_state_targets: Counter = field(default_factory=Counter)
    explicit_edges: list[str] = field(default_factory=list)
    repaired_orphans: list[str] = field(default_factory=list)
    merged_edges: int = 0
    self_edges_removed: int = 0


def stop(message: str) -> None:
    sys.exit(f"build_v1: {message}")


def alias_key(text: str) -> str:
    return text if len(text) <= 3 else text.lower()  # the checker's rule: short aliases are maths symbols


def add_aliases(row: dict, names: list) -> None:
    have = {alias_key(str(a)) for a in row.get("aliases") or []} | {alias_key(row["id"]), alias_key(row["name"])}
    for name in names:
        text = str(name).strip()
        if alias_key(text) not in have:
            row.setdefault("aliases", []).append(text)
            have.add(alias_key(text))


def extend_unique(row: dict, key: str, items: list | None) -> None:
    for item in items or []:
        if item not in (row.get(key) or []):
            row.setdefault(key, []).append(item)


def add_note(row: dict, text: str) -> None:
    row["notes"] = f"{row['notes']} {text}" if row.get("notes") else text


def fold(keep: dict, gone: dict, gone_file: str, log: Log) -> None:
    """Fold one row into the row that survives. The plan names what folds; the rest goes into notes."""
    same_id = keep["id"] == gone["id"]
    label = f"the {gone_file} row" if same_id else f"{gone['id']} ({gone_file})"
    add_aliases(keep, ([] if same_id else [gone["id"]]) + [gone["name"]] + list(gone.get("aliases") or []))
    extend_unique(keep, "seen_values", gone.get("seen_values"))
    extend_unique(keep, "sources", gone.get("sources"))
    extend_unique(keep, "seed_ids", gone.get("seed_ids"))
    extend_unique(keep, "inputs", gone.get("inputs"))
    extend_unique(keep, "open_questions", gone.get("open_questions"))
    keep["affects"] = list(keep.get("affects") or []) + list(gone.get("affects") or [])

    if gone["level"] != keep["level"] or gone["measure"] != keep["measure"]:
        log.level_measure.append(
            f"`{keep['id']}` keeps {keep['level']}, {keep['measure']}; {label} had {gone['level']}, {gone['measure']}"
        )
    if gone["status"] == "running" and keep["status"] != "running":
        log.running_absorbed.append(f"`{keep['id']}` stays {keep['status']}; {label} was running")

    took_derivation = settle_default_and_derivation(keep, gone, label, log)
    differs = [
        f"{key} {gone.get(key)}"
        for key in ("level", "kind", "measure", "status", "configurable", "changed_by", "applies_to")
        if gone.get(key) != keep.get(key)
    ]
    parts = [f"Folded {label}."]
    if differs:
        parts.append("It had " + ", ".join(differs) + ".")
    if not took_derivation and gone["derivation"] != keep["derivation"]:
        parts.append(f"Its derivation: {gone['derivation']}")
    if gone.get("notes"):
        parts.append(f"Its notes: {gone['notes']}")
    add_note(keep, " ".join(parts))


def settle_default_and_derivation(keep: dict, gone: dict, label: str, log: Log) -> bool:
    """Return True when the absorbed row's derivation moved into the survivor's derivation.

    A default travels only into a null default with the same measure, because the two rows then
    state one quantity. Any absorbed default is also kept in seen_values, so nothing is lost.
    """
    gone_default = gone.get("default")
    if gone_default is not None:
        source = (gone.get("sources") or [{}])[0]
        seen = {"value": gone_default, "gen": source.get("gen", "expansion"), "note": f"default of {label}"}
        if source.get("ref"):
            seen["ref"] = source["ref"]
        extend_unique(keep, "seen_values", [seen])
        if keep.get("default") is None and keep["measure"] == gone["measure"]:
            log.adopted_default.append(f"`{keep['id']}` = {gone_default}, from {label}")
            keep["default"] = gone_default
            take_derivation(keep, gone)
            return True
        if keep.get("default") != gone_default:
            log.default_not_adopted.append(
                f"`{keep['id']}` stays {keep.get('default')}; {label} had {gone_default} ({gone['measure']}), now in seen_values"
            )
        return False
    if keep.get("default") is None and is_open(keep["derivation"]) and not is_open(gone["derivation"]):
        log.adopted_derivation.append(f"`{keep['id']}` takes its working from {label}")
        take_derivation(keep, gone)
        return True
    return False


def sentence(text: str) -> str:
    text = text.strip()
    return text if text[-1] in ".!?" else f"{text}."


def take_derivation(keep: dict, gone: dict) -> None:
    keep["derivation"] = f"{sentence(gone['derivation'])} Earlier text under {keep['id']}: {keep['derivation']}"
    keep["basis"] = gone["basis"]


def apply_plan_note(row: dict, note: str | None) -> None:
    """Every plan note lands in notes. These patterns are the notes that also change a field."""
    if not note:
        return
    add_note(row, f"Plan: {note}")
    if match := re.search(r"\bmeasure '([^']+)'", note):
        row["measure"] = match[1]
    if match := re.search(r"\blevel '([^']+)'", note):
        row["level"] = match[1]
    if match := re.search(r"\bname '([^']+)'", note):
        row["name"] = match[1]
    if match := re.search(r"its text gains '(.+)'\.?$", note):
        row["derivation"] = f"{sentence(row['derivation'])} Exits are never blocked {match[1]}."
    if match := re.search(r"values at go-live: \[([^\]]*)\]", note):
        row["default"] = [x.strip() for x in match[1].split(",")]
        row["basis"] = "reasoned"
    if match := re.search(r"value at go-live: ([\w.]+)", note):
        text = match[1].rstrip(".")
        try:
            row["default"] = int(text) if re.fullmatch(r"\d+", text) else float(text)
        except ValueError:
            row["default"] = text
        row["basis"] = "reasoned"
        row["derivation"] = f"{note} Earlier text: {row['derivation']}"


def load_rows() -> list[tuple[str, dict]]:
    rows: list[tuple[str, dict]] = []
    for path in [HERE / "variables.yaml"] + sorted((HERE / "additions").glob("*.yaml")):
        rows += [(path.name, row) for row in yaml.safe_load(path.read_text(encoding="utf-8")) or []]
    return rows


def collapse_duplicates(rows: list[tuple[str, dict]], plan: dict, log: Log) -> tuple[dict, dict, list[str]]:
    """Section 1: one id in two files becomes one row. Returns rows by id, each id's home file, the order."""
    by_id: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for file_name, row in rows:
        by_id[row["id"]].append((file_name, row))
    plan_dups = {d["keep"]: d for d in plan["duplicates"]}
    survivors: dict[str, dict] = {}
    homes: dict[str, str] = {}
    for rid, items in by_id.items():
        if len(items) == 1:
            homes[rid], survivors[rid] = items[0]
            continue
        if rid not in plan_dups:
            stop(f"{rid} is in several files and the plan does not say which wins")
        dup = plan_dups[rid]
        keep = next((row for name, row in items if name == dup["keep_file"]), None)
        if keep is None:
            stop(f"{rid}: keep_file {dup['keep_file']} does not hold this id")
        for name, row in items:
            if row is not keep:
                fold(keep, row, name, log)
        apply_plan_note(keep, dup.get("note"))
        homes[rid], survivors[rid] = dup["keep_file"], keep
    return survivors, homes, list(by_id)


def implied_merges(plan: dict, log: Log) -> list[dict]:
    """A section 1 note can promise a merge that section 3 forgot. Do what the note says."""
    listed = {a for section in ("aliases", "merges") for m in plan[section] for a in m.get("absorb") or []}
    merges = []
    for dup in plan["duplicates"]:
        match = re.search(r"(\w+) merges into it below", dup.get("note") or "")
        if match and match[1] not in listed:
            merges.append({"keep": dup["keep"], "absorb": [match[1]]})
            log.implied_merges.append(f"`{match[1]}` into `{dup['keep']}`")
    return merges


def is_state_target(rid: str, log: Log) -> bool:
    if rid in PLAN_STATE_IDS or rid.startswith("kill_switch_"):
        return True
    if rid.endswith("_state"):
        log.extended_state_targets[rid] += 1
        return True
    return False


def edge_type(source_level: str, target: dict, log: Log) -> str:
    gap = RANK[source_level] - RANK[target["level"]]
    if gap == 0:
        return "same:level"
    if gap < 0:
        return "up:event"
    return "down:state" if is_state_target(target["id"], log) else "down:cap"


def build(plan: dict, log: Log) -> tuple[list[dict], list[dict], dict[str, list[str]]]:
    survivors, homes, order = collapse_duplicates(load_rows(), plan, log)
    resolve: dict[str, str] = {}

    def rid(raw: str) -> str:
        while raw in resolve:
            raw = resolve[raw]
        return raw

    # Sections 2 and 3: merges.
    for merge in plan["aliases"] + plan["merges"] + implied_merges(plan, log):
        keep = survivors[merge["keep"]]
        for gone_id in merge.get("absorb") or []:
            fold(keep, survivors.pop(gone_id), homes[gone_id], log)
            resolve[gone_id] = merge["keep"]
        apply_plan_note(keep, merge.get("note"))

    # Section 4: deaths. An entry with keep: true stays, with its new status and note.
    dead: list[dict] = []
    for item in plan["dies"]:
        row = survivors[item["id"]]
        status = re.search(rf"\bstatus ({STATUS_WORDS})\b", item["reason"])
        if item.get("keep"):
            if status:
                row["status"] = status[1]
            add_note(row, f"Plan ({item['with']}): {item['reason']}")
            continue
        was = row["status"]
        extra = {"tier": "dead", "dead_reason": item["reason"], "dead_with": str(item["with"]), "status": "dropped"}
        if was != "dropped":
            extra["status_before"] = was
        dead.append({**row, **extra, "removed_references": []})
        del survivors[item["id"]]
    dead_ids = {row["id"]: row for row in dead}

    # Section 5: renames.
    for item in plan["rename"]:
        row = survivors.pop(item["from"])
        row["aliases"] = [a for a in row.get("aliases") or [] if alias_key(a) != alias_key(item["to"])]
        row["id"] = item["to"]
        add_aliases(row, [item["from"]])
        add_note(row, f"Plan: renamed from {item['from']}. {item['reason']}")
        survivors[item["to"]] = row
        resolve[item["from"]] = item["to"]
        order[order.index(item["from"])] = item["to"]

    # Point every reference at the survivor. References to the dead go, and dead.yaml records them.
    for row in survivors.values():
        me = row["id"]
        inputs: list[str] = []
        for raw in row.get("inputs") or []:
            target = rid(raw)
            if target in dead_ids:
                dead_ids[target]["removed_references"].append({"from": me, "field": "inputs"})
            elif target == me:
                log.self_edges_removed += 1
            elif target not in inputs:
                inputs.append(target)
        row["inputs"] = inputs
        edges: dict[str, dict] = {}
        for edge in row.get("affects") or []:
            target = rid(edge["id"])
            if target in dead_ids:
                dead_ids[target]["removed_references"].append({"from": me, "field": "affects", "how": edge["how"]})
            elif target == me:
                log.self_edges_removed += 1
            elif target in edges:
                log.merged_edges += 1
                if edges[target]["direction"] != edge["direction"]:
                    edges[target]["direction"] = "either"
                if edge["how"] not in edges[target]["how"]:
                    edges[target]["how"] += f"; {edge['how']}"
            else:
                edges[target] = {"id": target, "direction": edge["direction"], "how": edge["how"]}
        row["affects"] = list(edges.values())

    # Section 6: orphans. The action text names the inputs and the typed edges to add.
    for item in plan["orphans"]:
        row = survivors[rid(item["id"])]
        if match := re.search(r"inputs \[([^\]]*)\]", item["action"]):
            extend_unique(row, "inputs", [rid(x.strip()) for x in match[1].split(",") if x.strip()])
        for target, kind in re.findall(r"(\w+) \((down:cap|down:state|up:event)\)", item["action"]):
            target = rid(target)
            row["affects"].append({
                "id": target, "direction": "either", "type": kind,
                "how": f"coupled by the funnel's merge plan, section 6 ({kind})",
            })
            log.explicit_edges.append(
                f"`{row['id']}` ({row['level']}) to `{target}` ({survivors[target]['level']}): {kind}"
            )

    # Rows the plan's deaths left with no coupling. Each edge is typed by the level rule below.
    for source, target, direction, how in REPAIRED_ORPHANS:
        if survivors[source]["affects"] or survivors[source]["inputs"]:
            stop(f"{source} is no longer an orphan; drop it from REPAIRED_ORPHANS")
        survivors[source]["affects"].append({"id": target, "direction": direction, "how": how})
        log.repaired_orphans.append(f"`{source}` to `{target}`: {how}")

    # Section 7: status. A row that runs in the shipped stack cannot become a proposal.
    for change in plan["status"]:
        for raw in change["ids"]:
            row = survivors[rid(raw)]
            if row["status"] == "running":
                log.status_kept_running.append(f"`{row['id']}`")
            else:
                row["status"] = change["to"]

    # Section 8: tiers. Anything not listed is later.
    tier_of: dict[str, str] = {}
    parts: dict[str, list[str]] = {}

    def assign(raw: str, tier: str) -> str:
        target = rid(raw)
        if target not in survivors:
            stop(f"section 8 lists {raw} as {tier}, but it does not survive")
        if tier_of.get(target, tier) != tier:
            stop(f"section 8 lists {raw} as both {tier_of[target]} and {tier}")
        tier_of[target] = tier
        return target

    for part, ids in plan["tiers"]["core"].items():
        parts[part] = [assign(raw, "core") for raw in ids]
    parts["fork"] = [assign(raw, "fork") for raw in plan["tiers"]["fork_F_A"]]
    for raw in plan["tiers"]["shadow"]:
        assign(raw, "shadow")
    if set(plan["tiers"]["dead"]) != set(dead_ids):
        stop("section 8's dead list and section 4 disagree")
    for row in survivors.values():
        row["tier"] = tier_of.get(row["id"], "later")
        if row["tier"] in LIVE_TIERS and row["status"] == "dropped":
            row["status"] = "proposal"
            add_note(row, f"An earlier generation dropped this; the funnel brings it back at tier {row['tier']}.")
            log.revived_from_dropped.append(f"`{row['id']}` ({row['tier']})")

    # Type every affects edge. An explicit type from section 6 stands.
    for row in survivors.values():
        for edge in row["affects"]:
            if "type" not in edge:
                edge["type"] = edge_type(row["level"], survivors[edge["id"]], log)

    ordered = [survivors[i] for i in order if i in survivors]
    return ordered, dead, parts


def shaped(row: dict, first: list[str]) -> dict:
    """Fixed field order; optional fields that came out empty are left off."""
    out = {key: row[key] for key in first if key in row}
    for key, value in row.items():
        if key not in out:
            out[key] = value
    keep_empty = {"default", "inputs", "affects", "removed_references"}
    out = {k: v for k, v in out.items() if k in keep_empty or v not in (None, [], "")}
    if out.get("affects"):
        out["affects"] = [{k: e[k] for k in ("id", "direction", "type", "how") if k in e} for e in out["affects"]]
    return out


def write_yaml(path: Path, header: str, rows: list[dict]) -> None:
    body = yaml.dump(rows, Dumper=NoAnchors, sort_keys=False, allow_unicode=True, width=1000, default_flow_style=False)
    path.write_text(f"# {header}\n{body}", encoding="utf-8", newline="\n")


def cell(value) -> str:  # noqa: ANN001
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(cell(x) for x in value)
    if isinstance(value, dict):
        return ", ".join(f"{k}: {cell(v)}" for k, v in value.items())
    return str(value).replace("|", "/").replace("\n", " ")


def funnel_parts() -> dict[int, tuple[str, int]]:
    """Section 5.1's twelve rows: {number: (short title, variable count)}."""
    section = FUNNEL_FILE.read_text(encoding="utf-8").split("### 5.1", 1)[1].split("### 5.2", 1)[0]
    found = re.findall(r"^\| (\d+) \| ([^|]+?) \| [^|]+ \| (\d+)", section, flags=re.MULTILINE)
    if len(found) != 12:
        stop(f"expected twelve parts in FUNNEL.md section 5.1, found {len(found)}")
    return {int(n): (re.split(r"[:;,]", text, maxsplit=1)[0].strip(), int(count)) for n, text, count in found}


def core_markdown(rows: list[dict], parts: dict[str, list[str]]) -> tuple[str, list[str]]:
    by_id = {row["id"]: row for row in rows}
    titles = funnel_parts()
    head = ["| Id | Name | Level | Measure | Derivation basis | Default |", "|---|---|---|---|---|---|"]

    def table(ids: list[str]) -> list[str]:
        lines = list(head)
        for i in ids:
            row = by_id[i]
            lines.append(
                f"| `{i}` | {cell(row['name'])} | {row['level']} | {cell(row['measure'])} | {row.get('basis', 'none')} | {cell(row.get('default'))} |"
            )
        return lines

    core_keys = [key for key in parts if key != "fork"]
    total = sum(len(parts[key]) for key in core_keys)
    out = [
        "# Ledger v1: the core tier",
        "",
        "Generated by `build_v1.py`. Do not edit by hand.",
        "",
        f"{total} variables, grouped by the twelve parts in `funnel/FUNNEL.md` section 5.1. `none` under Default means no value is set yet; `seen_values` and the derivation in `variables.yaml` hold what is known.",
        "",
    ]
    mismatches = []
    for key in core_keys:
        number = int(re.match(r"part_(\d+)", key)[1])
        title, funnel_count = titles[number]
        if funnel_count != len(parts[key]):
            mismatches.append(f"part {number}: FUNNEL.md says {funnel_count}, the plan lists {len(parts[key])}")
        out += [f"## Part {number}. {title} ({len(parts[key])})", ""] + table(parts[key]) + [""]
    out += [
        f"## Fork F-A only, not counted above ({len(parts['fork'])})",
        "",
        "These join part 3 only if the architects' fork F-A takes the applier with modes (`funnel/FUNNEL.md` section 5.3).",
        "",
    ] + table(parts["fork"]) + [""]
    return "\n".join(out), mismatches


def bullets(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- none"]


def notes_markdown(rows: list[dict], dead: list[dict], log: Log, mismatches: list[str]) -> str:
    tiers = Counter(row["tier"] for row in rows)
    types = Counter(edge["type"] for row in rows for edge in row["affects"])
    old_rows = len(load_rows())
    idea_core = sum(1 for row in rows if row["tier"] == "core" and row["status"] == "idea")
    near = sorted(
        f"`{row['id']}` and `{m[2]}`"
        for row in rows
        if (m := re.match(r"^(x1_|ev_)(.+)$", row["id"])) and m[2] in {r["id"] for r in rows}
    )
    out = f"""# Ledger v1: notes

Generated by `build_v1.py`. Do not edit by hand; the text and the lists below come from the script.

{old_rows} v0 and additions rows became {len(rows)} entries and {len(dead)} dead rows. Tiers: core {tiers['core']}, fork {tiers['fork']}, shadow {tiers['shadow']}, later {tiers['later']}.

Rerun from the `risk-core` folder:

```
uv run --no-project --with pyyaml python ledger/build_v1.py
uv run --no-project --with pyyaml python ledger/check.py --v1
```

## Where the plan is wrong or ambiguous, and what the build did

1. **Same-level edges have no type.** The plan types every `affects` edge as `down:cap`, `down:state` or `up:event` from the two levels, but {types['same:level']} of {sum(types.values())} edges join rows at one level. Calling those down or up would be false, so they get a fourth value, `same:level`. The level order is the checker's list: {', '.join(LEVELS)}.
2. **The plan's own section 6 edges go against its level rule.** All of them are honoured as written, and the checker prints them:
{chr(10).join(bullets(log.explicit_edges))}
3. **Section 1 promises a merge that section 3 omits.** Done as the note says: {', '.join(log.implied_merges) or 'none'}. The absorbed row's default of 5 is a threshold, while the surviving row reads as a measure of where a day sits. Settled by the fold (architecture/SPINE.md): the row measures where the day sits and its default is the line below which the day reads "bad"; one row, two readings, kept.
4. **Section 7 would mark running rows as proposals.** A row that runs in the shipped stack stays `running`: {', '.join(log.status_kept_running) or 'none'}. Its derivation says it is confirmed in code.
5. **Core and shadow rows with status `dropped`.** Section 7 revives only `house_money_multiplier`, but section 8 also puts these at a live tier. They become `proposal`, and the checker now refuses a dropped row at a live tier: {', '.join(log.revived_from_dropped) or 'none'}.
6. **The canary merges into a core row but is a later plug-in.** `ev_approval_markets` is core and absorbs `ev_canary_share` and `x1_canary_share`, while FUNNEL 5.1 part 11 and DP7 say the canary comes later. Applied as written, so a market list now carries percent shares in its history, and its couplings to `size_levels` and `size_ramp_to_full` hang off a core row. Worth a second look.
7. **`choke_budget_fire_rate` changed meaning.** The plan makes it the total budget across all cuts; FUNNEL 5.2 states that test as 0.75 of baseline. Settled by the fold and the last round: the plan's note sets name, measure (ratio) and the go-live value 0.75; the metric is dollars risked over the flat baseline on every opportunity, refusals at zero (CHECK.md B8); the old per-brake 5 percent stays in `seen_values`. The id keeps its old name so references resolve.
8. **The decay check dies by halves.** `decay_recent_trades` and `decay_record_days` die because the check is replaced, but `decay_watch_drop_r`, `decay_watch_loss_streak`, `decay_alarm_expectancy_r` and `decay_alarm_loss_streak` survive as later and running. All six run in the shipped stack today, so the two dead rows keep `status_before: running` and the code must lose them in the build.
9. **`holding_horizon` keeps dial-era couplings.** The plan drops the dial and says it raises yellow only, but its edges to `round_trip_cost_r`, `gap_allowance_r` and `hourly_volatility_profile` are unchanged because the plan does not remove them.
10. **Notes that state a value.** `house_money_scope` says "value at go-live: portfolio", so that became its default. Numbers stay notes, because FUNNEL.md says no number in it is a value: the go-live fractions on `size_level_fraction_table`, and format 4 and 5 on `compiler_format`, whose name still says format 2.
11. **A note and section 8 disagree.** `last_trip_size_level`'s note says later and section 8 says shadow; section 8 wins, and FUNNEL 5.2 agrees. `loss_event_window`'s note says shadow use only and section 8 says core; section 8 wins.
12. **Level moved by the fold.** `open_risk_cap_per_key_usd` was at position level, though FUNNEL 5.2 says the bet key cap counts one bet across units. The plan's note now sets it to portfolio, where the guard holds the bet-key ledger (SPINE.md AD-8); its edge types follow.
13. **Section 8 uses a pre-rename id.** It lists `x1_compiler_format`; the build follows the rename to `compiler_format`.
14. **"Seen_values kept" has nothing to keep.** `session_multiplier` and `sweep_cap_equity` have no `seen_values`; their old values sit in the derivation text. The whole row moves to `dead.yaml`, so nothing is lost.
15. **Section 6a names code fields, not ledger ids.** `r_after_costs` and `net_r` were not ids here. The fold adds `ledger/additions/X8-architecture-fold.yaml` with the rows the spine needs and the ledger lacked: `net_r` (part 8; `r_after_costs` holds gross, is renamed `gross_r` and is no alias of it, CHECK.md B1), `drift_warning_window_trades` and `drift_warnings_to_paper` (part 6, the drift rule as a derivation), `day_stop_sigma_multiple` (part 7, the day stop's k); it also promotes `level_lockout_days` from later to core (part 6), because the drift monitor's lock reads it. The twelve part counts below therefore differ from FUNNEL 5.1 by these five and by item 19.
16. **The tier list in the plan has `fork`.** The three F-A ids get `tier: fork`, as the plan's header says, not core or later.
17. **The plan's deaths make new orphans.** Removing references to dead ids left three rows with no coupling, and the plan does not mention them. Two had a real target left, so each gets one edge, which is this script's call and not the plan's:
{chr(10).join(bullets(log.repaired_orphans))}
18. **The last orphan died.** `cap_multiplier` fed only `sweep_cap_equity`, the 2.5x cliff section 4 replaces with the ratchet. The fold put it in `dies` with DP16, so the checker reports no orphan.
19. **The last round (architecture/CHECK.md).** `edge_to_cost_ratio_min` and `session_loss_limit_r` move to shadow; `conversion_market` and `b_split_rule` join part 5, so the core stays 207. Plan notes now set `x1_number_authority_mode`'s measure, the lists on `x1_never_self_tune_list` and `derivation_fallback_order` (a new pattern, "values at go-live: [...]"), and the go-live words on `state_carry_rule`, `risk_stop_resume_rule` and `x1_guard_unavailable_action`. Every core numeric row has its rule in `architecture/preset-rules.yaml`, printed by `architecture/build_preset_numbers.py` into `architecture/PRESET-NUMBERS.md`.

## Same idea, not merged because the plan does not list it

These survive as two rows. Add them to the plan if they are one idea. The fold merged `ev_trades_toward_proof` into `trades_toward_proof` and `x1_risk_state_emit_interval` into `risk_state_emit_interval`, and kept `ev_fallback_dwell_trades` apart from `fallback_dwell_trades`: one is the verification decider's dwell, the other the sizer fallback's.

{chr(10).join(bullets(near))}

## Rules used where the plan is silent

- The plan folds name, aliases, seen_values, sources, seed_ids, inputs and affects. The survivor's level, kind, measure, status, configurable, changed_by and applies_to stand. The absorbed row's differing values and its derivation go into the survivor's `notes`, so nothing vanishes.
- A default moves across only into a null default with the same measure. Every absorbed default also goes into `seen_values`.
- If the survivor's derivation is open and an absorbed row has working, the entry takes that derivation and basis, with the earlier text kept after it.
- Two edges to one target become one: `either` if their directions differ, both `how` lines kept ({log.merged_edges} joined). Edges that became self-references are removed ({log.self_edges_removed}).
- "A state" in the type rule means the plan's `brake_state`, `x1_trading_state` and `kill_switch_*`, plus any id ending in `_state`: {', '.join(f'`{k}`' for k in sorted(log.extended_state_targets)) or 'none'}.
- References to dead ids are removed and recorded under `removed_references` in `dead.yaml`. Dead rows get `status: dropped`, with `status_before` if it differed.
- {idea_core} core rows stay at status `idea`, because section 7 says everything else picked stays at its current status.

## Lists

### Level or measure disagreements (survivor stands unless noted)

Only `tier_dwell` has a plan note that sets the measure, and section 1's `keep_file` settles the duplicates.

{chr(10).join(bullets(log.level_measure))}

### Defaults adopted from an absorbed row

{chr(10).join(bullets(log.adopted_default))}

### Absorbed defaults not adopted

{chr(10).join(bullets(log.default_not_adopted))}

### Derivations taken from an absorbed row

{chr(10).join(bullets(log.adopted_derivation))}

### Absorbed rows that were running

The survivor's status stands, and the absorbed status is in its notes.

{chr(10).join(bullets(log.running_absorbed))}

### FUNNEL.md section 5.1 against the plan's part lists

{chr(10).join(bullets(mismatches)) if mismatches else 'All twelve part counts match.'}
"""
    return out


def main() -> int:
    for handle in (sys.stdout, sys.stderr):
        if hasattr(handle, "reconfigure"):
            handle.reconfigure(encoding="utf-8", newline="\n")
    plan = yaml.safe_load(PLAN_FILE.read_text(encoding="utf-8"))
    log = Log()
    rows, dead, parts = build(plan, log)
    rows = [shaped(row, FIELD_ORDER) for row in rows]
    dead = [shaped(row, DEAD_FIRST) for row in dead]
    bad_types = {edge["type"] for row in rows for edge in row["affects"]} - set(EDGE_TYPES)
    if bad_types:
        stop(f"edge types outside the list: {bad_types}")

    V1.mkdir(exist_ok=True)
    write_yaml(V1 / "variables.yaml", "Ledger v1. Generated by build_v1.py from variables.yaml, additions/ and funnel/ledger-merge.yaml. Do not edit.", rows)
    write_yaml(V1 / "dead.yaml", "Variables that left the ledger in v1, with the reason. Generated by build_v1.py. Do not edit.", dead)
    core, mismatches = core_markdown(rows, parts)
    (V1 / "core.md").write_text(core, encoding="utf-8", newline="\n")
    (V1 / "NOTES.md").write_text(notes_markdown(rows, dead, log, mismatches), encoding="utf-8", newline="\n")

    tiers = Counter(row["tier"] for row in rows)
    print(f"v1: {len(rows)} entries {dict(tiers)}, {len(dead)} dead. Now run check.py --v1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
