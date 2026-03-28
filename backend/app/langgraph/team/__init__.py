# -*- coding: utf-8 -*-
"""
Agent Team 模块

该模块实现 Agent Team 功能：
- AgentTeamManager: 团队管理器
- CreateTeamTool: 团队创建工具
- SubagentCoordinator: 子代理协调器

核心功能：
- 主 Agent 可以创建多个 subagent 协同工作
- 支持不同类型的子代理（代码、研究、写作等）
- 自动协调和聚合结果
"""

from app.langgraph.team.manager import AgentTeamManager
from app.langgraph.team.tool import CreateTeamTool
from app.langgraph.team.coordinator import SubagentCoordinator
from app.langgraph.team.types import (
    SubagentType,
    SubagentConfig,
    TeamConfig,
    TaskResult,
)

__all__ = [
    "AgentTeamManager",
    "CreateTeamTool",
    "SubagentCoordinator",
    "SubagentType",
    "SubagentConfig",
    "TeamConfig",
    "TaskResult",
]