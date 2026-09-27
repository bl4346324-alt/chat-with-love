import re
import base64
import json
import logging
from io import BytesIO
from typing import List, Dict, Any, Optional
from PIL import Image
import httpx

from app.config import settings
from app.models import MessageItem

logger = logging.getLogger("ocr_service")

class OCRService:
    def __init__(self, api_key: str = None, base_url: str = None, vision_model: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.vision_model = vision_model

    @property
    def effective_api_key(self):
        return self.api_key or settings.LLM_API_KEY

    @property
    def effective_base_url(self):
        return (self.base_url or settings.LLM_BASE_URL).rstrip("/")

    @property
    def effective_vision_model(self):
        return self.vision_model or settings.VISION_MODEL

    def parse_plain_text(self, raw_text: str, default_other_name: str = "对方") -> List[MessageItem]:
        """
        解析用户粘贴的纯文本聊天记录，支持多种常见微信导出或手动复制格式。
        例如：
        我: 在干嘛呢
        她: 刚到家累死了
        或者纯行交替
        """
        lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]
        messages: List[MessageItem] = []
        
        # 常见前缀正则：我、你、对方、小明、[时间] 昵称: 内容
        prefix_pattern = re.compile(r"^(\[?[0-9: \-\/apmAPM]+\]?\s*)?(我|你|对方|他|她|[a-zA-Z0-9_\u4e00-\u9fa5]{1,10})[:：\s]\s*(.*)$")

        for idx, line in enumerate(lines):
            match = prefix_pattern.match(line)
            if match:
                time_str = match.group(1).strip("[] ") if match.group(1) else None
                speaker = match.group(2).strip()
                content = match.group(3).strip()
                
                is_me = speaker in ["我", "me", "Me", "自己"]
                messages.append(MessageItem(
                    sender="me" if is_me else default_other_name,
                    text=content or line,
                    time=time_str,
                    is_me=is_me
                ))
            else:
                # 若无明确说话人前缀，最后一行通常是对方最新发来的消息，或者简单按单行记录
                is_me = (idx % 2 == 0) if len(lines) > 1 else False
                messages.append(MessageItem(
                    sender="me" if is_me else default_other_name,
                    text=line,
                    time=None,
                    is_me=is_me
                ))

        if not messages and raw_text.strip():
            messages.append(MessageItem(
                sender=default_other_name,
                text=raw_text.strip(),
                is_me=False
            ))
        return messages

    def _local_rapid_ocr(self, image: Image.Image, default_other_name: str = "对方") -> List[MessageItem]:
        """
        使用本地离线 OCR (RapidOCR) 快速提取微信截图中的对话文本、时间与左右气泡归属
        无需外网 API，零 Token 消耗，响应时间通常在 100~200ms
        """
        try:
            import numpy as np
            from rapidocr_onnxruntime import RapidOCR
            if not hasattr(OCRService, "_shared_ocr_engine"):
                OCRService._shared_ocr_engine = RapidOCR()

            img_rgb = image.convert('RGB')
            res, _ = OCRService._shared_ocr_engine(np.array(img_rgb))
            if not res:
                return []

            W, H = image.size
            # 按垂直方向（从上到下）排序
            res = sorted(res, key=lambda x: min(pt[1] for pt in x[0]))

            raw_items = []
            current_time = None
            time_pattern = re.compile(r"^(\d{1,2}:\d{2}|昨天|今天|星期[一二三四五六日]|周[一二三四五六日]|上午|下午)")
            filter_keywords = [
                "按Enter发送", "发送(S)", "微信", "WiFi", "5G", "4G", "中国移动", "中国联通", "中国电信",
                "服务", "更多", "返回", "聊天详情", "发消息", "按住说话", "相册", "拍摄", "视频通话"
            ]

            for item in res:
                box, text, score = item
                text = text.strip()
                if not text or len(text) < 1:
                    continue

                ys = [pt[1] for pt in box]
                xs = [pt[0] for pt in box]
                cy = sum(ys) / len(ys)
                cx = sum(xs) / len(xs)
                min_x = min(xs)
                max_x = max(xs)
                min_y = min(ys)
                max_y = max(ys)
                h = max_y - min_y
                
                # 过滤状态栏顶部的电池/信号/导航等干扰信息
                if cy < H * 0.06 and (any(k in text for k in ["%", "G", "WiFi", "Wi-Fi"]) or text in filter_keywords):
                    continue
                # 过滤底部输入框按键
                if cy > H * 0.93 and any(k in text for k in filter_keywords):
                    continue
                if text in filter_keywords:
                    continue

                # 识别时间标签
                if time_pattern.search(text) and len(text) <= 15:
                    current_time = text
                    continue

                # 微信左右气泡归属判断：
                # 对方（左侧气泡）：左边缘紧贴左侧(min_x通常在10%-30%W)，且右边缘不超过80%W
                # 我方（右侧气泡）：右边缘紧贴右侧(max_x通常在70%-90%W)，且左边缘通常>20%W
                if max_x > W * 0.65 and cx > W * 0.45:
                    is_me = True
                elif min_x < W * 0.35 and cx < W * 0.55:
                    is_me = False
                else:
                    is_me = cx > (W * 0.5)

                raw_items.append({
                    "is_me": is_me,
                    "text": text,
                    "time": current_time,
                    "min_y": min_y,
                    "max_y": max_y,
                    "h": h,
                    "min_x": min_x,
                    "max_x": max_x
                })

            if not raw_items:
                return []

            # 智能合并同气泡多行文字（垂直间距小且同侧归属）
            messages: List[MessageItem] = []
            for item in raw_items:
                if messages and messages[-1].is_me == item["is_me"]:
                    prev_item = raw_items[raw_items.index(item) - 1]
                    vertical_gap = item["min_y"] - prev_item["max_y"]
                    # 若在同一时间窗口且垂直间距极小，视为同一气泡的换行
                    if vertical_gap < item["h"] * 1.5:
                        messages[-1].text += "\n" + item["text"]
                        continue

                messages.append(MessageItem(
                    sender="me" if item["is_me"] else default_other_name,
                    text=item["text"],
                    time=item["time"],
                    is_me=item["is_me"]
                ))

            return messages
        except Exception as e:
            logger.warning(f"本地离线 OCR 识别异常: {e}")
            return []

    async def parse_screenshot(self, image_bytes: bytes, default_other_name: str = "对方") -> List[MessageItem]:
        """
        解析用户粘贴或上传的微信聊天截图。
        优先采用本地离线 OCR (RapidOCR) 零 Token 极速解析；
        若未识别到文字且配置了外部视觉 API，则回退至云端多模态视觉模型。
        """
        try:
            image = Image.open(BytesIO(image_bytes))
            max_size = 1400
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        except Exception as e:
            logger.error(f"图片打开失败: {e}")
            raise RuntimeError(f"图片格式无法解析: {e}")

        # 1. 优先尝试本地离线 OCR 解析 (0 Token，完全兼容 DeepSeek 纯文本模型)
        local_messages = self._local_rapid_ocr(image, default_other_name=default_other_name)
        if local_messages and len(local_messages) > 0:
            logger.info(f"本地离线 OCR 成功提取到 {len(local_messages)} 条对话")
            return local_messages

        # 2. 如果本地未能识别到文字，且配置了非 DeepSeek 的视觉模型，则尝试云端视觉大模型
        if self.effective_api_key and "deepseek.com" not in self.effective_base_url.lower():
            try:
                buffered = BytesIO()
                image.save(buffered, format="JPEG", quality=85)
                compressed_bytes = buffered.getvalue()
                parsed_messages = await self._call_vision_api(compressed_bytes, default_other_name)
                if parsed_messages:
                    return parsed_messages
            except Exception as e:
                logger.error(f"视觉大模型 OCR 识别失败: {e}")

        # 3. 如果本地 OCR 未能提取到气泡，给出明确指引
        raise RuntimeError(
            "未能从截图中清晰识别到聊天气泡文字。\n"
            "建议：可在左侧切换到【文本记录输入】直接复制或输入对话文字，秒级体验 Jev + DeepSeek 的高情商实战回复！"
        )

    async def _call_vision_api(self, image_bytes: bytes, default_other_name: str) -> Optional[List[MessageItem]]:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        prompt = """
你是一位顶级的聊天记录多模态解析专家。请观察这张微信/社交软件的聊天截图，严格按从上到下、时间先后的顺序提取对话。
规则：
1. 区分说话人：通常绿色气泡或屏幕右侧气泡为“我”（sender: 'me'，is_me: true）；白色气泡或屏幕左侧气泡为“对方”（sender: 'other'，is_me: false）。
2. 如有时间戳标签，提取为 time 字段（例如 '21:04'）。
3. 必须只输出纯 JSON 数组，严禁包含 markdown 代码块或其它解释文字。格式如下：
[
  {"sender": "me", "text": "...", "time": "21:00", "is_me": true},
  {"sender": "other", "text": "...", "time": "21:02", "is_me": false}
]
"""
        payload = {
            "model": self.effective_vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1500,
            "temperature": 0.1
        }

        endpoint = f"{self.effective_base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.effective_api_key}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(endpoint, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            # 清理可能的 markdown 标记
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            
            raw_list = json.loads(content.strip())
            results: List[MessageItem] = []
            for item in raw_list:
                results.append(MessageItem(
                    sender="me" if item.get("is_me", False) else default_other_name,
                    text=item.get("text", ""),
                    time=item.get("time"),
                    is_me=item.get("is_me", False)
                ))
            return results
