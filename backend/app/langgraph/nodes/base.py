# -*- coding: utf-8 -*-
"""
节点基类模块

该模块定义了 LangGraph 节点的基础抽象类和通用接口。
所有具体节点实现都应继承 BaseNode。
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from app.langgraph.state import AgentState

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider
    from nanobot.agent.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class NodeResult:
    """
    节点执行结果
    
    Attributes:
        success: 是否成功
        state_update: 状态更新字典
        next_node: 下一个节点名称（可选）
        error: 错误信息
        metadata: 元数据
    """
    success: bool = True
    state_update: Dict[str, Any] = field(default_factory=dict)
    next_node: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "state_update": self.state_update,
            "next_node": self.next_node,
            "error": self.error,
            "metadata": self.metadata,
        }


class BaseNode(ABC):
    """
    节点基类
    
    所有 LangGraph 节点都应继承此类。
    提供通用的初始化、执行和错误处理逻辑。
    
    Attributes:
        name: 节点名称
        provider: LLM Provider
        tools: 工具注册表
        config: 配置字典
    """
    
    def __init__(
        self,
        name: str,
        provider: Optional["LLMProvider"] = None,
        tools: Optional["ToolRegistry"] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化节点
        
        Args:
            name: 节点名称
            provider: LLM Provider 实例
            tools: 工具注册表实例
            config: 配置字典
        """
        self.name = name
        self.provider = provider
        self.tools = tools
        self.config = config or {}
        self._logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def execute(self, state: AgentState) -> NodeResult:
        """
        执行节点逻辑
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            NodeResult: 执行结果
        """
        pass
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        使节点可调用，符合 LangGraph 节点函数签名
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            AgentState: 更新后的状态
        """
        try:
            result = asyncio.get_event_loop().run_until_complete(self.execute(state))
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            result = asyncio.run(self.execute(state))
        
        # 更新状态
        if result.success:
            state.update(result.state_update)
            if result.error:
                state["error"] = result.error
        else:
            state["error"] = result.error or f"Node {self.name} failed"
        
        return state
    
    async def __acall__(self, state: AgentState) -> AgentState:
        """
        异步调用方法
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            AgentState: 更新后的状态
        """
        result = await self.execute(state)
        
        # 更新状态
        if result.success:
            state.update(result.state_update)
            if result.error:
                state["error"] = result.error
        else:
            state["error"] = result.error or f"Node {self.name} failed"
        
        return state
    
    def log(self, level: int, message: str, **kwargs):
        """记录日志"""
        self._logger.log(level, f"[{self.name}] {message}", **kwargs)
    
    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        self.log(logging.INFO, message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """记录错误日志"""
        self.log(logging.ERROR, message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.log(logging.DEBUG, message, **kwargs)


class AsyncNodeMixin:
    """
    异步节点混入类
    
    提供异步执行的辅助方法。
    """
    
    @staticmethod
    async def run_async(func: Callable, *args, **kwargs) -> Any:
        """在异步上下文中运行同步函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    @staticmethod
    async def gather_with_concurrency(n: int, *tasks) -> List[Any]:
        """限制并发数的 gather"""
        semaphore = asyncio.Semaphore(n)
        
        async def sem_task(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*[sem_task(t) for t in tasks])


class StreamingNodeMixin:
    """
    流式输出节点混入类
    
    提供流式输出的辅助方法。
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stream_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    
    def set_stream_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        设置流式输出回调
        
        Args:
            callback: 回调函数，接收 (content, metadata) 参数
        """
        self._stream_callback = callback
    
    def emit_stream(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        发送流式内容
        
        Args:
            content: 内容
            metadata: 元数据
        """
        if self._stream_callback:
            self._stream_callback(content, metadata or {})