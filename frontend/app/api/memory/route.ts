import { NextRequest, NextResponse } from 'next/server'
import { readMemory, writeMemory, searchHistory } from '@/lib/nanobot/memory'
import type { MemoryType } from '@/types/nanobot'

/**
 * GET /api/memory
 * 获取内存文件内容
 *
 * Query parameters:
 * - type: longTerm | history | heartbeat (默认 longTerm)
 * - search: 搜索关键词（仅对 history 有效）
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const type = (searchParams.get('type') || 'longTerm') as MemoryType
    const searchQuery = searchParams.get('search')

    // 验证类型
    if (!['longTerm', 'history', 'heartbeat'].includes(type)) {
      return NextResponse.json(
        { error: 'Invalid memory type' },
        { status: 400 }
      )
    }

    // 如果是搜索历史
    if (type === 'history' && searchQuery) {
      const results = await searchHistory(searchQuery)
      return NextResponse.json({
        data: {
          type,
          content: results.join('\n'),
          matches: results.length
        },
        success: true
      })
    }

    // 读取内存文件
    const content = await readMemory(type)

    return NextResponse.json({
      data: {
        type,
        content
      },
      success: true
    })
  } catch (error) {
    console.error('Failed to read memory:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve memory',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * PUT /api/memory
 * 更新内存文件内容
 *
 * Body:
 * - type: longTerm | history | heartbeat
 * - content: 文件内容
 */
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const type = body.type as MemoryType
    const content = body.content as string

    // 验证参数
    if (!type || !['longTerm', 'history', 'heartbeat'].includes(type)) {
      return NextResponse.json(
        { error: 'Invalid memory type' },
        { status: 400 }
      )
    }

    if (typeof content !== 'string') {
      return NextResponse.json(
        { error: 'Content must be a string' },
        { status: 400 }
      )
    }

    // 写入内存文件
    await writeMemory(type, content)

    return NextResponse.json({
      data: { message: 'Memory updated successfully' },
      success: true
    })
  } catch (error) {
    console.error('Failed to write memory:', error)
    return NextResponse.json(
      {
        error: 'Failed to update memory',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
