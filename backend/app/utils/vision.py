# -*- coding: utf-8 -*-
"""
Vision 模型检测模块

该模块提供了检测 AI 模型是否支持视觉（图像理解）能力的功能。

使用方式:
    from app.utils.vision import is_vision_model

    if is_vision_model("gpt-4o"):
        print("该模型支持图像理解")
"""
from typing import List


# ==================== Vision 模型关键词 ====================
# 包含这些关键词的模型通常支持图像理解能力
VISION_MODEL_PATTERNS: List[str] = [
    # OpenAI 系列
    "gpt-4-vision",
    "gpt-4-turbo",
    "gpt-4o",
    "gpt-4o-mini",

    # Anthropic 系列
    "claude-3",
    "claude-3.5",

    # Google 系列
    "gemini-1.5",
    "gemini-2",

    # 网关服务
    "openrouter/",

    # 智谱 GLM Vision 系列
    "glm-4v",
    "glm-4.6v",
    "glm-4.1v",

    # 其他 Vision 模型
    "qwen-vl",
    "deepseek-vl",
    "llava",

    # 通用关键词
    "vision",
]


def is_vision_model(model: str) -> bool:
    """
    检测模型是否支持 Vision（图像理解）能力

    通过检查模型名称中是否包含 Vision 模型的关键词来判断。

    参数:
        model: 模型名称，如 "gpt-4o"、"claude-3-sonnet" 等

    返回:
        bool: 如果模型支持 Vision 能力返回 True，否则返回 False

    示例:
        >>> is_vision_model("gpt-4o")
        True
        >>> is_vision_model("gpt-3.5-turbo")
        False
    """
    if not model:
        return False

    model_lower = model.lower()
    return any(pattern in model_lower for pattern in VISION_MODEL_PATTERNS)
