"""Attended native start/resume through operator config and authenticated CT-40.

Dry by default: no store, SDK, auth or model calls. --allow-live requires separate
human authorization and prior official native login. No keys or login automation.
"""

from __future__ import annotations

# ruff: noqa: E402 - unpacked example pins the candidate's own source paths
import argparse
import asyncio
import json
import os
import queue
import struct
import subprocess
import sys
import threading
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_CANDIDATE = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(path) for path in sorted(_CANDIDATE.glob("packages/*/src"))]
sys.path[:0] = [str(path) for path in sorted((_CANDIDATE / "qmx-agents/packages").glob("*/src"))]

from qma.daemon.knowledge import KnowledgeService
from qma.daemon.pairing import CT40_WS_SUBPROTOCOL, issue_pairing_session
from qma.daemon.plugins import research_corpus_plugin_load_config
from qma.daemon.process import DaemonProcess
from qma.wire.initialize import WIRE_PROTOCOL_VERSION
from qmf.core import Result, is_refusal

SESSION = "psess:native-daemon-proof"
GRANT = "grant:native-daemon-proof"


def value[T](result: Result[T]) -> T:
    if is_refusal(result):
        raise RuntimeError("Synthetic daemon operation refused")
    return result.value


def compose(root: Path, boot: str) -> DaemonProcess:
    return value(
        DaemonProcess.compose(
            root,
            machine="native-daemon-proof",
            boot_epoch_id=boot,
            bind_port=0,
            plugin_load_configs=research_corpus_plugin_load_config(root / "corpus"),
        )
    )


def prepare(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    if root.exists():
        raise ValueError("New proof root required; previous unknown proof must not be replayed")
    for native_path in (args.native_home.resolve(), args.empty_workspace.resolve()):
        if root == native_path or root in native_path.parents or native_path in root.parents:
            raise ValueError("Proof store and native directories must be separate")
    root.mkdir(parents=True)
    corpus = root / "corpus"
    corpus.mkdir()
    (corpus / "README.md").write_text("Synthetic permitted metadata proof.", encoding="utf-8")
    (corpus / "IDEA.md").write_text("Excluded synthetic metadata.", encoding="utf-8")
    process = compose(root, "discover")
    try:
        pack = process.roster.loader.get("research-corpus")
        if pack is None:
            raise RuntimeError("Synthetic corpus pack unavailable")
        contribution = next(row.qualified_id for row in pack.published if row.point == "tool")
        snapshot = value(KnowledgeService(registry=process.roster.knowledge).snapshot("strats"))
        manifest = {
            "instance": pack.instance_id,
            "contribution": contribution,
            "snapshot": snapshot.id,
        }
    finally:
        process.close()
    provider: dict[str, Any] = {
        "protocol": "native-session",
        "backend": args.provider,
        "executable": str(args.executable.resolve()),
        "dedicated_home": str(args.native_home.resolve()),
        "empty_workspace": str(args.empty_workspace.resolve()),
    }
    if args.provider == "claude":
        provider["native_policy_reviewed"] = args.native_policy_reviewed
    profile: dict[str, Any] = {
        "role": "application",
        "authority_profile": "app-use",
        "app_instance_id": manifest["instance"],
        "provider_id": "native",
        "instructions": "Only the explicitly host-granted synthetic metadata read is permitted.",
        "timeout_seconds": 60,
        "tools": ["research_browse"],
    }
    if args.model is not None:
        profile["model"] = args.model
    sdk = {
        "enabled": True,
        "providers": {"native": provider},
        "profiles": {"reader": profile},
        "instance_revisions": {manifest["instance"]: 1},
        "research_browse": {
            "source_id": "strats",
            "snapshot_ref": manifest["snapshot"],
            "allowed_locators": ["README.md"],
        },
        "max_workers": 1,
    }
    (root / "operator-config.json").write_text(json.dumps({"agent_sdk": sdk}), encoding="utf-8")
    (root / "proof-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


async def worker(root: Path, boot: str) -> None:
    process = compose(root, boot)
    try:
        manifest = json.loads((root / "proof-manifest.json").read_text(encoding="utf-8"))
        if boot == "one":
            value(
                process.product_sessions.mint(
                    product_session_id=SESSION,
                    profile="app-use",
                    principal="operator",
                    contribution={
                        "qualified_id": manifest["contribution"],
                        "package_version": "0.1.0",
                    },
                    instance_id=manifest["instance"],
                    config_revision=1,
                    as_of=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                )
            )
            value(
                process.product_sessions.host_grant(
                    SESSION,
                    grant_id=GRANT,
                    op_id="qml.research.browse",
                    op_version=1,
                    effect_class="read",
                    parameter_ceiling={"allow_keys": ["snapshot_ref", "locator"]},
                    expires_at=(datetime.now(UTC) + timedelta(minutes=10))
                    .isoformat()
                    .replace("+00:00", "Z"),
                )
            )
        value(await process.bind())
        paired = value(
            issue_pairing_session(
                journal=process.journal,
                sqlite=process.sqlite,
                origin="http://127.0.0.1:5173",
                expires_at=time.time_ns() + 600_000_000_000,
            )
        )
        if process.bound is None:
            raise RuntimeError("Daemon did not bind")
        # Proof bearer stays in the private parent's pipe, never the result report.
        print(
            json.dumps(
                {"port": process.bound.port, "proof": paired.pairing_proof, "pid": os.getpid()}
            ),
            flush=True,
        )
        while True:
            line = await asyncio.to_thread(sys.stdin.readline)
            if not line or line.strip() == "stop":
                break
            if line.strip() == "evidence":
                events = value(process.journal.read_events())
                rows = [
                    {
                        "kind": event.payload["kind"],
                        "key": event.payload["key"],
                        "body": json.loads(str(event.payload["body"])),
                    }
                    for event in events
                    if event.event == "agent_graph.record"
                ]
                print(json.dumps(rows), flush=True)
            elif line.strip() == "revoke":
                value(
                    process.product_sessions.revoke_grant(
                        SESSION,
                        grant_id=GRANT,
                        principal="operator",
                        reason="Synthetic proof revocation",
                        revoked_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                    )
                )
                print(json.dumps({"revoked": True}), flush=True)
    finally:
        await process.aclose()


def start_worker(root: Path, boot: str) -> tuple[subprocess.Popen[str], dict[str, Any]]:
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__)), "--worker", str(root), boot],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    try:
        if process.stdout is None:
            raise RuntimeError("Missing daemon pipe")
        line = read_pipe_line(process)
        if not line:
            raise RuntimeError("Daemon startup refused")
        return process, json.loads(line)
    except Exception:
        process.kill()
        process.wait(timeout=5)
        raise


def read_pipe_line(process: subprocess.Popen[str]) -> str:
    if process.stdout is None:
        raise RuntimeError("Missing daemon output pipe")
    stream = process.stdout
    output: queue.Queue[str] = queue.Queue(maxsize=1)
    threading.Thread(target=lambda: output.put(stream.readline()), daemon=True).start()
    return output.get(timeout=30)


def control(process: subprocess.Popen[str], command: str) -> Any:
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("Missing daemon control pipe")
    process.stdin.write(command + "\n")
    process.stdin.flush()
    if command in {"evidence", "revoke"}:
        return json.loads(read_pipe_line(process))
    return None


def stop_worker(process: subprocess.Popen[str]) -> None:
    try:
        if process.poll() is None:
            control(process, "stop")
            process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        for stream in (process.stdin, process.stdout):
            if stream is not None:
                stream.close()


async def connect(
    info: dict[str, Any], *, proof: str | None = None
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    reader, writer = await asyncio.open_connection("127.0.0.1", info["port"])
    token = info["proof"] if proof is None else proof
    writer.write(
        (
            f"GET / HTTP/1.1\r\nHost: 127.0.0.1:{info['port']}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Version: 13\r\n"
            "Sec-WebSocket-Key: YWdlbnQtdGVzdC1rZXkxMg==\r\n"
            f"Sec-WebSocket-Protocol: {CT40_WS_SUBPROTOCOL}, qmx.pair.{token}\r\n"
            "Origin: http://127.0.0.1:5173\r\n\r\n"
        ).encode()
    )
    await writer.drain()
    opening = await asyncio.wait_for(reader.readuntil(b"\r\n\r\n"), 3)
    if b"101 Switching Protocols" not in opening:
        writer.close()
        await writer.wait_closed()
        raise RuntimeError("Authenticated daemon connection refused")
    receipt(
        await rpc(
            reader,
            writer,
            "initialize",
            {"protocolVersion": WIRE_PROTOCOL_VERSION, "capabilities": {}},
        )
    )
    return reader, writer


async def rpc(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, method: str, params: dict[str, Any]
) -> dict[str, Any]:
    data = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    mask = os.urandom(4)
    prefix = (
        bytes([0x81, 0x80 | len(data)])
        if len(data) < 126
        else bytes([0x81, 0xFE]) + struct.pack("!H", len(data))
    )
    writer.write(prefix + mask + bytes(byte ^ mask[index % 4] for index, byte in enumerate(data)))
    await writer.drain()
    head = await asyncio.wait_for(reader.readexactly(2), 3)
    length = head[1] & 0x7F
    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", await reader.readexactly(8))[0]
    if length > 1_048_576:
        raise RuntimeError("Daemon response exceeds proof limit")
    return json.loads(await asyncio.wait_for(reader.readexactly(length), 3))


def receipt(response: dict[str, Any]) -> dict[str, Any]:
    if "error" in response:
        raise RuntimeError("Authenticated daemon request refused")
    return response["result"]


async def wait_result(
    reader: asyncio.StreamReader, writer: asyncio.StreamWriter, request_id: str
) -> dict[str, Any]:
    deadline = time.monotonic() + 75
    while time.monotonic() < deadline:
        row = receipt(
            await rpc(
                reader,
                writer,
                "get_agent_request",
                {"request_id": request_id, "product_session_ref": SESSION},
            )
        )
        if row["status"] in {"completed", "failed", "interrupted", "cancelled"}:
            return row
        await asyncio.sleep(0.02)
    raise RuntimeError("Proof deadline elapsed; unknown outcome requires reconciliation")


async def journey(root: Path, manifest: dict[str, Any], report: dict[str, Any]) -> None:
    marker = "NATIVE-PROOF-" + uuid.uuid4().hex
    prompts = [
        f"Call research_browse exactly once with snapshot_ref={json.dumps(manifest['snapshot'])}. "
        f"Then return this marker: {marker}. Use only the supplied metadata.",
        "Resume our previous exchange. Return the exact previous proof marker. Do not call tools.",
    ]
    for index, boot in enumerate(("one", "two")):
        process, info = start_worker(root, boot)
        writer = None
        try:
            report["pids"].append(info["pid"])
            reader, writer = await connect(info)
            accepted = receipt(
                await rpc(
                    reader,
                    writer,
                    "submit_agent_request",
                    {
                        "product_session_ref": SESSION,
                        "profile_id": "reader",
                        "prompt": prompts[index],
                        "idempotency_key": f"native-daemon-{index}",
                    },
                )
            )
            row = await wait_result(reader, writer, accepted["request_id"])
            report["requests"].append(row)
            report["records"] = control(process, "evidence")
            (root / "daemon-proof-result.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
            if row["status"] != "completed" or marker not in row.get("content", ""):
                raise RuntimeError("Native turn unverified; no retry or fallback")
        finally:
            if writer is not None:
                writer.close()
                await writer.wait_closed()
            stop_worker(process)
    native = [
        row
        for row in report["records"]
        if row["kind"] == "native_session" and row["body"]["status"] == "completed"
    ]
    effects = [
        row
        for row in report["records"]
        if row["kind"] == "effect" and row["body"]["status"] == "observed"
    ]
    ids = {row["body"].get("session_id") for row in native}
    if (
        len(native) != 2
        or len(ids) != 1
        or not next(iter(ids), None)
        or len(effects) != 1
        or len(set(report["pids"])) != 2
    ):
        raise RuntimeError("Native restart/host-effect acceptance not established")
    report.update(
        {
            "verified": True,
            "native_session_id": next(iter(ids)),
            "host_effect_receipts": 1,
            "acceptance": "authenticated daemon + fresh process + retained native ID "
            "+ prior marker + observed host metadata",
        }
    )


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments[:1] == ["--worker"] and len(arguments) == 3:
        asyncio.run(worker(Path(arguments[1]), arguments[2]))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=("codex", "claude"), required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--native-home", type=Path, required=True)
    parser.add_argument("--empty-workspace", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--model")
    parser.add_argument("--native-policy-reviewed", action="store_true")
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args(arguments)
    if not args.allow_live:
        print(
            json.dumps(
                {
                    "mode": "dry",
                    "auth_calls": 0,
                    "model_calls": 0,
                    "next": "Separate approval, human pinned native login, then --allow-live",
                }
            )
        )
        return 0
    if args.provider == "claude" and not args.native_policy_reviewed:
        parser.error("Claude requires reviewed personal unmanaged native policy")
    report: dict[str, Any] = {
        "verified": False,
        "backend": args.provider,
        "pids": [],
        "requests": [],
        "records": [],
        "authentication_owner": "official native CLI",
    }
    prepared = False
    try:
        manifest = prepare(args)
        prepared = True
        asyncio.run(journey(args.root.resolve(), manifest, report))
    except Exception:
        print("Daemon proof stopped. No retry or fallback; inspect synthetic journal before rerun.")
        return 1
    finally:
        if prepared:
            (args.root / "daemon-proof-result.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
    print(
        json.dumps(
            {"verified": report["verified"], "report": str(args.root / "daemon-proof-result.json")}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
