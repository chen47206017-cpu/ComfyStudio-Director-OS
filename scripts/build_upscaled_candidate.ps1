[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Video,
    [Parameter(Mandatory)]
    [string]$Subtitle,
    [Parameter(Mandatory)]
    [string]$Output,
    [ValidateSet('h264_nvenc', 'libx264')]
    [string]$VideoCodec = 'h264_nvenc',
    [string]$FfmpegPath = '',
    [string]$FfprobePath = '',
    [string]$PythonPath = '',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$TargetWidth = 1080
$TargetHeight = 1920
$TargetFps = 24
$MinDurationSeconds = 4.8
$MaxDurationSeconds = 5.2
$ProjectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path

function Get-FullPath([string]$RawPath) {
    if ([string]::IsNullOrWhiteSpace($RawPath)) {
        throw 'Path must not be empty.'
    }
    if ([IO.Path]::IsPathRooted($RawPath)) {
        return [IO.Path]::GetFullPath($RawPath)
    }
    return [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $RawPath))
}

function Test-WithinProject([string]$Path) {
    $root = $ProjectRoot.TrimEnd('\', '/')
    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    return $full.Equals($root, [StringComparison]::OrdinalIgnoreCase) -or
        $full.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)
}

function Resolve-ProjectFile([string]$RawPath, [string]$Label) {
    $candidate = Get-FullPath $RawPath
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "$Label was not found: $candidate"
    }
    $resolved = (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path
    if (-not (Test-WithinProject $resolved)) {
        throw "$Label must be inside the project directory: $resolved"
    }
    return $resolved
}

function Resolve-ProjectDestination([string]$RawPath) {
    $candidate = Get-FullPath $RawPath
    if (-not (Test-WithinProject $candidate)) {
        throw "Output must be inside the project directory: $candidate"
    }
    $parent = Split-Path -Parent $candidate
    if (-not $parent) {
        throw "Output must have a parent directory: $candidate"
    }
    $null = New-Item -ItemType Directory -Force -Path $parent
    $resolvedParent = (Resolve-Path -LiteralPath $parent -ErrorAction Stop).Path
    if (-not (Test-WithinProject $resolvedParent)) {
        throw "Output parent must be inside the project directory: $resolvedParent"
    }
    return Join-Path $resolvedParent (Split-Path -Leaf $candidate)
}

function Find-Executable([string]$Requested, [string]$Name, [string]$EnvironmentName, [string]$VersionArgument = '-version') {
    $candidate = $Requested
    if (-not $candidate) { $candidate = [Environment]::GetEnvironmentVariable($EnvironmentName) }
    if (-not $candidate) {
        $command = Get-Command $Name -ErrorAction SilentlyContinue
        if ($command) { $candidate = $command.Source }
    }
    if (-not $candidate) {
        throw "$Name is not available. Pass -$($Name.Substring(0,1).ToUpperInvariant() + $Name.Substring(1))Path or set $EnvironmentName."
    }
    $resolved = Get-FullPath $candidate
    if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) {
        throw "$Name executable was not found: $resolved"
    }
    try {
        & $resolved $VersionArgument *> $null
    } catch {
        throw "$name executable could not be started: $resolved"
    }
    if ($LASTEXITCODE -ne 0) {
        throw "$name executable could not be started: $resolved"
    }
    return $resolved
}

function Get-Sha256Record([string]$Path) {
    $item = Get-Item -LiteralPath $Path -ErrorAction Stop
    $hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    return [ordered]@{
        path = $item.FullName
        size_bytes = [int64]$item.Length
        sha256 = $hash
    }
}

function Get-ProjectRelative([string]$Path) {
    $root = $ProjectRoot.TrimEnd('\', '/')
    $full = [IO.Path]::GetFullPath($Path)
    if ($full.Equals($root, [StringComparison]::OrdinalIgnoreCase)) { return '.' }
    return $full.Substring($root.Length).TrimStart('\', '/')
}

function Invoke-Probe([string]$Path, [string]$ProbeExecutable) {
    $arguments = @(
        '-v', 'error',
        '-show_entries', 'format=duration,format_name:stream=index,codec_type,codec_name,width,height,pix_fmt,avg_frame_rate,r_frame_rate,nb_frames,bit_rate',
        '-of', 'json',
        $Path
    )
    $raw = & $ProbeExecutable @arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "FFprobe failed for ${Path}: $($raw -join "`n")"
    }
    try {
        return (($raw -join "`n") | ConvertFrom-Json)
    } catch {
        throw "FFprobe returned invalid JSON for $Path"
    }
}

function Get-VideoStream($Probe) {
    return @($Probe.streams | Where-Object { $_.codec_type -eq 'video' }) | Select-Object -First 1
}

function Get-AudioStream($Probe) {
    return @($Probe.streams | Where-Object { $_.codec_type -eq 'audio' }) | Select-Object -First 1
}

function Convert-RationalToDouble([string]$Value) {
    if (-not $Value) { return $null }
    $parts = $Value -split '/'
    if ($parts.Count -eq 2 -and [double]$parts[1] -ne 0) {
        return [double]$parts[0] / [double]$parts[1]
    }
    try { return [double]$Value } catch { return $null }
}

function Get-SubtitleFont([string]$Preferred) {
    if ($Preferred) { return $Preferred }
    $directories = @('C:\Windows\Fonts')
    if ($env:LOCALAPPDATA) {
        $directories += (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts')
    }
    foreach ($directory in $directories) {
        $match = Get-ChildItem -LiteralPath $directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match 'SourceHan|Source Han|思源' } |
            Select-Object -First 1
        if ($match) { return 'Source Han Sans CN Medium' }
    }
    return 'Microsoft YaHei'
}

$inputPath = Resolve-ProjectFile $Video 'Video'
$subtitlePath = Resolve-ProjectFile $Subtitle 'Subtitle'
$outputPath = Resolve-ProjectDestination $Output
if ([IO.Path]::GetExtension($inputPath).ToLowerInvariant() -notin @('.mp4', '.mov', '.mkv', '.webm')) {
    throw 'Video must be an MP4, MOV, MKV, or WebM file.'
}
if ([IO.Path]::GetExtension($subtitlePath).ToLowerInvariant() -ne '.ass') {
    throw 'Subtitle must be an ASS file.'
}
if ([IO.Path]::GetExtension($outputPath).ToLowerInvariant() -ne '.mp4') {
    throw 'Output must be an MP4 file.'
}

$metadataPath = Join-Path (Split-Path -Parent $outputPath) (([IO.Path]::GetFileNameWithoutExtension($outputPath)) + '.candidate.json')
$qaDirectory = Join-Path (Split-Path -Parent $outputPath) (([IO.Path]::GetFileNameWithoutExtension($outputPath)) + '.qa_frames')
if (-not $Force -and ((Test-Path -LiteralPath $outputPath -PathType Leaf) -or (Test-Path -LiteralPath $metadataPath -PathType Leaf) -or (Test-Path -LiteralPath $qaDirectory))) {
    throw "Output or sidecar already exists. Choose a new path or pass -Force: $outputPath"
}

$ffmpegPath = Find-Executable $FfmpegPath 'ffmpeg' 'FFMPEG_PATH'
if (-not $FfprobePath) {
    $siblingProbe = Join-Path (Split-Path -Parent $ffmpegPath) 'ffprobe.exe'
    if (Test-Path -LiteralPath $siblingProbe -PathType Leaf) { $FfprobePath = $siblingProbe }
}
$ffprobePath = Find-Executable $FfprobePath 'ffprobe' 'FFPROBE_PATH'
$pythonPath = Find-Executable $PythonPath 'python' 'PYTHON_PATH' '--version'
$validatorPath = Join-Path $ProjectRoot 'scripts\validate_subtitles.py'
if (-not (Test-Path -LiteralPath $validatorPath -PathType Leaf)) {
    throw "Subtitle validator was not found: $validatorPath"
}

$sourceProbe = Invoke-Probe $inputPath $ffprobePath
$sourceVideo = Get-VideoStream $sourceProbe
if (-not $sourceVideo) { throw 'Input video has no video stream.' }

$validatorRaw = & $pythonPath $validatorPath $subtitlePath '--json' '--video-width' $TargetWidth '--video-height' $TargetHeight 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "SUBTITLE_LOCK_V1 preflight failed: $($validatorRaw -join "`n")"
}
try { $subtitlePreflight = ($validatorRaw -join "`n") | ConvertFrom-Json } catch { throw 'Subtitle validator returned invalid JSON.' }
if (-not $subtitlePreflight.ok) { throw 'SUBTITLE_LOCK_V1 preflight did not pass.' }

$staging = Join-Path (Split-Path -Parent $outputPath) ('.' + [IO.Path]::GetFileNameWithoutExtension($outputPath) + '.' + [guid]::NewGuid().ToString('N') + '.staging')
$stagedOutput = Join-Path $staging 'candidate.partial.mp4'
$stagedAss = Join-Path $staging 'subtitle.ass'
$stagedQa = Join-Path $staging 'qa_frames'
$stagedMetadata = Join-Path $staging 'candidate.json'
$ffmpegLog = Join-Path $staging 'ffmpeg.log'
$temporaryAss = Join-Path ([IO.Path]::GetTempPath()) ('subtitle-lock-candidate-' + [guid]::NewGuid().ToString('N') + '.ass')
New-Item -ItemType Directory -Force -Path $staging, $stagedQa | Out-Null
try {
    $subtitleText = Get-Content -LiteralPath $subtitlePath -Raw -Encoding utf8
    $subtitleFont = Get-SubtitleFont ''
    if ($subtitleFont -ne 'Source Han Sans CN Medium') {
        $subtitleText = $subtitleText.Replace('Source Han Sans CN Medium', $subtitleFont)
        $subtitleText = $subtitleText.Replace('Source Han Sans CN SemiBold', $subtitleFont)
    }
    [IO.File]::WriteAllText($temporaryAss, $subtitleText, [Text.UTF8Encoding]::new($false))
    Copy-Item -LiteralPath $subtitlePath -Destination $stagedAss -Force

    $assFilterPath = ($temporaryAss -replace '\\', '/') -replace ':', '\:'
    $filter = "scale=${TargetWidth}:${TargetHeight}:flags=lanczos,fps=${TargetFps},ass='$assFilterPath'"
    $ffmpegArgs = @('-hide_banner', '-loglevel', 'error', '-y', '-i', $inputPath, '-vf', $filter, '-map', '0:v:0', '-map', '0:a?', '-c:v', $VideoCodec)
    if ($VideoCodec -eq 'h264_nvenc') {
        $ffmpegArgs += @('-preset', 'p5', '-rc', 'vbr', '-cq', '20', '-b:v', '0')
    } else {
        $ffmpegArgs += @('-preset', 'medium', '-crf', '18')
    }
    $ffmpegArgs += @('-pix_fmt', 'yuv420p', '-r', $TargetFps)
    if (Get-AudioStream $sourceProbe) {
        $ffmpegArgs += @('-c:a', 'aac', '-b:a', '192k')
    }
    $ffmpegArgs += @('-movflags', '+faststart', $stagedOutput)
    & $ffmpegPath @ffmpegArgs *> $ffmpegLog
    if ($LASTEXITCODE -ne 0) {
        $details = if (Test-Path -LiteralPath $ffmpegLog) { (Get-Content -LiteralPath $ffmpegLog -Tail 40) -join "`n" } else { '' }
        throw "FFmpeg candidate export failed with exit code $LASTEXITCODE. $details"
    }
    if ((-not (Test-Path -LiteralPath $stagedOutput -PathType Leaf)) -or ((Get-Item -LiteralPath $stagedOutput).Length -le 0)) {
        throw 'FFmpeg reported success but did not create a non-empty candidate.'
    }

    $outputProbe = Invoke-Probe $stagedOutput $ffprobePath
    $outputVideo = Get-VideoStream $outputProbe
    if (-not $outputVideo) { throw 'Candidate has no video stream after export.' }
    $outputFps = Convert-RationalToDouble ([string]$outputVideo.avg_frame_rate)
    $outputDuration = [double]$outputProbe.format.duration
    $outputFrames = if ($outputVideo.nb_frames) { [int]$outputVideo.nb_frames } else { $null }
    if ([int]$outputVideo.width -ne $TargetWidth -or [int]$outputVideo.height -ne $TargetHeight) {
        throw "Candidate dimensions are $($outputVideo.width)x$($outputVideo.height), expected ${TargetWidth}x${TargetHeight}."
    }
    if ($null -eq $outputFps -or [math]::Abs($outputFps - $TargetFps) -gt 0.01) {
        throw "Candidate frame rate is $($outputVideo.avg_frame_rate), expected ${TargetFps} fps."
    }
    if ($outputDuration -lt $MinDurationSeconds -or $outputDuration -gt $MaxDurationSeconds) {
        throw "Candidate duration is $outputDuration seconds, expected approximately 5 seconds."
    }

    $frameSpecs = @(
        @{ Name = 'frame_first.jpg'; Seek = '0' },
        @{ Name = 'frame_mid.jpg'; Seek = '2.50' },
        @{ Name = 'frame_last.jpg'; Seek = ''; EndSeek = '-0.05' }
    )
    $frameRecords = @()
    foreach ($spec in $frameSpecs) {
        $framePath = Join-Path $stagedQa $spec.Name
        $frameArgs = @('-hide_banner', '-loglevel', 'error', '-y')
        if ($spec.EndSeek) { $frameArgs += @('-sseof', $spec.EndSeek) } else { $frameArgs += @('-ss', $spec.Seek) }
        $frameArgs += @('-i', $stagedOutput, '-frames:v', '1', '-q:v', '2', $framePath)
        & $ffmpegPath @frameArgs *> $ffmpegLog
        if (($LASTEXITCODE -ne 0) -or (-not (Test-Path -LiteralPath $framePath -PathType Leaf))) {
            throw "Could not extract QA frame $($spec.Name)."
        }
        $frameRecords += [ordered]@{
            name = $spec.Name
            # Record the published QA path, not the disposable staging path.
            path = (Join-Path $qaDirectory $spec.Name)
            project_relative_path = Get-ProjectRelative (Join-Path $qaDirectory $spec.Name)
            size_bytes = [int64](Get-Item -LiteralPath $framePath).Length
            sha256 = (Get-Sha256Record $framePath).sha256
        }
    }

    $sourceRecord = Get-Sha256Record $inputPath
    $subtitleRecord = Get-Sha256Record $subtitlePath
    $stagedRecord = Get-Sha256Record $stagedOutput
    $metadata = [ordered]@{
        schema_version = 1
        artifact_type = 'video'
        classification = 'UPSCALED_CANDIDATE'
        delivery_status = 'REJECTED_FOR_DELIVERY'
        quality_status = 'TECHNICAL_PASS_VISUAL_QUALITY_UNACCEPTED'
        generated_at = (Get-Date).ToString('o')
        source = [ordered]@{
            path = $inputPath
            project_relative_path = Get-ProjectRelative $inputPath
            size_bytes = $sourceRecord.size_bytes
            sha256 = $sourceRecord.sha256
            probe = $sourceProbe
        }
        subtitle = [ordered]@{
            path = $subtitlePath
            project_relative_path = Get-ProjectRelative $subtitlePath
            size_bytes = $subtitleRecord.size_bytes
            sha256 = $subtitleRecord.sha256
            preflight = $subtitlePreflight
        }
        transform = [ordered]@{
            operation = 'lanczos_upscale_and_subtitle_burn'
            target_width = $TargetWidth
            target_height = $TargetHeight
            target_fps = $TargetFps
            duration_window_seconds = @($MinDurationSeconds, $MaxDurationSeconds)
            codec = $VideoCodec
            subtitle_style = 'SUBTITLE_LOCK_V1'
        }
        output = [ordered]@{
            path = $outputPath
            project_relative_path = Get-ProjectRelative $outputPath
            size_bytes = $stagedRecord.size_bytes
            sha256 = $stagedRecord.sha256
            probe = $outputProbe
            width = [int]$outputVideo.width
            height = [int]$outputVideo.height
            fps = $outputFps
            frames = $outputFrames
            duration_seconds = $outputDuration
            aspect_ratio = '9:16'
            audio_present = [bool](Get-AudioStream $outputProbe)
        }
        qa = [ordered]@{
            frames = $frameRecords
            visual_review = 'NOT_PERFORMED_BY_SCRIPT'
        }
        notes = @(
            'This file is an upscaled candidate derived from a 432x768 local Wan smoke render; it is not native 1080x1920 generation.',
            'The candidate passes container, dimensions, frame-rate, duration, subtitle-preflight, hash, and frame-extraction checks only.',
            'It remains REJECTED_FOR_DELIVERY until visual quality, identity consistency, motion, and the final production render gates pass.',
            'The source had no audio stream; audio_present is recorded from the exported file and is not synthesized here.'
        )
    }
    $metadataJson = $metadata | ConvertTo-Json -Depth 14
    [IO.File]::WriteAllText($stagedMetadata, $metadataJson, [Text.UTF8Encoding]::new($false))

    if ($Force) {
        if (Test-Path -LiteralPath $outputPath) { Remove-Item -LiteralPath $outputPath -Force }
        if (Test-Path -LiteralPath $metadataPath) { Remove-Item -LiteralPath $metadataPath -Force }
        if (Test-Path -LiteralPath $qaDirectory) { Remove-Item -LiteralPath $qaDirectory -Recurse -Force }
    }
    Move-Item -LiteralPath $stagedOutput -Destination $outputPath
    Move-Item -LiteralPath $stagedQa -Destination $qaDirectory
    Move-Item -LiteralPath $stagedMetadata -Destination $metadataPath
    Write-Output "Created UPSCALED_CANDIDATE: $outputPath"
    Write-Output "Metadata: $metadataPath"
    Write-Output "QA frames: $qaDirectory"
} finally {
    Remove-Item -LiteralPath $temporaryAss -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
}
