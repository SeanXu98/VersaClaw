'use client'

import { useEffect, useState } from 'react'
import { Brain, FileText, History, Heart, Save, Search, ArrowLeft, Loader2, Check, X } from 'lucide-react'
import Link from 'next/link'
import type { MemoryType } from '@/types/nanobot'

interface MemoryData {
  type: MemoryType
  content: string
}

const MEMORY_TABS: { type: MemoryType; label: string; icon: React.ReactNode; description: string }[] = [
  { type: 'longTerm', label: '长期记忆', icon: <Brain className="w-4 h-4" />, description: '存储重要的持久化信息' },
  { type: 'history', label: '历史日志', icon: <History className="w-4 h-4" />, description: '记录历史对话和事件' },
  { type: 'heartbeat', label: '心跳任务', icon: <Heart className="w-4 h-4" />, description: '定时执行的心跳任务' },
]

export default function MemoryPage() {
  const [activeTab, setActiveTab] = useState<MemoryType>('longTerm')
  const [content, setContent] = useState('')
  const [originalContent, setOriginalContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<string[] | null>(null)
  const [searching, setSearching] = useState(false)

  // 加载记忆内容
  useEffect(() => {
    loadMemory(activeTab)
  }, [activeTab])

  const loadMemory = async (type: MemoryType) => {
    setLoading(true)
    setError(null)
    setSearchResults(null)
    try {
      const response = await fetch(`/api/memory?type=${type}`)
      const data = await response.json()
      if (data.success) {
        setContent(data.data.content || '')
        setOriginalContent(data.data.content || '')
      } else {
        setError(data.error || '加载失败')
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const response = await fetch('/api/memory', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: activeTab, content })
      })
      const data = await response.json()
      if (data.success) {
        setOriginalContent(content)
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      } else {
        setError(data.error || '保存失败')
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim() || activeTab !== 'history') return

    setSearching(true)
    setSearchResults(null)
    try {
      const response = await fetch(`/api/memory?type=history&search=${encodeURIComponent(searchQuery)}`)
      const data = await response.json()
      if (data.success) {
        setSearchResults(data.data.matches ? data.data.content.split('\n').filter(Boolean) : [])
      }
    } catch (err) {
      console.error('Search failed:', err)
    } finally {
      setSearching(false)
    }
  }

  const hasChanges = content !== originalContent

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-emerald-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="text-lg font-semibold">Home</span>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-600 to-teal-600 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">记忆管理</h1>
                <p className="text-sm text-slate-500">查看和管理Nanobot的长期记忆</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {hasChanges && (
                <span className="text-sm text-amber-600 font-medium">未保存的更改</span>
              )}
              <button
                onClick={handleSave}
                disabled={!hasChanges || saving}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  hasChanges
                    ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                    : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                }`}
              >
                {saving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : saved ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                {saving ? '保存中...' : saved ? '已保存' : '保存'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 mb-6">
          <div className="flex border-b border-slate-200">
            {MEMORY_TABS.map((tab) => (
              <button
                key={tab.type}
                onClick={() => setActiveTab(tab.type)}
                className={`flex-1 flex items-center justify-center gap-2 px-6 py-4 text-sm font-medium transition-all ${
                  activeTab === tab.type
                    ? 'text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50/50'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
          <div className="px-6 py-3 bg-slate-50 border-b border-slate-200">
            <p className="text-sm text-slate-600">
              {MEMORY_TABS.find(t => t.type === activeTab)?.description}
            </p>
          </div>
        </div>

        {/* Search Bar (only for history) */}
        {activeTab === 'history' && (
          <div className="bg-white rounded-xl shadow-md border border-slate-200 p-4 mb-6">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="搜索历史日志..."
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim()}
                className="px-6 py-2.5 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-all disabled:bg-emerald-300 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                搜索
              </button>
              {searchResults !== null && (
                <button
                  onClick={() => {
                    setSearchResults(null)
                    setSearchQuery('')
                  }}
                  className="px-4 py-2.5 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-50 transition-all"
                >
                  清除
                </button>
              )}
            </div>
            {searchResults !== null && (
              <div className="mt-3 text-sm text-slate-600">
                找到 <span className="font-semibold text-emerald-600">{searchResults.length}</span> 条匹配记录
              </div>
            )}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-center gap-3">
            <X className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {/* Editor */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
              <span className="ml-3 text-slate-600">加载中...</span>
            </div>
          ) : (
            <div className="relative">
              <textarea
                value={searchResults !== null ? searchResults.join('\n') : content}
                onChange={(e) => {
                  if (searchResults === null) {
                    setContent(e.target.value)
                  }
                }}
                readOnly={searchResults !== null}
                placeholder={searchResults !== null ? '搜索结果只读，清除搜索后可编辑' : '在此输入记忆内容...'}
                className={`w-full h-[60vh] p-6 font-mono text-sm resize-none focus:outline-none ${
                  searchResults !== null ? 'bg-slate-50' : ''
                }`}
                spellCheck={false}
              />
              <div className="absolute bottom-4 right-4 text-xs text-slate-400">
                {content.length} 字符
              </div>
            </div>
          )}
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
          <InfoCard
            icon={<FileText className="w-5 h-5" />}
            title="MEMORY.md"
            description="存储用户偏好、重要事实等长期记忆"
            active={activeTab === 'longTerm'}
          />
          <InfoCard
            icon={<History className="w-5 h-5" />}
            title="HISTORY.md"
            description="按时间顺序记录对话和事件历史"
            active={activeTab === 'history'}
          />
          <InfoCard
            icon={<Heart className="w-5 h-5" />}
            title="HEARTBEAT.md"
            description="定时心跳任务的配置和执行记录"
            active={activeTab === 'heartbeat'}
          />
        </div>
      </main>
    </div>
  )
}

function InfoCard({
  icon,
  title,
  description,
  active
}: {
  icon: React.ReactNode
  title: string
  description: string
  active: boolean
}) {
  return (
    <div className={`rounded-xl p-4 border transition-all ${
      active
        ? 'bg-emerald-50 border-emerald-200'
        : 'bg-white border-slate-200'
    }`}>
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
          active ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600'
        }`}>
          {icon}
        </div>
        <h3 className="font-semibold text-slate-800">{title}</h3>
      </div>
      <p className="text-sm text-slate-600 ml-11">{description}</p>
    </div>
  )
}
