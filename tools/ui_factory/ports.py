"""Conflict-free localhost ports and disposable data roots."""

from __future__ import annotations

import json
import socket
from dataclasses import asdict, dataclass
from pathlib import Path

from ui_factory.lock import FileLock


@dataclass(frozen=True)
class PortLease:
    unit_id: str
    app_port: int
    api_port: int
    data_root: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _next_free(start: int, taken: set[int]) -> int:
    port = start
    while port < 65535:
        if port not in taken and _port_open(port):
            return port
        port += 1
    raise RuntimeError("no free localhost ports")


class PortAllocator:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.path = state_dir / "ports.json"
        self._lock = state_dir / "ports.lock"

    def _load(self) -> dict[str, PortLease]:
        if not self.path.is_file():
            return {}
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        leases: dict[str, PortLease] = {}
        if isinstance(raw, dict):
            for key, value in raw.items():
                if isinstance(value, dict):
                    leases[str(key)] = PortLease(
                        unit_id=str(value.get("unit_id") or key),
                        app_port=int(value.get("app_port") or 0),
                        api_port=int(value.get("api_port") or 0),
                        data_root=str(value.get("data_root") or ""),
                    )
        return leases

    def _save(self, leases: dict[str, PortLease]) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = {k: v.to_dict() for k, v in leases.items()}
        self.path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def acquire(self, unit_id: str) -> PortLease:
        with FileLock(self._lock):
            leases = self._load()
            if unit_id in leases:
                return leases[unit_id]
            taken: set[int] = set()
            for lease in leases.values():
                taken.add(lease.app_port)
                taken.add(lease.api_port)
            app = _next_free(4173, taken)
            taken.add(app)
            api = _next_free(18765, taken)
            data_root = str(self.state_dir / "data-roots" / unit_id)
            Path(data_root).mkdir(parents=True, exist_ok=True)
            lease = PortLease(
                unit_id=unit_id,
                app_port=app,
                api_port=api,
                data_root=data_root,
            )
            leases[unit_id] = lease
            self._save(leases)
            return lease

    def release(self, unit_id: str) -> None:
        with FileLock(self._lock):
            leases = self._load()
            leases.pop(unit_id, None)
            self._save(leases)
