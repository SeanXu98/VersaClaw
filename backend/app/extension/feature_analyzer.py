# -*- coding: utf-8 -*-
"""
请求特征分析模块

该模块负责分析请求内容的特征，包括：
- 检测消息是否包含图片
- 统计图片数量和大小
- 分析任务类型
- 判断是否需要视觉模型

使用方式:
    from app.extension.feature_analyzer import RequestFeatureAnalyzer

    analyzer = RequestFeatureAnalyzer()
    features = analyzer.analyze(message_content, media_files)
    if features.has_images:
        # 使用视觉模型
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from pathlib import Path


@dataclass
class RequestFeatures:
    """
    请求特征数据结构
    
    Attributes:
        has_images: 是否包含图片
        image_count: 图片数量
        image_sizes: 图片大小列表（字节）
        total_image_size: 图片总大小（字节）
        text_length: 文本长度
        has_code_blocks: 是否包含代码块
        has_math: 是否包含数学公式
        task_type: 任务类型（conversation, code, analysis, etc.）
        complexity_score: 复杂度评分（0-10）
        requires_vision: 是否需要视觉模型
    """
    has_images: bool = False
    image_count: int = 0
    image_sizes: List[int] = field(default_factory=list)
    total_image_size: int = 0
    text_length: int = 0
    has_code_blocks: bool = False
    has_math: bool = False
    task_type: str = "conversation"
    complexity_score: int = 0
    
    @property
    def requires_vision(self) -> bool:
        """判断是否需要视觉模型"""
        return self.has_images
    
    @property
    def has_large_images(self) -> bool:
        """判断是否包含大图片（>1MB）"""
        return any(size > 1024 * 1024 for size in self.image_sizes)
    
    @property
    def summary(self) -> str:
        """返回特征摘要"""
        parts = []
        if self.has_images:
            parts.append(f"{self.image_count}张图片")
        if self.has_code_blocks:
            parts.append("含代码")
        if self.has_math:
            parts.append("含数学公式")
        return ", ".join(parts) if parts else "纯文本对话"


class RequestFeatureAnalyzer:
    """
    请求特征分析器
    
    分析消息内容的特征，用于智能模型选择。
    
    使用方式:
        analyzer = RequestFeatureAnalyzer()
        features = analyzer.analyze(content, media_files)
    """
    
    # 代码块标记
    CODE_BLOCK_MARKERS = ["```", "    ", "\tdef ", "\tclass ", "def ", "class ", "function ", "import "]
    
    # 数学公式标记
    MATH_MARKERS = ["$$", "\\[", "\\(", "\\begin{equation}", "\\frac", "\\sum", "\\int"]
    
    def __init__(self, upload_dir: Optional[Path] = None):
        """
        初始化分析器
        
        Args:
            upload_dir: 图片上传目录路径，用于计算图片大小
        """
        self.upload_dir = upload_dir or Path.home() / ".nanobot" / "uploads" / "images"
    
    def analyze(
        self,
        content: str | list | None,
        media_files: Optional[List[str]] = None,
    ) -> RequestFeatures:
        """
        分析请求内容特征
        
        Args:
            content: 消息内容（字符串或多模态内容列表）
            media_files: 媒体文件路径列表
        
        Returns:
            RequestFeatures: 请求特征对象
        """
        features = RequestFeatures()
        
        # 分析内容
        if content is None:
            return features
        
        if isinstance(content, str):
            self._analyze_text(content, features)
        elif isinstance(content, list):
            self._analyze_multimodal(content, features)
        
        # 分析媒体文件
        if media_files:
            self._analyze_media_files(media_files, features)
        
        # 计算复杂度评分
        features.complexity_score = self._calculate_complexity(features)
        
        # 推断任务类型
        features.task_type = self._infer_task_type(content, features)
        
        return features
    
    def _analyze_text(self, text: str, features: RequestFeatures) -> None:
        """分析纯文本内容"""
        features.text_length = len(text)
        
        # 检测代码块
        features.has_code_blocks = any(marker in text for marker in self.CODE_BLOCK_MARKERS)
        
        # 检测数学公式
        features.has_math = any(marker in text for marker in self.MATH_MARKERS)
    
    def _analyze_multimodal(self, content: list, features: RequestFeatures) -> None:
        """分析多模态内容"""
        text_parts = []
        
        for block in content:
            if not isinstance(block, dict):
                continue
            
            block_type = block.get("type")
            
            if block_type == "text":
                text = block.get("text", "")
                text_parts.append(text)
            
            elif block_type == "image_url":
                features.has_images = True
                features.image_count += 1
                
                # 尝试获取图片大小
                image_url = block.get("image_url", {}).get("url", "")
                size = self._estimate_image_size(image_url)
                features.image_sizes.append(size)
                features.total_image_size += size
        
        # 合并文本内容进行分析
        combined_text = " ".join(text_parts)
        self._analyze_text(combined_text, features)
    
    def _analyze_media_files(self, media_files: List[str], features: RequestFeatures) -> None:
        """分析媒体文件"""
        for file_path in media_files:
            try:
                path = Path(file_path)
                if path.exists():
                    features.has_images = True
                    features.image_count += 1
                    size = path.stat().st_size
                    features.image_sizes.append(size)
                    features.total_image_size += size
            except Exception:
                pass
    
    def _estimate_image_size(self, image_url: str) -> int:
        """
        估算图片大小
        
        Args:
            image_url: 图片 URL（可能是 base64 数据 URL）
        
        Returns:
            int: 估算的图片大小（字节）
        """
        if image_url.startswith("data:image/"):
            # base64 编码的图片
            try:
                # 提取 base64 数据部分
                _, data = image_url.split(",", 1)
                # base64 编码后的大小约为原始数据的 4/3
                return int(len(data) * 3 / 4)
            except Exception:
                return 0
        return 0
    
    def _calculate_complexity(self, features: RequestFeatures) -> int:
        """
        计算请求复杂度评分
        
        评分标准：
        - 图片：每张 +1，最多 +3
        - 代码块：+2
        - 数学公式：+1
        - 长文本（>2000字符）：+1
        - 大图片（>1MB）：+1
        
        Returns:
            int: 复杂度评分（0-10）
        """
        score = 0
        
        # 图片评分
        score += min(features.image_count, 3)
        
        # 代码块评分
        if features.has_code_blocks:
            score += 2
        
        # 数学公式评分
        if features.has_math:
            score += 1
        
        # 长文本评分
        if features.text_length > 2000:
            score += 1
        
        # 大图片评分
        if features.has_large_images:
            score += 1
        
        return min(score, 10)
    
    def _infer_task_type(self, content: Any, features: RequestFeatures) -> str:
        """
        推断任务类型
        
        Args:
            content: 原始内容
            features: 已分析的特征
        
        Returns:
            str: 任务类型
        """
        if features.has_images:
            return "vision"
        
        if features.has_code_blocks:
            return "code"
        
        if features.has_math:
            return "math"
        
        # 检查文本中的关键词
        text = ""
        if isinstance(content, str):
            text = content.lower()
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "").lower()
        
        # 分析关键词
        analysis_keywords = ["分析", "analyze", "比较", "compare", "总结", "summarize"]
        if any(kw in text for kw in analysis_keywords):
            return "analysis"
        
        return "conversation"
