"""
Interview Agent — Stage 7

OfferDrill 面经驱动 AI 模拟面试官核心逻辑。
- 从 data/interview_bank.json 加载面经题库
- 根据面试类型/侧重/年级筛选并随机抽题
- 结合简历内容，调用 Kimi API 扮演面试官
- 对用户回答给出评分反馈（accuracy/structure/depth/communication）
- 追问或推进至下一题

State 存储在内存中（服务重启丢失）：
  RESUME_STORE:     session_id -> 简历文本
  INTERVIEW_SESSIONS: session_id -> 会话状态
"""

import json
import os
import random
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure backend/llm_client.py can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import llm_client

_BANK_PATH = Path(__file__).resolve().parent.parent / "data" / "interview_bank.json"
_QUESTION_BANK: List[Dict[str, Any]] = []

# In-memory stores (no database per constraints)
RESUME_STORE: Dict[str, str] = {}
INTERVIEW_SESSIONS: Dict[str, Dict[str, Any]] = {}
USER_PROFILE_STORE: Dict[str, Dict[str, Any]] = {}


def save_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save or update a user profile. Returns the saved profile with profile_id."""
    profile_id = profile_data.get("profile_id")
    if not profile_id:
        profile_id = str(uuid.uuid4())[:12]

    now = datetime.now().isoformat()
    profile = {
        "profile_id": profile_id,
        "grade": profile_data.get("grade", ""),
        "major": profile_data.get("major", ""),
        "school_or_background": profile_data.get("school_or_background", ""),
        "target": profile_data.get("target", ""),
        "target_school_or_major": profile_data.get("target_school_or_major", ""),
        "preferred_interview_mode": profile_data.get("preferred_interview_mode", "general_mock"),
        "preferred_focus_mode": profile_data.get("preferred_focus_mode", "balanced"),
        "resume_id": profile_data.get("resume_id", ""),
        "resume_preview": profile_data.get("resume_preview", ""),
        "created_at": profile_data.get("created_at", now),
        "updated_at": now,
    }
    USER_PROFILE_STORE[profile_id] = profile
    return profile


def get_profile(profile_id: str) -> Optional[Dict[str, Any]]:
    return USER_PROFILE_STORE.get(profile_id)


def _load_bank() -> List[Dict[str, Any]]:
    global _QUESTION_BANK
    if _QUESTION_BANK:
        return _QUESTION_BANK
    if not _BANK_PATH.exists():
        return []
    with open(_BANK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    _QUESTION_BANK = data if isinstance(data, list) else []
    return _QUESTION_BANK


# ---------------------------------------------------------------------------
# Target synonym expansion maps user-friendly targets to bank role_or_major
# ---------------------------------------------------------------------------
_TARGET_SYNONYMS: Dict[str, List[str]] = {
    "ai应用开发": ["AI应用开发", "AI工程", "大模型应用", "RAG", "Agent", "AIGC"],
    "大模型应用开发": ["大模型应用开发", "AI应用开发", "AI工程", "大模型应用", "RAG", "Agent", "AIGC"],
    "llm应用": ["AI应用开发", "大模型应用开发", "AI工程", "RAG", "Agent"],
    "agent开发": ["Agent", "AI应用开发", "AI工程", "大模型应用开发"],
    "rag开发": ["RAG", "AI应用开发", "大模型应用开发", "AI工程"],
    "ai工程": ["AI工程", "AI应用开发", "大模型应用开发"],
    "aigc应用": ["AIGC", "AI应用开发", "大模型应用开发"],
    "后端": ["后端开发", "服务端", "Web后端"],
    "java后端": ["后端开发", "服务端"],
    "服务端": ["后端开发", "服务端"],
    "web后端": ["后端开发", "Web后端"],
    "go后端": ["后端开发"],
    "python后端": ["后端开发"],
    "算法": ["算法工程师", "机器学习", "深度学习"],
    "机器学习": ["算法工程师", "机器学习", "深度学习"],
    "深度学习": ["算法工程师", "深度学习", "机器学习"],
    "cv": ["算法工程师", "深度学习", "计算机视觉"],
    "nlp": ["算法工程师", "深度学习", "自然语言处理"],
    "推荐算法": ["算法工程师", "推荐"],
    "模型训练": ["算法工程师", "深度学习", "机器学习"],
    "产品": ["产品经理", "AI产品经理", "产品"],
    "产品经理": ["产品经理", "AI产品经理"],
    "用户增长": ["产品经理", "增长"],
    "产品运营": ["产品经理", "运营"],
    "tob产品": ["产品经理", "ToB"],
    "ai产品经理": ["AI产品经理", "产品经理"],
    "保研": ["保研", "复试", "研究生面试", "推免"],
    "复试": ["保研", "复试", "研究生面试"],
    "研究生面试": ["保研", "复试", "研究生面试"],
    "推免": ["保研", "推免", "复试"],
    "导师面": ["保研", "复试"],
    "学术面试": ["保研", "复试", "研究生面试"],
}


def _expand_target_keywords(target: Optional[str]) -> List[str]:
    """Expand user target into a list of matching keywords for the bank."""
    if not target:
        return []
    normalized = target.strip().lower().replace(" ", "").replace("/", "").replace("-", "")
    keywords = []
    # Direct match first
    keywords.append(target.strip())
    # Synonym expansion
    for key, expansions in _TARGET_SYNONYMS.items():
        if key in normalized:
            for ex in expansions:
                if ex not in keywords:
                    keywords.append(ex)
    return keywords


def _target_matches(q_role: str, target_keywords: List[str]) -> bool:
    """Check if a question's role_or_major matches any of the expanded target keywords."""
    if not target_keywords:
        return True
    q_role_norm = q_role.strip().lower().replace(" ", "").replace("/", "").replace("-", "")
    for kw in target_keywords:
        kw_norm = kw.strip().lower().replace(" ", "").replace("/", "").replace("-", "")
        if kw_norm in q_role_norm or q_role_norm in kw_norm:
            return True
    return False


def _score_question(
    q: Dict[str, Any],
    interview_mode: str,
    focus_mode: Optional[str],
    target_keywords: List[str],
    grade: Optional[str],
    resume_text: Optional[str] = None,
) -> int:
    """Score a question for relevance. Higher = better match."""
    score = 0
    # interview_mode exact match: +5
    if q.get("interview_mode") == interview_mode:
        score += 5
    # focus_mode exact match: +4
    if focus_mode and q.get("focus_mode") == focus_mode:
        score += 4
    # role/major keyword match: +5
    if _target_matches(q.get("role_or_major", ""), target_keywords):
        score += 5
    # topic related to focus_mode: +2
    topic = q.get("topic", "")
    if focus_mode and focus_mode.replace("_", "") in topic.lower().replace(" ", ""):
        score += 2
    # grade_range contains grade: +2
    if grade and grade in q.get("grade_range", []):
        score += 2
    # resume keywords overlap with question topic: +2
    if resume_text and resume_text.strip():
        resume_lower = resume_text.lower()
        topic_words = [w for w in topic.lower().split() if len(w) >= 2]
        for w in topic_words:
            if w in resume_lower:
                score += 2
                break
    return score


def pick_questions(
    interview_mode: str,
    focus_mode: Optional[str] = None,
    role_or_major: Optional[str] = None,
    grade: Optional[str] = None,
    num: int = 5,
    resume_text: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter question bank using scoring-based selection with relaxed fallback."""
    bank = _load_bank()
    target_keywords = _expand_target_keywords(role_or_major)

    # Phase 1: Score all questions
    scored = []
    for q in bank:
        s = _score_question(q, interview_mode, focus_mode, target_keywords, grade, resume_text)
        scored.append((s, q))

    # Phase 2: Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Phase 3: Try to pick top N with score > 0
    filtered = [q for s, q in scored if s > 0]
    if len(filtered) >= num:
        return filtered[:num]

    # Phase 4: Not enough — relaxed strategies
    # 4a: Same mode, any focus, same target
    relaxed = [q for q in bank if q.get("interview_mode") == interview_mode and _target_matches(q.get("role_or_major", ""), target_keywords)]
    for q in relaxed:
        if q not in filtered:
            filtered.append(q)
    if len(filtered) >= num:
        return filtered[:num]

    # 4b: Same mode, any target, any focus
    relaxed = [q for q in bank if q.get("interview_mode") == interview_mode]
    for q in relaxed:
        if q not in filtered:
            filtered.append(q)
    if len(filtered) >= num:
        return filtered[:num]

    # 4c: general_mock fallback (universal)
    relaxed = [q for q in bank if q.get("interview_mode") == "general_mock"]
    for q in relaxed:
        if q not in filtered:
            filtered.append(q)
    if len(filtered) >= num:
        return filtered[:num]

    # 4d: Anything left
    for q in bank:
        if q not in filtered:
            filtered.append(q)

    return filtered[:num]


def _get_style_examples(
    interview_mode: str,
    focus_mode: Optional[str],
    target_keywords: List[str],
    num_examples: int = 3,
) -> List[Dict[str, Any]]:
    """Pick a few existing bank questions as style examples for LLM fallback."""
    bank = _load_bank()
    candidates = []
    for q in bank:
        score = 0
        if q.get("interview_mode") == interview_mode:
            score += 3
        if focus_mode and q.get("focus_mode") == focus_mode:
            score += 2
        if _target_matches(q.get("role_or_major", ""), target_keywords):
            score += 2
        if score > 0:
            candidates.append((score, q))
    candidates.sort(key=lambda x: x[0], reverse=True)
    return [q for _, q in candidates[:num_examples]]


def _build_fallback_prompt(
    interview_mode: str,
    focus_mode: Optional[str],
    grade: Optional[str],
    major: Optional[str],
    target: Optional[str],
    resume_text: Optional[str],
    num_questions: int,
    style_examples: List[Dict[str, Any]],
) -> str:
    """Build the prompt for LLM fallback question generation."""
    mode_label = {
        "graduate_reexam": "研究生复试/保研面试",
        "industry_interview": "互联网大厂实习/校招面试",
        "general_mock": "综合模拟面试",
    }.get(interview_mode, "模拟面试")

    focus_label = {
        "balanced": "综合考察",
        "fundamentals": "基础能力",
        "project_experience": "项目经历深挖",
    }.get(focus_mode or "", "综合考察")

    lines = [
        f"你是一位资深{mode_label}出题专家。现在需要为一位申请【{target or '综合岗位'}】的【{grade or '未指定年级'}】学生生成 {num_questions} 道模拟面试题。",
        f"考察侧重点：{focus_label}。",
        "",
        "【重要风格要求】",
        "你不是出教材题，而是在模拟真实面经场景中的面试官提问。",
        "题目要像候选人在小红书/牛客/知乎面经里记录的那种问题：",
        "1. 直接、具体、带追问感。",
        "2. 常从候选人项目或简历切入。",
        "3. 经常问'为什么这么做''如果换一种情况怎么办''怎么评估效果''线上出问题怎么排查'。",
        "4. 不要一上来问太宏大的概念题。",
        "5. 不要像课程考试题。",
        "6. 每道题必须有 follow_up 追问。",
        "7. 题目语气要像面试官现场口头提问，口语化、自然。",
        "",
        "5道题应覆盖：",
        "- 1道自我介绍/背景或项目总览",
        "- 2道岗位核心技术",
        "- 1道项目深挖/简历追问",
        "- 1道综合场景/反思改进",
        "",
    ]

    if style_examples:
        lines.append("【参考风格样例】以下是题库中已有的真实面经风格题目，请你模仿其结构和语气，但生成全新的题目：")
        lines.append("")
        for i, ex in enumerate(style_examples, 1):
            lines.append(f"样例{i}:")
            lines.append(f"  topic: {ex.get('topic', '')}")
            lines.append(f"  question: {ex.get('question', '')}")
            lines.append(f"  follow_up: {ex.get('follow_up', [])}")
            lines.append(f"  answer_points: {ex.get('answer_points', [])}")
            lines.append("")

    if resume_text and resume_text.strip():
        snippet = resume_text.strip()[:1500]
        lines.append("【候选人简历片段】")
        lines.append(snippet)
        lines.append("请结合简历内容生成有针对性的追问型题目。")
        lines.append("")

    lines.append("【输出格式要求】")
    lines.append("请严格输出为 JSON 数组格式，不要包含 markdown 代码块标记，只输出纯 JSON 数组：")
    lines.append("[")
    lines.append('  {')
    lines.append('    "id": "generated_001",')
    lines.append('    "interview_mode": "' + interview_mode + '",')
    lines.append('    "focus_mode": "' + (focus_mode or "balanced") + '",')
    lines.append('    "role_or_major": "' + (target or "综合") + '",')
    lines.append('    "grade_range": ["' + (grade or "大三") + '"],')
    lines.append('    "topic": "题目主题",')
    lines.append('    "question": "面试官口语化提问",')
    lines.append('    "answer_points": ["要点1", "要点2", "要点3", "要点4"],')
    lines.append('    "follow_up": ["追问1", "追问2"],')
    lines.append('    "standard_answer": "一个较好的回答应该...",')
    lines.append('    "rubric": {')
    lines.append('      "accuracy": "准确性评价维度",')
    lines.append('      "structure": "结构性评价维度",')
    lines.append('      "depth": "深度评价维度",')
    lines.append('      "communication": "表达评价维度"')
    lines.append('    }')
    lines.append('  }')
    lines.append("]")
    lines.append("")
    lines.append("要求：")
    lines.append(f"- 必须生成恰好 {num_questions} 道题")
    lines.append("- 每道题的 id 用 generated_001, generated_002 等格式")
    lines.append("- question 字段必须口语化、自然，像面试官现场提问")
    lines.append("- follow_up 必须存在且像即时追问")
    lines.append("- answer_points 要具体可执行")
    lines.append("- 题目必须是全新的，不要逐字复制样例题")
    lines.append("- 直接输出 JSON，不要任何其他文字")

    return "\n".join(lines)


def _parse_fallback_json(text: str) -> List[Dict[str, Any]]:
    """Parse LLM response into a list of question dicts."""
    text = text.strip()
    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "questions" in data:
            return data["questions"]
    except Exception:
        pass
    return []


def _build_local_fallback_questions(
    interview_mode: str,
    focus_mode: Optional[str],
    target: Optional[str],
    num_questions: int = 5,
) -> List[Dict[str, Any]]:
    """Build generic fallback questions when LLM is unavailable."""
    # Determine topic set based on target keywords
    target_lower = (target or "").lower()
    if any(k in target_lower for k in ["ai", "大模型", "llm", "rag", "agent", "aigc"]):
        templates = [
            {
                "topic": "AI项目介绍",
                "question": "请介绍一个你做过或深入了解的 AI 应用项目。用户的问题从输入到模型给出回答，中间经历了哪些关键步骤？",
                "answer_points": ["项目背景和目标用户", "数据或知识库准备", "模型选择或 API 调用", "结果输出和展示"],
                "follow_up": ["如果模型回答不准确，你怎么优化？", "这个项目如果扩大用户量，最大的瓶颈会在哪里？"],
            },
            {
                "topic": "RAG与检索",
                "question": "如果你要用 RAG 做一个智能问答系统，文档是怎么进入知识库的？怎么保证检索到的内容和用户问题相关？",
                "answer_points": ["文档切分和索引方式", "Embedding 模型和向量库", "检索策略和重排序", "相关性保障措施"],
                "follow_up": ["如果检索不到相关内容，系统应该怎么回答？", "怎么评估检索质量好不好？"],
            },
            {
                "topic": "幻觉控制",
                "question": "大模型有时候会'胡说'，也就是幻觉。你在项目里有没有遇到过？是怎么发现和控制这个问题的？",
                "answer_points": ["幻觉的具体表现", "发现方法", "控制手段", "效果评估"],
                "follow_up": ["如果用户故意引导模型产生不当内容，你怎么处理？", "幻觉率和回答质量之间怎么平衡？"],
            },
            {
                "topic": "工具调用",
                "question": "你实现过让大模型调用外部工具的功能吗？如果工具调用失败，系统会怎么处理？",
                "answer_points": ["工具定义和选择", "调用流程", "失败处理", "结果回传和展示"],
                "follow_up": ["如果模型选错了工具怎么办？", "工具响应很慢时怎么优化用户体验？"],
            },
            {
                "topic": "上线与安全",
                "question": "如果要把你的 AI 应用上线给真实用户，你会重点关注哪些安全、成本和性能问题？",
                "answer_points": ["安全风险", "成本控制", "性能优化", "监控和告警"],
                "follow_up": ["用户上传敏感文件让模型分析，怎么保证数据安全？", "API 按 token 计费，怎么控制成本？"],
            },
        ]
    elif any(k in target_lower for k in ["算法", "机器学习", "深度学习", "cv", "nlp"]):
        templates = [
            {
                "topic": "模型训练",
                "question": "请介绍你训练一个模型的完整流程，从数据准备到模型评估。哪个环节你觉得最难？",
                "answer_points": ["数据准备和清洗", "模型选型和 baseline", "训练过程和调参", "评估和迭代"],
                "follow_up": ["训练过程中 loss 不下降怎么排查？", "模型上线后效果比离线差，可能是什么原因？"],
            },
            {
                "topic": "过拟合",
                "question": "什么是过拟合？你在项目中遇到过吗？当时是怎么发现和解决的？",
                "answer_points": ["过拟合定义和表现", "发现方法", "解决手段", "项目中的处理"],
                "follow_up": ["数据量很小怎么缓解过拟合？", "Dropout 在推理时怎么处理？"],
            },
            {
                "topic": "损失函数",
                "question": "你在项目里用过哪些损失函数？为什么选这个？",
                "answer_points": ["列举损失函数", "选择理由", "多任务加权", "实际案例"],
                "follow_up": ["类别不平衡时用什么损失函数？", "如果任务目标变了，损失函数怎么调整？"],
            },
            {
                "topic": "CNN与Transformer",
                "question": "你项目里用 CNN 还是 Transformer？如果重新设计会换吗？",
                "answer_points": ["当前架构选择理由", "CNN特点", "Transformer特点", "重新设计取舍"],
                "follow_up": ["Transformer在图像任务的主要缺点？", "数据量只有几千张选哪个？"],
            },
            {
                "topic": "实验复现",
                "question": "你有没有复现过论文实验？过程中遇到什么问题？怎么确认结果是对的？",
                "answer_points": ["复现的论文", "流程", "遇到的问题", "验证方法"],
                "follow_up": ["代码不开源怎么复现？", "结果和论文差很多优先怀疑哪里？"],
            },
        ]
    elif any(k in target_lower for k in ["产品", "pm", "产品经理"]):
        templates = [
            {
                "topic": "需求分析",
                "question": "你分析过用户需求吗？举一个 case，你是怎么确定这个需求值得做的？",
                "answer_points": ["需求来源", "验证方法", "优先级判断", "预期效果"],
                "follow_up": ["老板和业务方优先级冲突怎么办？", "怎么判断真需求和伪需求？"],
            },
            {
                "topic": "竞品分析",
                "question": "你做竞品分析看什么维度？举一个你分析过的竞品，得到了什么结论？",
                "answer_points": ["分析维度", "信息渠道", "差异化分析", "结论和行动"],
                "follow_up": ["竞品功能多但体验差，怎么判断哪个更重要？", "怎么防止变成抄功能？"],
            },
            {
                "topic": "指标设计",
                "question": "你设计过产品指标吗？举一个例子，指标涨了但满意度降了怎么解释？",
                "answer_points": ["指标体系", "定义和计算", "指标权衡", "异常分析"],
                "follow_up": ["DAU涨但留存降了是好事吗？", "怎么判断虚荣指标？"],
            },
            {
                "topic": "MVP设计",
                "question": "如果要做 AI 面试助手 MVP，哪些必须有，哪些可以后面加？",
                "answer_points": ["核心定位", "必须有功能", "延后功能", "验证方式"],
                "follow_up": ["MVP上线后反馈不好，方向错还是执行错？", "资源只够3个功能怎么选？"],
            },
            {
                "topic": "跨团队沟通",
                "question": "你怎么和技术团队沟通需求？开发说'做不了'怎么处理？",
                "answer_points": ["沟通方式", "可行性评估", "应对策略", "建立信任"],
                "follow_up": ["开发估期比预期长，砍需求还是加排期？", "怎么保证开发理解一致？"],
            },
        ]
    elif any(k in target_lower for k in ["保研", "复试", "推免", "研究生"]):
        templates = [
            {
                "topic": "科研兴趣",
                "question": "请用两分钟介绍你的科研兴趣，以及为什么选择这个方向？",
                "answer_points": ["具体方向", "兴趣来源", "前沿了解", "与导师契合度"],
                "follow_up": ["读过该领域哪些代表性论文？", "如果导师方向不同怎么调整？"],
            },
            {
                "topic": "项目经历",
                "question": "详细介绍一个最能体现你能力的项目，遇到什么技术挑战，怎么解决的？",
                "answer_points": ["项目背景", "个人职责", "技术难点", "解决方案", "成果收获"],
                "follow_up": ["重新做会改进什么？", "有没有用到导师论文的方法？"],
            },
            {
                "topic": "论文/竞赛",
                "question": "你发表过论文或参加过竞赛吗？详细介绍你的贡献和成果。",
                "answer_points": ["背景动机", "个人贡献", "核心方法", "结果收获"],
                "follow_up": ["复现最难的部分是什么？", "审稿人质疑不新颖怎么回应？"],
            },
            {
                "topic": "目标院校",
                "question": "你为什么选择我们实验室？了解我们组最近哪些工作？",
                "answer_points": ["方向了解", "具体论文", "兴趣契合", "成长期望"],
                "follow_up": ["如果方向不同怎么办？", "有没有联系过师兄师姐？"],
            },
            {
                "topic": "专业基础",
                "question": "请解释深度学习中 Batch Normalization 的原理，训练和推理时的差异。",
                "answer_points": ["BN原理", "训练行为", "推理行为", "作用"],
                "follow_up": ["BN和LayerNorm区别？", "Batch Size很小时效果会变差吗？"],
            },
        ]
    else:
        # Generic backend/tech fallback
        templates = [
            {
                "topic": "项目介绍",
                "question": "请介绍一个你最有代表性的项目，你在其中承担了什么角色，遇到了什么挑战？",
                "answer_points": ["项目背景", "个人职责", "技术挑战", "解决方案", "量化成果"],
                "follow_up": ["如果重新做会改进什么？", "项目最大的技术债是什么？"],
            },
            {
                "topic": "系统设计",
                "question": "你的项目是怎么做系统设计的？如果用户量扩大10倍，哪里最先成为瓶颈？",
                "answer_points": ["架构设计", "技术选型理由", "可扩展性考虑", "瓶颈预判"],
                "follow_up": ["怎么验证你的扩展方案有效？", "扩容时数据迁移怎么处理？"],
            },
            {
                "topic": "技术难点",
                "question": "项目里遇到过的最大技术难题是什么？你是怎么排查和解决的？",
                "answer_points": ["问题现象", "排查过程", "根因分析", "解决方案", "预防措施"],
                "follow_up": ["如果当时没有解决，有没有备选方案？", "怎么防止类似问题再次发生？"],
            },
            {
                "topic": "团队协作",
                "question": "描述一次你在团队中解决冲突或推动决策的经历。",
                "answer_points": ["具体场景", "各方立场", "你的行动", "结果反思"],
                "follow_up": ["如果重新处理会怎么做？", "技术分歧时应该听谁的？"],
            },
            {
                "topic": "职业规划",
                "question": "你为什么想做这个方向？对自己的职业规划是什么？",
                "answer_points": ["真实兴趣来源", "能力匹配点", "短期目标", "长期目标"],
                "follow_up": ["如果工作内容不符预期怎么办？", "最近在学习什么新技术？"],
            },
        ]

    questions = []
    for i, t in enumerate(templates[:num_questions], 1):
        q = {
            "id": f"generated_fallback_{i:03d}",
            "interview_mode": interview_mode,
            "focus_mode": focus_mode or "balanced",
            "role_or_major": target or "综合",
            "grade_range": [grade or "大三"],
            "topic": t["topic"],
            "question": t["question"],
            "answer_points": t["answer_points"],
            "follow_up": t["follow_up"],
            "standard_answer": "一个较好的回答应该结构清晰、有具体案例和数据支撑，展示解决问题的思路和能力。",
            "rubric": {
                "accuracy": "是否覆盖核心要点",
                "structure": "是否有清晰的逻辑结构",
                "depth": "是否有深入的分析或具体细节",
                "communication": "表达是否清晰流畅"
            }
        }
        questions.append(q)
    return questions


def generate_fallback_questions(
    interview_mode: str,
    focus_mode: Optional[str],
    grade: Optional[str],
    major: Optional[str],
    target: Optional[str],
    resume_text: Optional[str],
    num_questions: int = 5,
) -> List[Dict[str, Any]]:
    """Generate fallback questions via LLM or local templates."""
    target_keywords = _expand_target_keywords(target)
    style_examples = _get_style_examples(interview_mode, focus_mode, target_keywords, num_examples=3)
    prompt = _build_fallback_prompt(interview_mode, focus_mode, grade, major, target, resume_text, num_questions, style_examples)

    # Try LLM first
    if _has_api_key():
        try:
            system_prompt = (
                "你是一位资深面试出题专家。请严格按照用户要求的格式输出 JSON 数组，不要输出任何其他文字。"
            )
            response = llm_client.call_llm(prompt, system_prompt=system_prompt)
            parsed = _parse_fallback_json(response)
            if len(parsed) >= num_questions // 2:
                # Validate and enrich
                result = []
                for i, q in enumerate(parsed[:num_questions], 1):
                    q["id"] = q.get("id", f"generated_{i:03d}")
                    q["interview_mode"] = interview_mode
                    q["focus_mode"] = focus_mode or "balanced"
                    q["role_or_major"] = target or "综合"
                    q["grade_range"] = q.get("grade_range", [grade or "大三"])
                    if "rubric" not in q:
                        q["rubric"] = {
                            "accuracy": "是否覆盖核心要点",
                            "structure": "是否有清晰的逻辑结构",
                            "depth": "是否有深入的分析或具体细节",
                            "communication": "表达是否清晰流畅"
                        }
                    result.append(q)
                return result
        except Exception:
            pass

    # Fallback to local templates
    return _build_local_fallback_questions(interview_mode, focus_mode, target, num_questions)


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def extract_resume_evidence(resume_text: str, max_items: int = 5) -> List[str]:
    """Extract short, quotable evidence snippets from resume text.
    No embeddings, no external deps — pure rule/keyword based extraction.
    """
    if not resume_text or not resume_text.strip():
        return []

    # Tech keywords that indicate substantive content worth quoting
    KEYWORDS = [
        "项目", "经历", "实习", "论文", "竞赛", "系统", "平台",
        "Spring", "Spring Boot", "Redis", "Kafka", "MyBatis", "SQL",
        "FastAPI", "React", "Vue", "RAG", "Agent", "大模型",
        "深度学习", "机器学习", "PyTorch", "TensorFlow", "YOLO", "OpenCV",
        "数据库", "缓存", "消息队列", "Docker", "Nginx", "云服务器", "部署",
        "分布式", "微服务", "高并发", "高可用", "性能优化",
        "爬虫", "推荐", "搜索", "排序", "分类", "检测", "分割",
        "Kubernetes", "K8s", "ES", "Elasticsearch", "ClickHouse", "MongoDB",
        "gRPC", "REST", "API", "网关", "链路追踪", "监控",
        "算法", "模型", "训练", "推理", "调优", "特征工程",
        "数据清洗", "数据分析", "可视化", "BI", "A/B", "实验",
        "产品", "用户", "需求", "运营", "增长", "转化", "留存",
        "埋点", "漏斗", "路径", "画像", "标签", "推荐",
    ]

    # Split into lines and clean
    raw_lines = resume_text.splitlines()
    candidates = []
    for line in raw_lines:
        stripped = line.strip()
        if len(stripped) < 10:
            continue
        # Keep lines that contain at least one keyword
        lowered = stripped.lower()
        if any(kw.lower() in lowered for kw in KEYWORDS):
            # Deduplicate by exact match (case-insensitive)
            if stripped.lower() not in [c.lower() for c in candidates]:
                candidates.append(stripped)

    # Sort by richness (more keywords = richer snippet)
    def _score(snippet: str) -> int:
        lowered = snippet.lower()
        return sum(1 for kw in KEYWORDS if kw.lower() in lowered)

    candidates.sort(key=_score, reverse=True)

    # Truncate each snippet to ~80 chars max, but keep whole words
    result = []
    for snippet in candidates[:max_items]:
        if len(snippet) > 80:
            # Try to cut at a comma, semicolon, or space near 80 chars
            cut = 80
            for delim in ["，", ",", "；", ";", " "]:
                pos = snippet.rfind(delim, 60, 85)
                if pos > 0:
                    cut = pos + 1
                    break
            snippet = snippet[:cut].strip()
        result.append(snippet)

    return result


def _build_interviewer_system_prompt(
    interview_mode: str,
    role_or_major: str,
    grade: str,
    resume_text: str,
    profile: Optional[Dict[str, Any]] = None,
    job_type: str = "developer",
    resume_evidence: Optional[List[str]] = None,
) -> str:
    mode_label = {
        "graduate_reexam": "研究生复试/保研面试",
        "industry_interview": "互联网大厂实习/校招面试",
        "general_mock": "综合模拟面试",
    }.get(interview_mode, "模拟面试")

    job_type_label = {
        "developer": "开发工程师",
        "algorithm": "算法工程师",
        "product": "产品经理",
        "general": "综合岗位",
    }.get(job_type, "技术岗位")

    prompt = (
        f"你是一位专业的 {mode_label} 面试官，面试方向为【{job_type_label}】。"
        f"你正在面试一位申请【{role_or_major}】的【{grade}】学生。"
        "你的语气专业、友善但严格。"
        "你会根据候选人的回答质量给出具体反馈，并在必要时进行追问。"
        "如果回答已经充分，你会简短肯定后推进到下一题。"
        "不要泄露标准答案。"
        "不要使用任何 Markdown 标题格式（如 # ##）。"
        "使用纯文本或简单的列表格式即可。"
    )

    if job_type == "developer":
        prompt += (
            "\n\n【岗位侧重】你重点关注候选人的工程实现能力、系统设计、性能优化、"
            "接口设计、数据库、缓存、部署运维等工程实践能力。"
        )
    elif job_type == "algorithm":
        prompt += (
            "\n\n【岗位侧重】你重点关注候选人的算法思路、模型原理、时间/空间复杂度、"
            "数据处理、评估指标、实验设计和论文/竞赛经历。"
        )
    elif job_type == "product":
        prompt += (
            "\n\n【岗位侧重】你重点关注候选人的用户洞察、需求分析、产品判断、"
            "数据指标、优先级决策、沟通协作和项目推进能力。"
        )
    else:
        prompt += (
            "\n\n【岗位侧重】你采用通用专业技术面试风格，均衡考察基础、项目和综合素质。"
        )

    if profile:
        prompt += "\n\n=== 候选人资料 ==="
        if profile.get("major"):
            prompt += f"\n专业: {profile['major']}"
        if profile.get("school_or_background"):
            prompt += f"\n学校/背景: {profile['school_or_background']}"
        if profile.get("target"):
            prompt += f"\n目标岗位: {profile['target']}"
        if profile.get("target_school_or_major"):
            prompt += f"\n目标院校/专业方向: {profile['target_school_or_major']}"
        prompt += "\n请在面试中结合以上资料提出针对性问题。"

    if resume_text and resume_text.strip():
        # Truncate resume for system prompt to avoid token bloat
        resume_snippet = resume_text.strip()
        if len(resume_snippet) > 3000:
            resume_snippet = resume_snippet[:3000] + "\n\n[简历内容过长，已截断]"
        prompt += (
            "\n\n你已经阅读了候选人的简历，内容如下：\n"
            "---\n"
            f"{resume_snippet}\n"
            "---\n"
            "请在面试中结合简历内容提出针对性问题或追问。"
            "特别关注简历中提到的项目、技术栈和量化成果。"
        )

    if resume_evidence:
        prompt += (
            "\n\n【简历依据】\n"
            "以下是从候选人简历中提取到的可引用片段：\n"
        )
        for i, ev in enumerate(resume_evidence, 1):
            prompt += f"{i}. {ev}\n"
        prompt += (
            "\n【提问要求】\n"
            "你在提出项目经历相关问题时，必须优先引用上述其中一个片段，使用以下表达之一：\n"
            "- '我看到你的简历中提到「...」，请你具体说明……'\n"
            "- '根据你简历里的「...」经历，我想追问……'\n"
            "- '你在简历中写到使用「...」技术，请结合项目说明……'\n"
            "如果片段不足或不确定，不要捏造简历内容，只能说："
            "'结合你的项目经历，请你说明……'"
        )
    return prompt


_FORBIDDEN_CLOSING_PHRASES = [
    "反问环节",
    "面试结束",
    "今天就到这里",
    "今天到这里",
    "最后总结",
    "所有题目已完成",
    "最后一题已经结束",
    "进入总结",
    "总结环节",
    "面试到此结束",
    "正式面试结束",
    "提问环节",
]


def _sanitize_interviewer_reply(text: str, is_last_question: bool) -> str:
    """Sanitize interviewer reply: strip forbidden closing phrases on non-last questions."""
    if is_last_question:
        return text.strip()
    # For non-last questions, remove any sentence/line containing forbidden phrases
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            cleaned_lines.append(line)
            continue
        lowered = line_stripped.lower()
        if any(phrase in lowered for phrase in _FORBIDDEN_CLOSING_PHRASES):
            continue
        cleaned_lines.append(line)
    result = "\n".join(cleaned_lines).strip()
    # If sanitization stripped too much, provide a safe fallback
    if len(result) < 10:
        result = "感谢你的回答。我们继续下一题。"
    return result


def _build_prompt_for_answer(
    session: Dict[str, Any],
    user_answer: str,
    is_last_question: bool,
    job_type: str = "developer",
    resume_evidence: Optional[List[str]] = None,
) -> str:
    """Build the user-facing prompt sent to the LLM for evaluation + next step."""
    questions = session["questions"]
    current_idx = session["current_idx"]
    current_q = questions[current_idx] if current_idx < len(questions) else None
    total = len(questions)
    profile = session.get("profile")

    lines = []
    lines.append("=== 面试上下文 ===")
    lines.append(f"面试类型: {session['mode']}")
    lines.append(f"目标岗位/专业: {session['role']}")
    lines.append(f"岗位类型: {job_type}")
    lines.append(f"年级: {session['grade']}")
    if profile:
        if profile.get("major"):
            lines.append(f"专业: {profile['major']}")
        if profile.get("school_or_background"):
            lines.append(f"学校/背景: {profile['school_or_background']}")
        if profile.get("target"):
            lines.append(f"目标岗位: {profile['target']}")
        if profile.get("target_school_or_major"):
            lines.append(f"目标院校/专业: {profile['target_school_or_major']}")
    lines.append("")

    # Previous Q&A history
    if session["answers"]:
        lines.append("=== 已完成的问答 ===")
        for i, ans in enumerate(session["answers"], 1):
            lines.append(f"【第{i}题】{ans['question_text']}")
            lines.append(f"候选人回答: {ans['user_answer']}")
            if ans.get("evaluation"):
                ev = ans["evaluation"]
                lines.append(
                    f"评分: 准确性{ev.get('accuracy', 'N/A')} 结构{ev.get('structure', 'N/A')} "
                    f"深度{ev.get('depth', 'N/A')} 表达{ev.get('communication', 'N/A')}"
                )
            lines.append("")

    # Current question
    if current_q:
        lines.append("=== 当前题目 ===")
        lines.append(f"题目: {current_q['question']}")
        lines.append(f"考察方向: {current_q.get('topic', '综合')}")
        lines.append("评分标准（内部参考，不要告诉候选人）:")
        rubric = current_q.get("rubric", {})
        for k, v in rubric.items():
            lines.append(f"  - {k}: {v}")
        lines.append("")
        lines.append("=== 候选人当前回答 ===")
        lines.append(user_answer)
        lines.append("")

        # Stage-specific instruction
        if is_last_question:
            lines.append(
                f"【重要规则】当前是最后一题（第 {current_idx + 1} / {total} 题）。\n"
                "- 请完成本题点评，然后给出总体总结和对候选人的建议。\n"
                "- 最后明确提示：本轮模拟面试已完成。\n"
                "- 绝对不要再提出新的正式面试题。\n"
            )
        else:
            next_q = questions[current_idx + 1]
            lines.append(
                f"【重要规则】当前是第 {current_idx + 1} / {total} 题，不是最后一题。\n"
                "- 你只能完成本题点评，然后自然过渡到下一道题。\n"
                "- 绝对禁止说以下词汇或表达：反问环节、面试结束、今天就到这里、最后总结、"
                "所有题目已完成、最后一题已经结束、进入总结、总结环节、面试到此结束、正式面试结束、提问环节、本轮模拟面试已完成。\n"
                "- 不要给候选人任何面试即将结束的信号。\n"
                f"- 直接给出下一道题的题目内容：{next_q['question']}\n"
            )

        # Resume evidence injection for evaluation and follow-up
        resume_text = session.get("resume_text", "")
        focus_mode = session.get("focus", "")
        topic = current_q.get("topic", "")
        is_project_related = "项目" in topic or focus_mode == "project_experience"

        if resume_evidence and is_project_related:
            lines.append("")
            lines.append("【简历依据】")
            lines.append("以下是从候选人简历中提取到的可引用片段：")
            for i, ev in enumerate(resume_evidence, 1):
                lines.append(f"{i}. {ev}")
            lines.append(
                "\n【提问要求】"
                "如果涉及项目经历的提问或追问，优先引用上述片段，"
                "不要捏造简历中不存在的项目名、公司名、论文名或指标。"
            )

        if resume_evidence and is_project_related:
            lines.append("")
            lines.append(
                "【点评要求】\n"
                "点评时结合简历中的技术关键词，判断用户回答是否充分展开了简历中提到的能力：\n"
                "- 如果用户回答绕开了简历中的关键技术（如简历提到了 Redis + Kafka，但回答只说了缓存），"
                "请明确指出并建议补充。\n"
                "- 如果用户回答充分覆盖了简历中的技术点，请给予肯定。\n"
                "- 不要编造简历中没有的内容。"
            )

        lines.append("")
        lines.append(
            "请按以下格式回复：\n\n"
            "EVALUATION:\n"
            "准确性: [0-100] — [一句话评价]\n"
            "结构: [0-100] — [一句话评价]\n"
            "深度: [0-100] — [一句话评价]\n"
            "表达: [0-100] — [一句话评价]\n"
            "总体反馈: [1-2句总结]\n\n"
            "INTERVIEWER:\n"
            "[你的面试官回复。"
        )
        if is_last_question:
            lines.append("完成本题点评并给出总体总结，最后提示本轮模拟面试已完成。不要再提出新的正式面试题。]")
        else:
            lines.append("完成本题点评后自然过渡到下一题。绝对不要说面试结束或反问环节或本轮模拟面试已完成。]")
    else:
        lines.append("面试已经结束。请给候选人一个总体评价和建议。")

    return "\n".join(lines)


def _parse_evaluation(text: str) -> Dict[str, Any]:
    """Parse evaluation scores from LLM response."""
    evaluation = {
        "accuracy": None,
        "structure": None,
        "depth": None,
        "communication": None,
        "overall_feedback": "",
    }

    # Split at INTERVIEWER: marker
    parts = re.split(r"\n?INTERVIEWER:\s*", text, maxsplit=1)
    eval_text = parts[0] if parts else text

    # Extract scores
    score_pattern = re.compile(
        r"(?:准确性|accuracy)[：:]\s*(\d+).*?[—\-]\s*(.+)",
        re.IGNORECASE,
    )
    m = score_pattern.search(eval_text)
    if m:
        evaluation["accuracy"] = int(m.group(1))

    score_pattern = re.compile(
        r"(?:结构|structure)[：:]\s*(\d+).*?[—\-]\s*(.+)",
        re.IGNORECASE,
    )
    m = score_pattern.search(eval_text)
    if m:
        evaluation["structure"] = int(m.group(1))

    score_pattern = re.compile(
        r"(?:深度|depth)[：:]\s*(\d+).*?[—\-]\s*(.+)",
        re.IGNORECASE,
    )
    m = score_pattern.search(eval_text)
    if m:
        evaluation["depth"] = int(m.group(1))

    score_pattern = re.compile(
        r"(?:表达|communication)[：:]\s*(\d+).*?[—\-]\s*(.+)",
        re.IGNORECASE,
    )
    m = score_pattern.search(eval_text)
    if m:
        evaluation["communication"] = int(m.group(1))

    # Overall feedback
    fb_match = re.search(
        r"(?:总体反馈|overall feedback| Overall)[：:]\s*(.+?)(?=\n|$)",
        eval_text,
        re.IGNORECASE | re.DOTALL,
    )
    if fb_match:
        evaluation["overall_feedback"] = fb_match.group(1).strip()

    return evaluation


def _extract_interviewer_reply(text: str) -> str:
    """Extract the interviewer reply portion from LLM response."""
    parts = re.split(r"\n?INTERVIEWER:\s*", text, maxsplit=1)
    if len(parts) >= 2:
        return parts[-1].strip()
    # Fallback: if no marker, return everything after "总体反馈"
    fb_match = re.search(r"总体反馈.*\n(.+)", text, re.DOTALL)
    if fb_match:
        return fb_match.group(1).strip()
    return text.strip()


def start_interview(
    interview_mode: str,
    focus_mode: Optional[str],
    role_or_major: Optional[str],
    grade: Optional[str],
    resume_session_id: Optional[str] = None,
    num_questions: int = 5,
    profile: Optional[Dict[str, Any]] = None,
    job_type: str = "developer",
) -> Dict[str, Any]:
    """Start a new interview session, pick questions, and return session info."""
    session_id = str(uuid.uuid4())[:12]
    warnings: List[str] = []

    resume_text = ""
    if resume_session_id:
        resume_text = RESUME_STORE.get(resume_session_id, "")

    # Phase 1: Try bank questions
    questions = pick_questions(
        interview_mode=interview_mode,
        focus_mode=focus_mode,
        role_or_major=role_or_major,
        grade=grade,
        num=num_questions,
        resume_text=resume_text,
    )

    question_source = "interview_bank"

    # Phase 2: If bank doesn't have enough, try fallback generation
    bank_count = len(questions)
    if bank_count < num_questions:
        fallback_needed = num_questions - bank_count
        fallback_questions = generate_fallback_questions(
            interview_mode=interview_mode,
            focus_mode=focus_mode,
            grade=grade,
            major=profile.get("major") if profile else None,
            target=role_or_major,
            resume_text=resume_text,
            num_questions=fallback_needed,
        )
        questions.extend(fallback_questions)
        if bank_count == 0:
            question_source = "llm_generated"
            warnings.append("当前岗位题库覆盖不足，系统已基于面经风格自动生成面试题。")
        else:
            question_source = "mixed"
            warnings.append(f"当前岗位题库部分覆盖（{bank_count}/{num_questions}道），剩余题目由系统基于面经风格自动生成。")

    # If still no questions (shouldn't happen with fallback), use local generic
    if not questions:
        questions = _build_local_fallback_questions(interview_mode, focus_mode, role_or_major, num_questions)
        question_source = "llm_generated"
        warnings.append("当前岗位题库覆盖不足，系统已基于面经风格自动生成面试题。")

    resume_evidence = extract_resume_evidence(resume_text) if resume_text else []

    session = {
        "session_id": session_id,
        "mode": interview_mode,
        "focus": focus_mode,
        "role": role_or_major or "综合",
        "grade": grade or "未指定",
        "questions": questions,
        "current_idx": 0,
        "answers": [],
        "started_at": datetime.now().isoformat(),
        "status": "ready",
        "resume_text": resume_text,
        "resume_session_id": resume_session_id,
        "profile": profile,
        "job_type": job_type,
        "resume_evidence": resume_evidence,
    }

    INTERVIEW_SESSIONS[session_id] = session

    first_question = questions[0] if questions else None

    result: Dict[str, Any] = {
        "session_id": session_id,
        "status": session["status"],
        "total_questions": len(questions),
        "current_question": first_question,
        "progress": {"current": 1, "total": len(questions)},
        "question_source": question_source,
    }
    if warnings:
        result["warnings"] = warnings
    return result


def submit_answer(
    session_id: str,
    user_answer: str,
) -> Dict[str, Any]:
    """Process a user answer: evaluate, store, advance, generate next question or summary."""
    session = INTERVIEW_SESSIONS.get(session_id)
    if not session:
        return {"error": "Session not found", "session_id": session_id}

    if session["status"] == "completed":
        return {"error": "Interview already completed", "session_id": session_id}

    questions = session["questions"]
    current_idx = session["current_idx"]
    total = len(questions)

    if current_idx >= total:
        session["status"] = "completed"
        summary = _build_summary(session)
        summary["interviewer_reply"] = ""
        summary["evaluation"] = {}
        summary["next_question"] = None
        summary["closing_message"] = "本轮模拟面试已完成。"
        return summary

    current_q = questions[current_idx]
    has_next_question = current_idx + 1 < total
    is_last_question = not has_next_question

    # Build prompt and call LLM
    job_type = session.get("job_type", "developer")
    resume_evidence = session.get("resume_evidence")
    prompt = _build_prompt_for_answer(session, user_answer, is_last_question, job_type=job_type, resume_evidence=resume_evidence)
    system_prompt = _build_interviewer_system_prompt(
        session["mode"],
        session["role"],
        session["grade"],
        session.get("resume_text", ""),
        session.get("profile"),
        job_type=job_type,
        resume_evidence=resume_evidence,
    )

    llm_response = ""
    if _has_api_key():
        try:
            llm_response = llm_client.call_llm(prompt, system_prompt=system_prompt)
        except Exception as e:
            if has_next_question:
                llm_response = (
                    f"EVALUATION:\n"
                    f"准确性: 60 — 由于 API 调用失败，无法完成自动评分。\n"
                    f"结构: 60\n"
                    f"深度: 60\n"
                    f"表达: 60\n"
                    f"总体反馈: 系统暂时无法评分，请继续下一题。\n\n"
                    f"INTERVIEWER:\n"
                    f"感谢你的回答。由于系统原因，本次评分由系统暂代。"
                    f"下一题：{questions[current_idx + 1]['question']}"
                )
            else:
                llm_response = (
                    f"EVALUATION:\n"
                    f"准确性: 60 — 由于 API 调用失败，无法完成自动评分。\n"
                    f"结构: 60\n"
                    f"深度: 60\n"
                    f"表达: 60\n"
                    f"总体反馈: 系统暂时无法评分。\n\n"
                    f"INTERVIEWER:\n"
                    f"感谢你的回答。由于系统原因，本次评分由系统暂代。\n\n"
                    f"本轮模拟面试已完成。"
                )
    else:
        # Mock mode: generate simple feedback
        llm_response = _build_mock_evaluation(session, user_answer, current_q, is_last_question)

    evaluation = _parse_evaluation(llm_response)
    interviewer_reply = _extract_interviewer_reply(llm_response)

    # Sanitize: strip forbidden closing phrases from non-last replies
    if has_next_question:
        interviewer_reply = _sanitize_interviewer_reply(interviewer_reply, is_last_question=False)

    # Store answer
    session["answers"].append({
        "question_id": current_q.get("id"),
        "question_text": current_q["question"],
        "user_answer": user_answer,
        "evaluation": evaluation,
        "interviewer_reply": interviewer_reply,
    })

    # Advance
    session["current_idx"] = current_idx + 1
    next_idx = session["current_idx"]

    if next_idx >= total:
        session["status"] = "completed"
        summary = _build_summary(session)
        return {
            "session_id": session_id,
            "status": "completed",
            "interviewer_reply": interviewer_reply,
            "evaluation": evaluation,
            "next_question": None,
            "summary": summary,
            "closing_message": "本轮模拟面试已完成。",
            "progress": {"current": total, "total": total},
        }

    next_q = questions[next_idx]
    session["status"] = "in_progress"

    return {
        "session_id": session_id,
        "status": "in_progress",
        "interviewer_reply": interviewer_reply,
        "evaluation": evaluation,
        "next_question": next_q,
        "summary": None,
        "closing_message": None,
        "progress": {"current": next_idx + 1, "total": total},
    }


def _build_mock_evaluation(
    session: Dict[str, Any],
    user_answer: str,
    current_q: Dict[str, Any],
    is_last_question: bool,
) -> str:
    """Generate a mock evaluation when no API key is available."""
    questions = session["questions"]
    current_idx = session["current_idx"]

    answer_len = len(user_answer.strip())
    base_score = min(85, max(60, 60 + answer_len // 20))

    if is_last_question:
        return (
            f"EVALUATION:\n"
            f"准确性: {base_score} — 回答覆盖了主要要点。\n"
            f"结构: {base_score} — 结构尚可，可进一步加强逻辑层次。\n"
            f"深度: {base_score - 5} — 有一定深度，建议结合更多实际案例。\n"
            f"表达: {base_score + 5} — 表达清晰。\n"
            f"总体反馈: 整体回答不错，可在深度和案例支撑上继续提升。\n\n"
            f"INTERVIEWER:\n"
            f"感谢你的回答。下面是对你整场面试的总结。\n\n"
            f"你在面试中展现了良好的基础知识和表达能力。建议在后续学习中多关注实际项目经验，"
            f"并在回答中增加具体的数据和案例支撑。\n\n"
            f"本轮模拟面试已完成。"
        )

    next_q_text = f"下一题：{questions[current_idx + 1]['question']}"
    return (
        f"EVALUATION:\n"
        f"准确性: {base_score} — 回答覆盖了主要要点。\n"
        f"结构: {base_score} — 结构尚可，可进一步加强逻辑层次。\n"
        f"深度: {base_score - 5} — 有一定深度，建议结合更多实际案例。\n"
        f"表达: {base_score + 5} — 表达清晰。\n"
        f"总体反馈: 整体回答不错，可在深度和案例支撑上继续提升。\n\n"
        f"INTERVIEWER:\n"
        f"感谢你的回答。{next_q_text}"
    )


def _build_summary(session: Dict[str, Any]) -> Dict[str, Any]:
    """Build the final interview summary."""
    answers = session["answers"]
    total = len(answers)
    if total == 0:
        return {
            "session_id": session["session_id"],
            "status": "completed",
            "summary": "未作答任何题目。",
            "overall_scores": {},
            "answers": [],
            "closing_message": "本轮模拟面试已完成。",
            "progress": {"current": 0, "total": 0},
        }

    scores = {"accuracy": [], "structure": [], "depth": [], "communication": []}
    for ans in answers:
        ev = ans.get("evaluation", {})
        for key in scores:
            val = ev.get(key)
            if val is not None:
                scores[key].append(val)

    overall = {}
    for key, vals in scores.items():
        overall[key] = round(sum(vals) / len(vals), 1) if vals else None

    # Build summary text
    lines = ["### 面试总结", ""]
    lines.append(f"面试类型：{session['mode']} | 目标：{session['role']} | 年级：{session['grade']}")
    lines.append(f"共答题 {total} 道，总体评分如下：")
    lines.append("")
    for key, label in [("accuracy", "准确性"), ("structure", "结构"), ("depth", "深度"), ("communication", "表达")]:
        val = overall.get(key)
        if val is not None:
            lines.append(f"- {label}: {val}/100")
    lines.append("")
    lines.append("#### 逐题回顾")
    for i, ans in enumerate(answers, 1):
        ev = ans.get("evaluation", {})
        lines.append(f"**Q{i}**: {ans['question_text']}")
        lines.append(f"- 准确性: {ev.get('accuracy', 'N/A')} | 结构: {ev.get('structure', 'N/A')} | 深度: {ev.get('depth', 'N/A')} | 表达: {ev.get('communication', 'N/A')}")
        if ev.get("overall_feedback"):
            lines.append(f"- 反馈: {ev['overall_feedback']}")
        lines.append("")

    summary_text = "\n".join(lines)

    return {
        "session_id": session["session_id"],
        "status": "completed",
        "summary": summary_text,
        "overall_scores": overall,
        "answers": answers,
        "closing_message": "本轮模拟面试已完成。",
        "progress": {"current": total, "total": total},
    }


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return INTERVIEW_SESSIONS.get(session_id)


def get_bank_summary() -> Dict[str, Any]:
    """Return summary stats of the question bank for the frontend."""
    bank = _load_bank()
    modes = {}
    focuses = {}
    roles = set()
    grades = set()
    for q in bank:
        modes[q.get("interview_mode", "unknown")] = modes.get(q.get("interview_mode", "unknown"), 0) + 1
        focuses[q.get("focus_mode", "unknown")] = focuses.get(q.get("focus_mode", "unknown"), 0) + 1
        roles.add(q.get("role_or_major", ""))
        for g in q.get("grade_range", []):
            grades.add(g)
    return {
        "total_questions": len(bank),
        "by_mode": modes,
        "by_focus": focuses,
        "roles": sorted(roles),
        "grades": sorted(grades),
    }
