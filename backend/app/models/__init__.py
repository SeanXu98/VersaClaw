# -*- coding: utf-8 -*-
"""
Pydantic 数据模型包

该包定义了所有 API 请求和响应的数据模型。

包含的模型:
    - ImageData: 图片数据模型
    - ChatRequest: 聊天请求模型
    - ChatResponse: 聊天响应模型
    - UploadResponse: 文件上传响应模型
    - ProviderConfigRequest: Provider 配置请求模型

使用方式:
    from app.models import ChatRequest, ChatResponse
"""
from .schemas import (
    ImageData,
    ChatRequest,
    UploadResponse,
    ChatResponse,
    ProviderConfigRequest,
)

__all__ = [
    "ImageData",
    "ChatRequest",
    "UploadResponse",
    "ChatResponse",
    "ProviderConfigRequest",
]
