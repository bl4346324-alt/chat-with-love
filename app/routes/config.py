import os
from fastapi import APIRouter
from app.config import settings
from app.models import ConfigUpdateRequest

router = APIRouter(prefix="/api/config", tags=["config"])

def mask_key(k: str) -> str:
    if not k:
        return ""
    if len(k) <= 8:
        return "***"
    return k[:3] + "..." + k[-4:]

@router.get("")
def get_config():
    return {
        "jev_configured": bool(settings.JEV_API_KEY),
        "jev_key_masked": mask_key(settings.JEV_API_KEY),
        "jev_base_url": settings.JEV_BASE_URL,
        "llm_configured": bool(settings.LLM_API_KEY),
        "llm_key_masked": mask_key(settings.LLM_API_KEY),
        "llm_base_url": settings.LLM_BASE_URL,
        "llm_model": settings.LLM_MODEL,
        "vision_model": settings.VISION_MODEL
    }

@router.post("")
def update_config(req: ConfigUpdateRequest):
    env_path = settings.DATA_DIR.parent / ".env"
    env_lines = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env_lines[k.strip()] = v.strip()

    if req.jev_api_key is not None and req.jev_api_key != "":
        os.environ["JEV_API_KEY"] = req.jev_api_key.strip()
        env_lines["JEV_API_KEY"] = req.jev_api_key.strip()
    if req.jev_base_url is not None and req.jev_base_url != "":
        os.environ["JEV_BASE_URL"] = req.jev_base_url.strip()
        env_lines["JEV_BASE_URL"] = req.jev_base_url.strip()
    if req.llm_api_key is not None and req.llm_api_key != "":
        os.environ["LLM_API_KEY"] = req.llm_api_key.strip()
        env_lines["LLM_API_KEY"] = req.llm_api_key.strip()
    if req.llm_base_url is not None and req.llm_base_url != "":
        os.environ["LLM_BASE_URL"] = req.llm_base_url.strip()
        env_lines["LLM_BASE_URL"] = req.llm_base_url.strip()
    if req.llm_model is not None and req.llm_model != "":
        os.environ["LLM_MODEL"] = req.llm_model.strip()
        env_lines["LLM_MODEL"] = req.llm_model.strip()
    if req.vision_model is not None and req.vision_model != "":
        os.environ["VISION_MODEL"] = req.vision_model.strip()
        env_lines["VISION_MODEL"] = req.vision_model.strip()

    # 保存到本地 .env，无需用户手动修改代码
    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in env_lines.items():
            f.write(f"{k}={v}\n")
        
    return {
        "success": True,
        "message": "配置更新成功，已直接生效",
        "jev_configured": bool(settings.JEV_API_KEY),
        "llm_configured": bool(settings.LLM_API_KEY)
    }
