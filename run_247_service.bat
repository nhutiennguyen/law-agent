@echo off
chcp 65001 > nul
title AI Lawyer - 24/7 Service Daemon
cd /d "%~dp0"

echo ============================================================
echo   AI HUYNH NGUYEN KHANG - HE THONG CHAY 24/7 (BACKGROUND)
echo ============================================================

:: Kill existing instances on port 8000 if any
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Start Backend in background
start /b python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

:: Wait 3 seconds for backend to initialize
timeout /t 3 /nobreak > nul

:: Start Cloudflare Tunnel with auto-retry loop
:LOOP
echo [%date% %time%] Dang duy tri ket noi Cloudflare Tunnel...
.\cloudflared.exe tunnel --url http://127.0.0.1:8000
echo [%date% %time%] Mat ket noi, tu dong khoi dong lai sau 5 giay...
timeout /t 5 /nobreak > nul
goto LOOP
