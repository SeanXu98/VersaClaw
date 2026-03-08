#!/usr/bin/env python3
"""
Stream Processor - 流式处理封装模块

注意：这是临时方案，用于在 nanobot 官方支持 process_stream 之前提供流式响应能力。

当 nanobot 官方添加 process_stream 方法后，可以直接替换此模块的实现。

设计原则：
1. 封装流式处理逻辑，提供清晰的接口
2. 保留 nanobot 的全部 Agent 能力（工具调用、会话管理、memory）
3. 支持多模态消息（图片）
4. 代码可维护，易于未来迁移

使用方式：
    processor = StreamProcessor(agent_loop)
    async for event in processor.process_stream(content, session_key, images=images):
        yield event
"""

import asyncio
import base64
import json
import re
import uuid
from pathlib import Path
from typing import AsyncGenerator, Callable, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ImageData:
    """图片数据结构"""
    id: str
    url: str
    thumbnail_url: Optional[str] = None
    mime_type: str = "image/png"
    size: Optional[int] = None
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class StreamEvent:
    """流式事件结构"""
    type: str
    content: Optional[str] = None
    error: Optional[str] = None
    data: Optional[dict] = None

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        event_dict = {"type": self.type}
        if self.content is not None:
            event_dict["content"] = self.content
        if self.error is not None:
            event_dict["error"] = self.error
        if self.data is not None:
            event_dict.update(self.data)
        return json.dumps(event_dict, ensure_ascii=False)


# 心跳事件类型常量
EVENT_TYPES = {
    "CONTENT": "content",
    "REASONING": "reasoning",
    "TOOL_CALL_START": "tool_call_start",
    "TOOL_CALL_END": "tool_call_end",
    "ITERATION_START": "iteration_start",
    "HEARTBEAT": "heartbeat",
    "DONE": "done",
    "ERROR": "error"
}


class StreamProcessor:
    """
    流式处理器

    封装了使用 nanobot AgentLoop 进行流式消息处理的逻辑。
    通过 on_progress 回调和 asyncio.Queue 实现流式输出。

    注意：
    - process_direct 方法的 on_progress 回调主要在工具调用时触发
    - 普通对话是一次性返回完整内容
    - 这是 nanobot API 的限制，非真正逐 token 流式
    - 我们通过心跳事件和中间状态来改善用户体验
    """

    def __init__(
        self,
        agent_loop: Any,
        upload_dir: Optional[str] = None,
        vision_check_fn: Optional[Callable[[str], bool]] = None
    ):
        """
        初始化流式处理器

        Args:
            agent_loop: nanobot AgentLoop 实例
            upload_dir: 图片上传目录路径
            vision_check_fn: Vision 模型检测函数
        """
        self.agent_loop = agent_loop
        self.upload_dir = Path(upload_dir or Path.home() / ".nanobot" / "uploads" / "images")
        self.vision_check_fn = vision_check_fn or self._default_vision_check

    def _default_vision_check(self, model: str) -> bool:
        """默认的 Vision 模型检测"""
        if not model:
            return False
        patterns = [
            "gpt-4-vision", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "claude-3", "claude-3.5", "gemini-1.5", "gemini-2",
            "openrouter/", "vision", "llava",
            "glm-4v", "glm-4.6v", "glm-4.1v",  # 智谱 GLM Vision 系列
        ]
        return any(p in model.lower() for p in patterns)

    async def process_stream(
        self,
        content: str | list,
        session_key: str,
        images: Optional[List[ImageData]] = None,
        model: Optional[str] = None,
        channel: str = "web",
        timeout: float = 120.0
    ) -> AsyncGenerator[str, None]:
        """
        流式处理消息，生成 SSE 格式的事件

        Args:
            content: 消息内容（字符串或多模态内容列表）
            session_key: 会话标识
            images: 图片列表
            model: 使用的模型
            channel: 渠道标识
            timeout: 超时时间（秒）

        Yields:
            SSE 格式的事件字符串 "data: {...}\n\n"
        """
        # 检查模型是否支持 Vision（如果有图片）
        if images and model:
            if not self.vision_check_fn(model):
                yield self._format_event(StreamEvent(
                    type="error",
                    error=f"模型 {model} 不支持图像理解，请切换到 Vision 模型"
                ))
                return

        # 发送图片处理状态
        if images:
            for img in images:
                yield self._format_event(StreamEvent(
                    type="image_processing",
                    data={"image_id": img.id, "status": "processing"}
                ))

        # 创建事件队列
        event_queue: asyncio.Queue = asyncio.Queue()
        final_result = {"content": None, "reasoning_content": None, "thinking_blocks": None, "error": None}
        last_heartbeat = asyncio.get_event_loop().time()

        async def on_progress(progress_content: str, **kwargs):
            """进度回调函数"""
            nonlocal last_heartbeat
            last_heartbeat = asyncio.get_event_loop().time()
            print(f"[DEBUG] on_progress: tool_hint={kwargs.get('tool_hint')}, content={progress_content[:100] if progress_content else 'empty'}...")

            if kwargs.get("tool_hint"):
                # 解析工具调用提示
                async for event in self._parse_tool_hint(progress_content):
                    print(f"[DEBUG] Sending tool event: {event.type}, data={event.data}")
                    await event_queue.put(event)
            else:
                # 检测是否是 reasoning/thinking 内容
                # 对于支持思考过程的模型，非工具调用的进度内容通常是 reasoning
                # 发送 reasoning 事件，让用户能看到思考过程
                if progress_content and progress_content.strip():
                    await event_queue.put(StreamEvent(
                        type="reasoning",
                        content=progress_content
                    ))

        async def process_task():
            """后台处理任务"""
            try:
                result = await self._process_content(
                    content=content,
                    session_key=session_key,
                    images=images,
                    channel=channel,
                    on_progress=on_progress
                )
                final_result["content"] = result.get("content", "")
                final_result["reasoning_content"] = result.get("reasoning_content")
                final_result["thinking_blocks"] = result.get("thinking_blocks")
            except Exception as e:
                import traceback
                traceback.print_exc()
                final_result["error"] = str(e)
            finally:
                # 发送结束信号
                await event_queue.put(None)

        # 启动处理任务
        task = asyncio.create_task(process_task())

        # 从队列读取并发送事件，同时发送心跳
        heartbeat_interval = 2.0  # 每2秒发送一次心跳
        while True:
            try:
                event = await asyncio.wait_for(event_queue.get(), timeout=heartbeat_interval)
                if event is None:
                    break
                yield self._format_event(event)
            except asyncio.TimeoutError:
                if task.done():
                    break
                # 发送心跳事件，让用户知道还在处理中
                current_time = asyncio.get_event_loop().time()
                if current_time - last_heartbeat > heartbeat_interval:
                    yield self._format_event(StreamEvent(type="heartbeat", data={"status": "processing"}))
                    last_heartbeat = current_time
                continue

        # 等待任务完成
        await task

        # 发送最终结果
        if final_result["error"]:
            yield self._format_event(StreamEvent(type="error", error=final_result["error"]))
        else:
            # 发送 reasoning 内容（如果有）- 直接发送，前端会处理
            reasoning = final_result.get("reasoning_content")
            print(f"[DEBUG] Final reasoning content: {bool(reasoning)}, length: {len(reasoning) if reasoning else 0}")
            if reasoning:
                yield self._format_event(StreamEvent(
                    type="reasoning",
                    content=reasoning
                ))

            # 发送完成事件 - content 直接放在顶层
            # 同时包含 reasoning_content，避免前端竞态条件
            thinking_blocks = final_result.get("thinking_blocks")
            content = final_result["content"] or ""
            print(f"[DEBUG] Done event: content_length={len(content)}, has_thinking={bool(thinking_blocks)}")
            yield self._format_event(StreamEvent(
                type="done",
                content=content,
                data={
                    "thinking_blocks": thinking_blocks,
                    "reasoning_content": reasoning  # 也包含在 done 事件中
                }
            ))

        # 发送图片处理完成状态
        if images:
            for img in images:
                yield self._format_event(StreamEvent(
                    type="image_processing",
                    data={"image_id": img.id, "status": "completed"}
                ))

    async def _process_content(
        self,
        content: str | list,
        session_key: str,
        images: Optional[List[ImageData]],
        channel: str,
        on_progress: Callable
    ) -> dict:
        """
        处理消息内容

        Args:
            content: 消息内容
            session_key: 会话标识
            images: 图片列表
            channel: 渠道标识
            on_progress: 进度回调

        Returns:
            包含 content 和 reasoning_content 的字典
        """
        message_text = content
        media_files = []
        original_image_ids = []

        # 处理多模态内容
        if isinstance(content, list):
            message_text, media_files, original_image_ids = await self._process_multimodal_content(content, images)

        # 根据是否有媒体文件选择处理方式
        if media_files:
            # 使用 _process_message 支持 media 参数
            result = await self._process_with_media(
                message_text=message_text,
                media_files=media_files,
                session_key=session_key,
                channel=channel,
                on_progress=on_progress,
                images=images  # 传递原始图片信息，用于不删除已上传的图片
            )
        else:
            # 使用 _process_message 直接获取完整响应
            result = await self._process_direct_with_reasoning(
                message_text=message_text,
                session_key=session_key,
                channel=channel,
                on_progress=on_progress
            )

        return result or {"content": ""}

    async def _process_multimodal_content(self, content: list, images: Optional[List[ImageData]] = None) -> tuple[str, list, list]:
        """
        处理多模态内容，提取文本并准备图片文件

        Args:
            content: 多模态内容列表
            images: 原始图片信息列表（包含 id, url 等）

        Returns:
            (文本内容, 图片文件路径列表, 原始图片ID列表)
        """
        text_parts = []
        media_files = []
        original_image_ids = []

        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # 创建图片 URL 到 ID 的映射
        image_id_map = {}
        if images:
            for img in images:
                # 图片 ID 对应的文件路径
                for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ""]:
                    potential_path = self.upload_dir / f"{img.id}{ext}"
                    if potential_path.exists():
                        image_id_map[img.id] = str(potential_path)
                        break

        for block in content:
            if not isinstance(block, dict):
                continue

            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))

            elif block.get("type") == "image_url":
                image_url = block.get("image_url", {}).get("url", "")

                if image_url.startswith("data:image/"):
                    # 尝试匹配原始图片 ID
                    matched_id = self._match_base64_to_image(image_url, image_id_map)

                    if matched_id and matched_id in image_id_map:
                        # 使用原始上传的图片
                        original_path = image_id_map[matched_id]
                        media_files.append(original_path)
                        original_image_ids.append(matched_id)
                        text_parts.append(f"[图片: {matched_id}.png]")
                    else:
                        # 无法匹配，保存为临时文件（兼容旧逻辑）
                        temp_path = await self._save_base64_image(image_url)
                        if temp_path:
                            media_files.append(temp_path)
                            text_parts.append(f"[图片: {Path(temp_path).name}]")

        return "\n".join(text_parts), media_files, original_image_ids

    def _match_base64_to_image(self, data_url: str, image_id_map: dict) -> Optional[str]:
        """
        尝试将 base64 数据匹配到原始图片

        Args:
            data_url: base64 数据 URL
            image_id_map: 图片 ID 到文件路径的映射

        Returns:
            匹配的图片 ID，未匹配返回 None
        """
        try:
            # 提取 base64 数据
            _, data = data_url.split(",", 1)
            incoming_bytes = base64.b64decode(data)

            # 计算哈希用于快速比较
            import hashlib
            incoming_hash = hashlib.md5(incoming_bytes).hexdigest()

            # 遍历已上传的图片进行匹配
            for image_id, file_path in image_id_map.items():
                try:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()
                    file_hash = hashlib.md5(file_bytes).hexdigest()

                    if incoming_hash == file_hash:
                        return image_id
                except Exception:
                    continue

        except Exception as e:
            print(f"Error matching base64 to image: {e}")

        return None

    async def _save_base64_image(self, data_url: str) -> Optional[str]:
        """
        将 base64 数据 URL 保存为临时文件

        Args:
            data_url: base64 数据 URL (data:image/png;base64,...)

        Returns:
            临时文件路径，失败返回 None
        """
        try:
            header, data = data_url.split(",", 1)

            # 提取 MIME 类型
            mime_part = header.split(":")[1].split(";")[0]
            ext = mime_part.split("/")[1] if "/" in mime_part else "png"

            # 生成临时文件名
            temp_filename = f"temp_{uuid.uuid4().hex}.{ext}"
            temp_path = self.upload_dir / temp_filename

            # 保存文件
            temp_path.write_bytes(base64.b64decode(data))

            return str(temp_path)

        except Exception as e:
            print(f"Error saving base64 image: {e}")
            return None

    async def _process_with_media(
        self,
        message_text: str,
        media_files: list,
        session_key: str,
        channel: str,
        on_progress: Callable,
        images: Optional[List[ImageData]] = None
    ) -> dict:
        """
        使用 _process_message 处理带媒体的消息

        注意：这里使用了 nanobot 的内部 API (_process_message)
        因为公共 API (process_direct) 不支持 media 参数

        Args:
            message_text: 消息文本
            media_files: 媒体文件路径列表
            session_key: 会话标识
            channel: 渠道标识
            on_progress: 进度回调
            images: 原始图片信息列表（用于判断哪些文件不应删除）

        Returns:
            包含 content 和 reasoning_content 的字典
        """
        from nanobot.bus.events import InboundMessage

        chat_id = session_key.split(":")[-1] if ":" in session_key else "stream"

        msg = InboundMessage(
            channel=channel,
            sender_id="user",
            chat_id=chat_id,
            content=message_text,
            media=media_files  # 媒体文件列表
        )

        try:
            response = await self.agent_loop._process_message(
                msg,
                session_key=session_key,
                on_progress=on_progress
            )

            result = {
                "content": response.content if response else "",
                "reasoning_content": None,
                "thinking_blocks": None
            }

            # 尝试从 session 获取最后一条 assistant 消息的 reasoning 内容
            if response and hasattr(self.agent_loop, 'sessions'):
                try:
                    session = self.agent_loop.sessions.get_or_create(session_key)
                    history = session.get_history(max_messages=2)  # 获取更多历史
                    print(f"[DEBUG] _process_with_media - history length: {len(history)}")
                    if history:
                        for i, msg in enumerate(history):
                            print(f"[DEBUG]   msg[{i}]: role={msg.get('role')}, has_reasoning={bool(msg.get('reasoning_content'))}, has_thinking={bool(msg.get('thinking_blocks'))}")
                        # 找最后一条 assistant 消息
                        for msg in reversed(history):
                            if msg.get("role") == "assistant":
                                result["reasoning_content"] = msg.get("reasoning_content")
                                result["thinking_blocks"] = msg.get("thinking_blocks")
                                print(f"[DEBUG] Found reasoning: {bool(result['reasoning_content'])}, thinking: {bool(result['thinking_blocks'])}")
                                break
                except Exception as e:
                    print(f"[DEBUG] Failed to get reasoning from session: {e}")
                    import traceback
                    traceback.print_exc()

        finally:
            # 清理临时文件（只删除 temp_ 开头的临时文件，保留原始上传的图片）
            for temp_file in media_files:
                file_name = Path(temp_file).name
                # 只删除 temp_ 开头的临时文件
                if file_name.startswith("temp_"):
                    try:
                        Path(temp_file).unlink(missing_ok=True)
                    except Exception:
                        pass

        return result

    async def _process_direct_with_reasoning(
        self,
        message_text: str,
        session_key: str,
        channel: str,
        on_progress: Callable
    ) -> dict:
        """
        直接处理消息并获取完整的响应（包含 reasoning）

        Args:
            message_text: 消息文本
            session_key: 会话标识
            channel: 渠道标识
            on_progress: 进度回调

        Returns:
            包含 content 和 reasoning_content 的字典
        """
        from nanobot.bus.events import InboundMessage

        chat_id = session_key.split(":")[-1] if ":" in session_key else "stream"

        msg = InboundMessage(
            channel=channel,
            sender_id="user",
            chat_id=chat_id,
            content=message_text
        )

        response = await self.agent_loop._process_message(
            msg,
            session_key=session_key,
            on_progress=on_progress
        )

        result = {
            "content": response.content if response else "",
            "reasoning_content": None,
            "thinking_blocks": None
        }

        # 尝试从 session 获取最后一条 assistant 消息的 reasoning 内容
        if response and hasattr(self.agent_loop, 'sessions'):
            try:
                session = self.agent_loop.sessions.get_or_create(session_key)
                history = session.get_history(max_messages=3)  # 获取更多历史
                print(f"[DEBUG] _process_direct_with_reasoning - history length: {len(history)}")
                if history:
                    for i, msg in enumerate(history):
                        print(f"[DEBUG]   msg[{i}]: role={msg.get('role')}, has_reasoning={bool(msg.get('reasoning_content'))}, has_thinking={bool(msg.get('thinking_blocks'))}")
                    # 找最后一条 assistant 消息
                    for msg in reversed(history):
                        if msg.get("role") == "assistant":
                            result["reasoning_content"] = msg.get("reasoning_content")
                            result["thinking_blocks"] = msg.get("thinking_blocks")
                            print(f"[DEBUG] Found reasoning: {bool(result['reasoning_content'])}, thinking: {bool(result['thinking_blocks'])}")
                            if result["reasoning_content"]:
                                print(f"[DEBUG] reasoning_content preview: {result['reasoning_content'][:200]}...")
                            break
            except Exception as e:
                print(f"[DEBUG] Failed to get reasoning from session: {e}")
                import traceback
                traceback.print_exc()

        return result

    async def _parse_tool_hint(self, content: str) -> AsyncGenerator[StreamEvent, None]:
        """
        解析工具调用提示，生成工具事件

        Args:
            content: 进度内容，可能包含工具调用提示

        Yields:
            工具调用事件 (tool_call_start 和 tool_call_end)

        Note:
            nanobot 的工具调用提示格式: Tool call: tool_name({"arg": "value"})
            例如: Tool call: write_file({"path": "test.txt", "content": "hello"})
        """
        # 尝试解析 JSON 格式的工具调用（nanobot 新格式）
        # 格式: Tool call: tool_name({"arg": "value"})
        json_pattern = r'Tool call:\s*(\w+)\((\{[^}]*\})\)'
        json_matches = re.findall(json_pattern, content)

        for tool_name, args_json in json_matches:
            tool_id = f"tool_{tool_name}_{uuid.uuid4().hex[:8]}"
            try:
                args = json.loads(args_json)
            except json.JSONDecodeError:
                args = {"raw": args_json}

            # 发送 tool_call_start 事件
            yield StreamEvent(
                type="tool_call_start",
                data={
                    "tool_id": tool_id,
                    "name": tool_name,
                    "arguments": args
                }
            )

            # 立即发送 tool_call_end 事件（假设工具执行成功）
            # 因为 nanobot 在 on_progress 中只提供工具调用信息，不提供执行结果
            # 我们假设工具执行完成，result 为空（实际结果会在最终响应中体现）
            yield StreamEvent(
                type="tool_call_end",
                data={
                    "tool_id": tool_id,
                    "name": tool_name,
                    "result": ""  # 结果会在最终响应中体现
                }
            )

        # 兼容旧格式: tool_name("arg")
        if not json_matches:
            simple_pattern = r'(\w+)\("([^"]*?)"?\)'
            simple_matches = re.findall(simple_pattern, content)

            for tool_name, args in simple_matches:
                tool_id = f"tool_{tool_name}_{uuid.uuid4().hex[:8]}"

                # 发送 tool_call_start 事件
                yield StreamEvent(
                    type="tool_call_start",
                    data={
                        "tool_id": tool_id,
                        "name": tool_name,
                        "arguments": {"path": args} if tool_name in ["read_file", "write_file"] else {"query": args}
                    }
                )

                # 发送 tool_call_end 事件
                yield StreamEvent(
                    type="tool_call_end",
                    data={
                        "tool_id": tool_id,
                        "name": tool_name,
                        "result": ""
                    }
                )

    def _format_event(self, event: StreamEvent) -> str:
        """
        格式化事件为 SSE 格式

        Args:
            event: 流式事件

        Returns:
            SSE 格式字符串 "data: {...}\n\n"
        """
        return f"data: {event.to_json()}\n\n"


# 便捷函数：创建 SSE 响应
def create_sse_response(
    agent_loop: Any,
    content: str | list,
    session_key: str,
    images: Optional[List[ImageData]] = None,
    model: Optional[str] = None,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    创建 SSE 响应的便捷函数

    使用方式:
        return StreamingResponse(
            create_sse_response(agent_loop, content, session_key, images, model),
            media_type="text/event-stream"
        )
    """
    processor = StreamProcessor(agent_loop)
    return processor.process_stream(
        content=content,
        session_key=session_key,
        images=images,
        model=model,
        **kwargs
    )
