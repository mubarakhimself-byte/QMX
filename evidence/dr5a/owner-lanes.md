# DR5A owner lanes 1 to 4, exact commands

Run from `D:/QMX-worktrees/bld-dr5a` (PC) unless a line says otherwise. Every shell first runs this block, because the agent tests live in the `qmx-agents` workspace.

```powershell
$env:TMP='D:/Temp'; $env:TEMP='D:/Temp'; $env:UV_CACHE_DIR='D:/Caches/uv'
Get-ChildItem env: | Where-Object { $_.Name -like 'ANTHROPIC*' -or $_.Name -like 'CLAUDE*' -or $_.Name -eq 'NODE_USE_SYSTEM_CA' } | ForEach-Object { Remove-Item "env:$($_.Name)" }
cd D:/QMX-worktrees/bld-dr5a/qmx-agents
uv sync --frozen --all-packages --all-groups
```

The head is `git -C D:/QMX-worktrees/bld-dr5a rev-parse HEAD`; the parent is `3d05adaeb45f52fff186a87b314a9de8244f88df`.

## Lane 1. Regression lane against the parent

Run the three suites at the parent and at the head, then compare the failure sets. Save `dr5a-regression.log`.

```powershell
git -C D:/QMX-worktrees/bld-dr5a worktree add --detach D:/Temp/dr5a-parent 3d05adaeb45f52fff186a87b314a9de8244f88df
cd D:/Temp/dr5a-parent/qmx-agents
uv sync --frozen --all-packages --all-groups
uv run --no-sync python -m pytest packages/qmx-broker/tests packages/qmx-engine/tests packages/qmx-control/tests -n 2 -q > D:/QMX-worktrees/bld-dr5a/evidence/dr5a/dr5a-regression-parent.log 2>&1
cd D:/QMX-worktrees/bld-dr5a/qmx-agents
uv run --no-sync python -m pytest packages/qmx-broker/tests packages/qmx-engine/tests packages/qmx-control/tests -n 2 -q > D:/QMX-worktrees/bld-dr5a/evidence/dr5a/dr5a-regression.log 2>&1
git -C D:/QMX-worktrees/bld-dr5a worktree remove --force D:/Temp/dr5a-parent
```

Pass when the head fails nothing the parent passes. The owner ran the three packages' new tests only, not the full suites (the coordinator runs lane 1).

## Lane 2. P-NOTRADE, add time with the stub adapter

```powershell
cd D:/QMX-worktrees/bld-dr5a
uv run --no-sync --project qmx-agents python scripts/probes/data/p_notrade.py
```

Save `dr5a-p-notrade.log`. Pass when the existing allow-list half passes and the W13 line reads `stored False, row needs_you, writes 0`.

## Lane 3. P-VAULT-AWAY, the connections half with the PC stopped

```powershell
cd D:/QMX-worktrees/bld-dr5a
uv run --no-sync --project qmx-agents python scripts/probes/data/p_vault_away.py
```

Save `dr5a-p-vault-away.log`. The PC's vault object is deleted before the server half runs. Pass when the model half still passes and the `server-homed data connection` number reads `ok` with a latency, the data key opened from the server's own key file.

## Lane 4. The health workflow on a scratch server home

Three data connections read `ok`, and one blocked endpoint reads `down` with one incident. Save `dr5a-health.log`.

```powershell
$scratchHome = 'D:/Temp/dr5a-health'; $shared = "$scratchHome.zones/run/work"
Remove-Item -Recurse -Force $scratchHome, "$scratchHome.zones" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $shared | Out-Null
@'
[[connections]]
id = "dukascopy"
name = "Dukascopy"
adapter = "dukascopy"
kind = "data"

[[connections.connections]]
id = "dukascopy-eurusd"
credential_ref = "qmx/data/dukascopy-eurusd"
home = "contabo"

[[connections]]
id = "binance-vision"
name = "Binance public files"
adapter = "binance-vision"
kind = "data"

[[connections.connections]]
id = "binance-vision-spot"
credential_ref = "qmx/data/binance-vision-spot"
home = "contabo"

[[connections]]
id = "ccxt-public"
name = "CCXT public"
adapter = "ccxt-public"
kind = "data"
exchange = "binance"

[[connections.connections]]
id = "ccxt-public-binance"
credential_ref = "qmx/data/ccxt-public-binance"
home = "contabo"

[[connections]]
id = "blocked"
name = "Blocked endpoint"
adapter = "http"
kind = "data"
exchange = "https://blocked.invalid/qmx"

[[connections.connections]]
id = "blocked-endpoint"
credential_ref = "qmx/data/blocked-endpoint"
home = "contabo"
'@ | Set-Content -Encoding utf8 "$scratchHome/settings.toml"
cd D:/QMX-worktrees/bld-dr5a/qmx-agents
$env:QMX_WORK_SHARED = $shared
'{"in": {"dry_run": false}}' | uv run --no-sync python packages/qmx-engine/src/qmx_engine/templates/connections-health/scripts/health.py | Tee-Object -FilePath D:/QMX-worktrees/bld-dr5a/evidence/dr5a/dr5a-health.log
Get-Content "$scratchHome/logs/connections-health.json"
```

Pass when the three providers read `ok` with a latency and `blocked-endpoint` reads `down`; one incident appears in `sqlite3 "$scratchHome/inbox.sqlite" "select signature, count from incidents"` (Windows: open it with Python's sqlite3). Remove `$scratchHome` and `$scratchHome.zones` afterwards.

## The owner's fast checks (what this PR's owner ran)

```powershell
cd D:/QMX-worktrees/bld-dr5a/qmx-agents
uv run --no-sync python -m pytest packages/qmx-broker/tests/test_registry.py -n 2 -q
uv run --no-sync python -m pytest packages/qmx-control/tests/test_connections.py packages/qmx-control/tests/test_brokers.py -n 2 -q
uv run --no-sync python -m pytest packages/qmx-engine/tests/test_connections_health.py -n 2 -q
uv run --no-sync python -m pytest packages/qmx-engine/tests/test_templates.py -n 2 -q
cd packages/qmx-broker && uv run --no-sync python -m poethepoet fmt-check && uv run --no-sync python -m poethepoet lint && uv run --no-sync python -m poethepoet types
cd ../qmx-control && uv run --no-sync python -m poethepoet fmt-check && uv run --no-sync python -m poethepoet lint && uv run --no-sync python -m poethepoet types
cd ../qmx-engine && uv run --no-sync python -m poethepoet fmt-check && uv run --no-sync python -m poethepoet lint && uv run --no-sync python -m poethepoet types
cd D:/QMX-worktrees/bld-dr5a && uv run --no-sync python tools/secret_scan.py
```
