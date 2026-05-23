"""
Planner Agent — Stage 3

Deterministic task decomposition based on intent.
No external service calls. User-readable tasks only.
"""

from typing import List


_TASK_TEMPLATES = {
    "deployment_help": [
        "Understand the deployment target and constraints",
        "Identify the necessary environment and dependencies",
        "Outline the deployment steps (build, transfer, start)",
        "Provide verification and rollback suggestions",
    ],
    "coding_task": [
        "Understand the code issue or requirement",
        "Reproduce or isolate the problem",
        "Propose a fix or implementation approach",
        "Provide code snippets and explain the changes",
    ],
    "technical_question": [
        "Clarify the core technical concept being asked",
        "Break down the explanation into digestible parts",
        "Provide examples or analogies where helpful",
        "Summarize key takeaways",
    ],
    "research_summary": [
        "Identify the research topic and scope",
        "Gather key points and findings",
        "Structure the summary logically",
        "Highlight conclusions or recommendations",
    ],
    "document_qa": [
        "Identify the relevant document or knowledge source",
        "Extract key information related to the question",
        "Synthesize a concise answer from the material",
        "Cite sources or suggest follow-up reading",
    ],
    "multimodal_request": [
        "Acknowledge the multimodal input request",
        "Explain that the current system is text-first",
        "Suggest text-based alternatives for now",
        "Note that multimodal support is a planned extension",
    ],
    "general_chat": [
        "Understand the user's message",
        "Prepare a friendly and relevant response",
    ],
    "unknown": [
        "Attempt to understand the unclear request",
        "Ask clarifying questions or provide general guidance",
    ],
}


def plan(intent: str, user_message: str) -> List[str]:
    """
    Return a list of decomposed tasks for the given intent.
    Tasks are user-facing and do not contain hidden reasoning.
    """
    return list(_TASK_TEMPLATES.get(intent, _TASK_TEMPLATES["general_chat"]))
