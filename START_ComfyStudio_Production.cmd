@echo off
chcp 65001 >nul
title ComfyStudio Production startup check
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0START_ComfyStudio_Production.ps1"
if errorlevel 1 (
  echo.
  echo Startup check failed. See upgrade_logs\startup\startup.log
)
pause
