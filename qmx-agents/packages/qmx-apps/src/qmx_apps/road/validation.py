"""Run real app tests and MCP probes in disposable P12 volumes."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pydantic import JsonValue
from qmx_ledger.journal import fingerprint

from qmx_apps.backup import snapshot
from qmx_apps.errors import AppError, Document
from qmx_apps.road.models import Proof, Stage, json_document
from qmx_apps.volume import Volume, VolumeLease
from qmx_apps.windows_job import WindowsJob

if TYPE_CHECKING:
    from qmx_apps.manifest import Definition
    from qmx_apps.supervisor import Supervisor


def validate(owner: Supervisor, image: Definition, stage: Stage) -> tuple[Document, Document]:
    from qmx_apps.supervisor import Instance  # noqa: PLC0415

    app_id = image.manifest.id
    with tempfile.TemporaryDirectory(prefix="qmx-proof-") as temporary:
        home = Path(temporary)
        isolated = type(owner)(home, secret_getter=owner.secret_getter, proof_mode=stage)
        volume = Volume(home, app_id)
        volume.create(agents=bool(image.manifest.entrypoints.agents))
        source = Volume(owner.home, app_id)
        snapshot(source, volume.root)
        # Share the immutable image and locked venv, never the live volume/catalog.
        isolated.environments = owner.environments
        isolated.select_image(image)
        try:
            if stage == "tests":
                lease = VolumeLease(home, app_id)
                instance = Instance(image, volume, lease, tier=isolated.tier)
                job_name = f"Local\\qmx-tests-{instance.id}"
                job = (
                    WindowsJob(job_name, image.manifest.budget)
                    if sys.platform == "win32" and isolated.tier == "T1"
                    else None
                )
                try:
                    environment = isolated.environment(instance)
                    config = isolated.configuration(instance, job_name, environment)
                    config["tests"] = True
                    transport = isolated.transport(instance, config, environment)
                    result = subprocess.run(
                        [transport.command, *transport.args],
                        env=transport.env,
                        cwd=transport.cwd,
                        capture_output=True,
                        timeout=min(300, image.manifest.budget.cpu_seconds + 45),
                        check=False,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                    )
                    report_path = volume.root / "data/test-result.json"
                    report = json_document(report_path.read_bytes()) if report_path.exists() else {}
                    report["exit_code"] = result.returncode
                    report["passed"] = (
                        result.returncode == 0
                        and report.get("passed") is True
                        and bool(report.get("tests_run"))
                    )
                    return {"suite": "unittest discover", "source": "recorded"}, report
                except subprocess.TimeoutExpired as error:
                    raise AppError(
                        "tests_failed", "App tests exceeded the bounded test duration.", 422
                    ) from error
                finally:
                    isolated.kill(instance)
                    if job:
                        job.close()
                    lease.close()
            path = image.root / "proofs" / f"{stage}.json"
            if not path.is_file() or path.stat().st_size > 65536:
                raise AppError(
                    "proof_required",
                    "Provide a bounded proofs/<stage>.json with real MCP cases.",
                    422,
                )
            try:
                proof = Proof.model_validate(json_document(path.read_bytes()))
            except ValueError as error:
                raise AppError(
                    "invalid_proof", "Correct the closed, bounded MCP proof fields.", 422
                ) from error
            expected_source = "recorded" if stage == "sandbox" else "live"
            if proof.source != expected_source:
                raise AppError(
                    "wrong_source", "Sandbox uses recorded data; shadow uses live data.", 422
                )
            isolated.start(app_id)
            tools = cast(list[Document], isolated.registry()[0]["tools"])
            results: list[Document] = []
            for case in proof.cases:
                tool = next((tool for tool in tools if tool["name"] == case.tool), None)
                annotations = tool.get("annotations") if tool else None
                if stage == "shadow" and not (
                    isinstance(annotations, dict) and annotations.get("readOnlyHint") is True
                ):
                    raise AppError(
                        "shadow_write_denied",
                        "Shadow probes require read-only MCP tools without external effects.",
                        409,
                    )
                result = isolated.call(app_id, case.tool, case.arguments)
                results.append({"tool": case.tool, "response": result})
                if result["result"] != case.expected:
                    return {"proof": cast(Document, proof.model_dump(mode="json"))}, {
                        "passed": False,
                        "cases": cast(list[JsonValue], results),
                        "reason": "Output differed from the immutable expectation",
                    }
            return {
                "proof_hash": fingerprint(json_document(path.read_bytes())),
                "proof": cast(Document, proof.model_dump(mode="json")),
            }, {
                "passed": True,
                "cases": cast(list[JsonValue], results),
                "runtime": isolated.status(app_id),
                "outputs_consumed": False,
            }
        except AppError as error:
            return {"source": "recorded" if stage in {"tests", "sandbox"} else "live"}, {
                "passed": False,
                "error": error.document(),
                "runtime": isolated.status(app_id),
                "logs": cast(list[JsonValue], isolated.logs(app_id)),
            }
        finally:
            isolated.close()
