"""
Intent Agent — Stage 3

Simple rule-based intent recognition.
No external service calls. Fast, stable, and explainable.
"""

# Keywords mapped to intents
KEYWORD_RULES = {
    # More specific intents first
    "multimodal_request": [
        "图片", "语音", "视频", "音频", "截图", "多模态",
        "image", "voice", "audio", "video", "screenshot",
        "multimodal", "photo", "picture", "录音", "摄像",
    ],
    "document_qa": [
        "文档", "pdf", "上传文件", "根据资料", "document",
        "upload", "file", "知识库", "资料库",
    ],
    "deployment_help": [
        "deploy", "server", "nginx", "uvicorn", "vite", "ssh",
        "ecs", "云服务器", "阿里云", "端口", "域名", "ssl",
        "https", "production", "上线", "发布", "运维",
    ],
    "coding_task": [
        "code", "bug", "报错", "函数", "类", "接口",
        "git", "python", "react", "fastapi", "代码",
        "调试", "error", "exception", "traceback", "crash",
        "500", "404", "refactor", "编译", "运行",
    ],
    "technical_question": [
        "explain", "what is", "how to", "why", "原理", "机制",
        "架构", "什么是", "怎么做", "为什么", "区别",
        "compare", "difference", "vs", "versus", "优劣",
        "性能", "优化", "best practice", "设计模式",
    ],
    "research_summary": [
        "总结", "概括", "调研", "论文", "资料", "综述",
        "review", "summary", "survey", "research",
        "文献", "报告",
    ],
}


def classify(user_message: str) -> str:
    """
    Classify user message into one of the supported intent categories.
    Returns the intent string.
    """
    if not user_message or not user_message.strip():
        return "unknown"

    msg = user_message.lower()

    # Check each intent's keyword list; the first match wins.
    # Order matters: more specific intents should be checked first.
    for intent, keywords in KEYWORD_RULES.items():
        for kw in keywords:
            if kw.lower() in msg:
                return intent

    # Greeting is a special case
    if any(word in msg for word in ("hello", "hi", "hey", "你好", "您好")):
        return "general_chat"

    return "general_chat"
