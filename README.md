# Chat-with-Love (心语军师)

> 基于 **TypeSafe Jev（系统一决策模型）** 与 **狗头军师（goutoujunshi）135+ 篇实战知识库** 构建的微信聊天心智洞察与军师决策系统。

---

## 🌟 核心特性

1. **微信截图一键粘贴 (Ctrl+V)**：
   - 网页内直接按下 `Ctrl+V`（Mac 为 `Cmd+V`）即可粘贴微信聊天截图；
   - 自动解析双方气泡颜色、左右位置、时间戳，还原真实对话流。
2. **Jev 毫秒级心智直觉判决 (System 1)**：
   - 基于 TypeSafe AI 的 Jev 系统一模型（70~300ms 极速响应，零生成 Token 消耗）；
   - 瞬间计算**好感度评分 (0-100)**、**防备心指数 (0-100)**、**权力动态**与**废物测试识别**。
3. **狗头军师实战知识路由与三阶话术 (System 2)**：
   - 按照 Jev 的判定，精准路由到 7 大主策略（承接、降压、调侃、轻推、约见、澄清、收线）；
   - 生成：**稳健走心版**、**高情商策略版**、**设立边界版** 三套可直接复制的成品话术；
   - 提供发送时机、心理学设计 rationale 以及对方 3 种后续反应预判。
4. **开箱即用与极简配置**：
   - 未填 Key 时自动使用高保真内置启发模型，可立即上手体验；
   - 填入 Jev API Key 与 LLM API Key 后无缝切换为全功能大模型在线驱动。

---

## 🚀 快速启动

在项目根目录下直接运行启动脚本：

```bash
./run.sh
```

或者使用 Python 命令：

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后在浏览器打开：
👉 **http://localhost:8000**

---

## ⚙️ API 配置说明

点击网页右上角的 **「API 配置」** 按钮，或者在本地根目录创建 `.env` 文件：

```ini
# TypeSafe AI Jev (系统一)
JEV_API_KEY=your_jev_api_key_here
JEV_BASE_URL=https://api.typesafe.ai/v1

# 生成大模型 (系统二，兼容 OpenAI 协议的各类中转 API)
LLM_API_KEY=your_llm_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=deepseek-chat

# 视觉模型 (用于云端截图气泡提取，可选)
VISION_MODEL=gpt-4o
```

---

## 📂 工程结构

```
chat-with-love/
├── app/
│   ├── config.py              # 核心配置与环境变量读取
│   ├── database.py            # SQLite 本地存储与历史记录管理
│   ├── models.py              # Pydantic 数据规范
│   ├── main.py                # FastAPI 入口与静态页面挂载
│   ├── services/
│   │   ├── jev_service.py     # TypeSafe Jev (系统一) 客户端及启发式决策
│   │   ├── ocr_service.py     # 微信截图气泡提取与纯文本对话结构化
│   │   ├── llm_service.py     # 融合狗头军师实战库的三阶话术生成
│   │   └── knowledge_service.py # 狗头军师 7 大核心策略知识路由器
│   ├── routes/
│   │   ├── analyze.py         # /api/analyze/text & /api/analyze/screenshot
│   │   ├── config.py          # /api/config 动态读取与更新配置
│   │   └── history.py         # /api/history 历史复盘查看
│   └── static/
│       ├── index.html         # 现代化军师看板界面
│       └── js/app.js          # 剪贴板监听、气泡渲染、一键复制
├── goutoujunshi-repo/         # 克隆自官方的狗头军师完整知识库
├── requirements.txt           # 依赖清单
├── run.sh                     # 一键启动脚本
└── README.md                  # 说明文档
```
