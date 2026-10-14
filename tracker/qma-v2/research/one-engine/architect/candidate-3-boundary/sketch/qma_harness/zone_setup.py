"""Provision, audit and share for the agent zone, per OS.

`qmx zone setup` runs `plan_setup` then `apply` once with elevation (admin
PowerShell on Windows, sudo on macOS and Linux). Everything after setup runs
without elevation: shares are owner-level ACL edits, the service restarts
itself, and the link carries all control.

Invariants:
- `plan_setup` is pure. It returns the full step list for an OS; the
  executor observes each step's current state and acts only on a difference,
  so re-running setup converges and a crash halfway is repaired by the next run.
- The zone account is a standard account: not an administrator, not in
  `staff` (macOS), not in `sudo`/`wheel` (Linux), no interactive shell on
  macOS and Linux.
- The zone runtime folder is owned by the operator and read-and-execute for
  the zone, so the operator updates it without elevation and the zone cannot
  change the code it runs.
- Protected roots get an explicit deny (Windows) or mode/ACL change (POSIX)
  for the zone account. Shares are explicit allows below them; on Windows an
  explicit allow on a child beats an inherited deny.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from qma_harness.model import AclFinding, BoundaryVerdict, Share

OsKind = Literal["windows", "macos", "linux"]


@dataclass(frozen=True)
class ZoneAccount:
    os: OsKind
    name: str  # "qmx-agent" on Windows and Linux, "_qmxagent" on macOS
    home: Path  # C:/Users/qmx-agent, /var/qmx-agent, /var/lib/qmx-agent
    runtime: Path  # C:/ProgramData/QMX/zone, /Library/Application Support/QMX/zone, /opt/qmx/zone
    state: Path  # holds the zone credential file; operator RW, zone R
    service: str  # QMXZone, ai.qmx.zone, qmx-zone.service


@dataclass(frozen=True)
class SetupSettings:
    operator: str  # the operator's account name
    memory_cap_mb: int
    door_port: int
    protected_roots: tuple[Path, ...]  # operator home, ~/.qmx, dev roots, non-system volume roots
    default_share: Path  # ~/QMX Workspace, operator-owned, zone write


# ------------------------------------------------------------------ steps


@dataclass(frozen=True)
class CreateAccount:
    """Windows: New-LocalUser, standard, password chosen by the operator in the
    setup prompt (kept by SCM for the service logon and by the operator for the
    native sign-in fallback; QMA does not store it). Works on Windows Home.
    macOS: dscl role user with UID < 500 and IsHidden, shell /usr/bin/false,
    own primary group. Linux: useradd --system --create-home, shell nologin."""

    account: ZoneAccount


@dataclass(frozen=True)
class GrantServiceLogon:
    """Windows only. SeServiceLogonRight via LsaAddAccountRights (no secpol on Home)."""

    account: ZoneAccount


@dataclass(frozen=True)
class HideFromSignIn:
    """Windows only. Winlogon SpecialAccounts\\UserList value 0."""

    account: ZoneAccount


@dataclass(frozen=True)
class InstallRuntime:
    """Create a venv in `runtime` with Python, the pinned claude-agent-sdk
    wheel, qma_zone_wire and qma_zone. Owner operator; zone read and execute."""

    account: ZoneAccount
    sdk_version: str


@dataclass(frozen=True)
class SetAcl:
    path: Path
    principal: str
    rights: Literal["none", "read", "write", "traverse"]
    kind: Literal["allow", "deny"]


@dataclass(frozen=True)
class WriteZoneCredential:
    """32 random bytes. File in `state`, operator RW and zone R. Same value in
    the operator keyring at qmx/zone-credential for the door's check."""

    account: ZoneAccount


@dataclass(frozen=True)
class InstallService:
    """Windows: service running as .\\qmx-agent, automatic start, restart on
    failure. The runner puts itself in a Job Object with a job memory limit and
    kill-on-close at start, so every CLI and Bash child is capped and dies with it.
    macOS: /Library/LaunchDaemons/ai.qmx.zone.plist with UserName, KeepAlive,
    RunAtLoad. No whole-zone memory cap exists; the harness caps live threads.
    Linux: /etc/systemd/system/qmx-zone.service with User=, Restart=always,
    MemoryMax=, TasksMax=, NoNewPrivileges=yes, PrivateTmp=yes."""

    account: ZoneAccount
    memory_cap_mb: int
    door_port: int


@dataclass(frozen=True)
class PrepareKeychain:
    """macOS only, and only if check M1 shows the CLI cannot store its login
    without a keychain. Creates a keychain file in the zone home, sets it as the
    zone account's default and disables auto-lock. Its password sits in a 0600
    file in the zone home and the runner unlocks it at start. QMA handles the
    keychain password, never the Claude token inside it."""

    account: ZoneAccount


@dataclass(frozen=True)
class StartService:
    account: ZoneAccount


SetupStep = (
    CreateAccount | GrantServiceLogon | HideFromSignIn | InstallRuntime | SetAcl
    | WriteZoneCredential | InstallService | PrepareKeychain | StartService
)


def plan_setup(os: OsKind, settings: SetupSettings) -> tuple[SetupStep, ...]:
    """Pure. The ordered step list for one OS.

    Windows: CreateAccount, GrantServiceLogon, HideFromSignIn, InstallRuntime,
    SetAcl(deny read+write for each protected root, including each non-system
    fixed volume root such as D:/), SetAcl(allow write on the default share),
    WriteZoneCredential, InstallService, StartService.

    macOS: CreateAccount, InstallRuntime, SetAcl(chmod 750 on the operator home
    with group staff; 700 on ~/.qmx), SetAcl(+a allow on the default share and
    search on its parents), WriteZoneCredential, PrepareKeychain (conditional),
    InstallService, StartService.

    Linux: CreateAccount, InstallRuntime, SetAcl(750 on the operator home, 700
    on ~/.qmx), SetAcl(setfacl u:qmx-agent:rwX plus default ACL on the share,
    u:qmx-agent:x on its parents), WriteZoneCredential, InstallService,
    StartService.
    """
    raise NotImplementedError


@dataclass(frozen=True)
class StepResult:
    step: SetupStep
    outcome: Literal["already_done", "applied", "failed"]
    detail: str


def apply(plan: tuple[SetupStep, ...]) -> tuple[StepResult, ...]:
    """Elevated. Observe each step, act on a difference, record the result.
    Stops at the first failure; re-running resumes from there."""
    raise NotImplementedError


def audit(account: ZoneAccount, settings: SetupSettings,
          shares: tuple[Share, ...]) -> tuple[AclFinding, ...]:
    """Outside-in, no elevation. Reads effective rights of the zone account on
    each protected root, each share, the zone runtime, the qmx-control install
    and its venv, and the Python the operator side runs. Windows uses the
    effective-access API; POSIX uses stat plus ACL listing."""
    raise NotImplementedError


def loopback_listeners(operator: str) -> tuple[str, ...]:
    """Outside-in. Loopback TCP listeners owned by the operator's account,
    other than qmx-control's operator API, which requires the operator bearer.
    Each one is a service the zone could reach. Reported, not blocked."""
    raise NotImplementedError


def verdict(acl: tuple[AclFinding, ...], probe: tuple[str, ...],
            loopback: tuple[str, ...]) -> BoundaryVerdict:
    """Pure. Sealed only if every finding matches its expectation, the probe
    reached nothing protected, and no unexpected listener exists."""
    raise NotImplementedError


def share(path: Path, access: Literal["read", "write"], account: ZoneAccount) -> Share:
    """No elevation. The operator owns `path`, so he can add the allow entry.
    Windows: icacls grant with inheritance. macOS: chmod +a, plus search on
    parents. Linux: setfacl, default ACL, plus x on parents. Idempotent."""
    raise NotImplementedError


def unshare(target: Share, account: ZoneAccount) -> None:
    raise NotImplementedError


def teardown(account: ZoneAccount) -> tuple[StepResult, ...]:
    """Elevated. Stop and remove the service, remove ACL entries, remove the
    account. Keeps the zone home unless the operator asks, since it holds
    transcripts."""
    raise NotImplementedError
