param(
    [Parameter(Mandatory = $true)][string]$PythonExe,
    [string[]]$ExtraDependencyPath = @(),
    [ValidateSet('seams', 'native', 'memory', 'quality', 'qma', 'qmn', 'data-qmb')][string]$Suite = 'seams',
    [Parameter(Mandatory = $true)][string]$EvidenceRoot
)
$ErrorActionPreference = 'Stop'
$candidateRepo = Split-Path $PSScriptRoot -Parent
$candidateScripts = Split-Path ([IO.Path]::GetFullPath($PythonExe)) -Parent
$candidateQmb = Join-Path $candidateScripts 'qmb.exe'
if ($Suite -in @('seams', 'data-qmb') -and -not (Test-Path -LiteralPath $candidateQmb -PathType Leaf)) {
    throw 'This suite requires an installed qmb.exe beside PythonExe. PYTHONPATH alone does not install console entrypoints.'
}
$env:PATH = $candidateScripts + [IO.Path]::PathSeparator + $env:PATH
$candidateEvidence = Join-Path ([IO.Path]::GetFullPath($EvidenceRoot)) ($Suite + '-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $candidateEvidence | Out-Null
$candidateSources = @(Get-ChildItem (Join-Path $candidateRepo 'packages'), (Join-Path $candidateRepo 'extensions') -Directory | ForEach-Object { Join-Path $_.FullName 'src' })
$candidateSources += @('qml/src', 'qmb/src', 'qmn/src', 'qmx-agents/packages/qma-core/src', 'qmx-agents/packages/qma-wire/src', 'qmx-agents/packages/qma-daemon/src', 'qmb/tests', 'qmn/tests', 'qmx-agents/packages/qma-daemon/tests' | ForEach-Object { Join-Path $candidateRepo $_ })
$env:PYTHONPATH = ($candidateSources + @($ExtraDependencyPath)) -join [IO.Path]::PathSeparator
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:LANGSMITH_TRACING = 'false'
$env:LANGCHAIN_TRACING_V2 = 'false'
$env:RUFF_CACHE_DIR = Join-Path $candidateEvidence 'ruff-cache'
$env:COVERAGE_FILE = Join-Path $candidateEvidence '.coverage'
$candidateTests = @()
$candidatePytestOptions = @('-q', '-ra', '-o', ('cache_dir=' + (Join-Path $candidateEvidence 'pytest-cache')), ('--basetemp=' + (Join-Path $candidateEvidence 'pytest-temp')))
$candidateCwd = $candidateRepo
switch ($Suite) {
    'quality' {
        $candidateTests = @(
            'tools/tests/test_readiness_gate.py',
            'tools/tests/test_mutation_workflow.py',
            'tools/tests/test_mutation_gate.py',
            'tools/tests/test_stage_mutation_config.py',
            'tools/tests/test_coverage_report.py'
        )
        $candidatePytestOptions += '--no-cov'
    }
    'memory' {
        $candidateTests = @(
            'qmx-agents/packages/qma-daemon/tests/test_durable_memory.py',
            'qmx-agents/packages/qma-daemon/tests/test_memory_extraction.py',
            'qmx-agents/packages/qma-daemon/tests/test_durable_memory_requests.py',
            'qmx-agents/packages/qma-daemon/tests/test_research_workflow.py',
            'qmx-agents/packages/qma-daemon/tests/test_agent_extensions.py',
            'qmx-agents/packages/qma-daemon/tests/test_agent_extensions_daemon.py',
            'qmx-agents/packages/qma-daemon/tests/test_combined_backend_composition.py'
        )
    }
    'native' {
        $candidateTests = @(
            'qmx-agents/packages/qma-daemon/tests/test_native_sessions.py',
            'qmx-agents/packages/qma-daemon/tests/test_native_codex_bridge.py',
            'qmx-agents/packages/qma-daemon/tests/test_native_operator_routing.py',
            'qmx-agents/packages/qma-daemon/tests/test_native_configured_daemon.py',
            'qmx-agents/packages/qma-daemon/tests/test_combined_backend_composition.py'
        )
    }
    'seams' {
        $candidateTests = @(
            'qmx-agents/packages/qma-daemon/tests/test_combined_backend_composition.py',
            'qmx-agents/packages/qma-daemon/tests/test_agent_extensions_daemon.py',
            'qmx-agents/packages/qma-daemon/tests/test_request_runtime_configured_daemon.py',
            'qmx-agents/packages/qma-daemon/tests/test_native_operator_routing.py',
            'qmx-agents/packages/qma-daemon/tests/test_native_configured_daemon.py',
            'qmx-agents/packages/qma-daemon/tests/test_native_sessions.py',
            'qmx-agents/packages/qma-daemon/tests/test_spot_daemon_binding.py',
            'qmx-agents/packages/qma-daemon/tests/test_spot_query_door.py',
            'qmx-agents/packages/qma-daemon/tests/test_qmb_local_startup.py',
            'qmx-agents/packages/qma-daemon/tests/test_qmb_cli_transport.py',
            'qmx-agents/packages/qma-daemon/tests/test_product_session_host_retry.py',
            'qmx-agents/packages/qma-wire/tests/test_qmb_required_evidence.py',
            'qmb/tests/test_operator_replay_process.py',
            'qmb/tests/test_download_replay_connection.py',
            'packages/qmf-data/tests/test_intake_process_lock.py',
            'qmn/tests/test_spot_paper_process.py'
        )
    }
    'qma' {
        $candidateCwd = Join-Path $candidateRepo 'qmx-agents'
        $candidateTests = @('packages', 'tests')
        $candidatePytestOptions += @('--cov=packages/qma-core/src', '--cov=packages/qma-wire/src', '--cov=packages/qma-daemon/src', '--cov-branch', '--cov-fail-under=80', '--cov-report=term', ('--cov-report=json:' + (Join-Path $candidateEvidence 'coverage.json')))
    }
    'qmn' { $candidateTests = @('qmn/tests') }
    'data-qmb' { $candidateTests = @('packages/qmf-data/tests', 'qmb/tests') }
}
Push-Location -LiteralPath $candidateCwd
try {
    $candidateIdentity = [ordered]@{ suite = $Suite; head = (& git rev-parse HEAD); status = @(& git status --short); script_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash; python = $PythonExe; scripts_path = $candidateScripts; qmb_entrypoint = $candidateQmb; dependencies = $ExtraDependencyPath; pythonpath = $env:PYTHONPATH; cwd = $candidateCwd; arguments = @('-m', 'pytest') + $candidateTests + $candidatePytestOptions }
    $candidateIdentity | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $candidateEvidence 'command.json') -Encoding utf8
    & $PythonExe -m pytest @candidateTests @candidatePytestOptions *> (Join-Path $candidateEvidence 'pytest.txt')
    $candidateExit = $LASTEXITCODE
    $candidateExit | Set-Content (Join-Path $candidateEvidence 'pytest.exit')
    Get-Content (Join-Path $candidateEvidence 'pytest.txt') -Tail 18
    Write-Output "Evidence: $candidateEvidence"
} finally { Pop-Location }
exit $candidateExit
