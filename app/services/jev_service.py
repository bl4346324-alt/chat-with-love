import httpx
import logging
from typing import Dict, Any, List
from app.config import settings
from app.models import JevDecision, MessageItem

logger = logging.getLogger("jev_service")

class JevService:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url

    @property
    def effective_api_key(self):
        return self.api_key or settings.JEV_API_KEY

    @property
    def effective_base_url(self):
        return (self.base_url or settings.JEV_BASE_URL).rstrip("/")

    async def decide_dialogue_state(self, dialogue: List[MessageItem], user_mbti: str = "", target_mbti: str = "") -> JevDecision:
        """
        调用 TypeSafe AI 的 Jev 系统一模型进行毫秒级心理与意图决断。
        如果未配置 Jev Key 或网络受阻，无缝切换为高精准本地启发式智能判断（开发/离线演示模式）。
        """
        # 构建对话上下文 State
        dialogue_lines = []
        for msg in dialogue:
            sender_label = "我" if msg.is_me else "对方"
            dialogue_lines.append(f"{sender_label}: {msg.text}")
        state_text = "\n".join(dialogue_lines)
        if user_mbti or target_mbti:
            state_text = f"[背景: 我的MBTI={user_mbti or '未知'}, 对方MBTI={target_mbti or '未知'}]\n" + state_text

        if self.effective_api_key:
            try:
                decision = await self._call_jev_api(state_text)
                if decision:
                    return decision
            except Exception as e:
                logger.error(f"Jev API 调用失败: {e}")
                raise RuntimeError(f"TypeSafe Jev API 调用失败: {e}，请检查网络或密钥。")
        
        # 仅在未配置 Key 时作为初始引导演示
        return self._heuristic_mock_decision(dialogue, user_mbti, target_mbti)

    async def _call_jev_api(self, state_text: str) -> JevDecision:
        headers = {
            "Authorization": f"Bearer {self.effective_api_key}",
            "Content-Type": "application/json"
        }
        
        questions = {
            "primary_strategy": {
                "type": "choice",
                "instructions": "根据对方当下的情绪与表达，判断我方这轮最适宜采取的主策略：",
                "criteria": {
                    "承接": "对方正在倾诉、受挫、兴奋或分享，需要情感被接住",
                    "降压": "对方忙、累、冷、回避，需要给空间停止施压",
                    "调侃": "对方在接梗、反问或互动良好，可增加张力与幽默",
                    "轻推": "对话顺畅但原地打转，可将泛聊向纵深推进一步",
                    "约见": "双方有共同话题或窗口期，可发起低压力具体邀约",
                    "澄清": "对方表达模糊或有矛盾，需厘清单一事实",
                    "收线": "对方持续单向冷漠、不尊重或无意愿，守住自尊及时止损"
                }
            },
            "hidden_intent": {
                "type": "choice",
                "instructions": "分析对方说这些话背后的核心心理动机：",
                "criteria": {
                    "寻求情绪共情": "倾诉日常与疲惫，希望被理解与陪伴",
                    "试探防御底线": "暗含试探、考量或轻度防御",
                    "礼貌敷衍回应": "缺乏交流欲望，出于社交礼貌简短回复",
                    "暗示期待带领": "释放软性好感，等待被主动邀约或引出话题",
                    "轻松日常闲聊": "无特殊负担的随意日常分享"
                }
            },
            "interest_score": {
                "type": "score",
                "instructions": "评估对方当前对我的好感与互动热情指数：",
                "criteria": ["冷淡排斥", "礼貌中立", "明显好感"]
            },
            "defense_score": {
                "type": "score",
                "instructions": "评估对方当下的心理防备心与警戒程度：",
                "criteria": ["敞开放松", "稍有保留", "戒备警惕"]
            },
            "power_dynamic": {
                "type": "score",
                "instructions": "评估互动权力平衡状态：",
                "criteria": ["对方主导冷落", "平等互惠平衡", "我方主导引领"]
            },
            "is_shit_test": {
                "type": "noul",
                "instructions": "对方这句话是否属于'废物测试'或话语陷阱？"
            },
            "is_urgent_crisis": {
                "type": "noul",
                "instructions": "是否存在暴力控制、人身危险或亟需紧急转介的危机？"
            }
        }

        endpoint = f"{self.effective_base_url}/systemone"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                endpoint,
                json={
                    "model": "jev-latest",
                    "state": state_text,
                    "questions": questions
                },
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            answers = data.get("answers", {})
            
            strat = answers.get("primary_strategy", {}).get("choice", "承接")
            intent = answers.get("hidden_intent", {}).get("choice", "轻松日常闲聊")
            
            # 依据 Jev score 的归一化浮点数映射为 0-100
            raw_interest = float(answers.get("interest_score", {}).get("score", 1.0))
            raw_defense = float(answers.get("defense_score", {}).get("score", 0.8))
            raw_power = float(answers.get("power_dynamic", {}).get("score", 1.0))

            interest = int(min(100, max(0, raw_interest * 50)))
            defense = int(min(100, max(0, raw_defense * 50)))
            power = int(min(100, max(0, raw_power * 50)))

            shit_test_prob = float(answers.get("is_shit_test", {}).get("noul", 0.0))
            crisis_prob = float(answers.get("is_urgent_crisis", {}).get("noul", 0.0))
            
            return JevDecision(
                primary_strategy=strat,
                strategy_explanation=f"基于对方当下语义特征与互动张力，Jev决策模型选定[{strat}]策略以实现最佳互惠沟通。",
                hidden_intent=intent,
                interest_score=interest,
                defense_score=defense,
                power_dynamic=power,
                is_shit_test=shit_test_prob >= 0.5,
                shit_test_prob=round(shit_test_prob, 2),
                is_crisis=crisis_prob >= 0.7,
                emotional_state="平和" if defense < 40 else "有防御/疲惫"
            )

    def _heuristic_mock_decision(self, dialogue: List[MessageItem], user_mbti: str, target_mbti: str) -> JevDecision:
        """根据对话特征进行高精准本地启发式决策模拟"""
        other_texts = [m.text for m in dialogue if not m.is_me]
        recent_other_context = " ".join(other_texts[-3:]) if other_texts else ""
        last_other_text = other_texts[-1] if other_texts else ""
        
        # 关键词与特征规则
        tired_words = ["累", "加班", "烦", "好惨", "难受", "困", "无语", "崩", "散架", "不想动", "连轴转", "头大", "折腾"]
        cold_words = ["哦", "嗯", "好吧", "随便", "呵呵", "没干嘛", "在忙"]
        playful_words = ["哈哈", "笑死", "居然", "你猜", "才不", "逗你", "佩服", "有意思", "笑哭"]
        invite_words = ["想吃", "哪家", "好玩", "推荐", "周末", "放假", "听说", "哪天", "去不"]
        shit_test_words = ["你是不是对谁都这样", "渣男", "海王", "直男", "你很闲", "看你表现", "油嘴滑舌", "套路"]

        is_shit_test = any(w in recent_other_context for w in shit_test_words)
        is_tired = any(w in recent_other_context for w in tired_words)
        is_cold = (any(last_other_text == w or last_other_text.startswith(w) for w in cold_words) or len(last_other_text) <= 2) and not is_tired
        is_invite = any(w in recent_other_context for w in invite_words)
        is_playful = any(w in recent_other_context for w in playful_words)

        if is_shit_test:
            strat = "调侃"
            intent = "试探防御底线"
            interest = 70
            defense = 65
            shit_prob = 0.85
            desc = "对方正在进行言语测试或试探框架，切勿急躁自证解释，适合幽默反拨化解。"
            emotion = "试探/微挑衅"
        elif is_tired:
            strat = "降压"
            intent = "寻求情绪共情"
            interest = 65
            defense = 35
            shit_prob = 0.05
            desc = "对方表达了疲惫与压力，需要的是被看见和舒适陪伴，切忌说教或追问。"
            emotion = "疲惫求安慰"
        elif is_cold:
            strat = "收线"
            intent = "礼貌敷衍回应"
            interest = 35
            defense = 75
            shit_prob = 0.15
            desc = "对方字数极短且缺乏互动延续，当前社交能量不足，应优雅收线，避免追发讨好。"
            emotion = "冷淡疏离"
        elif is_invite:
            strat = "约见"
            intent = "暗示期待带领"
            interest = 82
            defense = 30
            shit_prob = 0.10
            desc = "对方释放了对具体活动/地点的兴趣，窗口期显现，适合发起低压力具体邀约。"
            emotion = "兴致高涨"
        elif is_playful:
            strat = "调侃"
            intent = "轻松日常闲聊"
            interest = 78
            defense = 25
            shit_prob = 0.20
            desc = "对话氛围轻松，情绪价值双向流动，可通过调侃反转增加暧昧张力。"
            emotion = "欢快愉悦"
        else:
            strat = "轻推"
            intent = "轻松日常闲聊"
            interest = 55
            defense = 45
            shit_prob = 0.10
            desc = "日常交流平稳顺畅，可适度从浅层事实话题推向个人生活感受与故事。"
            emotion = "平静平和"

        return JevDecision(
            primary_strategy=strat,
            strategy_explanation=desc,
            hidden_intent=intent,
            interest_score=interest,
            defense_score=defense,
            power_dynamic=55 if interest >= 60 else 40,
            is_shit_test=is_shit_test,
            shit_test_prob=shit_prob,
            is_crisis=False,
            emotional_state=emotion
        )
