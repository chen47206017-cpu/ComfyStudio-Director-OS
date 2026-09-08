$ErrorActionPreference = "Stop"

$Root = "F:\一人公司\comfyui-production"

$ReportDir = "$Root\reports\h3\H3-R2V-SMOKE-001"

New-Item `
    -ItemType Directory `
    -Force `
    -Path $ReportDir |
Out-Null


$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"

$Report = "$ReportDir\pagefile-config-$Stamp.txt"


Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "H3 PAGEFILE 最终修复" -ForegroundColor Cyan
Write-Host "D = 5888MB" -ForegroundColor Cyan
Write-Host "F = 32768~49152MB" -ForegroundColor Cyan
Write-Host "=================================================="


# ============================================================
# 1. 管理员权限
# ============================================================

$Identity = [Security.Principal.WindowsIdentity]::GetCurrent()

$Principal = New-Object `
    Security.Principal.WindowsPrincipal($Identity)

$IsAdmin = $Principal.IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $IsAdmin) {
    throw "FAIL：必须使用管理员 PowerShell。"
}

Write-Host ""
Write-Host "ADMIN_GATE = PASS" -ForegroundColor Green


# ============================================================
# 2. 显示 CIM 属性真实类型
# ============================================================

Write-Host ""
Write-Host "========== Win32_PageFileSetting 属性类型 ==========" -ForegroundColor Cyan

$Class = Get-CimClass `
    -ClassName Win32_PageFileSetting

$Class.CimClassProperties |
Where-Object {
    $_.Name -in @(
        "Name",
        "InitialSize",
        "MaximumSize"
    )
} |
Select-Object `
    Name,
    CimType |
Format-Table -AutoSize


# ============================================================
# 3. 保存修改前状态
# ============================================================

$CS = Get-CimInstance Win32_ComputerSystem

$OldSettings = @(
    Get-CimInstance `
        Win32_PageFileSetting `
        -ErrorAction SilentlyContinue
)

$OldUsage = @(
    Get-CimInstance `
        Win32_PageFileUsage `
        -ErrorAction SilentlyContinue
)

$RegPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"

$OldRegistry = (
    Get-ItemProperty `
        -Path $RegPath `
        -Name PagingFiles `
        -ErrorAction SilentlyContinue
).PagingFiles


@"
H3 PAGEFILE BEFORE
==================

时间：
$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

AutomaticManagedPagefile:
$($CS.AutomaticManagedPagefile)

PageFileSetting:
$($OldSettings | Select Name,InitialSize,MaximumSize | Format-Table -AutoSize | Out-String)

PageFileUsage:
$($OldUsage | Select Name,AllocatedBaseSize,CurrentUsage,PeakUsage | Format-Table -AutoSize | Out-String)

Registry PagingFiles:
$($OldRegistry | Out-String)
"@ |
Set-Content `
    -LiteralPath $Report `
    -Encoding UTF8


Write-Host ""
Write-Host "修改前状态已保存：" -ForegroundColor Green
Write-Host $Report


# ============================================================
# 4. 关闭自动页面文件管理
# ============================================================

$CS |
Set-CimInstance `
    -Property @{
        AutomaticManagedPagefile = $false
    } |
Out-Null


$CSCheck = Get-CimInstance Win32_ComputerSystem

if ($CSCheck.AutomaticManagedPagefile) {
    throw "FAIL：无法关闭 AutomaticManagedPagefile。"
}

Write-Host ""
Write-Host "AUTO_PAGEFILE_GATE = PASS" -ForegroundColor Green


# ============================================================
# 5. 删除旧的下一次启动PageFileSetting
# ============================================================

$ExistingSettings = @(
    Get-CimInstance `
        Win32_PageFileSetting `
        -ErrorAction SilentlyContinue
)

foreach ($Setting in $ExistingSettings) {

    Write-Host "删除旧配置：" $Setting.Name -ForegroundColor Yellow

    $Setting |
    Remove-CimInstance
}


# ============================================================
# 6. 使用明确 UInt32 创建 D
# ============================================================

Write-Host ""
Write-Host "创建 D 页面文件配置..." -ForegroundColor Cyan

$DProperties = @{
    Name        = [string]"D:\pagefile.sys"
    InitialSize = [uint32]5888
    MaximumSize = [uint32]5888
}


# ============================================================
# 7. 使用明确 UInt32 创建 F
# ============================================================

$FProperties = @{
    Name        = [string]"F:\pagefile.sys"
    InitialSize = [uint32]32768
    MaximumSize = [uint32]49152
}


$CimSucceeded = $true


try {

    New-CimInstance `
        -Namespace "root\cimv2" `
        -ClassName Win32_PageFileSetting `
        -Property $DProperties |
    Out-Null

    Write-Host "CIM D CREATE = PASS" -ForegroundColor Green


    New-CimInstance `
        -Namespace "root\cimv2" `
        -ClassName Win32_PageFileSetting `
        -Property $FProperties |
    Out-Null

    Write-Host "CIM F CREATE = PASS" -ForegroundColor Green

}
catch {

    $CimSucceeded = $false

    Write-Host ""
    Write-Host "CIM CREATE失败：" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Yellow
}


# ============================================================
# 8. 如果 CIM 创建失败，使用 Windows 注册表原生配置
# ============================================================

if (-not $CimSucceeded) {

    Write-Host ""
    Write-Host "切换到 Registry MultiString 配置..." -ForegroundColor Cyan

    $PagingFiles = [string[]]@(
        "D:\pagefile.sys 5888 5888",
        "F:\pagefile.sys 32768 49152"
    )

    New-ItemProperty `
        -Path $RegPath `
        -Name "PagingFiles" `
        -PropertyType MultiString `
        -Value $PagingFiles `
        -Force |
    Out-Null

    Write-Host "REGISTRY PAGEFILE WRITE = PASS" -ForegroundColor Green
}


# ============================================================
# 9. 无论 CIM 是否成功，都确保 Registry 值完全一致
# ============================================================

$DesiredPagingFiles = [string[]]@(
    "D:\pagefile.sys 5888 5888",
    "F:\pagefile.sys 32768 49152"
)

New-ItemProperty `
    -Path $RegPath `
    -Name "PagingFiles" `
    -PropertyType MultiString `
    -Value $DesiredPagingFiles `
    -Force |
Out-Null


# ============================================================
# 10. 最终 Registry 验证
# ============================================================

Write-Host ""
Write-Host "========== Registry最终配置 ==========" -ForegroundColor Cyan

$RegistryPagingFiles = @(
    (
        Get-ItemProperty `
            -Path $RegPath `
            -Name PagingFiles
    ).PagingFiles
)

$RegistryPagingFiles |
ForEach-Object {
    Write-Host $_
}


$ExpectedD = "D:\pagefile.sys 5888 5888"
$ExpectedF = "F:\pagefile.sys 32768 49152"


$RegistryD = (
    $RegistryPagingFiles -contains $ExpectedD
)

$RegistryF = (
    $RegistryPagingFiles -contains $ExpectedF
)

$RegistryC = (
    @(
        $RegistryPagingFiles |
        Where-Object {
            $_ -like "C:\pagefile.sys*"
        }
    ).Count -gt 0
)


# ============================================================
# 11. CIM重新读取
# ============================================================

Write-Host ""
Write-Host "========== CIM最终配置 ==========" -ForegroundColor Cyan

$FinalSettings = @(
    Get-CimInstance `
        Win32_PageFileSetting `
        -ErrorAction SilentlyContinue
)

$FinalSettings |
Select-Object `
    Name,
    InitialSize,
    MaximumSize |
Sort-Object Name |
Format-Table -AutoSize


# ============================================================
# 12. 门禁
# ============================================================

Write-Host ""
Write-Host "========== PAGEFILE CONFIG GATE ==========" -ForegroundColor Cyan

Write-Host "Registry D =" $RegistryD
Write-Host "Registry F =" $RegistryF
Write-Host "Registry C =" $RegistryC


$Gate = (
    $RegistryD -and
    $RegistryF -and
    (-not $RegistryC) -and
    (-not $CSCheck.AutomaticManagedPagefile)
)


if (-not $Gate) {

    Write-Host ""
    Write-Host "PAGEFILE_CONFIG_GATE = FAIL" -ForegroundColor Red

    throw "页面文件配置未达到安全门禁，禁止重启。"
}


# ============================================================
# 13. 写入最终报告
# ============================================================

@"

H3 PAGEFILE AFTER
=================

时间：
$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

AutomaticManagedPagefile:
$($CSCheck.AutomaticManagedPagefile)

Registry PagingFiles:
$($RegistryPagingFiles | Out-String)

CIM Settings:
$($FinalSettings | Select Name,InitialSize,MaximumSize | Format-Table -AutoSize | Out-String)

PAGEFILE_CONFIG_GATE:
PASS
"@ |
Add-Content `
    -LiteralPath $Report `
    -Encoding UTF8


Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "PAGEFILE_CONFIG_GATE = PASS" -ForegroundColor Green
Write-Host "=================================================="

Write-Host ""
Write-Host "下一次启动目标：" -ForegroundColor Green
Write-Host "D:\pagefile.sys 5888 5888"
Write-Host "F:\pagefile.sys 32768 49152"

Write-Host ""
Write-Host "报告：" -ForegroundColor Green
Write-Host $Report

Write-Host ""
Write-Host "现在才可以重启 Windows。" -ForegroundColor Yellow
