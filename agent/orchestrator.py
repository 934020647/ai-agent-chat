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
from agent import response_agent
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


def _typing_chunks(text: str, chunk_size: int = 6):
    """Slice text into small chunks for typing fallback effect."""
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


def _build_agent_flow(
    intent: str,
    tasks: List[str],
    retrieved_context: List[dict],
    react_trace: List[dict],
    mode: str = "llm",
) -> List[Dict[str, str]]:
    """Build a user-visible multi-agent collaboration flow summary."""
    flow = [
        {
            "agent": "IntentAgent",
            "input": "user message",
            "output": intent,
            "status": "completed",
        },
        {
            "agent": "PlannerAgent",
            "input": "intent + message",
            "output": f"{len(tasks)} tasks generated",
            "status": "completed",
        },
        {
            "agent": "RagAgent",
            "input": "user message",
            "output": f"{len(retrieved_context)} context snippets retrieved",
            "status": "completed",
        },
        {
            "agent": "ReactAgent",
            "input": "intent + tasks + retrieved_context",
            "output": f"{len(react_trace)} action/observation items generated",
            "status": "completed",
        },
        {
            "agent": "ResponseAgent",
            "input": "message + context + trace",
            "output": "streaming final answer" if mode != "mock" else "mock answer generated",
            "status": "completed",
        },
    ]
    return flow


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

    # Step 3.7: build and push agent collaboration flow
    agent_flow = _build_agent_flow(intent, tasks, retrieved_context, react_trace)
    yield {
        "type": "agent_flow",
        "agent_flow": agent_flow,
        "mode": "thinking",
    }
    await asyncio.sleep(0.2)

    # Step 4: generating reply via ResponseAgent
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
        # Run blocking Kimi SDK call in a background thread via ResponseAgent
        future = loop.run_in_executor(
            None,
            response_agent.collect_stream_response,
            message, intent, tasks, retrieved_context, react_trace,
        )

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
        full_reply = response_agent._build_mock_reply(message, intent)
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
        "agent_flow": agent_flow,
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

    reply, mode, api_failed = response_agent.generate_response(
        message, intent, tasks, retrieved_context, react_trace
    )
    agent_flow = _build_agent_flow(intent, tasks, retrieved_context, react_trace, mode)

    return {
        "reply": reply,
        "intent": intent,
        "tasks": tasks,
        "steps": _build_steps(intent, mode, api_failed),
        "retrieved_context": retrieved_context,
        "mode": mode,
        "react_trace": react_trace,
        "agent_flow": agent_flow,
    }
