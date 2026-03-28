# -*- coding: utf-8 -*-
"""
DashScope Provider 包装类 - 方案B：继承 LiteLLMProvider，只修改模型解析

核心问题：
- LiteLLM 的 dashscope/ provider 使用原生 DashScope SDK
- 原生 SDK 不支持视觉模型（qwen-vl-*）
- 阿里云官方推荐使用 OpenAI 兼容模式

解决方案：
- 继承 LiteLLMProvider
- 重写 _resolve_model 方法
- 对视觉模型使用 "openai/" 前缀（让 LiteLLM 用 OpenAI SDK 调用）
- 对文本模型保持 "dashscope/" 前缀

这样既保留了 LiteLLM 的所有功能，又解决了视觉模型问题。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from nanobot.providers.litellm_provider import LiteLLMProvider
from nanobot.providers.base import LLMResponse

# 配置日志
logger = logging.getLogger(__name__)


# DashScope 视觉模型关键词
DASHSCOPE_VISION_PATTERNS = [
    "qwen-vl",
    "qwen3-vl", 
    "qwen-omni",
    "qvq-",
]


def is_dashscope_vision_model(model: str) -> bool:
    """检测是否是 DashScope 视觉模型"""
    if not model:
        return False
    model_lower = model.lower()
    return any(pattern in model_lower for pattern in DASHSCOPE_VISION_PATTERNS)


class DashScopeVisionProvider(LiteLLMProvider):
    """
    DashScope Provider - 支持视觉模型
    
    继承 LiteLLMProvider，只重写 _resolve_model 方法。
    
    工作原理：
    1. 视觉模型（qwen-vl-*）：使用 "openai/" 前缀
       - LiteLLM 会用 OpenAI SDK 调用 api_base
       - 阿里云的 OpenAI 兼容端点会正确处理
    
    2. 文本模型（qwen-max, qwen-plus）：使用 "dashscope/" 前缀
       - LiteLLM 会用原生 DashScope SDK
       - 功能正常
    
    这样用户可以正常使用 "dashscope" provider，无需任何额外配置。
    """
    
    def _resolve_model(self, model: str) -> str:
        """
        解析模型名称 - 对视觉模型使用 openai/ 前缀
        
        关键逻辑：
        - 视觉模型 -> "openai/model"（让 LiteLLM 用 OpenAI SDK）
        - 文本模型 -> "dashscope/model"（保持原有行为）
        """
        # 先检测是否是视觉模型
        if is_dashscope_vision_model(model):
            # 移除已有的前缀
            if "/" in model:
                model = model.split("/", 1)[1]
            # 使用 openai/ 前缀，让 LiteLLM 用 OpenAI SDK 调用
            resolved = f"openai/{model}"
            logger.debug(f"[DashScopeProvider] 视觉模型 {model} -> {resolved}")
            return resolved
        
        # 非视觉模型，使用父类的解析逻辑
        return super()._resolve_model(model)