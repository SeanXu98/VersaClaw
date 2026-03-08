# -*- coding: utf-8 -*-
"""
API 路由处理包

该包定义了所有的 API 路由处理函数。

包含的路由:
    - chat: 聊天相关接口（/api/chat, /api/chat/stream）
    - sessions: 会话管理接口（/api/sessions）
    - images: 图片上传接口（/api/upload/image）
    - models: 模型和 Provider 管理接口（/api/models）
    - config: 配置管理接口（/api/config）

使用方式:
    from app.routers import chat_router, sessions_router
"""
# 导入路由（文件创建后可用）
try:
    from .chat import router as chat_router
except ImportError:
    chat_router = None

try:
    from .sessions import router as sessions_router
except ImportError:
    sessions_router = None

try:
    from .images import router as images_router
except ImportError:
    images_router = None

try:
    from .models import router as models_router
except ImportError:
    models_router = None

try:
    from .config import router as config_router
except ImportError:
    config_router = None

__all__ = [
    "chat_router",
    "sessions_router",
    "images_router",
    "models_router",
    "config_router",
]
