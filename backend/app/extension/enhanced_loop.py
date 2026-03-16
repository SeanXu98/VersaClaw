# -*- coding: utf-8 -*-
"""
增强的 Agent 循环模块

该模块通过继承 Nanobot AgentLoop 实现多模态处理能力：
- 自动检测请求是否包含图片
- 集成 ModelScheduler 进行智能模型选择
- 保持原有工具调用、上下文管理等能力

设计原则：
- 继承而非修改：继承 AgentLoop，重写关键方法
- 保留父类能力：所有原有功能完全保持
- 注入而非替换：仅在特定环节注入多模态逻辑

使用方式:
    from app.extension.enhanced_loop import EnhancedAgentLoop

    agent_loop = EnhancedAgentLoop(
        bus=bus,
        provider=provider,
        workspace=workspace,
        config=extended_config,
    )
"""

from __future__ import annotations

import asyncio
import json
import re
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, TYPE_CHECKING

from loguru import logger

from nanobot.agent.loop import AgentLoop
from nanobot.agent.context import ContextBuilder
from nanobot.agent.subagent import SubagentManager
from nanobot.agent.tools.registry import ToolRegistry
from nanobot.agent.tools.filesystem import ReadFileTool, WriteFileTool, EditFileTool, ListDirTool
from nanobot.agent.tools.shell import ExecTool
from nanobot.agent.tools.web import WebFetchTool, WebSearchTool
from nanobot.agent.tools.message import MessageTool
from nanobot.agent.tools.spawn import SpawnTool
from nanobot.agent.tools.cron import CronTool
from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.providers.base import LLMProvider
from nanobot.session.manager import SessionManager

from app.extension.scheduler import ModelScheduler, ModelSelectionResult
from app.extension.feature_analyzer import RequestFeatureAnalyzer, RequestFeatures
from app.extension.config_extension import ExtendedConfig

if TYPE_CHECKING:
    from nanobot.config.schema import ChannelsConfig, ExecToolConfig
    from nanobot.cron.service import CronService


class EnhancedAgentLoop(AgentLoop):
    """
    增强的 Agent 循环
    
    继承 Nanobot AgentLoop，在保持原有能力的基础上增加：
    1. 多模态请求检测：自动识别图片内容
    2. 智能模型调度：根据请求特征选择合适的模型
    3. 视觉模型切换：检测到图片时自动切换到视觉模型
    
    关键重写方法：
    - _process_message: 入口处增加多模态检测和模型选择
    - _run_agent_loop: 根据选择的模型执行
    
    使用方式:
        agent_loop = EnhancedAgentLoop(
            bus=bus,
            provider=provider,
            workspace=workspace,
            config=extended_config,
        )
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
        # 新增参数：扩展配置
        extended_config: Optional[ExtendedConfig] = None,
    ):
        """
        初始化增强的 Agent 循环
        
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
            extended_config: 扩展配置（新增）
        """
        # 调用父类初始化
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
        
        # 初始化扩展组件
        self.extended_config = extended_config or ExtendedConfig()
        self.model_scheduler = ModelScheduler(provider, self.extended_config)
        self.feature_analyzer = RequestFeatureAnalyzer(workspace)
        
        # 当前请求的模型选择结果（用于追踪）
        self._current_model_selection: Optional[ModelSelectionResult] = None
        
        logger.info("[EnhancedAgentLoop] 初始化完成，支持多模态处理")
    
    async def _process_message(
        self,
        msg: InboundMessage,
        session_key: str | None = None,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
    ) -> OutboundMessage | None:
        """
        处理单个入站消息（重写）
        
        在父类基础上增加：
        1. 多模态请求检测
        2. 智能模型选择
        3. 视觉模型自动切换
        
        Args:
            msg: 入站消息
            session_key: 会话标识
            on_progress: 进度回调
        
        Returns:
            OutboundMessage | None: 响应消息
        """
        # 分析请求特征
        features = self._analyze_request(msg)
        
        # 选择合适的模型
        selection = self.model_scheduler.select_model(features)
        self._current_model_selection = selection
        
        # 记录模型选择
        if selection.fallback_used:
            logger.warning(
                f"[EnhancedAgentLoop] 模型降级: {selection.original_model} -> {selection.model}, "
                f"原因: {selection.reason}"
            )
        elif features.requires_vision:
            logger.info(
                f"[EnhancedAgentLoop] 检测到图片，使用视觉模型: {selection.model}"
            )
        
        # 临时切换模型（如果需要）
        original_model = self.model
        if selection.model != original_model:
            self.model = selection.model
            logger.debug(f"[EnhancedAgentLoop] 临时切换模型: {original_model} -> {selection.model}")
        
        try:
            # 调用父类处理
            response = await super()._process_message(msg, session_key, on_progress)
            
            # 记录成功
            self.model_scheduler.record_success(selection.model)
            
            return response
        
        except Exception as e:
            # 记录错误
            self.model_scheduler.record_error(selection.model, str(e))
            
            # 尝试降级处理
            if self._should_fallback(e, selection):
                fallback_result = await self._try_fallback(
                    msg, session_key, on_progress, selection, features
                )
                if fallback_result:
                    return fallback_result
            
            raise
        
        finally:
            # 恢复原始模型
            if selection.model != original_model:
                self.model = original_model
            self._current_model_selection = None
    
    def _analyze_request(self, msg: InboundMessage) -> RequestFeatures:
        """
        分析请求特征
        
        Args:
            msg: 入站消息
        
        Returns:
            RequestFeatures: 请求特征
        """
        content = msg.content
        media_files = msg.media if hasattr(msg, 'media') else None
        
        return self.feature_analyzer.analyze(content, media_files)
    
    def _should_fallback(self, error: Exception, selection: ModelSelectionResult) -> bool:
        """
        判断是否应该尝试降级
        
        Args:
            error: 发生的错误
            selection: 当前模型选择结果
        
        Returns:
            bool: 是否应该降级
        """
        # 如果已经使用了 fallback，不再继续降级
        if selection.fallback_used:
            return False
        
        # 检查是否是模型不可用错误
        error_str = str(error).lower()
        fallback_triggers = [
            "model not found",
            "does not support",
            "not available",
            "rate limit",
            "overloaded",
            "429",
            "503",
        ]
        
        return any(trigger in error_str for trigger in fallback_triggers)
    
    async def _try_fallback(
        self,
        msg: InboundMessage,
        session_key: str | None,
        on_progress: Callable[[str], Awaitable[None]] | None,
        failed_selection: ModelSelectionResult,
        features: RequestFeatures,
    ) -> OutboundMessage | None:
        """
        尝试使用降级模型处理请求
        
        Args:
            msg: 入站消息
            session_key: 会话标识
            on_progress: 进度回调
            failed_selection: 失败的模型选择结果
            features: 请求特征
        
        Returns:
            OutboundMessage | None: 响应消息
        """
        # 获取降级链
        model_type = "vision" if features.requires_vision else "text"
        fallback_chain = self.model_scheduler.get_fallback_chain(model_type)
        
        # 跳过已失败的模型
        for fallback_model in fallback_chain:
            if fallback_model == failed_selection.model:
                continue
            
            if not self.model_scheduler._is_model_available(fallback_model):
                continue
            
            logger.info(f"[EnhancedAgentLoop] 尝试降级模型: {fallback_model}")
            
            # 临时切换模型
            original_model = self.model
            self.model = fallback_model
            
            try:
                response = await super()._process_message(msg, session_key, on_progress)
                self.model_scheduler.record_success(fallback_model)
                return response
            
            except Exception as e:
                self.model_scheduler.record_error(fallback_model, str(e))
                logger.warning(f"[EnhancedAgentLoop] 降级模型 {fallback_model} 失败: {e}")
            
            finally:
                self.model = original_model
        
        return None
    
    # ==================== 公开接口 ====================
    
    def get_current_model_selection(self) -> Optional[ModelSelectionResult]:
        """
        获取当前请求的模型选择结果
        
        Returns:
            ModelSelectionResult | None: 模型选择结果
        """
        return self._current_model_selection
    
    def get_scheduler(self) -> ModelScheduler:
        """
        获取模型调度器
        
        Returns:
            ModelScheduler: 模型调度器实例
        """
        return self.model_scheduler
    
    # ==================== 便捷方法 ====================
    
    def select_model_for_content(
        self,
        content: str | list | None,
        media_files: Optional[list] = None,
    ) -> ModelSelectionResult:
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
    
    def is_current_model_vision_capable(self) -> bool:
        """
        检查当前模型是否支持视觉能力
        
        Returns:
            bool: 是否支持视觉能力
        """
        if self._current_model_selection:
            return self._current_model_selection.model_type == "vision"
        return self.model_scheduler.is_vision_model(self.model)
