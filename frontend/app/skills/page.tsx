'use client'

import { useEffect, useState } from 'react'
import { Zap, Star, Package, CheckCircle2 } from 'lucide-react'

export default function SkillsPage() {
  const [skills, setSkills] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/skills')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setSkills(data.data)
        }
      })
      .catch(err => console.error('Failed to fetch skills:', err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-lg text-slate-600">加载中...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-indigo-50 to-slate-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-lg flex items-center justify-center">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-800">技能管理</h1>
              <p className="text-sm text-slate-500">管理内置和自定义技能</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <StatCard
            label="总技能"
            value={skills?.total ?? 0}
            icon={<Zap className="w-5 h-5" />}
            color="indigo"
          />
          <StatCard
            label="内置技能"
            value={skills?.builtin ?? 0}
            icon={<Star className="w-5 h-5" />}
            color="blue"
          />
          <StatCard
            label="自定义技能"
            value={skills?.custom ?? 0}
            icon={<Package className="w-5 h-5" />}
            color="purple"
          />
        </div>

        {/* Skills List */}
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 p-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-6">技能列表</h2>
          <div className="space-y-3">
            {skills?.skills?.map((skill: any) => (
              <SkillCard key={skill.name} skill={skill} />
            ))}
          </div>
        </div>
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
    indigo: 'from-indigo-500 to-indigo-600',
    blue: 'from-blue-500 to-blue-600',
    purple: 'from-purple-500 to-purple-600',
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

function SkillCard({ skill }: { skill: any }) {
  return (
    <div className="group border-2 border-slate-200 rounded-xl p-5 hover:border-indigo-300 hover:shadow-md transition-all duration-300 bg-white hover:bg-gradient-to-br hover:from-indigo-50 hover:to-white">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="font-semibold text-slate-800 text-lg">{skill.frontmatter.name}</h3>
            {skill.isBuiltIn && (
              <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium border border-blue-200">
                内置
              </span>
            )}
            {skill.frontmatter.always && (
              <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full text-xs font-medium border border-emerald-200 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                Always
              </span>
            )}
          </div>
          <p className="text-sm text-slate-600 leading-relaxed">
            {skill.frontmatter.description}
          </p>
        </div>
        <div className="ml-4">
          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-lg flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform">
            <Zap className="w-6 h-6" />
          </div>
        </div>
      </div>
    </div>
  )
}
