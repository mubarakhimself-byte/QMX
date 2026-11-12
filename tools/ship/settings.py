"""Every tunable number and command the scripts use, with its default.

A program folder may override any of them in `ship.toml` under `[settings]`. An unknown key is an
error, so a typo never silently falls back to the default.
"""

from __future__ import annotations

import dataclasses
import tomllib
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class Settings:
    seats: int = 3  # builders held at once; the method's starting value
    max_attempts: int = 2  # quality rounds per slice: the build and one fix round
    breaker_parks: int = 3  # quality parks in a row that stop the run
    remote: str = "origin"
    slice_branch_prefix: str = "slice/"
    git_timeout_s: int = 600  # one git call, fetch and push included
    fact_timeout_s: int = 120  # one brief fact
    check_timeout_s: int = 3600  # one lint, types or test command in slice_checks
    land_timeout_s: int = 7200  # the test run on a landing batch
    nightly_timeout_s: int = 10800  # the whole-suite run
    bisect_step_timeout_s: int = 1800  # one bisect step
    heartbeat_interval_s: int = 30  # how often the wrapper touches the heartbeat file
    liveness_stale_s: int = 2700  # no push and no heartbeat for this long means stuck (45 minutes)
    power_poll_s: int = 60  # power_watch loop period
    power_settle_s: int = 600  # wait after mains returns, for the router
    net_timeout_s: int = 20  # one internet or GitHub probe
    internet_probe: str = "1.1.1.1:443"  # host:port a TCP connect must reach
    keep_awake_poll_s: int = 30  # the keep-awake helper checks its flag this often
    teardown_wait_s: int = 120  # how long teardown waits for the keep-awake helper to exit
    updates_paused_min_h: float = 12  # Windows updates must stay paused at least this long
    evidence_required: tuple[str, ...] = ("how.md", "red.log", "report.md")
    data_env_vars: tuple[str, ...] = ("QMX_HOME", "QMX_DATA_DIR")  # pointed at the run's temp folder
    strip_env_prefixes: tuple[str, ...] = ("CLAUDE", "ANTHROPIC")  # removed from every test run
    gh: tuple[str, ...] = ("gh",)
    lock_cmd: tuple[str, ...] = ("uv", "lock")  # regenerates a uv.lock after a landing rebase
    protected_branches: tuple[str, ...] = ("main", "integration", "engine/base")


def load_settings(program_dir: Path) -> Settings:
    path = program_dir / "ship.toml"
    if not path.exists():
        return Settings()
    raw = tomllib.loads(path.read_text("utf-8")).get("settings", {})
    known = {f.name: f for f in dataclasses.fields(Settings)}
    unknown = sorted(set(raw) - set(known))
    if unknown:
        raise SystemExit(f"ship.toml: unknown settings {unknown}")
    values = {k: tuple(v) if isinstance(v, list) else v for k, v in raw.items()}
    return Settings(**values)
