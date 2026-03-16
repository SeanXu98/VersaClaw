# -*- coding: utf-8 -*-
"""
Vision Agent 定义模块

该模块定义专用于图像理解的子代理配置，包括：
- 系统提示词
- 默认模型配置
- 能力定义

Vision Agent 通过 Nanobot 的 SubagentManager 创建和管理，
无需修改 Nanobot 源码。

使用方式:
    from app.extension.vision_agent import VisionAgentConfig, VisionAgentManager

    config = VisionAgentConfig()
    manager = VisionAgentManager(subagent_manager)
    result = await manager.analyze_image(image_path, "描述这张图片")
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ==================== Vision Agent 系统提示词 ====================

VISION_AGENT_SYSTEM_PROMPT = """# Vision Agent

You are a specialized vision agent focused on image understanding and analysis.

## Core Capabilities

1. **Image Description**: Provide detailed descriptions of image content
2. **Text Extraction**: Extract and transcribe text from images (OCR)
3. **Chart & Table Parsing**: Analyze and interpret charts, graphs, and tables
4. **Visual Q&A**: Answer questions about image content
5. **Comparison**: Compare multiple images and identify differences

## Guidelines

- Be precise and detailed in your descriptions
- When extracting text, preserve the original formatting as much as possible
- For charts and tables, provide structured output when appropriate
- If you cannot clearly see or interpret something, state that uncertainty
- Focus on what is explicitly visible in the image, avoid speculation

## Output Format

- Use clear, structured responses
- For text extraction, use code blocks when appropriate
- For data analysis, use markdown tables when helpful
- Keep responses focused and relevant to the task

## Limitations

- You can only analyze images that are provided to you
- You cannot modify or create images
- You cannot access external resources beyond the provided images
"""


# ==================== Vision Agent 配置 ====================

@dataclass
class VisionAgentConfig:
    """
    Vision Agent 配置
    
    Attributes:
        name: Agent 名称
        system_prompt: 系统提示词
        default_model: 默认视觉模型
        fallback_models: 备选模型列表
        max_iterations: 最大迭代次数
        enabled: 是否启用
    """
    name: str = "vision"
    system_prompt: str = VISION_AGENT_SYSTEM_PROMPT
    default_model: Optional[str] = None
    fallback_models: List[str] = field(default_factory=list)
    max_iterations: int = 10
    enabled: bool = True
    
    def __post_init__(self):
        """初始化后处理"""
        # 如果没有指定默认模型，使用常见的视觉模型
        if self.default_model is None:
            self.default_model = "gpt-4o"


@dataclass
class VisionAnalysisRequest:
    """
    视觉分析请求
    
    Attributes:
        image_paths: 图片路径列表
        query: 查询/任务描述
        context: 额外上下文信息
    """
    image_paths: List[str]
    query: str
    context: Optional[str] = None


@dataclass
class VisionAnalysisResult:
    """
    视觉分析结果
    
    Attributes:
        success: 是否成功
        content: 分析结果内容
        error: 错误信息（失败时）
        model_used: 使用的模型
        tokens_used: 使用的 token 数量
    """
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: int = 0


# ==================== 视觉模型能力定义 ====================

VISION_MODEL_CAPABILITIES = {
    # OpenAI 系列
    "gpt-4o": {
        "max_images": 10,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "2048x2048",
    },
    "gpt-4o-mini": {
        "max_images": 10,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "2048x2048",
    },
    "gpt-4-turbo": {
        "max_images": 10,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "2048x2048",
    },
    "gpt-4-vision-preview": {
        "max_images": 10,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "2048x2048",
    },
    # Anthropic 系列
    "claude-3-opus": {
        "max_images": 20,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "8000x8000",
    },
    "claude-3-sonnet": {
        "max_images": 20,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "8000x8000",
    },
    "claude-3-haiku": {
        "max_images": 20,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "8000x8000",
    },
    "claude-3.5-sonnet": {
        "max_images": 20,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "8000x8000",
    },
    # Google 系列
    "gemini-1.5-pro": {
        "max_images": 100,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "无限制",
    },
    "gemini-1.5-flash": {
        "max_images": 100,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "无限制",
    },
    # 智谱系列
    "glm-4v": {
        "max_images": 5,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "4096x4096",
    },
}


def get_vision_model_capability(model: str) -> Dict[str, Any]:
    """
    获取视觉模型能力信息
    
    Args:
        model: 模型名称
    
    Returns:
        Dict: 模型能力信息
    """
    # 标准化模型名称
    model_lower = model.lower()
    
    # 直接匹配
    if model_lower in VISION_MODEL_CAPABILITIES:
        return VISION_MODEL_CAPABILITIES[model_lower]
    
    # 模糊匹配
    for key, capabilities in VISION_MODEL_CAPABILITIES.items():
        if key in model_lower or model_lower in key:
            return capabilities
    
    # 默认能力
    return {
        "max_images": 5,
        "supports_ocr": True,
        "supports_charts": True,
        "max_resolution": "2048x2048",
    }
