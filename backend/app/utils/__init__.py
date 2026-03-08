# -*- coding: utf-8 -*-
"""
工具函数包

该包提供项目中通用的工具函数。

包含的模块:
    - vision: Vision 模型检测
    - helpers: 通用辅助函数

导出的函数:
    - is_vision_model: 检测模型是否支持视觉能力
    - VISION_MODEL_PATTERNS: Vision 模型关键词列表
    - mask_api_key: 遮罩 API Key
    - get_sessions_dir: 获取会话目录路径

使用方式:
    from app.utils import is_vision_model, mask_api_key
"""
from .vision import is_vision_model, VISION_MODEL_PATTERNS
from .helpers import mask_api_key, get_sessions_dir

__all__ = [
    "is_vision_model",
    "VISION_MODEL_PATTERNS",
    "mask_api_key",
    "get_sessions_dir",
]
