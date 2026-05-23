"""
AI Agent Chat Backend — Stage 2 (Kimi API Integration)

Supports:
- Mock mode when OPENAI_API_KEY is missing.
- Kimi API mode when OPENAI_API_KEY is present.
- Friendly fallback when the API call fails.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

import llm_client

# Load environment variables from backend/.env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

app = FastAPI(title="AI Agent Chat Backend")

# CORS configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Acceptable for early development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    intent: str
    tasks: List[str]
    steps: List[str]
    retrieved_context: List[str]
    mode: str


def _classify_intent(user_message: str) -> str:
    """Simple rule-based intent classification."""
    msg = user_message.lower()
    if not msg:
        return "unknown"
    if any(word in msg for word in ("hello", "hi", "hey")):
        return "greeting"
    if any(word in msg for word in ("code", "python", "program", "debug")):
        return "coding_task"
    if any(word in msg for word in ("deploy", "server", "nginx")):
        return "deployment_help"
    if any(word in msg for word in ("explain", "what is", "how to", "why")):
        return "technical_question"
    return "general_chat"


def _build_tasks(intent: str) -> List[str]:
    """Return deterministic tasks based on intent."""
    base = ["Understand the user's request"]
    if intent == "coding_task":
        return base + ["Analyze the code requirement", "Prepare a code-focused response"]
    if intent == "technical_question":
        return base + ["Break down the technical topic", "Provide a clear explanation"]
    if intent == "deployment_help":
        return base + ["Identify deployment steps", "Suggest actionable guidance"]
    return base + ["Prepare a structured response"]


def _build_steps(mode: str, api_failed: bool = False) -> List[str]:
    """Return deterministic execution steps."""
    steps = [
        "Received the user message",
        "Classified the request intent",
    ]
    if api_failed:
        steps.append("Attempted to call Kimi API but encountered an error")
        steps.append("Returned a friendly fallback response")
    elif mode == "llm":
        steps.append("Called Kimi API to generate the reply")
        steps.append("Returned structured data to the frontend")
    else:
        steps.append("Generated a mock response")
        steps.append("Returned structured data to the frontend")
    return steps


def _build_mock_reply(user_message: str, intent: str) -> str:
    """Build a Stage 1-style mock reply."""
    if not user_message:
        return "I didn't receive a message. How can I help you today?"
    if intent == "greeting":
        return f"Hello! You said: '{user_message}'. I'm ready to help."
    if intent == "coding_task":
        return f"I see you're asking about coding: '{user_message}'. In a real setup, I'd generate or review code for you."
    return f"You asked: '{user_message}'. This is a mock response demonstrating the structured chat format."


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "AI Agent Chat Backend is running"
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.
    Returns structured response with reply, intent, tasks, steps, and empty retrieved_context.
    Uses Kimi API when OPENAI_API_KEY is set; otherwise falls back to mock mode.
    """
    user_message = request.message.strip()
    intent = _classify_intent(user_message)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if api_key:
        try:
            reply = llm_client.call_llm(user_message)
            mode = "llm"
            api_failed = False
        except Exception:
            # API call failed — do not leak sensitive details
            reply = (
                "I'm temporarily unable to reach the AI model. "
                "Please try again in a moment."
            )
            mode = "error_fallback"
            api_failed = True
    else:
        reply = _build_mock_reply(user_message, intent)
        mode = "mock"
        api_failed = False

    return ChatResponse(
        reply=reply,
        intent=intent,
        tasks=_build_tasks(intent),
        steps=_build_steps(mode, api_failed),
        retrieved_context=[],
        mode=mode
    )
