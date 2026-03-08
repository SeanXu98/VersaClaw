# -*- coding: utf-8 -*-
"""
应用配置模块

该模块定义了应用程序的所有配置项，包括：
- 服务器配置（主机、端口）
- 文件上传配置（目录、大小限制、允许类型）
- 流式处理配置（超时、心跳间隔）
- Provider 元数据（显示名称、关键词、文档链接）

使用方式:
    from app.config import settings, PROVIDER_METADATA

    # 获取上传目录
    upload_dir = settings.UPLOAD_DIR

    # 获取 Provider 信息
    provider_info = PROVIDER_METADATA["openai"]
"""
import os
from pathlib import Path
from typing import List


class Settings:
    """
    应用配置类

    所有配置项都作为类属性定义，支持通过环境变量覆盖默认值。

    属性:
        API_HOST: API 服务器监听地址
        API_PORT: API 服务器监听端口
        UPLOAD_DIR: 图片上传目录
        THUMBNAIL_DIR: 缩略图目录
        MAX_FILE_SIZE: 最大文件大小（字节）
        ALLOWED_IMAGE_TYPES: 允许的图片 MIME 类型列表
        STREAM_TIMEOUT: 流式请求超时时间（秒）
        HEARTBEAT_INTERVAL: 心跳间隔（秒）
        NANOBOT_CONFIG_PATH: Nanobot 配置文件路径
    """

    # ==================== 服务器配置 ====================
    API_HOST: str = os.getenv("NANOBOT_API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("NANOBOT_API_PORT", "18790"))

    # ==================== 文件上传配置 ====================
    UPLOAD_DIR: Path = Path.home() / ".nanobot" / "uploads" / "images"
    THUMBNAIL_DIR: Path = UPLOAD_DIR / "thumbnails"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_IMAGE_TYPES: List[str] = [
        "image/png",
        "image/jpeg",
        "image/gif",
        "image/webp"
    ]

    # ==================== 流式处理配置 ====================
    STREAM_TIMEOUT: float = 120.0
    HEARTBEAT_INTERVAL: float = 2.0

    # ==================== Nanobot 路径配置 ====================
    NANOBOT_CONFIG_PATH: Path = Path.home() / ".nanobot" / "config.json"

    @classmethod
    def ensure_upload_dirs(cls) -> None:
        """
        确保上传目录存在

        如果目录不存在，会自动创建上传目录和缩略图目录。
        """
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)


# ==================== Provider 元数据 ====================
# 定义各个 AI Provider 的显示信息、分类和文档链接
PROVIDER_METADATA = {
    # -------------------- 网关服务 --------------------
    "openrouter": {
        "display_name": "OpenRouter",
        "keywords": ["gateway", "multi-model"],
        "is_gateway": True,
        "is_local": False,
        "documentation_url": "https://openrouter.ai/docs"
    },
    "aihubmix": {
        "display_name": "AIHubMix",
        "keywords": ["gateway", "chinese"],
        "is_gateway": True,
        "is_local": False,
        "documentation_url": "https://aihubmix.com/docs"
    },
    "custom": {
        "display_name": "自定义网关",
        "keywords": ["gateway", "custom"],
        "is_gateway": True,
        "is_local": False
    },

    # -------------------- 国际服务商 --------------------
    "anthropic": {
        "display_name": "Anthropic (Claude)",
        "keywords": ["international", "claude"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://docs.anthropic.com"
    },
    "openai": {
        "display_name": "OpenAI",
        "keywords": ["international", "gpt"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://platform.openai.com/docs"
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "keywords": ["international", "reasoning"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://platform.deepseek.com/docs"
    },
    "groq": {
        "display_name": "Groq",
        "keywords": ["international", "fast"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://console.groq.com/docs"
    },
    "gemini": {
        "display_name": "Google Gemini",
        "keywords": ["international", "google"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://ai.google.dev/docs"
    },

    # -------------------- 国内服务商 --------------------
    "dashscope": {
        "display_name": "通义千问 (Qwen)",
        "keywords": ["chinese", "alibaba"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://help.aliyun.com/zh/dashscope/"
    },
    "moonshot": {
        "display_name": "Moonshot (Kimi)",
        "keywords": ["chinese", "kimi"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://platform.moonshot.cn/docs"
    },
    "zhipu": {
        "display_name": "智谱 (GLM)",
        "keywords": ["chinese", "glm"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://open.bigmodel.cn/dev/api"
    },
    "minimax": {
        "display_name": "MiniMax",
        "keywords": ["chinese"],
        "is_gateway": False,
        "is_local": False,
        "documentation_url": "https://www.minimaxi.com/document"
    },

    # -------------------- 本地部署 --------------------
    "vllm": {
        "display_name": "vLLM (本地)",
        "keywords": ["local", "self-hosted"],
        "is_gateway": False,
        "is_local": True,
        "documentation_url": "https://docs.vllm.ai/"
    }
}


# 全局配置实例
settings = Settings()
