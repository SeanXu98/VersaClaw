import { NextRequest, NextResponse } from 'next/server'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * GET /api/chat/sessions
 * 获取所有会话列表
 *
 * Query parameters:
 * - page: 页码（从1开始，默认1）
 * - limit: 每页数量（默认20）
 * - sort: 排序方式 (updated_at_desc | updated_at_asc | created_at_desc | created_at_asc)
 */
export async function GET(request: NextRequest) {
  try {
    // 调用后端 API
    const apiResponse = await fetch(`${API_SERVER_URL}/api/sessions`)
    if (!apiResponse.ok) {
      throw new Error(`API server returned ${apiResponse.status}`)
    }

    const apiData = await apiResponse.json()
    if (!apiData.success) {
      throw new Error(apiData.error || 'Failed to get sessions')
    }

    let sessions = apiData.data.sessions || []

    const searchParams = request.nextUrl.searchParams
    const page = parseInt(searchParams.get('page') || '1', 10)
    const limit = parseInt(searchParams.get('limit') || '20', 10)
    const sort = searchParams.get('sort') || 'updated_at_desc'

    // 验证参数
    if (page < 1 || limit < 1 || limit > 100) {
      return NextResponse.json(
        { error: 'Invalid pagination parameters' },
        { status: 400 }
      )
    }

    // 排序
    switch (sort) {
      case 'updated_at_asc':
        sessions.sort((a: any, b: any) =>
          new Date(a.metadata.updated_at).getTime() - new Date(b.metadata.updated_at).getTime()
        )
        break
      case 'created_at_desc':
        sessions.sort((a: any, b: any) =>
          new Date(b.metadata.created_at).getTime() - new Date(a.metadata.created_at).getTime()
        )
        break
      case 'created_at_asc':
        sessions.sort((a: any, b: any) =>
          new Date(a.metadata.created_at).getTime() - new Date(b.metadata.created_at).getTime()
        )
        break
      case 'updated_at_desc':
      default:
        // 默认已经按 updated_at 降序排列（在后端 API 中）
        break
    }

    // 分页
    const total = sessions.length
    const totalPages = Math.ceil(total / limit)
    const startIndex = (page - 1) * limit
    const endIndex = startIndex + limit
    const paginatedSessions = sessions.slice(startIndex, endIndex)

    return NextResponse.json({
      data: {
        sessions: paginatedSessions,
        pagination: {
          page,
          limit,
          total,
          totalPages,
          hasNext: page < totalPages,
          hasPrev: page > 1
        }
      },
      success: true
    })
  } catch (error) {
    console.error('Failed to list sessions:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve sessions',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
