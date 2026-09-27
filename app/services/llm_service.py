import json
import logging
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings
from app.models import MessageItem, JevDecision, ReplyOption, BranchPrediction
from app.services.knowledge_service import get_strategy_knowledge

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
        target_mbti: str = ""
    ) -> Dict[str, Any]:
        """
        基于 Jev 系统一的决策结果与狗头军师实战知识，驱动大模型生成高质量的三阶回复与分支预测
        """
        strategy_doc = get_strategy_knowledge(jev_decision.primary_strategy)

        if self.effective_api_key:
            try:
                result = await self._call_llm_api(dialogue, jev_decision, strategy_doc, user_mbti, target_mbti)
                if result:
                    return result
            except Exception as e:
                logger.error(f"大模型调用失败: {e}")
                raise RuntimeError(f"大模型调用失败: {e}，请检查 API Key、Base URL 或网络连接。")
        
        # 仅在未配置 Key 时作为初始引导演示
        return self._fallback_knowledge_replies(jev_decision)

    async def _call_llm_api(
        self,
        dialogue: List[MessageItem],
        jev: JevDecision,
        strategy_doc: str,
        user_mbti: str,
        target_mbti: str
    ) -> Optional[Dict[str, Any]]:
        endpoint = f"{self.effective_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.effective_api_key}",
            "Content-Type": "application/json"
        }

        # 整理上下文
        chat_transcript = "\n".join([f"{'我' if m.is_me else m.sender}: {m.text}" for m in dialogue])

        system_prompt = f"""
你是一位顶尖的恋爱与社交军师，秉承“反PUA、重自尊、互惠真诚、因地制宜”的沟通哲学。
目前系统一决策模型 (Jev) 已对对话进行了毫秒级心智判决：
- 主导策略：【{jev.primary_strategy}】（{jev.strategy_explanation}）
- 对方深层意图：{jev.hidden_intent}
- 好感度：{jev.interest_score}/100，防备心：{jev.defense_score}/100
- 废物测试：{'是' if jev.is_shit_test else '否'} (置信度 {jev.shit_test_prob})
- 用户MBTI: {user_mbti or '未设置'}，对方MBTI: {target_mbti or '未设置'}

{strategy_doc}

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
        target_mbti: str = ""
    ):
        """
        流式生成三阶回复与分支，逐字吐出 Token 并返回最终完整数据
        """
        strategy_doc = get_strategy_knowledge(jev_decision.primary_strategy)
        endpoint = f"{self.effective_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.effective_api_key}",
            "Content-Type": "application/json"
        }
        chat_transcript = "\n".join([f"{'我' if m.is_me else m.sender}: {m.text}" for m in dialogue])

        system_prompt = f"""
你是一位顶尖的恋爱与社交军师，秉承“反PUA、重自尊、互惠真诚、因地制宜”的沟通哲学。
目前系统一决策模型 (Jev) 已对对话进行了毫秒级心智判决：
- 主导策略：【{jev_decision.primary_strategy}】（{jev_decision.strategy_explanation}）
- 对方深层意图：{jev_decision.hidden_intent}
- 好感度：{jev_decision.interest_score}/100，防备心：{jev_decision.defense_score}/100
- 废物测试：{'是' if jev_decision.is_shit_test else '否'} (置信度 {jev_decision.shit_test_prob})
- 用户MBTI: {user_mbti or '未设置'}，对方MBTI: {target_mbti or '未设置'}

{strategy_doc}

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

        # 无 Key 或接口调用异常时的内置高保真打字机流
        fallback_data = self._fallback_knowledge_replies(jev_decision)
        raw_json_str = json.dumps({
            "replies": [r.dict() if hasattr(r, 'dict') else r for r in fallback_data["replies"]],
            "branch": fallback_data["branch"].dict() if hasattr(fallback_data["branch"], 'dict') else fallback_data["branch"]
        }, ensure_ascii=False, indent=2)

        # 模拟打字机流速 (每片 3-8 字符，间隔 15ms)
        chunk_size = 4
        for i in range(0, len(raw_json_str), chunk_size):
            yield raw_json_str[i:i+chunk_size]
            await asyncio.sleep(0.012)

    def _fallback_knowledge_replies(self, jev: JevDecision) -> Dict[str, Any]:
        """离线演示或无 Key 时的狗头军师实战方案"""
        strat = jev.primary_strategy
        
        reply_templates = {
            "降压": [
                ReplyOption(
                    tier="稳健走心版",
                    content="听起来今天真把你耗空了。你先好好歇会儿，不用硬聊，想吐槽或者好点了再找我。",
                    rationale="情绪先行，认同对方的身体与心理耗竭感，主动卸除即时回复的社交负担。",
                    timing="现在直接发送，发完后不要再追加任何消息",
                    tone_tags=["关怀", "无压力", "松弛"]
                ),
                ReplyOption(
                    tier="高情商策略版",
                    content="今天这个世界对你不太客气啊。给你两个选项：吐槽五分钟，或先欠着我一份好心情。",
                    rationale="用轻微的拟人化调侃化解沉重感，提供明确选项将沉重话题转为轻松互动。",
                    timing="现在发送，语气保持幽默",
                    tone_tags=["调侃", "反转", "趣味"]
                ),
                ReplyOption(
                    tier="设立边界版",
                    content="行，那你先忙你的。我正好也去把手头的事情清一清，晚点聊。",
                    rationale="不纠缠不追问，展示自己同样充实独立的生活状态，平衡双方精力投入。",
                    timing="建议间隔 10 分钟后淡定回复",
                    tone_tags=["独立", "利落", "框架"]
                )
            ],
            "调侃": [
                ReplyOption(
                    tier="稳健走心版",
                    content="哈哈你反应挺快啊，看来今天心情很不错，状态满分。",
                    rationale="正面认可对方的幽默感，传递积极正向的情绪共鸣。",
                    timing="秒回或顺着当下热度发",
                    tone_tags=["真诚", "赞许"]
                ),
                ReplyOption(
                    tier="高情商策略版",
                    content="只笑不接球，这轮先算我半胜。坦白交代，刚才是不是偷偷去查回复话术了？",
                    rationale="借对方的反应造梗，制造暧昧的拉扯感与胜负欲，把话题皮球踢回去。",
                    timing="趁热打铁发送",
                    tone_tags=["推拉", "幽默", "暧昧"]
                ),
                ReplyOption(
                    tier="设立边界版",
                    content="这个梗接得勉强及格，给你一次重新组织语言重新赢回来的机会。",
                    rationale="傲娇框架，以玩味的态度保持高位气场。",
                    timing="适度留白后发送",
                    tone_tags=["高位", "有趣", "框架"]
                )
            ]
        }

        default_replies = reply_templates.get(strat, [
            ReplyOption(
                tier="稳健走心版",
                content="刚才看到你分享的这个，我回来琢磨了一下觉得挺有意思，你是怎么开始接触它的？",
                rationale="由浅入深，从对方提到的细节取材，展示好奇心与细致关注。",
                timing="适合在当下发，开启深入话题",
                tone_tags=["倾听", "好奇"]
            ),
            ReplyOption(
                tier="高情商策略版",
                content="发现你平时看着挺沉稳，聊到这个话题居然眼睛会发光，看来我挖掘到隐藏彩蛋了。",
                rationale="将话题由事物引向对方的人格魅力，轻度赞赏不油腻。",
                timing="随心发送",
                tone_tags=["观察敏锐", "赞美"]
            ),
            ReplyOption(
                tier="设立边界版",
                content="光聊这些日常太官方了，不如说说你最近真正觉得有意思的一件事？",
                rationale="打破平淡寒暄，引导双方进入有深度的高质量交流。",
                timing="在对话陷入平淡时发送",
                tone_tags=["真率", "破冰"]
            )
        ])

        branch = BranchPrediction(
            if_positive="对方主动延展新话题或热烈反问时：顺着对方兴趣加深一步，不要急着索取线下承诺。",
            if_neutral="对方只回复礼貌字眼或表情包时：适可而止，停止追加追问，隔天换新场景再开场。",
            if_cooling="对方未回或数小时后简短敷衍时：进入观察窗口，暂停主动发起，给彼此自然呼吸空间。"
        )

        return {
            "replies": default_replies,
            "branch": branch
        }
