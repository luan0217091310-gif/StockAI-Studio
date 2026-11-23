@echo off
chcp 65001 >nul
title StockAI Studio
cd /d "%~dp0"
set "STOCKAI_DATA_DIR=%~dp0data"
set PYTHONIOENCODING=utf-8
set "UVEXE=uv"
where uv >nul 2>nul
if errorlevel 1 (
  for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv*") do set "UVEXE=%%D\uv.exe"
)
echo Dang khoi dong StockAI Studio... (dong cua so nay de tat ung dung)
"%UVEXE%" run python app.py %*
pause
