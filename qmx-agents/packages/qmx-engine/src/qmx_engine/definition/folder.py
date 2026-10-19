"""A workflow is a folder (AD-2): `definition.json` plus the files its refs name.

A ref is any `*_ref` parameter, plus a `script` or `source` parameter that is not a URL: those
two name files a node executes, so they must be hashed like a prompt, or an edited script would
keep the old version's "tested" mark (AD-11). A `subworkflow` node's `workflow` parameter names a
block folder inside this one: every file under it is carried as a ref of its own path, so a bundle
holds the child and its bytes are hashed (AD-5, B-76).
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Final, NamedTuple

from pydantic import JsonValue
from qmx_ledger.journal import fingerprint

DEFINITION: Final = "definition.json"
HASHED_FIELDS: Final = ("nodes", "connections", "settings", "inputs", "outputs")
FILE_PARAMETERS: Final = frozenset({"script", "source"})


class Problem(NamedTuple):
    code: str
    path: str
    message: str


class WorkflowFolder(NamedTuple):
    root: Path
    document: dict[str, JsonValue] | None
    refs: Mapping[str, bytes]
    """Ref text as written in the document, and each block file's folder-relative path, to the
    bytes of the file it names."""
    problems: list[Problem]


def refs_in(document: Mapping[str, JsonValue]) -> Iterator[tuple[str, str]]:
    """Every `(path, ref)` in the document's node parameters, in document order."""
    nodes = document.get("nodes")
    if not isinstance(nodes, list):
        return
    for index, node in enumerate(nodes):
        parameters = node.get("parameters") if isinstance(node, dict) else None
        if isinstance(parameters, dict):
            yield from _refs(parameters, f"nodes[{index}].parameters")


def _refs(value: JsonValue, path: str) -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for key, item in value.items():
            here = f"{path}.{key}"
            if isinstance(item, str) and (
                key.endswith("_ref") or (key in FILE_PARAMETERS and "://" not in item)
            ):
                yield here, item
            else:
                yield from _refs(item, here)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _refs(item, f"{path}[{index}]")


def blocks_in(document: Mapping[str, JsonValue]) -> Iterator[tuple[str, str]]:
    """Every `(path, folder)` a `subworkflow` node names as its child, in document order."""
    nodes = document.get("nodes")
    if not isinstance(nodes, list):
        return
    for index, node in enumerate(nodes):
        if not isinstance(node, dict) or node.get("type") != "subworkflow":
            continue
        parameters = node.get("parameters")
        block = parameters.get("workflow") if isinstance(parameters, dict) else None
        if isinstance(block, str):
            yield f"nodes[{index}].parameters.workflow", PurePosixPath(block).as_posix()


def escapes(ref: str) -> bool:
    pure = PurePosixPath(ref)
    return pure.is_absolute() or ".." in pure.parts or pure.as_posix() in ("", ".")


def load(root: Path) -> WorkflowFolder:
    definition = root / DEFINITION
    try:
        document: JsonValue = json.loads(definition.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return WorkflowFolder(root, None, {}, [Problem("definition_missing", "", str(definition))])
    except json.JSONDecodeError as error:
        return WorkflowFolder(root, None, {}, [Problem("json_invalid", "", str(error))])
    if not isinstance(document, dict):
        return WorkflowFolder(root, None, {}, [Problem("json_invalid", "", "not a JSON object")])
    base = root.resolve()
    refs: dict[str, bytes] = {}
    problems: list[Problem] = []
    for path, ref in refs_in(document):
        target = (base / ref).resolve()
        if PurePosixPath(ref).is_absolute() or not target.is_relative_to(base):
            problems.append(Problem("ref_escapes_folder", path, "the ref leaves the folder"))
        elif not target.is_file():
            problems.append(Problem("ref_missing", path, "the ref names no file in the folder"))
        else:
            refs[ref] = target.read_bytes()
    for path, block in blocks_in(document):
        target = (base / block).resolve()
        if escapes(block) or not target.is_relative_to(base) or target == base:
            problems.append(Problem("ref_escapes_folder", path, "the block leaves the folder"))
        elif not (target / DEFINITION).is_file():
            problems.append(Problem("ref_missing", path, "the block holds no definition.json"))
        else:
            for file in sorted(p for p in target.rglob("*") if p.is_file()):
                refs[file.relative_to(base).as_posix()] = file.read_bytes()
    return WorkflowFolder(root, document, refs, problems)


def content_hash(folder: WorkflowFolder) -> str:
    """`sha256:<hex>` over the hashed fields, node positions left out, plus every ref file's
    bytes. `meta` and `position` are layout and authorship, so moving a node changes nothing,
    except `meta.needs` and `pinData`, which change what a test run proves (L-26, L-75); each is
    hashed only when present, so a document without them keeps the hash it had. A variant's
    patches are not hashed: only its resolved snapshot has a hash (AD-11)."""
    document, refs = folder.document or {}, folder.refs
    if document.get("extends") is not None:
        raise ValueError("an unresolved variant has no content hash; resolve it first")
    nodes = document.get("nodes")
    hashed: dict[str, JsonValue] = {name: document.get(name) for name in HASHED_FIELDS}
    if document.get("pinData") is not None:
        hashed["pinData"] = document["pinData"]
    meta = document.get("meta")
    if isinstance(meta, dict) and meta.get("needs"):
        hashed["needs"] = meta["needs"]
    if isinstance(nodes, list):
        hashed["nodes"] = [
            {k: v for k, v in node.items() if k != "position"} if isinstance(node, dict) else node
            for node in nodes
        ]
    hashed["refs"] = {ref: sha256(data).hexdigest() for ref, data in sorted(refs.items())}
    return f"sha256:{fingerprint(hashed)}"
