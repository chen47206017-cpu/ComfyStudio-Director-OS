[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path (Join-Path $ProjectRoot 'runtime') 'comfyui-local.pid'

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Output 'No ComfyUI process is managed by this project.'
    exit 0
}

$pidValue = 0
try { $pidValue = [int](Get-Content -Raw -LiteralPath $PidFile) } catch { }
if ($pidValue -le 0) {
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    throw 'The managed ComfyUI PID file was invalid.'
}

$process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
if (-not $process) {
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    Write-Output "Managed ComfyUI process $pidValue was already stopped."
    exit 0
}

if ($process.ProcessName -notin @('python', 'pythonw')) {
    throw "Refusing to stop PID $pidValue because it is $($process.ProcessName), not Python."
}

Stop-Process -Id $pidValue
Wait-Process -Id $pidValue -Timeout 15 -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
Write-Output "Stopped managed ComfyUI process $pidValue."
