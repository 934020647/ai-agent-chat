"""
LLM Client — Stage 2

A thin wrapper around the OpenAI Python SDK for calling Kimi API.
Falls back gracefully when the API key is missing or the call fails.
"""

import os
from openai import OpenAI

DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_MODEL = "kimi-k2.6"

SYSTEM_PROMPT = (
    "You are an AI task assistant for a cloud-deployed AI Agent Chat Platform. "
    "Answer the user's question clearly and helpfully. "
    "When appropriate, explain tasks in a structured way. "
    "Do not reveal hidden chain-of-thought. "
    "Only provide concise user-facing reasoning summaries."
)


def _get_client():
    """Initialize OpenAI client from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    if not base_url:
        base_url = DEFAULT_BASE_URL

    return OpenAI(api_key=api_key, base_url=base_url)


def _get_model():
    """Return the model name from env, or the default."""
    model = os.getenv("MODEL_NAME", "").strip()
    return model if model else DEFAULT_MODEL


def call_llm(user_message: str) -> str:
    """
    Call the Kimi API and return the assistant's reply text.
    Raises an exception on failure so the caller can decide how to handle it.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = _get_model()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=1,
    )

    reply = response.choices[0].message.content
    return reply.strip() if reply else ""
