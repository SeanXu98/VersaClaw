import { NextRequest, NextResponse } from 'next/server'
import { readConfig, writeConfig } from '@/lib/nanobot/config'
import type { ProviderConfig } from '@/types/nanobot'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * GET /api/models/providers/[name]
 * 获取单个提供商的配置
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    const config = await readConfig()

    const providerConfig = config.providers?.[name]

    if (!providerConfig) {
      return NextResponse.json(
        { error: 'Provider not configured' },
        { status: 404 }
      )
    }

    // 不返回完整的API密钥，只返回遮罩版本
    const maskedConfig = {
      ...providerConfig,
      api_key: maskApiKey(providerConfig.apiKey)
    }

    return NextResponse.json({
      data: maskedConfig,
      success: true
    })
  } catch (error) {
    console.error('Failed to get provider config:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve provider configuration',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * POST /api/models/providers/[name]
 * 配置或更新提供商
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
        { error: 'API key is required' },
        { status: 400 }
      )
    }

    // 读取当前配置
    const config = await readConfig()

    // 更新提供商配置
    if (!config.providers) {
      config.providers = {}
    }

    // 保存配置 - 使用 snake_case 格式以兼容 Python 后端
    // 注意：writeConfig 会自动将 camelCase 转换为 snake_case
    config.providers[name] = {
      apiKey: body.api_key,
      apiBase: body.api_base,
      models: body.models,
      extraHeaders: body.extra_headers
    }

    // 如果用户配置了模型，将第一个模型设置为默认模型
    if (body.models && body.models.length > 0) {
      if (!config.agents) {
        config.agents = { defaults: { model: body.models[0] } }
      } else if (!config.agents.defaults) {
        config.agents.defaults = { model: body.models[0] }
      } else {
        config.agents.defaults.model = body.models[0]
      }
    }

    // 保存配置（会自动转换为 snake_case）
    await writeConfig(config)

    // 触发后端重载
    try {
      const reloadResponse = await fetch(`${API_SERVER_URL}/api/config/reload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (!reloadResponse.ok) {
        console.warn('Failed to trigger backend config reload:', reloadResponse.statusText)
      } else {
        const reloadData = await reloadResponse.json()
        console.log('Backend config reload:', reloadData)
      }
    } catch (reloadError) {
      console.warn('Backend config reload failed (server may not be running):', reloadError)
    }

    return NextResponse.json({
      data: { message: 'Provider configured successfully' },
      success: true
    })
  } catch (error) {
    console.error('Failed to configure provider:', error)
    return NextResponse.json(
      {
        error: 'Failed to configure provider',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * DELETE /api/models/providers/[name]
 * 删除提供商配置
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    const config = await readConfig()

    if (!config.providers || !config.providers[name]) {
      return NextResponse.json(
        { error: 'Provider not configured' },
        { status: 404 }
      )
    }

    // 删除提供商配置
    delete config.providers[name]

    // 保存配置
    await writeConfig(config)

    return NextResponse.json({
      data: { message: 'Provider removed successfully' },
      success: true
    })
  } catch (error) {
    console.error('Failed to delete provider:', error)
    return NextResponse.json(
      {
        error: 'Failed to delete provider',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * 遮罩API密钥
 */
function maskApiKey(key?: string): string {
  if (!key) return '****'
  if (key.length <= 8) return '****'
  return `${key.slice(0, 4)}...${key.slice(-4)}`
}
