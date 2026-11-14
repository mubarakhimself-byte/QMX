"""PROGRAM.yaml, version 2: the program's one index. Grammar and example in FACTORY-DESIGN 11.4.

The parser reads a small YAML subset and nothing else, so a planner's slip fails loudly with its line
number instead of being read as something it did not mean: two-space indentation; `key: scalar`;
`key:` followed by an indented mapping or a `- ` list; inline lists `[a, b]` and inline mappings
`{k: v}`; scalars are `null`, `yes`/`no`/`true`/`false`, integers, double-quoted strings, or bare words
up to a ` #` comment. No anchors, no multi-line strings, no tabs.

A version-1 file (no `kind`, a `scope_gate:` line) is read by `legacy` into the same `Index`.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
import re

from ship.layout import Program

KINDS = ("feature", "audit", "sweep", "fix", "wire")
GATES_BY_KIND = {
    "feature": ("cut", "plan", "go"),
    "wire": ("cut", "plan", "go"),
    "audit": ("intent", "verdicts", "go"),
    "sweep": ("go",),
    "fix": ("go",),
}
KEY = r"[A-Za-z_][A-Za-z0-9_.-]*"
KEY_LINE = re.compile(rf"^(?P<key>{KEY}):(?:[ ]+(?P<value>.*))?$")
INT = re.compile(r"^-?[0-9]+$")
BARE_SAFE = re.compile(r"^[A-Za-z0-9_./@+-][A-Za-z0-9_./@:+-]*$")


class ProgramError(Exception):
    def __init__(self, line_no: int, message: str):
        super().__init__(f"PROGRAM.yaml line {line_no}: {message}" if line_no else f"PROGRAM.yaml: {message}")
        self.line_no = line_no
        self.message = message


@dataclasses.dataclass
class _Line:
    no: int
    indent: int
    text: str


def _strip_comment(text: str) -> str:
    """Drop a ` #` comment that sits outside double quotes."""
    quoted = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and quoted:
            i += 2
            continue
        if ch == '"':
            quoted = not quoted
        elif ch == "#" and not quoted and (i == 0 or text[i - 1] == " "):
            return text[:i].rstrip()
        i += 1
    return text.rstrip()


def _lines(text: str) -> list[_Line]:
    out = []
    for no, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw:
            raise ProgramError(no, "a tab; indent with two spaces")
        body = _strip_comment(raw)
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        if indent % 2:
            raise ProgramError(no, f"indentation of {indent} spaces; use steps of two")
        out.append(_Line(no, indent, body.strip()))
    return out


def parse(text: str) -> dict:
    """The mapping a PROGRAM.yaml holds. ProgramError names the first line outside the subset."""
    lines = _lines(text)
    if not lines:
        return {}
    if lines[0].indent:
        raise ProgramError(lines[0].no, "the file must start at column 0")
    value, i = _block(lines, 0, 0)
    if i < len(lines):
        raise ProgramError(lines[i].no, "unexpected indentation")
    if not isinstance(value, dict):
        raise ProgramError(lines[0].no, "the file must be a mapping")
    return value


def _is_item(line: _Line) -> bool:
    return line.text == "-" or line.text.startswith("- ")


def _block(lines: list[_Line], i: int, indent: int) -> tuple[object, int]:
    if _is_item(lines[i]):
        return _list(lines, i, indent)
    return _mapping(lines, i, indent)


def _mapping(lines: list[_Line], i: int, indent: int) -> tuple[dict, int]:
    out: dict = {}
    while i < len(lines) and lines[i].indent == indent and not _is_item(lines[i]):
        line = lines[i]
        m = KEY_LINE.match(line.text)
        if not m:
            raise ProgramError(line.no, f"want `key: value`, got {line.text!r}")
        key = m.group("key")
        if key in out:
            raise ProgramError(line.no, f"{key} given twice")
        i += 1
        if m.group("value") is not None:
            out[key] = _scalar_or_flow(m.group("value"), line.no)
        elif i < len(lines) and lines[i].indent == indent + 2:
            out[key], i = _block(lines, i, indent + 2)
        elif i < len(lines) and lines[i].indent == indent and _is_item(lines[i]):
            out[key], i = _list(lines, i, indent)
        else:
            out[key] = None
        if i < len(lines) and lines[i].indent > indent:
            raise ProgramError(lines[i].no, "unexpected indentation")
    return out, i


def _list(lines: list[_Line], i: int, indent: int) -> tuple[list, int]:
    out: list = []
    while i < len(lines) and lines[i].indent == indent and _is_item(lines[i]):
        line = lines[i]
        rest = line.text[1:].strip()
        if not rest:
            i += 1
            if i < len(lines) and lines[i].indent == indent + 2:
                value, i = _block(lines, i, indent + 2)
                out.append(value)
            else:
                out.append(None)
        elif KEY_LINE.match(rest) and not rest.startswith(("{", "[", '"')):
            lines[i] = _Line(line.no, indent + 2, rest)  # "- key: v" opens a mapping one step in
            value, i = _mapping(lines, i, indent + 2)
            out.append(value)
        else:
            out.append(_scalar_or_flow(rest, line.no))
            i += 1
        if i < len(lines) and lines[i].indent > indent:
            raise ProgramError(lines[i].no, "unexpected indentation")
    return out, i


def _scalar_or_flow(text: str, no: int) -> object:
    value, end = _flow(text, 0, no)
    if text[end:].strip():
        raise ProgramError(no, f"unexpected text after the value: {text[end:].strip()!r}")
    return value


def _flow(text: str, i: int, no: int, inside: bool = False) -> tuple[object, int]:
    while i < len(text) and text[i] == " ":
        i += 1
    if i >= len(text):
        raise ProgramError(no, "a value is missing")
    ch = text[i]
    if ch == "[":
        return _flow_seq(text, i + 1, no)
    if ch == "{":
        return _flow_map(text, i + 1, no)
    if ch == '"':
        return _quoted(text, i, no)
    if ch in "|>":
        raise ProgramError(no, "multi-line strings are not in the subset; write one line in double quotes")
    if ch in "&*!":
        raise ProgramError(no, "anchors, aliases and tags are not in the subset")
    if ch == "'":
        raise ProgramError(no, "single-quoted strings are not in the subset; use double quotes")
    stop = ",]}" if inside else ""
    j = i
    while j < len(text) and text[j] not in stop:
        j += 1
    word = text[i:j].strip()
    if not word:
        raise ProgramError(no, "a value is missing")
    return _word(word), j


def _word(word: str) -> object:
    low = word.lower()
    if low in ("null", "~"):
        return None
    if low in ("yes", "true"):
        return True
    if low in ("no", "false"):
        return False
    if INT.match(word):
        return int(word)
    return word


def _quoted(text: str, i: int, no: int) -> tuple[str, int]:
    out = []
    j = i + 1
    while j < len(text):
        ch = text[j]
        if ch == "\\" and j + 1 < len(text):
            out.append({"n": "\n", "t": "\t"}.get(text[j + 1], text[j + 1]))
            j += 2
            continue
        if ch == '"':
            return "".join(out), j + 1
        out.append(ch)
        j += 1
    raise ProgramError(no, "a double-quoted string does not end on its line (multi-line strings are not in the subset)")


def _skip(text: str, i: int) -> int:
    while i < len(text) and text[i] == " ":
        i += 1
    return i


def _flow_seq(text: str, i: int, no: int) -> tuple[list, int]:
    out: list = []
    i = _skip(text, i)
    if i < len(text) and text[i] == "]":
        return out, i + 1
    while True:
        value, i = _flow(text, i, no, inside=True)
        out.append(value)
        i = _skip(text, i)
        if i < len(text) and text[i] == ",":
            i += 1
            continue
        if i < len(text) and text[i] == "]":
            return out, i + 1
        raise ProgramError(no, "an inline list is not closed with ]")


def _flow_map(text: str, i: int, no: int) -> tuple[dict, int]:
    out: dict = {}
    i = _skip(text, i)
    if i < len(text) and text[i] == "}":
        return out, i + 1
    while True:
        m = re.compile(rf"({KEY}):[ ]").match(text, i)
        if not m:
            raise ProgramError(no, f"want `key: value` inside {{...}} at {text[i:i + 20]!r}")
        if m.group(1) in out:
            raise ProgramError(no, f"{m.group(1)} given twice")
        value, i = _flow(text, m.end(), no, inside=True)
        out[m.group(1)] = value
        i = _skip(text, i)
        if i < len(text) and text[i] == ",":
            i = _skip(text, i + 1)
            continue
        if i < len(text) and text[i] == "}":
            return out, i + 1
        raise ProgramError(no, "an inline mapping is not closed with }")


@dataclasses.dataclass
class Stop:
    id: str
    tier: str | None = None
    done_when: str | None = None
    handoff: str | None = None
    merged: str | None = None  # version 1 only: the target sha MERGE wrote


@dataclasses.dataclass
class Index:
    program: str | None = None
    project: str | None = None
    kind: str = "feature"
    parent: str | None = None
    area: list = dataclasses.field(default_factory=list)
    inputs: dict = dataclasses.field(default_factory=dict)
    build_branch: str | None = None
    parent_tip: str | None = None
    core_sentence: str | None = None
    budget: dict = dataclasses.field(default_factory=dict)
    gates: dict = dataclasses.field(default_factory=dict)
    stop_points: list = dataclasses.field(default_factory=list)
    chains: list = dataclasses.field(default_factory=list)
    abandoned: object = None
    version: int = 2

    def gate(self, name: str) -> dict | None:
        value = self.gates.get(name)
        return value if isinstance(value, dict) else None

    @property
    def stops(self) -> list[Stop]:
        out = []
        for item in self.stop_points:
            if not isinstance(item, dict) or item.get("id") is None:
                continue
            out.append(Stop(id=str(item["id"]), tier=_opt(item.get("tier")), done_when=_opt(item.get("done_when")),
                            handoff=_opt(item.get("handoff")), merged=_opt(item.get("merged"))))
        return out

    def last_gate_before_go(self) -> str | None:
        return {"feature": "plan", "wire": "plan", "audit": "verdicts"}.get(self.kind)


def _opt(value: object) -> str | None:
    return None if value is None else str(value)


def from_dict(raw: dict) -> Index:
    """The Index of a parsed version-2 file. An unknown kind is an error."""
    kind = raw.get("kind") or "feature"
    if kind not in KINDS:
        raise ProgramError(0, f"kind {kind!r}; want one of {list(KINDS)}")
    gates = raw.get("gates") or {}
    if not isinstance(gates, dict):
        raise ProgramError(0, "gates must be a mapping")
    return Index(
        program=_opt(raw.get("program")), project=_opt(raw.get("project")), kind=kind,
        parent=_opt(raw.get("parent")), area=list(raw.get("area") or []), inputs=dict(raw.get("inputs") or {}),
        build_branch=_opt(raw.get("build_branch")), parent_tip=_opt(raw.get("parent_tip")),
        core_sentence=_opt(raw.get("core_sentence")), budget=dict(raw.get("budget") or {}), gates=gates,
        stop_points=list(raw.get("stop_points") or []), chains=list(raw.get("chains") or []),
        abandoned=raw.get("abandoned"),
    )


def is_version_1(text: str) -> bool:
    return not re.search(r"^kind:", text, re.M) and bool(re.search(r"^scope_gate:", text, re.M))


def legacy(text: str, folder_name: str = "") -> Index:
    """A version-1 PROGRAM.yaml read the way phase_state.py read it: the header lines and the
    stop points. `scope_gate` becomes `gates.go`; a folder named `<parent>-fix-<X>` is kind `fix`."""
    head = text.split("\nfiles:")[0]

    def value(key: str) -> str | None:
        m = re.search(rf"^{key}:[ ]*(.*?)\s*(?:[ ]#.*)?$", head, re.M)
        if not m or m.group(1) in ("", "null", "~"):
            return None
        return m.group(1)

    scope = value("scope_gate")
    go = None
    if scope:
        try:
            go = _scalar_or_flow(scope, 0)
        except ProgramError:
            go = {"source": scope}
        if not isinstance(go, dict):
            go = {"source": str(go)}
    fix = re.match(r"(.+)-fix-([A-Za-z0-9]+)$", folder_name)
    block = text.split("\nstop_points:", 1)[1].split("\nfiles:")[0] if "\nstop_points:" in text else ""
    stops = []
    for m in re.finditer(r"^\s*-\s*id:\s*(\S+)(.*?)(?=^\s*-\s*id:|\Z)", block, re.M | re.S):
        merged = re.search(r"merged:\s*(\S+)", m.group(2))
        done = re.search(r"done_when:\s*(.*)", m.group(2))
        sha = merged.group(1) if merged and merged.group(1) not in ("null", "~") else None
        stops.append({"id": m.group(1), "merged": sha, "done_when": done.group(1).strip() if done else None})
    return Index(program=value("program"), kind="fix" if fix else "feature", parent=fix.group(1) if fix else None,
                 build_branch=value("build_branch"), parent_tip=value("parent_tip"), gates={"go": go},
                 stop_points=stops, version=1)


def load(program: Program) -> Index:
    """The program's index. A version-1 file goes through `legacy`."""
    text = program.project_file.read_text("utf-8")
    if is_version_1(text):
        return legacy(text, program.dir.name)
    return from_dict(parse(text))


def _render(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "yes"
    if value is False:
        return "no"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {_render(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(_render(v) for v in value) + "]"
    text = str(value)
    if BARE_SAFE.match(text) and _word(text) == text:
        return text
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def set_gate(program: Program, name: str, by: str, source: str, advance: bool, at: str | None = None) -> str:
    """Write one gate into PROGRAM.yaml. Only the `gates:` block changes; every other byte stays.
    Refuses a gate the program's kind does not have. Returns the new gate line."""
    path = program.project_file
    text = path.read_bytes().decode("utf-8")  # bytes, so a CRLF file keeps its line ends
    if is_version_1(text):
        raise ProgramError(0, "a version-1 PROGRAM.yaml; gates are written to version 2 only")
    index = from_dict(parse(text))
    allowed = GATES_BY_KIND[index.kind]
    if name not in allowed:
        raise ProgramError(0, f"kind {index.kind} has no gate {name!r}; its gates are {list(allowed)}")
    at = at or dt.datetime.now(dt.timezone.utc).date().isoformat()
    line = (f"  {name}: {{by: {_render(by)}, at: {_render(at)}, source: {_quote(source)}, "
            f"advance: {_render(bool(advance))}}}")
    newline = "\r\n" if "\r\n" in text else "\n"
    rows = text.split(newline)
    top = [i for i, row in enumerate(rows) if re.match(r"^gates:(\s|$)", row)]
    if not top:
        raise ProgramError(0, "no gates: line")
    start = top[0]
    end = start + 1  # one past the block: indented lines, with blank or comment lines only between them
    j = start + 1
    while j < len(rows):
        row = rows[j]
        if row.startswith(" ") and row.strip() and not row.strip().startswith("#"):
            end = j + 1
        elif row.strip() and not row.startswith(" ") and not row.startswith("#"):
            break
        j += 1
    if _strip_comment(rows[start][len("gates:"):]).strip():  # `gates: {...}` or `gates: null` on one line
        gates = {**index.gates, name: None}
        block = ["gates:"] + [line if k == name else f"  {k}: {_render(v)}" for k, v in gates.items()]
    else:
        block = rows[start:end]
        found = None
        for k, row in enumerate(block[1:], start=1):
            if re.match(rf"^  {re.escape(name)}:(\s|$)", row):
                found = k
                break
        if found is None:
            block = block + [line]
        else:
            stop = found + 1
            while stop < len(block) and block[stop].startswith("    "):
                stop += 1
            block = block[:found] + [line] + block[stop:]
    new = newline.join(rows[:start] + block + rows[end:])
    tmp = path.with_suffix(".yaml.tmp")
    tmp.write_bytes(new.encode("utf-8"))
    os.replace(tmp, path)
    log_gate(program, name, from_dict(parse(new)).gates.get(name))
    return line.strip()


# ---- the gates log (D-L22) --------------------------------------------------------------------------
# PROGRAM.yaml is a plan file planner roles may write, so a gate there proves nothing by itself. Only
# `set_gate` (`ship gate`, the conveyor's Go, the kit's fix programs) appends to `.kit/gates.log`, which no
# worker role may write; arm, phase and merge refuse while the YAML's gates differ from the log.


def _gate_value(value: object) -> dict | None:
    if not isinstance(value, dict):
        return None
    return {k: (v if isinstance(v, bool) or v is None else str(v)) for k, v in sorted(value.items())}


def log_gate(program: Program, name: str, value: object) -> None:
    """Append one gate, as the YAML now holds it, to `.kit/gates.log`."""
    path = program.gates_log
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {"gate": name, "value": _gate_value(value),
           "at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")}
    with open(path, "a", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(row, sort_keys=True) + "\n")


def logged_gates(program: Program) -> dict[str, dict]:
    """The log's last word on each gate (a gate set back to null drops out)."""
    out: dict[str, dict] = {}
    try:
        lines = program.gates_log.read_text("utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or not row.get("gate"):
            continue
        value = _gate_value(row.get("value"))
        if value is None:
            out.pop(str(row["gate"]), None)
        else:
            out[str(row["gate"])] = value
    return out


def gates_problem(program: Program, index: "Index | None" = None) -> str | None:
    """None when every gate PROGRAM.yaml holds is the one `ship gate` wrote, else why not."""
    index = index if index is not None else load(program)
    yaml = {k: _gate_value(v) for k, v in index.gates.items() if _gate_value(v) is not None}
    logged = logged_gates(program)
    for name in sorted(set(yaml) | set(logged)):
        if yaml.get(name) != logged.get(name):
            return (f"gates.{name} in PROGRAM.yaml is {yaml.get(name)} but ship gate wrote {logged.get(name)}; "
                    "only `ship gate` sets a gate")
    return None


def _quote(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
