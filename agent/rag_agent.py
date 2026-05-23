"""
RAG Agent — Stage 5

Lightweight keyword-based retrieval from data/knowledge_base.md.
No external APIs. No embeddings. No vector database.
Returns 0-3 relevant knowledge snippets ranked by simple keyword overlap.
"""

import re
from pathlib import Path
from typing import List, Dict, Any


# Path to the knowledge base markdown file
_KB_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.md"


# Synonym expansion: each key expands to a list of related terms.
_SYNONYMS: Dict[str, List[str]] = {
    "deploy": ["部署", "deploy", "ecs", "nginx", "server", "云服务器", "阿里云", "上线", "发布", "production"],
    "agent": ["agent", "意图", "任务拆解", "react", "orchestrator", "planner", "intent", "rag"],
    "security": ["key", "安全", "env", "chain-of-thought", "隐私", "api key", "密钥", "github", "提交"],
    "rag": ["rag", "检索", "knowledge", "知识库", "retrieval", "上下文", "context"],
    "architecture": ["架构", "architecture", "技术栈", "fastapi", "react", "vite", "组件", "结构"],
    "overview": ["项目", "project", "overview", "平台", "功能", "目标"],
}


def _load_kb_text() -> str:
    """Load the knowledge base file. Returns empty string if missing."""
    try:
        return _KB_PATH.read_text(encoding="utf-8")
    except Exception:
        return ""


def _split_into_chunks(text: str) -> List[Dict[str, str]]:
    """
    Split markdown text into chunks by level-2 headings (## Title).
    Returns list of {"title": "...", "content": "..."}.
    """
    chunks: List[Dict[str, str]] = []
    if not text.strip():
        return chunks

    # Split by ## headings, keeping the heading text
    pattern = r"\n##\s+(.+?)\n"
    parts = re.split(pattern, text)

    # parts[0] is preamble before first ## (usually empty or # title)
    # parts[1] = first heading, parts[2] = content after first heading, etc.
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if content:
            chunks.append({"title": title, "content": content})

    return chunks


def _extract_keywords(query: str) -> List[str]:
    """
    Extract search keywords from user query.
    - Lowercase everything.
    - Split by non-word characters for mixed CJK/Latin.
    - Expand synonyms.
    - Remove very short tokens (<=1 char) unless they are CJK characters.
    """
    if not query:
        return []

    q = query.lower().strip()

    # Simple tokenization: split on non-alphanumeric and non-CJK
    # CJK range: \u4e00-\u9fff
    tokens = re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", q)

    # Collect unique keywords
    keywords: set = set()
    for t in tokens:
        if len(t) >= 2 or (len(t) == 1 and "\u4e00" <= t <= "\u9fff"):
            keywords.add(t)

    # Expand synonyms
    expanded: set = set(keywords)
    for kw in keywords:
        for base, syns in _SYNONYMS.items():
            if kw in syns or base == kw:
                expanded.update(syns)
                expanded.add(base)

    return list(expanded)


def _score_chunk(chunk: Dict[str, str], keywords: List[str]) -> int:
    """Count keyword occurrences in chunk title + content."""
    text = (chunk.get("title", "") + " " + chunk.get("content", "")).lower()
    score = 0
    for kw in keywords:
        score += text.count(kw.lower())
    return score


def retrieve(user_message: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve relevant knowledge snippets for the user query.

    Returns a list of dicts:
        [{"title": "...", "content": "...", "score": int}, ...]

    - Empty list if no match or knowledge base is missing.
    - At most `top_k` results, sorted by score descending.
    """
    text = _load_kb_text()
    if not text:
        return []

    chunks = _split_into_chunks(text)
    if not chunks:
        return []

    keywords = _extract_keywords(user_message)
    if not keywords:
        return []

    scored = []
    for chunk in chunks:
        s = _score_chunk(chunk, keywords)
        if s > 0:
            scored.append({
                "title": chunk["title"],
                "content": chunk["content"],
                "score": s,
            })

    # Sort by score descending, then truncate
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
