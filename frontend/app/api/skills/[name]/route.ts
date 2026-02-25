import { NextRequest, NextResponse } from 'next/server'
import { readSkill, writeSkill, deleteSkill } from '@/lib/nanobot/skills'
import type { SkillFrontmatter } from '@/types/nanobot'

/**
 * GET /api/skills/[name]
 * 获取单个技能的详细信息
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    const skill = await readSkill(name)

    return NextResponse.json({
      data: skill,
      success: true
    })
  } catch (error) {
    const errorMessage = (error as Error).message

    if (errorMessage.includes('not found')) {
      return NextResponse.json(
        { error: 'Skill not found' },
        { status: 404 }
      )
    }

    console.error('Failed to read skill:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve skill',
        details: errorMessage
      },
      { status: 500 }
    )
  }
}

/**
 * PUT /api/skills/[name]
 * 创建或更新技能
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    const body = await request.json()

    const frontmatter: SkillFrontmatter = {
      name: body.frontmatter?.name || name,
      description: body.frontmatter?.description || '',
      always: body.frontmatter?.always || false,
      metadata: body.frontmatter?.metadata
    }

    const content = body.content || ''

    await writeSkill(name, frontmatter, content)

    return NextResponse.json({
      data: { message: 'Skill saved successfully' },
      success: true
    })
  } catch (error) {
    console.error('Failed to save skill:', error)
    return NextResponse.json(
      {
        error: 'Failed to save skill',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * DELETE /api/skills/[name]
 * 删除技能
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    await deleteSkill(name)

    return NextResponse.json({
      data: { message: 'Skill deleted successfully' },
      success: true
    })
  } catch (error) {
    console.error('Failed to delete skill:', error)
    return NextResponse.json(
      {
        error: 'Failed to delete skill',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
