#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi

echo "=================================================="
echo "  🚀 Chat-with-Love (心语军师) 启动中..."
echo "  - 网页访问入口: http://localhost:8000"
echo "  - 局域网/手机访问: http://0.0.0.0:8000"
echo "=================================================="

exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
