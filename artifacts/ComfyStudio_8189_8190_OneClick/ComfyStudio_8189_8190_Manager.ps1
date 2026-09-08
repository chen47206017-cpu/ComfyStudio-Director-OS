[CmdletBinding()]
param([switch]$CheckOnly,[switch]$NoBrowser)
$ErrorActionPreference = "Stop"
$ProductionRoot = $PSScriptRoot
$StudioRoot = Join-Path $ProductionRoot "ComfyStudio_StudioOS_CURRENT"
$ComfyRoot = Join-Path $ProductionRoot "staging\comfyui-v0.34.0\ComfyUI-0.34.0"
$ComfyPython = Join-Path $ComfyRoot ".venv\Scripts\python.exe"
$ExtraModels = Join-Path $ComfyRoot "extra_model_paths.yaml"
$StudioPython = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $StudioPython) { $StudioPython = "C:\Users\chen4\AppData\Local\Programs\Python\Python312\python.exe" }
$ComfyUrl = "http://127.0.0.1:8189"
$StudioUrl = "http://127.0.0.1:8190"
$LogRoot = Join-Path $ProductionRoot "upgrade_logs\startup"
New-Item -ItemType Directory -Force -Path $LogRoot | Out-Null
function Get-BeijingStamp { [DateTimeOffset]::Now.ToOffset([TimeSpan]::FromHours(8)).ToString("yyyy-MM-ddTHH:mm:ss+08:00") }
function Write-StartupLog([string]$Message) { $line = "[{0}] {1}" -f (Get-BeijingStamp), $Message; Write-Host $line; Add-Content -LiteralPath (Join-Path $LogRoot "startup.log") -Value $line -Encoding ASCII }
function Test-Service([string]$Url,[string]$Path) { try { $r=Invoke-WebRequest -UseBasicParsing -Uri ($Url+$Path) -TimeoutSec 5; [pscustomobject]@{Online=($r.StatusCode -ge 200 -and $r.StatusCode -lt 500);Status=$r.StatusCode;Error=$null} } catch { [pscustomobject]@{Online=$false;Status=$null;Error=$_.Exception.Message} } }
function Wait-Service([string]$Name,[string]$Url,[string]$Path,[int]$TimeoutSeconds) { $deadline=(Get-Date).AddSeconds($TimeoutSeconds); do { $check=Test-Service $Url $Path; if($check.Online){Write-StartupLog "$Name online HTTP $($check.Status)";return $true}; Start-Sleep -Seconds 2 } while((Get-Date)-lt $deadline); Write-StartupLog "$Name timeout: $($check.Error)"; return $false }
Write-StartupLog "Checking ComfyUI 8189 and ComfyStudio 8190"
$comfyCheck=Test-Service $ComfyUrl "/system_stats"
$studioCheck=Test-Service $StudioUrl "/api/v10/health/live"
if($comfyCheck.Online){Write-StartupLog "ComfyUI 8189 already online"} elseif($CheckOnly){Write-StartupLog "CheckOnly: ComfyUI 8189 offline; no start"} else { if(-not(Test-Path $ComfyPython)){throw "Missing ComfyUI Python"}; if(-not(Test-Path $ExtraModels)){throw "Missing model config"}; Write-StartupLog "Starting isolated ComfyUI 8189 in background"; Start-Process -FilePath $ComfyPython -WorkingDirectory $ComfyRoot -ArgumentList @("main.py","--listen","127.0.0.1","--port","8189","--preview-method","auto","--extra-model-paths-config",$ExtraModels) -RedirectStandardOutput (Join-Path $LogRoot "comfyui-8189.stdout.log") -RedirectStandardError (Join-Path $LogRoot "comfyui-8189.stderr.log") -WindowStyle Hidden }
if($studioCheck.Online){Write-StartupLog "ComfyStudio 8190 already online"} elseif($CheckOnly){Write-StartupLog "CheckOnly: ComfyStudio 8190 offline; no start"} else { if(-not(Test-Path $StudioRoot)){throw "Missing StudioOS"}; Write-StartupLog "Starting ComfyStudio 8190 in background"; Start-Process -FilePath $StudioPython -WorkingDirectory $StudioRoot -ArgumentList @("backend\app.py") -RedirectStandardOutput (Join-Path $LogRoot "studioos-8190.stdout.log") -RedirectStandardError (Join-Path $LogRoot "studioos-8190.stderr.log") -WindowStyle Hidden }
$comfyReady = Wait-Service "ComfyUI 8189" $ComfyUrl "/system_stats" 180
$studioReady = Wait-Service "ComfyStudio 8190" $StudioUrl "/api/v10/health/live" 45
if($comfyReady -and $studioReady){Write-StartupLog "Startup check passed: 8189 and 8190 online"; if(-not $CheckOnly -and -not $NoBrowser){Start-Process "$StudioUrl/director/"}; exit 0}
Write-StartupLog "Startup check failed: ComfyUI=$comfyReady, ComfyStudio=$studioReady"; exit 1

