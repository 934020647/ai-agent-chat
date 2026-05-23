"""
React Agent — Stage 4

Generates a lightweight, user-visible ReAct-style action trace.
Does NOT call external APIs.
Does NOT expose hidden chain-of-thought.
Only produces safe, demo-friendly action/observation summaries.
"""

from typing import List, Dict, Any


_TRACES = {
    "deployment_help": [
        {"action": "classify_intent", "observation": "Recognized user intent as deployment_help"},
        {"action": "decompose_task", "observation": "Generated deployment steps for cloud environment"},
        {"action": "prepare_model_prompt", "observation": "Prepared context with deployment checklist"},
        {"action": "stream_response", "observation": "Streaming deployment guide to frontend"},
    ],
    "coding_task": [
        {"action": "classify_intent", "observation": "Recognized user intent as coding_task"},
        {"action": "decompose_task", "observation": "Broke down code issue into debugging steps"},
        {"action": "prepare_model_prompt", "observation": "Prepared context with code snippets and error patterns"},
        {"action": "stream_response", "observation": "Streaming code explanation and fix to frontend"},
    ],
    "technical_question": [
        {"action": "classify_intent", "observation": "Recognized user intent as technical_question"},
        {"action": "decompose_task", "observation": "Structured technical explanation into digestible parts"},
        {"action": "prepare_model_prompt", "observation": "Prepared context with key concepts and examples"},
        {"action": "stream_response", "observation": "Streaming technical answer to frontend"},
    ],
    "research_summary": [
        {"action": "classify_intent", "observation": "Recognized user intent as research_summary"},
        {"action": "decompose_task", "observation": "Outlined summary structure and key points"},
        {"action": "prepare_model_prompt", "observation": "Prepared context with research scope"},
        {"action": "stream_response", "observation": "Streaming synthesized summary to frontend"},
    ],
    "document_qa": [
        {"action": "classify_intent", "observation": "Recognized user intent as document_qa"},
        {"action": "decompose_task", "observation": "Identified document sources and relevant passages"},
        {"action": "prepare_model_prompt", "observation": "Prepared context with document excerpts"},
        {"action": "stream_response", "observation": "Streaming document-based answer to frontend"},
    ],
    "multimodal_request": [
        {"action": "classify_intent", "observation": "Recognized user intent as multimodal_request"},
        {"action": "decompose_task", "observation": "Evaluated multimodal requirements against current text-first system"},
        {"action": "prepare_model_prompt", "observation": "Prepared context noting multimodal as planned extension"},
        {"action": "stream_response", "observation": "Streaming text-based response to frontend"},
    ],
    "general_chat": [
        {"action": "classify_intent", "observation": "Recognized user intent as general_chat"},
        {"action": "decompose_task", "observation": "Prepared friendly response structure"},
        {"action": "prepare_model_prompt", "observation": "Prepared context for general conversation"},
        {"action": "stream_response", "observation": "Streaming chat response to frontend"},
    ],
    "unknown": [
        {"action": "classify_intent", "observation": "Intent unclear, falling back to general guidance"},
        {"action": "decompose_task", "observation": "Prepared clarifying questions"},
        {"action": "prepare_model_prompt", "observation": "Prepared safe fallback prompt"},
        {"action": "stream_response", "observation": "Streaming fallback response to frontend"},
    ],
}


def build_trace(intent: str, user_message: str) -> List[Dict[str, Any]]:
    """
    Return a ReAct-style action trace for the given intent.
    No hidden reasoning. Only user-facing action/observation pairs.
    """
    return list(_TRACES.get(intent, _TRACES["unknown"]))
