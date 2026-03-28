# -*- coding: utf-8 -*-
"""
Agent Team 类型定义模块

该模块定义 Agent Team 相关的所有类型：
- SubagentType: 子代理类型枚举
- SubagentConfig: 子代理配置
- TeamConfig: 团队配置
- TaskResult: 任务结果
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SubagentType(str, Enum):
    """
    子代理类型枚举
    
    定义可用的子代理类型，每种类型有不同的专长和工具集。
    """
    
    # 通用型
    GENERAL = "general"            # 通用助手
    
    # 专业型
    CODER = "coder"                # 代码编写
    RESEARCHER = "researcher"      # 研究分析
    WRITER = "writer"              # 内容创作
    REVIEWER = "reviewer"          # 审核校对
    TESTER = "tester"              # 测试验证
    
    # 领域型
    DATA_ANALYST = "data_analyst"  # 数据分析
    TRANSLATOR = "translator"      # 翻译
    SUMMARIZER = "summarizer"      # 摘要总结
    EXPLAINER = "explainer"        # 解释说明
    
    # 特殊型
    VISION = "vision"              # 视觉理解
    COORDINATOR = "coordinator"    # 协调器


@dataclass
class SubagentConfig:
    """
    子代理配置
    
    定义子代理的配置参数，包括名称、角色、模型等。
    
    Attributes:
        id: 子代理 ID
        name: 子代理名称
        type: 子代理类型
        role_description: 角色描述
        system_prompt: 系统提示词
        model: 使用的模型
        tools: 可用工具列表
        max_iterations: 最大迭代次数
        temperature: 温度参数
        priority: 优先级（用于执行顺序）
    """
    
    id: str
    name: str
    type: SubagentType
    role_description: str = ""
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    tools: List[str] = field(default_factory=list)
    max_iterations: int = 10
    temperature: float = 0.1
    priority: int = 0
    
    def __post_init__(self):
        """初始化后处理"""
        # 如果没有提供系统提示词，使用默认的
        if self.system_prompt is None:
            self.system_prompt = self._get_default_system_prompt()
        
        # 如果没有提供角色描述，使用默认的
        if not self.role_description:
            self.role_description = self._get_default_role_description()
    
    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        prompts = {
            SubagentType.CODER: """You are an expert coder specialized in writing high-quality code.
Your task is to write clean, efficient, and well-documented code.
Follow best practices and coding standards.""",
            
            SubagentType.RESEARCHER: """You are a research analyst specialized in gathering and analyzing information.
Your task is to research topics thoroughly and provide accurate, well-sourced information.""",
            
            SubagentType.WRITER: """You are a professional writer specialized in creating engaging content.
Your task is to write clear, compelling, and well-structured content.""",
            
            SubagentType.REVIEWER: """You are a meticulous reviewer specialized in quality assurance.
Your task is to review work for errors, inconsistencies, and areas of improvement.""",
            
            SubagentType.TESTER: """You are a QA engineer specialized in testing and validation.
Your task is to create comprehensive test cases and verify functionality.""",
            
            SubagentType.DATA_ANALYST: """You are a data analyst specialized in data processing and insights.
Your task is to analyze data and provide meaningful insights.""",
            
            SubagentType.TRANSLATOR: """You are a professional translator specialized in accurate translation.
Your task is to translate text while preserving meaning and tone.""",
            
            SubagentType.SUMMARIZER: """You are a summarization expert specialized in distilling key information.
Your task is to create concise, accurate summaries of content.""",
            
            SubagentType.EXPLAINER: """You are an educator specialized in making complex topics accessible.
Your task is to explain concepts clearly and provide helpful examples.""",
            
            SubagentType.VISION: """You are a vision expert specialized in image understanding.
Your task is to analyze images and provide detailed descriptions.""",
            
            SubagentType.COORDINATOR: """You are a team coordinator specialized in orchestrating work.
Your task is to coordinate subagent activities and aggregate results.""",
            
            SubagentType.GENERAL: """You are a helpful assistant ready to assist with various tasks.
Provide accurate and helpful responses to the user's requests.""",
        }
        return prompts.get(self.type, prompts[SubagentType.GENERAL])
    
    def _get_default_role_description(self) -> str:
        """获取默认角色描述"""
        descriptions = {
            SubagentType.CODER: "代码编写专家",
            SubagentType.RESEARCHER: "研究分析专家",
            SubagentType.WRITER: "内容创作专家",
            SubagentType.REVIEWER: "审核校对专家",
            SubagentType.TESTER: "测试验证专家",
            SubagentType.DATA_ANALYST: "数据分析专家",
            SubagentType.TRANSLATOR: "翻译专家",
            SubagentType.SUMMARIZER: "摘要总结专家",
            SubagentType.EXPLAINER: "解释说明专家",
            SubagentType.VISION: "视觉理解专家",
            SubagentType.COORDINATOR: "团队协调专家",
            SubagentType.GENERAL: "通用助手",
        }
        return descriptions.get(self.type, "通用助手")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "role_description": self.role_description,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "tools": self.tools,
            "max_iterations": self.max_iterations,
            "temperature": self.temperature,
            "priority": self.priority,
        }


@dataclass
class TeamConfig:
    """
    团队配置
    
    定义一个 Agent 团队的配置，包括成员和协作模式。
    
    Attributes:
        team_id: 团队 ID
        name: 团队名称
        description: 团队描述
        members: 成员配置列表
        coordination_mode: 协作模式 (parallel/sequential/hierarchical)
        max_parallel_tasks: 最大并行任务数
        aggregation_strategy: 结果聚合策略
        timeout: 超时时间（秒）
    """
    
    team_id: str
    name: str = "Agent Team"
    description: str = ""
    members: List[SubagentConfig] = field(default_factory=list)
    coordination_mode: str = "parallel"  # parallel, sequential, hierarchical
    max_parallel_tasks: int = 3
    aggregation_strategy: str = "combine"  # combine, summarize, vote
    timeout: float = 300.0  # 5 分钟
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "name": self.name,
            "description": self.description,
            "members": [m.to_dict() for m in self.members],
            "coordination_mode": self.coordination_mode,
            "max_parallel_tasks": self.max_parallel_tasks,
            "aggregation_strategy": self.aggregation_strategy,
            "timeout": self.timeout,
        }


@dataclass
class TaskResult:
    """
    任务结果
    
    记录子代理执行任务的结果。
    
    Attributes:
        subagent_id: 子代理 ID
        subagent_name: 子代理名称
        success: 是否成功
        output: 输出结果
        error: 错误信息
        tokens_used: 使用的 token 数量
        execution_time: 执行时间（秒）
        metadata: 元数据
    """
    
    subagent_id: str
    subagent_name: str
    success: bool = True
    output: str = ""
    error: Optional[str] = None
    tokens_used: int = 0
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "subagent_id": self.subagent_id,
            "subagent_name": self.subagent_name,
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "tokens_used": self.tokens_used,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


@dataclass
class TeamResult:
    """
    团队执行结果
    
    记录整个团队执行任务的结果。
    
    Attributes:
        team_id: 团队 ID
        success: 是否成功
        task_results: 各子任务结果
        aggregated_output: 聚合后的输出
        total_tokens: 总 token 使用量
        total_time: 总执行时间
    """
    
    team_id: str
    success: bool = True
    task_results: List[TaskResult] = field(default_factory=list)
    aggregated_output: str = ""
    total_tokens: int = 0
    total_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "success": self.success,
            "task_results": [r.to_dict() for r in self.task_results],
            "aggregated_output": self.aggregated_output,
            "total_tokens": self.total_tokens,
            "total_time": self.total_time,
        }