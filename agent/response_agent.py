"""
Response Agent — Stage 6

Final response generation agent.
Encapsulates both non-streaming and streaming reply generation
by calling llm_client internally.
Does NOT handle intent classification, task planning, RAG retrieval,
or ReAct trace generation.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Ensure backend/llm_client.py can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import llm_client


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _build_mock_reply(user_message: str, intent: str) -> str:
    """Build a mock reply when no API key is available."""
    if not user_message:
        return "I didn't receive a message. How can I help you today?"

    if intent == "multimodal_request":
        return (
            f"You mentioned a multimodal request: '{user_message}'. "
            "The current system supports text chat only. "
            "Multimodal features (image, audio, video) are planned for future stages."
        )
    if intent == "deployment_help":
        return (
            f"You asked about deployment: '{user_message}'. "
            "In a real setup, I'd walk you through server configuration, "
            "environment setup, and service startup steps."
        )
    if intent == "coding_task":
        return (
            f"You asked about coding: '{user_message}'. "
            "In a real setup, I'd analyze the code, identify issues, and suggest fixes."
        )
    if intent == "technical_question":
        return (
            f"You asked a technical question: '{user_message}'. "
            "In a real setup, I'd explain the concepts clearly with examples."
        )
    if intent == "research_summary":
        return (
            f"You asked for a summary/research on: '{user_message}'. "
            "In a real setup, I'd synthesize key findings and present them concisely."
        )
    if intent == "document_qa":
        return (
            f"You asked about document Q&A: '{user_message}'. "
            "In a real setup, I'd retrieve relevant passages and answer based on the source material."
        )

    return f"You asked: '{user_message}'. This is a mock response demonstrating the structured chat format."


def generate_response(
    message: str,
    intent: str,
    tasks: List[str],
    retrieved_context: List[dict],
    react_trace: List[dict],
) -> Tuple[str, str, bool]:
    """
    Generate a non-streaming response.

    Returns:
        (reply, mode, api_failed)
        mode is one of: "llm", "mock", "error_fallback"
    """
    if _has_api_key():
        try:
            reply = llm_client.generate_reply(message, intent, tasks, retrieved_context)
            return reply, "llm", False
        except Exception:
            reply = (
                "I'm temporarily unable to reach the AI model. "
                "Please try again in a moment."
            )
            return reply, "error_fallback", True

    reply = _build_mock_reply(message, intent)
    return reply, "mock", False


def collect_stream_response(
    message: str,
    intent: str,
    tasks: List[str],
    retrieved_context: List[dict],
    react_trace: List[dict],
) -> str:
    """
    Synchronous function that collects the full streamed reply from Kimi.
    Designed to run inside a thread pool so the async event loop stays free.

    For mock mode, the caller should use _build_mock_reply directly
    and apply typing fallback in the orchestrator.
    """
    parts = []
    for delta in llm_client.stream_reply_sync(message, intent, tasks, retrieved_context):
        if delta:
            parts.append(delta)
    return "".join(parts)
