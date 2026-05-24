#!/usr/bin/env python3
"""Audit interview_bank.json for low-technical / HR / generic questions."""

import json
import sys
from pathlib import Path

BANK_PATH = Path(__file__).resolve().parent.parent / "data" / "interview_bank.json"

# ---------------------------------------------------------------------------
# Hard-ban patterns (must match agent/interview_agent.py)
# ---------------------------------------------------------------------------
_HARD_BANNED_ALWAYS = [
    "非技术背景",
    "请用一分钟", "一分钟向", "一分钟解释",
    "什么是 API",
    "最大的缺点", "优点和缺点",
    "最近遇到的困难",
    "怎么克服",
    "如何看待加班",
    "用一句话概括", "一句话概括",
    "核心竞争力",
]

_HARD_BANNED_CONTEXTUAL = [
    "遇到的挑战", "最大的挑战",
    "团队冲突", "描述一次你在团队中", "遇到冲突的经历",
    "平时如何学习", "怎么学习新技术",
    "沟通能力", "表达能力",
]

# Exempt in graduate_reexam (standard grad-school questions)
_HARD_BANNED_GRAD_EXEMPT = [
    "为什么选择我们", "为什么选择这个方向", "职业规划",
]

_TECH_CONTEXT_PATTERNS = [
    "技术问题", "线上问题", "项目故障", "线上故障", "排查", "性能", "工程", "系统",
    "模型", "数据", "检索", "评估", "api调用", "接口设计", "限流", "鉴权",
    "错误码", "缓存", "数据库", "部署", "安全", "成本", "延迟", "并发",
    "架构", "算法", "训练", "推理", "调优", "优化", "bug", "缺陷", "监控",
]

# ---------------------------------------------------------------------------
# Soft suspicious patterns (informational only)
# ---------------------------------------------------------------------------
STRONG_PATTERNS = [
    "非技术背景", "一分钟", "最大的缺点", "优点和缺点", "最近遇到的困难",
    "遇到的挑战", "怎么克服", "为什么选择我们", "职业规划", "如何看待加班",
    "团队冲突", "平时如何学习", "核心竞争力", "用一句话", "描述一次",
    "沟通表达", "动机问题", "自我认知", "行为面", "HR",
    "如果重新处理", "你认为技术意见分歧", "如果工作内容和预期不符",
    "如果重新做", "如果让你", "如果数据量再扩大", "如果用户量再扩大",
]


def is_hard_banned(q: dict) -> tuple[bool, list[str]]:
    """Check if a question is hard-banned (must never appear in tech interviews)."""
    reasons = []
    question = q.get("question", "")
    topic = q.get("topic", "")
    answer_points = q.get("answer_points", [])
    follow_up = q.get("follow_up", [])
    standard_answer = q.get("standard_answer", "")

    combined_text = f"{question} {topic} {' '.join(str(p) for p in answer_points)} {' '.join(str(f) for f in follow_up)} {standard_answer}"
    combined_lower = combined_text.lower()
    interview_mode = q.get("interview_mode", "")

    for pat in _HARD_BANNED_ALWAYS:
        if pat in combined_lower:
            reasons.append(f"HARD_BANNED_ALWAYS: {pat}")

    has_tech_context = any(tc in combined_lower for tc in _TECH_CONTEXT_PATTERNS)
    if not has_tech_context:
        for pat in _HARD_BANNED_CONTEXTUAL:
            if pat in combined_lower:
                reasons.append(f"HARD_BANNED_CONTEXTUAL: {pat}")

    if interview_mode != "graduate_reexam":
        for pat in _HARD_BANNED_GRAD_EXEMPT:
            if pat in combined_lower:
                reasons.append(f"HARD_BANNED_GRAD_EXEMPT: {pat}")

    return len(reasons) > 0, reasons


def is_suspicious(q: dict) -> tuple[bool, list[str]]:
    """Check if a question is suspiciously low-tech. Returns (is_suspicious, reasons)."""
    reasons = []
    question = q.get("question", "")
    topic = q.get("topic", "")
    answer_points = q.get("answer_points", [])
    follow_up = q.get("follow_up", [])
    standard_answer = q.get("standard_answer", "")

    combined_text = f"{question} {topic} {' '.join(str(p) for p in answer_points)} {' '.join(str(f) for f in follow_up)} {standard_answer}"
    combined_lower = combined_text.lower()
    question_lower = question.lower()

    for pat in STRONG_PATTERNS:
        if pat in combined_lower:
            # Check if there's tech context that exempts it
            has_tech_context = any(tc in question_lower for tc in _TECH_CONTEXT_PATTERNS)
            if not has_tech_context:
                reasons.append(f"命中强过滤词: {pat}")

    return len(reasons) > 0, reasons


def main():
    with open(BANK_PATH, "r", encoding="utf-8") as f:
        bank = json.load(f)

    hard_banned = []
    suspicious = []
    by_mode = {}
    by_focus = {}

    for q in bank:
        is_banned, ban_reasons = is_hard_banned(q)
        if is_banned:
            hard_banned.append({
                "id": q.get("id"),
                "interview_mode": q.get("interview_mode"),
                "focus_mode": q.get("focus_mode"),
                "role_or_major": q.get("role_or_major"),
                "topic": q.get("topic"),
                "question": q.get("question"),
                "reasons": ban_reasons,
            })

        is_sus, reasons = is_suspicious(q)
        if is_sus:
            suspicious.append({
                "id": q.get("id"),
                "interview_mode": q.get("interview_mode"),
                "focus_mode": q.get("focus_mode"),
                "role_or_major": q.get("role_or_major"),
                "topic": q.get("topic"),
                "question": q.get("question"),
                "reasons": reasons,
            })

        mode = q.get("interview_mode", "unknown")
        focus = q.get("focus_mode", "unknown")
        by_mode.setdefault(mode, {"total": 0, "suspicious": 0})
        by_focus.setdefault(focus, {"total": 0, "suspicious": 0})
        by_mode[mode]["total"] += 1
        by_focus[focus]["total"] += 1
        if is_sus:
            by_mode[mode]["suspicious"] += 1
            by_focus[focus]["suspicious"] += 1

    print("=" * 70)
    print(f"题库审计报告")
    print("=" * 70)
    print(f"总题数: {len(bank)}")
    print(f"HARD_BANNED 题目: {len(hard_banned)}")
    print(f"可疑低技术题: {len(suspicious)}")
    print(f"\n按 interview_mode 统计:")
    for mode, stats in sorted(by_mode.items()):
        pct = stats["suspicious"] / stats["total"] * 100 if stats["total"] else 0
        print(f"  {mode}: {stats['suspicious']}/{stats['total']} ({pct:.0f}%)")
    print(f"\n按 focus_mode 统计:")
    for focus, stats in sorted(by_focus.items()):
        pct = stats["suspicious"] / stats["total"] * 100 if stats["total"] else 0
        print(f"  {focus}: {stats['suspicious']}/{stats['total']} ({pct:.0f}%)")

    if hard_banned:
        print(f"\n{'!' * 70}")
        print(f"HARD_BANNED 题目详情（必须修复）")
        print("!" * 70)
        grouped = {}
        for item in hard_banned:
            mode = item["interview_mode"]
            grouped.setdefault(mode, []).append(item)
        for mode, items in sorted(grouped.items()):
            print(f"\n--- {mode} ---")
            for item in items:
                print(f"\n  ID: {item['id']}")
                print(f"  Role: {item['role_or_major']}")
                print(f"  Topic: {item['topic']}")
                print(f"  Question: {item['question'][:80]}...")
                print(f"  Reasons: {', '.join(item['reasons'])}")
        print(f"\n❌ 发现 {len(hard_banned)} 道 HARD_BANNED 题目，程序退出码 1")
        sys.exit(1)

    print(f"\n{'=' * 70}")
    print(f"可疑题目详情（按 interview_mode 分组）")
    print("=" * 70)

    grouped = {}
    for item in suspicious:
        mode = item["interview_mode"]
        grouped.setdefault(mode, []).append(item)

    for mode, items in sorted(grouped.items()):
        print(f"\n--- {mode} ---")
        for item in items:
            print(f"\n  ID: {item['id']}")
            print(f"  Role: {item['role_or_major']}")
            print(f"  Topic: {item['topic']}")
            print(f"  Question: {item['question'][:80]}...")
            print(f"  Reasons: {', '.join(item['reasons'])}")

    print(f"\n✅ 未发现 HARD_BANNED 题目，通过审计。")
    sys.exit(0)


if __name__ == "__main__":
    main()
