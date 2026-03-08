'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import {
  MessageSquare,
  Send,
  Trash2,
  Plus,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  Loader2,
  CheckCircle,
  XCircle,
  PanelRightClose,
  PanelRightOpen,
  Menu,
  X,
  Eye,
  Brain,
  Wrench
} from 'lucide-react'
import Link from 'next/link'
import RightPanel, { ToolRecord, TodoItem } from '@/components/RightPanel'
import ImageUploader from '@/components/ImageUploader'
import type {
  Session,
  ModelInfo,
  StreamEvent,
  StreamingMessage,
  ToolCallState,
  ContentStreamEvent,
  ReasoningStreamEvent,
  ToolCallStartEvent,
  ToolCallEndEvent,
  IterationStartEvent,
  DoneStreamEvent,
  ErrorStreamEvent,
  UploadedImage
} from '@/types/nanobot'

// 后端 API 地址
const BACKEND_URL = process.env.NEXT_PUBLIC_NANOBOT_API_URL || 'http://localhost:18790'

// 获取完整的图片 URL
function getFullImageUrl(url: string): string {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url
  }
  // 相对路径，添加后端地址
  return `${BACKEND_URL}${url}`
}

// 可折叠的消息详情组件（思考过程、工具调用）
function CollapsibleSection({
  title,
  icon: Icon,
  children,
  defaultCollapsed = true,
  colorClass = 'amber'
}: {
  title: string
  icon: React.ElementType
  children: React.ReactNode
  defaultCollapsed?: boolean
  colorClass?: 'amber' | 'blue' | 'green'
}) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed)

  const colorMap = {
    amber: {
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-700',
      contentText: 'text-amber-800'
    },
    blue: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-700',
      contentText: 'text-blue-800'
    },
    green: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-700',
      contentText: 'text-green-800'
    }
  }

  const colors = colorMap[colorClass]

  return (
    <div className={`mb-2 ${colors.bg} rounded-lg border ${colors.border}`}>
      <button
        className="w-full flex items-center gap-2 p-2 text-left"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <Icon className={`w-4 h-4 ${colors.text}`} />
        <span className={`text-xs font-medium ${colors.text}`}>{title}</span>
        {isCollapsed ? (
          <ChevronDown className={`w-3 h-3 ${colors.text} ml-auto`} />
        ) : (
          <ChevronUp className={`w-3 h-3 ${colors.text} ml-auto`} />
        )}
      </button>
      {!isCollapsed && (
        <div className={`px-3 pb-2 text-xs ${colors.contentText} whitespace-pre-wrap break-words max-h-40 overflow-y-auto`}>
          {children}
        </div>
      )}
    </div>
  )
}

// 从消息内容中提取文本（处理多模态格式）
function extractTextContent(content: string | any[] | null | undefined): string {
  if (!content) return ''
  if (typeof content === 'string') {
    // 过滤掉图片标记 [图片: xxx.png]
    return content.replace(/\[图片:[^\]]+\]/g, '').replace(/\[image\]/gi, '').trim()
  }
  if (Array.isArray(content)) {
    return content
      .filter(block => block.type === 'text')
      .map(block => block.text.replace(/\[图片:[^\]]+\]/g, '').replace(/\[image\]/gi, '').trim())
      .join('\n')
      .trim()
  }
  return String(content)
}

// 从消息内容中提取图片ID（处理 [图片: xxx.png] 格式）
function extractImageIds(content: string | any[] | null | undefined): string[] {
  if (!content) return []
  let text = ''
  if (typeof content === 'string') {
    text = content
  } else if (Array.isArray(content)) {
    text = content
      .filter(block => block.type === 'text')
      .map(block => block.text)
      .join('\n')
  } else {
    return []
  }

  // 匹配 [图片: temp_xxx.png] 或 [图片: xxx.png] 格式
  const imageMatches = text.match(/\[图片:\s*([^\]]+)\]/g)
  if (!imageMatches) return []

  return imageMatches
    .map(match => {
      const idMatch = match.match(/\[图片:\s*([^\]]+)\]/)
      return idMatch ? idMatch[1].trim() : null
    })
    .filter((id): id is string => id !== null)
}

// 从图片文件名中提取实际的图片 ID
function extractActualImageId(filename: string): string | null {
  // 文件名格式可能是:
  // 1. temp_{uuid}.{ext} - 需要提取 uuid 部分
  // 2. {uuid}.{ext} - 直接使用 uuid 部分
  // 3. {uuid} - 无扩展名

  // 去除扩展名
  const nameWithoutExt = filename.replace(/\.[^.]+$/, '')

  // 如果是 temp_ 开头的临时文件，提取 UUID 部分
  if (nameWithoutExt.startsWith('temp_')) {
    // temp_{uuid} -> {uuid}
    return nameWithoutExt.substring(5)
  }

  // 否则直接使用文件名（假设就是 UUID）
  // 验证是否是有效的 UUID 格式
  const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
  if (uuidPattern.test(nameWithoutExt)) {
    return nameWithoutExt
  }

  // 如果不是标准 UUID，返回原始文件名让后端尝试匹配
  return nameWithoutExt
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSession, setCurrentSession] = useState<Session | null>(null)
  const [messages, setMessages] = useState<StreamingMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  // 侧边栏状态
  const [showLeftPanel, setShowLeftPanel] = useState(true)

  // 模型选择相关状态
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([])
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [showModelSelector, setShowModelSelector] = useState(false)

  // 流式消息相关状态
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const [streamingReasoning, setStreamingReasoning] = useState('')
  const [activeToolCalls, setActiveToolCalls] = useState<ToolCallState[]>([])
  const [currentIteration, setCurrentIteration] = useState(0)
  const [maxIterations, setMaxIterations] = useState(0)

  // 右侧面板状态
  const [showRightPanel, setShowRightPanel] = useState(true)
  const [toolRecords, setToolRecords] = useState<ToolRecord[]>([])
  const [todos, setTodos] = useState<TodoItem[]>([])

  // 图片上传相关状态
  const [pendingImages, setPendingImages] = useState<UploadedImage[]>([])

  // 图片预览模态框状态
  const [previewImage, setPreviewImage] = useState<string | null>(null)

  // 消息列表滚动引用
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  // 判断当前选中的模型是否是 Vision 模型
  const isVisionModel = useCallback(() => {
    if (!selectedModel) return false
    for (const provider of availableModels) {
      if (provider.vision_models?.includes(selectedModel)) {
        return true
      }
    }
    // 常见的 Vision 模型关键词
    const visionKeywords = ['vision', 'gpt-4o', 'gpt-4-turbo', 'claude-3', 'gemini', 'qwen-vl', 'glm-4v']
    return visionKeywords.some(keyword => selectedModel.toLowerCase().includes(keyword))
  }, [selectedModel, availableModels])

  // 自动滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, streamingContent, streamingReasoning, activeToolCalls, scrollToBottom])

  useEffect(() => {
    loadSessions()
    loadAvailableModels()
  }, [])

  useEffect(() => {
    if (currentSession) {
      loadSessionMessages(currentSession.key)
    }
  }, [currentSession])

  const loadAvailableModels = async () => {
    try {
      const response = await fetch('/api/models/available')
      const data = await response.json()
      if (data.success) {
        setAvailableModels(data.data.models)
        if (data.data.models.length > 0 && data.data.models[0].models.length > 0) {
          // 优先选择 Vision 模型
          const firstProvider = data.data.models[0]
          if (firstProvider.vision_models && firstProvider.vision_models.length > 0) {
            setSelectedModel(firstProvider.vision_models[0])
          } else {
            setSelectedModel(firstProvider.models[0])
          }
        }
      }
    } catch (error) {
      console.error('Failed to load available models:', error)
    }
  }

  const loadSessions = async () => {
    try {
      const response = await fetch('/api/chat/sessions')
      const data = await response.json()
      if (data.success) {
        setSessions(data.data.sessions)
        if (data.data.sessions.length > 0 && !currentSession) {
          setCurrentSession(data.data.sessions[0])
        }
      }
    } catch (error) {
      console.error('Failed to load sessions:', error)
    }
  }

  const loadSessionMessages = async (sessionKey: string) => {
    try {
      const response = await fetch(`/api/chat/sessions/${sessionKey}`)
      const data = await response.json()
      if (data.success) {
        setMessages(data.data.messages.map((msg: any) => ({
          ...msg,
          isStreaming: false
        })))
      }
    } catch (error) {
      console.error('Failed to load session:', error)
    }
  }

  // 解析SSE事件
  const parseSSEEvent = (line: string): StreamEvent | null => {
    if (!line.startsWith('data: ')) return null
    try {
      return JSON.parse(line.slice(6)) as StreamEvent
    } catch {
      return null
    }
  }

  // 处理流式事件
  const handleStreamEvent = (event: StreamEvent) => {
    switch (event.type) {
      case 'content':
        setStreamingContent(prev => prev + (event as ContentStreamEvent).content)
        break

      case 'reasoning':
        setStreamingReasoning(prev => prev + (event as ReasoningStreamEvent).content)
        break

      case 'heartbeat':
        // 心跳事件，不需要特殊处理，只是保持连接活跃
        // 用户会看到"正在思考..."的动画继续播放
        break

      case 'tool_call_start': {
        const toolEvent = event as ToolCallStartEvent
        // 处理 arguments 可能是字符串或对象的情况
        let parsedArgs: Record<string, any>
        if (typeof toolEvent.arguments === 'string') {
          try {
            parsedArgs = JSON.parse(toolEvent.arguments)
          } catch {
            // 如果不是 JSON 字符串，包装成对象
            parsedArgs = { value: toolEvent.arguments }
          }
        } else if (toolEvent.arguments && typeof toolEvent.arguments === 'object') {
          parsedArgs = toolEvent.arguments
        } else {
          parsedArgs = {}
        }

        const newTool: ToolCallState = {
          id: toolEvent.tool_id,
          name: toolEvent.name,
          arguments: parsedArgs,
          status: 'running',
          startTime: Date.now()
        }
        setActiveToolCalls(prev => [...prev, newTool])

        // 添加到工具记录
        const toolRecord: ToolRecord = {
          id: toolEvent.tool_id,
          name: toolEvent.name,
          arguments: parsedArgs,
          status: 'running',
          startTime: Date.now(),
          iteration: currentIteration || undefined
        }
        setToolRecords(prev => [...prev, toolRecord])
        break
      }

      case 'tool_call_end': {
        const toolEvent = event as ToolCallEndEvent
        setActiveToolCalls(prev => prev.map(tc =>
          tc.id === toolEvent.tool_id
            ? { ...tc, result: toolEvent.result, status: 'completed', endTime: Date.now() }
            : tc
        ))

        // 更新工具记录
        setToolRecords(prev => prev.map(tr =>
          tr.id === toolEvent.tool_id
            ? { ...tr, result: toolEvent.result, status: 'completed', endTime: Date.now() }
            : tr
        ))
        break
      }

      case 'iteration_start': {
        const iterEvent = event as IterationStartEvent
        setCurrentIteration(iterEvent.iteration)
        setMaxIterations(iterEvent.max_iterations)
        break
      }

      case 'done': {
        const doneEvent = event as DoneStreamEvent
        // 优先使用流式过程中的 reasoning，否则使用 done 事件中的
        const finalReasoning = streamingReasoning || (doneEvent as any).reasoning_content || undefined
        // 添加最终的助手消息
        const finalMessage: StreamingMessage = {
          role: 'assistant',
          content: doneEvent.content || streamingContent,
          timestamp: new Date().toISOString(),
          isStreaming: false,
          reasoningContent: finalReasoning,
          toolCalls: activeToolCalls.length > 0 ? activeToolCalls : undefined,
          tools_used: doneEvent.tools_used
        }
        setMessages(prev => [...prev, finalMessage])
        resetStreamingState()
        // 刷新会话列表
        loadSessions()
        break
      }

      case 'error': {
        const errorEvent = event as ErrorStreamEvent
        console.error('Stream error:', errorEvent.error)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `错误: ${errorEvent.error}`,
          timestamp: new Date().toISOString(),
          isStreaming: false
        }])
        resetStreamingState()
        break
      }
    }
  }

  // 重置流式状态
  const resetStreamingState = () => {
    setIsStreaming(false)
    setLoading(false)
    setStreamingContent('')
    setStreamingReasoning('')
    setActiveToolCalls([])
    setCurrentIteration(0)
    setMaxIterations(0)
    abortControllerRef.current = null
  }

  // 清除工具历史记录
  const handleClearToolHistory = () => {
    setToolRecords([])
  }

  // 图片上传成功回调
  const handleImageUploadSuccess = (images: UploadedImage[]) => {
    setPendingImages(prev => [...prev, ...images])
  }

  // 移除图片
  const handleRemoveImage = (imageId: string) => {
    setPendingImages(prev => prev.filter(img => img.id !== imageId))
  }

  // 发送流式消息
  const handleSendMessage = async () => {
    if ((!input.trim() && pendingImages.length === 0) || loading || isStreaming) return

    const userMessage: StreamingMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
      isStreaming: false,
      images: pendingImages.length > 0 ? pendingImages : undefined
    }

    // 添加用户消息
    setMessages(prev => [...prev, userMessage])
    const messageToSend = input.trim()
    const imagesToSend = [...pendingImages]
    setInput('')
    setPendingImages([])
    setLoading(true)
    setIsStreaming(true)

    // 创建AbortController用于取消请求
    abortControllerRef.current = new AbortController()

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageToSend,
          sessionKey: currentSession?.key,
          model: selectedModel || undefined,
          images: imagesToSend.length > 0 ? imagesToSend : undefined
        }),
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.trim()) {
            const event = parseSSEEvent(line)
            if (event) {
              handleStreamEvent(event)
            }
          }
        }
      }

      // 处理剩余的buffer
      if (buffer.trim()) {
        const event = parseSSEEvent(buffer)
        if (event) {
          handleStreamEvent(event)
        }
      }

    } catch (error: any) {
      if (error.name === 'AbortError') {
        console.log('Stream aborted by user')
      } else {
        console.error('Failed to send message:', error)
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `发送失败: ${error.message}`,
          timestamp: new Date().toISOString(),
          isStreaming: false
        }])
      }
      resetStreamingState()
    }
  }

  // 取消流式响应
  const handleCancelStream = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }

  const handleDeleteSession = async (sessionKey: string) => {
    if (!confirm('确定要删除这个会话吗？')) return

    try {
      const response = await fetch(`/api/chat/sessions/${sessionKey}`, {
        method: 'DELETE'
      })
      const data = await response.json()

      if (data.success) {
        if (currentSession?.key === sessionKey) {
          setCurrentSession(null)
          setMessages([])
          // 清除工具记录和待办
          setToolRecords([])
          setTodos([])
        }
        await loadSessions()
      } else {
        alert('删除失败')
      }
    } catch (error) {
      console.error('Failed to delete session:', error)
      alert('删除失败')
    }
  }

  const handleNewSession = () => {
    const newSessionKey = `web:${Date.now()}`
    const newSession: Session = {
      key: newSessionKey,
      filename: `${newSessionKey}.jsonl`,
      metadata: {
        session_id: newSessionKey,
        title: '新对话',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      },
      messageCount: 0
    }

    setCurrentSession(newSession)
    setMessages([])
    // 清除工具记录和待办
    setToolRecords([])
    setTodos([])
    setPendingImages([])
    // 将新会话添加到列表开头
    setSessions(prev => [newSession, ...prev])
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)

    if (minutes < 1) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}小时前`
    const days = Math.floor(hours / 24)
    return `${days}天前`
  }

  return (
    <div className="h-screen flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-20 flex-shrink-0">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              {/* 左侧面板切换按钮 */}
              <button
                onClick={() => setShowLeftPanel(!showLeftPanel)}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
                title={showLeftPanel ? '隐藏会话列表' : '显示会话列表'}
              >
                <Menu className="w-5 h-5 text-slate-600" />
              </button>
              <Link href="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors">
                <ArrowLeft className="w-5 h-5" />
                <span className="hidden sm:inline text-lg font-semibold">首页</span>
              </Link>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-600 rounded-lg flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800">聊天</h1>
                <p className="text-xs text-slate-500">与 Nanobot 对话</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* 右侧面板切换按钮 */}
              <button
                onClick={() => setShowRightPanel(!showRightPanel)}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
                title={showRightPanel ? '隐藏执行面板' : '显示执行面板'}
              >
                {showRightPanel ? (
                  <PanelRightClose className="w-5 h-5 text-slate-600" />
                ) : (
                  <PanelRightOpen className="w-5 h-5 text-slate-600" />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区域 - 三栏布局 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧会话列表 */}
        {showLeftPanel && (
          <div className="w-64 flex-shrink-0 border-r border-slate-200 bg-white flex flex-col">
            <div className="p-3 border-b border-slate-200">
              <button
                onClick={handleNewSession}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span>新建会话</span>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {sessions.length === 0 ? (
                <div className="p-4 text-center text-slate-400 text-sm">
                  <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>暂无会话</p>
                </div>
              ) : (
                <div className="p-2 space-y-1">
                  {sessions.map(session => (
                    <div
                      key={session.key}
                      className={`group relative rounded-lg transition-colors ${
                        currentSession?.key === session.key
                          ? 'bg-blue-50 border border-blue-200'
                          : 'hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      <button
                        onClick={() => {
                          setCurrentSession(session)
                          setToolRecords([])
                          setTodos([])
                        }}
                        className="w-full text-left px-3 py-2.5"
                      >
                        <div className="font-medium text-sm text-slate-700 truncate">
                          {(session as any).title || session.key}
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          {formatTime(session.metadata.updated_at)}
                          <span className="mx-1">·</span>
                          {session.messageCount} 条消息
                        </div>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteSession(session.key)
                        }}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded opacity-0 group-hover:opacity-100 hover:bg-red-50 text-slate-400 hover:text-red-500 transition-all"
                        title="删除会话"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 中间聊天区域 */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <div className="flex-1 overflow-auto p-4">
            <div className="max-w-3xl mx-auto">
              {/* 当前会话信息 */}
              {currentSession && (
                <div className="mb-4 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-lg border border-slate-200">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <div className="text-sm text-slate-600">
                      当前会话: <span className="font-medium text-slate-800">{currentSession.metadata.title}</span>
                      <span className="mx-2">·</span>
                      <span className="text-slate-500">{messages.length} 条消息</span>
                      {toolRecords.length > 0 && (
                        <>
                          <span className="mx-2">·</span>
                          <span className="text-blue-500">{toolRecords.length} 次工具调用</span>
                        </>
                      )}
                    </div>

                    {/* 模型选择器 */}
                    {availableModels.length > 0 && (
                      <div className="relative">
                        <button
                          onClick={() => setShowModelSelector(!showModelSelector)}
                          className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm text-slate-700 transition-colors"
                        >
                          {isVisionModel() && (
                            <span title="支持图片">
                              <Eye className="w-3.5 h-3.5 text-purple-500" />
                            </span>
                          )}
                          <span className="font-medium">{selectedModel || '选择模型'}</span>
                          <ChevronDown className="w-4 h-4" />
                        </button>

                        {showModelSelector && (
                          <>
                            <div
                              className="fixed inset-0 z-10"
                              onClick={() => setShowModelSelector(false)}
                            />
                            <div className="absolute right-0 mt-1 w-72 bg-white rounded-lg shadow-lg border border-slate-200 z-20 max-h-80 overflow-auto">
                              {availableModels.map((provider) => (
                                <div key={provider.provider} className="border-b border-slate-100 last:border-b-0">
                                  <div className="px-3 py-2 text-xs font-semibold text-slate-500 bg-slate-50 uppercase sticky top-0">
                                    {provider.provider}
                                  </div>
                                  {provider.models.map((model) => {
                                    const isVision = provider.vision_models?.includes(model)
                                    return (
                                      <button
                                        key={model}
                                        onClick={() => {
                                          setSelectedModel(model)
                                          setShowModelSelector(false)
                                        }}
                                        className={`w-full text-left px-3 py-2 text-sm hover:bg-blue-50 transition-colors flex items-center gap-2 ${
                                          selectedModel === model ? 'bg-blue-50 text-blue-700' : 'text-slate-700'
                                        }`}
                                      >
                                        {isVision && (
                                          <Eye className="w-3.5 h-3.5 text-purple-500 flex-shrink-0" />
                                        )}
                                        <span className="truncate">{model}</span>
                                      </button>
                                    )
                                  })}
                                </div>
                              ))}
                            </div>
                          </>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* 消息列表 */}
              <div className="space-y-4 mb-4">
                {messages.length === 0 && !isStreaming ? (
                  <div className="text-center py-12 text-slate-500">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 text-slate-400" />
                    <p className="text-lg">开始新对话</p>
                    <p className="text-sm mt-2">输入消息开始与 Nanobot 聊天</p>
                    {isVisionModel() && (
                      <p className="text-xs mt-2 text-purple-500">
                        <Eye className="w-3 h-3 inline mr-1" />
                        当前模型支持图片理解
                      </p>
                    )}
                  </div>
                ) : (
                  <>
                    {messages.map((msg, index) => (
                      <div
                        key={`msg-${index}`}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                            msg.role === 'user'
                              ? 'bg-blue-600 text-white'
                              : 'bg-white text-slate-800 border border-slate-200 shadow-sm'
                          }`}
                        >
                          {/* 用户图片展示 */}
                          {msg.role === 'user' && msg.images && msg.images.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-2">
                              {msg.images.map((img) => (
                                <img
                                  key={img.id}
                                  src={getFullImageUrl(img.thumbnail_url || img.url)}
                                  alt={img.filename}
                                  className="w-20 h-20 object-cover rounded-lg border border-white/20 cursor-pointer hover:opacity-80 transition-opacity"
                                  onClick={() => setPreviewImage(getFullImageUrl(img.url))}
                                />
                              ))}
                            </div>
                          )}
                          {/* 历史消息中的图片展示（从 [图片: xxx.png] 格式解析） */}
                          {msg.role === 'user' && extractImageIds(msg.content).length > 0 && !msg.images && (
                            <div className="flex flex-wrap gap-2 mb-2">
                              {extractImageIds(msg.content).map((imageFilename) => {
                                const actualId = extractActualImageId(imageFilename)
                                return actualId ? (
                                  <img
                                    key={imageFilename}
                                    src={`/api/upload/image/${actualId}?thumbnail`}
                                    alt={imageFilename}
                                    className="w-20 h-20 object-cover rounded-lg border border-white/20 cursor-pointer hover:opacity-80 transition-opacity"
                                    onError={(e) => {
                                      // 缩略图加载失败时尝试加载原图
                                      const target = e.target as HTMLImageElement
                                      if (target.src.includes('thumbnail')) {
                                        target.src = `/api/upload/image/${actualId}`
                                      } else {
                                        target.style.display = 'none'
                                      }
                                    }}
                                    onClick={() => {
                                      // 点击在模态框中查看大图
                                      setPreviewImage(`/api/upload/image/${actualId}`)
                                    }}
                                  />
                                ) : null
                              }).filter(Boolean)}
                            </div>
                          )}
                          {/* 历史消息中的推理过程展示 - 可折叠 */}
                          {msg.role === 'assistant' && msg.reasoningContent && (
                            <CollapsibleSection
                              title="思考过程"
                              icon={Brain}
                              colorClass="amber"
                              defaultCollapsed={true}
                            >
                              {msg.reasoningContent}
                            </CollapsibleSection>
                          )}
                          {/* 历史消息中的工具调用展示 - 可折叠 */}
                          {msg.role === 'assistant' && msg.toolCalls && msg.toolCalls.length > 0 && (
                            <CollapsibleSection
                              title={`工具调用 (${msg.toolCalls.length})`}
                              icon={Wrench}
                              colorClass="blue"
                              defaultCollapsed={true}
                            >
                              {msg.toolCalls.map((tc, i) => (
                                <div key={tc.id || i} className="mb-2 pb-2 border-b border-blue-100 last:border-b-0">
                                  <div className="font-medium">{tc.name}</div>
                                  <div className="text-blue-600 text-xs mt-1">
                                    参数: {JSON.stringify(tc.arguments, null, 2)}
                                  </div>
                                  {tc.result && (
                                    <div className="text-green-600 text-xs mt-1">
                                      结果: {tc.result.substring(0, 200)}{tc.result.length > 200 ? '...' : ''}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </CollapsibleSection>
                          )}
                          {/* 消息内容 */}
                          <div className="text-sm whitespace-pre-wrap break-words">
                            {extractTextContent(msg.content)}
                          </div>

                          <div className="text-xs mt-2 opacity-60">
                            {formatTime(msg.timestamp || new Date().toISOString())}
                            {msg.tools_used && msg.tools_used.length > 0 && (
                              <span className="ml-2">
                                · 使用了 {msg.tools_used.join(', ')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* 流式消息展示 */}
                    {isStreaming && (
                      <div className="flex justify-start">
                        <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-white text-slate-800 border border-slate-200 shadow-sm">
                          {/* 推理过程 - 折叠展示 */}
                          {streamingReasoning && (
                            <div className="mb-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                              <div className="flex items-center gap-2 text-amber-700 text-xs font-medium mb-2">
                                <Brain className="w-4 h-4" />
                                <span>思考过程</span>
                                <Loader2 className="w-3 h-3 animate-spin ml-auto" />
                              </div>
                              <div className="text-xs text-amber-800 whitespace-pre-wrap break-words max-h-40 overflow-y-auto">
                                {streamingReasoning}
                              </div>
                            </div>
                          )}

                          {/* 流式内容 */}
                          {streamingContent && (
                            <div className="text-sm whitespace-pre-wrap break-words">
                              {streamingContent}
                              <span className="inline-block w-2 h-4 bg-blue-500 ml-1 animate-pulse" />
                            </div>
                          )}

                          {/* 加载指示器 */}
                          {!streamingContent && !streamingReasoning && activeToolCalls.length === 0 && (
                            <div className="flex items-center gap-2 text-slate-500">
                              <Loader2 className="w-4 h-4 animate-spin" />
                              <span className="text-sm">正在思考...</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                )}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>

          {/* 输入区域 */}
          <div className="border-t border-slate-200 bg-white flex-shrink-0">
            <div className="max-w-3xl mx-auto p-4">
              {/* 图片上传区域 - 仅 Vision 模型显示 */}
              {isVisionModel() && (
                <div className="mb-3">
                  <ImageUploader
                    onUploadSuccess={handleImageUploadSuccess}
                    onUploadError={(error) => console.error('Upload error:', error)}
                    maxFiles={5}
                    maxSize={10}
                    disabled={isStreaming}
                    pendingImages={pendingImages}
                    onRemoveImage={handleRemoveImage}
                  />
                </div>
              )}

              <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={isVisionModel() ? "输入消息... (可上传图片)" : "输入消息... (按 Enter 发送)"}
                  disabled={loading && !isStreaming}
                  className="flex-1 px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-slate-100 disabled:opacity-50"
                />
                {isStreaming ? (
                  <button
                    type="button"
                    onClick={handleCancelStream}
                    className="px-6 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 transition-all flex items-center gap-2"
                  >
                    停止
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={loading || (!input.trim() && pendingImages.length === 0)}
                    className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:bg-blue-400 disabled:opacity-50 transition-all flex items-center gap-2"
                  >
                    {loading ? (
                      <div className="w-5 h-5 border-2 border-white/30 border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        <span className="hidden sm:inline">发送</span>
                      </>
                    )}
                  </button>
                )}
              </form>
            </div>
          </div>
        </main>

        {/* 右侧面板 */}
        {showRightPanel && (
          <div className="w-80 flex-shrink-0 border-l border-slate-200">
            <RightPanel
              toolRecords={toolRecords}
              activeToolCalls={activeToolCalls.map(tc => ({
                ...tc,
                iteration: currentIteration || undefined
              }))}
              todos={todos}
              currentIteration={currentIteration}
              maxIterations={maxIterations}
              isStreaming={isStreaming}
              onClearHistory={handleClearToolHistory}
            />
          </div>
        )}
      </div>

      {/* 图片预览模态框 */}
      {previewImage && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setPreviewImage(null)}
        >
          <button
            className="absolute top-4 right-4 p-2 bg-white/10 hover:bg-white/20 rounded-full text-white transition-colors"
            onClick={() => setPreviewImage(null)}
          >
            <X className="w-6 h-6" />
          </button>
          <img
            src={previewImage}
            alt="Preview"
            className="max-w-full max-h-full object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  )
}
