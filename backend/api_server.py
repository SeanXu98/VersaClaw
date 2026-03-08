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
from typing import Optional, List
import uvicorn

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse, FileResponse
    from pydantic import BaseModel
    from typing import List
    import uuid
    import base64
except ImportError:
    print("FastAPI not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn"])
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel

# 导入 nanobot 模块 (通过 pip install nanobot-ai 安装)
try:
    from nanobot.config.loader import load_config
    from nanobot.bus.queue import MessageBus
    from nanobot.agent.loop import AgentLoop
except ImportError:
    print("Nanobot modules not found. Please install: pip install nanobot-ai")
    sys.exit(1)

# 导入流式处理模块
from stream_processor import StreamProcessor, ImageData as StreamImageData

app = FastAPI(title="Nanobot API Server", version="0.1.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 图片上传相关配置和数据模型 ====================

class ImageData(BaseModel):
    """图片数据模型"""
    id: str
    url: str
    thumbnail_url: Optional[str] = None
    mime_type: str
    size: Optional[int] = None
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class UploadConfig:
    """图片上传配置"""
    UPLOAD_DIR: str = os.path.expanduser("~/.nanobot/uploads/images")
    THUMBNAIL_DIR: str = os.path.expanduser("~/.nanobot/uploads/images/thumbnails")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_TYPES: list = ["image/png", "image/jpeg", "image/gif", "image/webp"]


class ChatRequest(BaseModel):
    """聊天请求模型（支持多模态）"""
    message: str
    session_key: Optional[str] = "web:direct"
    model: Optional[str] = None
    images: Optional[List[ImageData]] = None  # 支持多模态图片


class UploadResponse(BaseModel):
    """上传响应模型"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


# Vision 模型检测模式
VISION_MODEL_PATTERNS = [
    # OpenAI
    "gpt-4-vision", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
    # Anthropic
    "claude-3", "claude-3.5",
    # Google
    "gemini-1.5", "gemini-2",
    # OpenRouter
    "openrouter/",
    # 智谱 GLM Vision 系列
    "glm-4v", "glm-4.6v", "glm-4.1v",
    # 其他可能的 Vision 模型
    "vision", "llava",
]


def is_vision_model(model: str) -> bool:
    """检测模型是否支持 Vision 能力"""
    if not model:
        return False
    model_lower = model.lower()
    return any(pattern in model_lower for pattern in VISION_MODEL_PATTERNS)


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

        # 获取 provider 配置
        p = config.get_provider()
        model = config.agents.defaults.model

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
    - image_processing: 图片处理状态
    - done: 处理完成
    - error: 错误

    注意：此端点使用 StreamProcessor 封装类处理流式响应。
    这是临时方案，等待 nanobot 官方支持 process_stream 方法。
    详见 stream_processor.py 文件。
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

            # 获取请求中的图片（如果有）
            images = request.images
            model = request.model or (agent_loop.model if agent_loop else None)

            # 如果指定了模型，临时更新 agent_loop 的模型
            original_model = None
            if request.model and agent_loop:
                original_model = agent_loop.model
                agent_loop.model = request.model
                print(f"Stream using model: {request.model}")

            try:
                # 构建消息内容（支持多模态）
                if images:
                    content = build_multimodal_content(request.message, images)
                    print(f"Multimodal content: {len(content)} blocks (1 text + {len(images)} images)")
                else:
                    content = request.message

                # 创建流式处理器
                processor = StreamProcessor(
                    agent_loop=agent_loop,
                    upload_dir=UploadConfig.UPLOAD_DIR,
                    vision_check_fn=is_vision_model
                )

                # 转换图片数据格式
                stream_images = None
                if images:
                    stream_images = [
                        StreamImageData(
                            id=img.id,
                            url=img.url,
                            thumbnail_url=img.thumbnail_url,
                            mime_type=img.mime_type,
                            size=img.size,
                            filename=img.filename,
                            width=img.width,
                            height=img.height
                        )
                        for img in images
                    ]

                # 使用 StreamProcessor 生成流式事件
                async for event in processor.process_stream(
                    content=content,
                    session_key=session_key,
                    images=stream_images,
                    model=model,
                    channel="web",
                    timeout=120.0
                ):
                    yield event

            finally:
                # 恢复原始模型
                if original_model:
                    agent_loop.model = original_model

        except Exception as e:
            print(f"Error in stream: {e}")
            import traceback
            traceback.print_exc()
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
        from pathlib import Path

        # 会话目录在 workspace 目录下的 sessions 子目录
        sessions_dir = Path(config.workspace_path) / "sessions"

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

                        # 提取第一条用户消息作为标题
                        title = "新会话"
                        for line in lines[1:]:  # 跳过 metadata 行
                            try:
                                msg = json.loads(line)
                                if msg.get("role") == "user":
                                    content = msg.get("content", "")
                                    # 处理多模态内容格式
                                    if isinstance(content, list):
                                        # 提取文本内容
                                        text_parts = []
                                        for block in content:
                                            if isinstance(block, dict) and block.get("type") == "text":
                                                text = block.get("text", "")
                                                # 过滤掉图片标记
                                                text = text.replace("[image]", "").replace("[图片:", "").strip()
                                                if text and not text.startswith("temp_"):
                                                    text_parts.append(text)
                                        title = " ".join(text_parts).strip()[:50]  # 限制50字符
                                    elif isinstance(content, str):
                                        # 过滤掉图片标记
                                        title = content.replace("[image]", "").replace("[图片:", "").strip()[:50]
                                    if title:
                                        break
                            except:
                                continue

                        if not title:
                            title = "新会话"

                        sessions.append({
                            "key": session_key,
                            "filename": file.name,
                            "metadata": metadata,
                            "messageCount": messages_count,
                            "title": title
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

        # 会话目录在 workspace 目录下的 sessions 子目录
        sessions_dir = Path(config.workspace_path) / "sessions"
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

        # 会话目录在 workspace 目录下的 sessions 子目录
        sessions_dir = Path(config.workspace_path) / "sessions"
        session_file = sessions_dir / f"{session_key.replace(':', '_')}.jsonl"

        if session_file.exists():
            session_file.unlink()
            return {"success": True, "data": {"message": "Session deleted"}}
        else:
            return {"success": False, "error": "Session not found"}
    except Exception as e:
        print(f"Error deleting session: {e}")
        return {"success": False, "error": str(e)}


# ==================== 图片上传 API ====================

def get_upload_dir() -> Path:
    """获取上传目录路径"""
    upload_dir = Path.home() / ".nanobot" / "uploads" / "images"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 创建缩略图目录
    thumbnails_dir = upload_dir / "thumbnails"
    thumbnails_dir.mkdir(parents=True, exist_ok=True)

    return upload_dir


@app.post("/api/upload/image")
async def upload_image(file: UploadFile = File(...)):
    """上传单张图片"""

    # 验证文件类型
    if file.content_type not in UploadConfig.ALLOWED_TYPES:
        return UploadResponse(
            success=False,
            error=f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(UploadConfig.ALLOWED_TYPES)}"
        )

    # 读取文件内容
    content = await file.read()

    # 验证文件大小
    if len(content) > UploadConfig.MAX_FILE_SIZE:
        return UploadResponse(
            success=False,
            error=f"文件太大，最大允许 {UploadConfig.MAX_FILE_SIZE / 1024 / 1024}MB"
        )

    try:
        # 生成唯一文件 ID
        image_id = str(uuid.uuid4())

        # 确定文件扩展名
        ext = Path(file.filename).suffix.lower() or ".png"

        # 保存文件
        upload_dir = get_upload_dir()
        file_path = upload_dir / f"{image_id}{ext}"

        with open(file_path, "wb") as f:
            f.write(content)

        # 获取图片尺寸（可选）
        width, height = None, None
        try:
            # 尝试使用 Pillow 获取尺寸
            try:
                from PIL import Image
                img = Image.open(file_path)
                width, height = img.size
                img.close()
            except ImportError:
                pass  # Pillow 未安装，跳过尺寸获取
        except Exception:
            pass  # 图片读取失败，跳过尺寸获取

        # 返回上传结果
        return UploadResponse(
            success=True,
            data={
                "id": image_id,
                "filename": file.filename,
                "url": f"/api/upload/image/{image_id}",
                "thumbnail_url": f"/api/upload/image/{image_id}/thumbnail",
                "size": len(content),
                "mime_type": file.content_type,
                "width": width,
                "height": height
            }
        )

    except Exception as e:
        print(f"Error uploading image: {e}")
        return UploadResponse(
            success=False,
            error=f"上传失败: {str(e)}"
        )


@app.get("/api/upload/image/{image_id}")
async def get_image(image_id: str):
    """获取上传的图片"""

    upload_dir = get_upload_dir()

    # 尝试不同的扩展名
    for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ""]:
        file_path = upload_dir / f"{image_id}{ext}"
        if file_path.exists():
            return FileResponse(
                path=file_path,
                media_type="image/" + ext.lstrip("."),
                filename=f"{image_id}{ext}"
            )

    raise HTTPException(status_code=404, detail="Image not found")


@app.get("/api/upload/image/{image_id}/thumbnail")
async def get_image_thumbnail(image_id: str):
    """获取图片缩略图"""

    upload_dir = get_upload_dir()
    thumbnails_dir = upload_dir / "thumbnails"

    # 尝试查找已存在的缩略图
    for ext in [".jpg", ".png", ""]:
        thumb_path = thumbnails_dir / f"{image_id}_thumb{ext}"
        if thumb_path.exists():
            return FileResponse(
                path=thumb_path,
                media_type="image/jpeg",
                filename=f"{image_id}_thumb.jpg"
            )

    # 如果缩略图不存在，尝试生成
    original_path = None
    original_ext = None

    for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ""]:
        test_path = upload_dir / f"{image_id}{ext}"
        if test_path.exists():
            original_path = test_path
            original_ext = ext
            break

    if not original_path:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        # 尝试使用 Pillow 生成缩略图
        try:
            from PIL import Image

            img = Image.open(original_path)

            # 生成缩略图 (最大 200x200)
            img.thumbnail((200, 200))

            # 保存缩略图
            thumb_path = thumbnails_dir / f"{image_id}_thumb.jpg"
            img.convert("RGB").save(thumb_path, "JPEG", quality=85)
            img.close()

            return FileResponse(
                path=thumb_path,
                media_type="image/jpeg",
                filename=f"{image_id}_thumb.jpg"
            )

        except ImportError:
            # Pillow 未安装，返回原图
            return FileResponse(
                path=original_path,
                media_type=f"image/{original_ext.lstrip('.')}",
                filename=f"{image_id}{original_ext}"
            )

    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        # 生成失败，返回原图
        return FileResponse(
            path=original_path,
            media_type=f"image/{original_ext.lstrip('.')}",
            filename=f"{image_id}{original_ext}"
        )


@app.delete("/api/upload/image/{image_id}")
async def delete_image(image_id: str):
    """删除上传的图片"""

    upload_dir = get_upload_dir()
    deleted = False

    try:
        # 删除原图
        for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ""]:
            file_path = upload_dir / f"{image_id}{ext}"
            if file_path.exists():
                file_path.unlink()
                deleted = True
                break

        # 删除缩略图
        thumbnails_dir = upload_dir / "thumbnails"
        for ext in [".jpg", ".png", ""]:
            thumb_path = thumbnails_dir / f"{image_id}_thumb{ext}"
            if thumb_path.exists():
                thumb_path.unlink()

        if deleted:
            return {"success": True, "data": {"message": "Image deleted"}}
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting image: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/models/{model}/capabilities")
async def get_model_capabilities(model: str):
    """获取模型能力信息"""
    return {
        "success": True,
        "data": {
            "model": model,
            "vision": is_vision_model(model),
            "tools": True  # 大多数现代模型都支持工具调用
        }
    }


# ==================== 多模态聊天支持 ====================

def load_image_as_base64(image_id: str) -> tuple[str, str]:
    """
    加载图片并转换为 base64
    返回: (base64_string, mime_type)
    """
    upload_dir = get_upload_dir()

    for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ""]:
        file_path = upload_dir / f"{image_id}{ext}"
        if file_path.exists():
            with open(file_path, "rb") as f:
                image_data = f.read()

            # 确定 MIME 类型
            mime_type_map = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            mime_type = mime_type_map.get(ext, "image/png")

            base64_string = base64.b64encode(image_data).decode("utf-8")
            return base64_string, mime_type

    raise FileNotFoundError(f"Image not found: {image_id}")


def build_multimodal_content(message: str, images: List[ImageData] = None) -> list:
    """
    构建多模态消息内容
    返回 OpenAI 格式的内容列表
    """
    content = [{"type": "text", "text": message}]

    if images:
        for img in images:
            try:
                # 如果 URL 是 base64 data URL，直接使用
                if img.url and img.url.startswith("data:"):
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": img.url}
                    })
                else:
                    # 从服务器加载图片并转为 base64
                    base64_data, mime_type = load_image_as_base64(img.id)
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_data}"}
                    })
            except Exception as e:
                print(f"Error loading image {img.id}: {e}")
                # 跳过加载失败的图片

    return content


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
