"""Small provider adapters; all execution and shipping lives on the target."""

from __future__ import annotations

import importlib
import json
import shlex
import shutil
import subprocess
from collections.abc import Callable
from typing import Any, Protocol

import keyring

from qmx_remote.models import Document, RemoteError, RunBundle, Status, Target


class ComputeProvider(Protocol):
    def provision(self, run_id: str, bundle: RunBundle) -> Document: ...
    def start(self, handle: Document, secrets: dict[str, str]) -> Document: ...
    def status(self, handle: Document) -> Status: ...
    def logs(self, handle: Document) -> str: ...
    def stop(self, handle: Document) -> None: ...
    def teardown(self, handle: Document) -> None: ...


class SSHProvider:
    def __init__(self, target: Target, bucket: str = ""):
        self.target = target
        self.bucket = bucket

    def _call(self, args: list[str], *, secrets: dict[str, str] | None = None) -> str:
        executable = shutil.which("ssh")
        if executable is None:
            raise RemoteError("Install OpenSSH and configure the target host.")
        # Secrets travel through stdin, never argv, files or diagnostics.
        script = (
            "import json,os,subprocess,sys; d=json.load(sys.stdin); "
            "p=subprocess.run(d['args'],env={**os.environ,**d['env']},"
            "capture_output=True); sys.stdout.buffer.write(p.stdout); sys.exit(p.returncode)"
        )
        result = subprocess.run(
            [
                executable,
                "-T",
                "-o",
                "BatchMode=yes",
                "--",
                self.target.host,
                "python3 -c " + shlex.quote(script),
            ],
            input=json.dumps({"args": args, "env": secrets or {}}).encode(),
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode:
            raise RemoteError("SSH node operation failed; check its image and node configuration.")
        return result.stdout.decode("utf-8").strip()

    def provision(self, run_id: str, bundle: RunBundle) -> Document:
        if not self.target.image:
            raise RemoteError("Set the prebuilt remote worker image in target Settings.")
        return {
            "run_id": run_id,
            "container": "qmx-run-" + run_id,
            "resources": bundle.resources.model_dump(mode="json"),
            "code": bundle.code is not None,
        }

    def start(self, handle: Document, secrets: dict[str, str]) -> Document:
        resources = handle["resources"]
        if not isinstance(resources, dict):
            raise RemoteError("Provider handle has no resources.")
        run_id = str(handle["run_id"])
        local_bucket = self.target.bucket_local and (
            not self.bucket or self.bucket.endswith(":" + self.target.root)
        )
        workspace = self.target.root + "/work/" + run_id
        self._call(["mkdir", "-p", "--", workspace])
        args = [
            "docker",
            "run",
            "--detach",
            "--name",
            str(handle["container"]),
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--memory",
            str(resources["memory_mb"]) + "m",
            "--cpus",
            str(resources["cpus"]),
            "--pids-limit",
            "256",
            "--tmpfs",
            "/tmp:rw,nosuid,size=256m",  # noqa: S108 - private container tmpfs
            "--mount",
            f"type=bind,src={workspace},dst=/work",
            "--env",
            "TMPDIR=/work",
            "--env",
            "HOME=/work",
        ]
        if local_bucket:
            for directory in ("requests", "runs"):
                args.extend(
                    [
                        "--mount",
                        f"type=bind,src={self.target.root}/{directory}/{run_id},dst=/bucket/{directory}/{run_id}",
                    ]
                )
        if handle.get("code"):
            code = self.target.root + "/code/" + run_id
            self._call(["mkdir", "-p", "--", code])
            args.extend(["--mount", f"type=bind,src={code},dst=/bucket/code/{run_id}"])
        if resources["gpu"]:
            args.extend(["--gpus", str(resources["gpu"])])
        for name in secrets:
            args.extend(["--env", name])
        args.extend(
            [
                "--entrypoint",
                "python",
                self.target.image,
                "-m",
                "qmx_remote.worker",
                "--bucket",
                "/bucket" if local_bucket else self.bucket,
                "--run-id",
                str(handle["run_id"]),
            ]
        )
        self._call(args, secrets=secrets)
        return handle

    def status(self, handle: Document) -> Status:
        output = self._call(
            ["docker", "inspect", "--format", "{{json .State}}", str(handle["container"])]
        )
        state = json.loads(output)
        if state["Running"]:
            return "running"
        return "interrupted"

    def logs(self, handle: Document) -> str:
        return self._call(["docker", "logs", "--tail", "1000", str(handle["container"])])

    def stop(self, handle: Document) -> None:
        self._call(["docker", "stop", "--time", "30", str(handle["container"])])

    def teardown(self, handle: Document) -> None:
        self._call(["docker", "rm", "--force", str(handle["container"])])


class AmpProvider(SSHProvider):
    """The VPS runs the SDK consumer, so shipping survives the laptop disconnecting."""

    def provision(self, run_id: str, bundle: RunBundle) -> Document:
        if bundle.kind != "amp":
            raise RemoteError("Amp targets accept delegated agent tasks only.")
        if bundle.code and self.target.executor != "runner":
            raise RemoteError("Code publication requires an Amp runner on the VPS.")
        if self.target.executor == "runner" and not self.target.runner_id:
            raise RemoteError("Set an Amp runner_id in target Settings.")
        return super().provision(run_id, bundle)


class ModalProvider:
    def __init__(
        self,
        target: Target,
        bucket: str,
        *,
        sdk: Any = None,
        secret_getter: Callable[[str, str], str | None] = keyring.get_password,
    ):
        self.target = target
        self.bucket = bucket
        self.sdk = sdk
        self.secret_getter = secret_getter

    def _client(self) -> Any:
        token_id = self.secret_getter("qmx/modal-token-id", "modal-token-id")
        token_secret = self.secret_getter("qmx/modal-token-secret", "modal-token-secret")
        if not token_id or not token_secret:
            raise RemoteError("Set qmx/modal-token-id and qmx/modal-token-secret in the vault.")
        return self._sdk().Client.from_credentials(token_id, token_secret)

    def _sdk(self) -> Any:
        if self.sdk is None:
            self.sdk = importlib.import_module("modal")
        return self.sdk

    def provision(self, run_id: str, bundle: RunBundle) -> Document:
        if not self.target.image:
            raise RemoteError("Set a prebuilt Modal worker image in Settings.")
        return {"run_id": run_id, "resources": bundle.resources.model_dump(mode="json")}

    def start(self, handle: Document, secrets: dict[str, str]) -> Document:
        sdk = self._sdk()
        client = self._client()
        resources = handle["resources"]
        if not isinstance(resources, dict):
            raise RemoteError("Provider handle has no resources.")
        options: dict[str, Any] = {}
        if resources["gpu"]:
            if not self.target.gpu_type:
                raise RemoteError("Configure Modal gpu_type for GPU jobs.")
            options["gpu"] = f"{self.target.gpu_type}:{resources['gpu']}"
        sandbox = sdk.Sandbox.create(
            "python",
            "-m",
            "qmx_remote.worker",
            "--bucket",
            self.bucket,
            "--run-id",
            str(handle["run_id"]),
            app=sdk.App.lookup("qmx-remote", create_if_missing=True, client=client),
            image=sdk.Image.from_registry(self.target.image),
            secrets=[sdk.Secret.from_dict(secrets)],
            timeout=resources["timeout"],
            memory=resources["memory_mb"],
            cpu=resources["cpus"],
            client=client,
            **options,
        )
        return {**handle, "sandbox_id": sandbox.object_id}

    def _sandbox(self, handle: Document) -> Any:
        return self._sdk().Sandbox.from_id(str(handle["sandbox_id"]), client=self._client())

    def status(self, handle: Document) -> Status:
        code = self._sandbox(handle).poll()
        return "running" if code is None else "interrupted"

    def logs(self, handle: Document) -> str:
        # A live stdout.read() blocks; the worker ships a nonblocking log tail to the bucket.
        return "Read the incremental logs in the run results store."

    def stop(self, handle: Document) -> None:
        self._sandbox(handle).terminate()

    def teardown(self, handle: Document) -> None:
        if "sandbox_id" not in handle:
            return
        self.stop(handle)


class E2BProvider:
    def __init__(
        self,
        target: Target,
        bucket: str,
        *,
        sdk: Any = None,
        secret_getter: Callable[[str, str], str | None] = keyring.get_password,
    ):
        self.target = target
        self.bucket = bucket
        self.sdk = sdk
        self.secret_getter = secret_getter

    def _key(self) -> str:
        key = self.secret_getter("qmx/e2b", "e2b")
        if not key:
            raise RemoteError("Set qmx/e2b in the vault.")
        return key

    def _sdk(self) -> Any:
        if self.sdk is None:
            self.sdk = importlib.import_module("e2b")
        return self.sdk

    def provision(self, run_id: str, bundle: RunBundle) -> Document:
        if bundle.resources.gpu:
            raise RemoteError("E2B is a CPU target; choose a configured GPU provider.")
        if not self.target.image:
            raise RemoteError("Set a prebuilt E2B worker template in Settings.")
        return {"run_id": run_id, "timeout": bundle.resources.timeout}

    def start(self, handle: Document, secrets: dict[str, str]) -> Document:
        sandbox = self._sdk().Sandbox.create(
            template=self.target.image, timeout=handle["timeout"], envs=secrets, api_key=self._key()
        )
        try:
            command = (
                shlex.join(
                    [
                        "python",
                        "-m",
                        "qmx_remote.worker",
                        "--bucket",
                        self.bucket,
                        "--run-id",
                        str(handle["run_id"]),
                    ]
                )
                + " > /home/user/qmx-worker.log 2>&1"
            )
            process = sandbox.commands.run(command, background=True, timeout=0)
        except BaseException:
            sandbox.kill()
            raise
        return {**handle, "sandbox_id": sandbox.sandbox_id, "pid": process.pid}

    def _sandbox(self, handle: Document) -> Any:
        return self._sdk().Sandbox.connect(str(handle["sandbox_id"]), api_key=self._key())

    def status(self, handle: Document) -> Status:
        processes = self._sandbox(handle).commands.list()
        return "running" if any(p.pid == handle["pid"] for p in processes) else "interrupted"

    def logs(self, handle: Document) -> str:
        return str(self._sandbox(handle).files.read("/home/user/qmx-worker.log"))

    def stop(self, handle: Document) -> None:
        self._sandbox(handle).commands.kill(int(str(handle["pid"])))

    def teardown(self, handle: Document) -> None:
        if "sandbox_id" not in handle:
            return
        self._sandbox(handle).kill()


def registry(
    target: Target,
    bucket: str,
    *,
    secret_getter: Callable[[str, str], str | None] = keyring.get_password,
) -> ComputeProvider:
    match target.provider:
        case "ssh":
            return SSHProvider(target, bucket)
        case "amp":
            return AmpProvider(target, bucket)
        case "modal":
            return ModalProvider(target, bucket, secret_getter=secret_getter)
        case "e2b":
            return E2BProvider(target, bucket, secret_getter=secret_getter)
