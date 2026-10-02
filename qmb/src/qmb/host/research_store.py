"""Application filesystem adapter for QML-authored canonical research bytes.

Persists only canonical Stage 0 bytes keyed by ``research_ref``. Distinct from
seed ``root_path``. Not daemon sqlite, not QMA staging, not a new COMP store,
not Stats, and not a second AD-4 include/exclude. COMP-QMA-DAEMON must not write
this root and must not bind a second CT-44 ``source_id`` in v1.
"""

from __future__ import annotations

import errno
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from qmf.core.fingerprint import Fingerprint
from qmf.core.refusal import Ok, Result, TypedRefusal, is_refusal
from qml._refuse import invalid, policy
from qml.research import save_hypothesis
from qml.research.stage0 import (
    Hypothesis,
    SavedHypothesis,
    fingerprint_hypothesis,
    restore_hypothesis,
    save_authored_hypothesis,
)

from qmb.host.bot_registration import mint_ct06_envelope, mint_generation_envelope

if os.name == "nt":
    from qmb.host import _windows_research

__all__ = [
    "QMA_BINDS_SECOND_CT44_OVER_RESEARCH_ROOT_V1",
    "QMA_WRITES_RESEARCH_ROOT",
    "RESEARCH_ROOT_IS_QMA_SETTING",
    "RESEARCH_ROOT_IS_SEED_ROOT",
    "PersistedHypothesis",
    "mint_ct06_envelope",
    "mint_generation_envelope",
    "persist_research_blob",
    "read_research_blob",
    "research_blob_path",
    "save_research_hypothesis",
]

# AD-8 / AD-21 ownership law — QMA does not write or re-bind this store in v1.
QMA_WRITES_RESEARCH_ROOT: Final[bool] = False
RESEARCH_ROOT_IS_QMA_SETTING: Final[bool] = False
RESEARCH_ROOT_IS_SEED_ROOT: Final[bool] = False
QMA_BINDS_SECOND_CT44_OVER_RESEARCH_ROOT_V1: Final[bool] = False

_FIELD_RESEARCH_ROOT: Final[str] = "research_root"
_SYMLINK_ROOT_REASON: Final[str] = "refusing to follow a symlink at research_root"
_SYMLINK_WRITE_REASON: Final[str] = "refusing to follow a symlink or write outside research_root"
_PERSIST_FAIL_REASON: Final[str] = "the host could not persist canonical research bytes"
_OPEN_SUPPORTS_DIR_FD: Final[bool] = os.open in os.supports_dir_fd
_DIRECTORY_FLAG_NAME: Final[str] = "O_DIRECTORY"


@dataclass(frozen=True, slots=True)
class PersistedHypothesis:
    """Host-persisted Stage 0 blob: canonical bytes under ``research_root``."""

    research_root: Path
    path: Path
    canonical_bytes: bytes
    research_ref: Fingerprint


def research_blob_path(research_root: object, research_ref: object) -> Result[Path]:
    """Resolve the blob path for a ``research_ref`` under ``research_root``."""
    root = _admit_root(research_root)
    if is_refusal(root):
        return root
    ref = _admit_ref(research_ref)
    if is_refusal(ref):
        return ref
    # Filesystem-safe key derived from the fp1 string (colons are not path-safe).
    name = ref.value.value.replace(":", "-")
    return Ok(root.value / name)


def persist_research_blob(
    *,
    research_root: object,
    research_ref: object,
    canonical_bytes: object,
) -> Result[PersistedHypothesis]:
    """Persist only the canonical Stage 0 bytes keyed by ``research_ref``."""
    if QMA_WRITES_RESEARCH_ROOT:
        return policy(
            _FIELD_RESEARCH_ROOT,
            "COMP-QMA-DAEMON must not write the research root in v1",
        )
    prepared = _prepare_persist(research_root, research_ref, canonical_bytes)
    if is_refusal(prepared):
        return prepared
    root, ref, payload, path = prepared.value
    written = _write_research_blob(root=root, path=path, payload=payload)
    if is_refusal(written):
        return written
    return Ok(
        PersistedHypothesis(
            research_root=root,
            path=path,
            canonical_bytes=payload,
            research_ref=ref,
        )
    )


def read_research_blob(
    *,
    research_root: object,
    research_ref: object,
) -> Result[bytes]:
    """Read previously persisted canonical bytes. Host I/O only."""
    path = research_blob_path(research_root, research_ref)
    if is_refusal(path):
        return path
    root = _admit_root(research_root)
    if is_refusal(root):
        return root
    ref = _admit_ref(research_ref)
    if is_refusal(ref):
        return ref
    if os.name == "nt":
        try:
            payload = _windows_research.read_blob(root.value, path.value.name)
        except _windows_research.UnsafePath as exc:
            return policy(_FIELD_RESEARCH_ROOT, str(exc))
        except FileNotFoundError as exc:
            return invalid(
                "research_ref",
                "no canonical research blob is stored under research_root for that ref",
                research_ref=path.value.name,
                given=type(exc).__name__,
            )
        except OSError as exc:
            return _persist_os_error(path.value, exc)
        return _validate_canonical_blob(payload, ref.value)
    opened = _open_research_root(root.value, create=False)
    if is_refusal(opened):
        return opened
    try:
        payload = _read_blob_at(opened.value, path.value.name, path.value)
    finally:
        os.close(opened.value)
    if is_refusal(payload):
        return payload
    return _validate_canonical_blob(payload.value, ref.value)


def save_research_hypothesis(
    hypothesis: object,
    *,
    research_root: object,
) -> Result[PersistedHypothesis]:
    """Explicit QML authoring save: mint bytes + ref, then persist under research_root."""
    if not isinstance(hypothesis, Hypothesis):
        return invalid(
            "hypothesis",
            "the host saves an authored Stage 0 Hypothesis; viewing cited seed "
            "mints no research_ref",
            given=type(hypothesis).__name__,
        )
    saved = save_authored_hypothesis(hypothesis)
    if is_refusal(saved):
        return saved
    blob: SavedHypothesis = saved.value
    return persist_research_blob(
        research_root=research_root,
        research_ref=blob.research_ref,
        canonical_bytes=blob.canonical_bytes,
    )


def _prepare_persist(
    research_root: object,
    research_ref: object,
    canonical_bytes: object,
) -> Result[tuple[Path, Fingerprint, bytes, Path]]:
    admitted = _admit_persist_inputs(research_root, research_ref, canonical_bytes)
    if is_refusal(admitted):
        return admitted
    root, ref, payload = admitted.value
    path = research_blob_path(root, ref)
    if is_refusal(path):
        return path
    return Ok((root, ref, payload, path.value))


def _admit_persist_inputs(
    research_root: object,
    research_ref: object,
    canonical_bytes: object,
) -> Result[tuple[Path, Fingerprint, bytes]]:
    root = _admit_root(research_root)
    if is_refusal(root):
        return root
    ref = _admit_ref(research_ref)
    if is_refusal(ref):
        return ref
    payload = _validate_canonical_blob(canonical_bytes, ref.value)
    if is_refusal(payload):
        return payload
    return Ok((root.value, ref.value, payload.value))


def _validate_canonical_blob(canonical_bytes: object, research_ref: Fingerprint) -> Result[bytes]:
    if not isinstance(canonical_bytes, (bytes, bytearray)):
        return invalid(
            "canonical_bytes",
            "the host persists only canonical Stage 0 bytes",
            given=type(canonical_bytes).__name__,
        )
    payload = bytes(canonical_bytes)
    try:
        envelope = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        return invalid("canonical_bytes", "research blobs are canonical UTF-8 Stage 0 JSON")
    hypothesis = restore_hypothesis(envelope)
    if is_refusal(hypothesis):
        return hypothesis
    actual_ref = fingerprint_hypothesis(hypothesis.value)
    if is_refusal(actual_ref):
        return actual_ref
    if actual_ref.value != research_ref:
        return policy(
            "research_ref",
            "canonical Stage 0 content must match its content-addressed research_ref",
            expected=research_ref.value,
            actual=actual_ref.value.value,
        )
    canonical = save_hypothesis(hypothesis.value)
    if is_refusal(canonical):
        return canonical
    if canonical.value.canonical_bytes != payload:
        return invalid(
            "canonical_bytes",
            "persisted Stage 0 bytes must be the canonical serialization of their hypothesis",
        )
    return Ok(payload)


def _persist_os_error(path: Path, exc: OSError) -> TypedRefusal:
    return invalid(
        _FIELD_RESEARCH_ROOT,
        _PERSIST_FAIL_REASON,
        given=type(exc).__name__,
        path=str(path),
    )


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    offset = 0
    while offset < len(view):
        offset += os.write(fd, view[offset:])


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def _unlink_owned_temp(root_fd: int, temp_name: str, temp_fd: int) -> None:
    """Remove the temporary path only while it still names our open file."""
    try:
        named = os.stat(temp_name, dir_fd=root_fd, follow_symlinks=False)
        opened = os.fstat(temp_fd)
        if stat.S_ISREG(named.st_mode) and _same_file_identity(named, opened):
            os.unlink(temp_name, dir_fd=root_fd)
    except OSError:
        return


def _verify_published_blob(
    root_fd: int,
    leaf: str,
    temp_fd: int,
    path: Path,
    expected: bytes,
) -> Result[None]:
    """Require the published name to be the exact regular inode still held open."""
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        return policy(_FIELD_RESEARCH_ROOT, "published blob verification requires O_NOFOLLOW")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        published_fd = os.open(leaf, flags, dir_fd=root_fd)
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            return policy(_FIELD_RESEARCH_ROOT, "published research blob is not a regular file")
        return _persist_os_error(path, exc)
    try:
        published_stat = os.fstat(published_fd)
        source_stat = os.fstat(temp_fd)
        if (
            not stat.S_ISREG(published_stat.st_mode)
            or not _same_file_identity(published_stat, source_stat)
        ):
            return policy(
                _FIELD_RESEARCH_ROOT,
                "published research blob is the exact regular temporary inode",
            )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(published_fd, 65_536)
            if not chunk:
                break
            chunks.append(chunk)
        if b"".join(chunks) != expected:
            return policy(_FIELD_RESEARCH_ROOT, "published research bytes match the admitted blob")
        return Ok(None)
    except OSError as exc:
        return _persist_os_error(path, exc)
    finally:
        os.close(published_fd)


def _nofollow_open_flags() -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None or not _OPEN_SUPPORTS_DIR_FD:
        raise NotImplementedError(
            "no-follow directory-descriptor filesystem operations unavailable"
        )
    return os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)


def _open_research_root(root: Path, *, create: bool) -> Result[int]:
    """Acquire every root component without following symlinks; return pinned directory fd."""
    try:
        flags = _nofollow_open_flags()
    except NotImplementedError:
        return policy(
            _FIELD_RESEARCH_ROOT,
            "safe research-root access requires no-follow directory descriptors on this platform",
            failure_id="research_store.safe_open_unsupported",
        )
    directory = cast(int, getattr(os, _DIRECTORY_FLAG_NAME))
    try:
        absolute = Path(os.path.abspath(root))
        fd = os.open("/", flags | directory)
    except OSError as exc:
        return _persist_os_error(root, exc)
    parts = absolute.parts[1:]
    for part in parts:
        try:
            child = os.open(part, flags | directory, dir_fd=fd)
        except FileNotFoundError as exc:
            if not create:
                os.close(fd)
                return invalid(
                    "research_ref",
                    "no canonical research blob is stored under research_root",
                    given=type(exc).__name__,
                )
            try:
                os.mkdir(part, 0o700, dir_fd=fd)
                child = os.open(part, flags | directory, dir_fd=fd)
            except FileExistsError:
                try:
                    child = os.open(part, flags | directory, dir_fd=fd)
                except OSError as nested:
                    os.close(fd)
                    return _root_open_refusal(root, nested)
            except OSError as nested:
                os.close(fd)
                return _root_open_refusal(root, nested)
        except OSError as exc:
            os.close(fd)
            return _root_open_refusal(root, exc)
        os.close(fd)
        fd = child
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            os.close(fd)
            return policy(_FIELD_RESEARCH_ROOT, _SYMLINK_ROOT_REASON)
    except OSError as exc:
        os.close(fd)
        return _persist_os_error(root, exc)
    return Ok(fd)


def _root_open_refusal(root: Path, exc: OSError) -> TypedRefusal:
    if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
        return policy(_FIELD_RESEARCH_ROOT, _SYMLINK_ROOT_REASON)
    return _persist_os_error(root, exc)


def _read_blob_at(
    root_fd: int,
    leaf: str,
    path: Path,
    *,
    missing_ok: bool = False,
) -> Result[bytes | None]:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None or not _OPEN_SUPPORTS_DIR_FD:
        return policy(
            _FIELD_RESEARCH_ROOT,
            "safe blob reads require no-follow directory descriptors",
        )
    flags = os.O_RDONLY | nofollow | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(leaf, flags, dir_fd=root_fd)
    except FileNotFoundError as exc:
        if missing_ok:
            return Ok(None)
        return invalid(
            "research_ref",
            "no canonical research blob is stored under research_root for that ref",
            research_ref=path.name,
            given=type(exc).__name__,
        )
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.ENOTDIR}:
            return policy(_FIELD_RESEARCH_ROOT, _SYMLINK_WRITE_REASON)
        return _persist_os_error(path, exc)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return policy(_FIELD_RESEARCH_ROOT, "research blob leaf must be a regular file")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 65_536)
            if not chunk:
                break
            chunks.append(chunk)
        return Ok(b"".join(chunks))
    except OSError as exc:
        return _persist_os_error(path, exc)
    finally:
        os.close(fd)


def _write_research_blob(*, root: Path, path: Path, payload: bytes) -> Result[None]:
    """Create a no-clobber blob using only a pinned no-follow root descriptor."""
    if os.name == "nt":
        try:
            _windows_research.write_blob(root, path.name, payload)
        except _windows_research.UnsafePath as exc:
            return policy(_FIELD_RESEARCH_ROOT, str(exc))
        except OSError as exc:
            return _persist_os_error(path, exc)
        return Ok(None)
    opened = _open_research_root(root, create=True)
    if is_refusal(opened):
        return opened
    root_fd = opened.value
    try:
        old = _read_blob_at(root_fd, path.name, path, missing_ok=True)
        if is_refusal(old):
            return old
        if old.value is not None:
            if old.value == payload:
                return Ok(None)
            return policy(
                "research_ref",
                "an existing content-addressed blob cannot be overwritten by different bytes",
                research_ref=path.name,
            )
        if os.link not in os.supports_dir_fd or os.unlink not in os.supports_dir_fd:
            return policy(
                _FIELD_RESEARCH_ROOT,
                "safe blob creation requires descriptor-relative no-clobber links",
                failure_id="research_store.safe_write_unsupported",
            )
        flags = _nofollow_open_flags() | os.O_CREAT | os.O_EXCL | os.O_WRONLY
        temp_name: str | None = None
        temp_fd: int | None = None
        for attempt in range(32):
            candidate = f".{path.name}.write-{os.getpid()}-{attempt}"
            try:
                temp_fd = os.open(candidate, flags, 0o600, dir_fd=root_fd)
            except FileExistsError:
                continue
            except OSError as exc:
                return _persist_os_error(path, exc)
            temp_name = candidate
            break
        if temp_name is None or temp_fd is None:
            return policy(
                _FIELD_RESEARCH_ROOT,
                "no exclusive temporary filename was available for the research blob",
                failure_id="research_store.temp_name_exhausted",
            )
        try:
            _write_all(temp_fd, payload)
            os.fsync(temp_fd)
        except OSError as exc:
            _unlink_owned_temp(root_fd, temp_name, temp_fd)
            os.close(temp_fd)
            return _persist_os_error(path, exc)
        try:
            os.link(
                temp_name,
                path.name,
                src_dir_fd=root_fd,
                dst_dir_fd=root_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            raced = _read_blob_at(root_fd, path.name, path)
            if is_refusal(raced):
                return raced
            if raced.value != payload:
                return policy("research_ref", "concurrent blob creation has different bytes")
            verified = Ok(None)
        except OSError as exc:
            return _persist_os_error(path, exc)
        else:
            verified = _verify_published_blob(
                root_fd,
                path.name,
                temp_fd,
                path,
                payload,
            )
        finally:
            _unlink_owned_temp(root_fd, temp_name, temp_fd)
            os.close(temp_fd)
        if is_refusal(verified):
            return verified
        try:
            os.fsync(root_fd)
        except OSError as exc:
            return _persist_os_error(root, exc)
        return Ok(None)
    finally:
        os.close(root_fd)


def _admit_root(research_root: object) -> Result[Path]:
    if isinstance(research_root, Path):
        root = research_root
    elif isinstance(research_root, str) and research_root.strip() != "":
        root = Path(research_root)
    else:
        return invalid(
            _FIELD_RESEARCH_ROOT,
            "research_root is a filesystem path distinct from seed root_path; "
            "it is not a QMA daemon / research-corpus setting",
            given=repr(research_root),
            is_qma_setting=RESEARCH_ROOT_IS_QMA_SETTING,
            is_seed_root=RESEARCH_ROOT_IS_SEED_ROOT,
        )
    return Ok(root)


def _admit_ref(research_ref: object) -> Result[Fingerprint]:
    candidate = research_ref.value if isinstance(research_ref, Fingerprint) else research_ref
    parsed = Fingerprint.try_create(candidate)
    if is_refusal(parsed):
        return invalid(
            "research_ref",
            "research_ref is an fp1-shaped fingerprint string",
            given=repr(research_ref),
        )
    return Ok(parsed.value)
