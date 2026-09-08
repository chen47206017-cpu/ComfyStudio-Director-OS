$ErrorActionPreference = "Stop"

# ============================================================
# ComfyStudio V1 Asset Library Bootstrap
# 目标：
# 1. G盘 = 大型素材 / 项目 / 输出
# 2. F盘 = 程序 / 索引 / Workflow / Runtime
# 3. 不修改 G:\ComfyUI
# 4. 不修改 H3 Runtime
# ============================================================

$StudioRoot = "F:\一人公司\comfyui-production"
$DataRoot   = "G:\ComfyStudioData"

$ConfigRoot = "$StudioRoot\config\comfystudio"
$ScriptRoot = "$StudioRoot\scripts"
$ReportRoot = "$StudioRoot\reports\comfystudio"
$RuntimeRoot = "$StudioRoot\runtime\asset-library"

$AssetRoot  = "$DataRoot\assets"
$ProjectRoot = "$DataRoot\projects"
$WorkerRoot = "$DataRoot\workers"

$ProjectName = "楼上是25岁的我，楼下是未来女儿"
$ProjectId   = "upstairs_25_future_daughter"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "ComfyStudio V1 资料库初始化" -ForegroundColor Cyan
Write-Host "============================================================"

# ============================================================
# 0. 基础盘符门禁
# ============================================================

if (-not (Test-Path "F:\")) {
    throw "FAIL：F盘不存在。"
}

if (-not (Test-Path "G:\")) {
    throw "FAIL：G盘不存在。"
}

Write-Host "DRIVE_F_GATE = PASS" -ForegroundColor Green
Write-Host "DRIVE_G_GATE = PASS" -ForegroundColor Green


# ============================================================
# 1. 创建 G盘 Asset Library
# ============================================================

$Directories = @(

    # ---------------- Characters ----------------
    "$AssetRoot\characters",
    "$AssetRoot\characters\苏婉晴",
    "$AssetRoot\characters\苏婉晴\25岁",
    "$AssetRoot\characters\苏婉晴\45岁",

    "$AssetRoot\characters\陈远舟",
    "$AssetRoot\characters\陈远舟\27岁",
    "$AssetRoot\characters\陈远舟\47岁",

    "$AssetRoot\characters\陈念",
    "$AssetRoot\characters\陈念\40岁",

    "$AssetRoot\characters\顾川",
    "$AssetRoot\characters\顾川\48岁",

    # ---------------- Scenes ----------------
    "$AssetRoot\scenes",
    "$AssetRoot\scenes\2006",
    "$AssetRoot\scenes\2006\苏婉晴工作室",
    "$AssetRoot\scenes\2026",
    "$AssetRoot\scenes\2046",

    # ---------------- Props ----------------
    "$AssetRoot\props",
    "$AssetRoot\props\2006",
    "$AssetRoot\props\2026",
    "$AssetRoot\props\2046",

    # ---------------- Audio ----------------
    "$AssetRoot\audio",
    "$AssetRoot\audio\voices",
    "$AssetRoot\audio\voices\苏婉晴\25岁",
    "$AssetRoot\audio\voices\苏婉晴\45岁",
    "$AssetRoot\audio\voices\陈远舟\27岁",
    "$AssetRoot\audio\voices\陈远舟\47岁",
    "$AssetRoot\audio\voices\陈念\40岁",
    "$AssetRoot\audio\voices\顾川\48岁",

    "$AssetRoot\audio\dialogue",
    "$AssetRoot\audio\dialogue\E01",
    "$AssetRoot\audio\dialogue\E02",

    "$AssetRoot\audio\sfx",
    "$AssetRoot\audio\ambience",

    # ---------------- Video Reference ----------------
    "$AssetRoot\video_reference",
    "$AssetRoot\video_reference\E01",
    "$AssetRoot\video_reference\E02",

    # ---------------- Generic References ----------------
    "$AssetRoot\reference_images",
    "$AssetRoot\reference_video",

    # ---------------- Project ----------------
    "$ProjectRoot\$ProjectName",
    "$ProjectRoot\$ProjectName\canon",

    "$ProjectRoot\$ProjectName\episodes",

    "$ProjectRoot\$ProjectName\episodes\E01",
    "$ProjectRoot\$ProjectName\episodes\E01\shots",
    "$ProjectRoot\$ProjectName\episodes\E01\references",
    "$ProjectRoot\$ProjectName\episodes\E01\audio",

    "$ProjectRoot\$ProjectName\episodes\E02",
    "$ProjectRoot\$ProjectName\episodes\E02\shots",
    "$ProjectRoot\$ProjectName\episodes\E02\references",
    "$ProjectRoot\$ProjectName\episodes\E02\audio",

    # ---------------- Worker ----------------
    "$WorkerRoot\h3-f",
    "$WorkerRoot\h3-f\input",
    "$WorkerRoot\h3-f\output",

    # ---------------- Archive ----------------
    "$DataRoot\archive",

    # ---------------- F盘 ----------------
    $ConfigRoot,
    $ScriptRoot,
    $ReportRoot,
    $RuntimeRoot,
    "$StudioRoot\workflows\generated"
)

foreach ($Dir in $Directories) {

    New-Item `
        -ItemType Directory `
        -Force `
        -Path $Dir |
    Out-Null
}

Write-Host ""
Write-Host "DIRECTORY_GATE = PASS" -ForegroundColor Green


# ============================================================
# 2. 导入现有 苏婉晴45 参考资产
#
# Canon人物名：
# 苏婉晴
#
# 旧文件可能误写：
# 苏晚晴45.png
# ============================================================

$SW45Destination = "$AssetRoot\characters\苏婉晴\45岁\CHAR_SW45_MASTER_v1.png"

$SW45Sources = @(
    "F:\AI短剧\苏晚晴45.png",
    "$WorkerRoot\h3-f\input\H3_SMOKE_SW45.png"
)

$SW45Imported = $false
$SW45SourceUsed = ""

foreach ($Source in $SW45Sources) {

    if (Test-Path -LiteralPath $Source) {

        Copy-Item `
            -LiteralPath $Source `
            -Destination $SW45Destination `
            -Force

        $SW45Imported = $true
        $SW45SourceUsed = $Source

        break
    }
}

if ($SW45Imported) {

    $SW45Hash = (
        Get-FileHash `
            -LiteralPath $SW45Destination `
            -Algorithm SHA256
    ).Hash

    Write-Host "SW45_MASTER_IMPORT = PASS" -ForegroundColor Green
    Write-Host "来源：" $SW45SourceUsed
    Write-Host "目标：" $SW45Destination
    Write-Host "SHA256：" $SW45Hash

}
else {

    $SW45Hash = ""

    Write-Host "SW45_MASTER_IMPORT = SKIP" -ForegroundColor Yellow
    Write-Host "没有找到现有苏婉晴45图片；资料库仍继续建立。"
}


# ============================================================
# 3. Canon
# ============================================================

$CanonPath = "$ProjectRoot\$ProjectName\canon\canon_v1.json"

$Canon = [ordered]@{

    schema_version = 1

    project_id = $ProjectId

    title = $ProjectName

    updated_at = (Get-Date).ToString("s")

    timeline = [ordered]@{

        "2006" = [ordered]@{
            "苏婉晴" = 25
            "陈远舟" = 27
        }

        "2026" = [ordered]@{
            "苏婉晴" = 45
            "陈远舟" = 47
            "顾川"   = 48
        }

        "2046" = [ordered]@{
            "陈念" = 40
        }
    }

    identity_rules = @(
        "25岁苏婉晴与45岁苏婉晴为同一人物，相差20年。",
        "Face DNA保持一致，年龄变化主要体现在软组织和皮肤纹理。",
        "女儿固定名称为陈念。",
        "不得把苏婉晴与陈念生成成母女同脸、双胞胎或融合脸。"
    )

    time_space_rules = @(
        "普通人物不得跨年代直接互相看见。",
        "普通人物不得跨年代直接听见对方。",
        "跨年代交流必须遵循已经冻结的通信规则。",
        "2006使用有线座机。",
        "2026使用现代智能手机。",
        "不得静默改变时空规则。"
    )

    e02_locked_rules = @(
        "2006工作室磨砂玻璃门从开场到陈远舟离开始终关闭。",
        "25岁苏婉晴LOOK：高盘发、米白/暖象牙白衬衫、蓝灰或牛仔感马甲。",
        "不得把25岁苏婉晴生成成45岁燕麦灰风衣体系。",
        "E02结束钩子固定：不对少了一张。随后黑场。"
    )

    e02_dialogue_lock = [ordered]@{

        S005 = @(
            "陈远舟：原稿给我，我替你送过去。",
            "苏婉晴：送去哪儿？",
            "陈远舟：项目评审。",
            "苏婉晴：那我自己送。"
        )

        S006 = @(
            "陈远舟：晚晴，别任性。",
            "苏婉晴：这是我的设计。",
            "苏婉晴：署谁的名字，我自己决定。"
        )
    }
}

$Canon |
ConvertTo-Json -Depth 30 |
Set-Content `
    -LiteralPath $CanonPath `
    -Encoding UTF8

Write-Host ""
Write-Host "CANON_GATE = PASS" -ForegroundColor Green
Write-Host $CanonPath


# ============================================================
# 4. Asset Registry
# ============================================================

$AssetRegistryPath = "$ConfigRoot\asset_registry.json"

$InitialAssets = @()

if ($SW45Imported) {

    $InitialAssets += [pscustomobject]@{

        id = "char.sw45.master"

        type = "character"

        character = "苏婉晴"

        age = 45

        path = $SW45Destination

        sha256 = $SW45Hash

        status = "active"

        role = "master_reference"

        created_at = (Get-Date).ToString("s")
    }
}

$Registry = [ordered]@{

    schema_version = 1

    root = $AssetRoot

    updated_at = (Get-Date).ToString("s")

    categories = [ordered]@{

        character = "$AssetRoot\characters"

        scene = "$AssetRoot\scenes"

        prop = "$AssetRoot\props"

        voice = "$AssetRoot\audio\voices"

        dialogue = "$AssetRoot\audio\dialogue"

        sfx = "$AssetRoot\audio\sfx"

        ambience = "$AssetRoot\audio\ambience"

        video_reference = "$AssetRoot\video_reference"
    }

    assets = $InitialAssets
}

$Registry |
ConvertTo-Json -Depth 30 |
Set-Content `
    -LiteralPath $AssetRegistryPath `
    -Encoding UTF8

Write-Host ""
Write-Host "ASSET_REGISTRY_GATE = PASS" -ForegroundColor Green
Write-Host $AssetRegistryPath


# ============================================================
# 5. Worker Registry
# ============================================================

$WorkerRegistryPath = "$ConfigRoot\worker_registry.json"

$WorkerRegistry = [ordered]@{

    schema_version = 1

    workers = @(

        [ordered]@{

            id = "h3-f"

            display_name = "MiniMax H3 本地 Worker"

            endpoint = "http://127.0.0.1:8189"

            runtime_root = "F:\一人公司\comfyui-production\staging\comfyui-v0.34.0\ComfyUI-0.34.0"

            model_root = "G:\ComfyUI\models"

            input_root = "$WorkerRoot\h3-f\input"

            output_root = "$WorkerRoot\h3-f\output"

            status = "candidate"

            capabilities = [ordered]@{

                image_reference = $true

                multi_image_storage = $true

                reference_to_video = $true

                motion_context_nodes = $true

                video_reference_storage = $true

                audio_reference_storage = $true

                audio_reference_workflow_connected = $false

                video_reference_workflow_connected = $false

                production_baseline = $false
            }
        }
    )
}

$WorkerRegistry |
ConvertTo-Json -Depth 30 |
Set-Content `
    -LiteralPath $WorkerRegistryPath `
    -Encoding UTF8

Write-Host ""
Write-Host "WORKER_REGISTRY_GATE = PASS" -ForegroundColor Green


# ============================================================
# 6. Capability Status
#
# 明确区分：
# 已经存储可用
# 与
# 已经接入生成Workflow
# ============================================================

$CapabilityPath = "$ConfigRoot\capability_status.json"

$Capability = [ordered]@{

    schema_version = 1

    updated_at = (Get-Date).ToString("s")

    capabilities = [ordered]@{

        single_image_reference = [ordered]@{
            storage = "ready"
            workflow = "connected"
        }

        multi_image_reference = [ordered]@{
            storage = "ready"
            workflow = "pending_binding"
        }

        video_reference = [ordered]@{
            storage = "ready"
            workflow = "pending_motion_context_binding"
        }

        voice_reference = [ordered]@{
            storage = "ready"
            workflow = "pending_voice_pipeline"
        }

        dialogue_audio = [ordered]@{
            storage = "ready"
            workflow = "pending_audio_mux"
        }

        asset_library = [ordered]@{
            storage = "ready"
            registry = "ready"
            graphical_ui = "pending"
        }
    }
}

$Capability |
ConvertTo-Json -Depth 30 |
Set-Content `
    -LiteralPath $CapabilityPath `
    -Encoding UTF8


# ============================================================
# 7. Shot Manifest Template
# ============================================================

$ShotTemplatePath = "$ProjectRoot\$ProjectName\episodes\E02\shots\E02_SHOT_TEMPLATE.json"

$ShotTemplate = [ordered]@{

    schema_version = 1

    project_id = $ProjectId

    episode = "E02"

    shot_id = "E02_SXXX"

    model = [ordered]@{
        worker = "h3-f"
        family = "MiniMax H3"
        mode = "reference_to_video"
    }

    generation = [ordered]@{
        aspect_ratio = "9:16"
        megapixels = 0.4
        duration_seconds = 5
        fps = 24
        steps = 20
        turbo = $false
    }

    bindings = [ordered]@{

        characters = @()

        scene = ""

        props = @()

        image_refs = @()

        video_refs = @()

        audio_refs = @()
    }

    continuity = [ordered]@{

        inherit_previous_shot = $false

        previous_shot_id = ""

        door_state = ""

        phone_state = ""

        prop_state = ""
    }

    prompt = ""
}

$ShotTemplate |
ConvertTo-Json -Depth 30 |
Set-Content `
    -LiteralPath $ShotTemplatePath `
    -Encoding UTF8

Write-Host ""
Write-Host "SHOT_TEMPLATE_GATE = PASS" -ForegroundColor Green


# ============================================================
# 8. 创建素材导入脚本
# ============================================================

$ImporterPath = "$ScriptRoot\导入_ComfyStudio_素材.ps1"

@"
param(

    [Parameter(Mandatory=`$true)]
    [string]`$SourcePath,

    [Parameter(Mandatory=`$true)]
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
    [string]`$AssetType,

    [Parameter(Mandatory=`$true)]
    [string]`$TargetSubfolder,

    [Parameter(Mandatory=`$true)]
    [string]`$TargetName,

    [Parameter(Mandatory=`$true)]
    [string]`$AssetId,

    [string]`$ProjectId = "",

    [string]`$Episode = "",

    [switch]`$Replace
)

`$ErrorActionPreference = "Stop"

`$AssetRoot = "G:\ComfyStudioData\assets"

`$RegistryPath = "F:\一人公司\comfyui-production\config\comfystudio\asset_registry.json"


if (-not (Test-Path -LiteralPath `$SourcePath)) {

    throw "源素材不存在：`$SourcePath"
}


`$TypeMap = @{

    character = "characters"

    scene = "scenes"

    prop = "props"

    voice = "audio\voices"

    dialogue = "audio\dialogue"

    sfx = "audio\sfx"

    ambience = "audio\ambience"

    video_reference = "video_reference"
}


`$RelativeRoot = `$TypeMap[`$AssetType]

`$DestinationRoot = Join-Path `
    `$AssetRoot `
    `$RelativeRoot

if (`$TargetSubfolder) {

    `$DestinationDir = Join-Path `
        `$DestinationRoot `
        `$TargetSubfolder
}
else {

    `$DestinationDir = `$DestinationRoot
}


New-Item `
    -ItemType Directory `
    -Force `
    -Path `$DestinationDir |
Out-Null


`$Destination = Join-Path `
    `$DestinationDir `
    `$TargetName


if (
    (Test-Path -LiteralPath `$Destination) -and
    (-not `$Replace)
) {

    throw "目标文件已经存在。需要覆盖时加入 -Replace：`$Destination"
}


Copy-Item `
    -LiteralPath `$SourcePath `
    -Destination `$Destination `
    -Force


`$Hash = (
    Get-FileHash `
        -LiteralPath `$Destination `
        -Algorithm SHA256
).Hash


`$Registry = Get-Content `
    -LiteralPath `$RegistryPath `
    -Raw |
ConvertFrom-Json


`$Assets = @(`$Registry.assets)

`$Existing = @(
    `$Assets |
    Where-Object {
        `$_.id -eq `$AssetId
    }
)


if (
    (`$Existing.Count -gt 0) -and
    (-not `$Replace)
) {

    throw "AssetId已经存在：`$AssetId。需要替换时加入 -Replace。"
}


if (`$Existing.Count -gt 0) {

    `$Assets = @(
        `$Assets |
        Where-Object {
            `$_.id -ne `$AssetId
        }
    )
}


`$Entry = [pscustomobject]@{

    id = `$AssetId

    type = `$AssetType

    path = `$Destination

    sha256 = `$Hash

    project_id = `$ProjectId

    episode = `$Episode

    status = "active"

    created_at = (Get-Date).ToString("s")
}


`$Registry.assets = @(
    `$Assets + `$Entry
)

`$Registry.updated_at = (
    Get-Date
).ToString("s")


`$Registry |
ConvertTo-Json -Depth 30 |
Set-Content `
    -LiteralPath `$RegistryPath `
    -Encoding UTF8


Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "ASSET_IMPORT_GATE = PASS" -ForegroundColor Green
Write-Host "============================================"

Write-Host "Asset ID：" `$AssetId
Write-Host "类型：" `$AssetType
Write-Host "目标：" `$Destination
Write-Host "SHA256：" `$Hash
"@ |
Set-Content `
    -LiteralPath $ImporterPath `
    -Encoding UTF8


# ============================================================
# 9. 创建 Shot Staging 脚本
#
# 功能：
# 根据镜头 Manifest，把注册资产复制到 H3 Worker input
#
# 注意：
# 这里只负责准备素材；
# 不代表当前H3 Workflow已经自动消费音频/视频输入。
# ============================================================

$StagerPath = "$ScriptRoot\准备_ComfyStudio_镜头素材.ps1"

@"
param(

    [Parameter(Mandatory=`$true)]
    [string]`$ManifestPath
)

`$ErrorActionPreference = "Stop"

`$RegistryPath = "F:\一人公司\comfyui-production\config\comfystudio\asset_registry.json"

`$WorkerInput = "G:\ComfyStudioData\workers\h3-f\input"

`$ReportRoot = "F:\一人公司\comfyui-production\reports\comfystudio"


if (-not (Test-Path -LiteralPath `$ManifestPath)) {

    throw "镜头Manifest不存在：`$ManifestPath"
}


`$Manifest = Get-Content `
    -LiteralPath `$ManifestPath `
    -Raw |
ConvertFrom-Json


`$Registry = Get-Content `
    -LiteralPath `$RegistryPath `
    -Raw |
ConvertFrom-Json


`$Assets = @(`$Registry.assets)

New-Item `
    -ItemType Directory `
    -Force `
    -Path `$WorkerInput |
Out-Null

New-Item `
    -ItemType Directory `
    -Force `
    -Path `$ReportRoot |
Out-Null


`$Results = @()


function Stage-Asset {

    param(
        [string]`$AssetId,
        [string]`$Prefix,
        [int]`$Index
    )


    `$Match = @(
        `$Assets |
        Where-Object {
            `$_.id -eq `$AssetId
        }
    )


    if (`$Match.Count -eq 0) {

        throw "找不到 AssetId：`$AssetId"
    }


    `$Asset = `$Match[0]


    if (-not (Test-Path -LiteralPath `$Asset.path)) {

        throw "注册资产文件不存在：`$(`$Asset.path)"
    }


    `$Ext = [System.IO.Path]::GetExtension(
        `$Asset.path
    )


    `$SafeId = `$AssetId -replace '[^a-zA-Z0-9._-]', '_'

    `$TargetName = (
        "{0}{1:D2}_{2}{3}" -f `
        `$Prefix,
        `$Index,
        `$SafeId,
        `$Ext
    )


    `$Target = Join-Path `
        `$WorkerInput `
        `$TargetName


    Copy-Item `
        -LiteralPath `$Asset.path `
        -Destination `$Target `
        -Force


    `$Hash = (
        Get-FileHash `
            -LiteralPath `$Target `
            -Algorithm SHA256
    ).Hash


    `$script:Results += [pscustomobject]@{

        asset_id = `$AssetId

        target = `$Target

        sha256 = `$Hash
    }
}


`$ImageRefs = @(
    `$Manifest.bindings.image_refs
)

`$VideoRefs = @(
    `$Manifest.bindings.video_refs
)

`$AudioRefs = @(
    `$Manifest.bindings.audio_refs
)


for (`$i = 0; `$i -lt `$ImageRefs.Count; `$i++) {

    Stage-Asset `
        -AssetId `$ImageRefs[`$i] `
        -Prefix "IMG" `
        -Index (`$i + 1)
}


for (`$i = 0; `$i -lt `$VideoRefs.Count; `$i++) {

    Stage-Asset `
        -AssetId `$VideoRefs[`$i] `
        -Prefix "VID" `
        -Index (`$i + 1)
}


for (`$i = 0; `$i -lt `$AudioRefs.Count; `$i++) {

    Stage-Asset `
        -AssetId `$AudioRefs[`$i] `
        -Prefix "AUD" `
        -Index (`$i + 1)
}


`$ReportPath = Join-Path `
    `$ReportRoot `
    ("stage-" + `$Manifest.shot_id + "-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".json")


`$Report = [ordered]@{

    shot_id = `$Manifest.shot_id

    manifest = `$ManifestPath

    worker_input = `$WorkerInput

    staged_at = (Get-Date).ToString("s")

    assets = `$Results
}


`$Report |
ConvertTo-Json -Depth 30 |
Set-Content `
    -LiteralPath `$ReportPath `
    -Encoding UTF8


Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "SHOT_STAGE_GATE = PASS" -ForegroundColor Green
Write-Host "============================================"

Write-Host "镜头：" `$Manifest.shot_id
Write-Host "已准备素材：" `$Results.Count
Write-Host "报告：" `$ReportPath

`$Results |
Format-Table -AutoSize
"@ |
Set-Content `
    -LiteralPath $StagerPath `
    -Encoding UTF8


# ============================================================
# 10. README
# ============================================================

$ReadmePath = "$DataRoot\README_ComfyStudio_资料库.txt"

@"
ComfyStudio V1 资料库
====================

G盘：
$DataRoot

assets\characters
    角色图片与人物参考

assets\scenes
    场景母版

assets\props
    道具图片

assets\audio\voices
    固定角色声音参考

assets\audio\dialogue
    每集具体台词音频

assets\audio\sfx
    音效

assets\audio\ambience
    环境声

assets\video_reference
    上一镜视频 / 动作参考 / Motion Context来源

projects
    项目 Canon / 每集 / 每镜 Manifest

workers\h3-f\input
    Studio送给 H3 的 staging 输入

workers\h3-f\output
    H3输出


F盘：
$StudioRoot

config\comfystudio\asset_registry.json
    全局资产索引

config\comfystudio\worker_registry.json
    Worker索引

config\comfystudio\capability_status.json
    当前已经接通 / 尚未接通的能力

scripts\导入_ComfyStudio_素材.ps1
    注册图片 / 视频 / 音频资产

scripts\准备_ComfyStudio_镜头素材.ps1
    根据镜头Manifest把素材Stage给H3


当前能力：

单图参考：
    已接通

多图参考：
    资料库已准备
    Workflow绑定下一阶段完成

视频参考：
    资料库存储已准备
    H3 Motion Context Workflow绑定下一阶段完成

角色声音参考：
    资料库存储已准备
    Voice/TTS Pipeline下一阶段完成

台词音频：
    资料库存储已准备
    音轨混合下一阶段完成
"@ |
Set-Content `
    -LiteralPath $ReadmePath `
    -Encoding UTF8


# ============================================================
# 11. 最终验证
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "FINAL VERIFY" -ForegroundColor Cyan
Write-Host "============================================================"


$Checks = @{

    AssetCharacters =
        Test-Path "$AssetRoot\characters"

    AssetScenes =
        Test-Path "$AssetRoot\scenes"

    AssetProps =
        Test-Path "$AssetRoot\props"

    AssetVoices =
        Test-Path "$AssetRoot\audio\voices"

    AssetVideo =
        Test-Path "$AssetRoot\video_reference"

    ProjectCanon =
        Test-Path $CanonPath

    AssetRegistry =
        Test-Path $AssetRegistryPath

    WorkerRegistry =
        Test-Path $WorkerRegistryPath

    CapabilityStatus =
        Test-Path $CapabilityPath

    ShotTemplate =
        Test-Path $ShotTemplatePath

    Importer =
        Test-Path $ImporterPath

    Stager =
        Test-Path $StagerPath
}


$Checks.GetEnumerator() |
Sort-Object Name |
Format-Table `
    Name,
    Value `
    -AutoSize


$Failed = @(
    $Checks.GetEnumerator() |
    Where-Object {
        -not $_.Value
    }
)


if ($Failed.Count -gt 0) {

    Write-Host ""
    Write-Host "COMFYSTUDIO_LIBRARY_GATE = FAIL" -ForegroundColor Red

    throw "资料库初始化不完整。"
}


Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "COMFYSTUDIO_LIBRARY_GATE = PASS" -ForegroundColor Green
Write-Host "============================================================"

Write-Host ""
Write-Host "资产根目录：" -ForegroundColor Green
Write-Host $AssetRoot

Write-Host ""
Write-Host "项目根目录：" -ForegroundColor Green
Write-Host "$ProjectRoot\$ProjectName"

Write-Host ""
Write-Host "Canon：" -ForegroundColor Green
Write-Host $CanonPath

Write-Host ""
Write-Host "资产索引：" -ForegroundColor Green
Write-Host $AssetRegistryPath

Write-Host ""
Write-Host "导入素材：" -ForegroundColor Green
Write-Host $ImporterPath

Write-Host ""
Write-Host "镜头Staging：" -ForegroundColor Green
Write-Host $StagerPath
