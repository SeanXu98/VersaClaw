# -*- coding: utf-8 -*-
"""
视觉路由节点模块

该模块实现智能视觉理解判断，根据用户消息内容：
1. 检测是否包含图片
2. 分析文本内容判断是否需要视觉理解
3. 选择合适的模型类型

这是 LangGraph 图的入口节点，决定后续路由方向。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from app.langgraph.nodes.base import BaseNode, NodeResult
from app.langgraph.state import AgentState, MessageType, VisionAnalysisResult

if TYPE_CHECKING:
    from app.extension.config_extension import ExtendedConfig

logger = logging.getLogger(__name__)


@dataclass
class VisionDetectionResult:
    """
    视觉检测结果
    
    Attributes:
        requires_vision: 是否需要视觉模型
        confidence: 置信度
        detected_type: 检测到的类型
        elements: 检测到的元素
        reason: 判断原因
    """
    requires_vision: bool = False
    confidence: float = 0.0
    detected_type: str = "text"
    elements: List[str] = None
    reason: str = ""
    
    def __post_init__(self):
        if self.elements is None:
            self.elements = []


class VisionRouter(BaseNode):
    """
    视觉路由节点
    
    负责分析用户输入，判断是否需要视觉理解能力。
    
    检测维度：
    1. 直接图片检测：消息中包含图片
    2. 文本意图分析：用户提到"看图"、"图片中"等关键词
    3. URL 检测：消息中包含图片 URL
    4. Base64 检测：消息中包含 base64 编码的图片数据
    
    路由决策：
    - 有图片 -> vision 路径
    - 无图片但文本暗示图片 -> 可能需要 vision
    - 纯文本 -> text 路径
    """
    
    # 视觉相关关键词（多语言）
    VISION_KEYWORDS = [
        # 中文
        "图片", "图像", "看图", "图中", "图片里", "图像里", "照片", "截图",
        "画", "图表", "表格", "示意图", "流程图", "架构图",
        "识别", "辨认", "ocr", "文字识别", "提取文字",
        "比较图片", "对比图片", "分析图片", "描述图片",
        # 英文
        "image", "picture", "photo", "screenshot", "diagram", "chart",
        "look at", "see the", "in the image", "in the picture",
        "recognize", "identify", "ocr", "extract text",
        "analyze image", "describe image", "compare images",
        # 通用
        "视觉", "vision", "multimodal",
    ]
    
    # 图片 URL 模式
    IMAGE_URL_PATTERNS = [
        r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|bmp)',
        r'https?://[^\s]*/image[s]?/[^\s]*',
        r'https?://[^\s]*\?.*?(?:format=|type=)(?:jpg|jpeg|png|gif|webp)',
    ]
    
    # Base64 图片模式
    BASE64_IMAGE_PATTERN = r'data:image/(?:png|jpeg|jpg|gif|webp);base64,[a-zA-Z0-9+/=]+'
    
    def __init__(
        self,
        name: str = "vision_router",
        config: Optional["ExtendedConfig"] = None,
        vision_check_fn: Optional[callable] = None,
    ):
        """
        初始化视觉路由器
        
        Args:
            name: 节点名称
            config: 扩展配置
            vision_check_fn: 自定义视觉模型检测函数
        """
        super().__init__(name=name, config=config)
        self.extended_config = config
        self.vision_check_fn = vision_check_fn
    
    async def execute(self, state: AgentState) -> NodeResult:
        """
        执行视觉路由判断
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            NodeResult: 包含路由决策的结果
        """
        query = state.get("current_query", "")
        images = state.get("images", [])
        selected_model = state.get("selected_model", "")
        
        # 1. 检测图片
        has_explicit_images = len(images) > 0
        
        # 2. 分析文本内容
        text_analysis = self._analyze_text(query)
        
        # 3. 检测图片 URL 或 base64
        has_image_urls = self._detect_image_urls(query)
        has_base64_images = self._detect_base64_images(query)
        
        # 4. 综合判断
        requires_vision = (
            has_explicit_images or 
            has_image_urls or 
            has_base64_images or 
            text_analysis.requires_vision
        )
        
        # 5. 确定消息类型
        if has_explicit_images or has_image_urls or has_base64_images:
            message_type = MessageType.MULTIMODAL
        elif text_analysis.requires_vision:
            message_type = MessageType.MULTIMODAL
        else:
            message_type = MessageType.TEXT
        
        # 6. 选择模型
        model_type = "vision" if requires_vision else "text"
        final_model = self._select_model(
            requires_vision=requires_vision,
            user_model=selected_model,
        )
        
        # 构建视觉分析结果
        vision_result = VisionAnalysisResult(
            requires_vision=requires_vision,
            confidence=text_analysis.confidence if not has_explicit_images else 1.0,
            detected_elements=text_analysis.elements + (
                ["explicit_images"] if has_explicit_images else []
            ),
            recommended_model=final_model if requires_vision else None,
            reason=self._build_reason(
                has_explicit_images, has_image_urls, has_base64_images, text_analysis
            ),
        )
        
        # 记录日志
        self.log_info(
            f"Vision routing: requires_vision={requires_vision}, "
            f"model_type={model_type}, model={final_model}"
        )
        
        return NodeResult(
            success=True,
            state_update={
                "message_type": message_type,
                "vision_analysis": vision_result.to_dict(),
                "selected_model": final_model,
                "model_type": model_type,
            },
            next_node="vision_agent" if requires_vision else "main_agent",
        )
    
    def _analyze_text(self, text: str) -> VisionDetectionResult:
        """
        分析文本内容判断是否暗示视觉需求
        
        Args:
            text: 用户输入文本
        
        Returns:
            VisionDetectionResult: 分析结果
        """
        if not text:
            return VisionDetectionResult()
        
        text_lower = text.lower()
        detected_elements = []
        confidence = 0.0
        
        # 检查关键词
        for keyword in self.VISION_KEYWORDS:
            if keyword.lower() in text_lower:
                detected_elements.append(keyword)
                confidence = max(confidence, 0.5)
        
        # 检查特定模式
        patterns = [
            (r'分析.*图', "analyze_image"),
            (r'描述.*图', "describe_image"),
            (r'识别.*文字', "ocr"),
            (r'提取.*文字', "ocr"),
            (r'比较.*图', "compare_images"),
        ]
        
        for pattern, element in patterns:
            if re.search(pattern, text):
                detected_elements.append(element)
                confidence = max(confidence, 0.7)
        
        # 判断是否需要视觉
        requires_vision = confidence > 0.3
        
        return VisionDetectionResult(
            requires_vision=requires_vision,
            confidence=confidence,
            detected_type="vision_hint" if requires_vision else "text",
            elements=detected_elements,
            reason=f"Detected {len(detected_elements)} vision-related elements" if detected_elements else "No vision hints detected",
        )
    
    def _detect_image_urls(self, text: str) -> bool:
        """检测文本中的图片 URL"""
        for pattern in self.IMAGE_URL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _detect_base64_images(self, text: str) -> bool:
        """检测文本中的 base64 图片数据"""
        return bool(re.search(self.BASE64_IMAGE_PATTERN, text))
    
    def _select_model(
        self,
        requires_vision: bool,
        user_model: Optional[str] = None,
    ) -> str:
        """
        选择模型
        
        Args:
            requires_vision: 是否需要视觉能力
            user_model: 用户指定的模型
        
        Returns:
            str: 选中的模型名称
        """
        # 用户指定模型优先
        if user_model:
            # 检查用户指定的模型是否满足需求
            if self.vision_check_fn and requires_vision:
                if self.vision_check_fn(user_model):
                    return user_model
                else:
                    self.log_info(
                        f"User specified model {user_model} does not support vision, "
                        f"will try to use configured vision model"
                    )
            else:
                return user_model
        
        # 根据需求选择模型
        if requires_vision and self.extended_config:
            if self.extended_config.defaults.has_image_model_configured:
                return self.extended_config.image_model
        
        # 返回默认模型
        if self.extended_config:
            return self.extended_config.text_model
        
        return ""
    
    def _build_reason(
        self,
        has_explicit_images: bool,
        has_image_urls: bool,
        has_base64_images: bool,
        text_analysis: VisionDetectionResult,
    ) -> str:
        """构建判断原因"""
        reasons = []
        
        if has_explicit_images:
            reasons.append("消息包含图片")
        if has_image_urls:
            reasons.append("检测到图片URL")
        if has_base64_images:
            reasons.append("检测到base64图片数据")
        if text_analysis.requires_vision:
            reasons.append(f"文本暗示视觉需求: {', '.join(text_analysis.elements[:3])}")
        
        if reasons:
            return "; ".join(reasons)
        return "纯文本对话，无需视觉能力"


def route_vision(state: AgentState) -> str:
    """
    LangGraph 条件路由函数
    
    根据 state 中的 vision_analysis 决定下一步路由。
    
    Args:
        state: 当前状态
    
    Returns:
        str: 下一个节点名称
    """
    vision_analysis = state.get("vision_analysis", {})
    requires_vision = vision_analysis.get("requires_vision", False)
    
    if requires_vision:
        return "vision_agent"
    return "main_agent"