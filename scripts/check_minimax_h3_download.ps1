[CmdletBinding()]
param(
    [string]$ManifestPath = ''
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ManifestPath)) {
    $ManifestPath = Join-Path $PSScriptRoot '..\minimax_h3.download-state.json'
}

function Fail([string]$Message) {
    [pscustomobject]@{
        ok = $false
        error = $Message
        inspection = 'DEFERRED'
    } | ConvertTo-Json -Depth 8
    exit 2
}

try {
    $resolvedManifest = [System.IO.Path]::GetFullPath($ManifestPath)
    if (-not (Test-Path -LiteralPath $resolvedManifest -PathType Leaf)) {
        Fail "Manifest not found: $resolvedManifest"
    }

    # This is deliberately the only file read: the project-local manifest.
    $manifest = Get-Content -LiteralPath $resolvedManifest -Raw | ConvertFrom-Json
    if ($null -eq $manifest -or $manifest.schema_version -ne 1) {
        Fail 'Unsupported or missing manifest schema_version.'
    }
    if ($manifest.state -notin @('PENDING_USER_DOWNLOAD', 'DEFERRED')) {
        Fail "Unsafe manifest state: $($manifest.state)"
    }
    if ($manifest.inspection_policy.filesystem_access -ne 'MANIFEST_ONLY' -or
        $manifest.inspection_policy.model_files -ne 'DEFERRED' -or
        $manifest.inspection_policy.hashing -ne 'DEFERRED' -or
        $manifest.inspection_policy.model_loading -ne 'PROHIBITED') {
        Fail 'Manifest inspection policy is not safe for an active transfer.'
    }

    $artifacts = @($manifest.artifacts)
    if ($artifacts.Count -ne 6) {
        Fail "Expected six H3 artifacts; found $($artifacts.Count)."
    }
    foreach ($artifact in $artifacts) {
        if ($artifact.status -notin @('PENDING', 'DEFERRED') -or
            $artifact.verification -ne 'DEFERRED' -or
            $null -ne $artifact.size_bytes -or
            $null -ne $artifact.sha256) {
            Fail "Artifact is not deferred-only: $($artifact.id)"
        }
    }

    [pscustomobject]@{
        ok = $true
        state = [string]$manifest.state
        inspection = 'DEFERRED'
        filesystem_access = 'MANIFEST_ONLY'
        network_access = 'NONE'
        proxy_changes = 'NONE'
        source_verification = [string]$manifest.source_verification.status
        artifact_count = $artifacts.Count
        pending_count = @($artifacts | Where-Object { $_.status -eq 'PENDING' }).Count
        artifacts = @($artifacts | ForEach-Object {
            [pscustomobject]@{
                id = [string]$_.id
                status = [string]$_.status
                verification = [string]$_.verification
                repository = [string]$_.repository
                source_path = [string]$_.source_path
                target_relative_path = [string]$_.target_relative_path
            }
        })
        next_step = [string]$manifest.next_step
    } | ConvertTo-Json -Depth 8
    exit 0
} catch {
    Fail "Manifest validation failed: $($_.Exception.Message)"
}
