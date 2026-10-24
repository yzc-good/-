@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo    English Translator - Launcher
echo ============================================
echo.
echo    1) Open offline  (read + click-to-lookup)
echo    2) Start local service  (import PDF/Word, translate)
echo    0) Exit
echo.
set /p choice=Enter 1, 2 or 0:
echo.

if "%choice%"=="1" goto openfile
if "%choice%"=="2" goto server
exit /b

:openfile
start "" "%~dp0EnglishTranslator.html"
exit /b

:server
set "PY="
where python >nul 2>nul
if not errorlevel 1 set "PY=python"
if not defined PY (
  where py >nul 2>nul
  if not errorlevel 1 set "PY=py -3"
)
if not defined PY (
  if exist "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" set "PY=%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
)
if not defined PY (
  echo [ERROR] Python not found. Install Python 3, or use option 1.
  pause
  exit /b 1
)
echo Using Python: %PY%
echo Starting local service...
if exist "%~dp0_port.txt" del "%~dp0_port.txt" >nul 2>nul
start "EngTrans Service" /min cmd /c "%PY% server.py"

set "PORT=8338"
for /l %%i in (1,1,20) do (
  if exist "%~dp0_port.txt" goto ready
  ping -n 2 127.0.0.1 >nul
)
:ready
if exist "%~dp0_port.txt" set /p PORT=<"%~dp0_port.txt"
echo.
echo Service URL: http://127.0.0.1:%PORT%
start "" "http://127.0.0.1:%PORT%"
echo Service started. Close the minimized "EngTrans Service" window to stop.
ping -n 4 127.0.0.1 >nul
exit /b