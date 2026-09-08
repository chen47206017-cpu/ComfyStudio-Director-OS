[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path (Join-Path $Root 'runtime') 'comfyui-api.pid'
if (-not (Test-Path $PidFile)) {
    Write-Output 'ComfyUI API is not running (no PID file).'
    exit 0
}

$pidValue = 0
try { $pidValue = [int](Get-Content -Raw $PidFile) } catch { $pidValue = 0 }
if ($pidValue -gt 0) {
    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if (-not $process) {
        Write-Output "ComfyUI API process $pidValue was not found."
    } else {
        try {
            $proc = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $pidValue" -ErrorAction Stop
        } catch {
            throw "Unable to verify the command line for managed PID $pidValue; it was not stopped or removed."
        }
        $commandLine = [string]$proc.CommandLine
        if ($commandLine -notlike '*comfyui_production.server*') {
            throw "PID file $PidFile points to unrelated process $pidValue; it was not stopped or removed."
        }
        Stop-Process -Id $pidValue -ErrorAction Stop
        try { Wait-Process -Id $pidValue -Timeout 10 -ErrorAction SilentlyContinue } catch { }
        Write-Output "Stopped ComfyUI production API (PID $pidValue)."
    }
}
Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
