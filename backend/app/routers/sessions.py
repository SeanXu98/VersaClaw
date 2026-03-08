# -*- coding: utf-8 -*-
"""
会话管理 API 路由模块

该模块提供会话管理相关的 API 端点：
- GET /api/sessions: 列出所有会话
- GET /api/sessions/{session_key}: 获取会话详情
- DELETE /api/sessions/{session_key}: 删除会话

会话数据存储在 workspace/sessions 目录下，格式为 JSONL。
"""
import json
import logging
from pathlib import Path
from fastapi import APIRouter, Depends

from app.services.nanobot_service import NanobotService
from app.dependencies import get_nanobot_service
from app.utils.helpers import get_sessions_dir

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/sessions", tags=["会话管理"])


@router.get("")
async def list_sessions(
    service: NanobotService = Depends(get_nanobot_service)
):
    """
    列出所有会话

    返回所有会话的列表，包含：
    - 会话标识
    - 标题（从第一条用户消息提取）
    - 消息数量
    - 元数据（创建时间、更新时间等）

    响应:
        - success: 是否成功
        - data.sessions: 会话列表
    """
    try:
        sessions_dir = get_sessions_dir(service.config.workspace_path)

        if not sessions_dir.exists():
            return {"success": True, "data": {"sessions": []}}

        sessions = []
        for file in sessions_dir.glob("*.jsonl"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if not lines:
                        continue

                    metadata = json.loads(lines[0])
                    messages_count = len(lines) - 1
                    session_key = file.stem.replace('_', ':')

                    # 提取第一条用户消息作为标题
                    title = "新会话"
                    for line in lines[1:]:  # 跳过元数据行
                        try:
                            msg = json.loads(line)
                            if msg.get("role") == "user":
                                content = msg.get("content", "")

                                # 处理多模态内容格式
                                if isinstance(content, list):
                                    text_parts = []
                                    for block in content:
                                        if isinstance(block, dict) and block.get("type") == "text":
                                            text = block.get("text", "")
                                            # 过滤图片标记
                                            text = text.replace("[image]", "").replace("[图片:", "").strip()
                                            if text and not text.startswith("temp_"):
                                                text_parts.append(text)
                                    title = " ".join(text_parts).strip()[:50]  # 限制50字符
                                elif isinstance(content, str):
                                    # 过滤图片标记
                                    title = content.replace("[image]", "").replace("[图片:", "").strip()[:50]

                                if title:
                                    break
                        except Exception:
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
                logger.warning(f"[会话管理] 读取会话文件失败 {file}: {e}")
                continue

        # 按更新时间排序（最新的在前）
        sessions.sort(
            key=lambda x: x.get("metadata", {}).get("updated_at", ""),
            reverse=True
        )

        logger.info(f"[会话管理] 列出会话成功，共 {len(sessions)} 个会话")
        return {"success": True, "data": {"sessions": sessions}}

    except Exception as e:
        logger.error(f"[会话管理] 列出会话失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/{session_key}")
async def get_session(
    session_key: str,
    service: NanobotService = Depends(get_nanobot_service)
):
    """
    获取会话详情

    参数:
        - session_key: 会话标识

    响应:
        - success: 是否成功
        - data.key: 会话标识
        - data.metadata: 会话元数据
        - data.messages: 消息列表
    """
    try:
        sessions_dir = get_sessions_dir(service.config.workspace_path)
        session_file = sessions_dir / f"{session_key.replace(':', '_')}.jsonl"

        if not session_file.exists():
            return {"success": False, "error": "会话不存在"}

        with open(session_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if not lines:
            return {"success": False, "error": "会话为空"}

        metadata = json.loads(lines[0])
        messages = [json.loads(line) for line in lines[1:]]

        logger.info(f"[会话管理] 获取会话详情成功: {session_key}")
        return {
            "success": True,
            "data": {
                "key": session_key,
                "metadata": metadata,
                "messages": messages
            }
        }

    except Exception as e:
        logger.error(f"[会话管理] 获取会话详情失败: {e}")
        return {"success": False, "error": str(e)}


@router.delete("/{session_key}")
async def delete_session(
    session_key: str,
    service: NanobotService = Depends(get_nanobot_service)
):
    """
    删除会话

    参数:
        - session_key: 会话标识

    响应:
        - success: 是否成功
        - data.message: 成功消息
        - error: 错误信息（失败时）
    """
    try:
        sessions_dir = get_sessions_dir(service.config.workspace_path)
        session_file = sessions_dir / f"{session_key.replace(':', '_')}.jsonl"

        if session_file.exists():
            session_file.unlink()
            logger.info(f"[会话管理] 删除会话成功: {session_key}")
            return {"success": True, "data": {"message": "会话已删除"}}
        else:
            return {"success": False, "error": "会话不存在"}

    except Exception as e:
        logger.error(f"[会话管理] 删除会话失败: {e}")
        return {"success": False, "error": str(e)}
