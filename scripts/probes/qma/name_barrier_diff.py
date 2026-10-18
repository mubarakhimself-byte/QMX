"""Differential of the money-path name barrier, base against head.

Loads `check_descriptor` twice: the head copy installed in the agents venv, and the base copy
read from `git show <base>:<path>`. Every spelling in a generated corpus, and every real tool
name, goes through both. PASS when no name the base refuses is allowed at head, and no real
tool name is refused at head that the base allowed. Every allowed-to-refused spelling is
written to `<evidence>/name-barrier-a2r.txt`, and their underscore forms are logged.

    python name_barrier_diff.py --base origin/qma/hp7 --evidence D:/.../evidence/hp8 \
        [--names extra.json ...]

`--names` takes JSON lists or JSON objects whose keys or values are tool names (the HP3
verifier's harvest files).
"""

from __future__ import annotations

import argparse
import asyncio
import collections
import importlib.util
import itertools
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
DESCRIPTORS = "qmx-agents/packages/qma-core/src/qma/core/barriers/descriptors.py"
SKIP = {".venv", "node_modules", "archive", ".git", "__pycache__"}
DECORATED = [
    re.compile(r"@(?:\w+\.)?tool\(\s*(?:name\s*=\s*)?[\"']([^\"']+)[\"']"),
    re.compile(r"\.tool\([^)]*?name\s*=\s*[\"']([^\"']+)[\"']", re.S),
    re.compile(r"@(?:\w+\.)+tool(?:\(\s*\))?\s*\n(?:\s*@.*\n)*\s*(?:async\s+)?def\s+(\w+)"),
    re.compile(r"@tool\s*\n(?:\s*@.*\n)*\s*(?:async\s+)?def\s+(\w+)"),
    re.compile(r"\bname:\s*str\s*=\s*[\"']([^\"']+)[\"']"),
    re.compile(r"StructuredTool\.from_function\([^)]*?name\s*=\s*[\"']([^\"']+)[\"']", re.S),
]

Check = Callable[[str, dict[str, Any]], None]


def base_check(base: str) -> Check:
    source = subprocess.run(
        [shutil.which("git") or "git", "-C", str(REPO), "show", f"{base}:{DESCRIPTORS}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout
    copy = Path(tempfile.mkdtemp()) / "base_descriptors.py"
    copy.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("base_descriptors", copy)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {base}:{DESCRIPTORS}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.check_descriptor


def verdict(check: Check, name: str, metadata: dict[str, Any]) -> str:
    try:
        check(name, metadata)
    except Exception as error:
        return f"refuse:{str(error).split(':')[0]}"
    return "allow"


def harvested() -> set[str]:
    names: set[str] = set()
    for path in REPO.rglob("*.py"):
        if SKIP & set(path.relative_to(REPO).parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for pattern in DECORATED:
            names |= {match.group(1) for match in pattern.finditer(text)}
    return names


def live_names() -> set[str]:
    from unittest.mock import MagicMock  # noqa: PLC0415

    from qmx_broker.server import create_server  # noqa: PLC0415
    from qmx_broker.service import BrokerService  # noqa: PLC0415
    from qmx_control.server import OPERATIONS  # noqa: PLC0415
    from qmx_tools.functions import domain_functions  # noqa: PLC0415

    names = {name for group in domain_functions(MagicMock()).values() for name in group}
    names |= {row[0] for row in OPERATIONS}
    with tempfile.TemporaryDirectory() as home:
        tools = asyncio.run(create_server(BrokerService(Path(home))).list_tools())
    return names | {tool.name for tool in tools}


def extra_names(paths: list[Path]) -> set[str]:
    names: set[str] = set()
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list) or path.name.startswith("harvest"):
            names |= set(data)
        else:
            names |= {name for group in data.values() for name in group}
    return names


ACTS = [
    "submit_order", "amend_order", "cancel_order", "replace_order", "open_position",
    "close_position", "reduce_position", "hedge_position", "set_protection", "amend_protection",
    "size", "resize", "mint_sizing_decision", "create_binding", "amend_binding",
    "activate_binding", "stand_down_binding", "delete_binding", "set_book_mode", "set_seat_state",
    "set_book_parameter", "set_bms_parameter", "set_priority_rank", "set_capital_floor",
    "arm_kill_switch", "disarm_kill_switch", "change_kill_switch", "change_control_action",
    "order", "position", "protection", "sizing", "binding", "mode", "control", "zone_transition",
    "promotion", "create_order", "place_order", "place_an_order", "order_submit", "order_cancel",
    "re_size", "kill_switch", "control_action", "transition_zone", "promote", "stand_down",
]  # fmt: skip
BENIGN = [
    "get_quote", "list_positions", "read_positions", "order_book", "order_history",
    "position_size", "account_summary", "dark_mode", "page_size", "font_size", "access_control",
    "research_browse", "read_order", "get_order_status", "list_orders", "orders", "positions",
    "sizing_report", "binding_report", "promotion_history", "control_panel", "mode_info",
    "create_report", "submit_report", "cancel_job", "stand_up", "kill_process", "switch_mode",
    "book", "seat", "exit", "quotes", "symbol_info", "bars", "account_state", "list_accounts",
    "ping", "exit_plan_mode", "enter_plan_mode", "todo_write", "notebook_edit", "web_fetch",
]  # fmt: skip
PREFIXES = [[], ["get"], ["list"], ["paper"], ["mcp", "qmx"], ["mcp", "broker"]]
SUFFIXES = [[], ["2"], ["v2"], ["10"], ["status"]]
SEPARATORS = ["_", "-", " ", ".", "", "__"]


def styles(words: list[str]) -> Iterator[str]:
    for separator in SEPARATORS:
        yield separator.join(words)
        yield separator.join(word.upper() for word in words)
        yield separator.join(word.title() for word in words)
        yield separator.join([words[0], *(word.title() for word in words[1:])])
    yield "".join(word[:1].upper() + word[1:-1] + word[-1:].upper() for word in words)
    yield "".join(word.swapcase() for word in words)


def corpus(real: set[str]) -> Iterator[str]:
    seen: set[str] = set()
    for phrase, prefix, suffix in itertools.product(
        ACTS + BENIGN + sorted(real), PREFIXES, SUFFIXES
    ):
        words = [*prefix, *phrase.split("_"), *suffix]
        words = [word for word in words if word]
        for spelled in styles(words):
            for variant in (spelled, spelled + "2", f" {spelled} "):
                if variant not in seen:
                    seen.add(variant)
                    yield variant


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="origin/qma/hp7")
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--names", type=Path, nargs="*", default=[])
    args = parser.parse_args()
    from qma.core.barriers.descriptors import check_descriptor  # noqa: PLC0415

    base = base_check(args.base)
    real = harvested() | live_names() | extra_names(args.names)
    tool_doc: dict[str, Any] = {"annotations": {"readOnlyHint": True}}
    real_rows = [
        (name, verdict(base, name, tool_doc), verdict(check_descriptor, name, tool_doc))
        for name in sorted(real)
    ]
    print(f"real tool names: {len(real_rows)}")
    real_changed = [row for row in real_rows if row[1] != row[2]]
    print(f"real names refused at base: {sorted(n for n, b, _ in real_rows if b != 'allow')}")
    print(f"real names whose verdict changed: {real_changed}")

    counts: collections.Counter[str] = collections.Counter()
    a2r: list[str] = []
    r2a: list[str] = []
    sites = (
        lambda n: (n, {}),
        lambda n: ("read_bars", {"acts": [n]}),
        lambda n: ("read_bars", {"mcp": {"tool_name": n}}),
    )
    for index, spelled in enumerate(corpus(real)):
        for site, shape in enumerate(sites):
            if site and index % 5:
                continue
            name, metadata = shape(spelled)
            before, after = verdict(base, name, metadata), verdict(check_descriptor, name, metadata)
            counts["cases"] += 1
            if before == after:
                continue
            if before == "allow":
                counts["allowed->refused"] += 1
                a2r.append(spelled)
            elif after == "allow":
                counts["refused->allowed"] += 1
                r2a.append(spelled)
            else:
                counts["reason changed"] += 1
    print(f"corpus: {dict(counts)}")
    distinct = sorted(set(a2r))
    forms = sorted(
        {
            "_".join(
                word
                for word in re.split(
                    r"[\W_]+",
                    re.sub(
                        r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=[0-9])",
                        "_",
                        spelled,
                    ).casefold(),
                )
                if word
            )
            for spelled in distinct
        }
    )
    args.evidence.mkdir(parents=True, exist_ok=True)
    listing = args.evidence / "name-barrier-a2r.txt"
    listing.write_text("\n".join(repr(name) for name in distinct) + "\n", encoding="utf-8")
    print(f"allowed->refused distinct spellings: {len(distinct)} (all in {listing})")
    print(f"allowed->refused underscore forms ({len(forms)}):")
    for form in forms:
        print(f"  {form}")
    print(f"refused->allowed spellings: {sorted(set(r2a))}")
    ok = not r2a and not real_changed
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
