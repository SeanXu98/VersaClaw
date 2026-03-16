# -*- coding: utf-8 -*-
"""
Nanobot 服务模块

该模块负责管理 Nanobot 组件的完整生命周期，包括：
- 配置加载和重载
- 消息总线管理
- Agent 循环管理（使用增强的 EnhancedAgentLoop）
- LLM Provider 管理
- 多模态模型调度

使用方式:
    from app.services.nanobot_service import NanobotService

    service = NanobotService()
    await service.initialize()
"""
import logging
from typing import Optional, Any

from nanobot.config.loader import load_config
from nanobot.bus.queue import MessageBus

# 使用增强的 AgentLoop 替代原生 AgentLoop
from app.extension import (
    EnhancedAgentLoop,
    ExtendedConfig,
    get_extended_config,
)

# 配置日志
logger = logging.getLogger(__name__)


class NanobotService:
    """
    Nanobot 服务类

    管理 Nanobot 组件的初始化、重载和关闭。
    使用 EnhancedAgentLoop 支持多模态处理。

    属性:
        config: Nanobot 配置对象
        extended_config: 扩展配置对象
        bus: 消息总线实例
        agent_loop: 增强的 Agent 循环实例
        provider: LLM Provider 实例
    """

    def __init__(self):
        """初始化服务（尚未加载配置）"""
        self.config: Optional[Any] = None
        self.extended_config: Optional[ExtendedConfig] = None
        self.bus: Optional[MessageBus] = None
        self.agent_loop: Optional[EnhancedAgentLoop] = None
        self.provider: Optional[Any] = None
        self._initialized: bool = False

    @property
    def is_initialized(self) -> bool:
        """检查服务是否已初始化"""
        return self._initialized

    async def initialize(self) -> bool:
        """
        初始化 Nanobot 组件

        该方法会：
        1. 加载配置文件（包括扩展配置）
        2. 创建消息总线
        3. 创建 LLM Provider
        4. 创建增强的 Agent 循环（支持多模态）

        返回:
            bool: 初始化成功返回 True，失败返回 False
        """
        try:
            # 加载配置
            self.config = load_config()
            logger.info("[Nanobot 服务] 配置加载成功")

            # 加载扩展配置
            self.extended_config = get_extended_config()
            if self.extended_config.defaults.has_image_model_configured:
                logger.info(
                    f"[Nanobot 服务] 视觉模型配置: {self.extended_config.image_model}"
                )

            # 创建消息总线
            from nanobot.providers.litellm_provider import LiteLLMProvider

            self.bus = MessageBus()

            # 创建 Provider
            p = self.config.get_provider()
            model = self.config.agents.defaults.model

            # 检查 API Key 配置
            if not (p and p.api_key) and not model.startswith("bedrock/"):
                logger.warning("[Nanobot 服务] 未配置 API Key，请在 ~/.nanobot/config.json 中设置")

            self.provider = LiteLLMProvider(
                api_key=p.api_key if p else None,
                api_base=self.config.get_api_base(),
                default_model=model,
                extra_headers=p.extra_headers if p else None,
                provider_name=self.config.get_provider_name(),
            )

            # 创建增强的 Agent 循环（支持多模态）
            self.agent_loop = EnhancedAgentLoop(
                bus=self.bus,
                provider=self.provider,
                workspace=self.config.workspace_path,
                model=self.config.agents.defaults.model,
                max_iterations=self.config.agents.defaults.max_tool_iterations,
                temperature=self.config.agents.defaults.temperature,
                max_tokens=self.config.agents.defaults.max_tokens,
                memory_window=self.config.agents.defaults.memory_window,
                reasoning_effort=self.config.agents.defaults.reasoning_effort,
                brave_api_key=self.config.tools.web.search.api_key,
                web_proxy=self.config.tools.web.proxy,
                exec_config=self.config.tools.exec,
                restrict_to_workspace=self.config.tools.restrict_to_workspace,
                mcp_servers=self.config.tools.mcp_servers,
                extended_config=self.extended_config,
            )

            self._initialized = True
            logger.info("[Nanobot 服务] ✓ 初始化成功（支持多模态）")
            return True

        except Exception as e:
            logger.error(f"[Nanobot 服务] ✗ 初始化失败: {e}")
            return False

    async def reload(self) -> bool:
        """
        重新加载 Nanobot 配置

        该方法会：
        1. 关闭旧的 MCP 连接
        2. 重新加载配置文件（包括扩展配置）
        3. 重新创建 Provider
        4. 重新创建增强的 Agent 循环

        返回:
            bool: 重载成功返回 True，失败返回 False
        """
        try:
            logger.info("[Nanobot 服务] 🔄 正在重新加载配置...")

            # 关闭旧的 MCP 连接
            if self.agent_loop:
                await self.agent_loop.close_mcp()

            # 重新加载配置
            self.config = load_config()

            # 重新加载扩展配置
            self.extended_config = get_extended_config()

            # 获取 Provider 配置
            p = self.config.get_provider()
            model = self.config.agents.defaults.model

            # 重新创建 Provider
            from nanobot.providers.litellm_provider import LiteLLMProvider

            self.provider = LiteLLMProvider(
                api_key=p.api_key if p else None,
                api_base=self.config.get_api_base(),
                default_model=model,
                extra_headers=p.extra_headers if p else None,
                provider_name=self.config.get_provider_name(),
            )

            # 重新创建增强的 Agent 循环
            self.agent_loop = EnhancedAgentLoop(
                bus=self.bus,
                provider=self.provider,
                workspace=self.config.workspace_path,
                model=self.config.agents.defaults.model,
                max_iterations=self.config.agents.defaults.max_tool_iterations,
                temperature=self.config.agents.defaults.temperature,
                max_tokens=self.config.agents.defaults.max_tokens,
                memory_window=self.config.agents.defaults.memory_window,
                reasoning_effort=self.config.agents.defaults.reasoning_effort,
                brave_api_key=self.config.tools.web.search.api_key,
                web_proxy=self.config.tools.web.proxy,
                exec_config=self.config.tools.exec,
                restrict_to_workspace=self.config.tools.restrict_to_workspace,
                mcp_servers=self.config.tools.mcp_servers,
                extended_config=self.extended_config,
            )

            logger.info("[Nanobot 服务] ✓ 配置重载成功")
            logger.info(f"[Nanobot 服务]   模型: {self.config.agents.defaults.model}")
            logger.info(f"[Nanobot 服务]   Provider: {self.config.get_provider_name()}")
            logger.info(f"[Nanobot 服务]   API Base: {self.config.get_api_base()}")
            if self.extended_config.defaults.has_image_model_configured:
                logger.info(f"[Nanobot 服务]   视觉模型: {self.extended_config.image_model}")
            return True

        except Exception as e:
            logger.error(f"[Nanobot 服务] ✗ 配置重载失败: {e}")
            return False

    async def shutdown(self) -> None:
        """
        关闭服务并清理资源

        该方法会关闭 MCP 连接并标记服务为未初始化状态。
        """
        if self.agent_loop:
            await self.agent_loop.close_mcp()
        self._initialized = False
        logger.info("[Nanobot 服务] 服务已关闭")

    def get_config_info(self) -> dict:
        """
        获取当前配置信息（不含敏感数据）

        返回:
            dict: 包含模型、Provider、API Base 等信息的字典
        """
        if not self.config:
            return {}

        info = {
            "model": self.config.agents.defaults.model,
            "provider": self.config.get_provider_name(),
            "api_base": self.config.get_api_base(),
            "temperature": self.config.agents.defaults.temperature,
            "max_tokens": self.config.agents.defaults.max_tokens,
        }

        # 添加视觉模型信息
        if self.extended_config and self.extended_config.defaults.has_image_model_configured:
            info["image_model"] = self.extended_config.image_model
            info["image_model_fallbacks"] = self.extended_config.image_model_fallbacks

        return info

    def get_extended_config(self) -> Optional[ExtendedConfig]:
        """
        获取扩展配置

        返回:
            ExtendedConfig | None: 扩展配置对象
        """
        return self.extended_config
