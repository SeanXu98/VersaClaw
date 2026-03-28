# -*- coding: utf-8 -*-
"""
LangGraph 状态定义模块

该模块定义了 Agent 图执行过程中使用的所有状态类型：
- AgentState: Agent 运行时状态
- GraphState: LangGraph 图的全局状态
- 各类辅助数据结构

设计原则：
- 使用 TypedDict 和 dataclass 确保类型安全
- 支持状态的可序列化
- 与 LangGraph 的 StateGraph 兼容
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Annotated
from typing_extensions import TypedDict, NotRequired

from langgraph.graph import add_messages


class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MULTIMODAL = "multimodal"


class AgentRole(str, Enum):
    """Agent 角色枚举"""
    MAIN = "main"              # 主 Agent
    VISION = "vision"          # 视觉理解 Agent
    CODE = "code"              # 代码执行 Agent
    RESEARCH = "research"      # 研究分析 Agent
    WRITER = "writer"          # 内容创作 Agent
    COORDINATOR = "coordinator"  # 协调器 Agent


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class VisionAnalysisResult:
    """
    视觉分析结果
    
    Attributes:
        requires_vision: 是否需要视觉理解
        confidence: 置信度 (0-1)
        detected_elements: 检测到的元素类型
        recommended_model: 推荐的模型
        reason: 判断原因
    """
    requires_vision: bool = False
    confidence: float = 0.0
    detected_elements: List[str] = field(default_factory=list)
    recommended_model: Optional[str] = None
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "requires_vision": self.requires_vision,
            "confidence": self.confidence,
            "detected_elements": self.detected_elements,
            "recommended_model": self.recommended_model,
            "reason": self.reason,
        }


@dataclass
class SubagentTask:
    """
    子代理任务
    
    Attributes:
        id: 任务 ID
        role: 子代理角色
        description: 任务描述
        status: 任务状态
        input_data: 输入数据
        output_data: 输出数据
        error: 错误信息
        model_used: 使用的模型
        tokens_used: 使用的 token 数量
    """
    id: str
    role: AgentRole
    description: str
    status: TaskStatus = TaskStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "description": self.description,
            "status": self.status.value,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
        }


@dataclass
class TeamResult:
    """
    团队执行结果
    
    Attributes:
        team_id: 团队 ID
        tasks: 子任务列表
        aggregated_result: 聚合结果
        total_tokens: 总 token 使用量
        execution_time: 执行时间（秒）
        success: 是否成功
    """
    team_id: str
    tasks: List[SubagentTask] = field(default_factory=list)
    aggregated_result: Optional[str] = None
    total_tokens: int = 0
    execution_time: float = 0.0
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "aggregated_result": self.aggregated_result,
            "total_tokens": self.total_tokens,
            "execution_time": self.execution_time,
            "success": self.success,
        }


class Message(TypedDict):
    """
    消息结构
    
    与 LangChain 的消息格式兼容
    """
    role: str
    content: str | List[Dict[str, Any]]
    name: NotRequired[str]
    tool_calls: NotRequired[List[Dict[str, Any]]]
    tool_call_id: NotRequired[str]


class AgentState(TypedDict):
    """
    Agent 运行时状态
    
    这是 LangGraph 图中传递的核心状态对象。
    使用 Annotated 类型确保正确的合并行为。
    
    Attributes:
        messages: 消息历史（使用 add_messages reducer）
        current_query: 当前用户查询
        session_key: 会话标识
        channel: 渠道标识
        message_type: 消息类型
        images: 图片列表
        vision_analysis: 视觉分析结果
        selected_model: 选中的模型
        model_type: 模型类型 (text/vision)
        tool_calls: 工具调用记录
        tool_results: 工具执行结果
        subagent_tasks: 子代理任务
        team_result: 团队执行结果
        iteration: 当前迭代次数
        max_iterations: 最大迭代次数
        final_response: 最终响应
        error: 错误信息
        metadata: 元数据
    """
    # 消息历史 - 使用 add_messages reducer 自动合并
    messages: Annotated[List[Message], add_messages]
    
    # 用户输入
    current_query: str
    session_key: str
    channel: str
    
    # 消息类型判断
    message_type: MessageType
    images: List[Dict[str, Any]]
    
    # 视觉分析结果
    vision_analysis: Dict[str, Any]
    
    # 模型选择
    selected_model: str
    model_type: str  # "text" or "vision"
    
    # 工具调用
    tool_calls: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    
    # Agent Team
    subagent_tasks: List[Dict[str, Any]]
    team_result: Dict[str, Any]
    
    # 迭代控制
    iteration: int
    max_iterations: int
    
    # ReAct 循环控制
    should_continue: bool  # LLM 自主决定是否继续（非工具调用场景）
    continue_reason: str   # 继续推理的原因
    
    # 输出
    final_response: str
    reasoning_content: str
    
    # 错误处理
    error: str
    
    # 元数据
    metadata: Dict[str, Any]


class GraphState(TypedDict):
    """
    图全局状态
    
    用于管理整个图的全局配置和状态。
    
    Attributes:
        provider: LLM Provider 配置
        config: 扩展配置
        workspace: 工作空间路径
        tools: 可用工具列表
        active_agents: 活跃的 Agent 列表
    """
    provider: Dict[str, Any]
    config: Dict[str, Any]
    workspace: str
    tools: List[Dict[str, Any]]
    active_agents: List[str]


def create_initial_state(
    query: str,
    session_key: str = "default",
    channel: str = "web",
    images: Optional[List[Dict[str, Any]]] = None,
    model: Optional[str] = None,
    max_iterations: int = 40,
    history: Optional[List[Message]] = None,
) -> AgentState:
    """
    创建初始 Agent 状态
    
    Args:
        query: 用户查询
        session_key: 会话标识
        channel: 渠道标识
        images: 图片列表
        model: 指定模型
        max_iterations: 最大迭代次数
        history: 会话历史消息列表
    
    Returns:
        AgentState: 初始化的状态对象
    """
    return AgentState(
        messages=history or [],  # 使用会话历史
        current_query=query,
        session_key=session_key,
        channel=channel,
        message_type=MessageType.TEXT,
        images=images or [],
        vision_analysis={},
        selected_model=model or "",
        model_type="text",
        tool_calls=[],
        tool_results={},
        subagent_tasks=[],
        team_result={},
        iteration=0,
        max_iterations=max_iterations,
        should_continue=False,
        continue_reason="",
        final_response="",
        reasoning_content="",
        error="",
        metadata={},
    )