'use client'

import { useState, useEffect, useMemo } from 'react'
import {
  Wrench,
  CheckCircle,
  XCircle,
  Loader2,
  ChevronDown,
  ChevronRight,
  ListTodo,
  Clock,
  Trash2,
  Brain,
  Sparkles
} from 'lucide-react'

/**
 * 工具调用记录项
 */
export interface ToolRecord {
  id: string
  name: string
  arguments: Record<string, any>
  result?: string
  status: 'running' | 'completed' | 'error'
  startTime: number
  endTime?: number
  iteration?: number
}

/**
 * 待办事项项
 */
export interface TodoItem {
  id: string
  content: string
  status: 'pending' | 'in_progress' | 'completed'
  createdAt: number
  completedAt?: number
}

interface RightPanelProps {
  // 工具调用记录
  toolRecords: ToolRecord[]
  // 当前正在执行的工具
  activeToolCalls: ToolRecord[]
  // 待办事项（可选，如果不提供则从工具调用中自动生成）
  todos?: TodoItem[]
  // 当前迭代信息
  currentIteration: number
  maxIterations: number
  // 流式状态
  isStreaming: boolean
  // 清除历史记录的回调
  onClearHistory?: () => void
}

// 工具名称到友好描述的映射
const TOOL_DESCRIPTIONS: Record<string, (args: Record<string, any>) => string> = {
  'write_file': (args) => `写入文件: ${args.path || args.filename || '未知'}`,
  'read_file': (args) => `读取文件: ${args.path || args.filename || '未知'}`,
  'web_search': (args) => `搜索: ${args.query || '未知'}`,
  'execute': (args) => `执行命令: ${args.command || '未知'}`,
  'memory_save': (args) => `保存记忆: ${args.key || '未知'}`,
  'memory_recall': (args) => `回忆记忆: ${args.query || '未知'}`,
}

// 从工具记录生成待办事项
function generateTodosFromTools(toolRecords: ToolRecord[], activeToolCalls: ToolRecord[]): TodoItem[] {
  // 使用 Map 按 id 去重，避免重复的待办事项
  const allToolsMap = new Map<string, ToolRecord>()
  // 先添加历史记录
  toolRecords.forEach(tool => {
    allToolsMap.set(tool.id, tool)
  })
  // 再更新活动工具的状态
  activeToolCalls.forEach(tool => {
    const existing = allToolsMap.get(tool.id)
    if (existing) {
      // 如果已存在，更新状态为 running
      allToolsMap.set(tool.id, { ...existing, ...tool, status: 'running' })
    } else {
      allToolsMap.set(tool.id, tool)
    }
  })

  const allTools = Array.from(allToolsMap.values())
  const todos: TodoItem[] = []

  allTools.forEach(tool => {
    const getDescription = TOOL_DESCRIPTIONS[tool.name]
    if (getDescription) {
      todos.push({
        id: `todo-${tool.id}`,
        content: getDescription(tool.arguments),
        status: tool.status === 'running' ? 'in_progress' : 'completed',
        createdAt: tool.startTime,
        completedAt: tool.status === 'completed' ? tool.endTime || tool.startTime : undefined
      })
    }
  })

  return todos
}

/**
 * 格式化时间戳
 */
const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

/**
 * 计算执行时长
 */
const formatDuration = (startTime: number, endTime?: number): string => {
  const end = endTime || Date.now()
  const duration = Math.floor((end - startTime) / 1000)
  if (duration < 60) return `${duration}s`
  const minutes = Math.floor(duration / 60)
  const seconds = duration % 60
  return `${minutes}m ${seconds}s`
}

/**
 * 截断长文本
 */
const truncateText = (text: string, maxLength: number = 150): string => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

/**
 * 格式化参数显示
 */
const formatArguments = (args: Record<string, any>): string => {
  try {
    return JSON.stringify(args, null, 2)
  } catch {
    return String(args)
  }
}

/**
 * 获取工具图标颜色
 */
const getToolIconColor = (name: string): string => {
  const colors: Record<string, string> = {
    'search': 'text-green-500',
    'web_search': 'text-green-500',
    'read_file': 'text-blue-500',
    'write_file': 'text-orange-500',
    'execute': 'text-purple-500',
    'github': 'text-gray-700',
    'memory': 'text-pink-500',
    'cron': 'text-cyan-500',
  }
  return colors[name.toLowerCase()] || 'text-slate-500'
}

export default function RightPanel({
  toolRecords,
  activeToolCalls,
  todos: externalTodos,
  currentIteration,
  maxIterations,
  isStreaming,
  onClearHistory
}: RightPanelProps) {
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set())
  const [showToolHistory, setShowToolHistory] = useState(true)
  const [showTodos, setShowTodos] = useState(true)

  // 使用 toolRecords 作为主要数据源，去重显示
  // 使用 Map 按 id 去重，保留最新的记录
  const allToolsMap = new Map<string, ToolRecord>()
  // 先添加历史记录
  toolRecords.forEach(tool => {
    allToolsMap.set(tool.id, tool)
  })
  // 再更新活动工具的状态
  activeToolCalls.forEach(tool => {
    const existing = allToolsMap.get(tool.id)
    if (existing) {
      // 如果已存在，更新状态为 running
      allToolsMap.set(tool.id, { ...existing, ...tool, status: 'running' })
    } else {
      allToolsMap.set(tool.id, tool)
    }
  })
  const allTools = Array.from(allToolsMap.values())

  // 统计工具执行情况
  const completedCount = allTools.filter(t => t.status === 'completed').length
  const errorCount = allTools.filter(t => t.status === 'error').length
  const runningCount = allTools.filter(t => t.status === 'running').length

  // 生成或使用外部传入的待办事项
  const todos = useMemo(() => {
    if (externalTodos && externalTodos.length > 0) {
      return externalTodos
    }
    // 从工具调用中自动生成待办事项
    return generateTodosFromTools(toolRecords, activeToolCalls)
  }, [externalTodos, toolRecords, activeToolCalls])

  // 统计待办事项
  const pendingTodos = todos.filter(t => t.status === 'pending' || t.status === 'in_progress')
  const completedTodos = todos.filter(t => t.status === 'completed')

  // 自动展开正在运行的工具
  useEffect(() => {
    if (activeToolCalls.length > 0) {
      setExpandedTools(prev => {
        const next = new Set(prev)
        activeToolCalls.forEach(t => next.add(t.id))
        return next
      })
    }
  }, [activeToolCalls])

  const toggleToolExpand = (id: string) => {
    setExpandedTools(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-white to-slate-50/50">
      {/* 头部 */}
      <div className="p-4 border-b border-slate-200 bg-gradient-to-r from-blue-50 via-white to-purple-50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-800">Agent 状态</h2>
            <p className="text-xs text-slate-500">实时执行监控</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* 工具执行记录 */}
        <div className="border-b border-slate-100">
          <button
            onClick={() => setShowToolHistory(!showToolHistory)}
            className="w-full p-4 flex items-center justify-between hover:bg-slate-50/50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center">
                <Wrench className="w-3.5 h-3.5 text-slate-500" />
              </div>
              <span className="font-medium text-slate-700 text-sm">工具执行</span>
              <div className="flex items-center gap-1 ml-2">
                {runningCount > 0 && (
                  <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    执行中{runningCount}
                  </span>
                )}
                {completedCount > 0 && (
                  <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                    完成{completedCount}
                  </span>
                )}
                {errorCount > 0 && (
                  <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
                    失败{errorCount}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {toolRecords.length > 0 && onClearHistory && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    onClearHistory()
                  }}
                  className="p-1 hover:bg-slate-200 rounded text-slate-400 hover:text-red-500 transition-colors"
                  title="清除历史"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
              {showToolHistory ? (
                <ChevronDown className="w-4 h-4 text-slate-400" />
              ) : (
                <ChevronRight className="w-4 h-4 text-slate-400" />
              )}
            </div>
          </button>

          {showToolHistory && (
            <div className="px-4 pb-4 space-y-2">
              {allTools.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm">
                  <Wrench className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p>暂无工具调用</p>
                </div>
              ) : (
                allTools.map((tool) => (
                  <div
                    key={tool.id}
                    className={`rounded-lg border overflow-hidden transition-all ${
                      tool.status === 'running'
                        ? 'bg-blue-50/50 border-blue-200 shadow-sm'
                        : tool.status === 'error'
                        ? 'bg-red-50/50 border-red-200'
                        : 'bg-white border-slate-200'
                    }`}
                  >
                    {/* 工具头部 */}
                    <button
                      onClick={() => toggleToolExpand(tool.id)}
                      className="w-full px-3 py-2.5 flex items-center gap-2 text-left hover:bg-black/5 transition-colors"
                    >
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                        tool.status === 'running'
                          ? 'bg-blue-100'
                          : tool.status === 'completed'
                          ? 'bg-green-100'
                          : 'bg-red-100'
                      }`}>
                        {tool.status === 'running' ? (
                          <Loader2 className="w-3.5 h-3.5 text-blue-600 animate-spin" />
                        ) : tool.status === 'completed' ? (
                          <CheckCircle className="w-3.5 h-3.5 text-green-600" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-red-600" />
                        )}
                      </div>
                      <span className={`text-sm font-medium flex-1 ${getToolIconColor(tool.name)}`}>
                        {tool.name}
                      </span>
                      {tool.iteration && (
                        <span className="text-xs text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
                          #{tool.iteration}
                        </span>
                      )}
                      <span className="text-xs text-slate-400 font-mono">
                        {tool.status === 'running'
                          ? formatDuration(tool.startTime)
                          : formatDuration(tool.startTime, tool.endTime)}
                      </span>
                      {expandedTools.has(tool.id) ? (
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                      )}
                    </button>

                    {/* 展开内容 */}
                    {expandedTools.has(tool.id) && (
                      <div className="px-3 pb-3 border-t border-inherit">
                        {/* 参数 */}
                        <div className="mt-2">
                          <div className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                            <span className="font-medium">参数</span>
                          </div>
                          <pre className="p-2 bg-slate-100 rounded text-xs text-slate-600 overflow-x-auto max-h-20 font-mono">
                            {formatArguments(tool.arguments)}
                          </pre>
                        </div>
                        {/* 结果 */}
                        {tool.result && (
                          <div className="mt-2">
                            <div className="text-xs text-slate-500 mb-1 flex items-center gap-1">
                              <span className="font-medium">结果</span>
                            </div>
                            <pre className={`p-2 rounded text-xs overflow-x-auto max-h-24 font-mono ${
                              tool.status === 'error'
                                ? 'bg-red-50 text-red-700 border border-red-200'
                                : 'bg-green-50 text-green-700 border border-green-200'
                            }`}>
                              {truncateText(tool.result, 500)}
                            </pre>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* 待办事项 */}
        <div>
          <button
            onClick={() => setShowTodos(!showTodos)}
            className="w-full p-4 flex items-center justify-between hover:bg-slate-50/50 transition-colors"
          >
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center">
                <ListTodo className="w-3.5 h-3.5 text-purple-600" />
              </div>
              <span className="font-medium text-slate-700 text-sm">待办事项</span>
              <div className="flex items-center gap-1 ml-2">
                {pendingTodos.length > 0 && (
                  <span className="px-1.5 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
                    {pendingTodos.length} 待处理
                  </span>
                )}
                {completedTodos.length > 0 && (
                  <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                    完成{completedTodos.length}
                  </span>
                )}
              </div>
            </div>
            {showTodos ? (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-400" />
            )}
          </button>

          {showTodos && (
            <div className="px-4 pb-4 space-y-2">
              {todos.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm">
                  <ListTodo className="w-8 h-8 mx-auto mb-2 opacity-30" />
                  <p>暂无待办事项</p>
                  <p className="text-xs mt-1 text-slate-300">Agent 执行任务时会自动更新</p>
                </div>
              ) : (
                todos.map((todo) => (
                  <div
                    key={todo.id}
                    className={`p-3 rounded-lg border transition-all ${
                      todo.status === 'completed'
                        ? 'bg-green-50/50 border-green-200'
                        : todo.status === 'in_progress'
                        ? 'bg-blue-50/50 border-blue-200 shadow-sm'
                        : 'bg-white border-slate-200'
                    }`}
                  >
                    <div className="flex items-start gap-2 min-w-0">
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                        todo.status === 'completed'
                          ? 'bg-green-100'
                          : todo.status === 'in_progress'
                          ? 'bg-blue-100'
                          : 'bg-slate-100'
                      }`}>
                        {todo.status === 'completed' ? (
                          <CheckCircle className="w-3 h-3 text-green-600" />
                        ) : todo.status === 'in_progress' ? (
                          <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />
                        ) : (
                          <Clock className="w-3 h-3 text-slate-400" />
                        )}
                      </div>
                      <span
                        className={`text-sm flex-1 min-w-0 break-all ${
                          todo.status === 'completed'
                            ? 'text-green-700 line-through'
                            : 'text-slate-700'
                        }`}
                      >
                        {todo.content}
                      </span>
                    </div>
                    <div className="mt-1 text-xs text-slate-400 ml-7">
                      {todo.status === 'completed' && todo.completedAt
                        ? `完成于 ${formatTime(todo.completedAt)}`
                        : `创建于 ${formatTime(todo.createdAt)}`}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
