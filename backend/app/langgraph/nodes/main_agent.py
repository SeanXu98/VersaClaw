# -*- coding: utf-8 -*-
"""
主 Agent 节点模块

该模块实现主要的对话处理 Agent 节点：
1. 接收用户输入
2. 调用 LLM 生成响应
3. 处理工具调用
4. 返回最终结果

这是 LangGraph 图的核心处理节点。
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from app.langgraph.nodes.base import BaseNode, NodeResult, StreamingNodeMixin
from app.langgraph.state import AgentState, Message


def convert_message_to_dict(msg: Any) -> Dict[str, Any]:
    """
    将消息转换为字典格式
    
    LangGraph 的 add_messages reducer 会将字典消息转换为 LangChain 的
    HumanMessage/AIMessage 对象。此函数将它们转换回字典格式，
    以便 LiteLLMProvider 可以正确处理。
    
    Args:
        msg: 消息对象，可以是字典或 LangChain 消息对象
    
    Returns:
        Dict: 字典格式的消息
    """
    if isinstance(msg, dict):
        return msg
    
    # 处理 LangChain 消息对象
    if hasattr(msg, 'type'):
        # 映射 LangChain 消息类型到 role
        msg_type = msg.type
        role_mapping = {
            'human': 'user',
            'ai': 'assistant',
            'system': 'system',
            'tool': 'tool',
        }
        role = role_mapping.get(msg_type, msg_type)
        
        result = {"role": role, "content": getattr(msg, 'content', '') or ''}
        
        # 处理工具调用
        if hasattr(msg, 'tool_calls') and msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.get('id') if isinstance(tc, dict) else getattr(tc, 'id', ''),
                    "type": "function",
                    "function": {
                        "name": tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', ''),
                        "arguments": tc.get('arguments') if isinstance(tc, dict) else getattr(tc, 'arguments', '{}'),
                    }
                }
                for tc in msg.tool_calls
            ]
        
        # 处理 tool_call_id
        if hasattr(msg, 'tool_call_id') and msg.tool_call_id:
            result["tool_call_id"] = msg.tool_call_id
        
        # 处理 name（用于工具响应）
        if hasattr(msg, 'name') and msg.name:
            result["name"] = msg.name
        
        return result
    
    # 其他情况，尝试转换为字符串
    return {"role": "user", "content": str(msg)}

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider
    from nanobot.agent.tools.registry import ToolRegistry
    from nanobot.agent.context import ContextBuilder
    from nanobot.session.manager import SessionManager
    from app.extension.config_extension import ExtendedConfig

logger = logging.getLogger(__name__)


class MainAgentNode(BaseNode, StreamingNodeMixin):
    """
    主 Agent 节点
    
    负责核心的对话处理逻辑：
    1. 构建上下文
    2. 调用 LLM
    3. 处理工具调用
    4. 生成最终响应
    
    该节点可以独立处理纯文本对话，也可以作为复杂工作流的一部分。
    """
    
    # 系统提示词模板
    SYSTEM_PROMPT_TEMPLATE = """You are a helpful AI assistant powered by the Nanobot framework.

## Core Capabilities
- Answer questions and provide information
- Execute tools to accomplish tasks
- Create and coordinate subagent teams for complex tasks
- Process and analyze images when needed

## Tool Usage
- Use tools when they can help accomplish the user's task
- Always explain what you're doing when using tools
- Handle tool results appropriately

## Agent Team
When encountering complex tasks that benefit from parallel processing or specialized expertise:
- Use the `create_team` tool to spawn specialized subagents
- Coordinate their work and aggregate results
- Provide a comprehensive response to the user

## Continue Reasoning
If you need to continue reasoning without tool calls (e.g., multi-step thinking, self-reflection):
- End your response with: [CONTINUE: <reason>]
- Example: "I need to think more about this approach. [CONTINUE: refine the analysis]"
- This signals you want another turn to continue the reasoning process

## Guidelines
- Be helpful, accurate, and concise
- When uncertain, ask for clarification
- Acknowledge limitations honestly
"""
    
    def __init__(
        self,
        name: str = "main_agent",
        provider: Optional["LLMProvider"] = None,
        tools: Optional["ToolRegistry"] = None,
        context_builder: Optional["ContextBuilder"] = None,
        session_manager: Optional["SessionManager"] = None,
        config: Optional["ExtendedConfig"] = None,
        on_progress: Optional[Callable] = None,
    ):
        """
        初始化主 Agent 节点
        
        Args:
            name: 节点名称
            provider: LLM Provider 实例
            tools: 工具注册表
            context_builder: 上下文构建器
            session_manager: 会话管理器
            config: 扩展配置
            on_progress: 进度回调函数
        """
        super().__init__(
            name=name,
            provider=provider,
            tools=tools,
            config=config,
        )
        self.context_builder = context_builder
        self.session_manager = session_manager
        self.extended_config = config
        self.on_progress = on_progress
    
    async def execute(self, state: AgentState) -> NodeResult:
        """
        执行主 Agent 处理逻辑
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            NodeResult: 处理结果
        """
        try:
            # 获取状态信息
            query = state.get("current_query", "")
            messages = state.get("messages", [])
            selected_model = state.get("selected_model", "")
            iteration = state.get("iteration", 0)
            max_iterations = state.get("max_iterations", 40)
            
            # 检查迭代限制
            if iteration >= max_iterations:
                return NodeResult(
                    success=False,
                    error=f"达到最大迭代次数 {max_iterations}",
                    state_update={"final_response": "抱歉，任务过于复杂，已达到最大处理步数。"},
                )
            
            # 构建消息
            full_messages = await self._build_messages(state)
            
            # 获取工具定义
            tool_definitions = await self._get_tool_definitions()
            
            # 调用 LLM
            self.log_info(f"Calling LLM with model: {selected_model}")
            
            response = await self._call_llm(
                messages=full_messages,
                tools=tool_definitions,
                model=selected_model,
            )
            
            # 处理响应
            if response.get("has_tool_calls", False):
                # 有工具调用
                return await self._handle_tool_calls(state, response)
            else:
                # 无工具调用，生成最终响应
                return await self._handle_final_response(state, response)
            
        except Exception as e:
            self.log_error(f"Error in main agent: {e}")
            return NodeResult(
                success=False,
                error=str(e),
                state_update={
                    "error": str(e),
                    "final_response": f"处理过程中发生错误: {str(e)}",
                },
            )
    
    async def _build_messages(self, state: AgentState) -> List[Message]:
        """
        构建完整的消息列表
        
        Args:
            state: 当前状态
        
        Returns:
            List[Message]: 消息列表
        """
        messages = []
        
        # 添加系统消息
        messages.append({
            "role": "system",
            "content": self._get_system_prompt(),
        })
        
        # 添加历史消息 - 需要转换 LangChain 消息对象为字典
        history = state.get("messages", [])
        for msg in history:
            messages.append(convert_message_to_dict(msg))
        
        # 添加当前用户消息
        query = state.get("current_query", "")
        images = state.get("images", [])
        
        if images:
            # 多模态消息
            user_content = self._build_multimodal_content(query, images)
            messages.append({
                "role": "user",
                "content": user_content,
            })
        else:
            # 纯文本消息
            messages.append({
                "role": "user",
                "content": query,
            })
        
        return messages
    
    def _build_multimodal_content(
        self,
        text: str,
        images: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        构建多模态内容
        
        Args:
            text: 文本内容
            images: 图片列表
        
        Returns:
            List[Dict]: 多模态内容列表
        """
        content = []
        
        # 添加图片
        for img in images:
            image_url = img.get("url", "")
            if image_url:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url},
                })
        
        # 添加文本
        if text:
            content.append({
                "type": "text",
                "text": text,
            })
        
        return content
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return self.SYSTEM_PROMPT_TEMPLATE
    
    async def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        获取工具定义列表
        
        Returns:
            List[Dict]: 工具定义
        """
        if self.tools:
            return self.tools.get_definitions()
        return []
    
    async def _call_llm(
        self,
        messages: List[Message],
        tools: List[Dict[str, Any]],
        model: str,
    ) -> Dict[str, Any]:
        """
        调用 LLM
        
        Args:
            messages: 消息列表
            tools: 工具定义
            model: 模型名称
        
        Returns:
            Dict: LLM 响应
        """
        if not self.provider:
            raise ValueError("LLM Provider not configured")
        
        # 构建调用参数
        kwargs = {
            "messages": messages,
            "tools": tools if tools else None,
            "model": model if model else None,
        }
        
        # 调用 Provider - 使用 chat() 方法（LiteLLMProvider 的原生方法）
        # chat_with_retry 是 ModelScheduler 的封装，provider 本身只有 chat()
        response = await self.provider.chat(**kwargs)
        
        # 解析响应
        return self._parse_llm_response(response)
    
    # CONTINUE 信号正则表达式
    CONTINUE_PATTERN = re.compile(r'\[CONTINUE:\s*([^\]]+)\]\s*$', re.IGNORECASE | re.MULTILINE)
    
    def _parse_llm_response(self, response: Any) -> Dict[str, Any]:
        """
        解析 LLM 响应
        
        Args:
            response: 原始响应
        
        Returns:
            Dict: 解析后的响应
        """
        result = {
            "content": "",
            "has_tool_calls": False,
            "tool_calls": [],
            "reasoning_content": None,
            "should_continue": False,
            "continue_reason": "",
        }
        
        if hasattr(response, "content"):
            result["content"] = response.content or ""
        
        if hasattr(response, "has_tool_calls") and response.has_tool_calls:
            result["has_tool_calls"] = True
            if hasattr(response, "tool_calls"):
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments if isinstance(tc.arguments, dict) else json.loads(tc.arguments or "{}"),
                    }
                    for tc in response.tool_calls
                ]
        
        if hasattr(response, "reasoning_content"):
            result["reasoning_content"] = response.reasoning_content
        
        # 检测 CONTINUE 信号（仅当没有工具调用时）
        if not result["has_tool_calls"] and result["content"]:
            continue_match = self.CONTINUE_PATTERN.search(result["content"])
            if continue_match:
                result["should_continue"] = True
                result["continue_reason"] = continue_match.group(1).strip()
                # 从内容中移除 CONTINUE 信号
                result["content"] = self.CONTINUE_PATTERN.sub("", result["content"]).strip()
        
        return result
    
    async def _handle_tool_calls(
        self,
        state: AgentState,
        response: Dict[str, Any],
    ) -> NodeResult:
        """
        处理工具调用
        
        Args:
            state: 当前状态
            response: LLM 响应
        
        Returns:
            NodeResult: 处理结果
        """
        tool_calls = response.get("tool_calls", [])
        
        # 记录工具调用
        state_update = {
            "tool_calls": tool_calls,
            "iteration": state.get("iteration", 0) + 1,
        }
        
        # 添加助手消息到历史
        messages = state.get("messages", [])
        messages.append({
            "role": "assistant",
            "content": response.get("content", ""),
            "tool_calls": tool_calls,
        })
        state_update["messages"] = messages
        
        # 发送进度通知
        if self.on_progress:
            await self.on_progress(
                f"正在执行工具: {', '.join(tc['name'] for tc in tool_calls)}",
                tool_hint=True,
            )
        
        # 判断是否需要继续执行
        return NodeResult(
            success=True,
            state_update=state_update,
            next_node="tool_execution",
        )
    
    async def _handle_final_response(
        self,
        state: AgentState,
        response: Dict[str, Any],
    ) -> NodeResult:
        """
        处理最终响应
        
        Args:
            state: 当前状态
            response: LLM 响应
        
        Returns:
            NodeResult: 处理结果
        """
        content = response.get("content", "")
        reasoning = response.get("reasoning_content")
        should_continue = response.get("should_continue", False)
        continue_reason = response.get("continue_reason", "")
        
        # 添加助手消息到历史
        messages = state.get("messages", [])
        messages.append({
            "role": "assistant",
            "content": content,
        })
        
        state_update = {
            "messages": messages,
            "should_continue": should_continue,
            "continue_reason": continue_reason,
            "final_response": content if not should_continue else "",
            "reasoning_content": reasoning or "",
        }
        
        # 根据是否继续推理决定下一个节点
        if should_continue:
            logger.info(f"[MainAgent] LLM requested to continue: {continue_reason}")
            # 增加迭代计数
            state_update["iteration"] = state.get("iteration", 0) + 1
            return NodeResult(
                success=True,
                state_update=state_update,
                next_node="main_agent",  # 继续推理
            )
        
        return NodeResult(
            success=True,
            state_update=state_update,
            next_node="end",  # 结束
        )