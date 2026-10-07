from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class MessageItem(BaseModel):
    sender: str = Field(..., description="'me' or 'other' or specific nickname")
    text: str
    time: Optional[str] = None
    is_me: bool = False

class TextAnalysisRequest(BaseModel):
    text: str = Field(..., description="聊天记录纯文本")
    target_alias: Optional[str] = "对方"
    user_mbti: Optional[str] = ""
    target_mbti: Optional[str] = ""
    current_goal: Optional[str] = "推进关系"
    auto_invoke: Optional[bool] = False

class JevDecision(BaseModel):
    primary_strategy: str = Field(..., description="承接 / 降压 / 调侃 / 轻推 / 约见 / 澄清 / 收线")
    strategy_explanation: str = Field("", description="主策略选取理由")
    hidden_intent: str = Field(..., description="对方深层心理意图")
    interest_score: int = Field(..., ge=0, le=100, description="好感度/兴趣度 0-100")
    defense_score: int = Field(..., ge=0, le=100, description="心理防备度 0-100")
    power_dynamic: int = Field(50, ge=0, le=100, description="权力平衡度 (0对方主导, 100我方主导)")
    is_shit_test: bool = Field(False, description="是否为废物测试/话语陷阱")
    shit_test_prob: float = Field(0.0, description="废物测试置信概率 (0.0-1.0)")
    is_crisis: bool = Field(False, description="是否存在语言暴力或安全危机")
    emotional_state: str = Field("平稳", description="对方当下的主要情绪")

class SkillInsight(BaseModel):
    active_skills: List[str] = Field(default_factory=lambda: ["情圣 (QingSheng v6.0)", "狗头军师 (GouTouJunShi)"])
    stage_number: int = Field(2, ge=1, le=7, description="当前所处关系推进阶段 1-7")
    stage_name: str = Field(..., description="阶段名称，如：阶段3：关系升温")
    stage_goal: str = Field(..., description="当前阶段核心目标")
    signal_type: str = Field(..., description="IOI 兴趣信号 / IOD 设防信号 / 废物测试 / 平稳日常")
    signal_detail: str = Field(..., description="信号深度解读")
    tactics_suggested: List[str] = Field(default_factory=list, description="推荐实战技法标签")

class ReplyOption(BaseModel):
    tier: str = Field(..., description="稳健走心版 / 高情商策略版 / 设立边界版")
    content: str = Field(..., description="可直接复制发送的话术")
    rationale: str = Field(..., description="心理学设计理由")
    timing: str = Field("适时发送", description="发送时机与节奏建议")
    tone_tags: List[str] = Field(default_factory=list, description="语气标签")

class BranchPrediction(BaseModel):
    if_positive: str = Field(..., description="对方积极延展/反问时的接球建议")
    if_neutral: str = Field(..., description="对方礼貌但含糊时的后续应对")
    if_cooling: str = Field(..., description="对方冷淡/不回时的停止与观察窗口")

class AnalysisResponse(BaseModel):
    success: bool = True
    dialogue: List[MessageItem]
    jev: JevDecision
    skill_insight: Optional[SkillInsight] = None
    replies: List[ReplyOption]
    branch: BranchPrediction
    latency_ms: int = 0
    is_mock: bool = False
    error: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    jev_api_key: Optional[str] = None
    jev_base_url: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    vision_model: Optional[str] = None

class StreamAnalysisRequest(BaseModel):
    text: Optional[str] = None
    image_base64: Optional[str] = None
    target_alias: Optional[str] = "对方"
    user_mbti: Optional[str] = ""
    target_mbti: Optional[str] = ""
    auto_invoke: Optional[bool] = False
