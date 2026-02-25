import { NextRequest, NextResponse } from 'next/server'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * POST /api/chat
 * 发送消息到 Nanobot
 * 注意：消息由后端 Nanobot API 保存到会话文件，前端只负责转发请求
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json() as {
      message: string
      sessionKey?: string
      model?: string
    }

    const { message, sessionKey, model } = body

    if (!message || message.trim() === '') {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      )
    }

    // 生成会话 key（如果未提供）
    const targetSessionKey = sessionKey || `web:${Date.now()}`

    // 调用 Nanobot API 获取响应（后端会保存消息到会话文件）
    let assistantResponse = ''
    try {
      const apiResponse = await fetch(`${API_SERVER_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_key: targetSessionKey,
          model: model || undefined
        })
      })

      if (!apiResponse.ok) {
        throw new Error(`API server returned ${apiResponse.status}`)
      }

      const apiData = await apiResponse.json()
      if (apiData.success && apiData.data?.response) {
        assistantResponse = apiData.data.response
      } else {
        throw new Error(apiData.error || 'No response from Nanobot')
      }
    } catch (apiError) {
      console.error('Failed to call Nanobot API:', apiError)
      return NextResponse.json(
        {
          error: 'Failed to get response from Nanobot',
          details: (apiError as Error).message
        },
        { status: 500 }
      )
    }

    return NextResponse.json({
      data: {
        message: message,
        response: assistantResponse,
        sessionKey: targetSessionKey
      },
      success: true
    })
  } catch (error) {
    console.error('Failed to send message:', error)
    return NextResponse.json(
      {
        error: 'Failed to send message',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
