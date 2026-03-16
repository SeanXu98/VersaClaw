'use client'

import { useEffect, useState } from 'react'
import { Bot, CheckCircle2, Circle, ExternalLink, Sparkles, X, Key, Settings, Save, ArrowLeft, Loader2, Eye, ChevronDown, ChevronUp } from 'lucide-react'
import Link from 'next/link'
import type { ProviderMeta } from '@/types/nanobot'
import { isVisionModel } from '@/utils/model'

// Provider 推荐模型配置
const PROVIDER_RECOMMENDED_MODELS: Record<string, { text: string[], vision: string[] }> = {
  openai: {
    text: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
    vision: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo']
  },
  anthropic: {
    text: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
    vision: ['claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229']
  },
  gemini: {
    text: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'],
    vision: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']
  },
  zhipu: {
    text: ['glm-5', 'glm-4.7', 'glm-4.7-flash', 'glm-4.6', 'glm-4-flash'],
    vision: ['glm-4.6v', 'glm-4.5v', 'glm-4v-plus', 'glm-4v-flash']
  },
  dashscope: {
    text: ['qwen-max', 'qwen-plus', 'qwen-turbo'],
    vision: ['qwen-vl-max', 'qwen-vl-plus']
  },
  deepseek: {
    text: ['deepseek-chat', 'deepseek-coder'],
    vision: ['deepseek-vl2']
  },
  moonshot: {
    text: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
    vision: []
  },
  openrouter: {
    text: ['openai/gpt-4o', 'anthropic/claude-3.5-sonnet', 'meta-llama/llama-3-70b-instruct'],
    vision: ['openai/gpt-4o', 'anthropic/claude-3.5-sonnet', 'google/gemini-pro-vision']
  },
  aihubmix: {
    text: ['gpt-4o', 'claude-3-5-sonnet', 'gemini-2.0-flash'],
    vision: ['gpt-4o', 'claude-3-5-sonnet', 'gemini-2.0-flash']
  }
}

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

  // 模型配置状态
  const [modelConfig, setModelConfig] = useState<{
    model: string | null
    imageModel: {
      primary: string | null
      fallbacks: string[]
      autoSwitch: boolean
    }
    allModels: string[]
    visionModels: string[]
  } | null>(null)
  const [loadingModelConfig, setLoadingModelConfig] = useState(false)
  const [showModelConfig, setShowModelConfig] = useState(true)

  // 配置对话框状态
  const [configDialog, setConfigDialog] = useState<{
    isOpen: boolean
    provider: ProviderMeta | null
    isLoadingConfig: boolean
  }>({ isOpen: false, provider: null, isLoadingConfig: false })
  const [apiKey, setApiKey] = useState('')
  const [apiBase, setApiBase] = useState('')
  const [selectedMainModel, setSelectedMainModel] = useState('')
  const [selectedVisionModel, setSelectedVisionModel] = useState('')
  const [customModel, setCustomModel] = useState('')
  const [hasExistingConfig, setHasExistingConfig] = useState(false)

  // 获取 Provider 的推荐模型
  const getProviderRecommendedModels = (providerName: string) => {
    return PROVIDER_RECOMMENDED_MODELS[providerName] || { text: [], vision: [] }
  }

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

    fetchModelConfig()
  }, [])

  const fetchModelConfig = async () => {
    setLoadingModelConfig(true)
    try {
      const response = await fetch('/api/models/config')
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          setModelConfig(data.data)
        }
      }
    } catch (err) {
      console.error('Failed to fetch model config:', err)
    } finally {
      setLoadingModelConfig(false)
    }
  }

  const handleOpenConfig = async (provider: ProviderMeta) => {
    setConfigDialog({ isOpen: true, provider, isLoadingConfig: true })
    setApiKey('')
    setApiBase('')
    setSelectedMainModel('')
    setSelectedVisionModel('')
    setCustomModel('')
    setHasExistingConfig(false)

    if (providers?.configured.includes(provider.name)) {
      try {
        const response = await fetch(`/api/models/providers/${provider.name}`)
        if (response.ok) {
          const data = await response.json()
          if (data.success && data.data) {
            setApiBase(data.data.apiBase || '')
            const configuredModels = data.data.models || []
            if (configuredModels.length > 0) {
              setSelectedMainModel(modelConfig?.model || configuredModels[0])
            }
            if (modelConfig?.imageModel?.primary) {
              setSelectedVisionModel(modelConfig.imageModel.primary)
            }
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
    setSelectedMainModel('')
    setSelectedVisionModel('')
    setCustomModel('')
    setHasExistingConfig(false)
  }

  const handleSaveConfig = async () => {
    if (!configDialog.provider) return

    const finalMainModel = selectedMainModel || customModel
    if (!finalMainModel) {
      alert('请选择或输入主模型')
      return
    }

    const recommendedModels = getProviderRecommendedModels(configDialog.provider.name)
    const allModels = new Set([
      ...recommendedModels.text,
      ...recommendedModels.vision,
      finalMainModel,
      selectedVisionModel
    ].filter(Boolean))

    try {
      // 1. 保存 Provider 配置
      const providerResponse = await fetch(`/api/models/providers/${configDialog.provider.name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: apiKey,
          api_base: apiBase || undefined,
          models: Array.from(allModels)
        })
      })
      const providerData = await providerResponse.json()

      if (!providerData.success) {
        alert('Provider 配置失败: ' + (providerData.error || '未知错误'))
        return
      }

      // 2. 更新模型配置
      await fetch('/api/models/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: finalMainModel,
          imageModel: selectedVisionModel ? {
            primary: selectedVisionModel,
            fallbacks: [],
            autoSwitch: true
          } : undefined
        })
      })

      // 刷新数据
      const providersResponse = await fetch('/api/models/providers')
      const providersData = await providersResponse.json()
      if (providersData.success) {
        setProviders(providersData.data)
      }
      await fetchModelConfig()
      handleCloseDialog()
      alert('配置已保存！')
    } catch (error) {
      console.error('Failed to save config:', error)
      alert('配置失败: ' + (error as Error).message)
    }
  }

  const handleRemoveConfig = async (providerName: string) => {
    if (!confirm('确定要移除此提供商配置吗？')) return

    try {
      const response = await fetch(`/api/models/providers/${providerName}`, { method: 'DELETE' })
      const data = await response.json()

      if (data.success) {
        const providersResponse = await fetch('/api/models/providers')
        const providersData = await providersResponse.json()
        if (providersData.success) {
          setProviders(providersData.data)
        }
        fetchModelConfig()
      } else {
        alert('移除失败: ' + (data.error || '未知错误'))
      }
    } catch (error) {
      console.error('Failed to remove config:', error)
      alert('移除失败: ' + (error as Error).message)
    }
  }

  const handleUpdateMainModel = async (model: string) => {
    try {
      const response = await fetch('/api/models/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model })
      })
      const data = await response.json()
      if (data.success) {
        fetchModelConfig()
      } else {
        alert('更新失败: ' + (data.error || '未知错误'))
      }
    } catch (error) {
      console.error('Failed to update model:', error)
      alert('更新失败: ' + (error as Error).message)
    }
  }

  const handleUpdateImageModel = async (primary: string) => {
    try {
      const response = await fetch('/api/models/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          imageModel: { primary, fallbacks: [], autoSwitch: true }
        })
      })
      const data = await response.json()
      if (data.success) {
        fetchModelConfig()
      } else {
        alert('更新失败: ' + (data.error || '未知错误'))
      }
    } catch (error) {
      console.error('Failed to update image model:', error)
      alert('更新失败: ' + (error as Error).message)
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
                <p className="text-sm text-slate-500">配置LLM提供商和模型路由</p>
              </div>
            </div>
            <div className="w-24"></div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard label="总提供商" value={providers?.all.length ?? 0} icon={<Bot className="w-5 h-5" />} color="purple" />
          <StatCard label="已配置" value={providers?.configured.length ?? 0} icon={<CheckCircle2 className="w-5 h-5" />} color="emerald" />
          <StatCard label="活跃" value={providers?.all.filter(p => p.status === 'active').length ?? 0} icon={<Sparkles className="w-5 h-5" />} color="blue" />
        </div>

        {/* Model Configuration */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-6 mb-8">
          <div className="flex items-center justify-between cursor-pointer" onClick={() => setShowModelConfig(!showModelConfig)}>
            <div>
              <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                <Settings className="w-5 h-5 text-purple-600" />
                模型路由配置
              </h2>
              <p className="text-sm text-slate-500 mt-1">选择主模型和视觉模型，系统自动路由请求</p>
            </div>
            <button className="text-slate-400 hover:text-slate-600 transition-colors">
              {showModelConfig ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
            </button>
          </div>

          {showModelConfig && (
            <div className="mt-6 space-y-6">
              {loadingModelConfig ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                  <span className="ml-2 text-slate-600">加载配置中...</span>
                </div>
              ) : (
                <>
                  {/* Main Model */}
                  <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="flex items-center gap-2 mb-3">
                      <Bot className="w-4 h-4 text-purple-600" />
                      <span className="font-medium text-slate-800">主模型</span>
                      <span className="text-xs text-slate-500">（文本对话默认使用）</span>
                    </div>
                    {modelConfig?.allModels && modelConfig.allModels.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {modelConfig.allModels.map(model => (
                          <button key={model} onClick={() => handleUpdateMainModel(model)}
                            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                              modelConfig.model === model ? 'bg-purple-600 text-white' : 'bg-white border border-slate-300 text-slate-700 hover:border-purple-400'
                            }`}>
                            {model}
                            {isVisionModel(model) && <Eye className="w-3 h-3 ml-1 inline text-emerald-400" />}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-slate-500">请先配置 Provider</p>
                    )}
                  </div>

                  {/* Vision Model */}
                  <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
                    <div className="flex items-center gap-2 mb-3">
                      <Eye className="w-4 h-4 text-emerald-600" />
                      <span className="font-medium text-slate-800">视觉模型</span>
                      <span className="text-xs text-slate-500">（检测到图片时自动切换）</span>
                    </div>
                    {modelConfig?.visionModels && modelConfig.visionModels.length > 0 ? (
                      <div className="flex flex-wrap gap-2">
                        {modelConfig.visionModels.map(model => (
                          <button key={model} onClick={() => handleUpdateImageModel(model)}
                            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                              modelConfig.imageModel?.primary === model ? 'bg-emerald-600 text-white' : 'bg-white border border-emerald-300 text-slate-700 hover:border-emerald-400'
                            }`}>
                            {model}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-slate-500">
                        {modelConfig?.allModels && modelConfig.allModels.length > 0
                          ? '当前没有支持视觉的模型，请添加如 gpt-4o、claude-3.5-sonnet 等'
                          : '请先配置 Provider'}
                      </p>
                    )}
                  </div>

                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200 text-sm text-blue-700">
                    <strong>提示：</strong>如果主模型支持视觉（如 GPT-4o、Claude-3.5），无需单独配置视觉模型。
                  </div>
                </>
              )}
            </div>
          )}
        </div>

        {/* Provider Categories */}
        <div className="space-y-6">
          <ProviderSection title="🌐 网关提供商" description="统一接入多个模型提供商" providers={providers?.categorized.gateway ?? []} onOpenConfig={handleOpenConfig} onRemoveConfig={handleRemoveConfig} />
          <ProviderSection title="🌍 国际提供商" description="全球领先的AI模型服务" providers={providers?.categorized.international ?? []} onOpenConfig={handleOpenConfig} onRemoveConfig={handleRemoveConfig} />
          <ProviderSection title="🇨🇳 国内提供商" description="本土化的AI模型服务" providers={providers?.categorized.chinese ?? []} onOpenConfig={handleOpenConfig} onRemoveConfig={handleRemoveConfig} />
          <ProviderSection title="💻 本地提供商" description="自托管的模型服务" providers={providers?.categorized.local ?? []} onOpenConfig={handleOpenConfig} onRemoveConfig={handleRemoveConfig} />
        </div>

        {/* Config Dialog */}
        {configDialog.isOpen && configDialog.provider && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-2">
                  <Settings className="w-6 h-6 text-purple-600" />
                  配置 {configDialog.provider.display_name}
                </h2>
                <button onClick={handleCloseDialog} className="text-slate-400 hover:text-slate-600 transition-colors">
                  <X className="w-6 h-6" />
                </button>
              </div>

              {configDialog.isLoadingConfig ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                  <span className="ml-2 text-slate-600">加载配置中...</span>
                </div>
              ) : (
                <div className="space-y-5">
                  {hasExistingConfig && (
                    <div className="px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700">
                      此提供商已配置。API Key 需要重新输入。
                    </div>
                  )}

                  {/* API Key */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      API Key <span className="text-red-500">*</span>
                    </label>
                    <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
                      placeholder={hasExistingConfig ? "输入新的 API Key 以更新" : "输入您的 API Key"}
                      className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm" />
                  </div>

                  {/* Main Model Selection */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      主模型 <span className="text-red-500">*</span>
                    </label>
                    {(() => {
                      const recommended = getProviderRecommendedModels(configDialog.provider?.name || '')
                      const allModels = [...recommended.text, ...recommended.vision]
                      if (allModels.length > 0) {
                        return (
                          <div className="flex flex-wrap gap-2 mb-2">
                            {allModels.map(model => (
                              <button key={model} type="button" onClick={() => { setSelectedMainModel(model); setCustomModel('') }}
                                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                                  selectedMainModel === model ? 'bg-purple-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                                }`}>
                                {model}
                                {recommended.vision.includes(model) && <Eye className="w-3 h-3 ml-1 inline text-emerald-500" />}
                              </button>
                            ))}
                          </div>
                        )
                      }
                      return null
                    })()}
                    <input type="text" value={customModel} onChange={(e) => { setCustomModel(e.target.value); setSelectedMainModel('') }}
                      placeholder="或输入自定义模型名称"
                      className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm" />
                  </div>

                  {/* Vision Model Selection */}
                  {(() => {
                    const recommended = getProviderRecommendedModels(configDialog.provider?.name || '')
                    if (recommended.vision.length > 0) {
                      return (
                        <div>
                          <label className="block text-sm font-medium text-slate-700 mb-1.5">
                            视觉模型 <span className="text-slate-400 font-normal">（可选，检测图片时自动切换）</span>
                          </label>
                          <div className="flex flex-wrap gap-2">
                            <button type="button" onClick={() => setSelectedVisionModel('')}
                              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                                !selectedVisionModel ? 'bg-slate-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                              }`}>
                              不单独配置
                            </button>
                            {recommended.vision.map(model => (
                              <button key={model} type="button" onClick={() => setSelectedVisionModel(model)}
                                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                                  selectedVisionModel === model ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                                }`}>
                                {model}
                              </button>
                            ))}
                          </div>
                        </div>
                      )
                    }
                    return null
                  })()}

                  {/* API Base */}
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      API Base URL <span className="text-slate-400 font-normal">（可选）</span>
                    </label>
                    <input type="text" value={apiBase} onChange={(e) => setApiBase(e.target.value)}
                      placeholder="https://api.example.com/v1"
                      className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm" />
                  </div>

                  <div className="flex gap-2 pt-2">
                    <button onClick={handleCloseDialog}
                      className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-all">
                      取消
                    </button>
                    <button onClick={handleSaveConfig} disabled={!apiKey || (!selectedMainModel && !customModel)}
                      className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-1.5 ${
                        !apiKey || (!selectedMainModel && !customModel)
                          ? 'bg-purple-300 text-purple-500 cursor-not-allowed'
                          : 'bg-purple-600 text-white hover:bg-purple-700'
                      }`}>
                      <Save className="w-4 h-4" />
                      保存配置
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function StatCard({ label, value, icon, color }: { label: string; value: number; icon: React.ReactNode; color: string }) {
  const colorClasses: Record<string, string> = {
    purple: 'from-purple-500 to-purple-600',
    emerald: 'from-emerald-500 to-emerald-600',
    blue: 'from-blue-500 to-blue-600',
  }
  return (
    <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 hover:shadow-lg transition-all">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-medium text-slate-600">{label}</div>
        <div className={`w-10 h-10 bg-gradient-to-br ${colorClasses[color]} rounded-lg flex items-center justify-center text-white`}>{icon}</div>
      </div>
      <div className="text-3xl font-bold text-slate-800">{value}</div>
    </div>
  )
}

function ProviderSection({ title, description, providers, onOpenConfig, onRemoveConfig }: {
  title: string; description: string; providers: ProviderMeta[]; onOpenConfig: (provider: ProviderMeta) => void; onRemoveConfig: (providerName: string) => void
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
          <ProviderCard key={provider.name} provider={provider} onOpenConfig={onOpenConfig} onRemoveConfig={onRemoveConfig} />
        ))}
      </div>
    </div>
  )
}

function ProviderCard({ provider, onOpenConfig, onRemoveConfig }: {
  provider: ProviderMeta; onOpenConfig: (provider: ProviderMeta) => void; onRemoveConfig: (providerName: string) => void
}) {
  const isActive = provider.status === 'active'
  const hasVisionModels = (provider.vision_models_count ?? 0) > 0
  const configuredModels = provider.configured_models || []

  return (
    <div className={`group relative border-2 rounded-xl p-5 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${
      isActive ? 'border-emerald-200 bg-gradient-to-br from-emerald-50 to-white' : 'border-slate-200 bg-white hover:border-slate-300'
    }`}>
      <div className="absolute top-4 right-4 flex items-center gap-1.5">
        {hasVisionModels && (
          <div className="flex items-center gap-1 px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium border border-emerald-200">
            <Eye className="w-3 h-3" />Vision
          </div>
        )}
        {isActive ? (
          <div className="flex items-center gap-1.5 px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-medium border border-blue-200">
            <CheckCircle2 className="w-3 h-3" />已配置
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-medium">
            <Circle className="w-3 h-3" />未配置
          </div>
        )}
      </div>

      <h3 className="font-semibold text-slate-800 mb-2 pr-28">{provider.display_name}</h3>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {provider.keywords.slice(0, 3).map(keyword => (
          <span key={keyword} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">{keyword}</span>
        ))}
      </div>

      {isActive && configuredModels.length > 0 && (
        <div className="mb-3">
          <div className="text-xs text-slate-500 mb-1.5">
            已配置 {configuredModels.length} 个模型{hasVisionModels && ` (含 ${provider.vision_models_count} 个 Vision)`}
          </div>
          <div className="flex flex-wrap gap-1">
            {configuredModels.slice(0, 4).map(model => (
              <span key={model} className={`px-1.5 py-0.5 rounded text-xs ${
                isVisionModel(model) ? 'bg-emerald-100 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'
              }`}>{model}</span>
            ))}
            {configuredModels.length > 4 && (
              <span className="px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded text-xs">+{configuredModels.length - 4}</span>
            )}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <button onClick={() => onOpenConfig(provider)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
            isActive ? 'bg-slate-100 text-slate-600 hover:bg-slate-200' : 'bg-purple-600 text-white hover:bg-purple-700'
          }`}>
          <Key className="w-4 h-4" />{isActive ? '重新配置' : '配置'}
        </button>
        {isActive && (
          <button onClick={() => onRemoveConfig(provider.name)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-all">
            <X className="w-4 h-4" />移除
          </button>
        )}
      </div>

      {provider.documentation_url && (
        <a href={provider.documentation_url} target="_blank" rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 font-medium group-hover:underline mt-2">
          查看文档<ExternalLink className="w-3.5 h-3.5" />
        </a>
      )}
    </div>
  )
}
