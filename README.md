# Nanobot-Swarm

<div align="center">
  <h3>Nanobot AI Agent 可视化管理平台</h3>
  <p>一个现代化的 Web 前端，用于管理和监控 <a href="https://github.com/HKUDS/nanobot">Nanobot</a> AI Agent</p>

  <p>
    <img src="https://img.shields.io/badge/Next.js-16-black?style=flat&logo=next.js" alt="Next.js">
    <img src="https://img.shields.io/badge/React-19-blue?style=flat&logo=react" alt="React">
    <img src="https://img.shields.io/badge/TypeScript-5.9-blue?style=flat&logo=typescript" alt="TypeScript">
    <img src="https://img.shields.io/badge/TailwindCSS-3.4-cyan?style=flat&logo=tailwindcss" alt="TailwindCSS">
    <img src="https://img.shields.io/badge/Python-3.11+-yellow?style=flat&logo=python" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.100+-green?style=flat&logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/Docker-ready-blue?style=flat&logo=docker" alt="Docker">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

---

## 简介

Nanobot-Swarm 是基于 [Nanobot](https://github.com/HKUDS/nanobot)（港大开源的轻量级 AI Agent）开发的可视化管理平台。它提供了友好的 Web 界面来配置 LLM 提供商、管理会话、与 AI 进行对话交互，无需修改 Nanobot 源码即可实现完整的可视化管理。

### 核心特性

- 🎯 **一体化管理** - 前后端集成，开箱即用
- 📁 **清晰架构** - 前后端代码分离，独立维护
- 🐳 **容器化部署** - 支持 Docker 一键部署
- 🚀 **实时流式输出** - SSE 支持，实时显示 AI 响应
- 🔧 **灵活配置** - 支持 15+ LLM 提供商
- 🎨 **现代化 UI** - Glass-morphism 设计风格

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     Nanobot-Swarm                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐     ┌─────────────────────────────┐   │
│  │   Frontend      │     │       Backend               │   │
│  │   (Next.js)     │────▶│    (FastAPI + Nanobot)      │   │
│  │   Port: 5000    │     │    Port: 18790              │   │
│  └─────────────────┘     └─────────────────────────────┘   │
│         │                          │                        │
│    frontend/                  backend/                      │
│    ├── app/                   ├── api_server.py             │
│    ├── lib/                   ├── nanobot/                  │
│    └── types/                 └── requirements.txt          │
│                                    │                        │
│                                    ▼                        │
│                           ┌──────────────┐                 │
│                           │  ~/.nanobot/ │                 │
│                           └──────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
  - [Docker 一键部署（推荐）](#docker-一键部署推荐)
  - [单独启动前后端](#单独启动前后端)
- [配置说明](#配置说明)
- [项目结构](#项目结构)
- [API 文档](#api-文档)
- [开发指南](#开发指南)
- [常见问题](#常见问题)

---

## 功能特性

### 前端功能

- **仪表板** - 系统状态概览、快速导航
- **模型管理** - 15+ LLM 提供商配置
  - 网关：OpenRouter、AIHubMix、Custom
  - 国际：Anthropic、OpenAI、DeepSeek、Groq、Gemini
  - 国内：通义千问、Moonshot/Kimi、智谱GLM、MiniMax
  - 本地：vLLM
- **聊天界面** - 类 ChatGPT 的对话体验
  - 会话管理
  - 模型选择
  - 实时流式输出
  - 工具调用可视化
- **技能管理** - 自定义技能 SKILL.md 编辑
- **记忆管理** - 长期记忆和历史日志查看
- **渠道管理** - IM 平台集成（Telegram、Discord、Slack 等）
- **定时任务** - Cron 任务调度

### 后端功能

- **FastAPI 服务** - 高性能异步 API
- **SSE 流式响应** - 实时推送 AI 响应
- **会话管理** - 创建、读取、删除会话
- **配置热重载** - 无需重启更新配置
- **健康检查** - 服务状态监控

---

## 技术栈

### 前端 (`frontend/`)
- **框架**: Next.js 16 (App Router) + React 19
- **语言**: TypeScript 5.9
- **样式**: Tailwind CSS 3.4
- **图标**: Lucide React

### 后端 (`backend/`)
- **框架**: FastAPI + Uvicorn
- **核心**: Nanobot AI Agent
- **LLM 集成**: LiteLLM

### 部署
- **容器**: Docker + Docker Compose
- **数据持久化**: Volume 挂载

---

## 快速开始

### 前置条件

1. **Docker 部署**（推荐）
   - Docker 20.10+
   - Docker Compose 2.0+

2. **手动部署**
   - Node.js 18+
   - Python 3.11+
   - 已安装 [Nanobot](https://github.com/HKUDS/nanobot) 并完成初始化

---

### Docker 一键部署（推荐）

这是最简单的部署方式，适合快速体验和生产环境使用。

#### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/Nanobot-Swarm.git
cd Nanobot-Swarm
```

#### 2. 一键启动

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 3. 访问应用

- **前端界面**: http://localhost:5000
- **后端 API**: http://localhost:18790
- **健康检查**: http://localhost:18790/health

#### 4. 停止服务

```bash
docker-compose down
```

#### 数据持久化

默认使用 Docker Volume 存储数据。如需使用主机目录：

```yaml
# 编辑 docker-compose.yml，将 volumes 部分改为：
volumes:
  - ~/.nanobot:/root/.nanobot
```

---

### 单独启动前后端

适合开发调试或需要独立部署的场景。

#### 方式一：启动后端服务

```bash
# 进入后端目录
cd backend

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Nanobot（如果尚未安装）
pip install -e ./nanobot/nanobot-main

# 启动后端服务
python api_server.py

# 或使用 uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 18790
```

后端服务将在 http://localhost:18790 启动。

#### 方式二：启动前端服务

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 配置环境变量（可选）
cp ../.env.local.example .env.local
# 编辑 .env.local，设置 NANOBOT_API_URL=http://localhost:18790

# 开发模式
npm run dev

# 或生产模式
npm run build
npm start
```

前端服务将在 http://localhost:5000 启动。

#### 单独使用 Docker 长像

**构建镜像：**

```bash
# 在项目根目录执行
docker build -f Dockerfile.backend -t nanobot-swarm-backend .
docker build -f Dockerfile.frontend -t nanobot-swarm-frontend .
```

**运行容器：**

```bash
# 运行后端
docker run -d \
  --name nanobot-backend \
  -p 18790:18790 \
  -v ~/.nanobot:/root/.nanobot \
  nanobot-swarm-backend

# 运行前端
docker run -d \
  --name nanobot-frontend \
  -p 5000:5000 \
  -e NANOBOT_API_URL=http://host.docker.internal:18790 \
  nanobot-swarm-frontend
```

---

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NANOBOT_HOME` | Nanobot 配置目录 | `~/.nanobot` |
| `NANOBOT_API_URL` | 后端 API 地址 | `http://localhost:18790` |
| `NANOBOT_API_HOST` | 后端监听地址 | `0.0.0.0` |
| `NANOBOT_API_PORT` | 后端端口 | `18790` |
| `NEXT_PUBLIC_APP_NAME` | 应用名称 | Nanobot-Swarm |

### Nanobot 配置

首次使用需要初始化 Nanobot 配置：

```bash
# 初始化配置
nanobot onboard

# 配置文件位置
~/.nanobot/config.json
```

---

## 项目结构

```
Nanobot-Swarm/
├── frontend/                    # 前端项目 (Next.js)
│   ├── app/                     # 页面和 API 路由
│   │   ├── api/                 # API 代理层
│   │   │   ├── chat/            # 聊天相关 API
│   │   │   ├── models/          # 模型管理 API
│   │   │   └── ...
│   │   ├── chat/                # 聊天页面
│   │   ├── models/              # 模型管理页面
│   │   └── page.tsx             # 仪表板主页
│   ├── lib/                     # 工具函数库
│   │   └── nanobot/             # Nanobot 文件系统访问层
│   ├── types/                   # TypeScript 类型定义
│   ├── package.json             # Node.js 配置
│   ├── next.config.js           # Next.js 配置
│   └── tailwind.config.ts       # Tailwind 配置
│
├── backend/                     # 后端项目 (Python)
│   ├── api_server.py            # FastAPI 服务入口
│   ├── requirements.txt         # Python 依赖
│   └── nanobot/                 # Nanobot 源码
│       └── nanobot-main/
│
├── docker-compose.yml           # Docker Compose 配置
├── Dockerfile.frontend          # 前端 Dockerfile
├── Dockerfile.backend           # 后端 Dockerfile
├── .env.local.example           # 环境变量示例
├── README.md                    # 项目说明
├── Nanobot_Swarm_项目技术文档.md  # 技术文档
└── LICENSE                      # MIT 许可证
```

---

## API 文档

### 后端 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 服务信息 |
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/chat` | 发送消息（同步） |
| `POST` | `/api/chat/stream` | 发送消息（SSE 流式） |
| `GET` | `/api/sessions` | 获取会话列表 |
| `GET` | `/api/sessions/{key}` | 获取会话详情 |
| `DELETE` | `/api/sessions/{key}` | 删除会话 |
| `GET` | `/api/config` | 获取配置 |
| `POST` | `/api/config/reload` | 重载配置 |

### 示例请求

```bash
# 健康检查
curl http://localhost:18790/health

# 发送消息（流式）
curl -X POST http://localhost:18790/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_key": "test:123"}'

# 获取会话列表
curl http://localhost:18790/api/sessions
```

---

## 开发指南

### 本地开发

```bash
# 终端 1：启动后端
cd backend
pip install -r requirements.txt
pip install -e ./nanobot/nanobot-main
python api_server.py

# 终端 2：启动前端
cd frontend
npm install
npm run dev
```

### 代码检查

```bash
# 前端
cd frontend
npm run lint
npm run build

# 后端
cd backend
pip install ruff
ruff check .
```

### 构建生产版本

```bash
# 前端
cd frontend
npm run build

# Docker（在项目根目录）
docker-compose build
```

---

## 常见问题

### Q: 如何配置 API Key？

A: 在前端"模型管理"页面选择提供商，输入 API Key 保存即可。也可以直接编辑 `~/.nanobot/config.json`。

### Q: Docker 容器无法访问宿主机服务？

A: 使用 `host.docker.internal` 代替 `localhost`：
```yaml
environment:
  - NANOBOT_API_URL=http://host.docker.internal:18790
```

### Q: 如何备份数据？

A: 备份 `~/.nanobot/` 目录即可：
```bash
tar -czvf nanobot-backup.tar.gz ~/.nanobot/
```

### Q: 前端样式加载失败？

A: 确保 `output: 'standalone'` 已添加到 `frontend/next.config.js`，并重新构建镜像。

---

## 相关项目

- [Nanobot](https://github.com/HKUDS/nanobot) - 港大开源的轻量级 AI Agent

---

## License

MIT License

---

<p align="center">
  <sub>基于 <a href="https://github.com/HKUDS/nanobot">Nanobot</a> 构建</sub>
</p>
