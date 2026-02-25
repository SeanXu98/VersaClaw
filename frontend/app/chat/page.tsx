'use client'

import { useEffect, useState, useRef, useCallback } from 'react'
import { MessageSquare, Send, Trash2, Plus, ArrowLeft, ChevronDown, Wrench, Brain, Loader2, CheckCircle, XCircle, Zap } from 'lucide-react'
import Link from 'next/link'
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
  ErrorStreamEvent
} from '@/types/nanobot'

export default function ChatPage() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [currentSession, setCurrentSession] = useState<Session | null>(null)
  const [messages, setMessages] = useState<StreamingMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [showSessionList, setShowSessionList] = useState(false)

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

  // 消息列表滚动引用
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

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
          setSelectedModel(data.data.models[0].models[0])
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

      case 'tool_call_start': {
        const toolEvent = event as ToolCallStartEvent
        setActiveToolCalls(prev => [...prev, {
          id: toolEvent.tool_id,
          name: toolEvent.name,
          arguments: toolEvent.arguments,
          status: 'running',
          startTime: Date.now()
        }])
        break
      }

      case 'tool_call_end': {
        const toolEvent = event as ToolCallEndEvent
        setActiveToolCalls(prev => prev.map(tc =>
          tc.id === toolEvent.tool_id
            ? { ...tc, result: toolEvent.result, status: 'completed', endTime: Date.now() }
            : tc
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
        // 添加最终的助手消息
        const finalMessage: StreamingMessage = {
          role: 'assistant',
          content: doneEvent.content || streamingContent,
          timestamp: new Date().toISOString(),
          isStreaming: false,
          reasoningContent: streamingReasoning || undefined,
          toolCalls: activeToolCalls.length > 0 ? activeToolCalls : undefined,
          tools_used: doneEvent.tools_used
        }
        setMessages(prev => [...prev, finalMessage])
        resetStreamingState()
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

  // 发送流式消息
  const handleSendMessage = async () => {
    if (!input.trim() || loading || isStreaming) return

    const userMessage: StreamingMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
      isStreaming: false
    }

    // 添加用户消息
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setIsStreaming(true)

    // 创建AbortController用于取消请求
    abortControllerRef.current = new AbortController()

    try {
      const response = await fetch('/api/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input.trim(),
          sessionKey: currentSession?.key,
          model: selectedModel || undefined
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
    setShowSessionList(false)
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

  // 格式化工具参数显示
  const formatToolArguments = (args: Record<string, any>): string => {
    try {
      return JSON.stringify(args, null, 2)
    } catch {
      return String(args)
    }
  }

  // 截断工具结果显示
  const truncateResult = (result: string, maxLength: number = 200): string => {
    if (result.length <= maxLength) return result
    return result.slice(0, maxLength) + '...'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-3">
            <Link href="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="text-lg font-semibold">首页</span>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-cyan-600 rounded-lg flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">聊天</h1>
                <p className="text-sm text-slate-500">与 Nanobot 对话</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowSessionList(!showSessionList)}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
                title="会话列表"
              >
                <Plus className="w-5 h-5 text-slate-600" />
              </button>
              {currentSession && (
                <button
                  onClick={() => handleDeleteSession(currentSession.key)}
                  className="p-2 rounded-lg hover:bg-red-50 transition-colors"
                  title="删除会话"
                >
                  <Trash2 className="w-5 h-5 text-slate-600 hover:text-red-600" />
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* 会话列表弹窗 */}
      {showSessionList && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between p-4 border-b border-slate-200">
              <h2 className="text-lg font-semibold">选择会话</h2>
              <button
                onClick={() => setShowSessionList(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                ✕
              </button>
            </div>
            <div className="p-4 space-y-2">
              <button
                onClick={handleNewSession}
                className="w-full text-left px-4 py-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4 mr-2 inline" />
                新建会话
              </button>
              {sessions.map(session => (
                <button
                  key={session.key}
                  onClick={() => {
                    setCurrentSession(session)
                    setShowSessionList(false)
                  }}
                  className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                    currentSession?.key === session.key
                      ? 'bg-blue-100 text-blue-800'
                      : 'hover:bg-slate-100 text-slate-700'
                  }`}
                >
                  <div className="font-medium">{session.metadata.title}</div>
                  <div className="text-xs text-slate-500">{formatTime(session.metadata.updated_at)}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <main className="flex-1 flex flex-col">
        <div className="flex-1 overflow-auto p-4">
          <div className="max-w-4xl mx-auto">
            {/* 当前会话信息 */}
            {currentSession && (
              <div className="mb-4 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-lg border border-slate-200">
                <div className="flex items-center justify-between flex-wrap gap-2">
                  <div className="text-sm text-slate-600">
                    当前会话: <span className="font-medium text-slate-800">{currentSession.metadata.title}</span>
                    <span className="mx-2">·</span>
                    <span className="text-slate-500">{messages.length} 条消息</span>
                  </div>

                  {/* 模型选择器 */}
                  {availableModels.length > 0 && (
                    <div className="relative">
                      <button
                        onClick={() => setShowModelSelector(!showModelSelector)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm text-slate-700 transition-colors"
                      >
                        <span className="font-medium">{selectedModel || '选择模型'}</span>
                        <ChevronDown className="w-4 h-4" />
                      </button>

                      {showModelSelector && (
                        <div className="absolute right-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-slate-200 z-20 max-h-64 overflow-auto">
                          {availableModels.map((provider) => (
                            <div key={provider.provider} className="border-b border-slate-100 last:border-b-0">
                              <div className="px-3 py-2 text-xs font-semibold text-slate-500 bg-slate-50 uppercase">
                                {provider.provider}
                              </div>
                              {provider.models.map((model) => (
                                <button
                                  key={model}
                                  onClick={() => {
                                    setSelectedModel(model)
                                    setShowModelSelector(false)
                                  }}
                                  className={`w-full text-left px-3 py-2 text-sm hover:bg-blue-50 transition-colors ${
                                    selectedModel === model ? 'bg-blue-50 text-blue-700' : 'text-slate-700'
                                  }`}
                                >
                                  {model}
                                </button>
                              ))}
                            </div>
                          ))}
                        </div>
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
                        {/* 推理过程展示 */}
                        {msg.role === 'assistant' && msg.reasoningContent && (
                          <div className="mb-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                            <div className="flex items-center gap-2 text-amber-700 text-xs font-medium mb-2">
                              <Brain className="w-4 h-4" />
                              推理过程
                            </div>
                            <div className="text-sm text-amber-800 whitespace-pre-wrap">
                              {msg.reasoningContent}
                            </div>
                          </div>
                        )}

                        {/* 工具调用展示 */}
                        {msg.role === 'assistant' && msg.toolCalls && msg.toolCalls.length > 0 && (
                          <div className="mb-3 space-y-2">
                            {msg.toolCalls.map((tool, ti) => (
                              <div key={`tool-${ti}`} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                                <div className="flex items-center gap-2 text-slate-700 text-xs font-medium mb-2">
                                  <Wrench className="w-4 h-4" />
                                  <span>{tool.name}</span>
                                  {tool.status === 'completed' ? (
                                    <CheckCircle className="w-4 h-4 text-green-500 ml-auto" />
                                  ) : tool.status === 'error' ? (
                                    <XCircle className="w-4 h-4 text-red-500 ml-auto" />
                                  ) : (
                                    <Loader2 className="w-4 h-4 text-blue-500 ml-auto animate-spin" />
                                  )}
                                </div>
                                <details className="text-xs">
                                  <summary className="cursor-pointer text-slate-500 hover:text-slate-700">
                                    查看参数
                                  </summary>
                                  <pre className="mt-2 p-2 bg-slate-100 rounded text-slate-600 overflow-auto">
                                    {formatToolArguments(tool.arguments)}
                                  </pre>
                                </details>
                                {tool.result && (
                                  <details className="text-xs mt-2">
                                    <summary className="cursor-pointer text-slate-500 hover:text-slate-700">
                                      查看结果
                                    </summary>
                                    <pre className="mt-2 p-2 bg-slate-100 rounded text-slate-600 overflow-auto max-h-40">
                                      {tool.result}
                                    </pre>
                                  </details>
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* 消息内容 */}
                        <div className="text-sm whitespace-pre-wrap break-words">
                          {msg.content}
                        </div>

                        <div className="text-xs mt-2 opacity-60">
                          {formatTime(msg.timestamp || new Date().toISOString())}
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* 流式消息展示 */}
                  {isStreaming && (
                    <div className="flex justify-start">
                      <div className="max-w-[85%] rounded-2xl px-4 py-3 bg-white text-slate-800 border border-slate-200 shadow-sm">
                        {/* 迭代指示器 */}
                        {maxIterations > 0 && (
                          <div className="flex items-center gap-2 text-xs text-slate-500 mb-2">
                            <Zap className="w-4 h-4" />
                            <span>迭代 {currentIteration}/{maxIterations}</span>
                          </div>
                        )}

                        {/* 实时推理过程 */}
                        {streamingReasoning && (
                          <div className="mb-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                            <div className="flex items-center gap-2 text-amber-700 text-xs font-medium mb-2">
                              <Brain className="w-4 h-4 animate-pulse" />
                              正在推理...
                            </div>
                            <div className="text-sm text-amber-800 whitespace-pre-wrap">
                              {streamingReasoning}
                            </div>
                          </div>
                        )}

                        {/* 实时工具调用 */}
                        {activeToolCalls.length > 0 && (
                          <div className="mb-3 space-y-2">
                            {activeToolCalls.map((tool) => (
                              <div key={tool.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                                <div className="flex items-center gap-2 text-slate-700 text-xs font-medium mb-2">
                                  <Wrench className="w-4 h-4" />
                                  <span>{tool.name}</span>
                                  {tool.status === 'running' ? (
                                    <Loader2 className="w-4 h-4 text-blue-500 ml-auto animate-spin" />
                                  ) : (
                                    <CheckCircle className="w-4 h-4 text-green-500 ml-auto" />
                                  )}
                                </div>
                                <details className="text-xs" open={tool.status === 'running'}>
                                  <summary className="cursor-pointer text-slate-500 hover:text-slate-700">
                                    查看参数
                                  </summary>
                                  <pre className="mt-2 p-2 bg-slate-100 rounded text-slate-600 overflow-auto">
                                    {formatToolArguments(tool.arguments)}
                                  </pre>
                                </details>
                                {tool.result && (
                                  <div className="mt-2 text-xs">
                                    <div className="text-slate-500 mb-1">执行结果:</div>
                                    <pre className="p-2 bg-green-50 rounded text-green-700 overflow-auto max-h-32">
                                      {truncateResult(tool.result)}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            ))}
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
        <div className="border-t border-slate-200 bg-white">
          <div className="max-w-4xl mx-auto p-4">
            <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }} className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="输入消息... (按 Enter 发送)"
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
                  disabled={loading || !input.trim()}
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
    </div>
  )
}
