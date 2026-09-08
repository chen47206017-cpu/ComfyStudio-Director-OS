[CmdletBinding()]
param(
    [int]$Port = 8188,
    [switch]$OpenBrowser,
    [switch]$NoBrowser,
    [switch]$Wait
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ComfyRoot = 'G:\ComfyUI'
$Python = Join-Path $ComfyRoot 'venv\Scripts\python.exe'
$Runtime = Join-Path $ProjectRoot 'runtime'
$PidFile = Join-Path $Runtime 'comfyui-local.pid'
$OutLog = Join-Path $Runtime 'comfyui-local.log'
$ErrLog = Join-Path $Runtime 'comfyui-local.err.log'
$BaseUri = "http://127.0.0.1:$Port"
$HealthUri = "$BaseUri/system_stats"

function Resolve-AutoOpen {
    # Process environment wins; project .env is only a fallback. Keep this
    # parser narrow so unrelated dotenv values are never used.
    $raw = [Environment]::GetEnvironmentVariable('COMFY_AUTO_OPEN')
    if ($null -eq $raw) {
        $dotenvPath = Join-Path $ProjectRoot '.env'
        if (Test-Path -LiteralPath $dotenvPath -PathType Leaf) {
            foreach ($line in Get-Content -LiteralPath $dotenvPath) {
                if ($line -match '^\s*(?:export\s+)?COMFY_AUTO_OPEN\s*=\s*(?<value>.*)$') {
                    $raw = $Matches['value'].Trim()
                    if ($raw.StartsWith('"') -or $raw.StartsWith("'")) {
                        if ($raw.Length -ge 2 -and (($raw.StartsWith('"') -and $raw.EndsWith('"')) -or ($raw.StartsWith("'") -and $raw.EndsWith("'")))) {
                            $raw = $raw.Substring(1, $raw.Length - 2)
                        }
                    }
                }
            }
        }
    }
    if ($null -eq $raw -or [string]::IsNullOrWhiteSpace([string]$raw)) { return $false }
    switch (([string]$raw).Trim().ToLowerInvariant()) {
        '1' { return $true }
        'true' { return $true }
        'yes' { return $true }
        'on' { return $true }
        '0' { return $false }
        'false' { return $false }
        'no' { return $false }
        'off' { return $false }
        default { throw 'COMFY_AUTO_OPEN must be one of 0, 1, true, false, yes, no, on, or off.' }
    }
}

$openBrowserRequested = (-not $NoBrowser) -and ($OpenBrowser -or (Resolve-AutoOpen))

function Test-ComfyUiHealth {
    try {
        $null = Invoke-RestMethod -Uri $HealthUri -Method Get -TimeoutSec 3
        return $true
    } catch {
        return $false
    }
}

if ($Port -lt 1 -or $Port -gt 65535) {
    throw 'Port must be between 1 and 65535.'
}
if (-not (Test-Path -LiteralPath $Python)) {
    throw "ComfyUI Python was not found: $Python"
}

$null = New-Item -ItemType Directory -Force -Path $Runtime
if (Test-ComfyUiHealth) {
    Write-Output "ComfyUI is already reachable at $BaseUri."
    if ($openBrowserRequested) { Start-Process $BaseUri }
    exit 0
}

if (Test-Path -LiteralPath $PidFile) {
    $recordedPid = 0
    try { $recordedPid = [int](Get-Content -Raw -LiteralPath $PidFile) } catch { }
    if ($recordedPid -gt 0 -and (Get-Process -Id $recordedPid -ErrorAction SilentlyContinue)) {
        throw "The recorded ComfyUI process $recordedPid is still running but $HealthUri is unavailable. Check $ErrLog before starting another instance."
    }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}

$torchLib = Join-Path $ComfyRoot 'venv\Lib\site-packages\torch\lib'
$previousPath = $env:PATH
$env:PATH = "$torchLib;$previousPath"
try {
    $arguments = @('main.py', '--listen', '127.0.0.1', '--port', "$Port", '--preview-method', 'auto')
    $process = Start-Process -FilePath $Python -ArgumentList $arguments -WorkingDirectory $ComfyRoot `
        -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru -WindowStyle Hidden
} finally {
    $env:PATH = $previousPath
}

$process.Id | Set-Content -LiteralPath $PidFile -Encoding ascii
Write-Output "Started ComfyUI (PID $($process.Id)) at $BaseUri."

if ($Wait -or $openBrowserRequested) {
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-ComfyUiHealth) {
            if ($openBrowserRequested) { Start-Process $BaseUri }
            Write-Output "ComfyUI is healthy at $BaseUri."
            exit 0
        }
    }
    throw "ComfyUI did not become reachable at $HealthUri. Check $ErrLog."
}
