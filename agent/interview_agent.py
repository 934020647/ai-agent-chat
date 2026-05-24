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


def pick_questions(
    interview_mode: str,
    focus_mode: Optional[str] = None,
    role_or_major: Optional[str] = None,
    grade: Optional[str] = None,
    num: int = 5,
) -> List[Dict[str, Any]]:
    """Filter question bank and randomly sample up to `num` questions."""
    bank = _load_bank()
    filtered = []
    for q in bank:
        if q.get("interview_mode") != interview_mode:
            continue
        if focus_mode and q.get("focus_mode") != focus_mode:
            continue
        if role_or_major and role_or_major not in q.get("role_or_major", ""):
            continue
        if grade and grade not in q.get("grade_range", []):
            continue
        filtered.append(q)

    if len(filtered) <= num:
        return filtered
    return random.sample(filtered, num)


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _build_interviewer_system_prompt(
    interview_mode: str,
    role_or_major: str,
    grade: str,
    resume_text: str,
) -> str:
    mode_label = {
        "graduate_reexam": "研究生复试/保研面试",
        "industry_interview": "互联网大厂实习/校招面试",
        "general_mock": "综合模拟面试",
    }.get(interview_mode, "模拟面试")

    prompt = (
        f"你是一位专业的 {mode_label} 面试官。"
        f"你正在面试一位申请【{role_or_major}】的【{grade}】学生。"
        "你的语气专业、友善但严格。"
        "你会根据候选人的回答质量给出具体反馈，并在必要时进行追问。"
        "如果回答已经充分，你会简短肯定后推进到下一题。"
        "不要泄露标准答案。"
        "不要使用任何 Markdown 标题格式（如 # ##）。"
        "使用纯文本或简单的列表格式即可。"
    )
    if resume_text and resume_text.strip():
        prompt += (
            "\n\n你已经阅读了候选人的简历，内容如下：\n"
            "---\n"
            f"{resume_text}\n"
            "---\n"
            "请在面试中结合简历内容提出针对性问题或追问。"
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
) -> str:
    """Build the user-facing prompt sent to the LLM for evaluation + next step."""
    questions = session["questions"]
    current_idx = session["current_idx"]
    current_q = questions[current_idx] if current_idx < len(questions) else None
    total = len(questions)

    lines = []
    lines.append("=== 面试上下文 ===")
    lines.append(f"面试类型: {session['mode']}")
    lines.append(f"目标岗位/专业: {session['role']}")
    lines.append(f"年级: {session['grade']}")
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
                "- 最后明确提示：现在进入反问环节，你可以向面试官提问。\n"
                "- 绝对不要再提出新的正式面试题。\n"
            )
        else:
            next_q = questions[current_idx + 1]
            lines.append(
                f"【重要规则】当前是第 {current_idx + 1} / {total} 题，不是最后一题。\n"
                "- 你只能完成本题点评，然后自然过渡到下一道题。\n"
                "- 绝对禁止说以下词汇或表达：反问环节、面试结束、今天就到这里、最后总结、"
                "所有题目已完成、最后一题已经结束、进入总结、总结环节、面试到此结束、正式面试结束、提问环节。\n"
                "- 不要给候选人任何面试即将结束的信号。\n"
                f"- 直接给出下一道题的题目内容：{next_q['question']}\n"
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
            lines.append("完成本题点评并给出总体总结，最后提示进入反问环节。不要再提出新的正式面试题。]")
        else:
            lines.append("完成本题点评后自然过渡到下一题。绝对不要说面试结束或反问环节。]")
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
) -> Dict[str, Any]:
    """Start a new interview session, pick questions, and return session info."""
    session_id = str(uuid.uuid4())[:12]

    questions = pick_questions(
        interview_mode=interview_mode,
        focus_mode=focus_mode,
        role_or_major=role_or_major,
        grade=grade,
        num=num_questions,
    )

    resume_text = ""
    if resume_session_id:
        resume_text = RESUME_STORE.get(resume_session_id, "")

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
    }

    INTERVIEW_SESSIONS[session_id] = session

    first_question = questions[0] if questions else None

    return {
        "session_id": session_id,
        "status": session["status"],
        "total_questions": len(questions),
        "current_question": first_question,
        "progress": {"current": 1, "total": len(questions)},
    }


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
        summary["closing_message"] = "现在进入反问环节，你可以向面试官提问。"
        return summary

    current_q = questions[current_idx]
    has_next_question = current_idx + 1 < total
    is_last_question = not has_next_question

    # Build prompt and call LLM
    prompt = _build_prompt_for_answer(session, user_answer, is_last_question)
    system_prompt = _build_interviewer_system_prompt(
        session["mode"],
        session["role"],
        session["grade"],
        session.get("resume_text", ""),
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
                    f"现在进入反问环节，你可以向面试官提问。"
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
            "closing_message": "现在进入反问环节，你可以向面试官提问。",
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
            f"现在进入反问环节，你可以向面试官提问。"
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
            "closing_message": "现在进入反问环节，你可以向面试官提问。",
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
        "closing_message": "现在进入反问环节，你可以向面试官提问。",
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
