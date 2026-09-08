[CmdletBinding()]
param(
    [int]$Port = 8188
)

$ErrorActionPreference = 'Stop'
$uri = "http://127.0.0.1:$Port/system_stats"
try {
    $result = Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec 5
    $result | ConvertTo-Json -Depth 8
    exit 0
} catch {
    Write-Error "ComfyUI health check failed at $uri : $($_.Exception.Message)"
    exit 1
}
