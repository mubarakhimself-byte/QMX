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
    evidence_required: tuple[str, ...] = ("how.md", "red.log", "report.md", "pr.md")
    slice_verdict_required: bool = False  # land wants a CLEAN slice verdict; off: machine checks gate, review is at checkpoints
    quality_timeout_s: int = 3600  # one Skylos, Vulture or mutmut command
    watcher_stale_s: int = 300  # power.json older than this means no power_watch is running
    data_env_vars: tuple[str, ...] = ("QMX_HOME", "QMX_DATA_DIR")  # pointed at the run's temp folder
    strip_env_prefixes: tuple[str, ...] = ("CLAUDE", "ANTHROPIC")  # removed from every test run
    gh: tuple[str, ...] = ("gh",)
    lock_cmd: tuple[str, ...] = ("uv", "lock")  # regenerates a uv.lock after a landing rebase
    protected_branches: tuple[str, ...] = ("main", "engine/base")
    # CI (ci.py). "github": qmx-ci on GitHub Actions runs the checkpoint deep run and gives Linux
    # evidence for slices and landings; "local": this machine only. github falls back to local by
    # itself when gh or GitHub cannot be reached, or the workflow is not on the branch.
    ci: str = "local"  # off by default until qmx-ci is on the target branch; a program opts in in ship.toml
    github_repo: str = "mubarakhimself-byte/QMX"  # every gh call names it; the checkout has other remotes
    ci_workflow: str = "qmx-ci.yml"
    ci_gate_base: str = "engine/base"  # the branch the checkpoint PR targets; its gate job reads the deep run
    ci_poll_s: int = 120  # how often a --wait watcher reads a run
    ci_wait_timeout_s: int = 43200  # a --wait watcher gives up (exit 2) after this; the run goes on
    ci_find_s: int = 180  # after a dispatch, how long to look for the new run in the listing
    ci_slice_grace_s: int = 3600  # land waits this long after slice_checks for the Linux slice run
    # U06: headless workers (launch.py)
    claude: tuple[str, ...] = ("claude",)  # the Claude Code CLI; tests put (python, tests/fake_claude.py) here
    factory_home: str = "D:/factory"  # the factory repo; FACTORY_HOME overrides it (see launch.factory_home)
    limit_patterns: tuple[str, ...] = ("usage limit", "rate limit")  # a worker's text holding one ended on a limit
    limit_backoff_s: int = 1800  # when a limit names no reset time, wait this long
    max_restarts: int = 3  # infra restarts of one slice before it is parked for him
    # U07: ship run, the build loop
    prompt_dir: str = ""  # worker prompts; "" means <factory_home>/skills/factory/prompts
    chain_poll_s: float = 20  # the run loop's (and later the conveyor's) tick period
    verify_timeout_s: int = 1800  # run: a verify_ready child is stopped past this and tried again
    slice_checks_timeout_s: int = 14400  # run: a slice_checks child is stopped past this and tried again
    land_run_timeout_s: int = 14400  # run: a land child is stopped past this and tried again
    worker_env_extra: tuple[str, ...] = ()  # launch: variables passed to workers beyond the allow-list
    # U08: arm checks
    disk_warn_gb: float = 20  # preflight warns (never refuses) below this much free space on the worktree drive
    main_check_ignore: tuple[str, ...] = ("tracker", ".claude")  # never stop a run, even under a code root
    # U09: trace and the checkpoint review
    worker_timeout_s: float = 0  # > 0 caps every worker role's time limit (tests and drills); 0 keeps roles.toml's
    # U38: claims, locks and the worker pool
    merge_queue_stale_s: int = 900  # a merge waiter that has not asked again for this long loses its place
    # U11: ship chain, the conveyor
    arm_preflight: bool = True  # the conveyor's arm step runs `preflight`; tests on a scratch repo turn it off


def repo_args(settings: Settings) -> list[str]:
    """`-R owner/name` for every gh call: the checkout has more than one GitHub remote."""
    return ["-R", settings.github_repo] if settings.github_repo else []


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
    if values.get("ci", "github") not in CI_BACKENDS:
        raise SystemExit(f"ship.toml: ci = {values['ci']!r}; want one of {list(CI_BACKENDS)}")
    return Settings(**values)


CI_BACKENDS = ("github", "local")
