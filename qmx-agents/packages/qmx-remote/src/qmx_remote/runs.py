"""Persist provider handles locally; recover data from the target's bucket."""

from __future__ import annotations

import json
import shutil
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import cast
from uuid import uuid4

import keyring
from pydantic import Field, JsonValue
from qmx_agents.guards.journal import RunJournal

from qmx_remote.models import (
    Document,
    Manifest,
    RemoteError,
    RemoteSettings,
    RunBundle,
    StrictModel,
    Target,
)
from qmx_remote.providers import ComputeProvider, registry
from qmx_remote.store import ResultsStore, checksum


class RunState(StrictModel):
    manifest: Manifest
    target: Target
    bucket: str
    handle: Document = Field(default_factory=dict)
    released: bool = False


class RemoteRuns:
    def __init__(
        self,
        home: Path,
        settings: RemoteSettings,
        *,
        providers: Callable[[Target, str], ComputeProvider] | None = None,
        secret_getter: Callable[[str, str], str | None] = keyring.get_password,
    ):
        self.home = home
        self.settings = settings
        self.providers: Callable[[Target, str], ComputeProvider] = providers or (
            lambda target, bucket: registry(target, bucket, secret_getter=secret_getter)
        )
        self.secret_getter = secret_getter
        self.lock = threading.RLock()

    def _path(self, run_id: str) -> Path:
        ResultsStore(self.settings.bucket).location(run_id)
        return self.home / "remote" / run_id / "state.json"

    def _save(self, state: RunState) -> None:
        state.manifest.seal()
        path = self._path(state.manifest.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(state.model_dump_json(), encoding="utf-8")
        temporary.replace(path)

    def _read(self, run_id: str) -> RunState:
        try:
            return RunState.model_validate_json(self._path(run_id).read_bytes())
        except FileNotFoundError as error:
            raise RemoteError("Unknown remote run id.") from error

    def _request(self, state: RunState, source: Path | None, *, resume: bool = False) -> None:
        manifest = state.manifest
        with tempfile.TemporaryDirectory(prefix="qmx-request-") as temporary:
            stage = Path(temporary)
            for name, digest in manifest.bundle.files.items():
                if source is None:
                    raise RemoteError("Provide the definition directory for bundled files.")
                path = source / name
                if (
                    not path.resolve().is_relative_to(source.resolve())
                    or path.is_symlink()
                    or checksum(path) != digest
                ):
                    raise RemoteError("Bundled definition file hash mismatch.")
                target = stage / "definition" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
            request = {
                "manifest": manifest.model_dump(mode="json"),
                "target": state.target.model_dump(mode="json"),
                "resume": resume,
            }
            (stage / "request.json").write_text(json.dumps(request), encoding="utf-8")
            ResultsStore.copy(stage, state.bucket + "/requests/" + manifest.run_id)

    def _launch(self, state: RunState, source: Path | None, *, resume: bool = False) -> Document:
        provider = self.providers(state.target, state.bucket)
        state.handle = provider.provision(state.manifest.run_id, state.manifest.bundle)
        state.released = False
        self._save(state)
        credentials: dict[str, str] = {}
        start_attempted = False
        try:
            self._request(state, source, resume=resume)
            # Replace the old terminal status before a resumed worker can be polled.
            # Preserve its verified artifacts and checkpoint until the first flush.
            ResultsStore(state.bucket).commit(state.manifest)
            for name, reference in state.manifest.bundle.credentials_scope.items():
                value = self.secret_getter(reference, reference.removeprefix("qmx/"))
                if value is None:
                    raise RemoteError("A scoped credential is missing from the vault.")
                credentials[name] = value
            start_attempted = True
            state.handle = provider.start(state.handle, credentials)
            state.manifest.status = "running"
            self._save(state)
        except BaseException:
            state.manifest.status = "failed"
            # These adapters validate in provision and allocate only in start.
            state.released = not start_attempted
            self._save(state)
            if start_attempted:
                provider.teardown(state.handle)
                state.released = True
                self._save(state)
            raise
        finally:
            credentials.clear()
        return state.manifest.model_dump(mode="json")

    def start(
        self, bundle: RunBundle, target: str | None = None, source: Path | None = None
    ) -> Document:
        with self.lock:
            name, node = self.settings.place(target, bundle.resources)
            manifest = Manifest(run_id=uuid4().hex, bundle=bundle, target=name)
            state = RunState(manifest=manifest, target=node, bucket=self.settings.bucket)
            return self._launch(state, source)

    def status(self, run_id: str) -> Document:
        with self.lock:
            state = self._read(run_id)
            if state.manifest.status not in {"failed", "stopped", "completed"}:
                store = ResultsStore(state.bucket)
                remote = store.read(run_id)
                if remote.bundle != state.manifest.bundle:
                    raise RemoteError("Remote manifest changed the run bundle.")
                state.manifest = remote
                if state.manifest.status not in {"completed", "failed", "stopped"}:
                    state.manifest.status = self.providers(state.target, state.bucket).status(
                        state.handle
                    )
                self._save(state)
            if state.manifest.status in {"completed", "failed"} and not state.released:
                self.providers(state.target, state.bucket).teardown(state.handle)
                state.released = True
                self._save(state)
            return state.manifest.model_dump(mode="json")

    def logs(self, run_id: str) -> Document:
        state = self._read(run_id)
        destination = self.home / "remote" / run_id / "downloaded"
        ResultsStore(state.bucket).fetch(run_id, destination)
        lines: list[str] = []
        for path in sorted((destination / "logs").glob("*")):
            if path.is_file():
                lines.extend(path.read_text(encoding="utf-8").splitlines()[-1000:])
        return {"run_id": run_id, "lines": cast(list[JsonValue], lines[-1000:])}

    def fetch(self, run_id: str) -> Document:
        with self.lock:
            state = self._read(run_id)
            destination = self.home / "remote" / run_id / "downloaded"
            manifest = ResultsStore(state.bucket).fetch(run_id, destination)
            if manifest.bundle != state.manifest.bundle:
                raise RemoteError("Fetched manifest changed the run bundle.")
            with RunJournal(self.home / "journals" / f"remote-{run_id}.jsonl", run_id) as journal:
                journal.append(
                    "remote_fetch",
                    {
                        "target": manifest.target,
                        "revision": manifest.revision,
                        "artifact_ref": str(destination),
                    },
                )
            return {
                "run_id": run_id,
                "status": manifest.status,
                "path": str(destination),
                "artifacts": [item.model_dump(mode="json") for item in manifest.artifacts],
            }

    def resume(self, run_id: str, target: str | None = None) -> Document:
        with self.lock:
            self.status(run_id)
            state = self._read(run_id)
            if state.manifest.status in {"running", "provisioned", "completed"}:
                raise RemoteError("Only a stopped, failed or interrupted run can resume.")
            store = ResultsStore(state.bucket)
            manifest = store.read(run_id)
            if manifest.bundle != state.manifest.bundle or not manifest.checkpoint:
                raise RemoteError("No verified checkpoint for this run is available.")
            downloaded = self.home / "remote" / run_id / "downloaded"
            store.fetch(run_id, downloaded)
            old_provider = self.providers(state.target, state.bucket)
            if not state.released:
                old_provider.teardown(state.handle)
            name, node = self.settings.place(target, manifest.bundle.resources)
            state.target = node
            state.manifest = manifest
            state.manifest.target = name
            state.manifest.status = "provisioned"
            # Reuse the immutable definition already in the bucket; only the request changes.
            with tempfile.TemporaryDirectory(prefix="qmx-resume-") as temporary:
                stage = Path(temporary)
                ResultsStore.copy(state.bucket + "/requests/" + run_id, stage)
                return self._launch(state, stage / "definition", resume=True)

    def stop(self, run_id: str) -> Document:
        with self.lock:
            state = self._read(run_id)
            if state.manifest.status == "stopped":
                return state.manifest.model_dump(mode="json")
            provider = self.providers(state.target, state.bucket)
            if not state.released:
                provider.stop(state.handle)
                provider.teardown(state.handle)
                state.released = True
            state.manifest.status = "stopped"
            self._save(state)
            return state.manifest.model_dump(mode="json")
