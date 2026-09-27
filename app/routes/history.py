from fastapi import APIRouter
from app.database import get_recent_analyses

router = APIRouter(prefix="/api/history", tags=["history"])

@router.get("")
def get_history(limit: int = 20):
    return {
        "success": True,
        "items": get_recent_analyses(limit=limit)
    }
