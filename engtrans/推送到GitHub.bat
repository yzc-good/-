@echo off
rem Launcher for sync_to_github.ps1 (ASCII only, on purpose)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0sync_to_github.ps1"
if errorlevel 1 pause
