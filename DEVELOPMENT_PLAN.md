# DEVELOPMENT_PLAN.md

# AI Agent Chat Platform Development Plan

## 0. Current Development Focus

Current focus: **Implement Stage 1 ONLY**.

Kimi Code must not implement Stage 2-9 until explicitly instructed.

For the current stage:

- Do not implement real LLM calls.
- Do not implement RAG.
- Do not implement ReAct workflow.
- Do not implement multi-agent orchestration.
- Do not implement file upload or multimodal features.
- Do not modify Nginx configuration.
- Do not add database, Redis, Docker, Celery, message queue, vector database, or complex infrastructure.
- Do not overwrite existing files without first checking their contents.
- Do not delete existing files unless explicitly instructed.

The immediate priority is to build a stable minimum runnable frontend-backend chat web app.

The project should first prove that:

1. The frontend can be accessed from a browser.
2. The backend can be accessed from a browser or curl.
3. The frontend can call the backend successfully.
4. The backend can return structured mock chat data.
5. The frontend can display reply, intent, task decomposition, and execution steps.

Only after Stage 1 is fully verified should later stages be implemented.

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

The project preparation document requires a public cloud server, a web page accessible through a public URL, a simple chat service, model invocation through a specified model/API, GitHub code submission, and a short demo video. The server should also include the required SSH public keys for project inspection.

Current server environment:

- Cloud provider: Alibaba Cloud ECS
- OS: Ubuntu 22.04
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
├── README.md
├── .env.example
├── .gitignore
└── AGENTS.md
````

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

Important frontend decision:

* Use JavaScript + JSX.
* Do not use TypeScript unless explicitly instructed.
* Use Vite environment variables with the `VITE_` prefix.
* Read frontend environment variables through `import.meta.env`.

### Backend

* Python
* FastAPI
* Uvicorn
* Pydantic
* python-dotenv
* OpenAI-compatible API client

Backend model strategy:

The backend should use an OpenAI-compatible API client. This allows the same backend code to work with:

* OpenAI cloud API
* DeepSeek API
* OpenRouter API
* Alibaba Cloud DashScope OpenAI-compatible endpoint
* Local Ollama OpenAI-compatible endpoint
* Local vLLM OpenAI-compatible server
* Local Xinference OpenAI-compatible server

The model provider should be changed through `.env`, not by changing application code.

### Agent Layer

* Pure Python modules first
* Keep the architecture clear and readable
* Avoid over-engineering in the early stages
* Prefer explicit modules over hidden frameworks
* Keep response format stable across stages

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
18. Use JavaScript + JSX for the frontend in this project. Do not use TypeScript unless explicitly instructed.
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

The interaction should make the user feel that the system is:

* Understanding the question.
* Planning the task.
* Executing step by step.
* Producing the final answer.

The UI should be simple, stable, and demo-friendly.

Recommended Stage 1 layout:

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

The initial backend should expose these endpoints:

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
* `retrieved_context`: retrieved knowledge snippets. Empty in Stage 1.
* `mode`: current backend mode, such as `mock`, `llm`, or `agent`.

In Stage 1, this endpoint should return mock data.

In Stage 2, this endpoint should optionally call an LLM API.

In Stage 3 and later, this endpoint should call the agent orchestrator.

The frontend API contract must remain stable across stages.

---

## 7. Environment Variables

Use `.env` for private configuration.

Do not commit `.env`.

Use `.env.example` to document required variables.

### Backend Environment Variables

Backend should support OpenAI-compatible API configuration.

This makes the backend compatible with both cloud model providers and local model services.

Supported examples:

* OpenAI API
* DeepSeek API
* OpenRouter API
* Alibaba Cloud DashScope OpenAI-compatible endpoint
* Local Ollama OpenAI-compatible endpoint
* Local vLLM OpenAI-compatible server
* Local Xinference OpenAI-compatible server

Backend `.env.example`:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
```

Rules:

* Do not hardcode API keys.
* Do not expose backend API keys to frontend.
* If `OPENAI_API_KEY` is missing, backend should use mock mode.
* If `OPENAI_BASE_URL` is missing, use a safe default or mock mode.
* If `MODEL_NAME` is missing, use a safe default or mock mode.
* If model API call fails, return a friendly error and keep the response format stable.

### Frontend Environment Variables

Frontend `.env.example`:

```env
VITE_API_BASE_URL=http://YOUR_SERVER_PUBLIC_IP:8000
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

For development, the actual `frontend/.env` can contain:

```env
VITE_API_BASE_URL=http://SERVER_PUBLIC_IP:8000
```

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

For Stage 1 browser testing:

```text
Frontend:
http://SERVER_PUBLIC_IP:5173

Backend:
http://SERVER_PUBLIC_IP:8000
```

For final production demo:

```text
http://SERVER_PUBLIC_IP
```

In final production, users should not need to manually visit `:5173` or `:8000`.

---

## 9. Development Stages

---

# Stage 1: Minimum Runnable Chat Web App

## Goal

Build the simplest runnable frontend-backend chat system.

Current focus: **Stage 1 ONLY**.

Do not implement real LLM calls, RAG, ReAct, multi-agent orchestration, multimodal upload, or Nginx production deployment in this stage.

## Stage 1 Backend Requirements

Create a FastAPI backend in `backend/`.

Backend files should include:

```text
backend/
├── main.py
├── requirements.txt
└── .env.example
```

Required endpoints:

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

Frontend health check.

Expected response:

```json
{
  "status": "ok"
}
```

### POST `/api/chat`

Main mock chat endpoint.

Request:

```json
{
  "message": "user input here"
}
```

Response:

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

Backend must include CORS configuration.

Use:

```python
from fastapi.middleware.cors import CORSMiddleware
```

Development CORS policy:

* Allow `http://localhost:5173`
* Allow `http://127.0.0.1:5173`
* Allow `http://SERVER_PUBLIC_IP:5173`
* During early development, `allow_origins=["*"]` is acceptable for quick testing.

Backend must not use real LLM API in Stage 1.

Backend must not introduce database, Redis, vector database, Celery, Docker, or any complex infrastructure in Stage 1.

If chat history is needed in Stage 1, store it only in frontend state or simple in-memory backend data. Do not add persistent storage.

Backend `requirements.txt` must include at least:

```text
fastapi
uvicorn[standard]
python-dotenv
pydantic
```

## Stage 1 Frontend Requirements

Create a React + Vite frontend in `frontend/`.

Use JavaScript + JSX.

Do not use TypeScript unless explicitly instructed.

Frontend should include:

1. Title/header area.
2. Chat input box.
3. Send button.
4. Loading state.
5. Error state.
6. Reply display.
7. Intent display.
8. Task decomposition display.
9. Execution steps display.

Frontend must read backend API address from:

```js
import.meta.env.VITE_API_BASE_URL
```

Do not use:

```js
process.env
```

Frontend `.env.example` should include:

```env
VITE_API_BASE_URL=http://YOUR_SERVER_PUBLIC_IP:8000
```

For development, the actual `frontend/.env` can contain:

```env
VITE_API_BASE_URL=http://SERVER_PUBLIC_IP:8000
```

The frontend should call:

```text
POST ${VITE_API_BASE_URL}/api/chat
```

## Stage 1 Security Group Requirements

Alibaba Cloud security group must allow these ports during development:

```text
TCP 5173/5173  0.0.0.0/0   Vite frontend dev server
TCP 8000/8000  0.0.0.0/0   FastAPI backend
TCP 80/80      0.0.0.0/0   Nginx production web access
TCP 443/443    0.0.0.0/0   HTTPS production access
TCP 22/22      restricted or 0.0.0.0/0 for SSH
```

For Stage 1 browser testing:

```text
http://SERVER_PUBLIC_IP:5173
```

Backend health check:

```text
http://SERVER_PUBLIC_IP:8000
```

## Stage 1 Test Commands

Backend:

```bash
cd /root/ai-agent-chat/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd /root/ai-agent-chat/frontend
npm install
npm run dev -- --host 0.0.0.0
```

Expected browser access:

```text
http://SERVER_PUBLIC_IP:5173
```

Expected backend access:

```text
http://SERVER_PUBLIC_IP:8000
```

## Stage 1 Completion Criteria

Stage 1 is complete only if:

1. Backend can start without errors.
2. Frontend can start without errors.
3. Browser can access the frontend page.
4. Frontend can send a message to backend.
5. Backend returns mock structured response.
6. Frontend displays reply, intent, tasks, and steps.
7. No API key is required.
8. No real LLM call is made.
9. No Nginx config is modified.
10. README.md includes the correct Stage 1 run commands.

---

# Stage 2: LLM API Integration

## Goal

Replace mock final answer with optional LLM call while keeping the same `/api/chat` response format.

Backend should use an OpenAI-compatible API client, such as the OpenAI Python SDK.

This design should support:

* OpenAI cloud API
* DeepSeek API
* OpenRouter API
* Alibaba Cloud DashScope OpenAI-compatible API
* Local Ollama OpenAI-compatible endpoint
* Local vLLM OpenAI-compatible server
* Local Xinference OpenAI-compatible server

Required environment variables:

```env
OPENAI_API_KEY=
OPENAI_BASE_URL=
MODEL_NAME=
```

Rules:

1. If `OPENAI_API_KEY` is missing, use mock mode.
2. If `OPENAI_BASE_URL` is missing, use mock mode or a safe default.
3. If `MODEL_NAME` is missing, use mock mode or a safe default.
4. Do not expose API keys to frontend.
5. Keep `/api/chat` response format unchanged.
6. Add clear error handling.
7. If model API fails, return a friendly error while preserving the same response schema.

The API response should still include:

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

Do not implement multi-agent orchestration in Stage 2.

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

This ensures the frontend does not need to be modified when the backend evolves from direct LLM call to agent orchestration.

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
5. Generate final reply.
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

# Stage 7: Multimodal Extension Points

## Goal

Prepare for text-first multimodal extension.

Tasks:

1. Add frontend file upload component, but keep it optional.
2. Add backend placeholder endpoint:

   * `POST /api/upload`
3. Support image or PDF upload later.
4. For now, return file metadata only.
5. Do not implement complex OCR or speech processing unless required.

Future extension options:

* Image understanding API
* OCR
* Speech-to-text
* Text-to-speech
* Voice chat

Stage 7 should not break the text chat flow.

---

# Stage 8: Production Deployment

## Goal

Deploy final web app through Nginx.

Do not execute this stage until Stage 1-7 are stable.

Target:

Final public access should be:

```text
http://SERVER_PUBLIC_IP
```

Users should not need to manually visit `:5173` or `:8000`.

## Frontend Build

Build frontend:

```bash
cd /root/ai-agent-chat/frontend
npm run build
```

The generated frontend static files should be copied to:

```text
/var/www/ai-agent-chat
```

Suggested commands:

```bash
mkdir -p /var/www/ai-agent-chat
cp -r /root/ai-agent-chat/frontend/dist/* /var/www/ai-agent-chat/
```

## Backend Service

Backend should run as a systemd service.

Suggested backend service name:

```text
ai-agent-chat-backend.service
```

Backend should listen on:

```text
127.0.0.1:8000
```

or:

```text
0.0.0.0:8000
```

For Nginx reverse proxy, `127.0.0.1:8000` is preferred.

## Suggested Nginx Reverse Proxy Template

Do not apply this template until Stage 8.

```nginx
server {
    listen 80;
    server_name _;

    root /var/www/ai-agent-chat;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

After Nginx config changes:

```bash
nginx -t
systemctl reload nginx
```

Final test:

```text
http://SERVER_PUBLIC_IP
```

---

# Stage 9: Demo Preparation

## Goal

Prepare a 3-minute demo.

Demo flow:

1. Show GitHub repository.
2. Show server deployment URL.
3. Open public web page.
4. Ask a simple question.
5. Show intent recognition.
6. Show task decomposition.
7. Show execution steps.
8. Show final answer.
9. Optionally show RAG or multi-agent modules.
10. Briefly explain architecture.

Keep demo simple and reliable.

Suggested demo question:

```text
我想在阿里云服务器上部署一个 AI 聊天网页，请你帮我拆解任务并给出执行步骤。
```

Expected demo highlights:

* Public web page is accessible.
* Chat interface works.
* Backend responds.
* System recognizes intent.
* System decomposes task.
* System shows execution steps.
* GitHub repository contains source code and commit history.

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
Add LLM API integration
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

---

## 12. First Task for Kimi Code

Start with Stage 1 only.

Do not implement LLM, RAG, ReAct, multi-agent, upload, or Nginx deployment yet.

Task:

1. Read `AGENTS.md`, `README.md`, and `DEVELOPMENT_PLAN.md`.
2. Implement only Stage 1.
3. Create React + Vite frontend in `frontend/`.
4. Create FastAPI backend in `backend/`.
5. Implement mock `/api/chat`.
6. Configure backend CORS.
7. Build a clean chat UI.
8. Display reply, intent, tasks, steps, retrieved context, and mode.
9. Use `import.meta.env.VITE_API_BASE_URL` in frontend.
10. Provide exact test commands.
11. Do not modify Nginx configuration.
12. Do not delete existing files.
13. Do not commit automatically unless explicitly asked.

After finishing Stage 1, report:

1. Files created or modified.
2. How to run backend.
3. How to run frontend.
4. How to test in browser.
5. Any required security group ports.
6. Any known limitations.

---

## 13. Prompt to Give Kimi Code for Stage 1

Use this prompt when asking Kimi Code to start Stage 1:

```text
请先阅读 AGENTS.md、README.md 和 DEVELOPMENT_PLAN.md。

当前只允许执行 Stage 1：Minimum Runnable Chat Web App。

严格要求：
1. 不要实现真实 LLM。
2. 不要实现 RAG。
3. 不要实现 ReAct。
4. 不要实现多 Agent。
5. 不要实现文件上传或多模态。
6. 不要修改 Nginx。
7. 不要引入数据库、Redis、Docker、Celery。
8. 如果文件已经存在，先读取内容再修改，不要直接覆盖。
9. 前端使用 React + Vite + JavaScript + JSX。
10. 后端使用 FastAPI。
11. 后端必须配置 CORS。
12. 前端必须通过 import.meta.env.VITE_API_BASE_URL 读取后端地址。
13. /api/chat 必须返回 reply、intent、tasks、steps、retrieved_context、mode。
14. 完成后告诉我：修改了哪些文件、如何启动后端、如何启动前端、需要开放哪些端口、如何在浏览器测试。

现在开始实现 Stage 1。
```

---

## 14. Stage 1 Manual Verification Checklist

After Kimi Code finishes Stage 1, manually verify:

### Backend

```bash
cd /root/ai-agent-chat/backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Open:

```text
http://SERVER_PUBLIC_IP:8000
```

Expected:

```json
{
  "status": "ok",
  "message": "AI Agent Chat Backend is running"
}
```

Test chat API:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, please decompose my task."}'
```

Expected response should include:

```json
{
  "reply": "...",
  "intent": "...",
  "tasks": [],
  "steps": [],
  "retrieved_context": [],
  "mode": "mock"
}
```

### Frontend

```bash
cd /root/ai-agent-chat/frontend
npm run dev -- --host 0.0.0.0
```

Open:

```text
http://SERVER_PUBLIC_IP:5173
```

Expected:

1. Page loads.
2. Input box is visible.
3. Send button is visible.
4. User can send a message.
5. Backend reply is displayed.
6. Intent is displayed.
7. Tasks are displayed.
8. Steps are displayed.
9. No CORS error appears in browser console.

### Git

After verification:

```bash
cd /root/ai-agent-chat
git status
git add .
git commit -m "Implement minimum chat web app"
git push
```
