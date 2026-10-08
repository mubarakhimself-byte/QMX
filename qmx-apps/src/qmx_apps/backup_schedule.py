"""A host-owned nightly timer that reloads settings before each sweep."""

import threading
import time
from collections.abc import Callable

from qmx_apps.backup import BackupSettings


class BackupSchedule:
    def __init__(
        self,
        settings: Callable[[], BackupSettings | None],
        apps: Callable[[], list[str]],
        run: Callable[[str], object],
        failed: Callable[[str, Exception], None],
    ) -> None:
        self.settings = settings
        self.apps = apps
        self.run = run
        self.failed = failed
        self._last: dict[str, float] = {}
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._serve, name="qmx-backups", daemon=True)
        self._thread.start()

    def sweep(self, now: float) -> None:
        settings = self.settings()
        if settings is None or not settings.enabled:
            return
        for app_id in self.apps():
            last = self._last.setdefault(app_id, now)
            if now - last < settings.interval_seconds:
                continue
            try:
                self.run(app_id)
            except Exception as error:
                self.failed(app_id, error)
            finally:
                self._last[app_id] = now

    def _serve(self) -> None:
        while not self._stop.wait(1):
            try:
                self.sweep(time.monotonic())
            except Exception as error:
                self.failed("", error)

    def close(self) -> None:
        self._stop.set()
        self._thread.join()
