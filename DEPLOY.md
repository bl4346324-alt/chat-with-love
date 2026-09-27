# Chat-with-Love · 心语军师 云服务器部署指南

本指南手把手教你如何将心语军师部署到 Linux 云服务器（阿里云、腾讯云、华为云、AWS、轻量应用服务器等）。

---

## 目录
1. [服务器准备与配置要求](#1-服务器准备与配置要求)
2. [方式一：Docker 一键容器化部署（强烈推荐）](#2-方式一docker-一键容器化部署强烈推荐)
3. [方式二：原生 Python + Systemd 后台常驻部署](#3-方式二原生-python--systemd-后台常驻部署)
4. [配置 Nginx 反向代理与 HTTPS 域名（可选）](#4-配置-nginx-反向代理与-https-域名可选)
5. [常见问题与排错排查](#5-常见问题与排错排查)

---

## 1. 服务器准备与配置要求

- **操作系统**：Ubuntu 20.04/22.04/24.04、Debian 11/12 或 CentOS 7/8/9
- **最低配置**：1 核 CPU / 1GB 内存（推荐 2 核 2GB / 2核 4GB，离线 OCR 响应更快）
- **防火墙/安全组**：在腾讯云 / 阿里云等控制台安全组放行 **8000 端口**（TCP）。

---

## 2. 方式一：Docker 一键容器化部署（强烈推荐）

使用 Docker 部署能完全隔离 Python 依赖与系统环境，且自带进程守护与开机自启。

### 步骤 1：在服务器安装 Docker 与 Docker Compose
如果服务器尚未安装 Docker，在服务器终端执行：
```bash
# Ubuntu / Debian 快速安装
curl -fsSL https://get.docker.com | bash
sudo systemctl enable --now docker
```

### 步骤 2：将代码上传到服务器
在你的本地电脑终端中执行（将 `root@your-server-ip` 替换为你的服务器地址）：
```bash
# 在本地 chat-with-love 根目录下执行
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='data' ./ root@your-server-ip:/opt/chat-with-love
```

### 步骤 3：在服务器上配置 API 密钥
登录你的云服务器：
```bash
ssh root@your-server-ip
cd /opt/chat-with-love

# 创建并编辑 .env 配置文件
nano .env  # 或 vim .env
```
在 `.env` 中填入你的真实密钥：
```env
# TypeSafe Jev (系统一)
JEV_API_KEY=你的Jev密钥
JEV_BASE_URL=https://api.typesafe.ai/v1

# DeepSeek (系统二)
LLM_API_KEY=sk-你的DeepSeek密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```
按 `Ctrl+O` 回车保存，`Ctrl+X` 退出 nano。

### 步骤 4：启动容器
在 `/opt/chat-with-love` 目录下执行：
```bash
docker compose up -d --build
```

### 步骤 5：验证运行状态
```bash
# 查看容器状态
docker ps

# 查看实时日志
docker logs -f chat-with-love
```
在浏览器访问：`http://你的服务器公网IP:8000` 即可开始使用！

---

## 3. 方式二：原生 Python + Systemd 后台常驻部署

### 步骤 1：安装 Python 基础依赖
以 Ubuntu / Debian 为例：
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv libglib2.0-0 libgomp1
```

### 步骤 2：部署代码与安装依赖
```bash
# 假设代码目录为 /opt/chat-with-love
cd /opt/chat-with-love

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

### 步骤 3：配置系统守护服务 (Systemd)
创建 systemd 服务文件：
```bash
sudo nano /etc/systemd/system/chat-love.service
```
粘贴以下内容：
```ini
[Unit]
Description=Chat-with-Love FastAPI Daemon
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chat-with-love
EnvironmentFile=/opt/chat-with-love/.env
ExecStart=/opt/chat-with-love/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

保存退出后，启用并启动服务：
```bash
# 重新加载服务配置
sudo systemctl daemon-reload

# 开机自启并立刻启动
sudo systemctl enable --now chat-love

# 查看运行状态
sudo systemctl status chat-love
```

---

## 4. 配置 Nginx 反向代理与 HTTPS 域名（可选）

如果想绑定域名，并使用标准的 80 / 443 (HTTPS) 端口访问：

### Nginx 配置示例 (`/etc/nginx/sites-available/chat-love.conf`)
```nginx
server {
    listen 80;
    server_name your-domain.com; # 你的域名

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 核心：必须关闭代理缓冲，确保 SSE 流式打字机 0.2 秒极速输出！
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }
}
```

启用配置并重载 Nginx：
```bash
sudo ln -s /etc/nginx/sites-available/chat-love.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

如果需要免费 HTTPS 证书，执行：
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 5. 常见问题与排错排查

1. **浏览器无法打开网页（ERR_CONNECTION_TIMED_OUT）**：
   - 检查云服务器控制台的安全组规则，是否添加了 `TCP 8000` 入站规则。
2. **打字机没有流式效果，而是停顿几秒后一次性吐出**：
   - 如果使用了 Nginx，务必在 Nginx 的 location 配置中加入 `proxy_buffering off;`，避免 Nginx 缓存 SSE 数据包。
3. **密钥安全问题**：
   - 不要将 `.env` 提交到公开的 GitHub 仓库；
   - 外部访问你网站的用户无法通过查看网页源代码或 F12 抓包获取你的 Key，所有请求均在后端中转。
