param(

    [Parameter(Mandatory=$true)]
    [string]$SourcePath,

    [Parameter(Mandatory=$true)]
    [ValidateSet(
        "character",
        "scene",
        "prop",
        "voice",
        "dialogue",
        "sfx",
        "ambience",
        "video_reference"
    )]
    [string]$AssetType,

    [Parameter(Mandatory=$true)]
    [string]$TargetSubfolder,

    [Parameter(Mandatory=$true)]
    [string]$TargetName,

    [Parameter(Mandatory=$true)]
    [string]$AssetId,

    [string]$ProjectId = "",

    [string]$Episode = "",

    [switch]$Replace
)

$ErrorActionPreference = "Stop"

$AssetRoot = "G:\ComfyStudioData\assets"

$RegistryPath = "F:\一人公司\comfyui-production\config\comfystudio\asset_registry.json"


if (-not (Test-Path -LiteralPath $SourcePath)) {

    throw "源素材不存在：$SourcePath"
}


$TypeMap = @{

    character = "characters"

    scene = "scenes"

    prop = "props"

    voice = "audio\voices"

    dialogue = "audio\dialogue"

    sfx = "audio\sfx"

    ambience = "audio\ambience"

    video_reference = "video_reference"
}


$RelativeRoot = $TypeMap[$AssetType]

$DestinationRoot = Join-Path 
    $AssetRoot 
    $RelativeRoot

if ($TargetSubfolder) {

    $DestinationDir = Join-Path 
        $DestinationRoot 
        $TargetSubfolder
}
else {

    $DestinationDir = $DestinationRoot
}


New-Item 
    -ItemType Directory 
    -Force 
    -Path $DestinationDir |
Out-Null


$Destination = Join-Path 
    $DestinationDir 
    $TargetName


if (
    (Test-Path -LiteralPath $Destination) -and
    (-not $Replace)
) {

    throw "目标文件已经存在。需要覆盖时加入 -Replace：$Destination"
}


Copy-Item 
    -LiteralPath $SourcePath 
    -Destination $Destination 
    -Force


$Hash = (
    Get-FileHash 
        -LiteralPath $Destination 
        -Algorithm SHA256
).Hash


$Registry = Get-Content 
    -LiteralPath $RegistryPath 
    -Raw |
ConvertFrom-Json


$Assets = @($Registry.assets)

$Existing = @(
    $Assets |
    Where-Object {
        $_.id -eq $AssetId
    }
)


if (
    ($Existing.Count -gt 0) -and
    (-not $Replace)
) {

    throw "AssetId已经存在：$AssetId。需要替换时加入 -Replace。"
}


if ($Existing.Count -gt 0) {

    $Assets = @(
        $Assets |
        Where-Object {
            $_.id -ne $AssetId
        }
    )
}


$Entry = [pscustomobject]@{

    id = $AssetId

    type = $AssetType

    path = $Destination

    sha256 = $Hash

    project_id = $ProjectId

    episode = $Episode

    status = "active"

    created_at = (Get-Date).ToString("s")
}


$Registry.assets = @(
    $Assets + $Entry
)

$Registry.updated_at = (
    Get-Date
).ToString("s")


$Registry |
ConvertTo-Json -Depth 30 |
Set-Content 
    -LiteralPath $RegistryPath 
    -Encoding UTF8


Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "ASSET_IMPORT_GATE = PASS" -ForegroundColor Green
Write-Host "============================================"

Write-Host "Asset ID：" $AssetId
Write-Host "类型：" $AssetType
Write-Host "目标：" $Destination
Write-Host "SHA256：" $Hash
