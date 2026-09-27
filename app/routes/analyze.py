import time
import base64
import json
import re
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse

from app.models import (
    TextAnalysisRequest, StreamAnalysisRequest, AnalysisResponse,
    MessageItem, JevDecision, ReplyOption, BranchPrediction
)
from app.services.ocr_service import OCRService
from app.services.jev_service import JevService
from app.services.llm_service import LLMService
from app.database import save_analysis
from app.config import settings

logger = logging.getLogger("analyze_router")
router = APIRouter(prefix="/api/analyze", tags=["analyze"])

ocr_service = OCRService()
jev_service = JevService()
llm_service = LLMService()

def parse_partial_replies(text: str):
    """从流式 JSON 文本中提取已生成的三阶话术与分支"""
    replies = []
    tiers = ['稳健走心版', '高情商策略版', '设立边界版']
    
    for tier in tiers:
        if tier in text:
            tier_idx = text.find(f'"{tier}"')
            if tier_idx == -1:
                tier_idx = text.find(tier)
            obj_start = text.rfind('{', 0, tier_idx)
            if obj_start == -1:
                obj_start = tier_idx
            
            next_start = len(text)
            for other_tier in tiers:
                if other_tier != tier and other_tier in text:
                    oi = text.find(f'"{other_tier}"')
                    if oi > tier_idx and oi < next_start:
                        next_start = oi
            branch_idx = text.find('"branch"')
            if branch_idx > tier_idx and branch_idx < next_start:
                next_start = branch_idx
                
            block = text[obj_start:next_start]
            
            content_m = re.search(r'"content"\s*:\s*"([^"]*)', block)
            content = content_m.group(1).replace('\\n', '\n').replace('\\"', '"') if content_m else ''
            
            rationale_m = re.search(r'"rationale"\s*:\s*"([^"]*)', block)
            rationale = rationale_m.group(1).replace('\\n', '\n').replace('\\"', '"') if rationale_m else ''
            
            timing_m = re.search(r'"timing"\s*:\s*"([^"]*)', block)
            timing = timing_m.group(1).replace('\\n', '\n').replace('\\"', '"') if timing_m else ''
            
            replies.append({
                'tier': tier,
                'content': content,
                'rationale': rationale,
                'timing': timing
            })
            
    branch = {}
    pos_m = re.search(r'"if_positive"\s*:\s*"([^"]*)', text)
    if pos_m:
        branch['if_positive'] = pos_m.group(1).replace('\\n', '\n').replace('\\"', '"')
    neu_m = re.search(r'"if_neutral"\s*:\s*"([^"]*)', text)
    if neu_m:
        branch['if_neutral'] = neu_m.group(1).replace('\\n', '\n').replace('\\"', '"')
    neg_m = re.search(r'"if_cooling"\s*:\s*"([^"]*)', text)
    if neg_m:
        branch['if_cooling'] = neg_m.group(1).replace('\\n', '\n').replace('\\"', '"')
        
    return replies, branch


@router.post("/text", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    start_time = time.time()
    try:
        # 1. 结构化文本解析
        dialogue = ocr_service.parse_plain_text(request.text, default_other_name=request.target_alias or "对方")
        if not dialogue:
            raise HTTPException(status_code=400, detail="未解析到有效对话内容，请检查输入")

        # 2. Jev 系统一毫秒级决策 (判断策略、心理意图、好感度、防备心)
        jev_decision = await jev_service.decide_dialogue_state(
            dialogue=dialogue,
            user_mbti=request.user_mbti or "",
            target_mbti=request.target_mbti or ""
        )

        # 3. 大模型系统二高情商话术生成
        generation_res = await llm_service.generate_replies(
            dialogue=dialogue,
            jev_decision=jev_decision,
            user_mbti=request.user_mbti or "",
            target_mbti=request.target_mbti or ""
        )

        replies = [ReplyOption(**r) if isinstance(r, dict) else r for r in generation_res["replies"]]
        branch = BranchPrediction(**generation_res["branch"]) if isinstance(generation_res["branch"], dict) else generation_res["branch"]

        latency = int((time.time() - start_time) * 1000)

        # 4. 存储分析结果到本地 SQLite
        save_analysis(
            source_type="text",
            raw_input=request.text,
            dialogue_parsed=[d.dict() for d in dialogue],
            jev_result=jev_decision.dict(),
            llm_result={"replies": [r.dict() for r in replies], "branch": branch.dict()}
        )

        return AnalysisResponse(
            success=True,
            dialogue=dialogue,
            jev=jev_decision,
            replies=replies,
            branch=branch,
            latency_ms=latency,
            is_mock=not bool(settings.JEV_API_KEY)
        )
    except Exception as e:
        return AnalysisResponse(
            success=False,
            dialogue=[],
            jev=JevDecision(
                primary_strategy="承接",
                strategy_explanation="分析发生异常",
                hidden_intent="未知",
                interest_score=50,
                defense_score=50
            ),
            replies=[],
            branch=BranchPrediction(if_positive="", if_neutral="", if_cooling=""),
            error=str(e),
            latency_ms=int((time.time() - start_time) * 1000)
        )

@router.post("/screenshot", response_model=AnalysisResponse)
async def analyze_screenshot(
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    target_alias: Optional[str] = Form("对方"),
    user_mbti: Optional[str] = Form(""),
    target_mbti: Optional[str] = Form("")
):
    start_time = time.time()
    try:
        # 获取图片数据
        image_bytes = None
        if file:
            image_bytes = await file.read()
        elif image_base64:
            # 剥离可能的 base64 前缀
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            image_bytes = base64.b64decode(image_base64)
        
        if not image_bytes:
            raise HTTPException(status_code=400, detail="未接收到图片数据")

        # 1. 微信截图视觉解析 (区分左右气泡与时间)
        dialogue = await ocr_service.parse_screenshot(image_bytes, default_other_name=target_alias or "对方")

        # 2. Jev 系统一毫秒级决策
        jev_decision = await jev_service.decide_dialogue_state(
            dialogue=dialogue,
            user_mbti=user_mbti or "",
            target_mbti=target_mbti or ""
        )

        # 3. 大模型系统二生成
        generation_res = await llm_service.generate_replies(
            dialogue=dialogue,
            jev_decision=jev_decision,
            user_mbti=user_mbti or "",
            target_mbti=target_mbti or ""
        )

        replies = [ReplyOption(**r) if isinstance(r, dict) else r for r in generation_res["replies"]]
        branch = BranchPrediction(**generation_res["branch"]) if isinstance(generation_res["branch"], dict) else generation_res["branch"]

        latency = int((time.time() - start_time) * 1000)

        # 4. 存储分析结果到本地 SQLite
        save_analysis(
            source_type="screenshot",
            raw_input="[图片上传/粘贴截图]",
            dialogue_parsed=[d.dict() for d in dialogue],
            jev_result=jev_decision.dict(),
            llm_result={"replies": [r.dict() for r in replies], "branch": branch.dict()}
        )

        return AnalysisResponse(
            success=True,
            dialogue=dialogue,
            jev=jev_decision,
            replies=replies,
            branch=branch,
            latency_ms=latency,
            is_mock=not bool(settings.JEV_API_KEY)
        )
    except Exception as e:
        return AnalysisResponse(
            success=False,
            dialogue=[],
            jev=JevDecision(
                primary_strategy="承接",
                strategy_explanation="截图分析发生异常",
                hidden_intent="未知",
                interest_score=50,
                defense_score=50
            ),
            replies=[],
            branch=BranchPrediction(if_positive="", if_neutral="", if_cooling=""),
            error=str(e),
            latency_ms=int((time.time() - start_time) * 1000)
        )

@router.post("/stream")
async def analyze_stream(request: StreamAnalysisRequest):
    """
    流式打字机 0.2 秒极速反馈 SSE 接口：
    1. 100~200ms 内完成离线本地 OCR / 文本解析，立即推送 event: dialogue
    2. ~200ms Jev 系统一毫秒级决策完成，立即推送 event: jev (亮起策略标签与三维心理雷达)
    3. 大模型系统二逐字流式打字生成，推送 event: stream_delta (三阶话术卡片打字机联动)
    4. 生成完毕落库并推送 event: done
    """
    async def event_generator():
        start_time = time.time()
        try:
            # 1. 对话记录解析
            dialogue: List[MessageItem] = []
            if request.image_base64:
                raw_b64 = request.image_base64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",")[1]
                image_bytes = base64.b64decode(raw_b64)
                dialogue = await ocr_service.parse_screenshot(image_bytes, default_other_name=request.target_alias or "对方")
            elif request.text:
                dialogue = ocr_service.parse_plain_text(request.text, default_other_name=request.target_alias or "对方")

            if not dialogue:
                yield f"event: error\ndata: {json.dumps({'error': '未解析到有效对话内容，请检查输入或截图'}, ensure_ascii=False)}\n\n"
                return

            ocr_latency = int((time.time() - start_time) * 1000)
            yield f"event: dialogue\ndata: {json.dumps({'dialogue': [d.dict() for d in dialogue], 'count': len(dialogue), 'latency_ms': ocr_latency}, ensure_ascii=False)}\n\n"

            # 2. Jev 系统一毫秒级心智决策 (0.2s 极速反馈)
            jev_start = time.time()
            jev_decision = await jev_service.decide_dialogue_state(
                dialogue=dialogue,
                user_mbti=request.user_mbti or "",
                target_mbti=request.target_mbti or ""
            )
            total_jev_latency = int((time.time() - start_time) * 1000)
            yield f"event: jev\ndata: {json.dumps({'jev': jev_decision.dict(), 'latency_ms': total_jev_latency}, ensure_ascii=False)}\n\n"

            # 3. 大模型系统二实战话术打字机流式生成
            accumulated_text = ""
            async for chunk in llm_service.generate_replies_stream(
                dialogue=dialogue,
                jev_decision=jev_decision,
                user_mbti=request.user_mbti or "",
                target_mbti=request.target_mbti or ""
            ):
                accumulated_text += chunk
                partial_replies, partial_branch = parse_partial_replies(accumulated_text)
                yield f"event: stream_delta\ndata: {json.dumps({'delta': chunk, 'replies': partial_replies, 'branch': partial_branch}, ensure_ascii=False)}\n\n"

            # 4. 完成解析与持久化存储
            final_replies = []
            final_branch = {}
            try:
                parsed_json = json.loads(accumulated_text.strip())
                final_replies = parsed_json.get("replies", [])
                final_branch = parsed_json.get("branch", {})
            except Exception:
                final_replies, final_branch = parse_partial_replies(accumulated_text)

            replies_objs = [ReplyOption(**r) if isinstance(r, dict) else r for r in final_replies]
            branch_obj = BranchPrediction(**final_branch) if isinstance(final_branch, dict) and "if_positive" in final_branch else BranchPrediction(if_positive="", if_neutral="", if_cooling="")

            save_analysis(
                source_type="screenshot" if request.image_base64 else "text",
                raw_input=request.text or "[截图上传/粘贴]",
                dialogue_parsed=[d.dict() for d in dialogue],
                jev_result=jev_decision.dict(),
                llm_result={"replies": [r.dict() for r in replies_objs], "branch": branch_obj.dict()}
            )

            total_latency = int((time.time() - start_time) * 1000)
            done_payload = {
                "success": True,
                "dialogue": [d.dict() for d in dialogue],
                "jev": jev_decision.dict(),
                "replies": [r.dict() for r in replies_objs],
                "branch": branch_obj.dict(),
                "latency_ms": total_latency,
                "is_mock": not bool(settings.JEV_API_KEY)
            }
            yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"流式分析管道异常: {e}", exc_info=True)
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

