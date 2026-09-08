[CmdletBinding()]
param(
    [int]$Port = 0,
    [switch]$Wait
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Runtime = Join-Path $Root 'runtime'
$PidFile = Join-Path $Runtime 'comfyui-api.pid'
$OutLog = Join-Path $Runtime 'comfyui-api.log'
$ErrLog = Join-Path $Runtime 'comfyui-api.err.log'
$null = New-Item -ItemType Directory -Force -Path $Runtime

function Resolve-IntegrationApiPort {
    param([int]$DefaultPort = 8092)

    # Settings.from_env reads the project .env only when the process variable
    # is absent. Mirror that precedence here so the health probe and child
    # process use the same port.
    $raw = [Environment]::GetEnvironmentVariable('COMFY_API_PORT')
    if ($null -eq $raw) {
        $dotenvPath = Join-Path $Root '.env'
        if (Test-Path -LiteralPath $dotenvPath -PathType Leaf) {
            foreach ($line in Get-Content -LiteralPath $dotenvPath) {
                if ($line -match '^\s*(?:export\s+)?COMFY_API_PORT\s*=\s*(?<value>.*)$') {
                    $value = $Matches['value'].Trim()
                    if ($value.StartsWith('"') -or $value.StartsWith("'")) {
                        if ($value.Length -lt 2 -or -not (
                            ($value.StartsWith('"') -and $value.EndsWith('"')) -or
                            ($value.StartsWith("'") -and $value.EndsWith("'"))
                        )) {
                            continue
                        }
                        $value = $value.Substring(1, $value.Length - 2)
                    }
                    $raw = $value
                }
            }
        }
    }
    if ($null -eq $raw) { return $DefaultPort }
    $raw = ([string]$raw).Trim()
    if ($raw -notmatch '^\d+$') {
        throw 'COMFY_API_PORT must be an integer between 1 and 65535.'
    }
    $resolved = [int]$raw
    if ($resolved -lt 1 -or $resolved -gt 65535) {
        throw 'COMFY_API_PORT must be an integer between 1 and 65535.'
    }
    return $resolved
}

function Test-IntegrationApiCapability {
    param([int]$ApiPort)

    $baseUrl = "http://127.0.0.1:$ApiPort/api/comfyui"
    try {
        $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 2
    } catch {
        return [pscustomobject]@{
            State = 'UNREACHABLE'
            Error = "No integration API response at $baseUrl : $($_.Exception.Message)"
        }
    }
    if ($health.ok -ne $true -or $health.service -ne 'comfyui-production') {
        return [pscustomobject]@{
            State = 'UNHEALTHY'
            Error = "The listener at $baseUrl returned a non-comfyui-production health response."
        }
    }
    try {
        $catalog = Invoke-RestMethod -Uri "$baseUrl/engines" -Method Get -TimeoutSec 2
    } catch {
        return [pscustomobject]@{
            State = 'HEALTH_ONLY'
            Error = "Health succeeded at $baseUrl, but GET /engines failed. Refusing to start a replacement."
        }
    }
    $engine = @($catalog.engines) | Where-Object { $_.id -eq 'MINIMAX_H3' } | Select-Object -First 1
    if ($null -eq $engine) {
        return [pscustomobject]@{
            State = 'INCOMPLETE'
            Error = "The listener at $baseUrl has no MINIMAX_H3 engine catalog entry."
        }
    }
    $body = @{
        engine = 'MINIMAX_H3'
        prompt = 'control-plane capability probe'
        duration = 5
        reference_images = @('https://media.example.test/reference.png')
    } | ConvertTo-Json -Compress
    try {
        $plan = Invoke-RestMethod -Uri "$baseUrl/h3/dry-run" -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 2
    } catch {
        return [pscustomobject]@{
            State = 'HEALTH_ONLY'
            Error = "Health and catalog succeeded at $baseUrl, but POST /h3/dry-run failed. Refusing to start a replacement."
        }
    }
    if ($plan.execution -ne 'DRY_RUN_ONLY' -or $plan.local_status -ne 'BLOCKED_LOCAL_H3') {
        return [pscustomobject]@{
            State = 'INCOMPLETE'
            Error = "The listener at $baseUrl returned an unexpected H3 dry-run state."
        }
    }
    return [pscustomobject]@{ State = 'CAPABLE'; Plan = $plan }
}

# Prefer the service's own health response over PID inspection.  On some
# Windows configurations querying another Python process' command line is
# denied; a healthy loopback API is still definitive evidence that starting
# another listener would be unsafe.
$configuredPort = Resolve-IntegrationApiPort
$healthPort = if ($Port -gt 0) { $Port } else { $configuredPort }
$healthUrl = "http://127.0.0.1:$healthPort/api/comfyui"
$probe = Test-IntegrationApiCapability -ApiPort $healthPort
if ($probe.State -eq 'CAPABLE') {
    Write-Output "ComfyUI production API is already healthy and H3-capable at $healthUrl."
    exit 0
}
if ($probe.State -ne 'UNREACHABLE') {
    throw "Refusing to start another integration API at $healthUrl. $($probe.Error)"
}

if (Test-Path $PidFile) {
    $oldPid = 0
    try {
        $oldPid = [int](Get-Content -Raw $PidFile)
    } catch {
        $oldPid = 0
    }
    if ($oldPid -gt 0) {
        $old = Get-CimInstance -ClassName Win32_Process -Filter "ProcessId = $oldPid" -ErrorAction SilentlyContinue
        if ($old) {
            $commandLine = [string]$old.CommandLine
            if ($commandLine -like '*comfyui_production.server*') {
                Write-Output "ComfyUI API already running (PID $oldPid)."
                exit 0
            }
            throw "PID file $PidFile points to unrelated process $oldPid; it was not modified. Verify it and remove the stale PID file manually."
        }
    }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw 'python was not found on PATH'
}

$env:PYTHONPATH = Join-Path $Root 'src'
$arguments = @('-m', 'comfyui_production.server', '--port', "$healthPort")

$proc = Start-Process -FilePath $python.Source -ArgumentList $arguments -WorkingDirectory $Root `
    -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru -WindowStyle Hidden
$proc.Id | Set-Content -LiteralPath $PidFile -Encoding ascii
Write-Output "Started ComfyUI production API (PID $($proc.Id))."

if ($Wait) {
    $url = $healthUrl
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        if ($proc.HasExited) {
            Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
            throw "ComfyUI API exited before becoming healthy. Check $ErrLog."
        }
        $response = Test-IntegrationApiCapability -ApiPort $healthPort
        if ($response.State -eq 'CAPABLE') {
            [pscustomobject]@{
                ok = $true
                service = 'comfyui-production'
                api_port = $healthPort
                h3_local_status = $response.Plan.local_status
                dry_run_execution = $response.Plan.execution
                workflow_id = $response.Plan.workflow_id
            } | ConvertTo-Json -Depth 8
            break
        } # capability probe completed
        if ($response.State -ne 'UNREACHABLE' -and $i -eq 29) {
            throw "API became reachable at $url but failed the H3 capability check: $($response.Error)"
        }
        if ($i -eq 29) { throw "API did not become H3-capable at $url" }
    }
}
