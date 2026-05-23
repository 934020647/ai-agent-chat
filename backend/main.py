"""
AI Agent Chat Backend — Stage 3 (Intent Recognition and Task Decomposition)

Supports:
- Mock mode when OPENAI_API_KEY is missing.
- Kimi API mode when OPENAI_API_KEY is present.
- Friendly fallback when the API call fails.

/api/chat delegates to agent/orchestrator.py while keeping the response schema stable.
"""

import sys
from pathlib import Path

# Allow importing agent/ package from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any

from agent import orchestrator

# Load environment variables from backend/.env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

app = FastAPI(title="AI Agent Chat Backend")

# CORS configuration for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ReactTraceItem(BaseModel):
    action: str
    observation: str


class RetrievedContextItem(BaseModel):
    title: str
    content: str
    score: int


class ChatResponse(BaseModel):
    reply: str
    intent: str
    tasks: List[str]
    steps: List[str]
    retrieved_context: List[RetrievedContextItem]
    mode: str
    react_trace: List[ReactTraceItem] = []


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
    Delegates to the agent orchestrator while preserving the stable response schema.
    """
    result = orchestrator.handle_chat(request.message)
    return ChatResponse(**result)


async def _sse_stream(message: str):
    """Wrap orchestrator.stream_chat() into SSE format."""
    async for event in orchestrator.stream_chat(message):
        yield f"data: {json.dumps(event)}\n\n"


@app.post("/api/chat/stream")
def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint.
    Returns SSE events showing progress and the final result.
    """
    return StreamingResponse(
        _sse_stream(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
