[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Video,
    [Parameter(Mandatory)]
    [string]$Subtitle,
    [string]$Output,
    [ValidateSet('Primary', 'PrimarySemibold')]
    [string]$Style = 'Primary',
    [string]$FontName = '',
    [ValidateSet('h264_nvenc', 'libx264')]
    [string]$VideoCodec = 'h264_nvenc'
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$videoPath = (Resolve-Path -LiteralPath $Video -ErrorAction Stop).Path
$subtitlePath = (Resolve-Path -LiteralPath $Subtitle -ErrorAction Stop).Path
if ([IO.Path]::GetExtension($videoPath).ToLowerInvariant() -notin @('.mp4', '.mov', '.mkv', '.webm')) {
    throw 'Video must be an MP4, MOV, MKV, or WebM file.'
}
if ([IO.Path]::GetExtension($subtitlePath).ToLowerInvariant() -ne '.ass') {
    throw 'Subtitle must be an ASS file.'
}

$ffmpegPath = ''
$ffmpegCommand = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpegCommand -and (Test-Path -LiteralPath $ffmpegCommand.Source)) {
    try {
        & $ffmpegCommand.Source -version *> $null
        if ($LASTEXITCODE -eq 0) { $ffmpegPath = $ffmpegCommand.Source }
    } catch { }
}
if (-not $ffmpegPath) {
    $bundledFfmpeg = 'G:\ComfyUI\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
    if (Test-Path -LiteralPath $bundledFfmpeg) { $ffmpegPath = $bundledFfmpeg }
}
if (-not $ffmpegPath) {
    throw 'FFmpeg is not executable. Install FFmpeg or retain the ComfyUI imageio-ffmpeg runtime.'
}
if (-not $Output) {
    $directory = Split-Path -Parent $videoPath
    $Output = Join-Path $directory (([IO.Path]::GetFileNameWithoutExtension($videoPath)) + '_subtitled.mp4')
}
$outputPath = [IO.Path]::GetFullPath($Output)
if ([StringComparer]::OrdinalIgnoreCase.Equals($outputPath, $videoPath)) {
    throw 'Output must not overwrite the source video.'
}
$outputDirectory = Split-Path -Parent $outputPath
$null = New-Item -ItemType Directory -Force -Path $outputDirectory

$pythonPath = ''
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCommand -and (Test-Path -LiteralPath $pythonCommand.Source)) {
    $pythonPath = $pythonCommand.Source
}
if (-not $pythonPath) {
    $bundledPython = 'G:\ComfyUI\venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $bundledPython) { $pythonPath = $bundledPython }
}
if (-not $pythonPath) {
    throw 'Python is not executable; the SUBTITLE_LOCK_V1 preflight cannot run.'
}
$validatorPath = Join-Path $ProjectRoot 'scripts\validate_subtitles.py'
if (-not (Test-Path -LiteralPath $validatorPath -PathType Leaf)) {
    throw "Subtitle validator was not found: $validatorPath"
}
& $pythonPath $validatorPath $subtitlePath
if ($LASTEXITCODE -ne 0) {
    throw 'SUBTITLE_LOCK_V1 preflight failed; no video was written.'
}

if ($FontName -match '[,\r\n]') {
    throw 'FontName cannot contain commas or line breaks.'
}
$primaryFont = 'Source Han Sans CN Medium'
$semiboldFont = 'Source Han Sans CN SemiBold'
if ($FontName) {
    $primaryFont = $FontName
    $semiboldFont = $FontName
} else {
    $fontDirectories = @('C:\Windows\Fonts')
    if ($env:LOCALAPPDATA) {
        $fontDirectories += (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts')
    }
    $sourceHan = $null
    foreach ($fontDirectory in $fontDirectories) {
        $sourceHan = Get-ChildItem -LiteralPath $fontDirectory -ErrorAction SilentlyContinue |
            Where-Object Name -match 'SourceHan|Source Han|NotoSansCJK|思源' |
            Select-Object -First 1
        if ($sourceHan) { break }
    }
    if (-not $sourceHan) {
        $primaryFont = 'Microsoft YaHei'
        $semiboldFont = 'Microsoft YaHei'
    }
}

$temporaryAss = Join-Path ([IO.Path]::GetTempPath()) ("subtitle-lock-" + [guid]::NewGuid().ToString('N') + '.ass')
$temporaryOutput = Join-Path $outputDirectory ('.' + [IO.Path]::GetFileNameWithoutExtension($outputPath) + '.' + [guid]::NewGuid().ToString('N') + '.partial.mp4')
try {
    $content = Get-Content -LiteralPath $subtitlePath -Raw -Encoding utf8
    if ($Style -eq 'PrimarySemibold') {
        $content = $content -replace '(?m)^(Dialogue:\s*\d+,[^,\r\n]*,[^,\r\n]*,)Primary,', '$1PrimarySemibold,'
    }
    $content = $content.Replace('Source Han Sans CN Medium', $primaryFont)
    $content = $content.Replace('Source Han Sans CN SemiBold', $semiboldFont)
    [IO.File]::WriteAllText($temporaryAss, $content, [Text.UTF8Encoding]::new($false))

    $assFilterPath = ($temporaryAss -replace '\\', '/') -replace ':', '\:'
    $filter = "ass='$assFilterPath'"
    $ffmpegArgs = @('-hide_banner', '-y', '-i', $videoPath, '-vf', $filter, '-c:v', $VideoCodec)
    if ($VideoCodec -eq 'h264_nvenc') {
        $ffmpegArgs += @('-preset', 'p5', '-rc', 'vbr', '-cq', '20', '-b:v', '0')
    } else {
        $ffmpegArgs += @('-preset', 'medium', '-crf', '18')
    }
    $ffmpegArgs += @('-c:a', 'copy', $temporaryOutput)
    & $ffmpegPath @ffmpegArgs
    if ($LASTEXITCODE -ne 0) {
        if ($VideoCodec -eq 'h264_nvenc') {
            throw 'NVENC subtitle export failed. Re-run with -VideoCodec libx264 for a CPU fallback.'
        }
        throw "FFmpeg subtitle export failed with exit code $LASTEXITCODE."
    }
    if (-not (Test-Path -LiteralPath $temporaryOutput -PathType Leaf) -or (Get-Item -LiteralPath $temporaryOutput).Length -le 0) {
        throw 'FFmpeg reported success but did not create a non-empty output.'
    }
    Move-Item -LiteralPath $temporaryOutput -Destination $outputPath -Force
} finally {
    Remove-Item -LiteralPath $temporaryAss -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $temporaryOutput -Force -ErrorAction SilentlyContinue
}

Write-Output "Created subtitled video: $outputPath"
