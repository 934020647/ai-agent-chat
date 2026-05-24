"""
Resume Review Agent — Stage 8

OfferDrill 简历测评 Agent。
- 接收简历文本 + 用户资料
- 调用 Kimi API 生成结构化简历测评
- 不泄露 hidden chain-of-thought
- 不保存敏感信息到文件
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure backend/llm_client.py can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import llm_client


SYSTEM_PROMPT = (
    "你是一位资深的互联网大厂技术面试官和职业发展顾问。"
    "你的任务是根据候选人的简历和用户资料，生成一份结构化、 actionable 的简历测评报告。"
    "测评要专业、具体、有深度，避免空话套话。"
    "不要使用任何 Markdown 标题格式（如 # ##）。"
)


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _build_review_prompt(resume_text: str, profile: Optional[Dict[str, Any]]) -> str:
    lines = []
    lines.append("=== 任务 ===")
    lines.append("请对以下简历进行深度测评，并返回结构化 JSON 格式的报告。")
    lines.append("")

    if profile:
        lines.append("=== 用户资料 ===")
        lines.append(f"年级: {profile.get('grade', '未指定')}")
        lines.append(f"专业: {profile.get('major', '未指定')}")
        lines.append(f"学校/背景: {profile.get('school_or_background', '未指定')}")
        lines.append(f"目标岗位: {profile.get('target', '未指定')}")
        lines.append(f"目标院校/专业: {profile.get('target_school_or_major', '未指定')}")
        lines.append(f"默认面试模式: {profile.get('preferred_interview_mode', '未指定')}")
        lines.append(f"默认考察侧重: {profile.get('preferred_focus_mode', '未指定')}")
        lines.append("")

    lines.append("=== 简历内容 ===")
    # Truncate very long resumes to avoid token limit
    max_chars = 8000
    text = resume_text.strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[简历内容过长，已截断至前 8000 字符]"
    lines.append(text)
    lines.append("")

    lines.append(
        "=== 输出格式要求 ===\n"
        "请严格按以下 JSON 格式输出（不要包含其他文字，用 ```json 代码块包裹）：\n\n"
        "```json\n"
        "{\n"
        '  "overall_score": 82,\n'
        '  "summary": "一句话总结简历核心优劣势",\n'
        '  "strengths": ["亮点1", "亮点2"],\n'
        '  "risks": ["风险1", "风险2"],\n'
        '  "likely_questions": [\n'
        '    {\n'
        '      "area": "项目深挖",\n'
        '      "question": "具体问题",\n'
        '      "follow_ups": ["追问1", "追问2"]\n'
        '    }\n'
        '  ],\n'
        '  "revision_suggestions": ["修改建议1", "修改建议2"],\n'
        '  "suitable_roles": ["适合岗位1", "适合岗位2"],\n'
        '  "skill_gap_suggestions": ["补强建议1", "补强建议2"]\n'
        "}\n"
        "```\n\n"
        "评分标准：\n"
        "- overall_score: 0-100，综合评估简历质量\n"
        "- strengths: 简历亮点，最多 5 条\n"
        "- risks: 简历风险/不足，最多 5 条\n"
        "- likely_questions: 基于简历内容，面试官最可能追问的 3-5 个问题，每个问题配 2 个延伸追问\n"
        "- revision_suggestions: 具体可执行的简历修改建议，最多 5 条\n"
        "- suitable_roles: 根据简历内容推荐的适合岗位，最多 3 个\n"
        "- skill_gap_suggestions: 为了匹配目标岗位还需要补强的能力，最多 5 条\n"
    )

    return "\n".join(lines)


def _extract_json_block(text: str) -> Optional[str]:
    """Extract JSON from markdown code block or raw text."""
    # Try ```json ... ``` first
    m = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Try ``` ... ```
    m = re.search(r"```\s*(\{.*\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Try raw JSON object
    m = re.search(r"(\{.*\})", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def _build_fallback(raw_text: str) -> Dict[str, Any]:
    return {
        "parse_error": True,
        "raw_review": raw_text,
        "overall_score": None,
        "summary": "简历测评生成中，请稍后重试。",
        "strengths": [],
        "risks": [],
        "likely_questions": [],
        "revision_suggestions": [],
        "suitable_roles": [],
        "skill_gap_suggestions": [],
    }


def review_resume(resume_text: str, profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Review a resume and return structured evaluation.

    Returns:
        Dict with keys: overall_score, summary, strengths, risks,
        likely_questions, revision_suggestions, suitable_roles,
        skill_gap_suggestions
    """
    if not resume_text or not resume_text.strip():
        return {
            "overall_score": None,
            "summary": "简历内容为空，无法测评。请上传可提取文本的 PDF 文件（当前不支持扫描版/OCR）。",
            "strengths": [],
            "risks": ["简历无可提取文本"],
            "likely_questions": [],
            "revision_suggestions": ["请上传包含可提取文本的 PDF 简历，而非扫描版图片 PDF。"],
            "suitable_roles": [],
            "skill_gap_suggestions": [],
        }

    prompt = _build_review_prompt(resume_text, profile)

    if not _has_api_key():
        # Mock mode: generate a basic review based on resume keywords
        return _build_mock_review(resume_text, profile)

    try:
        raw_response = llm_client.call_llm(prompt, system_prompt=SYSTEM_PROMPT)
    except Exception as e:
        return _build_fallback(f"[API Error: {e}]")

    json_str = _extract_json_block(raw_response)
    if not json_str:
        return _build_fallback(raw_response)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError:
        return _build_fallback(raw_response)

    # Normalize fields
    normalized = {
        "overall_score": result.get("overall_score"),
        "summary": result.get("summary", ""),
        "strengths": result.get("strengths", []),
        "risks": result.get("risks", []),
        "likely_questions": result.get("likely_questions", []),
        "revision_suggestions": result.get("revision_suggestions", []),
        "suitable_roles": result.get("suitable_roles", []),
        "skill_gap_suggestions": result.get("skill_gap_suggestions", []),
    }
    return normalized


def _build_mock_review(resume_text: str, profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a mock resume review when no API key is available."""
    target = profile.get("target", "技术岗位") if profile else "技术岗位"
    keywords = []
    if "redis" in resume_text.lower():
        keywords.append("Redis")
    if "python" in resume_text.lower():
        keywords.append("Python")
    if "java" in resume_text.lower():
        keywords.append("Java")
    if "mysql" in resume_text.lower() or "sql" in resume_text.lower():
        keywords.append("数据库/SQL")
    if "docker" in resume_text.lower() or "k8s" in resume_text.lower() or "kubernetes" in resume_text.lower():
        keywords.append("容器/云原生")
    if "ai" in resume_text.lower() or "llm" in resume_text.lower() or "模型" in resume_text.lower():
        keywords.append("AI/大模型")
    if "rag" in resume_text.lower():
        keywords.append("RAG")
    if "grpc" in resume_text.lower() or "微服务" in resume_text.lower():
        keywords.append("微服务/gRPC")
    if not keywords:
        keywords.append("通用开发技能")

    score = min(90, max(65, 70 + len(keywords) * 3))

    return {
        "overall_score": score,
        "summary": f"这份简历展现了{'、'.join(keywords)}相关经验，整体适合{target}方向。建议补充量化指标和深入技术细节。",
        "strengths": [
            f"技术栈覆盖 {', '.join(keywords[:3])}，与目标岗位相关",
            "项目经历结构完整，有实际开发经验",
        ],
        "risks": [
            "项目结果缺少量化指标（QPS、延迟、用户量等）",
            "技术深度描述较浅，容易被追问细节",
            "缺乏对挑战和解决过程的描述",
        ],
        "likely_questions": [
            {
                "area": "项目深挖",
                "question": "你项目中最有技术挑战的部分是什么？如何解决的？",
                "follow_ups": [
                    "如果数据量扩大10倍，架构上需要做什么调整？",
                    "有没有做过性能压测？瓶颈在哪里？",
                ],
            },
            {
                "area": "技术基础",
                "question": "请解释你项目中用到的核心技术的底层原理。",
                "follow_ups": [
                    "它的优缺点是什么？",
                    "有没有替代方案？为什么选择这个？",
                ],
            },
            {
                "area": "岗位匹配",
                "question": f"你为什么选择{target}这个方向？",
                "follow_ups": [
                    "你认为自己在这个方向上的优势是什么？",
                    "如果工作内容与预期不符，你会怎么调整？",
                ],
            },
        ],
        "revision_suggestions": [
            "每段项目经历补充 1-2 个量化指标，例如'将接口响应时间从 300ms 优化到 80ms'。",
            "技术描述从'使用了 XX'改为'基于 XX 设计了 XX 方案，解决了 XX 问题，带来 XX 收益'。",
            "增加'挑战-行动-结果'结构，突出个人贡献。",
        ],
        "suitable_roles": [
            target,
            "全栈开发实习" if "前端" in resume_text or "react" in resume_text.lower() else "后端开发实习",
        ],
        "skill_gap_suggestions": [
            "补充系统设计和架构能力，准备'如果规模扩大X倍怎么办'类问题。",
            "深入理解项目中使用技术的底层原理，准备源码级追问。",
            "准备行为面试题（BQ），例如团队合作、冲突解决、时间管理等。",
        ],
    }
