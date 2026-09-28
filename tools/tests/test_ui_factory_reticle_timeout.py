"""A stuck quality process must return failed evidence instead of crashing."""

from __future__ import annotations

import sys
from pathlib import Path

from ui_factory.quality import run_command


def test_unresponsive_command_retains_deadline_failure(tmp_path: Path) -> None:
    result = run_command(
        name="ui-reticle:stalled",
        argv=[sys.executable, "-c", "import time; time.sleep(30)"],
        cwd=tmp_path,
        log_dir=tmp_path / "logs",
        env=None,
        timeout=1,
    )
    assert result.exit_code == 124
    assert result.duration_ms < 5000
    assert "deadline exceeded" in Path(result.log_path).read_text(encoding="utf-8")
