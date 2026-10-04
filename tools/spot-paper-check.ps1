param(
    [Parameter(Mandatory = $true)][string]$PythonExe,
    [string[]]$ExtraDependencyPath = @()
)
$ErrorActionPreference = 'Stop'
$spotRepo = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $spotRepo
$spotSources = @(Get-ChildItem packages, extensions -Directory | ForEach-Object {
    Join-Path $_.FullName 'src'
}) + @('qml/src', 'qmb/src', 'qmn/src', 'qmx-agents/packages/qma-core/src',
    'qmx-agents/packages/qma-wire/src', 'qmx-agents/packages/qma-daemon/src' |
    ForEach-Object { Join-Path $spotRepo $_ })
$env:PYTHONPATH = (@($spotSources) + @($ExtraDependencyPath)) -join [IO.Path]::PathSeparator
$spotOutput = Join-Path $spotRepo ('.test-tmp/spot-check-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $spotOutput -Force | Out-Null
$spotTests = @('packages/qmf-venue/tests/test_spot_metadata.py',
    'qmn/tests/test_spot_paper_slice.py', 'qmn/tests/test_spot_recorded_source.py',
    'qmn/tests/test_spot_paper_process.py',
    'qmx-agents/packages/qma-daemon/tests/test_spot_query_door.py')
$spotModules = @('packages/qmf-venue/src/qmf/venue/spot.py',
    'qmn/src/qmn/venue/spot_paper.py', 'qmn/src/qmn/venue/spot_recorded.py',
    'qmx-agents/packages/qma-daemon/src/qma/daemon/request_runtime/spot_tools.py',
    'tools/spot_paper_journey.py')
$spotFiles = @($spotModules) + @($spotTests)
& $PythonExe -m ruff check @spotFiles
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $PythonExe -m ruff format --check @spotFiles
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$spotTypeConfig = @{
    typeCheckingMode = 'strict'; pythonVersion = '3.14'; pythonPlatform = 'Windows'
    extraPaths = @($spotSources) + @($ExtraDependencyPath) + @(
        (Join-Path $spotRepo 'qmn/tests'),
        (Join-Path $spotRepo 'qmx-agents/packages/qma-daemon/tests'))
    include = @($spotFiles | ForEach-Object {
        [IO.Path]::GetRelativePath($spotOutput, (Join-Path $spotRepo $_))
    })
}
$spotTypePath = Join-Path $spotOutput 'pyright.json'
$spotTypeConfig | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $spotTypePath
& $PythonExe -m pyright --project $spotTypePath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $PythonExe -m pytest -q --basetemp (Join-Path $spotOutput 'pytest') @spotTests
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $PythonExe tools/spot_paper_journey.py seed (Join-Path $spotOutput 'journey')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $PythonExe tools/spot_paper_journey.py verify (Join-Path $spotOutput 'journey')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "Spot simulation evidence: $spotOutput"
