"""Strict runtime-wheel closure metadata and target validation.

This module intentionally uses only the Python standard library so the installer
can validate an offline wheel archive before it creates its destination venv.
"""

from __future__ import annotations

import ast
import email.parser
import hashlib
import itertools
import json
import platform
import re
import stat
import sys
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import cast

RUNTIME_CLASS = "qmx-runtime-wheel-closure-v1"
RUNTIME_FILENAME = "runtime-wheels.tar.gz"
RUNTIME_INVENTORY_FILENAME = "runtime-wheelhouse.json"
RUNTIME_TARGET: Mapping[str, object] = {
    "implementation": "CPython",
    "platform": "linux",
    "machine": "x86_64",
    "python_version": "3.14",
}
_HASH = re.compile(r"^sha256:([0-9a-f]{64})$")
_REQ = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[A-Za-z0-9_.+!-]+)"
    r"(?:\s*;\s*(?P<marker>.*))?$"
)


def normalize_name(value: str) -> str:
    return re.sub(r"[-_.]+", "_", value).lower()


def marker_environment(*, target: bool) -> dict[str, str]:
    if target:
        return {
            "python_version": "3.14",
            "python_full_version": "3.14.0",
            "implementation_name": "cpython",
            "implementation_version": "3.14.0",
            "platform_python_implementation": "CPython",
            "platform_machine": "x86_64",
            "platform_system": "Linux",
            "sys_platform": "linux",
            "os_name": "posix",
            "extra": "",
        }
    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "python_full_version": platform.python_version(),
        "implementation_name": sys.implementation.name,
        "implementation_version": platform.python_version(),
        "platform_python_implementation": platform.python_implementation(),
        "platform_machine": platform.machine().lower(),
        "platform_system": platform.system(),
        "sys_platform": sys.platform,
        "os_name": __import__("os").name,
        "extra": "",
    }


def _version_tuple(value: str) -> tuple[object, ...]:
    tokens = re.findall(r"\d+|[A-Za-z]+", value)
    return tuple(int(token) if token.isdigit() else token.casefold() for token in tokens)


def _compare(left: object, right: object, operator: ast.cmpop, variable: str | None) -> bool:
    if not isinstance(left, (str, int)) or not isinstance(right, (str, int)):
        raise ValueError("unsupported marker operands")
    if isinstance(left, str) and isinstance(right, str) and variable in {
        "python_version",
        "python_full_version",
        "implementation_version",
    }:
        lhs: object = _version_tuple(left)
        rhs: object = _version_tuple(right)
    else:
        lhs, rhs = left, right
    if isinstance(operator, ast.Eq):
        return lhs == rhs
    if isinstance(operator, ast.NotEq):
        return lhs != rhs
    if isinstance(operator, ast.In):
        return str(lhs) in str(rhs)
    if isinstance(operator, ast.NotIn):
        return str(lhs) not in str(rhs)
    if isinstance(operator, ast.Lt):
        return lhs < rhs  # type: ignore[operator]
    if isinstance(operator, ast.LtE):
        return lhs <= rhs  # type: ignore[operator]
    if isinstance(operator, ast.Gt):
        return lhs > rhs  # type: ignore[operator]
    if isinstance(operator, ast.GtE):
        return lhs >= rhs  # type: ignore[operator]
    raise ValueError("unsupported marker comparison")


def evaluate_marker(marker: str | None, environment: Mapping[str, str]) -> bool:
    if marker is None or not marker.strip():
        return True
    try:
        expression = ast.parse(marker, mode="eval").body
    except SyntaxError as error:
        raise ValueError("malformed environment marker") from error

    def visit(node: ast.AST) -> object:
        if isinstance(node, ast.BoolOp):
            values = [bool(visit(item)) for item in node.values]
            if isinstance(node.op, ast.And):
                return all(values)
            if isinstance(node.op, ast.Or):
                return any(values)
        if isinstance(node, ast.Name):
            if node.id not in environment:
                raise ValueError(f"unsupported target marker variable: {node.id}")
            return environment[node.id]
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Compare) and len(node.ops) == len(node.comparators) == 1:
            left = node.left
            right = node.comparators[0]
            variable = left.id if isinstance(left, ast.Name) else None
            left_value = visit(left)
            right_value = visit(right)
            if variable is None and isinstance(right, ast.Name):
                variable = right.id
            return _compare(left_value, right_value, node.ops[0], variable)
        raise ValueError("unsupported environment marker syntax")

    return bool(visit(expression))


def parse_locked_requirements(
    lock_texts: Iterable[str], *, environment: Mapping[str, str],
) -> dict[str, dict[str, object]]:
    """Parse exported uv locks and return marker-active exact package pins."""
    pending_rows: dict[str, list[dict[str, object]]] = {}
    for text in lock_texts:
        current: dict[str, object] | None = None
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            line = line.split("  #", 1)[0].rstrip()
            if line.endswith("\\"):
                line = line[:-1].rstrip()
            if not line:
                continue
            if line.startswith("--hash="):
                if current is None:
                    raise ValueError("lock hash is detached from a requirement")
                current_hashes = cast(list[str], current["hashes"])
                current_hashes.append(line.removeprefix("--hash="))
                continue
            if line.startswith(("--index-url ", "--extra-index-url ", "--trusted-host ")):
                current = None
                continue
            match = _REQ.fullmatch(line)
            if match is None:
                raise ValueError(f"unsupported locked requirement: {line}")
            name = normalize_name(match.group("name"))
            version = match.group("version")
            marker = match.group("marker")
            current = {"name": name, "version": version, "marker": marker, "hashes": []}
            if not evaluate_marker(marker, environment):
                continue
            # Continuation hash lines are consumed in the following iterations;
            # defer publication until the next requirement/end of this file.
            pending_rows.setdefault(name, []).append(current)
        # Hash continuation lines have now populated each pending row.
    active: dict[str, dict[str, object]] = {}
    for name, rows in pending_rows.items():
        versions = {cast(str, row["version"]) for row in rows}
        if len(versions) != 1:
            raise ValueError(f"active locks disagree on pinned version for {name}")
        hash_sets: list[set[str]] = []
        for row in rows:
            raw_hashes = row.get("hashes")
            if not isinstance(raw_hashes, list) or any(
                not isinstance(digest, str) for digest in cast(list[object], raw_hashes)
            ):
                raise ValueError(f"active lock hashes are malformed for {name}")
            hash_sets.append(set(cast(list[str], raw_hashes)))
        if any(not values for values in hash_sets):
            raise ValueError(f"active locked requirement has no hashes: {name}")
        permitted: set[str] = hash_sets[0]
        for values in hash_sets[1:]:
            permitted = permitted & values
        if not permitted:
            raise ValueError(f"active lock scopes have no common wheel hash: {name}")
        for digest in permitted:
            if _HASH.fullmatch(digest) is None:
                raise ValueError(f"malformed lock hash for {name}")
        active[name] = {
            "name": name,
            "version": next(iter(versions)),
            "hashes": sorted(permitted),
            "requirements": [
                {"marker": row["marker"], "hashes": sorted(set(cast(list[str], row["hashes"]))) }
                for row in rows
            ],
        }
    return active


def wheel_metadata(path: Path) -> dict[str, object]:
    """Validate wheel structure and return canonical distribution metadata."""
    filename = path.name
    parts = filename[:-4].split("-") if filename.endswith(".whl") else []
    if len(parts) < 5:
        raise ValueError(f"malformed wheel filename: {filename}")
    name, version = normalize_name(parts[0]), parts[1]
    filename_tag_parts = [field.split(".") for field in parts[-3:]]
    filename_tags = {
        "-".join(tag_parts) for tag_parts in itertools.product(*filename_tag_parts)
    }
    try:
        with zipfile.ZipFile(path) as wheel:
            bad_member = wheel.testzip()
            if bad_member is not None:
                raise ValueError(f"corrupt wheel member: {filename}")
            members = wheel.infolist()
            names = [item.filename for item in members]
            if len(names) != len(set(names)) or any(
                stat.S_ISLNK(item.external_attr >> 16) for item in members
            ):
                raise ValueError(f"wheel contains duplicate or linked members: {filename}")
            if any(
                member.startswith("/")
                or "\\" in member
                or PurePosixPath(member).as_posix() != member.rstrip("/")
                or any(part in {"", ".", ".."} for part in member.rstrip("/").split("/"))
                for member in names
            ):
                raise ValueError(f"unsafe wheel member: {filename}")
            dist_infos = {member.split("/", 1)[0] for member in names if ".dist-info/" in member}
            if len(dist_infos) != 1:
                raise ValueError(f"wheel metadata is missing or ambiguous: {filename}")
            root = next(iter(dist_infos))
            dist_info_name = root.removesuffix(".dist-info")
            dist_info_distribution, separator, dist_info_version = dist_info_name.rpartition("-")
            if (
                not separator
                or normalize_name(dist_info_distribution) != name
                or dist_info_version != version
            ):
                raise ValueError(f"wheel dist-info directory disagrees with filename: {filename}")
            required = {f"{root}/METADATA", f"{root}/WHEEL", f"{root}/RECORD"}
            if not required.issubset(names):
                raise ValueError(f"wheel metadata is incomplete: {filename}")
            metadata = email.parser.Parser().parsestr(wheel.read(f"{root}/METADATA").decode())
            wheel_text = wheel.read(f"{root}/WHEEL").decode()
    except (OSError, UnicodeError, zipfile.BadZipFile) as error:
        raise ValueError(f"malformed wheel: {filename}") from error
    wheel_tags = {
        line.partition(":")[2].strip()
        for line in wheel_text.splitlines()
        if line.startswith("Tag:")
    }
    if normalize_name(metadata.get("Name", "")) != name or metadata.get("Version") != version:
        raise ValueError(f"wheel filename and METADATA disagree: {filename}")
    if len(wheel_tags) != sum(line.startswith("Tag:") for line in wheel_text.splitlines()):
        raise ValueError(f"wheel WHEEL file repeats a tag: {filename}")
    # Require an exact WHEEL declaration for every expanded filename tag.
    # WHEEL may also list equivalent compatibility aliases not present in the
    # filename (for example manylinux policy aliases in published wheels).
    declared_filename_tags = wheel_tags.intersection(filename_tags)
    if not filename_tags or declared_filename_tags != filename_tags:
        raise ValueError(f"wheel filename and WHEEL tags disagree: {filename}")
    return {
        "distribution": name,
        "version": version,
        "tags": sorted(filename_tags),
    }


def _tag_compatible(tag: str, *, glibc: tuple[int, int]) -> bool:
    try:
        python_tag, abi_tag, platform_tag = tag.split("-")
    except ValueError:
        return False
    if platform_tag == "any":
        return abi_tag == "none" and any(
            item in {"py3", "py2.py3"} for item in python_tag.split(".")
        )
    if platform_tag == "manylinux2014_x86_64":
        platform_ok = glibc >= (2, 17)
    else:
        match = re.fullmatch(r"manylinux_(\d+)_(\d+)_x86_64", platform_tag)
        if match is None:
            return False
        platform_ok = glibc >= (int(match.group(1)), int(match.group(2)))
    if not platform_ok:
        return False
    if python_tag == "cp314" and abi_tag in {"cp314", "abi3"}:
        return True
    if python_tag.startswith("cp") and abi_tag == "abi3":
        try:
            return int(python_tag[2:]) <= 314
        except ValueError:
            return False
    return python_tag == "py3" and abi_tag == "none"


def tag_glibc_floor(tag: str) -> tuple[int, int] | None:
    """Return the minimum glibc encoded by a compatible Linux wheel tag."""
    try:
        python_tag, abi_tag, platform_tag = tag.split("-")
    except ValueError:
        return None
    python_ok = (
        python_tag == "cp314" and abi_tag in {"cp314", "abi3"}
    ) or (
        python_tag.startswith("cp")
        and abi_tag == "abi3"
        and python_tag[2:].isdigit()
        and int(python_tag[2:]) <= 314
    ) or (python_tag in {"py3", "py2.py3"} and abi_tag == "none")
    if not python_ok:
        return None
    if platform_tag == "any":
        return (2, 17)
    if platform_tag == "manylinux2014_x86_64":
        return (2, 17)
    match = re.fullmatch(r"manylinux_(\d+)_(\d+)_x86_64", platform_tag)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def validate_runtime_target(
    *, target: Mapping[str, object], running: bool = False
) -> tuple[int, int]:
    expected_keys = set(RUNTIME_TARGET) | {"glibc_min"}
    if set(target) != expected_keys or any(
        target.get(key) != value for key, value in RUNTIME_TARGET.items()
    ):
        raise ValueError(
            "runtime wheel archive declares the supported Linux CPython 3.14 x86_64 target"
        )
    glibc_min = target.get("glibc_min")
    if not isinstance(glibc_min, str) or re.fullmatch(r"\d+\.\d+", glibc_min) is None:
        raise ValueError("runtime wheel inventory declares a valid minimum glibc version")
    if running:
        if sys.version_info[:2] != (3, 14) or platform.python_implementation() != "CPython":
            raise ValueError("runtime wheel closure requires CPython 3.14")
        if sys.platform != "linux" or platform.machine().lower() not in {"x86_64", "amd64"}:
            raise ValueError(
                "runtime wheel closure is for Linux x86_64; use the explicit online mode"
            )
        libc, version = platform.libc_ver()
        if libc != "glibc":
            raise ValueError("runtime wheel closure requires glibc")
        try:
            glibc = tuple(int(part) for part in version.split(".")[:2])
        except ValueError as error:
            raise ValueError("runtime target glibc version is unreadable") from error
        if len(glibc) != 2:
            raise ValueError("runtime target glibc version is unreadable")
        minimum = tuple(int(part) for part in glibc_min.split("."))
        if glibc < minimum:
            raise ValueError("runtime wheel closure requires a newer glibc than this host")
        return cast(tuple[int, int], glibc)
    parts = tuple(int(part) for part in glibc_min.split("."))
    if len(parts) != 2:
        raise ValueError("runtime wheel inventory has malformed glibc version")
    return parts[0], parts[1]


def validate_inventory_requirements(
    *, inventory: Mapping[str, object], lock_text: str, glibc: tuple[int, int]
) -> dict[str, dict[str, object]]:
    requirements = parse_locked_requirements(
        (lock_text,), environment=marker_environment(target=True)
    )
    raw_requirements = inventory.get("requirements")
    if not isinstance(raw_requirements, list) or cast(list[object], raw_requirements) != [
        {"name": name, **requirements[name]} for name in sorted(requirements)
    ]:
        raise ValueError("runtime wheel inventory requirements do not match active locked pins")
    raw_wheels = inventory.get("wheels")
    if not isinstance(raw_wheels, list):
        raise ValueError("runtime wheel inventory has no wheel list")
    wheels: dict[str, dict[str, object]] = {}
    filenames: set[str] = set()
    for raw in cast(list[object], raw_wheels):
        if not isinstance(raw, Mapping):
            raise ValueError("runtime wheel inventory entries are objects")
        entry = cast(Mapping[str, object], raw)
        filename = entry.get("filename")
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError("runtime wheel inventory filenames are local wheel names")
        if filename in filenames:
            raise ValueError(f"duplicate runtime wheel: {filename}")
        filenames.add(filename)
        distribution = entry.get("distribution")
        version = entry.get("version")
        digest = entry.get("sha256")
        if not all(isinstance(value, str) for value in (distribution, version, digest)):
            raise ValueError(f"runtime wheel inventory metadata is incomplete: {filename}")
        if _HASH.fullmatch(f"sha256:{digest}") is None:
            raise ValueError(f"runtime wheel checksum is malformed: {filename}")
        name = normalize_name(cast(str, distribution))
        if name in wheels:
            raise ValueError(f"duplicate runtime wheel distribution: {name}")
        requirement = requirements.get(name)
        if requirement is None or requirement["version"] != version:
            raise ValueError(f"runtime wheel is not an active locked package: {filename}")
        allowed_hashes = cast(list[str], requirement["hashes"])
        if f"sha256:{digest}" not in allowed_hashes:
            raise ValueError(f"runtime wheel SHA256 is not allowed by its package lock: {filename}")
        tags_value = entry.get("tags")
        if (
            not isinstance(tags_value, list)
            or not tags_value
            or any(not isinstance(tag, str) for tag in cast(list[object], tags_value))
        ):
            raise ValueError(f"runtime wheel tags are malformed: {filename}")
        tags = cast(list[str], tags_value)
        compatible = [tag for tag in tags if _tag_compatible(tag, glibc=glibc)]
        if not compatible:
            raise ValueError(f"runtime wheel is incompatible with Linux CPython 3.14: {filename}")
        wheels[name] = dict(entry)
    missing = sorted(set(requirements) - set(wheels))
    if missing:
        raise ValueError(f"active locked runtime wheel is missing: {missing[0]}")
    if set(wheels) != set(requirements):
        raise ValueError("runtime wheel inventory is not the exact active lock closure")
    return wheels


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_inventory_bytes(inventory: Mapping[str, object]) -> bytes:
    return (json.dumps(inventory, sort_keys=True, indent=2) + "\n").encode()
