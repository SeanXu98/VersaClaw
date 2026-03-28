# -*- coding: utf-8 -*-
"""
Vision Agent 管理器模块

该模块提供 Vision Agent 的创建和调用能力，包括：
- 通过 Nanobot SubagentManager 创建 Vision Agent
- 执行图片分析任务
- 返回分析结果给主 Agent

设计原则：
- 复用 Nanobot 的 SubagentManager，不修改源码
- 提供清晰的接口，对调用方透明
- 支持异步执行和结果回调

使用方式:
    from app.extension.vision_agent_manager import VisionAgentManager

    manager = VisionAgentManager(subagent_manager, config)
    result = await manager.analyze(image_paths, query)
"""

import asyncio
import base64
import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from app.extension.vision_agent import (
    VisionAgentConfig,
    VisionAnalysisRequest,
    VisionAnalysisResult,
    get_vision_model_capability,
)
from app.extension.config_extension import ExtendedConfig

# 配置日志
logger = logging.getLogger(__name__)


class VisionAgentManager:
    """
    Vision Agent 管理器
    
    管理 Vision Agent 的创建和执行，提供图片理解能力。
    
    核心能力：
    1. 创建专用的 Vision Agent 实例
    2. 执行图片分析任务
    3. 支持多图片处理
    4. 返回结构化结果
    
    使用方式:
        manager = VisionAgentManager(
            subagent_manager=subagent_manager,
            provider=provider,
            config=vision_config,
        )
        result = await manager.analyze(image_paths, "描述这些图片")
    """
    
    def __init__(
        self,
        subagent_manager: Any,
        provider: Any,
        config: Optional[VisionAgentConfig] = None,
        extended_config: Optional[ExtendedConfig] = None,
    ):
        """
        初始化 Vision Agent 管理器
        
        Args:
            subagent_manager: Nanobot SubagentManager 实例
            provider: LLM Provider 实例
            config: Vision Agent 配置
            extended_config: 扩展配置（用于获取视觉模型）
        """
        self.subagent_manager = subagent_manager
        self.provider = provider
        self.config = config or VisionAgentConfig()
        self.extended_config = extended_config
        
        # 获取视觉模型
        self._vision_model = self._determine_vision_model()
        
        logger.info(f"[VisionAgentManager] 初始化完成，视觉模型: {self._vision_model}")
    
    def _determine_vision_model(self) -> str:
        """确定使用的视觉模型"""
        # 优先使用配置的模型
        if self.config.default_model:
            return self.config.default_model
        
        # 使用扩展配置中的视觉模型
        if self.extended_config and self.extended_config.defaults.has_image_model_configured:
            return self.extended_config.image_model
        
        # 使用 SubagentManager 的默认模型
        if hasattr(self.subagent_manager, 'model') and self.subagent_manager.model:
            return self.subagent_manager.model
        
        # 最终默认
        return "gpt-4o"
    
    async def analyze(
        self,
        image_paths: List[str],
        query: str,
        context: Optional[str] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> VisionAnalysisResult:
        """
        分析图片
        
        Args:
            image_paths: 图片路径列表
            query: 查询/任务描述
            context: 额外上下文信息
            on_progress: 进度回调
        
        Returns:
            VisionAnalysisResult: 分析结果
        """
        try:
            # 检查图片数量限制
            capability = get_vision_model_capability(self._vision_model)
            max_images = capability.get("max_images", 5)
            
            if len(image_paths) > max_images:
                logger.warning(
                    f"[VisionAgentManager] 图片数量 {len(image_paths)} 超过限制 {max_images}，"
                    f"将只处理前 {max_images} 张"
                )
                image_paths = image_paths[:max_images]
            
            # 构建消息
            messages = await self._build_messages(image_paths, query, context)
            
            # 调用 LLM
            if on_progress:
                on_progress(f"正在使用 {self._vision_model} 分析图片...")
            
            # 使用 chat() 方法（LiteLLMProvider 的原生方法）
            response = await self.provider.chat(
                messages=messages,
                model=self._vision_model,
            )
            
            # 处理响应
            content = response.content if response else None
            
            if content:
                return VisionAnalysisResult(
                    success=True,
                    content=content,
                    model_used=self._vision_model,
                    tokens_used=response.usage.get("total_tokens", 0) if response.usage else 0,
                )
            else:
                return VisionAnalysisResult(
                    success=False,
                    error="模型未返回有效内容",
                    model_used=self._vision_model,
                )
        
        except Exception as e:
            logger.error(f"[VisionAgentManager] 图片分析失败: {e}")
            return VisionAnalysisResult(
                success=False,
                error=str(e),
                model_used=self._vision_model,
            )
    
    async def analyze_single(
        self,
        image_path: str,
        query: str,
        context: Optional[str] = None,
    ) -> VisionAnalysisResult:
        """
        分析单张图片
        
        Args:
            image_path: 图片路径
            query: 查询/任务描述
            context: 额外上下文信息
        
        Returns:
            VisionAnalysisResult: 分析结果
        """
        return await self.analyze([image_path], query, context)
    
    async def extract_text(self, image_path: str) -> VisionAnalysisResult:
        """
        提取图片中的文字（OCR）
        
        Args:
            image_path: 图片路径
        
        Returns:
            VisionAnalysisResult: 提取结果
        """
        return await self.analyze(
            [image_path],
            "请提取图片中的所有文字内容，保持原始格式和布局。",
        )
    
    async def describe(self, image_path: str, detail_level: str = "medium") -> VisionAnalysisResult:
        """
        描述图片内容
        
        Args:
            image_path: 图片路径
            detail_level: 详细程度 (brief/medium/detailed)
        
        Returns:
            VisionAnalysisResult: 描述结果
        """
        detail_prompts = {
            "brief": "请用一两句话简要描述这张图片的主要内容。",
            "medium": "请详细描述这张图片的内容，包括主要元素、场景和细节。",
            "detailed": "请非常详细地描述这张图片的所有内容，包括：\n1. 整体场景描述\n2. 主要元素和对象\n3. 人物（如果有）的外观、动作和表情\n4. 文字内容（如果有）\n5. 颜色、光线和构图\n6. 图片传达的氛围或情感",
        }
        
        query = detail_prompts.get(detail_level, detail_prompts["medium"])
        return await self.analyze([image_path], query)
    
    async def analyze_chart(self, image_path: str) -> VisionAnalysisResult:
        """
        分析图表
        
        Args:
            image_path: 图表图片路径
        
        Returns:
            VisionAnalysisResult: 分析结果
        """
        return await self.analyze(
            [image_path],
            "请分析这个图表，包括：\n1. 图表类型\n2. 数据趋势\n3. 关键数据点\n4. 结论或洞察",
        )
    
    async def compare_images(
        self,
        image_paths: List[str],
        query: Optional[str] = None,
    ) -> VisionAnalysisResult:
        """
        比较多张图片
        
        Args:
            image_paths: 图片路径列表
            query: 自定义比较问题
        
        Returns:
            VisionAnalysisResult: 比较结果
        """
        default_query = "请比较这些图片，找出它们的相同点和不同点。"
        return await self.analyze(image_paths, query or default_query)
    
    async def _build_messages(
        self,
        image_paths: List[str],
        query: str,
        context: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        构建多模态消息
        
        Args:
            image_paths: 图片路径列表
            query: 查询内容
            context: 上下文信息
        
        Returns:
            List[Dict]: 消息列表
        """
        # 系统消息
        messages = [
            {
                "role": "system",
                "content": self.config.system_prompt,
            }
        ]
        
        # 构建用户消息（多模态）
        user_content = []
        
        # 添加图片
        for image_path in image_paths:
            image_data = await self._load_image(image_path)
            if image_data:
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_data,
                    },
                })
        
        # 添加文本内容
        text_parts = []
        if context:
            text_parts.append(f"上下文：{context}")
        text_parts.append(query)
        
        user_content.append({
            "type": "text",
            "text": "\n\n".join(text_parts),
        })
        
        messages.append({
            "role": "user",
            "content": user_content,
        })
        
        return messages
    
    async def _load_image(self, image_path: str) -> Optional[str]:
        """
        加载图片并转换为 base64 数据 URL
        
        Args:
            image_path: 图片路径
        
        Returns:
            Optional[str]: base64 数据 URL，失败返回 None
        """
        try:
            path = Path(image_path)
            if not path.exists():
                logger.warning(f"[VisionAgentManager] 图片不存在: {image_path}")
                return None
            
            # 读取图片
            image_bytes = path.read_bytes()
            
            # 检测 MIME 类型
            import mimetypes
            mime_type = mimetypes.guess_type(image_path)[0]
            if not mime_type or not mime_type.startswith("image/"):
                # 尝试从文件头检测
                mime_type = self._detect_mime_from_bytes(image_bytes)
            
            if not mime_type:
                mime_type = "image/png"  # 默认
            
            # 转换为 base64
            b64_data = base64.b64encode(image_bytes).decode()
            
            return f"data:{mime_type};base64,{b64_data}"
        
        except Exception as e:
            logger.error(f"[VisionAgentManager] 加载图片失败 {image_path}: {e}")
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
    
    # ==================== 通过 SubagentManager 执行 ====================
    
    async def spawn_as_subagent(
        self,
        task: str,
        image_paths: List[str],
        origin_channel: str = "web",
        origin_chat_id: str = "direct",
        session_key: Optional[str] = None,
    ) -> str:
        """
        作为子代理执行任务
        
        通过 Nanobot 的 SubagentManager 创建子代理执行图片分析任务。
        
        Args:
            task: 任务描述
            image_paths: 图片路径列表
            origin_channel: 来源渠道
            origin_chat_id: 来源聊天 ID
            session_key: 会话标识
        
        Returns:
            str: 子代理启动信息
        """
        # 构建完整的任务描述
        full_task = f"""{task}

图片路径：
{chr(10).join(f'- {p}' for p in image_paths)}

请使用文件工具读取图片，然后进行分析。"""
        
        # 通过 SubagentManager 创建子代理
        return await self.subagent_manager.spawn(
            task=full_task,
            label="Vision Analysis",
            origin_channel=origin_channel,
            origin_chat_id=origin_chat_id,
            session_key=session_key,
        )
