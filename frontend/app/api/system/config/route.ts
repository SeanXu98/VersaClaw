import { NextRequest, NextResponse } from 'next/server'
import { readConfig, writeConfig } from '@/lib/nanobot/config'
import type { NanobotConfig } from '@/types/nanobot'

const API_SERVER_URL = process.env.NANOBOT_API_URL || 'http://localhost:18790'

/**
 * GET /api/system/config
 * 获取完整的Nanobot配置
 */
export async function GET() {
  try {
    const config = await readConfig()
    return NextResponse.json({ data: config, success: true })
  } catch (error) {
    console.error('Failed to read config:', error)
    return NextResponse.json(
      {
        error: 'Failed to read configuration',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * PUT /api/system/config
 * 更新Nanobot配置（原子性写入）并触发后端重载
 */
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json() as NanobotConfig

    // 验证配置格式（基本验证）
    if (typeof body !== 'object' || body === null) {
      return NextResponse.json(
        { error: 'Invalid configuration format' },
        { status: 400 }
      )
    }

    // 写入配置（原子性操作）
    await writeConfig(body)

    // 触发后端API服务器重载配置
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
      // 继续返回成功，因为配置已保存
    }

    return NextResponse.json({
      data: { message: 'Configuration updated and reloaded' },
      success: true
    })
  } catch (error) {
    console.error('Failed to write config:', error)
    return NextResponse.json(
      {
        error: 'Failed to update configuration',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * PATCH /api/system/config
 * 部分更新配置并触发后端重载
 */
export async function PATCH(request: NextRequest) {
  try {
    const updates = await request.json() as Partial<NanobotConfig>

    // 验证更新格式
    if (typeof updates !== 'object' || updates === null) {
      return NextResponse.json(
        { error: 'Invalid update format' },
        { status: 400 }
      )
    }

    // 读取当前配置
    const current = await readConfig()

    // 深度合并配置
    const merged = deepMerge(current, updates)

    // 写入更新后的配置
    await writeConfig(merged)

    // 触发后端API服务器重载配置
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
      // 继续返回成功，因为配置已保存
    }

    return NextResponse.json({
      data: { message: 'Configuration updated and reloaded' },
      success: true
    })
  } catch (error) {
    console.error('Failed to patch config:', error)
    return NextResponse.json(
      {
        error: 'Failed to update configuration',
        details: (error as Error).message
      },
      { status: 500 }
    )
  }
}

/**
 * 深度合并两个对象
 */
function deepMerge<T extends Record<string, any>>(target: T, source: Partial<T>): T {
  const result = { ...target }

  for (const key in source) {
    const sourceValue = source[key]
    const targetValue = result[key]

    if (sourceValue && typeof sourceValue === 'object' && !Array.isArray(sourceValue)) {
      if (targetValue && typeof targetValue === 'object' && !Array.isArray(targetValue)) {
        result[key] = deepMerge(targetValue, sourceValue)
      } else {
        result[key] = sourceValue
      }
    } else {
      result[key] = sourceValue as T[Extract<keyof T, string>]
    }
  }

  return result
}
