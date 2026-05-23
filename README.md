# AI Agent Chat Platform

This project is a cloud-deployed AI chat platform for the challenge project.

Planned features:

- Public web page deployment
- LLM-based text chat
- Streaming response
- Intent recognition
- Task decomposition
- ReAct-style agent reasoning
- Multi-agent collaboration
- RAG retrieval
- Multimodal extension
- GitHub-based code submission

## Deployment Target

- Cloud Server: Alibaba Cloud ECS
- OS: Ubuntu 22.04
- Frontend: React + Vite
- Backend: FastAPI
- Web Server: Nginx

## Stage 1: Minimum Runnable Chat Web App

### Project Structure

```text
ai-agent-chat/
├── agent/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── data/
├── frontend/
│   ├── .env
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       └── index.css
├── scripts/
├── README.md
├── .env.example
├── .gitignore
└── AGENTS.md
```

### Run the Backend

```bash
cd /root/ai-agent-chat/backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Run the Frontend

```bash
cd /root/ai-agent-chat/frontend
npm run dev -- --host 0.0.0.0
```

### Browser Testing

- Frontend: http://39.106.227.41:5173
- Backend health: http://39.106.227.41:8000
- Backend API: http://39.106.227.41:8000/api/chat

### Security Group Ports

- TCP 8000 — FastAPI backend
- TCP 5173 — Vite frontend dev server
- TCP 80 — Nginx (production, not used in Stage 1)
- TCP 443 — HTTPS (production, not used in Stage 1)
