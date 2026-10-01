"""Internal process entrypoint used by ``just node-config-*`` wrappers.

These operations use the same pure library functions as the node API. The
scaffold is deliberately distinct from the supervisor's pinned deployment
document and cannot authorize boot or venue access.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import stat
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final, cast

from qmf.core.refusal import is_refusal

from qmn.config import config_explain, config_init, config_validate

_MAX_CONFIG_BYTES = 1 << 20
_O_NOFOLLOW: Final[int] = cast("int", getattr(os, "O_NOFOLLOW", 0))
_O_DIRECTORY: Final[int] = cast("int", getattr(os, "O_DIRECTORY", 0))
_DIRFD_IO_SUPPORTED = (
    _O_NOFOLLOW != 0
    and _O_DIRECTORY != 0
    and os.open in os.supports_dir_fd
    and os.mkdir in os.supports_dir_fd
    and os.stat in os.supports_dir_fd
    and os.unlink in os.supports_dir_fd
)


def _secure_dirfd_available() -> bool:
    return _DIRFD_IO_SUPPORTED


def _open_directory_at(name: str, directory_fd: int) -> int:
    fd = os.open(
        name,
        os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW,
        dir_fd=directory_fd,
    )
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError(errno.ENOTDIR, "path component is not a directory")
    except BaseException:
        os.close(fd)
        raise
    return fd


def _open_absolute_directory(path: Path) -> int:
    """Walk an absolute directory path from `/`, rejecting symlink components."""
    if not _secure_dirfd_available():
        raise OSError(errno.ENOTSUP, "descriptor-relative no-follow I/O is unavailable")
    current = os.open("/", os.O_RDONLY | _O_DIRECTORY | _O_NOFOLLOW)
    try:
        for part in path.parts[1:]:
            next_fd = _open_directory_at(part, current)
            os.close(current)
            current = next_fd
        return current
    except BaseException:
        os.close(current)
        raise


def _open_parent(root: Path, relative: Path, *, create: bool) -> tuple[int, str]:
    if not relative.parts or relative.is_absolute() or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise ValueError("config path must be a normalized relative path")
    parent_fd = _open_absolute_directory(root)
    try:
        for part in relative.parts[:-1]:
            try:
                next_fd = _open_directory_at(part, parent_fd)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, 0o700, dir_fd=parent_fd)
                next_fd = _open_directory_at(part, parent_fd)
            os.close(parent_fd)
            parent_fd = next_fd
        return parent_fd, relative.parts[-1]
    except BaseException:
        os.close(parent_fd)
        raise


def _path(root_value: str, value: str, *, must_exist: bool) -> tuple[Path, Path]:
    root = Path(root_value).resolve(strict=True)
    relative = Path(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("config path must be a normalized relative path")
    if not _secure_dirfd_available():
        raise OSError(errno.ENOTSUP, "descriptor-relative no-follow I/O is unavailable")
    return root, relative


def _read(root: Path, relative: Path) -> object:
    parent_fd, leaf = _open_parent(root, relative, create=False)
    fd: int | None = None
    try:
        fd = os.open(
            leaf,
            os.O_RDONLY | _O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0),
            dir_fd=parent_fd,
        )
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_CONFIG_BYTES:
            raise ValueError("config artifact must be a regular file under 1 MiB")
        data = bytearray()
        while len(data) <= _MAX_CONFIG_BYTES:
            chunk = os.read(fd, min(65536, _MAX_CONFIG_BYTES + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) > _MAX_CONFIG_BYTES:
            raise ValueError("config artifact exceeds 1 MiB")
    finally:
        try:
            if fd is not None:
                os.close(fd)
        finally:
            os.close(parent_fd)
    return json.loads(bytes(data).decode("utf-8"))


def _write_new(root: Path, relative: Path, payload: bytes) -> None:
    parent_fd, leaf = _open_parent(root, relative, create=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | _O_NOFOLLOW
    fd: int | None = None
    created_identity: tuple[int, int] | None = None
    try:
        fd = os.open(leaf, flags, 0o600, dir_fd=parent_fd)
        own_info = os.fstat(fd)
        if not stat.S_ISREG(own_info.st_mode):
            raise OSError(errno.EINVAL, "created config target is not a regular file")
        created_identity = (own_info.st_dev, own_info.st_ino)
        view = memoryview(payload)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError(errno.EIO, "short write while creating config artifact")
            view = view[written:]
        os.fsync(fd)
        published_info = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISREG(published_info.st_mode) or (
            published_info.st_dev,
            published_info.st_ino,
        ) != created_identity:
            raise OSError(errno.EPERM, "config leaf changed during creation")
        os.fsync(parent_fd)
    except BaseException:
        if created_identity is not None:
            try:
                current_info = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
                if (current_info.st_dev, current_info.st_ino) == created_identity:
                    os.unlink(leaf, dir_fd=parent_fd)
                    os.fsync(parent_fd)
            except OSError:
                pass
        raise
    finally:
        try:
            if fd is not None:
                os.close(fd)
        finally:
            os.close(parent_fd)


def _emit(payload: object) -> None:
    print(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "validate", "explain"))
    parser.add_argument("--root", required=True)
    parser.add_argument("--path", required=True)
    args = parser.parse_args(argv)
    try:
        root, relative = _path(args.root, args.path, must_exist=args.action != "init")
        path = root / relative
        if args.action == "init":
            result = config_init()
            if is_refusal(result):
                print(f"refused: {result.context}", file=sys.stderr)
                return 2
            _write_new(
                root,
                relative,
                (json.dumps(result.value.fp1_identity(), sort_keys=True, indent=2) + "\n").encode(),
            )
            _emit(
                {
                    "artifact": str(path),
                    "class": "resolved-node-config",
                    "message": (
                        "blank schema scaffold written; blank rows block boot and live binding"
                    ),
                    "row_count": len(result.value.rows),
                    "status": "scaffolded_not_boot_ready",
                }
            )
            return 0
        artifact = _read(root, relative)
        checked = config_validate(artifact)
        if is_refusal(checked):
            print(f"refused: {checked.context}", file=sys.stderr)
            return 2
        explained = config_explain(checked.value)
        if is_refusal(explained):
            print(f"refused: {explained.context}", file=sys.stderr)
            return 2
        detail = explained.value
        detail["artifact_path"] = str(path)
        detail["status"] = (
            "schema_valid_boot_blocked" if not checked.value.may_boot() else "schema_valid"
        )
        if not checked.value.may_boot():
            detail["operator_message"] = (
                "schema is valid, but unresolved/blank rows still block boot; this is not a "
                "configured-runtime assessment"
            )
        if args.action == "explain":
            _emit(detail)
            return 0
        _emit(
            {
                "artifact_path": str(path),
                "boot_blocking": detail["boot_blocking"],
                "fingerprint": detail["fingerprint"],
                "live_blocking": detail["live_blocking"],
                "may_boot": detail["may_boot"],
                "may_bind_role_live": detail["may_bind_role_live"],
                "row_count": detail["row_count"],
                "status": detail["status"],
            }
        )
        return 0 if checked.value.may_boot() else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(
            f"refused: config file unavailable or invalid ({type(exc).__name__})",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
