# -*- coding: utf-8 -*-
"""
Create Team Tool 模块

该模块实现创建 Agent 团队的工具：
- 主 Agent 可以调用此工具创建子代理团队
- 支持多种子代理类型
- 自动协调和聚合结果

这是给主 Agent 提供的关键工具，用于处理复杂任务。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.langgraph.team.types import SubagentType

if TYPE_CHECKING:
    from nanobot.agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


# 工具定义（符合 OpenAI function calling 格式）
CREATE_TEAM_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "create_team",
        "description": """Create a team of specialized subagents to work on complex tasks collaboratively.

Use this tool when:
1. The task requires multiple different skills (coding, research, writing, etc.)
2. Different aspects of the task can be parallelized
3. You need specialized expertise that you don't have

The team will work together and return a comprehensive result.""",
        "parameters": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "Name for the team (e.g., 'Research Team', 'Code Review Team')"
                },
                "task_description": {
                    "type": "string",
                    "description": "Clear description of the overall task for the team"
                },
                "members": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "coder", "researcher", "writer", "reviewer",
                                    "tester", "data_analyst", "translator",
                                    "summarizer", "explainer", "general"
                                ],
                                "description": "Type of subagent"
                            },
                            "name": {
                                "type": "string",
                                "description": "Name for this subagent"
                            },
                            "task": {
                                "type": "string",
                                "description": "Specific task for this subagent"
                            },
                            "tools": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Tools this subagent can use"
                            }
                        },
                        "required": ["type", "task"]
                    },
                    "description": "List of team members with their roles and tasks"
                },
                "coordination_mode": {
                    "type": "string",
                    "enum": ["parallel", "sequential", "hierarchical"],
                    "default": "parallel",
                    "description": "How team members coordinate"
                },
                "aggregation_strategy": {
                    "type": "string",
                    "enum": ["combine", "summarize", "vote"],
                    "default": "combine",
                    "description": "How to aggregate results from team members"
                }
            },
            "required": ["team_name", "task_description", "members"]
        }
    }
}


class CreateTeamTool:
    """
    创建团队工具
    
    允许主 Agent 创建子代理团队来处理复杂任务。
    
    使用方式:
        tool = CreateTeamTool(team_manager)
        result = await tool.execute(
            team_name="Research Team",
            task_description="Research the impact of AI on healthcare",
            members=[
                {"type": "researcher", "task": "Research AI applications"},
                {"type": "data_analyst", "task": "Analyze healthcare data"},
            ]
        )
    """
    
    def __init__(
        self,
        team_manager: Any = None,
        provider: Any = None,
    ):
        """
        初始化工具
        
        Args:
            team_manager: AgentTeamManager 实例
            provider: LLM Provider 实例
        """
        self.team_manager = team_manager
        self.provider = provider
    
    @property
    def definition(self) -> Dict[str, Any]:
        """返回工具定义"""
        return CREATE_TEAM_TOOL_DEFINITION
    
    async def execute(
        self,
        team_name: str,
        task_description: str,
        members: List[Dict[str, Any]],
        coordination_mode: str = "parallel",
        aggregation_strategy: str = "combine",
    ) -> str:
        """
        执行创建团队操作
        
        Args:
            team_name: 团队名称
            task_description: 任务描述
            members: 成员配置列表
            coordination_mode: 协作模式
            aggregation_strategy: 聚合策略
        
        Returns:
            str: 执行结果
        """
        from app.langgraph.team import AgentTeamManager
        
        try:
            # 如果没有 team_manager，创建一个
            if not self.team_manager:
                self.team_manager = AgentTeamManager(provider=self.provider)
            
            logger.info(
                f"[CreateTeamTool] Creating team '{team_name}' with {len(members)} members"
            )
            
            # 创建团队配置
            team_config = self.team_manager.create_team(
                name=team_name,
                description=task_description,
                members=members,
                coordination_mode=coordination_mode,
                aggregation_strategy=aggregation_strategy,
            )
            
            # 执行团队任务
            result = await self.team_manager.execute_team(
                team_config=team_config,
                task_description=task_description,
            )
            
            # 格式化结果
            if result.success:
                return self._format_success_result(result)
            else:
                return self._format_error_result(result)
            
        except Exception as e:
            logger.error(f"[CreateTeamTool] Failed to create team: {e}")
            return f"创建团队失败: {str(e)}"
    
    def _format_success_result(self, result: Any) -> str:
        """格式化成功结果"""
        lines = [
            f"# 团队执行结果",
            f"",
            f"团队 ID: {result.team_id}",
            f"执行时间: {result.total_time:.2f}秒",
            f"Token 使用: {result.total_tokens}",
            f"",
            f"## 各成员结果",
            "",
        ]
        
        for task_result in result.task_results:
            status = "✓" if task_result.success else "✗"
            lines.append(f"### {status} {task_result.subagent_name}")
            lines.append(f"时间: {task_result.execution_time:.2f}秒")
            if task_result.error:
                lines.append(f"错误: {task_result.error}")
            else:
                lines.append("")
                lines.append(task_result.output[:500])
                if len(task_result.output) > 500:
                    lines.append("...")
            lines.append("")
        
        lines.append("## 聚合结果")
        lines.append("")
        lines.append(result.aggregated_output)
        
        return "\n".join(lines)
    
    def _format_error_result(self, result: Any) -> str:
        """格式化错误结果"""
        return f"团队执行失败: 部分成员执行出错，请查看详细信息。"


def register_create_team_tool(
    tool_registry: "ToolRegistry",
    team_manager: Any = None,
    provider: Any = None,
) -> None:
    """
    注册 create_team 工具到工具注册表
    
    Args:
        tool_registry: Nanobot 工具注册表
        team_manager: AgentTeamManager 实例
        provider: LLM Provider 实例
    """
    tool = CreateTeamTool(team_manager=team_manager, provider=provider)
    
    # 注册工具
    tool_registry.register(
        name="create_team",
        definition=tool.definition,
        handler=tool.execute,
    )
    
    logger.info("[CreateTeamTool] Registered create_team tool")