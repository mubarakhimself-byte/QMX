# qmx-recover.ps1: the PC's twin of the server's qmx-recover (engine AD-71, ruling 139).
# `qmx node setup` writes it to <home>\bin\ with qmx-recover.conf beside it (the SSH target, the
# server's tailnet address, this PC's host port and Python; no secret). It never prints a key or
# a code: a pairing code is copied from file to file and never shown.
param(
    [Parameter(Position = 0)] [string] $What = 'help',
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)] [string[]] $Rest = @()
)

$ErrorActionPreference = 'Stop'
$conf = @{
    TARGET = ''
    SSH_KEY = ''
    SERVER_TAILNET = ''
    SERVER_HOME = '/srv/qmx/home/.qmx'
    QMX_HOME = (Split-Path -Parent $PSScriptRoot)
    PORT = '8766'
    PYTHON = ''
}
$confFile = if ($env:QMX_RECOVER_CONF) { $env:QMX_RECOVER_CONF } else { Join-Path $PSScriptRoot 'qmx-recover.conf' }
if (Test-Path -LiteralPath $confFile) {
    foreach ($row in Get-Content -LiteralPath $confFile) {
        $key, $value = $row -split '=', 2
        if ($null -ne $value -and $conf.ContainsKey($key)) { $conf[$key] = $value }
    }
}

function Show-Help {
    @'
qmx-recover (PC): check QMX on this PC and reach your server, without an agent.
Run it as: qmx-recover <what>

  status            Whether QMX answers on this PC and whether the server answers.
  server <what>     Run the server's qmx-recover with the same words, for example "server status".
  pair              Make a fresh pairing code on both ends.
  vault             Send the key copy to the server again.
  restart           Stop and start QMX on this PC.
  logs              The last 200 lines of QMX's log on this PC.
'@
}

function Write-Line([string] $Part, [string] $Reason, [string] $Verdict) {
    '{0,-11} {1}  {2}' -f $Part, $Reason, $Verdict
}

function Get-SshArgs {
    if (-not $conf.TARGET) { throw "No server is set in $confFile. Run ""qmx node setup"" first." }
    $sshArgs = @('-o', 'ConnectTimeout=10')
    if ($conf.SSH_KEY) { $sshArgs += @('-i', $conf.SSH_KEY) }
    $sshArgs + @($conf.TARGET)
}

function Test-Python {
    if (-not $conf.PYTHON -or -not (Test-Path -LiteralPath $conf.PYTHON)) { return $false }
    & $conf.PYTHON -c 'import qmx_control.node' 2>$null
    $LASTEXITCODE -eq 0
}

function Invoke-Qmx([string[]] $Arguments) {
    & $conf.PYTHON -m qmx_control.node @Arguments
}

function Show-Status {
    try {
        $code = (Invoke-WebRequest -Uri "http://127.0.0.1:$($conf.PORT)/api/health" -TimeoutSec 5 -SkipHttpErrorCheck).StatusCode
    } catch { $code = 0 }
    if ($code -eq 401 -or $code -eq 200) {
        Write-Line 'pc host' "answers on 127.0.0.1:$($conf.PORT) and asks for its key" 'PASS'
    } else {
        Write-Line 'pc host' "does not answer on 127.0.0.1:$($conf.PORT); try: qmx-recover restart" 'FAIL'
    }
    if ($conf.SERVER_TAILNET) {
        tailscale ping -c 1 $conf.SERVER_TAILNET *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Line 'tailnet' "the server answers at $($conf.SERVER_TAILNET)" 'PASS'
        } else {
            Write-Line 'tailnet' "the server does not answer at $($conf.SERVER_TAILNET)" 'FAIL'
        }
    }
    $sshArgs = Get-SshArgs
    ssh @sshArgs true *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Line 'ssh' "you can log in to $($conf.TARGET)" 'PASS'
    } else {
        Write-Line 'ssh' "cannot log in to $($conf.TARGET); use Contabo's VNC console" 'FAIL'
    }
}

function Invoke-Server([string[]] $Words) {
    if ($Words.Count -eq 0) { $Words = @('status') }
    foreach ($word in $Words) {
        if ($word -notmatch '^[a-z-]+$') { throw "Only plain words go to the server, not ""$word""." }
    }
    $sshArgs = Get-SshArgs
    ssh -t @sshArgs sudo qmx-recover @Words
}

function Invoke-Pair {
    if (Test-Python) {
        Invoke-Qmx @('node', 'pair', '--home', $conf.QMX_HOME, '--ssh-host', $conf.TARGET)
        return
    }
    "QMX's Python does not work here, so the server makes the code and this PC copies it."
    $sshArgs = Get-SshArgs
    ssh @sshArgs sudo qmx-recover pair | Out-Host
    if ($LASTEXITCODE -ne 0) { throw 'The server could not make a fresh pairing code. Nothing changed here.' }
    $code = (ssh @sshArgs sudo cat "$($conf.SERVER_HOME)/vault/pairing-key" | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $code) { throw 'The fresh code did not reach this PC. Run "qmx-recover pair" again.' }
    $vault = Join-Path $conf.QMX_HOME 'vault'
    $key = Join-Path $vault 'pairing-key'
    New-Item -ItemType Directory -Force -Path $vault | Out-Null
    if (Test-Path -LiteralPath $key) {
        Move-Item -LiteralPath $key -Destination (Join-Path $vault 'pairing-key.previous') -Force
        Remove-Item -LiteralPath (Join-Path $vault 'run-pass-key') -Force -ErrorAction SilentlyContinue
    }
    [IO.File]::WriteAllText("$key.tmp", "$code`n")
    Move-Item -LiteralPath "$key.tmp" -Destination $key -Force
    'Paired: this PC holds the new code, and the old one is kept for passes already handed out.'
    'Restart QMX on this PC so it uses the new code: qmx-recover restart'
}

function Invoke-Vault {
    if (-not (Test-Python)) { throw "QMX's Python does not work on this PC, so the key copy cannot be built. Reinstall QMX here first." }
    Invoke-Qmx @('node', 'vault', 'install', '--ssh-host', $conf.TARGET, '--pc-home', $conf.QMX_HOME)
}

function Invoke-Restart {
    if (-not (Test-Python)) { throw "QMX's Python does not work on this PC. Reinstall QMX here first." }
    & $conf.PYTHON -m qmx_host stop --home $conf.QMX_HOME
    & $conf.PYTHON -m qmx_host start --home $conf.QMX_HOME --port $conf.PORT
}

function Show-Logs {
    $log = Join-Path $conf.QMX_HOME 'control.log'
    if (-not (Test-Path -LiteralPath $log)) { "There is no log at $log yet."; return }
    Get-Content -LiteralPath $log -Tail 200
}

try {
    switch ($What) {
        'status' { Show-Status }
        'server' { Invoke-Server $Rest }
        'pair' { Invoke-Pair }
        'vault' { Invoke-Vault }
        'restart' { Invoke-Restart }
        'logs' { Show-Logs }
        { $_ -in 'help', '-h', '--help' } { Show-Help }
        default { "There is no ""$What"". Run ""qmx-recover help"" for the list."; exit 2 }
    }
} catch {
    $_.Exception.Message
    exit 1
}
