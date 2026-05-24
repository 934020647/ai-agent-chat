"""
LLM Client — Stage 2 + Stage 3.7 + Stage 3.8

A thin wrapper around the OpenAI Python SDK for calling Kimi API.
Falls back gracefully when the API key is missing or the call fails.

Added stream_reply_sync() for token-level streaming (synchronous generator).
"""

import os
from datetime import datetime
from openai import OpenAI

DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
DEFAULT_MODEL = "kimi-k2.6"

SYSTEM_PROMPT = (
    "You are an AI task assistant for a cloud-deployed AI Agent Chat Platform. "
    "Answer the user's question clearly and helpfully. "
    "When appropriate, explain tasks in a structured way. "
    "Do not reveal hidden chain-of-thought. "
    "Only provide concise user-facing reasoning summaries. "
    "You may receive retrieved project context from the local knowledge base. "
    "Use it when relevant. If the context is insufficient, answer based on the user request and clearly state limitations when needed."
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


def call_llm(user_message: str, system_prompt: str = None) -> str:
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
            {"role": "system", "content": system_prompt if system_prompt else SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=1,
    )

    reply = response.choices[0].message.content
    return reply.strip() if reply else ""


def stream_reply_sync(user_message: str, intent: str, tasks: list[str], retrieved_context: list[dict] = None, system_prompt: str = None):
    """
    Synchronous generator that streams deltas from Kimi API.
    Run this inside a thread pool so it does not block the asyncio event loop.
    """
    client = _get_client()
    if client is None:
        yield ""
        return

    model = _get_model()

    tasks_text = "\n".join(f"- {t}" for t in tasks)
    retrieved_text = ""
    if retrieved_context:
        snippets = []
        for item in retrieved_context:
            title = item.get("title", "")
            content = item.get("content", "")
            snippets.append(f"[{title}]\n{content}")
        retrieved_text = "\n\n".join(snippets)

    context_prompt = (
        f"User intent: {intent}\n"
        f"Planned tasks:\n{tasks_text}\n"
    )
    if retrieved_text:
        context_prompt += (
            f"\nRetrieved project context:\n{retrieved_text}\n\n"
            f"Now answer the user's question directly and helpfully, using the retrieved context when relevant."
        )
    else:
        context_prompt += "\nNow answer the user's question directly and helpfully."

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt if system_prompt else SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": context_prompt},
        ],
        temperature=1,
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            # Diagnostic: print timestamp and delta length (no sensitive data)
            print(f"[LLM STREAM] {datetime.now().isoformat()} delta_len={len(delta)}", flush=True)
            yield delta


def generate_reply(user_message: str, intent: str, tasks: list[str], retrieved_context: list[dict] = None, system_prompt: str = None) -> str:
    """
    Generate a reply using Kimi API with enriched context.
    Keeps the same client configuration as call_llm().
    """
    client = _get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not set")

    model = _get_model()

    tasks_text = "\n".join(f"- {t}" for t in tasks)
    retrieved_text = ""
    if retrieved_context:
        snippets = []
        for item in retrieved_context:
            title = item.get("title", "")
            content = item.get("content", "")
            snippets.append(f"[{title}]\n{content}")
        retrieved_text = "\n\n".join(snippets)

    context_prompt = (
        f"User intent: {intent}\n"
        f"Planned tasks:\n{tasks_text}\n"
    )
    if retrieved_text:
        context_prompt += (
            f"\nRetrieved project context:\n{retrieved_text}\n\n"
            f"Now answer the user's question directly and helpfully, using the retrieved context when relevant."
        )
    else:
        context_prompt += "\nNow answer the user's question directly and helpfully."

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt if system_prompt else SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": context_prompt},
        ],
        temperature=1,
    )

    reply = response.choices[0].message.content
    return reply.strip() if reply else ""
