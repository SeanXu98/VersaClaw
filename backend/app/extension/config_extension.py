# -*- coding: utf-8 -*-
"""
配置扩展模块

该模块扩展 Nanobot 的配置结构，添加以下能力：
- 支持独立的 imageModel 配置
- 支持模型 fallback 链
- 向后兼容旧配置

设计原则：
- 新字段有默认值，旧配置无需修改即可工作
- 配置结构清晰，易于理解和维护

使用方式:
    from app.extension.config_extension import get_extended_config

    config = get_extended_config()
    if config.agents.defaults.image_model:
        # 使用配置的视觉模型
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class ImageModelConfig(BaseModel):
    """
    视觉模型配置
    
    Attributes:
        primary: 首选视觉模型
        fallbacks: 备选模型列表（按优先级排序）
        auto_switch: 是否自动切换到视觉模型（当检测到图片时）
    """
    
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    primary: Optional[str] = None
    fallbacks: List[str] = Field(default_factory=list)
    auto_switch: bool = True


class ModelFallbackConfig(BaseModel):
    """
    模型降级配置
    
    Attributes:
        enabled: 是否启用降级
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
    """
    
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    enabled: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0


class ExtendedAgentDefaults(BaseModel):
    """
    扩展的 Agent 默认配置
    
    在 Nanobot 原有配置基础上增加：
    - image_model: 视觉模型配置
    - model_fallback: 模型降级配置
    
    向后兼容：新字段有默认值，旧配置无需修改
    """
    
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    # 原有字段（从 Nanobot 配置继承）
    workspace: str = "~/.nanobot/workspace"
    model: str = "anthropic/claude-opus-4-5"
    provider: str = "auto"
    max_tokens: int = 8192
    context_window_tokens: int = 65_536
    temperature: float = 0.1
    max_tool_iterations: int = 40
    
    # 新增字段：视觉模型配置
    image_model: Optional[ImageModelConfig] = None
    
    # 新增字段：模型降级配置
    model_fallback: ModelFallbackConfig = Field(default_factory=ModelFallbackConfig)
    
    @property
    def has_image_model_configured(self) -> bool:
        """检查是否配置了视觉模型"""
        return self.image_model is not None and self.image_model.primary is not None
    
    def get_image_model(self) -> Optional[str]:
        """获取首选视觉模型"""
        if self.image_model and self.image_model.primary:
            return self.image_model.primary
        return None
    
    def get_image_model_fallbacks(self) -> List[str]:
        """获取视觉模型降级链"""
        if self.image_model and self.image_model.fallbacks:
            return self.image_model.fallbacks
        return []


class ExtendedAgentsConfig(BaseModel):
    """扩展的 Agent 配置"""
    
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    defaults: ExtendedAgentDefaults = Field(default_factory=ExtendedAgentDefaults)


class ExtendedConfig(BaseModel):
    """
    扩展配置
    
    包含 Nanobot 原有配置和新增的扩展配置
    """
    
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    
    agents: ExtendedAgentsConfig = Field(default_factory=ExtendedAgentsConfig)
    
    # 原始 Nanobot 配置（用于兼容）
    _raw_config: Optional[Dict[str, Any]] = None
    
    @property
    def defaults(self) -> ExtendedAgentDefaults:
        """获取默认配置"""
        return self.agents.defaults
    
    @property
    def text_model(self) -> str:
        """获取文本模型"""
        return self.agents.defaults.model
    
    @property
    def image_model(self) -> Optional[str]:
        """获取视觉模型"""
        return self.agents.defaults.get_image_model()
    
    @property
    def image_model_fallbacks(self) -> List[str]:
        """获取视觉模型降级链"""
        return self.agents.defaults.get_image_model_fallbacks()


# 配置文件路径
DEFAULT_CONFIG_PATH = Path.home() / ".nanobot" / "config.json"


def get_extended_config(config_path: Optional[Path] = None) -> ExtendedConfig:
    """
    获取扩展配置
    
    从配置文件加载配置，并应用默认值。
    向后兼容：如果配置文件中没有新字段，使用默认值。
    
    Args:
        config_path: 配置文件路径，默认为 ~/.nanobot/config.json
    
    Returns:
        ExtendedConfig: 扩展配置对象
    """
    path = config_path or DEFAULT_CONFIG_PATH
    
    if not path.exists():
        return ExtendedConfig()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_config = json.load(f)
        
        # 解析配置
        config = ExtendedConfig.model_validate(raw_config)
        config._raw_config = raw_config
        
        return config
    
    except Exception as e:
        # 配置解析失败时返回默认配置
        import logging
        logging.warning(f"Failed to load extended config: {e}")
        return ExtendedConfig()


def update_config_with_image_model(
    config_path: Optional[Path] = None,
    image_model: Optional[str] = None,
    image_model_fallbacks: Optional[List[str]] = None,
) -> bool:
    """
    更新配置文件中的视觉模型设置
    
    Args:
        config_path: 配置文件路径
        image_model: 首选视觉模型
        image_model_fallbacks: 备选模型列表
    
    Returns:
        bool: 是否更新成功
    """
    path = config_path or DEFAULT_CONFIG_PATH
    
    try:
        # 读取现有配置
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {}
        
        # 确保 agents.defaults 存在
        if "agents" not in config:
            config["agents"] = {}
        if "defaults" not in config["agents"]:
            config["agents"]["defaults"] = {}
        
        # 更新视觉模型配置
        if image_model or image_model_fallbacks:
            if "imageModel" not in config["agents"]["defaults"]:
                config["agents"]["defaults"]["imageModel"] = {}
            
            if image_model:
                config["agents"]["defaults"]["imageModel"]["primary"] = image_model
            
            if image_model_fallbacks:
                config["agents"]["defaults"]["imageModel"]["fallbacks"] = image_model_fallbacks
        
        # 写回配置文件
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        return True
    
    except Exception as e:
        import logging
        logging.error(f"Failed to update config: {e}")
        return False
