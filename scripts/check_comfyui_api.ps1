[CmdletBinding()]
param(
    [int]$Port = 0
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot

function Resolve-IntegrationApiPort {
    param([int]$DefaultPort = 8092)

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
        $health = Invoke-RestMethod -Uri "$baseUrl/health" -Method Get -TimeoutSec 5
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
        $catalog = Invoke-RestMethod -Uri "$baseUrl/engines" -Method Get -TimeoutSec 5
    } catch {
        return [pscustomobject]@{
            State = 'HEALTH_ONLY'
            Error = "Health succeeded at $baseUrl, but GET /engines failed. This is a health-only listener; no replacement was started."
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
        $plan = Invoke-RestMethod -Uri "$baseUrl/h3/dry-run" -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 5
    } catch {
        return [pscustomobject]@{
            State = 'HEALTH_ONLY'
            Error = "Health and catalog succeeded at $baseUrl, but POST /h3/dry-run failed. This is not the H3 control plane; no replacement was started."
        }
    }
    if ($plan.execution -ne 'DRY_RUN_ONLY' -or $plan.local_status -ne 'BLOCKED_LOCAL_H3') {
        return [pscustomobject]@{
            State = 'INCOMPLETE'
            Error = "The listener at $baseUrl returned an unexpected H3 dry-run state."
        }
    }
    return [pscustomobject]@{
        State = 'CAPABLE'
        Health = $health
        Catalog = $catalog
        Plan = $plan
    }
}

if ($Port -lt 0 -or $Port -gt 65535) {
    throw 'Port must be between 1 and 65535 when supplied.'
}
$effectivePort = if ($Port -gt 0) { $Port } else { Resolve-IntegrationApiPort }
$probe = Test-IntegrationApiCapability -ApiPort $effectivePort
if ($probe.State -eq 'CAPABLE') {
    [pscustomobject]@{
        ok = $true
        service = 'comfyui-production'
        api_port = $effectivePort
        h3_engine = 'MINIMAX_H3'
        h3_local_status = $probe.Plan.local_status
        dry_run_execution = $probe.Plan.execution
        workflow_id = $probe.Plan.workflow_id
        vendor_task_id = $null
    } | ConvertTo-Json -Depth 10
    exit 0
}
[Console]::Error.WriteLine("ComfyUI API capability check failed at http://127.0.0.1:$effectivePort/api/comfyui : $($probe.Error)")
if ($probe.State -eq 'HEALTH_ONLY' -or $probe.State -eq 'INCOMPLETE') { exit 2 }
exit 1
