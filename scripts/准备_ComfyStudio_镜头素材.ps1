param(

    [Parameter(Mandatory=$true)]
    [string]$ManifestPath
)

$ErrorActionPreference = "Stop"

$RegistryPath = "F:\一人公司\comfyui-production\config\comfystudio\asset_registry.json"

$WorkerInput = "G:\ComfyStudioData\workers\h3-f\input"

$ReportRoot = "F:\一人公司\comfyui-production\reports\comfystudio"


if (-not (Test-Path -LiteralPath $ManifestPath)) {

    throw "镜头Manifest不存在：$ManifestPath"
}


$Manifest = Get-Content 
    -LiteralPath $ManifestPath 
    -Raw |
ConvertFrom-Json


$Registry = Get-Content 
    -LiteralPath $RegistryPath 
    -Raw |
ConvertFrom-Json


$Assets = @($Registry.assets)

New-Item 
    -ItemType Directory 
    -Force 
    -Path $WorkerInput |
Out-Null

New-Item 
    -ItemType Directory 
    -Force 
    -Path $ReportRoot |
Out-Null


$Results = @()


function Stage-Asset {

    param(
        [string]$AssetId,
        [string]$Prefix,
        [int]$Index
    )


    $Match = @(
        $Assets |
        Where-Object {
            $_.id -eq $AssetId
        }
    )


    if ($Match.Count -eq 0) {

        throw "找不到 AssetId：$AssetId"
    }


    $Asset = $Match[0]


    if (-not (Test-Path -LiteralPath $Asset.path)) {

        throw "注册资产文件不存在：$($Asset.path)"
    }


    $Ext = [System.IO.Path]::GetExtension(
        $Asset.path
    )


    $SafeId = $AssetId -replace '[^a-zA-Z0-9._-]', '_'

    $TargetName = (
        "{0}{1:D2}_{2}{3}" -f 
        $Prefix,
        $Index,
        $SafeId,
        $Ext
    )


    $Target = Join-Path 
        $WorkerInput 
        $TargetName


    Copy-Item 
        -LiteralPath $Asset.path 
        -Destination $Target 
        -Force


    $Hash = (
        Get-FileHash 
            -LiteralPath $Target 
            -Algorithm SHA256
    ).Hash


    $script:Results += [pscustomobject]@{

        asset_id = $AssetId

        target = $Target

        sha256 = $Hash
    }
}


$ImageRefs = @(
    $Manifest.bindings.image_refs
)

$VideoRefs = @(
    $Manifest.bindings.video_refs
)

$AudioRefs = @(
    $Manifest.bindings.audio_refs
)


for ($i = 0; $i -lt $ImageRefs.Count; $i++) {

    Stage-Asset 
        -AssetId $ImageRefs[$i] 
        -Prefix "IMG" 
        -Index ($i + 1)
}


for ($i = 0; $i -lt $VideoRefs.Count; $i++) {

    Stage-Asset 
        -AssetId $VideoRefs[$i] 
        -Prefix "VID" 
        -Index ($i + 1)
}


for ($i = 0; $i -lt $AudioRefs.Count; $i++) {

    Stage-Asset 
        -AssetId $AudioRefs[$i] 
        -Prefix "AUD" 
        -Index ($i + 1)
}


$ReportPath = Join-Path 
    $ReportRoot 
    ("stage-" + $Manifest.shot_id + "-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")


$Report = [ordered]@{

    shot_id = $Manifest.shot_id

    manifest = $ManifestPath

    worker_input = $WorkerInput

    staged_at = (Get-Date).ToString("s")

    assets = $Results
}


$Report |
ConvertTo-Json -Depth 30 |
Set-Content 
    -LiteralPath $ReportPath 
    -Encoding UTF8


Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "SHOT_STAGE_GATE = PASS" -ForegroundColor Green
Write-Host "============================================"

Write-Host "镜头：" $Manifest.shot_id
Write-Host "已准备素材：" $Results.Count
Write-Host "报告：" $ReportPath

$Results |
Format-Table -AutoSize
