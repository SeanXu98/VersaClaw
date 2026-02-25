'use client'

import { useEffect, useState } from 'react'
import {
  Radio, ArrowLeft, Settings, CheckCircle2, Circle, Power, PowerOff,
  X, Save, Loader2
} from 'lucide-react'
import Link from 'next/link'
import type { ChannelMeta, ChannelName } from '@/types/nanobot'

interface ChannelsData {
  channels: ChannelMeta[]
  total: number
  enabled: number
  configured: number
}

// 渠道配置字段定义
const CHANNEL_FIELDS: Record<ChannelName, { key: string; label: string; type: string; required: boolean; placeholder?: string }[]> = {
  telegram: [
    { key: 'token', label: 'Bot Token', type: 'password', required: true, placeholder: '从 @BotFather 获取' }
  ],
  discord: [
    { key: 'token', label: 'Bot Token', type: 'password', required: true, placeholder: '从 Discord Developer Portal 获取' }
  ],
  whatsapp: [
    { key: 'bridge_url', label: 'Bridge URL', type: 'text', required: true, placeholder: 'http://localhost:3000' },
    { key: 'bridge_token', label: 'Bridge Token', type: 'password', required: false, placeholder: '可选的认证令牌' }
  ],
  feishu: [
    { key: 'app_id', label: 'App ID', type: 'text', required: true, placeholder: '飞书应用的 App ID' },
    { key: 'app_secret', label: 'App Secret', type: 'password', required: true, placeholder: '飞书应用的 App Secret' }
  ],
  slack: [
    { key: 'bot_token', label: 'Bot Token', type: 'password', required: true, placeholder: 'xoxb-...' },
    { key: 'app_token', label: 'App Token', type: 'password', required: true, placeholder: 'xapp-...' }
  ],
  dingtalk: [
    { key: 'client_id', label: 'Client ID', type: 'text', required: true, placeholder: '钉钉应用的 Client ID' },
    { key: 'client_secret', label: 'Client Secret', type: 'password', required: true, placeholder: '钉钉应用的 Client Secret' }
  ],
  mochat: [
    { key: 'base_url', label: 'Base URL', type: 'text', required: true, placeholder: '企业微信 API 地址' },
    { key: 'claw_token', label: 'Claw Token', type: 'password', required: true, placeholder: '认证令牌' }
  ],
  email: [
    { key: 'imap_host', label: 'IMAP Host', type: 'text', required: true, placeholder: 'imap.example.com' },
    { key: 'imap_port', label: 'IMAP Port', type: 'number', required: true, placeholder: '993' },
    { key: 'smtp_host', label: 'SMTP Host', type: 'text', required: true, placeholder: 'smtp.example.com' },
    { key: 'smtp_port', label: 'SMTP Port', type: 'number', required: true, placeholder: '465' },
    { key: 'username', label: 'Username', type: 'text', required: true, placeholder: 'your@email.com' },
    { key: 'password', label: 'Password', type: 'password', required: true, placeholder: '邮箱密码或应用密码' }
  ],
  qq: [
    { key: 'app_id', label: 'App ID', type: 'text', required: true, placeholder: 'QQ 应用的 App ID' },
    { key: 'secret', label: 'Secret', type: 'password', required: true, placeholder: 'QQ 应用的 Secret' }
  ]
}

export default function ChannelsPage() {
  const [data, setData] = useState<ChannelsData | null>(null)
  const [loading, setLoading] = useState(true)

  // 配置对话框状态
  const [configDialog, setConfigDialog] = useState<{
    isOpen: boolean
    channel: ChannelMeta | null
    isLoadingConfig: boolean
  }>({ isOpen: false, channel: null, isLoadingConfig: false })
  const [configValues, setConfigValues] = useState<Record<string, string>>({})
  const [enabled, setEnabled] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchChannels()
  }, [])

  const fetchChannels = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/channels')
      const result = await response.json()
      if (result.success) {
        setData(result.data)
      }
    } catch (err) {
      console.error('Failed to fetch channels:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenConfig = async (channel: ChannelMeta) => {
    setConfigDialog({ isOpen: true, channel, isLoadingConfig: true })
    setConfigValues({})
    setEnabled(true)

    // 尝试加载现有配置
    try {
      const response = await fetch(`/api/channels/${channel.name}`)
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          // 不回显敏感字段，只加载非敏感配置
          const fields = CHANNEL_FIELDS[channel.name] || []
          const nonSensitiveValues: Record<string, string> = {}
          fields.forEach(f => {
            if (f.type !== 'password' && result.data[f.key] !== undefined) {
              nonSensitiveValues[f.key] = String(result.data[f.key])
            }
          })
          setConfigValues(nonSensitiveValues)
          setEnabled(result.data.enabled ?? true)
        }
      }
    } catch (err) {
      console.error('Failed to load channel config:', err)
    }

    setConfigDialog(prev => ({ ...prev, isLoadingConfig: false }))
  }

  const handleCloseDialog = () => {
    setConfigDialog({ isOpen: false, channel: null, isLoadingConfig: false })
    setConfigValues({})
    setEnabled(true)
  }

  const handleSaveConfig = async () => {
    if (!configDialog.channel) return

    const fields = CHANNEL_FIELDS[configDialog.channel.name] || []

    // 验证必填字段
    for (const field of fields) {
      if (field.required && !configValues[field.key]) {
        alert(`请填写 ${field.label}`)
        return
      }
    }

    setSaving(true)
    try {
      const response = await fetch(`/api/channels/${configDialog.channel.name}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enabled,
          ...configValues
        })
      })
      const result = await response.json()

      if (result.success) {
        await fetchChannels()
        handleCloseDialog()
      } else {
        alert('配置失败: ' + (result.error || '未知错误'))
      }
    } catch (err) {
      console.error('Failed to save config:', err)
      alert('配置失败: ' + (err as Error).message)
    } finally {
      setSaving(false)
    }
  }

  const handleToggleChannel = async (channel: ChannelMeta) => {
    try {
      const response = await fetch(`/api/channels/${channel.name}`)
      if (response.ok) {
        const result = await response.json()
        if (result.success && result.data) {
          const newEnabled = !result.data.enabled
          await fetch(`/api/channels/${channel.name}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              ...result.data,
              enabled: newEnabled
            })
          })
          await fetchChannels()
        }
      }
    } catch (err) {
      console.error('Failed to toggle channel:', err)
    }
  }

  const handleRemoveConfig = async (channelName: ChannelName) => {
    if (!confirm('确定要移除此渠道配置吗？')) return

    try {
      const response = await fetch(`/api/channels/${channelName}`, {
        method: 'DELETE'
      })
      const result = await response.json()

      if (result.success) {
        await fetchChannels()
      } else {
        alert('移除失败: ' + (result.error || '未知错误'))
      }
    } catch (err) {
      console.error('Failed to remove config:', err)
      alert('移除失败: ' + (err as Error).message)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-orange-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-lg text-slate-600">加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-orange-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="text-lg font-semibold">Home</span>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-orange-600 to-red-600 rounded-lg flex items-center justify-center">
                <Radio className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">渠道管理</h1>
                <p className="text-sm text-slate-500">配置IM渠道（Telegram、Discord等）</p>
              </div>
            </div>
            <div className="w-24"></div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <StatCard
            label="总渠道"
            value={data?.total ?? 0}
            icon={<Radio className="w-5 h-5" />}
            color="orange"
          />
          <StatCard
            label="已配置"
            value={data?.configured ?? 0}
            icon={<CheckCircle2 className="w-5 h-5" />}
            color="blue"
          />
          <StatCard
            label="运行中"
            value={data?.enabled ?? 0}
            icon={<Power className="w-5 h-5" />}
            color="emerald"
          />
          <StatCard
            label="已停止"
            value={(data?.configured ?? 0) - (data?.enabled ?? 0)}
            icon={<PowerOff className="w-5 h-5" />}
            color="slate"
          />
        </div>

        {/* Channels Grid */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-6">可用渠道</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data?.channels.map((channel) => (
              <ChannelCard
                key={channel.name}
                channel={channel}
                onOpenConfig={handleOpenConfig}
                onToggle={handleToggleChannel}
                onRemove={handleRemoveConfig}
              />
            ))}
          </div>
        </div>
      </main>

      {/* Config Dialog */}
      {configDialog.isOpen && configDialog.channel && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-6 max-w-md w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-slate-800 flex items-center gap-3">
                <span className="text-2xl">{configDialog.channel.icon}</span>
                配置 {configDialog.channel.display_name}
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
                <Loader2 className="w-6 h-6 animate-spin text-orange-600" />
                <span className="ml-2 text-slate-600">加载配置中...</span>
              </div>
            ) : (
              <>
                <div className="space-y-4">
                  {/* Enable Toggle */}
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <span className="font-medium text-slate-700">启用渠道</span>
                    <button
                      onClick={() => setEnabled(!enabled)}
                      className={`relative w-12 h-6 rounded-full transition-colors ${
                        enabled ? 'bg-emerald-500' : 'bg-slate-300'
                      }`}
                    >
                      <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                        enabled ? 'left-7' : 'left-1'
                      }`} />
                    </button>
                  </div>

                  {/* Dynamic Fields */}
                  {CHANNEL_FIELDS[configDialog.channel.name]?.map((field) => (
                    <div key={field.key}>
                      <label className="block text-sm font-medium text-slate-700 mb-1.5">
                        {field.label}
                        {field.required && <span className="text-red-500 ml-1">*</span>}
                      </label>
                      <input
                        type={field.type}
                        value={configValues[field.key] || ''}
                        onChange={(e) => setConfigValues(prev => ({
                          ...prev,
                          [field.key]: e.target.value
                        }))}
                        placeholder={field.placeholder}
                        className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent text-sm"
                      />
                    </div>
                  ))}
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
                    disabled={saving}
                    className="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-1.5 bg-orange-600 text-white hover:bg-orange-700 disabled:bg-orange-300"
                  >
                    {saving ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Save className="w-4 h-4" />
                    )}
                    保存
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
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
  const colorClasses: Record<string, string> = {
    orange: 'from-orange-500 to-orange-600',
    blue: 'from-blue-500 to-blue-600',
    emerald: 'from-emerald-500 to-emerald-600',
    slate: 'from-slate-500 to-slate-600',
  }

  return (
    <div className="bg-white rounded-xl shadow-md border border-slate-200 p-6 hover:shadow-lg transition-all">
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-medium text-slate-600">{label}</div>
        <div className={`w-10 h-10 bg-gradient-to-br ${colorClasses[color]} rounded-lg flex items-center justify-center text-white`}>
          {icon}
        </div>
      </div>
      <div className="text-3xl font-bold text-slate-800">{value}</div>
    </div>
  )
}

function ChannelCard({
  channel,
  onOpenConfig,
  onToggle,
  onRemove
}: {
  channel: ChannelMeta
  onOpenConfig: (channel: ChannelMeta) => void
  onToggle: (channel: ChannelMeta) => void
  onRemove: (channelName: ChannelName) => void
}) {
  const isConfigured = channel.status !== 'stopped' || channel.message_count > 0
  const isRunning = channel.status === 'running'

  return (
    <div className={`group border-2 rounded-xl p-5 transition-all duration-300 hover:shadow-lg ${
      isRunning
        ? 'border-emerald-200 bg-gradient-to-br from-emerald-50 to-white'
        : isConfigured
        ? 'border-amber-200 bg-gradient-to-br from-amber-50 to-white'
        : 'border-slate-200 bg-white hover:border-slate-300'
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{channel.icon}</span>
          <div>
            <h3 className="font-semibold text-slate-800">{channel.display_name}</h3>
            <p className="text-xs text-slate-500">{channel.name}</p>
          </div>
        </div>
        {isRunning ? (
          <div className="flex items-center gap-1.5 px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium border border-emerald-200">
            <CheckCircle2 className="w-3 h-3" />
            运行中
          </div>
        ) : isConfigured ? (
          <div className="flex items-center gap-1.5 px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-medium border border-amber-200">
            <Circle className="w-3 h-3" />
            已配置
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-medium">
            <Circle className="w-3 h-3" />
            未配置
          </div>
        )}
      </div>

      {/* Stats */}
      {isConfigured && (
        <div className="text-sm text-slate-600 mb-4">
          消息数: <span className="font-medium">{channel.message_count}</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onOpenConfig(channel)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
            isConfigured
              ? 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              : 'bg-orange-600 text-white hover:bg-orange-700'
          }`}
        >
          <Settings className="w-4 h-4" />
          {isConfigured ? '编辑' : '配置'}
        </button>
        {isConfigured && (
          <>
            <button
              onClick={() => onToggle(channel)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                isRunning
                  ? 'text-amber-600 hover:bg-amber-50'
                  : 'text-emerald-600 hover:bg-emerald-50'
              }`}
            >
              {isRunning ? <PowerOff className="w-4 h-4" /> : <Power className="w-4 h-4" />}
              {isRunning ? '停用' : '启用'}
            </button>
            <button
              onClick={() => onRemove(channel.name)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-all"
            >
              <X className="w-4 h-4" />
              移除
            </button>
          </>
        )}
      </div>
    </div>
  )
}
