/**
 * Nanobot TypeScript Type Definitions
 *
 * Comprehensive type definitions for all Nanobot data structures
 */

// ============================================================================
// Configuration Types
// ============================================================================

export interface NanobotConfig {
  agents?: {
    defaults?: {
      workspace?: string
      model?: string
      max_tokens?: number
      temperature?: number
      max_tool_iterations?: number
      memory_window?: number
    }
  }
  channels?: {
    [key: string]: ChannelConfig
  }
  providers?: {
    [key: string]: ProviderConfig
  }
  tools?: ToolsConfig
}

// ============================================================================
// Channel Types
// ============================================================================

/**
 * Base channel configuration
 */
interface BaseChannelConfig {
  enabled: boolean
  allow_from?: string[]
}

/**
 * Telegram channel configuration
 */
export interface TelegramChannelConfig extends BaseChannelConfig {
  token: string
}

/**
 * Discord channel configuration
 */
export interface DiscordChannelConfig extends BaseChannelConfig {
  token: string
  intents?: string[]
}

/**
 * WhatsApp channel configuration
 */
export interface WhatsAppChannelConfig extends BaseChannelConfig {
  bridge_url: string
  bridge_token: string
}

/**
 * Feishu (Lark) channel configuration
 */
export interface FeishuChannelConfig extends BaseChannelConfig {
  app_id: string
  app_secret: string
}

/**
 * Slack channel configuration
 */
export interface SlackChannelConfig extends BaseChannelConfig {
  bot_token: string
  app_token: string
}

/**
 * DingTalk channel configuration
 */
export interface DingTalkChannelConfig extends BaseChannelConfig {
  client_id: string
  client_secret: string
}

/**
 * Mochat channel configuration
 */
export interface MochatChannelConfig extends BaseChannelConfig {
  base_url: string
  claw_token: string
}

/**
 * Email channel configuration
 */
export interface EmailChannelConfig extends BaseChannelConfig {
  imap_host: string
  imap_port: number
  smtp_host: string
  smtp_port: number
  username: string
  password: string
}

/**
 * QQ channel configuration
 */
export interface QQChannelConfig extends BaseChannelConfig {
  app_id: string
  secret: string
}

/**
 * Union type for all channel configurations
 */
export type ChannelConfig =
  | TelegramChannelConfig
  | DiscordChannelConfig
  | WhatsAppChannelConfig
  | FeishuChannelConfig
  | SlackChannelConfig
  | DingTalkChannelConfig
  | MochatChannelConfig
  | EmailChannelConfig
  | QQChannelConfig

/**
 * Channel names
 */
export type ChannelName =
  | 'telegram'
  | 'discord'
  | 'whatsapp'
  | 'feishu'
  | 'slack'
  | 'dingtalk'
  | 'mochat'
  | 'email'
  | 'qq'

// ============================================================================
// Provider Types
// ============================================================================

/**
 * LLM Provider configuration
 */
export interface ProviderConfig {
  api_key: string
  api_base?: string
  models?: string[]
  extra_headers?: Record<string, string>
}

/**
 * Provider names
 */
export type ProviderName =
  // Gateways
  | 'openrouter'
  | 'aihubmix'
  | 'custom'
  // International
  | 'anthropic'
  | 'openai'
  | 'deepseek'
  | 'groq'
  | 'gemini'
  // Chinese
  | 'dashscope' // Qwen
  | 'moonshot' // Kimi
  | 'zhipu' // GLM
  | 'minimax'
  // Local
  | 'vllm'

// ============================================================================
// Tools Configuration
// ============================================================================

export interface ToolsConfig {
  web?: {
    search?: {
      api_key: string
      max_results: number
    }
  }
  exec?: {
    timeout: number
  }
  restrict_to_workspace?: boolean
  mcp_servers?: {
    [name: string]: MCPServerConfig
  }
}

export interface MCPServerConfig {
  command?: string
  args?: string[]
  url?: string
  env?: Record<string, string>
}

// ============================================================================
// Session Types
// ============================================================================

/**
 * Session message
 */
export interface SessionMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: string
  tools_used?: string[]
}

/**
 * Session metadata (first line of JSONL file)
 */
export interface SessionMetadata {
  _type?: 'metadata'
  session_id?: string
  title?: string
  created_at: string
  updated_at: string
  last_consolidated?: number
}

/**
 * Session info for list view
 */
export interface SessionInfo {
  key: string
  filename: string
  metadata: SessionMetadata
  messageCount: number
}

/**
 * Session type alias for frontend use
 */
export type Session = SessionInfo

/**
 * Model info for provider grouping
 */
export interface ModelInfo {
  provider: string
  models: string[]
}

/**
 * Full session data
 */
export interface SessionData {
  metadata: SessionMetadata
  messages: SessionMessage[]
}

// ============================================================================
// Memory Types
// ============================================================================

/**
 * Memory file types
 */
export type MemoryType = 'longTerm' | 'history' | 'heartbeat'

/**
 * Memory files structure
 */
export interface MemoryFiles {
  'MEMORY.md': string
  'HISTORY.md': string
  'HEARTBEAT.md': string
}

// ============================================================================
// Skill Types
// ============================================================================

/**
 * Skill metadata (parsed from frontmatter metadata field)
 */
export interface SkillMetadata {
  nanobot?: {
    requires?: {
      bins?: string[]
      env?: string[]
    }
  }
  [key: string]: any
}

/**
 * Skill frontmatter
 */
export interface SkillFrontmatter {
  name: string
  description: string
  always: boolean
  metadata?: string // JSON string
}

/**
 * Skill file structure
 */
export interface SkillFile {
  frontmatter: SkillFrontmatter
  content: string
}

/**
 * Skill info for list view
 */
export interface SkillInfo {
  name: string
  frontmatter: SkillFrontmatter
  metadata?: SkillMetadata
  isBuiltIn: boolean
}

/**
 * Built-in skill names
 */
export type BuiltInSkillName =
  | 'memory'
  | 'cron'
  | 'github'
  | 'weather'
  | 'summarize'
  | 'skill-creator'
  | 'tmux'

// ============================================================================
// Cron Types
// ============================================================================

/**
 * Cron job schedule types
 */
export type CronScheduleType = 'at' | 'every' | 'cron'

/**
 * Cron job payload types
 */
export type CronPayloadType = 'reminder' | 'task' | 'heartbeat'

/**
 * Cron job schedule configuration
 */
export interface CronSchedule {
  type: CronScheduleType
  at_ms?: number
  every_ms?: number
  expr?: string
  tz?: string
}

/**
 * Cron job payload
 */
export interface CronPayload {
  type: CronPayloadType
  channel: string
  chat_id: string
  message: string
}

/**
 * Cron job state
 */
export interface CronState {
  next_run: number
  last_run?: number
}

/**
 * Cron job
 */
export interface CronJob {
  id: string
  name: string
  enabled: boolean
  schedule: CronSchedule
  payload: CronPayload
  state: CronState
  created_at: number
}

/**
 * Cron store (.cron.json structure)
 */
export interface CronStore {
  jobs: CronJob[]
}

// ============================================================================
// Frontend Extension Types
// ============================================================================

/**
 * Frontend session metadata (stored in browser LocalStorage)
 */
export interface FrontendSessionMeta {
  session_key: string
  display_name: string
  pinned: boolean
  tags: string[]
  last_viewed: string
  unread_count: number
}

/**
 * Provider extended information for UI
 */
export interface ProviderMeta {
  name: ProviderName
  display_name: string
  keywords: string[]
  is_gateway: boolean
  is_local: boolean
  icon?: string
  documentation_url?: string
  status: 'active' | 'inactive' | 'error'
  last_test?: string
  test_result?: string
}

/**
 * Channel extended information for UI
 */
export interface ChannelMeta {
  name: ChannelName
  display_name: string
  icon?: string
  status: 'running' | 'stopped' | 'error'
  message_count: number
  last_message_at?: string
  error_message?: string
}

// ============================================================================
// System Types
// ============================================================================

/**
 * System status
 */
export interface SystemStatus {
  nanobot_running: boolean
  enabled_channels: number
  configured_providers: number
  total_sessions: number
  uptime?: number
}

/**
 * API Error response
 */
export interface ApiError {
  error: string
  details?: string
  code?: string
}

/**
 * API Success response with data
 */
export interface ApiResponse<T> {
  data: T
  success: true
}

// ============================================================================
// Streaming Chat Types
// ============================================================================

/**
 * Streaming event types from the backend
 */
export type StreamEventType =
  | 'content'
  | 'reasoning'
  | 'tool_call_start'
  | 'tool_call_end'
  | 'iteration_start'
  | 'done'
  | 'error'

/**
 * Base stream event
 */
export interface BaseStreamEvent {
  type: StreamEventType
}

/**
 * Content stream event - text chunk from LLM
 */
export interface ContentStreamEvent extends BaseStreamEvent {
  type: 'content'
  content: string
}

/**
 * Reasoning stream event - reasoning content (DeepSeek-R1, etc.)
 */
export interface ReasoningStreamEvent extends BaseStreamEvent {
  type: 'reasoning'
  content: string
}

/**
 * Tool call start event
 */
export interface ToolCallStartEvent extends BaseStreamEvent {
  type: 'tool_call_start'
  tool_id: string
  name: string
  arguments: Record<string, any>
}

/**
 * Tool call end event with result
 */
export interface ToolCallEndEvent extends BaseStreamEvent {
  type: 'tool_call_end'
  tool_id: string
  name: string
  result: string
}

/**
 * Agent iteration start event
 */
export interface IterationStartEvent extends BaseStreamEvent {
  type: 'iteration_start'
  iteration: number
  max_iterations: number
}

/**
 * Processing complete event
 */
export interface DoneStreamEvent extends BaseStreamEvent {
  type: 'done'
  content: string
  tools_used: string[]
}

/**
 * Error event
 */
export interface ErrorStreamEvent extends BaseStreamEvent {
  type: 'error'
  error: string
}

/**
 * Union type for all stream events
 */
export type StreamEvent =
  | ContentStreamEvent
  | ReasoningStreamEvent
  | ToolCallStartEvent
  | ToolCallEndEvent
  | IterationStartEvent
  | DoneStreamEvent
  | ErrorStreamEvent

/**
 * Tool call state for UI display
 */
export interface ToolCallState {
  id: string
  name: string
  arguments: Record<string, any>
  result?: string
  status: 'running' | 'completed' | 'error'
  startTime: number
  endTime?: number
}

/**
 * Message with streaming metadata
 */
export interface StreamingMessage extends SessionMessage {
  isStreaming?: boolean
  reasoningContent?: string
  toolCalls?: ToolCallState[]
  currentIteration?: number
  maxIterations?: number
}

/**
 * Chat state for managing streaming conversations
 */
export interface ChatState {
  messages: StreamingMessage[]
  isStreaming: boolean
  currentMessage: StreamingMessage | null
  error: string | null
}
