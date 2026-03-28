# -*- coding: utf-8 -*-
"""
Agent Team Manager 模块

该模块实现 Agent 团队管理器：
1. 创建和管理子代理团队
2. 协调子代理执行
3. 聚合子代理结果
4. 提供统一的接口给主 Agent
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from app.langgraph.team.types import (
    SubagentType,
    SubagentConfig,
    TeamConfig,
    TaskResult,
    TeamResult,
)

if TYPE_CHECKING:
    from nanobot.providers.base import LLMProvider
    from app.extension.config_extension import ExtendedConfig

logger = logging.getLogger(__name__)


class AgentTeamManager:
    """
    Agent 团队管理器
    
    负责创建、协调和管理子代理团队。
    
    核心能力：
    1. 根据配置创建子代理团队
    2. 分配任务给子代理
    3. 协调子代理并行或顺序执行
    4. 聚合子代理结果
    
    使用方式：
        manager = AgentTeamManager(provider=provider)
        
        # 创建团队
        team = manager.create_team(
            name="Research Team",
            members=[
                {"type": "researcher", "task": "research topic A"},
                {"type": "analyst", "task": "analyze data B"},
            ]
        )
        
        # 执行团队任务
        result = await manager.execute_team(team)
    """
    
    def __init__(
        self,
        provider: Optional["LLMProvider"] = None,
        config: Optional["ExtendedConfig"] = None,
        on_progress: Optional[Callable] = None,
    ):
        """
        初始化团队管理器
        
        Args:
            provider: LLM Provider 实例
            config: 扩展配置
            on_progress: 进度回调
        """
        self.provider = provider
        self.config = config
        self.on_progress = on_progress
        
        # 活跃的团队
        self._active_teams: Dict[str, TeamConfig] = {}
        
        # 执行结果缓存
        self._results: Dict[str, TeamResult] = {}
    
    def create_team(
        self,
        name: str,
        description: str = "",
        members: Optional[List[Dict[str, Any]]] = None,
        coordination_mode: str = "parallel",
        aggregation_strategy: str = "combine",
    ) -> TeamConfig:
        """
        创建团队配置
        
        Args:
            name: 团队名称
            description: 团队描述
            members: 成员配置列表
            coordination_mode: 协作模式
            aggregation_strategy: 聚合策略
        
        Returns:
            TeamConfig: 团队配置
        """
        team_id = f"team_{uuid.uuid4().hex[:8]}"
        
        # 创建成员配置
        member_configs = []
        if members:
            for i, member in enumerate(members):
                subagent_type = SubagentType(member.get("type", "general"))
                member_config = SubagentConfig(
                    id=f"{team_id}_member_{i}",
                    name=member.get("name", f"Agent {i+1}"),
                    type=subagent_type,
                    role_description=member.get("role_description", ""),
                    model=member.get("model"),
                    tools=member.get("tools", []),
                    max_iterations=member.get("max_iterations", 10),
                )
                member_configs.append(member_config)
        
        team_config = TeamConfig(
            team_id=team_id,
            name=name,
            description=description,
            members=member_configs,
            coordination_mode=coordination_mode,
            aggregation_strategy=aggregation_strategy,
        )
        
        # 记录活跃团队
        self._active_teams[team_id] = team_config
        
        logger.info(f"[AgentTeamManager] Created team: {name} with {len(member_configs)} members")
        
        return team_config
    
    async def execute_team(
        self,
        team_config: TeamConfig,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> TeamResult:
        """
        执行团队任务
        
        Args:
            team_config: 团队配置
            task_description: 任务描述
            context: 执行上下文
        
        Returns:
            TeamResult: 执行结果
        """
        start_time = time.time()
        team_id = team_config.team_id
        
        logger.info(f"[AgentTeamManager] Executing team {team_id}: {task_description}")
        
        # 发送进度通知
        if self.on_progress:
            await self.on_progress(f"启动团队 {team_config.name} 执行任务...")
        
        try:
            # 根据协作模式执行（带超时控制）
            try:
                task_results = await asyncio.wait_for(
                    self._execute_by_mode(team_config, task_description, context),
                    timeout=team_config.timeout,
                )
            except asyncio.TimeoutError:
                logger.error(f"[AgentTeamManager] Team {team_id} execution timed out after {team_config.timeout}s")
                return TeamResult(
                    team_id=team_id,
                    success=False,
                    aggregated_output=f"团队执行超时（{team_config.timeout}秒）",
                )
            
            # 聚合结果
            aggregated = await self._aggregate_results(
                task_results, team_config.aggregation_strategy
            )
            
            # 计算统计
            total_tokens = sum(r.tokens_used for r in task_results)
            total_time = time.time() - start_time
            
            result = TeamResult(
                team_id=team_id,
                success=all(r.success for r in task_results),
                task_results=task_results,
                aggregated_output=aggregated,
                total_tokens=total_tokens,
                total_time=total_time,
            )
            
            # 缓存结果
            self._results[team_id] = result
            
            logger.info(
                f"[AgentTeamManager] Team {team_id} completed: "
                f"success={result.success}, time={total_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"[AgentTeamManager] Team execution failed: {e}")
            return TeamResult(
                team_id=team_id,
                success=False,
                aggregated_output=f"团队执行失败: {str(e)}",
            )
        finally:
            # 清理活跃团队（防止内存泄漏）
            if team_id in self._active_teams:
                del self._active_teams[team_id]
    
    async def _execute_by_mode(
        self,
        team_config: TeamConfig,
        task_description: str,
        context: Optional[Dict[str, Any]],
    ) -> List[TaskResult]:
        """
        根据协作模式执行任务
        
        Args:
            team_config: 团队配置
            task_description: 任务描述
            context: 执行上下文
        
        Returns:
            List[TaskResult]: 任务结果列表
        """
        if team_config.coordination_mode == "parallel":
            return await self._execute_parallel(team_config, task_description, context)
        elif team_config.coordination_mode == "sequential":
            return await self._execute_sequential(team_config, task_description, context)
        else:  # hierarchical
            return await self._execute_hierarchical(team_config, task_description, context)
    
    async def _execute_parallel(
        self,
        team_config: TeamConfig,
        task_description: str,
        context: Optional[Dict[str, Any]],
    ) -> List[TaskResult]:
        """
        并行执行任务
        
        Args:
            team_config: 团队配置
            task_description: 任务描述
            context: 执行上下文
        
        Returns:
            List[TaskResult]: 任务结果列表
        """
        # 创建并发任务
        tasks = []
        semaphore = asyncio.Semaphore(team_config.max_parallel_tasks)
        
        async def execute_member(member: SubagentConfig) -> TaskResult:
            async with semaphore:
                return await self._execute_subagent(
                    member, task_description, context
                )
        
        for member in team_config.members:
            tasks.append(execute_member(member))
        
        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        task_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_results.append(TaskResult(
                    subagent_id=team_config.members[i].id,
                    subagent_name=team_config.members[i].name,
                    success=False,
                    error=str(result),
                ))
            else:
                task_results.append(result)
        
        return task_results
    
    async def _execute_sequential(
        self,
        team_config: TeamConfig,
        task_description: str,
        context: Optional[Dict[str, Any]],
    ) -> List[TaskResult]:
        """
        顺序执行任务
        
        Args:
            team_config: 团队配置
            task_description: 任务描述
            context: 执行上下文
        
        Returns:
            List[TaskResult]: 任务结果列表
        """
        results = []
        
        # 按优先级排序
        sorted_members = sorted(
            team_config.members,
            key=lambda m: m.priority,
            reverse=True,
        )
        
        current_context = context or {}
        
        for member in sorted_members:
            # 发送进度
            if self.on_progress:
                await self.on_progress(f"正在执行: {member.name}")
            
            # 执行子代理
            result = await self._execute_subagent(
                member, task_description, current_context
            )
            results.append(result)
            
            # 更新上下文（将前一个结果传递给下一个）
            if result.success:
                current_context["previous_result"] = result.output
            
            # 如果失败且没有 fallback，停止执行
            if not result.success:
                logger.warning(
                    f"[AgentTeamManager] Member {member.name} failed, stopping sequential execution"
                )
                break
        
        return results
    
    async def _execute_hierarchical(
        self,
        team_config: TeamConfig,
        task_description: str,
        context: Optional[Dict[str, Any]],
    ) -> List[TaskResult]:
        """
        层级执行任务
        
        协调器先分析任务，分配给子代理，然后聚合结果。
        协调器的输出会作为上下文传递给各子代理。
        
        Args:
            team_config: 团队配置
            task_description: 任务描述
            context: 执行上下文
        
        Returns:
            List[TaskResult]: 任务结果列表
        """
        # 1. 协调器分析任务并生成分配方案
        coordinator = SubagentConfig(
            id=f"{team_config.team_id}_coordinator",
            name="Coordinator",
            type=SubagentType.COORDINATOR,
        )
        
        # 构建成员信息供协调器参考
        member_info = [
            {"name": m.name, "type": m.type.value, "role": m.role_description}
            for m in team_config.members
        ]
        
        coordination_prompt = f"""Analyze the following task and create a coordination plan.

Task: {task_description}

Available team members:
{chr(10).join(f"- {m['name']} ({m['type']}): {m['role']}" for m in member_info)}

Please provide:
1. Task breakdown for each team member
2. Any dependencies between subtasks
3. Expected output format

Output your plan in a clear, structured format."""
        
        # 2. 协调器生成分配方案
        coordination_result = await self._execute_subagent(
            coordinator,
            coordination_prompt,
            context,
        )
        
        results = [coordination_result]
        
        # 3. 如果协调器成功，将分配方案作为上下文传递给子代理
        enhanced_context = dict(context) if context else {}
        if coordination_result.success:
            enhanced_context["coordination_plan"] = coordination_result.output
            enhanced_context["team_goal"] = task_description
        
        # 4. 子代理执行分配的任务（并行执行以提高效率）
        for member in team_config.members:
            if self.on_progress:
                await self.on_progress(f"正在执行: {member.name}")
            
            # 为每个成员生成个性化任务描述
            member_task = self._build_member_task(member, task_description, coordination_result.output)
            
            result = await self._execute_subagent(
                member,
                member_task,
                enhanced_context,
            )
            results.append(result)
        
        return results
    
    def _build_member_task(
        self,
        member: SubagentConfig,
        task_description: str,
        coordination_plan: str,
    ) -> str:
        """
        为成员构建个性化任务描述
        
        Args:
            member: 成员配置
            task_description: 原始任务描述
            coordination_plan: 协调器生成的分配方案
        
        Returns:
            str: 个性化任务描述
        """
        return f"""You are {member.name}, a {member.role_description}.

Overall Task: {task_description}

Coordination Plan:
{coordination_plan}

Please focus on your area of expertise and contribute to the team goal.
Provide your output in a clear format that can be combined with others' contributions."""
    
    async def _execute_subagent(
        self,
        config: SubagentConfig,
        task: str,
        context: Optional[Dict[str, Any]],
    ) -> TaskResult:
        """
        执行单个子代理
        
        Args:
            config: 子代理配置
            task: 任务描述
            context: 执行上下文
        
        Returns:
            TaskResult: 执行结果
        """
        start_time = time.time()
        
        try:
            if not self.provider:
                raise ValueError("LLM Provider not configured")
            
            # 确定使用的模型
            model = config.model
            if not model and self.config:
                model = self.config.text_model
            
            # 构建消息
            messages = self._build_messages(config, task, context)
            
            # 调用 LLM - 使用 chat() 方法（LiteLLMProvider 的原生方法）
            response = await self.provider.chat(
                messages=messages,
                model=model,
                temperature=config.temperature,
                max_tokens=4096,
            )
            
            # 提取结果
            output = response.content if hasattr(response, "content") else str(response)
            tokens = response.usage.get("total_tokens", 0) if hasattr(response, "usage") else 0
            
            return TaskResult(
                subagent_id=config.id,
                subagent_name=config.name,
                success=True,
                output=output,
                tokens_used=tokens,
                execution_time=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"[AgentTeamManager] Subagent {config.name} failed: {e}")
            return TaskResult(
                subagent_id=config.id,
                subagent_name=config.name,
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
            )
    
    def _build_messages(
        self,
        config: SubagentConfig,
        task: str,
        context: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        构建子代理消息
        
        Args:
            config: 子代理配置
            task: 任务描述
            context: 执行上下文
        
        Returns:
            List[Dict]: 消息列表
        """
        messages = [
            {"role": "system", "content": config.system_prompt},
        ]
        
        # 添加上下文
        if context:
            context_str = self._format_context(context)
            if context_str:
                messages.append({
                    "role": "user",
                    "content": f"Context:\n{context_str}\n\nPlease proceed with your task.",
                })
        
        # 添加任务
        messages.append({
            "role": "user",
            "content": task,
        })
        
        return messages
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文"""
        parts = []
        
        if "previous_result" in context:
            parts.append(f"Previous result:\n{context['previous_result']}")
        
        if "team_goal" in context:
            parts.append(f"Team goal:\n{context['team_goal']}")
        
        return "\n\n".join(parts)
    
    async def _aggregate_results(
        self,
        results: List[TaskResult],
        strategy: str,
    ) -> str:
        """
        聚合子代理结果
        
        Args:
            results: 任务结果列表
            strategy: 聚合策略
        
        Returns:
            str: 聚合后的结果
        """
        if not results:
            return ""
        
        # 过滤成功的结果
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return "所有子代理执行失败"
        
        if strategy == "combine":
            # 直接合并
            parts = []
            for r in successful_results:
                parts.append(f"**{r.subagent_name}**:\n{r.output}")
            return "\n\n---\n\n".join(parts)
        
        elif strategy == "summarize":
            # 使用 LLM 总结
            if self.provider:
                combined = "\n\n".join(r.output for r in successful_results)
                messages = [
                    {
                        "role": "system",
                        "content": "You are a summarizer. Create a coherent summary from the following contributions.",
                    },
                    {"role": "user", "content": combined},
                ]
                response = await self.provider.chat(messages=messages)
                return response.content if hasattr(response, "content") else combined
            else:
                return "\n\n".join(r.output for r in successful_results)
        
        elif strategy == "vote":
            # 简单投票（选择最长或最详细的）
            best = max(successful_results, key=lambda r: len(r.output))
            return best.output
        
        return successful_results[0].output
    
    def get_team_result(self, team_id: str) -> Optional[TeamResult]:
        """获取团队执行结果"""
        return self._results.get(team_id)
    
    def get_active_teams(self) -> List[str]:
        """获取活跃团队 ID 列表"""
        return list(self._active_teams.keys())