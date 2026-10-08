"""T2 keeps lifecycle and MCP handling in the local supervisor, isolation in Docker."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import tempfile
import time
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from typing import Any

import keyring
from fastmcp.client.transports import StdioTransport

from qmx_apps.errors import AppError
from qmx_apps.manifest import Definition, image_files
from qmx_apps.supervisor import EventSink, Instance, Supervisor
from qmx_apps.volume import Volume, VolumeLease

BASE = (
    "ghcr.io/astral-sh/uv:0.12.23-python3.14-trixie-slim@sha256:"
    "8e88a074b0969bdc461f681727238e109438d70771828909f9ef19cfcc96c43a"
)
UBUNTU = "ubuntu:24.04@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55"
PROXY_IMAGE = "qmx-egress:squid-ubuntu24.04"


def docker(*args: str, env: dict[str, str] | None = None, required: bool = True) -> str:
    executable = shutil.which("docker")
    if executable is None:
        raise AppError("docker_missing", "Install Docker Engine on this node.", 503)
    result = subprocess.run(
        [executable, *args], capture_output=True, text=True, env=env, check=False, timeout=600
    )
    if required and result.returncode:
        # CLI diagnostics can contain injected credentials; only expose the operation.
        raise AppError("docker_failed", f"Docker {args[0]} failed; check the node engine.", 503)
    return result.stdout.strip() if result.returncode == 0 else ""


def proxy_config(hosts: list[str]) -> str:
    for host in hosts:
        if not re.fullmatch(r"[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", host):
            raise AppError("invalid_network", "T2 network entries must be exact DNS hostnames.")
    lines = [
        "http_port 3128",
        "acl safe_ports port 80 443",
        "acl tls_ports port 443",
        "acl connect method CONNECT",
        "acl private dst 0.0.0.0/8 10.0.0.0/8 127.0.0.0/8 169.254.0.0/16 "
        "172.16.0.0/12 192.168.0.0/16 ::1 fc00::/7 fe80::/10",
        "http_access deny !safe_ports",
        "http_access deny connect !tls_ports",
        "http_access deny private",
    ]
    if hosts:
        lines.extend(["acl declared dstdomain -n " + " ".join(hosts), "http_access allow declared"])
    lines.extend(
        [
            "http_access deny all",
            "cache deny all",
            "access_log stdio:/dev/stdout",
            "cache_log /dev/stderr",
            "pid_filename /tmp/squid.pid",
            "coredump_dir /tmp",
        ]
    )
    return "\n".join(lines) + "\n"


def build_image(definition: Definition) -> str:
    tag = f"qmx-app:{definition.hash}"
    with tempfile.TemporaryDirectory(prefix="qmx-docker-") as temporary:
        context = Path(temporary)
        for source in image_files(definition.root):
            target = context / "image" / source.relative_to(definition.root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copyfile(Path(__file__).with_name("bootstrap.py"), context / "bootstrap.py")
        (context / "Dockerfile").write_text(
            f"FROM {BASE} AS build\n"
            "RUN apt-get update && apt-get install -y --no-install-recommends git "
            "&& rm -rf /var/lib/apt/lists/*\n"
            "COPY image /image\nWORKDIR /image\n"
            "ENV UV_PROJECT_ENVIRONMENT=/opt/app-env UV_PYTHON_DOWNLOADS=never\n"
            "RUN uv sync --frozen --no-dev --no-editable --no-install-project\n"
            f"FROM {BASE}\n"
            "COPY --from=build /opt/app-env /opt/app-env\n"
            "COPY image /image\nCOPY bootstrap.py /bootstrap.py\n"
            "ENV PATH=/opt/app-env/bin:/usr/local/bin:/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1\n"
            'WORKDIR /volume\nENTRYPOINT ["/opt/app-env/bin/python", "/bootstrap.py"]\n',
            encoding="utf-8",
        )
        docker("build", "--tag", tag, str(context))
    return tag


def build_proxy() -> None:
    if docker("image", "inspect", PROXY_IMAGE, required=False):
        return
    with tempfile.TemporaryDirectory(prefix="qmx-proxy-") as temporary:
        (Path(temporary) / "Dockerfile").write_text(
            f"FROM {UBUNTU}\n"
            "RUN apt-get update && apt-get install -y --no-install-recommends "
            "squid ca-certificates "
            "&& rm -rf /var/lib/apt/lists/*\n"
            'ENTRYPOINT ["squid", "-N", "-f", "/etc/squid/qmx.conf"]\n',
            encoding="utf-8",
        )
        docker("build", "--tag", PROXY_IMAGE, temporary)


class DockerSupervisor(Supervisor):
    tier = "T2"

    def __init__(
        self,
        home: Path,
        *,
        node: str = "node",
        replicas: dict[str, str] | None = None,
        event_sink: EventSink | None = None,
        secret_getter: Callable[[str, str], str | None] = keyring.get_password,
        proof_mode: str = "",
    ) -> None:
        super().__init__(
            home, event_sink=event_sink, secret_getter=secret_getter, proof_mode=proof_mode
        )
        self.node = node
        self.replicas = replicas or {}
        self._resources: dict[str, list[tuple[str, str]]] = {}
        self._stderr_lines: dict[str, int] = {}

    def _install_environment(self, definition: Definition, image: Path) -> None:
        proxy_config(definition.manifest.capabilities.network)
        build_image(definition)
        if definition.manifest.capabilities.network:
            build_proxy()

    def transport(
        self, instance: Instance, config: dict[str, Any], environment: dict[str, str]
    ) -> StdioTransport:
        manifest = instance.definition.manifest
        if manifest.id in self.replicas:
            # A second checkpointer requires SQLite's WAL-reset fix in the app writer.
            version = tuple(
                int(part)
                for part in docker(
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "--read-only",
                    "--entrypoint",
                    "/opt/app-env/bin/python",
                    f"qmx-app:{instance.definition.hash}",
                    "-c",
                    "import sqlite3; print(sqlite3.sqlite_version)",
                ).split(".")
            )
            if not (version >= (3, 51, 3) or (3, 50, 7) <= version < (3, 51, 0)):
                raise AppError(
                    "sqlite_version",
                    "Litestream requires a SQLite 3.51.3 or 3.50.7 writer.",
                    409,
                )
        instance.node = self.node
        name = f"qmx-{instance.id}"
        resources = self._resources.setdefault(instance.id, [])
        # A new network per instance prevents access to other app volumes/services.
        network = "none"
        if manifest.capabilities.network and self.proof_mode not in {"tests", "sandbox"}:
            network = name + "-net"
            docker(
                "network",
                "create",
                "--internal",
                "--opt",
                "com.docker.network.bridge.gateway_mode_ipv4=isolated",
                network,
            )
            resources.append(("network", network))
            proxy = name + "-proxy"
            directory = self.home / "network" / instance.id
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / "squid.conf"
            path.write_text(proxy_config(manifest.capabilities.network), encoding="utf-8")
            docker(
                "create",
                "--name",
                proxy,
                "--network",
                "bridge",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--user",
                "proxy",
                "--tmpfs",
                "/tmp:rw,noexec,nosuid,size=16m",  # noqa: S108 - private container tmpfs
                "--mount",
                f"type=bind,src={path},dst=/etc/squid/qmx.conf,readonly",
                PROXY_IMAGE,
            )
            resources.append(("container", proxy))
            docker("network", "connect", "--alias", "egress", network, proxy)
            docker("start", proxy)
            environment.update(HTTP_PROXY="http://egress:3128", HTTPS_PROXY="http://egress:3128")
            environment.update(http_proxy="http://egress:3128", https_proxy="http://egress:3128")
        environment.update(
            QMX_VOLUME="/volume",
            HOME="/volume",
            USERPROFILE="/volume",
            APPDATA="/volume",
            LOCALAPPDATA="/volume",
            TEMP="/volume/data/tmp",
            TMP="/volume/data/tmp",
            PATH="/opt/app-env/bin:/usr/local/bin:/usr/bin:/bin",
        )
        config.update(image="/image", volume="/volume", env_names=list(environment), tier="T2")
        uid = str(instance.volume.root.stat().st_uid) if os.name == "posix" else "1000"
        gid = str(instance.volume.root.stat().st_gid) if os.name == "posix" else "1000"
        road = instance.volume.root / "road"
        road.mkdir(exist_ok=True)
        options = [
            "create",
            "--name",
            name,
            "--interactive",
            "--network",
            network,
            "--dns",
            "127.0.0.1",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user",
            f"{uid}:{gid}",
            "--pids-limit",
            "128",
            "--memory",
            f"{manifest.budget.memory_mb}m",
            "--memory-swap",
            f"{manifest.budget.memory_mb}m",
            "--cpus",
            str(manifest.budget.cpu_percent / 100),
            "--mount",
            f"type=bind,src={instance.volume.root},dst=/volume",
            # Native app code must not rewrite the host's publication authority.
            "--mount",
            f"type=bind,src={road},dst=/volume/road,readonly",
        ]
        for key in environment:
            options.extend(["--env", key])
        docker(
            *options,
            f"qmx-app:{instance.definition.hash}",
            json.dumps(config),
            env={**os.environ, **environment},
        )
        resources.append(("container", name))
        if manifest.id in self.replicas:
            replica = self.replicas[manifest.id]
            if not replica.startswith(("s3://", "file://")) or "@" in replica:
                raise AppError(
                    "invalid_replica", "Use an S3 or local file replica without credentials."
                )
            sidecar = name + "-litestream"
            directory = self.home / "replicas" / instance.id
            directory.mkdir(parents=True, exist_ok=True)
            configuration = directory / "litestream.yml"
            configuration.write_text(
                "sync-interval: 1s\nsnapshot:\n  interval: 24h\n  retention: 24h\n"
                "dbs:\n  - path: /volume/app.db\n    replica:\n      url: "
                + json.dumps(replica)
                + "\n",
                encoding="utf-8",
            )
            options = [
                "create",
                "--name",
                sidecar,
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--mount",
                f"type=bind,src={instance.volume.root},dst=/volume",
                "--mount",
                f"type=bind,src={configuration},dst=/etc/litestream.yml,readonly",
            ]
            for key in manifest.capabilities.secrets:
                options.extend(["--env", key])
            docker(
                *options,
                "litestream/litestream:0.5.17",
                "replicate",
                env={**os.environ, **environment},
            )
            resources.append(("container", sidecar))
            docker("start", sidecar)
        instance.limits = {
            "memory_mb": manifest.budget.memory_mb,
            "cpu_percent": manifest.budget.cpu_percent,
            "cpu_seconds": manifest.budget.cpu_seconds,
            "network": "isolated bridge + Squid" if network != "none" else "none",
        }
        executable = shutil.which("docker")
        if executable is None:
            raise AppError("docker_missing", "Install Docker Engine.", 503)
        return StdioTransport(
            command=executable,
            args=["start", "--attach", "--interactive", name],
            env={
                key: value
                for key, value in os.environ.items()
                if key.upper() in {"PATH", "SYSTEMROOT", "HOME", "USERPROFILE"}
            },
            keep_alive=False,
            log_file=instance.volume.root / f"logs/{instance.id}.stderr.log",
        )

    def _log(self, app_id: str, event: str, data: dict[str, Any]) -> None:
        super()._log(app_id, event, data)
        self.emit(app_id, {"app_id": app_id, "type": "log", "event": event, **data})

    def _heartbeat(self, instance: Instance) -> None:
        if instance.id not in self._resources:
            return
        # Read cgroups from outside the app interpreter, including exited children.
        output = docker(
            "exec",
            f"qmx-{instance.id}",
            "sh",
            "-c",
            f"cat /volume/data/heartbeat-{instance.id}.json; printf '\\n'; "
            "cat /sys/fs/cgroup/cpu.stat; cat /sys/fs/cgroup/memory.current",
            required=False,
        )
        if not output:
            return
        try:
            lines = output.splitlines()
            pulse = json.loads(lines[0])
            instance.heartbeat = time.monotonic() - max(0, time.time() - pulse["utc"])
            instance.job_runs = pulse["job_runs"]
            instance.job_errors = pulse["job_errors"]
            instance.cpu = (
                int(next(line.split()[1] for line in lines if line.startswith("usage_usec ")))
                / 1_000_000
            )
            instance.memory = int(lines[-1])
            self._capture_stderr(instance)
        except ValueError, KeyError, StopIteration:
            return

    def kill(self, instance: Instance) -> None:
        resources = self._resources.get(instance.id, [])
        while resources:
            kind, name = resources[-1]
            docker(kind, "rm", *(["--force"] if kind == "container" else []), name)
            resources.pop()
        self._resources.pop(instance.id, None)

    def _capture_stderr(self, instance: Instance) -> None:
        path = instance.volume.root / f"logs/{instance.id}.stderr.log"
        if not path.exists():
            return
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines[self._stderr_lines.get(instance.id, 0) :]:
            redacted = line
            for secret in instance.secrets:
                redacted = redacted.replace(secret, "[redacted]")
            self._log(instance.definition.manifest.id, "stderr", {"message": redacted})
        self._stderr_lines[instance.id] = len(lines)

    def snapshot(self, app_id: str, destination: Path) -> Path:
        definition = self._definition(app_id)
        if app_id in self._instances:
            raise AppError("app_running", "Stop the app before moving its volume.", 409)
        lease = VolumeLease(self.home, app_id)
        try:
            volume = Volume(self.home, app_id)
            target = destination.resolve() / definition.hash
            target.mkdir(parents=True, exist_ok=False)
            hashes: dict[str, str] = {}
            for source in image_files(volume.root):
                relative = source.relative_to(volume.root)
                if source.name.endswith(("-wal", "-shm")) or relative.parts[0] == "logs":
                    continue
                if relative.parts[:2] == ("data", "tmp") or source.name.startswith("heartbeat-"):
                    continue
                output = target / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                if source.suffix == ".db":
                    with (
                        closing(sqlite3.connect(source)) as db,
                        closing(sqlite3.connect(output)) as copy,
                    ):
                        db.backup(copy)
                        if copy.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                            raise AppError("backup_invalid", "SQLite snapshot failed verification.")
                else:
                    shutil.copyfile(source, output)
                hashes[relative.as_posix()] = hashlib.sha256(output.read_bytes()).hexdigest()
            (target / "snapshot.json").write_text(
                json.dumps(
                    {
                        "app_id": app_id,
                        "definition_hash": definition.hash,
                        "files": hashes,
                    }
                ),
                encoding="utf-8",
            )
            return target
        finally:
            lease.close()

    def restore(self, app_id: str, snapshot: Path) -> None:
        definition = self._definition(app_id)
        if app_id in self._instances:
            raise AppError("app_running", "Stop the app before restoring.", 409)
        root = snapshot.resolve()
        data = json.loads((root / "snapshot.json").read_text(encoding="utf-8"))
        if data["app_id"] != app_id or data["definition_hash"] != definition.hash:
            raise AppError("backup_mismatch", "Install the snapshot's definition before restoring.")
        lease = VolumeLease(self.home, app_id)
        try:
            volume = Volume(self.home, app_id)
            if (volume.root / "app.db").exists():
                raise AppError("volume_exists", "Restore onto a fresh node or empty volume.", 409)
            for name, digest in data["files"].items():
                source = (root / name).resolve()
                if not source.is_relative_to(root) or source.is_symlink():
                    raise AppError("backup_invalid", "Snapshot paths must stay inside the backup.")
                volume.check_write(name)
                if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                    raise AppError("backup_invalid", "Snapshot checksum mismatch.")
                if source.suffix == ".db":
                    with closing(sqlite3.connect(source)) as db:
                        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                            raise AppError("backup_invalid", "Snapshot database is corrupt.")
            for name in data["files"]:
                target = volume.check_write(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(root / name, target)
            volume.create(agents=bool(definition.manifest.entrypoints.agents))
        finally:
            lease.close()
