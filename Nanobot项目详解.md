# 🐈 nanobot 项目深度解析

> 香港大学数据科学实验室（HKUDS）出品的超轻量级个人 AI 助手框架

---

## 目录

1. [项目概述](#一项目概述)
2. [技术栈与依赖](#二技术栈与依赖)
3. [代码结构](#三代码结构)
4. [核心模块详解](#四核心模块详解)
5. [Channel 通道系统](#五channel-通道系统)
6. [消息总线](#六消息总线messagebus)
7. [配置系统](#七配置系统)
8. [数据流与架构](#八数据流与架构)
9. [代码示例](#九代码示例)
10. [扩展开发指南](#十扩展开发指南)

---

## 一、项目概述

### 1.1 基本信息

| 属性 | 值 |
|------|-----|
| **项目名称** | nanobot |
| **版本** | 0.1.4.post3 |
| **仓库地址** | https://github.com/HKUDS/nanobot |
| **核心代码量** | ~4,000 行（相比 OpenClaw 的 430,000+ 行减少 99%） |
| **Python 版本** | >= 3.11 |
| **许可证** | MIT |

### 1.2 核心特性

```
┌─────────────────────────────────────────────────────────────┐
│  🪶 Ultra-Lightweight   - 仅 4000 行核心代码                │
│  🔬 Research-Ready      - 清晰可读，易于理解和扩展          │
│  ⚡ Lightning Fast      - 极小的内存占用，快速启动          │
│  💎 Easy-to-Use         - 一键部署，开箱即用                │
└─────────────────────────────────────────────────────────────┘
```

**支持的功能**：
- 🤖 多 LLM 提供商（OpenRouter, Anthropic, OpenAI, DeepSeek 等 17+）
- 💬 多消息渠道（Telegram, Discord, WhatsApp, Slack, 飞书, 钉钉 等 10+）
- 🔧 MCP (Model Context Protocol) 工具服务器支持
- 📝 会话管理与记忆系统
- ⏰ 定时任务（Cron）
- 💓 心跳服务（Heartbeat）
- 🧬 子代理支持（Subagent）

### 1.3 架构图

```
                         ┌────────────────────────────────────────┐
                         │              Channels                   │
                         │  Telegram │ Discord │ Slack │ WhatsApp │
                         └──────────────────┬─────────────────────┘
                                            │
                                            ▼
                         ┌────────────────────────────────────────┐
                         │            MessageBus                   │
                         │        (Inbound/Outbound Queue)        │
                         └──────────────────┬─────────────────────┘
                                            │
                                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              AgentLoop                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Context    │  │   Session   │  │    Tools    │  │   Provider  │      │
│  │  Builder    │  │   Manager   │  │   Registry  │  │  (LiteLLM)  │      │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                    Agent Iteration Loop                             │ │
│  │   1. Build Context  →  2. Call LLM  →  3. Execute Tools            │ │
│  │                    ←←←←←←←←←←←←←←←←←←←←                            │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 二、技术栈与依赖

### 2.1 核心依赖

```toml
[project.dependencies]
"typer>=0.20.0,<1.0.0"           # CLI 框架 - 构建命令行界面
"litellm>=1.81.5,<2.0.0"         # LLM 统一接口 - 抽象不同 AI 模型
"pydantic>=2.12.0,<3.0.0"        # 数据验证 - 配置和参数校验
"pydantic-settings>=2.12.0"      # 配置管理 - 环境变量和配置文件
"websockets>=16.0,<17.0"         # WebSocket - 实时通信
"httpx>=0.28.0,<1.0.0"           # HTTP 客户端 - 异步 HTTP 请求
"mcp>=1.26.0,<2.0.0"             # MCP 协议 - 外部工具集成
"loguru>=0.7.0,<1.0.0"           # 日志系统 - 结构化日志
"rich>=13.0.0,<14.0.0"           # 终端美化 - 丰富的输出格式
```

### 2.2 可选依赖

```toml
[project.optional-dependencies]
telegram = ["python-telegram-bot>=21.0,<23.0"]
discord = ["discord.py>=2.4.0,<3.0.0"]
slack = ["slack-sdk>=3.19.0,<4.0.0", "slack-bolt>=1.18.0,<2.0.0"]
matrix = ["matrix-nio>=0.24.0,<0.26.0"]
email = ["aioimaplib>=1.0.0,<2.0.0"]
```

---

## 三、代码结构

### 3.1 目录树

```
nanobot/
├── 📁 agent/                 # 🧠 核心 Agent 逻辑
│   ├── loop.py              #    Agent 主循环（LLM ↔ 工具执行）
│   ├── context.py           #    提示词构建器
│   ├── memory.py            #    持久化记忆存储
│   ├── skills.py            #    技能加载器
│   ├── subagent.py          #    子代理管理器
│   └── 📁 tools/            #    内置工具集
│       ├── registry.py      #      工具注册表
│       ├── filesystem.py    #      文件系统工具（读/写/编辑/列表）
│       ├── shell.py         #      Shell 命令执行
│       ├── web.py           #      网络搜索/抓取
│       ├── message.py       #      消息发送
│       ├── spawn.py         #      子代理生成
│       └── mcp.py           #      MCP 工具集成
│
├── 📁 bus/                   # 🚌 消息路由
│   ├── events.py            #    事件类型定义
│   └── queue.py             #    消息队列实现
│
├── 📁 channels/              # 📱 聊天渠道集成
│   ├── manager.py           #    渠道管理器
│   ├── telegram.py          #    Telegram 机器人
│   ├── discord.py           #    Discord 机器人
│   ├── slack.py             #    Slack 机器人
│   ├── feishu.py            #    飞书机器人
│   ├── dingtalk.py          #    钉钉机器人
│   ├── whatsapp.py          #    WhatsApp 消息
│   ├── email.py             #    邮件收发
│   ├── qq.py                #    QQ 机器人
│   ├── matrix.py            #    Matrix 协议
│   └── mochat.py            #    Mochat 平台
│
├── 📁 cli/                   # 🖥️ 命令行接口
│   └── commands.py          #    CLI 命令定义
│
├── 📁 config/                # ⚙️ 配置管理
│   ├── schema.py            #    Pydantic 配置模式定义
│   └── loader.py            #    配置加载器
│
├── 📁 cron/                  # ⏰ 定时任务服务
│   └── service.py           #    Cron 调度实现
│
├── 📁 heartbeat/             # 💓 心跳服务
│   └── service.py           #    定期任务唤醒
│
├── 📁 providers/             # 🤖 LLM 提供商
│   ├── base.py              #    提供商基类
│   ├── litellm_provider.py  #    LiteLLM 实现
│   └── registry.py          #    提供商注册表
│
├── 📁 session/               # 💬 会话管理
│   └── manager.py           #    会话持久化
│
├── 📁 skills/                # 🎯 内置技能
│   ├── github/              #    GitHub 集成
│   ├── weather/             #    天气查询
│   └── tmux/                #    Tmux 控制
│
└── 📁 utils/                 # 🔧 工具函数
    └── helpers.py           #    通用辅助函数
```

### 3.2 关键文件说明

| 文件 | 职责 | 代码量 |
|------|------|--------|
| `agent/loop.py` | Agent 主循环，核心处理引擎 | ~300 行 |
| `agent/context.py` | 系统提示词构建 | ~200 行 |
| `providers/registry.py` | LLM 提供商元数据注册 | ~150 行 |
| `config/schema.py` | Pydantic 配置模式 | ~500 行 |
| `session/manager.py` | 会话状态持久化 | ~150 行 |
| `cli/commands.py` | CLI 命令入口 | ~200 行 |

---

## 四、核心模块详解

### 4.1 AgentLoop 核心循环

**位置**: `nanobot/agent/loop.py`

AgentLoop 是整个系统的**心脏**，负责协调所有组件完成 AI 对话和任务执行。

#### 类定义

```python
class AgentLoop:
    """
    The agent loop is the core processing engine.
    It:
    1. Receives messages from the bus
    2. Builds context with history, memory, skills
    3. Calls the LLM
    4. Executes tool calls
    5. Sends responses back
    """

    # 工具结果最大字符数，防止上下文过长
    _TOOL_RESULT_MAX_CHARS = 500

    def __init__(
        self,
        bus: MessageBus,                    # 消息总线
        provider: LLMProvider,              # LLM 提供商
        workspace: Path,                    # 工作目录
        model: str | None = None,           # 模型名称
        max_iterations: int = 40,           # 最大工具调用迭代次数
        temperature: float = 0.1,           # 温度参数
        max_tokens: int = 4096,             # 最大 token 数
        memory_window: int = 100,           # 记忆窗口大小
        reasoning_effort: str | None = None,# 推理强度
        brave_api_key: str | None = None,   # Brave 搜索 API Key
        web_proxy: str | None = None,       # 网络代理
        exec_config: ExecToolConfig | None = None,  # Shell 执行配置
        cron_service: CronService | None = None,    # 定时任务服务
        restrict_to_workspace: bool = False,        # 是否限制在工作目录
        session_manager: SessionManager | None = None,  # 会话管理器
        mcp_servers: dict | None = None,    # MCP 服务器配置
        channels_config: ChannelsConfig | None = None,  # 渠道配置
    ):
        self.bus = bus
        self.provider = provider
        self.workspace = workspace
        self.model = model
        self.max_iterations = max_iterations
        self.temperature = temperature
        self.max_tokens = max_tokens
        # ... 其他初始化
```

#### 核心循环实现

```python
async def _run_agent_loop(
    self,
    initial_messages: list[dict],
    on_progress: Callable[..., Awaitable[None]] | None = None,
) -> tuple[str | None, list[str], list[dict]]:
    """
    Run the agent iteration loop.
    Returns: (final_content, tools_used, messages)
    """
    messages = initial_messages
    iteration = 0
    final_content = None
    tools_used: list[str] = []

    # ========== 主循环 ==========
    while iteration < self.max_iterations:
        iteration += 1

        # 1️⃣ 调用 LLM
        response = await self.provider.chat(
            messages=messages,
            tools=self.tools.get_definitions(),  # 注入工具定义
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            reasoning_effort=self.reasoning_effort,
        )

        # 2️⃣ 处理工具调用
        if response.has_tool_calls:
            # 发送进度回调（思考内容）
            if on_progress:
                clean = self._strip_think(response.content)
                if clean:
                    await on_progress(clean)
                await on_progress(
                    self._tool_hint(response.tool_calls),
                    tool_hint=True
                )

            # 添加助手消息到历史
            messages = self.context.add_assistant_message(
                messages,
                response.content,
                tool_call_dicts,
                reasoning_content=response.reasoning_content,
                thinking_blocks=response.thinking_blocks,
            )

            # 3️⃣ 执行工具
            for tool_call in response.tool_calls:
                tools_used.append(tool_call.name)
                result = await self.tools.execute(
                    tool_call.name,
                    tool_call.arguments
                )
                # 添加工具结果到上下文
                messages = self.context.add_tool_result(
                    messages,
                    tool_call.id,
                    tool_call.name,
                    result
                )

        else:
            # 无工具调用，返回最终结果
            clean = self._strip_think(response.content)
            messages = self.context.add_assistant_message(
                messages, clean,
                reasoning_content=response.reasoning_content,
                thinking_blocks=response.thinking_blocks,
            )
            final_content = clean
            break

    return final_content, tools_used, messages
```

#### 流式处理支持

```python
async def process_stream(
    self,
    content: str | list[dict],
    session_key: str,
    channel: str = "cli",
    chat_id: str | None = None,
    media: list[dict] | None = None,
) -> AsyncGenerator[dict, None]:
    """流式处理消息，返回 SSE 事件流"""

    # 创建进度回调
    async def on_progress(
        text: str,
        tool_hint: bool = False,
        event_type: str = "content"
    ):
        yield {
            "type": event_type,
            "content": text,
            "tool_hint": tool_hint
        }

    # 执行主循环
    async for event in self._run_agent_loop(messages, on_progress):
        yield event
```

---

### 4.2 ContextBuilder 上下文构建

**位置**: `nanobot/agent/context.py`

ContextBuilder 负责**构建 Agent 的系统提示和消息上下文**。

#### 系统提示构建

```python
class ContextBuilder:
    """Builds the context (system prompt + messages) for the agent."""

    # 启动时加载的文件
    BOOTSTRAP_FILES = [
        "AGENTS.md",    # Agent 行为定义
        "SOUL.md",      # 核心人格
        "USER.md",      # 用户偏好
        "TOOLS.md",     # 工具使用指南
        "IDENTITY.md"   # 身份定义
    ]

    def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
        """构建系统提示词"""

        parts = [self._get_identity()]  # 基础身份

        # 加载 bootstrap 文件
        bootstrap = self._load_bootstrap_files()
        if bootstrap:
            parts.append(bootstrap)

        # 注入长期记忆
        memory = self.memory.get_memory_context()
        if memory:
            parts.append(f"# Memory\n\n{memory}")

        # 注入活跃技能
        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
            if always_content:
                parts.append(f"# Active Skills\n\n{always_content}")

        return "\n\n---\n\n".join(parts)
```

#### Identity 模板

```python
def _get_identity(self) -> str:
    """生成基础身份提示词"""

    runtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# nanobot

You are nanobot, a helpful AI assistant.

## Runtime
{runtime}

## Workspace
Your workspace is at: {workspace_path}
- Long-term memory: {workspace_path}/memory/MEMORY.md
- History log: {workspace_path}/memory/HISTORY.md
- Custom skills: {workspace_path}/skills/{{skill-name}}/SKILL.md

## nanobot Guidelines
- State intent before tool calls, but NEVER predict or claim results before receiving them.
- Before modifying a file, read it first. Do not assume files or directories exist.
- After writing or editing a file, re-read it if accuracy matters.
- If a tool call fails, analyze the error before retrying with a different approach.
- Ask for clarification when the request is ambiguous.

Reply directly with text for conversations. Only use the 'message' tool to send to a specific chat channel."""
```

#### 消息格式化

```python
def add_assistant_message(
    self,
    messages: list[dict],
    content: str | None,
    tool_calls: list[dict] | None = None,
    reasoning_content: str | None = None,
    thinking_blocks: list[dict] | None = None,
) -> list[dict]:
    """添加助手消息到历史"""

    entry: dict = {"role": "assistant"}

    if content:
        entry["content"] = content

    if tool_calls:
        entry["tool_calls"] = tool_calls

    # Claude 思考块支持
    if thinking_blocks:
        entry["thinking_blocks"] = thinking_blocks

    messages.append(entry)
    return messages


def add_tool_result(
    self,
    messages: list[dict],
    tool_call_id: str,
    tool_name: str,
    result: str,
) -> list[dict]:
    """添加工具调用结果"""

    # 截断过长的结果
    if len(result) > self._TOOL_RESULT_MAX_CHARS:
        result = result[:self._TOOL_RESULT_MAX_CHARS] + "\n... (truncated)"

    messages.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "content": result,
    })
    return messages
```

---

### 4.3 Provider 注册机制

**位置**: `nanobot/providers/registry.py`

nanobot 使用**注册表模式**作为单一事实来源管理所有 LLM 提供商。

#### ProviderSpec 数据结构

```python
@dataclass(frozen=True)
class ProviderSpec:
    """One LLM provider's metadata."""

    # ===== 身份信息 =====
    name: str                        # 配置字段名（如 "openrouter"）
    keywords: tuple[str, ...]        # 模型名关键词匹配（如 ("claude", "anthropic")）
    env_key: str                     # LiteLLM 环境变量（如 "OPENROUTER_API_KEY"）
    display_name: str = ""           # 显示名称（如 "OpenRouter"）

    # ===== 模型前缀处理 =====
    litellm_prefix: str = ""         # LiteLLM 前缀（如 "openrouter/"）
    skip_prefixes: tuple[str, ...] = ()  # 跳过前缀（避免重复）

    # ===== Gateway/本地检测 =====
    is_gateway: bool = False         # 是否为网关类型（可路由多个模型）
    is_local: bool = False           # 是否为本地部署
    detect_by_key_prefix: str = ""   # API Key 前缀检测（如 "sk-or-"）
    detect_by_base_keyword: str = "" # API Base URL 关键词检测
    default_api_base: str = ""       # 默认 Base URL

    # ===== OAuth 支持 =====
    is_oauth: bool = False           # 是否需要 OAuth 认证
    supports_prompt_caching: bool = False  # 是否支持提示缓存
```

#### 支持的提供商列表

```python
PROVIDERS: tuple[ProviderSpec, ...] = (
    # ========== Direct / No LiteLLM prefix ==========
    ProviderSpec(
        name="custom",
        keywords=(),
        env_key="",
        display_name="Custom",
        is_local=True,
    ),

    # ========== Gateways ==========
    ProviderSpec(
        name="openrouter",
        keywords=("openrouter",),
        env_key="OPENROUTER_API_KEY",
        display_name="OpenRouter",
        litellm_prefix="openrouter",
        skip_prefixes=("openrouter/",),
        is_gateway=True,
        detect_by_key_prefix="sk-or-",
        detect_by_base_keyword="openrouter",
    ),

    ProviderSpec(
        name="aihubmix",
        keywords=("aihubmix",),
        env_key="AIHUBMIX_API_KEY",
        display_name="AiHubMix",
        litellm_prefix="openai",
        is_gateway=True,
        strip_model_prefix=True,
    ),

    # ========== Standard Providers ==========
    ProviderSpec(
        name="anthropic",
        keywords=("claude", "anthropic"),
        env_key="ANTHROPIC_API_KEY",
        display_name="Anthropic",
        supports_prompt_caching=True,
    ),

    ProviderSpec(
        name="openai",
        keywords=("gpt", "o1", "o3", "chatgpt"),
        env_key="OPENAI_API_KEY",
        display_name="OpenAI",
    ),

    ProviderSpec(
        name="deepseek",
        keywords=("deepseek",),
        env_key="DEEPSEEK_API_KEY",
        display_name="DeepSeek",
        litellm_prefix="deepseek",
    ),

    ProviderSpec(
        name="gemini",
        keywords=("gemini",),
        env_key="GEMINI_API_KEY",
        display_name="Google AI Studio",
        litellm_prefix="gemini",
    ),

    # ========== 国内厂商 ==========
    ProviderSpec(
        name="dashscope",
        keywords=("qwen",),
        env_key="DASHSCOPE_API_KEY",
        display_name="Alibaba Qwen",
        litellm_prefix="dashscope",
        skip_prefixes=("dashscope/",),
    ),

    ProviderSpec(
        name="zhipu",
        keywords=("glm", "zhipu"),
        env_key="ZHIPUAI_API_KEY",
        display_name="Zhipu GLM",
        litellm_prefix="zhipu",
    ),

    ProviderSpec(
        name="moonshot",
        keywords=("moonshot", "kimi"),
        env_key="MOONSHOT_API_KEY",
        display_name="Moonshot Kimi",
        litellm_prefix="moonshot",
    ),

    # ========== 本地部署 ==========
    ProviderSpec(
        name="vllm",
        keywords=(),
        env_key="VLLM_API_KEY",
        display_name="vLLM (local)",
        litellm_prefix="hosted_vllm",
        is_local=True,
    ),

    # ========== OAuth Providers ==========
    ProviderSpec(
        name="openai_codex",
        keywords=("codex",),
        env_key="OPENAI_CODEX_API_KEY",
        display_name="OpenAI Codex",
        is_oauth=True,
    ),

    ProviderSpec(
        name="github_copilot",
        keywords=("copilot",),
        env_key="GITHUB_COPILOT_API_KEY",
        display_name="GitHub Copilot",
        litellm_prefix="github_copilot",
        is_oauth=True,
    ),
)
```

#### 匹配算法

```python
def find_by_model(model: str) -> ProviderSpec | None:
    """通过模型名关键词匹配提供商"""

    model_lower = model.lower()
    model_normalized = model_lower.replace("-", "_")

    # 只匹配标准提供商（非 Gateway/本地）
    std_specs = [s for s in PROVIDERS if not s.is_gateway and not s.is_local]

    # 1️⃣ 优先匹配显式前缀
    if "/" in model:
        model_prefix, _ = model.split("/", 1)
        normalized_prefix = model_prefix.replace("-", "_")

        for spec in std_specs:
            if normalized_prefix == spec.name.replace("-", "_"):
                return spec

    # 2️⃣ 匹配关键词
    for spec in std_specs:
        for kw in spec.keywords:
            if kw in model_lower or kw.replace("-", "_") in model_normalized:
                return spec

    return None


def find_gateway_by_config(api_key: str, api_base: str) -> ProviderSpec | None:
    """通过配置检测 Gateway 类型"""

    gateway_specs = [s for s in PROVIDERS if s.is_gateway]

    for spec in gateway_specs:
        # API Key 前缀检测
        if spec.detect_by_key_prefix and api_key.startswith(spec.detect_by_key_prefix):
            return spec

        # URL 关键词检测
        if spec.detect_by_base_keyword and spec.detect_by_base_keyword in api_base:
            return spec

    return None
```

---

### 4.4 Tool 工具系统

**位置**: `nanobot/agent/tools/`

nanobot 的工具系统基于**注册表模式**，支持动态注册和执行。

#### Tool 基类

```python
from abc import ABC, abstractmethod

class Tool(ABC):
    """工具基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述（LLM 可见）"""
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """参数 Schema（JSON Schema 格式）"""
        pass

    @abstractmethod
    async def execute(self, **params) -> str:
        """执行工具"""
        pass

    def validate_params(self, params: dict) -> list[str]:
        """验证参数，返回错误列表"""
        errors = []
        schema = self.parameters
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for field in required:
            if field not in params:
                errors.append(f"Missing required field: {field}")

        return errors

    def get_definition(self) -> dict:
        """获取 OpenAI 函数调用格式的定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }
```

#### ToolRegistry 注册表

```python
class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    @property
    def tool_names(self) -> list[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())

    def get_definitions(self) -> list[dict]:
        """获取所有工具定义（用于 LLM 调用）"""
        return [t.get_definition() for t in self._tools.values()]

    async def execute(self, name: str, params: dict) -> str:
        """执行工具"""
        _HINT = "\n\n[Analyze the error above and try a different approach.]"

        tool = self._tools.get(name)
        if not tool:
            available = ", ".join(self.tool_names)
            return f"Error: Tool '{name}' not found. Available: {available}"

        try:
            # 验证参数
            errors = tool.validate_params(params)
            if errors:
                return f"Error: Invalid parameters: {'; '.join(errors)}" + _HINT

            # 执行工具
            result = await tool.execute(**params)

            # 处理错误结果
            if isinstance(result, str) and result.startswith("Error"):
                return result + _HINT

            return result

        except Exception as e:
            return f"Error executing {name}: {str(e)}" + _HINT
```

#### 内置工具列表

| 工具名 | 功能 | 参数 |
|--------|------|------|
| `read_file` | 读取文件 | `path: str` |
| `write_file` | 写入文件 | `path: str, content: str` |
| `edit_file` | 编辑文件 | `path: str, old_text: str, new_text: str` |
| `list_dir` | 列出目录 | `path: str` |
| `exec` | 执行 Shell 命令 | `command: str, timeout: int` |
| `web_search` | 网络搜索 | `query: str` |
| `web_fetch` | 获取网页内容 | `url: str` |
| `message` | 发送消息到其他渠道 | `channel: str, chat_id: str, content: str` |
| `spawn` | 创建子代理 | `task: str` |
| `cron_add` | 添加定时任务 | `schedule: str, task: str` |

#### 文件读取工具示例

```python
class ReadFileTool(Tool):
    """读取文件工具"""

    def __init__(self, workspace: Path, allowed_dir: Path | None = None):
        self.workspace = workspace
        self.allowed_dir = allowed_dir or workspace

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file. Use this to examine existing files."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read (relative to workspace)"
                }
            },
            "required": ["path"]
        }

    async def execute(self, path: str) -> str:
        """执行文件读取"""
        try:
            # 路径安全检查
            full_path = self._resolve_path(path)

            if not full_path.exists():
                return f"Error: File not found: {path}"

            if not full_path.is_file():
                return f"Error: Not a file: {path}"

            # 读取文件
            content = full_path.read_text(encoding="utf-8")
            return content

        except Exception as e:
            return f"Error reading file: {str(e)}"

    def _resolve_path(self, path: str) -> Path:
        """解析并验证路径"""
        full_path = (self.workspace / path).resolve()

        # 防止路径遍历攻击
        if not str(full_path).startswith(str(self.allowed_dir.resolve())):
            raise ValueError(f"Path outside allowed directory: {path}")

        return full_path
```

---

### 4.5 Session 会话管理

**位置**: `nanobot/session/manager.py`

会话管理器负责**持久化对话历史**，支持跨重启保持状态。

#### Session 数据类

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class Session:
    """一个对话会话"""

    key: str                              # 会话键，格式: channel:chat_id
    messages: list[dict[str, Any]] = field(default_factory=list)  # 消息历史
    created_at: datetime = field(default_factory=datetime.now)    # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)    # 更新时间
    metadata: dict[str, Any] = field(default_factory=dict)        # 元数据
    last_consolidated: int = 0            # 已归档的消息数量
```

#### SessionManager 实现

```python
class SessionManager:
    """会话管理器，使用 JSONL 格式存储会话"""

    def __init__(self, sessions_dir: Path):
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Session] = {}

    def get_or_create(self, key: str) -> Session:
        """获取或创建会话"""
        if key in self._cache:
            return self._cache[key]

        session = self._load(key)
        if session is None:
            session = Session(key=key)

        self._cache[key] = session
        return session

    def save(self, session: Session) -> None:
        """保存会话到磁盘（JSONL 格式）"""
        session.updated_at = datetime.now()
        path = self._get_session_path(session.key)

        with open(path, "w", encoding="utf-8") as f:
            # 第一行：元数据
            metadata_line = {
                "_type": "metadata",
                "key": session.key,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "last_consolidated": session.last_consolidated
            }
            f.write(json.dumps(metadata_line, ensure_ascii=False) + "\n")

            # 后续行：消息
            for msg in session.messages:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")

    def _load(self, key: str) -> Session | None:
        """从磁盘加载会话"""
        path = self._get_session_path(key)
        if not path.exists():
            return None

        messages = []
        metadata = {}

        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                data = json.loads(line.strip())
                if i == 0 and data.get("_type") == "metadata":
                    metadata = data
                else:
                    messages.append(data)

        session = Session(
            key=key,
            messages=messages,
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat())),
            last_consolidated=metadata.get("last_consolidated", 0)
        )
        return session

    def _get_session_path(self, key: str) -> Path:
        """获取会话文件路径"""
        safe_key = key.replace(":", "_").replace("/", "_")
        return self.sessions_dir / f"{safe_key}.jsonl"
```

---

### 4.6 Memory 记忆系统

**位置**: `nanobot/agent/memory.py`

记忆系统实现**短期会话记忆**和**长期持久化记忆**的双层架构。

#### 记忆存储

```python
class MemoryStore:
    """长期记忆存储"""

    MEMORY_FILE = "MEMORY.md"
    HISTORY_FILE = "HISTORY.md"

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.memory_dir = workspace / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def get_memory_context(self) -> str | None:
        """获取记忆上下文"""
        memory_path = self.memory_dir / self.MEMORY_FILE

        if not memory_path.exists():
            return None

        content = memory_path.read_text(encoding="utf-8").strip()
        return content if content else None

    async def consolidate(
        self,
        session: Session,
        provider: LLMProvider,
        model: str,
        archive_all: bool = False,
        memory_window: int = 100,
    ) -> bool:
        """
        记忆整合：将短期记忆中的重要信息提取到长期记忆

        流程：
        1. 获取未归档的消息
        2. 调用 LLM 提取重要信息
        3. 更新 MEMORY.md
        4. 标记消息为已归档
        """
        unconsolidated = session.messages[session.last_consolidated:]

        if not unconsolidated:
            return False

        # 构建整合提示词
        current_memory = self.get_memory_context() or "(No existing memory)"

        prompt = f"""Review the following conversation and extract important information to remember.
Update the memory file with new facts, user preferences, or important context.

# Current Memory
{current_memory}

# Recent Conversation
{self._format_messages(unconsolidated)}

# Instructions
- Only add genuinely important, persistent information
- Remove outdated information
- Keep the memory concise and well-organized
- Return the updated memory content only"""

        # 调用 LLM
        response = await provider.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.1,
            max_tokens=4096,
        )

        # 更新记忆文件
        new_memory = response.content.strip()
        memory_path = self.memory_dir / self.MEMORY_FILE
        memory_path.write_text(new_memory, encoding="utf-8")

        # 更新会话归档标记
        if archive_all:
            session.last_consolidated = len(session.messages)
        else:
            session.last_consolidated = max(0, len(session.messages) - memory_window)

        return True
```

---

## 五、Channel 通道系统

**位置**: `nanobot/channels/`

Channel 系统实现了**多消息平台的统一接口**。

### 5.1 通道管理器

```python
class ChannelManager:
    """管理所有启用的通道"""

    def __init__(self, config: ChannelsConfig, bus: MessageBus):
        self.config = config
        self.bus = bus
        self._channels: dict[str, Channel] = {}

    async def start_all(self) -> None:
        """启动所有启用的通道"""
        if self.config.telegram.enabled:
            self._channels["telegram"] = TelegramChannel(
                config=self.config.telegram,
                outbound_callback=self.bus.publish_outbound
            )

        if self.config.discord.enabled:
            self._channels["discord"] = DiscordChannel(
                config=self.config.discord,
                outbound_callback=self.bus.publish_outbound
            )

        # ... 其他通道

        # 并行启动所有通道
        await asyncio.gather(*[
            ch.start(self.bus.publish_inbound)
            for ch in self._channels.values()
        ])
```

### 5.2 通道抽象接口

```python
from abc import ABC, abstractmethod

class Channel(ABC):
    """通道抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """通道名称"""
        pass

    @abstractmethod
    async def start(self, on_message: Callable) -> None:
        """启动通道，接收消息回调"""
        pass

    @abstractmethod
    async def send(self, chat_id: str, content: str, **kwargs) -> None:
        """发送消息到指定会话"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """停止通道"""
        pass
```

### 5.3 Telegram 通道实现

```python
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters

class TelegramChannel(Channel):
    """Telegram 通道实现"""

    def __init__(
        self,
        config: TelegramConfig,
        outbound_callback: Callable
    ):
        self.config = config
        self.outbound_callback = outbound_callback
        self.app: Application | None = None

    @property
    def name(self) -> str:
        return "telegram"

    async def start(self, on_message: Callable) -> None:
        """启动 Telegram Bot"""
        self.app = Application.builder().token(self.config.token).build()

        async def handle_update(update: Update, context):
            message = update.message
            if not message or not message.text:
                return

            # 权限检查
            user_id = str(message.from_user.id)
            if self.config.allow_from and user_id not in self.config.allow_from:
                return

            # 构造消息事件
            event = InboundEvent(
                channel="telegram",
                chat_id=str(message.chat_id),
                user_id=user_id,
                content=message.text,
                timestamp=datetime.now(),
            )

            await on_message(event)

        # 注册消息处理器
        self.app.add_handler(MessageHandler(filters.TEXT, handle_update))

        # 启动轮询
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

    async def send(self, chat_id: str, content: str, **kwargs) -> None:
        """发送消息"""
        bot = self.app.bot
        await bot.send_message(chat_id=int(chat_id), text=content)

    async def stop(self) -> None:
        """停止 Bot"""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
```

### 5.4 支持的通道一览

| 通道 | 协议 | 认证方式 | 特点 |
|------|------|----------|------|
| **Telegram** | HTTP Long Polling | Bot Token | 推荐，稳定可靠 |
| **Discord** | WebSocket | Bot Token + Intents | 支持群组提及 |
| **Slack** | Socket Mode | Bot Token + App Token | 支持线程回复 |
| **WhatsApp** | WebSocket Bridge | QR Code 配对 | 需要安装 bridge |
| **飞书** | WebSocket 长连接 | App ID + Secret | 无需公网 IP |
| **钉钉** | Stream Mode | App Key + Secret | 无需公网 IP |
| **QQ** | WebSocket | App ID + Secret | 仅支持私聊 |
| **Matrix** | Client-Server API | Access Token | 支持 E2EE |
| **Email** | IMAP/SMTP | 账号密码 | 定时轮询 |
| **Mochat** | Socket.IO | Claw Token | Agent 社交网络 |

---

## 六、消息总线（MessageBus）

**位置**: `nanobot/bus/queue.py`

MessageBus 是系统的**消息路由中心**，实现组件间的解耦通信。

### 6.1 消息总线实现

```python
import asyncio
from asyncio import Queue

class MessageBus:
    """
    消息总线：解耦通道和 Agent 的消息路由

    ┌──────────┐    Inbound    ┌──────────┐
    │ Channels │ ────────────> │  Agent   │
    │          │ <──────────── │  Loop    │
    └──────────┘   Outbound   └──────────┘
    """

    def __init__(self):
        # 入站队列：通道 → Agent
        self._inbound: Queue[InboundEvent] = Queue()

        # 出站队列：Agent → 通道
        self._outbound: Queue[OutboundEvent] = Queue()

        # 出站回调映射
        self._outbound_handlers: dict[str, Callable] = {}

    async def publish_inbound(self, event: InboundEvent) -> None:
        """发布入站消息"""
        await self._inbound.put(event)

    async def publish_outbound(self, event: OutboundEvent) -> None:
        """发布出站消息"""
        await self._outbound.put(event)

    async def receive_inbound(self) -> InboundEvent:
        """接收入站消息（阻塞）"""
        return await self._inbound.get()

    async def receive_outbound(self) -> OutboundEvent:
        """接收出站消息（阻塞）"""
        return await self._outbound.get()

    def register_outbound_handler(self, channel: str, handler: Callable) -> None:
        """注册出站处理器"""
        self._outbound_handlers[channel] = handler
```

### 6.2 事件类型

```python
@dataclass
class InboundEvent:
    """入站消息事件"""
    channel: str          # 来源通道
    chat_id: str          # 会话 ID
    user_id: str          # 用户 ID
    content: str          # 消息内容
    timestamp: datetime   # 时间戳
    media: list[dict] | None = None  # 媒体附件


@dataclass
class OutboundEvent:
    """出站消息事件"""
    channel: str          # 目标通道
    chat_id: str          # 会话 ID
    content: str          # 消息内容
    timestamp: datetime   # 时间戳
```

---

## 七、配置系统

**位置**: `nanobot/config/`

### 7.1 配置 Schema（Pydantic）

```python
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# ========== Agent 配置 ==========
class AgentDefaults(BaseModel):
    """Agent 默认配置"""
    workspace: str = "~/.nanobot/workspace"
    model: str = "anthropic/claude-opus-4-5"
    provider: str = "auto"
    max_tokens: int = 8192
    temperature: float = 0.1
    max_tool_iterations: int = 40
    memory_window: int = 100
    reasoning_effort: str | None = None


class AgentsConfig(BaseModel):
    """Agents 配置"""
    defaults: AgentDefaults = Field(default_factory=AgentDefaults)


# ========== Provider 配置 ==========
class ProviderConfig(BaseModel):
    """单个 Provider 配置"""
    api_key: str = ""
    api_base: str = ""
    models: list[str] = Field(default_factory=list)
    extra_headers: dict[str, str] = Field(default_factory=dict)


class ProvidersConfig(BaseModel):
    """所有 Providers 配置"""
    anthropic: ProviderConfig = Field(default_factory=ProviderConfig)
    openai: ProviderConfig = Field(default_factory=ProviderConfig)
    openrouter: ProviderConfig = Field(default_factory=ProviderConfig)
    deepseek: ProviderConfig = Field(default_factory=ProviderConfig)
    # ... 其他 providers


# ========== Channel 配置 ==========
class TelegramConfig(BaseModel):
    """Telegram 配置"""
    enabled: bool = False
    token: str = ""
    allow_from: list[str] = Field(default_factory=list)
    proxy: str | None = None


class SlackConfig(BaseModel):
    """Slack 配置"""
    enabled: bool = False
    mode: str = "socket"
    bot_token: str = ""
    app_token: str = ""
    reply_in_thread: bool = True
    group_policy: str = "mention"


class ChannelsConfig(BaseModel):
    """所有 Channels 配置"""
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    discord: DiscordConfig = Field(default_factory=DiscordConfig)
    slack: SlackConfig = Field(default_factory=SlackConfig)
    # ... 其他 channels


# ========== Tools 配置 ==========
class ToolsConfig(BaseModel):
    """工具配置"""
    restrict_to_workspace: bool = False
    mcp_servers: dict[str, dict] = Field(default_factory=dict)
    web: WebToolsConfig = Field(default_factory=WebToolsConfig)
    exec: ExecToolConfig = Field(default_factory=ExecToolConfig)


# ========== 根配置 ==========
class Config(BaseSettings):
    """根配置"""
    agents: AgentsConfig = Field(default_factory=AgentsConfig)
    channels: ChannelsConfig = Field(default_factory=ChannelsConfig)
    providers: ProvidersConfig = Field(default_factory=ProvidersConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)

    model_config = SettingsConfigDict(
        env_prefix="NANOBOT_",
        env_nested_delimiter="__",
    )
```

### 7.2 配置文件示例

```json
{
  "agents": {
    "defaults": {
      "workspace": "~/.nanobot/workspace",
      "model": "anthropic/claude-opus-4-5",
      "provider": "auto",
      "maxTokens": 8192,
      "temperature": 0.1
    }
  },
  "providers": {
    "anthropic": {
      "apiKey": "sk-ant-xxxxx"
    },
    "openrouter": {
      "apiKey": "sk-or-xxxxx"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "123456:ABC-xxx",
      "allowFrom": ["user_id_1"]
    },
    "slack": {
      "enabled": true,
      "botToken": "xoxb-xxx",
      "appToken": "xapp-xxx"
    }
  },
  "tools": {
    "restrictToWorkspace": true,
    "mcpServers": {
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
      }
    }
  }
}
```

---

## 八、数据流与架构

### 8.1 消息处理流程

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                  消息处理流程                                 │
└──────────────────────────────────────────────────────────────────────────────┘

1. 用户发送消息
   │
   ▼
2. Channel (Telegram/Discord/...) 接收消息
   │
   ▼
3. 发布 InboundEvent 到 MessageBus
   │
   ▼
4. AgentLoop 从 MessageBus 接收消息
   │
   ▼
5. 获取或创建 Session
   │
   ▼
6. ContextBuilder 构建上下文
   ├── 加载系统提示词 (Identity + Bootstrap Files)
   ├── 注入会话历史
   ├── 注入长期记忆 (MEMORY.md)
   └── 注入活跃技能
   │
   ▼
7. 调用 LiteLLMProvider
   │
   ▼
8. 解析 LLM 响应
   │
   ├── 有工具调用 ──> 执行工具 ──> 添加工具结果 ──> 返回步骤 7
   │
   └── 无工具调用 ──> 继续
   │
   ▼
9. 保存会话到磁盘
   │
   ▼
10. 返回响应到 MessageBus
    │
    ▼
11. Channel 发送消息给用户
```

### 8.2 设计模式总结

| 模式 | 应用场景 | 示例 |
|------|----------|------|
| **注册表模式** | Provider、Tool、Channel 的管理 | `PROVIDERS`, `ToolRegistry` |
| **策略模式** | 不同 Channel 的实现 | `TelegramChannel`, `DiscordChannel` |
| **观察者模式** | 消息事件分发 | `MessageBus` |
| **工厂模式** | Channel 实例创建 | `ChannelManager` |
| **模板方法模式** | Tool 执行流程 | `Tool.execute()` |
| **单例模式** | 配置管理 | `load_config()` |
| **迭代器模式** | Agent 循环 | `_run_agent_loop()` |

---

## 九、代码示例

### 9.1 最小可运行示例

```python
"""
nanobot 最小可运行示例
展示如何使用 nanobot 进行一次简单的对话
"""

import asyncio
from pathlib import Path

from nanobot.config.loader import load_config
from nanobot.bus.queue import MessageBus
from nanobot.providers.litellm_provider import LiteLLMProvider
from nanobot.agent.loop import AgentLoop


async def main():
    # 1. 加载配置
    config = load_config()

    # 2. 创建消息总线
    bus = MessageBus()

    # 3. 创建 LLM Provider
    provider = LiteLLMProvider(
        api_key=config.providers.openrouter.api_key,  # 或其他 provider
        api_base=config.providers.openrouter.api_base,
        default_model=config.agents.defaults.model,
    )

    # 4. 创建 Agent Loop
    agent = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=Path(config.agents.defaults.workspace).expanduser(),
        model=config.agents.defaults.model,
        max_iterations=10,  # 限制迭代次数
    )

    # 5. 发送消息
    result = await agent.process_direct(
        content="Hello! What can you help me with?",
        session_key="demo:example",
        channel="demo",
    )

    print(f"Response: {result}")


if __name__ == "__main__":
    asyncio.run(main())
```

### 9.2 添加自定义工具

```python
"""
添加自定义工具示例
"""

from nanobot.agent.tools.registry import Tool, ToolRegistry


class WeatherTool(Tool):
    """天气查询工具"""

    @property
    def name(self) -> str:
        return "get_weather"

    @property
    def description(self) -> str:
        return "Get the current weather for a city"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'Beijing'"
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["city"]
        }

    async def execute(self, city: str, unit: str = "celsius") -> str:
        """执行天气查询（示例返回模拟数据）"""
        # 实际应用中应该调用天气 API
        weather_data = {
            "Beijing": {"temp": 25, "condition": "Sunny"},
            "Shanghai": {"temp": 28, "condition": "Cloudy"},
        }

        data = weather_data.get(city, {"temp": 20, "condition": "Unknown"})

        temp = data["temp"]
        if unit == "fahrenheit":
            temp = temp * 9 / 5 + 32

        return f"Weather in {city}: {temp}°{unit[0].upper()}, {data['condition']}"


# 注册工具
registry = ToolRegistry()
registry.register(WeatherTool())

# 获取工具定义（用于 LLM 调用）
definitions = registry.get_definitions()
print(definitions)
# [{'type': 'function', 'function': {'name': 'get_weather', ...}}]
```

### 9.3 流式处理示例

```python
"""
流式处理示例
"""

import asyncio
from nanobot.agent.loop import AgentLoop


async def stream_example():
    """展示流式处理的用法"""

    agent = AgentLoop(...)

    # 流式处理
    async for event in agent.process_stream(
        content="Write a short poem about AI",
        session_key="demo:stream",
        channel="demo",
    ):
        event_type = event.get("type")

        if event_type == "content":
            # 增量内容
            print(event["content"], end="", flush=True)

        elif event_type == "tool_hint":
            # 工具调用提示
            print(f"\n[Tool: {event['content']}]")

        elif event_type == "done":
            # 完成信号
            print("\n\n[Done]")

        elif event_type == "error":
            # 错误处理
            print(f"\nError: {event['content']}")


asyncio.run(stream_example())
```

### 9.4 MCP 工具集成示例

```python
"""
MCP (Model Context Protocol) 工具集成示例
"""

# 配置 MCP 服务器
config = {
    "tools": {
        "mcpServers": {
            # 本地 stdio 模式
            "filesystem": {
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    "/path/to/allowed/directory"
                ]
            },
            # 远程 HTTP 模式
            "custom-tools": {
                "url": "https://api.example.com/mcp/",
                "headers": {
                    "Authorization": "Bearer your-api-key"
                },
                "toolTimeout": 60  # 超时时间（秒）
            }
        }
    }
}

# MCP 工具会在 AgentLoop 初始化时自动发现和注册
agent = AgentLoop(
    ...,
    mcp_servers=config["tools"]["mcpServers"],
)

# 现在 Agent 可以使用 MCP 服务器提供的工具了
```

---

## 十、扩展开发指南

### 10.1 添加新的 LLM Provider

**步骤 1**: 在 `nanobot/providers/registry.py` 中添加 `ProviderSpec`

```python
PROVIDERS = (
    # ... 现有 providers

    ProviderSpec(
        name="my_provider",
        keywords=("my_model", "myprovider"),
        env_key="MY_PROVIDER_API_KEY",
        display_name="My Provider",
        litellm_prefix="my_provider",  # LiteLLM 前缀
        skip_prefixes=("my_provider/",),
    ),
)
```

**步骤 2**: 在 `nanobot/config/schema.py` 中添加配置字段

```python
class ProvidersConfig(BaseModel):
    # ... 现有字段
    my_provider: ProviderConfig = Field(default_factory=ProviderConfig)
```

**步骤 3**: 在配置文件中添加 API Key

```json
{
  "providers": {
    "my_provider": {
      "apiKey": "your-api-key"
    }
  }
}
```

### 10.2 添加新的 Channel

**步骤 1**: 创建 Channel 实现类

```python
# nanobot/channels/my_channel.py

from nanobot.channels.base import Channel
from nanobot.bus.events import InboundEvent

class MyChannel(Channel):
    """自定义通道实现"""

    def __init__(self, config: MyChannelConfig, outbound_callback: Callable):
        self.config = config
        self.outbound_callback = outbound_callback

    @property
    def name(self) -> str:
        return "my_channel"

    async def start(self, on_message: Callable) -> None:
        """启动通道"""
        # 初始化连接
        # 注册消息处理器
        pass

    async def send(self, chat_id: str, content: str, **kwargs) -> None:
        """发送消息"""
        pass

    async def stop(self) -> None:
        """停止通道"""
        pass
```

**步骤 2**: 添加配置 Schema

```python
# nanobot/config/schema.py

class MyChannelConfig(BaseModel):
    enabled: bool = False
    api_key: str = ""
    allow_from: list[str] = Field(default_factory=list)


class ChannelsConfig(BaseModel):
    # ... 现有字段
    my_channel: MyChannelConfig = Field(default_factory=MyChannelConfig)
```

**步骤 3**: 在 ChannelManager 中注册

```python
# nanobot/channels/manager.py

async def start_all(self) -> None:
    # ... 现有通道

    if self.config.my_channel.enabled:
        from nanobot.channels.my_channel import MyChannel
        self._channels["my_channel"] = MyChannel(
            config=self.config.my_channel,
            outbound_callback=self.bus.publish_outbound
        )
```

### 10.3 添加新的技能（Skill）

**步骤 1**: 创建技能目录

```bash
mkdir -p ~/.nanobot/workspace/skills/my_skill
```

**步骤 2**: 创建 SKILL.md 文件

```markdown
---
name: my_skill
description: A custom skill for doing something useful
always: false
---

# My Custom Skill

## Description
This skill helps the agent to perform specific tasks.

## Instructions
When the user asks about X, you should:
1. First do Y
2. Then do Z

## Example Usage
User: "Help me with X"
Assistant: "I'll use my_skill to help you..."
```

**步骤 3**: 技能会自动被 Agent 加载和使用

---

## 总结

### 项目优势

| 优势 | 说明 |
|------|------|
| 🪶 **超轻量级** | 仅 ~4000 行核心代码 |
| 🧩 **模块化设计** | 清晰的模块边界，低耦合 |
| 🔌 **多渠道支持** | 10+ 消息平台集成 |
| 🤖 **多 LLM 支持** | 17+ LLM 提供商 |
| ⚡ **异步架构** | 全异步设计，高性能 |
| 🔧 **可扩展性** | Skill 系统、MCP 工具支持 |

### 适用场景

- 🔰 **学习 AI Agent 架构** - 清晰的代码结构适合学习
- 🤖 **个人 AI 助手** - 快速部署个人助手
- 💬 **多渠道客服机器人** - 统一接入多个平台
- ⚙️ **自动化任务执行** - Shell 命令、文件操作等
- 🔔 **定时提醒和任务** - Cron 和 Heartbeat 支持
- 📚 **研究实验** - 易于修改和扩展

---

## 十一、架构设计思想与原理

### 11.1 核心设计哲学

nanobot 的设计遵循 **"少即是多"（Less is More）** 的核心哲学，其设计目标可以总结为：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        nanobot 设计哲学                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │  Simplicity │     │ Modularity  │     │ Extensibility│                 │
│   │   简洁性    │     │   模块化    │     │   可扩展性   │                  │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                  │
│          │                   │                   │                         │
│          ▼                   ▼                   ▼                         │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    核心设计原则                                  │      │
│   │                                                                  │      │
│   │  1. 单一职责：每个模块只做一件事，并做好它                        │      │
│   │  2. 依赖倒置：高层模块不依赖低层模块，两者都依赖抽象              │      │
│   │  3. 接口隔离：使用小而精的接口，而非大而全的接口                  │      │
│   │  4. 组合优于继承：通过组合实现功能扩展                           │      │
│   │  5. 约定优于配置：合理的默认值减少配置负担                       │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 11.1.1 极简主义（Minimalism）

nanobot 的核心 Agent 代码仅约 **4,000 行**，这并非偶然，而是刻意的设计选择：

```python
# 设计对比
OPENCLAW_LINES = 430_000      # OpenClaw 代码行数
NANOBOT_LINES = 4_000         # nanobot 核心代码行数
REDUCTION = 99.1%              # 减少比例

# 设计理念：保留 1% 的核心功能，覆盖 99% 的使用场景
```

**实现手段**：
1. **删除冗余抽象**：避免过度工程化，只保留必要的抽象层
2. **利用现有库**：使用 LiteLLM 而非自己实现多 LLM 适配
3. **扁平化层次**：减少继承深度，使用组合替代
4. **移除中间层**：直接暴露核心 API，减少包装层

#### 11.1.2 关注点分离（Separation of Concerns）

nanobot 将系统清晰地划分为四个核心关注点：

```
┌────────────────────────────────────────────────────────────────────┐
│                        关注点分离                                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────┐│
│  │   通信层     │  │   核心层     │  │   能力层     │  │ 存储层  ││
│  │  Channels    │  │  AgentLoop   │  │   Tools      │  │ Session ││
│  │  MessageBus  │  │  Context     │  │   Skills     │  │ Memory  ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────┘│
│                                                                    │
│  职责：            职责：            职责：            职责：       │
│  - 消息收发       - LLM 交互       - 工具执行       - 状态持久化  │
│  - 平台适配       - 上下文管理     - 技能加载       - 历史记录    │
│  - 事件路由       - 循环控制       - MCP 集成       - 记忆整合    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### 11.2 Agent 架构原理

#### 11.2.1 ReAct 模式（Reasoning + Acting）

nanobot 采用 **ReAct（Reasoning and Acting）** 模式作为 Agent 的核心推理框架：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ReAct 循环原理                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐         │
│    │  User   │ ───> │  LLM    │ ───> │  Tool   │ ───> │  LLM    │ ───> ...│
│    │ Input   │      │ Reason  │      │ Execute │      │ Reflect │         │
│    └─────────┘      └─────────┘      └─────────┘      └─────────┘         │
│                          │                                    │            │
│                          ▼                                    ▼            │
│                    ┌───────────┐                       ┌───────────┐       │
│                    │ Thought:  │                       │ Response  │       │
│                    │ "I need   │                       │ to User   │       │
│                    │  to..."   │                       │           │       │
│                    └───────────┘                       └───────────┘       │
│                          │                                                    │
│                          ▼                                                    │
│                    ┌───────────┐                                             │
│                    │ Action:   │                                             │
│                    │ tool_name │                                             │
│                    │ {args}    │                                             │
│                    └───────────┘                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**ReAct 循环的代码实现**：

```python
async def _run_agent_loop(self, messages, on_progress):
    """ReAct 循环实现"""

    while iteration < self.max_iterations:
        # ========== Reasoning 阶段 ==========
        # LLM 思考：分析当前状态，决定下一步行动
        response = await self.provider.chat(
            messages=messages,
            tools=self.tools.get_definitions(),  # 可用工具列表
        )

        if response.has_tool_calls:
            # ========== Acting 阶段 ==========
            # 1. Thought（思考）：response.content 包含 LLM 的推理过程
            # 2. Action（行动）：执行工具调用

            for tool_call in response.tool_calls:
                # 执行工具
                result = await self.tools.execute(
                    tool_call.name,
                    tool_call.arguments
                )

                # 添加观察结果（Observation）到上下文
                messages = self.context.add_tool_result(
                    messages,
                    tool_call.id,
                    tool_call.name,
                    result
                )

            # 继续循环，让 LLM 基于观察结果进行下一轮推理
            continue

        else:
            # 无需行动，返回最终答案
            return response.content
```

#### 11.2.2 上下文管理策略

nanobot 使用**分层上下文管理**策略，平衡 token 消耗和上下文完整性：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        上下文层次结构                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Layer 1: System Prompt (始终存在)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ # Identity                                                           │   │
│  │ - 角色定义                                                           │   │
│  │ - 运行时信息（时间、工作目录）                                         │   │
│  │ - 行为准则                                                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Layer 2: Bootstrap Files (按需加载)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - AGENTS.md: Agent 行为定义                                          │   │
│  │ - SOUL.md: 核心人格                                                  │   │
│  │ - USER.md: 用户偏好                                                  │   │
│  │ - TOOLS.md: 工具使用指南                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Layer 3: Long-term Memory (MEMORY.md)                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - 用户个人信息                                                       │   │
│  │ - 重要偏好和习惯                                                     │   │
│  │ - 持久化的对话要点                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Layer 4: Active Skills (按需激活)                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - always=true 的技能会自动注入                                        │   │
│  │ - 其他技能按需加载                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Layer 5: Session History (滑动窗口)                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ - 最近的 N 条消息（默认 100 条）                                       │   │
│  │ - 超过窗口的消息会被整合到 Memory                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**上下文构建代码**：

```python
def build_messages_for_llm(self, session: Session, user_input: str) -> list[dict]:
    """构建发送给 LLM 的消息列表"""

    messages = []

    # 1. 系统提示词（始终存在）
    system_prompt = self.build_system_prompt()
    messages.append({"role": "system", "content": system_prompt})

    # 2. 会话历史（滑动窗口）
    history = session.get_history(max_messages=self.memory_window)
    messages.extend(history)

    # 3. 当前用户输入
    messages.append({"role": "user", "content": user_input})

    return messages
```

#### 11.2.3 工具调用机制

nanobot 的工具系统基于 **OpenAI Function Calling** 标准，但做了简化：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        工具调用流程                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │
│  │   LLM   │ ──> │ Tool Calls  │ ──> │  Registry   │ ──> │   Execute   │  │
│  │ Response│     │   Parse     │     │   Lookup    │     │   Tool      │  │
│  └─────────┘     └─────────────┘     └─────────────┘     └─────────────┘  │
│       │                                                         │          │
│       │  {                                                      │          │
│       │    "name": "read_file",                                 │          │
│       │    "arguments": {                                       │          │
│       │      "path": "test.py"                                  │          │
│       │    }                                                    │          │
│       │  }                                                      │          │
│       ▼                                                         ▼          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                           Tool Result                               │  │
│  │                                                                     │  │
│  │  {                                                                  │  │
│  │    "role": "tool",                                                  │  │
│  │    "tool_call_id": "call_123",                                      │  │
│  │    "name": "read_file",                                             │  │
│  │    "content": "# file contents..."                                  │  │
│  │  }                                                                  │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**工具定义格式**：

```python
# OpenAI Function Calling 格式
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read"
                }
            },
            "required": ["path"]
        }
    }
}
```

### 11.3 消息总线设计

#### 11.3.1 事件驱动架构

nanobot 使用**事件驱动架构**解耦 Channel 和 Agent：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        事件驱动架构                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    ┌─────────────────────────────────┐                      │
│                    │         MessageBus              │                      │
│                    │                                 │                      │
│                    │   ┌─────────────────────────┐   │                      │
│                    │   │     Inbound Queue       │   │                      │
│                    │   │  [Event] → [Event] → ...│   │                      │
│                    │   └─────────────────────────┘   │                      │
│                    │                                 │                      │
│                    │   ┌─────────────────────────┐   │                      │
│                    │   │     Outbound Queue      │   │                      │
│                    │   │  [Event] → [Event] → ...│   │                      │
│                    │   └─────────────────────────┘   │                      │
│                    └─────────────────────────────────┘                      │
│                              ▲                     │                        │
│                              │                     ▼                        │
│    ┌──────────┐    ┌──────────┐          ┌──────────┐    ┌──────────┐     │
│    │ Telegram │    │ Discord  │          │  Agent   │    │   Slack  │     │
│    │ Channel  │    │ Channel  │          │   Loop   │    │  Channel │     │
│    └──────────┘    └──────────┘          └──────────┘    └──────────┘     │
│         │               │                      │               │           │
│         └───────────────┼──────────────────────┼───────────────┘           │
│                         │                      │                            │
│                         ▼                      ▼                            │
│                   publish_inbound()     process() → publish_outbound()     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 11.3.2 异步消息处理

```python
class MessageBus:
    """异步消息总线实现"""

    def __init__(self):
        # 使用 asyncio.Queue 实现生产者-消费者模式
        self._inbound: asyncio.Queue[InboundEvent] = asyncio.Queue()
        self._outbound: asyncio.Queue[OutboundEvent] = asyncio.Queue()

    async def run_forever(self, agent: AgentLoop, channels: dict[str, Channel]):
        """主事件循环"""

        async def process_inbound():
            """处理入站消息"""
            while True:
                event = await self._inbound.get()
                # 分发给 Agent 处理
                response = await agent.process(event)
                # 发布出站消息
                await self._outbound.put(response)

        async def process_outbound():
            """处理出站消息"""
            while True:
                event = await self._outbound.get()
                # 分发给对应 Channel 发送
                channel = channels[event.channel]
                await channel.send(event.chat_id, event.content)

        # 并行运行两个处理器
        await asyncio.gather(
            process_inbound(),
            process_outbound(),
        )
```

### 11.4 记忆系统设计

#### 11.4.1 双层记忆架构

nanobot 实现了**短期记忆 + 长期记忆**的双层架构：

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        双层记忆架构                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Short-term Memory (Session)                     │   │
│  │                                                                       │   │
│  │  存储：内存 + JSONL 文件                                              │   │
│  │  内容：完整的对话历史                                                 │   │
│  │  容量：滑动窗口（默认最近 100 条消息）                                 │   │
│  │  特点：精确、完整、但容量有限                                          │   │
│  │                                                                       │   │
│  │  [User] ──> [Assistant] ──> [Tool] ──> [Tool Result] ──> ...        │   │
│  │                                                                       │   │
│  └───────────────────────────────┬─────────────────────────────────────┘   │
│                                  │                                         │
│                                  │ Consolidate (整合)                      │
│                                  │ (当超过窗口大小时触发)                   │
│                                  ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Long-term Memory (MEMORY.md)                    │   │
│  │                                                                       │   │
│  │  存储：Markdown 文件                                                  │   │
│  │  内容：LLM 提取的重要信息、用户偏好、关键事实                          │   │
│  │  容量：无限制（但建议保持简洁）                                        │   │
│  │  特点：持久化、可编辑、人类可读                                        │   │
│  │                                                                       │   │
│  │  # User Profile                                                      │   │
│  │  - Name: Alice                                                       │   │
│  │  - Language: Chinese, English                                        │   │
│  │  - Preferences:                                                      │   │
│  │    - Prefers concise responses                                       │   │
│  │    - Uses dark mode                                                  │   │
│  │  - Important dates:                                                  │   │
│  │    - Birthday: 1990-05-15                                            │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 11.4.2 记忆整合算法

```python
async def consolidate_memory(
    session: Session,
    provider: LLMProvider,
    memory_store: MemoryStore,
) -> None:
    """
    记忆整合算法：将短期记忆中的关键信息提取到长期记忆

    触发条件：
    1. 会话历史超过 memory_window
    2. 用户显式请求
    3. Agent 主动判断需要记住某些信息
    """

    # 1. 获取当前长期记忆
    current_memory = memory_store.get_memory_context() or ""

    # 2. 获取未整合的短期记忆
    unconsolidated = session.messages[session.last_consolidated:]

    # 3. 构建整合提示词
    prompt = f"""You are a memory consolidation system.

Current Memory:
{current_memory}

New Information from Recent Conversation:
{format_messages(unconsolidated)}

Task: Update the memory file with new important information.
Rules:
1. Only add genuinely important, persistent information
2. Remove outdated or incorrect information
3. Keep the memory concise and well-organized
4. Use Markdown format
5. Do NOT include temporary or context-specific details

Return ONLY the updated memory content."""

    # 4. 调用 LLM 进行整合
    response = await provider.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,  # 低温度，确保一致性
    )

    # 5. 更新长期记忆文件
    memory_store.save_memory(response.content)

    # 6. 更新整合标记
    session.last_consolidated = len(session.messages) - memory_window
```

### 11.5 LLM Provider 抽象

#### 11.5.1 统一接口设计

nanobot 通过 **LiteLLM** 实现对不同 LLM 的统一抽象：

```python
class LLMProvider(ABC):
    """LLM 提供商抽象基类"""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """发送聊天请求"""
        pass


class LiteLLMProvider(LLMProvider):
    """基于 LiteLLM 的统一实现"""

    async def chat(self, messages, tools=None, model=None, **kwargs):
        # LiteLLM 统一了不同提供商的 API 差异
        response = await litellm.acompletion(
            model=self._resolve_model(model),
            messages=messages,
            tools=tools,
            temperature=kwargs.get("temperature", 0.1),
            max_tokens=kwargs.get("max_tokens", 4096),
        )

        return self._normalize_response(response)
```

#### 11.5.2 Provider 自动检测

```python
def detect_provider(model: str, config: Config) -> ProviderSpec:
    """
    自动检测应该使用的 Provider

    检测优先级：
    1. 显式配置的 provider
    2. 模型名前缀 (e.g., "openrouter/claude-...")
    3. 模型名关键词 (e.g., "claude" -> Anthropic)
    4. API Key 前缀检测 (e.g., "sk-or-" -> OpenRouter)
    5. 默认 Provider
    """

    # 1. 显式配置
    if config.agents.defaults.provider != "auto":
        return find_by_name(config.agents.defaults.provider)

    # 2. 模型名前缀
    if "/" in model:
        prefix = model.split("/")[0]
        if spec := find_by_name(prefix):
            return spec

    # 3. 模型名关键词
    if spec := find_by_model(model):
        return spec

    # 4. API Key 前缀检测
    for provider_config in config.providers:
        if api_key := provider_config.api_key:
            if spec := find_by_key_prefix(api_key):
                return spec

    # 5. 默认
    return PROVIDERS[0]
```

---

## 十二、nanobot vs OpenClaw 对比分析

### 12.1 项目定位对比

| 维度 | nanobot | OpenClaw |
|------|---------|----------|
| **定位** | 研究型、轻量级 | 生产型、全功能 |
| **目标用户** | 研究者、开发者、学习者 | 企业用户、重度用户 |
| **代码量** | ~4,000 行（核心） | ~430,000 行 |
| **学习曲线** | 低（几小时掌握） | 高（数周掌握） |
| **部署复杂度** | 简单（pip install） | 复杂（多服务依赖） |

### 12.2 架构对比

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        架构对比图                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  nanobot (扁平化架构)                      OpenClaw (分层架构)              │
│                                                                             │
│  ┌───────────────────────┐                ┌───────────────────────┐       │
│  │        CLI            │                │      Web Frontend     │       │
│  └───────────┬───────────┘                └───────────┬───────────┘       │
│              │                                        │                    │
│              ▼                                        ▼                    │
│  ┌───────────────────────┐                ┌───────────────────────┐       │
│  │     MessageBus        │                │      API Gateway      │       │
│  │  (asyncio.Queue)      │                │      (FastAPI)        │       │
│  └───────────┬───────────┘                └───────────┬───────────┘       │
│              │                                        │                    │
│              ▼                                        ▼                    │
│  ┌───────────────────────┐                ┌───────────────────────┐       │
│  │     AgentLoop         │                │    Message Queue      │       │
│  │  (单文件 ~300 行)     │                │     (Redis/RabbitMQ)  │       │
│  └───────────┬───────────┘                └───────────┬───────────┘       │
│              │                                        │                    │
│              ▼                                        ▼                    │
│  ┌───────────────────────┐                ┌───────────────────────┐       │
│  │  LiteLLM (第三方库)   │                │    LLM Gateway        │       │
│  └───────────────────────┘                │    (自研适配层)       │       │
│                                           └───────────┬───────────┘       │
│                                                       │                    │
│                                                       ▼                    │
│                                           ┌───────────────────────┐       │
│                                           │    Agent Orchestrator │       │
│                                           │    (多 Agent 协调)    │       │
│                                           └───────────────────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.3 功能对比

| 功能模块 | nanobot | OpenClaw | 对比说明 |
|----------|---------|----------|----------|
| **LLM 支持** | 通过 LiteLLM（17+ 提供商） | 自研适配层 | nanobot 更简洁，OpenClaw 更可控 |
| **消息渠道** | 10+（内置） | 15+（内置 + 插件） | 相似覆盖面 |
| **工具系统** | 简单注册表 | 复杂插件系统 | nanobot 更易扩展 |
| **记忆系统** | 文件存储（MEMORY.md） | 向量数据库 + 图数据库 | OpenClaw 更强大 |
| **会话管理** | JSONL 文件 | 数据库（PostgreSQL） | nanobot 更简单 |
| **多 Agent** | 基础 Subagent | 完整多 Agent 协作 | OpenClaw 更完善 |
| **定时任务** | 简单 Cron | 分布式调度 | 相似功能 |
| **MCP 支持** | 原生支持 | 需要插件 | nanobot 更现代 |
| **Web UI** | 无（通过 NanoClaw 项目） | 内置完整 Web UI | OpenClaw 更完整 |

### 12.4 代码结构对比

```
nanobot/                              OpenClaw/
├── agent/                           ├── core/
│   ├── loop.py         (~300 行)    │   ├── agent/          (~5000 行)
│   ├── context.py      (~200 行)    │   ├── orchestrator/   (~3000 行)
│   ├── memory.py       (~150 行)    │   ├── memory/         (~4000 行)
│   └── tools/                       │   └── tools/          (~8000 行)
│       └── *.py        (~500 行)    │
├── channels/                        ├── channels/
│   └── *.py           (~2000 行)    │   └── */              (~15000 行)
├── providers/                       ├── llm/
│   └── registry.py    (~150 行)     │   └── providers/      (~10000 行)
├── config/                          ├── config/
│   └── schema.py      (~500 行)     │   └── */              (~5000 行)
├── session/                         ├── storage/
│   └── manager.py     (~150 行)     │   └── */              (~8000 行)
└── cli/                             ├── api/
    └── commands.py    (~200 行)     │   └── routes/         (~10000 行)
                                     ├── web/
                                     │   └── frontend/       (~50000 行)
                                     └── plugins/
                                         └── */              (~100000 行)

总计: ~4,000 行核心代码              总计: ~430,000 行代码
```

### 12.5 技术选型对比

| 技术领域 | nanobot | OpenClaw | 设计考量 |
|----------|---------|----------|----------|
| **LLM 抽象** | LiteLLM（第三方） | 自研适配层 | nanobot 减少维护负担 |
| **数据存储** | 文件系统（JSONL/MD） | PostgreSQL + Redis | nanobot 零依赖，OpenClaw 高性能 |
| **消息队列** | asyncio.Queue | Redis/RabbitMQ | nanobot 单进程，OpenClaw 分布式 |
| **配置管理** | Pydantic + JSON | YAML + 环境变量 | 相似复杂度 |
| **日志系统** | Loguru | 自定义日志框架 | nanobot 更简洁 |
| **异步框架** | asyncio | asyncio + Celery | OpenClaw 支持后台任务 |
| **API 框架** | 无（CLI 为主） | FastAPI | OpenClaw 面向服务 |

### 12.6 适用场景对比

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        适用场景对比                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  nanobot 最适合：                         OpenClaw 最适合：                  │
│                                                                             │
│  ✅ 个人 AI 助手                          ✅ 企业级客服系统                  │
│  ✅ 研究实验和原型开发                    ✅ 高并发生产环境                  │
│  ✅ 学习 Agent 架构                      ✅ 多租户 SaaS 服务                │
│  ✅ 快速部署和迭代                       ✅ 复杂工作流编排                  │
│  ✅ 资源受限环境                         ✅ 需要完整 Web UI                 │
│  ✅ 定制化开发                           ✅ 大规模数据处理                  │
│                                                                             │
│  nanobot 不适合：                         OpenClaw 不适合：                  │
│                                                                             │
│  ❌ 高并发生产环境                        ❌ 快速原型开发                    │
│  ❌ 需要完整 Web UI                      ❌ 学习 Agent 架构                 │
│  ❌ 多租户场景                           ❌ 资源受限环境                    │
│  ❌ 复杂多 Agent 协作                    ❌ 简单个人使用                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 12.7 性能对比

| 指标 | nanobot | OpenClaw |
|------|---------|----------|
| **启动时间** | < 1 秒 | 5-10 秒 |
| **内存占用** | ~50 MB | ~500 MB |
| **响应延迟** | 低（单进程） | 中（多服务） |
| **并发能力** | 有限 | 高 |
| **扩展性** | 垂直扩展 | 水平扩展 |

### 12.8 学习成本对比

| 学习内容 | nanobot | OpenClaw |
|----------|---------|----------|
| **基础使用** | 30 分钟 | 2 小时 |
| **理解架构** | 2 小时 | 1 周 |
| **二次开发** | 1 天 | 1-2 周 |
| **完整掌握** | 1 周 | 1-2 月 |

### 12.9 迁移建议

如果你正在考虑从 OpenClaw 迁移到 nanobot（或反之），以下是一些建议：

#### 从 OpenClaw 迁移到 nanobot

```python
# 1. 配置迁移
# OpenClaw: config.yaml
# nanobot: config.json

# 2. 记忆迁移
# OpenClaw: 向量数据库 → 导出为文本
# nanobot: 直接写入 MEMORY.md

# 3. 工具迁移
# OpenClaw: 插件系统
# nanobot: Tool 基类继承

# 4. 渠道迁移
# 大部分渠道配置相似，只需调整字段名
```

#### 从 nanobot 迁移到 OpenClaw

```python
# 1. 需要设置额外的服务
# - PostgreSQL
# - Redis
# - Web 前端

# 2. 数据迁移
# MEMORY.md → 向量数据库
# JSONL sessions → PostgreSQL

# 3. 工具迁移
# Tool 基类 → OpenClaw 插件系统
```

---

## 十三、总结与展望

### 13.1 nanobot 的核心价值

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        nanobot 核心价值                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1️⃣ 教育价值                                                               │
│     - 清晰的代码结构，适合学习 Agent 架构                                   │
│     - 极简实现，每行代码都有意义                                            │
│     - 无需理解复杂的框架和依赖                                              │
│                                                                             │
│  2️⃣ 研究价值                                                               │
│     - 快速原型验证                                                          │
│     - 算法实验和迭代                                                        │
│     - 论文复现的起点                                                        │
│                                                                             │
│  3️⃣ 实用价值                                                               │
│     - 个人 AI 助手的最佳选择                                                │
│     - 低资源消耗，适合个人服务器                                            │
│     - 快速部署，即装即用                                                    │
│                                                                             │
│  4️⃣ 社区价值                                                               │
│     - 开源贡献的友好入口                                                    │
│     - 代码审查和改进的典范                                                  │
│     - 可扩展的生态系统                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 13.2 关键设计决策回顾

| 设计决策 | 理由 |
|----------|------|
| **使用 LiteLLM** | 避免重复造轮子，自动获得新模型支持 |
| **文件存储** | 零依赖，易于备份和迁移 |
| **asyncio.Queue** | 单进程足够，避免消息队列复杂性 |
| **Pydantic 配置** | 类型安全 + 验证 + IDE 支持 |
| **Tool 注册表** | 简单灵活，易于扩展 |
| **JSONL 会话** | 流式读写，易于调试 |
| **Markdown 记忆** | 人类可读，便于编辑 |

### 13.3 未来发展方向

根据项目 Roadmap 和社区讨论，nanobot 可能的发展方向：

1. **多模态支持**：图像、语音、视频处理
2. **长期记忆增强**：向量数据库集成（可选）
3. **更好的推理能力**：多步规划和反思
4. **更多集成**：日历、邮件、文档系统
5. **自我改进**：从反馈中学习和优化

---

## 十四、提示词（Prompt）设计深度解析

### 14.1 提示词工程在 Agent 中的重要性

提示词是 AI Agent 的"灵魂"，它定义了 Agent 的：
- **身份认知**：Agent 是谁，扮演什么角色
- **行为边界**：能做什么，不能做什么
- **决策逻辑**：如何思考和选择行动
- **输出风格**：如何与用户交流

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      提示词在 Agent 系统中的位置                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                          ┌─────────────────────┐                            │
│                          │    System Prompt    │                            │
│                          │    (系统提示词)      │                            │
│                          │                     │                            │
│                          │  ┌───────────────┐  │                            │
│                          │  │   Identity    │  │  ← 角色定义                │
│                          │  │   身份        │  │                            │
│                          │  └───────────────┘  │                            │
│                          │  ┌───────────────┐  │                            │
│                          │  │   Memory      │  │  ← 长期记忆                │
│                          │  │   记忆        │  │                            │
│                          │  └───────────────┘  │                            │
│                          │  ┌───────────────┐  │                            │
│                          │  │   Skills      │  │  ← 技能指令                │
│                          │  │   技能        │  │                            │
│                          │  └───────────────┘  │                            │
│                          │  ┌───────────────┐  │                            │
│                          │  │   Guidelines  │  │  ← 行为准则                │
│                          │  │   准则        │  │                            │
│                          │  └───────────────┘  │                            │
│                          └──────────┬──────────┘                            │
│                                     │                                       │
│                                     ▼                                       │
│         ┌───────────────────────────────────────────────────────┐          │
│         │                    LLM (大语言模型)                     │          │
│         │                                                       │          │
│         │   输入: System Prompt + Session History + User Input  │          │
│         │   输出: 文本回复 或 Tool Calls                         │          │
│         └───────────────────────────────────────────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 14.2 nanobot 提示词设计哲学

nanobot 的提示词设计遵循 **"简洁而精准"** 的原则：

#### 14.2.1 设计原则

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    nanobot 提示词设计五原则                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1️⃣ 最小必要原则（Minimum Necessary）                                       │
│     - 只包含完成任务所需的最少信息                                           │
│     - 避免冗余和重复                                                        │
│     - 每句话都有明确目的                                                    │
│                                                                             │
│  2️⃣ 结构化原则（Structured）                                                │
│     - 使用 Markdown 格式组织                                                │
│     - 清晰的标题和分段                                                      │
│     - 便于 LLM 解析和理解                                                   │
│                                                                             │
│  3️⃣ 可扩展原则（Extensible）                                                │
│     - 支持 Bootstrap Files 动态加载                                         │
│     - 支持 Skills 系统扩展                                                  │
│     - 用户可自定义注入内容                                                  │
│                                                                             │
│  4️⃣ 上下文优先原则（Context-First）                                         │
│     - 运行时信息注入（时间、目录）                                           │
│     - 动态记忆整合                                                          │
│     - 会话历史滑动窗口                                                      │
│                                                                             │
│  5️⃣ 安全边界原则（Safe Boundary）                                           │
│     - 明确工具使用边界                                                      │
│     - 错误处理指引                                                          │
│     - 防止幻觉和过度承诺                                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 14.2.2 提示词结构分解

nanobot 的系统提示词由以下部分组成：

```python
def build_system_prompt(self) -> str:
    """
    nanobot 系统提示词构建流程
    """
    parts = []

    # ========== Part 1: 基础身份 ==========
    parts.append(self._get_identity())
    # 内容：角色定义、运行时信息、工作目录、核心准则

    # ========== Part 2: Bootstrap 文件 ==========
    bootstrap = self._load_bootstrap_files()
    if bootstrap:
        parts.append(bootstrap)
    # 内容：AGENTS.md, SOUL.md, USER.md, TOOLS.md, IDENTITY.md

    # ========== Part 3: 长期记忆 ==========
    memory = self.memory.get_memory_context()
    if memory:
        parts.append(f"# Memory\n\n{memory}")
    # 内容：MEMORY.md 中的持久化信息

    # ========== Part 4: 活跃技能 ==========
    always_skills = self.skills.get_always_skills()
    if always_skills:
        skill_content = self.skills.load_skills_for_context(always_skills)
        if skill_content:
            parts.append(f"# Active Skills\n\n{skill_content}")
    # 内容：always=true 的技能定义

    # ========== 合并 ==========
    return "\n\n---\n\n".join(parts)
```

### 14.3 核心身份提示词详解

#### 14.3.1 Identity 模板完整解析

```python
# nanobot/agent/context.py

def _get_identity(self) -> str:
    """生成基础身份提示词"""

    # 运行时动态信息
    runtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    workspace_path = str(self.workspace)
    skill_dir = str(self.workspace / "skills")

    return f"""# nanobot

You are nanobot, a helpful AI assistant.

## Runtime
{runtime}

## Workspace
Your workspace is at: {workspace_path}
- Long-term memory: {workspace_path}/memory/MEMORY.md
- History log: {workspace_path}/memory/HISTORY.md
- Custom skills: {skill_dir}/{{skill-name}}/SKILL.md

## nanobot Guidelines
- State intent before tool calls, but NEVER predict or claim results before receiving them.
- Before modifying a file, read it first. Do not assume files or directories exist.
- After writing or editing a file, re-read it if accuracy matters.
- If a tool call fails, analyze the error before retrying with a different approach.
- Ask for clarification when the request is ambiguous.

Reply directly with text for conversations. Only use the 'message' tool to send to a specific chat channel."""
```

#### 14.3.2 逐句解析

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Identity 提示词逐句解析                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  "# nanobot"                                                                │
│  └─ 目的：建立品牌认知，让 LLM 知道自己是谁                                  │
│                                                                             │
│  "You are nanobot, a helpful AI assistant."                                 │
│  └─ 目的：定义基本角色 - 乐于助人的助手                                      │
│  └─ 特点：简洁，没有过度约束                                                 │
│                                                                             │
│  "## Runtime" + "{timestamp}"                                               │
│  └─ 目的：注入时间感知，帮助 LLM 理解"现在"                                  │
│  └─ 应用：处理时间相关问题、日程安排等                                       │
│                                                                             │
│  "## Workspace" + 路径信息                                                  │
│  └─ 目的：明确工作边界，让 LLM 知道文件操作范围                              │
│  └─ 应用：read_file, write_file 等工具的上下文                              │
│                                                                             │
│  "## nanobot Guidelines" 五条准则：                                         │
│                                                                             │
│  1. "State intent before tool calls, but NEVER predict results"             │
│     └─ 目的：防止 LLM 幻觉，先声明意图，不预测结果                           │
│     └─ 问题场景：LLM 可能声称"我已经读取了文件"但实际上还没执行              │
│                                                                             │
│  2. "Before modifying a file, read it first"                                │
│     └─ 目的：确保文件操作的准确性                                           │
│     └─ 问题场景：直接写入可能覆盖重要内容                                    │
│                                                                             │
│  3. "After writing or editing a file, re-read it if accuracy matters"       │
│     └─ 目的：验证写入结果，确保操作成功                                      │
│     └─ 问题场景：写入失败或部分写入                                         │
│                                                                             │
│  4. "If a tool call fails, analyze the error before retrying"               │
│     └─ 目的：避免盲目重试，引导分析性思维                                    │
│     └─ 问题场景：无限循环重试相同的错误操作                                  │
│                                                                             │
│  5. "Ask for clarification when the request is ambiguous"                   │
│     └─ 目的：鼓励询问，避免误解                                              │
│     └─ 问题场景：基于错误理解执行任务                                        │
│                                                                             │
│  "Reply directly with text for conversations..."                            │
│  └─ 目的：区分对话模式和工具调用模式                                         │
│  └─ 应用：普通聊天直接回复，发送到其他渠道用 message 工具                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 14.4 Bootstrap 文件系统

#### 14.4.1 文件结构与用途

nanobot 支持通过 Bootstrap 文件扩展提示词：

```
~/.nanobot/workspace/
├── AGENTS.md      # Agent 行为定义（全局设置）
├── SOUL.md        # 核心人格（性格、价值观）
├── USER.md        # 用户偏好（个人信息、习惯）
├── TOOLS.md       # 工具使用指南（最佳实践）
└── IDENTITY.md    # 自定义身份（覆盖默认身份）
```

#### 14.4.2 各文件设计意图

```python
BOOTSTRAP_FILES = [
    "AGENTS.md",    # 多 Agent 场景下的行为定义
    "SOUL.md",      # 情感化设计，让 Agent 更有"个性"
    "USER.md",      # 个性化定制，记住用户偏好
    "TOOLS.md",     # 工具使用的最佳实践和示例
    "IDENTITY.md"   # 完全自定义身份（高级用户）
]
```

**AGENTS.md 示例**：
```markdown
# Agent Configuration

## Response Style
- Be concise and direct
- Use bullet points for lists
- Avoid unnecessary pleasantries

## Task Handling
- Break complex tasks into steps
- Confirm understanding before execution
- Report progress for long-running tasks

## Error Handling
- Explain errors in plain language
- Suggest alternative approaches
- Never blame the user
```

**USER.md 示例**：
```markdown
# User Preferences

## Personal Info
- Name: Alice
- Timezone: UTC+8
- Primary Language: Chinese

## Coding Preferences
- Use Python for scripting
- Prefer type hints
- Follow PEP 8 style guide

## Communication Style
- Prefer technical explanations
- Include code examples
- Skip basic tutorials
```

**TOOLS.md 示例**：
```markdown
# Tool Usage Guide

## File Operations
- Always use relative paths from workspace
- Check file existence before reading
- Create backups before major edits

## Shell Commands
- Prefer cross-platform commands
- Quote paths with spaces
- Set appropriate timeouts

## Web Search
- Verify sources before citing
- Summarize key findings
- Note publication dates
```

### 14.5 技能（Skills）提示词系统

#### 14.5.1 技能定义格式

```markdown
---
name: github
description: GitHub integration for repository operations
always: false
trigger:
  - "github"
  - "repository"
  - "pull request"
---

# GitHub Skill

## Description
This skill enables GitHub repository operations including:
- Creating and managing issues
- Opening pull requests
- Reviewing code
- Managing branches

## Instructions
When the user asks about GitHub operations:

1. First, verify repository context:
   - Check if we're in a git repository
   - Identify the remote URL
   - Determine the current branch

2. For PR creation:
   - Ensure branch is pushed
   - Generate meaningful title and description
   - Request review assignment

3. For issue management:
   - Use clear, descriptive titles
   - Apply appropriate labels
   - Link related issues

## Example Usage
User: "Create a PR for this feature"
Assistant:
  "I'll create a pull request for you. Let me first check the current branch status..."
  [executes: git branch --show-current]
  [executes: gh pr create --title "..." --body "..."]

## Constraints
- Never force push to main/master
- Always request review for production changes
- Keep commits atomic and descriptive
```

#### 14.5.2 技能加载机制

```python
class SkillsLoader:
    """技能加载器"""

    def __init__(self, workspace: Path):
        self.skills_dir = workspace / "skills"
        self._cache: dict[str, SkillDefinition] = {}

    def get_always_skills(self) -> list[str]:
        """获取 always=true 的技能列表"""
        always_skills = []
        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    metadata = self._parse_frontmatter(skill_file)
                    if metadata.get("always", False):
                        always_skills.append(skill_path.name)
        return always_skills

    def load_skills_for_context(self, skill_names: list[str]) -> str:
        """加载技能内容到上下文"""
        contents = []
        for name in skill_names:
            skill_file = self.skills_dir / name / "SKILL.md"
            if skill_file.exists():
                content = skill_file.read_text(encoding="utf-8")
                # 移除 frontmatter，只保留内容
                content = self._strip_frontmatter(content)
                contents.append(f"## Skill: {name}\n\n{content}")
        return "\n\n".join(contents)
```

### 14.6 记忆系统提示词设计

#### 14.6.1 记忆注入方式

```python
def get_memory_context(self) -> str | None:
    """获取记忆上下文"""
    memory_path = self.memory_dir / "MEMORY.md"

    if not memory_path.exists():
        return None

    content = memory_path.read_text(encoding="utf-8").strip()
    return content if content else None

# 在构建系统提示词时
memory = self.memory.get_memory_context()
if memory:
    parts.append(f"# Memory\n\n{memory}")
```

#### 14.6.2 MEMORY.md 推荐格式

```markdown
# User Profile

## Personal Information
- Name: Alice Chen
- Occupation: Software Engineer
- Location: Beijing, China

## Preferences
- Language: Chinese (primary), English (technical)
- Communication: Direct and concise
- Code style: Type hints, docstrings, PEP 8

## Technical Background
- Expertise: Python, TypeScript, Kubernetes
- Current projects: nanobot, NanoClaw
- Tools: VS Code, JetBrains IDEs

## Important Dates
- 2026-02-15: Project deadline for feature X
- Weekly standup: Every Monday 10:00 AM

## Ongoing Tasks
- [ ] Review PR #123
- [ ] Update documentation for API v2
- [ ] Prepare presentation for team meeting

## Notes
- Prefers async communication
- Available for pair programming on Tuesdays
- Interested in AI/ML topics
```

#### 14.6.3 记忆整合提示词

```python
MEMORY_CONSOLIDATION_PROMPT = """You are a memory consolidation system.

Current Memory:
{current_memory}

New Information from Recent Conversation:
{recent_conversation}

Task: Update the memory file with new important information.

Rules:
1. Only add genuinely important, persistent information
2. Remove outdated or incorrect information
3. Keep the memory concise and well-organized
4. Use Markdown format
5. Do NOT include temporary or context-specific details
6. Preserve existing structure when possible
7. Highlight new additions with context

Categories to consider:
- Personal information (name, preferences, background)
- Technical preferences (languages, frameworks, tools)
- Project context (current work, deadlines)
- Important dates and events
- Ongoing tasks and reminders
- Notes and miscellaneous facts

Return ONLY the updated memory content in Markdown format.
Do not include any explanations or meta-commentary."""
```

### 14.7 工具调用提示词设计

#### 14.7.1 工具定义注入

```python
def get_tool_definitions(self) -> list[dict]:
    """获取工具定义（注入到 LLM API 调用）"""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file from the workspace. Use this to examine existing files before modifying them or to understand the current state of a file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the file from the workspace root. Example: 'src/main.py'"
                        }
                    },
                    "required": ["path"]
                }
            }
        },
        # ... 更多工具定义
    ]
```

#### 14.7.2 工具使用指引（在 Guidelines 中）

```
## Tool Usage Guidelines

### When to Use Tools
- read_file: Before editing any file, or when user asks about file contents
- write_file: Creating new files or complete rewrites
- edit_file: Making specific changes to existing files
- list_dir: Exploring directory structure
- exec: Running shell commands (use with caution)
- web_search: Finding current information beyond training data
- web_fetch: Reading content from URLs

### Tool Call Best Practices
1. Always state your intent before calling a tool
2. Never predict tool results - wait for actual output
3. Handle errors gracefully - analyze before retrying
4. Chain tools logically - read before edit, verify after write
5. Use appropriate timeouts for long-running commands

### Error Recovery
- File not found: Check path, verify with list_dir
- Permission denied: Explain limitation, suggest alternatives
- Timeout: Consider breaking into smaller operations
- Invalid arguments: Re-read tool description, correct parameters
```

### 14.8 会话历史管理

#### 14.8.1 消息格式

```python
# nanobot 使用标准的 OpenAI 消息格式

messages = [
    # 系统消息（提示词）
    {"role": "system", "content": "..."},

    # 历史消息
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi! How can I help you today?"},

    # 工具调用消息
    {"role": "assistant", "content": "Let me check that file.",
     "tool_calls": [{
         "id": "call_123",
         "type": "function",
         "function": {"name": "read_file", "arguments": '{"path": "test.py"}'}
     }]},
    {"role": "tool", "tool_call_id": "call_123", "name": "read_file",
     "content": "# file contents..."},

    # 当前用户输入
    {"role": "user", "content": "Can you add a comment to line 5?"}
]
```

#### 14.8.2 历史截断策略

```python
def get_history(self, max_messages: int = 500) -> list[dict]:
    """获取会话历史，应用滑动窗口"""

    # 获取未整合的消息
    unconsolidated = self.messages[self.last_consolidated:]

    # 应用滑动窗口
    sliced = unconsolidated[-max_messages:]

    # 确保不以孤立的消息开头（避免 orphaned tool_result）
    for i, msg in enumerate(sliced):
        if msg.get("role") == "user":
            sliced = sliced[i:]
            break

    return sliced
```

---

## 十五、nanobot vs OpenClaw 提示词对比

### 15.1 提示词哲学对比

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      提示词设计哲学对比                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  nanobot                              OpenClaw                               │
│  ─────────                            ─────────                              │
│                                                                             │
│  理念: "简洁而精准"                    理念: "全面而详尽"                    │
│                                                                             │
│  ┌─────────────────────────┐          ┌─────────────────────────┐          │
│  │ • 核心提示词 ~500 字符  │          │ • 核心提示词 ~5000 字符 │          │
│  │ • 5 条核心准则          │          │ • 30+ 条详细规则        │          │
│  │ • 动态扩展为主          │          │ • 静态定义为主          │          │
│  │ • 单一身份定义          │          │ • 多角色/模式切换       │          │
│  │ • 文件化记忆系统        │          │ • 向量数据库记忆        │          │
│  │ • 用户可完全定制        │          │ • 预设模板为主          │          │
│  └─────────────────────────┘          └─────────────────────────┘          │
│                                                                             │
│  Token 效率: 高                        Token 效率: 中                        │
│  可定制性: 高                          可定制性: 中                          │
│  学习成本: 低                          学习成本: 高                          │
│  功能覆盖: 核心功能                    功能覆盖: 全面                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.2 身份定义对比

#### nanobot 身份定义

```markdown
# nanobot

You are nanobot, a helpful AI assistant.

## Runtime
2026-03-07 10:30:00

## Workspace
Your workspace is at: /home/user/.nanobot/workspace
- Long-term memory: /home/user/.nanobot/workspace/memory/MEMORY.md
- History log: /home/user/.nanobot/workspace/memory/HISTORY.md
- Custom skills: /home/user/.nanobot/workspace/skills/{skill-name}/SKILL.md

## nanobot Guidelines
- State intent before tool calls, but NEVER predict or claim results before receiving them.
- Before modifying a file, read it first. Do not assume files or directories exist.
- After writing or editing a file, re-read it if accuracy matters.
- If a tool call fails, analyze the error before retrying with a different approach.
- Ask for clarification when the request is ambiguous.

Reply directly with text for conversations. Only use the 'message' tool to send to a specific chat channel.
```

**字数**: ~200 词
**Token**: ~300 tokens

#### OpenClaw 身份定义（简化版）

```markdown
# OpenClaw Agent System

You are an advanced AI agent powered by the OpenClaw framework. You have access to a comprehensive set of tools and capabilities to assist users with a wide range of tasks.

## Core Identity
- Name: OpenClaw Agent
- Version: 2.0
- Capabilities: File operations, web browsing, code execution, API integration, multi-modal processing

## Behavioral Guidelines

### Communication Style
1. Be professional yet friendly
2. Provide detailed explanations when appropriate
3. Use markdown formatting for better readability
4. Include code blocks with proper syntax highlighting
5. Cite sources when referencing external information

### Task Execution
1. Analyze the request thoroughly before acting
2. Break complex tasks into manageable steps
3. Provide progress updates for long-running operations
4. Verify results before claiming completion
5. Handle errors gracefully with clear explanations

### Safety and Ethics
1. Never execute potentially harmful commands without explicit user confirmation
2. Respect user privacy and data confidentiality
3. Follow the principle of least privilege
4. Report any security concerns immediately
5. Adhere to content guidelines and policies

### Tool Usage Protocol
1. Select the most appropriate tool for each task
2. Validate inputs before tool execution
3. Handle tool errors with retry logic when appropriate
4. Log all tool executions for audit purposes
5. Clean up temporary resources after use

### Memory and Context
1. Maintain context across conversation turns
2. Reference previous interactions when relevant
3. Store important information in long-term memory
4. Respect memory limits and pruning rules
5. Consolidate memories periodically

### Multi-Agent Coordination
1. Communicate clearly with other agents
2. Share relevant context and resources
3. Follow established handoff protocols
4. Report status to orchestrator
5. Handle conflicts through negotiation

## Workspace Information
- Root directory: /app/workspace
- Memory backend: PostgreSQL + Qdrant
- Cache directory: /tmp/openclaw
- Log directory: /var/log/openclaw

## Available Capabilities
- File system operations (read, write, edit, delete)
- Shell command execution (sandboxed)
- Web search and browsing
- API integration (REST, GraphQL)
- Code generation and review
- Data analysis and visualization
- Multi-modal content processing
- Scheduled task execution

## Response Format
- Use structured sections for complex responses
- Include relevant metadata when helpful
- Provide actionable recommendations
- Summarize key points for quick reference

Remember: You are a helpful assistant dedicated to providing the best possible support to users while maintaining safety and ethical standards.
```

**字数**: ~500 词
**Token**: ~800 tokens

### 15.3 提示词结构对比

| 维度 | nanobot | OpenClaw |
|------|---------|----------|
| **基础身份** | 简短（~200 词） | 详细（~500 词） |
| **行为准则** | 5 条核心规则 | 30+ 条详细规则 |
| **工具说明** | 通过 API 注入 | 内嵌在提示词中 |
| **记忆系统** | Markdown 文件 | 向量数据库 |
| **技能系统** | 动态加载 | 静态定义 |
| **多语言支持** | 无特殊处理 | 详细语言指引 |
| **错误处理** | 简单指引 | 完整协议 |
| **安全边界** | 隐式 | 显式详细 |

### 15.4 记忆系统对比

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        记忆系统架构对比                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  nanobot (文件化记忆)                  OpenClaw (向量数据库记忆)              │
│                                                                             │
│  ┌─────────────────────┐              ┌─────────────────────┐              │
│  │    MEMORY.md        │              │   Qdrant/Chroma     │              │
│  │    (Markdown 文件)  │              │   (向量数据库)       │              │
│  └──────────┬──────────┘              └──────────┬──────────┘              │
│             │                                    │                         │
│             ▼                                    ▼                         │
│  ┌─────────────────────┐              ┌─────────────────────┐              │
│  │ • 人类可读          │              │ • 语义搜索          │              │
│  │ • 可直接编辑        │              │ • 自动相似度匹配    │              │
│  │ • LLM 整合更新      │              │ • Embedding 向量化  │              │
│  │ • 容量有限 (~10KB)  │              │ • 容量无限          │              │
│  │ • 结构化 Markdown   │              │ • 非结构化存储      │              │
│  └─────────────────────┘              └─────────────────────┘              │
│                                                                             │
│  优点:                                优点:                                 │
│  ✅ 简单直观                          ✅ 语义理解能力强                      │
│  ✅ 零依赖                            ✅ 大规模记忆支持                      │
│  ✅ 易于备份迁移                      ✅ 自动关联检索                        │
│  ✅ 可手动编辑                        ✅ 去重和合并                          │
│                                                                             │
│  缺点:                                缺点:                                 │
│  ❌ 无语义搜索                        ❌ 需要额外服务                        │
│  ❌ 手动维护                          ❌ 不可直接查看                        │
│  ❌ 容量有限                          ❌ 复杂度高                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.5 工具调用提示词对比

#### nanobot 工具调用

```python
# 工具定义通过 API 注入，不在提示词中
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {...}
        }
    }
]

# 提示词中只有简短指引
"- Before modifying a file, read it first."
```

#### OpenClaw 工具调用

```markdown
## Available Tools

### File Operations

#### read_file
- Purpose: Read the contents of a file from the filesystem
- Parameters:
  - path (string, required): The absolute or relative path to the file
- Returns: The file contents as a string
- Error handling:
  - File not found: Returns error message with suggestions
  - Permission denied: Suggests alternative approaches
- Best practices:
  - Always check file existence before reading
  - Use relative paths when possible
  - Handle encoding issues gracefully
- Example usage:
  ```
  User: "Show me the contents of config.yaml"
  Tool call: read_file(path="config.yaml")
  ```

#### write_file
- Purpose: Create or overwrite a file with new contents
- Parameters:
  - path (string, required): The path where the file should be written
  - content (string, required): The content to write to the file
- Returns: Confirmation message with bytes written
- Safety considerations:
  - Warn before overwriting existing files
  - Create backup for critical files
  - Validate content before writing
- ...

[继续详细定义其他工具...]
```

### 15.6 技能/插件系统对比

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        技能系统对比                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  nanobot Skills                        OpenClaw Plugins                     │
│                                                                             │
│  结构:                                结构:                                 │
│  skills/                              plugins/                              │
│  └── github/                          └── github/                           │
│      └── SKILL.md                         ├── plugin.yaml   (配置)          │
│                                          ├── __init__.py   (入口)           │
│                                          ├── tools.py      (工具定义)       │
│                                          ├── prompts.py    (提示词)         │
│                                          └── handlers.py   (处理器)         │
│                                                                             │
│  加载方式:                            加载方式:                              │
│  • 文件系统扫描                        • 插件注册表                          │
│  • Markdown 解析                       • Python 模块加载                     │
│  • 动态注入提示词                      • 依赖注入                            │
│                                                                             │
│  复杂度: 低                           复杂度: 高                             │
│  灵活性: 高                           灵活性: 中                             │
│  功能: 提示词扩展                      功能: 完整扩展系统                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 15.7 Token 消耗对比

| 场景 | nanobot | OpenClaw |
|------|---------|----------|
| **基础对话（无历史）** | ~500 tokens | ~2000 tokens |
| **含 10 轮历史** | ~2000 tokens | ~5000 tokens |
| **含 50 轮历史** | ~8000 tokens | ~20000 tokens |
| **含技能/插件** | +200-500 tokens/skill | +1000-3000 tokens/plugin |
| **含记忆** | +500-2000 tokens | +0 (向量检索) |

### 15.8 设计权衡分析

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        设计权衡分析                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  nanobot 选择"简洁"的权衡:                                                  │
│                                                                             │
│  获得的:                              牺牲的:                               │
│  ✅ 更低的 Token 消耗                  ❌ 更少的内置指引                     │
│  ✅ 更快的响应速度                     ❌ 更高的用户学习曲线                 │
│  ✅ 更高的可定制性                     ❌ 需要更多手动配置                   │
│  ✅ 更容易理解代码                     ❌ 功能覆盖相对有限                   │
│  ✅ 更低的部署成本                     ❌ 生产级保障较弱                     │
│                                                                             │
│  OpenClaw 选择"全面"的权衡:                                                 │
│                                                                             │
│  获得的:                              牺牲的:                               │
│  ✅ 开箱即用的完整功能                 ❌ 更高的 Token 消耗                  │
│  ✅ 详细的行为指引                     ❌ 更复杂的代码库                     │
│  ✅ 生产级可靠性                       ❌ 更高的部署成本                     │
│  ✅ 企业级安全保障                     ❌ 更难进行定制                       │
│  ✅ 完善的错误处理                     ❌ 更高的学习曲线                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 十六、提示词最佳实践

### 16.1 nanobot 提示词优化建议

#### 16.1.1 自定义身份

```markdown
<!-- IDENTITY.md -->
# Custom Assistant Identity

## Role
You are an expert software architect specializing in Python backend development.

## Expertise
- FastAPI and async programming
- PostgreSQL database design
- Microservices architecture
- CI/CD pipelines

## Communication Style
- Use code examples extensively
- Explain trade-offs in design decisions
- Reference relevant documentation links
- Suggest best practices proactively

## Constraints
- Never suggest deprecated libraries
- Always consider security implications
- Prefer standard library when possible
```

#### 16.1.2 优化用户偏好

```markdown
<!-- USER.md -->
# User Preferences

## Context
- Working on: nanobot project
- Team size: 3 developers
- Deployment: Docker + Kubernetes

## Code Standards
- Python 3.11+ features
- Pydantic v2 for validation
- pytest for testing
- Ruff for linting

## Git Workflow
- Main branch: main
- Feature branches: feature/*
- Commit style: Conventional Commits
- PR required for all changes
```

#### 16.1.3 技能定义最佳实践

```markdown
---
name: code_review
description: Automated code review with best practices check
always: false
trigger:
  - "review"
  - "code review"
  - "check my code"
---

# Code Review Skill

## Purpose
Perform comprehensive code review focusing on:
- Code quality and readability
- Security vulnerabilities
- Performance considerations
- Best practices adherence

## Review Checklist

### Security
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] Authentication/Authorization checks
- [ ] Sensitive data handling

### Performance
- [ ] N+1 query detection
- [ ] Memory leak prevention
- [ ] Async/await usage
- [ ] Caching opportunities

### Code Quality
- [ ] Function complexity
- [ ] Code duplication
- [ ] Naming conventions
- [ ] Documentation

## Output Format
```
## Code Review Summary

### Critical Issues 🔴
- [List critical issues]

### Warnings 🟡
- [List warnings]

### Suggestions 🟢
- [List suggestions]

### Good Practices ✅
- [Highlight good practices found]
```
```

### 16.2 记忆管理最佳实践

```markdown
<!-- MEMORY.md 最佳实践 -->

# User Profile

## Quick Reference
<!-- 高频信息放在最前面 -->
- Primary language: Chinese
- Timezone: UTC+8
- Preferred model: Claude

## Current Context
<!-- 当前项目状态 -->
- Active project: NanoClaw frontend
- Next deadline: 2026-03-15
- Blockers: Waiting for API documentation

## Preferences
<!-- 稳定的偏好设置 -->
- Code style: PEP 8, ESLint recommended
- Commit message: Conventional Commits
- Documentation: Docstrings required

## Technical Stack
<!-- 技术栈信息 -->
- Frontend: Next.js, React, Tailwind
- Backend: Python, FastAPI
- Database: PostgreSQL
- Deployment: Docker, Kubernetes

## Notes
<!-- 杂项笔记，保持简洁 -->
- Prefers detailed explanations for new concepts
- Likes code examples with comments
- Available for calls on weekdays 2-6 PM
```

### 16.3 避免常见陷阱

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      提示词常见陷阱与解决方案                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  陷阱 1: 过度约束                                                           │
│  ─────────────────                                                          │
│  问题: 提示词包含太多"不要做 X"                                              │
│  解决: 使用正面指令，"应该做 Y"                                              │
│                                                                             │
│  陷阱 2: 模糊指令                                                           │
│  ─────────────────                                                          │
│  问题: "适当处理错误"                                                        │
│  解决: "如果文件不存在，使用 list_dir 确认路径后重试"                          │
│                                                                             │
│  陷阱 3: 过长提示词                                                          │
│  ─────────────────                                                          │
│  问题: 提示词超过 2000 tokens                                                │
│  解决: 拆分到 Skills 或 Bootstrap 文件                                       │
│                                                                             │
│  陷阱 4: 静态信息                                                            │
│  ─────────────────                                                          │
│  问题: 硬编码时间、路径等信息                                                 │
│  解决: 使用动态注入，如 {runtime}, {workspace_path}                           │
│                                                                             │
│  陷阱 5: 忽略错误处理                                                         │
│  ─────────────────                                                          │
│  问题: 只描述成功场景                                                        │
│  解决: 添加"If tool call fails, analyze error before retrying"               │
│                                                                             │
│  陷阱 6: 记忆膨胀                                                            │
│  ─────────────────                                                          │
│  问题: MEMORY.md 无限增长                                                    │
│  解决: 定期整合，只保留持久化信息                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 十七、总结

### 17.1 提示词设计核心要点

| 要点 | 说明 |
|------|------|
| **简洁性** | 每句话都有目的，避免冗余 |
| **结构化** | 使用 Markdown 组织，便于解析 |
| **动态性** | 注入运行时信息，保持时效 |
| **可扩展** | 通过文件系统扩展，不修改代码 |
| **安全性** | 设置边界，防止幻觉和误操作 |

### 17.2 nanobot vs OpenClaw 提示词选择建议

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        选择建议                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  选择 nanobot 提示词风格，如果：                                            │
│  ✅ 你想要完全控制提示词内容                                                │
│  ✅ 你重视 Token 效率和成本                                                 │
│  ✅ 你需要快速迭代和实验                                                    │
│  ✅ 你的使用场景相对简单                                                    │
│  ✅ 你希望学习和理解 Agent 内部机制                                         │
│                                                                             │
│  选择 OpenClaw 提示词风格，如果：                                           │
│  ✅ 你需要开箱即用的完整功能                                                │
│  ✅ 你有严格的合规和安全要求                                                │
│  ✅ 你处理复杂的业务逻辑                                                    │
│  ✅ 你需要企业级可靠性                                                      │
│  ✅ 你有资源支持复杂的部署                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 17.3 文档总结

本文档详细分析了 nanobot 项目的：

1. **项目概述与技术栈** - 轻量级定位和核心依赖
2. **代码结构** - 清晰的模块划分
3. **核心模块** - AgentLoop、Context、Memory、Provider、Tool
4. **Channel 系统** - 多平台消息集成
5. **消息总线** - 事件驱动架构
6. **配置系统** - Pydantic 驱动的类型安全配置
7. **数据流与架构** - ReAct 循环和设计模式
8. **代码示例** - 实用的开发模板
9. **扩展指南** - 添加 Provider、Channel、Skill
10. **架构设计思想** - 极简主义哲学
11. **nanobot vs OpenClaw** - 全面对比分析
12. **提示词设计** - 深度解析和最佳实践

---

**文档版本**: 3.0
**生成日期**: 2026-03-07
**项目版本**: nanobot v0.1.4.post3
**仓库地址**: https://github.com/HKUDS/nanobot
