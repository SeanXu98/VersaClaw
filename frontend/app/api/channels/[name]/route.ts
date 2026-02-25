import { NextRequest, NextResponse } from 'next/server'
import { readConfig, writeConfig } from '@/lib/nanobot/config'

/**
 * GET /api/channels/[name]
 * 获取单个渠道的配置
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    const config = await readConfig()

    const channelConfig = config.channels?.[name]

    if (!channelConfig) {
      return NextResponse.json(
        { error: 'Channel not configured' },
        { status: 404 }
      )
    }

    // 遮罩敏感信息
    const maskedConfig = maskSensitiveFields(channelConfig)

    return NextResponse.json({
      data: maskedConfig,
      success: true
    })
  } catch (error) {
    console.error('Failed to get channel config:', error)
    return NextResponse.json(
      {
        error: 'Failed to retrieve channel configuration',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * POST /api/channels/[name]
 * 配置或更新渠道
 */
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    const body = await request.json()

    // 读取当前配置
    const config = await readConfig()

    // 更新渠道配置
    if (!config.channels) {
      config.channels = {}
    }

    config.channels[name] = body

    // 保存配置
    await writeConfig(config)

    return NextResponse.json({
      data: { message: 'Channel configured successfully' },
      success: true
    })
  } catch (error) {
    console.error('Failed to configure channel:', error)
    return NextResponse.json(
      {
        error: 'Failed to configure channel',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * DELETE /api/channels/[name]
 * 删除渠道配置
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ name: string }> }
) {
  try {
    const { name } = await params
    const config = await readConfig()

    if (!config.channels || !config.channels[name]) {
      return NextResponse.json(
        { error: 'Channel not configured' },
        { status: 404 }
      )
    }

    // 删除渠道配置
    delete config.channels[name]

    // 保存配置
    await writeConfig(config)

    return NextResponse.json({
      data: { message: 'Channel removed successfully' },
      success: true
    })
  } catch (error) {
    console.error('Failed to delete channel:', error)
    return NextResponse.json(
      {
        error: 'Failed to delete channel',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * 遮罩敏感字段（token, secret, password等）
 */
function maskSensitiveFields(config: any): any {
  const masked = { ...config }
  const sensitiveKeys = ['token', 'secret', 'password', 'api_key', 'app_secret', 'client_secret', 'bridge_token', 'claw_token', 'bot_token', 'app_token']

  for (const key of Object.keys(masked)) {
    if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
      const value = masked[key]
      if (typeof value === 'string' && value.length > 8) {
        masked[key] = `${value.slice(0, 4)}...${value.slice(-4)}`
      } else {
        masked[key] = '****'
      }
    }
  }

  return masked
}
