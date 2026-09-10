@echo off
chcp 65001 > nul
echo Dang dung he thong AI Lawyer...
taskkill /f /im cloudflared.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo Da dung toan bo tien trinh 24/7 thanh cong.
pause
