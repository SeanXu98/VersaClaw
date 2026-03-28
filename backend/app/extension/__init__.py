# -*- coding: utf-8 -*-
"""
VersaClaw 扩展层

该包提供对 Nanobot 框架的扩展能力，包括：
- AgentLoopAdapter: AgentLoop 到 LangGraph 的适配器
- ModelScheduler: 智能模型调度器
- VisionAgent: 视觉理解子代理
- AgentTeamManager: 子代理团队管理器
- 配置扩展: 支持独立的 imageModel 配置

设计原则：
1. 适配器模式：AgentLoopAdapter 连接 Nanobot 和 LangGraph
2. 封装而非替代：ModelScheduler 封装 Provider
3. 复用而非重建：直接使用 Nanobot 的 SubagentManager 等
4. 兼容而非替换：配置向后兼容
5. LangGraph 集成：支持多 Agent 协作和 Agent Team 功能
"""

from app.extension.scheduler import ModelScheduler, ModelSelectionResult
from app.extension.feature_analyzer import RequestFeatureAnalyzer, RequestFeatures
from app.extension.config_extension import (
    ImageModelConfig,
    ModelFallbackConfig,
    AgentTeamConfig,
    LangGraphConfig,
    ExtendedAgentDefaults,
    ExtendedAgentsConfig,
    ExtendedConfig,
    get_extended_config,
    update_config_with_image_model,
)
from app.extension.agent_loop_adapter import AgentLoopAdapter, EnhancedAgentLoop
from app.extension.vision_agent import (
    VisionAgentConfig,
    VisionAnalysisRequest,
    VisionAnalysisResult,
    VISION_AGENT_SYSTEM_PROMPT,
    VISION_MODEL_CAPABILITIES,
    get_vision_model_capability,
)
from app.extension.vision_agent_manager import VisionAgentManager

# 导出 LangGraph 相关组件
from app.langgraph import (
    AgentGraphBuilder,
    create_agent_graph,
    AgentState,
    GraphState,
)
from app.langgraph.team import (
    AgentTeamManager,
    CreateTeamTool,
    SubagentCoordinator,
    SubagentType,
    TeamConfig,
    TaskResult,
)

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
    "AgentTeamConfig",
    "LangGraphConfig",
    "ExtendedAgentDefaults",
    "ExtendedAgentsConfig",
    "ExtendedConfig",
    "get_extended_config",
    "update_config_with_image_model",
    # AgentLoop 适配器
    "AgentLoopAdapter",
    "EnhancedAgentLoop",  # 向后兼容别名
    # Vision Agent
    "VisionAgentConfig",
    "VisionAnalysisRequest",
    "VisionAnalysisResult",
    "VISION_AGENT_SYSTEM_PROMPT",
    "VISION_MODEL_CAPABILITIES",
    "get_vision_model_capability",
    "VisionAgentManager",
    # LangGraph 组件
    "AgentGraphBuilder",
    "create_agent_graph",
    "AgentState",
    "GraphState",
    # Agent Team
    "AgentTeamManager",
    "CreateTeamTool",
    "SubagentCoordinator",
    "SubagentType",
    "TeamConfig",
    "TaskResult",
]
