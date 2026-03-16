import { NextRequest, NextResponse } from 'next/server'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * GET /api/models/config
 * 获取模型配置（代理到后端）
 */
export async function GET() {
  try {
    const response = await fetch(`${API_SERVER_URL}/api/models/config`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to get model config:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to get model config',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * POST /api/models/config
 * 更新模型配置（代理到后端）
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${API_SERVER_URL}/api/models/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to update model config:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to update model config',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
