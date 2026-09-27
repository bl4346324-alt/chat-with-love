import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 优先读取系统环境变量，若未配置则加载本地 .env
load_dotenv(BASE_DIR / ".env", override=False)

class Settings:
    APP_NAME: str = "Chat-with-Love (心语军师)"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "chat_love.sqlite3"
    
    # 动态从操作系统环境变量读取，支持多种常用别名
    @property
    def JEV_API_KEY(self) -> str:
        return (
            os.environ.get("JEV_API_KEY") or 
            os.environ.get("JEV_KEY") or 
            os.environ.get("TYPESAFE_API_KEY") or 
            ""
        ).strip()

    @property
    def JEV_BASE_URL(self) -> str:
        return (
            os.environ.get("JEV_BASE_URL") or 
            os.environ.get("JEV_URL") or 
            "https://api.typesafe.ai/v1"
        ).strip().rstrip("/")

    @property
    def LLM_API_KEY(self) -> str:
        return (
            os.environ.get("LLM_API_KEY") or 
            os.environ.get("OPENAI_API_KEY") or 
            os.environ.get("DEEPSEEK_API_KEY") or 
            os.environ.get("API_KEY") or 
            ""
        ).strip()

    @property
    def LLM_BASE_URL(self) -> str:
        return (
            os.environ.get("LLM_BASE_URL") or 
            os.environ.get("OPENAI_BASE_URL") or 
            os.environ.get("OPENAI_API_BASE") or 
            "https://api.openai.com/v1"
        ).strip().rstrip("/")

    @property
    def LLM_MODEL(self) -> str:
        return (
            os.environ.get("LLM_MODEL") or 
            os.environ.get("MODEL_NAME") or 
            os.environ.get("MODEL") or 
            "deepseek-chat"
        ).strip()

    @property
    def VISION_MODEL(self) -> str:
        return (
            os.environ.get("VISION_MODEL") or 
            os.environ.get("VISION_LLM") or 
            "gpt-4o"
        ).strip()

settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
