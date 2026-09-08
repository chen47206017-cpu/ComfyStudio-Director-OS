$ErrorActionPreference = "Stop"

$Project = "F:\一人公司\comfyui-production"

$H3Root = "$Project\staging\comfyui-v0.34.0\ComfyUI-0.34.0"
$Py = "$H3Root\.venv\Scripts\python.exe"

$InputDir  = "G:\ComfyStudioData\workers\h3-f\input"
$OutputDir = "G:\ComfyStudioData\workers\h3-f\output"
$TempDir   = "$Project\runtime\temp\h3-f"

$LogDir = "$Project\reports\h3\H3-R2V-SMOKE-001\diagnostic"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Log = "$LogDir\comfy8189-$Timestamp.log"

# ------------------------------------------------
# 原生崩溃诊断
# ------------------------------------------------

$env:PYTHONFAULTHANDLER = "1"
$env:PYTHONUNBUFFERED = "1"

# CUDA错误尽量在真实发生位置同步暴露
$env:CUDA_LAUNCH_BLOCKING = "1"

# PyTorch C++错误尽可能输出C++调用栈
$env:TORCH_SHOW_CPP_STACKTRACES = "1"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "H3 8189 诊断启动模式" -ForegroundColor Cyan
Write-Host "============================================"

Write-Host "Python：$Py"
Write-Host "Root：$H3Root"
Write-Host "Log：$Log"

Write-Host ""
Write-Host "检查解释器..." -ForegroundColor Cyan

& $Py -c "import sys,torch; print('EXE=',sys.executable); print('TORCH=',torch.__version__); print('CUDA=',torch.version.cuda); print('CUDA_OK=',torch.cuda.is_available()); print('GPU=',torch.cuda.get_device_name(0)); print('CAP=',torch.cuda.get_device_capability(0))"

if ($LASTEXITCODE -ne 0) {
    throw "Python/Torch基础检查失败"
}

Write-Host ""
Write-Host "启动8189..." -ForegroundColor Cyan

Push-Location $H3Root

try {

    & $Py main.py `
        --listen 127.0.0.1 `
        --port 8189 `
        --extra-model-paths-config "$H3Root\extra_model_paths.yaml" `
        --input-directory "$InputDir" `
        --output-directory "$OutputDir" `
        --temp-directory "$TempDir" `
        2>&1 |
    Tee-Object `
        -FilePath $Log

}
finally {

    Pop-Location

    Write-Host ""
    Write-Host "8189进程已经结束。" -ForegroundColor Yellow
    Write-Host "完整日志：" -ForegroundColor Yellow
    Write-Host $Log
}
