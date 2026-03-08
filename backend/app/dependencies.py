# -*- coding: utf-8 -*-
"""
FastAPI 依赖注入模块

该模块提供了 FastAPI 路由的依赖注入函数，用于：
- 获取 Nanobot 服务实例
- 获取图片服务实例

使用方式:
    from app.dependencies import get_nanobot_service, get_image_service

    @router.get("/chat")
    async def chat(service: NanobotService = Depends(get_nanobot_service)):
        ...
"""
from typing import Optional
from fastapi import Depends, HTTPException

from app.services.nanobot_service import NanobotService
from app.services.image_service import ImageService, image_service


# 全局 Nanobot 服务实例
_nanobot_service: Optional[NanobotService] = None


def set_nanobot_service(service: NanobotService) -> None:
    """
    设置全局 Nanobot 服务实例

    该函数在应用启动时调用，用于设置服务实例。

    参数:
        service: NanobotService 实例
    """
    global _nanobot_service
    _nanobot_service = service


def get_nanobot_service() -> NanobotService:
    """
    获取 Nanobot 服务依赖

    如果服务未初始化，会抛出 503 错误。

    抛出:
        HTTPException: 服务未初始化时抛出 503 错误

    返回:
        NanobotService: Nanobot 服务实例
    """
    if _nanobot_service is None or not _nanobot_service.is_initialized:
        raise HTTPException(
            status_code=503,
            detail="Nanobot 服务未初始化"
        )
    return _nanobot_service


def get_nanobot_service_optional() -> Optional[NanobotService]:
    """
    获取 Nanobot 服务（可能为 None 或未初始化）

    该函数不会抛出异常，适用于健康检查等场景。

    返回:
        Optional[NanobotService]: Nanobot 服务实例，可能为 None
    """
    return _nanobot_service


def get_image_service() -> ImageService:
    """
    获取图片服务依赖

    返回:
        ImageService: 图片服务实例（全局单例）
    """
    return image_service
