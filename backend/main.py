"""
AI Agent Chat Backend — Stage 3 + Stage 7 (Interview Coach)

Supports:
- Mock mode when OPENAI_API_KEY is missing.
- Kimi API mode when OPENAI_API_KEY is present.
- Friendly fallback when the API call fails.
- Interview simulation with resume upload and question bank.

/api/chat delegates to agent/orchestrator.py while keeping the response schema stable.
/api/interview/* provides OfferDrill interview simulation endpoints.
"""

import sys
from pathlib import Path

# Allow importing agent/ package from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import shutil
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from agent import orchestrator
from agent import interview_agent

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


# ---------- Shared Schemas ----------

class ChatRequest(BaseModel):
    message: str


class ReactTraceItem(BaseModel):
    action: str
    observation: str


class RetrievedContextItem(BaseModel):
    title: str
    content: str
    score: int


class AgentFlowItem(BaseModel):
    agent: str
    input: str
    output: str
    status: str


class ChatResponse(BaseModel):
    reply: str
    intent: str
    tasks: List[str]
    steps: List[str]
    retrieved_context: List[RetrievedContextItem]
    mode: str
    react_trace: List[ReactTraceItem] = []
    agent_flow: List[AgentFlowItem] = []


# ---------- Chat Endpoints ----------

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


# ---------- Interview Endpoints ----------

def _extract_pdf_text(file_path: Path) -> str:
    """Extract text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(file_path))
        texts = []
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                texts.append(txt)
        return "\n\n".join(texts)
    except Exception as e:
        return f"[PDF extraction failed: {e}]"


@app.post("/api/interview/upload-resume")
def upload_resume(file: UploadFile = File(...)):
    """Upload a resume PDF, extract text, and return a resume session ID."""
    uploads_dir = Path(__file__).resolve().parent.parent / "uploads"
    uploads_dir.mkdir(exist_ok=True)

    resume_session_id = str(uuid.uuid4())[:12]
    file_path = uploads_dir / f"{resume_session_id}_{file.filename}"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    resume_text = _extract_pdf_text(file_path)
    interview_agent.RESUME_STORE[resume_session_id] = resume_text

    # Clean up uploaded file after extraction (keep memory store only)
    try:
        file_path.unlink()
    except Exception:
        pass

    return {
        "resume_session_id": resume_session_id,
        "filename": file.filename,
        "text_length": len(resume_text),
        "status": "ok",
    }


class InterviewStartRequest(BaseModel):
    interview_mode: str  # graduate_reexam, industry_interview, general_mock
    focus_mode: Optional[str] = None  # balanced, fundamentals, project_experience
    role_or_major: Optional[str] = None
    grade: Optional[str] = None  # 大一, 大二, ..., 研二
    resume_session_id: Optional[str] = None
    num_questions: int = 5


@app.post("/api/interview/start")
def interview_start(request: InterviewStartRequest):
    """Start a new interview session with selected configuration."""
    result = interview_agent.start_interview(
        interview_mode=request.interview_mode,
        focus_mode=request.focus_mode,
        role_or_major=request.role_or_major,
        grade=request.grade,
        resume_session_id=request.resume_session_id,
        num_questions=request.num_questions,
    )
    return result


class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str


@app.post("/api/interview/answer")
def interview_answer(request: InterviewAnswerRequest):
    """Submit an answer and get interviewer feedback + next question."""
    result = interview_agent.submit_answer(
        session_id=request.session_id,
        user_answer=request.answer,
    )
    return result


@app.get("/api/interview/status/{session_id}")
def interview_status(session_id: str):
    """Get the current status of an interview session."""
    session = interview_agent.get_session(session_id)
    if not session:
        return {"error": "Session not found", "session_id": session_id}
    return {
        "session_id": session["session_id"],
        "status": session["status"],
        "mode": session["mode"],
        "role": session["role"],
        "grade": session["grade"],
        "current_idx": session["current_idx"],
        "total_questions": len(session["questions"]),
        "answers": session["answers"],
        "progress": {
            "current": min(session["current_idx"] + 1, len(session["questions"])),
            "total": len(session["questions"]),
        },
    }


@app.get("/api/interview/bank")
def interview_bank():
    """Return question bank summary for frontend dropdown configuration."""
    return interview_agent.get_bank_summary()
