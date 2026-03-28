# -*- coding: utf-8 -*-
"""
AgentLoop 适配器模块

该模块作为 Nanobot AgentLoop 和 LangGraph AgentGraphBuilder 之间的适配器：

职责边界：
┌─────────────────────────────────────────────────────────────────┐
│                    AgentLoopAdapter                              │
│                      (适配层/桥接层)                             │
├─────────────────────────────────────────────────────────────────┤
│  1. 初始化 Nanobot 核心组件（继承 AgentLoop）                    │
│  2. 构建 NanobotContext，注入给 LangGraph                       │
│  3. 提供统一的处理接口，委托给 AgentGraphBuilder                 │
│  4. 保持向后兼容，支持旧版 API                                   │
└─────────────────────────────────────────────────────────────────┘

设计原则：
- 适配器模式：连接两个系统
- 依赖注入：Nanobot 能力注入到 LangGraph
- 委托执行：核心逻辑由 LangGraph 图处理
- 保持兼容：继承 AgentLoop 复用工具注册等能力

使用方式:
    from app.extension.agent_loop_adapter import AgentLoopAdapter
    
    adapter = AgentLoopAdapter(
        bus=bus,
        provider=provider,
        workspace=workspace,
        extended_config=config,
    )
    
    # 使用 LangGraph 处理（推荐）
    result = await adapter.process("你好")
    
    # 流式处理
    async for event in adapter.process_stream("你好"):
        print(event)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncGenerator, Awaitable, Callable, Optional, TYPE_CHECKING

from loguru import logger

# Nanobot 核心组件
from nanobot.agent.loop import AgentLoop
from nanobot.agent.context import ContextBuilder
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider
from nanobot.session.manager import SessionManager

# 扩展组件
from app.extension.scheduler import ModelScheduler
from app.extension.feature_analyzer import RequestFeatureAnalyzer
from app.extension.config_extension import ExtendedConfig

# LangGraph 核心
from app.langgraph import AgentGraphBuilder, NanobotContext

if TYPE_CHECKING:
    from nanobot.config.schema import ChannelsConfig, ExecToolConfig
    from nanobot.cron.service import CronService


class AgentLoopAdapter(AgentLoop):
    """
    AgentLoop 适配器 - 连接 Nanobot 和 LangGraph
    
    继承 Nanobot AgentLoop 以复用核心能力，但主要处理逻辑委托给 LangGraph。
    
    架构角色：
    ┌──────────────┐     ┌──────────────────────┐     ┌─────────────┐
    │   调用方      │────▶│  AgentLoopAdapter    │────▶│ AgentGraph  │
    │ (StreamProc) │     │     (适配层)         │     │  Builder    │
    └──────────────┘     └──────────────────────┘     └─────────────┘
                                  │
                                  │ 构建 NanobotContext
                                  ▼
                    ┌─────────────────────────────┐
                    │  Nanobot 核心能力注入：      │
                    │  • provider (LLM 调用)      │
                    │  • tools (工具注册表)       │
                    │  • session_manager (会话)   │
                    │  • context_builder (上下文) │
                    └─────────────────────────────┘
    
    使用方式:
        adapter = AgentLoopAdapter(...)
        
        # 主要接口 - 委托给 LangGraph
        result = await adapter.process(content, session_key)
        
        # 流式接口
        async for event in adapter.process_stream(content, session_key):
            yield event
    """
    
    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int = 40,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        memory_window: int = 100,
        reasoning_effort: str | None = None,
        brave_api_key: str | None = None,
        web_proxy: str | None = None,
        exec_config: "ExecToolConfig | None" = None,
        cron_service: "CronService | None" = None,
        restrict_to_workspace: bool = False,
        session_manager: SessionManager | None = None,
        mcp_servers: dict | None = None,
        channels_config: "ChannelsConfig | None" = None,
        # 扩展配置
        extended_config: Optional[ExtendedConfig] = None,
    ):
        """
        初始化 AgentLoop 适配器
        
        Args:
            bus: 消息总线
            provider: LLM Provider
            workspace: 工作空间路径
            model: 默认模型
            max_iterations: 最大迭代次数
            temperature: 温度参数
            max_tokens: 最大 token 数
            memory_window: 记忆窗口大小
            reasoning_effort: 推理强度
            brave_api_key: Brave 搜索 API Key
            web_proxy: Web 代理
            exec_config: 执行工具配置
            cron_service: 定时任务服务
            restrict_to_workspace: 是否限制在工作空间
            session_manager: 会话管理器
            mcp_servers: MCP 服务器配置
            channels_config: 渠道配置
            extended_config: 扩展配置
        """
        # 调用父类初始化 - 获取 Nanobot 核心能力
        super().__init__(
            bus=bus,
            provider=provider,
            workspace=workspace,
            model=model,
            max_iterations=max_iterations,
            temperature=temperature,
            max_tokens=max_tokens,
            memory_window=memory_window,
            reasoning_effort=reasoning_effort,
            brave_api_key=brave_api_key,
            web_proxy=web_proxy,
            exec_config=exec_config,
            cron_service=cron_service,
            restrict_to_workspace=restrict_to_workspace,
            session_manager=session_manager,
            mcp_servers=mcp_servers,
            channels_config=channels_config,
        )
        
        # 扩展配置
        self.extended_config = extended_config or ExtendedConfig()
        
        # 辅助组件（用于兼容旧逻辑）
        self.model_scheduler = ModelScheduler(provider, self.extended_config)
        self.feature_analyzer = RequestFeatureAnalyzer(workspace)
        
        # LangGraph 图构建器（延迟初始化）
        self._graph_builder: Optional[AgentGraphBuilder] = None
        
        logger.info("[AgentLoopAdapter] 初始化完成 - 适配层模式")
    
    # ==================== 核心接口 - 委托给 LangGraph ====================
    
    def _get_nanobot_context(self) -> NanobotContext:
        """
        构建 Nanobot 能力上下文
        
        将 Nanobot 的核心能力封装成 NanobotContext，
        传递给 LangGraph 节点使用。
        
        Returns:
            NanobotContext: Nanobot 能力上下文
        """
        return NanobotContext(
            provider=self.provider,
            tools=self.tools,
            session_manager=getattr(self, 'sessions', None),
            context_builder=getattr(self, 'context_builder', None),
            bus=self.bus,
            workspace=str(self.workspace) if hasattr(self, 'workspace') else None,
        )
    
    def get_graph_builder(self) -> AgentGraphBuilder:
        """
        获取或创建 LangGraph 图构建器
        
        Returns:
            AgentGraphBuilder: 图构建器实例
        """
        if self._graph_builder is None:
            # 构建 NanobotContext
            nanobot_context = self._get_nanobot_context()
            
            # 创建图构建器
            self._graph_builder = AgentGraphBuilder(
                nanobot_context=nanobot_context,
                config=self.extended_config,
            )
            
            logger.debug("[AgentLoopAdapter] 创建 AgentGraphBuilder")
        
        return self._graph_builder
    
    async def process(
        self,
        content: str | list,
        session_key: str = "default",
        channel: str = "web",
        model: Optional[str] = None,
        images: Optional[list] = None,
    ) -> str:
        """
        处理消息（主入口）
        
        委托给 LangGraph AgentGraphBuilder 处理。
        
        Args:
            content: 消息内容
            session_key: 会话标识
            channel: 渠道标识
            model: 指定模型
            images: 图片列表
        
        Returns:
            str: 响应内容
        """
        builder = self.get_graph_builder()
        
        # 准备图片数据
        image_data = None
        if images:
            image_data = [
                {"id": img.get("id"), "url": img.get("url")}
                for img in images
            ]
        
        # 获取或创建会话（使用原生能力）
        session = self.sessions.get_or_create(session_key)
        
        # 加载会话历史（使用原生能力）
        history = session.get_history(max_messages=self.memory_window)
        
        # 委托给 LangGraph 执行，传入历史消息
        result = await builder.ainvoke(
            query=content if isinstance(content, str) else str(content),
            session_key=session_key,
            channel=channel,
            images=image_data,
            model=model or self.model,
            history=history,  # 传入会话历史
        )
        
        # 使用原生的 _save_turn 保存对话轮次
        response_content = result.get("final_response", "")
        messages = [
            {"role": "user", "content": content},
            {"role": "assistant", "content": response_content},
        ]
        self._save_turn(session, messages, 0)
        
        # 使用原生的 sessions.save() 保存到磁盘
        self.sessions.save(session)
        logger.debug(f"[AgentLoopAdapter] 会话已保存: {session_key}")
        
        return response_content
    
    async def process_stream(
        self,
        content: str | list,
        session_key: str = "default",
        channel: str = "web",
        model: Optional[str] = None,
        images: Optional[list] = None,
        on_progress: Optional[Callable[..., Awaitable[None]]] = None,
    ) -> AsyncGenerator[dict, None]:
        """
        流式处理消息（主入口）
        
        委托给 LangGraph AgentGraphBuilder 流式处理。
        
        Args:
            content: 消息内容
            session_key: 会话标识
            channel: 渠道标识
            model: 指定模型
            images: 图片列表
            on_progress: 进度回调
        
        Yields:
            dict: 流式事件
        """
        builder = self.get_graph_builder()
        
        # 准备图片数据
        image_data = None
        if images:
            image_data = [
                {"id": img.get("id"), "url": img.get("url")}
                for img in images
            ]
        
        # 委托给 LangGraph 流式执行
        async for event in builder.astream(
            query=content if isinstance(content, str) else str(content),
            session_key=session_key,
            channel=channel,
            images=image_data,
            model=model or self.model,
        ):
            yield event
    
    # ==================== 向后兼容 - 支持旧版 API ====================
    
    async def _process_message(
        self,
        msg: InboundMessage,
        session_key: str | None = None,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> OutboundMessage | None:
        """
        处理单个入站消息（重写父类方法）
        
        保持与 Nanobot AgentLoop 的兼容性，
        同时使用 LangGraph 处理。
        
        Args:
            msg: 入站消息
            session_key: 会话标识
            on_progress: 进度回调
        
        Returns:
            OutboundMessage | None: 响应消息
        """
        # 提取消息内容
        content = msg.content
        media_files = getattr(msg, 'media', None)
        
        # 转换图片格式
        images = None
        if media_files:
            images = [
                {"id": m.get("id"), "url": m.get("url")}
                for m in media_files
            ]
        
        # 使用 LangGraph 处理
        response = await self.process(
            content=content,
            session_key=session_key or "default",
            channel=getattr(msg, 'channel', 'web'),
            images=images,
        )
        
        # 构建响应消息
        # OutboundMessage 需要 channel 和 chat_id，而不是 session_key
        # session_key 格式为 "channel:chat_id"
        key = session_key or "web:default"
        if ":" in key:
            channel_part, chat_id_part = key.split(":", 1)
        else:
            channel_part = getattr(msg, 'channel', 'web')
            chat_id_part = key
        
        return OutboundMessage(
            channel=channel_part,
            chat_id=chat_id_part,
            content=response,
        )
    
    # ==================== 便捷方法 ====================
    
    def get_scheduler(self) -> ModelScheduler:
        """
        获取模型调度器
        
        Returns:
            ModelScheduler: 模型调度器实例
        """
        return self.model_scheduler
    
    def select_model_for_content(
        self,
        content: str | list | None,
        media_files: Optional[list] = None,
    ):
        """
        为指定内容选择模型
        
        Args:
            content: 消息内容
            media_files: 媒体文件列表
        
        Returns:
            ModelSelectionResult: 模型选择结果
        """
        features = self.feature_analyzer.analyze(content, media_files)
        return self.model_scheduler.select_model(features)
    
    # ==================== 旧版兼容方法（已废弃，保留向后兼容） ====================
    
    async def process_with_langgraph(
        self,
        content: str | list,
        session_key: str,
        channel: str = "web",
        model: Optional[str] = None,
        images: Optional[list] = None,
    ) -> str:
        """
        使用 LangGraph 处理消息（已废弃，请使用 process）
        
        Deprecated: 使用 process() 代替
        """
        logger.warning("[AgentLoopAdapter] process_with_langgraph 已废弃，请使用 process()")
        return await self.process(content, session_key, channel, model, images)
    
    async def process_stream_with_langgraph(
        self,
        content: str | list,
        session_key: str,
        channel: str = "web",
        model: Optional[str] = None,
        images: Optional[list] = None,
        on_progress: Optional[Callable[..., Awaitable[None]]] = None,
    ):
        """
        使用 LangGraph 流式处理消息（已废弃，请使用 process_stream）
        
        Deprecated: 使用 process_stream() 代替
        """
        logger.warning("[AgentLoopAdapter] process_stream_with_langgraph 已废弃，请使用 process_stream()")
        async for event in self.process_stream(content, session_key, channel, model, images, on_progress):
            yield event
    
    def enable_langgraph(self, enable: bool = True) -> None:
        """
        启用或禁用 LangGraph 模式（已废弃，始终使用 LangGraph）
        
        Deprecated: 现在始终使用 LangGraph 模式
        """
        logger.warning("[AgentLoopAdapter] enable_langgraph 已废弃，现在始终使用 LangGraph 模式")


# 向后兼容别名
EnhancedAgentLoop = AgentLoopAdapter