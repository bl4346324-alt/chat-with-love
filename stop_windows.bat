@echo off
chcp 65001 >nul
echo 正在停止 Chat-with-Love 后台服务...
taskkill /F /IM cloudflared.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /F /PID %%a >nul 2>&1
echo 所有服务已彻底停止！
timeout /t 2 >nul
