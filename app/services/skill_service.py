"""
情圣 (QingSheng) × 狗头军师 (GouTouJunShi) 恋爱与社交 Skill 核心驱动引擎
从 GitHub 开源项目装载，并在输入聊天内容后提供全自动调用、阶段诊断、信号解码与高情商策略支持。
- GitHub 来源 1: https://github.com/tomwong001/qingsheng-skill (情圣)
- GitHub 来源 2: https://github.com/shengjidaguai-china/goutoujunshi (狗头军师)
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.models import MessageItem, SkillInsight

logger = logging.getLogger("skill_service")

# 7 阶段推进定义 (源自情圣 skill/references/stages.md)
LOVE_STAGES = [
    {
        "stage": 1,
        "name": "阶段1：开场破冰",
        "title": "破冰初识",
        "goal": "建立可聊天的连接，消除陌生感与防御心，让对方愿意轻松回复",
        "tactics": ["冷读切入", "生活细节共鸣", "无压力开放提问", "避免查户口"]
    },
    {
        "stage": 2,
        "name": "阶段2：建立好感",
        "title": "好感舒适",
        "goal": "从普通朋友到有意思的人，展现真实生活与品味，激发彼此好奇心",
        "tactics": ["情绪共情", "生活细节分享", "软性DHV展示", "故事代替说教"]
    },
    {
        "stage": 3,
        "name": "阶段3：关系升温",
        "title": "升温张力",
        "goal": "打破客套平淡，通过拉扯与适度调侃制造情绪张力、专属感与暧昧心动",
        "tactics": ["拉扯升温", "幽默曲解", "制造专属梗", "高位离场"]
    },
    {
        "stage": 4,
        "name": "阶段4：邀约见面",
        "title": "邀约推进",
        "goal": "通过邀约三步法（埋线->模糊邀约->确定具体邀约），低压力落地现实接触",
        "tactics": ["场景埋线", "模糊试探", "二选一具体邀约", "留体面出口"]
    },
    {
        "stage": 5,
        "name": "阶段5：约会实战",
        "title": "约会互动",
        "goal": "线下真实接触、自然松弛互动，建立面对面真实信任与情绪升温",
        "tactics": ["自然互动", "共情倾听", "轻度肢体社交校准", "事后轻松复盘"]
    },
    {
        "stage": 6,
        "name": "阶段6：亲密升级",
        "title": "深度亲密",
        "goal": "深层脆弱坦露、深度价值观契合与情感归属，确认彼此心意",
        "tactics": ["深度自我暴露", "情感接纳", "边界确认", "专注当下陪伴"]
    },
    {
        "stage": 7,
        "name": "阶段7：确立关系",
        "title": "确立承诺",
        "goal": "水到渠成、双向奔赴，正式确认恋爱排他性关系与未来规划",
        "tactics": ["真诚表达心意", "排他性确认", "尊重对方节奏", "明确长期承诺"]
    }
]

class SkillService:
    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.qingsheng_dir = self.root_dir / "skills" / "qingsheng-skill"
        self.goutoujunshi_dir = self.root_dir / "goutoujunshi-repo"
        self.installed_skills = self._detect_installed_skills()

    def _detect_installed_skills(self) -> List[Dict[str, Any]]:
        """检测并读取项目中安装的恋爱 Skill"""
        skills = []
        
        # 1. 情圣 Skill
        if self.qingsheng_dir.exists():
            version_file = self.qingsheng_dir / "VERSION"
            version = version_file.read_text(encoding="utf-8").strip() if version_file.exists() else "v6.0"
            skills.append({
                "id": "qingsheng",
                "name": "情圣 (QingSheng)",
                "version": version,
                "author": "tomwong001",
                "repo": "https://github.com/tomwong001/qingsheng-skill",
                "description": "中文社交与恋爱私教（7阶段推进系统、IOI/IOD信号雷达、邀约三步法、拉扯与废物测试破解）",
                "status": "active"
            })
        
        # 2. 狗头军师 Skill
        if self.goutoujunshi_dir.exists():
            skills.append({
                "id": "goutoujunshi",
                "name": "狗头军师 (GouTouJunShi)",
                "version": "v1.0",
                "author": "shengjidaguai-china",
                "repo": "https://github.com/shengjidaguai-china/goutoujunshi",
                "description": "恋爱军师与情绪支持系统（135+篇实战知识库、7大核心策略路由器、反PUA自尊伦理底线）",
                "status": "active"
            })
        
        return skills

    def get_installed_skills(self) -> List[Dict[str, Any]]:
        return self.installed_skills

    def analyze_love_dialogue(
        self,
        dialogue: List[MessageItem],
        user_mbti: str = "",
        target_mbti: str = ""
    ) -> SkillInsight:
        """
        深度调用情圣与狗头军师 Skill：
        在用户输入聊天内容后，自动完成恋爱阶段研判、信号（IOI/IOD/测试）解码，并推荐最适战术。
        """
        if not dialogue:
            return SkillInsight(
                active_skills=["情圣 (QingSheng v6.0)", "狗头军师 (GouTouJunShi)"],
                stage_number=1,
                stage_name="阶段1：开场破冰",
                stage_goal="建立初识沟通线索",
                signal_type="中立日常",
                signal_detail="等待对话输入",
                tactics_suggested=["冷读切入", "开放话题"]
            )

        # 提取双方文本
        other_msgs = [m.text for m in dialogue if not m.is_me]
        my_msgs = [m.text for m in dialogue if m.is_me]
        all_text = " ".join([m.text for m in dialogue])
        latest_other = other_msgs[-1] if other_msgs else (dialogue[-1].text if dialogue else "")

        # 1. 信号检测 (IOI / IOD / 废物测试)
        signal_type = "中立日常"
        signal_detail = "当前互动处于平稳日常沟通，未出现极端防御或强烈好感。"
        
        # 废物测试识别特征
        shit_test_keywords = ["海王", "渣男", "会撩", "套路", "对所有女生", "花心", "哄女孩", "油嘴滑舌", "你猜", "直男"]
        is_shit_test = any(k in latest_other for k in shit_test_keywords) or ("是不是" in latest_other and ("都这样" in latest_other or "撩" in latest_other))
        
        # IOD 信号特征 (冷淡、敷衍、回避)
        iod_keywords = ["哦", "嗯", "好吧", "随便", "呵呵", "没空", "以后再说", "不想聊", "去洗澡了", "忙着呢"]
        is_iod = False
        if len(latest_other) <= 4 and any(k in latest_other for k in ["哦", "嗯", "好吧", "随便"]):
            is_iod = True
        elif any(k in latest_other for k in iod_keywords):
            is_iod = True

        # IOI 信号特征 (主动倾诉、延展话题、分享脆弱、好奇提问、撒娇/接梗)
        ioi_keywords = ["哈哈", "别提了", "累死", "真的吗", "你呢", "想去", "好看吗", "推荐", "好吃", "什么时候", "发我看看", "😭", "🥺", "😏", "🙈"]
        is_ioi = any(k in latest_other for k in ioi_keywords) or ("？" in latest_other or "?" in latest_other)

        if is_shit_test:
            signal_type = "废物测试 (设防试探)"
            signal_detail = "对方正在用挑衅或调侃的方式试探你的心理稳定性与框架，重点在于观察你是否慌张或讨好自证。"
        elif is_iod:
            signal_type = "IOD 降温信号 (轻度设防)"
            signal_detail = "对方回复简短或字数较少，可能由于现实忙碌、精力受限或当前互动缺乏吸引力，需主动卸压。"
        elif is_ioi:
            signal_type = "IOI 兴趣信号 (主动投入)"
            signal_detail = "对方愿意分享个人情绪、反问你的生活或主动延展话题，释放出积极的互动接纳度与信任感。"

        # 2. 阶段判定 (1 - 7 阶段)
        stage_num = 2  # 默认好感建立阶段
        
        # 阶段4: 邀约特征
        invite_keywords = ["周末", "周六", "周日", "约", "出来", "见面", "咖啡", "吃饭", "电影", "那家店", "探店", "逛逛", "展"]
        # 阶段3: 升温与调侃特征
        flirt_keywords = ["哈哈", "逗你", "好玩", "嫌弃", "帅", "可爱", "笨", "打你", "夸我", "想得美", "套路"]
        # 阶段6/7: 深层亲密与承诺
        deep_keywords = ["未来", "在一起", "男/女朋友", "谈恋爱", "独一无二", "安全感", "心动", "吃醋"]

        if any(k in all_text for k in deep_keywords) and len(dialogue) >= 6:
            stage_num = 6
        elif any(k in all_text for k in invite_keywords) or "一起去" in all_text:
            stage_num = 4
        elif is_shit_test or any(k in all_text for k in flirt_keywords) or len(dialogue) >= 5:
            stage_num = 3
        elif len(dialogue) <= 2 and ("你好" in all_text or "刚加" in all_text or "加上" in all_text):
            stage_num = 1
        else:
            stage_num = 2

        # 匹配对应阶段定义
        selected_stage = next((s for s in LOVE_STAGES if s["stage"] == stage_num), LOVE_STAGES[1])
        
        # 动态组合推荐战术
        tactics = list(selected_stage["tactics"])
        if is_shit_test:
            tactics = ["幽默曲解", "框架反转", "绝不自证辩解"] + tactics[:1]
        elif is_iod:
            tactics = ["降压给台阶", "高位离场", "停止连发小作文"] + tactics[:1]
        elif is_ioi:
            tactics = ["接住情绪", "适度推拉", "埋线邀约"] + tactics[:1]

        active_names = [s["name"] for s in self.installed_skills]
        if not active_names:
            active_names = ["情圣 (QingSheng v6.0)", "狗头军师 (GouTouJunShi)"]

        return SkillInsight(
            active_skills=active_names,
            stage_number=stage_num,
            stage_name=selected_stage["name"],
            stage_goal=selected_stage["goal"],
            signal_type=signal_type,
            signal_detail=signal_detail,
            tactics_suggested=tactics
        )

    def build_skill_prompt_injection(
        self,
        insight: SkillInsight,
        primary_strategy: str,
        user_mbti: str = "",
        target_mbti: str = ""
    ) -> str:
        """
        构建深度融合 GitHub《情圣》与《狗头军师》精髓的大模型 Prompt 强化指令
        """
        tactics_str = "、".join([f"#{t}" for t in insight.tactics_suggested])
        
        return f"""
【已装载 GitHub 恋爱技能库】：情圣 (QingSheng) × 狗头军师 (GouTouJunShi)
【当前关系阶段诊断】：{insight.stage_name}（核心目标：{insight.stage_goal}）
【互动信号心智解码】：{insight.signal_type} —— {insight.signal_detail}
【推荐实战技法矩阵】：{tactics_str}

【情圣与军师实操戒律】：
1. 像真实的高情商好兄弟一样出谋划策，禁止“查户口追问机器”和“客服机器人”腔调。
2. 话术以 1~2 句话为主，简练有力接地气，绝不发冗长小作文，给对方留出自由接球空间。
3. 稳健走心版：真诚共情、安全舒服、卸除防御；
4. 高情商策略版：温暖幽默、轻微推拉、带出心动与情绪张力；
5. 设立边界版：守住个人框架与自尊，不卑不亢，不过度讨好。
"""

    def get_fallback_replies_for_stage(
        self,
        insight: SkillInsight,
        strategy: str,
        latest_message: str = ""
    ) -> Dict[str, Any]:
        """
        离线/未配 Key 时的情圣高保真实战话术库（直取自情圣实战案例库与 stages.md）
        """
        stage = insight.stage_number
        signal = insight.signal_type
        
        # 1. 废物测试场景
        if "废物测试" in signal or "海王" in latest_message or "会说话" in latest_message:
            return {
                "replies": [
                    {
                        "tier": "稳健走心版",
                        "content": "哪有什么套路，不过是遇到聊得来的人，愿意多花点心思罢了。",
                        "rationale": "诚恳真挚承接，不慌张不掩饰，以坦诚化解防御。",
                        "timing": "间隔 5-10 分钟发送，保持沉稳",
                        "tone_tags": ["真诚", "坦荡", "舒适"]
                    },
                    {
                        "tier": "高情商策略版",
                        "content": "坦白交代，刚刚是不是偷偷去查话术宝典来考我了？那我这轮答卷能打几分？😏",
                        "rationale": "情圣经典反弹与角色扮演，反客为主让对方成为评分者，制造调皮张力。",
                        "timing": "即刻回复，展现极佳的临场松弛感",
                        "tone_tags": ["幽默", "推拉", "框架掌控"]
                    },
                    {
                        "tier": "设立边界版",
                        "content": "别给我戴高帽子，我这人其实挺认真的，经不起你这么夸。",
                        "rationale": "守住个人真实框架，既不迎合也不被其标签牵制。",
                        "timing": "适时发送",
                        "tone_tags": ["自尊", "清晰", "框架"]
                    }
                ],
                "branch": {
                    "if_positive": "若对方发笑脸或调侃'打零分'，顺势回复'那我得申请线下重考一次了'埋线邀约。",
                    "if_neutral": "若对方回'哈哈'或敷衍表情，主动切入轻巧日常话题，不再就此辩解。",
                    "if_cooling": "若对方未回应，保持静止，切忌连发自证清白。"
                }
            }

        # 2. 对方疲惫/吐槽/倾诉日常 (IOI 倾诉)
        if any(w in latest_message for w in ["累", "加班", "开会", "散架", "烦", "好难"]):
            return {
                "replies": [
                    {
                        "tier": "稳健走心版",
                        "content": "听起来今天真是高负荷运转。赶紧躺平缓一缓，想吐槽随时找我，不想说话就先好好休息。",
                        "rationale": "狗头军师核心承接法则：先共情感受，主动给予免回特权，提供最大的心理安全感。",
                        "timing": "现在直接发，接住当下情绪",
                        "tone_tags": ["温暖", "共情", "无压力"]
                    },
                    {
                        "tier": "高情商策略版",
                        "content": "今天这个世界对你不太客气啊。给你两个选项：吐槽五分钟，或先欠我一份好心情。今天免回特权先给你发一张！",
                        "rationale": "幽默轻抚情绪，既能化解沉闷氛围，又顺理成章建立松弛的二人互动空间。",
                        "timing": "即刻发送",
                        "tone_tags": ["松弛感", "幽默", "关怀"]
                    },
                    {
                        "tier": "设立边界版",
                        "content": "快去泡个热水澡放空一下。手头的事先扔一边，今晚属于你自己的时间。",
                        "rationale": "边界感关怀，不强行占用对方精力，体现独立生活格调。",
                        "timing": "适时发送",
                        "tone_tags": ["体贴", "边界", "舒服"]
                    }
                ],
                "branch": {
                    "if_positive": "如果对方开始大倒苦水，耐心倾听并顺着对方情绪共鸣，严禁此时理性说教。",
                    "if_neutral": "如果对方简短回复'嗯嗯去躺了'，回复'晚安，好梦'体面收尾。",
                    "if_cooling": "如果对方已读未回，理解对方体力耗尽，次日中午再以轻巧日常重启。"
                }
            }

        # 3. 对方冷淡或敷衍 (IOD 信号)
        if "IOD" in signal or any(w in latest_message for w in ["哦", "随便", "好吧"]):
            return {
                "replies": [
                    {
                        "tier": "稳健走心版",
                        "content": "看你手头挺忙的，那你先处理手头的事，回头有空再聊。",
                        "rationale": "主动退后一步卸除社交压迫感，体面给对方台阶，不纠缠。",
                        "timing": "直接发送后暂停追加",
                        "tone_tags": ["体面", "无压", "尊重"]
                    },
                    {
                        "tier": "高情商策略版",
                        "content": "看起来你的能量槽见底了，本军师先行告退，给你回血的时间。😄",
                        "rationale": "情圣高位退场法：在气氛变僵前主动体面离场，保留好奇与个人生活姿态。",
                        "timing": "直接发送",
                        "tone_tags": ["松弛", "高位离场", "有趣"]
                    },
                    {
                        "tier": "设立边界版",
                        "content": "行，那你先忙你的。我正好也去把手头方案收个尾。",
                        "rationale": "展示独立生活与时间价值，不把个人注意力单方面附着在对方身上。",
                        "timing": "适时发送",
                        "tone_tags": ["独立", "框架", "自尊"]
                    }
                ],
                "branch": {
                    "if_positive": "若对方主动解释'刚才在处理紧急事情'，宽容接纳并恢复正常节奏。",
                    "if_neutral": "若对方仅回复'好'，彻底停止发送，至少冷冻观察 24-48 小时。",
                    "if_cooling": "若对方无回应，完全放平心态，不过度内耗，专注自身现实生活。"
                }
            }

        # 4. 通用日常升温
        return {
            "replies": [
                {
                    "tier": "稳健走心版",
                    "content": "刚才聊到你喜欢的这件事我回来琢磨了一下，发现你在这方面审美还真挺独到的。",
                    "rationale": "情圣阶段2/3好感深化：由事及人，真诚肯定对方独特特质，引发深入探讨。",
                    "timing": "适时发送",
                    "tone_tags": ["真诚", "共鸣", "舒适"]
                },
                {
                    "tier": "高情商策略版",
                    "content": "平时看你挺文静的，聊到这个眼睛居然会放光，看来总算挖到你的隐藏属性了😏",
                    "rationale": "情圣拉扯与冷读：通过反差观察建立二人专属默契，制造轻微暧昧张力。",
                    "timing": "即刻发送",
                    "tone_tags": ["推拉", "调侃", "张力"]
                },
                {
                    "tier": "设立边界版",
                    "content": "光聊这些日常太官方了，不如跟我说说你最近真正觉得有意思的一件事？",
                    "rationale": "跳出事务性问答，主动引领对话走向深度个人真实体验。",
                    "timing": "适时发送",
                    "tone_tags": ["引领", "深度", "自尊"]
                }
            ],
            "branch": {
                "if_positive": "对方兴致勃勃展开分享时，用共情与'然后呢'继续鼓励表达，适时埋下共同体验的种子。",
                "if_neutral": "对方反问你时，简短真诚分享一个自己生活中的有趣小切片，不长篇大论。",
                "if_cooling": "对方反应平平则顺其自然收尾，留出下次开启的悬念。"
            }
        }

skill_service = SkillService()
