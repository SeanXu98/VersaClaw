import { NextRequest } from 'next/server'
import type { UploadedImage } from '@/types/nanobot'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * POST /api/chat/stream
 * 流式聊天接口，代理后端SSE事件流
 *
 * 事件类型:
 * - content: 文本内容块
 * - reasoning: 推理内容块
 * - tool_call_start: 工具调用开始
 * - tool_call_end: 工具调用结束
 * - iteration_start: Agent迭代开始
 * - done: 处理完成
 * - error: 错误
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json() as {
      message: string
      sessionKey?: string
      model?: string
      images?: UploadedImage[]
    }

    const { message, sessionKey, model, images } = body

    if (!message || message.trim() === '') {
      return new Response(
        JSON.stringify({ error: 'Message is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // 生成会话 key（如果未提供）
    const targetSessionKey = sessionKey || `web:${Date.now()}`

    // 构建请求体，如果有图片则包含图片信息
    const requestBody: Record<string, unknown> = {
      message: message,
      session_key: targetSessionKey,
      model: model || undefined
    }

    // 如果有图片，转换格式后发送给后端
    if (images && images.length > 0) {
      requestBody.images = images.map(img => ({
        id: img.id,
        filename: img.filename,
        url: img.url,
        mime_type: img.mime_type
      }))
    }

    // 调用 Nanobot API 的流式端点
    const apiResponse = await fetch(`${API_SERVER_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(requestBody)
    })

    if (!apiResponse.ok) {
      return new Response(
        JSON.stringify({ error: `API server returned ${apiResponse.status}` }),
        { status: apiResponse.status, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // 直接转发SSE流
    return new Response(apiResponse.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      }
    })
  } catch (error) {
    console.error('Failed to stream chat:', error)
    return new Response(
      JSON.stringify({
        error: 'Failed to stream chat',
        details: (error as Error).message
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
