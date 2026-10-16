"""Deterministically verified proposals require operator approval before writes."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from threading import RLock

import wcmatch.glob as wcglob  # pyright: ignore[reportMissingTypeStubs]
from deepagents.backends.protocol import (
    BackendProtocol,
    DeleteResult,
    EditResult,
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
    GlobResult,
    GrepResult,
    LsResult,
    ReadResult,
    SandboxBackendProtocol,
    WriteResult,
)
from qmx_ledger.journal import RunJournal, encoded, fingerprint


class AdmissionDenied(ValueError):
    pass


def valid_path(path: str) -> bool:
    return (
        path.startswith("/")
        and "\\" not in path
        and ":" not in path
        and "\x00" not in path
        # Win32 strips these suffixes, which can disguise protected paths.
        and all(part == part.rstrip(". ") for part in path.split("/"))
        # DOS short names can alias a protected directory on Windows volumes.
        and not any(re.fullmatch(r"[^.]{1,6}~[0-9]+(?:\..*)?", part) for part in path.split("/"))
        and "//" not in path
    )


@dataclass(frozen=True)
class WriteProposal:
    path: str
    content: str
    before_hash: str | None

    @property
    def id(self) -> str:
        return fingerprint({"path": self.path, "content": self.content, "before": self.before_hash})


class AdmissionGate:
    def __init__(self, journal: RunJournal | None = None) -> None:
        self.journal = journal
        self._staged: dict[str, WriteProposal] = {}
        self._approved: set[str] = set()
        self.lock = RLock()

    def stage(self, proposal: WriteProposal, verifier: Callable[[WriteProposal], bool]) -> str:
        with self.lock:
            if self.journal is None:
                raise AdmissionDenied("Admission requires an evidence journal")
            if not valid_path(proposal.path) or not verifier(proposal):
                if self.journal:
                    self.journal.quarantine(
                        encoded(proposal.__dict__), "Admission validation failed"
                    )
                raise AdmissionDenied("Deterministic validation failed")
            if self.journal:
                reference = self.journal.store_result(encoded(proposal.__dict__))
                self.journal.append(
                    "proposal_staged", {"proposal_id": proposal.id, "result_ref": reference}
                )
            self._staged[proposal.id] = proposal
            return proposal.id

    def approve(self, proposal_id: str, *, principal: str) -> None:
        """Called by the authenticated operator service, never exposed as an agent tool."""
        with self.lock:
            if principal != "operator" or proposal_id not in self._staged:
                raise AdmissionDenied("A staged proposal requires the operator")
            if self.journal:
                self.journal.append(
                    "approval", {"proposal_id": proposal_id, "principal": principal}
                )
            self._approved.add(proposal_id)

    def check(self, proposal: WriteProposal) -> None:
        if proposal.id not in self._approved or self._staged.get(proposal.id) != proposal:
            raise AdmissionDenied("Stage, verify and approve this exact write before applying it")

    def record(self, proposal: WriteProposal, event: str) -> None:
        if self.journal:
            self.journal.append(
                event,
                {
                    "proposal_id": proposal.id,
                    "path": proposal.path,
                    "before_hash": proposal.before_hash,
                    "after_hash": sha256(proposal.content.encode()).hexdigest(),
                },
            )
        if event == "write_applied":
            self._approved.remove(proposal.id)


class AdmissionBackend(BackendProtocol):
    def __init__(
        self,
        inner: BackendProtocol,
        gate: AdmissionGate,
        *,
        guarded_prefixes: tuple[str, ...] = ("/artifacts/", "/memories/global/"),
        write: list[str] | None = None,
        deny_write: list[str] | None = None,
    ) -> None:
        self.inner = inner
        self.gate = gate
        self.guarded_prefixes = guarded_prefixes
        self.write_paths = write
        self.deny_paths = deny_write or []

    def _allowed(self, path: str) -> bool:
        def matches(pattern: str) -> bool:
            return wcglob.globmatch(path, pattern, flags=wcglob.BRACE | wcglob.GLOBSTAR)

        return (
            valid_path(path)
            and not any(matches(p) for p in self.deny_paths)
            and (self.write_paths is None or any(matches(p) for p in self.write_paths))
        )

    def _guarded(self, path: str) -> bool:
        # Windows-backed volumes resolve case aliases to the same evidence.
        path = path.casefold()
        return any(
            path == prefix.rstrip("/").casefold() or path.startswith(prefix.casefold())
            for prefix in self.guarded_prefixes
        )

    def _quarantine(self, path: str, data: bytes, reason: str) -> str:
        if self.gate.journal:
            self.gate.journal.quarantine(data, f"{path}: {reason}")
        return f"Admission denied: {reason}"

    def _before(self, path: str) -> str | None:
        result = self.inner.download_files([path])[0]
        if result.error == "file_not_found":
            return None
        if result.error or result.content is None:
            raise AdmissionDenied(f"Cannot verify current content: {result.error}")
        return sha256(result.content).hexdigest()

    def write(self, file_path: str, content: str) -> WriteResult:
        with self.gate.lock:
            if not self._allowed(file_path):
                return WriteResult(
                    error=self._quarantine(file_path, content.encode(), "path is not writable")
                )
            if not self._guarded(file_path):
                return self.inner.write(file_path, content)
            try:
                proposal = WriteProposal(file_path, content, self._before(file_path))
                self.gate.check(proposal)
            except AdmissionDenied as exc:
                return WriteResult(error=self._quarantine(file_path, content.encode(), str(exc)))
            self.gate.record(proposal, "before_write")
            result = self.inner.write(file_path, content)
            self.gate.record(proposal, "write_failed" if result.error else "write_applied")
            return result

    def edit(
        self, file_path: str, old_string: str, new_string: str, replace_all: bool = False
    ) -> EditResult:
        with self.gate.lock:
            if not self._allowed(file_path):
                return EditResult(error="Admission denied: path is not writable")
            if not self._guarded(file_path):
                return self.inner.edit(file_path, old_string, new_string, replace_all)
            result = self.inner.download_files([file_path])[0]
            if result.error or result.content is None:
                return EditResult(error="Admission denied: cannot verify current content")
            text = result.content.decode("utf-8")
            count = text.count(old_string)
            if not old_string or count == 0 or (count != 1 and not replace_all):
                return EditResult(error="Admission denied: edit must match uniquely")
            content = text.replace(old_string, new_string, -1 if replace_all else 1)
            proposal = WriteProposal(file_path, content, sha256(result.content).hexdigest())
            try:
                self.gate.check(proposal)
            except AdmissionDenied as exc:
                return EditResult(error=f"Admission denied: {exc}")
            self.gate.record(proposal, "before_write")
            edited = self.inner.edit(file_path, old_string, new_string, replace_all)
            self.gate.record(proposal, "write_failed" if edited.error else "write_applied")
            return edited

    def delete(self, file_path: str) -> DeleteResult:
        # Recursive deletion must not erase protected evidence through an ancestor.
        if (
            not self._allowed(file_path)
            or self._guarded(file_path)
            or any(
                prefix.casefold().startswith(file_path.rstrip("/").casefold() + "/")
                for prefix in self.guarded_prefixes
            )
        ):
            return DeleteResult(error="Admission denied: protected evidence cannot be deleted")
        # Recursive host cleanup must check each descendant's policy.
        if self.inner.download_files([file_path])[0].error:
            return DeleteResult(error="Admission denied: directory cleanup requires the host")
        # State backends can store both an exact file and descendants under it.
        # Backend glob patterns without slashes match basenames at every depth.
        # Include dotfiles explicitly: wildcard-only patterns omit them.
        descendants = self.inner.glob("{**,.*}", "/")
        prefix = file_path.rstrip("/").casefold() + "/"
        if (
            descendants.error
            or descendants.matches is None
            or any(entry["path"].casefold().startswith(prefix) for entry in descendants.matches)
        ):
            return DeleteResult(error="Admission denied: directory cleanup requires the host")
        return self.inner.delete(file_path)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        # Imports cannot bypass staging, approval or create-only writes.
        return [
            FileUploadResponse(
                path=path, error=self._quarantine(path, data, "uploads require staging")
            )
            for path, data in files
        ]

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        return self.inner.download_files(paths)

    def ls(self, path: str) -> LsResult:
        return self.inner.ls(path)

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> ReadResult:
        return self.inner.read(file_path, offset, limit)

    def grep(
        self,
        pattern: str,
        path: str | None = None,
        glob: str | None = None,
        *,
        max_count: int | None = None,
    ) -> GrepResult:
        return self.inner.grep(pattern, path, glob, max_count=max_count)

    def glob(self, pattern: str, path: str | None = None) -> GlobResult:
        return self.inner.glob(pattern, path)


class AdmissionSandboxBackend(AdmissionBackend, SandboxBackendProtocol):
    """Keep supervised execution available while file tools retain admission checks."""

    execution: SandboxBackendProtocol

    @property
    def id(self) -> str:
        return self.execution.id

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        return self.execution.execute(command, timeout=timeout)

    async def aexecute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        return await self.execution.aexecute(command, timeout=timeout)
