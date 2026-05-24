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
from agent import resume_review_agent

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

    preview = resume_text[:500] if resume_text else ""
    status = "ok"
    warning = None
    if not resume_text or not resume_text.strip():
        status = "warning"
        warning = "未能从 PDF 中提取文本，可能是扫描版图片 PDF。当前版本不支持 OCR。"

    return {
        "resume_session_id": resume_session_id,
        "resume_id": resume_session_id,
        "filename": file.filename,
        "size": len(resume_text),
        "extracted_text_preview": preview,
        "status": status,
        "warning": warning,
    }


class InterviewStartRequest(BaseModel):
    interview_mode: str  # graduate_reexam, industry_interview, general_mock
    focus_mode: Optional[str] = None  # balanced, fundamentals, project_experience
    role_or_major: Optional[str] = None
    target: Optional[str] = None
    grade: Optional[str] = None  # 大一, 大二, ..., 研二
    major: Optional[str] = None
    resume_session_id: Optional[str] = None
    resume_id: Optional[str] = None
    num_questions: int = 5
    profile_id: Optional[str] = None
    job_type: Optional[str] = "developer"


@app.post("/api/interview/start")
def interview_start(request: InterviewStartRequest):
    """Start a new interview session with selected configuration.
    If profile_id is provided, profile fields are used as defaults
    and can be overridden by explicit request parameters.
    If profile_id is expired, falls back to request fields.
    If resume is missing, starts without resume context.
    """
    warnings = []
    profile = None
    if request.profile_id:
        profile = interview_agent.get_profile(request.profile_id)
        if not profile:
            warnings.append("Profile expired. Using request fields instead.")

    # Resolve target: request.target > request.role_or_major > profile.target > profile.role_or_major
    target = (
        request.target
        if request.target is not None and request.target.strip()
        else (
            request.role_or_major
            if request.role_or_major is not None and request.role_or_major.strip()
            else (
                profile.get("target")
                if profile
                else None
            )
        )
    )

    if not target:
        return {"error": "Missing target. Please provide interview target or role."}

    grade = request.grade if request.grade is not None else (profile.get("grade") if profile else None)
    major = request.major if request.major is not None else (profile.get("major") if profile else None)
    resume_session_id = (
        request.resume_session_id
        if request.resume_session_id is not None
        else (
            request.resume_id
            if request.resume_id is not None
            else (profile.get("resume_id") if profile else None)
        )
    )

    # Check resume exists; if not, drop it and warn
    if resume_session_id and resume_session_id not in interview_agent.RESUME_STORE:
        warnings.append("Resume not found, starting interview without resume context.")
        resume_session_id = None

    interview_mode = request.interview_mode if request.interview_mode is not None else (profile.get("preferred_interview_mode") if profile else "general_mock")
    focus_mode = request.focus_mode if request.focus_mode is not None else (profile.get("preferred_focus_mode") if profile else None)
    job_type = request.job_type if request.job_type is not None else (profile.get("preferred_job_type") if profile else "developer")

    result = interview_agent.start_interview(
        interview_mode=interview_mode,
        focus_mode=focus_mode,
        role_or_major=target,
        grade=grade,
        resume_session_id=resume_session_id,
        num_questions=request.num_questions,
        profile=profile,
        job_type=job_type,
    )
    if result.get("total_questions", 0) == 0:
        return {
            "error": f"当前面试配置（{interview_mode} + {focus_mode or 'balanced'} + {target}）在题库中没有匹配题目。请尝试切换面试模式或目标岗位。"
        }
    if warnings:
        result["warnings"] = warnings
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


# ---------- Profile Endpoints ----------

class ProfileSaveRequest(BaseModel):
    grade: Optional[str] = None
    major: Optional[str] = None
    school_or_background: Optional[str] = None
    target: Optional[str] = None
    target_school_or_major: Optional[str] = None
    preferred_interview_mode: Optional[str] = "general_mock"
    preferred_focus_mode: Optional[str] = "balanced"
    resume_id: Optional[str] = None
    resume_session_id: Optional[str] = None
    resume_preview: Optional[str] = None
    profile_id: Optional[str] = None


@app.post("/api/profile/save")
def profile_save(request: ProfileSaveRequest):
    """Save or update a user profile."""
    data = request.model_dump(exclude_none=True)
    # Compatibility: resume_session_id maps to resume_id
    if "resume_session_id" in data and "resume_id" not in data:
        data["resume_id"] = data.pop("resume_session_id")
    profile = interview_agent.save_profile(data)
    return {
        "profile_id": profile["profile_id"],
        "profile": profile,
        "status": "success",
    }


@app.get("/api/profile/{profile_id}")
def profile_get(profile_id: str):
    """Get a user profile by ID."""
    profile = interview_agent.get_profile(profile_id)
    if not profile:
        return {"error": "Profile not found", "profile_id": profile_id}
    resume_preview = ""
    if profile.get("resume_id"):
        resume_text = interview_agent.RESUME_STORE.get(profile.get("resume_id"), "")
        resume_preview = resume_text[:300] if resume_text else ""
    return {
        "profile_id": profile["profile_id"],
        "profile": profile,
        "resume_preview": resume_preview,
    }


# ---------- Resume Review Endpoints ----------

class ResumeReviewRequest(BaseModel):
    resume_id: Optional[str] = None
    resume_session_id: Optional[str] = None
    profile_id: Optional[str] = None


@app.post("/api/resume/review")
def resume_review(request: ResumeReviewRequest):
    """Generate a structured resume review based on resume text and optional profile.
    Accepts resume_id, resume_session_id, or profile_id (from which resume_id is resolved).
    """
    candidate_resume_id = request.resume_id or request.resume_session_id

    if not candidate_resume_id and request.profile_id:
        profile = interview_agent.get_profile(request.profile_id)
        if profile:
            candidate_resume_id = profile.get("resume_id")

    if not candidate_resume_id:
        return {"error": "No resume_id provided. Please upload a PDF resume first."}

    resume_text = interview_agent.RESUME_STORE.get(candidate_resume_id)
    if resume_text is None:
        return {
            "error": "Resume not found. The server may have restarted or the resume was not uploaded successfully. Please upload the resume again.",
            "resume_id": candidate_resume_id,
        }

    profile = None
    if request.profile_id:
        profile = interview_agent.get_profile(request.profile_id)

    result = resume_review_agent.review_resume(resume_text, profile)
    return result
