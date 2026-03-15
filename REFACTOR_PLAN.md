# VersaClaw 多模态多Agent架构重构规划

## 一、项目背景与目标

### 1.1 当前架构问题

当前VersaClaw项目基于Nanobot框架扩展了多模态能力，支持图片上传功能，但存在以下问题：

**架构层面**
- 图片处理逻辑分散在多个模块（ImageService、StreamProcessor、chat路由），缺乏统一抽象
- 没有独立的Vision Agent，图片理解直接嵌入主Agent流程，导致职责混乱
- 模型选择逻辑简单粗暴，仅通过字符串匹配判断是否为视觉模型

**扩展性问题**
- 缺乏模型调度层，无法根据任务类型智能选择最优模型
- Agent之间无法协作，复杂任务无法拆解分配
- 新增多模态能力需要修改多处代码，扩展成本高

**用户体验问题**
- 图片处理过程对用户不透明，无法感知处理进度
- 非视觉模型接收图片时错误提示不友好
- 无法针对不同任务使用不同能力的模型

### 1.2 重构目标

参考OpenClaw的多模态实现方式，构建优雅的多Agent架构：

**核心目标**
- 主Agent负责理解用户意图、拆解复杂任务、分配子任务给子Agent
- 每个Agent（主/子）拥有独立的ModelScheduler调度器
- 模型Provider层支持ImageModel配置，实现文本模型与视觉模型的分离
- 在AgentLoop中根据请求内容自动判断并选择合适的模型

**预期收益**
- 架构清晰，职责分明，易于维护和扩展
- 支持复杂任务的自动拆解和并行处理
- 模型选择智能化，优化成本和性能
- 为后续接入更多模态（音频、视频）奠定基础

---

## 二、整体架构设计

### 2.1 架构概览

重构采用**扩展层封装策略**，在保持Nanobot PyPI引用的前提下，通过继承和组合方式增强系统能力。架构分为两层：

**VersaClaw扩展层（新增）**
- EnhancedAgentLoop：继承Nanobot AgentLoop，注入模型调度和多模态检测逻辑
- ModelScheduler：封装Nanobot Provider，实现智能模型选择
- VisionAgent定义：基于Nanobot SubagentManager创建的专用子代理配置
- 配置扩展：在Nanobot配置结构上增加imageModel字段

**Nanobot核心层（PyPI引用，保持不变）**
- AgentLoop：核心处理引擎，被EnhancedAgentLoop继承
- SubagentManager：子代理管理器，直接复用创建Vision Agent
- Provider：LLM提供商抽象，被ModelScheduler封装调用
- SessionManager：会话管理，完全复用
- ToolRegistry：工具注册表，完全复用
- MessageBus：消息总线，完全复用

### 2.2 扩展策略详解

**继承扩展**
- EnhancedAgentLoop继承AgentLoop
- 重写关键方法注入模型调度逻辑
- 保留父类所有功能，仅增强特定环节

**组合封装**
- ModelScheduler内部持有Provider实例
- 对外暴露与Provider一致的接口
- 内部实现智能调度，对调用方透明

**配置扩展**
- 在Nanobot现有配置结构上添加新字段
- 向后兼容，旧配置文件仍可正常工作
- 新字段有合理默认值

**直接复用**
- SubagentManager：直接使用其API创建Vision Agent
- SessionManager：会话管理逻辑完全复用
- ToolRegistry：工具注册机制完全复用

### 2.3 核心组件关系

系统核心组件之间的关系如下（方括号标注来源）：

**请求处理流程**
1. 用户请求通过API路由进入系统
2. [扩展层] EnhancedAgentLoop分析请求，识别是否含图片
3. [扩展层] ModelScheduler根据请求特征选择模型
4. [核心层] Provider执行实际API调用
5. [扩展层] 若需深度图片分析，创建Vision Agent
6. [核心层] SubagentManager管理子代理生命周期
7. 响应流式返回给用户

**模型调度流程**
1. [扩展层] EnhancedAgentLoop检测请求内容类型
2. [扩展层] 向ModelScheduler请求合适的模型
3. [扩展层] ModelScheduler根据配置和特征选择模型
4. [扩展层] ModelScheduler调用内部持有的Provider实例
5. [核心层] Provider执行实际API调用并返回结果

---

## 三、核心模块设计

### 3.1 模型调度层（ModelScheduler）

#### 3.1.1 设计目标

ModelScheduler是整个重构的核心组件，负责：

- 根据请求内容特征智能选择模型
- 支持主模型（text model）和视觉模型（image model）的独立配置
- 实现模型降级和容错机制
- 提供统一的模型调用接口

#### 3.1.2 核心能力

**模型配置管理**
- 主模型配置：用于处理纯文本对话和任务规划
- 视觉模型配置：专门处理包含图片的多模态请求
- Fallback链：当首选模型不可用时自动切换到备选模型

**请求特征分析**
- 检测消息内容是否包含图片
- 分析任务类型（对话、代码、分析等）
- 评估任务复杂度，决定是否需要高级模型

**调度策略**
- 纯文本请求：使用主模型，优先选择快速低成本模型
- 含图片请求：使用视觉模型，确保多模态理解能力
- 复杂推理任务：可选择启用推理增强的模型

#### 3.1.3 配置结构

模型配置采用分层结构，支持全局默认配置和Agent级别覆盖：

**全局配置**
- 默认主模型及其fallback链
- 默认视觉模型及其fallback链
- 通用参数（temperature、max_tokens等）

**Agent级配置**
- 特定Agent可覆盖全局模型配置
- 支持为不同Agent配置不同能力的模型
- 子Agent可继承主Agent配置或独立配置

### 3.2 ModelScheduler设计（封装Provider）

#### 3.2.1 设计目标

ModelScheduler封装Nanobot Provider，增加智能模型选择能力，而非替代Provider。

#### 3.2.2 与Provider的关系

**封装策略**
- ModelScheduler内部持有Nanobot Provider实例
- 对外暴露与Provider一致的调用接口
- 内部实现模型选择逻辑，对调用方透明
- 不修改Nanobot Provider源码

**调用链路**
EnhancedAgentLoop → ModelScheduler → Provider → LLM API

#### 3.2.3 核心能力

**模型配置管理**
- 主模型配置：处理纯文本对话
- 视觉模型配置：处理含图片请求
- Fallback链：首选模型不可用时自动切换

**请求特征分析**
- 检测消息内容是否包含图片
- 统计图片数量和大小
- 判断是否需要视觉模型

**调度策略**
- 纯文本请求：使用主模型
- 含图片请求：使用视觉模型
- 模型不可用时：沿fallback链降级

### 3.3 EnhancedAgentLoop设计（继承AgentLoop）

#### 3.3.1 设计目标

EnhancedAgentLoop继承Nanobot AgentLoop，在保持原有能力的基础上增加多模态处理能力。

#### 3.3.2 与AgentLoop的关系

**继承策略**
- 继承Nanobot AgentLoop父类
- 重写关键方法注入模型调度逻辑
- 保留父类所有工具调用、上下文管理能力
- 不修改Nanobot AgentLoop源码

**重写的方法**
- _process_message：入口处增加多模态检测
- 模型调用点：通过ModelScheduler选择模型

#### 3.3.3 核心能力

**多模态请求检测**
- 检测消息内容是否为多元素列表
- 识别图片格式和大小
- 标记是否需要视觉模型

**模型调度集成**
- 检测到图片时请求视觉模型
- 纯文本时使用主模型
- 处理模型切换的上下文一致性

**流式输出保持**
- 继承父类流式输出能力
- 工具调用过程实时反馈

### 3.4 Vision Agent设计（基于SubagentManager）

#### 3.4.1 设计目标

Vision Agent是一种专用子代理，通过Nanobot SubagentManager创建和管理，无需修改Nanobot源码。

#### 3.4.2 实现方式

**复用SubagentManager**
- Nanobot已有完整的SubagentManager实现
- 直接使用其API创建Vision Agent实例
- 无需增强或修改SubagentManager

**Vision Agent定义**
- 定义专用的系统提示词
- 配置视觉模型作为默认模型
- 可选配置专用工具集

#### 3.4.3 核心职责

**图片理解能力**
- 图片内容描述
- 图片中文字提取
- 图表、表格解析

**调用时机**
- 主Agent判断需要深度图片分析时
- 通过SpawnTool或SubagentManager API创建
- 任务完成后结果返回主Agent

### 3.5 完全复用的Nanobot组件

以下组件直接使用Nanobot实现，无需修改或增强：

**SubagentManager**
- 已有完整的子代理创建、调度、监控能力
- 支持传入model参数指定子代理使用的模型
- 支持并行执行和取消
- 直接使用，无需任何修改

**SessionManager**
- 会话管理逻辑完整
- 支持历史消息存储和检索
- 直接使用，无需任何修改

**ToolRegistry**
- 工具注册和执行机制完善
- 支持自定义工具扩展
- 直接使用，无需任何修改

**MessageBus**
- 消息分发和路由机制完整
- 直接使用，无需任何修改

**MemoryConsolidator**
- 记忆整合机制完整
- 直接使用，无需任何修改

---

## 四、数据流设计

### 4.1 纯文本对话流程

用户发送纯文本消息的处理流程：

**步骤一：请求接收**
- 前端通过API发送消息
- 后端验证参数，提取session_key

**步骤二：主Agent处理**
- 获取或创建会话
- 加载历史上下文
- 构建完整消息列表

**步骤三：模型调度**
- ModelScheduler检测为纯文本请求
- 选择配置的主模型
- Provider执行API调用

**步骤四：响应生成**
- 流式输出响应内容
- 处理可能的工具调用
- 更新会话历史

### 4.2 图片理解流程

用户发送带图片消息的处理流程：

**步骤一：图片上传**
- 前端上传图片到图片服务
- 返回图片ID和元数据

**步骤二：请求构建**
- 构建多模态消息内容
- 包含文本和图片引用

**步骤三：多模态检测**
- AgentLoop检测到图片内容
- 标记为需要视觉模型处理

**步骤四：模型调度**
- ModelScheduler选择视觉模型
- 加载图片数据（base64或URL）
- 构建多模态API请求

**步骤五：视觉理解**
- 视觉模型处理图片内容
- 返回图片描述或分析结果
- 可选：调用Vision Agent进行深度分析

**步骤六：响应整合**
- 将视觉理解结果融入对话
- 生成最终文本响应
- 更新会话历史

### 4.3 复杂任务处理流程

用户提出需要多步骤处理的复杂任务：

**步骤一：意图分析**
- 主Agent分析任务复杂度
- 识别需要调用的能力

**步骤二：任务拆解**
- 将复杂任务拆解为子任务
- 确定子任务类型和依赖关系

**步骤三：子Agent调度**
- 为每个子任务创建或复用子Agent
- 分配任务和上下文
- 并行执行独立子任务

**步骤四：结果收集**
- 等待所有子Agent完成
- 收集各子Agent的输出
- 处理可能的失败和重试

**步骤五：结果整合**
- 主Agent汇总所有结果
- 去重、排序、格式化
- 生成最终响应

---

## 五、配置体系设计

### 5.1 模型配置结构

采用分层配置，支持灵活的模型选择策略：

**主模型配置**
- primary：首选模型标识
- fallbacks：备选模型列表
- 参数覆盖：temperature、max_tokens等

**视觉模型配置**
- primary：首选视觉模型
- fallbacks：备选视觉模型列表
- 自动降级策略

**任务特定配置**
- 代码任务可指定代码专用模型
- 推理任务可指定推理增强模型
- 支持自定义任务类型和模型映射

### 5.2 Agent配置结构

每个Agent可独立配置：

**基础配置**
- Agent标识和名称
- 系统提示词模板
- 可用工具列表

**模型配置**
- 使用全局配置或独立配置
- 任务类型到模型的映射

**行为配置**
- 最大迭代次数
- 工具调用策略
- 输出格式约束

### 5.3 Provider配置结构

Provider配置管理API访问：

**认证配置**
- API密钥
- 自定义端点
- 请求头扩展

**行为配置**
- 超时设置
- 重试策略
- 速率限制

---

## 六、实现原理详解

### 6.1 模型调度原理

ModelScheduler的核心调度逻辑：

**请求特征提取**
- 分析消息内容的类型组成
- 统计文本长度和图片数量
- 识别特殊标记（如代码块、数学公式）

**模型匹配算法**
- 建立任务特征到模型能力的映射表
- 根据特征评分选择最优模型
- 考虑成本、速度、能力的平衡

**降级策略**
- 首选模型不可用时尝试fallback链
- 记录降级原因和频率
- 动态调整模型优先级

### 6.2 Agent协作原理

主Agent与子Agent的协作机制：

**任务分发**
- 主Agent通过工具调用创建子Agent
- 传递任务描述和上下文片段
- 设定子Agent的执行约束

**状态同步**
- 子Agent通过消息队列返回进度
- 主Agent监控执行状态
- 支持中途取消和调整

**结果传递**
- 子Agent完成后的结果写入共享区域
- 主Agent读取并整合结果
- 清理临时资源

### 6.3 多模态处理原理

图片在系统中的处理流程：

**图片预处理**
- 检查格式和大小
- 必要时进行压缩或裁剪
- 生成缩略图用于预览

**编码传输**
- 小图片使用base64内嵌
- 大图片使用URL引用
- 缓存已处理的图片数据

**上下文管理**
- 图片在历史消息中以引用形式存储
- 避免重复传输图片数据
- 支持图片的懒加载

---

## 七、执行规划

### 7.1 阶段一：基础设施搭建

**目标**：建立扩展层基础设施

**主要工作**
- 新建ModelScheduler类，封装Nanobot Provider
- 扩展配置结构，添加imageModel字段（向后兼容）
- 实现模型选择和降级逻辑
- 编写单元测试

**验收标准**
- ModelScheduler能根据请求特征选择模型
- 配置文件支持独立的imageModel配置
- 旧配置文件仍可正常工作

### 7.2 阶段二：EnhancedAgentLoop实现

**目标**：通过继承扩展AgentLoop能力

**主要工作**
- 新建EnhancedAgentLoop类，继承Nanobot AgentLoop
- 重写_process_message方法，注入多模态检测
- 集成ModelScheduler进行模型选择
- 修改NanobotService使用EnhancedAgentLoop

**验收标准**
- EnhancedAgentLoop能自动检测并处理图片
- 图片请求自动路由到视觉模型
- 原有功能完全保持

### 7.3 阶段三：Vision Agent配置

**目标**：定义并集成Vision Agent

**主要工作**
- 定义Vision Agent的系统提示词
- 配置Vision Agent的默认模型（视觉模型）
- 编写Vision Agent调用逻辑
- 测试主Agent与Vision Agent的协作

**验收标准**
- Vision Agent能独立处理图片理解任务
- 主Agent能通过SubagentManager创建Vision Agent
- 结果能正确返回主Agent

### 7.4 阶段四：前端适配

**目标**：前端界面支持新的多模态交互体验

**主要工作**
- 优化图片上传和预览体验
- 展示Agent任务拆解过程
- 可视化模型选择和切换
- 支持子Agent执行状态展示

**验收标准**
- 图片上传流程顺畅
- 用户能感知任务处理进度
- 模型切换对用户透明

### 7.5 阶段五：测试与优化

**目标**：确保系统稳定性和性能

**主要工作**
- 编写单元测试和集成测试
- 性能基准测试和优化
- 错误处理完善
- 文档编写

**验收标准**
- 测试覆盖率达标
- 响应延迟在可接受范围
- 错误处理完善，用户体验友好

---

## 八、风险与对策

### 8.1 技术风险

**Nanobot API变更风险**
- 风险：Nanobot更新可能改变内部API
- 对策：只依赖公开API，内部API变更时及时适配

**模型兼容性风险**
- 风险：不同Provider的多模态API格式差异大
- 对策：ModelScheduler内部统一处理格式差异

**性能风险**
- 风险：模型选择逻辑可能增加延迟
- 对策：特征检测逻辑轻量化，配置预加载

### 8.2 兼容性风险

**现有功能兼容**
- 风险：重构可能影响现有功能
- 对策：EnhancedAgentLoop继承而非替代，渐进式迁移

**配置迁移**
- 风险：旧配置文件格式不兼容
- 对策：新字段有默认值，旧配置无需修改即可工作

### 8.3 维护风险

**上游同步风险**
- 风险：Nanobot更新可能引入冲突
- 对策：保持PyPI引用，定期跟进上游版本；扩展层代码独立，易于适配

---

## 九、总结

本重构规划参考OpenClaw的多模态多Agent架构设计，采用**扩展层封装策略**，在保持Nanobot PyPI引用的前提下实现能力增强。

**核心设计原则**
- 继承而非修改：EnhancedAgentLoop继承AgentLoop
- 封装而非替代：ModelScheduler封装Provider
- 复用而非重建：SubagentManager等直接使用
- 兼容而非替换：配置向后兼容

**扩展层组件**
- ModelScheduler：封装Provider，实现智能模型选择
- EnhancedAgentLoop：继承AgentLoop，注入多模态处理
- Vision Agent定义：基于SubagentManager的子代理配置
- 配置扩展：添加imageModel字段

**完全复用的Nanobot组件**
- SubagentManager、SessionManager、ToolRegistry、MessageBus、MemoryConsolidator

重构分五个阶段执行，渐进式推进，确保系统稳定性和功能完整性。预期重构完成后，系统将具备智能的模型选择能力、优雅的多模态处理流程，同时保持与Nanobot上游的兼容性。
