# VersaClaw

<div align="center">
  <h3>多模态 AI Agent 可视化管理平台</h3>
  <p>基于 <a href="https://github.com/HKUDS/nanobot">Nanobot</a> 的现代化 Web 管理界面，支持文本、语音、图像等多模态交互</p>

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

**VersaClaw** (/ˈvɜːrsə klɔː/) 是基于 [Nanobot](https://github.com/HKUDS/nanobot)（港大开源的轻量级 AI Agent）开发的多模态可视化管理平台。

> **Versa** 源自 Latin "versatilis"，意为多面、通用、灵活；**Claw** 延续了 Nanobot 生态的"爪"概念，象征精准与力量。

它提供了友好的 Web 界面来配置 LLM 提供商、管理会话、与 AI 进行对话交互，无需修改 Nanobot 源码即可实现完整的可视化管理。未来将支持语音、图像等多模态交互能力。

### 核心特性

- 🎯 **一体化管理** - 前后端集成，开箱即用
- 📦 **简洁依赖** - 通过 PyPI 引用 nanobot-ai，代码更精简
- 🐳 **容器化部署** - 支持 Docker 一键部署
- 🚀 **实时流式输出** - SSE 支持，实时显示 AI 响应
- 🔧 **灵活配置** - 支持 15+ LLM 提供商
- 🎨 **现代化 UI** - Glass-morphism 设计风格
- 🔮 **多模态规划** - 架构预留语音、图像等多模态扩展能力

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                       VersaClaw                              │
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
│    ├── lib/                   └── requirements.txt          │
│    └── types/                       │                       │
│                                     ▼                       │
│                          ┌──────────────────┐              │
│                          │  nanobot-ai      │ (PyPI)       │
│                          │  ~/.nanobot/     │              │
│                          └──────────────────┘              │
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
- [路线图](#路线图)
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
- **核心**: [nanobot-ai](https://pypi.org/project/nanobot-ai/) (PyPI)
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

---

### Docker 一键部署（推荐）

这是最简单的部署方式，适合快速体验和生产环境使用。

#### 1. 克隆仓库

```bash
git clone https://github.com/SeanXu98/VersaClaw.git
cd VersaClaw
```

#### 2. 一键启动

```bash
# 构建并启动所有服务
docker compose up -d

# 查看日志
docker compose logs -f
```

#### 3. 访问应用

- **前端界面**: http://localhost:5000
- **后端 API**: http://localhost:18790
- **API 文档**: http://localhost:18790/docs
- **健康检查**: http://localhost:18790/health

#### 4. 停止服务

```bash
docker compose down
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

# 安装 Python 依赖（会自动安装 nanobot-ai）
pip install -r requirements.txt

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

#### 单独使用 Docker 镜像

**构建镜像：**

```bash
# 在项目根目录执行
docker build -f Dockerfile.backend -t versaclaw-backend .
docker build -f Dockerfile.frontend -t versaclaw-frontend .
```

**运行容器：**

```bash
# 运行后端
docker run -d \
  --name versaclaw-backend \
  -p 18790:18790 \
  -v ~/.nanobot:/root/.nanobot \
  versaclaw-backend

# 运行前端
docker run -d \
  --name versaclaw-frontend \
  -p 5000:5000 \
  -e NANOBOT_API_URL=http://host.docker.internal:18790 \
  versaclaw-frontend
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
| `NEXT_PUBLIC_APP_NAME` | 应用名称 | VersaClaw |

### Nanobot 配置

首次使用需要初始化 Nanobot 配置：

```bash
# 安装 nanobot-ai
pip install nanobot-ai

# 初始化配置
nanobot onboard

# 配置文件位置
~/.nanobot/config.json
```

---

## 项目结构

```
VersaClaw/
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
│   └── requirements.txt         # Python 依赖 (包含 nanobot-ai)
│
├── docker-compose.yml           # Docker Compose 配置
├── Dockerfile.frontend          # 前端 Dockerfile
├── Dockerfile.backend           # 后端 Dockerfile
├── .env.local.example           # 环境变量示例
├── README.md                    # 项目说明
└── LICENSE                      # MIT 许可证
```

---

## API 文档

### 后端 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/` | 服务信息 |
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/config` | 获取配置 |
| `POST` | `/api/config/reload` | 重载配置 |
| `POST` | `/api/chat` | 发送消息（同步） |
| `POST` | `/api/chat/stream` | 发送消息（SSE 流式） |
| `GET` | `/api/chat/sessions` | 获取会话列表 |
| `GET` | `/api/chat/sessions/{key}` | 获取会话详情 |
| `DELETE` | `/api/chat/sessions/{key}` | 删除会话 |
| `GET` | `/api/models/available` | 获取可用模型列表 |
| `GET` | `/api/models/providers` | 获取提供商配置 |
| `GET` | `/api/skills` | 获取技能列表 |
| `GET` | `/api/memory` | 获取记忆内容 |
| `GET` | `/api/cron` | 获取定时任务 |

### 示例请求

```bash
# 健康检查
curl http://localhost:18790/health

# 发送消息（流式）
curl -X POST http://localhost:18790/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_key": "test:123"}'

# 获取会话列表
curl http://localhost:18790/api/chat/sessions

# 获取配置
curl http://localhost:18790/api/config
```

完整 API 文档请访问：http://localhost:18790/docs

---

## 开发指南

### 本地开发

```bash
# 终端 1：启动后端
cd backend
pip install -r requirements.txt
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
docker compose build
```

---

## 路线图

### v0.1.x (当前)
- [x] 文本对话
- [x] 多 LLM 提供商支持
- [x] 会话管理
- [x] 技能/记忆管理

### v0.2.x (计划中)
- [ ] 语音输入/输出
- [ ] 图像理解
- [ ] 文件上传处理

### v0.3.x (未来)
- [ ] 视频理解
- [ ] 实时语音对话
- [ ] 多模态 Agent 编排

---

## 多模态接入规划

VersaClaw 的架构设计充分考虑了未来多模态能力的扩展，以下是计划中的接入方向：

### 🎤 语音模态

| 功能 | 技术方案 | 状态 |
|------|----------|------|
| 语音输入 (ASR) | OpenAI Whisper API / 本地 Whisper 模型 | 计划中 |
| 语音输出 (TTS) | OpenAI TTS / Edge TTS / 本地 TTS 引擎 | 计划中 |
| 实时语音对话 | WebRTC + WebSocket 流式传输 | 规划中 |
| 语音活动检测 (VAD) | Silero VAD / Web VAD API | 规划中 |

**预期用户体验**：
```
用户语音输入 → ASR 转文字 → LLM 处理 → TTS 合成 → 播放语音响应
```

### 🖼️ 图像模态

| 功能 | 技术方案 | 状态 |
|------|----------|------|
| 图像理解 | GPT-4V / Claude Vision / Gemini Vision | 计划中 |
| 图像生成 | DALL-E 3 / Stable Diffusion / Midjourney API | 规划中 |
| 图像编辑 | Inpainting / Outpainting 能力 | 规划中 |
| OCR 文字识别 | GPT-4V 内置 / Tesseract 备选 | 计划中 |

**预期用户体验**：
```
上传图片 → Vision 模型分析 → 结合上下文对话 → 可选生成新图片
```

### 📹 视频模态

| 功能 | 技术方案 | 状态 |
|------|----------|------|
| 视频理解 | GPT-4V (帧抽取) / Gemini 1.5 Pro | 规划中 |
| 视频摘要 | 关键帧提取 + 多模态理解 | 规划中 |
| 实时视频流 | WebRTC + 实时帧分析 | 未来规划 |

### 📄 文档模态

| 功能 | 技术方案 | 状态 |
|------|----------|------|
| PDF 解析 | PyPDF / pdfplumber + OCR | 计划中 |
| Office 文档 | python-docx / openpyxl | 计划中 |
| 代码文件 | 语法高亮 + 智能分析 | 计划中 |

### 🔧 技术架构预留

```
┌─────────────────────────────────────────────────────────────┐
│                    VersaClaw 多模态架构                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  文本输入    │  │  语音输入    │  │  图像输入    │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│              ┌───────────────────────┐                     │
│              │   Modal Router        │                     │
│              │   (模态路由/预处理)     │                     │
│              └───────────┬───────────┘                     │
│                          ▼                                  │
│              ┌───────────────────────┐                     │
│              │   Multi-Modal Agent   │                     │
│              │   (统一多模态处理)      │                     │
│              └───────────┬───────────┘                     │
│                          ▼                                  │
│         ┌────────────────┼────────────────┐                │
│         │                │                │                 │
│         ▼                ▼                ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   LLM API   │  │   TTS API   │  │ Vision API  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 多模态 API 扩展规划

```python
# 未来 API 设计草案
POST /api/chat/multimodal
{
  "session_key": "user:123",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "这张图片里有什么？"},
        {"type": "image_url", "url": "data:image/jpeg;base64,..."}
      ]
    }
  ],
  "modalities": ["text", "audio"]  # 期望的输出模态
}
```

如果你对多模态功能有特定需求或建议，欢迎在 [Issues](https://github.com/SeanXu98/VersaClaw/issues) 中讨论！

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

### Q: 后端启动报错找不到 nanobot 模块？

A: 确保已安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

---

## 相关项目

- [Nanobot](https://github.com/HKUDS/nanobot) - 港大开源的轻量级 AI Agent
- [nanobot-ai (PyPI)](https://pypi.org/project/nanobot-ai/) - Nanobot Python 包

---

## License

MIT License

---

<p align="center">
  <sub>基于 <a href="https://github.com/HKUDS/nanobot">Nanobot</a> 构建 | 多模态 AI Agent 平台</sub>
</p>
