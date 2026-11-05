"""A keyring backend over one throwaway JSON file, so a lane's real host touches no Credential
Manager entry. Named by PYTHON_KEYRING_BACKEND; the file is C38_KEYRING_FILE."""

from __future__ import annotations

import json
import os
from pathlib import Path

from keyring.backend import KeyringBackend


class FileKeyring(KeyringBackend):
    priority = 1  # pyright: ignore[reportAssignmentType, reportIncompatibleMethodOverride]

    @property
    def path(self) -> Path:
        return Path(os.environ["C38_KEYRING_FILE"])

    def _held(self) -> dict[str, str]:
        return json.loads(self.path.read_text("utf-8")) if self.path.is_file() else {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._held().get(f"{service}|{username}")

    def set_password(self, service: str, username: str, password: str) -> None:
        held = self._held()
        held[f"{service}|{username}"] = password
        self.path.write_text(json.dumps(held), "utf-8")

    def delete_password(self, service: str, username: str) -> None:
        held = self._held()
        held.pop(f"{service}|{username}", None)
        self.path.write_text(json.dumps(held), "utf-8")
