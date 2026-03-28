# -*- coding: utf-8 -*-
"""
视觉 Agent 节点模块

该模块实现视觉理解 Agent 节点：
1. 处理包含图片的消息
2. 调用多模态模型进行分析
3. 返回视觉理解结果

这是 LangGraph 图中专门处理视觉任务的节点。
"""

from __future__ import annotations

import base64
import logging
import mimetypes
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from app.langgraph.nodes.base import BaseNode, NodeResult, StreamingNodeMixin
from app.langgraph.state import AgentState, Message

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider
    from app.extension.config_extension import ExtendedConfig

logger = logging.getLogger(__name__)


class VisionAgentNode(BaseNode, StreamingNodeMixin):
    """
    视觉 Agent 节点
    
    定位：**预处理节点**，而非独立 Agent。
    
    职责：
    1. 调用视觉模型理解图片内容
    2. 将图片理解结果作为系统消息注入到消息历史
    3. 由 MainAgent 决定后续操作（可能继续对话、调用工具等）
    
    设计原则：
    - 不产生 final_response（任务未完成）
    - 不直接结束流程
    - 作为 MainAgent 的"视觉感知"前置处理
    
    支持的视觉任务：
    - 图片内容描述
    - 图片文字提取 (OCR)
    - 图表、表格解析
    - 多图片比较
    - 视觉问答
    """
    
    # 视觉 Agent 系统提示词
    SYSTEM_PROMPT = """You are a specialized vision agent focused on image understanding and analysis.

## Core Capabilities

1. **Image Description**: Provide detailed descriptions of image content
2. **Text Extraction**: Extract and transcribe text from images (OCR)
3. **Chart & Table Parsing**: Analyze and interpret charts, graphs, and tables
4. **Visual Q&A**: Answer questions about image content
5. **Comparison**: Compare multiple images and identify differences

## Guidelines

- Be precise and detailed in your descriptions
- When extracting text, preserve the original formatting as much as possible
- For charts and tables, provide structured output when appropriate
- If you cannot clearly see or interpret something, state that uncertainty
- Focus on what is explicitly visible in the image, avoid speculation

## Output Format

- Use clear, structured responses
- For text extraction, use code blocks when appropriate
- For data analysis, use markdown tables when helpful
- Keep responses focused and relevant to the task
"""
    
    def __init__(
        self,
        name: str = "vision_agent",
        provider: Optional["LLMProvider"] = None,
        config: Optional["ExtendedConfig"] = None,
        on_progress: Optional[Callable] = None,
        upload_dir: Optional[str] = None,
    ):
        """
        初始化视觉 Agent 节点
        
        Args:
            name: 节点名称
            provider: LLM Provider 实例
            config: 扩展配置
            on_progress: 进度回调
            upload_dir: 图片上传目录
        """
        super().__init__(
            name=name,
            provider=provider,
            config=config,
        )
        self.extended_config = config
        self.on_progress = on_progress
        self.upload_dir = Path(upload_dir) if upload_dir else Path.home() / ".nanobot" / "uploads" / "images"
    
    async def execute(self, state: AgentState) -> NodeResult:
        """
        执行视觉理解处理
        
        设计原则：
        - 作为预处理节点，不产生最终答案
        - 将图片理解结果注入到消息历史
        - 由 MainAgent 决定后续操作
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            NodeResult: 处理结果
        """
        try:
            # 获取状态信息
            query = state.get("current_query", "")
            images = state.get("images", [])
            vision_analysis = state.get("vision_analysis", {})
            selected_model = state.get("selected_model", "")
            messages = state.get("messages", [])
            
            # 确定使用的模型
            model = self._determine_model(selected_model, vision_analysis)
            
            if not model:
                return NodeResult(
                    success=False,
                    error="No vision model configured. Please set up imageModel in config.",
                    state_update={
                        "final_response": "抱歉，当前未配置视觉模型，无法处理图片。",
                    },
                )
            
            # 发送进度通知
            if self.on_progress:
                await self.on_progress(f"正在使用 {model} 分析图片...")
            
            # 构建多模态消息
            vision_messages = await self._build_multimodal_messages(query, images)
            
            # 调用视觉模型
            self.log_info(f"Calling vision model: {model}")
            
            response = await self._call_vision_model(
                messages=vision_messages,
                model=model,
            )
            
            # 处理响应
            vision_result = response.get("content", "")
            
            # 核心变更：将图片理解结果作为系统消息注入到历史
            # 而不是设置 final_response
            messages = list(messages)  # 复制消息列表
            messages.append({
                "role": "system",
                "content": f"[图片理解结果]\n{vision_result}",
                "name": "vision_agent",
            })
            
            self.log_info(f"Vision analysis completed, injected result into message history")
            
            # 更新状态
            state_update = {
                "messages": messages,
                "selected_model": model,
                "model_type": "vision",
                # 注意：不设置 final_response，任务未完成
                # MainAgent 会根据消息历史决定后续操作
            }
            
            return NodeResult(
                success=True,
                state_update=state_update,
                # 不需要显式设置 next_node，图中有普通边 vision_agent -> main_agent
            )
            
        except Exception as e:
            self.log_error(f"Error in vision agent: {e}")
            return NodeResult(
                success=False,
                error=str(e),
                state_update={
                    "error": str(e),
                    "final_response": f"图片处理过程中发生错误: {str(e)}",
                },
            )
    
    def _determine_model(
        self,
        selected_model: str,
        vision_analysis: Dict[str, Any],
    ) -> str:
        """
        确定使用的视觉模型
        
        Args:
            selected_model: 已选择的模型
            vision_analysis: 视觉分析结果
        
        Returns:
            str: 模型名称
        """
        # 如果已经选择了模型，直接使用
        if selected_model:
            return selected_model
        
        # 从视觉分析结果获取推荐模型
        recommended = vision_analysis.get("recommended_model")
        if recommended:
            return recommended
        
        # 从配置获取
        if self.extended_config and self.extended_config.defaults.has_image_model_configured:
            return self.extended_config.image_model
        
        # 默认返回空
        return ""
    
    async def _build_multimodal_messages(
        self,
        query: str,
        images: List[Dict[str, Any]],
    ) -> List[Message]:
        """
        构建多模态消息列表
        
        Args:
            query: 用户查询
            images: 图片列表
        
        Returns:
            List[Message]: 消息列表
        """
        messages = []
        
        # 添加系统消息
        messages.append({
            "role": "system",
            "content": self.SYSTEM_PROMPT,
        })
        
        # 构建用户消息内容
        user_content = []
        
        # 添加图片
        for img in images:
            image_data = await self._process_image(img)
            if image_data:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": image_data},
                })
        
        # 添加文本
        user_content.append({
            "type": "text",
            "text": query,
        })
        
        messages.append({
            "role": "user",
            "content": user_content,
        })
        
        return messages
    
    async def _process_image(self, image_info: Dict[str, Any]) -> Optional[str]:
        """
        处理图片，返回可用的图片数据
        
        Args:
            image_info: 图片信息
        
        Returns:
            Optional[str]: 图片 URL 或 base64 数据 URL
        """
        # 如果已有 URL，直接返回
        url = image_info.get("url", "")
        if url and url.startswith(("http://", "https://", "data:")):
            return url
        
        # 如果有文件路径，读取并转换为 base64
        image_id = image_info.get("id", "")
        if image_id:
            # 尝试在 upload 目录查找
            for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ""]:
                potential_path = self.upload_dir / f"{image_id}{ext}"
                if potential_path.exists():
                    return await self._load_image_as_base64(potential_path)
        
        # 如果有缩略图 URL
        thumbnail_url = image_info.get("thumbnail_url", "")
        if thumbnail_url and thumbnail_url.startswith(("http://", "https://")):
            return thumbnail_url
        
        return None
    
    async def _load_image_as_base64(self, image_path: Path) -> Optional[str]:
        """
        加载图片并转换为 base64 数据 URL
        
        Args:
            image_path: 图片路径
        
        Returns:
            Optional[str]: base64 数据 URL
        """
        try:
            if not image_path.exists():
                self.log_error(f"Image not found: {image_path}")
                return None
            
            # 读取图片
            image_bytes = image_path.read_bytes()
            
            # 检测 MIME 类型
            mime_type = mimetypes.guess_type(str(image_path))[0]
            if not mime_type or not mime_type.startswith("image/"):
                # 从文件头检测
                mime_type = self._detect_mime_from_bytes(image_bytes)
            
            if not mime_type:
                mime_type = "image/png"
            
            # 转换为 base64
            b64_data = base64.b64encode(image_bytes).decode()
            
            return f"data:{mime_type};base64,{b64_data}"
            
        except Exception as e:
            self.log_error(f"Failed to load image: {e}")
            return None
    
    def _detect_mime_from_bytes(self, data: bytes) -> Optional[str]:
        """从字节头检测 MIME 类型"""
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif data[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif data[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        elif data[:4] == b'RIFF' and data[8:12] == b'WEBP':
            return "image/webp"
        return None
    
    async def _call_vision_model(
        self,
        messages: List[Message],
        model: str,
    ) -> Dict[str, Any]:
        """
        调用视觉模型
        
        Args:
            messages: 消息列表
            model: 模型名称
        
        Returns:
            Dict: 模型响应
        """
        if not self.provider:
            raise ValueError("LLM Provider not configured")
        
        # 使用 chat() 方法（LiteLLMProvider 的原生方法）
        response = await self.provider.chat(
            messages=messages,
            model=model,
        )
        
        return {
            "content": response.content if hasattr(response, "content") else "",
            "reasoning_content": getattr(response, "reasoning_content", None),
            "usage": response.usage if hasattr(response, "usage") else {},
        }