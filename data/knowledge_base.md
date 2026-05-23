# Project Knowledge Base

## Project Overview

AI Agent Chat Platform 是一个部署在 Alibaba Cloud ECS 上的任务型 AI Agent 聊天平台。

- 前端使用 React + Vite。
- 后端使用 FastAPI。
- 模型调用使用 Kimi API / Moonshot Open Platform。
- 系统通过 IntentAgent、PlannerAgent、ReactAgent、RagAgent、Orchestrator 协同工作。

平台目标是提供一个透明、可控的 AI 任务助手，让用户感受到系统正在理解请求、规划任务、逐步执行并返回清晰答案。

## Deployment Notes

- 开发阶段使用 5173 访问 Vite 前端，8000 访问 FastAPI 后端。
- 生产阶段计划使用 Nginx 统一入口。
- React build 产物由 Nginx 托管。
- /api 请求由 Nginx 反向代理到 FastAPI。
- backend/.env 存储 Kimi API Key，不提交到 GitHub。
- 部署环境为 Alibaba Cloud ECS，操作系统 Ubuntu 22.04。

## Agent Architecture

- IntentAgent 负责识别用户意图。
- PlannerAgent 负责生成任务拆解。
- ReactAgent 负责生成 Action / Observation Trace。
- RagAgent 负责从 knowledge_base.md 检索上下文。
- Orchestrator 负责编排所有 Agent 和 Kimi API 调用。

所有 Agent 均为纯 Python 模块，不依赖外部框架。Orchestrator 通过调用各 Agent 模块完成完整对话流程。

## Supported Intents

系统支持以下意图类别：

- general_chat
- technical_question
- coding_task
- deployment_help
- research_summary
- document_qa
- multimodal_request
- unknown

## Security Notes

- 不要把 API Key 写入源代码。
- 不要提交 backend/.env。
- 不展示 hidden chain-of-thought。
- 只展示用户可见的执行摘要。
- 生产环境建议关闭直接暴露 8000，只通过 Nginx /api 访问。
- 后端 CORS 配置为开发阶段允许所有来源，生产环境应收紧。

## RAG 说明

RAG（Retrieval-Augmented Generation）在本项目中通过 RagAgent 实现。

当前版本使用 keyword-based retrieval：
- 从 data/knowledge_base.md 读取文本。
- 按章节切分为 chunks。
- 使用关键词匹配进行检索。
- 不使用 embedding，不使用向量数据库。

RAG 的作用是为 Kimi API 提供项目相关的本地知识上下文，使回答更贴近项目实际情况。

## Demo Questions

以下是适合测试系统的示例问题：

- 这个项目的技术架构是什么？
- 项目如何部署到阿里云？
- 系统有哪些 Agent？
- RAG 在这个项目里起什么作用？
- 为什么不能暴露 hidden chain-of-thought？
