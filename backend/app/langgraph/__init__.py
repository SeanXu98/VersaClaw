# -*- coding: utf-8 -*-
"""
LangGraph Agent 扩展模块

该模块基于 LangGraph 框架实现 Multi-Agent 架构扩展，包括：
- AgentState: 统一的 Agent 状态管理
- GraphBuilder: LangGraph 图构建器
- VisionRouter: 视觉理解智能路由
- AgentTeamManager: 子代理团队管理

核心功能：
1. 自动视觉理解判断：根据用户消息自动选择文本或多模态模型
2. Agent Team：主 Agent 可创建多个 subagent 协同工作

设计原则：
- 保持与 Nanobot 的兼容性
- 使用 LangGraph 的有状态图管理
- 支持流式输出和工具调用
"""

from app.langgraph.state import (
    AgentState,
    GraphState,
    MessageType,
    AgentRole,
    TaskStatus,
    VisionAnalysisResult,
    SubagentTask,
    TeamResult,
)

from app.langgraph.graph import AgentGraphBuilder, create_agent_graph, NanobotContext

__all__ = [
    # State
    "AgentState",
    "GraphState",
    "MessageType",
    "AgentRole",
    "TaskStatus",
    "VisionAnalysisResult",
    "SubagentTask",
    "TeamResult",
    # Graph
    "AgentGraphBuilder",
    "create_agent_graph",
    "NanobotContext",
]