import { NextResponse } from 'next/server'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * GET /api/models/providers
 * 获取所有提供商列表及其配置状态（代理到后端）
 */
export async function GET() {
  try {
    const response = await fetch(`${API_SERVER_URL}/api/models/providers`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to list providers:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to retrieve providers',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
