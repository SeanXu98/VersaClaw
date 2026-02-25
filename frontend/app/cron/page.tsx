'use client'

import { useEffect, useState } from 'react'
import {
  Clock, ArrowLeft, Plus, Play, Pause, Trash2, Edit, Calendar,
  Timer, RefreshCw, CheckCircle2, XCircle, X, Save, Loader2
} from 'lucide-react'
import Link from 'next/link'
import type { CronJob, CronSchedule } from '@/types/nanobot'

interface CronData {
  jobs: CronJob[]
  total: number
  enabled: number
  disabled: number
}

export default function CronPage() {
  const [data, setData] = useState<CronData | null>(null)
  const [loading, setLoading] = useState(true)

  // 创建/编辑对话框状态
  const [dialog, setDialog] = useState<{
    isOpen: boolean
    mode: 'create' | 'edit'
    job: CronJob | null
    saving: boolean
  }>({ isOpen: false, mode: 'create', job: null, saving: false })

  // 表单状态
  const [formData, setFormData] = useState({
    name: '',
    enabled: true,
    scheduleType: 'every' as 'every' | 'cron' | 'at',
    everySeconds: 3600,
    cronExpr: '0 9 * * *',
    atTime: '',
    message: '',
    channel: 'cli',
    chatId: 'direct'
  })

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/cron')
      const result = await response.json()
      if (result.success) {
        setData(result.data)
      }
    } catch (err) {
      console.error('Failed to fetch cron jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenCreate = () => {
    setFormData({
      name: '',
      enabled: true,
      scheduleType: 'every',
      everySeconds: 3600,
      cronExpr: '0 9 * * *',
      atTime: '',
      message: '',
      channel: 'cli',
      chatId: 'direct'
    })
    setDialog({ isOpen: true, mode: 'create', job: null, saving: false })
  }

  const handleOpenEdit = (job: CronJob) => {
    const scheduleType = job.schedule.type
    setFormData({
      name: job.name,
      enabled: job.enabled,
      scheduleType: scheduleType as 'every' | 'cron' | 'at',
      everySeconds: job.schedule.every_ms ? job.schedule.every_ms / 1000 : 3600,
      cronExpr: job.schedule.expr || '0 9 * * *',
      atTime: job.schedule.at_ms ? new Date(job.schedule.at_ms).toISOString().slice(0, 16) : '',
      message: job.payload.message,
      channel: job.payload.channel,
      chatId: job.payload.chat_id
    })
    setDialog({ isOpen: true, mode: 'edit', job, saving: false })
  }

  const handleCloseDialog = () => {
    setDialog({ isOpen: false, mode: 'create', job: null, saving: false })
  }

  const buildSchedule = (): CronSchedule => {
    switch (formData.scheduleType) {
      case 'every':
        return { type: 'every', every_ms: formData.everySeconds * 1000 }
      case 'cron':
        return { type: 'cron', expr: formData.cronExpr }
      case 'at':
        return { type: 'at', at_ms: new Date(formData.atTime).getTime() }
      default:
        return { type: 'every', every_ms: 3600000 }
    }
  }

  const handleSave = async () => {
    if (!formData.name || !formData.message) {
      alert('请填写任务名称和消息内容')
      return
    }

    setDialog(prev => ({ ...prev, saving: true }))

    try {
      const payload = {
        name: formData.name,
        enabled: formData.enabled,
        schedule: buildSchedule(),
        payload: {
          type: 'task' as const,
          channel: formData.channel,
          chat_id: formData.chatId,
          message: formData.message
        },
        state: {
          next_run: Date.now()
        }
      }

      if (dialog.mode === 'create') {
        const response = await fetch('/api/cron', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        const result = await response.json()
        if (!result.success) {
          alert('创建失败: ' + (result.error || '未知错误'))
          return
        }
      } else if (dialog.job) {
        const response = await fetch(`/api/cron/${dialog.job.id}`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })
        const result = await response.json()
        if (!result.success) {
          alert('更新失败: ' + (result.error || '未知错误'))
          return
        }
      }

      await fetchJobs()
      handleCloseDialog()
    } catch (err) {
      console.error('Failed to save cron job:', err)
      alert('保存失败: ' + (err as Error).message)
    } finally {
      setDialog(prev => ({ ...prev, saving: false }))
    }
  }

  const handleToggle = async (job: CronJob) => {
    try {
      await fetch(`/api/cron/${job.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !job.enabled })
      })
      await fetchJobs()
    } catch (err) {
      console.error('Failed to toggle job:', err)
    }
  }

  const handleDelete = async (job: CronJob) => {
    if (!confirm(`确定要删除任务 "${job.name}" 吗？`)) return

    try {
      await fetch(`/api/cron/${job.id}`, { method: 'DELETE' })
      await fetchJobs()
    } catch (err) {
      console.error('Failed to delete job:', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-pink-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-lg text-slate-600">加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-pink-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors">
              <ArrowLeft className="w-5 h-5" />
              <span className="text-lg font-semibold">Home</span>
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-pink-600 to-rose-600 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">定时任务</h1>
                <p className="text-sm text-slate-500">管理定时任务和提醒</p>
              </div>
            </div>
            <button
              onClick={handleOpenCreate}
              className="flex items-center gap-2 px-4 py-2 bg-pink-600 text-white rounded-lg font-medium hover:bg-pink-700 transition-all"
            >
              <Plus className="w-5 h-5" />
              新建任务
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            label="总任务"
            value={data?.total ?? 0}
            icon={<Clock className="w-5 h-5" />}
            color="pink"
          />
          <StatCard
            label="已启用"
            value={data?.enabled ?? 0}
            icon={<CheckCircle2 className="w-5 h-5" />}
            color="emerald"
          />
          <StatCard
            label="已暂停"
            value={data?.disabled ?? 0}
            icon={<Pause className="w-5 h-5" />}
            color="slate"
          />
        </div>

        {/* Jobs List */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
          {data?.jobs && data.jobs.length > 0 ? (
            <div className="divide-y divide-slate-200">
              {data.jobs.map((job) => (
                <JobRow
                  key={job.id}
                  job={job}
                  onToggle={handleToggle}
                  onEdit={handleOpenEdit}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-16">
              <Clock className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-600 mb-2">暂无定时任务</h3>
              <p className="text-slate-500 mb-4">点击上方按钮创建您的第一个定时任务</p>
              <button
                onClick={handleOpenCreate}
                className="inline-flex items-center gap-2 px-4 py-2 bg-pink-600 text-white rounded-lg font-medium hover:bg-pink-700 transition-all"
              >
                <Plus className="w-5 h-5" />
                创建任务
              </button>
            </div>
          )}
        </div>
      </main>

      {/* Create/Edit Dialog */}
      {dialog.isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 p-6 max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-slate-800">
                {dialog.mode === 'create' ? '新建定时任务' : '编辑任务'}
              </h2>
              <button
                onClick={handleCloseDialog}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Task Name */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  任务名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="例如：每日提醒"
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                />
              </div>

              {/* Schedule Type */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">调度类型</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { value: 'every', label: '间隔执行', icon: <Timer className="w-4 h-4" /> },
                    { value: 'cron', label: 'Cron表达式', icon: <Calendar className="w-4 h-4" /> },
                    { value: 'at', label: '指定时间', icon: <Clock className="w-4 h-4" /> },
                  ].map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setFormData(prev => ({ ...prev, scheduleType: opt.value as any }))}
                      className={`flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                        formData.scheduleType === opt.value
                          ? 'bg-pink-600 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {opt.icon}
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Schedule Config */}
              {formData.scheduleType === 'every' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    执行间隔（秒）
                  </label>
                  <select
                    value={formData.everySeconds}
                    onChange={(e) => setFormData(prev => ({ ...prev, everySeconds: Number(e.target.value) }))}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                  >
                    <option value={60}>每分钟</option>
                    <option value={300}>每5分钟</option>
                    <option value={900}>每15分钟</option>
                    <option value={1800}>每30分钟</option>
                    <option value={3600}>每小时</option>
                    <option value={86400}>每天</option>
                  </select>
                </div>
              )}

              {formData.scheduleType === 'cron' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Cron 表达式
                  </label>
                  <input
                    type="text"
                    value={formData.cronExpr}
                    onChange={(e) => setFormData(prev => ({ ...prev, cronExpr: e.target.value }))}
                    placeholder="0 9 * * *"
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent font-mono"
                  />
                  <p className="text-xs text-slate-500 mt-1">
                    示例: "0 9 * * *" = 每天上午9点
                  </p>
                </div>
              )}

              {formData.scheduleType === 'at' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    执行时间
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.atTime}
                    onChange={(e) => setFormData(prev => ({ ...prev, atTime: e.target.value }))}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                  />
                </div>
              )}

              {/* Message */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  消息内容 <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={formData.message}
                  onChange={(e) => setFormData(prev => ({ ...prev, message: e.target.value }))}
                  placeholder="任务触发时发送给AI的消息..."
                  rows={3}
                  className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Channel & ChatId */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">渠道</label>
                  <select
                    value={formData.channel}
                    onChange={(e) => setFormData(prev => ({ ...prev, channel: e.target.value }))}
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                  >
                    <option value="cli">CLI</option>
                    <option value="telegram">Telegram</option>
                    <option value="discord">Discord</option>
                    <option value="whatsapp">WhatsApp</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">聊天ID</label>
                  <input
                    type="text"
                    value={formData.chatId}
                    onChange={(e) => setFormData(prev => ({ ...prev, chatId: e.target.value }))}
                    placeholder="direct"
                    className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                  />
                </div>
              </div>

              {/* Enable Toggle */}
              <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                <span className="font-medium text-slate-700">启用任务</span>
                <button
                  onClick={() => setFormData(prev => ({ ...prev, enabled: !prev.enabled }))}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    formData.enabled ? 'bg-emerald-500' : 'bg-slate-300'
                  }`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                    formData.enabled ? 'left-7' : 'left-1'
                  }`} />
                </button>
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
                onClick={handleSave}
                disabled={dialog.saving}
                className="flex-1 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-1.5 bg-pink-600 text-white hover:bg-pink-700 disabled:bg-pink-300"
              >
                {dialog.saving ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Save className="w-4 h-4" />
                )}
                保存
              </button>
            </div>
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
    pink: 'from-pink-500 to-pink-600',
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

function JobRow({
  job,
  onToggle,
  onEdit,
  onDelete
}: {
  job: CronJob
  onToggle: (job: CronJob) => void
  onEdit: (job: CronJob) => void
  onDelete: (job: CronJob) => void
}) {
  const formatSchedule = () => {
    if (job.schedule.type === 'every') {
      const seconds = (job.schedule.every_ms || 0) / 1000
      if (seconds >= 86400) return `每 ${seconds / 86400} 天`
      if (seconds >= 3600) return `每 ${seconds / 3600} 小时`
      if (seconds >= 60) return `每 ${seconds / 60} 分钟`
      return `每 ${seconds} 秒`
    }
    if (job.schedule.type === 'cron') {
      return job.schedule.expr
    }
    if (job.schedule.type === 'at' && job.schedule.at_ms) {
      return new Date(job.schedule.at_ms).toLocaleString('zh-CN')
    }
    return '未知'
  }

  const formatNextRun = () => {
    if (!job.state.next_run) return '-'
    return new Date(job.state.next_run).toLocaleString('zh-CN')
  }

  return (
    <div className={`p-5 hover:bg-slate-50 transition-all ${!job.enabled ? 'bg-slate-50/50' : ''}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            job.enabled
              ? 'bg-emerald-100 text-emerald-600'
              : 'bg-slate-100 text-slate-400'
          }`}>
            {job.enabled ? (
              <CheckCircle2 className="w-5 h-5" />
            ) : (
              <XCircle className="w-5 h-5" />
            )}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-slate-800">{job.name}</h3>
              {!job.enabled && (
                <span className="px-2 py-0.5 bg-slate-200 text-slate-600 rounded text-xs">已暂停</span>
              )}
            </div>
            <p className="text-sm text-slate-500 mt-0.5 line-clamp-1">{job.payload.message}</p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right text-sm">
            <div className="text-slate-600">{formatSchedule()}</div>
            <div className="text-slate-400 text-xs">下次执行: {formatNextRun()}</div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => onToggle(job)}
              className={`p-2 rounded-lg transition-all ${
                job.enabled
                  ? 'text-amber-600 hover:bg-amber-50'
                  : 'text-emerald-600 hover:bg-emerald-50'
              }`}
              title={job.enabled ? '暂停' : '启用'}
            >
              {job.enabled ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            <button
              onClick={() => onEdit(job)}
              className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg transition-all"
              title="编辑"
            >
              <Edit className="w-5 h-5" />
            </button>
            <button
              onClick={() => onDelete(job)}
              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-all"
              title="删除"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
