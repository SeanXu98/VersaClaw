# -*- coding: utf-8 -*-
"""
模型调度器模块

该模块提供智能模型选择能力，包括：
- 根据请求特征自动选择模型
- 支持主模型和视觉模型的独立配置
- 实现模型降级和容错机制
- 封装 Nanobot Provider，不修改源码

设计原则：
- ModelScheduler 内部持有 Nanobot Provider 实例
- 对外暴露与 Provider 一致的调用接口
- 内部实现模型选择逻辑，对调用方透明

使用方式:
    from app.extension.scheduler import ModelScheduler

    scheduler = ModelScheduler(provider, config)
    model = scheduler.select_model(features)
    response = await scheduler.chat_with_model(messages, model)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from app.extension.config_extension import ExtendedConfig, ExtendedAgentDefaults
from app.extension.feature_analyzer import RequestFeatures

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ModelSelectionResult:
    """
    模型选择结果
    
    Attributes:
        model: 选中的模型
        model_type: 模型类型（text / vision）
        fallback_used: 是否使用了降级模型
        original_model: 原始首选模型（如果使用了降级）
        reason: 选择原因
    """
    model: str
    model_type: str = "text"
    fallback_used: bool = False
    original_model: Optional[str] = None
    reason: str = ""


@dataclass
class ModelHealthStatus:
    """
    模型健康状态
    
    Attributes:
        model: 模型名称
        is_available: 是否可用
        last_check_time: 上次检查时间
        error_count: 错误计数
        last_error: 上次错误信息
    """
    model: str
    is_available: bool = True
    last_check_time: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None


class ModelScheduler:
    """
    模型调度器
    
    封装 Nanobot Provider，实现智能模型选择。
    
    核心能力：
    1. 模型配置管理：主模型、视觉模型、fallback 链
    2. 请求特征分析：检测图片、分析任务类型
    3. 智能调度策略：根据特征选择最优模型
    4. 降级容错机制：模型不可用时自动切换
    
    使用方式:
        scheduler = ModelScheduler(provider, config)
        
        # 根据特征选择模型
        result = scheduler.select_model(features)
        
        # 使用选中的模型调用 Provider
        response = await scheduler.chat_with_retry(messages, model=result.model)
    """
    
    # 视觉模型关键词（用于自动检测）
    VISION_MODEL_PATTERNS = [
        "gpt-4-vision", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
        "claude-3", "claude-3.5",
        "gemini-1.5", "gemini-2",
        "openrouter/",
        "glm-4v", "glm-4.6v", "glm-4.1v",
        "qwen-vl", "deepseek-vl", "llava",
        "vision",
    ]
    
    def __init__(
        self,
        provider: Any,
        config: Optional[ExtendedConfig] = None,
        vision_check_fn: Optional[Callable[[str], bool]] = None,
    ):
        """
        初始化模型调度器
        
        Args:
            provider: Nanobot Provider 实例
            config: 扩展配置对象
            vision_check_fn: 自定义视觉模型检测函数
        """
        self.provider = provider
        self.config = config or ExtendedConfig()
        self.vision_check_fn = vision_check_fn or self._default_vision_check
        
        # 模型健康状态缓存
        self._health_cache: Dict[str, ModelHealthStatus] = {}
        
        # 错误计数阈值（超过此阈值标记模型不可用）
        self._error_threshold = 3
        
        # 错误恢复时间（秒）
        self._recovery_time = 300.0  # 5分钟
    
    def _default_vision_check(self, model: str) -> bool:
        """默认的视觉模型检测"""
        if not model:
            return False
        model_lower = model.lower()
        return any(pattern in model_lower for pattern in self.VISION_MODEL_PATTERNS)
    
    def is_vision_model(self, model: str) -> bool:
        """
        检测模型是否支持视觉能力
        
        Args:
            model: 模型名称
        
        Returns:
            bool: 是否支持视觉能力
        """
        return self.vision_check_fn(model)
    
    def select_model(
        self,
        features: RequestFeatures,
        preferred_model: Optional[str] = None,
    ) -> ModelSelectionResult:
        """
        根据请求特征选择模型
        
        Args:
            features: 请求特征
            preferred_model: 用户指定的模型（优先级最高）
        
        Returns:
            ModelSelectionResult: 模型选择结果
        """
        # 1. 用户指定模型优先
        if preferred_model:
            return ModelSelectionResult(
                model=preferred_model,
                model_type="vision" if self.is_vision_model(preferred_model) else "text",
                reason="用户指定模型",
            )
        
        # 2. 检查是否需要视觉模型
        if features.requires_vision:
            return self._select_vision_model(features)
        
        # 3. 纯文本请求，使用主模型
        return self._select_text_model(features)
    
    def _select_text_model(self, features: RequestFeatures) -> ModelSelectionResult:
        """选择文本模型"""
        primary_model = self.config.text_model
        
        # 检查模型健康状态
        if self._is_model_available(primary_model):
            return ModelSelectionResult(
                model=primary_model,
                model_type="text",
                reason="主模型可用",
            )
        
        # 主模型不可用，尝试降级
        logger.warning(f"主模型 {primary_model} 不可用，尝试降级")
        return ModelSelectionResult(
            model=primary_model,  # 仍然返回主模型，由调用方处理错误
            model_type="text",
            fallback_used=True,
            reason="主模型暂时不可用",
        )
    
    def _select_vision_model(self, features: RequestFeatures) -> ModelSelectionResult:
        """选择视觉模型"""
        defaults = self.config.defaults
        
        # 检查是否配置了独立的视觉模型
        if defaults.has_image_model_configured:
            primary_vision = defaults.get_image_model()
            
            if self._is_model_available(primary_vision):
                return ModelSelectionResult(
                    model=primary_vision,
                    model_type="vision",
                    reason="配置的视觉模型可用",
                )
            
            # 尝试 fallback 链
            for fallback in defaults.get_image_model_fallbacks():
                if self._is_model_available(fallback):
                    return ModelSelectionResult(
                        model=fallback,
                        model_type="vision",
                        fallback_used=True,
                        original_model=primary_vision,
                        reason=f"视觉模型降级到 {fallback}",
                    )
        
        # 没有配置独立视觉模型，检查主模型是否支持视觉
        primary_model = self.config.text_model
        if self.is_vision_model(primary_model):
            if self._is_model_available(primary_model):
                return ModelSelectionResult(
                    model=primary_model,
                    model_type="vision",
                    reason="主模型支持视觉能力",
                )
        
        # 主模型不支持视觉，需要用户配置视觉模型
        logger.warning("当前模型不支持视觉能力，请配置 imageModel")
        return ModelSelectionResult(
            model=primary_model,
            model_type="text",  # 标记为文本模型，调用方应提示用户
            reason="当前模型不支持视觉能力",
        )
    
    def _is_model_available(self, model: str) -> bool:
        """
        检查模型是否可用
        
        Args:
            model: 模型名称
        
        Returns:
            bool: 是否可用
        """
        import time
        
        status = self._health_cache.get(model)
        if status is None:
            return True  # 默认可用
        
        # 检查是否已过恢复时间
        if not status.is_available:
            elapsed = time.time() - status.last_check_time
            if elapsed > self._recovery_time:
                # 恢复模型可用性
                status.is_available = True
                status.error_count = 0
                return True
        
        return status.is_available
    
    def record_success(self, model: str) -> None:
        """
        记录模型调用成功
        
        Args:
            model: 模型名称
        """
        import time
        
        if model in self._health_cache:
            self._health_cache[model].is_available = True
            self._health_cache[model].error_count = 0
            self._health_cache[model].last_check_time = time.time()
    
    def record_error(self, model: str, error: str) -> None:
        """
        记录模型调用错误
        
        Args:
            model: 模型名称
            error: 错误信息
        """
        import time
        
        if model not in self._health_cache:
            self._health_cache[model] = ModelHealthStatus(model=model)
        
        status = self._health_cache[model]
        status.error_count += 1
        status.last_error = error
        status.last_check_time = time.time()
        
        # 超过阈值标记为不可用
        if status.error_count >= self._error_threshold:
            status.is_available = False
            logger.warning(f"模型 {model} 错误次数超过阈值，标记为不可用")
    
    def get_fallback_chain(self, model_type: str = "text") -> List[str]:
        """
        获取模型降级链
        
        Args:
            model_type: 模型类型（text / vision）
        
        Returns:
            List[str]: 降级链模型列表
        """
        if model_type == "vision":
            chain = []
            if self.config.defaults.has_image_model_configured:
                chain.append(self.config.defaults.get_image_model())
                chain.extend(self.config.defaults.get_image_model_fallbacks())
            return chain
        
        # 文本模型降级链
        return [self.config.text_model]
    
    # ==================== Provider 接口封装 ====================
    
    async def chat_with_retry(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        **kwargs,
    ) -> Any:
        """
        调用 Provider 的 chat_with_retry 方法
        
        封装 Provider 调用，自动记录成功/失败状态。
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            model: 模型名称
            **kwargs: 其他参数
        
        Returns:
            LLMResponse: LLM 响应
        """
        try:
            response = await self.provider.chat_with_retry(
                messages=messages,
                tools=tools,
                model=model,
                **kwargs,
            )
            
            # 记录成功
            if model:
                self.record_success(model)
            
            return response
        
        except Exception as e:
            # 记录错误
            if model:
                self.record_error(model, str(e))
            raise
    
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        **kwargs,
    ) -> Any:
        """
        调用 Provider 的 chat 方法
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            model: 模型名称
            **kwargs: 其他参数
        
        Returns:
            LLMResponse: LLM 响应
        """
        return await self.provider.chat(
            messages=messages,
            tools=tools,
            model=model,
            **kwargs,
        )
    
    def get_default_model(self) -> str:
        """获取默认模型"""
        return self.provider.get_default_model()
    
    @property
    def generation(self) -> Any:
        """获取生成设置"""
        return self.provider.generation
    
    # ==================== 便捷方法 ====================
    
    def get_model_for_request(
        self,
        content: str | list | None,
        media_files: Optional[List[str]] = None,
        preferred_model: Optional[str] = None,
    ) -> ModelSelectionResult:
        """
        根据请求内容获取合适的模型
        
        便捷方法，自动分析请求特征并选择模型。
        
        Args:
            content: 消息内容
            media_files: 媒体文件列表
            preferred_model: 用户指定的模型
        
        Returns:
            ModelSelectionResult: 模型选择结果
        """
        from app.extension.feature_analyzer import RequestFeatureAnalyzer
        
        analyzer = RequestFeatureAnalyzer()
        features = analyzer.analyze(content, media_files)
        
        return self.select_model(features, preferred_model)
