"""
Orchestrator — Stage 3 + Stage 3.6 + Stage 3.8

Coordinates IntentAgent, PlannerAgent, and LLM client
to produce a structured chat response.
Keeps the frontend API contract unchanged.

Added stream_chat() with:
- Non-blocking SSE via thread-pool + asyncio.Queue
- Heartbeat status events while waiting for Kimi
- Typing fallback: slicing full reply into small deltas
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure backend/llm_client.py can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from agent.intent_agent import classify
from agent.planner_agent import plan
from agent.react_agent import build_trace
from agent import rag_agent
import llm_client


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def _build_steps(intent: str, mode: str, api_failed: bool = False) -> List[str]:
    """Generate user-facing execution steps."""
    steps = [
        "Received the user message",
        f"Recognized intent as {intent}",
        "Generated task decomposition",
    ]

    if api_failed:
        steps.append("Attempted to call Kimi API but encountered an error")
        steps.append("Returned a friendly fallback response")
    elif mode == "llm":
        steps.append("Called Kimi API to generate the reply")
        steps.append("Returned structured response to frontend")
    else:
        steps.append("Generated a mock response")
        steps.append("Returned structured response to frontend")

    return steps


def _build_mock_reply(user_message: str, intent: str) -> str:
    """Build a Stage 1-style mock reply when no API key is available."""
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


def _typing_chunks(text: str, chunk_size: int = 6):
    """Slice text into small chunks for typing fallback effect."""
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


def _sync_collect_reply(message: str, intent: str, tasks: List[str], retrieved_context: List[dict] = None) -> str:
    """
    Synchronous function that collects the full reply from Kimi stream.
    Runs inside a thread pool so the async event loop stays free.
    """
    parts = []
    for delta in llm_client.stream_reply_sync(message, intent, tasks, retrieved_context):
        if delta:
            parts.append(delta)
    return "".join(parts)


def _heartbeat_steps(base_steps: List[str], extra: str, max_len: int = 5) -> List[str]:
    """Build a steps list capped at max_len, keeping early critical steps."""
    core = base_steps[:3]  # Always keep first 3 core steps
    tail = list(base_steps[3:])
    # Avoid duplicate extra
    if extra not in tail:
        tail.append(extra)
    # Keep tail truncated so total <= max_len
    allowed_tail = max_len - len(core)
    if allowed_tail < 1:
        allowed_tail = 1
    trimmed_tail = tail[-allowed_tail:]
    return core + trimmed_tail


async def stream_chat(user_message: str):
    """
    Async generator that yields streaming progress events.

    Uses a background thread for the blocking Kimi SDK call,
    while the main generator sends heartbeat status events.
    After the reply is ready, uses typing fallback to slice it
    into small deltas so the front-end sees gradual growth.
    """
    message = user_message.strip()

    # Step 1: received message
    yield {
        "type": "status",
        "steps": ["Received the user message"],
        "mode": "thinking",
    }
    await asyncio.sleep(0.2)

    # Step 2: recognizing intent
    yield {
        "type": "status",
        "steps": [
            "Received the user message",
            "Recognizing user intent",
        ],
        "mode": "thinking",
    }
    await asyncio.sleep(0.2)

    intent = classify(message)

    yield {
        "type": "intent",
        "intent": intent,
        "steps": [
            "Received the user message",
            f"Recognized intent as {intent}",
        ],
        "mode": "thinking",
    }
    await asyncio.sleep(0.2)

    # Step 3: decomposing task
    yield {
        "type": "status",
        "steps": [
            "Received the user message",
            f"Recognized intent as {intent}",
            "Decomposing the task",
        ],
        "mode": "thinking",
    }
    await asyncio.sleep(0.2)

    tasks = plan(intent, message)

    yield {
        "type": "tasks",
        "tasks": tasks,
        "steps": [
            "Received the user message",
            f"Recognized intent as {intent}",
            "Generated task decomposition",
        ],
        "mode": "thinking",
    }
    await asyncio.sleep(0.2)

    # Step 3.5: retrieve context from knowledge base
    retrieved_context = rag_agent.retrieve(message)

    yield {
        "type": "retrieved_context",
        "retrieved_context": retrieved_context,
        "mode": "thinking",
    }
    await asyncio.sleep(0.2)

    react_trace = build_trace(intent, message, retrieved_context)

    # Step 3.6: push react trace
    yield {
        "type": "react_trace",
        "react_trace": react_trace,
        "mode": "thinking",
    }
    await asyncio.sleep(0.2)

    # Step 4: generating reply
    base_status_steps = [
        "Received the user message",
        f"Recognized intent as {intent}",
        "Generated task decomposition",
        "Calling Kimi API to generate the reply",
    ]

    yield {
        "type": "status",
        "steps": list(base_status_steps),
        "mode": "thinking",
    }

    full_reply = ""
    mode = "mock"
    api_failed = False

    if _has_api_key():
        loop = asyncio.get_running_loop()
        # Run blocking Kimi SDK call in a background thread
        future = loop.run_in_executor(None, _sync_collect_reply, message, intent, tasks, retrieved_context)

        heartbeat_messages = [
            "Calling Kimi API to generate the reply",
            "Still waiting for Kimi response...",
            "Streaming response in progress...",
            "Received model output, rendering answer...",
            "Finalizing the response",
        ]
        heartbeat_idx = 0

        while not future.done():
            await asyncio.sleep(1.0)
            if not future.done():
                msg = heartbeat_messages[min(heartbeat_idx, len(heartbeat_messages) - 1)]
                heartbeat_idx += 1
                yield {
                    "type": "status",
                    "steps": _heartbeat_steps(base_status_steps, msg),
                    "mode": "llm",
                }

        try:
            full_reply = future.result()
            mode = "llm"
        except Exception:
            full_reply = (
                "I'm temporarily unable to reach the AI model. "
                "Please try again in a moment."
            )
            mode = "error_fallback"
            api_failed = True
    else:
        full_reply = _build_mock_reply(message, intent)
        mode = "mock"
        api_failed = False

    # Typing fallback: slice full reply into small deltas
    chunks = list(_typing_chunks(full_reply, chunk_size=6))
    total_chunks = len(chunks)
    progress_interval = max(1, total_chunks // 5)

    for idx, chunk in enumerate(chunks):
        yield {
            "type": "delta",
            "delta": chunk,
            "mode": mode,
        }
        await asyncio.sleep(0.10)

        # Push progress status periodically
        if (idx + 1) % progress_interval == 0 and idx + 1 < total_chunks:
            percent = int((idx + 1) / total_chunks * 100)
            yield {
                "type": "status",
                "steps": _heartbeat_steps(
                    base_status_steps,
                    f"Rendering answer: {percent}%",
                ),
                "mode": mode,
            }

    await asyncio.sleep(0.1)

    steps = _build_steps(intent, mode, api_failed)

    yield {
        "type": "final",
        "reply": full_reply,
        "intent": intent,
        "tasks": tasks,
        "steps": steps,
        "retrieved_context": retrieved_context,
        "mode": mode,
        "react_trace": react_trace,
    }

    yield {"type": "done"}


def handle_chat(user_message: str) -> Dict[str, Any]:
    """
    Main orchestration entry point (non-streaming).

    Returns a dict with keys:
        reply, intent, tasks, steps, retrieved_context, mode, react_trace
    """
    message = user_message.strip()
    intent = classify(message)
    tasks = plan(intent, message)
    retrieved_context = rag_agent.retrieve(message)
    react_trace = build_trace(intent, message, retrieved_context)

    if _has_api_key():
        try:
            reply = llm_client.generate_reply(message, intent, tasks, retrieved_context)
            mode = "llm"
            api_failed = False
        except Exception:
            reply = (
                "I'm temporarily unable to reach the AI model. "
                "Please try again in a moment."
            )
            mode = "error_fallback"
            api_failed = True
    else:
        reply = _build_mock_reply(message, intent)
        mode = "mock"
        api_failed = False

    return {
        "reply": reply,
        "intent": intent,
        "tasks": tasks,
        "steps": _build_steps(intent, mode, api_failed),
        "retrieved_context": retrieved_context,
        "mode": mode,
        "react_trace": react_trace,
    }
