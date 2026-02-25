'use client'

import { useEffect, useState } from 'react'
import {
  Settings, ArrowLeft, Save, RefreshCw, Loader2, Check, X,
  Cpu, MessageSquare, Database, Shield, Zap, Clock, AlertCircle
} from 'lucide-react'
import Link from 'next/link'
import type { NanobotConfig } from '@/types/nanobot'

interface SettingsData {
  agents: {
    defaults: {
      model: string
      max_tokens: number
      temperature: number
      max_tool_iterations: number
      memory_window: number
    }
  }
  tools: {
    restrict_to_workspace: boolean
    exec: {
      timeout: number
    }
    web: {
      search: {
        api_key: string
        max_results: number
      }
    }
  }
}

const DEFAULT_SETTINGS: SettingsData = {
  agents: {
    defaults: {
      model: 'deepseek/deepseek-chat',
      max_tokens: 4096,
      temperature: 0.7,
      max_tool_iterations: 10,
      memory_window: 20
    }
  },
  tools: {
    restrict_to_workspace: true,
    exec: {
      timeout: 60
    },
    web: {
      search: {
        api_key: '',
        max_results: 5
      }
    }
  }
}

export default function SettingsPage() {
  const [config, setConfig] = useState<SettingsData | null>(null)
  const [originalConfig, setOriginalConfig] = useState<SettingsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/system/config')
      const result = await response.json()
      if (result.success) {
        const loadedConfig = {
          agents: {
            defaults: {
              model: result.data.agents?.defaults?.model || DEFAULT_SETTINGS.agents.defaults.model,
              max_tokens: result.data.agents?.defaults?.max_tokens || DEFAULT_SETTINGS.agents.defaults.max_tokens,
              temperature: result.data.agents?.defaults?.temperature || DEFAULT_SETTINGS.agents.defaults.temperature,
              max_tool_iterations: result.data.agents?.defaults?.max_tool_iterations || DEFAULT_SETTINGS.agents.defaults.max_tool_iterations,
              memory_window: result.data.agents?.defaults?.memory_window || DEFAULT_SETTINGS.agents.defaults.memory_window
            }
          },
          tools: {
            restrict_to_workspace: result.data.tools?.restrict_to_workspace ?? DEFAULT_SETTINGS.tools.restrict_to_workspace,
            exec: {
              timeout: result.data.tools?.exec?.timeout || DEFAULT_SETTINGS.tools.exec.timeout
            },
            web: {
              search: {
                api_key: result.data.tools?.web?.search?.api_key || '',
                max_results: result.data.tools?.web?.search?.max_results || DEFAULT_SETTINGS.tools.web.search.max_results
              }
            }
          }
        }
        setConfig(loadedConfig)
        setOriginalConfig(JSON.parse(JSON.stringify(loadedConfig)))
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!config) return

    setSaving(true)
    setError(null)
    try {
      const response = await fetch('/api/system/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      })
      const result = await response.json()

      if (result.success) {
        setOriginalConfig(JSON.parse(JSON.stringify(config)))
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      } else {
        setError(result.error || '保存失败')
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    if (confirm('确定要重置为默认设置吗？')) {
      setConfig(JSON.parse(JSON.stringify(DEFAULT_SETTINGS)))
    }
  }

  const updateConfig = (path: string, value: any) => {
    if (!config) return

    const newConfig = { ...config }
    const keys = path.split('.')
    let current: any = newConfig

    for (let i = 0; i < keys.length - 1; i++) {
      current[keys[i]] = { ...current[keys[i]] }
      current = current[keys[i]]
    }
    current[keys[keys.length - 1]] = value

    setConfig(newConfig)
  }

  const hasChanges = JSON.stringify(config) !== JSON.stringify(originalConfig)

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-slate-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-lg text-slate-600">加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-slate-200">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="text-lg font-semibold">Home</span>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-slate-600 to-slate-700 rounded-lg flex items-center justify-center">
                <Settings className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">系统设置</h1>
                <p className="text-sm text-slate-500">配置Nanobot系统参数</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {hasChanges && (
                <span className="text-sm text-amber-600 font-medium">未保存的更改</span>
              )}
              <button
                onClick={handleReset}
                className="px-4 py-2 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-50 transition-all"
              >
                重置
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || saving}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                  hasChanges
                    ? 'bg-slate-700 text-white hover:bg-slate-800'
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

      <main className="max-w-4xl mx-auto px-6 py-8">
        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-700">{error}</span>
          </div>
        )}

        {config && (
          <div className="space-y-6">
            {/* Agent Settings */}
            <SettingsSection
              icon={<Cpu className="w-5 h-5" />}
              title="Agent 设置"
              description="配置AI Agent的核心参数"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SettingField
                  label="默认模型"
                  value={config.agents.defaults.model}
                  onChange={(v) => updateConfig('agents.defaults.model', v)}
                  type="text"
                  placeholder="例如: deepseek/deepseek-chat"
                />
                <SettingField
                  label="Temperature"
                  value={config.agents.defaults.temperature}
                  onChange={(v) => updateConfig('agents.defaults.temperature', Number(v))}
                  type="number"
                  min={0}
                  max={2}
                  step={0.1}
                  description="控制输出的随机性 (0-2)"
                />
                <SettingField
                  label="最大Token数"
                  value={config.agents.defaults.max_tokens}
                  onChange={(v) => updateConfig('agents.defaults.max_tokens', Number(v))}
                  type="number"
                  min={256}
                  max={32768}
                  description="单次回复的最大Token数"
                />
                <SettingField
                  label="最大工具迭代次数"
                  value={config.agents.defaults.max_tool_iterations}
                  onChange={(v) => updateConfig('agents.defaults.max_tool_iterations', Number(v))}
                  type="number"
                  min={1}
                  max={50}
                  description="Agent调用工具的最大次数"
                />
                <SettingField
                  label="记忆窗口大小"
                  value={config.agents.defaults.memory_window}
                  onChange={(v) => updateConfig('agents.defaults.memory_window', Number(v))}
                  type="number"
                  min={1}
                  max={100}
                  description="保留在上下文中的消息数量"
                />
              </div>
            </SettingsSection>

            {/* Tools Settings */}
            <SettingsSection
              icon={<Zap className="w-5 h-5" />}
              title="工具设置"
              description="配置工具执行和权限"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div>
                    <div className="font-medium text-slate-800">限制到工作空间</div>
                    <div className="text-sm text-slate-500">只允许访问工作空间目录内的文件</div>
                  </div>
                  <button
                    onClick={() => updateConfig('tools.restrict_to_workspace', !config.tools.restrict_to_workspace)}
                    className={`relative w-12 h-6 rounded-full transition-colors ${
                      config.tools.restrict_to_workspace ? 'bg-emerald-500' : 'bg-slate-300'
                    }`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      config.tools.restrict_to_workspace ? 'left-7' : 'left-1'
                    }`} />
                  </button>
                </div>

                <SettingField
                  label="命令执行超时 (秒)"
                  value={config.tools.exec.timeout}
                  onChange={(v) => updateConfig('tools.exec.timeout', Number(v))}
                  type="number"
                  min={5}
                  max={300}
                  description="Shell命令执行的最大等待时间"
                />
              </div>
            </SettingsSection>

            {/* Web Search Settings */}
            <SettingsSection
              icon={<Database className="w-5 h-5" />}
              title="网络搜索"
              description="配置Brave Search API"
            >
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SettingField
                  label="API Key"
                  value={config.tools.web.search.api_key}
                  onChange={(v) => updateConfig('tools.web.search.api_key', v)}
                  type="password"
                  placeholder="Brave Search API Key"
                />
                <SettingField
                  label="最大搜索结果"
                  value={config.tools.web.search.max_results}
                  onChange={(v) => updateConfig('tools.web.search.max_results', Number(v))}
                  type="number"
                  min={1}
                  max={20}
                  description="每次搜索返回的最大结果数"
                />
              </div>
            </SettingsSection>

            {/* Info Card */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="w-6 h-6 text-blue-500 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-blue-800 mb-1">注意事项</h3>
                  <ul className="text-sm text-blue-700 space-y-1">
                    <li>• 修改设置后需要重启 Nanobot 服务才能生效</li>
                    <li>• Temperature 值越低输出越确定，值越高输出越随机</li>
                    <li>• 较大的 memory_window 会增加Token消耗</li>
                    <li>• 禁用"限制到工作空间"可能带来安全风险</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function SettingsSection({
  icon,
  title,
  description,
  children
}: {
  icon: React.ReactNode
  title: string
  description: string
  children: React.ReactNode
}) {
  return (
    <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-slate-600 to-slate-700 rounded-lg flex items-center justify-center text-white">
            {icon}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-800">{title}</h2>
            <p className="text-sm text-slate-500">{description}</p>
          </div>
        </div>
      </div>
      <div className="p-6">
        {children}
      </div>
    </div>
  )
}

function SettingField({
  label,
  value,
  onChange,
  type,
  placeholder,
  description,
  min,
  max,
  step
}: {
  label: string
  value: string | number
  onChange: (value: string) => void
  type: 'text' | 'number' | 'password'
  placeholder?: string
  description?: string
  min?: number
  max?: number
  step?: number
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1.5">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-500 focus:border-transparent"
      />
      {description && (
        <p className="text-xs text-slate-500 mt-1">{description}</p>
      )}
    </div>
  )
}
