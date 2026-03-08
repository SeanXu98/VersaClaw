# -*- coding: utf-8 -*-
"""
配置管理 API 路由模块

该模块提供配置管理相关的 API 端点：
- POST /api/config/reload: 重新加载配置
- GET /api/config: 获取当前配置

配置信息包括：
- 当前使用的模型
- Provider 名称
- API Base URL
- 温度参数
- 最大 Token 数
"""
import logging
from fastapi import APIRouter, Depends

from app.services.nanobot_service import NanobotService
from app.dependencies import get_nanobot_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/config", tags=["配置管理"])


@router.post("/reload")
async def reload_config(
    service: NanobotService = Depends(get_nanobot_service)
):
    """
    重新加载配置

    从配置文件重新加载 Nanobot 配置，包括：
    - Provider 配置
    - 模型参数
    - 工具配置

    响应:
        - success: 是否成功
        - data.message: 成功消息
        - data.model: 当前模型
        - data.provider: Provider 名称
        - data.api_base: API Base URL
    """
    try:
        success = await service.reload()
        if success:
            config_info = service.get_config_info()
            logger.info("[配置管理] 配置重载成功")
            return {
                "success": True,
                "data": {
                    "message": "配置重载成功",
                    **config_info
                }
            }
        else:
            logger.error("[配置管理] 配置重载失败")
            return {"success": False, "error": "配置重载失败"}

    except Exception as e:
        logger.error(f"[配置管理] 配置重载失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("")
async def get_config(
    service: NanobotService = Depends(get_nanobot_service)
):
    """
    获取当前配置

    返回当前 Nanobot 的配置信息（不含敏感数据如 API Key）。

    响应:
        - success: 是否成功
        - data.model: 当前模型
        - data.provider: Provider 名称
        - data.api_base: API Base URL
        - data.temperature: 温度参数
        - data.max_tokens: 最大 Token 数
    """
    try:
        config_info = service.get_config_info()
        logger.info("[配置管理] 获取配置成功")
        return {
            "success": True,
            "data": config_info
        }
    except Exception as e:
        logger.error(f"[配置管理] 获取配置失败: {e}")
        return {"success": False, "error": str(e)}
