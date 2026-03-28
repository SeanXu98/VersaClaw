# -*- coding: utf-8 -*-
"""
工具执行节点模块

该模块实现工具调用执行 Agent 节点：
1. 接收工具调用请求
2. 执行对应的工具
3. 返回工具执行结果

这是 LangGraph 图中负责工具执行的核心节点。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from app.langgraph.nodes.base import BaseNode, NodeResult, StreamingNodeMixin
from app.langgraph.state import AgentState

if TYPE_CHECKING:
    from nanobot.agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutionNode(BaseNode, StreamingNodeMixin):
    """
    工具执行节点
    
    负责执行 Agent 调用的工具：
    1. 解析工具调用请求
    2. 执行对应的工具
    3. 收集执行结果
    4. 将结果添加到消息历史
    
    支持的工具类型：
    - 文件操作：read_file, write_file, edit_file, list_dir
    - Shell 执行：exec
    - Web 操作：web_fetch, web_search
    - 消息工具：message
    - 子代理：spawn
    - 团队创建：create_team（新增）
    """
    
    def __init__(
        self,
        name: str = "tool_execution",
        tools: Optional["ToolRegistry"] = None,
        on_progress: Optional[Callable] = None,
    ):
        """
        初始化工具执行节点
        
        Args:
            name: 节点名称
            tools: 工具注册表
            on_progress: 进度回调
        """
        super().__init__(name=name, tools=tools)
        self.on_progress = on_progress
    
    async def execute(self, state: AgentState) -> NodeResult:
        """
        执行工具调用
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            NodeResult: 执行结果
        """
        try:
            tool_calls = state.get("tool_calls", [])
            
            if not tool_calls:
                return NodeResult(
                    success=True,
                    state_update={},
                    next_node="main_agent",
                )
            
            # 执行所有工具调用
            tool_results = {}
            
            for tool_call in tool_calls:
                tool_id = tool_call.get("id", "")
                tool_name = tool_call.get("name", "")
                arguments = tool_call.get("arguments", {})
                
                self.log_info(f"Executing tool: {tool_name}")
                
                # 发送工具调用开始事件
                if self.on_progress:
                    await self.on_progress(
                        self._format_tool_hint(tool_name, arguments),
                        tool_hint=True,
                    )
                
                try:
                    # 执行工具
                    result = await self._execute_tool(tool_name, arguments)
                    
                    # 记录成功
                    tool_results[tool_id] = {
                        "name": tool_name,
                        "result": result,
                        "success": True,
                    }
                    
                    self.log_info(f"Tool {tool_name} executed successfully")
                    
                except Exception as e:
                    # 记录失败
                    error_msg = str(e)
                    tool_results[tool_id] = {
                        "name": tool_name,
                        "result": error_msg,
                        "success": False,
                    }
                    
                    self.log_error(f"Tool {tool_name} failed: {error_msg}")
            
            # 更新消息历史
            messages = state.get("messages", [])
            
            # 为每个工具结果添加消息
            for tool_call in tool_calls:
                tool_id = tool_call.get("id", "")
                tool_result = tool_results.get(tool_id, {})
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": str(tool_result.get("result", "")),
                })
            
            state_update = {
                "tool_results": tool_results,
                "messages": messages,
                "tool_calls": [],  # 清空待执行的调用
            }
            
            return NodeResult(
                success=True,
                state_update=state_update,
                next_node="main_agent",  # 返回主 Agent 继续处理
            )
            
        except Exception as e:
            self.log_error(f"Error in tool execution: {e}")
            return NodeResult(
                success=False,
                error=str(e),
                state_update={
                    "error": str(e),
                },
                next_node="main_agent",
            )
    
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """
        执行单个工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            Any: 工具执行结果
        """
        if not self.tools:
            raise ValueError("Tool registry not configured")
        
        # 检查是否是特殊工具
        if tool_name == "create_team":
            # 使用 AgentTeamManager 处理
            return await self._execute_create_team(arguments)
        
        # 使用 Nanobot 工具注册表执行
        result = await self.tools.execute(tool_name, arguments)
        return result
    
    async def _execute_create_team(
        self,
        arguments: Dict[str, Any],
    ) -> str:
        """
        执行创建团队工具
        
        Args:
            arguments: 工具参数，符合 CREATE_TEAM_TOOL_DEFINITION 的结构
        
        Returns:
            str: 执行结果
        """
        from app.langgraph.team import AgentTeamManager
        
        # 解析参数（根据工具定义的结构）
        team_name = arguments.get("team_name", "Agent Team")
        task_description = arguments.get("task_description", "")
        members = arguments.get("members", [])
        coordination_mode = arguments.get("coordination_mode", "parallel")
        aggregation_strategy = arguments.get("aggregation_strategy", "combine")
        
        # 创建团队管理器
        team_manager = AgentTeamManager(
            provider=self.tools.provider if hasattr(self.tools, "provider") else None,
        )
        
        # 创建团队配置
        team_config = team_manager.create_team(
            name=team_name,
            description=task_description,
            members=members,
            coordination_mode=coordination_mode,
            aggregation_strategy=aggregation_strategy,
        )
        
        # 执行团队任务
        result = await team_manager.execute_team(
            team_config=team_config,
            task_description=task_description,
        )
        
        # 返回聚合结果
        return result.aggregated_output
    
    def _format_tool_hint(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> str:
        """
        格式化工具调用提示
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
        
        Returns:
            str: 格式化的提示
        """
        # 简化参数显示
        if isinstance(arguments, dict):
            # 只显示关键参数
            key_args = {}
            for key, value in list(arguments.items())[:3]:
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                key_args[key] = value
            args_str = json.dumps(key_args, ensure_ascii=False)
        else:
            args_str = str(arguments)[:100]
        
        return f"Tool call: {tool_name}({args_str})"