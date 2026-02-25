#!/usr/bin/env python3
"""
Nanobot API Server
提供HTTP API供前端调用Nanobot功能
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional
import uvicorn

# 添加 nanobot-main 到 Python 路径
nanobot_path = Path(__file__).parent / "nanobot" / "nanobot-main"
sys.path.insert(0, str(nanobot_path))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
except ImportError:
    print("FastAPI not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel

# 导入 nanobot 模块
try:
    from nanobot.config.loader import load_config
    from nanobot.bus.queue import MessageBus
    from nanobot.agent.loop import AgentLoop
except ImportError:
    print("Nanobot modules not found. Please check the installation.")
    sys.exit(1)

app = FastAPI(title="Nanobot API Server", version="0.1.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class ChatRequest(BaseModel):
    message: str
    session_key: Optional[str] = "web:direct"
    model: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    data: dict
    error: Optional[str] = None

# 全局变量
config = None
bus = None
agent_loop = None
provider = None

async def init_nanobot():
    """初始化 Nanobot"""
    global config, bus, agent_loop, provider

    try:
        # 加载配置
        config = load_config()

        # 创建消息总线
        from nanobot.providers.litellm_provider import LiteLLMProvider
        from nanobot.config.loader import get_config_path

        bus = MessageBus()

        # 创建 provider
        p = config.get_provider()
        model = config.agents.defaults.model
        if not (p and p.api_key) and not model.startswith("bedrock/"):
            print("Warning: No API key configured. Please set one in ~/.nanobot/config.json")

        provider = LiteLLMProvider(
            api_key=p.api_key if p else None,
            api_base=config.get_api_base(),
            default_model=model,
            extra_headers=p.extra_headers if p else None,
            provider_name=config.get_provider_name(),
        )

        # 创建 agent loop
        agent_loop = AgentLoop(
            bus=bus,
            provider=provider,
            workspace=config.workspace_path,
            model=config.agents.defaults.model,
            temperature=config.agents.defaults.temperature,
            max_tokens=config.agents.defaults.max_tokens,
            max_iterations=config.agents.defaults.max_tool_iterations,
            memory_window=config.agents.defaults.memory_window,
            brave_api_key=config.tools.web.search.api_key or None,
            exec_config=config.tools.exec,
            restrict_to_workspace=config.tools.restrict_to_workspace,
            mcp_servers=config.tools.mcp_servers,
        )

        print("✓ Nanobot initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to initialize Nanobot: {e}")
        return False

async def reload_nanobot():
    """重新加载 Nanobot 配置"""
    global config, agent_loop, provider, bus

    try:
        print("🔄 Reloading Nanobot configuration...")

        # 关闭旧的 MCP 连接
        if agent_loop:
            await agent_loop.close_mcp()

        # 重新加载配置
        config = load_config()

        # 调试：显示 zhipu provider 的 API key 状态
        p = config.get_provider()
        model = config.agents.defaults.model
        print(f"Debug: Model = {model}")
        print(f"Debug: Matched provider name = {config.get_provider_name()}")

        if p:
            print(f"Debug: Provider has api_key = {bool(p.api_key)}")
            if p.api_key:
                key_preview = p.api_key[:8] + "..." if len(p.api_key) > 8 else p.api_key
                print(f"Debug: API key (first 8 chars) = {key_preview}")
        else:
            print("Debug: No provider matched")

        # 重新创建 provider
        from nanobot.providers.litellm_provider import LiteLLMProvider

        provider = LiteLLMProvider(
            api_key=p.api_key if p else None,
            api_base=config.get_api_base(),
            default_model=model,
            extra_headers=p.extra_headers if p else None,
            provider_name=config.get_provider_name(),
        )

        # 重新创建 agent loop
        agent_loop = AgentLoop(
            bus=bus,
            provider=provider,
            workspace=config.workspace_path,
            model=config.agents.defaults.model,
            temperature=config.agents.defaults.temperature,
            max_tokens=config.agents.defaults.max_tokens,
            max_iterations=config.agents.defaults.max_tool_iterations,
            memory_window=config.agents.defaults.memory_window,
            brave_api_key=config.tools.web.search.api_key or None,
            exec_config=config.tools.exec,
            restrict_to_workspace=config.tools.restrict_to_workspace,
            mcp_servers=config.tools.mcp_servers,
        )

        print("✓ Nanobot configuration reloaded successfully")
        print(f"  Model: {config.agents.defaults.model}")
        print(f"  Provider: {config.get_provider_name()}")
        print(f"  API Base: {config.get_api_base()}")
        return True
    except Exception as e:
        print(f"✗ Failed to reload Nanobot: {e}")
        return False

@app.on_event("startup")
async def startup():
    """启动时初始化"""
    await init_nanobot()

@app.on_event("shutdown")
async def shutdown():
    """关闭时清理资源"""
    global agent_loop
    if agent_loop:
        await agent_loop.close_mcp()
    print("Nanobot API Server shutdown complete")

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Nanobot API Server",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "nanobot_initialized": agent_loop is not None
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """处理聊天请求"""
    global agent_loop, provider, config

    if agent_loop is None:
        return ChatResponse(
            success=False,
            data={},
            error="Nanobot not initialized"
        )

    try:
        # 生成 session key
        session_key = request.session_key or f"web:{asyncio.get_event_loop().time()}"

        # 如果指定了模型，临时更新 agent_loop 的模型
        original_model = None
        if request.model and agent_loop:
            original_model = agent_loop.model
            agent_loop.model = request.model
            print(f"Using model: {request.model}")

        try:
            # 调用 agent 处理消息
            response = await agent_loop.process_direct(
                request.message,
                session_key
            )
        finally:
            # 恢复原始模型
            if original_model:
                agent_loop.model = original_model

        return ChatResponse(
            success=True,
            data={
                "response": response,
                "session_key": session_key
            }
        )
    except Exception as e:
        print(f"Error in chat: {e}")
        return ChatResponse(
            success=False,
            data={},
            error=str(e)
        )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    处理流式聊天请求，返回SSE事件流

    事件类型:
    - content: 文本内容块
    - reasoning: 推理内容块（DeepSeek-R1等模型）
    - tool_call_start: 工具调用开始
    - tool_call_end: 工具调用结束
    - iteration_start: Agent迭代开始
    - done: 处理完成
    - error: 错误
    """
    global agent_loop, config

    if agent_loop is None:
        return ChatResponse(
            success=False,
            data={},
            error="Nanobot not initialized"
        )

    async def event_generator():
        """生成SSE事件流"""
        try:
            # 生成 session key
            session_key = request.session_key or f"web:{asyncio.get_event_loop().time()}"

            # 如果指定了模型，临时更新 agent_loop 的模型
            original_model = None
            if request.model and agent_loop:
                original_model = agent_loop.model
                agent_loop.model = request.model
                print(f"Stream using model: {request.model}")

            try:
                # 调用流式处理方法
                async for event in agent_loop.process_stream(
                    content=request.message,
                    session_key=session_key,
                    channel="web",
                    chat_id=session_key.split(":")[-1] if ":" in session_key else "stream"
                ):
                    # 格式化为SSE事件
                    event_data = json.dumps(event, ensure_ascii=False)
                    yield f"data: {event_data}\n\n"
            finally:
                # 恢复原始模型
                if original_model:
                    agent_loop.model = original_model

        except Exception as e:
            print(f"Error in stream: {e}")
            error_event = json.dumps({"type": "error", "error": str(e)}, ensure_ascii=False)
            yield f"data: {error_event}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        }
    )

@app.get("/api/sessions")
async def list_sessions():
    """列出所有会话"""
    try:
        from nanobot.session.manager import SessionManager
        from pathlib import Path

        session_manager = SessionManager(config.workspace_path)
        sessions_dir = Path(config.workspace_path) / ".." / "sessions"

        if not sessions_dir.exists():
            return {"success": True, "data": {"sessions": []}}

        sessions = []
        for file in sessions_dir.glob("*.jsonl"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        metadata = json.loads(lines[0])
                        messages_count = len(lines) - 1
                        session_key = file.stem.replace('_', ':')
                        sessions.append({
                            "key": session_key,
                            "filename": file.name,
                            "metadata": metadata,
                            "messageCount": messages_count
                        })
            except Exception as e:
                print(f"Error reading session {file}: {e}")
                continue

        # 按更新时间排序
        sessions.sort(
            key=lambda x: x.get("metadata", {}).get("updated_at", ""),
            reverse=True
        )

        return {"success": True, "data": {"sessions": sessions}}
    except Exception as e:
        print(f"Error listing sessions: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/sessions/{session_key}")
async def get_session(session_key: str):
    """获取会话详情"""
    try:
        from pathlib import Path

        sessions_dir = Path(config.workspace_path) / ".." / "sessions"
        session_file = sessions_dir / f"{session_key.replace(':', '_')}.jsonl"

        if not session_file.exists():
            return {"success": False, "error": "Session not found"}

        with open(session_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            return {"success": False, "error": "Empty session"}

        metadata = json.loads(lines[0])
        messages = [json.loads(line) for line in lines[1:]]

        return {
            "success": True,
            "data": {
                "key": session_key,
                "metadata": metadata,
                "messages": messages
            }
        }
    except Exception as e:
        print(f"Error getting session: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/api/sessions/{session_key}")
async def delete_session(session_key: str):
    """删除会话"""
    try:
        from pathlib import Path

        sessions_dir = Path(config.workspace_path) / ".." / "sessions"
        session_file = sessions_dir / f"{session_key.replace(':', '_')}.jsonl"

        if session_file.exists():
            session_file.unlink()
            return {"success": True, "data": {"message": "Session deleted"}}
        else:
            return {"success": False, "error": "Session not found"}
    except Exception as e:
        print(f"Error deleting session: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/config/reload")
async def reload_config():
    """重新加载配置"""
    try:
        success = await reload_nanobot()
        if success:
            return {
                "success": True,
                "data": {
                    "message": "Configuration reloaded successfully",
                    "model": config.agents.defaults.model,
                    "provider": config.get_provider_name()
                }
            }
        else:
            return {"success": False, "error": "Failed to reload configuration"}
    except Exception as e:
        print(f"Error reloading config: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/config")
async def get_config():
    """获取当前配置"""
    try:
        # 返回配置的基本信息（不包括敏感的API密钥）
        return {
            "success": True,
            "data": {
                "model": config.agents.defaults.model,
                "provider": config.get_provider_name(),
                "api_base": config.get_api_base(),
                "temperature": config.agents.defaults.temperature,
                "max_tokens": config.agents.defaults.max_tokens
            }
        }
    except Exception as e:
        print(f"Error getting config: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import sys
    import io
    import os
    # 设置标准输出编码为 UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 允许通过环境变量配置主机和端口
    host = os.getenv("NANOBOT_API_HOST", "0.0.0.0")
    port = int(os.getenv("NANOBOT_API_PORT", "18790"))

    print("🤖 Nanobot API Server")
    print("=" * 40)
    print(f"Starting server on http://{host}:{port}")
    print()

    uvicorn.run(
        "api_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
