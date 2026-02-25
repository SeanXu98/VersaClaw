'use client'

import { useEffect, useState } from 'react'
import { Bot, CheckCircle2, Circle, ExternalLink, Sparkles, X, Key, Settings, Save, ArrowLeft, Loader2 } from 'lucide-react'
import Link from 'next/link'
import type { ProviderMeta } from '@/types/nanobot'

export default function ModelsPage() {
  const [providers, setProviders] = useState<{
    all: ProviderMeta[]
    categorized: {
      gateway: ProviderMeta[]
      international: ProviderMeta[]
      chinese: ProviderMeta[]
      local: ProviderMeta[]
    }
    configured: string[]
  } | null>(null)
  const [loading, setLoading] = useState(true)

  // 配置对话框状态
  const [configDialog, setConfigDialog] = useState<{
    isOpen: boolean
    provider: ProviderMeta | null
    isLoadingConfig: boolean
  }>({ isOpen: false, provider: null, isLoadingConfig: false })
  const [apiKey, setApiKey] = useState('')
  const [apiBase, setApiBase] = useState('')
  const [models, setModels] = useState('')
  const [hasExistingConfig, setHasExistingConfig] = useState(false)

  useEffect(() => {
    fetch('/api/models/providers')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setProviders(data.data)
        }
      })
      .catch(err => console.error('Failed to fetch providers:', err))
      .finally(() => setLoading(false))
  }, [])

  const handleOpenConfig = async (provider: ProviderMeta) => {
    setConfigDialog({ isOpen: true, provider, isLoadingConfig: true })
    setApiKey('')
    setApiBase('')
    setModels('')
    setHasExistingConfig(false)

    // 如果provider已配置，尝试加载现有配置
    if (providers?.configured.includes(provider.name)) {
      try {
        const response = await fetch(`/api/models/providers/${provider.name}`)
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.data) {
            // 显示遮罩的API Key作为占位符
            setApiKey('') // API Key 不回显，需要用户重新输入
            setApiBase(data.data.apiBase || '')
            setModels(data.data.models?.join(', ') || '')
            setHasExistingConfig(true)
          }
        }
      } catch (err) {
        console.error('Failed to load existing config:', err)
      }
    }
    setConfigDialog(prev => ({ ...prev, isLoadingConfig: false }))
  }

  const handleCloseDialog = () => {
    setConfigDialog({ isOpen: false, provider: null, isLoadingConfig: false })
    setApiKey('')
    setApiBase('')
    setModels('')
    setHasExistingConfig(false)
  }

  const handleSaveConfig = async () => {
    if (!configDialog.provider) return

    try {
      const response = await fetch(`/api/models/providers/${configDialog.provider.name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey,
          api_base: apiBase || undefined,
          models: models ? models.split(',').map(m => m.trim()).filter(Boolean) : undefined
        })
      })
      const data = await response.json()

      if (data.success) {
        // 刷新提供商列表
        const providersResponse = await fetch('/api/models/providers')
        const providersData = await providersResponse.json()
        if (providersData.success) {
          setProviders(providersData.data)
        }
        handleCloseDialog()
        // 提示用户需要重新启动后端以加载新配置
        alert('配置已保存！请刷新页面以使新配置生效。')
      } else {
        alert('配置失败: ' + (data.error || '未知错误'))
      }
    } catch (error) {
      console.error('Failed to save config:', error)
      alert('配置失败: ' + (error as Error).message)
    }
  }

  const handleRemoveConfig = async (providerName: string) => {
    if (!confirm('确定要移除此提供商配置吗？')) return

    try {
      const response = await fetch(`/api/models/providers/${providerName}`, {
        method: 'DELETE'
      })
      const data = await response.json()

      if (data.success) {
        // 刷新提供商列表
        const providersResponse = await fetch('/api/models/providers')
        const providersData = await providersResponse.json()
        if (providersData.success) {
          setProviders(providersData.data)
        }
      } else {
        alert('移除失败: ' + (data.error || '未知错误'))
      }
    } catch (error) {
      console.error('Failed to remove config:', error)
      alert('移除失败: ' + (error as Error).message)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-lg text-slate-600">加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="text-lg font-semibold">Home</span>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">模型管理</h1>
                <p className="text-sm text-slate-500">配置和管理LLM提供商</p>
              </div>
            </div>
            <div className="w-24"></div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            label="总提供商"
            value={providers?.all.length ?? 0}
            icon={<Bot className="w-5 h-5" />}
            color="purple"
          />
          <StatCard
            label="已配置"
            value={providers?.configured.length ?? 0}
            icon={<CheckCircle2 className="w-5 h-5" />}
            color="emerald"
          />
          <StatCard
            label="活跃"
            value={providers?.all.filter(p => p.status === 'active').length ?? 0}
            icon={<Sparkles className="w-5 h-5" />}
            color="blue"
          />
        </div>

        {/* Provider Categories */}
        <div className="space-y-6">
          <ProviderSection
            title="🌐 网关提供商"
            description="统一接入多个模型提供商"
            providers={providers?.categorized.gateway ?? []}
            onOpenConfig={handleOpenConfig}
            onRemoveConfig={handleRemoveConfig}
          />
          <ProviderSection
            title="🌍 国际提供商"
            description="全球领先的AI模型服务"
            providers={providers?.categorized.international ?? []}
            onOpenConfig={handleOpenConfig}
            onRemoveConfig={handleRemoveConfig}
          />
          <ProviderSection
            title="🇨🇳 国内提供商"
            description="本土化的AI模型服务"
            providers={providers?.categorized.chinese ?? []}
            onOpenConfig={handleOpenConfig}
            onRemoveConfig={handleRemoveConfig}
          />
          <ProviderSection
            title="💻 本地提供商"
            description="自托管的模型服务"
            providers={providers?.categorized.local ?? []}
            onOpenConfig={handleOpenConfig}
            onRemoveConfig={handleRemoveConfig}
          />
        </div>

        {/* Config Dialog */}
        {configDialog.isOpen && configDialog.provider && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-6 max-w-md w-full">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                  <Settings className="w-6 h-6 text-purple-600" />
                  配置 {configDialog.provider.display_name}
                </h2>
                <button
                  onClick={handleCloseDialog}
                  className="text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {configDialog.isLoadingConfig ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                  <span className="ml-2 text-slate-600">加载配置中...</span>
                </div>
              ) : (
                <>
                  {hasExistingConfig && (
                    <div className="mb-4 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
                      此提供商已配置。API Key 需要重新输入，其他配置项已显示。
                    </div>
                  )}

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">
                        API Key <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder={hasExistingConfig ? "输入新的 API Key 以更新" : "输入您的 API Key"}
                        className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">
                        模型型号 <span className="text-slate-400 font-normal">（可选，多个用逗号分隔）</span>
                      </label>
                      <input
                        type="text"
                        value={models}
                        onChange={(e) => setModels(e.target.value)}
                        placeholder="例如: glm-4, glm-4-flash, glm-3-turbo"
                        className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      />
                      <p className="text-xs text-slate-500 mt-1">
                        常用模型: glm-4, glm-4-flash, glm-4-plus, glm-3-turbo
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">
                        API Base URL <span className="text-slate-400 font-normal">（可选）</span>
                      </label>
                      <input
                        type="text"
                        value={apiBase}
                        onChange={(e) => setApiBase(e.target.value)}
                        placeholder="https://api.example.com/v1"
                        className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm"
                      />
                    </div>
                  </div>

                  <div className="flex gap-2 mt-6">
                    <button
                      onClick={handleCloseDialog}
                      className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-all"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleSaveConfig}
                      disabled={!apiKey}
                      className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-1.5 ${
                        !apiKey
                          ? 'bg-purple-300 text-purple-500 cursor-not-allowed'
                          : 'bg-purple-600 text-white hover:bg-purple-700'
                      }`}
                    >
                      <Save className="w-4 h-4" />
                      保存配置
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon,
  color
}: {
  label: string
  value: number
  icon: React.ReactNode
  color: string
}) {
  const colorClasses = {
    purple: 'from-purple-500 to-purple-600',
    emerald: 'from-emerald-500 to-emerald-600',
    blue: 'from-blue-500 to-blue-600',
  }

  return (
    <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 hover:shadow-lg transition-all">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-medium text-slate-600">{label}</div>
        <div className={`w-10 h-10 bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} rounded-lg flex items-center justify-center text-white`}>
          {icon}
        </div>
      </div>
      <div className="text-3xl font-bold text-slate-800">{value}</div>
    </div>
  )
}

function ProviderSection({
  title,
  description,
  providers,
  onOpenConfig,
  onRemoveConfig
}: {
  title: string
  description: string
  providers: ProviderMeta[]
  onOpenConfig: (provider: ProviderMeta) => void
  onRemoveConfig: (providerName: string) => void
}) {
  if (providers.length === 0) return null

  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-8">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-slate-800 mb-1">{title}</h2>
        <p className="text-sm text-slate-500">{description}</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {providers.map(provider => (
          <ProviderCard
            key={provider.name}
            provider={provider}
            onOpenConfig={onOpenConfig}
            onRemoveConfig={onRemoveConfig}
          />
        ))}
      </div>
    </div>
  )
}

function ProviderCard({ provider, onOpenConfig, onRemoveConfig }: {
  provider: ProviderMeta
  onOpenConfig: (provider: ProviderMeta) => void
  onRemoveConfig: (providerName: string) => void
}) {
  const isActive = provider.status === 'active'

  return (
    <div className={`group relative border-2 rounded-xl p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${
      isActive
        ? 'border-emerald-200 bg-gradient-to-br from-emerald-50 to-white'
        : 'border-slate-200 bg-white hover:border-slate-300'
    }`}>
      {/* Status Indicator */}
      <div className="absolute top-4 right-4">
        {isActive ? (
          <div className="flex items-center gap-1.5 px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" />
            已配置
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-medium">
            <Circle className="w-3 h-3" />
            未配置
          </div>
        )}
      </div>

      {/* Provider Name */}
      <h3 className="font-semibold text-slate-800 mb-2 pr-20">{provider.display_name}</h3>

      {/* Keywords */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {provider.keywords.slice(0, 3).map(keyword => (
          <span
            key={keyword}
            className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs"
          >
            {keyword}
          </span>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => onOpenConfig(provider)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
            isActive
              ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              : 'bg-purple-600 text-white hover:bg-purple-700'
          }`}
        >
          <Key className="w-4 h-4" />
          {isActive ? '重新配置' : '配置'}
        </button>
        {isActive && (
          <button
            onClick={() => onRemoveConfig(provider.name)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-all"
          >
            <X className="w-4 h-4" />
            移除
          </button>
        )}
      </div>

      {/* Documentation Link */}
      {provider.documentation_url && (
        <a
          href={provider.documentation_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium group-hover:underline"
        >
          查看文档
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      )}
    </div>
  )
}
