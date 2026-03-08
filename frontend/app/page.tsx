'use client'

import { useEffect, useState } from 'react'
import { Activity, Bot, MessageSquare, Zap, Radio, Clock, Settings, FileText } from 'lucide-react'
import type { SystemStatus } from '@/types/nanobot'

export default function Home() {
  const [status, setStatus] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/system/status')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setStatus(data.data)
        }
      })
      .catch(err => console.error('Failed to fetch status:', err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-lg text-slate-600">加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <Bot className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  VersaClaw
                </h1>
                <p className="text-sm text-slate-500">基于Nanobot扩展的AI Agent</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge
                isRunning={status?.nanobot_running}
              />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* System Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="系统状态"
            value={status?.nanobot_running ? '运行中' : '未运行'}
            icon={<Activity className="w-5 h-5" />}
            trend={status?.nanobot_running ? 'up' : 'down'}
            color="blue"
          />
          <MetricCard
            title="启用渠道"
            value={status?.enabled_channels ?? 0}
            icon={<Radio className="w-5 h-5" />}
            color="purple"
          />
          <MetricCard
            title="配置提供商"
            value={status?.configured_providers ?? 0}
            icon={<Bot className="w-5 h-5" />}
            color="indigo"
          />
          <MetricCard
            title="会话总数"
            value={status?.total_sessions ?? 0}
            icon={<MessageSquare className="w-5 h-5" />}
            color="emerald"
          />
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-8 mb-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-6 flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-600" />
            快速导航
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <NavCard href="/chat" icon={<MessageSquare />} label="聊天" color="blue" />
            <NavCard href="/models" icon={<Bot />} label="模型管理" color="purple" />
            <NavCard href="/skills" icon={<Zap />} label="技能管理" color="indigo" />
            <NavCard href="/memory" icon={<FileText />} label="记忆管理" color="emerald" />
            <NavCard href="/channels" icon={<Radio />} label="渠道管理" color="orange" />
            <NavCard href="/cron" icon={<Clock />} label="定时任务" color="pink" />
            <NavCard href="/settings" icon={<Settings />} label="系统设置" color="slate" />
            <NavCard href="/logs" icon={<FileText />} label="系统日志" color="amber" />
          </div>
        </div>

        {/* System Info */}
        {status?.uptime !== undefined && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border border-blue-100">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-slate-600 mb-1">运行时长</h3>
                <p className="text-2xl font-bold text-slate-800">
                  {formatUptime(status.uptime)}
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-600/10 rounded-xl flex items-center justify-center">
                <Clock className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function StatusBadge({ isRunning }: { isRunning?: boolean }) {
  return (
    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
      isRunning
        ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
        : 'bg-red-100 text-red-700 border border-red-200'
    }`}>
      <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-emerald-500' : 'bg-red-500'} animate-pulse`} />
      {isRunning ? '运行中' : '未运行'}
    </div>
  )
}

function MetricCard({
  title,
  value,
  icon,
  trend,
  color = 'blue'
}: {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: 'up' | 'down'
  color?: string
}) {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
    indigo: 'from-indigo-500 to-indigo-600',
    emerald: 'from-emerald-500 to-emerald-600',
    orange: 'from-orange-500 to-orange-600',
  }

  return (
    <div className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 border border-slate-200 overflow-hidden group">
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div className={`w-12 h-12 bg-gradient-to-br ${colorClasses[color as keyof typeof colorClasses]} rounded-lg flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform`}>
            {icon}
          </div>
          {trend && (
            <div className={`text-xs font-medium px-2 py-1 rounded-full ${
              trend === 'up' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'
            }`}>
              {trend === 'up' ? '↑' : '↓'}
            </div>
          )}
        </div>
        <h3 className="text-sm font-medium text-slate-600 mb-1">{title}</h3>
        <p className="text-3xl font-bold text-slate-800">{value}</p>
      </div>
    </div>
  )
}

function NavCard({
  href,
  icon,
  label,
  color = 'blue'
}: {
  href: string
  icon: React.ReactNode
  label: string
  color?: string
}) {
  const colorClasses = {
    blue: 'hover:border-blue-400 hover:bg-blue-50 group-hover:text-blue-600',
    purple: 'hover:border-purple-400 hover:bg-purple-50 group-hover:text-purple-600',
    indigo: 'hover:border-indigo-400 hover:bg-indigo-50 group-hover:text-indigo-600',
    emerald: 'hover:border-emerald-400 hover:bg-emerald-50 group-hover:text-emerald-600',
    orange: 'hover:border-orange-400 hover:bg-orange-50 group-hover:text-orange-600',
    pink: 'hover:border-pink-400 hover:bg-pink-50 group-hover:text-pink-600',
    slate: 'hover:border-slate-400 hover:bg-slate-50 group-hover:text-slate-600',
    amber: 'hover:border-amber-400 hover:bg-amber-50 group-hover:text-amber-600',
  }

  return (
    <a
      href={href}
      className={`group relative flex flex-col items-center justify-center p-6 bg-white border-2 border-slate-200 rounded-xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${colorClasses[color as keyof typeof colorClasses]}`}
    >
      <div className="w-12 h-12 mb-3 text-slate-600 group-hover:scale-110 transition-transform">
        {icon}
      </div>
      <span className="text-sm font-medium text-slate-700">{label}</span>
    </a>
  )
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (days > 0) return `${days}天 ${hours}小时`
  if (hours > 0) return `${hours}小时 ${minutes}分钟`
  return `${minutes}分钟`
}
