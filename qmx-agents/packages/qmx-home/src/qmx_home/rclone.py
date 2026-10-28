"""The one rclone runner on this PC (design 06 section 3). Standard library only.

It finds the binary (`[backup] rclone_path`, then `PATH`, then the pinned release fetched into
`cache/tools/rclone/` and checked against its published sha256) and refuses one older than
`MINIMUM`. Every call that needs remotes reads `data/rclone.conf`, which is encrypted with a
password QMX makes on first use and keeps in the key store as `qmx/rclone-config`; he never types
it. No secret is ever in a command line: the conf password, a key from the key store and an
answer to rclone's question loop each reach that one call in its environment, and an
`IsPassword` answer is obscured through `rclone obscure -` on stdin first, because rclone stores
a loop answer as given and a clear password makes a remote that cannot open (SYNC-PLAN
Appendix A). A call returns its exit code, one plain line and a failure sorted from the exit code
and rclone's JSON log; rclone's own text reaches no caller's screen. The record holds each call's
arguments with every `name=value` value masked, and the names of the variables it was given.

A conf that cannot be opened (its password is gone from the key store, or no longer matches) is
set aside once as `rclone.conf.unreadable-<stamp>`, so it never becomes a lock: the next call
starts a new conf and each storage on the old one is connected again.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import platform
import re
import secrets as tokens
import shutil
import subprocess
import sys
import threading
import urllib.request
import zipfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Final, Literal, Protocol, cast

from qmx_home import Layout

type Failure = Literal["offline", "signin", "full", "missing", "other"]
type Version = tuple[int, int, int]

CONF: Final = "rclone.conf"
UNREADABLE: Final = "rclone.conf.unreadable-"
CONFIG_KEY: Final = "qmx/rclone-config"
ENCRYPTED: Final = "RCLONE_ENCRYPT_V0:"
TOOLS: Final = ("tools", "rclone")
"""Under `cache/`: where the pinned release is unpacked."""


@dataclass(frozen=True, slots=True)
class Pinned:
    version: Version
    releases: Mapping[str, str]
    """The published sha256 of each platform's zip, by its name in the release (`windows-amd64`)."""
    base: str = "https://downloads.rclone.org"

    def url(self, system: str) -> str:
        tag = "v" + ".".join(map(str, self.version))
        return f"{self.base}/{tag}/rclone-{tag}-{system}.zip"


PINNED: Final = Pinned(
    (1, 75, 2),
    {
        "windows-amd64": "8a9db2bad1dc79a65b3348fd857069598e2aab7cf4d118b77b1df23055aff818",
        "windows-arm64": "7eb9844c9e5b723b9ef28821891caa17f6d9d1a375c49365cbe04114cec8dcd9",
        "linux-amd64": "349ac8fba6ff65d6247043f1750cdcb518ec5d500ef91463a10d37c0ccdf3702",
        "linux-arm64": "7e1e8d69654941b7b7df84ee74c5f7fb09cce7d5496947fb7bf16b55ff427d10",
        "osx-amd64": "574e1f31cf1c464e5fb0325cb66fcbdeaf1efa1802bd9b17f13c256fd74b6561",
        "osx-arm64": "610ab7d48615135dfc60b763858b11a426a0d3d1160c1bb76fb0ae6011b02edd",
    },
)
"""rclone v1.75.2, the version on his PC, with the hashes of its published SHA256SUMS."""
MINIMUM: Final[Version] = (1, 75, 2)

LINES: Final[Mapping[Failure, str]] = {
    "offline": "could not be reached; check the connection, and QMX tries again at the next sync",
    "signin": "needs you to sign in again",
    "full": "is full; make room there or choose another storage",
    "missing": "was not found; connect it again",
    "other": "did not answer as expected",
}
UNREADABLE_LINE: Final = (
    "the storages' settings on this PC could not be opened, so QMX set them aside as {name}; "
    "connect each storage again"
)
_SORTED: Final[tuple[tuple[Failure, re.Pattern[str]], ...]] = (
    (
        "signin",
        re.compile(
            r"invalid_grant|token (has )?expired|reauthenticat|couldn't fetch token|"
            r"oauth2: |401 unauthorized|invalid_client",
            re.IGNORECASE,
        ),
    ),
    (
        "full",
        re.compile(
            r"quota|insufficient storage|no space left|not enough space|disk full", re.IGNORECASE
        ),
    ),
    (
        "offline",
        re.compile(
            r"no such host|connection refused|actively refused|network is unreachable|"
            r"i/o timeout|timed out|dial tcp|connectex",
            re.IGNORECASE,
        ),
    ),
    (
        "missing",
        re.compile(
            r"directory not found|object not found|not found|nosuchbucket|"
            r"didn't find section in config file",
            re.IGNORECASE,
        ),
    ),
)
_BY_CODE: Final[Mapping[int, Failure]] = {3: "missing", 4: "missing", 5: "offline"}
"""rclone's documented exit codes: 3 a directory not found, 4 a file not found, 5 a temporary
error that a retry may fix."""
_UNDECRYPTABLE: Final = re.compile(r"unable to decrypt configuration|couldn't decrypt", re.I)


class Keys(Protocol):
    """The key store, by name; `qmx_broker.credentials.CredentialManager` on this PC."""

    def read(self, name: str) -> str | None: ...
    def replace(self, name: str, value: str) -> None: ...


class RcloneRefused(Exception):
    """No rclone this PC can use. The message is the one line to show."""


@dataclass(frozen=True, slots=True)
class Ran:
    code: int
    line: str
    """Empty when the call succeeded; otherwise what happened, in plain words, to follow the
    storage's name ("`<storage>` could not be reached; ...")."""
    failure: Failure | None
    out: str = field(default="", repr=False)
    """rclone's standard output, for the caller's own parsing only; never shown or logged."""


@dataclass(frozen=True, slots=True)
class Call:
    """One call as the record keeps it: arguments with every `name=value` value masked, and the
    names (never the values) of the variables it was handed."""

    args: tuple[str, ...]
    env: tuple[str, ...]


type Fetch = Callable[[str], bytes]


def _download(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=300) as response:  # noqa: S310 - a pinned https URL
        return response.read()


class Rclone:
    """rclone for one QMX folder. `keys` holds the conf's password; `path` is
    `[backup] rclone_path` (empty for none); `which` and `fetch` find and download a binary."""

    def __init__(
        self,
        layout: Layout,
        *,
        keys: Keys,
        path: str = "",
        which: Callable[[str], str | None] = shutil.which,
        fetch: Fetch = _download,
        pinned: Pinned = PINNED,
        minimum: Version = MINIMUM,
    ) -> None:
        self.layout = layout
        self.keys = keys
        self.path = path
        self.which = which
        self.fetch = fetch
        self.pinned = pinned
        self.minimum = minimum
        self.record: list[Call] = []
        self.set_aside: Path | None = None
        """The conf this runner set aside, once it did."""
        self._binary: Path | None = None
        self._lock = threading.Lock()

    @property
    def conf(self) -> Path:
        return self.layout.data / CONF

    def found(self) -> Path | None:
        """A usable binary already on this PC, without fetching one. Raises RcloneRefused for
        one older than the minimum."""
        if self._binary is not None:
            return self._binary
        for candidate in self._candidates():
            if candidate.is_file():
                self._usable(candidate)
                self._binary = candidate
                return candidate
        return None

    def binary(self) -> Path:
        """The binary every call runs, fetching the pinned release when this PC has none.
        Raises RcloneRefused with the line to show."""
        with self._lock:
            found = self.found()
            if found is not None:
                return found
            fetched = self._fetched()
            self._usable(fetched)
            self._binary = fetched
            return fetched

    def version(self) -> Version:
        return _version(self._bare(self.binary(), ["version"]).out)

    def obscure(self, value: str) -> str:
        """`value` as rclone stores a password, read from stdin so no command line holds it."""
        ran = self._bare(self.binary(), ["obscure", "-"], stdin=value)
        if ran.code:
            raise RcloneRefused("rclone could not prepare the answer; try again")
        return ran.out.strip()

    def run(
        self,
        args: Sequence[str],
        *,
        secrets: Mapping[str, str] | None = None,
        answer: str | None = None,
        password: bool = False,
        watch: Callable[[str], None] | None = None,
        cancel: threading.Event | None = None,
    ) -> Ran:
        """One rclone call on this folder's conf. `secrets` are variables for this call only
        (`RCLONE_CONFIG_<REMOTE>_<OPTION>`); `answer` is the loop's answer, passed as
        `RCLONE_RESULT` and obscured first when `password`. `watch` sees each line rclone logs
        while it runs; `cancel` stops it."""
        binary = self.binary()
        env = {**self._ready(), **(secrets or {})}
        if answer is not None:
            env["RCLONE_RESULT"] = self.obscure(answer) if password and answer else answer
        ran = self._call(binary, [*self._config(self.conf), *args], env, watch=watch, cancel=cancel)
        if ran.code and self._undecryptable(ran):
            name = self._set_aside()
            return Ran(ran.code, UNREADABLE_LINE.format(name=name), "missing")
        return ran

    def secrets_for(self, remote: str, option: str, reference: str) -> dict[str, str]:
        """The variable that hands `remote`'s `option` the key `reference` names, for one call.
        Empty when the key store does not hold it."""
        value = self.keys.read(reference)
        if value is None:
            return {}
        return {f"RCLONE_CONFIG_{remote.upper()}_{option.upper()}": value}

    def check_conf(self) -> Path | None:
        """Set the conf aside when the key store no longer holds its password, without a call.
        The conf set aside, or None."""
        if self.keys.read(CONFIG_KEY) is None and _encrypted(self.conf):
            self._set_aside()
        return self.set_aside

    def _candidates(self) -> list[Path]:
        named = [Path(self.path)] if self.path.strip() else []
        on_path = self.which("rclone")
        return [*named, *([Path(on_path)] if on_path else []), self._cached()]

    def _cached(self) -> Path:
        return self.layout.cache.joinpath(*TOOLS, "rclone.exe" if os.name == "nt" else "rclone")

    def _usable(self, binary: Path) -> None:
        version = _version(self._bare(binary, ["version"]).out)
        if version < self.minimum:
            raise RcloneRefused(
                f"the rclone at {binary} is version {_dotted(version)}, older than "
                f"{_dotted(self.minimum)}, which QMX needs; remove it or name a newer one in "
                "Settings"
            )

    def _fetched(self) -> Path:
        system = _system()
        expected = self.pinned.releases.get(system)
        if expected is None:
            raise RcloneRefused(
                f"QMX has no rclone release for this computer ({system}); install rclone and "
                "name it in Settings"
            )
        url = self.pinned.url(system)
        try:
            body = self.fetch(url)
        except OSError as error:
            raise RcloneRefused(
                f"QMX could not download rclone from {url} ({type(error).__name__}); check the "
                "connection and try again"
            ) from None
        found = hashlib.sha256(body).hexdigest()
        if found != expected:
            raise RcloneRefused(
                f"the rclone download from {url} did not match its published sha256 {expected} "
                f"(it was {found}); nothing was installed"
            )
        target = self._cached()
        target.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            member = next(
                (
                    n
                    for n in archive.namelist()
                    if n.rsplit("/", 1)[-1].casefold() == target.name.casefold()
                ),
                None,
            )
            if member is None:
                raise RcloneRefused(f"the rclone download from {url} holds no {target.name}")
            staged = target.with_suffix(".new")
            staged.write_bytes(archive.read(member))
        staged.chmod(0o755)
        staged.replace(target)
        return target

    def _ready(self) -> dict[str, str]:
        """The conf's password for this call, made on first use, with the conf encrypted before
        any remote is written to it."""
        password = self.keys.read(CONFIG_KEY)
        if password is None and _encrypted(self.conf):
            self._set_aside()
        if password is None:
            password = tokens.token_urlsafe(32)
            self.keys.replace(CONFIG_KEY, password)
        env = {"RCLONE_CONFIG_PASS": password}
        if not _encrypted(self.conf):
            self.conf.parent.mkdir(parents=True, exist_ok=True)
            self.conf.touch()
            script = f"import os,sys;sys.stdout.write(os.environ[{_NEW!r}])"
            command = f'"{sys.executable}" -I -c "{script}"'
            self._call(
                self.binary(),
                [*self._config(self.conf), "config", "encryption", "set"],
                {_NEW: password, "RCLONE_PASSWORD_COMMAND": command},
            )
            if not _encrypted(self.conf):
                raise RcloneRefused(
                    f"QMX could not protect {self.conf}; no storage was written to it"
                )
        return env

    def _undecryptable(self, ran: Ran) -> bool:
        return ran.failure == "other" and _encrypted(self.conf) and ran.line == _DECRYPT

    def _set_aside(self) -> Path:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        aside = self.conf.with_name(UNREADABLE + stamp)
        self.conf.replace(aside)
        self.set_aside = aside
        return aside

    @staticmethod
    def _config(conf: Path) -> list[str]:
        return ["--config", str(conf), "--ask-password=false", "--use-json-log"]

    def _bare(self, binary: Path, args: Sequence[str], *, stdin: str | None = None) -> Ran:
        """A call that needs no remote, on no conf at all."""
        return self._call(binary, ["--config", "", "--ask-password=false", *args], {}, stdin=stdin)

    def _call(
        self,
        binary: Path,
        args: Sequence[str],
        given: Mapping[str, str],
        *,
        stdin: str | None = None,
        watch: Callable[[str], None] | None = None,
        cancel: threading.Event | None = None,
    ) -> Ran:
        self.record.append(Call(tuple(_masked(args)), tuple(sorted(given))))
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("RCLONE_")}
        child = subprocess.Popen(
            [str(binary), *args],
            stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={**env, **given},
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        out: list[bytes] = []
        log: list[str] = []
        streams = cast("tuple[IO[bytes], IO[bytes]]", (child.stdout, child.stderr))

        def read_out() -> None:
            out.append(streams[0].read())

        def read_log() -> None:
            for raw in streams[1]:
                text = raw.decode("utf-8", "replace").rstrip()
                log.append(text)
                if watch is not None:
                    watch(_message(text))

        readers = [threading.Thread(target=t, daemon=True) for t in (read_out, read_log)]
        for reader in readers:
            reader.start()
        if stdin is not None:
            given_in = cast("IO[bytes]", child.stdin)
            given_in.write(stdin.encode("utf-8"))
            given_in.close()
        while child.poll() is None:
            if cancel is not None and cancel.wait(0.1):
                child.kill()
            elif cancel is None:
                child.wait()
        for reader in readers:
            reader.join()
        code = child.returncode
        text = b"".join(out).decode("utf-8", "replace")
        if code == 0:
            return Ran(0, "", None, text)
        messages = [_message(line) for line in log]
        if any(_UNDECRYPTABLE.search(m) for m in messages):
            return Ran(code, _DECRYPT, "other", text)
        failure = _sort(code, messages)
        return Ran(code, LINES[failure], failure, text)


_NEW: Final = "QMX_RCLONE_NEW_PASSWORD"
"""The variable the one-off password command prints, when a new conf is encrypted: rclone reads a
new password only through `RCLONE_PASSWORD_COMMAND`."""
_DECRYPT: Final = "the storages' settings on this PC could not be opened"


def _sort(code: int, messages: Sequence[str]) -> Failure:
    for failure, pattern in _SORTED:
        if any(pattern.search(m) for m in messages):
            return failure
    return _BY_CODE.get(code, "other")


def _message(line: str) -> str:
    """The message of one rclone log line, JSON or plain."""
    try:
        found: object = json.loads(line)
    except ValueError:
        return line
    message = cast("dict[str, object]", found).get("msg") if isinstance(found, dict) else None
    return message if isinstance(message, str) else line


def _masked(args: Sequence[str]) -> list[str]:
    return [f"{a.split('=', 1)[0]}=..." if "=" in a and not a.startswith("-") else a for a in args]


def _encrypted(conf: Path) -> bool:
    try:
        with conf.open("rb") as file:
            head = file.read(256)
    except OSError:
        return False
    return ENCRYPTED.encode() in head


def _version(text: str) -> Version:
    found = re.search(r"rclone v(\d+)\.(\d+)\.(\d+)", text)
    if found is None:
        raise RcloneRefused("this rclone did not say its version; install rclone again")
    major, minor, patch = (int(part) for part in found.groups())
    return major, minor, patch


def _dotted(version: Version) -> str:
    return ".".join(map(str, version))


def _system() -> str:
    name = {"win32": "windows", "darwin": "osx"}.get(sys.platform, sys.platform)
    machine = platform.machine().lower()
    arch = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}
    return f"{name}-{arch.get(machine, machine)}"
