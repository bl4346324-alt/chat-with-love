' Chat-with-Love Windows 后台静默启动脚本 (无黑框窗口)
Set WshShell = CreateObject("WScript.Shell")

' 1. 后台隐形启动 uvicorn 服务 (最后一个参数为 0 表示窗口完全隐藏)
WshShell.Run "cmd /c uvicorn app.main:app --host 0.0.0.0 --port 8000", 0, False

' 等待 2 秒确保后端服务就绪
WScript.Sleep 2000

' 2. 后台隐形启动 Cloudflare 隧道 (窗口完全隐藏，日志追加输出到 tunnel.log)
WshShell.Run "cmd /c cloudflared.exe tunnel --url http://127.0.0.1:8000 > tunnel.log 2>&1", 0, False
