$ErrorActionPreference = "Stop"

$Root = "F:\一人公司\comfyui-production"

$H3Root = "$Root\staging\comfyui-v0.34.0\ComfyUI-0.34.0"
$Py = "$H3Root\.venv\Scripts\python.exe"

$InputDir  = "G:\ComfyStudioData\workers\h3-f\input"
$OutputDir = "G:\ComfyStudioData\workers\h3-f\output"
$TempDir   = "$Root\runtime\temp\h3-f"

$Preflight = "$Root\runtime\temp\h3_nommap_preflight.py"

# 第二次真实实验单独留档
$RunDir = "$Root\reports\h3\H3-R2V-SMOKE-002-NOMMAP"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $RunDir |
Out-Null

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

$StdoutLog = "$RunDir\comfy8189-$Stamp-stdout.log"
$StderrLog = "$RunDir\comfy8189-$Stamp-stderr.log"
$PidFile   = "$RunDir\comfy8189-$Stamp.pid.txt"


Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "H3 8189 NO-MMAP Runtime V3" -ForegroundColor Cyan
Write-Host "============================================"


# ============================================================
# 1. Preflight
# ============================================================

Write-Host ""
Write-Host "========== 1. Runtime Preflight ==========" -ForegroundColor Cyan

& $Py $Preflight

if ($LASTEXITCODE -ne 0) {

    Write-Host ""
    Write-Host "PREFLIGHT_GATE = FAIL" -ForegroundColor Red

    exit 10
}

Write-Host ""
Write-Host "PREFLIGHT_GATE = PASS" -ForegroundColor Green


# ============================================================
# 2. 防止重复启动8189
# ============================================================

Write-Host ""
Write-Host "========== 2. 8189占用检查 ==========" -ForegroundColor Cyan

$ExistingListener = Get-NetTCPConnection `
    -LocalPort 8189 `
    -State Listen `
    -ErrorAction SilentlyContinue

if ($ExistingListener) {

    Write-Host "8189已经被占用。" -ForegroundColor Red

    $ExistingListener |
    Select-Object `
        LocalAddress,
        LocalPort,
        OwningProcess |
    Format-Table -AutoSize

    exit 11
}

Write-Host "PORT_8189_GATE = PASS" -ForegroundColor Green


# ============================================================
# 3. 诊断环境变量
# ============================================================

$env:PYTHONFAULTHANDLER = "1"
$env:PYTHONUNBUFFERED = "1"

# 第二次诊断保留同步CUDA
$env:CUDA_LAUNCH_BLOCKING = "1"

$env:TORCH_SHOW_CPP_STACKTRACES = "1"


# ============================================================
# 4. 参数
# ============================================================

$Arguments = @(
    "main.py",
    "--listen",
    "127.0.0.1",
    "--port",
    "8189",
    "--extra-model-paths-config",
    "$H3Root\extra_model_paths.yaml",
    "--input-directory",
    $InputDir,
    "--output-directory",
    $OutputDir,
    "--temp-directory",
    $TempDir,
    "--disable-mmap"
)


Write-Host ""
Write-Host "========== 3. 启动参数 ==========" -ForegroundColor Cyan

Write-Host "Python：" $Py
Write-Host "Runtime：" $H3Root
Write-Host "NO-MMAP：True"
Write-Host "CUDA_LAUNCH_BLOCKING：1"

Write-Host ""
Write-Host "STDOUT：" $StdoutLog
Write-Host "STDERR：" $StderrLog


# ============================================================
# 5. 独立启动ComfyUI
#
# 不再把 stderr 送进 PowerShell pipeline。
# 因此普通 [INFO] stderr 不会再变成 NativeCommandError。
# ============================================================

Write-Host ""
Write-Host "========== 4. 启动 ComfyUI ==========" -ForegroundColor Cyan

$Process = Start-Process `
    -FilePath $Py `
    -ArgumentList $Arguments `
    -WorkingDirectory $H3Root `
    -RedirectStandardOutput $StdoutLog `
    -RedirectStandardError $StderrLog `
    -PassThru


$Process.Id |
Set-Content `
    -LiteralPath $PidFile `
    -Encoding ASCII


Write-Host "PROCESS_STARTED = PASS" -ForegroundColor Green
Write-Host "PID =" $Process.Id


# ============================================================
# 6. 等待8189 READY
# ============================================================

Write-Host ""
Write-Host "========== 5. 等待8189 READY ==========" -ForegroundColor Cyan

$Base = "http://127.0.0.1:8189"

$Ready = $false

for ($i = 1; $i -le 90; $i++) {

    Start-Sleep -Seconds 2

    $Process.Refresh()

    if ($Process.HasExited) {

        Write-Host ""
        Write-Host "RUNTIME_PROCESS_EXITED = TRUE" -ForegroundColor Red
        Write-Host "ExitCode =" $Process.ExitCode

        Write-Host ""
        Write-Host "========== STDERR最后80行 ==========" -ForegroundColor Yellow

        if (Test-Path $StderrLog) {

            Get-Content `
                -LiteralPath $StderrLog `
                -Tail 80
        }

        Write-Host ""
        Write-Host "========== STDOUT最后80行 ==========" -ForegroundColor Yellow

        if (Test-Path $StdoutLog) {

            Get-Content `
                -LiteralPath $StdoutLog `
                -Tail 80
        }

        Write-Host ""
        Write-Host "H3_RUNTIME_GATE = FAIL" -ForegroundColor Red

        exit 12
    }


    try {

        $Stats = Invoke-RestMethod `
            "$Base/system_stats" `
            -TimeoutSec 2

        $Ready = $true

        break

    }
    catch {

        Write-Host `
            "等待8189... $($i * 2) 秒" `
            -ForegroundColor DarkGray
    }
}


if (-not $Ready) {

    Write-Host ""
    Write-Host "8189在180秒内没有READY。" -ForegroundColor Red
    Write-Host "PID仍为：" $Process.Id

    Write-Host ""
    Write-Host "STDERR：" $StderrLog
    Write-Host "STDOUT：" $StdoutLog

    Write-Host ""
    Write-Host "H3_RUNTIME_GATE = TIMEOUT" -ForegroundColor Red

    exit 13
}


# ============================================================
# 7. READY证据
# ============================================================

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "H3_RUNTIME_GATE = PASS" -ForegroundColor Green
Write-Host "============================================"

Write-Host ""
Write-Host "8189 = http://127.0.0.1:8189"
Write-Host "PID =" $Process.Id

Write-Host ""
Write-Host "NO-MMAP = ENABLED"
Write-Host "PREAD = ENABLED"

Write-Host ""
Write-Host "STDOUT："
Write-Host $StdoutLog

Write-Host ""
Write-Host "STDERR："
Write-Host $StderrLog

Write-Host ""
Write-Host "现在可以进行第二次 H3 Smoke。"
Write-Host "不要再次启动8189。"
