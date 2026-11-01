"""What every QMB job shares: its run folder, the request the core wrote there, and its leave.

The core lays a run out before the job starts (Part B AD-202): ``in/request.json`` is the run
request with the core's fields filled, and ``in/`` holds the unit, its pinned blocks, its
markets' instrument records and bars. A job writes only under ``out/`` and leaves one
``qmx.qmb.result-bundle/1`` under ``provides.backtest-result``. A domain failure is a ``failed``
bundle, never a raise, because the breaker counts every raise (AD-201, AD-204).
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, cast

from qmf.core import fingerprint_bytes
from qmf.core.refusal import TypedRefusal

OUTPUT: Final = "backtest-result"
CONTRACT: Final = "qmb/1"
MANIFEST: Final = cast(
    "dict[str, object]", tomllib.loads((Path(__file__).with_name("app.toml")).read_text("utf-8"))
)
TESTER: Final[dict[str, str]] = {
    "app": str(MANIFEST["id"]),
    "version": str(MANIFEST["version"]),
    "contract": CONTRACT,
}

type Document = dict[str, object]


def folder(inputs: Mapping[str, object]) -> Path:
    """The run's folder, as the supervisor names it inside the app's volume."""
    return Path(str(inputs["run_folder"]))


def request(run: Path) -> Document | str:
    """The run request the core wrote, or why there is none."""
    try:
        found: object = json.loads((run / "in" / "request.json").read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return f"the run folder holds no run request the core wrote: {error}"
    return cast("Document", found) if isinstance(found, dict) else "the run request is an object"


def unit_body(asked: Mapping[str, object], run_id: str) -> Document:
    """The fields QMB's unit runner reads, from the core's run request."""
    return {
        "run_id": run_id,
        "compiled_fingerprint": asked.get("compiled_fp"),
        "equity": asked.get("equity"),
        "execution_target": asked.get("execution_target"),
        "motion": asked.get("motion", "on"),
    }


def reason(refusal: TypedRefusal) -> str:
    context = refusal.context
    text = str(context.get("reason", refusal.category.value))
    field = context.get("field")
    return f"{field}: {text}" if field else text


def json_bytes(body: object) -> bytes:
    """The one serial form of a bundle file, so a rerun's file has the same fingerprint."""
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def write(run: Path, name: str, body: object) -> Document:
    """One bundle file under ``out/``, named by its slot's path and its fingerprint."""
    data = json_bytes(body)
    path = run / "out" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {
        "slot": "report",
        "path": f"out/{name}",
        "fp": fingerprint_bytes(data).value,
        "bytes": len(data),
    }


def leave(
    run_id: str,
    status: str,
    *,
    why: str | None = None,
    measures: Mapping[str, object] | None = None,
    labels: Mapping[str, object] | None = None,
    files: Sequence[Mapping[str, object]] = (),
    versions: Mapping[str, object] | None = None,
) -> Document:
    bundle: Document = {
        "schema_version": 1,
        "run_id": run_id,
        "status": status,
        "tester": dict(TESTER),
        "files": [dict(file) for file in files],
    }
    optional = {"reason": why, "measures": measures, "labels": labels, "versions": versions}
    bundle.update({name: dict(value) if isinstance(value, Mapping) else value
                   for name, value in optional.items() if value is not None})
    return {"output": OUTPUT, "data": bundle}


def failed(run_id: str, why: str) -> Document:
    """A domain failure: the run lands as failed with its reason, and nothing raised."""
    return leave(run_id, "failed", why=why)
