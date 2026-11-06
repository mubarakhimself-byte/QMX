"""Generate PRESET-NUMBERS.md from the ledger and preset-rules.yaml. Fails if a core numeric row has no rule, or a rule row is
not a core numeric row, or a rule, class, clock or owning row is outside its closed list. Rerunning gives the same bytes.

    uv run --no-project --with pyyaml python architecture/build_preset_numbers.py        (from tracker/risk-core)
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
LEDGER = HERE.parent / "ledger" / "v1" / "variables.yaml"
RULES = HERE / "preset-rules.yaml"
OUT = HERE / "PRESET-NUMBERS.md"
BARE = {"count", "USD", "R", "ratio", "percent", "minutes", "bars", "pips_points_ticks"}
# Numeric rows the ledger files under "other": a duration, a size or a rate with no bare measure of its own.
OTHER = re.compile(r"^other: (seconds|lots|days|hours|per quote or seconds|fires per month|days or trades|hours or trades|R per round trip by hour bucket)$")
LADDERS = {
    "preset-default@1": ("preset, refuse", "The value the chain resolves (preset, class, instrument, unit; later keys win, a child only tightens a cap), with its `why`. A blank recommends nothing, the ladder reaches `refuse`, and the live click blocks. It reads no record and moves only with a new version."),
    "horizon-floor-odds@1": ("own_record (card), preset, refuse", "`committed_cushion_usd / (result_spread_r x z x sqrt(trade_rate x days) x B)`, reserve inside the cushion. Preset rung: the smaller of the last value in force and `risk_fraction x cushion / B`. Produces the baseline and its sigma budgets."),
    "own-percentile@1": ("own_record (card), pooled_class, preset, refuse", "A percentile of the unit's own distribution: live record, else a block bootstrap of the frozen card. Serves the money brake's trip, the bad cohort, the cut's MAE line, the e-meter's scale."),
    "own-shrink@1": ("own_record (card), pooled_class, preset, refuse", "The own-record estimate shrunk toward the card by `n / (n + calibration_shrink_k)`, moving only past `calibration_min_trades`."),
    "cusum-from-card@1": ("own_record (card), preset, refuse", "The CUSUM's limit and allowance from the card's net edge and spread, at a target healthy alarm spacing. The reference is the holdout's `net_r`."),
    "day-stop-k@1": ("own_record (harness table), preset, refuse", "k from a table of k by N, drawn in the harness at the group's own bad day with the tail rows on and left on the group's receipt. The anchor reads the table; no draw on the runtime thread."),
    "spread-histogram@1": ("own_record (live baseline), pooled_class, refuse", "The SQS settings from percentiles of the spread histogram on the live account. A demo-conditioned baseline never satisfies live (DEC-0230), so the first live entry waits hours."),
    "reserve-and-key@1": ("own_record (card), preset, refuse", "The reserve: the largest bet key gapping to its class's worst step. The key cap: unit r x (L + z sqrt(L)) for the key's expected concurrent positions L."),
    "card-rate@1": ("own_record (card), preset, refuse", "A multiple of the card's trade rate at the unit's busiest hour."),
    "holdout-band@1": ("own_record (card), refuse", "The holdout's deflated band after costs. The low end decides at the door: below zero refused, at zero start 0.25, above zero start 0.50."),
    "proof-plan@1": ("own_record (card), preset, refuse", "Trades needed to prove the band's low end at the set confidence, with the incubation cap."),
    "cost-cell@1": ("measured fills, pooled_class", "A fact, not a number: the hour's measured cell, else the pooled stressed class default labelled `cost:uncalibrated`. Never refuses."),
    "kernel": ("measured, then the fact's fail mode", "A fact the kernel measures or computes (SPINE 4.4). Not in the preset."),
    "record": ("measured, then refuse", "A fact on the instrument record. Not in the preset."),
    "harness": ("measured", "A report the harness writes. Not in the preset."),
    "user_only": ("user, blocks the live click", "His value, through his door only, immediate and journalled. It compiles blank and blocks the live click."),
}
CLASSES = {"user": "his", "preset": "in the preset", "derive": "a rule computes it", "fact": "measured", "venue": "on the record", "report": "written only"}
OWNERS = {
    "unit-money-bench@1", "drift-monitor@1", "group-day-pair@1", "cushion-clip@1", "bet-key-cap@1", "per-trade-cap@1", "sanity-band@1",
    "margin-headroom@1", "order-rate@1", "stop-side@1", "sqs-gate@1", "news-window@1", "admission-gate@1", "horizon-floor-odds@1",
    "money-at-stop@1", "retry-then-lockout@1", "house-money-press@1", "fast-invalidation-cut@1", "time-exit-bars", "disaster-stop",
    "guard.applier", "guard.facts", "guard.level", "feasibility", "motion-engine", "cost-cell@1", "trade-row", "judge", "machine-check",
    "harness", "risk-state", "node-fast-lane", "order-path", "evidence",
}
CLOCKS = {"day", "allocation", "live", "his door", "record version", "on the order", "on the close", "on the card", "on a run"}


def stop(message: str) -> None:
    sys.exit(f"build_preset_numbers: {message}")


def text(value) -> str:  # noqa: ANN001
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(text(x) for x in value)
    if isinstance(value, dict):
        return ", ".join(f"{k} {text(v)}" for k, v in value.items())
    return str(value).replace("|", "/").replace("\n", " ")


def value_cell(row: dict, rule: dict) -> str:
    if row.get("default") is not None:
        return f"**{text(row['default'])}** (ledger)"
    if rule.get("v") is not None:
        return f"{text(rule['v'])} (model)"
    seen = [s["value"] for s in row.get("seen_values") or []][:2]
    if seen:
        return f"open; seen {'; '.join(text(s) for s in seen)}"
    return "open"


def main() -> int:
    rows = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    core = {r["id"]: r for r in rows if r["tier"] == "core"}
    numeric = {i: r for i, r in core.items() if str(r["measure"]) in BARE or OTHER.match(str(r["measure"]))}
    rules = yaml.safe_load(RULES.read_text(encoding="utf-8"))["rows"]
    missing = sorted(set(numeric) - set(rules))
    extra = sorted(set(rules) - set(numeric))
    if missing or extra:
        stop(f"core numeric rows with no rule: {missing}; rule lines for rows not core and numeric: {extra}")
    for rid, rule in rules.items():
        if rule["c"] not in CLASSES:
            stop(f"{rid}: class {rule['c']}")
        if rule["r"] not in LADDERS:
            stop(f"{rid}: rule {rule['r']}")
        if rule["o"] not in OWNERS:
            stop(f"{rid}: owning row {rule['o']}")
        if rule["k"] not in CLOCKS:
            stop(f"{rid}: clock {rule['k']}")
        if rule["c"] in ("user", "preset", "derive") and "m" not in rule:
            stop(f"{rid}: a number needs a mode")
    if {i for i, r in rules.items() if r["c"] == "user"} - set(core["x1_never_self_tune_list"]["default"]):
        stop("a user row is not on x1_never_self_tune_list")

    by_class = Counter(r["c"] for r in rules.values())
    used = Counter(r["r"] for r in rules.values())
    bare = sum(1 for r in numeric.values() if str(r["measure"]) in BARE)
    head = ["| Number | Level, measure | Value | Rule | Rung, day one | Clock | Cautious | Mode | Owning row | Note |", "|---|---|---|---|---|---|---|---|---|---|"]

    def line(rid: str) -> str:
        row, rule = numeric[rid], rules[rid]
        return (f"| `{rid}` | {row['level']}, {text(row['measure']).removeprefix('other: ')} | {value_cell(row, rule)} | `{rule['r']}` | {rule['g']} | {rule['k']} | {rule['d']} | "
                f"{rule.get('m', '-')} | `{rule['o']}` | {text(rule.get('n'))} |")

    out = [
        "# Preset numbers: every core numeric row with its rule",
        "",
        "Generated by `architecture/build_preset_numbers.py` from `ledger/v1/variables.yaml` and `architecture/preset-rules.yaml`. Do not edit by hand; change the rules file or the ledger and rerun. The script refuses a core numeric row with no rule.",
        "",
        "**Rules are decided. Values are open for the numbers lens.** A value marked `(ledger)` is the ledger's stated default. `(model)` is what `fold_sim.py` ran, with no authority. `seen` is an older generation's value, with no weight. Model numbers only.",
        "",
        f"{len(rules)} rows: {bare} with a bare measure, which is CHECK.md's 107 less the two the last round moved to shadow, plus {len(rules) - bare} durations and sizes the ledger files under `other:`. Not numbers and not listed: lists, rules, codes, states, `kill_switch_level` (his hand).",
        "",
        "| Class | Rows | Meaning |",
        "|---|---|---|",
        *[f"| {c} | {by_class[c]} | {m} |" for c, m in CLASSES.items()],
        "",
        "## The one rule a preset value uses: `preset-default@1`",
        "",
        "A preset number may not have `derivation: None`. A plain value goes through this block, so every number has one shape and one receipt. It implements `DerivationInstance` (SPINE 4.2) and is about 20 lines:",
        "",
        "```python",
        "class PresetDefault:                     # stdlib/preset-default/1/block.py; produces any number; reads nothing",
        "    def __init__(self, value: Decimal | str | None, why: str): ...   # the value the chain resolved for this number",
        "    def update(self, inputs) -> Recommendation | None:",
        "        if self.value is None:           # blank: no recommendation, the ladder reaches refuse, the live click blocks",
        "            return None",
        '        return Recommendation(target=self.value, low=None, high=None, rung="preset")',
        "```",
        "",
        "A first preset row, by this table:",
        "",
        "```yaml",
        "numbers:",
        "  money_brake_percentile:",
        "    measure: percent",
        "    level: unit",
        "    owner: preset",
        '    default: "1"',
        """    why: "the unit's own 1 % day; the numbers lens owns it\"""",
        "    authority: at_anchor",
        "    derivation: {rule: preset-default@1, ladder: [preset, refuse], clock: allocation, cautious_direction: up}",
        "  money_brake_threshold_r:",
        "    measure: R",
        "    level: unit",
        "    owner: derivation",
        '    default: ""                  # the preset rung is blank, so the ladder ends in refuse',
        '    why: "derives from the card; no fixed value"',
        "    authority: at_anchor",
        "    derivation: {rule: own-percentile@1, inputs: {percentile: money_brake_percentile}, ladder: [own_record, pooled_class, preset, refuse], min_count: 60, shrink_k: 100, clock: allocation, cautious_direction: up}",
        "```",
        "",
        "**To write the first preset:** take the rows in table A. A `user` row goes on the group and stays blank until he fills it. A `preset` row takes its value or stays blank; a blank compiles and blocks the live click, never paper or the harness. A `derive` row takes its rule and ladder. The click's card lists every number still on the preset rung, so he sees what is not calibrated.",
        "",
        "## The rules",
        "",
        "| Rule | Rows | Ladder | What it does |",
        "|---|---|---|---|",
        *[f"| `{r}` | {used[r]} | {LADDERS[r][0]} | {LADDERS[r][1]} |" for r in LADDERS],
        "",
        "Cautious: which way the value moves when data is missing. `up`, `down`, `hold`; `blocks`: a blank blocks the live click; `refuse`, `label`: a fact's fail mode. For a negative threshold such as `money_brake_threshold_r`, `up` means toward zero, tighter.",
        "",
        "## A. The numbers a preset or group carries",
        "",
        *head,
        *[line(i) for i in numeric if rules[i]["c"] in ("user", "preset", "derive")],
        "",
        "## B. Facts and reports: not in a preset, listed so nothing is lost",
        "",
        *head,
        *[line(i) for i in numeric if rules[i]["c"] not in ("user", "preset", "derive")],
        "",
    ]
    OUT.write_text("\n".join(out), encoding="utf-8", newline="\n")
    print(f"PRESET-NUMBERS.md: {len(rules)} rows {dict(by_class)}; {len([r for r in used if r not in ('kernel', 'record', 'harness', 'user_only')])} rule blocks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
