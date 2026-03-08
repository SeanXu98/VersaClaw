# -*- coding: utf-8 -*-
"""
聊天 API 路由模块

该模块提供聊天相关的 API 端点：
- POST /api/chat: 非流式聊天
- POST /api/chat/stream: 流式聊天（SSE）

支持功能：
- 多模态消息（文本 + 图片）
- 模型切换
- 会话管理
"""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.services.nanobot_service import NanobotService
from app.services.image_service import ImageService
from app.dependencies import get_nanobot_service, get_image_service
from app.models.schemas import ChatRequest, ChatResponse
from app.config import settings

# 导入流式处理器
from stream_processor import StreamProcessor, ImageData as StreamImageData

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(tags=["聊天"])


@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: NanobotService = Depends(get_nanobot_service)
):
    """
    非流式聊天接口

    发送消息并等待完整响应。

    请求体:
        - message: 用户消息内容
        - session_key: 会话标识（可选）
        - model: 指定模型（可选）
        - images: 图片列表（可选，用于多模态）

    响应:
        - success: 是否成功
        - data: 响应数据和会话标识
        - error: 错误信息（失败时）
    """
    try:
        # 生成会话标识
        session_key = request.session_key or f"web:{asyncio.get_event_loop().time()}"

        # 如果指定了模型，临时切换
        original_model = None
        if request.model and service.agent_loop:
            original_model = service.agent_loop.model
            service.agent_loop.model = request.model
            logger.info(f"[聊天] 使用模型: {request.model}")

        try:
            # 调用 Agent 处理消息
            response = await service.agent_loop.process_direct(
                request.message,
                session_key
            )
        finally:
            # 恢复原始模型
            if original_model:
                service.agent_loop.model = original_model

        return ChatResponse(
            success=True,
            data={
                "response": response,
                "session_key": session_key
            }
        )

    except Exception as e:
        logger.error(f"[聊天] 处理消息失败: {e}")
        return ChatResponse(
            success=False,
            data={},
            error=str(e)
        )


@router.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    nanobot_service: NanobotService = Depends(get_nanobot_service),
    image_service: ImageService = Depends(get_image_service)
):
    """
    流式聊天接口（SSE）

    发送消息并以 SSE（Server-Sent Events）格式返回流式响应。

    SSE 事件类型:
        - content: 文本内容块
        - reasoning: 推理内容块（DeepSeek-R1 等模型）
        - tool_call_start: 工具调用开始
        - tool_call_end: 工具调用结束
        - iteration_start: Agent 迭代开始
        - image_processing: 图片处理状态
        - heartbeat: 心跳事件（保持连接）
        - done: 处理完成
        - error: 发生错误

    注意:
        使用 StreamProcessor 封装类处理流式响应。
        这是临时方案，等待 nanobot 官方支持 process_stream 方法。
        详见 stream_processor.py 文件。
    """
    if nanobot_service.agent_loop is None:
        return ChatResponse(
            success=False,
            data={},
            error="Nanobot 未初始化"
        )

    async def event_generator():
        """生成 SSE 事件流"""
        try:
            # 生成会话标识
            session_key = request.session_key or f"web:{asyncio.get_event_loop().time()}"

            # 获取请求中的图片（如果有）
            images = request.images
            model = request.model or (nanobot_service.agent_loop.model if nanobot_service.agent_loop else None)

            # 如果指定了模型，临时切换
            original_model = None
            if request.model and nanobot_service.agent_loop:
                original_model = nanobot_service.agent_loop.model
                nanobot_service.agent_loop.model = request.model
                logger.info(f"[流式聊天] 使用模型: {request.model}")

            try:
                # 构建消息内容（支持多模态）
                if images:
                    content = image_service.build_multimodal_content(request.message, images)
                    logger.info(f"[流式聊天] 多模态内容: {len(content)} 个块 (1 文本 + {len(images)} 图片)")
                else:
                    content = request.message

                # 创建流式处理器
                processor = StreamProcessor(
                    agent_loop=nanobot_service.agent_loop,
                    upload_dir=str(settings.UPLOAD_DIR),
                    vision_check_fn=lambda m: _is_vision_model(m)
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
                    timeout=settings.STREAM_TIMEOUT
                ):
                    yield event

            finally:
                # 恢复原始模型
                if original_model:
                    nanobot_service.agent_loop.model = original_model

        except Exception as e:
            logger.error(f"[流式聊天] 处理失败: {e}")
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
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        }
    )


def _is_vision_model(model: str) -> bool:
    """
    检查模型是否支持视觉能力

    参数:
        model: 模型名称

    返回:
        bool: 是否支持视觉能力
    """
    from app.utils.vision import is_vision_model
    return is_vision_model(model)
