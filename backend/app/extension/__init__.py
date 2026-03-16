# -*- coding: utf-8 -*-
"""
VersaClaw 扩展层

该包提供对 Nanobot 框架的扩展能力，包括：
- ModelScheduler: 智能模型调度器
- EnhancedAgentLoop: 增强的 Agent 循环
- VisionAgent: 视觉理解子代理
- 配置扩展: 支持独立的 imageModel 配置

设计原则：
1. 继承而非修改：EnhancedAgentLoop 继承 AgentLoop
2. 封装而非替代：ModelScheduler 封装 Provider
3. 复用而非重建：直接使用 Nanobot 的 SubagentManager 等
4. 兼容而非替换：配置向后兼容
"""

from app.extension.scheduler import ModelScheduler, ModelSelectionResult
from app.extension.feature_analyzer import RequestFeatureAnalyzer, RequestFeatures
from app.extension.config_extension import (
    ImageModelConfig,
    ModelFallbackConfig,
    ExtendedAgentDefaults,
    ExtendedAgentsConfig,
    ExtendedConfig,
    get_extended_config,
    update_config_with_image_model,
)
from app.extension.enhanced_loop import EnhancedAgentLoop
from app.extension.vision_agent import (
    VisionAgentConfig,
    VisionAnalysisRequest,
    VisionAnalysisResult,
    VISION_AGENT_SYSTEM_PROMPT,
    VISION_MODEL_CAPABILITIES,
    get_vision_model_capability,
)
from app.extension.vision_agent_manager import VisionAgentManager

__all__ = [
    # 模型调度
    "ModelScheduler",
    "ModelSelectionResult",
    # 请求特征分析
    "RequestFeatureAnalyzer",
    "RequestFeatures",
    # 配置扩展
    "ImageModelConfig",
    "ModelFallbackConfig",
    "ExtendedAgentDefaults",
    "ExtendedAgentsConfig",
    "ExtendedConfig",
    "get_extended_config",
    "update_config_with_image_model",
    # 增强 Agent 循环
    "EnhancedAgentLoop",
    # Vision Agent
    "VisionAgentConfig",
    "VisionAnalysisRequest",
    "VisionAnalysisResult",
    "VISION_AGENT_SYSTEM_PROMPT",
    "VISION_MODEL_CAPABILITIES",
    "get_vision_model_capability",
    "VisionAgentManager",
]
