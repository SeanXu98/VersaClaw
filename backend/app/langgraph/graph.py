# -*- coding: utf-8 -*-
"""
Agent Graph Builder 模块

该模块实现 LangGraph 图构建器：
1. 创建 Agent 状态图
2. 添加节点和边
3. 配置条件路由
4. 提供执行接口

这是 LangGraph 架构的核心组件，是整个 Agent 系统的「大脑」。
所有请求处理逻辑都通过此图编排。

设计原则：
- 依赖注入：接收 Nanobot 能力作为参数
- 单一入口：所有请求通过 ainvoke/astream 进入
- 状态驱动：使用 AgentState 管理执行状态
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.langgraph.state import AgentState, create_initial_state
from app.langgraph.nodes import (
    BaseNode,
    MainAgentNode,
    VisionAgentNode,
    ToolExecutionNode,
    VisionRouter,
)

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider
    from nanobot.agent.tools.registry import ToolRegistry
    from nanobot.agent.context import ContextBuilder
    from nanobot.session.manager import SessionManager
    from app.extension.config_extension import ExtendedConfig

logger = logging.getLogger(__name__)


@dataclass
class NanobotContext:
    """
    Nanobot 能力上下文
    
    封装 Nanobot 框架提供的核心能力，通过依赖注入传递给 LangGraph 节点。
    
    这种设计允许：
    1. LangGraph 节点使用 Nanobot 的工具、会话管理等能力
    2. 保持关注点分离，LangGraph 只关心工作流编排
    3. 方便测试，可以注入 Mock 对象
    
    Attributes:
        provider: LLM Provider（调用大模型）
        tools: 工具注册表（文件操作、Shell 执行等）
        session_manager: 会话管理器（上下文记忆）
        context_builder: 上下文构建器（消息构建）
        bus: 消息总线（事件发布）
    """
    provider: Optional["LLMProvider"] = None
    tools: Optional["ToolRegistry"] = None
    session_manager: Optional["SessionManager"] = None
    context_builder: Optional["ContextBuilder"] = None
    bus: Optional[Any] = None  # MessageBus
    workspace: Optional[str] = None


class AgentGraphBuilder:
    """
    Agent 图构建器
    
    负责构建和管理 LangGraph 状态图。
    
    核心能力：
    1. 创建 Agent 工作流图
    2. 配置节点和边
    3. 设置条件路由
    4. 提供同步和异步执行接口
    
    图结构：
    ```
    START -> VisionRouter -> [vision_agent | main_agent]
                                |                    |
                                v                    v
                           main_agent <-------- main_agent
                                |
                                v
                        tool_execution (如有工具调用)
                                |
                                v
                           main_agent
                                |
                                v
                              END
    ```
    
    使用方式:
        # 方式一：使用 NanobotContext（推荐）
        context = NanobotContext(provider=provider, tools=tools, ...)
        builder = AgentGraphBuilder(nanobot_context=context, config=config)
        
        # 方式二：直接传参（向后兼容）
        builder = AgentGraphBuilder(provider=provider, tools=tools, config=config)
        
        graph = builder.build()
        result = await builder.ainvoke(query="你好")
    """
    
    def __init__(
        self,
        nanobot_context: Optional[NanobotContext] = None,
        provider: Optional["LLMProvider"] = None,
        tools: Optional["ToolRegistry"] = None,
        session_manager: Optional["SessionManager"] = None,
        config: Optional["ExtendedConfig"] = None,
        on_progress: Optional[Callable] = None,
    ):
        """
        初始化图构建器
        
        支持两种初始化方式：
        1. 传入 NanobotContext 对象（推荐）
        2. 分别传入各个组件（向后兼容）
        
        Args:
            nanobot_context: Nanobot 能力上下文（推荐）
            provider: LLM Provider 实例
            tools: 工具注册表
            session_manager: 会话管理器
            config: 扩展配置
            on_progress: 进度回调
        """
        # 如果提供了 NanobotContext，优先使用
        if nanobot_context:
            self.provider = nanobot_context.provider
            self.tools = nanobot_context.tools
            self.session_manager = nanobot_context.session_manager
            self.context_builder = nanobot_context.context_builder
            self.bus = nanobot_context.bus
            self.workspace = nanobot_context.workspace
        else:
            # 向后兼容：使用单独的参数
            self.provider = provider
            self.tools = tools
            self.session_manager = session_manager
            self.context_builder = None
            self.bus = None
            self.workspace = None
        
        self.config = config
        self.on_progress = on_progress
        
        # 节点实例
        self._nodes: Dict[str, BaseNode] = {}
        self._graph = None
        self._compiled_graph = None
    
    def build(self) -> "CompiledGraph":
        """
        构建 Agent 图
        
        Returns:
            CompiledGraph: 编译后的可执行图
        """
        logger.info("[AgentGraphBuilder] Building agent graph...")
        
        # 创建状态图
        graph = StateGraph(AgentState)
        
        # 创建节点
        self._create_nodes()
        
        # 添加节点到图
        self._add_nodes_to_graph(graph)
        
        # 设置入口点
        graph.set_entry_point("vision_router")
        
        # 添加条件边
        self._add_conditional_edges(graph)
        
        # 添加普通边
        self._add_edges(graph)
        
        # 编译图
        self._graph = graph
        self._compiled_graph = graph.compile(checkpointer=MemorySaver())
        
        logger.info("[AgentGraphBuilder] Agent graph built successfully")
        
        return self._compiled_graph
    
    def _create_nodes(self) -> None:
        """创建所有节点实例"""
        # 视觉路由器
        self._nodes["vision_router"] = VisionRouter(
            name="vision_router",
            config=self.config,
            vision_check_fn=self._get_vision_check_fn(),
        )
        
        # 主 Agent
        self._nodes["main_agent"] = MainAgentNode(
            name="main_agent",
            provider=self.provider,
            tools=self.tools,
            session_manager=self.session_manager,
            config=self.config,
            on_progress=self.on_progress,
        )
        
        # 视觉 Agent
        self._nodes["vision_agent"] = VisionAgentNode(
            name="vision_agent",
            provider=self.provider,
            config=self.config,
            on_progress=self.on_progress,
        )
        
        # 工具执行
        self._nodes["tool_execution"] = ToolExecutionNode(
            name="tool_execution",
            tools=self.tools,
            on_progress=self.on_progress,
        )
    
    def _add_nodes_to_graph(self, graph: StateGraph) -> None:
        """将节点添加到图中"""
        for name, node in self._nodes.items():
            graph.add_node(name, node)
    
    def _add_conditional_edges(self, graph: StateGraph) -> None:
        """添加条件边"""
        # 从 vision_router 的条件路由
        graph.add_conditional_edges(
            "vision_router",
            self._route_vision,
            {
                "vision_agent": "vision_agent",
                "main_agent": "main_agent",
            }
        )
        
        # 从 main_agent 的条件路由
        # 支持: tool_execution / main_agent(自循环) / END
        graph.add_conditional_edges(
            "main_agent",
            self._route_after_main,
            {
                "tool_execution": "tool_execution",
                "main_agent": "main_agent",  # 新增: 支持继续推理的自循环
                "end": END,
            }
        )
    
    def _add_edges(self, graph: StateGraph) -> None:
        """添加普通边"""
        # vision_agent -> main_agent
        graph.add_edge("vision_agent", "main_agent")
        
        # tool_execution -> main_agent
        graph.add_edge("tool_execution", "main_agent")
    
    def _route_vision(self, state: AgentState) -> str:
        """
        视觉路由条件函数
        
        Args:
            state: 当前状态
        
        Returns:
            str: 下一个节点名称
        """
        vision_analysis = state.get("vision_analysis", {})
        requires_vision = vision_analysis.get("requires_vision", False)
        
        if requires_vision:
            logger.debug("[AgentGraphBuilder] Routing to vision_agent")
            return "vision_agent"
        
        logger.debug("[AgentGraphBuilder] Routing to main_agent")
        return "main_agent"
    
    def _route_after_main(self, state: AgentState) -> str:
        """
        主 Agent 后续路由条件函数
        
        支持 ReAct 范式的三种退出方式：
        1. 有工具调用 → tool_execution
        2. LLM 请求继续推理（should_continue=True）→ main_agent 自循环
        3. 完成 → END
        
        Args:
            state: 当前状态
        
        Returns:
            str: 下一个节点名称
        """
        tool_calls = state.get("tool_calls", [])
        
        if tool_calls:
            logger.debug("[AgentGraphBuilder] Routing to tool_execution")
            return "tool_execution"
        
        # 检查 LLM 是否请求继续推理（非工具调用场景）
        should_continue = state.get("should_continue", False)
        if should_continue:
            continue_reason = state.get("continue_reason", "")
            logger.debug(f"[AgentGraphBuilder] Routing to main_agent for continued reasoning: {continue_reason}")
            return "main_agent"
        
        logger.debug("[AgentGraphBuilder] Routing to END")
        return "end"
    
    def _get_vision_check_fn(self) -> Callable[[str], bool]:
        """获取视觉模型检测函数"""
        if self.config and hasattr(self.config, "defaults"):
            vision_model = self.config.image_model
            if vision_model:
                return lambda m: m == vision_model or self._is_vision_model_by_pattern(m)
        
        return self._is_vision_model_by_pattern
    
    def _is_vision_model_by_pattern(self, model: str) -> bool:
        """通过模式匹配检测视觉模型"""
        if not model:
            return False
        
        patterns = [
            "gpt-4-vision", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
            "claude-3", "claude-3.5", "gemini-1.5", "gemini-2",
            "vision", "llava", "qwen-vl", "glm-4v",
        ]
        
        return any(p in model.lower() for p in patterns)
    
    async def ainvoke(
        self,
        query: str,
        session_key: str = "default",
        channel: str = "web",
        images: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        异步执行 Agent 图
        
        Args:
            query: 用户查询
            session_key: 会话标识
            channel: 渠道标识
            images: 图片列表
            model: 指定模型
            history: 会话历史消息
        
        Returns:
            Dict: 执行结果
        """
        if not self._compiled_graph:
            self.build()
        
        # 创建初始状态，传入历史消息
        initial_state = create_initial_state(
            query=query,
            session_key=session_key,
            channel=channel,
            images=images,
            model=model,
            history=history,
        )
        
        # 执行图
        config = {"configurable": {"thread_id": session_key}}
        result = await self._compiled_graph.ainvoke(initial_state, config=config)
        
        return result
    
    def invoke(
        self,
        query: str,
        session_key: str = "default",
        channel: str = "web",
        images: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        同步执行 Agent 图
        
        Args:
            query: 用户查询
            session_key: 会话标识
            channel: 渠道标识
            images: 图片列表
            model: 指定模型
            history: 会话历史消息
        
        Returns:
            Dict: 执行结果
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(
            self.ainvoke(
                query=query,
                session_key=session_key,
                channel=channel,
                images=images,
                model=model,
                history=history,
            )
        )
    
    async def astream(
        self,
        query: str,
        session_key: str = "default",
        channel: str = "web",
        images: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        流式执行 Agent 图
        
        Args:
            query: 用户查询
            session_key: 会话标识
            channel: 渠道标识
            images: 图片列表
            model: 指定模型
            history: 会话历史消息
        
        Yields:
            Dict: 状态更新事件
        """
        if not self._compiled_graph:
            self.build()
        
        # 创建初始状态，传入历史消息
        initial_state = create_initial_state(
            query=query,
            session_key=session_key,
            channel=channel,
            images=images,
            model=model,
            history=history,
        )
        
        # 流式执行图
        config = {"configurable": {"thread_id": session_key}}
        
        async for event in self._compiled_graph.astream_events(
            initial_state,
            config=config,
            version="v1",
        ):
            yield event
    
    def get_graph_visualization(self) -> str:
        """
        获取图的可视化表示（ASCII 格式）
        
        Returns:
            str: 图的可视化
        """
        if not self._compiled_graph:
            self.build()
        
        return self._get_ascii_visualization()
    
    def _get_ascii_visualization(self) -> str:
        """获取 ASCII 格式的图可视化"""
        return """
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Graph Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐                                                │
│  │    START    │                                                │
│  └──────┬──────┘                                                │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐     ┌──────────────────────┐                   │
│  │VisionRouter │────▶│  requires_vision?    │                   │
│  └─────────────┘     └──────────┬───────────┘                   │
│                                 │                                │
│              ┌──────────────────┼──────────────────┐            │
│              │ Yes              │ No               │            │
│              ▼                  ▼                  │            │
│     ┌──────────────┐    ┌──────────────┐           │            │
│     │ VisionAgent  │    │  MainAgent   │◀──────────┘            │
│     └──────┬───────┘    └──────┬───────┘                        │
│            │                   │                                 │
│            └───────────────────┤                                 │
│                                │                                 │
│                                ▼                                 │
│                    ┌───────────────────────┐                     │
│                    │   has_tool_calls?     │                     │
│                    └───────────┬───────────┘                     │
│                                │                                 │
│              ┌─────────────────┼─────────────────┐              │
│              │ Yes             │ No              │              │
│              ▼                 ▼                 │              │
│     ┌───────────────┐   ┌─────────────┐         │              │
│     │ToolExecution  │   │    END      │         │              │
│     └───────┬───────┘   └─────────────┘         │              │
│             │                                    │              │
│             └────────────────────────────────────┘              │
│                                                                │
└─────────────────────────────────────────────────────────────────┘
"""


def create_agent_graph(
    provider: Optional["LLMProvider"] = None,
    tools: Optional["ToolRegistry"] = None,
    config: Optional["ExtendedConfig"] = None,
    on_progress: Optional[Callable] = None,
) -> "CompiledGraph":
    """
    创建 Agent 图的便捷函数
    
    这是一个独立函数，用于快速创建编译好的 Agent 图。
    
    Args:
        provider: LLM Provider 实例
        tools: 工具注册表
        config: 扩展配置
        on_progress: 进度回调
    
    Returns:
        CompiledGraph: 编译后的可执行图
    
    使用方式:
        graph = create_agent_graph(provider=provider, config=config)
        result = await graph.ainvoke(initial_state)
    """
    builder = AgentGraphBuilder(
        provider=provider,
        tools=tools,
        config=config,
        on_progress=on_progress,
    )
    return builder.build()