"""
AI Agent Chat Backend — Stage 1 (Mock Mode)

A minimal FastAPI backend that returns structured mock chat responses.
No real LLM calls, no database, no persistent storage.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

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
    Stage 1 mock chat endpoint.
    Returns a structured response with reply, intent, tasks, steps, and empty retrieved_context.
    """
    user_message = request.message.strip()

    # Simple mock logic to vary the reply slightly based on input
    if not user_message:
        reply = "I didn't receive a message. How can I help you today?"
        intent = "unknown"
    elif "hello" in user_message.lower() or "hi" in user_message.lower():
        reply = f"Hello! You said: '{user_message}'. I'm a mock AI assistant ready to help."
        intent = "greeting"
    elif "code" in user_message.lower() or "python" in user_message.lower():
        reply = f"I see you're asking about coding: '{user_message}'. In a real setup, I'd generate or review code for you."
        intent = "coding_task"
    else:
        reply = f"You asked: '{user_message}'. This is a mock response demonstrating the structured chat format."
        intent = "general_chat"

    return ChatResponse(
        reply=reply,
        intent=intent,
        tasks=[
            "Understand the user's request",
            "Prepare a structured response"
        ],
        steps=[
            "Received the user message",
            "Classified the request intent",
            "Generated a mock response",
            "Returned structured data to the frontend"
        ],
        retrieved_context=[],
        mode="mock"
    )
