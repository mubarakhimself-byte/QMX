"""Run bundles and placement settings contain references, never credentials."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator
from qmx_agents.guards.journal import fingerprint

type Document = dict[str, JsonValue]
type Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
type Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$")]
type Status = Literal["provisioned", "running", "completed", "failed", "stopped", "interrupted"]


class RemoteError(ValueError):
    """Safe diagnostics for both platform transports."""

    status = 409

    def document(self) -> Document:
        return {"error": {"code": "remote_run_failed", "message": str(self)}}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def safe_path(name: str) -> str:
    path = PurePosixPath(name)
    if (
        not name
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in name.split("/"))
        or re.search(r"[\\:\x00-\x1f]", name)
    ):
        raise RemoteError("Run paths must be relative and stay inside the run.")
    return name


class Resources(StrictModel):
    gpu: int = Field(default=0, ge=0)
    memory_mb: int = Field(default=1024, gt=0)
    cpus: int = Field(default=1, gt=0)
    timeout: int = Field(default=3600, gt=0)


class CodeSource(StrictModel):
    repository: str
    revision: str = Field(pattern=r"^[a-f0-9]{40}$")

    @model_validator(mode="after")
    def validate_repository(self) -> Self:
        url = urlsplit(self.repository)
        if (
            url.scheme != "https"
            or not url.hostname
            or any((url.username, url.password, url.query, url.fragment))
        ):
            raise RemoteError("Code repositories must be HTTPS URLs without embedded credentials.")
        return self


class RunBundle(StrictModel):
    kind: Literal["workflow", "agent", "app", "job", "amp"]
    definition: Document
    definition_hash: Digest
    inputs: Document = Field(default_factory=dict)
    model_profile: Document = Field(default_factory=dict)
    credentials_scope: dict[str, str] = Field(default_factory=dict)
    resources: Resources = Field(default_factory=Resources)
    files: dict[str, Digest] = Field(default_factory=dict)
    command: list[str] = Field(default_factory=list)
    app_id: Identifier | None = None
    code: CodeSource | None = None

    @model_validator(mode="after")
    def validate_bundle(self) -> Self:
        if self.definition_hash != fingerprint(
            {"definition": self.definition, "files": self.files}
        ):
            raise RemoteError("Definition hash does not match the run bundle.")
        for name in self.files:
            safe_path(name)
        for name, reference in self.credentials_scope.items():
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name) or not reference.startswith("qmx/"):
                raise RemoteError(
                    "Credentials must be named environment variables with qmx/* refs."
                )
        if self.kind == "job" and not self.command:
            raise RemoteError("A job needs a command argument list.")
        if self.kind == "app" and self.app_id is None:
            raise RemoteError("An app run needs its app_id.")
        return self


class Target(StrictModel):
    provider: Literal["ssh", "amp", "modal", "e2b"] = "ssh"
    host: str = Field(default="", pattern=r"^(?:[a-zA-Z0-9][a-zA-Z0-9@._-]*)?$")
    root: str = "/srv/qmx/bucket"
    bucket_local: bool = True
    image: str = ""
    gpu: int = Field(default=0, ge=0)
    gpu_type: str | None = None
    executor: Literal["orb", "runner"] = "runner"
    runner_id: str | None = None
    runner_dir: str | None = None
    project: str | None = None

    @model_validator(mode="after")
    def validate_target(self) -> Self:
        if self.provider in {"ssh", "amp"} and not self.host:
            raise RemoteError("SSH and Amp targets need an SSH host for their durable worker.")
        if not self.root.startswith("/") or ".." in PurePosixPath(self.root).parts:
            raise RemoteError("Node root must be an absolute POSIX path.")
        return self


class RemoteSettings(StrictModel):
    default_target: str = "vps"
    bucket: str = "vps:/srv/qmx/bucket"
    targets: dict[str, Target] = Field(default_factory=dict)

    def place(self, requested: str | None, resources: Resources) -> tuple[str, Target]:
        name = requested or self.default_target
        if name not in self.targets:
            raise RemoteError("Configure the remote target in Settings first.")
        target = self.targets[name]
        if resources.gpu > target.gpu:
            if requested:
                raise RemoteError("Requested target does not have enough GPUs.")
            for candidate, node in self.targets.items():
                if node.gpu >= resources.gpu:
                    return candidate, node
            raise RemoteError("Configure a GPU node or provider before submitting this job.")
        return name, target


class Artifact(StrictModel):
    path: str
    sha256: Digest
    size: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_path(self) -> Self:
        safe_path(self.path)
        if self.path.split("/")[0] not in {"outputs", "logs", "traces", "checkpoints"} and (
            self.path != "journal.jsonl"
        ):
            raise RemoteError("Manifest files must belong to a run output directory.")
        return self


class Manifest(StrictModel):
    run_id: Identifier
    bundle: RunBundle
    target: str
    status: Status = "provisioned"
    versions: dict[str, str] = Field(default_factory=dict)
    artifacts: list[Artifact] = Field(default_factory=list[Artifact])
    checkpoint: Digest | None = None
    revision: int = Field(default=0, ge=0)
    fingerprint: Digest | None = None

    def seal(self) -> None:
        self.fingerprint = fingerprint(self.model_dump(mode="json", exclude={"fingerprint"}))

    def verify(self, run_id: str) -> None:
        if self.run_id != run_id or self.fingerprint != fingerprint(
            self.model_dump(mode="json", exclude={"fingerprint"})
        ):
            raise RemoteError("Run manifest identity or fingerprint mismatch.")
        names = [item.path for item in self.artifacts]
        if len(names) != len(set(names)):
            raise RemoteError("Duplicate manifest paths.")
        if self.checkpoint and not any(
            item.path == "checkpoints/latest.db" and item.sha256 == self.checkpoint
            for item in self.artifacts
        ):
            raise RemoteError("Manifest checkpoint is missing from the artifact list.")
