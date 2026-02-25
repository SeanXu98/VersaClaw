import { NextResponse } from 'next/server'
import { listSkills } from '@/lib/nanobot/skills'

/**
 * GET /api/skills
 * 获取所有技能列表
 */
export async function GET() {
  try {
    const skills = await listSkills()

    return NextResponse.json({
      data: {
        skills,
        total: skills.length,
        builtin: skills.filter(s => s.isBuiltIn).length,
        custom: skills.filter(s => !s.isBuiltIn).length
      },
      success: true
    })
  } catch (error) {
    console.error('Failed to list skills:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve skills',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
