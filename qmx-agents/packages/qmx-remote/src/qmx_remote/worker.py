"""Target-side execution and incremental shipping, independent of the laptop."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Callable
from contextlib import closing
from importlib.metadata import version
from pathlib import Path
from types import FrameType
from typing import Any

import aiosqlite
from deepagents.backends import FilesystemBackend
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from qmx_agents.guards.journal import RunJournal
from qmx_agents.router import ModelRouter, RouterConfig, RunContext
from qmx_agents.spec import BuildContext, build_agent, load_spec
from qmx_agents.workflows import Bindings, WorkflowSpec, compile
from qmx_apps.supervisor import Supervisor
from qmx_apps.volume import Volume

from qmx_remote.code import checkout, publish
from qmx_remote.models import Document, Manifest, RemoteError, Target
from qmx_remote.store import ResultsStore, checksum, files, snapshot_checkpoint


class Worker:
    def __init__(self, store: ResultsStore, root: Path, manifest: Manifest, *, interval: float = 5):
        self.store = store
        self.root = root
        self.manifest = manifest
        self.interval = interval
        self.finished = threading.Event()
        self.cancelled = threading.Event()
        self.failure: BaseException | None = None
        self.code_root: Path | None = None
        self.journal: RunJournal | None = None
        self.app_volume: Path | None = None
        self.mutex = threading.RLock()
        self.secrets = [
            os.environ[name] for name in manifest.bundle.credentials_scope if name in os.environ
        ]
        self.root.mkdir(parents=True, exist_ok=True)

    def redact(self, value: str) -> str:
        for secret in self.secrets:
            if secret:
                value = value.replace(secret, "[redacted]")
        return value

    def log(self, text: str) -> None:
        with self.mutex:
            path = self.root / "logs/worker.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as stream:
                stream.write(self.redact(text) + "\n")

    def flush(self) -> None:
        with self.mutex:
            if self.app_volume and self.app_volume.exists():
                for source in files(self.app_volume):
                    relative = source.relative_to(self.app_volume)
                    if source.name.endswith(("-wal", "-shm", ".lock")) or relative.parts[:2] == (
                        "data",
                        "tmp",
                    ):
                        continue
                    target = self.root / "outputs/app" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if source.suffix == ".db":
                        snapshot_checkpoint(source, target)
                    else:
                        shutil.copyfile(source, target)
            database = self.root / "state.db"
            if database.exists():
                snapshot_checkpoint(database, self.root / "checkpoints/latest.db")
            self.store.publish(self.root, self.manifest)

    def _ship(self) -> None:
        while not self.finished.wait(self.interval):
            try:
                self.flush()
            except BaseException as error:
                self.failure = error
                self.cancelled.set()
                return

    def run(self, execute: Callable[[Worker], Any]) -> Manifest:
        self.manifest.versions = {
            name: version(name) for name in ("qmx-remote", "qmx-agents", "langgraph")
        }
        self.manifest.status = "running"
        with RunJournal(self.root / "journal.jsonl", self.manifest.run_id) as journal:
            self.journal = journal
            journal.append(
                "run_start", {"kind": self.manifest.bundle.kind, "target": self.manifest.target}
            )
            self.flush()
            shipper = threading.Thread(target=self._ship, daemon=True)
            shipper.start()
            try:
                result = execute(self)
                if self.failure:
                    raise RemoteError("Incremental result shipping failed.") from self.failure
                self.manifest.status = "stopped" if self.cancelled.is_set() else "completed"
                output = self.root / "outputs/result.json"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(self.redact(json.dumps(result, default=str)), encoding="utf-8")
            except Exception:
                self.manifest.status = "failed"
                self.log(traceback.format_exc())
            finally:
                self.finished.set()
                shipper.join()
                journal.append("run_end", {"status": self.manifest.status})
                self.flush()
                self.secrets.clear()
                for name in self.manifest.bundle.credentials_scope:
                    os.environ.pop(name, None)
        return self.manifest


def execute_workflow(worker: Worker, resume: bool) -> Any:
    bundle = worker.manifest.bundle
    run_id = worker.manifest.run_id
    spec = WorkflowSpec.model_validate(bundle.definition)
    bindings = Bindings()
    context: BuildContext | None = None
    if bundle.model_profile:
        context = BuildContext(
            router=run_router(worker), run=RunContext(task_id=run_id), journal=worker.journal
        )
        bindings.agents = context

    async def drive() -> Any:
        async with aiosqlite.connect(worker.root / "state.db") as connection:
            graph: Any = compile(spec, AsyncSqliteSaver(connection), bindings=bindings)
            config: RunnableConfig = {"configurable": {"thread_id": f"{spec.name}:{run_id}"}}
            try:
                async for _ in graph.astream(
                    None if resume else {"inputs": bundle.inputs}, config, stream_mode="updates"
                ):
                    worker.flush()
                    if worker.cancelled.is_set():
                        break
                state = await graph.aget_state(config)
                if state.next and not worker.cancelled.is_set():
                    raise RemoteError("Workflow needs an approval before it can finish.")
                return state.values
            finally:
                if context:
                    await context.close_memory()

    return asyncio.run(drive())


def run_router(worker: Worker) -> ModelRouter:
    def credential(provider: str) -> str:
        for name, reference in worker.manifest.bundle.credentials_scope.items():
            if reference == "qmx/" + provider and name in os.environ:
                return os.environ[name]
        raise RemoteError("Run model provider has no injected scoped credential.")

    return ModelRouter(
        RouterConfig.model_validate(worker.manifest.bundle.model_profile),
        credential_getter=credential,
    )


def execute_agent(worker: Worker, resume: bool) -> Any:
    bundle = worker.manifest.bundle
    context = BuildContext(
        router=run_router(worker),
        run=RunContext(task_id=worker.manifest.run_id),
        journal=worker.journal,
    )
    if worker.code_root:
        context.backend = FilesystemBackend(root_dir=str(worker.code_root), virtual_mode=True)
    spec_path = worker.root / "definition/agent.yaml"

    async def drive() -> Any:
        async with aiosqlite.connect(worker.root / "state.db") as connection:
            context.checkpointer = AsyncSqliteSaver(connection)
            try:
                graph: Any = await build_agent(load_spec(spec_path), context)
                return await graph.ainvoke(
                    None if resume else bundle.inputs,
                    {"configurable": {"thread_id": worker.manifest.run_id}},
                    context=context.run,
                )
            finally:
                await context.close_memory()

    return asyncio.run(drive())


def execute_job(worker: Worker) -> Document:
    bundle = worker.manifest.bundle
    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {"PATH", "SYSTEMROOT", "HOME", "LANG"} or key in bundle.credentials_scope
    }
    environment["QMX_REMOTE_OUTPUT"] = str(worker.root / "outputs")
    (worker.root / "outputs").mkdir(exist_ok=True)
    definition = worker.code_root or worker.root / "definition"
    definition.mkdir(exist_ok=True)
    with subprocess.Popen(
        bundle.command,
        cwd=definition,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    ) as process:
        output = process.stdout
        if output is None:
            raise RemoteError("Job stdout pipe was not created.")
        reader = threading.Thread(
            target=lambda: [worker.log(line.rstrip()) for line in output], daemon=True
        )
        reader.start()
        started = time.monotonic()  # ambient-scan: allow - enforce the submitted job timeout
        try:
            while process.poll() is None:
                if worker.cancelled.wait(0.1):
                    process.terminate()
                    break
                elapsed = time.monotonic() - started  # ambient-scan: allow - elapsed timeout
                if elapsed > bundle.resources.timeout:
                    process.kill()
                    raise RemoteError("Remote job exceeded its timeout.")
        finally:
            process.wait()
        reader.join()
        if process.returncode and not worker.cancelled.is_set():
            raise RemoteError("Remote job exited unsuccessfully.")
        return {"exit_code": process.returncode}


def execute_app(worker: Worker) -> Document:
    bundle = worker.manifest.bundle

    def secret_getter(service: str, username: str) -> str | None:
        for name, reference in bundle.credentials_scope.items():
            if reference == service:
                return os.environ.get(name)
        return None

    home = worker.root / "app-home"
    worker.app_volume = Volume(home, str(bundle.app_id)).root
    with closing(Supervisor(home, secret_getter=secret_getter)) as supervisor:
        # The worker already runs inside T2/T3; its subprocess is inside that boundary.
        supervisor.install(worker.root / "definition", trust="operator")
        supervisor.start(str(bundle.app_id))
        arguments = bundle.inputs.get("arguments", {})
        if not isinstance(arguments, dict):
            raise RemoteError("App tool arguments must be an object.")
        return supervisor.call(str(bundle.app_id), str(bundle.inputs["tool"]), arguments)


async def execute_amp(worker: Worker, target: Target, *, sdk: Any = None) -> Document:
    sdk = sdk or importlib.import_module("amp_sdk")
    prompt = worker.manifest.bundle.inputs.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise RemoteError("Amp requires a plain string prompt.")
    runner_dir = target.runner_dir
    if worker.code_root:
        if target.executor != "runner":
            raise RemoteError(
                "Code publishing needs an Amp runner on the VPS shared code directory."
            )
        runner_dir = target.root + "/code/" + worker.manifest.run_id
        prompt = (
            "Work only on the checked-out branch runs/" + worker.manifest.run_id + ". " + prompt
        )
    options = sdk.AmpOptions(
        executor=target.executor,
        runner_id=target.runner_id,
        runner_dir=runner_dir,
        project=target.project,
        visibility="private",
        title="QMX " + worker.manifest.run_id,
        labels=["qmx", worker.manifest.run_id],
    )
    result: Document | None = None
    async for message in sdk.execute(prompt, options):
        worker.log(message.model_dump_json())
        if message.type == "system":
            (worker.root / "outputs").mkdir(exist_ok=True)
            (worker.root / "outputs/amp-thread.json").write_text(
                json.dumps({"session_id": message.session_id}), encoding="utf-8"
            )
        if message.type == "result":
            if message.is_error:
                raise RemoteError("Amp reported an unsuccessful remote task.")
            result = {"result": message.result, "session_id": message.session_id}
        worker.flush()
    if result is None:
        raise RemoteError("Amp stream ended without a final result.")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--run-id", required=True)
    arguments = parser.parse_args()
    store = ResultsStore(arguments.bucket)
    store.location(arguments.run_id)
    with tempfile.TemporaryDirectory(prefix="qmx-worker-") as temporary:
        root = Path(temporary)
        ResultsStore.copy(store.bucket + "/requests/" + arguments.run_id, root / "request")
        request = json.loads((root / "request/request.json").read_text(encoding="utf-8"))
        manifest = Manifest.model_validate(request["manifest"])
        if manifest.run_id != arguments.run_id:
            raise RemoteError("Request run identity mismatch.")
        if request["resume"]:
            store.fetch(manifest.run_id, root)
            shutil.copyfile(root / "checkpoints/latest.db", root / "state.db")
        definition = root / "request/definition"
        for name, digest in manifest.bundle.files.items():
            if checksum(definition / name) != digest:
                raise RemoteError("Remote definition hash mismatch.")
        if definition.exists():
            shutil.copytree(definition, root / "definition")
            sys.path.insert(0, str(root / "definition"))
        worker = Worker(store, root, manifest)
        if manifest.bundle.code:
            code_root = (
                Path(store.bucket) / "code" / manifest.run_id
                if target_is_local(store.bucket)
                else root / "code"
            )
            worker.code_root = checkout(code_root, manifest.bundle.code, manifest.run_id)

        def terminate(signum: int, frame: FrameType | None) -> None:
            worker.cancelled.set()

        signal.signal(signal.SIGTERM, terminate)
        target = Target.model_validate(request["target"])

        def execute(w: Worker) -> Any:
            match manifest.bundle.kind:
                case "workflow":
                    result = execute_workflow(w, request["resume"])
                case "agent":
                    result = execute_agent(w, request["resume"])
                case "app":
                    result = execute_app(w)
                case "amp":
                    result = asyncio.run(execute_amp(w, target))
                case "job":
                    result = execute_job(w)
            if w.code_root and not w.cancelled.is_set():
                publish(w.code_root, manifest.run_id)
            return result

        result = worker.run(execute)
        return 0 if result.status == "completed" else 1


def target_is_local(bucket: str) -> bool:
    return ":" not in bucket or (len(bucket) > 2 and bucket[1] == ":" and bucket[2] in "/\\")


if __name__ == "__main__":
    raise SystemExit(main())
