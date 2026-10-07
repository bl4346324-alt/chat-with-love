import json
import logging
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import MessageItem, JevDecision, ReplyOption, BranchPrediction, SkillInsight
from app.services.knowledge_service import get_strategy_knowledge
from app.services.skill_service import skill_service

logger = logging.getLogger("llm_service")

class LLMService:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    @property
    def effective_api_key(self):
        return self.api_key or settings.LLM_API_KEY

    @property
    def effective_base_url(self):
        return (self.base_url or settings.LLM_BASE_URL).rstrip("/")

    @property
    def effective_model(self):
        return self.model or settings.LLM_MODEL

    async def generate_replies(
        self,
        dialogue: List[MessageItem],
        jev_decision: JevDecision,
        user_mbti: str = "",
        target_mbti: str = "",
        skill_insight: Optional[SkillInsight] = None
    ) -> Dict[str, Any]:
        """
        基于 Jev 系统一决策结果与 GitHub 恋爱 Skill（情圣 × 狗头军师），驱动大模型生成三阶话术
        """
        if skill_insight is None:
            skill_insight = skill_service.analyze_love_dialogue(dialogue, user_mbti, target_mbti)

        strategy_doc = get_strategy_knowledge(jev_decision.primary_strategy)
        skill_prompt = skill_service.build_skill_prompt_injection(
            skill_insight, jev_decision.primary_strategy, user_mbti, target_mbti
        )

        if self.effective_api_key:
            try:
                result = await self._call_llm_api(
                    dialogue, jev_decision, strategy_doc, skill_prompt, user_mbti, target_mbti
                )
                if result:
                    return result
            except Exception as e:
                logger.warning(f"大模型 API 调用受阻 ({e})，转入情圣与狗头军师实战知识库生成方案")
        
        # 仅在未配置 Key 或接口调用异常时，使用情圣与狗头军师实战知识方案
        latest_text = dialogue[-1].text if dialogue else ""
        return skill_service.get_fallback_replies_for_stage(skill_insight, jev_decision.primary_strategy, latest_text)

    async def _call_llm_api(
        self,
        dialogue: List[MessageItem],
        jev: JevDecision,
        strategy_doc: str,
        skill_prompt: str,
        user_mbti: str,
        target_mbti: str
    ) -> Optional[Dict[str, Any]]:
        endpoint = f"{self.effective_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.effective_api_key}",
            "Content-Type": "application/json"
        }

        chat_transcript = "\n".join([f"{'我' if m.is_me else m.sender}: {m.text}" for m in dialogue])

        system_prompt = f"""
你是一位顶尖的恋爱与社交军师，秉承《情圣》与《狗头军师》的沟通哲学：“兄弟视角、反PUA、重自尊、互惠真诚、因地制宜”。
系统一心智模型判决如下：
- 主导策略：【{jev.primary_strategy}】（{jev.strategy_explanation}）
- 对方深层意图：{jev.hidden_intent}
- 好感度：{jev.interest_score}/100，防备心：{jev.defense_score}/100
- 废物测试：{'是' if jev.is_shit_test else '否'} (置信度 {jev.shit_test_prob})
- 用户MBTI: {user_mbti or '未设置'}，对方MBTI: {target_mbti or '未设置'}

{strategy_doc}

{skill_prompt}

请严格遵守：
1. 一句话不要堆叠太多动作（不要同时安慰又邀约又追问）。
2. 口吻要自然接地气，绝不油腻、绝不当舔狗、绝不发长篇大论小作文。
3. 按照 JSON 格式输出 3 种不同风格的回复成品及后续分支。
格式规范：
{{
  "replies": [
    {{
      "tier": "稳健走心版",
      "content": "具体的回复话术，可直接发送",
      "rationale": "背后的心理逻辑与情绪承接理由",
      "timing": "发送时机建议（例如：现在直接发 / 间隔15-30分钟）",
      "tone_tags": ["真诚", "舒适", "无压力"]
    }},
    {{
      "tier": "高情商策略版",
      "content": "带轻微调侃、推拉或张力的话术",
      "rationale": "制造张力与幽默感的逻辑",
      "timing": "发送时机建议",
      "tone_tags": ["幽默", "推拉", "松弛感"]
    }},
    {{
      "tier": "设立边界版",
      "content": "守住框架、不过度讨好、体面收尾的话术",
      "rationale": "守住个人时间与自尊的考量",
      "timing": "发送时机建议",
      "tone_tags": ["自尊", "框架", "界限"]
    }}
  ],
  "branch": {{
    "if_positive": "如果对方热烈回应或顺着接梗，下一步该如何推进",
    "if_neutral": "如果对方仅回复'哈哈'或敷衍客套，如何优雅暂停",
    "if_cooling": "如果对方未回或冷淡回撤，接下来的观察窗口与应对"
  }}
}}
"""

        user_content = f"以下是完整的对话记录：\n{chat_transcript}\n请分析并生成输出。"

        payload = {
            "model": self.effective_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

    async def generate_replies_stream(
        self,
        dialogue: List[MessageItem],
        jev_decision: JevDecision,
        user_mbti: str = "",
        target_mbti: str = "",
        skill_insight: Optional[SkillInsight] = None
    ):
        """
        流式生成三阶回复与分支，逐字吐出 Token 并返回最终完整数据
        """
        if skill_insight is None:
            skill_insight = skill_service.analyze_love_dialogue(dialogue, user_mbti, target_mbti)

        strategy_doc = get_strategy_knowledge(jev_decision.primary_strategy)
        skill_prompt = skill_service.build_skill_prompt_injection(
            skill_insight, jev_decision.primary_strategy, user_mbti, target_mbti
        )

        endpoint = f"{self.effective_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.effective_api_key}",
            "Content-Type": "application/json"
        }
        chat_transcript = "\n".join([f"{'我' if m.is_me else m.sender}: {m.text}" for m in dialogue])

        system_prompt = f"""
你是一位顶尖的恋爱与社交军师，秉承《情圣》与《狗头军师》的沟通哲学：“兄弟视角、反PUA、重自尊、互惠真诚、因地制宜”。
系统一心智模型判决如下：
- 主导策略：【{jev_decision.primary_strategy}】（{jev_decision.strategy_explanation}）
- 对方深层意图：{jev_decision.hidden_intent}
- 好感度：{jev_decision.interest_score}/100，防备心：{jev_decision.defense_score}/100
- 废物测试：{'是' if jev_decision.is_shit_test else '否'} (置信度 {jev_decision.shit_test_prob})
- 用户MBTI: {user_mbti or '未设置'}，对方MBTI: {target_mbti or '未设置'}

{strategy_doc}

{skill_prompt}

请严格遵守：
1. 一句话不要堆叠太多动作（不要同时安慰又邀约又追问）。
2. 口吻要自然接地气，严禁油腻、土味情话和高高在上的说教。
3. 按照 JSON 格式输出 3 种不同风格的回复成品及后续分支。
格式规范：
{{
  "replies": [
    {{
      "tier": "稳健走心版",
      "content": "具体的回复话术，可直接发送",
      "rationale": "背后的心理逻辑与情绪承接理由",
      "timing": "发送时机建议",
      "tone_tags": ["真诚", "舒适"]
    }},
    {{
      "tier": "高情商策略版",
      "content": "带轻微调侃、推拉或张力的话术",
      "rationale": "制造张力与幽默感的逻辑",
      "timing": "发送时机建议",
      "tone_tags": ["幽默", "推拉"]
    }},
    {{
      "tier": "设立边界版",
      "content": "守住框架、不过度讨好、体面收尾的话术",
      "rationale": "守住个人时间与自尊的考量",
      "timing": "发送时机建议",
      "tone_tags": ["自尊", "框架"]
    }}
  ],
  "branch": {{
    "if_positive": "对方积极接梗时的建议",
    "if_neutral": "对方礼貌含糊时的应对",
    "if_cooling": "对方冷淡未回时的观察窗口"
  }}
}}
"""
        payload = {
            "model": self.effective_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"以下是完整的对话记录：\n{chat_transcript}\n请分析并生成输出。"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
            "stream": True
        }

        if self.effective_api_key:
            try:
                async with httpx.AsyncClient(timeout=40.0) as client:
                    async with client.stream("POST", endpoint, json=payload, headers=headers) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    chunk = json.loads(data_str)
                                    delta = chunk["choices"][0]["delta"].get("content", "")
                                    if delta:
                                        yield delta
                                except Exception:
                                    pass
                return
            except Exception as e:
                logger.warning(f"大模型流式生成异常，转入内置军师实战知识流: {e}")

        # 无 Key 或接口调用异常时的内置高保真打字机流（基于情圣 & 狗头军师实战库）
        latest_text = dialogue[-1].text if dialogue else ""
        fallback_data = skill_service.get_fallback_replies_for_stage(
            skill_insight, jev_decision.primary_strategy, latest_text
        )
        raw_json_str = json.dumps({
            "replies": [r.dict() if hasattr(r, 'dict') else r for r in fallback_data["replies"]],
            "branch": fallback_data["branch"].dict() if hasattr(fallback_data["branch"], 'dict') else fallback_data["branch"]
        }, ensure_ascii=False, indent=2)

        # 模拟打字机流速 (每片 3-8 字符，间隔 15ms)
        chunk_size = 4
        for i in range(0, len(raw_json_str), chunk_size):
            yield raw_json_str[i:i+chunk_size]
            await asyncio.sleep(0.012)
