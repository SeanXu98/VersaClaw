# -*- coding: utf-8 -*-
"""
Subagent Coordinator 模块

该模块实现子代理协调器：
1. 分析任务需求
2. 分配子任务
3. 监控执行状态
4. 处理异常和重试

协调器是层级模式下的核心组件。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.langgraph.team.types import (
    SubagentType,
    SubagentConfig,
    TaskResult,
)

logger = logging.getLogger(__name__)


@dataclass
class SubtaskAllocation:
    """
    子任务分配
    
    Attributes:
        subtask_id: 子任务 ID
        subagent_type: 分配的子代理类型
        task_description: 任务描述
        dependencies: 依赖的其他子任务
        priority: 优先级
    """
    subtask_id: str
    subagent_type: SubagentType
    task_description: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 0


class SubagentCoordinator:
    """
    子代理协调器
    
    负责分析复杂任务并分配给合适的子代理。
    
    核心能力：
    1. 任务分解：将复杂任务分解为子任务
    2. 类型匹配：根据子任务特征匹配子代理类型
    3. 依赖分析：分析子任务之间的依赖关系
    4. 执行监控：监控执行状态并处理异常
    
    使用方式:
        coordinator = SubagentCoordinator()
        allocations = coordinator.analyze_task("Write a research paper on AI")
        for allocation in allocations:
            result = await execute_subagent(allocation)
    """
    
    # 任务类型到子代理类型的映射
    TASK_TYPE_MAPPING = {
        "code": SubagentType.CODER,
        "coding": SubagentType.CODER,
        "programming": SubagentType.CODER,
        "implement": SubagentType.CODER,
        "research": SubagentType.RESEARCHER,
        "analyze": SubagentType.DATA_ANALYST,
        "analysis": SubagentType.DATA_ANALYST,
        "write": SubagentType.WRITER,
        "writing": SubagentType.WRITER,
        "content": SubagentType.WRITER,
        "review": SubagentType.REVIEWER,
        "check": SubagentType.REVIEWER,
        "test": SubagentType.TESTER,
        "testing": SubagentType.TESTER,
        "translate": SubagentType.TRANSLATOR,
        "translation": SubagentType.TRANSLATOR,
        "summarize": SubagentType.SUMMARIZER,
        "summary": SubagentType.SUMMARIZER,
        "explain": SubagentType.EXPLAINER,
        "explaination": SubagentType.EXPLAINER,
        "vision": SubagentType.VISION,
        "image": SubagentType.VISION,
    }
    
    # 复杂任务分解模板
    TASK_DECOMPOSITION_TEMPLATES = {
        "research_paper": [
            {"type": "researcher", "phase": "research"},
            {"type": "data_analyst", "phase": "analysis"},
            {"type": "writer", "phase": "writing"},
            {"type": "reviewer", "phase": "review"},
        ],
        "code_project": [
            {"type": "researcher", "phase": "planning"},
            {"type": "coder", "phase": "implementation"},
            {"type": "tester", "phase": "testing"},
            {"type": "reviewer", "phase": "code_review"},
        ],
        "content_creation": [
            {"type": "researcher", "phase": "research"},
            {"type": "writer", "phase": "writing"},
            {"type": "reviewer", "phase": "edit"},
        ],
    }
    
    def __init__(self):
        """初始化协调器"""
        self._allocation_counter = 0
    
    def analyze_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[SubtaskAllocation]:
        """
        分析任务并生成子任务分配
        
        Args:
            task_description: 任务描述
            context: 执行上下文
        
        Returns:
            List[SubtaskAllocation]: 子任务分配列表
        """
        # 尝试匹配任务模板
        template = self._match_template(task_description)
        
        if template:
            return self._allocate_from_template(template, task_description)
        
        # 分析任务关键词
        return self._allocate_from_keywords(task_description)
    
    def _match_template(self, task: str) -> Optional[str]:
        """匹配任务模板"""
        task_lower = task.lower()
        
        # 研究论文
        if any(kw in task_lower for kw in ["research paper", "论文", "研究论文"]):
            return "research_paper"
        
        # 代码项目
        if any(kw in task_lower for kw in ["code project", "编程", "开发", "implement"]):
            return "code_project"
        
        # 内容创作
        if any(kw in task_lower for kw in ["content", "article", "blog", "文章", "博客"]):
            return "content_creation"
        
        return None
    
    def _allocate_from_template(
        self,
        template_name: str,
        task: str,
    ) -> List[SubtaskAllocation]:
        """从模板生成分配"""
        template = self.TASK_DECOMPOSITION_TEMPLATES.get(template_name, [])
        
        allocations = []
        for i, phase in enumerate(template):
            self._allocation_counter += 1
            allocation = SubtaskAllocation(
                subtask_id=f"subtask_{self._allocation_counter}",
                subagent_type=SubagentType(phase["type"]),
                task_description=f"[{phase['phase']}] {task}",
                dependencies=[],
                priority=len(template) - i,
            )
            allocations.append(allocation)
        
        # 设置依赖关系
        for i in range(1, len(allocations)):
            allocations[i].dependencies.append(allocations[i-1].subtask_id)
        
        return allocations
    
    def _allocate_from_keywords(self, task: str) -> List[SubtaskAllocation]:
        """从关键词生成分配"""
        task_lower = task.lower()
        
        # 检测任务类型
        detected_types = set()
        for keyword, subagent_type in self.TASK_TYPE_MAPPING.items():
            if keyword in task_lower:
                detected_types.add(subagent_type)
        
        # 如果没有检测到特定类型，使用通用类型
        if not detected_types:
            detected_types.add(SubagentType.GENERAL)
        
        # 创建分配
        allocations = []
        for i, subagent_type in enumerate(detected_types):
            self._allocation_counter += 1
            allocation = SubtaskAllocation(
                subtask_id=f"subtask_{self._allocation_counter}",
                subagent_type=subagent_type,
                task_description=task,
                dependencies=[],
                priority=len(detected_types) - i,
            )
            allocations.append(allocation)
        
        return allocations
    
    def create_subagent_config(
        self,
        allocation: SubtaskAllocation,
    ) -> SubagentConfig:
        """
        根据分配创建子代理配置
        
        Args:
            allocation: 子任务分配
        
        Returns:
            SubagentConfig: 子代理配置
        """
        return SubagentConfig(
            id=allocation.subtask_id,
            name=f"{allocation.subagent_type.value.capitalize()} Agent",
            type=allocation.subagent_type,
        )
    
    def aggregate_results(
        self,
        results: List[TaskResult],
    ) -> str:
        """
        聚合执行结果
        
        Args:
            results: 任务结果列表
        
        Returns:
            str: 聚合后的结果
        """
        successful = [r for r in results if r.success]
        
        if not successful:
            return "所有子任务执行失败"
        
        # 简单合并
        parts = []
        for result in successful:
            parts.append(f"**{result.subagent_name}**:\n{result.output}")
        
        return "\n\n---\n\n".join(parts)