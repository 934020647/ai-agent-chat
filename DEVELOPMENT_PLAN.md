# DEVELOPMENT_PLAN.md

# AI Agent Chat Platform Development Plan

## 0. Current Development Focus

Current focus: **Stage 2: Kimi API Integration**.

Stage 1 has already been implemented and manually verified:

- Frontend can be opened in browser.
- Backend can be accessed.
- Frontend can call backend.
- User can send a message.
- Page can display reply, intent, tasks, and steps.
- Current backend mode is mock.

Kimi Code must now implement **Stage 2 only**.

For Stage 2:

- Implement Kimi API cloud model integration.
- Use Kimi API / Moonshot Open Platform as the only model provider.
- Use OpenAI Python SDK because Kimi API is OpenAI-compatible.
- Do not implement local model deployment.
- Do not implement Ollama.
- Do not implement vLLM.
- Do not implement Xinference.
- Do not implement local GPU inference.
- Do not implement RAG.
- Do not implement ReAct workflow.
- Do not implement multi-agent orchestration.
- Do not implement file upload or multimodal features.
- Do not modify Nginx configuration.
- Do not add database, Redis, Docker, Celery, message queue, vector database, or complex infrastructure.
- Do not overwrite existing files without first checking their contents.
- Do not delete existing files unless explicitly instructed.

The immediate priority is to replace the Stage 1 mock final answer with an optional real Kimi API call while keeping the `/api/chat` response format stable.

---

## 1. Project Background

This project is built for a challenge preparation task.

The final deliverable should be:

1. A public web page deployed on an Alibaba Cloud ECS server.
2. A simple AI chat service accessible through the web page.
3. The backend can call a specified LLM model through an API.
4. The system can support text chat first, and optionally voice or multimodal input later.
5. All source code should be committed to a public GitHub repository.
6. The final demo should be recordable by phone or screen recording software.

The project preparation requirement is:

- Public cloud server.
- Public web URL.
- Simple web chat service.
- Model invocation through a specified model/API.
- GitHub code submission.
- Short demo video.

Current server environment:

- Cloud provider: Alibaba Cloud ECS
- OS: Ubuntu 22.04
- Public IP: `39.106.227.41`
- Project root: `/root/ai-agent-chat`
- Frontend directory: `/root/ai-agent-chat/frontend`
- Backend directory: `/root/ai-agent-chat/backend`
- Agent directory: `/root/ai-agent-chat/agent`
- Data directory: `/root/ai-agent-chat/data`
- Scripts directory: `/root/ai-agent-chat/scripts`
- Web server: Nginx installed and running
- Node.js: installed
- Python: installed
- GitHub remote: configured

Current repository structure:

```text
ai-agent-chat/
├── agent/
├── backend/
├── data/
├── frontend/
├── scripts/
├── AGENTS.md
├── DEVELOPMENT_PLAN.md
├── README.md
├── .env.example
└── .gitignore
````

Stage 1 has already created:

```text
backend/
├── main.py
├── requirements.txt
└── .env.example

frontend/
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
├── .env.example
└── src/
    ├── App.jsx
    ├── index.css
    └── main.jsx
```

---

## 2. Overall Product Goal

Build a user-friendly AI Agent Chat web platform.

The platform should not be just a simple ChatGPT wrapper. It should demonstrate an agent-oriented architecture with:

1. Accurate user intent recognition.
2. Explicit task decomposition.
3. Step-by-step execution feedback.
4. ReAct-style reasoning and tool-use structure.
5. RAG-ready knowledge retrieval.
6. Multi-agent collaboration extension.
7. Multimodal extension points.
8. Deployment-ready frontend and backend.

The first priority is to build a stable minimum viable product. Advanced features must be added incrementally.

The final product should make the user feel that the system is:

* Understanding the request.
* Planning the task.
* Executing the task step by step.
* Returning a clear final answer.
* Showing transparent progress without exposing hidden chain-of-thought.

---

## 3. Core Technical Stack

Use the following stack unless there is a strong reason to change it.

### Frontend

* React
* Vite
* JavaScript + JSX
* Plain CSS or CSS modules
* Fetch API for backend calls

Important frontend rules:

* Use JavaScript + JSX.
* Do not use TypeScript unless explicitly instructed.
* Use Vite environment variables with the `VITE_` prefix.
* Read frontend environment variables through `import.meta.env`.
* Do not use `process.env` in frontend code.

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* python-dotenv
* OpenAI Python SDK
* Kimi API / Moonshot Open Platform

### Backend Model Strategy

This project uses **cloud model API only**.

The only model provider for Stage 2 is:

* Kimi API / Moonshot Open Platform

Kimi API is OpenAI-compatible, so the backend should use the OpenAI Python SDK.

Default backend model configuration:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.moonshot.cn/v1
MODEL_NAME=kimi-k2.6
```

Rules:

* Use the OpenAI Python SDK to call Kimi API.
* Do not implement local model deployment.
* Do not implement Ollama.
* Do not implement vLLM.
* Do not implement Xinference.
* Do not implement local GPU inference.
* Do not hardcode API keys.
* Do not expose API keys to frontend.
* Store real API keys only in `backend/.env`.
* Keep `backend/.env.example` and root `.env.example` as templates only.
* If `OPENAI_API_KEY` is missing, backend should continue using mock mode.
* If Kimi API call fails, backend should return a friendly fallback response while preserving the same response schema.

### Agent Layer

* Pure Python modules first.
* Keep the architecture clear and readable.
* Avoid over-engineering in the early stages.
* Prefer explicit modules over hidden frameworks.
* Keep response format stable across stages.

### Deployment

* Nginx
* systemd service for backend
* Static frontend build served by Nginx
* Backend reverse proxy under `/api`

### Version Control

* Git
* GitHub public repository
* Commit after every stable milestone

---

## 4. Important Development Rules

Kimi Code must follow these rules:

1. Do not hardcode API keys.
2. Never commit `.env`.
3. Use `.env.example` to document required environment variables.
4. Keep every development stage runnable.
5. Do not delete existing files unless explicitly instructed.
6. Do not modify server-level configuration unless explicitly instructed.
7. Do not change Nginx configuration during early development stages.
8. Do not implement all advanced features at once.
9. Prefer simple, stable, explainable code over complex abstractions.
10. After modifying code, provide the exact commands needed to test it.
11. After each stage, update README.md if the run method changes.
12. Keep frontend and backend decoupled.
13. Keep agent modules independent and easy to inspect.
14. Every API response should be easy for the frontend to render.
15. All functions should have clear names and simple comments where needed.
16. If a file already exists, inspect its content before modifying it.
17. Do not overwrite existing files unless necessary.
18. Use JavaScript + JSX for the frontend. Do not use TypeScript unless explicitly instructed.
19. For frontend environment variables, only use variables prefixed with `VITE_`.
20. In Vite frontend code, read environment variables through `import.meta.env`, not `process.env`.
21. The frontend should read backend base URL from `import.meta.env.VITE_API_BASE_URL`.
22. Keep the `/api/chat` response format stable across all stages.
23. Stage 1 should use mock data only.
24. Stage 1 should not introduce persistent storage. If chat history is needed, store it only in frontend state or simple backend memory.
25. Backend must include CORS configuration during development.
26. After each stage, update README.md if run commands, environment variables, project structure, or deployment steps change.
27. Update AGENTS.md only if agent workflow, project structure, or build commands significantly change.
28. Do not expose hidden chain-of-thought. Only expose concise user-facing execution summaries.
29. Do not commit generated cache files, build outputs, virtual environments, or API keys.
30. If a command may affect system configuration, ask for confirmation before running it.
31. This project uses cloud model APIs only.
32. The primary cloud model provider is Kimi API / Moonshot Open Platform.
33. Do not implement local model deployment, Ollama, vLLM, Xinference, or GPU inference unless explicitly instructed later.
34. Use the OpenAI Python SDK to call Kimi API through the OpenAI-compatible endpoint.
35. Default backend model configuration should be:

    * `OPENAI_BASE_URL=https://api.moonshot.cn/v1`
    * `MODEL_NAME=kimi-k2.6`
36. Keep all real Kimi API keys only in `backend/.env`.
37. Do not put Kimi API keys in frontend files.
38. Do not put Kimi API keys in README.md, DEVELOPMENT_PLAN.md, AGENTS.md, `.env.example`, or source code.
39. Do not commit `backend/.env`.
40. If Stage 2 changes the backend response behavior, the frontend must still receive the same response fields.

---

## 5. Target User Experience

The final interface should look like a lightweight AI task assistant.

The page should include:

1. A clean title area.
2. A chat input box.
3. A send button.
4. A response display area.
5. A panel showing recognized intent.
6. A panel showing task decomposition.
7. A panel showing execution steps.
8. A panel showing retrieved knowledge or tool results later.
9. Clear loading state.
10. Clear error message if backend or model API fails.
11. A visible `mode` field showing `mock`, `llm`, `agent`, or `error_fallback`.

The interaction should make the user feel that the system is:

* Understanding the question.
* Planning the task.
* Executing step by step.
* Producing the final answer.

The UI should be simple, stable, and demo-friendly.

Recommended layout:

```text
+--------------------------------------------------+
| AI Agent Chat Platform                           |
| A transparent task-oriented AI assistant         |
+--------------------------------------------------+
| User input box                                   |
| [Send]                                           |
+--------------------------------------------------+
| Final Reply                                      |
| ...                                              |
+--------------------------------------------------+
| Mode                                             |
| mock / llm / agent / error_fallback              |
+--------------------------------------------------+
| Intent                                           |
| ...                                              |
+--------------------------------------------------+
| Task Decomposition                               |
| 1. ...                                           |
| 2. ...                                           |
+--------------------------------------------------+
| Execution Steps                                  |
| 1. ...                                           |
| 2. ...                                           |
+--------------------------------------------------+
```

---

## 6. Backend API Design

The backend should expose these endpoints:

### GET `/`

Health check.

Expected response:

```json
{
  "status": "ok",
  "message": "AI Agent Chat Backend is running"
}
```

### GET `/api/health`

Health check for frontend.

Expected response:

```json
{
  "status": "ok"
}
```

### POST `/api/chat`

Main chat endpoint.

Request:

```json
{
  "message": "user input here"
}
```

Response:

```json
{
  "reply": "final answer here",
  "intent": "recognized intent here",
  "tasks": [
    "task 1",
    "task 2"
  ],
  "steps": [
    "step 1",
    "step 2"
  ],
  "retrieved_context": [],
  "mode": "mock or llm"
}
```

Response fields:

* `reply`: final user-facing answer.
* `intent`: recognized user intent.
* `tasks`: list of decomposed tasks.
* `steps`: user-facing execution progress summaries.
* `retrieved_context`: retrieved knowledge snippets. Empty before RAG.
* `mode`: current backend mode, such as `mock`, `llm`, `agent`, or `error_fallback`.

In Stage 1, this endpoint returns mock data.

In Stage 2, this endpoint should optionally call Kimi API.

In Stage 3 and later, this endpoint should call the agent orchestrator.

The frontend API contract must remain stable across stages.

---

## 7. Environment Variables

Use `.env` for private configuration.

Do not commit `.env`.

Use `.env.example` to document required variables.

### Backend Environment Variables

This project uses cloud API only.

Primary model provider:

* Kimi API / Moonshot Open Platform

Kimi API is OpenAI-compatible, so the backend should use the OpenAI Python SDK.

Backend `.env.example`:

```env
# Kimi API / Moonshot Open Platform
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.moonshot.cn/v1
MODEL_NAME=kimi-k2.6
```

Backend real `.env` example:

```env
OPENAI_API_KEY=your_real_kimi_api_key_here
OPENAI_BASE_URL=https://api.moonshot.cn/v1
MODEL_NAME=kimi-k2.6
```

Rules:

* Do not hardcode API keys.
* Do not expose backend API keys to frontend.
* Do not commit `backend/.env`.
* The backend should read the API key from `backend/.env`.
* If `OPENAI_API_KEY` is missing, backend should use mock mode.
* If `OPENAI_BASE_URL` is missing, default to `https://api.moonshot.cn/v1`.
* If `MODEL_NAME` is missing, default to `kimi-k2.6`.
* If model API call fails, return a friendly error and keep the response format stable.
* Do not implement local model inference, Ollama, vLLM, Xinference, or GPU deployment in this project.

### Frontend Environment Variables

Frontend `.env.example`:

```env
VITE_API_BASE_URL=http://YOUR_SERVER_PUBLIC_IP:8000
```

Actual development `frontend/.env`:

```env
VITE_API_BASE_URL=http://39.106.227.41:8000
```

Important Vite rules:

* Vite only exposes environment variables prefixed with `VITE_`.
* Frontend code must read the value through:

```js
import.meta.env.VITE_API_BASE_URL
```

* Do not use:

```js
process.env
```

* Vite environment variables are statically embedded during `npm run build`.
* If `VITE_API_BASE_URL` changes in production, the frontend must be rebuilt.

For production behind Nginx reverse proxy, the frontend can later use:

```env
VITE_API_BASE_URL=
```

or:

```env
VITE_API_BASE_URL=http://SERVER_PUBLIC_IP
```

depending on the final routing design.

---

## 8. Alibaba Cloud Security Group Requirements

During development, the Alibaba Cloud ECS security group must allow:

```text
TCP 22/22      SSH and VS Code Remote-SSH
TCP 80/80      Nginx HTTP production access
TCP 443/443    HTTPS production access
TCP 5173/5173  Vite frontend development server
TCP 8000/8000  FastAPI backend development server
```

Recommended development rules:

```text
TCP 5173/5173  0.0.0.0/0   Vite frontend dev server
TCP 8000/8000  0.0.0.0/0   FastAPI backend
TCP 80/80      0.0.0.0/0   Nginx production web access
TCP 443/443    0.0.0.0/0   HTTPS production access
TCP 22/22      restricted to developer IP if possible
```

For development browser testing:

```text
Frontend:
http://39.106.227.41:5173

Backend:
http://39.106.227.41:8000
```

For final production demo:

```text
http://39.106.227.41
```

In final production, users should not need to manually visit `:5173` or `:8000`.

---

## 9. Development Stages

---

# Stage 1: Minimum Runnable Chat Web App

## Status

Stage 1 has already been implemented and manually verified.

Verified features:

1. Backend starts without errors.
2. Frontend starts without errors.
3. Browser can access frontend page.
4. Frontend can send a message to backend.
5. Backend returns mock structured response.
6. Frontend displays reply, intent, tasks, and steps.
7. No API key is required.
8. No real LLM call is made.
9. No Nginx config is modified.

## Stage 1 Backend Summary

Backend files:

```text
backend/
├── main.py
├── requirements.txt
└── .env.example
```

Required endpoints:

* `GET /`
* `GET /api/health`
* `POST /api/chat`

Stage 1 response format:

```json
{
  "reply": "mock final answer here",
  "intent": "general_chat",
  "tasks": [
    "Understand the user's request",
    "Prepare a structured response"
  ],
  "steps": [
    "Received the user message",
    "Classified the request intent",
    "Generated a mock response",
    "Returned structured data to the frontend"
  ],
  "retrieved_context": [],
  "mode": "mock"
}
```

Backend includes CORS configuration.

Backend must continue to support mock mode as fallback in later stages.

## Stage 1 Frontend Summary

Frontend files:

```text
frontend/
├── index.html
├── package.json
├── package-lock.json
├── vite.config.js
├── .env.example
└── src/
    ├── App.jsx
    ├── index.css
    └── main.jsx
```

Frontend must continue to:

1. Display input box.
2. Send message to backend.
3. Display reply.
4. Display intent.
5. Display task decomposition.
6. Display execution steps.
7. Display mode if provided.

---

# Stage 2: Kimi API Integration

## Goal

Replace the Stage 1 mock final answer with an optional real Kimi API call while keeping the same `/api/chat` response format.

The backend should use Kimi API / Moonshot Open Platform as the primary and only cloud model provider.

Kimi API is OpenAI-compatible, so the backend should use the OpenAI Python SDK.

Do not implement:

* Local model deployment
* Ollama
* vLLM
* Xinference
* GPU inference
* Any local LLM service
* RAG
* ReAct
* Multi-agent orchestration
* File upload
* Multimodal features
* Nginx production deployment

## Required Backend Environment Variables

Backend should read these variables from:

```text
/root/ai-agent-chat/backend/.env
```

Required content:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.moonshot.cn/v1
MODEL_NAME=kimi-k2.6
```

Real example:

```env
OPENAI_API_KEY=your_real_kimi_api_key_here
OPENAI_BASE_URL=https://api.moonshot.cn/v1
MODEL_NAME=kimi-k2.6
```

Important:

* The real API key must only be placed in `backend/.env`.
* Never commit `backend/.env`.
* Never put real API key into `.env.example`.
* Never put real API key into frontend files.
* Never put real API key into README.md.
* Never put real API key into source code.

## Required Dependencies

Backend `requirements.txt` should include:

```text
fastapi
uvicorn[standard]
python-dotenv
pydantic
openai
```

## Stage 2 Backend Rules

1. Keep `/api/chat` response format unchanged.
2. Use the OpenAI Python SDK to call Kimi API.
3. Read `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `MODEL_NAME` from environment variables.
4. If `OPENAI_API_KEY` is missing, continue using mock mode.
5. If `OPENAI_BASE_URL` is missing, default to `https://api.moonshot.cn/v1`.
6. If `MODEL_NAME` is missing, default to `kimi-k2.6`.
7. Do not expose API keys to frontend.
8. Do not write API keys into source code.
9. Do not commit `backend/.env`.
10. If API call fails, return a friendly fallback response while preserving the same response schema.
11. Do not modify frontend page structure unless necessary.
12. Do not implement RAG, ReAct, multi-agent orchestration, file upload, or Nginx deployment in Stage 2.

## Expected `/api/chat` Response Schema

The response must still include:

```json
{
  "reply": "...",
  "intent": "...",
  "tasks": [],
  "steps": [],
  "retrieved_context": [],
  "mode": "llm or mock"
}
```

## Suggested Kimi API Call Behavior

When `OPENAI_API_KEY` exists:

1. Build a concise system prompt.
2. Send the user message to Kimi API.
3. Use the model answer as `reply`.
4. Keep `intent`, `tasks`, and `steps` generated through simple deterministic logic for now.
5. Set `mode` to `llm`.

When `OPENAI_API_KEY` is missing:

1. Use the existing Stage 1 mock response.
2. Set `mode` to `mock`.

When Kimi API fails:

1. Return a user-friendly fallback reply.
2. Set `mode` to `error_fallback` or `mock`.
3. Include a safe execution step such as:

   * `Kimi API call failed, returned fallback response`
4. Do not expose sensitive error details to frontend.
5. Do not expose API key, request headers, stack traces, or internal paths.

## Suggested System Prompt for Kimi API

Use a short system prompt:

```text
You are an AI task assistant for a cloud-deployed AI Agent Chat Platform. 
Answer the user's question clearly and helpfully. 
When appropriate, explain tasks in a structured way. 
Do not reveal hidden chain-of-thought. 
Only provide concise user-facing reasoning summaries.
```

The backend should not rely on Kimi to return JSON in Stage 2. The backend can use Kimi only for the final `reply`, and keep `intent`, `tasks`, and `steps` deterministic.

## Stage 2 Test Commands

Install dependency:

```bash
cd /root/ai-agent-chat/backend
source .venv/bin/activate
pip install -r requirements.txt
```

Create backend `.env`:

```bash
cd /root/ai-agent-chat/backend
nano .env
```

Content:

```env
OPENAI_API_KEY=your_real_kimi_api_key_here
OPENAI_BASE_URL=https://api.moonshot.cn/v1
MODEL_NAME=kimi-k2.6
```

Run backend:

```bash
cd /root/ai-agent-chat/backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Test backend:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"请用三句话介绍一下人工智能 Agent"}'
```

Expected:

* If `.env` contains valid Kimi API key, response `mode` should be `llm`.
* If `.env` is missing or key is empty, response `mode` should be `mock`.
* If Kimi API fails, response should keep the schema and use friendly fallback.

## Stage 2 Completion Criteria

Stage 2 is complete only if:

1. Backend starts without errors.
2. `/api/chat` works without `backend/.env` and returns mock mode.
3. `/api/chat` works with valid Kimi API key and returns LLM-generated reply.
4. API key is not committed.
5. Frontend still works without structural changes.
6. Response fields remain:

   * `reply`
   * `intent`
   * `tasks`
   * `steps`
   * `retrieved_context`
   * `mode`
7. README.md explains how to configure Kimi API.
8. `.env.example` documents Kimi API variables but contains no real key.
9. `.gitignore` prevents `backend/.env` from being committed.

---

# Stage 3: Intent Recognition and Task Decomposition

## Goal

Introduce a lightweight agent orchestrator while keeping the frontend API contract unchanged.

Important transition rule:

Starting from Stage 3, `/api/chat` should no longer directly generate the full response inside `main.py`.

Instead, `/api/chat` should call:

```python
orchestrator.handle_chat(message)
```

However, the response format of `/api/chat` must remain unchanged.

This ensures the frontend does not need to be modified when the backend evolves from direct Kimi API call to agent orchestration.

Starting from Stage 3, the Kimi API call should be moved into or reused by the agent orchestrator. The orchestrator may call Kimi API internally through the same OpenAI-compatible client wrapper introduced in Stage 2.

Required modules:

```text
agent/
├── __init__.py
├── intent_agent.py
├── planner_agent.py
└── orchestrator.py
```

Initial intent categories:

```text
general_chat
technical_question
coding_task
deployment_help
research_summary
document_qa
multimodal_request
unknown
```

The orchestrator should:

1. Receive user message.
2. Call IntentAgent.
3. Call PlannerAgent.
4. Generate execution steps.
5. Generate final reply using Kimi API when available.
6. Return the same response schema used in Stage 1 and Stage 2.

Do not change frontend code unless absolutely necessary.

---

# Stage 4: ReAct-Style Workflow

## Goal

Add a lightweight ReAct-style execution structure.

The purpose is to show a transparent and controllable agent execution process.

Tasks:

1. Add `agent/react_agent.py`.
2. Implement a simple loop structure:

   * Thought
   * Action
   * Observation
   * Final
3. Do not expose private chain-of-thought.
4. Only expose concise user-facing execution steps.
5. Simulate tool calls first.
6. Later connect real tools if needed.

User-facing step format:

```json
[
  "Analyzed the user request",
  "Selected the appropriate response strategy",
  "Generated the answer",
  "Checked the response for completeness"
]
```

Important:

* Do not display hidden reasoning.
* Display only safe and concise progress summaries.
* Keep `/api/chat` response format stable.
* Keep the frontend unchanged unless a new panel is absolutely necessary.

---

# Stage 5: RAG-Ready Retrieval

## Goal

Add simple knowledge retrieval.

Tasks:

1. Add `data/knowledge_base.md`.
2. Add `agent/rag_agent.py`.
3. Implement simple keyword retrieval first.
4. Return relevant snippets in `retrieved_context`.
5. Frontend should display retrieved context in a collapsible or separate panel.

Do not add vector database in the first RAG version.

Later optional upgrade:

* FAISS
* Chroma
* sentence-transformers
* embedding API

Response format should remain:

```json
{
  "reply": "...",
  "intent": "...",
  "tasks": [],
  "steps": [],
  "retrieved_context": [],
  "mode": "agent"
}
```

---

# Stage 6: Multi-Agent Collaboration

## Goal

Refactor the system into a simple multi-agent architecture.

Agent roles:

1. IntentAgent

   * Understand user intent.
2. PlannerAgent

   * Break user request into tasks.
3. RagAgent

   * Retrieve relevant context.
4. ReactAgent

   * Execute step-by-step reasoning workflow.
5. ResponseAgent

   * Generate final user-facing answer.
6. Orchestrator

   * Coordinate all agents.

Keep the architecture easy to demo.

The point is not to build a complex autonomous system. The point is to show a clear agent pipeline.

Suggested structure:

```text
agent/
├── __init__.py
├── intent_agent.py
├── planner_agent.py
├── rag_agent.py
├── react_agent.py
├── response_agent.py
└── orchestrator.py
```

The orchestrator should be the only entry point used by the backend route.

The backend route should remain simple:

```python
result = orchestrator.handle_chat(request.message)
return result
```

---

## 10. Suggested Final Directory Structure

Target structure:

```text
ai-agent-chat/
├── agent/
│   ├── __init__.py
│   ├── intent_agent.py
│   ├── planner_agent.py
│   ├── rag_agent.py
│   ├── react_agent.py
│   ├── response_agent.py
│   └── orchestrator.py
├── backend/
│   ├── .env.example
│   ├── main.py
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       └── schemas.py
├── data/
│   └── knowledge_base.md
├── frontend/
│   ├── .env.example
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── api.js
│       └── styles.css
├── scripts/
│   ├── run_backend.sh
│   ├── run_frontend.sh
│   └── deploy.sh
├── AGENTS.md
├── DEVELOPMENT_PLAN.md
├── README.md
├── .gitignore
└── .env.example
```

This structure can be adjusted if needed, but changes should be explained.

---

## 11. Recommended Git Workflow

After each stable stage:

```bash
git status
git add .
git commit -m "Describe the stage completed"
git push
```

Suggested commits:

```text
Add development plan
Implement minimum chat web app
Add Kimi API integration
Add intent recognition and planning
Add ReAct-style agent workflow
Add simple RAG retrieval
Add multi-agent orchestrator
Add deployment scripts
Configure production deployment
Update README for final demo
```

Do not commit:

```text
.env
.venv/
node_modules/
dist/
__pycache__/
*.pyc
*.log
```

Before committing Stage 2, always run:

```bash
git status
git add --dry-run .
```

Confirm that these files are not included:

```text
backend/.env
frontend/.env
backend/.venv/
frontend/node_modules/
frontend/dist/
```

---

## 12. Prompt to Give Kimi Code for Stage 2

Use this prompt when asking Kimi Code to start Stage 2:

```text
请先阅读 AGENTS.md、README.md 和 DEVELOPMENT_PLAN.md。

Stage 1 已经验收通过。现在只允许执行 Stage 2：Kimi API Integration。

严格要求：

1. 只做 Kimi API 云端模型接入，不做本地模型部署。
2. 不要实现 Ollama、vLLM、Xinference、本地 GPU 推理或任何本地 LLM 服务。
3. 后端使用 OpenAI Python SDK 调用 Kimi API / Moonshot Open Platform。
4. Kimi API 使用 OpenAI-compatible 配置：
   - OPENAI_BASE_URL=https://api.moonshot.cn/v1
   - MODEL_NAME=kimi-k2.6
5. 从 backend/.env 读取：
   - OPENAI_API_KEY
   - OPENAI_BASE_URL
   - MODEL_NAME
6. 如果 OPENAI_API_KEY 缺失，继续使用 Stage 1 的 mock mode，不要报错。
7. 如果 OPENAI_BASE_URL 缺失，默认使用 https://api.moonshot.cn/v1。
8. 如果 MODEL_NAME 缺失，默认使用 kimi-k2.6。
9. 不要把 API Key 写入代码。
10. 不要提交 backend/.env。
11. 更新 backend/.env.example、根目录 .env.example 和 README.md，说明如何配置 Kimi API。
12. backend/requirements.txt 增加 openai。
13. 保持 /api/chat 的响应格式不变，必须仍然返回：
    - reply
    - intent
    - tasks
    - steps
    - retrieved_context
    - mode
14. 当前不要实现 RAG、ReAct、多 Agent、文件上传、多模态或 Nginx 部署。
15. 不要大改前端页面结构，只允许为了显示 mode 或错误信息做必要小改。
16. API 调用失败时要返回友好 fallback，不要把敏感错误堆栈暴露给前端。
17. 完成后告诉我：
    - 修改了哪些文件
    - 如何创建 backend/.env
    - 如何启动后端
    - 如何测试 mock mode
    - 如何测试 Kimi API mode

现在开始实现 Stage 2。
```

---

## 13. Stage 2 Manual Verification Checklist

After Kimi Code finishes Stage 2, manually verify:

### Check `.gitignore`

```bash
cd /root/ai-agent-chat
cat .gitignore
```

Must include:

```gitignore
.env
.env.local
backend/.env
frontend/.env
.venv/
venv/
node_modules/
dist/
build/
__pycache__/
*.pyc
*.log
```

### Test mock mode without API key

Temporarily remove backend `.env` if it exists:

```bash
cd /root/ai-agent-chat/backend
mv .env .env.bak
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"请介绍一下这个项目"}'
```

Expected:

```json
{
  "mode": "mock"
}
```

### Create real Kimi API `.env`

```bash
cd /root/ai-agent-chat/backend
nano .env
```

Content:

```env
OPENAI_API_KEY=your_real_kimi_api_key_here
OPENAI_BASE_URL=https://api.moonshot.cn/v1
MODEL_NAME=kimi-k2.6
```

Restart backend:

```bash
cd /root/ai-agent-chat/backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Test Kimi API mode:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"请用三句话介绍一下人工智能 Agent"}'
```

Expected:

```json
{
  "mode": "llm"
}
```

`reply` should be generated by Kimi API.

### Test frontend

Run frontend:

```bash
cd /root/ai-agent-chat/frontend
npm run dev -- --host 0.0.0.0
```

Open:

```text
http://39.106.227.41:5173
```

Expected:

1. Page loads.
2. User can send a message.
3. Backend returns Kimi-generated reply if `.env` is valid.
4. Mode displays `llm`.
5. Intent, tasks, and steps still display normally.
6. No CORS error appears in browser console.

### Git after verification

Before committing:

```bash
cd /root/ai-agent-chat
git status
git add --dry-run .
```

Confirm not included:

```text
backend/.env
frontend/.env
backend/.venv/
frontend/node_modules/
frontend/dist/
```

Commit:

```bash
git add .
git commit -m "Add Kimi API integration"
git push
```
