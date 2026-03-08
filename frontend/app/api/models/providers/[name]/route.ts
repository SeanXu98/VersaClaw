import { NextRequest, NextResponse } from 'next/server'
import type { ProviderConfig } from '@/types/nanobot'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * GET /api/models/providers/[name]
 * 获取单个提供商的配置（代理到后端）
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params

    const response = await fetch(`${API_SERVER_URL}/api/models/providers/${name}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to get provider config:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to get provider config',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * POST /api/models/providers/[name]
 * 配置或更新提供商（代理到后端）
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    const body = await request.json() as ProviderConfig

    // 验证必填字段
    if (!body.api_key) {
      return NextResponse.json(
        { success: false, error: 'API key is required' },
        { status: 400 }
      )
    }

    // 代理请求到后端
    const response = await fetch(`${API_SERVER_URL}/api/models/providers/${name}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: body.api_key,
        api_base: body.api_base || null,
        models: body.models || null,
        extra_headers: body.extra_headers || null
      })
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to configure provider:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to configure provider',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * DELETE /api/models/providers/[name]
 * 删除提供商配置（代理到后端）
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params

    const response = await fetch(`${API_SERVER_URL}/api/models/providers/${name}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    })

    const data = await response.json()

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status })
    }

    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to delete provider:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to delete provider',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}
