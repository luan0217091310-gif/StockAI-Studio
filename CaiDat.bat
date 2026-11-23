@echo off
chcp 65001 >nul
title Cai dat StockAI Studio
cd /d "%~dp0"
set "UVEXE=uv"
where uv >nul 2>nul
if errorlevel 1 (
  for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv*") do set "UVEXE=%%D\uv.exe"
)
where ffmpeg >nul 2>nul
if errorlevel 1 (
  echo [1/4] Cai FFmpeg...
  winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
)
if not exist "%UVEXE%" if "%UVEXE%" neq "uv" (
  echo [2/4] Cai uv...
  winget install -e --id astral-sh.uv --accept-source-agreements --accept-package-agreements
  for /d %%D in ("%LOCALAPPDATA%\Microsoft\WinGet\Packages\astral-sh.uv*") do set "UVEXE=%%D\uv.exe"
)
echo [3/4] Cai thu vien Python...
"%UVEXE%" sync || goto :err
set "STOCKAI_DATA_DIR=%~dp0data"
echo [4/4] Tao loi tat Desktop + Start Menu + tu khoi dong cung Windows...
"%UVEXE%" run python -m stockai install --autostart || goto :err
"%UVEXE%" run python -m stockai preflight
echo.
echo XONG. Mo app bang bieu tuong "StockAI Studio" tren Desktop.
pause
exit /b 0
:err
echo LOI khi cai dat - xem thong bao phia tren.
pause
exit /b 1
