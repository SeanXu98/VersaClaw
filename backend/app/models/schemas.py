# -*- coding: utf-8 -*-
"""
API 数据模型模块

该模块定义了所有 API 请求和响应的 Pydantic 数据模型。

包含的模型：
- ImageData: 图片数据模型（用于多模态消息）
- ChatRequest: 聊天请求模型
- ChatResponse: 聊天响应模型
- UploadResponse: 文件上传响应模型
- ProviderConfigRequest: Provider 配置请求模型

使用方式:
    from app.models.schemas import ChatRequest, ChatResponse
"""
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel


class ImageData(BaseModel):
    """
    图片数据模型

    用于多模态消息中传递图片信息。

    属性:
        id: 图片唯一标识符
        url: 图片访问 URL
        thumbnail_url: 缩略图 URL（可选）
        mime_type: MIME 类型，如 "image/png"
        size: 文件大小（字节，可选）
        filename: 原始文件名（可选）
        width: 图片宽度（像素，可选）
        height: 图片高度（像素，可选）
    """
    id: str
    url: str
    thumbnail_url: Optional[str] = None
    mime_type: str
    size: Optional[int] = None
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ChatRequest(BaseModel):
    """
    聊天请求模型

    支持纯文本和多模态（文本+图片）消息。

    属性:
        message: 用户消息内容
        session_key: 会话标识符，默认为 "web:direct"
        model: 指定使用的模型（可选，不指定则使用默认模型）
        images: 图片列表（可选，用于多模态消息）
    """
    message: str
    session_key: Optional[str] = "web:direct"
    model: Optional[str] = None
    images: Optional[List[ImageData]] = None


class UploadResponse(BaseModel):
    """
    文件上传响应模型

    属性:
        success: 是否上传成功
        data: 上传成功时的文件信息（可选）
        error: 上传失败时的错误信息（可选）
    """
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class ChatResponse(BaseModel):
    """
    聊天响应模型

    属性:
        success: 请求是否成功
        data: 成功时的响应数据（可选）
        error: 失败时的错误信息（可选）
    """
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class ProviderConfigRequest(BaseModel):
    """
    Provider 配置请求模型

    用于配置 AI 服务商的 API 密钥和相关参数。

    属性:
        api_key: API 密钥
        api_base: API 基础 URL（可选，用于自定义端点）
        models: 可用模型列表（可选）
        extra_headers: 额外的请求头（可选）
    """
    api_key: str
    api_base: Optional[str] = None
    models: Optional[List[str]] = None
    extra_headers: Optional[dict] = None


class ImageModelConfigRequest(BaseModel):
    """
    视觉模型配置请求模型

    用于配置视觉模型及其降级链。

    属性:
        primary: 首选视觉模型
        fallbacks: 备选模型列表（按优先级排序）
        auto_switch: 是否自动切换到视觉模型（当检测到图片时）
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    primary: Optional[str] = None
    fallbacks: Optional[List[str]] = None
    auto_switch: bool = True


class ModelConfigRequest(BaseModel):
    """
    模型配置请求模型

    用于配置主模型和视觉模型。

    属性:
        model: 主模型（文本对话默认使用）
        image_model: 视觉模型配置
    """
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    model: Optional[str] = None
    image_model: Optional[ImageModelConfigRequest] = None
