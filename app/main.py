from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from app.config import settings
from app.database import init_db
from app.routes import analyze, config, history, skills

# 初始化本地数据库
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 TypeSafe Jev 决策模型与情圣/狗头军师实战知识库的微信聊天心智洞察与军师决策系统"
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(analyze.router)
app.include_router(config.router)
app.include_router(history.router)
app.include_router(skills.router)

# 挂载静态资源
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Chat-with-Love API is running. Web UI will be ready shortly."}

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "jev_ready": bool(settings.JEV_API_KEY),
        "llm_ready": bool(settings.LLM_API_KEY)
    }
