from fastapi import APIRouter
from app.services.skill_service import skill_service

router = APIRouter(prefix="/api/skills", tags=["skills"])

@router.get("")
def list_skills():
    """获取项目中已装载的 GitHub 恋爱 Skill 列表及配置详情"""
    return {
        "success": True,
        "skills": skill_service.get_installed_skills(),
        "stages": [
            {"stage": 1, "name": "开场破冰", "goal": "破冰初识，建立安全无压力连接"},
            {"stage": 2, "name": "建立好感", "goal": "好感舒适，展示生活并引发好奇"},
            {"stage": 3, "name": "关系升温", "goal": "拉扯张力，制造幽默与专属默契"},
            {"stage": 4, "name": "邀约见面", "goal": "邀约三步法，自然落地现实相遇"},
            {"stage": 5, "name": "约会实战", "goal": "线下真实接触，自然松弛互动"},
            {"stage": 6, "name": "亲密升级", "goal": "深层脆弱坦露，确认彼此心意"},
            {"stage": 7, "name": "确立关系", "goal": "水到渠成，正式确立长期排他恋爱"}
        ]
    }
