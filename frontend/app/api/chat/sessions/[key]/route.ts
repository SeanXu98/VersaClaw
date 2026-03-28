import { NextRequest, NextResponse } from 'next/server'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * GET /api/chat/sessions/[key]
 * 获取单个会话的详细信息和消息历史
 *
 * Query parameters:
 * - limit: 返回最新的N条消息（可选）
 * - offset: 跳过前N条消息（可选）
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ key: string }> }
) {
  try {
    const { key: sessionKey } = await params
    const searchParams = request.nextUrl.searchParams
    const limit = searchParams.get('limit') ? parseInt(searchParams.get('limit')!, 10) : undefined
    const offset = searchParams.get('offset') ? parseInt(searchParams.get('offset')!, 10) : 0

    // 调用后端 API
    const apiResponse = await fetch(`${API_SERVER_URL}/api/sessions/${sessionKey}`)

    // 如果会话不存在（新会话），返回空消息列表而不是错误
    if (!apiResponse.ok) {
      if (apiResponse.status === 404) {
        // 新会话，返回空的消息列表
        return NextResponse.json({
          data: {
            key: sessionKey,
            metadata: {
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            },
            messages: [],
            totalMessages: 0
          },
          success: true
        })
      }
      throw new Error(`API server returned ${apiResponse.status}`)
    }

    const apiData = await apiResponse.json()
    if (!apiData.success) {
      // 会话不存在时，返回空消息列表（支持中文和英文错误信息）
      if (apiData.error === 'Session not found' || apiData.error === '会话不存在') {
        return NextResponse.json({
          data: {
            key: sessionKey,
            metadata: {
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString()
            },
            messages: [],
            totalMessages: 0
          },
          success: true
        })
      }
      throw new Error(apiData.error || 'Failed to get session')
    }

    // 应用分页参数
    let messages = apiData.data.messages || []
    const totalMessages = messages.length
    if (offset > 0) {
      messages = messages.slice(offset)
    }
    if (limit && limit > 0) {
      messages = messages.slice(0, limit)
    }

    return NextResponse.json({
      data: {
        key: sessionKey,
        metadata: apiData.data.metadata,
        messages,
        totalMessages
      },
      success: true
    })
  } catch (error) {
    console.error('Failed to read session:', error)
    // 对于新会话，返回空消息列表而不是错误
    return NextResponse.json({
      data: {
        key: 'unknown',
        metadata: {
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        messages: [],
        totalMessages: 0
      },
      success: true
    })
  }
}

/**
 * DELETE /api/chat/sessions/[key]
 * 删除指定会话
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ key: string }> }
) {
  try {
    const { key: sessionKey } = await params

    // 调用后端 API
    const apiResponse = await fetch(`${API_SERVER_URL}/api/sessions/${sessionKey}`, {
      method: 'DELETE'
    })

    if (!apiResponse.ok) {
      throw new Error(`API server returned ${apiResponse.status}`)
    }

    const apiData = await apiResponse.json()
    if (!apiData.success) {
      throw new Error(apiData.error || 'Failed to delete session')
    }

    return NextResponse.json({
      data: { message: 'Session deleted successfully' },
      success: true
    })
  } catch (error) {
    console.error('Failed to delete session:', error)
    return NextResponse.json(
      {
        error: 'Failed to delete session',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
